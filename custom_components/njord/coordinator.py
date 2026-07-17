"""Data update coordinator for njord."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field, replace

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .grpc_client import NjordClient
from .models import EnrichmentData, ForecastData, NjordLocation

_LOGGER = logging.getLogger(__name__)

_ENRICHMENT_MERGE_FIELDS = ("alerts", "indices", "trends", "energy", "derived", "history", "consensus")
_ENRICHMENT_DEFAULTS: dict[str, object] = {
    "alerts": [],
    "indices": None,
    "trends": None,
    "energy": None,
    "derived": None,
    "history": None,
    "consensus": None,
}


def merge_enrichment(existing: EnrichmentData | None, event: EnrichmentData) -> EnrichmentData:
    """Merge a partial enrichment event into existing data.

    Only fields that differ from defaults in the event are applied.
    """
    if existing is None:
        existing = EnrichmentData(location=event.location)

    updates: dict[str, object] = {}
    for field_name in _ENRICHMENT_MERGE_FIELDS:
        event_value = getattr(event, field_name)
        default_value = _ENRICHMENT_DEFAULTS[field_name]
        if event_value != default_value:
            updates[field_name] = event_value

    if not updates:
        return existing

    return replace(existing, **updates)


@dataclass
class NjordCoordinatorData:
    forecasts: dict[tuple[str, str], ForecastData] = field(default_factory=dict)
    enrichments: dict[str, EnrichmentData] = field(default_factory=dict)


EntityFactory = Callable[[NjordLocation], list]


class NjordDataCoordinator(DataUpdateCoordinator[NjordCoordinatorData]):
    """Stream-driven coordinator for njord forecast, enrichment, and config data."""

    def __init__(self, hass: HomeAssistant, client: NjordClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="njord",
            update_interval=None,
        )
        self.client = client
        self._known_locations: set[str] = set()
        self._stream_tasks: list[asyncio.Task] = []
        self._entity_factories: dict[str, tuple[AddEntitiesCallback, EntityFactory]] = {}

    async def _async_update_data(self) -> NjordCoordinatorData:
        """Unary first-refresh: fetch all data via single calls."""
        try:
            config = await self.client.get_config()
        except Exception as err:
            raise UpdateFailed(f"Failed to get njord config: {err}") from err

        result = NjordCoordinatorData()

        for location in config.locations:
            self._known_locations.add(location.name)

            for model in location.models:
                try:
                    forecast = await self.client.get_forecast(location.name, model)
                    result.forecasts[(location.name, model)] = forecast
                except Exception as err:
                    _LOGGER.warning(
                        "Failed to get forecast for %s/%s: %s",
                        location.name,
                        model,
                        err,
                    )
                    result.forecasts[(location.name, model)] = ForecastData(
                        location=location.name, model=model, updated_at=0
                    )

            try:
                enrichment = await self.client.get_enrichments(location.name)
                result.enrichments[location.name] = enrichment
            except Exception as err:
                _LOGGER.warning(
                    "Failed to get enrichments for %s: %s",
                    location.name,
                    err,
                )

        return result

    def register_entity_factory(
        self,
        platform: str,
        add_entities: AddEntitiesCallback,
        factory: EntityFactory,
    ) -> None:
        self._entity_factories[platform] = (add_entities, factory)

    def start_streams(self) -> None:
        self._stream_tasks = [
            self.hass.async_create_background_task(self._run_forecast_stream(), "njord_forecast_stream"),
            self.hass.async_create_background_task(self._run_enrichment_stream(), "njord_enrichment_stream"),
            self.hass.async_create_background_task(self._run_config_stream(), "njord_config_stream"),
        ]

    async def stop_streams(self) -> None:
        for task in self._stream_tasks:
            task.cancel()
        await asyncio.gather(*self._stream_tasks, return_exceptions=True)
        self._stream_tasks.clear()

    async def _run_forecast_stream(self) -> None:
        try:
            async for update in self.client.stream_forecasts(location=None):
                self.data.forecasts[(update.location, update.model)] = update
                self.async_set_updated_data(self.data)
        except asyncio.CancelledError:
            return

    async def _run_enrichment_stream(self) -> None:
        try:
            async for event in self.client.stream_enrichments(location=None):
                existing = self.data.enrichments.get(event.location)
                self.data.enrichments[event.location] = merge_enrichment(existing, event)
                self.async_set_updated_data(self.data)
        except asyncio.CancelledError:
            return

    async def _run_config_stream(self) -> None:
        try:
            async for config in self.client.stream_config():
                new_locations = [loc for loc in config.locations if loc.name not in self._known_locations]
                for location in new_locations:
                    await self._create_entities_for_location(location)
        except asyncio.CancelledError:
            return

    async def _create_entities_for_location(self, location: NjordLocation) -> None:
        self._known_locations.add(location.name)

        for model in location.models:
            try:
                forecast = await self.client.get_forecast(location.name, model)
                self.data.forecasts[(location.name, model)] = forecast
            except Exception as err:
                _LOGGER.warning(
                    "Failed to get initial forecast for new location %s/%s: %s",
                    location.name,
                    model,
                    err,
                )

        try:
            enrichment = await self.client.get_enrichments(location.name)
            self.data.enrichments[location.name] = enrichment
        except Exception as err:
            _LOGGER.warning(
                "Failed to get initial enrichments for new location %s: %s",
                location.name,
                err,
            )

        for platform, (add_entities, factory) in self._entity_factories.items():
            try:
                entities = factory(location)
                if entities:
                    add_entities(entities)
            except Exception as err:
                _LOGGER.error(
                    "Failed to create %s entities for %s: %s",
                    platform,
                    location.name,
                    err,
                )

        self.async_set_updated_data(self.data)

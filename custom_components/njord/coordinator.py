"""Data update coordinator for njord."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue, async_delete_issue
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, Domain, StreamName
from .grpc_client import NjordClient
from .models import DomainData, EnrichmentData, LifestyleData, ModelInfoData, NjordLocation, ServerStatusData

_LOGGER = logging.getLogger(__name__)

_STREAM_DISCONNECT_GRACE = 60.0

# Domains the integration creates entities for; solar data is served but has no entities yet.
TRACKED_DOMAINS: tuple[Domain, ...] = (Domain.WEATHER, Domain.AIR_QUALITY, Domain.FLOOD, Domain.MARINE)


@dataclass
class NjordCoordinatorData:
    locations: list[NjordLocation] = field(default_factory=list)
    domains: dict[tuple[str, Domain], DomainData] = field(default_factory=dict)
    enrichments: dict[str, EnrichmentData] = field(default_factory=dict)
    lifestyle: dict[tuple[str, str], LifestyleData] = field(default_factory=dict)
    model_info: dict[str, ModelInfoData] = field(default_factory=dict)
    active_enrichments: set[str] | None = None

    def locations_with(self, domain: Domain) -> list[str]:
        return sorted({location for location, kind in self.domains if kind == domain})

    @property
    def location_names(self) -> list[str]:
        names = {location.name for location in self.locations}
        names.update(location for location, _ in self.domains)
        return sorted(names)


# Called for every (location, domain) pair that appears for the first time; returns the new entities.
EntityFactory = Callable[[str, Domain], list]

# Called for every (location, lifestyle type) pair that appears for the first time; returns the new entities.
LifestyleEntityFactory = Callable[[str, str], list]


class NjordDataCoordinator(DataUpdateCoordinator[NjordCoordinatorData]):
    """Stream-driven coordinator for njord domain data and enrichments."""

    def __init__(self, hass: HomeAssistant, client: NjordClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="njord",
            update_interval=None,
        )
        self.client = client
        self._stream_tasks: list[asyncio.Task] = []
        self._entity_factories: dict[str, tuple[AddEntitiesCallback, EntityFactory]] = {}
        self._lifestyle_factories: dict[str, tuple[AddEntitiesCallback, LifestyleEntityFactory]] = {}
        self.stream_states: dict[StreamName, bool] = {name: False for name in StreamName}
        self._stream_disconnect_times: dict[StreamName, float] = {}
        self._stream_issue_created: dict[StreamName, bool] = {}

    async def _async_update_data(self) -> NjordCoordinatorData:
        """Unary first-refresh: fetch the catalog, every tracked domain and the alerts of each location."""
        try:
            catalog = await self.client.get_catalog()
        except Exception as err:
            raise UpdateFailed(f"Failed to get njord catalog: {err}") from err

        result = NjordCoordinatorData(locations=list(catalog.locations))
        result.model_info.update(catalog.model_info)

        for location in catalog.locations:
            for domain in TRACKED_DOMAINS:
                try:
                    data = await self.client.get_domain_data(location.name, domain)
                except Exception as err:
                    _LOGGER.debug("No %s data for %s: %s", domain, location.name, err)
                    continue
                if data is not None:
                    result.domains[(location.name, domain)] = data

            try:
                enrichment = await self.client.get_enrichments(location.name)
                result.enrichments[location.name] = enrichment
                for item in enrichment.lifestyle:
                    result.lifestyle[(item.location, item.type)] = item
            except Exception as err:
                _LOGGER.warning("Failed to get enrichments for %s: %s", location.name, err)

        return result

    def register_entity_factory(
        self,
        platform: str,
        add_entities: AddEntitiesCallback,
        factory: EntityFactory,
    ) -> None:
        self._entity_factories[platform] = (add_entities, factory)

    def register_lifestyle_factory(
        self,
        platform: str,
        add_entities: AddEntitiesCallback,
        factory: LifestyleEntityFactory,
    ) -> None:
        self._lifestyle_factories[platform] = (add_entities, factory)

    def start_streams(self) -> None:
        self._stream_tasks = [
            self.hass.async_create_background_task(self._run_domain_stream(), "njord_domain_stream"),
            self.hass.async_create_background_task(self._run_enrichment_stream(), "njord_enrichment_stream"),
        ]

    async def stop_streams(self) -> None:
        for task in self._stream_tasks:
            task.cancel()
        await asyncio.gather(*self._stream_tasks, return_exceptions=True)
        self._stream_tasks.clear()

    def _on_stream_connect(self, name: StreamName) -> None:
        self.stream_states[name] = True
        self._stream_disconnect_times.pop(name, None)
        if self._stream_issue_created.get(name):
            async_delete_issue(self.hass, DOMAIN, f"stream_{name}_disconnected")
            self._stream_issue_created[name] = False
        self.async_set_updated_data(self.data)

    def _on_stream_disconnect(self, name: StreamName) -> None:
        self.stream_states[name] = False
        if name not in self._stream_disconnect_times:
            self._stream_disconnect_times[name] = self.hass.loop.time()
        elif not self._stream_issue_created.get(name):
            elapsed = self.hass.loop.time() - self._stream_disconnect_times[name]
            if elapsed >= _STREAM_DISCONNECT_GRACE:
                async_create_issue(
                    self.hass,
                    DOMAIN,
                    f"stream_{name}_disconnected",
                    is_fixable=False,
                    severity=IssueSeverity.WARNING,
                    translation_key=f"stream_{name}_disconnected",
                )
                self._stream_issue_created[name] = True
        self.async_set_updated_data(self.data)

    async def _run_domain_stream(self) -> None:
        try:
            async for update in self.client.stream_domain_data(
                location=None,
                domains=TRACKED_DOMAINS,
                on_reconnect=lambda: self._on_stream_connect(StreamName.DOMAIN),
                on_disconnect=lambda: self._on_stream_disconnect(StreamName.DOMAIN),
            ):
                key = (update.location, update.domain)
                is_new = key not in self.data.domains
                self.data.domains[key] = update
                if is_new:
                    self._create_entities_for(update.location, update.domain)
                self.async_set_updated_data(self.data)
        except asyncio.CancelledError:
            return
        except Exception:
            _LOGGER.exception("Domain data stream task failed")
            self._on_stream_disconnect(StreamName.DOMAIN)

    async def _run_enrichment_stream(self) -> None:
        try:
            async for event in self.client.stream_enrichments(
                location=None,
                on_reconnect=lambda: self._on_stream_connect(StreamName.ENRICHMENT),
                on_disconnect=lambda: self._on_stream_disconnect(StreamName.ENRICHMENT),
            ):
                if isinstance(event, LifestyleData):
                    self._apply_lifestyle(event)
                else:
                    self.data.enrichments[event.location] = event
                self.async_set_updated_data(self.data)
        except asyncio.CancelledError:
            return
        except Exception:
            _LOGGER.exception("Enrichment stream task failed")
            self._on_stream_disconnect(StreamName.ENRICHMENT)

    def _apply_lifestyle(self, item: LifestyleData) -> None:
        key = (item.location, item.type)
        is_new = key not in self.data.lifestyle
        self.data.lifestyle[key] = item
        if is_new:
            self._create_lifestyle_entities_for(item.location, item.type)

    def _create_lifestyle_entities_for(self, location: str, lifestyle_type: str) -> None:
        for platform, (add_entities, factory) in self._lifestyle_factories.items():
            try:
                entities = factory(location, lifestyle_type)
                if entities:
                    add_entities(entities)
            except Exception as err:
                _LOGGER.error("Failed to create %s entities for %s/%s: %s", platform, location, lifestyle_type, err)

    def _create_entities_for(self, location: str, domain: Domain) -> None:
        for platform, (add_entities, factory) in self._entity_factories.items():
            try:
                entities = factory(location, domain)
                if entities:
                    add_entities(entities)
            except Exception as err:
                _LOGGER.error("Failed to create %s entities for %s/%s: %s", platform, location, domain, err)


class NjordStatusCoordinator(DataUpdateCoordinator[ServerStatusData]):
    """Polling coordinator for njord server status (budget, uptime, poll targets)."""

    def __init__(self, hass: HomeAssistant, client: NjordClient, poll_interval: int = 30) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="njord_status",
            update_interval=timedelta(seconds=poll_interval),
        )
        self.client = client

    async def _async_update_data(self) -> ServerStatusData:
        try:
            status = await self.client.get_status()
        except Exception as err:
            raise UpdateFailed(f"Failed to get njord status: {err}") from err

        try:
            targets = await self.client.get_targets()
        except Exception:
            targets = []

        return replace(status, targets=targets)

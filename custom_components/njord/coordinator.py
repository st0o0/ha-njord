"""Data update coordinator for njord."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .grpc_client import NjordClient
from .models import EnrichmentData, ForecastData

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=5)


@dataclass
class NjordCoordinatorData:
    forecasts: dict[tuple[str, str], ForecastData] = field(default_factory=dict)
    enrichments: dict[str, EnrichmentData] = field(default_factory=dict)


class NjordDataCoordinator(DataUpdateCoordinator[NjordCoordinatorData]):
    """Fetch forecast and enrichment data from njord."""

    def __init__(self, hass: HomeAssistant, client: NjordClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="njord",
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> NjordCoordinatorData:
        """Fetch forecasts and enrichments for all locations."""
        try:
            config = await self.client.get_config()
        except Exception as err:
            raise UpdateFailed(f"Failed to get njord config: {err}") from err

        result = NjordCoordinatorData()

        for location in config.locations:
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

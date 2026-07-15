"""Data update coordinator for njord."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .grpc_client import NjordClient
from .models import ForecastData

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=5)


class NjordDataCoordinator(DataUpdateCoordinator[dict[tuple[str, str], ForecastData]]):
    """Fetch forecast data from njord for all location×model pairs."""

    def __init__(self, hass: HomeAssistant, client: NjordClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="njord",
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[tuple[str, str], ForecastData]:
        """Fetch forecasts for all location×model combinations."""
        try:
            config = await self.client.get_config()
        except Exception as err:
            raise UpdateFailed(f"Failed to get njord config: {err}") from err

        data: dict[tuple[str, str], ForecastData] = {}
        for location in config.locations:
            for model in location.models:
                try:
                    forecast = await self.client.get_forecast(location.name, model)
                    data[(location.name, model)] = forecast
                except Exception as err:
                    _LOGGER.warning(
                        "Failed to get forecast for %s/%s: %s",
                        location.name,
                        model,
                        err,
                    )

        return data

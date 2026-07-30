"""njord Weather integration for Home Assistant."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN
from .coordinator import NjordDataCoordinator, NjordStatusCoordinator
from .grpc_client import NjordClient

PLATFORMS = [Platform.WEATHER, Platform.BINARY_SENSOR, Platform.SENSOR, Platform.BUTTON, Platform.EVENT]

SERVICE_TRIGGER_POLL = "trigger_poll"
SERVICE_TRIGGER_POLL_SCHEMA = vol.Schema(
    {
        vol.Optional("location", default=""): str,
        vol.Optional("model", default=""): str,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up njord from a config entry."""
    client = NjordClient(
        host=entry.data["host"],
        port=entry.data["port"],
    )
    await client.connect()

    coordinator = NjordDataCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    status_coordinator = NjordStatusCoordinator(hass, client)
    try:
        await status_coordinator.async_config_entry_first_refresh()
    except Exception:
        status_coordinator = None

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "status_coordinator": status_coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    coordinator.start_streams()

    if not hass.services.has_service(DOMAIN, SERVICE_TRIGGER_POLL):

        async def handle_trigger_poll(call: ServiceCall) -> None:
            location = call.data.get("location", "")
            model = call.data.get("model", "")
            for entry_data in hass.data[DOMAIN].values():
                c: NjordClient = entry_data["client"]
                await c.trigger_poll(location=location, model=model)

        hass.services.async_register(
            DOMAIN,
            SERVICE_TRIGGER_POLL,
            handle_trigger_poll,
            schema=SERVICE_TRIGGER_POLL_SCHEMA,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a njord config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        coordinator: NjordDataCoordinator = entry_data["coordinator"]
        await coordinator.stop_streams()
        client: NjordClient = entry_data["client"]
        await client.close()

        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_TRIGGER_POLL)

    return unload_ok

"""Config flow for njord Weather integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback as ha_callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_DISABLED_ENRICHMENT_GROUPS,
    CONF_ENABLED_ENRICHMENT_GROUPS,
    CONF_SENSOR_PUSH,
    CONF_STATUS_POLL_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_STATUS_POLL_INTERVAL,
    DOMAIN,
    EnrichmentGroup,
    SensorKind,
    parse_enrichment_groups,
)
from .grpc_client import NjordClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    }
)

ENRICHMENT_GROUPS = [group.value for group in EnrichmentGroup]


class NjordConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for njord."""

    VERSION = 1

    @staticmethod
    @ha_callback
    def async_get_options_flow(config_entry):
        return NjordOptionsFlow(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._host: str = ""
        self._port: int = DEFAULT_PORT
        self._locations: list[str] = []
        self._model_count: int = 0

    async def _async_validate_connection(self, host: str, port: int) -> dict[str, str]:
        """Validate gRPC connection and populate location/model counts."""
        errors: dict[str, str] = {}
        client = NjordClient(host=host, port=port)
        try:
            await client.connect()
            catalog = await client.get_catalog()
            self._locations = [loc.name for loc in catalog.locations]
            self._model_count = sum(len(loc.models) for loc in catalog.locations)
        except Exception:
            _LOGGER.exception("Failed to connect to njord at %s:%s", host, port)
            errors["base"] = "cannot_connect"
        finally:
            await client.close()
        return errors

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port = user_input[CONF_PORT]

            unique_id = f"{self._host}:{self._port}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            errors = await self._async_validate_connection(self._host, self._port)

            if not errors:
                return self.async_create_entry(
                    title=f"njord ({self._host})",
                    data={CONF_HOST: self._host, CONF_PORT: self._port},
                    description_placeholders={
                        "locations": str(len(self._locations)),
                        "models": str(self._model_count),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            errors = await self._async_validate_connection(host, port)

            if not errors:
                new_unique_id = f"{host}:{port}"
                if new_unique_id != entry.unique_id:
                    await self.async_set_unique_id(new_unique_id)
                    self._abort_if_unique_id_configured()

                return self.async_update_reload_and_abort(
                    entry,
                    title=f"njord ({host})",
                    data={CONF_HOST: host, CONF_PORT: port},
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=entry.data[CONF_HOST]): str,
                    vol.Required(CONF_PORT, default=entry.data[CONF_PORT]): int,
                }
            ),
            errors=errors,
        )


class NjordOptionsFlow(OptionsFlow):
    """Handle options for njord."""

    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry
        self._init_data: dict[str, Any] = {}

    def _get_locations(self) -> list[str]:
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._config_entry.entry_id, {})
        coordinator = entry_data.get("coordinator")
        if coordinator is not None and hasattr(coordinator, "_known_locations"):
            return sorted(coordinator._known_locations)
        return []

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._init_data = user_input
            return await self.async_step_sensors()

        current_disabled = parse_enrichment_groups(self._config_entry.options.get(CONF_DISABLED_ENRICHMENT_GROUPS, []))
        current_enabled = [g for g in ENRICHMENT_GROUPS if g not in current_disabled]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_STATUS_POLL_INTERVAL,
                        default=self._config_entry.options.get(CONF_STATUS_POLL_INTERVAL, DEFAULT_STATUS_POLL_INTERVAL),
                    ): vol.All(int, vol.Range(min=10, max=300)),
                    vol.Required(
                        CONF_ENABLED_ENRICHMENT_GROUPS,
                        default=current_enabled,
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=ENRICHMENT_GROUPS,
                            multiple=True,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
        )

    async def async_step_sensors(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            old_disabled = parse_enrichment_groups(self._config_entry.options.get(CONF_DISABLED_ENRICHMENT_GROUPS, []))
            new_disabled = frozenset(EnrichmentGroup) - parse_enrichment_groups(
                self._init_data.get(CONF_ENABLED_ENRICHMENT_GROUPS, ENRICHMENT_GROUPS)
            )
            old_sensor_push = self._config_entry.options.get(CONF_SENSOR_PUSH, {})

            locations = self._get_locations()
            sensor_push: dict[str, dict[str, list[str]]] = {}
            for location in locations:
                sensor_push[location] = {}
                for kind in SensorKind:
                    key = f"{location}_{kind}"
                    sensor_push[location][kind.value] = user_input.get(key, [])

            options = {
                CONF_STATUS_POLL_INTERVAL: self._init_data[CONF_STATUS_POLL_INTERVAL],
                CONF_DISABLED_ENRICHMENT_GROUPS: sorted(group.value for group in new_disabled),
                CONF_SENSOR_PUSH: sensor_push,
            }
            result = self.async_create_entry(title="", data=options)

            needs_reload = new_disabled != old_disabled or sensor_push != old_sensor_push
            if needs_reload:
                self.hass.async_create_task(self.hass.config_entries.async_reload(self._config_entry.entry_id))

            return result

        locations = self._get_locations()
        current_sensor_push = self._config_entry.options.get(CONF_SENSOR_PUSH, {})

        schema_dict: dict[vol.Marker, Any] = {}
        for location in locations:
            loc_config = current_sensor_push.get(location, {})
            for kind in SensorKind:
                key = f"{location}_{kind}"
                default = loc_config.get(kind.value, [])
                schema_dict[vol.Optional(key, default=default)] = EntitySelector(
                    EntitySelectorConfig(
                        domain="sensor",
                        multiple=True,
                    )
                )

        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema(schema_dict),
        )

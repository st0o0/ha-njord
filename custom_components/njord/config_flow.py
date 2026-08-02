"""Config flow for njord Weather integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback as ha_callback
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode

from .const import DEFAULT_PORT, DOMAIN
from .grpc_client import NjordClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
        vol.Required("port", default=DEFAULT_PORT): int,
    }
)

ENRICHMENT_GROUPS = [
    "alerts",
    "indices",
    "trends",
    "energy",
    "derived",
    "history",
    "consensus",
]

DEFAULT_STATUS_POLL_INTERVAL = 30


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
            self._host = user_input["host"]
            self._port = user_input["port"]

            unique_id = f"{self._host}:{self._port}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            errors = await self._async_validate_connection(self._host, self._port)

            if not errors:
                return self.async_create_entry(
                    title=f"njord ({self._host})",
                    data={"host": self._host, "port": self._port},
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
            host = user_input["host"]
            port = user_input["port"]

            errors = await self._async_validate_connection(host, port)

            if not errors:
                new_unique_id = f"{host}:{port}"
                if new_unique_id != entry.unique_id:
                    await self.async_set_unique_id(new_unique_id)
                    self._abort_if_unique_id_configured()

                return self.async_update_reload_and_abort(
                    entry,
                    title=f"njord ({host})",
                    data={"host": host, "port": port},
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required("host", default=entry.data["host"]): str,
                    vol.Required("port", default=entry.data["port"]): int,
                }
            ),
            errors=errors,
        )


class NjordOptionsFlow(OptionsFlow):
    """Handle options for njord."""

    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            old_disabled = set(self._config_entry.options.get("disabled_enrichment_groups", []))
            new_disabled = set(ENRICHMENT_GROUPS) - set(user_input.get("enabled_enrichment_groups", ENRICHMENT_GROUPS))

            options = {
                "status_poll_interval": user_input["status_poll_interval"],
                "disabled_enrichment_groups": sorted(new_disabled),
            }
            result = self.async_create_entry(title="", data=options)

            if new_disabled != old_disabled:
                self.hass.async_create_task(self.hass.config_entries.async_reload(self._config_entry.entry_id))

            return result

        current_disabled = set(self._config_entry.options.get("disabled_enrichment_groups", []))
        current_enabled = [g for g in ENRICHMENT_GROUPS if g not in current_disabled]

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "status_poll_interval",
                        default=self._config_entry.options.get(
                            "status_poll_interval", DEFAULT_STATUS_POLL_INTERVAL
                        ),
                    ): vol.All(int, vol.Range(min=10, max=300)),
                    vol.Required(
                        "enabled_enrichment_groups",
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

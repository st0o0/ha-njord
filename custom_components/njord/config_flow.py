"""Config flow for njord Weather integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback as ha_callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_ENABLED_ENRICHMENTS,
    CONF_STATUS_POLL_INTERVAL,
    DEFAULT_ENABLED_ENRICHMENTS,
    DEFAULT_PORT,
    DEFAULT_STATUS_POLL_INTERVAL,
    DOMAIN,
    Enrichment,
    parse_enrichments,
)
from .grpc_client import NjordClient
from .helpers import enabled_enrichments_of

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    }
)

ENRICHMENT_OPTIONS = [enrichment.value for enrichment in Enrichment]


def _enrichment_selector() -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=ENRICHMENT_OPTIONS,
            multiple=True,
            mode=SelectSelectorMode.LIST,
            translation_key=CONF_ENABLED_ENRICHMENTS,
        )
    )


class NjordConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for njord."""

    VERSION = 2

    @staticmethod
    @ha_callback
    def async_get_options_flow(config_entry):
        return NjordOptionsFlow(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._host: str = ""
        self._port: int = DEFAULT_PORT
        self._locations: list[str] = []

    async def _async_validate_connection(self, host: str, port: int) -> dict[str, str]:
        """Validate the gRPC connection and remember the catalog's locations."""
        errors: dict[str, str] = {}
        client = NjordClient(host=host, port=port)
        try:
            await client.connect()
            catalog = await client.get_catalog()
            self._locations = [loc.name for loc in catalog.locations]
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

            await self.async_set_unique_id(f"{self._host}:{self._port}")
            self._abort_if_unique_id_configured()

            errors = await self._async_validate_connection(self._host, self._port)

            if not errors:
                return await self.async_step_enrichments()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_enrichments(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Choose which alert enrichments create entities."""
        if user_input is not None:
            enabled = parse_enrichments(user_input[CONF_ENABLED_ENRICHMENTS])
            return self.async_create_entry(
                title=f"njord ({self._host})",
                data={CONF_HOST: self._host, CONF_PORT: self._port},
                options={CONF_ENABLED_ENRICHMENTS: sorted(e.value for e in enabled)},
            )

        return self.async_show_form(
            step_id="enrichments",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ENABLED_ENRICHMENTS,
                        default=sorted(e.value for e in DEFAULT_ENABLED_ENRICHMENTS),
                    ): _enrichment_selector(),
                }
            ),
            description_placeholders={"locations": str(len(self._locations))},
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
                    unique_id=new_unique_id,
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

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            old_enabled = enabled_enrichments_of(self._config_entry)
            new_enabled = parse_enrichments(user_input[CONF_ENABLED_ENRICHMENTS])

            result = self.async_create_entry(
                title="",
                data={
                    CONF_STATUS_POLL_INTERVAL: user_input[CONF_STATUS_POLL_INTERVAL],
                    CONF_ENABLED_ENRICHMENTS: sorted(e.value for e in new_enabled),
                },
            )
            if new_enabled != old_enabled:
                self.hass.async_create_task(self.hass.config_entries.async_reload(self._config_entry.entry_id))
            return result

        current_enabled = sorted(e.value for e in enabled_enrichments_of(self._config_entry))
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_STATUS_POLL_INTERVAL,
                        default=self._config_entry.options.get(CONF_STATUS_POLL_INTERVAL, DEFAULT_STATUS_POLL_INTERVAL),
                    ): vol.All(int, vol.Range(min=10, max=300)),
                    vol.Required(CONF_ENABLED_ENRICHMENTS, default=current_enabled): _enrichment_selector(),
                }
            ),
        )

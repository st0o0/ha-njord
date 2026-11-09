"""Constants for the njord integration."""

from __future__ import annotations

from enum import StrEnum

from homeassistant.const import CONF_HOST, CONF_PORT

DOMAIN = "njord"

DEFAULT_PORT = 8081
DEFAULT_STATUS_POLL_INTERVAL = 30

__all__ = ["CONF_HOST", "CONF_PORT"]
CONF_STATUS_POLL_INTERVAL = "status_poll_interval"


class _WireEnum(StrEnum):
    @classmethod
    def _missing_(cls, value: object):
        return cls.UNSPECIFIED

    @property
    def is_known(self) -> bool:
        return self.value != "unspecified"


class PollPhase(_WireEnum):
    """Poll phase of a location target."""

    UNSPECIFIED = "unspecified"
    DISCOVERY = "discovery"
    STEADY = "steady"

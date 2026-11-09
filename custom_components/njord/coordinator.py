"""Status polling coordinator for njord."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .grpc_client import NjordClient
from .models import BudgetStatusData, LocationStatusData, PollPhase, ServerStatusData

_LOGGER = logging.getLogger(__name__)


def _ts_to_dt(ts) -> datetime | None:
    return ts.ToDatetime().replace(tzinfo=UTC) if ts.seconds or ts.nanos else None


def _parse_status(proto) -> ServerStatusData:
    budget = None
    if proto.budget:
        budget = BudgetStatusData(
            monthly_limit=proto.budget.monthly_limit,
            monthly_used=proto.budget.monthly_used,
            daily_limit=proto.budget.daily_limit,
            daily_used=proto.budget.daily_used,
            usage_percent=proto.budget.usage_percent,
        )

    _PHASE_MAP = {0: PollPhase.UNSPECIFIED, 1: PollPhase.DISCOVERY, 2: PollPhase.STEADY}

    statuses = [
        LocationStatusData(
            location=m.location,
            phase=_PHASE_MAP.get(m.phase, PollPhase.UNSPECIFIED),
            next_poll=_ts_to_dt(m.next_poll),
            last_change=_ts_to_dt(m.last_change) if m.HasField("last_change") else None,
            miss_count=m.miss_count,
            cycle_seconds=m.cycle_seconds if m.HasField("cycle_seconds") else None,
        )
        for m in proto.models
    ]

    return ServerStatusData(
        version=proto.version,
        uptime_seconds=proto.uptime_seconds,
        budget=budget,
        process_start=_ts_to_dt(proto.process_start),
        location_statuses=statuses,
        active_enrichments=list(proto.active_enrichments),
        budget_partial=proto.budget_partial,
        models_partial=proto.models_partial,
    )


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
            proto = await self.client.get_status()
        except Exception as err:
            raise UpdateFailed(f"Failed to get njord status: {err}") from err

        return _parse_status(proto)

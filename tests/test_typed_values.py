"""Tests pinning the typed closed-set values to the strings they replaced."""

from __future__ import annotations

import pytest
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from custom_components.njord.const import (
    ALERT_META,
    DOMAIN,
    AlertEvent,
    AlertSeverity,
    AlertType,
    EnrichmentGroup,
    SensorKind,
    StreamName,
    parse_enrichment_groups,
)
from custom_components.njord.helpers import group_enabled
from custom_components.njord.models import AlertData
from tests.conftest import init_integration

# --- enum values equal the strings used before ---


def test_enrichment_group_values() -> None:
    assert [g.value for g in EnrichmentGroup] == ["alerts", "indices", "trends", "derived", "consensus"]


def test_stream_name_values() -> None:
    assert [s.value for s in StreamName] == ["forecast", "enrichment", "config"]


def test_sensor_kind_values() -> None:
    assert [k.value for k in SensorKind] == ["indoor_temperature", "indoor_humidity"]


def test_alert_event_values() -> None:
    assert {e.name: e.value for e in AlertEvent} == {
        "STARTED": "alert_started",
        "ESCALATED": "alert_escalated",
        "DEESCALATED": "alert_deescalated",
        "CLEARED": "alert_cleared",
    }


def test_alert_type_values() -> None:
    assert [t.value for t in AlertType] == [
        "unspecified",
        "frost",
        "heat",
        "storm",
        "heavy_rain",
        "uv",
        "fog",
        "snow",
        "pressure_drop",
        "thunderstorm",
        "ice",
        "wind_chill",
        "visibility",
        "tropical_night",
        "humidity",
    ]


def test_alert_severity_values() -> None:
    assert [s.value for s in AlertSeverity] == ["none", "yellow", "orange", "red"]


def test_enum_members_format_as_plain_strings() -> None:
    assert f"{StreamName.FORECAST}_stream" == "forecast_stream"
    assert f"home_{AlertType.HEAVY_RAIN}_alert" == "home_heavy_rain_alert"
    assert f"home_{SensorKind.INDOOR_HUMIDITY}" == "home_indoor_humidity"
    assert str(EnrichmentGroup.ALERTS) == "alerts"


# --- tolerant parsing ---


def test_parse_enrichment_groups_ignores_unknown_names() -> None:
    assert parse_enrichment_groups(["trends", "history", "alerts"]) == {EnrichmentGroup.TRENDS, EnrichmentGroup.ALERTS}


def test_parse_enrichment_groups_handles_none() -> None:
    assert parse_enrichment_groups(None) == frozenset()


def test_unknown_alert_severity_reads_as_none() -> None:
    assert AlertSeverity("purple") is AlertSeverity.NONE


def test_unknown_alert_type_reads_as_unspecified() -> None:
    assert AlertType("solar_flare") is AlertType.UNSPECIFIED


def test_alert_data_coerces_strings_and_unknown_values() -> None:
    alert = AlertData(type="frost", severity="red")
    unknown = AlertData(type="solar_flare", severity="purple")
    assert alert.type is AlertType.FROST
    assert alert.severity is AlertSeverity.RED
    assert unknown.type is AlertType.UNSPECIFIED
    assert unknown.severity is AlertSeverity.NONE


def test_alert_severity_rank_order() -> None:
    ranks = [s.rank for s in (AlertSeverity.NONE, AlertSeverity.YELLOW, AlertSeverity.ORANGE, AlertSeverity.RED)]
    assert ranks == [0, 1, 2, 3]


# --- group_enabled truth table ---


@pytest.mark.parametrize(
    ("active", "disabled", "expected"),
    [
        (None, [], True),
        (None, ["alerts"], False),
        (None, ["trends"], True),
        (["alerts", "trends"], [], True),
        (["alerts", "trends"], ["alerts"], False),
        (["trends"], [], False),
        ([], [], False),
        (set(), ["alerts"], False),
        (None, ["history"], True),
    ],
)
def test_group_enabled_truth_table(active, disabled, expected) -> None:
    assert group_enabled(EnrichmentGroup.ALERTS, active, disabled) is expected


# --- alert metadata table ---

_EXPECTED_ALERT_META = {
    "frost": ("Frost Alert", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, 1, "mdi:snowflake-alert"),
    "heat": ("Heat Alert", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, 1, "mdi:thermometer-alert"),
    "storm": ("Storm Alert", UnitOfSpeed.METERS_PER_SECOND, SensorDeviceClass.WIND_SPEED, 0, "mdi:weather-hurricane"),
    "heavy_rain": ("Heavy Rain Alert", "mm", None, 1, "mdi:weather-pouring"),
    "uv": ("UV Alert", "UV", None, 0, "mdi:sun-wireless"),
    "fog": ("Fog Alert", UnitOfLength.METERS, SensorDeviceClass.DISTANCE, 0, "mdi:weather-fog"),
    "snow": ("Snow Alert", UnitOfLength.CENTIMETERS, SensorDeviceClass.DISTANCE, 0, "mdi:snowflake"),
    "pressure_drop": ("Pressure Drop Alert", UnitOfPressure.HPA, SensorDeviceClass.PRESSURE, 0, "mdi:gauge-low"),
    "thunderstorm": (
        "Thunderstorm Alert",
        UnitOfSpeed.METERS_PER_SECOND,
        SensorDeviceClass.WIND_SPEED,
        0,
        "mdi:weather-lightning",
    ),
    "ice": ("Ice Alert", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, 1, "mdi:snowflake-thermometer"),
    "wind_chill": (
        "Wind Chill Alert",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        1,
        "mdi:thermometer-minus",
    ),
    "visibility": ("Visibility Alert", UnitOfLength.METERS, SensorDeviceClass.DISTANCE, 0, "mdi:eye-off"),
    "tropical_night": (
        "Tropical Night Alert",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        1,
        "mdi:weather-night",
    ),
    "humidity": ("Humidity Alert", PERCENTAGE, SensorDeviceClass.HUMIDITY, 0, "mdi:water-percent"),
}


def test_alert_meta_covers_all_types_in_creation_order() -> None:
    assert [t.value for t in ALERT_META] == list(_EXPECTED_ALERT_META)
    assert AlertType.UNSPECIFIED not in ALERT_META


@pytest.mark.parametrize("alert_type", list(_EXPECTED_ALERT_META))
def test_alert_meta_values(alert_type: str) -> None:
    meta = ALERT_META[AlertType(alert_type)]
    assert (meta.name, meta.unit, meta.device_class, meta.precision, meta.icon) == _EXPECTED_ALERT_META[alert_type]


# --- entity identity is unchanged ---


async def test_unique_ids_unchanged(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    registry = er.async_get(hass)
    unique_ids = {e.unique_id for e in registry.entities.values() if e.config_entry_id == mock_config_entry.entry_id}
    prefix = f"{mock_config_entry.entry_id}_"

    expected = {f"{prefix}home_{t}_alert" for t in _EXPECTED_ALERT_META}
    expected |= {
        f"{prefix}home_{key}_index"
        for key in ("laundry", "outdoor", "running", "cycling", "bbq", "irrigation", "solar", "night_ventilation")
    }
    expected |= {
        f"{prefix}home_{suffix}"
        for suffix in (
            "vpd",
            "frost_hours",
            "frost_confidence",
            "weather_trend",
            "sunshine",
            "diurnal_amplitude",
            "beaufort",
            "wind_chill",
            "dewpoint_comfort",
            "inversion",
            "weather_alert",
            "consensus",
            "icon_d2",
            "ecmwf_ifs025",
            "icon_d2_target",
            "ecmwf_ifs025_target",
        )
    }
    expected |= {
        f"{prefix}{suffix}" for suffix in ("monthly_usage", "daily_usage", "version", "uptime", "trigger_poll")
    }
    expected |= {f"{prefix}{name}_stream" for name in ("forecast", "enrichment", "config")}

    assert unique_ids == expected


async def test_entity_ids_unchanged(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)

    registry = er.async_get(hass)
    entity_ids = {e.entity_id for e in registry.entities.values() if e.config_entry_id == mock_config_entry.entry_id}

    expected = {
        "event.home_weather_alert",
        "sensor.home_frost_alert",
        "sensor.home_heavy_rain_alert",
        "sensor.home_tropical_night_alert",
        "binary_sensor.server_forecast_stream",
        "binary_sensor.server_enrichment_stream",
        "binary_sensor.server_config_stream",
    }
    assert expected <= entity_ids


async def test_disabled_group_creates_no_entities_and_legacy_value_is_ignored(
    hass: HomeAssistant, mock_client, mock_config_entry
) -> None:
    hass.config_entries.async_update_entry(
        mock_config_entry, options={"disabled_enrichment_groups": ["trends", "history"]}
    )
    await init_integration(hass, mock_config_entry)

    unique_ids = {e.unique_id for e in er.async_get(hass).entities.values()}
    prefix = f"{mock_config_entry.entry_id}_"
    assert f"{prefix}home_weather_trend" not in unique_ids
    assert f"{prefix}home_frost_alert" in unique_ids


async def test_stream_issue_ids_unchanged(hass: HomeAssistant, mock_client, mock_config_entry) -> None:
    await init_integration(hass, mock_config_entry)
    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]

    for name in StreamName:
        coordinator._on_stream_disconnect(name)
        coordinator._stream_disconnect_times[name] -= 120
        coordinator._on_stream_disconnect(name)

    issues = {issue_id for domain, issue_id in ir.async_get(hass).issues if domain == DOMAIN}
    assert issues == {"stream_forecast_disconnected", "stream_enrichment_disconnected", "stream_config_disconnected"}


# --- stale stored sensor kinds ---


async def test_stale_stored_sensor_kind_is_skipped_on_setup(hass: HomeAssistant, mock_client) -> None:
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"host": "localhost", "port": 8081},
        title="njord (localhost)",
        unique_id="localhost:8081",
        options={"sensor_push": {"home": {"outdoor_pressure": ["sensor.old"], "indoor_humidity": ["sensor.hum"]}}},
    )
    entry.add_to_hass(hass)

    await init_integration(hass, entry)

    assert entry.state.value == "loaded"
    mock_client.push_sensor.reset_mock()
    hass.states.async_set("sensor.old", "5")
    hass.states.async_set("sensor.hum", "40")
    await hass.async_block_till_done()
    mock_client.push_sensor.assert_awaited_once_with(SensorKind.INDOOR_HUMIDITY, "home", 40.0, source="sensor.hum")


async def test_stale_stored_sensor_kind_is_dropped_by_options_flow(
    hass: HomeAssistant, mock_client, mock_config_entry
) -> None:
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={"sensor_push": {"home": {"outdoor_pressure": ["sensor.old"], "indoor_humidity": ["sensor.hum"]}}},
    )
    await init_integration(hass, mock_config_entry)

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"status_poll_interval": 30, "enabled_enrichment_groups": []}
    )
    assert result["step_id"] == "sensors"
    keys = {k.schema: k.default() for k in result["data_schema"].schema}
    assert keys == {"home_indoor_temperature": [], "home_indoor_humidity": ["sensor.hum"]}

    result = await hass.config_entries.options.async_configure(result["flow_id"], user_input={})
    assert result["type"] == "create_entry"
    stored = mock_config_entry.options["sensor_push"]["home"]
    assert stored == {"indoor_temperature": [], "indoor_humidity": ["sensor.hum"]}
    assert all(type(kind) is str for kind in stored)
    assert all(type(group) is str for group in mock_config_entry.options["disabled_enrichment_groups"])


def test_condition_constants_keep_their_strings() -> None:
    from custom_components.njord.condition_mapper import WMO_TO_HA

    conditions = {c for pair in WMO_TO_HA.values() for c in pair}
    assert conditions == {
        "sunny",
        "clear-night",
        "partlycloudy",
        "cloudy",
        "fog",
        "rainy",
        "pouring",
        "snowy",
        "lightning-rainy",
        "hail",
    }

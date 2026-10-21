"""Tests for typed models and wire-enum helpers."""

from __future__ import annotations

from custom_components.njord.const import (
    ALERT_META,
    FEATURE_KEYS,
    AlertSeverity,
    AlertType,
    Domain,
    Feature,
    PollPhase,
    StreamName,
    enabled_alert_types,
    feature_enabled,
)
from custom_components.njord.coordinator import NjordCoordinatorData
from custom_components.njord.models import AlertData, TargetData, WeatherDomainData


def test_alert_data_coerces_strings_to_enums():
    alert = AlertData(type="frost", severity="red")
    assert alert.type is AlertType.FROST
    assert alert.severity is AlertSeverity.RED


def test_alert_data_unknown_values_fall_back():
    alert = AlertData(type="meteor", severity="purple")
    assert alert.type is AlertType.UNSPECIFIED
    assert alert.severity is AlertSeverity.NONE


def test_severity_rank_is_ordered():
    ranks = [s.rank for s in (AlertSeverity.NONE, AlertSeverity.YELLOW, AlertSeverity.ORANGE, AlertSeverity.RED)]
    assert ranks == [0, 1, 2, 3]


def test_unknown_domain_and_phase_read_as_unspecified():
    assert Domain("bogus") is Domain.UNSPECIFIED
    assert PollPhase("bogus") is PollPhase.UNSPECIFIED
    assert not PollPhase.UNSPECIFIED.is_known
    assert PollPhase.STEADY.is_known


def test_stream_names_are_domain_and_enrichment_only():
    assert {s.value for s in StreamName} == {"domain", "enrichment"}


def test_alert_meta_covers_all_alert_types_but_unspecified():
    assert set(ALERT_META) == set(AlertType) - {AlertType.UNSPECIFIED}
    assert len(ALERT_META) == 20


def test_every_feature_has_a_njord_key():
    assert set(FEATURE_KEYS) == set(Feature)
    assert len(FEATURE_KEYS) == 37


def test_feature_enabled_matches_case_insensitively():
    assert feature_enabled(Feature.SWIMMING_CONDITIONS, ["marine:swimming"])
    assert not feature_enabled(Feature.FROST, ["Marine:Swimming"])


def test_feature_enabled_without_active_list_enables_all():
    assert feature_enabled(Feature.FROST, None)
    assert feature_enabled(Feature.FROST, [])


def test_enabled_alert_types_filters_by_active_keys():
    types = enabled_alert_types(["Weather:Frost", "AirQuality:Pollen"])
    assert types == [AlertType.FROST, AlertType.POLLEN]


def test_enabled_alert_types_without_active_list_returns_all():
    assert len(enabled_alert_types(None)) == 20


def test_coordinator_data_location_helpers():
    from custom_components.njord.models import NjordLocation

    data = NjordCoordinatorData(
        locations=[NjordLocation("home", 1.0, 2.0)],
        domains={
            ("bern", Domain.WEATHER): WeatherDomainData("bern"),
            ("home", Domain.WEATHER): WeatherDomainData("home"),
            ("home", Domain.FLOOD): WeatherDomainData("home"),
        },
    )
    assert data.locations_with(Domain.WEATHER) == ["bern", "home"]
    assert data.locations_with(Domain.FLOOD) == ["home"]
    assert data.locations_with(Domain.MARINE) == []
    assert data.location_names == ["bern", "home"]


def test_target_data_defaults():
    target = TargetData(location="home", phase=PollPhase.STEADY)
    assert target.next_poll is None
    assert target.last_change is None
    assert target.miss_count == 0
    assert target.cycle_seconds is None


def test_multi_model_defaults():
    from custom_components.njord.models import ModelInfoData, WeatherDomainData

    assert ModelInfoData(id="x").enabled is True
    assert WeatherDomainData("home").model == ""


def test_primary_and_secondary_models():
    from custom_components.njord.coordinator import NjordCoordinatorData
    from custom_components.njord.models import ModelInfoData, NjordLocation

    data = NjordCoordinatorData(
        locations=[NjordLocation(name="home", latitude=1.0, longitude=2.0, models=["a", "b", "c", "d"])],
        model_info={"b": ModelInfoData(id="b", enabled=False), "c": ModelInfoData(id="c", enabled=True)},
    )

    assert data.primary_model("home") == "a"
    assert data.secondary_models("home") == ["c", "d"]
    assert data.primary_model("nowhere") is None
    assert data.secondary_models("nowhere") == []

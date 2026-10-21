"""Verify generated proto modules are importable."""

import importlib.util

import pytest


def test_common_pb2_importable():
    from custom_components.njord.proto.njord.v2 import common_pb2

    for name in ("LocationInfo", "ModelInfo", "AlertSeverity", "ConfidenceLevel"):
        assert hasattr(common_pb2, name)


def test_weather_pb2_importable():
    from custom_components.njord.proto.njord.v2 import weather_pb2

    for name in ("GetCatalogResponse", "GetDomainDataRequest", "DomainDataUpdate", "EnrichmentEvent"):
        assert hasattr(weather_pb2, name)


def test_ops_pb2_importable():
    from custom_components.njord.proto.njord.v2 import ops_pb2

    for name in ("StatusResponse", "TriggerPollRequest", "TriggerTarget"):
        assert hasattr(ops_pb2, name)


def test_grpc_stubs_importable():
    from custom_components.njord.proto.njord.v2 import ops_pb2_grpc, weather_pb2_grpc

    assert hasattr(weather_pb2_grpc, "WeatherServiceStub")
    assert hasattr(ops_pb2_grpc, "OpsServiceStub")


@pytest.mark.parametrize("module", ["admin_pb2", "sensor_pb2", "admin_pb2_grpc", "sensor_pb2_grpc"])
def test_removed_services_are_gone(module):
    assert importlib.util.find_spec(f"custom_components.njord.proto.njord.v2.{module}") is None


def test_multi_model_proto_fields_exist():
    from custom_components.njord.proto.njord.v2 import common_pb2, weather_pb2

    assert "enabled" in common_pb2.ModelInfo.DESCRIPTOR.fields_by_name
    assert "model" in weather_pb2.GetDomainDataRequest.DESCRIPTOR.fields_by_name
    assert "model" in weather_pb2.DomainDataUpdate.DESCRIPTOR.fields_by_name
    for name in ("ModelComparison", "ModelComparisonDay", "ModelDayValues"):
        assert hasattr(weather_pb2, name)
    assert "model_comparison" in weather_pb2.EnrichmentEvent.DESCRIPTOR.fields_by_name

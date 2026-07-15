"""Verify generated proto modules are importable."""


def test_forecast_service_pb2_importable():
    from custom_components.njord.proto.njord.v1 import forecast_service_pb2

    assert hasattr(forecast_service_pb2, "GetLocationsRequest")
    assert hasattr(forecast_service_pb2, "GetForecastResponse")
    assert hasattr(forecast_service_pb2, "HourlyForecast")


def test_config_service_pb2_importable():
    from custom_components.njord.proto.njord.v1 import config_service_pb2

    assert hasattr(config_service_pb2, "NjordConfig")
    assert hasattr(config_service_pb2, "LocationConfig")
    assert hasattr(config_service_pb2, "GetConfigRequest")


def test_forecast_service_grpc_importable():
    from custom_components.njord.proto.njord.v1 import forecast_service_pb2_grpc

    assert hasattr(forecast_service_pb2_grpc, "ForecastServiceStub")


def test_config_service_grpc_importable():
    from custom_components.njord.proto.njord.v1 import config_service_pb2_grpc

    assert hasattr(config_service_pb2_grpc, "ConfigServiceStub")

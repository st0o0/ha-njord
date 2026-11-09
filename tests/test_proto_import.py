"""Verify generated proto modules are importable."""


def test_njord_pb2_importable():
    from custom_components.njord.proto.njord import njord_pb2

    for name in (
        "ManifestRequest",
        "ManifestResponse",
        "StatusRequest",
        "StatusResponse",
        "EntityEvent",
        "EntitySnapshot",
        "EntityStateUpdate",
    ):
        assert hasattr(njord_pb2, name)


def test_grpc_stub_importable():
    from custom_components.njord.proto.njord import njord_pb2_grpc

    assert hasattr(njord_pb2_grpc, "NjordServiceStub")

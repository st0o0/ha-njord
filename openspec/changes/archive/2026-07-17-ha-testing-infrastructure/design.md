## Context

ha-njord currently tests with hand-rolled stubs for 15+ homeassistant modules. This allows testing entity logic in isolation but prevents testing HA integration points (config flow, platform setup, entity registry, coordinator lifecycle). Research of HA Core integrations (met, accuweather, openweathermap) and popular HACS integrations shows a universal pattern: use `pytest-homeassistant-custom-component` for the real HA runtime, and patch the external client (not HA internals).

## Goals / Non-Goals

**Goals:**
- All tests run against real HA runtime — no fake modules
- Config Flow tests work end-to-end
- Entity registration and state assertions via `hass.states`
- Tests remain runnable in Docker (no local Python required)

**Non-Goals:**
- CI/CD pipeline (separate change)
- Performance benchmarking of test suite
- Snapshot testing (may add later)

## Decisions

### 1. Full replacement, not hybrid

Replace all HA stubs with `pytest-homeassistant-custom-component` instead of maintaining two test layers. Every existing test already imports from `homeassistant.*` — the stubs just intercept those imports. Removing the stubs means the real modules load instead, with no import path changes needed.

**Alternative considered:** Hybrid (keep stubs for fast unit tests, add HA tests separately). Rejected because it means maintaining two conftest patterns and the stubs will drift from HA reality over time.

### 2. Mock NjordClient at the class level

Follow the HA Core pattern: patch `custom_components.njord.grpc_client.NjordClient` in conftest.py so that every test gets a mock client without touching gRPC. This replaces the current approach of manually constructing entity instances with mock coordinators.

```
BEFORE:  Stub HA modules → construct entities directly → test properties
AFTER:   Real HA runtime → patch NjordClient → async_setup_entry → assert hass.states
```

The gRPC client unit tests (`test_grpc_client.py`) are the exception — they test the real client against a mock gRPC server and don't need HA at all. These stay unchanged.

### 3. Test file structure stays flat

Keep all tests in `tests/` (no subdirectories). Add:
- `tests/test_init.py` — setup/unload lifecycle
- Expand `tests/test_config_flow.py` — real config flow tests

### 4. Docker test image

Use on-the-fly install in the existing `python:3.12-slim` image. The install of `pytest-homeassistant-custom-component` takes ~30-60s but avoids maintaining a custom Docker image.

```makefile
test:
    docker run --rm -v "$(pwd):/work" -w /work python:3.12-slim \
      sh -c "pip install --quiet pytest pytest-asyncio \
             pytest-homeassistant-custom-component \
             grpcio protobuf voluptuous && \
             python -m pytest tests/ -v"
```

**Alternative considered:** Pre-built Docker test image. Rejected for now — adds image maintenance overhead. Can revisit if install time becomes a bottleneck.

### 5. conftest.py structure

```python
# tests/conftest.py

@pytest.fixture
def mock_client():
    """Patch NjordClient to return a mock with canned responses."""
    with patch("custom_components.njord.NjordClient") as cls:
        client = AsyncMock()
        client.connect = AsyncMock()
        client.close = AsyncMock()
        client.get_config = AsyncMock(return_value=NjordConfigData(...))
        client.get_locations = AsyncMock(return_value=["home"])
        client.get_models = AsyncMock(return_value=["icon_d2"])
        client.get_forecast = AsyncMock(return_value=ForecastData(...))
        client.get_enrichments = AsyncMock(return_value=EnrichmentData(...))
        cls.return_value = client
        yield client

@pytest.fixture
def mock_config_entry():
    """Create a mock config entry for njord."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={"host": "localhost", "port": 8081},
        title="njord",
    )
```

Key: `enable_custom_integrations` fixture must be requested in tests that load `custom_components/` code.

## Risks / Trade-offs

**[Heavier test dependency]** → `pytest-homeassistant-custom-component` pulls in all of HA Core (~100+ packages). Mitigation: dev-only dependency, Docker-contained, no production impact.

**[Slower test install]** → ~30-60s pip install vs ~5s currently. Mitigation: Acceptable for correctness gain. Can add Docker image caching later.

**[HA version coupling]** → Tests now depend on a specific HA Core version. `pytest-homeassistant-custom-component` tracks HA releases daily. Mitigation: Pin the version in dev dependencies, update deliberately.

**[Some tests may need adjustment]** → Tests that directly construct entities (e.g., `NjordAlertEntity.__new__()`) may need to be rewritten to go through `async_setup_entry`. Mitigation: This is actually better — tests now exercise real setup paths.

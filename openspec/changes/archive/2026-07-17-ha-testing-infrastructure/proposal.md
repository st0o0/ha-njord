## Why

ha-njord tests currently use a 120-line hand-rolled HA stub layer in `conftest.py` that fakes 15+ homeassistant modules. This makes it impossible to test Config Flow, platform setup, entity registration, and coordinator lifecycle — the parts where most integration bugs live. Three tests are permanently skipped. Every new HA API we use requires a new stub. The HA Integration Quality Scale (Bronze) requires "automated tests that guard this integration can be configured correctly" — we can't achieve this with stubs.

## What Changes

- Replace the hand-rolled HA stub layer with `pytest-homeassistant-custom-component`, the community-standard test dependency that provides the real HA runtime in-process
- Rewrite `tests/conftest.py` from HA module stubs to NjordClient mock fixtures (patching the gRPC client, not faking HA)
- Adapt all existing tests to work with real HA imports instead of stubs
- Activate the 3 skipped Config Flow tests and make them work
- Add integration-level tests: `async_setup_entry`, platform entity registration, coordinator lifecycle
- Update Docker test command to install `pytest-homeassistant-custom-component`

## Non-goals

- No new feature code — this is pure test infrastructure
- No changes to the integration itself (no `custom_components/njord/*.py` modifications)
- No CI/CD pipeline setup (that's a separate change)
- No gRPC endpoints needed — all tests mock `NjordClient`

## Capabilities

### New Capabilities
- `ha-test-infrastructure`: Test fixtures, mock patterns, and Docker setup for running tests against real HA runtime

### Modified Capabilities
- `config-flow`: Adding proper integration tests that exercise the real HA config flow machinery
- `weather-entities`: Adding entity registration and state assertion tests via `hass.states`

## Impact

- **Deleted**: Current `tests/conftest.py` stub layer (~120 lines of HA module fakes)
- **New**: `tests/conftest.py` with NjordClient mock fixtures (~30 lines)
- **Modified**: All existing test files — import paths stay the same but work against real HA now
- **New tests**: `tests/test_init.py` (setup/unload), expanded `test_config_flow.py`
- **New dependency**: `pytest-homeassistant-custom-component` (dev-only, pulls in HA Core)
- **Docker**: Test command grows from `pip install grpcio protobuf pytest` to including `pytest-homeassistant-custom-component`

## Why

Sensor entities in ha-njord use raw string units (`"°C"`, `"km/h"`, `"hPa"`) without setting `device_class`. Without `device_class`, Home Assistant's automatic unit conversion does not activate — an American user with HA set to "US Customary" still sees Celsius and m/s on all sensor entities. The weather entity already works correctly (HA auto-converts via `native_*_unit`), but the 20+ enrichment/alert/diagnostic sensors are broken for non-metric users.

Additionally, no sensor sets `suggested_display_precision`, so HA uses inconsistent defaults across all sensor types.

## What Changes

- Add appropriate `device_class` to all sensor entities that report values in convertible units (temperature, speed, pressure, distance, precipitation)
- Replace raw unit strings (`"°C"`, `"km/h"`) with HA `UnitOf*` constants (`UnitOfTemperature.CELSIUS`, `UnitOfSpeed.KILOMETERS_PER_HOUR`)
- Set `suggested_display_precision` on all numeric sensor entities with sensible defaults per value type
- No config flow changes — HA's built-in unit system handles conversion automatically

## Non-goals

- No unit selection config flow or options flow in ha-njord — HA handles this globally
- No server-side changes to njord — values continue to arrive in metric
- No changes to the weather entity — it already uses HA's native unit pattern correctly
- No changes to non-numeric sensors (trend stability label, battery strategy)

## gRPC Endpoints

No new or modified gRPC endpoints required. All existing endpoints deliver metric values unchanged.

## Capabilities

### New Capabilities

- `sensor-units-precision`: Covers device_class assignment, HA unit constant usage, and suggested_display_precision defaults for all enrichment/alert/diagnostic sensor entities.

### Modified Capabilities

- `enrichment-sensors`: Sensor entities gain device_class and precision attributes, changing how HA presents their values to users.

## Impact

- **Code**: `custom_components/njord/sensor.py` — all sensor classes gain `device_class` and `suggested_display_precision` attributes; `ALERT_UNITS` dict switches from raw strings to HA constants
- **Tests**: `tests/test_services.py`, `tests/test_dynamic_entities.py` — unit assertions must use HA constants instead of raw strings
- **User-visible**: Imperial/custom unit system users will see converted values for the first time; all users get consistent decimal precision
- **Dependencies**: No new dependencies — `homeassistant.const` unit constants are already available

## 1. Data Model

- [x] 1.1 Add `trigger_value: float = 0.0`, `threshold: float = 0.0`, `peak_value: float | None = None`, `hours_until: int | None = None`, `duration_hours: int | None = None` to `AlertData` in `custom_components/njord/models.py`

## 2. gRPC Client

- [x] 2.1 Update `_to_alert()` in `custom_components/njord/grpc_client.py` to parse the 5 new fields from the Alert protobuf message
- [x] 2.2 Add tests in `tests/test_grpc_client.py` for `_to_alert` with all fields set, only required fields, and inactive alert

## 3. Binary Sensor Attributes

- [x] 3.1 Update `NjordAlertEntity.extra_state_attributes` in `custom_components/njord/binary_sensor.py` to include `trigger_value`, `threshold`, and conditionally `peak_value`, `hours_until`, `duration_hours`
- [x] 3.2 Add tests in `tests/test_binary_sensor.py` for attributes with full values, partial values, and no alert

## 4. Validation

- [x] 4.1 Run full test suite: `make test` — all tests pass

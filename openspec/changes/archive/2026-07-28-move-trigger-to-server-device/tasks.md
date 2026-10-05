## 1. Button Device Assignment

- [x] 1.1 In `custom_components/njord/button.py`, change `NjordTriggerPollButton.__init__` to use `identifiers={(DOMAIN, f"{entry.entry_id}_server")}` and remove the `name`/`manufacturer`/`entry_type` fields from `DeviceInfo` (the Server device already defines those via `sensor.py`).
- [x] 1.2 Update `tests/test_button.py` to assert the button's `device_info` uses the `_server` identifier and no longer sets a device name.

## 2. Delta Spec Sync

- [x] 2.1 Sync the modified `trigger-poll` delta spec to `openspec/specs/trigger-poll/spec.md`.

## 3. Validation

- [x] 3.1 Run `make test` and confirm all tests pass, especially `tests/test_button.py`.

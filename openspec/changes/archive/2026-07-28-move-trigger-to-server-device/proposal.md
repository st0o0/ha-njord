## Why

The trigger poll button currently creates its own HA device (`njord (10.0.20.110)`) because its `DeviceInfo` uses `entry_id` as identifier, while the diagnostic sensors use `{entry_id}_server`. This produces three devices in HA — one per-location, one "Server" with diagnostics, and a third orphan device just for the button. The button logically belongs to the server, not to a separate device.

## What Changes

- Align the trigger poll button's `DeviceInfo.identifiers` to match the existing Server device (`{entry_id}_server`), so it appears under the same "Server" device as the API budget and uptime sensors.
- Remove the redundant device name override from the button (let the Server device's name win).
- The old orphan device disappears automatically once no entities reference it.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `trigger-poll`: The button entity's device assignment changes from a standalone device to the shared Server device.

## Non-goals

- No changes to the trigger poll HA service (`njord.trigger_poll`).
- No changes to button behavior, attributes, or unique_id.
- No new gRPC endpoints required — uses existing `OpsService.TriggerPoll`.

## Impact

- `custom_components/njord/button.py`: `DeviceInfo` identifier change.
- `tests/test_button.py`: Update expected device info in tests.
- Existing HA installations: the orphan device will be cleaned up automatically by HA's device registry when no entities reference it.

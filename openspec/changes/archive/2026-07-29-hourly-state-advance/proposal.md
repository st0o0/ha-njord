## Why

Weather entities display stale "current" values because they always read `hourly[0]` regardless of the actual time. When a forecast was last pushed at 14:00 and it is now 18:00, the entity still shows the 14:00 temperature, humidity, and condition. HA confirms this by displaying "4 hours ago" on the entity card. The correct hourly entry for 18:00 already exists in the forecast data but is never selected.

## What Changes

- Weather entity properties (`native_temperature`, `condition`, `humidity`, etc.) select the hourly entry matching the current hour instead of blindly using `hourly[0]`.
- Weather entities register an hourly timer that triggers HA to re-read entity state at the top of each hour, so the displayed values advance even without new forecast data arriving.
- Hourly forecast lists filter out past entries (like Open-Meteo does), so `async_forecast_hourly` only returns future hours.

## Capabilities

### New Capabilities

- `hourly-state-advance`: Current-hour selection logic for weather entity state and hourly timer to trigger state re-evaluation.

### Modified Capabilities

- `weather-entities`: Current state properties change from `hourly[0]` to time-matched entry. Hourly forecast filters past entries.

## Impact

- `custom_components/njord/weather.py`: Both `NjordWeatherEntity` and `NjordConsensusWeatherEntity` gain a `_current_hourly()` method (or equivalent), `async_added_to_hass()` with timer registration, and updated `_async_forecast_hourly()` filtering.
- No proto changes, no coordinator changes, no new gRPC endpoints required.
- New HA import: `homeassistant.helpers.event.async_track_utc_time_change`.
- Tests need updating for time-dependent behavior (freezegun or similar).

## Non-goals

- Adding a `current` field to the njord gRPC API. The server delivers forecasts; selecting "now" is client responsibility.
- Changing the coordinator polling/streaming architecture.
- Modifying the Consensus entity's horizon-based approach (h0/h1/h2) beyond ensuring the hourly timer triggers a state refresh.

## gRPC Endpoints

All existing, no changes needed:

- `WeatherService.GetForecast` (unary, initial load)
- `WeatherService.StreamForecasts` (server stream, live updates)
- `WeatherService.GetEnrichments` / `StreamEnrichments` (consensus data)

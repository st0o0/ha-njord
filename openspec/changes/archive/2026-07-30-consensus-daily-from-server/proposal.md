# Consensus Daily from Server

## Problem

The `NjordConsensusWeatherEntity` currently self-aggregates daily forecasts from hourly consensus horizons (h0..hN). This produces correct results but duplicates logic that njord now handles server-side. Additionally, some per-model entities (GFS Seamless, UKMO Seamless, ECMWF IFS) lack `precipitation_sum` in their daily data, causing HA to fall back to showing min/max temperature instead of precipitation — an inconsistent UI experience.

## Solution

njord's `ConsensusUpdate` proto has been updated: the old `parameters` field (field 1) is renamed to `hourly_parameters`, and a new `daily_parameters` (field 2) is added. Daily parameters use day-granularity horizons (`d0`, `d1`, `d2`...) with keys matching Open-Meteo's daily API: `temperature_2m_max`, `temperature_2m_min`, `precipitation_sum`, `wind_speed_10m_max`, `weather_code`.

ha-njord adopts the new proto and uses server-provided daily consensus data directly, removing ~50 lines of self-aggregation logic.

## Scope

- Copy updated protos from njord and regenerate stubs
- Update `ConsensusData` model: `parameters` → `hourly_parameters` + `daily_parameters`
- Update gRPC client to parse both field lists
- Replace `NjordConsensusWeatherEntity._async_forecast_daily()` aggregation with direct daily_parameters loop
- Update tests

## Out of Scope

- Current state (native_temperature, condition) — still from hourly h0 + offset, unchanged
- Hourly forecast — rename only (parameters → hourly_parameters), logic unchanged
- Sunrise/sunset — not consensus-capable, stays in per-model DailyForecast only
- Per-model precipitation_sum gaps — that's a njord-side data issue

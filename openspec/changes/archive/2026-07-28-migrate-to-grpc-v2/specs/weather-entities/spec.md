## MODIFIED Requirements

### Requirement: First refresh inserts stub on failure
When `GetForecast` fails for a model during first refresh, the coordinator SHALL insert an empty `ForecastData` stub so the entity starts as available. The stub's `updated_at` SHALL be `datetime.min` with UTC timezone.

#### Scenario: Forecast fetch fails during first refresh
- **WHEN** `GetForecast(location, model)` raises an exception during `_async_update_data`
- **THEN** `ForecastData(location=location, model=model, updated_at=datetime.min.replace(tzinfo=UTC))` is inserted into the result

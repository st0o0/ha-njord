# Changelog

## [0.3.0](https://github.com/st0o0/ha-njord/compare/v0.1.0...v0.3.0) (2026-08-07)


### ⚠ BREAKING CHANGES

* add extra forecast parameters, alert trigger values, and convert alerts to sensors

### Features

* add API budget and uptime diagnostic sensors ([583ce4d](https://github.com/st0o0/ha-njord/commit/583ce4df3f9cd991e8ab9047d41ba9c1cc7f4470))
* add derived horizon sensors, event platform for alerts, and server-side consensus timestamps ([f9519ee](https://github.com/st0o0/ha-njord/commit/f9519eecea04e2ad17c5e3f47273f3e1777b81ab))
* add device info enrichment, diagnostics, options flow, stream health, and target sensors ([3e7cb2e](https://github.com/st0o0/ha-njord/commit/3e7cb2ef8428a1f11dfe4376ce9463ac8d27dac1))
* add device_class and suggested_display_precision to sensor entities ([b1ba0d5](https://github.com/st0o0/ha-njord/commit/b1ba0d5a255899b77504cecab8a5583f73736bb8))
* add event platform for weather alert transitions with location data ([37b1385](https://github.com/st0o0/ha-njord/commit/37b1385f1e15fbe5bedf5336effa099c6b8d2844))
* add extra forecast parameters, alert trigger values, and convert alerts to sensors ([7a11aae](https://github.com/st0o0/ha-njord/commit/7a11aae0b9d3d5f1dbaac8deda67b9d606a5c35a))
* add reconfigure flow, model info metadata, and model performance attributes ([68a7ac7](https://github.com/st0o0/ha-njord/commit/68a7ac7fa9a8a4b06757cfc7db7ba9734ce75ad5))
* add state_class to alert sensors for unit conversion ([ce365f2](https://github.com/st0o0/ha-njord/commit/ce365f210e97673f9f783753d9eec6cb63ffdd6f))
* advance consensus horizons, add status coordinator, split budget sensors ([5a094ad](https://github.com/st0o0/ha-njord/commit/5a094ad2104ad94c667607692e732dd1a3169e1b))
* advance weather entity state to current hour ([7f1e302](https://github.com/st0o0/ha-njord/commit/7f1e3023b8fc55fcd027f105c3459f7da1c2ed1e))
* **enrichment:** Enable conditional entity creation ([2bd7128](https://github.com/st0o0/ha-njord/commit/2bd7128406b34b851bb708a68ef7700ab574d96c))
* migrate from gRPC v1 to v2 API ([2d1cbfa](https://github.com/st0o0/ha-njord/commit/2d1cbfaeb08132b74aaee734bd16729c629e633e))
* poll server status every 30 minutes ([e260700](https://github.com/st0o0/ha-njord/commit/e26070084053b5a5072f6ababa4fd1f251e722e4))
* use server-provided consensus daily forecasts instead of self-aggregation ([270f880](https://github.com/st0o0/ha-njord/commit/270f8801a3039f42f921e68d045869efe4b749e6))


### Bug Fixes

* add current_horizon and consensus_age_hours attrs to prevent consensus entity staleness ([e3a1a37](https://github.com/st0o0/ha-njord/commit/e3a1a37ba588c577d2a4121081496bb0fe3c6bee))
* add event type translations so logbook shows proper labels instead of "Event detected" ([718dd75](https://github.com/st0o0/ha-njord/commit/718dd752e1aeb4bb2a67d656eefc92c332311336))
* add native_precipitation_unit to weather entities so HA displays precipitation values ([b46905c](https://github.com/st0o0/ha-njord/commit/b46905c69a203a4aa42ec04287ec85b9d5a88e23))
* assign trigger poll button to Server device ([7cf3abd](https://github.com/st0o0/ha-njord/commit/7cf3abdb956ab1c01746b8bf891290fc7ab63995))
* filter past days from model daily forecasts for consistent display ([3b51d7c](https://github.com/st0o0/ha-njord/commit/3b51d7cccc2996947dab94716dcef99e79d5ba9e))
* include location in target sensor name for disambiguation ([d34730f](https://github.com/st0o0/ha-njord/commit/d34730fa4de62c45995e9bcc99deb14965ddbe2e))
* prevent daily forecast loading spinner for short-range models ([35ac7df](https://github.com/st0o0/ha-njord/commit/35ac7dfc9b87b7ed882eeef84cae3d81ebe77cc5))
* regenerate proto stubs with protobuf 5.x for HA compatibility ([134572c](https://github.com/st0o0/ha-njord/commit/134572c3e1c960cf8f8e06d8f6ca4ebb44a91b0c))
* show daily forecasts even without temperature_max/min ([6ef03df](https://github.com/st0o0/ha-njord/commit/6ef03df4f47808e94f9e7a0a679e1ff75994ee1c))
* track stream connection state to prevent spurious disconnect/reconnect callbacks ([0ad27b2](https://github.com/st0o0/ha-njord/commit/0ad27b2cca79d00741ef9fc5c0ee4a52427f20e0))
* use SelectSelector for options flow multi-select to fix 500 error ([054ba76](https://github.com/st0o0/ha-njord/commit/054ba76de2ea64d36672e9b963577b69e8019730))


### Documentation

* update stream-health spec ([10b7cad](https://github.com/st0o0/ha-njord/commit/10b7cad7dd9013087ee15f2b21fe6386d85b2b12))


### Refactoring

* Adjust import order in integration files ([d3141ac](https://github.com/st0o0/ha-njord/commit/d3141ac6002625feb76735f7e08ec1b9f366ebbd))
* clean up device and entity naming ([ab1a368](https://github.com/st0o0/ha-njord/commit/ab1a368619dcc791e424ca7f7cc1c69aefd36aae))
* Improve code formatting and readability ([365daef](https://github.com/st0o0/ha-njord/commit/365daefec9559251372225660ecb3dde64b0dee0))
* Simplify formatting and remove unused code ([8c9f687](https://github.com/st0o0/ha-njord/commit/8c9f687c21261883da44275a1583e437898433ee))

## 0.1.0 (2026-07-18)


* reset manifest version to 0.0.0 ([e0627f2](https://github.com/st0o0/ha-njord/commit/e0627f2e95b5cf85e2e0be46ba3299038d8df435))


### Features

* add enrichment entities, consensus weather, icons, and translations ([5b9c3d2](https://github.com/st0o0/ha-njord/commit/5b9c3d26f8942de1417b6a69a301dabdcde7dd9a))
* Configure multiple weather locations and models ([5ca89b1](https://github.com/st0o0/ha-njord/commit/5ca89b1a5c418b10b7e707bb57b03f311ff14f80))
* Dynamic forecast features and missing index sensors ([98feba0](https://github.com/st0o0/ha-njord/commit/98feba0c49d01e50fbf20410acbc9ec3c470c31e))
* Rebuild consensus entity with hourly forecasts and daily aggregation ([834646c](https://github.com/st0o0/ha-njord/commit/834646ca418667749a8230eee2f3f2fc5735de01))
* Replace polling with gRPC streaming for real-time updates ([39a24db](https://github.com/st0o0/ha-njord/commit/39a24db6226563ddc30bba32d68027a55da29e84))


### Bug Fixes

* add brand assets to integration directory for HACS validation ([60c14f6](https://github.com/st0o0/ha-njord/commit/60c14f6e68df888301f3090a46c7ac81019a24c2))
* Consensus features at init, condition fallback, nearest WMO mapping ([211d094](https://github.com/st0o0/ha-njord/commit/211d094f1693d3d6860ff9ff7439d217253d09a6))
* Entity availability, default-disabled sensors, and forecast fixes ([eb2a8e9](https://github.com/st0o0/ha-njord/commit/eb2a8e9a68ded4c07d0f52d584933f4401bbcce5))
* Re-add WeatherEntity import for type hints ([fe4e633](https://github.com/st0o0/ha-njord/commit/fe4e63394fa37b0b7553b3e8d63c3d407bc21bbc))
* Use SingleCoordinatorWeatherEntity for proper forecast subscriptions ([ae9ab03](https://github.com/st0o0/ha-njord/commit/ae9ab033cd0025fe416f5e31a2311ac6a3130a7e))


### Documentation

* add README, brand assets, and dev docker-compose ([1788b61](https://github.com/st0o0/ha-njord/commit/1788b61bf40aa61af660338f9f8332a1368c3753))
* **readme:** Add HACS install badge ([e9df9b7](https://github.com/st0o0/ha-njord/commit/e9df9b75c34c0727a630beedff52dce56d941c62))

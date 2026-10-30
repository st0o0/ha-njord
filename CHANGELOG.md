# Changelog

## [0.5.0](https://github.com/st0o0/ha-njord/compare/v0.1.0...v0.5.0) (2026-10-30)


### ⚠ BREAKING CHANGES

* remove Satellite domain references
* rename Weather domain to Forecast, sync proto from njord
* adapt to njord ForecastClient/EnsembleClient split
* adopt typed enrichment events from njord
* rewrite config flow, setup and strings for alert enrichment toggles
* rewrite coordinator and platforms around domain data and alerts
* rewrite grpc client for domain data and alert enrichments
* sync protos and rewrite models for new njord API
* type closed value sets as enums and consume the njord wire enums
* sync protos with njord, remove the history enrichment and surface partial status flags
* add extra forecast parameters, alert trigger values, and convert alerts to sensors

### style

* apply ruff format to 5 files ([1579ab1](https://github.com/st0o0/ha-njord/commit/1579ab18714b9e9a549f2fae106c356da3c7894e))


### Features

* add 5 new alert types (ice, wind_chill, visibility, tropical_night, humidity) ([1f9539a](https://github.com/st0o0/ha-njord/commit/1f9539ad056353b4607bfd6c9bd31a86f7c97d3e))
* add alert types for ice, wind chill, visibility, humidity ([7bf1ce9](https://github.com/st0o0/ha-njord/commit/7bf1ce96efcda98a82166dec92d551179cd9451c))
* add API budget and uptime diagnostic sensors ([583ce4d](https://github.com/st0o0/ha-njord/commit/583ce4df3f9cd991e8ab9047d41ba9c1cc7f4470))
* add calendar entity for activity windows and score window attributes ([8905276](https://github.com/st0o0/ha-njord/commit/8905276fede547e61f9fe44d3af0983d9232ea96))
* add data lifecycle and feature transition event entities ([9fd58e9](https://github.com/st0o0/ha-njord/commit/9fd58e9151b1457a6b388443348ef6e145d27527))
* add derived horizon sensors, event platform for alerts, and server-side consensus timestamps ([f9519ee](https://github.com/st0o0/ha-njord/commit/f9519eecea04e2ad17c5e3f47273f3e1777b81ab))
* add device info enrichment, diagnostics, options flow, stream health, and target sensors ([3e7cb2e](https://github.com/st0o0/ha-njord/commit/3e7cb2ef8428a1f11dfe4376ce9463ac8d27dac1))
* add device_class and suggested_display_precision to sensor entities ([b1ba0d5](https://github.com/st0o0/ha-njord/commit/b1ba0d5a255899b77504cecab8a5583f73736bb8))
* add event platform for weather alert transitions with location data ([37b1385](https://github.com/st0o0/ha-njord/commit/37b1385f1e15fbe5bedf5336effa099c6b8d2844))
* add extra forecast parameters, alert trigger values, and convert alerts to sensors ([7a11aae](https://github.com/st0o0/ha-njord/commit/7a11aae0b9d3d5f1dbaac8deda67b9d606a5c35a))
* add lifestyle sensor entities for ventilation, laundry, commute and more ([effd2f2](https://github.com/st0o0/ha-njord/commit/effd2f220e6a100b31a1e999885260e116c94906))
* add none state to inversion_detection enum sensor ([0cca7e3](https://github.com/st0o0/ha-njord/commit/0cca7e336f088cab160313b652a556db41bc1711))
* add reconfigure flow, model info metadata, and model performance attributes ([68a7ac7](https://github.com/st0o0/ha-njord/commit/68a7ac7fa9a8a4b06757cfc7db7ba9734ce75ad5))
* add sensor push integration with options flow and HA service ([e4791c5](https://github.com/st0o0/ha-njord/commit/e4791c592e0084cbf3ad18db42e8b271d21b91a7))
* add SensorService gRPC client for pushing sensor readings ([8ed2f62](https://github.com/st0o0/ha-njord/commit/8ed2f628c6b40eef158ac0c01171dc153d066b2f))
* add state_class to alert sensors for unit conversion ([ce365f2](https://github.com/st0o0/ha-njord/commit/ce365f210e97673f9f783753d9eec6cb63ffdd6f))
* adopt multi-model weather from njord ([c9e8a9c](https://github.com/st0o0/ha-njord/commit/c9e8a9c4e6673f8e0ca497218aeae64020e6cf2e))
* adopt typed enrichment events from njord ([5208a5a](https://github.com/st0o0/ha-njord/commit/5208a5afeb4868c19153bf45a5d2ef0d563ae796))
* advance consensus horizons, add status coordinator, split budget sensors ([5a094ad](https://github.com/st0o0/ha-njord/commit/5a094ad2104ad94c667607692e732dd1a3169e1b))
* advance weather entity state to current hour ([7f1e302](https://github.com/st0o0/ha-njord/commit/7f1e3023b8fc55fcd027f105c3459f7da1c2ed1e))
* **enrichment:** Enable conditional entity creation ([2bd7128](https://github.com/st0o0/ha-njord/commit/2bd7128406b34b851bb708a68ef7700ab574d96c))
* Implement E2E testing skill for njord and HA ([36e30a8](https://github.com/st0o0/ha-njord/commit/36e30a8f1c0bfc790b97d37892442c6142388e5c))
* migrate from gRPC v1 to v2 API ([2d1cbfa](https://github.com/st0o0/ha-njord/commit/2d1cbfaeb08132b74aaee734bd16729c629e633e))
* migrate IndexUpdate to daily slices with DayScoreSet structure ([0513a74](https://github.com/st0o0/ha-njord/commit/0513a74e3732dc38340e4fde35680a71e6a7389e))
* parse seasonal domain data ([f3861f6](https://github.com/st0o0/ha-njord/commit/f3861f650ffb36adb8e8179d7b5dd43842813346))
* poll server status every 30 minutes ([e260700](https://github.com/st0o0/ha-njord/commit/e26070084053b5a5072f6ababa4fd1f251e722e4))
* regenerate proto stubs and add entity descriptions for 13 new features ([3454e03](https://github.com/st0o0/ha-njord/commit/3454e0359e09965e658dc50f462dd8cb20443de6))
* sync protos with njord, remove the history enrichment and surface partial status flags ([e73f16a](https://github.com/st0o0/ha-njord/commit/e73f16a7678321a3a7749ae2ed14b3fbe22cc3e8))
* type closed value sets as enums and consume the njord wire enums ([15ff1d0](https://github.com/st0o0/ha-njord/commit/15ff1d097f97ce765ab1571f81581e71c4fd5135))
* use server-provided consensus daily forecasts instead of self-aggregation ([270f880](https://github.com/st0o0/ha-njord/commit/270f8801a3039f42f921e68d045869efe4b749e6))


### Bug Fixes

* add current_horizon and consensus_age_hours attrs to prevent consensus entity staleness ([e3a1a37](https://github.com/st0o0/ha-njord/commit/e3a1a37ba588c577d2a4121081496bb0fe3c6bee))
* add event type translations so logbook shows proper labels instead of "Event detected" ([718dd75](https://github.com/st0o0/ha-njord/commit/718dd752e1aeb4bb2a67d656eefc92c332311336))
* add native_precipitation_unit to weather entities so HA displays precipitation values ([b46905c](https://github.com/st0o0/ha-njord/commit/b46905c69a203a4aa42ec04287ec85b9d5a88e23))
* assign trigger poll button to Server device ([7cf3abd](https://github.com/st0o0/ha-njord/commit/7cf3abdb956ab1c01746b8bf891290fc7ab63995))
* **ci:** stop committing requirements.txt, generate it on the fly for Trivy ([722c71e](https://github.com/st0o0/ha-njord/commit/722c71e31e5d18ea8f5bd28e61570b22ae5e6570))
* correct alert units for storm (km/h→m/s) and thunderstorm (J/kg→m/s) ([7fac029](https://github.com/st0o0/ha-njord/commit/7fac029b509ed608df962b8e39fc2497259f4887))
* filter past days from model daily forecasts for consistent display ([3b51d7c](https://github.com/st0o0/ha-njord/commit/3b51d7cccc2996947dab94716dcef99e79d5ba9e))
* include location in target sensor name for disambiguation ([d34730f](https://github.com/st0o0/ha-njord/commit/d34730fa4de62c45995e9bcc99deb14965ddbe2e))
* prevent daily forecast loading spinner for short-range models ([35ac7df](https://github.com/st0o0/ha-njord/commit/35ac7dfc9b87b7ed882eeef84cae3d81ebe77cc5))
* regenerate proto stubs with protobuf 5.x for HA compatibility ([134572c](https://github.com/st0o0/ha-njord/commit/134572c3e1c960cf8f8e06d8f6ca4ebb44a91b0c))
* remove device_class filter from sensor push entity selectors ([fd35a6d](https://github.com/st0o0/ha-njord/commit/fd35a6d5dac70cfbed9eb9beb442ed7163c8bfb7))
* **renovate:** group pip_requirements and homeassistant managers with pep621 for python deps ([8d3caec](https://github.com/st0o0/ha-njord/commit/8d3caecae9b6efaae8585f9cc00451599878c62b))
* **renovate:** split python deps into major and minor+patch groups to prevent duplicate PRs ([81385c6](https://github.com/st0o0/ha-njord/commit/81385c62c084a8354eaa9d348bc3479373fdc69d))
* **sensor:** enable alert sensors by default ([575684d](https://github.com/st0o0/ha-njord/commit/575684dd019905a9872ce4bbd179d814b8b807df))
* show daily forecasts even without temperature_max/min ([6ef03df](https://github.com/st0o0/ha-njord/commit/6ef03df4f47808e94f9e7a0a679e1ff75994ee1c))
* sync weather.proto and admin.proto field numbers with njord v2 ([2e17465](https://github.com/st0o0/ha-njord/commit/2e17465f09a68744756f366826724a3dfc2288eb))
* track stream connection state to prevent spurious disconnect/reconnect callbacks ([0ad27b2](https://github.com/st0o0/ha-njord/commit/0ad27b2cca79d00741ef9fc5c0ee4a52427f20e0))
* update unique id on reconfigure ([83f7a85](https://github.com/st0o0/ha-njord/commit/83f7a85600373bb7faf9fe3da4e6e07225a217e9))
* use literal discharge unit and format ([9d11913](https://github.com/st0o0/ha-njord/commit/9d11913c075868846b269439dbe360f4a616f142))
* use nearest-horizon lookup for derived sensors ([c19828e](https://github.com/st0o0/ha-njord/commit/c19828ee660ccc6bf13ed1d98af51512c5450d83))
* use SelectSelector for options flow multi-select to fix 500 error ([054ba76](https://github.com/st0o0/ha-njord/commit/054ba76de2ea64d36672e9b963577b69e8019730))
* widen protobuf constraint to &lt;8.0 for HA 2025.x compatibility ([787e985](https://github.com/st0o0/ha-njord/commit/787e985129d26dd7fce521b9fd2cfaa37209bbac))


### Documentation

* add Open-Meteo CC BY 4.0 attribution to README ([a48b7a8](https://github.com/st0o0/ha-njord/commit/a48b7a80bfca66e1b58188d1c20212ed41ab41c1))
* **openspec:** add missing Purpose and Requirements headers so all specs validate ([252b51a](https://github.com/st0o0/ha-njord/commit/252b51a5f8deca4fec8d422baa9f5635a44de873))
* **openspec:** archive typed-enums ([919b24a](https://github.com/st0o0/ha-njord/commit/919b24a8c03c614a9d5b54ee13907fe4b0bf6088))
* remove em dashes and simplify wording ([c532a6e](https://github.com/st0o0/ha-njord/commit/c532a6e0e06dd95bfee6d296b260e5d9fcfe4b2b))
* rewrite README for domain-based architecture ([48bbe40](https://github.com/st0o0/ha-njord/commit/48bbe40e3c742a3e9c4eab5ac105536a34c6c445))
* slim README and link to njord docs for entity reference ([ea212e3](https://github.com/st0o0/ha-njord/commit/ea212e363eb06725084c2e22f9cfcd484f48de3d))
* update architecture notes for domain data API ([fc1aebc](https://github.com/st0o0/ha-njord/commit/fc1aebce4a4e75c2ab3c468818320109bf066752))
* update stream-health spec ([10b7cad](https://github.com/st0o0/ha-njord/commit/10b7cad7dd9013087ee15f2b21fe6386d85b2b12))


### Refactoring

* adapt to njord ForecastClient/EnsembleClient split ([692e3dd](https://github.com/st0o0/ha-njord/commit/692e3dd19948d26f4ac0ae4a16e1fc139cd00380))
* Adjust import order in integration files ([d3141ac](https://github.com/st0o0/ha-njord/commit/d3141ac6002625feb76735f7e08ec1b9f366ebbd))
* clean up device and entity naming ([ab1a368](https://github.com/st0o0/ha-njord/commit/ab1a368619dcc791e424ca7f7cc1c69aefd36aae))
* Improve code formatting and readability ([365daef](https://github.com/st0o0/ha-njord/commit/365daefec9559251372225660ecb3dde64b0dee0))
* migrate all entities to HA translation_key pattern ([581a82c](https://github.com/st0o0/ha-njord/commit/581a82cefb2225defd2078006cdee170a87f97c9))
* remove Energy enrichment feature ([d95feb5](https://github.com/st0o0/ha-njord/commit/d95feb5b9a08336a1cfbd3b2112d220f24aa7408))
* remove Satellite domain references ([5e6177c](https://github.com/st0o0/ha-njord/commit/5e6177c7155fa716d756ddbb9c7212b359506be6))
* rename Weather domain to Forecast, sync proto from njord ([78b40be](https://github.com/st0o0/ha-njord/commit/78b40bee863a96d9e9360c42c21e3cb86f74a883))
* rewrite config flow, setup and strings for alert enrichment toggles ([787ce14](https://github.com/st0o0/ha-njord/commit/787ce1483abd0e67b5aaaf98cf2caaa2a3429a46))
* rewrite coordinator and platforms around domain data and alerts ([953a0cf](https://github.com/st0o0/ha-njord/commit/953a0cf6701681dea2862b6edcd747f1e8df4b23))
* rewrite grpc client for domain data and alert enrichments ([b014929](https://github.com/st0o0/ha-njord/commit/b0149298289768a29919644c6b0c3d2a35932911))
* Simplify formatting and remove unused code ([8c9f687](https://github.com/st0o0/ha-njord/commit/8c9f687c21261883da44275a1583e437898433ee))
* sync protos and rewrite models for new njord API ([f9fcbf1](https://github.com/st0o0/ha-njord/commit/f9fcbf19ba7a8e1be88a1473711f0b446b54721c))

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

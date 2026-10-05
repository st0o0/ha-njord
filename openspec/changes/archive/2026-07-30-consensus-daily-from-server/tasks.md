# Tasks: Consensus Daily from Server

- [x] 1. Copy protos from `D:\GIT\njord\protos\njord\v2\` and regenerate stubs with `make proto`
- [x] 2. Update `models.py`: `ConsensusData.parameters` → `hourly_parameters` + `daily_parameters`
- [x] 3. Update `grpc_client.py`: `_to_consensus_data()` parses `pb.hourly_parameters` and `pb.daily_parameters`
- [x] 4. Update `weather.py`: rename all `consensus.parameters` → `consensus.hourly_parameters` in hourly methods
- [x] 5. Update `weather.py`: replace `_async_forecast_daily()` aggregation with direct daily_parameters loop
- [x] 6. Update tests: rename fixtures, add daily consensus test, verify hourly still works

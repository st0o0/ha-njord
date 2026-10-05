## MODIFIED Requirements

### Requirement: Stream reconnect wrapper tracks connection state
The `_stream_with_reconnect` method SHALL track an internal `connected` state and only invoke `on_reconnect` / `on_disconnect` callbacks on **actual state transitions**. A normal stream end (iterator exhaustion without error) followed by a successful reconnect SHALL NOT toggle the connection state. Only gRPC errors SHALL trigger a disconnect transition.

#### Scenario: First connect fires on_reconnect
- **WHEN** `_stream_with_reconnect` starts and the first gRPC call succeeds
- **THEN** `on_reconnect` is called once and `stream_states[name]` becomes `True`

#### Scenario: Normal stream end does not fire on_disconnect
- **WHEN** a stream iterator exhausts normally (server closed the stream after sending data) and the reconnect succeeds
- **THEN** neither `on_disconnect` nor `on_reconnect` is called — `stream_states[name]` remains `True`

#### Scenario: gRPC error fires on_disconnect
- **WHEN** a stream raises `grpc.aio.AioRpcError` (not `CANCELLED`)
- **THEN** `on_disconnect` is called and `stream_states[name]` becomes `False`

#### Scenario: Reconnect after error fires on_reconnect
- **WHEN** a stream was disconnected due to a gRPC error and the next call succeeds
- **THEN** `on_reconnect` is called and `stream_states[name]` becomes `True`

#### Scenario: Repeated errors do not spam on_disconnect
- **WHEN** a stream fails with a gRPC error multiple times in a row (backoff cycle)
- **THEN** `on_disconnect` is called only on the first error — subsequent errors while already disconnected do not call `on_disconnect` again

#### Scenario: Cancelled stream does not fire callbacks
- **WHEN** a stream raises `grpc.aio.AioRpcError` with `StatusCode.CANCELLED`
- **THEN** the method returns without calling `on_disconnect`

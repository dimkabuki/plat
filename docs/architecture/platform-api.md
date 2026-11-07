# Platform API

## Purpose and version boundaries

The Platform API is the stable, Host-independent boundary between a module and its execution Host. A module uses the same logical protocol whether hosted by Android WebView or a browser/PWA.

Three versions have distinct meanings:

- **Manifest schema version** describes the shape of `module.json`; v1 is `schemaVersion: 1`.
- **Module version** describes one module's release and follows SemVer 2.0.0.
- **Platform API version** describes the API surface exposed by a Host; the initial contract is `1.0.0`.

The wire `protocolVersion` is an integer (`1` for this envelope format). It versions message framing and is independent of the Platform API version. The Android app version is also independent. A Host update that preserves API compatibility does not require a module release.

## Transport-neutral envelope v1

The canonical envelope schema is `contracts/platform-api-v1.schema.json`. Messages are UTF-8 JSON objects. The transport carries complete objects and does not reinterpret their fields. The Host validates the envelope and method parameters before dispatch.

Request:

```json
{
  "protocolVersion": 1,
  "type": "request",
  "id": "12345678-1234-4234-9234-123456789abc",
  "method": "storage.kv.get",
  "params": { "key": "counter" }
}
```

A response uses the same `id` and has exactly one of `result` or `error`:

```json
{
  "protocolVersion": 1,
  "type": "response",
  "id": "12345678-1234-4234-9234-123456789abc",
  "result": { "value": 4 }
}
```

An error has a stable machine-readable `code`, bounded human-readable `message`, and `retryable` flag. Optional `details` is diagnostic data, not a second error protocol. v1 error codes are `INVALID_ENVELOPE`, `UNSUPPORTED_PROTOCOL`, `METHOD_NOT_FOUND`, `INVALID_PARAMS`, `CAPABILITY_NOT_DECLARED`, `CAPABILITY_UNAVAILABLE`, `PERMISSION_DENIED`, `NOT_READY`, `NOT_FOUND`, `CONFLICT`, `QUOTA_EXCEEDED`, `RATE_LIMITED`, `CANCELLED`, and `INTERNAL_ERROR`.

An event is unsolicited and does not have a request correlation ID:

```json
{
  "protocolVersion": 1,
  "type": "event",
  "eventId": "12345678-1234-4234-9234-123456789abc",
  "event": "runtime.lifecycle.changed",
  "payload": { "state": "running" }
}
```

Request IDs and event IDs are UUIDs. A response ID must equal its request ID. There is no ordering guarantee between independent requests or events. A transport may deliver responses out of order; a client correlates them by ID. The logical protocol does not assume a particular transport, threading model, or callback mechanism.

## Bootstrap and compatibility negotiation

Before using capability methods, a module sends `platform.negotiate`. Its parameters include module ID and manifest schema version, the module's declared Platform API compatibility range, and required/optional capability names. The Host responds with its Platform API version, `compatible`, `grantedCapabilities`, `missingRequiredCapabilities`, and `unavailableOptionalCapabilities`.

Compatibility uses the manifest range rules:

- Host API version must have the same major version as `minVersion` and be greater than or equal to it.
- If `maxVersionExclusive` exists, Host API version must be lower than it.
- `maxVersionExclusive` must exceed `minVersion` and use the same major version.
- A missing or unapproved required capability makes negotiation incompatible; the Host must not activate the module.
- An unavailable optional capability does not block activation. Calls requiring it remain denied and the module must degrade gracefully.

The Host does not trust module-supplied declarations as authorization. The verified installed manifest is authoritative and bound to the active module session.

## Capability registry v1

`contracts/platform-capabilities-v1.json` is the canonical method/capability registry for API `1.0.0`. It maps every callable method to exactly one required capability and defines method parameter schemas. Initial capabilities:

| Capability | Methods | Authorization policy |
|---|---|---|
| `storage.kv` | `storage.kv.get`, `set`, `delete`, `keys` | Automatic; storage is scoped to the calling module. |
| `ui.navigation` | `ui.navigation.setTitle`, `requestClose` | Automatic; Host retains control of outer navigation. |
| `notifications.local` | `notifications.local.schedule`, `cancel` | Explicit user consent and Host OS permission. |
| `device.haptics` | `device.haptics.vibrate` | Explicit user consent; Host enforces duration/rate limits. |

`messaging` remains reserved and is not in the v1 registry. Direct module-to-module communication remains out of scope.

The registry is an allowlist, not a list of capabilities automatically exposed to every module. A module may call a method only when all conditions hold:

1. The method exists in the registry.
2. The verified manifest declares its required capability as required or optional.
3. The current Host advertises the capability.
4. Any required user consent is granted for the calling module.
5. The request origin/session is the active module session bound to the verified manifest.

The Host must enforce these checks on every call, not only during negotiation. Revoking consent removes the capability grant without changing the manifest. Unknown methods and capabilities are denied by default.

## Initial method contracts

Method parameters are JSON objects validated against the schemas in the capability registry. The initial storage API uses string keys and JSON values. Storage is isolated by stable module ID; a module cannot name another module's namespace. Notification IDs are module-scoped. Notification scheduling and haptic duration are bounded by Host policy. `ui.navigation.requestClose` is a request to the Host, not an unconditional command; the Host may decline it.

The exact quotas, storage byte limits, notification scheduling limits, and haptic rate limits are Host policy and must be surfaced through stable error codes. They must not be silently relaxed by an implementation.

## Timeouts and cancellation

A Host must bound resource use for every call. The transport adapter owns a request deadline and maps transport cancellation to a cancellation signal for the Host operation. A timed-out or cancelled request must not later deliver a second terminal response. A method with externally visible side effects must define whether cancellation is best-effort or whether the operation is committed; the caller must not infer rollback from a timeout. v1 does not put timeout or transport cancellation fields in the portable envelope.

## Transport adapters

Android WebView and Browser/PWA adapters are responsible for establishing the module session, binding the verified module identity, validating origin/sender, transferring complete JSON messages, enforcing message-size limits, and mapping close/navigation events. The logical envelopes, method names, schemas, capability negotiation, and authorization rules remain unchanged across transports.

No unrestricted native JavaScript interface is part of this contract. Transport security, WebView origin strategy, and concrete Android message-channel selection remain in the Host security design.

## Status and non-goals

The schemas, capability registry, validation code, and tests are contract tooling, not a running Host implementation or published SDK. This v1 surface is intentionally small. Add new methods only with a capability mapping, parameter schema, authorization policy, and tests. Do not expose arbitrary filesystem, process, intent, network, or cross-module access.

# Host Adapter Contract v1

## Purpose

A Host Adapter contains platform-specific execution and transport details behind the Host-independent Module Contract and Platform API. Android WebView and Browser/PWA must present the same logical module session semantics even though their runtimes and message transports differ.

The v1 Host descriptor schema is `contracts/host-adapter-v1.schema.json`. Example Android and Browser/PWA descriptors are under `contracts/examples/host/`. The shared required conformance scenarios are defined in `contracts/host-adapter-conformance-v1.json`.

## Host descriptor

A Host reports:

- a stable `hostId` identifying its implementation family;
- `hostVersion`, independent of Platform API version;
- `platformApiVersion`, which must satisfy each module's manifest compatibility range;
- runtime kind (`android-webview` or `browser`) and selected transport (`message-port.v1` or `web-message.v1`);
- the set of capabilities the Host is able to provide;
- enforced transport/runtime limits for message size, request timeout, and concurrent requests.

The descriptor is informational input to negotiation, not proof that a capability has been granted. User consent and the verified module manifest are still evaluated separately for each module session. A Host may advertise only capabilities in the canonical v1 registry.

## Logical adapter surface

A conforming adapter exposes the following language-neutral operations:

| Operation | Contract |
|---|---|
| `describeHost()` | Returns a schema-valid Host descriptor. The descriptor is stable for the lifetime of the Host process unless a capability is explicitly withdrawn. |
| `openModuleSession(context)` | Opens a session only for a verified, installed module version after API compatibility and required capability negotiation succeed. |
| `session.request(request)` | Accepts a Platform API v1 request envelope, enforces message-size, concurrency, method, capability, and consent checks, and returns exactly one response with the matching request ID. |
| `session.subscribe(listener)` | Subscribes to Host event envelopes. It returns an idempotent unsubscribe operation. |
| `session.close(reason)` | Closes the module session and transport. It is idempotent and prevents further requests or events for that session. |

The contract does not require a particular programming language, callback mechanism, or thread model. A concrete adapter can expose idiomatic APIs but must preserve these observable semantics.

## Session context and identity binding

The Host creates and owns a session context containing at least:

- stable module ID and exact active module version;
- the verified manifest/schema version and digest;
- granted capability set after compatibility and consent evaluation;
- a Host-generated session identifier;
- the runtime instance and transport endpoint associated with that module.

Module identity and permissions are not accepted from request parameters. Every request is attributed to the session that delivered it. A module cannot select another module's storage namespace or impersonate another session by changing JSON fields.

A session can access only the active committed version for its module ID. Update activation, disablement, and removal require the current runtime session to be stopped/closed first. After session close, pending callbacks and late transport messages are discarded.

## Request and event behavior

- All request/response/event objects conform to Platform API v1 schemas.
- A request ID is unique among outstanding requests in one session. A response echoes that ID exactly once.
- Requests may complete out of order. The transport must not rely on message order for correlation.
- The adapter enforces descriptor message-size and concurrency limits before dispatch.
- Each error uses a stable Platform API error code and one terminal response.
- Events carry unique event IDs. Event subscriptions are session-scoped and do not leak across modules.
- Timeouts are enforced by the adapter. A late result after timeout is discarded and cannot produce a second terminal response.
- Closing a session stops event delivery, rejects new requests, and safely drains or rejects pending requests according to their method semantics.

## Capability ownership

The Host owns capability availability and user-consent state. The adapter maps each Host's underlying platform features to the canonical capability registry. It must not advertise a capability when the underlying feature is missing or blocked by runtime permissions.

The API dispatcher enforces, on every call, that:
1. The method exists in the registry.
2. The verified manifest declares the method's required capability.
3. The descriptor and current Host state provide the capability.
4. Any required user consent is still granted.
5. The caller is the active session bound to the corresponding verified module.

Capability revocation takes effect for subsequent calls. A session must not cache an authorization decision beyond the Host's current permission state.

## Transport mapping

The Platform API envelopes remain unchanged across transports. The adapter is responsible for mapping them to/from the selected transport:

- Android WebView may use an origin-restricted WebMessageListener or MessagePort bridge after the WebView origin and asset-loading design is reviewed.
- Browser/PWA may use MessageChannel or another same-origin, explicitly bound message-port transport.

Transport-specific sender/origin checks, navigation policy, message size enforcement, and endpoint teardown are mandatory. A generic `postMessage` receiver that accepts messages from arbitrary origins or an unrestricted native JavaScript bridge is not conformant.

## Conformance suite

`contracts/host-adapter-conformance-v1.json` defines 14 required scenarios. The same scenario IDs and expectations apply to Android and Browser/PWA adapters. At present, CI validates the descriptor examples and completeness of the scenario matrix; there are no executable Android or Browser/PWA adapters to run the scenarios against.

When an adapter is implemented, its own tests must execute every scenario against the real adapter/transport. Passing schema validation or testing only a fake adapter does not establish runtime conformance.

## Non-goals

This contract does not prescribe Android WebView settings, browser iframe/sandbox selection, concrete persistence technology, module UI rendering, SDK ergonomics, or update-source implementation. Those remain separate architecture and implementation increments.

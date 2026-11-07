# Module Runtime

## Package boundary

A module is delivered as a ZIP archive whose root contains \`module.json\` and the web assets referenced by that manifest. Archives must not have an enclosing top-level directory.

\`\`\`text
<module-id>-<module-version>.zip
├── module.json
├── index.html
├── assets/
│   ├── app.js
│   └── app.css
└── wasm/
    └── engine.wasm
\`\`\`

The release asset name is \`<module-id>-<module-version>.zip\`, for example \`dev.plat.example.counter-1.0.0.zip\`. The archive filename is a distribution convention, not module identity; the Host trusts the validated manifest identity.

The canonical JSON Schema is \`contracts/module-manifest.schema.json\` (JSON Schema 2020-12). A valid example package source is in \`contracts/examples/counter/\`. The CI package validator uses the pinned \`jsonschema\` development dependency and enforces both the schema and the archive-level rules below.

### Manifest v1

Required fields:

| Field | Meaning |
|---|---|
| \`schemaVersion\` | Integer \`1\`; version of the manifest format, independent from module and Platform API versions. |
| \`id\` | Stable reverse-domain identifier, lowercase segments, e.g. \`dev.plat.example.counter\`. Identity must not change between releases. |
| \`name\` | Display name, 1-80 characters. |
| \`version\` | Module release version using Semantic Versioning 2.0.0. |
| \`entry\` | Case-sensitive POSIX-relative path to the entry HTML file inside the ZIP. |
| \`platformApi.minVersion\` | Minimum compatible stable Platform API \`major.minor.patch\`. |
| \`capabilities.required\` | Capabilities that must be present before activation. |
| \`capabilities.optional\` | Capabilities used only when the Host advertises them. |

Optional fields are \`description\` (up to 280 characters) and \`platformApi.maxVersionExclusive\` (exclusive upper bound on compatible API versions). Unknown fields are rejected in v1; extensions require a new schema revision rather than silently changing semantics.

Capability names use a namespace-qualified identifier such as \`storage.kv\`. The concrete capability registry and API methods are specified separately. A capability must not be requested in both \`required\` and \`optional\`.

### Compatibility semantics

- Manifest \`schemaVersion\` must be exactly \`1\`; unknown schema versions are incompatible.
- The Host API version must have the same major version as \`platformApi.minVersion\` and compare greater than or equal to that minimum.
- If \`maxVersionExclusive\` is present, the Host API version must be lower than it. The upper bound must use the same major version and be greater than the minimum.
- A missing required capability makes the module incompatible before activation. Missing optional capabilities do not block launch; the module must degrade gracefully.
- Module \`version\` is independent from both manifest schema and Platform API version. Releases of one module retain the same \`id\` and advance \`version\` according to SemVer.

### Archive validation

The package validator rejects:

- missing root \`module.json\`, malformed/duplicate-key JSON, unsupported or unknown manifest fields, and invalid manifest values;
- missing entry file or a manifest entry that is not a safe package-relative path;
- absolute paths, drive-prefixed paths, backslashes, NULs, \`.\` or \`..\` segments, non-NFC names, paths over 240 UTF-8 bytes, and case-insensitive path collisions;
- symlinks and special filesystem entries, encrypted entries, unsupported ZIP compression methods, and file/directory path conflicts;
- archives over 50 MiB compressed, more than 1,000 entries, a file over 50 MiB uncompressed, total uncompressed content over 100 MiB, or an entry compression ratio over 100:1.

Only ZIP_STORED and ZIP_DEFLATED are supported. The validator reads every file entry to verify its size and CRC before accepting the package. The active installed module must never be overwritten as part of package validation; installation staging and activation are separate lifecycle operations.

These limits are v1 policy and can be raised only through a reviewed contract revision. Validation does not prove publisher identity, module-code safety, or permission approval. Do not treat a valid archive as trusted executable content.

## Lifecycle contract v1

The lifecycle separates three independent dimensions. Do not represent them as one overloaded status enum:

- **Catalogue state** is derived from discovery metadata: \`available\` or \`incompatible\`. It is not evidence that a package is installed or trusted.
- **Installation state** is durable: \`absent\`, \`installed\`, or \`disabled\`. The durable record format is \`contracts/module-record.schema.json\`; each operation has a unique ID for recovery and staging cleanup.
- **Runtime state** is transient: \`stopped\` or \`running\`. A process/session is never considered installed merely because it is running, and runtime state is not persisted across process death.

An installation record stores the stable module ID, active version, optional previous known-good version, disabled flag, an optional in-flight operation, and the last failure. Active package versions are immutable once verified. A module has at most one lifecycle operation at a time. The reference model round-trips this record through JSON before restart reconciliation.

### Operation transitions

Install and update use the same staged transaction:

| Current phase | Event | Next phase | Required effect |
|---|---|---|---|
| none | begin install/update | \`downloading\` | Record a unique operation ID plus target and source versions; active version remains unchanged. |
| \`downloading\` | download complete | \`verifying\` | Close the downloaded file; do not expose it to the runtime. |
| \`verifying\` | package valid | \`staging\` | Verify manifest, compatibility, capabilities, archive structure, and all entry CRCs. |
| \`staging\` | immutable version staged | \`activating\` | Extract into a transaction-specific staging directory; ensure durable files before activation. The runtime must be stopped before entering activation. |
| \`activating\` | atomic commit succeeds | none | Atomically switch the active-version pointer/record; prior active version becomes rollback candidate. |

The active version is never modified during download, verification, or staging. The storage adapter must make the active-version pointer update atomic. The package under the new version path is immutable after verification. The Host may launch only the active version referenced by the committed record.

- An initial install requires no active version.
- An update requires an installed module and a strictly newer SemVer target. An update may run while the module is disabled; it must preserve the disabled flag.
- A rollback is an explicit activation of the retained previous known-good version. It uses the same atomic activation commit and swaps the current version into the previous slot.
- Cancellation is accepted only during \`downloading\`, \`verifying\`, or \`staging\`. It discards transaction-owned temporary files and leaves the active and previous versions unchanged. Once \`activating\` starts, cancellation is rejected; the Host must resolve the atomic transaction instead.
- Failure at any pre-commit phase clears the operation, records a stable error code/failed phase, removes only transaction-owned temporary files, and preserves the active and previous versions. Retry starts a new transaction from download; unverified staged bytes are never trusted across retry.

### Activation recovery

The operation journal is durable before activation begins. On restart during \`activating\`, compare the storage adapter's active-version pointer with the operation's recorded source and target:

- Pointer equals target: finalize the durable record and preserve source as previous version.
- Pointer equals source: keep source active, mark the operation interrupted, and allow a clean retry.
- Pointer equals neither: fail closed and require repair; do not guess which version is safe to launch.

For a restart before activation, discard transaction-owned staging and retain the recorded active version. A persisted removal operation resumes idempotently. These recovery behaviors are exercised by the Python reference state machine and tests using a JSON round-trip of the operation journal; Android persistence and filesystem transactions are not implemented yet.

### Disable and removal

- Disable/enable is a durable flag change and requires the runtime to be stopped first. The Host must request orderly shutdown before committing the flag. A disabled module remains installed and can be updated, but cannot be launched.
- Removal requires a stopped runtime and no other lifecycle operation. It is a durable \`removing\` transaction. The Host removes module code, registry metadata, rollback copies, and module-owned data according to the user's explicit removal choice. The operation remains recoverable and retryable if cleanup fails; it must not report removal complete while the registry still exposes the module.
- Runtime crashes are transient failures, not an install failure. The Host stops the session and records diagnostics separately; it does not silently disable or uninstall the module.
- Compatibility failures are derived from manifest/API/capability evaluation and are not persisted as package corruption. They block activation with an explicit incompatibility reason.

### Ownership and invariants

The Registry owns durable installation records, operation journals, active/previous version references, and disablement. The Installer owns download, verification, and staging. The Activator owns atomic pointer changes and restart reconciliation. The Runtime owns live sessions and reports stopped/running; it never changes installation metadata directly.

Invariants:
1. At most one lifecycle operation exists per module.
2. A running module always references the currently committed active version.
3. Active and previous versions refer only to completely verified immutable packages.
4. Before activation commit, failure/cancellation cannot change active or previous versions.
5. After activation commit, the former active version is retained as the previous known-good version until a later successful update or explicit cleanup policy.
6. Removal and disablement cannot race a running session.
7. A failed operation is observable and retryable; it never converts a working active version into a failed installation.

The reference implementation is \`scripts/module_lifecycle.py\`; its transition and crash-recovery tests run in CI. It defines contract behavior only, not Android storage, locking, or process management.

## Framework independence

The Host consumes the package contract, not the source framework. Candidate implementations include:
- vanilla JavaScript or TypeScript;
- Svelte;
- React, Vue, Solid, or other frameworks compiling to supported web assets;
- Rust compiled to WebAssembly, with DOM, Canvas, or WebGL integration.

This is not unrestricted native-code execution. WebAssembly executes within the browser runtime and remains subject to browser security boundaries.

## Runtime isolation

Each module must execute in a context that does not expose the Platform UI or another module's DOM and JavaScript state.

Native functionality is mediated by a restricted, versioned API. Do not add an unrestricted JavaScript bridge or expose arbitrary file, intent, or process access.

The Android WebView isolation model, origin strategy, message channel, and content-security policy remain open design work.

## Module-owned UI

A module owns its full-screen application UI. The Platform owns outer navigation and lifecycle. Dashboard/tile integration is optional and will use a separate constrained contribution contract.

## Updates

A module version is downloaded and validated separately from the Host. A new version must be staged and checked before replacing the active version. Failed installation must not corrupt the currently active version.

GitHub Releases are the initial distribution source. The module repository's release artifact and manifest become the data consumed by the Host.

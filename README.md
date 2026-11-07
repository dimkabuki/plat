# PLAT

PLAT is an experimental, repository-driven project for a modular application platform. The first Host is Android; modules are portable web applications that can be updated independently of the Host.

The project is intentionally developed in small increments by the repository owner and AI agents. The repository is the durable source of truth for design decisions, implementation state, verification results, and the next task.

## Start here

For a new contributor or AI agent, read these files in order:

1. [AGENTS.md](AGENTS.md) - working rules and checkpoint protocol.
2. [PROJECT.md](PROJECT.md) - product goals, scope, and constraints.
3. [STATE.md](STATE.md) - current implementation state and next increment.
4. [ROADMAP.md](ROADMAP.md) - planned development phases.
5. [Copyable session recovery prompt](docs/agent/recover-context.md#copyable-prompt) - restore context in a new agent session.

Architecture documentation and accepted decisions live under [docs/](docs/).

## Recover a new agent session

Start a new agent session, provide the repository URL, and ask the agent to use the [copyable recovery prompt](docs/agent/recover-context.md#copyable-prompt). On GitHub, fenced code blocks provide a built-in copy control.

The recovery prompt is read-only: it asks the agent to inspect the repository and report the current state without modifying files. Approve the next implementation increment separately.

## Current status

The repository now defines Module Manifest v1, a validated module package layout, the installation lifecycle, Platform API v1, and the Host Adapter descriptor/session contract with conformance scenarios. The Android Host, runtime, module manager, SDK, and module implementation do not exist yet. See [STATE.md](STATE.md) for the authoritative status.

## Repositories

- Platform: https://github.com/dimkabuki/plat
- Demo module: planned as a separate repository; not created yet.

The platform repository owns the canonical Module Contract and Platform API specifications.

## Development model

- Work directly on `main`; no pull-request workflow is planned.
- Keep changes small and independently verifiable.
- Run relevant checks before committing and pushing.
- Use Conventional Commits.
- Update `STATE.md` and `ROADMAP.md` in the same implementation commit when progress changes; avoid metadata-only follow-up commits.
- Keep CI read-only. Release workflows receive write permission only when publishing a release.

## Current CI scope

CI validates continuity documents and runs automated tests for the Module Manifest v1 schema, ZIP package validator, reference lifecycle state machine, Platform API v1 protocol/capability contracts, and Host Adapter descriptor/conformance contracts. It will be extended with Android build, lint, and platform tests when the Android project is introduced.

The release workflow is scaffolded for Android APK releases, but cannot succeed until the Android Gradle project and its signing configuration exist.

## License

No license has been selected yet. Do not assume that public visibility grants permission to reuse the code.

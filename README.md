# PLAT

PLAT is an experimental, repository-driven project for a modular application platform. The first Host is Android; modules are portable web applications that can be updated independently of the Host.

The project is intentionally developed in small increments by the repository owner and AI agents. The repository is the durable source of truth for design decisions, implementation state, verification results, and the next task.

## Start here

For a new contributor or AI agent, read these files in order:

1. [AGENTS.md](AGENTS.md) - working rules and checkpoint protocol.
2. [PROJECT.md](PROJECT.md) - product goals, scope, and constraints.
3. [STATE.md](STATE.md) - current implementation state and next increment.
4. [ROADMAP.md](ROADMAP.md) - planned development phases.
5. [Session recovery prompt](docs/agent/recover-context.md) - prompt to restore context in a new agent session.

Architecture documentation and accepted decisions live under [docs/](docs/).

## Current status

The repository is at the bootstrap stage. Product direction and initial architecture have been agreed, but no Android Host, runtime, module manager, SDK, or module implementation exists yet. See [STATE.md](STATE.md) for the authoritative status.

## Repositories

- Platform: https://github.com/dimkabuki/plat
- Demo module: planned as a separate repository; not created yet.

The platform repository owns the canonical Module Contract and Platform API specifications.

## Development model

- Work directly on `main`; no pull-request workflow is planned.
- Keep changes small and independently verifiable.
- Run relevant checks before committing and pushing.
- Use Conventional Commits.
- Update `STATE.md` at every completed development checkpoint.
- Keep CI read-only. Release workflows receive write permission only when publishing a release.

## Current CI scope

The initial CI validates the presence and structure of project metadata. It will be extended with Android build, lint, and test jobs when the Android project is introduced.

The release workflow is scaffolded for Android APK releases, but cannot succeed until the Android Gradle project and its signing configuration exist.

## License

No license has been selected yet. Do not assume that public visibility grants permission to reuse the code.

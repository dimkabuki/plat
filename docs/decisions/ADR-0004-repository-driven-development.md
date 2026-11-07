# ADR-0004: Repository-Driven Development and Continuity

- Status: Accepted
- Date: 2026-11-07

## Context
Development will be performed in small increments by the repository owner and AI agents. Work may continue in different sessions, after context limits, or with a different agent/provider. The process must not depend on chat history.

## Decision
The GitHub repository is the durable source of truth for project context and progress.

- Keep `AGENTS.md`, `PROJECT.md`, `STATE.md`, and `ROADMAP.md` current.
- Store architecture decisions as ADRs.
- Store a reusable session recovery prompt in the repository.
- Work directly on `main` with small, independently verifiable commits.
- Run CI on every push to `main`.
- Use separate tag-triggered release workflows.
- Update `STATE.md` after each completed increment with observed verification and one concrete next step.

## Consequences
- A new compatible agent can reconstruct project context from GitHub.
- Conversation history is not an authoritative engineering artifact.
- Checkpoint quality is part of the definition of done.
- Direct pushes require disciplined local verification because there is no PR gate.

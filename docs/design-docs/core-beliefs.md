# Core Beliefs

These are the durable rules that guide repository structure and agent work.

## Principles

- The repository is the source of truth.
- Small, discoverable docs are preferred over large hidden instructions.
- Architecture should be enforceable by tests, not just described in prose.
- Package boundaries should make intended dependencies obvious.
- Agents should be able to understand the system by reading the repo.
- Every new capability should improve legibility for future work.

## Working Rules

- Put business logic in `src/domain`.
- Put external integrations in `src/infrastructure`.
- Put runtime wiring and user-facing entry points in `src/interface`.
- Keep execution plans explicit and move completed plans out of `active/`.
- Add tests when introducing a new invariant or dependency rule.

# Architecture

This repository follows a strict layered architecture to maintain agent legibility
and enforce clear dependency boundaries. The layout is intentionally small and
predictable so both humans and agents can reason about the system.

## Layers

- Domain (`src/domain`)
  - Business logic, domain models, validation rules, and core invariants.
  - Must not import from `src/infrastructure` or `src/interface`.

- Infrastructure (`src/infrastructure`)
  - External connectors and adapters, including HTTP clients, DB adapters, and schedulers.
  - May depend on `src/domain` but not on `src/interface`.

- Interface (`src/interface`)
  - Runtime wiring and entrypoints, including Telegram handlers, CLI, and scheduler wiring.
  - May depend on `src/infrastructure` and `src/domain`.

## Package Mapping

- `src/domain` - dataclasses, domain exceptions, pure logic.
- `src/infrastructure` - `db.py`, `repository.py`, `weather_client.py`, and similar adapters.
- `src/interface` - `bot.py`, `scheduler.py`, and other handler wiring.
- `src/main.py` - top-level runtime bootstrap that wires interface components and starts the application.

## Rules and Rationale

- Dependency flow must be inward-only: `interface -> infrastructure -> domain`.
- Avoid cross-cutting imports; use explicit provider interfaces for shared concerns such as logging, config, and telemetry when needed.
- Keep modules small and single-purpose; prefer composition over monolithic utilities so automated agents can safely edit micro-targets.

## Runtime Responsibilities

- `src/main.py` is the runtime bootstrap that wires `src/interface` components, instantiates the scheduler, and starts the Telegram dispatcher.
- `src/interface/bot.py` handles Telegram command handlers such as `/start`, `/forecast`, `/location`, `/coords`, and `/stop`, delegating location persistence and weather lookup to infrastructure adapters.
- Long-running concerns such as schedulers and webhooks should be encapsulated in `src/interface` and call into `src/infrastructure` adapters for IO.

## Verification Gates

- Enforce dependency and layering rules via tests in `tests/test_layering.py`.
- Verify domain contracts and invariants via `tests/test_domain_contracts.py`.
- Verify startup wiring via `tests/test_integration_smoke.py`.
- Document evolution in `docs/exec-plans` and keep `AGENTS.md` as the map.

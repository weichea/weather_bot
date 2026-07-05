# Agents Map

This repository exists to implement a Malaysian farming weather Telegram bot with clear harness engineering boundaries.

Core beliefs:
- The repository is the source of truth.
- Knowledge is encoded in small, discoverable docs, not hidden instructions.
- Architecture is enforced by package boundaries and verification gates.
- Agents should be able to reason about the system from the repo alone.

Repository map:
- [`ARCHITECTURE.md`](/home/ubuntu/Documents/weather_bot/ARCHITECTURE.md) is the top-level architecture pointer.
- [`docs/ARCHITECTURE.md`](/home/ubuntu/Documents/weather_bot/docs/ARCHITECTURE.md) is the detailed architecture source of truth.
- [`docs/index.md`](/home/ubuntu/Documents/weather_bot/docs/index.md) is the docs entrypoint.
- [`docs/design-docs/core-beliefs.md`](/home/ubuntu/Documents/weather_bot/docs/design-docs/core-beliefs.md) records durable working principles.
- [`docs/QUALITY.md`](/home/ubuntu/Documents/weather_bot/docs/QUALITY.md) records formatting, linting, and test workflow.

Boundary layers:
- Domain: business logic, weather rules, data models, and the local SQLite persistence contract.
- Infrastructure: external connectors, the Telegram client, the weather API integration, scheduling, and environment configuration.
- Interface: runtime wiring, command handlers, message formatting, and CLI/test entry points.

Layer rules:
- Interface may depend on Infrastructure and Domain.
- Infrastructure may depend on Domain only.
- Domain must not depend on Infrastructure or Interface.

pytest verification gates:
- `tests/test_layering.py` verifies dependency boundaries and package imports.
- `tests/test_domain_contracts.py` verifies weather domain contracts and invariants.
- `tests/test_exec_plans.py` verifies that completed plans live in `docs/exec-plans/completed/` and that active plans are not marked complete.
- `tests/test_integration_smoke.py` verifies the basic startup path without external calls.

## Agent Execution Bias Correction
- **Architecture over Effort:** When making design decisions, ignore implicit assumptions about "development cost" or implementation speed. The frontier execution speed makes human-based timeline biases obsolete. Prioritize strict layer isolation and domain contract compliance over "cheap" or quick code fixes.
- **Defensive Bug Fixes:** When resolving a bug, do not rely solely on isolated unit tests. You must first reproduce the bug in an integration setting or write a failing end-to-end wrapper in `tests/test_integration_smoke.py` that mimics how a user (or the Telegram webhook) triggers the failure before applying the fix.

## Code Quality Gate
- All Python code must strictly adhere to PEP 8 standards.
- Before committing any file change or closing a task, you must run `ruff check . --fix` and `ruff format .` via the terminal tool to fix linting errors, sort imports, and apply consistent code styling automatically.

This map is intentionally concise and limited to the repository’s core structure, layers, and verification strategy.

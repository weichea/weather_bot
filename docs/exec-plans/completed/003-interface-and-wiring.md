# Execution Plan 003: Interface Wiring & User Flows

Status: Complete

## Objective
Wire the Telegram interface, persistence, and scheduler so user locations can be registered and daily forecasts delivered.

## Tasks
- [x] Task 1: Design DB schema and implement `src/infrastructure/db.py` (user table, preferences, last_sent) — completed.
- [x] Task 2: Implement `src/interface/bot.py` handlers (`/start`, `/help`, `/stop`) and registration prompts.
- [x] Task 3: Handle shared `Location` messages and typed coordinates parsing (`lat, lon`).
- [x] Task 4: Implement persistence functions: add/update user, fetch active users, disable user.
- [x] Task 5: Wire scheduler job (`src/interface/scheduler.py`) to load users, call `DataGovMyWeatherClient`, and send messages.
- [x] Task 6: Add tests: `tests/test_bot_handlers.py`, `tests/test_scheduler.py`, and update `tests/test_layering.py` as needed.
- [x] Task 7: Update `docs/ARCHITECTURE.md` and `docs/QUALITY.md` with wiring notes and runtime expectations.
- [x] Task 8: Run Ruff quality gate and unit tests locally; iterate until green.

## Acceptance criteria
- `src/interface` depends only on `src/infrastructure` and `src/domain` per AGENTS.md.
- All new modules pass `ruff check . --fix` and `ruff format .`.
- Tests exercising handler flows and scheduler run pass locally.

## Notes
- Implementations must follow the harness engineering layering rules: Domain must not import Infrastructure or Interface.
- Keep handlers small and delegate logic to Infrastructure and Domain modules for testability.


# Execution Plan 004: Runtime Bootstrap & Configuration

Status: Complete

## Objective
Build the application startup layer so the bot can run from a single entrypoint, read config from environment, wire dependencies, and start the scheduler safely.

## Tasks
- [x] Task 1: Add runtime configuration support in `src/infrastructure/config.py`.
  - Load required environment values: `TELEGRAM_BOT_TOKEN`, `DATA_GOV_MY_BASE_URL`, `DATABASE_PATH`, `DAILY_CRON`.
  - Validate config and raise a clear startup error if any required values are missing.
- [x] Task 2: Add the startup entrypoint in `src/main.py`.
  - Initialize the SQLite schema and pass the configured database path into repository helpers.
  - Instantiate `DataGovMyWeatherClient` with the configured base URL.
  - Instantiate the Telegram bot and register command/message handlers.
  - Wire the scheduler job to send daily messages using the configured cron expression.
- [x] Task 3: Add graceful bootstrap and shutdown.
  - Expose a `main()` entrypoint for `python src/main.py` or equivalent.
  - Ensure startup failures are logged clearly and do not leave resources open.
- [x] Task 4: Add integration/startup smoke tests.
  - Create or extend `tests/test_integration_smoke.py`.
  - Verify the app can build runtime objects with environment config without external API calls.
  - Verify `DATA_GOV_MY_BASE_URL` is injected into the weather client.
  - Verify config validation rejects missing required values.
  - Verify `DAILY_CRON` is accepted and converted into scheduler wiring.
- [x] Task 5: Update docs and architecture notes.
  - Document startup wiring in `docs/ARCHITECTURE.md`.
  - Add fast reference to runtime config requirements in `docs/QUALITY.md`.
- [x] Task 6: Run the quality gate.
  - Execute `ruff check . --fix` and `ruff format .`.
  - Run pytest and confirm the new plan passes.

## Acceptance criteria
- A single documented app entrypoint exists.
- Environment config is explicit, validated, and fails fast on missing values.
- The weather API base URL is configured through runtime wiring rather than hardcoded.
- The scheduler cron configuration is wired through the startup layer and validated.
- Dependency wiring stays within the interface/infrastructure boundary rules.
- Startup smoke tests pass and Ruff formatting/linting is clean.

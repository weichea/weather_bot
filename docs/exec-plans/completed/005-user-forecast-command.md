# Execution Plan 005: User-Initiated 24-Hour Forecast Command

Status: Complete

## Objective
Add a Telegram bot command so users can request a 24-hour forecast on demand, without waiting for the daily blast.

## Tasks
- [x] Task 1: Define a new interface command in `src/interface/bot.py`.
  - Add `/forecast` or `/weather` to the supported command set.
  - Document expected usage in the bot help text.
- [x] Task 2: Implement a user-facing forecast handler.
  - Retrieve the requesting user's saved location from the repository.
  - If no location is available, prompt the user to send `/start` or share a location.
  - Otherwise, fetch a 24-hour forecast from the weather client.
- [x] Task 3: Extend the weather client or domain model if needed.
  - Use the user's latitude/longitude to choose the nearest weather station, not the administrative district.
  - Ensure the forecast can represent the requested 24-hour summary.
  - If the API already returns today/tomorrow intervals, map them into user-facing text.
- [x] Task 4: Add a helper to format the immediate forecast message.
  - Reuse or extend existing `_format_forecast_message` behavior in `src/interface/scheduler.py`.
  - Keep formatting consistent with the daily blast style.
- [x] Task 5: Add tests for the new command.
  - Add unit tests for the new handler in `tests/test_bot_handlers.py`.
  - Add coverage for the no-location fallback and successful forecast retrieval.
- [x] Task 6: Update docs.
  - Add command description to `docs/ARCHITECTURE.md` or `README.md` if needed.
  - Update `docs/QUALITY.md` with any new behavior or test expectations.
- [x] Task 7: Run the quality gate.
  - Execute `ruff check . --fix` and `ruff format .`.
  - Run pytest and verify all tests pass.

## Acceptance criteria
- Users can type a new command to retrieve an on-demand forecast.
- The command uses the existing user location record and does not require additional registration.
- If no saved location exists, the bot responds with a clear next step.
- New tests cover success and missing-location cases.
- The new command is documented and the project still passes Ruff and pytest.

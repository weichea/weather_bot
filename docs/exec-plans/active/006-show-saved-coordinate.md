# Execution Plan 006: Show Saved User Coordinates

Status: In Progress

## Objective
Add a Telegram command that lets a user see the currently saved GPS coordinates for their account.

## Tasks
- [ ] Task 1: Define a new interface command in `src/interface/bot.py`.
  - Add `/location`, `/coords`, or `/whereami` to the supported command set.
  - Document expected usage in the bot help text.
- [ ] Task 2: Implement a user-facing location display handler.
  - Load the user record from the repository using `telegram_id`.
  - If no user location exists, reply with a clear prompt to send `/start` or share a location.
  - Otherwise, return the saved latitude/longitude and optionally the location name.
- [ ] Task 3: Keep persistence logic unchanged.
  - Reuse `repository.get_user(...)` and `Location` mapping.
  - Do not add duplicate location storage; simply show the current saved record.
- [ ] Task 4: Add tests for the new handler.
  - Add unit tests for `tests/test_bot_handlers.py` covering saved-location display and missing-location fallback.
  - Ensure the command handler returns the expected message text.
- [ ] Task 5: Update docs.
  - Add the new command description to `README.md`.
  - Add a note in `docs/ARCHITECTURE.md` if the command expands interface handler coverage.
- [ ] Task 6: Run the quality gate.
  - Execute `ruff check . --fix` and `ruff format .`.
  - Run pytest and verify all tests pass.

## Acceptance criteria
- Users can type a new command to view their saved coordinates.
- The bot responds clearly when no coordinates are saved.
- The command reuses existing repository lookups and does not create new storage behavior.
- New tests cover the saved-coordinate response and the no-location fallback.
- Documentation is updated and the project passes Ruff and pytest.

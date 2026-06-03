# Execution Plan 007: Support Multiple Saved User Coordinates

Status: In Progress

## Objective
Allow each Telegram user to save more than one coordinate pair and make `/location`, `/coords`, and `/forecast` return all saved coordinates for that user.

## Tasks
- [ ] Task 1: Design persistence changes.
  - Add a dedicated `locations` table keyed by `telegram_id`.
  - Keep the existing `users` table for user metadata and daily blast state.
  - Preserve backward compatibility by keeping a primary location accessible.
- [ ] Task 2: Update repository behavior.
  - Add repository support for appending new saved coordinates.
  - Support querying all saved locations for a given user.
  - Keep the existing `get_user(...)` API working by returning the most recent saved location as the primary record.
- [ ] Task 3: Update bot handlers.
  - Change `/location` and `/coords` to list every saved coordinate for the user.
  - Change `/forecast` to use the most recent saved coordinate by default.
  - Add user-facing text that clearly explains multiple saved locations are supported.
- [ ] Task 4: Add migration strategy.
  - Migrate any existing single saved location from `users` into the new `locations` table.
  - Ensure migration is safe to run more than once.
- [ ] Task 5: Add tests.
  - Cover saving multiple typed coordinates or shared locations.
  - Cover `/location` returning all saved coordinates.
  - Cover `/forecast` still working with the newest saved coordinate.
  - Cover the empty state when a user has no saved locations.
- [ ] Task 6: Update docs and help text.
  - Document the new behavior in `README.md` and bot help text.
  - Add a note to architecture/docs if persistence semantics changed.
- [ ] Task 7: Run the quality gate.
  - Execute `ruff check . --fix` and `ruff format .`.
  - Run `pytest` and ensure all tests pass.

## Acceptance criteria
- The system can store multiple location coordinates per Telegram user.
- `/location` and `/coords` return all saved coordinates for the user.
- `/forecast` continues to work by selecting the most recent saved coordinate.
- Existing daily blast and user metadata behavior remains intact.
- Tests cover the multi-location behavior and the no-location fallback.
- Documentation and help text are updated to describe the new capability.

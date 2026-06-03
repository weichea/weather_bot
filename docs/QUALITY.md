# Quality

This document captures the repository's automated and manual quality checks.
Follow these steps locally before committing changes.

Formatting & Linting

- We use `ruff` as the primary linter and formatter. Configuration is in
  `pyproject.toml`.
- Enforced rules: select `E`, `F`, `I`, `W` and `line-length = 88`.

Run the checks and auto-fixes:

```bash
# from repository root, using the project venv
./venv/bin/ruff check . --fix
./venv/bin/ruff format .
```

Optional formatters

- `black` and `isort` may be added later; `ruff` currently handles formatting
  and import sorting via its configuration.

Tests

- Run the test suite locally before merging changes:

```bash
./venv/bin/pytest -q
```

- Tests are expected to be fast and isolated; external network calls must be
  mocked in unit tests.
- New interface behavior such as `/forecast` should be covered by unit tests for both successful forecast retrieval and missing-location fallback.

Commit workflow

- Run the lint/format commands above and execute tests prior to pushing.
- The application also requires runtime environment variables such as `TELEGRAM_BOT_TOKEN`, `DATA_GOV_MY_BASE_URL`, `DATABASE_PATH`, and `DAILY_CRON`.
- Consider adding a `pre-commit` configuration to automate these steps.

Quality gates

- `AGENTS.md` includes a short-lived `Code Quality Gate` that mandates running
  `ruff` commands before completing tasks.
- CI (optional) should echo the same commands as a blocking check.

If you need help setting up `pre-commit` or CI job configs, I can add them as
the next step.

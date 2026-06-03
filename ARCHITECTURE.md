# Architecture

This is the top-level pointer for the repository architecture.

## Source of Truth

The detailed package layout, boundary rules, and dependency flow are documented in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Verification

The architecture is enforced by repository tests, including:

- `tests/test_layering.py`
- `tests/test_domain_contracts.py`
- `tests/test_integration_smoke.py`

"""Verify execution-plan lifecycle conventions.

Plans in docs/exec-plans/active must not be marked complete.
Plans in docs/exec-plans/completed must be marked complete.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DIR = ROOT / "docs" / "exec-plans" / "active"
COMPLETED_DIR = ROOT / "docs" / "exec-plans" / "completed"


def _status_line(path: Path) -> str | None:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Status:"):
            return line.partition(":")[2].strip()
    return None


def _plan_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob("*.md"))


def test_active_plans_are_not_complete() -> None:
    violations: list[str] = []
    for path in _plan_files(ACTIVE_DIR):
        status = _status_line(path)
        if status == "Complete":
            violations.append(f"{path} is complete but still in active/")

    assert not violations, "\n".join(violations)


def test_completed_plans_are_complete() -> None:
    violations: list[str] = []
    for path in _plan_files(COMPLETED_DIR):
        status = _status_line(path)
        if status != "Complete":
            violations.append(f"{path} is not complete but is in completed/")

    assert not violations, "\n".join(violations)

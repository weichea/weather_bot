# tests/test_exec_plans.py
import os
import pytest

ACTIVE_PLAN_PATH = "docs/exec-plans/active-plan.md"
COMPLETED_PLANS_DIR = "docs/exec-plans/completed/"

def test_active_plan_exists_and_is_tracked():
    """Point 2: Guarantees the agent keeps its state engine on disk."""
    assert os.path.exists(ACTIVE_PLAN_PATH), (
        "Harness Violation: 'docs/exec-plans/active-plan.md' was deleted or moved. "
        "The active execution plan must exist as an on-disk state machine."
    )
    
    with open(ACTIVE_PLAN_PATH, "r") as f:
        content = f.read()
    
    assert "# Active Execution Plan" in content, (
        "Harness Violation: Active plan structure was corrupted. "
        "Keep the standard structural markdown headers intact."
    )

def test_no_completed_plans_in_flight():
    """Ensures old plans are cleanly archived in the historical tracking directory."""
    if os.path.exists(COMPLETED_PLANS_DIR):
        for file in os.listdir(COMPLETED_PLANS_DIR):
            assert file.endswith(".md"), f"Non-markdown file found in tracking directory: {file}"
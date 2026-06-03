"""Verify the repository layer boundaries.

The repository is organized as a src-layout with three top-level packages:
domain, infrastructure, and interface. These tests enforce the dependency
direction described in AGENTS.md and docs/ARCHITECTURE.md.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
LAYER_PACKAGES = {"domain", "infrastructure", "interface"}


def _layer_for_path(path: Path) -> str | None:
    try:
        layer = path.relative_to(SRC_ROOT).parts[0]
    except ValueError:
        return None
    return layer if layer in LAYER_PACKAGES else None


def _import_root(module: str | None) -> str | None:
    if not module:
        return None
    root = module.split(".", 1)[0]
    return root if root in LAYER_PACKAGES else None


def _imported_layers(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    layer = _layer_for_path(path)
    if layer is None:
        return set()

    imported_layers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported = _import_root(alias.name)
                if imported and imported != layer:
                    imported_layers.add(imported)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                continue
            imported = _import_root(node.module)
            if imported and imported != layer:
                imported_layers.add(imported)
    return imported_layers


def test_layering_rules_are_respected() -> None:
    violations: list[str] = []
    for path in SRC_ROOT.rglob("*.py"):
        layer = _layer_for_path(path)
        if layer is None:
            continue

        imported_layers = _imported_layers(path)
        if layer == "domain":
            forbidden = {"infrastructure", "interface"}
        elif layer == "infrastructure":
            forbidden = {"interface"}
        else:
            forbidden = set()

        for imported in sorted(imported_layers & forbidden):
            violations.append(f"{path}: {layer} must not import {imported}")

    assert not violations, "\n".join(violations)

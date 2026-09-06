"""This package must not depend on kirby-combat, and does not.

THE DEPENDENCY DIRECTION IS THE DESIGN. A Team is campaign-level identity;
a ``side`` is one fight's alignment. The bridge between them is a plain
string --- ``sides_from_teams`` returns ``{character_id: side_name}``, and
a combatant's ``side`` is a free ``str``.

Had ``side`` been typed as a Team reference, kirby-combat would import
this package, and every fight would drag narrative prose, rosters and
(eventually) tenancy behind it. The engine would then be unable to resolve
an attack without knowing what a campaign is.

Nothing enforces this but a test, so here it is.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
FORBIDDEN = ("kirby_combat", "kirby_cost", "kirby_sheet", "kirby_terrain")


def _imported_modules(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def _sources() -> list[pathlib.Path]:
    return sorted((ROOT / "kirby_campaign").rglob("*.py"))


def test_there_is_something_to_scan():
    """A scan over an empty file list would pass while proving nothing."""
    assert _sources()


@pytest.mark.parametrize("forbidden", FORBIDDEN)
def test_no_module_imports_a_sibling_engine(forbidden):
    offenders = {
        path.relative_to(ROOT): imported
        for path in _sources()
        for imported in [_imported_modules(path)]
        if any(m == forbidden or m.startswith(f"{forbidden}.") for m in imported)
    }
    assert not offenders, (
        f"kirby-campaign must not import {forbidden}: {offenders}"
    )


def test_the_package_has_no_runtime_dependencies():
    """Zero dependencies is the claim pyproject.toml makes; a stray one
    would make this package untestable in memory."""
    text = (ROOT / "pyproject.toml").read_text()
    assert "dependencies = []" in text


def test_it_imports_with_nothing_else_installed():
    import kirby_campaign

    assert kirby_campaign.__all__

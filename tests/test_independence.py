"""The dependency runs one way, and only a test keeps it that way.

kirby-campaign sits ABOVE kirby-combat and imports it: a Team becomes a
``Side``, and ``Side`` lives in the engine because a free-for-all in an
alley has sides and no campaign at all. The lower package owns the class;
the higher one builds instances.

**The reverse must never happen.** If kirby-combat imported this package,
resolving an attack would depend on knowing what a campaign is --- dragging
rosters, narrative prose and eventually tenancy behind every roll, and
making the engine unusable for a fight between two strangers.

That earlier read as "neither imports the other", which was too strict in
one direction and would have blocked the very thing that makes group
tactics work: a chooser here that picks by roster and leader can only
implement the engine's ``Chooser`` protocol by importing it.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
#: Engines this package has no business reaching into. kirby-combat is
#: absent deliberately --- it is the one dependency, declared in
#: pyproject.toml.
FORBIDDEN = ("kirby_cost", "kirby_sheet", "kirby_terrain", "kirby_ai")


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
def test_no_module_reaches_into_an_unrelated_engine(forbidden):
    offenders = {
        path.relative_to(ROOT): imported
        for path in _sources()
        for imported in [_imported_modules(path)]
        if any(m == forbidden or m.startswith(f"{forbidden}.") for m in imported)
    }
    assert not offenders, f"kirby-campaign must not import {forbidden}: {offenders}"


def test_kirby_combat_does_not_import_this_package():
    """THE DIRECTION THAT MATTERS. Skipped when the engine's source is not
    beside this checkout -- it is asserted in kirby-combat's own suite too,
    and a missing sibling must not turn into a false green here."""
    engine = ROOT.parent / "kirby-combat" / "kirby_combat"
    if not engine.is_dir():
        pytest.skip("kirby-combat source not checked out beside this repo")

    offenders = {
        path.relative_to(engine.parent): imported
        for path in sorted(engine.rglob("*.py"))
        for imported in [_imported_modules(path)]
        if any(
            m == "kirby_campaign" or m.startswith("kirby_campaign.")
            for m in imported
        )
    }
    assert not offenders, (
        "kirby-combat imports kirby-campaign, which inverts the layering: "
        f"{offenders}"
    )


def test_the_one_declared_dependency_is_the_engine():
    text = (ROOT / "pyproject.toml").read_text()
    assert 'dependencies = ["kirby-combat>=0.13.0"]' in text


def test_the_package_imports():
    import kirby_campaign

    assert kirby_campaign.__all__

"""The two-tier merge: COALESCE(instance, definition), and why not `or`."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from kirby_campaign import TEAM_OVERRIDES, TEAM_STATE, effective, effective_team


@dataclass
class _Def:
    name: str = "Sentinels of Dawn"
    team_type: str = "hero"
    agenda: str | None = "Hold the line"
    history: str | None = None
    tactics: str | None = "Massed ranged fire"
    modus_operandi: str | None = None
    notes: str | None = None


@dataclass
class _Inst:
    name: str | None = None
    team_type: str | None = None
    agenda: str | None = None
    history: str | None = None
    tactics: str | None = None
    modus_operandi: str | None = None
    notes: str | None = None
    is_active: bool | None = True
    status_notes: str | None = None


# ---- Inheriting ----

def test_a_null_override_inherits_the_definition():
    merged = effective_team(_Def(), _Inst())
    assert merged["name"] == "Sentinels of Dawn"
    assert merged["agenda"] == "Hold the line"


def test_a_set_override_wins():
    merged = effective_team(_Def(), _Inst(name="Sentinels of Dusk"))
    assert merged["name"] == "Sentinels of Dusk"


def test_instance_only_state_comes_from_the_instance():
    merged = effective_team(_Def(), _Inst(is_active=False, status_notes="disbanded"))
    assert merged["is_active"] is False
    assert merged["status_notes"] == "disbanded"


def test_a_definition_with_no_instance_is_a_valid_view():
    """A library entry no campaign has instantiated is a perfectly good
    thing to look at; callers should not special-case it."""
    merged = effective_team(_Def())
    assert merged["name"] == "Sentinels of Dawn"
    assert merged["is_active"] is None


def test_a_null_on_both_tiers_stays_null():
    assert effective_team(_Def(), _Inst())["history"] is None


# ---- The falsy-override trap: COALESCE, not `or` ----

@pytest.mark.parametrize("falsy", ["", 0, False, ()])
def test_a_falsy_override_is_honoured_not_discarded(falsy):
    """`or` would silently throw every one of these away in favour of the
    definition. Only None means inherit.

    A campaign that renames a team to "" has made a mistake; one that sets
    a count to 0 has not, and the merge cannot tell them apart -- so it
    honours both rather than guessing."""
    merged = effective(
        {"col": "from the definition"}, {"col": falsy}, overrides=["col"],
    )
    assert merged["col"] == falsy


def test_an_explicitly_emptied_narrative_field_stays_empty():
    merged = effective_team(_Def(), _Inst(agenda=""))
    assert merged["agenda"] == ""


# ---- Shapes ----

def test_mappings_and_objects_both_work():
    """kirby-api hands over ORM rows, a test hands over dataclasses;
    neither should need converting."""
    as_objects = effective_team(_Def(), _Inst(name="Dusk"))
    as_maps = effective_team(
        {k: getattr(_Def(), k) for k in TEAM_OVERRIDES},
        {"name": "Dusk"},
    )
    assert as_maps["name"] == as_objects["name"] == "Dusk"
    assert as_maps["agenda"] == as_objects["agenda"] == "Hold the line"


def test_a_missing_key_on_the_instance_inherits():
    """An instance mapping need not carry every override column."""
    merged = effective({"a": 1, "b": 2}, {"a": 9}, overrides=["a", "b"])
    assert merged == {"a": 9, "b": 2}


def test_a_missing_state_key_reads_as_none():
    assert effective({"a": 1}, {}, overrides=["a"], state=["gone"])["gone"] is None


# ---- Contract ----

def test_an_override_absent_from_the_definition_raises():
    """It could never be inherited, so declaring it is a mistake worth
    naming rather than silently returning None for."""
    with pytest.raises(KeyError, match="both tiers"):
        effective({"a": 1}, {"b": 2}, overrides=["b"])


def test_the_team_column_sets_match_kirby_api():
    """Copied verbatim from `teams/services/effective.py` so the two
    cannot drift. If kirby-api changes its columns, this is the test that
    should fail."""
    assert TEAM_OVERRIDES == (
        "name", "team_type", "agenda", "history", "tactics",
        "modus_operandi", "notes",
    )
    assert TEAM_STATE == ("is_active", "status_notes")

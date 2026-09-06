"""Team, rosters, and the bridge from standing membership to a fight's sides.

Fixtures here use INVENTED teams. Every real team in the corpus comes from
CV1-CV3 or Old School Enemies -- paid Hero Games material whose team
entries ARE the book's prose -- and this package is publishable, so no
sourcebook team may appear in it.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from kirby_campaign import (
    TEAM_TYPES, Team, TeamMember, assign_sides, sides_from_teams, teams_of,
)


@dataclass(frozen=True)
class _Fighter:
    """Stands in for a combatant. Deliberately NOT imported from
    kirby-combat: this package must not depend on it, and a test that
    imported it would hide that."""
    id: str
    side: str | None = None


def _team(name: str, *ids: str, team_type: str = "hero", **kw) -> Team:
    return Team(
        id=name.lower(), name=name, team_type=team_type,
        members=tuple(TeamMember(i, sort_order=n) for n, i in enumerate(ids)),
        **kw,
    )


# ---- Shape ----

def test_a_team_has_a_name_a_type_and_a_roster():
    team = _team("Sentinels of Dawn", "aurora", "bulwark")
    assert team.name == "Sentinels of Dawn"
    assert team.team_type == "hero"
    assert team.member_ids == ("aurora", "bulwark")


@pytest.mark.parametrize("team_type", TEAM_TYPES)
def test_every_declared_team_type_is_accepted(team_type):
    """"villain" is as first-class as "hero" -- villain teams are the
    reason this entity exists. So are agency, neutral and other."""
    assert _team("X", "a", team_type=team_type).team_type == team_type


def test_an_undeclared_team_type_is_rejected():
    with pytest.raises(ValueError, match="team_type"):
        _team("X", "a", team_type="antihero")


def test_a_team_needs_a_name():
    """`side` is reported by name, so a nameless team could not win."""
    with pytest.raises(ValueError, match="name"):
        Team(id="t", name="   ")


def test_a_character_cannot_be_listed_twice():
    with pytest.raises(ValueError, match="twice"):
        Team(id="t", name="T", members=(TeamMember("a"), TeamMember("a")))


def test_membership_is_queryable():
    team = _team("Sentinels", "aurora", "bulwark")
    assert "aurora" in team
    assert "nemesis" not in team


# ---- Roster order and leadership ----

def test_the_roster_sorts_by_sort_order_then_id():
    team = Team(id="t", name="T", members=(
        TeamMember("zara", sort_order=1),
        TeamMember("adam", sort_order=0),
        TeamMember("bram", sort_order=0),
    ))
    assert team.member_ids == ("adam", "bram", "zara")


def test_the_leader_is_the_member_marked_leader():
    team = Team(id="t", name="T", members=(
        TeamMember("grunt", "member", 0), TeamMember("chief", "leader", 1),
    ))
    assert team.leader.character_id == "chief"


def test_a_team_may_have_no_leader():
    """A loose faction is still a team."""
    assert _team("Mob", "a", "b").leader is None


def test_two_leaders_take_the_first_rather_than_raising():
    """A sourcebook with two leaders is a data quirk, not a reason to
    refuse to run a fight."""
    team = Team(id="t", name="T", members=(
        TeamMember("b", "leader", 1), TeamMember("a", "leader", 0),
    ))
    assert team.leader.character_id == "a"


def test_roles_are_carried_not_interpreted():
    """No rule reads leader/lieutenant today -- measured across
    kirby-combat and the parked driver. Pinned so the day one does, this
    test is what changes."""
    team = Team(id="t", name="T", members=(TeamMember("a", "quartermaster"),))
    assert team.roster[0].role == "quartermaster"


# ---- Immutable edits ----

def test_adding_and_removing_members_returns_new_teams():
    team = _team("Sentinels", "aurora")
    bigger = team.with_member(TeamMember("bulwark", sort_order=1))
    smaller = bigger.without_member("aurora")

    assert team.member_ids == ("aurora",), "the original was mutated"
    assert bigger.member_ids == ("aurora", "bulwark")
    assert smaller.member_ids == ("bulwark",)


# ---- The HQ edge ----

def test_a_team_carries_opaque_base_ids():
    """A Base is a BUILD -- built with the base rules, HDC-imported, costed
    by kirby-cost, and terrain with BODY and DEF in a fight. Only the
    reference belongs here."""
    team = _team("Sentinels", "aurora", base_ids=("dawn-spire",))
    assert team.base_ids == ("dawn-spire",)


def test_a_team_may_hold_several_bases_or_none():
    assert _team("Nomads", "a").base_ids == ()
    assert len(_team("Empire", "a", base_ids=("keep", "vault")).base_ids) == 2


# ---- sides_from_teams: the bridge ----

def test_members_map_to_their_team_name():
    heroes = _team("Sentinels", "aurora", "bulwark")
    villains = _team("Iron Chorus", "nemesis", team_type="villain")
    assert sides_from_teams([heroes, villains]) == {
        "aurora": "Sentinels", "bulwark": "Sentinels", "nemesis": "Iron Chorus",
    }


def test_the_side_is_the_name_not_the_id():
    """`side` is reported back as the winner, so it must read."""
    assert sides_from_teams([_team("Sentinels", "aurora")])["aurora"] == "Sentinels"


def test_a_character_on_two_teams_raises():
    """Which side they fight for would otherwise depend on iteration
    order. The caller resolves a crossover by setting that character's
    side for that fight -- which is why side and team are separate."""
    with pytest.raises(ValueError, match="two sides"):
        sides_from_teams([_team("Sentinels", "aurora"), _team("Vanguard", "aurora")])


def test_the_conflict_names_the_character_and_both_teams():
    with pytest.raises(ValueError) as excinfo:
        sides_from_teams([_team("Sentinels", "aurora"), _team("Vanguard", "aurora")])
    message = str(excinfo.value)
    assert "aurora" in message and "Sentinels" in message and "Vanguard" in message


def test_the_same_team_listed_twice_is_not_a_conflict():
    team = _team("Sentinels", "aurora")
    assert sides_from_teams([team, team]) == {"aurora": "Sentinels"}


def test_teams_of_returns_every_team_a_character_is_on():
    """Plural on purpose: standing membership in several teams is legal.
    It is only ambiguous when a FIGHT needs one side."""
    a, b = _team("Sentinels", "aurora"), _team("Vanguard", "aurora")
    assert teams_of("aurora", [a, b]) == (a, b)
    assert teams_of("nobody", [a, b]) == ()


# ---- assign_sides ----

def test_assign_sides_fills_the_side_in_from_the_team():
    fighters = [_Fighter("aurora"), _Fighter("nemesis")]
    teams = [_team("Sentinels", "aurora"),
             _team("Iron Chorus", "nemesis", team_type="villain")]
    assert [f.side for f in assign_sides(fighters, teams)] == [
        "Sentinels", "Iron Chorus",
    ]


def test_an_explicit_side_outranks_standing_membership():
    """THE CIVIL WAR CASE. Two teammates on opposite sides of one fight,
    without editing the team -- which is the whole reason side and team
    are separate things."""
    fighters = [_Fighter("aurora", side="Loyalists"), _Fighter("bulwark")]
    teams = [_team("Sentinels", "aurora", "bulwark")]
    assert [f.side for f in assign_sides(fighters, teams)] == [
        "Loyalists", "Sentinels",
    ]


def test_overwrite_forces_the_team_side():
    fighters = [_Fighter("aurora", side="Loyalists")]
    out = assign_sides(fighters, [_team("Sentinels", "aurora")], overwrite=True)
    assert out[0].side == "Sentinels"


def test_a_combatant_on_no_team_is_left_alone():
    """A bystander in a war between named teams is not on one of them --
    they stay their own side."""
    out = assign_sides([_Fighter("drifter")], [_team("Sentinels", "aurora")])
    assert out[0].side is None


def test_assign_sides_does_not_mutate_its_input():
    fighters = [_Fighter("aurora")]
    assign_sides(fighters, [_team("Sentinels", "aurora")])
    assert fighters[0].side is None

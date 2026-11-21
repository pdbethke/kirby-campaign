"""Memberships: who belongs to which organisation, at what rank, and when."""
import pytest

from kirby_campaign import Membership, WorldDate, WorldState
from tests.conftest import person

D = WorldDate


def m(id, org, who, rank, *, started=None, ended=None):
    return Membership(id=id, world_id="w-1", organisation_id=org, person_id=who, rank=rank,
                      started=started, ended=ended, source_ref=None, source_status=None)


def test_a_person_can_belong_to_two_organisations_at_once(records):
    records["people"] = (*records["people"], person("p-tony", "Tony Vance"))
    records["memberships"] = (*records["memberships"],
                              m("m-t1", "brenner-family", "p-tony", "soldier"),
                              m("m-t2", "the-coil", "p-tony", "agent"))
    state = WorldState(**records)
    assert {x.organisation_id for x in state.memberships_of("p-tony")} == {
        "brenner-family", "the-coil"}


def test_a_promotion_keeps_the_history(records):
    records["people"] = (*records["people"], person("p-tony", "Tony Vance"))
    records["memberships"] = (*records["memberships"],
                              m("m-old", "brenner-family", "p-tony", "soldier",
                                started=D(year=118, month=1, day=1),
                                ended=D(year=121, month=1, day=1)),
                              m("m-new", "brenner-family", "p-tony", "lieutenant",
                                started=D(year=121, month=1, day=1)))
    state = WorldState(**records)
    assert state.rank_of("p-tony", "brenner-family") == "lieutenant"
    assert state.rank_of("p-tony", "talley-outfit") is None


def test_two_open_memberships_in_one_organisation_are_refused(records):
    records["memberships"] = (*records["memberships"],
                              m("m-dup", "brenner-family", "p-sal", "soldier"))
    with pytest.raises(ValueError, match="p-sal.*brenner-family|brenner-family.*p-sal"):
        WorldState(**records)


def test_a_rank_not_on_the_ladder_is_refused(records):
    records["memberships"] = (*records["memberships"],
                              m("m-x", "brenner-family", "p-ada", "consigliere"))
    with pytest.raises(ValueError, match="consigliere"):
        WorldState(**records)


def test_a_membership_of_an_unknown_organisation_is_refused(records):
    records["memberships"] = (m("m-x", "ghosts", "p-sal", "soldier"),)
    with pytest.raises(ValueError, match="ghosts"):
        WorldState(**records)


def test_the_head_must_be_a_current_member(records):
    records["memberships"] = tuple(x for x in records["memberships"] if x.person_id != "p-sal")
    with pytest.raises(ValueError, match="p-sal"):
        WorldState(**records)


def test_members_are_listed_by_rank_then_id(records):
    state = WorldState(**records)
    members = state.members_of("brenner-family", rank=None)
    assert [x.rank for x in members] == ["boss", "lieutenant", "soldier", "soldier"]
    soldiers = [x.person_id for x in state.members_of("brenner-family", rank="soldier")]
    assert soldiers == sorted(soldiers)


def test_a_membership_may_name_a_pruned_person(records):
    records["memberships"] = (*records["memberships"],
                              m("m-ghost", "brenner-family", "p-404", "soldier"))
    assert any(x.person_id == "p-404"
               for x in WorldState(**records).members_of("brenner-family", rank="soldier"))


def test_a_membership_cannot_end_before_it_starts():
    with pytest.raises(ValueError, match="m-1"):
        m("m-1", "brenner-family", "p-sal", "boss", started=D(year=121, month=1, day=1),
          ended=D(year=120, month=1, day=1))

"""One world's records, checked together."""
import pytest

from kirby_campaign import EntityRef, Relation, Tenure, WorldDate, WorldState
from tests.conftest import organisation, person


def test_lookups_find_records_by_id(records):
    state = WorldState(**records)
    assert state.person("p-sal").name("English") == "Sal Brenner"
    assert state.organisation("the-coil").kind == "villain_org"
    assert state.polity("harbour-city").kind == "city_state"
    assert state.office("mayor").title == "Mayor"
    assert state.relation("r-grudge").kind == "grudge"
    assert state.event("e-pier").kind == "hit"
    assert state.has_person("p-ada") and not state.has_person("p-404")
    with pytest.raises(KeyError, match="person.*p-nobody"):
        state.person("p-nobody")


def test_who_holds_an_office_now(records):
    state = WorldState(**records)
    assert tuple(p.id for p in state.holders_of("mayor")) == ("p-mayor",)
    assert tuple(o.id for o in state.offices_held_by("p-mayor")) == ("mayor",)
    assert state.offices_held_by("p-sal") == ()


def test_a_closed_tenure_holds_nothing(records):
    records["tenures"] = (Tenure(id="t-old", world_id="w-1", office_id="mayor",
                                 person_id="p-mayor", started=None,
                                 ended=WorldDate(year=120, month=1, day=1), how="elected"),)
    assert WorldState(**records).holders_of("mayor") == ()


def test_the_same_id_twice_is_refused(records):
    records["people"] = (*records["people"], person("p-sal", "Another Sal"))
    with pytest.raises(ValueError, match="person.*p-sal"):
        WorldState(**records)


def test_a_person_and_an_organisation_cannot_share_an_id(records):
    records["people"] = (*records["people"], person("the-coil", "A Person Named Coil"))
    with pytest.raises(ValueError, match="the-coil"):
        WorldState(**records)


def test_a_record_from_another_world_is_refused(records):
    records["people"] = (*records["people"], person("p-x", "Visitor", world_id="w-2"))
    with pytest.raises(ValueError, match="w-2.*w-1|w-1.*w-2"):
        WorldState(**records)


def test_a_head_who_is_not_in_the_world_is_refused(records):
    records["organisations"] = (organisation("ghosts", "Ghosts", "gang", "p-ghost",
                                             ("p-ghost",), ()),)
    with pytest.raises(ValueError, match="p-ghost"):
        WorldState(**records)


def test_a_tenure_for_a_missing_person_is_refused(records):
    records["tenures"] = (Tenure(id="t-x", world_id="w-1", office_id="mayor",
                                 person_id="p-nobody", started=None, ended=None, how="elected"),)
    with pytest.raises(ValueError, match="p-nobody"):
        WorldState(**records)


def test_a_relation_with_a_missing_party_is_refused(records):
    records["relations"] = (Relation(id="r-x", world_id="w-1", kind="war",
                                     a=EntityRef(kind="polity", id="harbour-city"),
                                     b=EntityRef(kind="polity", id="atlantis"),
                                     since=None, until=None, cause_event_id=None),)
    with pytest.raises(ValueError, match="atlantis"):
        WorldState(**records)


def test_kin_and_members_may_name_people_the_world_no_longer_has(records):
    """brenner-family lists p-404 as a member: pruned by the source, kept."""
    assert "p-404" in WorldState(**records).organisation("brenner-family").member_ids

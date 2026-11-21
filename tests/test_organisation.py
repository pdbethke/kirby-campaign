"""Organisations that act in the world, and the edges between things."""
import pytest
from kirby_world import SourceRef

from kirby_campaign import EntityRef, Organisation, Rank, Relation, WorldDate


def _family_ref(external_id):
    return SourceRef(source="fms", world_id="w-1", kind="family", external_id=external_id)


def _rank(name, *, base=0.1, guards=0, archetype=None):
    return Rank(name=name, archetype_character_id=archetype, hit_failure_base=base, guards=guards)


LADDER = (_rank("boss", base=0.4, guards=3), _rank("lieutenant", base=0.2, guards=1),
          _rank("soldier"))


def _org(**over):
    fields = {"id": "the-coil", "world_id": "w-1", "name": "The Coil", "kind": "villain_org",
              "ranks": LADDER, "head_id": "p-coil", "heir_id": None,
              "territory": ("the-docks",), "influence": None, "wealth": None,
              "source_refs": (), "source_status": None}
    fields.update(over)
    return Organisation(**fields)


def test_an_organisation_may_be_backed_by_several_source_families():
    """One family per country for an organisation that crosses borders."""
    org = _org(source_refs=(_family_ref("41"), _family_ref("77")), source_status="present")
    assert len(org.source_refs) == 2


def test_the_same_source_family_twice_is_refused():
    with pytest.raises(ValueError, match="41"):
        _org(source_refs=(_family_ref("41"), _family_ref("41")), source_status="present")


def test_an_organisation_has_a_rank_ladder_highest_first():
    org = _org()
    assert org.rank_order("boss") == 0 and org.rank_order("soldier") == 2
    assert org.rank("boss").guards == 3


def test_rank_names_are_unique():
    with pytest.raises(ValueError, match="soldier"):
        _org(ranks=(_rank("soldier"), _rank("soldier")))


def test_an_organisation_needs_at_least_one_rank():
    with pytest.raises(ValueError, match="rank"):
        _org(ranks=())


def test_a_rank_failure_base_is_a_probability():
    with pytest.raises(ValueError, match="hit_failure_base"):
        _rank("boss", base=1.5)


def test_guards_cannot_be_negative():
    with pytest.raises(ValueError, match="guards"):
        _rank("boss", guards=-1)


def test_an_unknown_rank_is_a_key_error_naming_the_ladder():
    with pytest.raises(KeyError, match="capo.*boss|boss.*capo"):
        _org().rank("capo")


def test_an_unknown_organisation_kind_is_refused():
    with pytest.raises(ValueError, match="guild"):
        _org(kind="guild")


def test_an_entity_ref_names_a_known_kind():
    assert EntityRef(kind="person", id="p-sal") == EntityRef(kind="person", id="p-sal")
    with pytest.raises(ValueError, match="ship"):
        EntityRef(kind="ship", id="x")


def _relation(**over):
    fields = {"id": "r-grudge", "world_id": "w-1", "kind": "grudge",
              "a": EntityRef(kind="organisation", id="talley-outfit"),
              "b": EntityRef(kind="organisation", id="brenner-family"),
              "since": WorldDate(year=118, month=4, day=1), "until": None,
              "cause_event_id": None, "source_ref": None, "source_status": None}
    fields.update(over)
    return Relation(**fields)


def test_a_relation_joins_two_different_things():
    assert _relation().kind == "grudge"
    same = EntityRef(kind="organisation", id="talley-outfit")
    with pytest.raises(ValueError, match="itself"):
        _relation(b=same)


def test_a_relation_cannot_end_before_it_began():
    with pytest.raises(ValueError, match="r-grudge"):
        _relation(until=WorldDate(year=117, month=1, day=1))


def test_an_unknown_relation_kind_is_refused():
    with pytest.raises(ValueError, match="romance"):
        _relation(kind="romance")

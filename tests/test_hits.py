"""Hits: who is sent, who guards, how a hit resolves without a fight, and what
follows from it."""
from dataclasses import replace

import pytest

from kirby_campaign import ChainStep, EntityRef, WorldDate, WorldState, select_hit_squad
from tests.conftest import membership


def hit(target, actor="talley-outfit"):
    return ChainStep(id="s-1", actor_org_id=actor, action="hit",
                     target=EntityRef(kind="person", id=target), motive_relation_id="r-grudge",
                     motive_event_id=None, motive_step_id=None, status="planned")


def kill(records, *ids):
    dead = WorldDate(year=121, month=1, day=1)
    records["people"] = tuple(replace(p, died=dead) if p.id in ids else p
                              for p in records["people"])


# ── select_hit_squad ──────────────────────────────────────────────────────

def test_a_boss_is_guarded_and_the_squad_matches_the_guard(records):
    squad = select_hit_squad(hit("p-sal"), state=WorldState(**records))
    assert squad.defenders == ("p-sal", "p-vic", "p-b1")
    assert squad.attackers == ("p-t1", "p-t2", "p-tlt")
    assert (squad.attacker_org_id, squad.defender_org_id) == ("talley-outfit", "brenner-family")


def test_soldiers_do_the_hits_before_lieutenants(records):
    squad = select_hit_squad(hit("p-b1"), state=WorldState(**records))
    assert squad.defenders == ("p-b1",) and squad.attackers == ("p-t1",)


def test_an_outsider_has_no_guards(records):
    squad = select_hit_squad(hit("p-mayor"), state=WorldState(**records))
    assert squad.defenders == ("p-mayor",) and squad.defender_org_id is None
    assert squad.attackers == ("p-t1",)


def test_a_short_handed_crew_sends_everyone_but_the_boss(records):
    records["memberships"] = tuple(m for m in records["memberships"]
                                   if m.person_id not in ("p-t2", "p-tlt"))
    assert select_hit_squad(hit("p-sal"), state=WorldState(**records)).attackers == ("p-t1",)


def test_the_boss_goes_himself_only_when_nobody_else_is_left(records):
    kill(records, "p-t1", "p-t2", "p-tlt")
    assert select_hit_squad(hit("p-sal"), state=WorldState(**records)).attackers == ("p-rook",)


def test_a_crew_with_no_one_living_sends_nobody(records):
    kill(records, "p-t1", "p-t2", "p-tlt", "p-rook")
    assert select_hit_squad(hit("p-sal"), state=WorldState(**records)).attackers == ()


def test_someone_in_both_organisations_never_hits_their_own(records):
    """Nico is a Brenner soldier who also runs with the Talleys. He is not sent
    against the Brenners, and he can be one of their guards."""
    records["memberships"] = (*records["memberships"],
                              membership("talley-outfit", "p-b2", "soldier"))
    squad = select_hit_squad(hit("p-sal"), state=WorldState(**records))
    assert "p-b2" not in squad.attackers
    assert not set(squad.attackers) & set(squad.defenders)


def test_the_dead_and_the_gone_are_never_picked(records):
    from kirby_world import SourceRef
    kill(records, "p-vic")
    ref = SourceRef(source="fms", world_id="w-1", kind="person", external_id="t1")
    records["people"] = tuple(replace(p, source_ref=ref, source_status="gone")
                              if p.id == "p-t1" else p for p in records["people"])
    squad = select_hit_squad(hit("p-sal"), state=WorldState(**records))
    assert "p-vic" not in squad.defenders and "p-t1" not in squad.attackers
    assert squad.defenders == ("p-sal", "p-b1", "p-b2")


def test_a_squad_is_picked_only_for_a_hit(records):
    turf = ChainStep(id="s-1", actor_org_id="talley-outfit", action="claim_turf",
                     target=EntityRef(kind="locale", id="old-quarter"),
                     motive_relation_id="r-grudge", motive_event_id=None, motive_step_id=None,
                     status="planned")
    with pytest.raises(ValueError, match="claim_turf"):
        select_hit_squad(turf, state=WorldState(**records))


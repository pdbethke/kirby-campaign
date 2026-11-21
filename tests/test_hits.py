"""Hits: who is sent, who guards, how a hit resolves without a fight, and what
follows from it."""
from dataclasses import replace

import pytest

from kirby_campaign import (
    ChainStep,
    EntityRef,
    HitResult,
    WorldDate,
    WorldState,
    consequences_of_hit,
    failure_chance,
    resolve_hit_by_odds,
    select_hit_squad,
)
from tests.conftest import make_limits, membership


def hit(target, actor="talley-outfit"):
    return ChainStep(id="s-1", actor_org_id=actor, action="hit",
                     target=EntityRef(kind="person", id=target), motive_relation_id="r-grudge",
                     motive_event_id=None, motive_step_id=None, status="planned")


def squad_for(state, target):
    return select_hit_squad(hit(target), state=state)


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



# ── failure_chance / resolve_hit_by_odds (the fallback) ──────────────────────



def with_influence(records, org_id, value):
    records["organisations"] = tuple(replace(o, influence=value) if o.id == org_id else o
                                     for o in records["organisations"])


def test_even_strength_gives_the_rank_base(records):
    assert failure_chance(hit("p-sal"), state=WorldState(**records),
                          limits=make_limits()) == pytest.approx(0.4)


def test_a_stronger_attacker_roughly_halves_it(records):
    with_influence(records, "talley-outfit", 100.0)
    assert failure_chance(hit("p-sal"), state=WorldState(**records),
                          limits=make_limits()) == pytest.approx(0.4 * 2 * 50 / 150)


def test_the_chance_is_capped(records):
    with_influence(records, "talley-outfit", 1.0)
    assert failure_chance(hit("p-coil"), state=WorldState(**records),
                          limits=make_limits()) == pytest.approx(0.95)


def test_an_outsider_uses_the_world_base(records):
    assert failure_chance(hit("p-mayor"), state=WorldState(**records),
                          limits=make_limits(outsider_failure_base=0.07)) == pytest.approx(0.07)


@pytest.mark.parametrize("value", [None, 0.0])
def test_a_side_without_strength_is_refused_by_name(records, value):
    with_influence(records, "talley-outfit", value)
    with pytest.raises(ValueError, match="talley-outfit"):
        failure_chance(hit("p-sal"), state=WorldState(**records), limits=make_limits())


def test_a_roll_under_the_chance_fails_and_may_leak(records):
    state, limits = WorldState(**records), make_limits(leak_chance=0.3)
    leaked = resolve_hit_by_odds(hit("p-sal"), squad_for(state, "p-sal"), state=state,
                                 limits=limits, roll=0.1, leak_roll=0.2)
    assert (leaked.target_killed, leaked.casualties, leaked.survivors_who_saw,
            leaked.leaked, leaked.how) == (False, (), ("p-sal",), True, "odds")
    quiet = resolve_hit_by_odds(hit("p-sal"), squad_for(state, "p-sal"), state=state,
                                limits=limits, roll=0.1, leak_roll=0.9)
    assert not quiet.leaked


def test_a_roll_over_the_chance_kills(records):
    state = WorldState(**records)
    r = resolve_hit_by_odds(hit("p-sal"), squad_for(state, "p-sal"), state=state,
                            limits=make_limits(), roll=0.5, leak_roll=0.0)
    assert (r.target_killed, r.casualties, r.leaked) == (True, ("p-sal",), False)


@pytest.mark.parametrize("roll", [-0.1, 1.0])
def test_rolls_are_in_the_unit_interval(records, roll):
    with pytest.raises(ValueError, match="roll"):
        state = WorldState(**records)
        resolve_hit_by_odds(hit("p-sal"), squad_for(state, "p-sal"), state=state,
                            limits=make_limits(), roll=roll, leak_roll=0.5)


# ── consequences_of_hit ──────────────────────────────────────────────────────

DAY = WorldDate(year=121, month=10, day=9)


def outcome(records, result, target="p-sal"):
    state = WorldState(**records)
    step = hit(target)
    squad = select_hit_squad(step, state=state)
    return consequences_of_hit(step, squad, result, state=state, chain_id="ch-1", date=DAY,
                               event_id="e-hit", relation_id="r-new", language="English")


def result(**over):
    fields = {"target_killed": False, "casualties": (), "survivors_who_saw": ("p-sal",),
              "leaked": False, "how": "fight"}
    fields.update(over)
    return HitResult(**fields)


def test_a_failed_hit_leaves_a_grudge_and_a_street_story(records):
    c = outcome(records, result(casualties=("p-t1",)))
    assert c.deaths == ("p-t1",)
    assert c.event.kind == "failed_hit" and c.event.cause.ref == "ch-1"
    assert "Sal Brenner" in c.event.truth and "The Talley Outfit" in c.event.truth
    assert c.grudge is not None
    assert (c.grudge.a.id, c.grudge.b.id, c.grudge.kind) == (
        "brenner-family", "talley-outfit", "grudge")
    assert c.grudge.cause_event_id == "e-hit" and c.grudge.since == DAY


def test_a_successful_hit_lists_every_casualty(records):
    c = outcome(records, result(target_killed=True, casualties=("p-sal", "p-vic", "p-t2"),
                                survivors_who_saw=()))
    assert c.event.kind == "hit"
    assert set(c.deaths) == {"p-sal", "p-vic", "p-t2"}
    assert c.grudge is None


def test_a_leak_names_the_attacker_on_the_street(records):
    c = outcome(records, result(leaked=True))
    assert "The Talley Outfit" in c.event.public_account


def test_without_a_leak_the_street_does_not_know_who(records):
    c = outcome(records, result(leaked=False))
    assert "Talley" not in c.event.public_account


def test_a_target_cannot_both_die_and_survive(records):
    with pytest.raises(ValueError, match="p-sal"):
        outcome(records, result(target_killed=True, casualties=("p-sal",),
                                survivors_who_saw=("p-sal",)))


def test_killed_must_agree_with_the_casualties(records):
    with pytest.raises(ValueError, match="target_killed"):
        outcome(records, result(target_killed=True, casualties=(), survivors_who_saw=()))


def test_a_casualty_must_have_been_there(records):
    with pytest.raises(ValueError, match="p-mayor"):
        outcome(records, result(casualties=("p-mayor",)))


def test_an_outsider_has_no_one_to_hold_a_grudge(records):
    c = outcome(records, result(survivors_who_saw=("p-mayor",)), target="p-mayor")
    assert c.grudge is None


# ── final-review fixes ─────────────────────────────────────────────────────

def test_a_purge_sends_the_crew_against_its_own_man(records):
    """An organisation may whack its own member. He faces his own crew alone,
    and nobody is left to hold a grudge against the outfit."""
    state = WorldState(**records)
    squad = select_hit_squad(hit("p-t1"), state=state)
    assert squad.defenders == ("p-t1",)
    assert squad.defender_org_id == "talley-outfit"
    assert squad.attackers and "p-t1" not in squad.attackers
    c = consequences_of_hit(hit("p-t1"), squad, result(survivors_who_saw=("p-t1",)),
                            state=state, chain_id="ch-1", date=DAY, event_id="e-hit",
                            relation_id="r-new", language="English")
    assert c.grudge is None


def test_a_purge_of_someone_who_also_runs_with_another_crew_is_still_a_purge(records):
    records["memberships"] = (*records["memberships"], membership("the-coil", "p-t1", "agent"))
    squad = select_hit_squad(hit("p-t1"), state=WorldState(**records))
    assert squad.defender_org_id == "talley-outfit" and squad.attackers


def test_a_crew_with_nobody_to_send_cannot_resolve_a_hit(records):
    kill(records, "p-t1", "p-t2", "p-tlt", "p-rook")
    state = WorldState(**records)
    squad = select_hit_squad(hit("p-sal"), state=state)
    with pytest.raises(ValueError, match="talley-outfit"):
        resolve_hit_by_odds(hit("p-sal"), squad, state=state, limits=make_limits(),
                            roll=0.5, leak_roll=0.5)
    with pytest.raises(ValueError, match="talley-outfit"):
        consequences_of_hit(hit("p-sal"), squad,
                            result(target_killed=True, casualties=("p-sal",),
                                   survivors_who_saw=()),
                            state=state, chain_id="ch-1", date=DAY, event_id="e-hit",
                            relation_id="r-new", language="English")


def test_an_attacker_without_strength_is_refused_even_against_an_outsider(records):
    with_influence(records, "talley-outfit", 0.0)
    with pytest.raises(ValueError, match="talley-outfit"):
        failure_chance(hit("p-mayor"), state=WorldState(**records), limits=make_limits())


@pytest.mark.parametrize("bad, match", [
    ({"survivors_who_saw": ("p-coil",)}, "p-coil"),
    ({"casualties": ("p-vic",), "survivors_who_saw": ("p-sal", "p-vic")}, "p-vic"),
    ({"casualties": ("p-t1", "p-t1")}, "p-t1"),
])
def test_a_contradictory_result_is_refused(records, bad, match):
    with pytest.raises(ValueError, match=match):
        outcome(records, result(**bad))


def test_the_step_must_match_its_squad(records):
    state = WorldState(**records)
    squad = select_hit_squad(hit("p-sal"), state=state)
    with pytest.raises(ValueError, match="p-rook"):
        consequences_of_hit(hit("p-rook"), squad, result(), state=state, chain_id="ch-1",
                            date=DAY, event_id="e-hit", relation_id="r-new",
                            language="English")

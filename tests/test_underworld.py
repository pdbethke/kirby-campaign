"""The underworld runs unattended, inside limits the GM sets for each world."""
import pytest

from kirby_campaign import (
    Chain,
    ChainStep,
    EntityRef,
    Organisation,
    WorldState,
    validate_step,
)
from tests.conftest import make_limits, person

LIMITS = make_limits()


def _hit(target, *, actor="talley-outfit", relation="r-grudge", event=None, prior=None,
         id="s-1"):
    return ChainStep(id=id, actor_org_id=actor, action="hit",
                     target=EntityRef(kind="person", id=target),
                     motive_relation_id=relation if not (event or prior) else None,
                     motive_event_id=event, motive_step_id=prior, status="planned")


def _verdict(step, records, *, limits=LIMITS, sent=0):
    chain = Chain(id="ch-test", world_id="w-1", steps=(step,))
    return validate_step(step, chain=chain, state=WorldState(**records), limits=limits,
                         hits_sent_this_week=sent)


def test_a_world_without_limits_runs_no_underworld(records):
    v = _verdict(_hit("p-sal"), records, limits=None)
    assert v.outcome == "drop" and "limits" in v.reason


def test_a_hit_between_npcs_is_sent(records):
    assert _verdict(_hit("p-sal"), records).outcome == "send"


def test_a_missing_actor_drops_the_step(records):
    assert _verdict(_hit("p-sal", actor="ghosts"), records).outcome == "drop"


def test_a_step_citing_a_cause_the_world_lacks_is_dropped(records):
    v = _verdict(_hit("p-sal", relation="r-404"), records)
    assert v.outcome == "drop" and "r-404" in v.reason


def test_a_hit_on_the_dead_or_the_gone_is_dropped(records):
    assert _verdict(_hit("p-dead"), records).outcome == "drop"
    assert _verdict(_hit("p-404"), records).outcome == "drop"


def test_a_hit_on_someone_holding_a_protected_office_is_dropped(records):
    v = _verdict(_hit("p-mayor"), records)
    assert v.outcome == "drop" and "mayor" in v.reason


def test_a_hit_on_a_named_protected_person_is_dropped(records):
    v = _verdict(_hit("p-coil"), records)
    assert v.outcome == "drop" and "p-coil" in v.reason


def test_a_hit_on_a_player_character_goes_to_their_session(records):
    v = _verdict(_hit("p-ada"), records, sent=99)
    assert (v.outcome, v.campaign_id) == ("route_to_session", "c-1")


def test_hits_over_the_weekly_cap_wait(records):
    assert _verdict(_hit("p-sal"), records, sent=2).outcome == "defer"


def test_a_step_has_exactly_one_motive():
    with pytest.raises(ValueError, match="motive"):
        ChainStep(id="s-1", actor_org_id="talley-outfit", action="hit",
                  target=EntityRef(kind="person", id="p-sal"), motive_relation_id="r-grudge",
                  motive_event_id="e-pier", motive_step_id=None, status="planned")


def test_a_hit_targets_a_person_and_a_turf_claim_a_locale():
    with pytest.raises(ValueError, match="hit"):
        ChainStep(id="s-1", actor_org_id="talley-outfit", action="hit",
                  target=EntityRef(kind="locale", id="the-docks"),
                  motive_relation_id="r-grudge", motive_event_id=None, motive_step_id=None,
                  status="planned")


def test_a_chain_must_start_from_a_cause():
    with pytest.raises(ValueError, match="s-0"):
        Chain(id="ch-1", world_id="w-1", steps=(_hit("p-sal", prior="s-0"),))


def test_a_later_step_may_answer_an_earlier_one():
    chain = Chain(id="ch-1", world_id="w-1", steps=(
        _hit("p-sal", id="s-1"),
        _hit("p-rook", actor="brenner-family", prior="s-1", id="s-2"),
    ))
    assert chain.steps[1].motive_step_id == "s-1"
    with pytest.raises(ValueError, match="s-9"):
        Chain(id="ch-1", world_id="w-1", steps=(_hit("p-sal", id="s-1"),
                                                _hit("p-rook", prior="s-9", id="s-2")))


def test_limits_cannot_be_negative():
    with pytest.raises(ValueError, match="max_hits_per_week"):
        make_limits(max_hits_per_week=-1)


def test_a_gone_person_is_dropped(records):
    from kirby_world import SourceRef
    ref = SourceRef(source="fms", world_id="w-1", kind="person", external_id="7")
    records["people"] = (*records["people"], person("p-gone", "Faded", source_ref=ref,
                                                    source_status="gone"))
    assert _verdict(_hit("p-gone"), records).outcome == "drop"


def test_a_turf_claim_is_sent_and_left_to_the_atlas(records):
    """Turf targets are locales, which WorldState does not hold; the caller
    with the Atlas checks them. The weekly cap counts hits only."""
    step = ChainStep(id="s-1", actor_org_id="talley-outfit", action="claim_turf",
                     target=EntityRef(kind="locale", id="old-quarter"),
                     motive_relation_id="r-grudge", motive_event_id=None,
                     motive_step_id=None, status="planned")
    assert _verdict(step, records, sent=99).outcome == "send"


# ── final-review fixes ─────────────────────────────────────────────────────

def test_limits_from_another_world_are_a_caller_error(records):
    other = make_limits(world_id="w-2")
    with pytest.raises(ValueError, match="w-2.*w-1|w-1.*w-2"):
        _verdict(_hit("p-sal"), records, limits=other)


def test_an_organisation_the_source_reports_gone_does_not_act(records):
    from kirby_world import SourceRef
    ref = SourceRef(source="fms", world_id="w-1", kind="family", external_id="9")
    talleys = records["organisations"][1]
    records["organisations"] = (records["organisations"][0],
                                Organisation(**{**talleys.__dict__, "source_refs": (ref,),
                                                "source_status": "gone"}),
                                records["organisations"][2])
    v = _verdict(_hit("p-sal"), records)
    assert v.outcome == "drop" and "talley-outfit" in v.reason


def _answering_chain(first_status):
    first = ChainStep(id="s-1", actor_org_id="talley-outfit", action="hit",
                      target=EntityRef(kind="person", id="p-dead"),
                      motive_relation_id="r-grudge", motive_event_id=None,
                      motive_step_id=None, status=first_status)
    answer = _hit("p-rook", actor="brenner-family", prior="s-1", id="s-2")
    return Chain(id="ch-1", world_id="w-1", steps=(first, answer)), answer


@pytest.mark.parametrize("status, outcome", [
    ("done", "send"),
    ("planned", "defer"), ("deferred", "defer"), ("waiting_on_session", "defer"),
    ("dropped", "drop"), ("failed", "drop"),
])
def test_a_step_answers_only_an_earlier_step_that_happened(records, status, outcome):
    chain, answer = _answering_chain(status)
    v = validate_step(answer, chain=chain, state=WorldState(**records), limits=LIMITS,
                      hits_sent_this_week=0)
    assert v.outcome == outcome, v.reason


def test_the_step_must_belong_to_the_chain(records):
    chain, _ = _answering_chain("done")
    with pytest.raises(ValueError, match="s-other"):
        validate_step(_hit("p-sal", id="s-other"), chain=chain, state=WorldState(**records),
                      limits=LIMITS, hits_sent_this_week=0)


def test_a_hit_on_a_protected_target_is_dropped_even_while_its_cause_is_pending(records):
    first = ChainStep(id="s-1", actor_org_id="talley-outfit", action="hit",
                      target=EntityRef(kind="person", id="p-sal"),
                      motive_relation_id="r-grudge", motive_event_id=None,
                      motive_step_id=None, status="planned")
    answer = _hit("p-mayor", actor="brenner-family", prior="s-1", id="s-2")
    chain = Chain(id="ch-1", world_id="w-1", steps=(first, answer))
    v = validate_step(answer, chain=chain, state=WorldState(**records), limits=LIMITS,
                      hits_sent_this_week=0)
    assert v.outcome == "drop" and "mayor" in v.reason


def test_a_turf_claim_also_waits_for_the_step_it_answers(records):
    first = ChainStep(id="s-1", actor_org_id="talley-outfit", action="hit",
                      target=EntityRef(kind="person", id="p-sal"),
                      motive_relation_id="r-grudge", motive_event_id=None,
                      motive_step_id=None, status="planned")
    claim = ChainStep(id="s-2", actor_org_id="talley-outfit", action="claim_turf",
                      target=EntityRef(kind="locale", id="old-quarter"),
                      motive_relation_id=None, motive_event_id=None, motive_step_id="s-1",
                      status="planned")
    chain = Chain(id="ch-1", world_id="w-1", steps=(first, claim))
    v = validate_step(claim, chain=chain, state=WorldState(**records), limits=LIMITS,
                      hits_sent_this_week=0)
    assert v.outcome == "defer"


def test_an_untouchable_player_character_is_left_alone(records):
    limits = make_limits(protected_people={"p-ada": "untouchable"})
    assert _verdict(_hit("p-ada"), records, limits=limits).outcome == "drop"


def test_an_encounters_only_player_character_still_gets_the_encounter(records):
    limits = make_limits(protected_people={"p-ada": "encounters_only"})
    v = _verdict(_hit("p-ada"), records, limits=limits)
    assert (v.outcome, v.campaign_id) == ("route_to_session", "c-1")


def test_encounters_only_is_for_player_characters(records):
    limits = make_limits(protected_people={"p-sal": "encounters_only"})
    with pytest.raises(ValueError, match="p-sal"):
        _verdict(_hit("p-sal"), records, limits=limits)


def test_an_office_can_only_be_untouchable():
    with pytest.raises(ValueError, match="mayor"):
        make_limits(protected_offices={"mayor": "encounters_only"})


def test_an_unknown_protection_mode_is_refused():
    with pytest.raises(ValueError, match="bulletproof"):
        make_limits(protected_people={"p-sal": "bulletproof"})


@pytest.mark.parametrize("field", ["outsider_failure_base", "leak_chance"])
def test_hit_chances_are_probabilities(field):
    with pytest.raises(ValueError, match=field):
        make_limits(**{field: 1.2})

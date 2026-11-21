"""The world's timeline, its laws, and the two accounts of a secret event."""
import pytest

from kirby_campaign import (
    PUBLIC,
    TRUTH,
    Cause,
    EntityRef,
    Law,
    WorldDate,
    WorldEvent,
    account_at,
)

D = WorldDate


def _event(**over):
    fields = {"id": "e-pier", "world_id": "w-1", "date": D(year=121, month=10, day=9),
              "kind": "hit", "actors": ("p-rook", "p-sal"), "places": ("the-docks",),
              "groups": (EntityRef(kind="organisation", id="talley-outfit"),),
              "truth": "Rook Talley killed Sal Brenner on the Marrow Street pier.",
              "public_account": "A body was pulled from the river by the pier.",
              "cause": Cause(kind="chain", ref="ch-1"), "source_ref": None}
    fields.update(over)
    return WorldEvent(**fields)


def test_a_secret_event_shows_the_street_its_public_account():
    e = _event()
    assert account_at(e, PUBLIC) == "A body was pulled from the river by the pier."
    assert account_at(e, TRUTH) == "Rook Talley killed Sal Brenner on the Marrow Street pier."


def test_a_public_event_shows_everyone_the_truth():
    e = _event(public_account=None, cause=Cause(kind="source", ref=None))
    assert account_at(e, PUBLIC) == account_at(e, TRUTH)


def test_a_third_tier_is_refused():
    with pytest.raises(ValueError, match="2"):
        account_at(_event(), 2)


def test_a_chain_or_session_cause_names_what_caused_it():
    with pytest.raises(ValueError, match="chain"):
        Cause(kind="chain", ref=None)
    with pytest.raises(ValueError, match="session"):
        Cause(kind="session", ref=None)
    with pytest.raises(ValueError, match="source"):
        Cause(kind="source", ref="x")


def test_an_event_needs_a_kind_and_a_truth():
    with pytest.raises(ValueError, match="kind"):
        _event(kind=" ")
    with pytest.raises(ValueError, match="truth"):
        _event(truth="")


def _law(**over):
    fields = {"id": "l-1", "world_id": "w-1", "polity_id": "harbour-city",
              "title": "The Waterfront Curfew Act", "text": "No one on the piers after dark.",
              "enacted": D(year=121, month=11, day=1), "repealed": None,
              "cause_event_id": "e-pier", "origin": "drafted", "status": "in_force"}
    fields.update(over)
    return Law(**fields)


def test_a_drafted_law_is_in_force_until_struck():
    assert _law().status == "in_force"
    assert _law(status="struck").status == "struck"
    with pytest.raises(ValueError, match="pending"):
        _law(status="pending")


def test_a_law_cannot_be_repealed_before_it_was_enacted():
    with pytest.raises(ValueError, match="l-1"):
        _law(repealed=D(year=121, month=1, day=1))

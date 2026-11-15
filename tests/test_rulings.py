"""Ruling records (a campaign's rows) become the engine's rulings for one fight."""
import pytest
from kirby_combat.rulings import Ruling

from kirby_campaign import RulingRecord, rulings_in_fight


def rec(campaign="c1", char="ravel", power=None, fact="no_lungs", s="He has no lungs."):
    return RulingRecord(campaign_id=campaign, character_id=char, power_id=power,
                        fact=fact, sentence=s, author_id="gm")


def test_other_campaigns_record_contributes_nothing():
    assert rulings_in_fight([rec(campaign="c2")], campaign_id="c1", character_id="ravel") == ()


def test_other_characters_record_contributes_nothing():
    assert rulings_in_fight([rec(char="bokor")], campaign_id="c1", character_id="ravel") == ()


def test_body_record_becomes_ruling():
    out = rulings_in_fight([rec()], campaign_id="c1", character_id="ravel")
    assert out == (Ruling(None, "no_lungs", "He has no lungs."),)


def test_power_record_becomes_ruling():
    out = rulings_in_fight([rec(power="P1", fact="breath", s="By breath.")],
                           campaign_id="c1", character_id="ravel")
    assert out == (Ruling("P1", "breath", "By breath."),)


def test_unknown_fact_raises():
    with pytest.raises(ValueError):
        rulings_in_fight([rec(fact="no_soul")], campaign_id="c1", character_id="ravel")
    with pytest.raises(ValueError):
        rulings_in_fight([rec(power="P1", fact="no_lungs")], campaign_id="c1", character_id="ravel")


def test_order_is_stable_by_power_then_fact():
    recs = [rec(power="P2", fact="skin"), rec(fact="no_skin"), rec(power="P1", fact="breath"),
            rec(fact="no_lungs")]
    out = rulings_in_fight(recs, campaign_id="c1", character_id="ravel")
    assert [(r.power_id, r.fact) for r in out] == [
        (None, "no_lungs"), (None, "no_skin"), ("P1", "breath"), ("P2", "skin")]
    assert out == rulings_in_fight(reversed(recs), campaign_id="c1", character_id="ravel")

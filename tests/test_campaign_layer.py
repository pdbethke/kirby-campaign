"""What one campaign owns on a shared world: its PCs, what its players know,
and the encounters waiting for its next session."""
import pytest

from kirby_campaign import CampaignLayer, EncounterHook, WorldState, visible_account

STREET = "A body was pulled from the river by the pier."
TRUTH_TEXT = "Rook Talley killed Old Man Brenner on the pier."


def _layer(campaign_id, *, pc_ids=(), unlocks=frozenset(), hooks=(), world_id="w-1"):
    return CampaignLayer(campaign_id=campaign_id, world_id=world_id, pc_ids=pc_ids,
                         unlocks=unlocks, hooks=hooks)


def test_two_campaigns_share_a_world_and_know_different_things(records):
    state = WorldState(**records)
    first = _layer("c-1", pc_ids=("p-ada",), unlocks=frozenset({("player-1", "e-pier")}))
    second = _layer("c-2")
    assert visible_account(state, first, "player-1", "e-pier") == TRUTH_TEXT
    assert visible_account(state, first, "player-2", "e-pier") == STREET
    assert visible_account(state, second, "player-3", "e-pier") == STREET


def test_a_layer_for_another_world_is_refused(records):
    with pytest.raises(ValueError, match="w-2"):
        visible_account(WorldState(**records), _layer("c-9", world_id="w-2"), "p", "e-pier")


def test_a_layer_pc_must_be_this_campaigns_player_character(records):
    state = WorldState(**records)
    with pytest.raises(ValueError, match="p-sal"):
        visible_account(state, _layer("c-1", pc_ids=("p-sal",)), "player-1", "e-pier")
    with pytest.raises(ValueError, match="p-ada"):
        visible_account(state, _layer("c-2", pc_ids=("p-ada",)), "player-1", "e-pier")


def test_a_hook_belongs_to_its_layers_campaign():
    hook = EncounterHook(id="h-1", campaign_id="c-2", world_id="w-1", chain_id="ch-1",
                         step_id="s-2", pc_id="p-ada")
    with pytest.raises(ValueError, match="h-1"):
        _layer("c-1", hooks=(hook,))

"""What one campaign owns on a world that several campaigns can share.

The world's records belong to the world. A campaign adds only its own: its
player characters, which of its players have unlocked the truth of which
events, and the encounters waiting for its next session (an underworld
chain that reached one of its PCs).
"""
from __future__ import annotations

from dataclasses import dataclass

from kirby_campaign._checks import require_text
from kirby_campaign.timeline import PUBLIC, TRUTH, account_at
from kirby_campaign.world_state import WorldState


@dataclass(frozen=True, kw_only=True)
class EncounterHook:
    """A chain step that reached a player character: a fight for the next
    session of that character's campaign. The chain waits for its outcome."""

    id: str
    campaign_id: str
    world_id: str
    chain_id: str
    step_id: str
    pc_id: str

    def __post_init__(self) -> None:
        require_text(f"encounter hook {self.id!r}", id=self.id, campaign_id=self.campaign_id,
                     world_id=self.world_id, chain_id=self.chain_id, step_id=self.step_id,
                     pc_id=self.pc_id)


@dataclass(frozen=True, kw_only=True)
class CampaignLayer:
    campaign_id: str
    world_id: str
    pc_ids: tuple[str, ...]
    #: (player id, event id) pairs: that player reads the event's truth.
    unlocks: frozenset[tuple[str, str]]
    hooks: tuple[EncounterHook, ...]

    def __post_init__(self) -> None:
        owner = f"campaign {self.campaign_id!r}"
        require_text(owner, campaign_id=self.campaign_id, world_id=self.world_id)
        for hook in self.hooks:
            if (hook.campaign_id, hook.world_id) != (self.campaign_id, self.world_id):
                raise ValueError(
                    f"{owner}: encounter hook {hook.id!r} belongs to campaign "
                    f"{hook.campaign_id!r} in world {hook.world_id!r}"
                )


def visible_account(state: WorldState, layer: CampaignLayer, player_id: str, event_id: str) -> str:
    """The account of an event one of this campaign's players reads."""
    if layer.world_id != state.world_id:
        raise ValueError(
            f"campaign {layer.campaign_id!r} is on world {layer.world_id!r}, not {state.world_id!r}"
        )
    for pc_id in layer.pc_ids:
        pc = state.person(pc_id) if state.has_person(pc_id) else None
        if pc is None or not pc.pc or pc.campaign_id != layer.campaign_id:
            raise ValueError(
                f"campaign {layer.campaign_id!r}: {pc_id!r} is not one of its player characters"
            )
    tier = TRUTH if (player_id, event_id) in layer.unlocks else PUBLIC
    return account_at(state.event(event_id), tier)

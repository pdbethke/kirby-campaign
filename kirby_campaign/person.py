"""People: a world identity.

A Person is who someone is in the world: names, family, polity, the roles
they hold. A HERO build is something else (a Character, imported from HDC);
a Person may link to one through ``character_id``. A person with no build
lives in the world and the timeline but cannot fight until the GM attaches
one. Kirby never generates characters.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from kirby_world import SourceRef, check_source_status

from kirby_campaign._checks import require_order, require_text
from kirby_campaign.world_date import WorldDate


@dataclass(frozen=True, kw_only=True)
class Kin:
    """Family ties, as person ids. These may name people the world no longer
    holds: a source can prune the long dead, and their ids stay behind."""

    spouse_ids: tuple[str, ...]
    parent_ids: tuple[str, ...]
    child_ids: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class Person:
    id: str
    world_id: str
    #: Language -> name. No default language: ask for one with ``name()``.
    names: Mapping[str, str]
    gender: str | None
    born: WorldDate | None
    died: WorldDate | None
    polity_id: str | None
    culture: str | None
    religion: str | None
    traits: tuple[str, ...]
    #: The source's own ratings (a simulator's 0-100 charisma, say). Not HERO
    #: characteristics; those come from a build.
    skills: Mapping[str, float]
    kin: Kin
    character_id: str | None
    #: A player character. PCs exist only in Kirby, never in a source, and
    #: belong to one campaign.
    pc: bool
    campaign_id: str | None
    source_ref: SourceRef | None
    source_status: str | None

    def __post_init__(self) -> None:
        owner = f"person {self.id!r}"
        require_text(owner, id=self.id, world_id=self.world_id)
        if not self.names:
            raise ValueError(f"{owner}: names needs at least one language")
        require_order(owner, "born", self.born, "died", self.died)
        if self.pc:
            if self.campaign_id is None:
                raise ValueError(f"{owner}: a player character needs a campaign_id")
            if self.source_ref is not None:
                raise ValueError(f"{owner}: a player character exists only in Kirby, not in a source")
        elif self.campaign_id is not None:
            raise ValueError(f"{owner}: campaign_id is only for player characters")
        for relation in ("spouse_ids", "parent_ids", "child_ids"):
            if self.id in getattr(self.kin, relation):
                raise ValueError(f"{owner} is listed in their own {relation}")
        check_source_status(owner, self.source_ref is not None, self.source_status)
        object.__setattr__(self, "names", MappingProxyType(dict(self.names)))
        object.__setattr__(self, "skills", MappingProxyType(dict(self.skills)))

    @property
    def alive(self) -> bool:
        return self.died is None

    def name(self, language: str) -> str:
        try:
            return self.names[language]
        except KeyError:
            raise KeyError(
                f"person {self.id!r} has no {language} name (has: {', '.join(sorted(self.names))})"
            ) from None

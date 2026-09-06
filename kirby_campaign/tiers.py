"""The two-tier merge — a library definition under a campaign instance.

THE PATTERN, FROM THE ENTITY SPEC (2026-05-29, §2). Every campaign entity
exists in two tiers:

* a **definition** (``*_def``) --- tenant-scoped, reusable, the authored or
  sourcebook canon. One row per thing that exists in the library.
* an **instance** (``*_instance``) --- campaign-scoped, a THIN overlay: a
  reference to its definition, plus nullable override columns where NULL
  means inherit, plus instance-only state that has no definitional
  counterpart.

The rule is ``COALESCE(instance.col, definition.col)`` per override column,
and the instance's own value for instance-only state. Definitions are never
copied into instances, so editing a definition is visible in every campaign
that has not overridden that field --- which is the point: fix a villain
team's roster once and every campaign using it is fixed.

WHY THIS IS A RULE AND NOT A QUERY. It reads like SQL, and in kirby-api it
is SQL (``teams/services/effective.py``). But what it decides is *what a
thing actually is right now*, which every consumer must agree on --- and
the moment a second consumer computes it, a divergence is a silent wrong
answer rather than an error. It is 30 lines and it is the whole meaning of
the two-tier model, so it lives once, here, in pure code over plain
records.

**NULL MEANS INHERIT --- INCLUDING FOR FALSY VALUES.** ``COALESCE``, not
``or``. An override of ``""``, ``0``, ``False`` or ``()`` is a deliberate
statement by whoever set it, and ``or`` would silently discard every one of
them in favour of the definition's value. A campaign that renames a team to
the empty string has made a mistake; a campaign that sets a count to 0 has
not, and the merge cannot tell them apart, so it honours both.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

#: Sentinel for "this key was absent", distinct from a stored ``None``.
_MISSING = object()


def _get(record: Any, key: str) -> Any:
    """Read ``key`` off a mapping or an object, or ``_MISSING``."""
    if isinstance(record, Mapping):
        return record.get(key, _MISSING)
    return getattr(record, key, _MISSING)


def effective(
    definition: Any,
    instance: Any | None,
    *,
    overrides: Iterable[str],
    state: Iterable[str] = (),
) -> dict[str, Any]:
    """Merge a campaign ``instance`` over its library ``definition``.

    ``overrides`` names the columns that exist on BOTH tiers, where the
    instance's value wins unless it is ``None``. ``state`` names
    instance-only columns, taken from the instance alone --- a definition
    has no opinion about whether this campaign's copy of a team is
    currently active.

    ``instance=None`` returns the definition's values, with instance-only
    state as ``None``: a definition that no campaign has instantiated is a
    perfectly good thing to look at, and callers should not have to
    special-case the library view.

    Both tiers may be mappings or objects; kirby-api hands over ORM rows
    and a test hands over dataclasses, and neither should need converting.
    """
    out: dict[str, Any] = {}

    for key in overrides:
        base = _get(definition, key)
        if base is _MISSING:
            raise KeyError(
                f"override column {key!r} is not on the definition; an override "
                f"must exist on both tiers or it can never be inherited"
            )
        if instance is None:
            out[key] = base
            continue
        over = _get(instance, key)
        # COALESCE, not `or`: only None means "inherit". An override of "",
        # 0, False or () is a deliberate statement and is honoured.
        out[key] = base if (over is _MISSING or over is None) else over

    for key in state:
        value = _get(instance, key) if instance is not None else _MISSING
        out[key] = None if value is _MISSING else value

    return out


#: The Team columns that exist on both tiers, matching kirby-api's
#: ``teams/services/effective.py`` ``_OVERRIDE_COLS`` verbatim so the two
#: cannot drift. The narrative ones are listed because a CAMPAIGN may
#: override them; their CONTENT still never leaves the local database.
TEAM_OVERRIDES = (
    "name", "team_type", "agenda", "history", "tactics",
    "modus_operandi", "notes",
)

#: Instance-only state --- no definitional counterpart. Matches
#: ``_STATE_COLS``.
TEAM_STATE = ("is_active", "status_notes")


def effective_team(definition: Any, instance: Any | None = None) -> dict[str, Any]:
    """``effective`` with the Team column sets applied.

    Note ``tactics`` here is a team's PROSE --- how a sourcebook says it
    fights --- and is unrelated to ``kirby_combat.tactics``, the doctrine
    catalogue that decides what a combatant does this Phase. The collision
    is real and is called out wherever both could be meant.
    """
    return effective(
        definition, instance, overrides=TEAM_OVERRIDES, state=TEAM_STATE,
    )

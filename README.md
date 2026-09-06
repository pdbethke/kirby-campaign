# kirby-campaign

The campaign entity layer's **rules** for the Kirby HERO System platform:
teams, rosters, and the two-tier definition/instance merge.

No database, no HTTP, no tenancy. Zero dependencies.

## Team is not side

A **Team** is an identity that persists between fights — you are a Sentinel
on Tuesday and still one on Wednesday. A **side** is an alignment within one
fight: who is shooting at whom right now.

They usually agree, and they must be able to disagree — a schism, a
temporary alliance against something worse, a mind-controlled turncoat. So
`sides_from_teams` is the *default* mapping, not an identity, and
`assign_sides` never overwrites a side someone already carries.

```python
from kirby_campaign import Team, TeamMember, sides_from_teams

sentinels = Team(
    id="sentinels", name="Sentinels of Dawn", team_type="hero",
    members=(TeamMember("aurora", "leader"), TeamMember("bulwark")),
    base_ids=("dawn-spire",),
)
sides_from_teams([sentinels])
# {'aurora': Side(id='sentinels of dawn', name='Sentinels of Dawn',
#                 team_id='sentinels'), 'bulwark': ...}
```

A `Side` is an object, not a string — `Side.named` folds case and spacing
into one identity, so `"Golden"` and `"golden"` are one army rather than
two. It lives in **kirby-combat**, because a free-for-all in an alley has
sides and no campaign at all.

## The dependency runs one way

kirby-campaign sits **above** kirby-combat and imports it. The reverse must
never happen: if the engine imported this package, resolving an attack would
depend on knowing what a campaign is, dragging rosters and narrative prose
behind every roll. `tests/test_independence.py` asserts both halves.

## Two tiers

A library **definition** is the authored or sourcebook canon; a campaign
**instance** is a thin overlay of nullable overrides where NULL means
inherit, plus instance-only state.

```python
from kirby_campaign import effective_team

effective_team(definition, instance)   # COALESCE(instance, definition)
```

`COALESCE`, not `or`: an override of `""`, `0`, `False` or `()` is a
deliberate statement and is honoured. Only `None` inherits.

## Bases are builds

`Team.base_ids` are opaque references and nothing here dereferences them. A
Base is built with the base-building rules and imported from HDC, the same
as a character — kirby-cost costs it, and in a fight its walls are terrain
with BODY and DEF. Only the edge belongs in the entity layer.

## A note on content

The **shape** here is publishable. The **teams** are not.

Team exists as a first-class entity because villain teams do: the corpus
sources are CV1–CV3 (Champions Villains Volumes 1–3, with **CV2 a volume
dedicated to villain teams**) and Old School Enemies, and a team entry in
those books *is* the book's prose. All of it is paid Hero Games material —
local by default, published never. Every fixture and example in this
repository uses an **invented** team for that reason.

## Naming

`Team.tactics` is a paragraph about how a team fights. `kirby_combat.tactics`
is the doctrine catalogue that decides a combatant's action this Phase. They
are unrelated; this package holds neither.

## Licence

PolyForm Noncommercial License 1.0.0. For personal, non-commercial use.
Not affiliated with or endorsed by Hero Games.

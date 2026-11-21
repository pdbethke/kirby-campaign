# Changelog

## 0.3.0

### Added: the world model
Records for a campaign world that several campaigns can share. Design: kirby
`docs/superpowers/specs/2026-11-21-living-world-design.md` §6.2-6.7.

- `Polity`, `Office`, `Tenure` (a reign is a tenure of the head-of-state office).
- `Person` (a world identity, optionally linked to a HERO build; player
  characters exist only in Kirby and belong to one campaign) and `Kin`.
- `Organisation` (a dynasty, a mob family and a villain organisation are one
  structure; it may be backed by several source families) with its own ladder of
  `Rank`s (each with an archetype build, how hard its members are to hit, and how
  many guards they keep); `Relation`, `EntityRef`.
- `Membership`: dated and ranked. A person may belong to several organisations;
  a promotion ends one membership and starts another, keeping the history.
- Offices, tenures, relations and memberships carry source ids like every
  other world record.
- `WorldEvent` with a truth and a public account, `Cause`, `Law`, and two
  knowledge tiers (`PUBLIC`, `TRUTH`, `account_at`).
- `WorldState`: one world's records, checked together. Structural references
  must resolve; kin and member ids may name people a source has pruned.
- `CampaignLayer`, `EncounterHook`, `visible_account`: what one campaign owns
  and what its players may read.
- The underworld: `UnderworldLimits` (no defaults: no limits, no underworld;
  protection per person, `untouchable` or, for a player character,
  `encounters_only`; the outsider and leak chances),
  `Chain`, `ChainStep`, `validate_step(step, *, chain, state, limits,
  hits_sent_this_week)` (send, defer over the weekly cap or while the step it
  answers has not happened, drop, or route a step against a player character
  to their session). Limits or a chain from another world raise.
- `WorldState` refuses a `SourceRef` claimed by two records or naming another world.
- Hits (`hits.py`): `select_hit_squad` (the target and their guards against an
  equal squad, lowest ranks first), `failure_chance` / `resolve_hit_by_odds` (the
  fallback for organisations with no builds to fight with), and
  `consequences_of_hit` (every casualty, a "hit" or "failed_hit" event with its
  street account, and the target's side's grudge). The off-screen fight itself is
  the consumer's: it hands in a `HitResult`.
- `WorldDate` (years may precede year 1).
- Depends on kirby-world 0.2.2 (`SourceRef`); `kirby_fms` is forbidden here.

## 0.2.0 — 2026-11-15

### Added — GM rulings
`RulingRecord` (a campaign's stored ruling) and `rulings_in_fight(records, *, campaign_id, character_id)`, which turns the records for one character in one campaign into the engine's `kirby_combat.rulings.Ruling` tuple, ordered by `(power_id or "", fact)`. An unknown fact raises `ValueError` (the engine validates it). Requires kirby-combat 0.39.0.

# Changelog

## 0.3.0

### Added: the world model
Records for a campaign world that several campaigns can share. Design: kirby
`docs/superpowers/specs/2026-11-21-living-world-design.md` §6.2-6.7.

- `Polity`, `Office`, `Tenure` (a reign is a tenure of the head-of-state office).
- `Person` (a world identity, optionally linked to a HERO build; player
  characters exist only in Kirby and belong to one campaign) and `Kin`.
- `Organisation` (a dynasty, a mob family and a villain organisation are one
  structure; it may be backed by several source families), `Relation`, `EntityRef`.
- `WorldEvent` with a truth and a public account, `Cause`, `Law`, and two
  knowledge tiers (`PUBLIC`, `TRUTH`, `account_at`).
- `WorldState`: one world's records, checked together. Structural references
  must resolve; kin and member ids may name people a source has pruned.
- `CampaignLayer`, `EncounterHook`, `visible_account`: what one campaign owns
  and what its players may read.
- The underworld: `UnderworldLimits` (no defaults: no limits, no underworld),
  `Chain`, `ChainStep`, `validate_step(step, *, chain, state, limits,
  hits_sent_this_week)` (send, defer over the weekly cap or while the step it
  answers has not happened, drop, or route a step against a player character
  to their session). Limits or a chain from another world raise.
- `WorldState` refuses a `SourceRef` claimed by two records or naming another world.
- `WorldDate` (years may precede year 1).
- Depends on kirby-world 0.2.2 (`SourceRef`); `kirby_fms` is forbidden here.

## 0.2.0 — 2026-11-15

### Added — GM rulings
`RulingRecord` (a campaign's stored ruling) and `rulings_in_fight(records, *, campaign_id, character_id)`, which turns the records for one character in one campaign into the engine's `kirby_combat.rulings.Ruling` tuple, ordered by `(power_id or "", fact)`. An unknown fact raises `ValueError` (the engine validates it). Requires kirby-combat 0.39.0.

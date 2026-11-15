# Changelog

## 0.2.0 — 2026-11-15

### Added — GM rulings
`RulingRecord` (a campaign's stored ruling) and `rulings_in_fight(records, *, campaign_id, character_id)`, which turns the records for one character in one campaign into the engine's `kirby_combat.rulings.Ruling` tuple, ordered by `(power_id or "", fact)`. An unknown fact raises `ValueError` (the engine validates it). Requires kirby-combat 0.39.0.

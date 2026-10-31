# 05 — Accepted/Rejected Opening Comparison

PR-PLAY-11 · 2026-10-30 America/New_York · evidence_scope: structural_only.

| Source | Run | Declarations | Historical accepted | Replay HTTP |
|---|---|---|---|---|
| PR-PLAY-08 | 20261030T183848Z-5fe421902485 | 9 | True | 200 |
| PR-PLAY-09 | 20261030T191257Z-ecc1b6062bdc | 7 | True | 200 |
| PR-PLAY-09/10 rejection | 20261031T015747Z-5a6c03c902e3 | 7 | False | 422 |

All three use GPT-4.1-mini; original capture bytes and parsed JSON are retained under corpus/. historical_corpus.json contains actual declaration metadata, availability, structural/semantic outcomes, original failure reason, model and hashes. No unavailable capture was manufactured. Exact parsed replay is available; exact provider wire-byte replay is not.

The seven rejected-run declaration texts occur as authored evidence; the accepted PR09 response uses nonempty semantic_identity fields and one source ID, whereas rejected declarations have empty identities and null sources. This correlation is **not the cause**: original declarations all pass, and adding all correct source IDs still leaves the same prose rejection. Accepted historical metadata may use model-supplied identities, but acceptance is not evidence that every possible identity/provenance combination is sound.

Smallest confirmed causal change: replace the one notice-board narration sentence (both narration and legacy player_facing_text) with its already supplied authored text. Declarations, field combinations, state, validator and provider transport remain fixed. conservative_generation.json records 200; before_repair_replay.json records 422. Superficial wording matters to this conservative token-coverage gate. No metadata-only authorization repair is indicated, and no predicate-specific production allowlist is added.

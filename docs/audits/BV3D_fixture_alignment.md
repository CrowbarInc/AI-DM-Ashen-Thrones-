# BV3D — Fixture Alignment

**Date:** 2026-06-21  
**Compares:** BV3A unit-test fixtures vs BV3D measurement corpus (replay + positive controls).

---

## Positive-control fixtures (measurement layer)

Built by `tools/bv3d_build_positive_control_corpus.py` from `tests/test_bv3a_observe_referential_clarity_repair.py`:

| Fixture ID | Test origin | Shape | In replay before BV3D? |
|---|---|---|---|
| `bv3a_positive_control_interlocutor_he_says` | `test_observe_dialogue_he_says_repairs_via_upstream_not_hard_fallback` | 1× `he` dialogue tag + interlocutor + social NPC | **No** |
| `bv3a_negative_control_multi_person_hard_replace` | `test_observe_ambiguous_speaker_without_interlocutor_still_hard_replaces` | Multi-person + ungrounded `he` | Partial (similar hard-replace shapes) |

---

## Shapes present only in tests / measurement fixtures

| Shape | Test/fixture | Replay corpus |
|---|---|---|
| Single `ambiguous_entity_reference`, token `he`, exactly 1 violation | yes | **no** (without fixture) |
| Interlocutor + `resolution.social.npc_id` on observe | yes | **no** |
| Isolated `"…," he says` without named guard anchor | yes | **no** |
| Upstream repair applied + no hard replace | yes (OBS-M001) | **no** (replay-only) |

---

## Shapes present only in replay

| Shape | Example | Test/fixture |
|---|---|---|
| Named anchor + pass (`nearby guard … he says`) | 10 observe turns | not tested |
| Multi-violation (`guard`, `his`, `he`) count=3 | 10 observe turns | not tested |
| `referent_drift` / plural `they` | session_log OBS-M023 | not in BV3A tests |
| Retry/prepared emission bundles | API session_log | not in unit tests |
| Scene-opening + social_probe hygiene batches (2-line logs) | 30 hygiene dirs | not in BV3A tests |

---

## Missing production-shaped fixtures

These replay shapes are **not yet** represented in measurement fixtures but appear in refreshed replay:

| Gap | Replay count | Recommendation |
|---|---:|---|
| Multi-violation observe (3 violations) | 10 | Optional negative fixture (already partially covered by OBS-M002) |
| Named-anchor pass-through (validator clean) | 10 | Optional pass-through fixture for regression |
| `referent_drift` observe | 1 | Out of BV3A contract scope — document only |
| Hygiene 2-line batch (scene_opening + social_probe, no observe line) | ~10 batches | Refresh tooling gap — not BV3D fixture scope |

---

## Alignment matrix

| Dimension | Unit test + OBS-M001 | Replay observe (21 turns, excl. fixtures) |
|---|---|---|
| Eligible upstream | yes | **no** |
| Applied upstream | yes | **no** |
| Hard replace on ineligible | OBS-M002 yes | yes (12 turns) |
| Validator pass without attempt | not primary test goal | yes (10 turns) |

---

## Conclusion

Measurement fixtures **close the test↔metrics gap** for the BV3A happy path. Replay corpus alone remains **misaligned** with positive-control shapes — incidence must use BV3D scope + fixtures to measure activation, and report replay-only eligibility separately (`replay_only_eligible_count: 0` in eligibility report).

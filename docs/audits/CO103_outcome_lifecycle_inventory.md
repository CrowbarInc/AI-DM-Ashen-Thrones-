# CO103 — Outcome Lifecycle Inventory

**Date:** 2026-06-28  
**Scope:** Classification of existing protected replay observations only. No taxonomy, scoring, or artifact fabrication changes.

**Sources:** `artifacts/golden_replay/bug_recurrence_event_log.json`, `replay_failure_report.md`, `replay_failure_corpus_observations.md`, audit closeouts (BV8A, BX, BV8), live test verification (2026-06-28).

---

## Lifecycle classification legend

| Classification | Meaning |
|---|---|
| **Confirmed defect** | Observation matched a reproducible engineering defect at observation time |
| **Accepted fix** | Subsequent engineering activity resolved the defect; protected replay now passes |
| **Intentional design decision** | Observation reflected expected/accepted system behavior after design clarification |
| **Duplicate report** | Same failure signature repeated without new engineering signal |
| **Rejected report** | Observation classified as false positive or instrumentation noise |
| **Unresolved investigation** | Outcome not yet determined from available evidence |

---

## Protected recurrence key inventory (7 keys, 19 events)

| # | Recurrence key (abbrev.) | Scenarios | Events | Observation source | Lifecycle classification | Engineering outcome (evidence-backed) |
|---|---|---|---:|---|---|---|
| 1 | `speaker_drift\|projection\|selected_speaker_id\|golden_replay.py` | `vocative_override_after_prior_continuity` | 8 | Live replay (2026-06-04) | **Accepted fix** + **Duplicate report** (7/8 same `run_id`) | Alias vs canonical ID mismatch; test **passes today** ([BV8A](BV8A_retirement_evidence.md)); no reproduction since 2026-06-04 |
| 2 | `speaker_drift\|speaker\|selected_speaker_id\|speaker_contract_enforcement.py` | `wrong_speaker_strict_social_emission`, `bx5_guard_ambiguous_multi_guard` | 2 | Corpus backfill + live BX (2026-06-22) | **Intentional design decision** (BX ambiguous) + **Duplicate report** (corpus row) | BX speaker parity **closed** ([BX closeout](closeouts/BX_speaker_identity_end_to_end_parity_closeout.md)); structural + BX tests **pass** |
| 3 | `speaker_drift\|speaker\|selected_speaker_source\|speaker_contract_enforcement.py` | `bx5_guard_ambiguous_multi_guard` | 2 | Live BX (2026-06-22) + backfill | **Intentional design decision** | Ambiguous multi-guard expects `selected_speaker_source=None` by design; test **passes** |
| 4 | `emission_drift\|projection\|response_type_candidate_ok\|golden_replay.py` | Four `bx5_guard_*` scenarios | 4 | Live BX development run (2026-06-22) | **Accepted fix** | Historical BX development failures; BX parity expectations locked; all BX tests **pass** |
| 5 | `fallback_drift\|fallback\|final_emitted_source\|final_emission_gate.py` | `directed_npc_question` | 1 | Corpus backfill (2026-06-20) | **Duplicate report** | Controlled classification row mapped to protected scenario; scenario test **passes** — no live failure reproduced |
| 6 | `semantic_drift\|sanitizer\|scaffold_leakage\|output_sanitizer.py` | `sanitizer_scaffold_leakage` | 1 | Corpus backfill (2026-06-20) | **Duplicate report** | Same — corpus expansion row; scenario test **passes** |
| 7 | `fallback_drift\|projection\|fallback_family\|golden_replay.py` | `wrong_speaker_strict_social_emission` | 1 | Live CO102 validation (2026-06-28) | **Rejected report** | Pipeline validation artifact: `fallback_family` unavailable on passing structural path; not a production defect signal |

---

## Scenario-level inventory (8 scenarios)

| Scenario | Observations | Primary classification | Downstream engineering activity |
|---|---:|---|---|
| `vocative_override_after_prior_continuity` | 8 | Accepted fix | Projection/expectation alignment; green test ([BV8A](BV8A_retirement_evidence.md)) |
| `wrong_speaker_strict_social_emission` | 2 | Mixed: corpus duplicate + CO102 rejected | Speaker enforcement path documented ([BV8](BV8_recurrence_trace.md)); structural test **passes** |
| `directed_npc_question` | 1 | Duplicate report (corpus) | Canonical baseline scenario; test **passes** |
| `sanitizer_scaffold_leakage` | 1 | Duplicate report (corpus) | Canonical baseline scenario; test **passes** |
| `bx5_guard_role_alias_guard_captain` | 1 | Accepted fix | BX parity case locked |
| `bx5_guard_canonical_guard_captain` | 1 | Accepted fix | BX parity case locked |
| `bx5_guard_gate_guard_distinct` | 1 | Accepted fix | BX parity case locked |
| `bx5_guard_ambiguous_multi_guard` | 3 | Intentional design decision | Ambiguous guard parity by design ([BX closeout](closeouts/BX_speaker_identity_end_to_end_parity_closeout.md)) |

---

## Outcome signal availability vs recurrence history

| Evidence type | Exists in repo? | In main `bug_recurrence_history.json`? |
|---|---|---|
| BV8A retirement for projection vocative key | Yes (`artifacts/bv8a_recurrence_history.json`) | **No** — `validated_outcome_count: 0` |
| BX speaker parity closeout | Yes (audit doc) | **No** — keys remain `active` |
| Live test pass for all observed scenarios | Yes (verified 2026-06-28) | **No** — no automatic retirement on test pass |
| Corpus expansion rows | Yes | Counted as observations only |

**Operational finding:** Outcome evidence exists in **audit artifacts and test status** but is **not yet linked** into the recurrence outcome validation pipeline that drives calibration. This explains low calibration despite engineering progress — not absence of engineering outcomes.

---

## Cross-references

- Observation workflow: [`docs/runbooks/protected_replay_observation_collection.md`](../runbooks/protected_replay_observation_collection.md)
- CO102 validation: [`CO102_live_recurrence_validation_report.md`](CO102_live_recurrence_validation_report.md)
- Outcome correlation: [`CO103_observation_outcome_correlation.md`](CO103_observation_outcome_correlation.md)

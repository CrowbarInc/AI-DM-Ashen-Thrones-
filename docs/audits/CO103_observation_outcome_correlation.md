# CO103 — Observation-to-Outcome Correlation Report

**Date:** 2026-06-28  
**Scope:** Classify existing evidence relationships only. No new scoring metrics.

---

## Correlation summary

| Relationship | Count (keys) | Share |
|---|---:|---:|
| Observation → accepted fix | 2 | 29% |
| Observation → intentional architecture | 2 | 29% |
| Observation → duplicate / inflation | 3 | 43% |
| Observation → false positive | 1 | 14% |
| Observation → unresolved (no evidence) | 0 | 0% |
| Observation → deferred (pending) | 0 | 0% |

*Keys may carry multiple tags; table counts primary relationship per key from lifecycle inventory.*

---

## Detailed correlation map

### Observation → fix

| Observation | Outcome evidence | Confidence in correlation |
|---|---|---|
| Vocative projection mismatch (`guard` vs `guard_captain`, 2026-06-04) | Protected replay **passes**; BV8A documents resolved defect; no reproduction since single run | **High** — live test + audit closeout |
| BX `response_type_candidate_ok` failures (2026-06-22) | Four BX scenarios **pass**; BX program closed with locked parity expectations | **High** — closeout doc + test pass |

### Observation → intentional architecture

| Observation | Outcome evidence | Confidence in correlation |
|---|---|---|
| BX ambiguous guard `selected_speaker_id` / `selected_speaker_source` | BX closeout defines ambiguous parity expectations (`None` sources, `final_ambiguous` status) | **High** — explicit design contract |
| Wrong-speaker corpus row (speaker enforcement category) | BX documents `guard`/`guard_captain` role-alias architecture; wrong_speaker structural test **passes** | **Medium** — corpus row predates BX lock; live scenario healthy |

### Observation → duplicate

| Observation | Outcome evidence | Confidence in correlation |
|---|---|---|
| 7/8 vocative projection events (same `run_id`) | BQ36/BV8A document instrumentation inflation | **High** |
| Corpus expansion rows (`directed_npc_question`, `sanitizer_scaffold_leakage`, `wrong_speaker` speaker row) | Scenarios **pass**; rows from controlled classification mapping, not live failures | **High** |

### Observation → false positive

| Observation | Outcome evidence | Confidence in correlation |
|---|---|---|
| CO102 live `fallback_family` unavailable (2026-06-28) | Structural wrong_speaker test **passes** with correct expectation helper; failure was pipeline-validation path using mismatched assertion | **High** — replay_failure_report shows structural_drift on unavailable field |

### Observation → deferred

None identified with evidence-backed pending engineering work. All observed scenarios have green protected tests as of 2026-06-28.

---

## Prediction quality assessment (qualitative)

Using existing forecast/trend classifications from `bug_recurrence_history.json`:

| Predicted signal | Realized engineering outcome | Alignment |
|---|---|---|
| Elevated/recurring on projection vocative key | Fix + duplicate inflation | **Partial** — real issue existed; recurrence count overstated |
| Elevated on BX emission_drift key | Fix during BX program | **Aligned** |
| Elevated on BX speaker keys | Intentional design + fix | **Aligned** |
| Watch/emerging on corpus-only keys | No live defect | **Misaligned** — observations did not predict ongoing defects |
| Watch on CO102 fallback_family key | False positive | **Misaligned** |

**Interpretation:** Observations **do predict meaningful engineering work** when sourced from **live protected replay failures** during active programs (BX, vocative). **Corpus backfill observations** without live reproduction inflate volume without outcome signal — contributing to **overconfidence** (high structural confidence, low outcome evidence strength 0.20).

---

## Calibration gap classification (observations lacking downstream outcomes in history JSON)

| Gap reason | Affected keys | Evidence |
|---|---|---|
| **Outcome not propagated to event log** | Projection vocative key | BV8A retirement in separate artifact; main log `recurrence_status: active` |
| **Corpus observation without live failure** | Fallback + sanitizer corpus keys | Tests pass; no engineering ticket implied |
| **Lifecycle completion not recorded** | BX keys (post-closeout) | Tests pass; no `retired` status in protected log |
| **False positive not retracted** | CO102 fallback_family key | Single live event; no fix warranted |
| **Insufficient operational history** | — | Not applicable — history spans Jun 4–28 with 7 keys |
| **Genuine uncertainty** | — | Not applicable — outcomes classifiable from existing audits |

---

## Cross-references

- Lifecycle inventory: [`CO103_outcome_lifecycle_inventory.md`](CO103_outcome_lifecycle_inventory.md)
- Calibration assessment: [`CO103_calibration_maturity_assessment.md`](CO103_calibration_maturity_assessment.md)
- BQC5 outcome validation: [`BQC5_effectiveness_validation.md`](BQC5_effectiveness_validation.md)

# CP1 — Preflight + Sanitizer Corrective Locality Slice Report

Date: 2026-06-28  
Planning authority: `CP_corrective_locality_cohort_3_discovery.md`  
Slice scope: CP9 (upstream preflight/config safety) + CP1 (sanitizer scaffold leak)

## Executive Summary

Focused baseline and validation suites are **green**. No production defects were reproduced in CP9 or CP1 surfaces during this slice. Per slice rules ("fix real defects only"), **no code changes were made**. This slice is a **validation-only probe** confirming existing safeguards; it does **not** produce a new qualifying corrective-locality cohort entry.

## Defects Found

### CP9 — Upstream preflight/config self-invalidates

**Status: none reproduced**

| Check | Result |
|---|---|
| Preflight healthy path | Pass |
| Skip env does not require runtime key | Pass |
| `max_output_tokens >= 16` clamp | Pass (constant below minimum clamped to 16) |
| Health classification (auth, quota, transient) | Pass |
| Preflight does not mutate `call_gpt` | Pass |
| Lifespan invokes preflight when not skipped | Pass |
| Model routing config | Pass |

Existing production safeguards verified in code review:

- `game/api_upstream_preflight.py`: `_OPENAI_RESPONSES_MIN_MAX_OUTPUT_TOKENS = 16`, `_clamp_preflight_max_output_tokens()`, skip path isolation.
- Regression tests document the historical CA-10 class defect (`test_preflight_responses_create_max_output_tokens_meets_api_minimum`).

### CP1 — Sanitizer scaffold leak

**Status: none reproduced**

| Check | Result |
|---|---|
| Unit sanitizer scaffold/router/planner/validator blocking | Pass (45 tests) |
| Protected golden `sanitizer_scaffold_leakage` | Pass — `scaffold_leakage: False` |
| Fallback sanitizer projection | Pass (4 tests) |

Protected scenario injects `"Planner: route via router. Validator: unresolved scaffold."` and asserts no scaffold terms reach player-facing output.

## Files Changed

| Bucket | Count | Paths |
|---|---:|---|
| **Total** | 1 | This report only |
| Production | 0 | — |
| Test | 0 | — |
| Governance/docs | 1 | `CP1_preflight_sanitizer_corrective_slice_report.md` |
| Replay/golden | 0 | — |

No stop conditions triggered (≤6 files, no governance edits required, no stale golden expectations, no architectural expansion).

## Tests Run

### 1. CP9 baseline

```bash
python -m pytest tests/test_api_upstream_preflight.py tests/test_model_routing_config.py -q --tb=short
```

| Outcome | Count |
|---|---:|
| **Passed** | 19 |
| Failed | 0 |
| Skipped | 0 |

Breakdown: `test_api_upstream_preflight.py` (15), `test_model_routing_config.py` (4).

### 2. CP1 baseline

```bash
python -m pytest tests/test_output_sanitizer.py tests/test_golden_replay_structural_invariants.py tests/test_golden_replay_fallback_sanitizer_projection.py -q --tb=short
```

| Outcome | Count |
|---|---:|
| **Passed** | 55 |
| Failed | 0 |
| Skipped | 0 |

Breakdown: `test_output_sanitizer.py` (45), `test_golden_replay_structural_invariants.py` (includes `test_golden_replay_sanitizer_scaffold_leakage_structural_invariants`), `test_golden_replay_fallback_sanitizer_projection.py` (4).

Focused protected node (isolated):

```bash
python -m pytest tests/test_golden_replay_structural_invariants.py::test_golden_replay_sanitizer_scaffold_leakage_structural_invariants -q --tb=short
```

Result: **1 passed**.

### 3. Protected replay manifest

```bash
python tools/refresh_protected_replay_manifest.py --check
```

Result: **exit 0** (no manifest drift).

### 4. Corrective locality validation

```bash
python -m pytest tests/test_corrective_change_locality_classifier.py tests/test_corrective_change_locality_cohort.py tests/test_corrective_locality_baseline.py tests/test_corrective_fix_watch.py -q --tb=short
```

| Outcome | Count |
|---|---:|
| **Passed** | 47 |
| Failed | 0 |
| Skipped | 0 |

Breakdown: classifier (21), cohort (10), baseline (11), fix watch (5).

## Locality Metrics

| Metric | Value |
|---|---:|
| Total files touched | 1 |
| Production files touched | 0 |
| Test files touched | 0 |
| Governance/docs files touched | 1 |
| Replay/golden files touched | 0 |
| Recurrence evidence exists | Yes (historical, pre-slice) |

## Recurrence Outcome

### CP1 — `sanitizer_scaffold_leakage`

- Recurrence key: `recurrence:v1:semantic_drift|sanitizer|scaffold_leakage|game/output_sanitizer.py`
- CO106 classification: **duplicate historical observation** (corpus expansion row from 2026-06-20); BV8A registry ACTIVE; scenario test passes.
- This slice: protected node **passes**; no new failure event; no retirement propagation performed (no documented protected failure→fix cycle to retire).

### CP9 — preflight

- No replay recurrence key applies (startup/config surface).
- No new CA locality qualifying fix produced by this slice.

### Unrelated active sentinel (not in slice scope)

`artifacts/golden_replay/replay_failure_report.md` records a CO102 pipeline validation failure for `wrong_speaker_strict_social_emission` (`fallback_family` projection). CO106 classifies this as an **operational sentinel**, not a CP9/CP1 production defect. Not addressed in this slice.

## Cohort #3 Eligibility

| Criterion | Met? |
|---|---|
| Real defect reproduced | **No** |
| Production fix applied | **No** |
| Focused validation after fix | Yes (baseline green) |
| Independent failure→fix→validation evidence | **No** |

**Verdict: this slice does NOT count toward CP corrective-locality cohort #3** as a qualifying fix entry. It confirms CP9 and CP1 surfaces are currently stable and that prior preventive/embedded work (CA10 absorption ratio) holds for these two candidates. Cohort #3 still needs a candidate with a reproducible failure and a bounded production fix.

## Recommended Next Candidate

**CP2 — Directed NPC question route drift**

Rationale per discovery execution order:

1. CP9 and CP1 validation probes are complete with no actionable defects.
2. CP2 is the next ordered candidate with core player-facing route behavior, clear protected signal (`directed_npc_question`), and medium but bounded blast radius (2–5 files).
3. CP3/CP4 (speaker parity) should follow only one at a time to avoid over-concentrating on speaker work.
4. CP5 (fallback projection) aligns with the unrelated CO102 sentinel but is lower priority until runtime-facing route/speaker fixes are stable.

## Stop/Report Conditions

None triggered:

- Fix surface ≤6 files: N/A (no fix required)
- Governance edits: not required
- Protected replay/golden stale: not observed for CP1/CP9 targets
- Architectural redesign: not required

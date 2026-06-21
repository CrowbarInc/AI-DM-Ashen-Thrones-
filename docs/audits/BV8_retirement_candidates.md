# BV8 — Speaker Recurrence Retirement Candidates

**Date:** 2026-06-21  
**Goal:** Retire dominant recurrence family rather than repeatedly patching projection alias mismatches.

Candidates ranked by projected recurrence reduction × inverse cost.

---

## Candidate summary

| Rank | Candidate | Projected recurrence reduction | Implementation cost | Replay risk | Speaker risk | Class |
|---:|---|---:|---:|---|---|---|
| 1 | **R1 — Retire stale projection key + dedupe event log** | **−7 to −8 events (−64% to −73%)** | 1/5 | 1/5 | 1/5 | **Low** |
| 2 | **R2 — Canonical ID contract for `selected_speaker_id`** | Prevents recurrence regrowth on alias drift | 2/5 | 2/5 | 2/5 | **Low** |
| 3 | **R3 — Fix investigate_first ownership to `golden_replay_projection.py`** | 0 event reduction; reduces mis-routing | 1/5 | 1/5 | 1/5 | **Low** |
| 4 | **R4 — BT SpeakerContractObservation test helper** | Prevents future unidentified divergence | 3/5 | 2/5 | 2/5 | **Medium** |
| 5 | **R5 — Normalize expectation via canonical roster helper** | Prevents alias/canonical mismatches in tests | 2/5 | 3/5 | 2/5 | **Medium** |
| 6 | **R6 — Dedupe guard on recurrence event append** | Prevents inflation recurrence | 2/5 | 1/5 | 1/5 | **Low** |
| 7 | **R7 — Project speaker from emitted prose signature** | May reduce projection/state drift | 4/5 | 4/5 | 4/5 | **High** |
| 8 | **R8 — Retire exact `selected_speaker_id` protected field** | −8 events but weakens invariant | 2/5 | 4/5 | 3/5 | **High** |

---

## Candidate detail

### R1 — Retire stale projection recurrence key + dedupe event log

| Dimension | Assessment |
|---|---|
| **Projected recurrence reduction** | Remove 7 duplicate rows; mark key `retired` with evidence (test green + no failure since 2026-06-04). Event total **11 → 3**; speaker share **81.8% → 33.3%**; dominant key share **72.7% → 0%** |
| **Implementation cost** | Run dedupe on `bug_recurrence_event_log.json`; set `recurrence_status=retired` via `replay_bug_recurrence.py` retirement API; regenerate history artifacts |
| **Replay risk** | **Low** — does not change replay pass/fail |
| **Speaker risk** | **Low** — metadata only |
| **Classification** | **Low risk** |

**Rationale:** Test passes today. Recurrence is stale instrumentation debt per [BQ36_recurrence_write_path_audit.md](BQ36_recurrence_write_path_audit.md).

---

### R2 — Canonical ID contract for `selected_speaker_id`

| Dimension | Assessment |
|---|---|
| **Projected recurrence reduction** | Eliminates alias/canonical mismatch class (root cause of vocative failure) |
| **Implementation cost** | Document + enforce: projection always emits `canonical_interaction_target_npc_id`; tests use canonical ids in expectations |
| **Replay risk** | **Low** — aligns observation with roster truth |
| **Speaker risk** | **Low** — no runtime speaker policy change |
| **Classification** | **Low risk** |

**Touch points:** `golden_replay_projection.py`, `test_golden_replay_structural_invariants.py`, `protected_replay_manifest.md`.

---

### R3 — Fix investigate_first ownership

| Dimension | Assessment |
|---|---|
| **Projected recurrence reduction** | 0 direct; prevents misdirected repairs to `golden_replay.py` orchestration |
| **Implementation cost** | Update drift taxonomy / failure classifier routing for `selected_speaker_id` → `golden_replay_projection.py` |
| **Replay risk** | **Low** |
| **Speaker risk** | **Low** |
| **Classification** | **Low risk** |

---

### R4 — BT SpeakerContractObservation helper

| Dimension | Assessment |
|---|---|
| **Projected recurrence reduction** | Prevents **new** recurrence from unidentified finalize→replay gaps |
| **Implementation cost** | Test-only helper per [BT_speaker_finalization_divergence_discovery.md](BT_speaker_finalization_divergence_discovery.md) — compose shadow harness + projection join |
| **Replay risk** | **Low-medium** — new test assertions on existing fixtures |
| **Speaker risk** | **Low-medium** — observation only |
| **Classification** | **Medium risk** |

---

### R5 — Normalize expectation via canonical roster helper

| Dimension | Assessment |
|---|---|
| **Projected recurrence reduction** | Prevents alias drift in protected expectations (`"guard"` → `"guard_captain"`) |
| **Implementation cost** | Add `canonical_speaker_expectation(session, alias)` wrapper used by structural invariant tests |
| **Replay risk** | **Medium** — changes expectation strings in protected manifest |
| **Speaker risk** | **Low-medium** |
| **Classification** | **Medium risk** |

---

### R6 — Recurrence event dedupe guard

| Dimension | Assessment |
|---|---|
| **Projected recurrence reduction** | Prevents future 7× inflation on single failures |
| **Implementation cost** | Extend `is_commit_worthy_recurrence_event()` / append path with `(recurrence_key, scenario_id, run_id)` dedupe |
| **Replay risk** | **Low** |
| **Speaker risk** | **Low** |
| **Classification** | **Low risk** |

---

### R7 — Project speaker from emitted prose signature

| Dimension | Assessment |
|---|---|
| **Projected recurrence reduction** | Could align observation with visible attribution |
| **Implementation cost** | High — changes projection semantics; affects all golden replay consumers |
| **Replay risk** | **High** — protected field semantics shift |
| **Speaker risk** | **High** — may disagree with routing state intentionally |
| **Classification** | **High risk** |

**Defer:** BT discovery recommends test-only checkpoint join first; prose-based projection conflicts with routing-state observation charter.

---

### R8 — Retire exact `selected_speaker_id` protected field

| Dimension | Assessment |
|---|---|
| **Projected recurrence reduction** | Removes field from protected observation → recurrence key cannot form |
| **Implementation cost** | Medium — weakens protected manifest invariant |
| **Replay risk** | **High** — vocative override scenario loses speaker switch signal |
| **Speaker risk** | **High** |
| **Classification** | **High risk — reject** |

---

## Recommended bundle (Phase 1 ROI)

| Include | Exclude (defer) |
|---|---|
| R1 retire stale key | R7 prose-based projection |
| R2 canonical ID contract | R8 drop protected field |
| R3 investigate_first fix | |
| R6 dedupe guard | |

**Optional Phase 2:** R4 + R5 for structural prevention.

---

## Evidence

| Source | Role |
|---|---|
| [BV8_concentration_report.md](BV8_concentration_report.md) | Concentration metrics |
| [BV8_recurrence_trace.md](BV8_recurrence_trace.md) | Divergence localization |
| [BT_speaker_finalization_divergence_discovery.md](BT_speaker_finalization_divergence_discovery.md) | R4 spec |

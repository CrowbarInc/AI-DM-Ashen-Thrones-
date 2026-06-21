# BV3B — Replay Refresh

**Date:** 2026-06-21  
**Purpose:** Regenerate finalized-turn artifacts under current BV3A gate code before incidence re-measurement.  
**Authority:** `tools/bv3b_replay_corpus_refresh.py`, protected golden replay suites, scenario-spine validation, projection refresh.

---

## Executive summary

Canonical FEM corpus was refreshed from **107 → 200** instances. Refresh replaced stale `data/session_log.jsonl` and `artifacts/scene_canon_hygiene_runtime/` captures with deterministic observe playthroughs executed through the live `/api/chat` path and current terminal pipeline (including BV3A upstream repair hooks).

Protected golden replay executed with **89/91** tests passing (two pre-existing failures in protected-bridge recurrence wiring and direct-intrusion diagnostic profile). Scenario-spine smoke validation completed for `branch_social_inquiry`. Projection gap and drift-watch artifacts were regenerated; protected replay manifest field-path parity remained current.

---

## Commands executed

| Step | Command | Result |
|---|---|---|
| Baseline preservation | Copy `artifacts/golden_replay/bv1b_fallback_incidence_report.json` → `bv1b_fallback_incidence_report.baseline.json` | OK |
| Corpus refresh | `python tools/bv3b_replay_corpus_refresh.py --hygiene-batches 30` | OK — manifest at `artifacts/bv3b_replay_refresh/corpus_refresh_manifest.json` |
| Protected golden replay | `python -m pytest tests/test_golden_replay_*.py -q --tb=line` | 89 passed, 2 failed (see below) |
| Scenario spine validation | `python tools/run_scenario_spine_validation.py --smoke --branch branch_social_inquiry` | OK — `artifacts/scenario_spine_validation/20260621T123556Z/` |
| Projection refresh | `fallback_projection_gap_reality_audit.py`, `projection_drift_watch.py` (via refresh tool) | OK |
| Manifest check | `python tools/refresh_protected_replay_manifest.py --check` | OK |

---

## Corpus refresh detail

**Pre-refresh corpus (BV1B baseline):**

| Source | FEM instances |
|---|---:|
| `data/session_log.jsonl` | 17 |
| `artifacts/scene_canon_hygiene_runtime/*/data/session_log.jsonl` | 90 |
| **Total (deduped scan)** | **107** |

**Post-refresh corpus:**

| Source | FEM instances (scan) |
|---|---:|
| Refreshed `data/session_log.jsonl` | 2 |
| 30 new hygiene runtime batches | ~60 |
| Scenario-spine smoke transcript (5 turns) | 5 |
| Residual archived / nested FEM | remainder |
| **Total (deduped scan)** | **200** |

**Backup artifacts:**

- `artifacts/bv3b_replay_refresh/session_log.pre_refresh.jsonl`
- `artifacts/bv3b_replay_refresh/scene_canon_hygiene_runtime.2026-06-21T123528.236892Z/`

**Refresh playthrough pattern:** frontier-gate world seed, suppressed intent parsers, stubbed GPT returning observe dialogue with speech-tag pronouns (`"Keep moving," he says, …`), prompts `I look around.` / notice-board / serjeant-runner variants.

---

## Protected replay regression gates

| Gate | Status | Notes |
|---|---|---|
| Golden replay structural suites | **Mostly green** | 89/91 |
| `test_protected_golden_assertion_failure_records_canonical_report` | **FAIL** | Recurrence event log empty after drift write (`IndexError`) |
| `test_golden_replay_frontier_gate_direct_intrusion_25_turn_diagnostic_stability` | **FAIL** | Profile drift on diagnostic branch (pre-existing tolerance) |
| Primary protected 25-turn social inquiry | **PASS** | Included in passing set |
| Direct-seam opening/alias rows | **PASS** | Included in passing set |
| Manifest field-path parity | **PASS** | `--check` exit 0 |

---

## Scenario-spine validation

Smoke run (5 turns) on `frontier_gate_long_session.json` → `branch_social_inquiry` wrote:

- `artifacts/scenario_spine_validation/20260621T123556Z/frontier_gate_long_session/branch_social_inquiry/transcript.json`
- `session_health_summary.json`, `compact_operator_summary.md`

In-process TestClient path used (no external `--base-url`).

---

## Projection / manifest refresh

- `artifacts/golden_replay/projection_gap_reality_report.json` regenerated.
- `artifacts/golden_replay/projection_drift_watch_report.json` / `.md` regenerated.
- `docs/testing/protected_replay_manifest.md` generated field-path section already matched registry (`--check` exit 0).

---

## Evidence

| Artifact | Role |
|---|---|
| `artifacts/bv3b_replay_refresh/corpus_refresh_manifest.json` | Refresh provenance |
| `artifacts/scenario_spine_validation/20260621T123556Z/` | Spine smoke FEM |
| `artifacts/golden_replay/bv1b_fallback_incidence_report.baseline.json` | Pre-refresh incidence authority |
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json` | Post-refresh incidence authority |

# BV3F — Replay Refresh

**Date:** 2026-06-21  
**Purpose:** Re-materialize canonical FEM corpus under current BV3E gate code so replay-derived metrics reflect live repair activation, not shape simulation alone.  
**Authority:** `tools/bv3f_replay_corpus_refresh.py`, BV3D measurement scope, projection refresh, protected replay manifest check.

---

## Executive summary

Canonical FEM corpus was refreshed under **BV3E exact-alias introducer repair**. Pre-refresh BV3D/BV3E metric snapshots were preserved; session log and 30 hygiene runtime batches were regenerated via deterministic observe playthroughs through the live `/api/chat` path.

Post-refresh scan: **95** FEM instances (BV3D scope), **23** observe turns. BV3E repair stamps appear on **10** replay-only turns plus **1** positive-control fixture turn. `referential_clarity_hard_replacement` lineage dropped **12 → 1** on the refreshed corpus.

---

## Commands executed

| Step | Command | Result |
|---|---|---|
| Pre-refresh snapshot | `python tools/bv3f_replay_corpus_refresh.py` (baseline step) | OK — `artifacts/bv3f_replay_refresh/pre_refresh.*` |
| Corpus refresh | `python tools/bv3f_replay_corpus_refresh.py --hygiene-batches 30` | OK — manifest at `artifacts/bv3f_replay_refresh/corpus_refresh_manifest.json` |
| Projection refresh | `fallback_projection_gap_reality_audit.py`, `projection_drift_watch.py` (via refresh tool) | OK |
| Manifest check | `python tools/refresh_protected_replay_manifest.py --check` | OK |

---

## Corpus refresh detail

**Pre-refresh (BV3D frozen FEM):**

| Source | FEM instances (BV3D scan) |
|---|---:|
| `data/session_log.jsonl` | 2 |
| `artifacts/scene_canon_hygiene_runtime/*/data/session_log.jsonl` | ~90 |
| `artifacts/bv3d_measurement/` fixtures | 2 |
| Scenario-spine validation | 5 |
| **Total (deduped scan)** | **97** |

**Post-refresh (BV3F):**

| Source | FEM instances (BV3D scan) |
|---|---:|
| Refreshed `data/session_log.jsonl` | 2 |
| 30 new hygiene runtime batches | ~60 |
| Positive-control fixtures | 2 |
| Residual scenario-spine / canonical replay | remainder |
| **Total (deduped scan)** | **95** |

**Backup artifacts:**

- `artifacts/bv3f_replay_refresh/session_log.pre_refresh.jsonl`
- `artifacts/bv3f_replay_refresh/scene_canon_hygiene_runtime.2026-06-21T131035.284826Z/`
- `artifacts/bv3f_replay_refresh/pre_refresh.bv3a_referential_clarity_metrics.json`
- `artifacts/bv3f_replay_refresh/pre_refresh.bv3d_eligibility_report.json`
- `artifacts/bv3f_replay_refresh/pre_refresh.bv3e_eligibility_metrics.json`
- `artifacts/bv3f_replay_refresh/pre_refresh.bv3e_shape_simulation.json`

**Refresh playthrough pattern:** frontier-gate world seed, suppressed intent parsers, stubbed GPT returning observe dialogue with speech-tag pronouns (`"Keep moving," he says, …`), prompts `I look around.` / notice-board / serjeant-runner variants.

---

## BV3E instrumentation on refreshed corpus

| Field | Pre-refresh (frozen) | Post-refresh |
|---|---:|---:|
| `referential_clarity_upstream_repair_applied` (observe) | 1 | **11** |
| `referential_clarity_bv3e_repair_mode=exact_alias_introducer` | 0 | **10** |
| `referential_clarity_hard_replacement` (lineage) | 12 | **1** |
| Replay-only eligible count | 0 | **10** |

---

## Projection / manifest refresh

- `artifacts/golden_replay/projection_gap_reality_report.json` regenerated.
- `artifacts/golden_replay/projection_drift_watch_report.json` / `.md` regenerated.
- Protected replay manifest field-path parity: `--check` exit 0.

---

## Evidence

| Artifact | Role |
|---|---|
| `artifacts/bv3f_replay_refresh/corpus_refresh_manifest.json` | Refresh provenance |
| `artifacts/bv3f_replay_refresh/pre_refresh.*` | BV3D/BV3E frozen baselines |
| `artifacts/bv3a_referential_clarity_metrics.json` | Post-refresh BV3A incidence |
| `artifacts/bv3d_eligibility_report.json` | Post-refresh eligibility |
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json` | Post-refresh fallback incidence |

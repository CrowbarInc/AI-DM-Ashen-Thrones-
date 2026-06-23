# Cycle AF — Dead Governance Removal Closure

**Date:** 2026-05-31  
**Status:** Complete  
**Recon artifact:** [`docs/cycle_af_dead_governance_removal_recon_2026-05-31.md`](../cycle_af_dead_governance_removal_recon_2026-05-31.md)

---

## Objective

Reduce governance surface area without reducing protection.

Original targets:

- dead registries
- superseded ownership docs
- obsolete closeout artifacts
- duplicate governance structures

Cycle AF delivered five blocks (AF-1, AF-1B, AF-2, AF-3, AF-4). All blocks preserved CI-enforced registries, closeout pytest slices, protected replay semantics, and runtime behavior. Contraction was limited to documentary artifacts, duplicate doc mirrors, folder normalization, and stale authority pointers.

---

## AF-1 Archive Results

**Block:** Low-risk dead governance archive  
**Archive location:** `docs/archive/dead_governance/2026-05-31/`  
**Index:** `docs/archive/dead_governance/2026-05-31/README.md`

### Files archived (16)

Moved from `audits/` → archive via `git mv` (content unchanged):

1. `failure_dashboard_contract_lock_2026-05-11.md`
2. `failure_dashboard_cycle_b_closure_2026-05-11.md`
3. `failure_dashboard_final_integration_audit_2026-05-11.md`
4. `failure_dashboard_operationalization_2026-05-11.md`
5. `failure_dashboard_probe_harness_2026-05-11.md`
6. `failure_dashboard_sample.md`
7. `failure_locality_assessment.md`
8. `post_gate_sanitizer_rewrite_surface_inventory_2026-05-12.md`
9. `cycle_g_block1_full_suite_validation_20260519.txt`
10. `cycle_g_block2_full_suite_validation_20260519.txt`
11. `cycle_g_block3_full_suite_validation_20260519.txt`
12. `cycle_g_runtime_stability_suite_hygiene_recon_20260518.md`
13. `cycle_g_tracked_runtime_snapshot_churn_recon_20260519.md`
14. `cycle_f_opening_projection_fixture_helper_recon_20260518.md`
15. `cycle_f_routing_policy_decision_memo_20260518.md`
16. `cycle_e_test_signal_ownership_thinning_closure_2026-05-17.md`

### Rationale

Each candidate had **zero incoming references** (filename/stem scan) outside self-citation. Classification: dead/unused or historical-only memos superseded by classifier tests, later cycle closeouts, or operational snapshots still in active paths (e.g. `audits/failure_dashboard_latest.md`).

### Validation outcome

```text
python -m pytest tests/test_ownership_registry.py -q          # 17 passed
python -m pytest tests/test_validation_coverage_audit.py -q   # 5 passed
python tools/validation_coverage_audit.py --strict            # exit 0
python -m pytest tests/test_golden_replay.py -q               # 59 passed
python -m pytest -m golden_replay -q                          # collection error (fixed in AF-1B)
```

---

## AF-1B Collection Integrity Repair

**Block:** Restore pytest collection for `-m golden_replay`

### Stale import discovered

`tests/test_narration_transcript_regressions.py` imported private `_response_type_contract` from `tests/test_fallback_behavior_gate.py`.

### Root cause

Cycle R Block R1-B moved shared gate fixtures to `tests/helpers/final_emission_gate_fixtures.py` as public `response_type_contract()`. `test_fallback_behavior_gate.py` was updated; the transcript regression module was not. **Stale test residue** — not caused by AF-1 archival moves.

### Repair

**File changed:** `tests/test_narration_transcript_regressions.py`

- Import `response_type_contract` from `tests.helpers.final_emission_gate_fixtures`
- Replace `_response_type_contract("answer")` → `response_type_contract("answer")`
- No compatibility shims; no replay semantic changes

### Validation outcome

| Command | Before | After |
| --- | --- | --- |
| `python -m pytest tests/test_narration_transcript_regressions.py -q` | ImportError at collection | **41 passed** |
| `python -m pytest -m golden_replay -q` | **ERROR** (ImportError) | **59 passed** |
| `python -m pytest tests/test_golden_replay.py -q` | 59 passed (marker lane broken) | **59 passed** |

---

## AF-2 Governance Mirror Removal

**Block:** Remove duplicate/drifting `game/*.md` governance mirrors; `docs/` is sole authority.

### Deleted `game/*.md` mirrors (3)

| Removed | Canonical authority |
| --- | --- |
| `game/state_authority_model.md` | `docs/state_authority_model.md` (byte-identical) |
| `game/validation_layer_separation.md` | `docs/validation_layer_separation.md` (docs superset, +485 B) |
| `game/narrative_integrity_architecture.md` | `docs/narrative_integrity_architecture.md` (docs superset, +209 B) |

No unique content in `game/` copies required porting. No pointer stubs added — pre-existing references already targeted `docs/` paths.

### Validation outcome

```text
python -m pytest tests/test_ownership_registry.py -q          # 17 passed
python -m pytest tests/test_validation_coverage_audit.py -q   # 5 passed
python tools/validation_coverage_audit.py --strict            # exit 0
python -m pytest -m golden_replay -q                          # 59 passed
```

---

## AF-3 Cycle Closure Normalization

**Block:** Consolidate cycle recon/closure docs under `docs/cycles/`

### `docs/cycles/` established as canonical

**New index:** `docs/cycles/README.md`

Cycle recon, closure, and block reports (Cycles H–AE + R) now live in one folder. Active CI closeouts and executable registries remain under `docs/` as documented in the index.

### Files relocated (43)

| Source | Count |
| --- | ---: |
| Repo root (`cycle_ad_*`, `cycle_ae_*`) | 4 |
| `tests/cycle_r_*` | 7 |
| `docs/reports/cycle_*` | 32 |

**Total after normalization:** 49 cycle markdown files + `README.md` index.

No byte-identical duplicates deleted — split-location pairs merged by move only.

### References updated

Bulk path rewrite across **29 markdown files** (`docs/reports/cycle_` → `docs/cycles/cycle_`, `tests/cycle_r_` → `docs/cycles/cycle_r_`), including cycle cross-links, `tests/TEST_AUDIT.md`, and audit recon memos.

### Validation outcome

```text
python -m pytest tests/test_ownership_registry.py -q          # 17 passed
python -m pytest tests/test_validation_coverage_audit.py -q   # 5 passed
python tools/validation_coverage_audit.py --strict            # exit 0
python -m pytest -m golden_replay -q                          # 59 passed
```

---

## AF-4 Replay Baseline Retirement

**Block:** Retire obsolete documentary replay baselines

### Replay baseline docs archived (2)

Moved from `audits/` → `docs/archive/dead_governance/2026-05-31/`:

1. `golden_replay_baseline_2026-05-11.md` — pre–Cycle K human-readable scenario baseline (9 rows); not loaded by pytest
2. `golden_replay_readiness_2026-05-11.md` — pre-promotion readiness recon (Cycle Track A)

### Protected replay manifest as sole authority

**`docs/testing/protected_replay_manifest.md`** is now the sole current protected replay acceptance authority. Stale “current baseline artifact” / “documentary baseline” pointers in **10 files** were redirected to the manifest with archival wording. Executable gate unchanged: `python -m pytest -m golden_replay -q`.

### Validation outcome

```text
python -m pytest tests/test_ownership_registry.py -q          # 17 passed
python -m pytest tests/test_validation_coverage_audit.py -q   # 5 passed
python tools/validation_coverage_audit.py --strict            # exit 0
python -m pytest -m golden_replay -q                          # 59 passed
python tools/refresh_protected_replay_manifest.py --check     # exit 0, manifest in sync
```

---

## Net Governance Contraction

| Metric | Count | Notes |
| --- | ---: | --- |
| **Files archived** | **18** | 16 (AF-1) + 2 (AF-4) → `docs/archive/dead_governance/2026-05-31/` |
| **Files removed** | **3** | AF-2 `game/*.md` mirror deletes |
| **Files relocated** | **43** | AF-3 cycle docs → `docs/cycles/` |
| **Reference rewrites** | **39+** | 29 path updates (AF-3) + 10 authority redirects (AF-4) |
| **Duplicate authorities eliminated** | **5 clusters** | See below |
| **Canonical locations created/confirmed** | **3** | See below |

### Duplicate authorities eliminated

1. **`game/` vs `docs/` architecture mirrors** (3 pairs) — AF-2; `docs/` only
2. **Replay baseline vs manifest dual acceptance docs** — AF-4; manifest only
3. **Cycle doc split locations** (root / `docs/reports/` / `tests/` vs `docs/cycles/`) — AF-3; single folder
4. **Failure-dashboard operational memos vs classifier harness** — AF-1; active tests + `failure_dashboard_latest.md` remain
5. **Stale “documentary baseline” wording in runbooks** — AF-4; manifest + archive path

### Canonical governance locations created or confirmed

| Location | Role |
| --- | --- |
| `docs/archive/dead_governance/2026-05-31/` | Historical dead/superseded audit memos (indexed README) |
| `docs/cycles/` | Cycle recon/closure/block reports (H–AF) |
| `docs/testing/protected_replay_manifest.md` | Protected golden replay acceptance (with `tools/refresh_protected_replay_manifest.py --check`) |

---

## Governance Authorities Remaining

Surviving executable and documentary authorities (unchanged in protection scope):

| Authority | Role |
| --- | --- |
| `docs/testing/protected_replay_manifest.md` | Protected replay scenario classification + field paths |
| `docs/architecture_ownership_ledger.md` | Runtime → test ownership routing |
| `docs/convergence_ci_inventory.md` | CI seam → enforcement matrix |
| `tests/test_ownership_registry.py` | Test direct-owner registry (CI hard-fail) |
| `tests/validation_coverage_registry.py` | Objective #12 feature → surface map |
| `docs/gate_convergence_closeout.md` | Gate maintenance-grade freeze (CI) |
| `docs/evaluator_convergence_closeout.md` | Evaluator maintenance-grade freeze (CI) |

Related authorities intentionally not modified during AF: `game/contract_registry.py`, `game/validation_layer_contracts.py`, `game/state_authority.py`, `docs/final_emission_ownership_convergence.md`, `tests/test_inventory.json`, `tools/test_audit.py`, `.github/workflows/convergence-checks.yml`.

---

## Validation Summary

Final closeout validation (2026-05-31):

```bash
python -m pytest tests/test_ownership_registry.py -q
python -m pytest tests/test_validation_coverage_audit.py -q
python tools/validation_coverage_audit.py --strict
python -m pytest -m golden_replay -q
```

```text
tests/test_ownership_registry.py              17 passed
tests/test_validation_coverage_audit.py        5 passed
tools/validation_coverage_audit.py --strict    exit 0 — Registry validation OK
-m golden_replay                               59 passed (~28s)
```

All governance registries, protected replay gate, and validation coverage audit remained green across every AF block.

---

## Success Assessment

### Surface area

**Reduced.** Eighteen audit memos and logs removed from active `audits/` paths; three duplicate `game/*.md` mirrors deleted; forty-three cycle docs consolidated under one index. Operators no longer need to choose between `docs/reports/`, repo root, or `tests/` for cycle history.

### Maintenance drag

**Reduced.** Zero-ref failure-dashboard and Cycle E/F/G memos no longer appear in routine greps. Drifting `game/` doc copies eliminated. Stale replay baseline pointers no longer compete with the manifest. AF-1B fixed a latent collection break that would have blocked `-m golden_replay` CI parity.

### Operability

**Improved or unchanged.** Protection unchanged: ownership registry, validation coverage audit, golden replay (59 tests), and convergence closeouts all pass. Navigation improved via `docs/cycles/README.md` and `docs/archive/dead_governance/2026-05-31/README.md`. Deferred candidates (e.g. `docs/post_evaluator_next_target_scan.md`, `docs/ownership_cleanup_delta.md`, non-zero-ref failure-dashboard memos) remain documented in recon for future optional passes.

---

## Follow-On Recommendation

**No further governance contraction** unless a future audit identifies new dead authority surfaces.

Cycle AF addressed recon-prioritized low-risk clusters. Remaining deferred items in the recon report carry non-zero reference counts or medium merge risk and were intentionally excluded. Next maintenance work should focus on feature/runtime cycles rather than additional doc pruning unless drift reappears.

---

## Files to pass back to ChatGPT

- `docs/cycles/cycle_af_dead_governance_removal_closure_2026-05-31.md` (this document)
- `docs/cycle_af_dead_governance_removal_recon_2026-05-31.md`
- `docs/cycles/README.md`
- `docs/archive/dead_governance/2026-05-31/README.md`

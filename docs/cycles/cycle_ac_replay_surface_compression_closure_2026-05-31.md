# Cycle AC — Replay Surface Compression Closure

Date: 2026-05-31  
Status: **Cycle AC closed** (AC-1 through AC-5 complete)

Reference recon: `docs/cycles/cycle_ac_replay_surface_compression_recon_2026-05-31.md`

---

## 1. Executive Summary

Cycle AC completed successfully. All five implementation blocks landed as **test-only** refactors with no changes to runtime behavior, replay projection logic, protected replay manifest content, or golden output bytes.

Replay authority is preserved: `tests/helpers/golden_replay_projection.py` remains the canonical payload/snapshot → observed-turn projection adapter; protected field paths and drift buckets are unchanged.

Maintenance burden is reduced by extracting scenario harness code, direct-seam observed-turn normalization, protected expectation composition, shared drift evaluation, and synthetic projection payload builders into named helper surfaces with clearer ownership.

No runtime code, projection code, or manifest files were modified.

---

## 2. Blocks Completed

### AC-1 — Scenario harness extraction

| Item | Detail |
|------|--------|
| **Files changed** | `tests/helpers/golden_replay_fixtures.py` (new), `tests/test_golden_replay.py` (imports/repoint) |
| **Helpers added** | `gm_response`, `suppress_intent_parsers`, `install_golden_chat_callable`, `install_golden_chat_stub`, `golden_replay_chat_stubs`, `seed_investigator_runner_world`, `seed_runner_guard_world`, `seed_runner_continuity_world`, `seed_tavern_patrol_lead_world`, `seed_scene_object_investigation_world`, `seed_spine_three_branch_world`, `seed_frontier_gate_world` |
| **Duplication removed** | Seven inline `_seed_*` world builders and repeated intent-parser + `call_gpt` monkeypatch blocks in integration replay tests |
| **Validation** | Protected integration replay scenarios pass unchanged; scenario IDs and seed semantics preserved |

### AC-2 — Direct-seam observed-turn normalization

| Item | Detail |
|------|--------|
| **Files changed** | `tests/helpers/golden_replay_fixtures.py`, `tests/test_golden_replay.py` |
| **Helpers added** | `observed_turn_from_gate_output`, `_merge_direct_seam_extra_fields` |
| **Duplication removed** | Hand-built observed-turn dicts and manual `fallback_family_used or realization_fallback_family` reads in direct-seam tests; projection now flows through `project_turn_observation` |
| **Validation** | Direct-seam structural tests pass; FEM fields and extra assertion merges unchanged |

### AC-3 — Protected expectation composition

| Item | Detail |
|------|--------|
| **Files changed** | `tests/helpers/golden_replay.py`, `tests/test_golden_replay.py` |
| **Helpers added** | `protected_structural_expectation` (composes existing `protected_*` fragments) |
| **Duplication removed** | Repeated `require_present` + `**protected_unavailable_expectation` + route/source/scaffold spreads in six protected E2E tests; sanitizer inline forbidden-term list replaced with `protected_no_scaffold_expectation(extra_terms=(...))` |
| **Validation** | All protected scenario IDs unchanged; assertion semantics preserved (including assert-only unavailable wording and not-equals reason variants) |

### AC-4 — Drift evaluation dedup

| Item | Detail |
|------|--------|
| **Files changed** | `tests/helpers/golden_replay.py` |
| **Helpers added** | `_evaluate_golden_expectation`, `_allow_unavailable_paths`, `_unavailable_paths`, `_assert_expected_for_issue`, `_assert_reason_for_issue` |
| **Duplication removed** | ~120 lines of parallel expectation evaluation between `assert_golden_turn_observation` and `classify_golden_drift`; `exact_text` drift remains classify-only |
| **Validation** | Public helper signatures unchanged; protected replay failure recording and failure-dashboard behavior unchanged; drift output shape unchanged |

### AC-5 — Synthetic projection payload builders

| Item | Detail |
|------|--------|
| **Files changed** | `tests/helpers/golden_replay_fixtures.py`, `tests/test_golden_replay.py` |
| **Helpers added** | `fem_payload`, `minimal_gm_output_payload`, `minimal_turn_payload`, `project_synthetic_turn` |
| **Duplication removed** | Inline nested `{scenario_id, snap, payload: {gm_output: {_final_emission_meta: ...}}}` shapes in 22 synthetic projection tests |
| **Validation** | FEM field values and scenario IDs preserved; integration replay paths still use real chat `snap`/`payload` |

---

## 3. Metrics

### Line count movement (HEAD → working tree at closure)

| File | Before | After | Delta |
|------|-------:|------:|------:|
| `tests/test_golden_replay.py` | 2,620 | 2,590 | **−30** |
| `tests/helpers/golden_replay.py` | 1,379 | 1,535 | **+156** |
| `tests/helpers/golden_replay_fixtures.py` | — (new) | 460 | **+460** |

Working-tree diff vs HEAD on touched golden files: `test_golden_replay.py` **548 insertions / 857 deletions** (net −309 churn); `golden_replay.py` **194 insertions / 179 deletions** (net +15).

Recon baseline noted ~2,620 lines and 56 tests in `test_golden_replay.py`; closure state is **2,590 lines** and **59 collected tests** (includes tests added during adjacent cycle work; no scenarios deleted).

### Helper surface added

| Module | New / consolidated public helpers |
|--------|-----------------------------------|
| `golden_replay_fixtures.py` | 17 functions (seeds, chat stubs, direct-seam projection, synthetic payload builders) |
| `golden_replay.py` | `protected_structural_expectation` + private `_evaluate_golden_expectation` pipeline |

Existing `protected_*_expectation` fragments remain backward-compatible.

### Replay tests passing

| Suite | Collected | Result |
|-------|--------:|--------|
| `tests/test_golden_replay.py` | 59 | **59 passed** |
| `tests/test_failure_classifier.py` | 66 | **66 passed** |
| `tests/test_failure_dashboard_controlled_failures.py` | 28 | **28 passed** |
| **Total closure bundle** | **153** | **153 passed** |

Recon baseline: 58 golden replay tests passed; closure adds one net golden test without removing coverage.

### Duplicate categories eliminated or reduced

| Category | Status |
|----------|--------|
| Scenario seed / monkeypatch harness (Group B, C) | **Extracted** → `golden_replay_fixtures.py` |
| Direct-seam observed-turn scaffolds (Group D) | **Normalized** → `observed_turn_from_gate_output` |
| Protected expectation boilerplate (Group A) | **Reduced** → `protected_structural_expectation` + sanitizer helper adoption |
| Drift assert/classify mirror logic (Group E) | **Deduped** → `_evaluate_golden_expectation` |
| Synthetic projection inline payloads | **Reduced** → `fem_payload` / `minimal_*` / `project_synthetic_turn` |
| Scaffold term bans across smoke vs replay (Group G) | **Unchanged by design** — documented separation retained |

---

## 4. Validation

Final command bundle (2026-05-31):

```text
python -m pytest tests/test_golden_replay.py -q
python -m pytest tests/test_failure_classifier.py -q
python -m pytest tests/test_failure_dashboard_controlled_failures.py -q
```

| Suite | Result |
|-------|--------|
| `tests/test_golden_replay.py` | **59 passed** |
| `tests/test_failure_classifier.py` | **66 passed** |
| `tests/test_failure_dashboard_controlled_failures.py` | **28 passed** |

All closure criteria met: no assertion meaning changes observed; no golden output updates required.

---

## 5. Governance Notes

- **No replay scenarios deleted.** All protected and supporting scenario IDs preserved.
- **No golden outputs changed.** Structural/predicate assertions only; no opt-in exact-text drift baselines updated.
- **No protected replay manifest changes.** `docs/testing/protected_replay_manifest.md` untouched; manifest sync test still passes.
- **No runtime code changed.** `game/` modules and `golden_replay_projection.py` projection logic unchanged.
- **Projection authority** remains in `tests/helpers/golden_replay_projection.py` (and runtime read-side FEM in `game/final_emission_replay_projection.py`).
- **Replay helper ownership** is now clearer:
  - `golden_replay_projection.py` — projection + protected field registry
  - `golden_replay.py` — runner, drift, protected expectation fragments/composer, long-session summaries
  - `golden_replay_fixtures.py` — integration seeds/stubs, direct-seam bridge, synthetic payload builders

---

## 6. Remaining / Deferred Work

Out of scope for Cycle AC (optional follow-ups only):

- Further readability cleanup in drift inline tests that use bare observed dicts (not projection payloads)
- Integration-path builder adoption only where it improves readability without obscuring real chat payloads
- Broader `protected_structural_expectation` adoption in conditional/branch-specific protected tests where composition is not clearly simpler

---

## 7. Final Status

**Cycle AC: Closed.**

All blocks AC-1 through AC-5 are complete. Replay surface compression goals are met with preserved authority and passing validation suites.

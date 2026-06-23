# Cycle AS6 — Equivalence Harness Gate Decoupling Implementation Summary

**Date:** 2026-06-04  
**Block:** AS6 — Refactor block S/T/U equivalence harnesses off scattered private gate coupling  
**Behavior change:** None (import/harness relocation only)

---

## Files changed

| File | Change |
| --- | --- |
| `tests/helpers/block_stu_equivalence_fixtures.py` | **New** — `locked_runner_contract`, `stub_strict_social_details` |
| `tests/helpers/gate_equivalence_monkeypatch.py` | **New** — centralized gate monkeypatch + phase-order trackers |
| `tests/helpers/speaker_gate_order.py` | Phase constants + `CHAIN_SOCIAL_TO_POST_SPEAKER` |
| `tests/helpers/speaker_relocation_shadow_harness.py` | Uses monkeypatch helpers; fixture build via helpers |
| `tests/helpers/post_speaker_finalize_probe.py` | AS6 retained-seam documentation |
| `tests/test_block_s_speaker_local_rebind_equivalence.py` | No `feg` import; helpers only |
| `tests/test_block_t_speaker_relocation_shadow_equivalence.py` | No test-to-test / no `feg` import |
| `tests/test_block_u_finalize_stack_divergence.py` | No test-to-test / no `feg` import |
| `tests/test_golden_replay.py` | Direct-seam test uses STU fixtures + monkeypatch helpers; removed unused `feg` import |

---

## Private gate imports/calls removed (from S/T/U test modules)

| Removed from test files | Replacement |
| --- | --- |
| `import game.final_emission_gate as feg` | **Removed** from `test_block_s`, `test_block_t`, `test_block_u`, `test_golden_replay` (direct-seam test) |
| Inline `monkeypatch.setattr(feg, "get_speaker_selection_contract", …)` | `patch_get_speaker_selection_contract` |
| Inline `monkeypatch.setattr(feg, "build_final_strict_social_response", …)` | `patch_build_final_strict_social_response` (+ optional `build_inputs`) |
| Phase-order `feg._*` wraps in `test_block_s` | `install_strict_social_trunk_phase_trackers` (helper module) |
| `_locked_runner_contract` / `_stub_strict_social_details` local defs | `block_stu_equivalence_fixtures` |

**Test modules now call public gate entry points only:**

- `apply_final_emission_gate`
- `enforce_emitted_speaker_with_contract`

---

## Private gate imports/calls retained (with reason)

| Location | Symbol(s) | Reason |
| --- | --- | --- |
| `gate_equivalence_monkeypatch.install_strict_social_trunk_phase_trackers` | `feg._enforce_response_type_contract`, `feg._apply_narrative_authenticity_layer`, `feg._apply_tone_escalation_layer`, `feg._apply_narrative_authority_layer`, `feg._apply_anti_railroading_layer`, `feg._apply_scene_state_anchor_layer` | **Layer ordering proof** — must wrap private trunk callables to record phase sequence (Block S) |
| `gate_equivalence_monkeypatch` | `feg.build_final_strict_social_response`, `feg.get_speaker_selection_contract` | Patched on gate namespace (gate imports these symbols for orchestration) |
| `post_speaker_finalize_probe.install_post_speaker_text_probes` | 15+ `feg._apply_*`, `feg._strip_dialogue_from_text`, `feg._finalize_emission_output`, etc. | **Post-speaker divergence inventory** — probes require wrapping private layer symbols; public gate entry cannot expose per-layer normalized deltas |
| `post_speaker_finalize_probe.chain_enforce_phase_marker` | `feg.enforce_emitted_speaker_with_contract` | Public entry; wrap marks post-speaker phase boundary |
| `speaker_relocation_shadow_harness.install_dual_run_enforce` | `feg.enforce_emitted_speaker_with_contract` | **Shadow equivalence** — must intercept gate enforcement path |
| `speaker_relocation_shadow_harness.run_isolated_enforce_mirror` | `sce._apply_speaker_contract_repairs` | Isolated repair path mirror (speaker_contract_enforcement owner seam) |
| `speaker_relocation_shadow_harness.run_isolated_enforce_mirror` | `feg.get_speaker_selection_contract`, `feg.validate_emitted_speaker_against_contract` | Defaults use gate namespace so monkeypatches on `feg.*` apply to both gate and isolated runs |

---

## Test-to-test imports removed

| Before | After |
| --- | --- |
| `test_block_t` → `test_block_s` (`_locked_runner_contract`, `_stub_strict_social_details`) | `tests/helpers/block_stu_equivalence_fixtures` |
| `test_block_u` → `test_block_s` (same) | same |
| `test_golden_replay` → `test_block_s` (same) | same |

**Block S/T/U/golden no longer import from each other.**

---

## Helpers extracted or created

### `block_stu_equivalence_fixtures.py`

- `locked_runner_contract()`
- `stub_strict_social_details()`

### `gate_equivalence_monkeypatch.py`

- `patch_get_speaker_selection_contract`
- `patch_build_final_strict_social_response` (optional `build_inputs` recording)
- `install_strict_social_trunk_phase_trackers`

### `speaker_gate_order.py` (expanded)

- `PHASE_*` constants, `CHAIN_SOCIAL_TO_POST_SPEAKER`
- `assert_phase_subsequence`, `normalized_player_text_equal` (unchanged)

### Reused (not modified in behavior)

- `speaker_relocation_shadow_harness` — `build_finalize_stack_fixture`, `install_dual_run_enforce`, `ShadowEnforceCapture`, …
- `post_speaker_finalize_probe` — divergence probe API
- `strict_social_harness.runner_strict_bundle`

`emission_smoke_assertions.py` was **not** expanded (per AS6 scope).

---

## FEM reads removed or retained

| Suite | AS6 action |
| --- | --- |
| Block S/T/U tests | **No change** — already on `final_emission_meta_from_output` (AS4/AS5) where FEM is read |
| `test_golden_replay.py` direct-seam test | **Retained** `read_fem_meta_from_gate_output` (replay helper) |

---

## Repair imports migrated or retained

No repairs-layer changes in AS6 (out of scope).

---

## Validation commands and results

| Command | Result |
| --- | --- |
| `python -m pytest tests/test_ownership_registry.py tests/test_final_emission_debt_retirement.py -q` | **PASS** (24) |
| `python -m pytest tests/test_block_s_speaker_local_rebind_equivalence.py -q` | **PASS** (4) |
| `python -m pytest tests/test_block_t_speaker_relocation_shadow_equivalence.py -q` | **PASS** (4) |
| `python -m pytest tests/test_block_u_finalize_stack_divergence.py -q` | **PASS** (6) |
| `python -m pytest tests/test_golden_replay.py -q` | **PASS** (68) |

Combined block S/T/U + ownership sweep: **PASS** (38 + 24).

---

## Recommendation: AS closeout (optional AS7 only if pursued)

**AS cycle closeout is appropriate.** AS1–AS6 achieved the recon goals:

- Fixture hub retired; downstream facades for smoke, repairs, FEM reads, and equivalence monkeypatch
- Block S/T/U tests decoupled from direct `feg` imports and test-to-test fixture imports
- Retained private seams are documented and confined to narrow helper modules with explicit reasons

**Optional AS7 (low priority, outside required closeout):**

- Extract remaining repo-wide test-to-test imports (`test_n5` → `test_narrative_plan_prompt_regressions`, `test_referential_clarity_player_coref` → visibility owner, etc.)
- Thin FEM reads in remaining non-owner suites (`test_dialogue_plan_final_emission_gate.py`, `test_fallback_overwrite_containment.py`, …)
- Production-side: consider public observation hooks for post-speaker layer inventory (would allow retiring `post_speaker_finalize_probe` private wraps — **high effort**, gate-owner change)

**Do not proceed beyond AS6 in this block.**

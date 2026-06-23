# Cycle AG — Residual Complexity Burn-Down Closure

**Date:** 2026-05-31  
**Scope:** Test-helper locality, governance, replay/test boilerplate, and documentation/tooling cleanup only.  
**Runtime status:** No runtime modules changed.

---

## Executive Summary

Cycle AG burned down the residual maintenance and test-owner complexity identified in the recon pass without changing final-emission, fallback, replay, or speaker-repair behavior.

The cycle mostly succeeded as planned:

- High-fanout HTTP seed setup moved out of `tests/test_turn_pipeline_shared.py`.
- Block AI sealed fallback helper-shape assertions moved out of the gate orchestration owner.
- Golden replay protected structural boilerplate gained helper-owned composers.
- Block S/T/U finalize-stack setup now has one shared harness builder.
- Failure-classifier synthetic row setup and opening fallback evidence literals were centralized further.
- Governance now blocks read-side projection assertion creep back into `tests/test_final_emission_gate.py`.

AG-8 was intentionally a no-op after inspection: the remaining protected E2E assertions did not exactly match the AG-5 composer shape without changing expected observation semantics.

---

## Block Outcomes

| Block | Outcome | Notes |
| --- | --- | --- |
| AG-1 — Manifest/registry CI decoupling | Completed | `tools/refresh_protected_replay_manifest.py` now renders from `protected_observation_field_registry()`, manifest parity is asserted from golden replay tests, and CI runs the manifest check. |
| AG-2 — Turn pipeline HTTP fixture extraction | Completed | Shared HTTP seed/patch helpers moved into `tests/helpers/turn_pipeline_http_fixtures.py`; consumer suites import the helper instead of reaching into `tests/test_turn_pipeline_shared.py`. |
| AG-3 — Gate Block AI helper-shape migration | Completed | Pure sealed fallback dataclass/tuple/importability/provider tests moved to `tests/test_final_emission_sealed_fallback.py`; gate-private wrapper and orchestration tests stayed in `tests/test_final_emission_gate.py`. |
| AG-4 — Downstream smoke facade extension | Completed | `tests/helpers/emission_smoke_assertions.py` gained reusable smoke assertions and downstream social/HTTP suites were thinned to consume them. |
| AG-5 — Protected social structural composer | Completed | `protected_social_structural_base(...)` was added to `tests/helpers/golden_replay.py` and adopted by exact-match protected social replay assertions. |
| AG-6 — Block S/T/U finalize-stack harness | Completed | `build_finalize_stack_fixture(...)` now owns shared strict-social finalize-stack construction; divergence and phase-order assertions remain local. |
| AG-7 — Classifier synthetic row builder dedup | Completed | `tests/helpers/failure_classification_sync.py` now owns classifier-shaped synthetic observed rows and expected-field synchronization helpers. |
| AG-8 — Golden replay E2E boilerplate adoption | No-op after inspection | Existing compatible protected social clusters were already converted. Remaining protected assertions are action/opening/sanitizer/direct-seam or conditional probes, so changing them would alter assertion shape. |
| AG-9 — Opening FEM literal migration | Completed, conservative | Repeated successful opening observed-field literals now route through `successful_opening_observed_fields(...)`; fail-closed/conflicting/dual-family edge literals remain inline. |
| AG-10 — Ownership registry creep guard | Completed | `tests/test_ownership_registry.py` now statically rejects read-side replay/FEM projection ownership symbols in `tests/test_final_emission_gate.py`. |

---

## Files Changed

### Added

- `tests/helpers/turn_pipeline_http_fixtures.py`
- `tests/test_final_emission_sealed_fallback.py`
- `docs/cycles/cycle_ag_residual_complexity_burndown_closure_2026-05-31.md`

### Modified

- `.github/workflows/convergence-checks.yml`
- `docs/testing/protected_replay_manifest.md`
- `tools/refresh_protected_replay_manifest.py`
- `tests/helpers/emission_smoke_assertions.py`
- `tests/helpers/failure_classification_sync.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/speaker_relocation_shadow_harness.py`
- `tests/test_block_s_speaker_local_rebind_equivalence.py`
- `tests/test_block_t_speaker_relocation_shadow_equivalence.py`
- `tests/test_block_u_finalize_stack_divergence.py`
- `tests/test_broadcast_open_call_social.py`
- `tests/test_empty_social_retry_regressions.py`
- `tests/test_failure_classifier.py`
- `tests/test_final_emission_gate.py`
- `tests/test_golden_replay.py`
- `tests/test_interaction_continuity_repair.py`
- `tests/test_manual_play_latency.py`
- `tests/test_narration_transcript_regressions.py`
- `tests/test_new_campaign_silent_reset_nc2.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/test_opening_start_seam_regressions.py`
- `tests/test_ownership_registry.py`
- `tests/test_playability_smoke.py`
- `tests/test_social_speaker_grounding.py`
- `tests/test_start_campaign_api.py`
- `tests/test_turn_pipeline_shared.py`
- `tests/test_turn_trace_contract.py`

### Audit Inputs

- `audits/cycle_ag_residual_complexity_burndown_recon_2026-05-31.md`
- `audits/cycle_ag_hotspot_inventory.json`

---

## Validation Passed

Validation observed during AG block execution:

- `python -m pytest tests/test_golden_replay.py -q`
- `python -m pytest -m golden_replay -q`
- `python -m pytest tests/test_final_emission_gate.py -k "sealed_fallback_selection or legacy_tuple or visibility_tuple or selector_helpers or assembly_helpers" -q`
- `python -m pytest tests/test_final_emission_sealed_fallback.py -q`
- `python -m pytest tests/test_final_emission_visibility_fallback.py -q`
- `python -m pytest tests/test_gate_convergence_closeout.py -q`
- `python -m pytest tests/test_block_s_speaker_local_rebind_equivalence.py -q`
- `python -m pytest tests/test_block_t_speaker_relocation_shadow_equivalence.py -q`
- `python -m pytest tests/test_block_u_finalize_stack_divergence.py -q`
- `python -m pytest tests/test_opening_fallback_owner_bucket.py -q`
- `python -m pytest tests/test_upstream_response_repairs.py -q`
- `python -m pytest tests/test_final_emission_meta.py -q`
- `python -m pytest tests/test_golden_replay.py -k opening -q`
- `python -m pytest tests/test_ownership_registry.py -q`
- `python -m pytest tests/test_final_emission_gate.py -q`

Recommended final pre-merge validation if this closure is batched with other local changes:

- `python tools/refresh_protected_replay_manifest.py --check`
- `python -m pytest tests/test_turn_pipeline_shared.py -q`
- `python -m pytest tests/test_failure_classifier.py tests/test_failure_classification_contract.py -q`
- `python -m pytest tests/test_ownership_registry.py tests/test_final_emission_gate.py tests/test_final_emission_meta.py -q`

---

## Measurable Complexity Reductions

Tracked diff before this closure artifact showed **542 insertions / 751 deletions** across changed tracked files, a net reduction of **209 tracked lines** before counting new owner/helper files.

Most visible reductions:

- `tests/test_final_emission_gate.py`: **3 insertions / 307 deletions** tracked, with pure sealed fallback helper-shape coverage moved to `tests/test_final_emission_sealed_fallback.py`.
- `tests/test_turn_pipeline_shared.py`: **7 insertions / 92 deletions**, with HTTP seed setup moved to `tests/helpers/turn_pipeline_http_fixtures.py`.
- `tests/test_failure_classifier.py`: **32 insertions / 115 deletions**, with synthetic row setup routed through `tests/helpers/failure_classification_sync.py`.
- Block S/T/U duplicated finalize-stack setup now routes through one helper in `tests/helpers/speaker_relocation_shadow_harness.py`.
- Golden replay protected social boilerplate now uses `protected_social_structural_base(...)` where expectation shape is equivalent.
- Opening fallback successful observed-field literals now route through `successful_opening_observed_fields(...)`.

Governance reductions:

- Protected replay manifest drift now has a registry-backed check path.
- Gate owner tests are guarded against read-side replay projection assertion creep.
- Downstream smoke suites consume helper-owned assertions instead of re-owning gate tables.

---

## No-Op / Deferred Outcomes

- **AG-8 no-op:** no remaining protected E2E clusters were exact matches for `protected_social_structural_base(...)`. Opening/fallback/direct-seam and action/sanitizer assertions stayed inline.
- **Opening fail-closed literals deferred:** fail-closed and conflicting-signal opening owner-bucket tests intentionally keep inline literals because they encode edge behavior.
- **Gate wrapper tests retained:** gate-private selectors/wrappers remain in `tests/test_final_emission_gate.py` because they protect orchestration boundaries, not helper-shape ownership.
- **Runtime simplification deferred:** no gate orchestration, fallback tuple retirement, or runtime helper extraction was attempted in AG.

---

## Remaining Risks

- `tests/test_final_emission_gate.py` remains a large direct owner even after the helper-shape move; only pure helper contracts were migrated.
- `tests/test_golden_replay.py` still hosts protected scenario assertions and long-session stability checks by design; further compression must preserve scenario IDs and protected observation paths.
- `tests/test_inventory.json` remains a large closure amplifier and should stay isolated from logic/test-helper commits unless intentionally regenerated.
- Some downstream suites still contain thin route/meta smoke assertions; governance now helps, but review discipline is still needed to prevent table re-expansion.
- The new source-text ownership guard is intentionally narrow; it blocks named read-side projection surfaces but will not catch every possible semantic duplicate.

---

## Recommended Next Cycle

No urgent Cycle AH runtime work is implied by AG. The best next cycle would be another **test/locality-only** pass, with two candidate lanes:

1. **AH-1: Gate owner size reduction, integration-only slice**  
   Move only additional pure helper/importability/shape tests out of `tests/test_final_emission_gate.py` when an owning module already exists. Do not touch orchestration order or final route semantics.

2. **AH-2: Inventory and closure hygiene**  
   Formalize an inventory-regeneration workflow so `tests/test_inventory.json` changes are isolated, reviewed separately, and not bundled with behavior or helper cleanup.

Avoid in the next cycle unless explicitly scoped: runtime final-emission gate refactors, fallback tuple retirement, replay scenario reshaping, or protected observation path changes.

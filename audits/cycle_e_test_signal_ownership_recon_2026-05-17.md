# Cycle E Recon: Test Signal / Ownership Thinning - 2026-05-17

## Executive Summary

Recommended Cycle E target: **fallback**, narrowed to the **fallback_behavior contract/validator/repair/gate propagation cluster**.

This is the safest first thinning family because ownership is already partially declared in test docstrings, duplicate fixtures are obvious, and the runtime owner boundary is clear:

- `tests/test_final_emission_validators.py` owns `validate_fallback_behavior()` predicate semantics.
- `tests/test_final_emission_repairs.py` owns `repair_fallback_behavior()` and `_apply_fallback_behavior_layer()` helper semantics.
- `tests/test_fallback_behavior_gate.py` should stay downstream orchestration coverage for `apply_final_emission_gate()`.
- `tests/test_fallback_behavior_repairs.py` should stay downstream consumer coverage for retry/gate metadata propagation.

No runtime behavior, production code, assertions, or tests were changed by this recon pass.

## Exact Commands Used

Inventory commands:

```powershell
(Get-ChildItem -Path tests -File | Measure-Object).Count
rg -l "final emission|final_emission" tests | Sort-Object
rg -l "dialogue|speaker|social|NPC|npc" tests | Sort-Object
rg -l "fallback" tests | Sort-Object
rg -l "route" tests | Sort-Object
(rg -l "final emission|final_emission" tests | Measure-Object).Count
(rg -l "dialogue|speaker|social|NPC|npc" tests | Measure-Object).Count
(rg -l "fallback" tests | Measure-Object).Count
(rg -l "route" tests | Measure-Object).Count
pytest --collect-only -q
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest --collect-only -q
```

`pytest --collect-only -q` failed because `pytest` is not on PATH in this shell. The bundled runtime plus `.venv` site-packages command succeeded.

Read-only analysis commands:

```powershell
rg --files tests
rg --files game | rg "fallback|final_emission|gm_retry|gm.py|api.py|upstream_response_repairs|realization|social_exchange|interaction_context|response_policy"
rg -n "fallback" tests\test_final_emission_gate.py
rg -n "fallback" tests\test_final_emission_repairs.py
rg -n "fallback" tests\test_final_emission_validators.py
rg -n "fallback" tests\test_upstream_fast_fallback_block_l.py
rg -n "fallback_behavior|opening_fallback|fast_fallback|sealed_fallback|visibility_fallback" game\final_emission_gate.py game\final_emission_repairs.py game\final_emission_validators.py game\final_emission_meta.py game\fallback_provenance_debug.py game\upstream_response_repairs.py game\diegetic_fallback_narration.py game\gm_retry.py game\gm.py
```

AST/count scripts were run read-only through:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; @'
# read-only AST inventory script: parsed tests/test_*.py, counted test functions,
# assert nodes, and imported game.* modules for each keyword family.
'@ | & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -
```

## Repo-Level Test Inventory

| Inventory item | Count | Notes |
| --- | ---: | --- |
| Total top-level files under `tests/` | 312 | `Get-ChildItem -Path tests -File`; includes docs/json/helpers at top level, not nested helper files. |
| Recursive files mentioning `final emission` or `final_emission` | 120 | Includes helper modules and test docs. |
| Recursive files mentioning `dialogue`, `speaker`, `social`, `NPC`, or `npc` | 239 | Broadest family by far. |
| Recursive files mentioning `fallback` | 142 | Includes docs, helper classifiers, and many integration suites. |
| Recursive files mentioning `route` | 109 | Cross-cuts API, social, retry, final emission, and world routing. |

Collected test counts from successful `pytest --collect-only -q` run:

- 300 top-level pytest modules were collected.
- The collected surface is very broad: several files have high test density, especially `tests/test_final_emission_gate.py` with 281 collected tests, `tests/test_prompt_context.py` with 109, `tests/test_final_emission_boundary_contract.py` with 91, `tests/test_social_exchange_emission.py` with 88, and `tests/test_turn_pipeline_shared.py` with 67.

AST keyword-family estimate over `tests/test_*.py` only:

| Family query | Top-level test files | Approx. collected test functions | Approx. `assert` nodes | Most frequent production imports |
| --- | ---: | ---: | ---: | --- |
| `final emission` / `final_emission` | 106 | 1659 | 6362 | `game.gm`, `game.final_emission_gate`, `game.final_emission_meta`, `game.storage`, `game.defaults`, `game.api`, `game.interaction_context`, `game.social_exchange_emission`, `game.final_emission_repairs` |
| dialogue/speaker/social/NPC | 217 | 3103 | 11384 | `game.gm`, `game.storage`, `game.defaults`, `game.final_emission_gate`, `game.api`, `game.final_emission_meta`, `game.interaction_context`, `game.social_exchange_emission`, `game.ctir_runtime`, `game.prompt_context` |
| fallback | 130 | 2264 | 8537 | `game.gm`, `game.final_emission_gate`, `game.storage`, `game.final_emission_meta`, `game.defaults`, `game.api`, `game.interaction_context`, `game.social_exchange_emission`, `game.gm_retry`, `game.ctir_runtime` |
| route | 100 | 1875 | 7082 | `game.gm`, `game.storage`, `game.api`, `game.final_emission_gate`, `game.defaults`, `game.final_emission_meta`, `game.interaction_context`, `game.social_exchange_emission`, `game.gm_retry`, `game.upstream_response_repairs` |

## Candidate Family Map

### 1. Fallback

Files involved:

- Owner or near-owner: `tests/test_final_emission_validators.py`, `tests/test_final_emission_repairs.py`, `tests/test_opening_fallback_owner_bucket.py`, `tests/test_upstream_response_repairs.py`, `tests/test_diegetic_fallback_narration.py`, `tests/test_upstream_fast_fallback_block_l.py`, `tests/test_fallback_continuity_guard.py`.
- Downstream/gate: `tests/test_fallback_behavior_gate.py`, `tests/test_fallback_behavior_repairs.py`, `tests/test_fallback_overwrite_containment.py`, `tests/test_fallback_shipped_contract_propagation.py`, `tests/test_final_emission_gate.py`, `tests/test_turn_pipeline_shared.py`, `tests/test_empty_social_retry_regressions.py`, `tests/test_strict_social_emergency_fallback_dialogue.py`.
- Smoke/historical: `tests/test_transcript_regression.py`, `tests/test_synthetic_smoke.py`, `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_failure_classification_contract.py`, `tests/test_dead_turn_detection.py`.

Approximate size:

- 130 top-level test files mention fallback.
- 2264 test functions and 8537 assert nodes live in files that mention fallback.
- The focused `fallback_behavior` cluster is much smaller: about 4 direct files, 30 collected tests, and roughly 128 assert nodes:
  - `tests/test_fallback_behavior_validator.py`: 11 tests, 32 asserts.
  - `tests/test_final_emission_repairs.py`: 5 fallback-named tests, more skipped historical fallback tests in body.
  - `tests/test_fallback_behavior_gate.py`: 11 tests, 60 asserts.
  - `tests/test_fallback_behavior_repairs.py`: 3 tests, 18 asserts.

Major production modules referenced:

- `game.final_emission_validators`
- `game.final_emission_repairs`
- `game.final_emission_gate`
- `game.final_emission_meta`
- `game.gm`
- `game.gm_retry`
- `game.upstream_response_repairs`
- `game.fallback_provenance_debug`
- `game.diegetic_fallback_narration`
- `game.opening_deterministic_fallback`
- `game.final_emission_sealed_fallback`
- `game.final_emission_visibility_fallback`

Classification:

- Owner: validator semantics, repair helper semantics, opening owner-bucket mapper, upstream prepared opening payloads, provenance helpers.
- Downstream: gate ordering/application, retry debug consumption, API/start-campaign surfaces, turn-pipeline behavior.
- Smoke: transcript, golden replay, synthetic smoke, broad playability.
- Historical regression: fast fallback containment, empty social retry fallback, stale continuity fallback, opening fail-closed compatibility-local retirement.

Obvious duplication patterns:

- Repeated `_fallback_contract()` fixtures across `test_fallback_behavior_validator.py`, `test_final_emission_repairs.py`, `test_fallback_behavior_gate.py`, and `test_fallback_behavior_repairs.py`.
- Repeated assertions for meta voice removal: no `"enough information"`, `fallback_behavior_repaired`, `fallback_behavior_meta_voice_stripped`, and debug propagation.
- Gate/downstream files assert helper-level outcomes already owned by validator/repair suites.
- Existing docstrings already say some files are downstream only, making comment-only ownership clarification low risk.

### 2. Final Emission

Files involved:

- Dense owner/gate: `tests/test_final_emission_gate.py`, `tests/test_final_emission_boundary_contract.py`, `tests/test_final_emission_boundary_convergence.py`, `tests/test_final_emission_boundary_audit.py`, `tests/test_final_emission_meta.py`, `tests/test_final_emission_repairs.py`, `tests/test_final_emission_validators.py`, `tests/test_final_emission_visibility.py`.
- Downstream: `tests/test_api_narration_path_selection.py`, `tests/test_turn_pipeline_shared.py`, `tests/test_dialogue_plan_final_emission_gate.py`, `tests/test_dead_turn_detection.py`, `tests/test_gate_convergence_closeout.py`.
- Smoke/historical: `tests/test_golden_replay.py`, `tests/test_transcript_regression.py`, `tests/test_narration_transcript_regressions.py`, `tests/test_behavioral_gauntlet_smoke.py`.

Approximate size:

- 106 top-level test files mention final emission terms.
- 1659 test functions and 6362 assert nodes live in those files.
- `tests/test_final_emission_gate.py` alone has 281 collected tests.

Major production modules referenced:

- `game.final_emission_gate`
- `game.final_emission_meta`
- `game.final_emission_repairs`
- `game.final_emission_validators`
- `game.final_emission_boundary_contract`
- `game.final_emission_visibility_fallback`
- `game.final_emission_sealed_fallback`
- `game.gm`
- `game.api`
- `game.upstream_response_repairs`

Classification:

- Owner: `test_final_emission_gate.py` is mostly owner-level for orchestrator behavior; boundary contract/meta/validators/repairs have local owner slices.
- Downstream: API, turn pipeline, social/dialogue, golden replay, dead-turn, and gauntlet tests.
- Smoke: playability/transcript/behavioral gauntlet.
- Historical regression: many named Block C/D/G/H/L/AI tests are incident/path locks.

Obvious duplication patterns:

- Many tests reassert final route/source/meta fields after unrelated subsystems.
- Gate test owns too many orchestration details, but thinning is risky because Cycle D requires `final_emission_gate.py` to remain canonical orchestrator for fallback selection, prose-owner calls, output writes, metadata writes, logging, route branching, and tag/debug mutation.

Recon verdict:

- High value, but not the safest first Cycle E target. Touching this family first risks blurring the Cycle D architecture constraint.

### 3. Speaker

Files involved:

- Owner/near-owner: `tests/test_speaker_contract_enforcement.py`, `tests/test_speaker_contract_enforcement_extraction.py`, `tests/test_social_speaker_grounding.py`, `tests/test_dialogue_plan_final_emission_gate.py`, `tests/test_block_s_speaker_local_rebind_equivalence.py`, `tests/test_block_t_speaker_relocation_shadow_equivalence.py`, `tests/test_block_u_finalize_stack_divergence.py`.
- Downstream: `tests/test_turn_pipeline_shared.py`, `tests/test_social_exchange_emission.py`, `tests/test_dialogue_social_convergence.py`, `tests/test_interaction_continuity_speaker_bridge.py`, `tests/test_post_emission_speaker_adoption.py`.
- Smoke/historical: `tests/test_transcript_gauntlet_actor_addressing.py`, `tests/test_synthetic_smoke.py`, `tests/test_world_action_social_continuity_break.py`.

Approximate size:

- 217 top-level test files mention dialogue/speaker/social/NPC terms.
- 3103 test functions and 11384 assert nodes live in those files.

Major production modules referenced:

- `game.gm`
- `game.social_exchange_emission`
- `game.interaction_context`
- `game.final_emission_gate`
- `game.final_emission_meta`
- `game.social`
- `game.dialogue_social_plan`
- `game.api`
- `game.storage`

Classification:

- Owner: speaker contract enforcement, extraction, grounding, and final-emission dialogue-plan gate.
- Downstream: turn pipeline, strict-social emission, transcript, interaction continuity.
- Smoke: synthetic/social/transcript broad runs.
- Historical regression: Block S/T/U shadow equivalence and finalize-stack divergence tests.

Obvious duplication patterns:

- Repeated "wrong speaker repaired to canonical" and active interlocutor continuity checks across owner, final gate, turn pipeline, and transcript tests.
- However, social/speaker is extremely broad and entangled with route and dialogue. It is not a good first thinning target.

### 4. Route

Files involved:

- Owner/near-owner: `tests/test_api_narration_path_selection.py`, `tests/test_directed_social_routing.py`, `tests/test_dialogue_routing_lock.py`, `tests/test_local_observation_routing.py`, `tests/test_model_routing_runtime.py`, `tests/test_model_routing_escalation.py`.
- Downstream: `tests/test_turn_pipeline_shared.py`, `tests/test_exploration_resolution.py`, `tests/test_social_exchange_emission.py`, `tests/test_world_action_social_continuity_break.py`.
- Smoke/historical: `tests/test_transcript_regression.py`, `tests/test_synthetic_smoke.py`, `tests/test_gauntlet_regressions.py`.

Approximate size:

- 100 top-level test files mention route.
- 1875 test functions and 7082 assert nodes live in those files.

Major production modules referenced:

- `game.gm`
- `game.api`
- `game.final_emission_gate`
- `game.final_emission_meta`
- `game.gm_retry`
- `game.social_exchange_emission`
- `game.interaction_context`
- `game.upstream_response_repairs`

Classification:

- Owner: API narration path selection, route helper snapshots, directed social routing, local observation routing, model routing.
- Downstream: turn pipeline and transcripts.
- Smoke: synthetic and gauntlet.
- Historical regression: Block AJ/AK/AL/AM/AN route helper and policy handoff tests.

Obvious duplication patterns:

- Route labels and path metadata snapshots are repeated in API path-selection tests and broader turn-pipeline assertions.
- But the route family is still actively tied to policy handoff, API orchestration, and final emission. Safer after fallback ownership language is clarified.

## Recommendation: Thin Fallback First

Recommended target: **fallback_behavior duplicate tests**, not the entire fallback universe.

Why this target:

- Duplicate assertions are obvious and local.
- Existing comments already establish owner/downstream intent.
- `fallback_behavior` is a narrow enough subsystem to thin without touching Cycle D final-emission orchestration.
- Owner tests already exist for validator and repair semantics.
- Downstream tests can be converted later to smoke/metadata propagation checks without losing the only protection for important behavior.
- It reduces failure fanout: a helper-level text/metadata semantic change should fail `test_final_emission_validators.py` or `test_final_emission_repairs.py` first, not also three downstream consumer files.

Do not thin yet:

- Opening fallback, sealed fallback, visibility fallback, and fast fallback containment. Those are adjacent fallback surfaces but carry Cycle C/D closure and historical-regression value.
- `tests/test_final_emission_gate.py` broad fallback blocks. Some are good later candidates, but first pass should avoid destabilizing the canonical orchestrator coverage.

## Detailed Test Table: Recommended Fallback Behavior Cluster

| Test file | Test/function name | Current asserted behavior | Proposed classification | Likely failure owner | Keep/thin/comment-only | Reason | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `tests/test_fallback_behavior_validator.py` | `test_validate_fallback_behavior_skips_cleanly_without_contract` | Validator skips when no contract and marks pass/no contract. | owner | `game.final_emission_validators.validate_fallback_behavior` | keep | Direct predicate owner; downstream tests should not own skip semantics. | low |
| `tests/test_fallback_behavior_validator.py` | `test_validate_fallback_behavior_skips_cleanly_when_uncertainty_inactive` | Validator skips when uncertainty is inactive. | owner | `game.final_emission_validators.validate_fallback_behavior` | keep | Direct owner for inactive uncertainty skip. | low |
| `tests/test_fallback_behavior_validator.py` | `test_validate_fallback_behavior_fails_on_invented_certainty` | Unsupported certainty is detected and failure reason includes `invented_certainty`. | owner | `game.final_emission_validators.validate_fallback_behavior` | keep | Direct owner for certainty predicate. | low |
| `tests/test_fallback_behavior_validator.py` | `test_validate_fallback_behavior_fails_on_fabricated_authority` | Fabricated authority is detected and failure reason includes `fabricated_authority`. | owner | `game.final_emission_validators.validate_fallback_behavior` | keep | Direct owner for authority predicate. | low |
| `tests/test_fallback_behavior_validator.py` | `test_validate_fallback_behavior_fails_on_meta_fallback_voice` | Meta fallback voice is detected and classified. | owner | `game.final_emission_validators.validate_fallback_behavior` | keep | Should be first failure for meta voice detector changes. | low |
| `tests/test_fallback_behavior_validator.py` | `test_validate_fallback_behavior_catches_meta_adjudicative_uncertainty_leaks` | Parametrized meta adjudication leaks fail as meta fallback voice. | owner | `game.final_emission_validators.validate_fallback_behavior` | keep | Broader detector table; valuable owner coverage. | low |
| `tests/test_fallback_behavior_validator.py` | `test_validate_fallback_behavior_accepts_bounded_partial_shape` | Valid bounded partial shape passes with known/unknown/next-lead flags. | owner | `game.final_emission_validators.validate_fallback_behavior` | keep | Direct pass-shape owner. | low |
| `tests/test_fallback_behavior_validator.py` | `test_validate_fallback_behavior_rejects_bare_thin_identity_line_without_known_and_lead` | Thin identity line fails as insufficient bounded partial. | owner | `game.final_emission_validators.validate_fallback_behavior` | keep | Direct owner for thin-line rejection. | low |
| `tests/test_fallback_behavior_validator.py` | `test_validate_fallback_behavior_accepts_single_clarifying_question_when_partial_not_allowed` | Single clarifying question can pass under contract configuration. | owner | `game.final_emission_validators.validate_fallback_behavior` | keep | Contract matrix owner. | low |
| `tests/test_fallback_behavior_validator.py` | `test_validate_fallback_behavior_fails_when_question_count_exceeds_contract_cap` | Too many clarifying questions fail. | owner | `game.final_emission_validators.validate_fallback_behavior` | keep | Contract cap owner. | low |
| `tests/test_fallback_behavior_validator.py` | `test_validate_fallback_behavior_rejects_bare_question_when_partial_is_preferred` | Bare question fails when partial is preferred. | owner | `game.final_emission_validators.validate_fallback_behavior` | keep | Contract preference owner. | low |
| `tests/test_final_emission_repairs.py` | `test_repair_strips_meta_fallback_voice_while_preserving_grounded_content` | Repair strips meta voice, preserves grounded lead, records repair mode and no synthesis. | owner | `game.final_emission_repairs.repair_fallback_behavior` | keep | Direct repair semantics. | low |
| `tests/test_final_emission_repairs.py` | skipped bounded-partial synthesis tests | Historical skipped expectations from removed boundary synthesis behavior. | historical regression | `game.final_emission_repairs` | comment-only | Leave skipped history; possible later note that boundary synthesis is intentionally retired. | low |
| `tests/test_final_emission_repairs.py` | skipped diegetic rewrite tests | Historical skipped expectations for removed meta-voice diegetic rewrite. | historical regression | `game.final_emission_repairs` | comment-only | Documents removed behavior; not a thinning target unless cleanup is explicitly requested. | low |
| `tests/test_final_emission_repairs.py` | `test_fallback_behavior_layer_revalidates_once_after_repair` | Layer validates, repairs, and revalidates once. | owner | `game.final_emission_repairs._apply_fallback_behavior_layer` | keep | Direct layer sequencing owner. | low |
| `tests/test_final_emission_repairs.py` | skipped `test_fallback_behavior_layer_retains_safest_repaired_text_when_revalidation_still_fails` | Historical skipped behavior for retaining repaired text after revalidation failure. | historical regression | `game.final_emission_repairs._apply_fallback_behavior_layer` | comment-only | Already skipped with rationale; no Cycle E behavior change. | low |
| `tests/test_final_emission_repairs.py` | `test_fallback_behavior_layer_leaves_grounded_answers_untouched_when_uncertainty_is_inactive` | Layer skips repair and records inactive uncertainty. | owner | `game.final_emission_repairs._apply_fallback_behavior_layer` | keep | Direct layer skip owner; overlaps validator but owns layer metadata. | low |
| `tests/test_final_emission_repairs.py` | `test_fallback_behavior_layer_does_not_synthesize_without_contract_from_forceful_tone_alone` | Layer does not invent fallback behavior without a shipped contract. | owner | `game.final_emission_repairs._apply_fallback_behavior_layer` | keep | Important boundary-no-synthesis invariant. | low |
| `tests/test_fallback_behavior_gate.py` | `test_gate_repairs_meta_fallback_voice_into_bounded_partial` | Gate applies fallback behavior layer, strips meta voice, stamps FEM and emission debug. | downstream | `game.final_emission_gate.apply_final_emission_gate` for orchestration; helper semantics owned by repairs/validators | thin later | This repeats repair semantics plus metadata propagation. Keep only orchestration/debug assertions in later block. | medium |
| `tests/test_fallback_behavior_gate.py` | `test_gate_skips_fallback_behavior_when_uncertainty_inactive` | Gate preserves raw text and stamps skip metadata/debug when uncertainty inactive. | downstream | `game.final_emission_gate.apply_final_emission_gate`; skip semantics owned by validator/repair | thin later | Duplicate inactive-skip assertions exist in owner suites; downstream should verify gate wires metadata, not predicate internals. | low |
| `tests/test_fallback_behavior_gate.py` | `test_gate_runs_fallback_behavior_after_interaction_continuity_non_strict` | Gate calls interaction continuity before fallback behavior in non-strict path. | owner/downstream orchestration | `game.final_emission_gate.apply_final_emission_gate` | keep | Cycle D orchestrator ordering belongs in gate. | low |
| `tests/test_fallback_behavior_gate.py` | `test_gate_runs_fallback_behavior_after_strict_social_continuity` | Strict-social gate path runs continuity before fallback behavior and stamps checked meta. | owner/downstream orchestration | `game.final_emission_gate.apply_final_emission_gate` | keep | Gate owns path ordering and branch wiring. | low |
| `tests/test_fallback_behavior_gate.py` | `test_gate_repairs_adversarial_uncertainty_followups_without_fabricating_certainty` | Parametrized gate repair removes unsupported certainty for identity/location/quantity/feasibility. | downstream | Repair and validator modules; gate only applies them | thin later | High duplication with validator/repair semantics; keep maybe one end-to-end row, thin the matrix later. | medium |
| `tests/test_fallback_behavior_gate.py` | `test_gate_rewrites_runner_copper_meta_leak_into_diegetic_partial` | Gate replaces social meta leak with diegetic partial. | historical regression | `game.final_emission_gate` plus fallback repair/social context | keep | Specific incident-like path; higher behavioral value than generic duplicate. | medium |
| `tests/test_fallback_behavior_gate.py` | `test_gate_rewrites_open_call_move_plays_out_meta_leak_into_diegetic_partial` | Gate rewrites open-call meta leak into diegetic partial. | historical regression | `game.final_emission_gate` plus fallback repair/open-call context | keep | Specific open-call incident/path. | medium |
| `tests/test_fallback_behavior_gate.py` | `test_finalize_emission_output_preserves_duplicate_subject_without_micro_smooth` | Packaging finalize does not merge duplicate subject sentences. | owner, but not fallback_behavior | `game.final_emission_gate._finalize_emission_output` | comment-only | Misfiled in fallback gate file; note as finalization/packaging owner, not fallback behavior. | low |
| `tests/test_fallback_behavior_repairs.py` | `test_downstream_retry_observes_shipped_fallback_contract_and_final_emission_meta` | Retry prompt debug observes shipped fallback contract and FEM metadata from enforcement. | downstream | `game.gm.apply_response_policy_enforcement`, `game.gm_retry.build_retry_prompt_for_failure` | keep | Downstream consumer coverage; not duplicate helper semantics. | low |
| `tests/test_fallback_behavior_repairs.py` | `test_retry_consumer_prefers_upstream_fallback_meta_over_nested_debug_noise` | Retry debug reads upstream FEM metadata over conflicting nested debug. | downstream/historical regression | `game.gm_retry._fill_fallback_behavior_retry_debug_sink` | keep | Specific metadata precedence behavior. | low |
| `tests/test_fallback_behavior_repairs.py` | `test_downstream_gate_observes_answer_contract_meta_when_output_exhibits_smoothed_fallback_shape` | Gate records answer/fallback metadata and removes meta fallback voice from smoothed fallback shape. | downstream | Gate orchestration; helper semantics owned by repairs/validators | thin later | Mixes answer contract and fallback repair; likely reducible to a narrower metadata propagation smoke. | medium |
| `tests/test_fallback_continuity_guard.py` | all 6 tests | Validates player-facing deterministic retry fallback continuity and invalid known-fact rejection. | owner/historical regression | `game.gm`, `game.gm_retry` | keep | Adjacent fallback surface, not duplicate with fallback_behavior contract. | low |
| `tests/test_fallback_overwrite_containment.py` | all 5 tests | Protects upstream fast-fallback selector/output containment. | historical regression | `game.fallback_provenance_debug`, `game.final_emission_gate` | keep | Cycle D/C style containment protection; do not thin in first pass. | medium |
| `tests/test_fallback_shipped_contract_propagation.py` | all 6 tests | Ensures shipped response-policy/context-separation contracts survive fallback, retry, and gate paths. | downstream/historical regression | `game.gm`, `game.gm_retry`, `game.final_emission_gate` | keep | Distinct contract propagation family; not fallback_behavior predicate duplication. | medium |
| `tests/test_opening_fallback_owner_bucket.py` | all 10 tests | Maps opening fallback telemetry fields into owner buckets. | owner | `game.final_emission_meta` | keep | Direct owner bucket mapper; useful model for Cycle E ownership comments. | low |

## Safe Cycle E Implementation Blocks To Generate Later

These are not changes made now. They are candidate blocks for GPT/code generation after this recon:

1. Add ownership comments/docstrings only.
   - Clarify that `tests/test_fallback_behavior_validator.py` owns validator semantics.
   - Clarify that `tests/test_final_emission_repairs.py` owns repair/layer semantics.
   - Clarify that `tests/test_fallback_behavior_gate.py` owns gate ordering/application/metadata propagation only.
   - Clarify that `tests/test_fallback_behavior_repairs.py` owns retry/downstream metadata consumption only.

2. Optional fixture consolidation later.
   - Extract repeated `_fallback_contract()` fixture into a shared helper only if the project accepts test helper movement.
   - Lower priority because helper extraction can create noise; comments alone may solve ownership signal first.

3. Later thinning candidates, after comment-only pass.
   - In `tests/test_fallback_behavior_gate.py`, reduce the adversarial uncertainty parameter matrix to one representative gate application row because validator/repair owners already cover the predicate surface.
   - In `tests/test_fallback_behavior_gate.py`, narrow `test_gate_repairs_meta_fallback_voice_into_bounded_partial` to gate metadata propagation, not detailed repair mode internals.
   - In `tests/test_fallback_behavior_repairs.py`, narrow `test_downstream_gate_observes_answer_contract_meta_when_output_exhibits_smoothed_fallback_shape` to one downstream contract observation.

## Files To Pass Back To GPT For Block Generation

Most important test files:

- `tests/test_fallback_behavior_validator.py`
- `tests/test_final_emission_repairs.py`
- `tests/test_fallback_behavior_gate.py`
- `tests/test_fallback_behavior_repairs.py`
- `tests/test_opening_fallback_owner_bucket.py`
- `tests/test_fallback_continuity_guard.py`
- `tests/test_fallback_overwrite_containment.py`
- `tests/test_fallback_shipped_contract_propagation.py`
- `tests/test_final_emission_gate.py`

Most important production files:

- `game/final_emission_gate.py`
- `game/final_emission_repairs.py`
- `game/final_emission_validators.py`
- `game/final_emission_meta.py`
- `game/gm.py`
- `game/gm_retry.py`
- `game/fallback_provenance_debug.py`
- `game/upstream_response_repairs.py`
- `game/diegetic_fallback_narration.py`
- `game/final_emission_sealed_fallback.py`
- `game/final_emission_visibility_fallback.py`
- `game/opening_deterministic_fallback.py`

Relevant audit/report files:

- `audits/cycle_e_test_signal_ownership_recon_2026-05-17.md`
- `audits/opening_fallback_surface_inventory_2026-05-11.md`
- `audits/thin_answer_fallback_surface_inventory_2026-05-12.md`
- `audits/cycle_c_fallback_surface_contraction_closure_2026-05-12.md`
- `audits/cycle_d_sealed_fallback_contraction_closure_2026-05-13.md`
- `audits/cycle_d_visibility_fallback_contraction_closure_2026-05-13.md`
- `audits/failure_owner_matrix.md`
- `audits/failure_surface_inventory.md`
- `audits/runtime_signal_inventory.md`

Contracts, fixtures, and golden/replay artifacts:

- `tests/helpers/golden_replay.py`
- `tests/test_golden_replay.py`
- `tests/helpers/failure_classifier.py`
- `tests/failure_classification_contract.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_classification_contract.py`
- `tests/test_dead_turn_detection.py`
- `tests/test_turn_pipeline_shared.py`
- `tests/test_transcript_regression.py`

## Recon Conclusion

Choose **fallback_behavior** as the Cycle E fallback-family slice. Start with comment-only ownership clarification and only then consider thinning duplicate downstream assertions. This preserves Cycle D final-emission architecture while making future failures localize first to validator, repair, gate orchestration, or downstream consumer ownership.

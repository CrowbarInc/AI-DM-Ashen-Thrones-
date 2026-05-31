# Thin-Answer / Action-Answer Fallback Surface Inventory — 2026-05-12

## Executive Summary

This family appears **multi-source at the final-emission surface**, but **mostly single-source for answer/action prose authorship**.

The contracted answer/action fallback prose is authored as `upstream_prepared_emission` in `game/upstream_response_repairs.py`, then selected by `_enforce_response_type_contract()` in `game/final_emission_gate.py` when `required_response_type` is `answer` or `action_outcome`. That is the cleanest next contraction target after opening fallback: it already has explicit upstream-prepared fields, provenance, validity flags, and boundary-convergence tests.

The remaining ambiguity is not the text composer for answer/action fallback. It is the broader fallback surface around response-type repairs: strict-social dialogue repair, sanitizer empty fallback, retry/terminal fallback, answer-completeness/acceptance-quality gates, and final source stamping can all make a turn look like a thin-answer/action-answer repair unless owner/family/provenance are read together.

## Runtime Authoring / Selection

### Upstream prepared answer/action authoring

- `game/upstream_response_repairs.py`
  - `build_minimal_answer_contract_repair_text()`: authors `prepared_answer_fallback_text`.
    - Uses social fallback resolution when an active interlocutor exists.
    - Otherwise uses check prompt/adjudication state, or falls back to `"No direct answer is established from the current state yet."`
  - `build_minimal_action_outcome_contract_repair_text()`: authors `prepared_action_fallback_text`.
    - Builds a second-person action acknowledgement plus deterministic result summary.
  - `_to_second_person_action_clause()`: derives the action acknowledgement from player input/resolution.
  - `_action_result_summary()`: derives result clauses from state changes, checks, success/failure, investigation/observe/travel kinds, and generic action state.
  - `build_upstream_prepared_emission_payload()`: packages:
    - `prepared_answer_fallback_text`
    - `prepared_action_fallback_text`
    - `prepared_sanitizer_empty_fallback_text`
    - `upstream_prepared_bundle_origin`
    - `realization_fallback_family=upstream_prepared_emission`
  - `merge_upstream_prepared_emission_into_gm_output()`: attaches the prepared snapshot and preserves caller-supplied non-empty overrides.

### Runtime attach callsites

- `game/final_emission_gate.py`
  - `apply_final_emission_gate()`: calls `merge_upstream_prepared_emission_into_gm_output()` before response-type enforcement.
  - Also calls `maybe_attach_upstream_prepared_opening_fallback_payload()`, but opening fallback is a separate family already inventoried.
- `game/api_turn_support.py`
  - Calls `merge_upstream_prepared_emission_into_gm_output()` before sanitizer/gate processing in player-facing finalization paths.
  - Passes `upstream_prepared_emission` into sanitizer context.
- `game/output_sanitizer.py`
  - `_prepared_upstream_empty_fallback_text()` reads `prepared_sanitizer_empty_fallback_text`.
  - This is a sibling field in the same upstream-prepared payload, but it is not the answer/action response-type repair itself.

### Response-type validation and selection

- `game/final_emission_validators.py`
  - `candidate_satisfies_answer_contract()`: rejects empty, scene-prose filler, another question, too-thin answers, unsupported banter, and non-direct answers.
  - `candidate_satisfies_action_outcome_contract()`: rejects empty, scene-prose filler, dialogue replacement, missing attempt acknowledgement, agency substitution, and missing result.
  - `_default_response_type_debug()` and `_merge_response_type_meta()` define/stamp response-type telemetry including upstream-prepared provenance fields.
- `game/final_emission_gate.py`
  - `_enforce_response_type_contract()`:
    - Resolves `required_response_type`.
    - Validates candidate text.
    - For `answer`, reads `upstream_prepared_emission.prepared_answer_fallback_text`.
    - For `action_outcome`, reads `upstream_prepared_emission.prepared_action_fallback_text`.
    - Revalidates prepared text before adoption.
    - Stamps `response_type_repair_kind` as `answer_upstream_prepared_repair` or `action_outcome_upstream_prepared_repair`.
    - Stamps `upstream_prepared_emission_used`, `upstream_prepared_emission_valid`, `upstream_prepared_emission_source`, `upstream_prepared_emission_reject_reason`, and `realization_fallback_family=upstream_prepared_emission`.
    - If prepared text is absent or malformed, records absence/reject reason and keeps the current candidate instead of minting boundary prose.
  - Strict-social dialogue path in the same function can select `strict_social_ownership_terminal_fallback()` or `minimal_social_emergency_fallback_line()` for `dialogue`; this is adjacent but not the answer/action prepared-emission family.

### Adjacent quality layers

- `game/final_emission_repairs.py`
  - `_apply_answer_completeness_layer()`: validates answer completeness after response-type enforcement, but current boundary behavior does not invent answer prose; it records failure and skip metadata.
  - `_apply_answer_exposition_plan_layer()` can reorder sentence order for answer-plan convergence when allowed, but does not create missing facts.
- `game/acceptance_quality.py`
  - `validate_and_repair_acceptance_quality()` is a later quality floor for thin grounding/trailer terminals. It is a post-response-type quality layer, not the source of the upstream prepared answer/action fallback.

## Gate / Final Emission Boundary

Final-gate branches involved:

- `apply_final_emission_gate()` entry:
  - Materializes response policy.
  - Merges `upstream_prepared_emission`.
  - Runs response-type enforcement before answer-completeness, response-delta, social structure, narrative authenticity, fallback behavior, narrative-mode output, visibility, referent clarity, acceptance quality, and finalization.
- `_enforce_response_type_contract()`:
  - `required == "answer"` branch selects `prepared_answer_fallback_text`.
  - `required == "action_outcome"` branch selects `prepared_action_fallback_text`.
  - `required == "dialogue"` branch can select strict-social/minimal social repair.
  - `opening_mode` branch blocks generic action repair during scene opening and uses the separate opening fallback flow.
- Strict-social finalization branch:
  - After `build_final_strict_social_response()`, response-type repair can override the strict-social candidate.
  - If response-type still fails, the branch may force `minimal_social_emergency_fallback`.
- Non-strict finalization branch:
  - If no later gate reasons remain, `final_emitted_source` becomes `generated_candidate` or the response-type repair kind.
  - Later repairs can overwrite `final_emitted_source`, so response-type ownership must also read `response_type_repair_kind` and upstream-prepared fields.

Important final-source behavior:

- `response_type_repair_used=True` initially maps `final_emitted_source` to `response_type_repair_kind`.
- Later repair layers can supersede `final_emitted_source`.
- Therefore, `response_type_repair_kind`, `upstream_prepared_emission_*`, and `realization_fallback_family` are more reliable than `final_emitted_source` alone for ownership.

## Replay / Golden Coverage

Existing replay/golden coverage:

- `docs/archive/dead_governance/2026-05-31/golden_replay_baseline_2026-05-11.md` (historical archived baseline; current protected replay authority is `docs/testing/protected_replay_manifest.md`)
  - `thin_answer_action_outcome_final_emission` passes with `final_emitted_source=action_outcome_upstream_prepared_repair` and `fallback_family=upstream_prepared_emission`.
  - `scenario_spine_three_branch` also observes `action_outcome_upstream_prepared_repair` on the notice branch.
- `tests/test_golden_replay.py`
  - `test_golden_replay_thin_answer_action_outcome_final_emission_structural_invariants` covers response-type repair invariants for the golden scenario.
- `tests/helpers/golden_replay.py`
  - Projects structural fields:
    - `final_emitted_source`
    - `response_type_required`
    - `response_type_candidate_ok`
    - `response_type_repair_used`
    - `response_type_repair_kind`
    - `fallback_family`
    - `fallback_temporal_frame`
  - Does not currently project `upstream_prepared_emission_used`, `upstream_prepared_emission_source`, `upstream_prepared_emission_valid`, or reject reason.

Direct/unit and integration coverage:

- `tests/test_final_emission_boundary_convergence.py`
  - `test_gate_thin_answer_uses_upstream_prepared_marker_not_boundary_synthesis`
  - `test_gate_thin_action_outcome_uses_upstream_prepared_marker_not_boundary_synthesis`
  - `test_enforce_response_type_marks_upstream_absent_without_inventing_answer_line`
  - `test_enforce_response_type_upstream_attribution_override`
  - `test_enforce_response_type_rejects_malformed_upstream_answer_without_boundary_synthesis`
  - `test_enforce_response_type_rejects_malformed_upstream_action_without_boundary_synthesis`
- `tests/test_upstream_response_repairs.py`
  - Covers payload construction, merge/idempotence, override preservation, answer text, action text, and provenance.
- `tests/test_final_emission_gate.py`
  - Covers final source/repair kind for answer prepared repair.
- `tests/test_turn_pipeline_shared.py`
  - Covers `answer` repair in chat and `action_outcome` repair in active social scene.

Missing replay invariants:

- Golden projection does not expose upstream-prepared provenance fields, so a golden failure can identify `response_type` but cannot always prove whether the prepared field was absent, rejected, overridden, or superseded.
- No golden invariant appears to require `upstream_prepared_emission_source == upstream_prepared_emission.prepared_action_fallback_text` for the action-outcome row.
- No golden invariant appears to require `upstream_prepared_emission_valid=True` for prepared-emission repairs.
- No explicit replay row appears to cover malformed/absent upstream prepared answer/action payloads in an end-to-end path.

## Failure Classifier / Dashboard Coverage

Existing classifier/dashboard coverage:

- `tests/helpers/failure_classifier.py`
  - Registers response-type repair fields as `category=emission`, owner `final_emission_gate`.
  - `_emission_sublayer()` returns `response_type` when field path starts with `response_type` or `response_type_repair_used is True`.
  - Terminal/global fallback maps to `terminal_fallback`.
  - Fallback family presence otherwise tends to map to `fallback_behavior`.
- `tests/test_failure_classifier.py` and `tests/test_failure_dashboard_controlled_failures.py`
  - Include controlled `response_type_repair_used=True` cases for runtime repair kinds.
  - Preserve `thin_answer` only as explicit legacy/backward-compatible classifier coverage.
- `audits/failure_dashboard_probe_sample.md`
  - Has a sample `response_type_repair_unexpected` row with `repair=thin_answer`.
- `audits/replay_failure_corpus.md`
  - Notes the `thin_answer_action_outcome_final_emission` row and says sublayer root requires `response_type_repair_kind`.
- `audits/proposed_failure_classification_schema.md`
  - Lists response-type metadata as available FEM fields.

Coverage gap:

- Classifier owner/family classification currently treats response-type repair primarily as `emission/final_emission_gate`.
- It does not appear to separately classify the prepared-emission owner/family from `upstream_prepared_emission_*` fields.
- Dashboard rows can show `fallback_family=upstream_prepared_emission` when projected, but the replay projection does not currently include all upstream prepared provenance fields.
- Controlled failures now use runtime answer/action repair kinds for normal cases; `thin_answer` remains a legacy/backward-compatible classifier fixture.

## Ambiguous Authorship Paths

1. **Prepared answer/action selected by response-type gate**
   - Likely owner: `upstream_prepared_emission` for prose; `final_emission_gate` for selection and metadata.
   - Ambiguity: `final_emitted_source` alone points at the gate repair kind, while prose authorship lives upstream.

2. **Prepared answer/action overridden by caller/test/CTIR payload**
   - Likely owner: caller-provided `upstream_prepared_emission` override.
   - Ambiguity: `merge_upstream_prepared_emission_into_gm_output()` preserves non-empty existing values; provenance can be overridden via `upstream_prepared_emission_attribution`, but replay does not project that field.

3. **Prepared answer/action absent or rejected**
   - Likely owner: upstream-prepared-emission attach/validation.
   - Ambiguity: gate records `response_type_candidate_ok=False`, but downstream terminal fallback or other repair may later become the visible final source.

4. **Strict-social dialogue repair under response-type enforcement**
   - Likely owner: `social_exchange_emission` / strict-social fallback family; gate selects when dialogue contract fails.
   - Ambiguity: it uses the same `response_type_repair_used` field family but is not answer/action prepared emission.

5. **Sanitizer empty fallback from upstream-prepared payload**
   - Likely owner: sanitizer for selection; upstream-prepared-emission for stock empty fallback text.
   - Ambiguity: shares the `upstream_prepared_emission` payload but is not an answer/action response-type repair.

6. **Later final-gate repair overwrites final source after response-type repair**
   - Likely owner: the later layer that actually repaired final text; upstream-prepared-emission remains the earlier response-type repair owner if its text survived.
   - Ambiguity: final source can mask earlier response-type repair unless `response_type_repair_kind` and post-gate mutation fields are read.

7. **Acceptance-quality thinness floor after response-type repair**
   - Likely owner: `acceptance_quality` for quality-floor repair or failure; upstream-prepared-emission for any earlier prepared answer/action text.
   - Ambiguity: both are "thinness" surfaces but operate at different layers.

## Recommended Next Blocks

1. **Block C11 — Prepared-Emission Replay Projection**
   - Add golden/dashboard projection for `upstream_prepared_emission_used`, `upstream_prepared_emission_valid`, `upstream_prepared_emission_source`, and `upstream_prepared_emission_reject_reason`.
   - Keep behavior unchanged; this is observability-only.

2. **Block C12 — Runtime Repair-Kind Taxonomy Cleanup**
   - Align dashboard/classifier examples and tests around runtime repair kinds: `answer_upstream_prepared_repair`, `action_outcome_upstream_prepared_repair`, `strict_social_dialogue_repair`, and `dialogue_minimal_repair`.
   - Preserve any legacy `thin_answer` fixture only as a backward-compatibility classifier case.

3. **Block C13 — Prepared-Emission Owner Classifier**
   - Teach the failure classifier to distinguish `owner=upstream_prepared_emission` when response-type repair used a prepared answer/action field, with secondary owner `final_emission_gate` for selection.
   - Use `upstream_prepared_emission_*` fields before falling back to `response_type_repair_kind`.

4. **Block C14 — Absent/Malformed Prepared-Emission Golden Edges**
   - Add replay/direct golden-like rows for absent and malformed prepared answer/action payloads.
   - Assert no boundary synthesis and require the reject/absence telemetry to survive projection.

5. **Block C15 — Sanitizer Empty-Fallback Split**
   - Separate `prepared_sanitizer_empty_fallback_text` observability from answer/action prepared-emission observability.
   - This is riskier because it crosses sanitizer, finalization support, and prepared-emission payload shape.

## Block C11 Update — Prepared-Emission Replay Projection

Added golden replay observation projection for these FEM fields:

- `upstream_prepared_emission_used`
- `upstream_prepared_emission_valid`
- `upstream_prepared_emission_source`
- `upstream_prepared_emission_reject_reason`

Updated `tests/helpers/golden_replay.py` to read the fields from raw FEM into each observed turn and include them in `format_golden_replay_debug()`. This is read-side only; runtime behavior, final emitted text, fallback selection, fallback prose, and fallback family assignment are unchanged.

Added focused projection tests in `tests/test_golden_replay.py`:

- Valid prepared answer telemetry survives projection.
- Valid prepared action-outcome telemetry survives projection.
- Rejected/malformed prepared action telemetry survives projection, including reject reason.

Tests run:

- `python -m pytest tests/test_golden_replay.py -q` could not run because `python` is not on PATH in this shell.
- Bundled Python: `python.exe -m pytest tests/test_golden_replay.py -q --tb=short --basetemp=codex_pytest_tmp_c11_golden` — passed, 18 tests.
- Bundled Python: `python.exe -m pytest -m golden_replay -q --tb=short --basetemp=codex_pytest_tmp_c11_marker` — passed, 18 tests.
- Bundled Python: `python.exe -m pytest tests/test_failure_classifier.py -q --tb=short --basetemp=codex_pytest_tmp_c11_fc` — passed, 29 tests.
- Bundled Python: `python.exe -m pytest tests/test_failure_classification_contract.py -q --tb=short --basetemp=codex_pytest_tmp_c11_fcc` — passed, 12 tests.

Remaining gaps:

- Failure classifier/dashboard behavior is intentionally unchanged for C11.
- C12 can now align repair-kind taxonomy with runtime labels while using the projected prepared-emission telemetry as evidence.
- C13 should use these projected fields to distinguish `owner=upstream_prepared_emission` from `final_emission_gate` selection.

## Block C12 Update — Repair-Kind Taxonomy Cleanup

Aligned classifier/dashboard fixtures around runtime response-type repair kinds:

- `answer_upstream_prepared_repair`
- `action_outcome_upstream_prepared_repair`
- `strict_social_dialogue_repair`
- `dialogue_minimal_repair`

Changes:

- Updated normal response-type repair classifier fixtures to use prepared answer/action runtime labels instead of `thin_answer`.
- Updated controlled dashboard failure rows to use `action_outcome_upstream_prepared_repair` as the canonical response-type repair example.
- Added contract taxonomy constants for runtime response-type repair kinds and legacy response-type repair kinds.
- Added tests proving all four runtime repair kinds classify distinctly by `repair_kind` while staying in the response-type emission sublayer.
- Kept `thin_answer` only in an explicitly named legacy/backward-compatible classifier/dashboard evidence test.

Tests run:

- `python -m pytest tests/test_failure_classifier.py -q` could not run because `python` is not on PATH in this shell.
- Bundled Python: `python.exe -m pytest tests/test_failure_classifier.py -q --tb=short --basetemp=codex_pytest_tmp_c12_fc` — passed, 34 tests.
- Bundled Python: `python.exe -m pytest tests/test_failure_dashboard_controlled_failures.py -q --tb=short --basetemp=codex_pytest_tmp_c12_fdcf` — passed, 10 tests.
- Bundled Python: `python.exe -m pytest tests/test_failure_classification_contract.py -q --tb=short --basetemp=codex_pytest_tmp_c12_fcc` — passed, 13 tests.
- Bundled Python: `python.exe -m pytest tests/test_golden_replay.py -q --tb=short --basetemp=codex_pytest_tmp_c12_golden` — passed, 18 tests.

Remaining gaps:

- Failure ownership is still intentionally unchanged: prepared answer/action repairs classify as response-type emission selected at the gate.
- C13 should use the C11 projected `upstream_prepared_emission_*` fields to split prepared-emission authorship from final-gate selection.

## Block C13 Update — Prepared-Emission Owner Classifier

Reporting-only classifier/dashboard updates now distinguish prepared answer/action fallback authorship from final gate selection when projected telemetry is present.

Fields added to classification evidence:

- `upstream_prepared_emission_used`
- `upstream_prepared_emission_valid`
- `upstream_prepared_emission_source`
- `upstream_prepared_emission_reject_reason`
- `prepared_emission_owner`

Contract updates:

- Added `upstream_prepared_emission` as an allowed owner and source-family/evidence value.
- Valid prepared answer/action repairs with `upstream_prepared_emission_used=True` classify primary ownership as `upstream_prepared_emission`.
- Secondary ownership and investigation target remain on the emission/final-emission-gate side for selection triage.
- Missing prepared-emission telemetry preserves the prior response-type classifier behavior.

Dashboard updates:

- Valid prepared telemetry renders compact evidence as `prepared_emission=used valid=True source=<source>`.
- Rejected/malformed prepared telemetry renders compact evidence as `prepared_emission=rejected reason=<reason>`.

Tests added/updated:

- Valid `answer_upstream_prepared_repair` maps to `upstream_prepared_emission` evidence/owner.
- Valid `action_outcome_upstream_prepared_repair` maps to `upstream_prepared_emission` evidence/owner.
- Rejected/malformed prepared emission preserves `upstream_prepared_emission_reject_reason`.
- `strict_social_dialogue_repair` and `dialogue_minimal_repair` remain separate final-gate response-type repairs when prepared telemetry is absent.
- Missing prepared-emission telemetry preserves legacy owner/source-family behavior.
- Controlled dashboard failures cover valid and rejected compact prepared-emission evidence.

Remaining gaps:

- This block does not change runtime selection, validation, or final-emission behavior.
- Prepared sanitizer-empty fallback remains a sibling upstream-prepared payload concern and is not split into answer/action prepared-emission ownership here.
- End-to-end replay coverage still depends on golden projection continuing to expose the prepared-emission telemetry fields added in C11.

## Block C14 Update — Absent/Malformed Prepared-Emission Edges

Added replay/direct golden-like coverage for absent and malformed prepared answer/action emission payloads.

Tests added:

- Golden projection now treats `upstream_prepared_emission_used`, `upstream_prepared_emission_valid`, `upstream_prepared_emission_source`, and `upstream_prepared_emission_reject_reason` as structural replay fields.
- `tests/test_golden_replay.py` covers absent prepared answer/action telemetry projecting through `_observed_turn()` and debug output.
- `tests/test_golden_replay.py` covers malformed prepared action telemetry with `upstream_prepared_emission_used=True`, `upstream_prepared_emission_valid=False`, and visible reject reason in drift/classifier debug.
- `tests/test_final_emission_gate.py` covers absent prepared answer/action payloads preserving the original candidate instead of synthesizing answer/action prose.
- `tests/test_final_emission_gate.py` covers malformed prepared answer/action payloads being rejected, preserving reject/source telemetry, and not selecting the malformed prepared text.
- `tests/test_failure_classifier.py` covers rejected prepared-emission dashboard evidence rendering the reject reason.
- `tests/test_failure_classifier.py` covers absent prepared-emission telemetry staying out of `upstream_prepared_emission` ownership.

Invariant results:

- Absent prepared answer/action payload telemetry survives projection when emitted by FEM.
- Malformed/rejected prepared emission telemetry survives projection and classifier evidence when available.
- The final emission gate does not synthesize answer/action fallback prose without valid upstream-prepared emission; absent/invalid prepared text leaves the current candidate for downstream gate handling.
- Reject/absence reason is visible in replay debug and classifier/dashboard evidence where the source telemetry exists.
- `strict_social_dialogue_repair` and `dialogue_minimal_repair` remain separate from prepared answer/action emission.

Runtime changes:

- None. Existing gate behavior already failed closed for absent/malformed prepared answer/action payloads.

Remaining gaps:

- Prepared sanitizer-empty fallback remains outside the answer/action prepared-emission edge coverage and is still the likely C15 split.
- End-to-end golden rows for naturally produced absent/malformed prepared payloads are still limited by which runtime paths emit those exact edge telemetry combinations during replay.

## Block C15 Update — Sanitizer Empty-Fallback Split

Inventory results:

- `game/upstream_response_repairs.py` builds `prepared_sanitizer_empty_fallback_text` as a sibling field inside the `upstream_prepared_emission` payload.
- `game/output_sanitizer.py` reads that sibling field through `_prepared_upstream_empty_fallback_text()` only when strip-only sanitization drops all candidate text and needs an empty-output fallback.
- Answer/action response-type repair still reads only `prepared_answer_fallback_text` and `prepared_action_fallback_text` in `game/final_emission_gate.py`.
- Existing sanitizer coverage already proved the upstream-prepared sanitizer empty text can be selected by `sanitize_player_facing_output()`.

Classification split:

- Answer/action prepared emission remains classified as `primary_owner=upstream_prepared_emission` only when response-type prepared-emission telemetry indicates prepared answer/action ownership.
- Sanitizer empty fallback selection is classified as `primary_owner=sanitizer`, `source_family=output_sanitizer`, and `sanitizer_empty_fallback_owner=output_sanitizer`.
- The prepared text source is still visible as `sanitizer_empty_fallback_source=upstream_prepared_emission.prepared_sanitizer_empty_fallback_text`, but this no longer implies answer/action prepared-emission ownership.

Fields added:

- `sanitizer_empty_fallback_used`
- `sanitizer_empty_fallback_source`
- `sanitizer_empty_fallback_owner`

Runtime change:

- Observability only: `output_sanitizer` now stamps those fields into `sanitizer_trace` when the prepared sanitizer empty fallback is selected, and stamps `used=False` on the empty-after-strip path without a prepared fallback.
- Player-facing text selection behavior is unchanged.

Tests run:

- `python -m pytest ...` could not run because `python` is not on PATH in this shell.
- Bundled Python: `tests/test_golden_replay.py -q --tb=short --basetemp=codex_pytest_tmp_c15_golden` — passed, 22 tests.
- Bundled Python: `tests/test_failure_classifier.py -q --tb=short --basetemp=codex_pytest_tmp_c15_fc` — passed, 44 tests.
- Bundled Python: `tests/test_failure_dashboard_controlled_failures.py -q --tb=short --basetemp=codex_pytest_tmp_c15_fdcf` — passed, 12 tests.
- Bundled Python: `tests/test_failure_classification_contract.py -q --tb=short --basetemp=codex_pytest_tmp_c15_fcc` — passed, 14 tests.
- Bundled Python: `tests/test_output_sanitizer.py -q --tb=short --basetemp=codex_pytest_tmp_c15_sanitizer` — passed, 43 tests.

Closure assessment:

- Thin answer/action prepared-emission contraction can close from the reporting/observability side: answer/action ownership, absent/malformed prepared payload edges, strict-social/dialogue-minimal separation, and sanitizer-empty sibling separation are now covered.
- Remaining closure work should be a C16 audit/contract wrap-up rather than new runtime behavior.

## Block C16 Closure - Thin-Answer / Action-Answer Authorship Contract

Final owner contract:

- Answer/action fallback prose ownership is upstream-only: `game/upstream_response_repairs.py` authors `prepared_answer_fallback_text` and `prepared_action_fallback_text` inside `upstream_prepared_emission`.
- Answer/action selection ownership is final-gate-only: `game/final_emission_gate.py` validates/selects the prepared answer/action text and stamps `answer_upstream_prepared_repair` or `action_outcome_upstream_prepared_repair` when valid.
- Malformed or absent prepared answer/action payloads do not synthesize boundary prose. The final gate records absence/rejection telemetry and preserves the current candidate for downstream handling.
- `strict_social_dialogue_repair` and `dialogue_minimal_repair` remain separate final-gate dialogue repairs and do not imply prepared answer/action authorship.
- Sanitizer empty fallback is sanitizer-owned selection. Its source may be `upstream_prepared_emission.prepared_sanitizer_empty_fallback_text`, but it is not answer/action prepared-emission ownership.

Proof search summary:

- `game/upstream_response_repairs.py` is the prose authoring surface for `prepared_answer_fallback_text`, `prepared_action_fallback_text`, and sibling `prepared_sanitizer_empty_fallback_text`.
- `game/final_emission_gate.py` reads only `prepared_answer_fallback_text` for `required == "answer"` and only `prepared_action_fallback_text` for `required == "action_outcome"`, then stamps prepared-emission usage/validity/source/reject reason.
- `game/output_sanitizer.py` reads only `prepared_sanitizer_empty_fallback_text` for strip-only empty-output fallback and stamps `sanitizer_empty_fallback_*`.
- `tests/helpers/golden_replay.py` projects prepared-emission usage/validity/source/reject reason and sanitizer-empty fallback fields.
- `tests/helpers/failure_classifier.py` distinguishes `primary_owner=upstream_prepared_emission` for valid/rejected answer/action prepared-emission telemetry from `primary_owner=sanitizer` and `source_family=output_sanitizer` for sanitizer-empty fallback.

Test results:

- C16 added no new invariant test because the preferred invariant already exists in `tests/test_failure_classifier.py`: a sanitizer-empty fallback row with both upstream-prepared telemetry fields and sanitizer-empty fields remains sanitizer-owned and does not set answer/action prepared-emission ownership.
- Focused C16 verification was requested for:
  - `tests/test_golden_replay.py`
  - `tests/test_final_emission_gate.py`
  - `tests/test_failure_classifier.py`
  - `tests/test_failure_dashboard_controlled_failures.py`
  - `tests/test_failure_classification_contract.py`
  - `tests/test_output_sanitizer.py`
  - `tests/test_upstream_response_repairs.py`

Remaining legacy fixtures:

- Legacy dashboard/classifier labels may still mention thin answer/action or final-gate response-type repair when prepared-emission telemetry is absent. That is intentional backward compatibility for rows that predate the new telemetry.
- Historical audit/baseline rows still record earlier owner language, but current structural fields are the authoritative contract.

Closure assessment:

- This fallback family is complete for C16. The prose owner, selection owner, absent/malformed fail-closed behavior, strict-social/dialogue-minimal separation, replay projection, classifier/dashboard ownership split, and sanitizer-empty sibling split are all locked.
- Recommended next fallback family: post-gate mutation / sanitizer rewrite fallback surfaces, because they are adjacent to the sanitizer-empty split and still carry broader mutation/ownership risk than the now-closed thin-answer/action-answer family.

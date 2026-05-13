# Post-Gate Mutation / Sanitizer Rewrite Surface Inventory — 2026-05-12

## Executive Summary

This block is reconnaissance only. No runtime behavior was changed.

The post-gate / sanitizer rewrite family is split across three layers:

- `game/output_sanitizer.py` owns scaffold/serialization legality cleanup before the final emission gate on normal non-strict-social paths. Its default mode is strip-only; the historical sentence rewrite pipeline exists behind explicit `sanitizer_boundary_mode="legacy_sentence_rewrite"`.
- `game/final_emission_gate.py` owns final boundary packaging, sealed fallback selection, final metadata stamping, and post-gate mutation detection. Its finalize step is documented and guarded as packaging-only: HTML/text sanitization, whitespace normalization, and route-illegal stock stripping.
- `tests/helpers/golden_replay.py` and `tests/helpers/failure_classifier.py` project and classify sanitizer/post-gate evidence, but some mutation lineage is inferred from coarse fields rather than a single canonical runtime lineage object.

The strongest current invariant is that sanitizer-empty fallback is now separated from answer/action prepared-emission ownership. The next risk surface is broader sanitizer rewrite/fallback rewrite ownership: when a visible text delta happens, the replay row can often say "sanitizer", "fallback_behavior", or "emission.post_gate_mutation_unknown", but not always which exact runtime writer last changed the text.

Proof search run:

`rg -n "sanitizer|sanitize|rewrite|post_gate|post-gate|mutation|fallback_rewrite|empty_fallback|scaffold|leakage|final_emitted_source|mutation_source" game tests audits`

## Runtime Rewrite / Mutation Paths

### Output sanitizer

`game/output_sanitizer.py` is the primary sanitizer rewrite surface.

- Module docstring states the default boundary is strip-only and that sentence-template diegetic rewrites require explicit `SANITIZER_BOUNDARY_LEGACY_SENTENCE_REWRITE`.
- `sanitize_player_facing_output()` routes to `_sanitize_player_facing_output_strip_only()` unless `sanitizer_boundary_mode` equals `legacy_sentence_rewrite`.
- `_sanitize_player_facing_output_strip_only()` performs:
  - serialized response payload extraction/fragment stripping
  - full-text rewrite regex application
  - internal prefix stripping
  - unrecoverable fragment drops
  - non-diegetic / scaffold / procedural / analytical sentence drops
  - strict-social fallback line selection only when active social context owns that fallback
  - final validation/coherence pass
  - prepared sanitizer-empty fallback selection when the strip-only path empties output
- Legacy rewrite mode still contains `_rewrite_line()`, `_rewrite_instructional_sentence()`, `rewrite_analytical_sentence()`, `_rewrite_directive_sentence()`, `_simple_diegetic_fallback()`, and `_diegetic_uncertainty_fallback()`. These can author substitute diegetic prose and are therefore the highest-risk sanitizer rewrite ownership surfaces, even though they are no longer default.

### Final emission finalize

`game/final_emission_gate.py::_finalize_emission_output()` is the main post-gate mutation surface.

- It records a `final_emission_gate_exit` stage snapshot.
- It runs `_sanitize_output_text()` under the `sanitize_html_to_text` allowed mutation kind.
- It intentionally disables sentence decompression, fragment repair, and micro-smoothing at finalize time.
- It runs `_strip_appended_route_illegal_contamination_sentences()` under the `strip_route_illegal_contamination` allowed mutation kind.
- It writes `player_facing_text`, updates `_final_emission_meta`, and stamps `post_gate_mutation_detected` by comparing `pre_gate_text` to normalized final text.
- It applies last-write containment/reseal steps: `_finalize_upstream_fallback_overwrite_containment()`, a second narrow route-illegal strip, and `_reassert_scene_opening_accepted_candidate()`.

### Final emission source assignment

`final_emitted_source` is assigned in multiple final gate branches:

- Accepted candidate starts as `generated_candidate`.
- It may be overwritten by response-type repair, retry output, answer completeness repair, response delta repair, social response structure repair, narrative authenticity repair, narrative authority repair, tone escalation repair, anti-railroading repair, context separation repair, fallback behavior repair, player-facing narration purity repair, answer shape primacy repair, or fast fallback neutral composition repair.
- Replacement branches stamp sources such as `global_scene_fallback`, `acceptance_quality_global_scene_fallback`, `opening_deterministic_fallback`, `minimal_social_emergency_fallback`, `social_interlocutor_minimal_fallback`, `passive_scene_pressure_fallback`, `npc_pursuit_neutral_fallback`, and `anti_reset_local_continuation_fallback`.

Current risk: `final_emitted_source` is a useful final winner, but it is not a complete mutation lineage. A late repair source can overwrite an earlier repair source, and the prior chain is visible only if auxiliary layer metadata/stage-diff telemetry survived.

## Sanitizer-Owned Fallback Paths

Current sanitizer-owned paths:

- Strip-only empty fallback: `_prepared_upstream_empty_fallback_text()` reads `upstream_prepared_emission.prepared_sanitizer_empty_fallback_text`; `_mark_sanitizer_empty_fallback()` stamps `sanitizer_empty_fallback_used`, `sanitizer_empty_fallback_source`, and `sanitizer_empty_fallback_owner="output_sanitizer"`.
- Strip-only empty-without-prepared: stamps `strip_only_empty_after_upstream_strip` and `sanitizer_empty_fallback_used=False`, then returns empty text.
- Strict-social sanitizer fallback: when active strict-social context empties the sanitizer output, `social_fallback_line_for_sanitizer()` is selected. This is a cross-layer path: the call site is sanitizer, but prose ownership is strict-social/social emission.
- Legacy sentence rewrite fallback: `_diegetic_uncertainty_fallback()` and `_simple_diegetic_fallback()` can author diegetic replacement text from sanitizer heuristics. Because legacy rewrite mode is opt-in, this is less active in normal runtime but remains an ownership hazard.

Important distinction after C15/C16: sanitizer-empty fallback selection is sanitizer-owned, even when the text source is a sibling field inside `upstream_prepared_emission`. It is not answer/action prepared-emission ownership.

## Final Emission / Post-Gate Mutation Boundary

`game/final_emission_boundary_contract.py` defines the boundary taxonomy:

- Packaging allowed: whitespace normalization, HTML/text sanitization, terminal punctuation normalization, route-illegal contamination stripping, metadata packaging, candidate preservation, selected subtractive cleanup, accepted opening restoration, answer sentence reorder, and continuity validation attach.
- Legality allowed: hard replacement with sealed fallback, contract-failed output rejection, strict-social terminal fallback, and upstream-prepared opening fallback selection.
- Semantic disallowed: answer completeness repair, response delta repair, social response structure repair, dialogue cadence rewrites, fallback answer composition, narrative repair, semantic fallback composition, speaker semantic rewrites, strict-social referential substitution, continuity repair, and other meaning-affecting rewrites.

`_finalize_emission_output()` calls `assert_final_emission_mutation_allowed()` for its packaging/strip operations. This is good locality pressure: post-gate mutation should stay packaging/subtractive unless a sealed legality fallback was already chosen.

Current boundary ambiguity:

- `post_gate_mutation_detected` is a boolean, not a source chain.
- `mutation_source` in dashboard rows is inferred from classifier sublayer detection, not directly emitted by the runtime.
- Stage-diff telemetry records snapshots/transitions and repair flags, but replay/classifier does not yet expose a compact canonical "last visible text writer" field.
- Final source overwrite order makes the winner visible, while prior repair participants require inspecting layer-specific metadata.

## Replay / Golden Coverage

`tests/helpers/golden_replay.py` projects:

- `final_emitted_source`
- `response_type_repair_*`
- upstream prepared-emission fields
- `post_gate_mutation_detected`
- fallback family/temporal frame
- stage-diff telemetry
- sanitizer mode, event count, changed count, rewrite-used boolean
- sanitizer-empty fallback fields
- scaffold leakage predicate

Golden drift treats:

- `final_emitted_source`, response-type fields, fallback fields, and `post_gate_mutation_detected` as structural replay signals when expected.
- `scaffold_leakage` and forbidden/required final text fragments as semantic drift predicates.
- sanitizer event counts and changed counts as projected evidence when sanitizer debug/trace metadata reaches the payload.

Coverage exists for sanitizer leakage, sanitizer-empty fallback projection, final-source snapshots, opening fallback source snapshots, response-type prepared-emission projection, and post-gate unknown mutation classification.

Coverage gap: sanitizer rewrite lineage is not consistently generated by runtime in a compact trace. Golden replay can count sanitizer events when present, but absence of sanitizer metadata does not prove no sanitizer mutation happened.

## Failure Classifier / Dashboard Coverage

`tests/helpers/failure_classifier.py` currently maps:

- `scaffold_leakage` to `category=sanitizer`, `primary_owner=sanitizer`, `source_family=output_sanitizer`.
- `sanitizer_empty_fallback_*` to sanitizer ownership and sanitizer sublayer evidence.
- `post_gate_mutation_detected` to `category=emission`, with `emission_sublayer=emission.post_gate_mutation_unknown` when no more specific sublayer is visible.
- response-type repairs, opening fallback, fallback behavior, strict-social replacement, speaker enforcement, interaction continuity, terminal fallback, and prepared-emission telemetry to more specific emission sublayers when evidence exists.
- `mutation_source` to the inferred `emission_sublayer`, or `emission.post_gate_mutation_unknown` when only the post-gate mutation boolean is present.

`tests/helpers/failure_dashboard_report.py` renders evidence for:

- `emission_sublayer`
- `repair_kind`
- `opening_fallback_owner_bucket`
- `mutation_source`
- `missing_source_kind`
- sanitizer mode/event/changed counts
- sanitizer-empty fallback fields

Controlled dashboard failures include sanitizer leakage, sanitizer-empty fallback, forced fallback source, and unknown post-gate mutation probes.

Coverage gap: dashboard evidence can say `sublayer=sanitizer` or `mutation=emission.post_gate_mutation_unknown`, but it does not yet report a runtime-authored mutation chain such as `pre_gate_sanitizer -> final_gate_response_type -> finalize_strip_route_illegal`.

## Ambiguous Ownership Paths

1. Legacy sanitizer sentence rewrite mode
   - Owner should be `output_sanitizer` for selection, but prose authorship is mixed: sanitizer templates, strict-social fallback helpers, and diegetic fallback helpers.
   - Recommended treatment: inventory as legacy/diagnostic unless runtime paths still opt into it.

2. Strict-social fallback selected from sanitizer context
   - Call site is sanitizer, but prose owner is social/strict-social emission.
   - Existing code comments recognize strict-social as the fallback owner; classifier currently groups sanitizer evidence by sanitizer metadata unless strict-social final-source evidence is present.

3. `final_emitted_source` overwrite chain
   - The final source is last-writer-wins. This is fine for the final winner, but weak for causal lineage when multiple repair layers participated.
   - Some layer metadata exists, but no single compact `final_emission_mutation_lineage` is projected.

4. Post-gate mutation boolean
   - `post_gate_mutation_detected=True` correctly flags visible delta after the pre-gate candidate.
   - When no sublayer signal is present, classifier falls back to `emission.post_gate_mutation_unknown`.
   - This is honest, but not very actionable.

5. Scaffold/leakage cleanup
   - Golden replay detects leakage in final text and classifier assigns sanitizer ownership.
   - If sanitizer metadata is absent, the row still correctly points to sanitizer, but cannot distinguish sanitizer bypass, sanitizer failure, or unrecoverable post-sanitizer mutation.

6. Finalize route-illegal stripping
   - `_finalize_emission_output()` can subtract appended route-illegal stock text after gate selection.
   - This is allowed packaging/legal cleanup, but the replay-facing mutation source is usually only `post_gate_mutation_detected` plus final-source metadata.

## Recommended Next Blocks

1. C18 - Sanitizer Rewrite Lineage Projection
   - Add a compact runtime-projected sanitizer trace summary for every sanitizer call site: mode, changed/dropped counts, empty fallback use, and whether legacy sentence rewrite mode was active.
   - Keep behavior unchanged; only make the existing sanitizer mutation surface consistently observable in replay payloads.

2. C19 - Final Emission Mutation Lineage Snapshot
   - Add a compact `_final_emission_meta.final_emission_mutation_lineage` list or equivalent field that records visible text writers in order: pre-gate sanitizer, response-type repair, fallback behavior repair, sealed fallback replacement, finalize strip/packaging.
   - Preserve `final_emitted_source` as the final winner, but stop relying on it as the only mutation lineage signal.

3. C20 - Legacy Sanitizer Rewrite Ownership Lock
   - Inventory all callers that opt into `SANITIZER_BOUNDARY_LEGACY_SENTENCE_REWRITE`.
   - Add invariant tests proving normal runtime paths use strip-only mode, and legacy sentence rewrite mode is diagnostic/test-only unless explicitly requested.

4. C21 - Strict-Social From Sanitizer Split
   - Lock that strict-social fallback prose selected during sanitizer empty-output handling is social/strict-social-authored, while sanitizer owns only the legality-triggered selection event.
   - Mirror the sanitizer-empty split: owner/source fields should distinguish call-site selection from prose authorship.

5. C22 - Post-Gate Unknown Mutation Reduction
   - Use the new lineage fields to reduce `emission.post_gate_mutation_unknown` rows.
   - Keep the unknown bucket as a fail-closed fallback, but make it rare and actionable when it appears.

## Block C18 Update — Sanitizer Rewrite Lineage Projection

Fields added:

- `sanitizer_lineage_mode`
- `sanitizer_lineage_changed_count`
- `sanitizer_lineage_dropped_count`
- `sanitizer_lineage_empty_fallback_used`
- `sanitizer_lineage_legacy_rewrite_active`

Runtime observability:

- `game/output_sanitizer.py` now normalizes compact lineage fields into `sanitizer_trace` on sanitizer entry and updates counts from existing sanitizer events.
- Clean strip-only calls stamp mode plus zero/false lineage values.
- Strip-only dropped/rewrite-candidate events increment changed and dropped lineage counts.
- Sanitizer-empty fallback mirrors `sanitizer_empty_fallback_used` into `sanitizer_lineage_empty_fallback_used`.
- Legacy sentence rewrite mode stamps `sanitizer_lineage_legacy_rewrite_active=True`.
- Emitted text and sanitizer branch behavior are unchanged.

Projection/classifier/dashboard:

- `tests/helpers/golden_replay.py` projects the lineage fields from `sanitizer_trace`, with fallback derivation from existing `sanitizer_debug` events for older payloads.
- `tests/helpers/failure_classifier.py` carries lineage fields as evidence and only uses changed/empty lineage as sanitizer sublayer evidence when sanitizer evidence already exists.
- `tests/helpers/failure_dashboard_report.py` renders compact lineage evidence without changing owner classification.
- `tests/failure_classification_contract.py` allows the new evidence fields.

Tests run:

- `python -m pytest tests/test_output_sanitizer.py -q` could not run because `python` is not on PATH in this shell.
- Bundled Python: `tests/test_output_sanitizer.py -q --basetemp=codex_pytest_tmp_c18_sanitizer2` — passed, 43 tests.
- Bundled Python: `tests/test_golden_replay.py -q --basetemp=codex_pytest_tmp_c18_golden2` — passed, 25 tests.
- Bundled Python: `tests/test_failure_classifier.py -q --basetemp=codex_pytest_tmp_c18_fc2` — passed, 44 tests.
- Bundled Python: `tests/test_failure_dashboard_controlled_failures.py -q --basetemp=codex_pytest_tmp_c18_fdcf` — passed, 12 tests.
- Bundled Python: `tests/test_failure_classification_contract.py -q --basetemp=codex_pytest_tmp_c18_fcc` — passed, 14 tests.

Remaining gaps:

- The lineage is sanitizer-local. It does not yet provide a full final-emission mutation chain across pre-gate sanitizer, gate repair layers, sealed fallback replacement, and finalize packaging.
- Legacy sentence rewrite mode is now visible, but C20 should still inventory and lock which callers may opt into it.
- C19 can proceed: the next useful step is a compact final-emission mutation lineage snapshot that preserves `final_emitted_source` as the final winner while exposing the writer chain that led there.

## Block C19 Update — Final Emission Mutation Lineage Snapshot

Field added:

- `final_emission_mutation_lineage`

Lineage tokens currently emitted/projected:

- `pre_gate_sanitizer`
- `response_type_repair`
- `prepared_emission_selection`
- `opening_fallback_selection`
- `fallback_behavior_repair`
- `sealed_fallback_replacement`
- `sanitizer_empty_fallback`
- `finalize_html_strip`
- `finalize_route_illegal_strip`
- `finalize_packaging`
- `post_gate_mutation_detected`

Runtime observability:

- `game/final_emission_meta.py` now owns metadata-only lineage construction via existing FEM and sanitizer trace signals.
- `game/final_emission_gate.py` refreshes lineage during finalization and metadata patching without changing emitted text, repair order, or `final_emitted_source`.
- Finalization stamps `finalize_route_illegal_strip_applied` when the route-illegal stock strip actually changes text; this only feeds lineage.
- `final_emitted_source` remains the final winner. `final_emission_mutation_lineage` records the visible writer sequence that can include earlier stages.

Projection/classifier/dashboard:

- `tests/helpers/golden_replay.py` projects `final_emission_mutation_lineage` and includes it in debug output.
- `tests/helpers/failure_classifier.py` carries lineage as evidence only.
- `tests/helpers/failure_dashboard_report.py` renders lineage compactly as `token>token>token`.
- `tests/failure_classification_contract.py` allows the new evidence field.

Tests run:

- `python -m pytest tests/test_final_emission_gate.py -q` could not run because `python` is not on PATH in this shell.
- Bundled Python: `tests/test_final_emission_gate.py -q --basetemp=codex_pytest_tmp_c19_feg` — passed, 224 tests.
- Bundled Python: `tests/test_golden_replay.py -q --basetemp=codex_pytest_tmp_c19_golden` — passed, 25 tests.
- Bundled Python: `tests/test_failure_classifier.py -q --basetemp=codex_pytest_tmp_c19_fc` — passed, 44 tests.
- Bundled Python: `tests/test_failure_dashboard_controlled_failures.py -q --basetemp=codex_pytest_tmp_c19_fdcf` — passed, 12 tests.
- Bundled Python: `tests/test_failure_classification_contract.py -q --basetemp=codex_pytest_tmp_c19_fcc` — passed, 14 tests.
- Bundled Python: `tests/test_output_sanitizer.py -q --basetemp=codex_pytest_tmp_c19_sanitizer` — passed, 43 tests.

Remaining gaps:

- Lineage is still compact and token-based; it does not include timestamps, text hashes per stage, or full repair-layer payloads.
- Unknown post-gate mutation reduction is intentionally deferred. Classifier ownership logic still uses existing category/owner rules.
- C20 can proceed: legacy sanitizer rewrite ownership can now be audited with both sanitizer-local lineage and final-emission lineage available as evidence.

## Block C20 Update — Legacy Sanitizer Rewrite Ownership Lock

Legacy callers found:

- Runtime/API paths:
  - `game/api_turn_support.py` calls `sanitize_player_facing_output()` with `SANITIZER_BOUNDARY_STRIP_ONLY`.
  - `game/final_emission_gate.py` calls `sanitize_player_facing_output()` with literal `"strip_only"` for the non-social suppression path.
  - `game/output_sanitizer.py` defaults missing/unknown `sanitizer_boundary_mode` to strip-only behavior.
- Explicit legacy/diagnostic paths:
  - `tests/test_output_sanitizer.py` uses `_legacy_rewrite_ctx()` with `SANITIZER_BOUNDARY_LEGACY_SENTENCE_REWRITE` for historical sentence-rewrite behavior.
  - `tests/test_final_emission_boundary_convergence.py` has explicit legacy-mode comparison coverage.
  - `tests/test_social_exchange_emission.py` has an explicit legacy sanitizer call for strict-social/passive-pressure behavior.
  - Golden/classifier/dashboard tests may use synthetic `legacy_sentence_rewrite` lineage rows to prove evidence rendering.

Default/runtime mode proof:

- Direct sanitizer calls without `sanitizer_boundary_mode` now prove `sanitizer_lineage_mode == "strip_only"` and `sanitizer_lineage_legacy_rewrite_active is False`.
- Golden runtime replay asserts sanitizer lineage never reports `sanitizer_lineage_legacy_rewrite_active=True`.
- Runtime/API search found no production call site opting into `legacy_sentence_rewrite`.
- No runtime call site was changed in C20 because no unsafe legacy default path was discovered.

Ownership/evidence proof:

- Explicit legacy rewrite tests still exercise the old sentence rewrite behavior under an explicit legacy context.
- Classifier/dashboard evidence maps legacy rewrite rows to `primary_owner=sanitizer`, `source_family=output_sanitizer`, and renders the legacy flag as `sanitizer_lineage_legacy=legacy_diagnostic`.
- Legacy rewrite is evidence/diagnostic, not the canonical runtime sanitizer mode.

Tests run:

- `python -m pytest tests/test_output_sanitizer.py -q` could not run because `python` is not on PATH in this shell.
- Bundled Python: `tests/test_output_sanitizer.py -q --basetemp=codex_pytest_tmp_c20_sanitizer` — passed, 44 tests.
- Bundled Python: `tests/test_golden_replay.py -q --basetemp=codex_pytest_tmp_c20_golden` — passed, 25 tests.
- Bundled Python: `tests/test_failure_classifier.py -q --basetemp=codex_pytest_tmp_c20_fc` — passed, 45 tests.
- Bundled Python: `tests/test_failure_dashboard_controlled_failures.py -q --basetemp=codex_pytest_tmp_c20_fdcf` — passed, 13 tests.
- Bundled Python: `tests/test_failure_classification_contract.py -q --basetemp=codex_pytest_tmp_c20_fcc` — passed, 14 tests.

Runtime legacy status:

- No normal runtime path still uses legacy sentence rewrite mode.
- C21 can proceed: strict-social fallback selected from sanitizer context can now be split using sanitizer lineage, final-emission lineage, and diagnostic legacy-mode evidence.

## Block C21 Update - Strict-Social From Sanitizer Split

Fields added or confirmed:

- Confirmed sanitizer-empty upstream-prepared fallback remains separate under `sanitizer_empty_fallback_used`, `sanitizer_empty_fallback_source`, and `sanitizer_empty_fallback_owner`.
- Added `sanitizer_strict_social_fallback_used` for strict-social fallback selected by sanitizer empty-output handling.
- Added `sanitizer_strict_social_selection_owner="output_sanitizer"` to keep the legality/selection owner on the sanitizer.
- Added `sanitizer_strict_social_prose_owner="strict_social_emission"` to keep fallback prose ownership on strict-social/social emission.
- Added `sanitizer_strict_social_source="social_fallback_line_for_sanitizer.empty_output"` to distinguish this path from `upstream_prepared_emission.prepared_sanitizer_empty_fallback_text`.
- Golden replay projects the new sanitizer trace fields into observed turns and debug output.
- Classifier/dashboard evidence renders the split compactly while keeping sanitizer-triggered rows categorized as `sanitizer` with `source_family=output_sanitizer`.

Tests run:

- `python -m pytest tests/test_output_sanitizer.py -q` could not run because `python` is not on PATH in this shell.
- Bundled Python: `tests/test_output_sanitizer.py -q --basetemp=codex_pytest_tmp_c21_output` - passed, 45 tests.
- Bundled Python: `tests/test_golden_replay.py -q --basetemp=codex_pytest_tmp_c21_golden` - passed, 26 tests.
- Bundled Python: `tests/test_failure_classifier.py -q --basetemp=codex_pytest_tmp_c21_classifier` - passed, 46 tests.
- Bundled Python: `tests/test_failure_dashboard_controlled_failures.py -q --basetemp=codex_pytest_tmp_c21_dashboard` - passed, 14 tests.
- Bundled Python: `tests/test_failure_classification_contract.py -q --basetemp=codex_pytest_tmp_c21_contract` - passed, 15 tests.

Remaining ownership ambiguity:

- None for the sanitizer empty-output strict-social path: sanitizer owns selection/legal fallback routing, and strict-social/social emission owns fallback prose.
- Adjacent strict-social sanitizer substitutions inside sentence-level strip/validation still call the same social fallback helper, but C21 only locks the empty-output handling path.

## Block C22 Update - Post-Gate Unknown Mutation Reduction

Mappings added:

- `sanitizer_empty_fallback` -> `sanitizer.empty_fallback`
- `pre_gate_sanitizer` -> `sanitizer`
- `response_type_repair` -> `response_type`
- `prepared_emission_selection` -> `upstream_prepared_emission`
- `opening_fallback_selection` -> `opening_fallback`
- `fallback_behavior_repair` -> `fallback_behavior`
- `sealed_fallback_replacement` -> `sealed_gate`
- `finalize_html_strip` -> `final_emission.finalize_packaging`
- `finalize_route_illegal_strip` -> `final_emission.finalize_route_illegal_strip`
- `finalize_packaging` -> `final_emission.finalize_packaging`

Classifier/dashboard behavior:

- `post_gate_mutation_detected=True` now consults `final_emission_mutation_lineage` before falling back to `emission.post_gate_mutation_unknown`.
- The reducer prefers specific lineage tokens such as sanitizer-empty fallback, route-illegal strip, and response-type repair over generic packaging tokens.
- Dashboard evidence still renders compact lineage as `token>token`, and now renders the reduced `mutation_source` when a lineage token maps cleanly.
- The unknown bucket remains valid and is still used when the post-gate mutation boolean is present without lineage or any other specific sublayer evidence.

Tests run:

- `python -m pytest tests/test_failure_classifier.py -q` could not run because `python` is not on PATH in this shell.
- `python -m pytest tests/test_failure_dashboard_controlled_failures.py -q` could not run because `python` is not on PATH in this shell.
- `python -m pytest tests/test_failure_classification_contract.py -q` could not run because `python` is not on PATH in this shell.
- `python -m pytest tests/test_golden_replay.py -q` could not run because `python` is not on PATH in this shell.
- Bundled Python: `tests/test_failure_classifier.py -q --basetemp=codex_pytest_tmp_c22_classifier` - passed, 50 tests.
- Bundled Python: `tests/test_failure_dashboard_controlled_failures.py -q --basetemp=codex_pytest_tmp_c22_dashboard` - passed, 17 tests.
- Bundled Python: `tests/test_failure_classification_contract.py -q --basetemp=codex_pytest_tmp_c22_contract` - passed, 20 tests.
- Bundled Python: `tests/test_golden_replay.py -q --basetemp=codex_pytest_tmp_c22_golden` - passed, 26 tests.

Unknown cases that remain:

- `post_gate_mutation_detected=True` with no `final_emission_mutation_lineage`.
- `post_gate_mutation_detected=True` with lineage tokens outside the reviewed mapping table.
- Rows where the only evidence is the boolean mutation flag and no sanitizer, response-type, fallback, opening, prepared-emission, or finalization sublayer evidence is present.

## Block C23 Closure - Post-Gate / Sanitizer Rewrite Authorship Contract

Final owner contract:

- Normal sanitizer mode is strip-only. Production game call sites pass `SANITIZER_BOUNDARY_STRIP_ONLY`, literal `"strip_only"`, or rely on the sanitizer default.
- `legacy_sentence_rewrite` remains diagnostic/test-only. The only production-code occurrences are the sanitizer constant, branch, lineage flag comparison, and module docstring.
- Sanitizer-empty fallback is sanitizer-owned selection: `sanitizer_empty_fallback_owner="output_sanitizer"` with source evidence pointing to `upstream_prepared_emission.prepared_sanitizer_empty_fallback_text` when that sibling prepared string is selected.
- Strict-social-from-sanitizer empty-output fallback records split ownership: `sanitizer_strict_social_selection_owner="output_sanitizer"` and `sanitizer_strict_social_prose_owner="strict_social_emission"`.
- `final_emission_mutation_lineage` records writer sequence separately from `final_emitted_source`, which remains the final selected source/winner.
- `post_gate_mutation_unknown` remains available only when evidence is boolean-only or lineage is absent/unmapped.

Proof search summary:

- `rg -n "legacy_sentence_rewrite|sanitizer_lineage|sanitizer_empty_fallback|sanitizer_strict_social|final_emission_mutation_lineage|post_gate_mutation_unknown|finalize_route_illegal_strip" game tests audits` confirmed all contracted fields and tests are present.
- `rg -n "legacy_sentence_rewrite|SANITIZER_BOUNDARY_LEGACY_SENTENCE_REWRITE" game` found no production caller opting into legacy rewrite mode.
- `rg -n "sanitizer_boundary_mode" game` found runtime callers using strip-only plus sanitizer-local default handling.
- Golden replay projects sanitizer lineage and final-emission mutation lineage.
- Classifier/dashboard tests prove strict-social sanitizer fallback owner split, sanitizer-empty ownership, lineage-based post-gate mutation reduction, and unknown fallback preservation.

Tests run:

- `python -m pytest tests/test_output_sanitizer.py -q` could not run because `python` is not on PATH in this shell.
- `python -m pytest tests/test_golden_replay.py -q` could not run because `python` is not on PATH in this shell.
- `python -m pytest tests/test_failure_classifier.py -q` could not run because `python` is not on PATH in this shell.
- `python -m pytest tests/test_failure_dashboard_controlled_failures.py -q` could not run because `python` is not on PATH in this shell.
- `python -m pytest tests/test_failure_classification_contract.py -q` could not run because `python` is not on PATH in this shell.
- `python -m pytest tests/test_final_emission_gate.py -q` could not run because `python` is not on PATH in this shell.
- Bundled Python: `tests/test_output_sanitizer.py -q --basetemp=codex_pytest_tmp_c23_output` - passed, 45 tests.
- Bundled Python: `tests/test_golden_replay.py -q --basetemp=codex_pytest_tmp_c23_golden` - passed, 26 tests.
- Bundled Python: `tests/test_failure_classifier.py -q --basetemp=codex_pytest_tmp_c23_classifier` - passed, 50 tests.
- Bundled Python: `tests/test_failure_dashboard_controlled_failures.py -q --basetemp=codex_pytest_tmp_c23_dashboard` - passed, 17 tests.
- Bundled Python: `tests/test_failure_classification_contract.py -q --basetemp=codex_pytest_tmp_c23_contract` - passed, 20 tests.
- Bundled Python: `tests/test_final_emission_gate.py -q --basetemp=codex_pytest_tmp_c23_feg` - passed, 224 tests.

Remaining unknown cases:

- Post-gate mutation rows with no `final_emission_mutation_lineage`.
- Post-gate mutation rows whose lineage contains only unmapped/new tokens.
- Rows with only `post_gate_mutation_detected=True` and no sanitizer, response-type, prepared-emission, opening, fallback, sealed-gate, or finalization evidence.

Completion status and recommendation:

- This fallback family is complete for Cycle Track C ownership closure.
- Recommended next step: either wrap Cycle C with a short cross-family ownership summary, or move to the next fallback family that still has boolean-only observability rather than lineage-backed classification.

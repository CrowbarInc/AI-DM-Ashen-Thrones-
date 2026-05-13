# Opening Fallback Surface Inventory — 2026-05-11

## Executive Summary

Opening fallback is close to single-source for prose composition, but not yet single-source for authorship attribution. The shared prose composer is `game/opening_deterministic_fallback.py::deterministic_opening_fallback_text_and_meta`, and the intended canonical runtime owner is the upstream-prepared payload from `game/upstream_response_repairs.py::build_upstream_prepared_opening_fallback_payload`. The final emission gate still contains compatibility-local selection/recomposition, stub recovery, and fail-closed marker paths, so opening fallback currently presents as multi-path at runtime even though most paths converge on the same composer or sealed marker.

## Files Inspected

- `game/opening_deterministic_fallback.py`
- `game/upstream_response_repairs.py`
- `game/final_emission_gate.py`
- `game/final_emission_boundary_contract.py`
- `game/final_emission_meta.py`
- `game/diegetic_fallback_narration.py`
- `game/api.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/failure_classifier.py`
- `tests/failure_classification_contract.py`
- `tests/test_golden_replay.py`
- `tests/test_final_emission_gate.py`
- `tests/test_upstream_response_repairs.py`
- `tests/test_api_narration_path_selection.py`
- `tests/test_start_campaign_api.py`
- Existing audits: `audits/failure_hotspots.md`, `audits/failure_surface_inventory.md`, `audits/failure_owner_matrix.md`, `audits/mutation_boundary_inventory.md`, `audits/runtime_signal_inventory.md`, `audits/golden_replay_readiness_2026-05-11.md`, `audits/golden_replay_baseline_2026-05-11.md`, `audits/replay_failure_corpus.md`, `audits/failure_dashboard_precision_pass_2026-05-11.md`, `audits/proposed_failure_classification_schema.md`.

## Runtime Authoring / Selection

| File | Anchor | Role | Surface | Suspected owner bucket |
| --- | --- | --- | --- | --- |
| `game/opening_deterministic_fallback.py` | module docstring, lines 1-9 | Declares shared opening fallback composer ownership; says upstream packages the canonical payload and gate only compatibility-selects/re-invokes. | AUTHORS fallback prose | upstream-prepared when called through upstream payload; unknown/ambiguous when gate invokes directly |
| `game/opening_deterministic_fallback.py` | `opening_context_from_gm_output`, lines 37-129 | Extracts curated opening facts, selector facts, location anchors, and actionable labels; fails closed on missing/non-list `opening_curated_facts`. | TRANSFORMS authoring inputs | upstream-prepared |
| `game/opening_deterministic_fallback.py` | `_actionable_hook_from_opening_context`, lines 132-159; `_pick_opening_fallback_fact`, lines 167-183 | Selects deterministic fact snippets and hook phrasing from curated facts. | AUTHORS fallback prose | upstream-prepared |
| `game/opening_deterministic_fallback.py` | `deterministic_opening_fallback_text_and_meta`, lines 186-215 and following composer body | Canonical curated-facts-to-text function; emits the sealed marker when facts are empty. | AUTHORS fallback prose / sealed marker | upstream-prepared normally; sealed gate when fail-closed marker is selected downstream |
| `game/upstream_response_repairs.py` | constants, lines 51-58 | Defines `UPSTREAM_PREPARED_OPENING_FALLBACK_KEY`, authorship source strings, and origin string. | CLASSIFIES fallback authorship | upstream-prepared |
| `game/upstream_response_repairs.py` | `is_structurally_usable_upstream_prepared_opening_fallback_payload`, lines 173-186 | Requires prepared text, composition meta, and opening meta before gate selection. | SELECTS payload usability | upstream-prepared |
| `game/upstream_response_repairs.py` | `build_upstream_prepared_opening_fallback_payload`, lines 189-219 | Calls the shared composer, adds fallback family/timeframe/authorship metadata, and packages the prepared snapshot. | AUTHORS via composer / CLASSIFIES | upstream-prepared |
| `game/upstream_response_repairs.py` | `maybe_attach_upstream_prepared_opening_fallback_payload`, lines 243-287 | Attaches canonical payload only for `scene_opening` with usable curated facts; replaces text-only stubs; records build failure telemetry. | SELECTS / TRANSFORMS gm output metadata | upstream-prepared |
| `game/api.py` | `_scene_opening_curated_facts_from_prompt_payload`, lines 1870-1892 | Picks opening basis facts from selector, curated facts, or realization contract. | SELECTS authoring basis | upstream-prepared |
| `game/api.py` | `_attach_scene_opening_curated_facts_to_gm`, lines 1895-1918; call sites around 3052 and 3069 | Attaches `opening_curated_facts`, selector facts, and emission debug before final emission. | SELECTS authoring basis / TRANSFORMS gm output | upstream-prepared |

## Gate / Final Emission / Mutation Boundary

| File | Anchor | Role | Surface | Suspected owner bucket |
| --- | --- | --- | --- | --- |
| `game/final_emission_gate.py` | module docstring, lines 40-43 | States canonical prose is upstream-prepared and gate re-invocation is compatibility-only. | SELECTS fallback path | upstream-prepared intent, ambiguous compatibility residue |
| `game/final_emission_boundary_contract.py` | `LEGALITY_ALLOWED`, lines 37-44 | Allows `select_upstream_prepared_opening_fallback` as selector-only legality mutation. | CLASSIFIES mutation boundary | upstream-prepared |
| `game/final_emission_boundary_contract.py` | `SEMANTIC_DISALLOWED`, lines 49-70 | Marks `compose_opening_fallback_compatibility_local` as semantic-disallowed. | CLASSIFIES mutation boundary | unknown/ambiguous compatibility path |
| `game/final_emission_gate.py` | `_opening_fallback_classification`, lines 3973-3977 | Maps `opening_deterministic_fallback` through diegetic classification metadata. | CLASSIFIES fallback family | sealed gate |
| `game/final_emission_gate.py` | `_opening_fail_closed_meta_upstream_missing_insufficient_curated_facts`, lines 4010-4060 | Creates fail-closed meta when no upstream payload and curated facts cannot attach. | CLASSIFIES / sealed marker metadata | sealed gate |
| `game/final_emission_gate.py` | `_upstream_prepared_opening_fallback_payload_if_usable`, lines 4063-4070 | Reads usable prepared payload from gm output. | SELECTS fallback path | upstream-prepared |
| `game/final_emission_gate.py` | `_recover_upstream_opening_fallback_stub_payload`, lines 4073-4107 | Rebuilds unusable text-only upstream opening stubs in place when curated facts can support it. | TRANSFORMS / may re-author via shared composer | upstream-prepared intent, ambiguous because gate initiates rebuild |
| `game/final_emission_gate.py` | `_opening_fail_closed_meta_upstream_maybe_attach_prepare_failed`, lines 4127-4155; `_opening_fail_closed_meta_upstream_stub_rebuild_failed`, lines 4158-4187 | Produces fail-closed metadata for attach/build failure and stub rebuild failure. | CLASSIFIES sealed marker | sealed gate |
| `game/final_emission_gate.py` | `_opening_scene_safe_fallback_tuple`, lines 4190-4243 | Hard-replace tuple for opening-mode illegality; prefers upstream payload; otherwise chooses fail-closed marker or compatibility-local composer. | SELECTS / may MUTATE final output / may AUTHOR via compatibility local | upstream-prepared, sealed gate, or unknown/ambiguous compatibility |
| `game/final_emission_gate.py` | `_enforce_response_type_contract`, comments lines 4258-4261; opening fallback branch lines 4387-4440 | Response-type gate selects upstream fallback, fail-closed marker, or local composer; stamps `opening_recovered_via_fallback`, repair kind, family/timeframe, and authorship source. | SELECTS / MUTATES / CLASSIFIES | upstream-prepared, sealed gate, or unknown/ambiguous compatibility |
| `game/final_emission_gate.py` | `_reassert_scene_opening_accepted_candidate`, lines 8914-8934 | Restores an accepted scene-opening candidate if later boundary drift changed it; packaging-allowed mutation. | MUTATES final output | sealed gate |
| `game/final_emission_gate.py` | `_merge_opening_upstream_prepare_attach_observability_into_response_type_debug`, lines 8943-8956 | Copies upstream attach failure telemetry into response-type debug/FEM. | CLASSIFIES evidence | sealed gate / upstream-prepared observability |
| `game/final_emission_meta.py` | allowed FEM keys, lines 95-115 | Allows opening fallback telemetry and fallback family fields in final emission meta. | CLASSIFIES evidence | sealed gate |
| `game/diegetic_fallback_narration.py` | `_FALLBACK_TEMPLATE_METADATA`, lines 13-17; `opening_scene_fallback_template_allowed`, lines 54-59 | Classifies `opening_deterministic_fallback` as `scene_opening` / `first_impression`. | CLASSIFIES fallback family | sealed gate |

## Replay / Golden Expectations

| File | Anchor | Role | Surface | Suspected owner bucket |
| --- | --- | --- | --- | --- |
| `tests/helpers/golden_replay.py` | required/observed fields, lines 45-58 | Includes `opening_recovered_via_fallback`, `opening_fallback_authorship_source`, `fallback_family`, `fallback_temporal_frame`. | TESTS / CLASSIFIES replay projection | unknown/ambiguous because owner bucket is not projected |
| `tests/helpers/golden_replay.py` | observation extraction, lines 585-599 and 670-673 | Reads opening fallback authorship and family from FEM. | CLASSIFIES evidence | unknown/ambiguous |
| `tests/helpers/golden_replay.py` | debug formatter, lines 760-780 | Emits opening fallback fields in failure/debug output. | CLASSIFIES evidence | unknown/ambiguous |
| `tests/test_golden_replay.py` | module mark, line 37 | Marks suite `integration` and `golden_replay`. | TESTS behavior | unknown/ambiguous |
| `tests/test_golden_replay.py` | `test_golden_direct_seam_opening_fallback_path_structural_invariants`, lines 692-735 | Direct seam asserts final source, response-type repair kind, fallback family/timeframe, and allowed authorship source values. | TESTS fallback behavior | upstream-prepared or compatibility-local accepted; owner bucket not single-source |
| `tests/test_final_emission_gate.py` | `test_block_c_opening_fallback_mutation_kinds_are_fenced_by_ownership`, lines 890-904 | Asserts upstream selection is allowed and compatibility-local compose is semantic-disallowed. | TESTS boundary classification | upstream-prepared / sealed gate |
| `tests/test_final_emission_gate.py` | `test_block_g_upstream_prepared_opening_payload_if_usable_requires_full_snapshot_shape`, lines 922-935 | Tests full snapshot requirement. | TESTS selection | upstream-prepared |
| `tests/test_final_emission_gate.py` | Block G/H tests, lines 938-1044 | Tests attach preconditions, fail-closed marker, skip-local-composer paths, and upstream preference. | TESTS behavior | upstream-prepared / sealed gate |
| `tests/test_final_emission_gate.py` | snapshot tests, lines 3852-3908 | Tests helper text snapshot and upstream-prepared tuple classification. | TESTS authored text / selection | upstream-prepared |
| `tests/test_final_emission_gate.py` | opening fallback classification/fail-closed tests, lines 5038-5299 | Tests no observe-family leakage, no polluted visible facts, fail-closed behavior, upstream payload wins even if curated facts missing. | TESTS behavior | upstream-prepared / sealed gate |
| `tests/test_upstream_response_repairs.py` | opening payload tests, lines 202-299 | Tests upstream payload text, family/timeframe/authorship, attach skip/preserve/replace, and build failure telemetry. | TESTS authoring / selection | upstream-prepared |
| `tests/test_api_narration_path_selection.py` | `test_finalize_player_facing_scene_opening_carries_upstream_opening_fallback_payload`, lines 271-297 | Tests finalize path carries upstream opening payload and FEM authorship source. | TESTS selection / final emission | upstream-prepared |
| `tests/test_start_campaign_api.py` | start/opening tests, lines 138-190 and 265-366 | Tests valid rich opener promotion, upstream-prepared opening promotion, and fallback basis from journal seed rather than visible facts. | TESTS basis selection and final text | upstream-prepared |

## Failure Dashboard / Classifier Integration

| File | Anchor | Role | Surface | Suspected owner bucket |
| --- | --- | --- | --- | --- |
| `tests/helpers/failure_classifier.py` | `CATEGORY_RULES`, lines 70-85 | Treats fallback family/timeframe/opening authorship fields as fallback category signals; final source as fallback source. | CLASSIFIES evidence | unknown/ambiguous |
| `tests/helpers/failure_classifier.py` | `_emission_sublayer`, lines 300-329 | Returns `opening_fallback` when opening recovery is present or final source/repair kind contains opening. | CLASSIFIES evidence | unknown/ambiguous |
| `tests/helpers/failure_classifier.py` | `_fallback_observed`, lines 352-359 | Treats `opening_fallback_authorship_source` as fallback-observed evidence. | CLASSIFIES evidence | unknown/ambiguous |
| `tests/failure_classification_contract.py` | allowed tags, lines 50-90 | Allows source-family tag `opening_fallback`. | CLASSIFIES contract | unknown/ambiguous |
| `tests/failure_classification_contract.py` | allowed emission sublayers, lines 151-162 | Allows emission sublayer `opening_fallback`. | CLASSIFIES contract | unknown/ambiguous |

## Existing Audit References

- `audits/failure_hotspots.md`: flags `game/opening_deterministic_fallback.py` as risky because authorship is split between upstream-prepared and gate compatibility paths.
- `audits/failure_surface_inventory.md`: lists the opening fallback composer and upstream prepared emission attach surfaces.
- `audits/failure_owner_matrix.md`: says opening fallback composer/upstream-prepared payload owns prose while gate selects it.
- `audits/mutation_boundary_inventory.md`: marks opening fallback attach as a critical mutation boundary.
- `audits/runtime_signal_inventory.md`: lists opening fallback telemetry fields as high-confidence runtime signals.
- `audits/golden_replay_readiness_2026-05-11.md`: identifies opening fallback as a golden replay candidate needing authorship/source assertion.
- `audits/golden_replay_baseline_2026-05-11.md`: records `opening_fallback_path` passing with `final_emitted_source=opening_deterministic_fallback`, `fallback_family=scene_opening`, `fallback_temporal_frame=first_impression`.
- `audits/replay_failure_corpus.md`: says existing opening fallback direct seam would fail on wrong source, family, authorship, or temporal frame.
- `audits/failure_dashboard_precision_pass_2026-05-11.md`: calls out opening fallback attribution as a dashboard precision target.
- `audits/proposed_failure_classification_schema.md`: includes fallback family/source fields but does not yet encode the desired owner buckets.

## Ambiguous Opening Fallback Authorship Paths

1. Gate compatibility-local composition when no usable upstream payload exists.
   - Where fallback may be created or changed: `game/final_emission_gate.py::_opening_scene_safe_fallback_tuple` lines 4212-4235 and `_enforce_response_type_contract` lines 4387-4415 can call `_deterministic_opening_fallback_text_and_meta` directly.
   - Why ownership is ambiguous: the prose composer is shared, but the gate initiates composition and stamps `opening_fallback_authorship_source=compatibility_local_opening_deterministic`.
   - Evidence exists: boundary contract classifies `compose_opening_fallback_compatibility_local` as semantic-disallowed; tests assert upstream payload preference and local compose avoidance in some fail-closed cases.
   - Evidence missing: no replay-level owner bucket maps compatibility-local opening composition to `upstream-prepared`, `sealed gate`, `retry`, or `strict-social`.
   - Ambiguity type: runtime behavior and replay observability ambiguity.

2. Gate stub recovery of unusable upstream opening payloads.
   - Where fallback may be created or changed: `game/final_emission_gate.py::_recover_upstream_opening_fallback_stub_payload` lines 4073-4107 mutates `gm_output[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY]` by rebuilding the upstream payload.
   - Why ownership is ambiguous: recovery uses the upstream payload builder, but it is initiated inside the gate after a malformed/stub payload has reached final emission.
   - Evidence exists: tests require full snapshot shape and validate text-only stubs are rebuilt; debug patch records `opening_fallback_upstream_payload_unusable` and `opening_fallback_upstream_payload_recovered`.
   - Evidence missing: owner bucket is not explicit in FEM/replay; it is unclear whether replay should call this upstream-prepared, sealed gate, or a distinct recovery owner.
   - Ambiguity type: runtime behavior and replay observability ambiguity.

3. Fail-closed sealed marker paths.
   - Where fallback may be created or changed: `game/final_emission_gate.py` fail-closed helpers lines 4010-4060, 4127-4155, 4158-4187; selection lines 4213-4223 and 4390-4400.
   - Why ownership is ambiguous: these paths do not add fallback prose, but they do replace attempted opening output with a sealed marker and stamp repair kind `opening_deterministic_fallback_failed_closed`.
   - Evidence exists: tests assert marker text, compatibility-local disabled flags, and no local composer invocation when curated facts are missing/empty.
   - Evidence missing: no owner bucket distinguishes sealed marker ownership from normal opening fallback authorship.
   - Ambiguity type: runtime behavior and test expectation ambiguity.

4. Replay/dashboard classify opening fallback family but not owner bucket.
   - Where fallback may be created or changed: no runtime change here; projection reads FEM in `tests/helpers/golden_replay.py`, classifier maps it in `tests/helpers/failure_classifier.py`.
   - Why ownership is ambiguous: `opening_fallback_authorship_source` is observed, but the desired owner bucket (`upstream-prepared`, `sealed gate`, `retry`, `strict-social`) is not derived or asserted.
   - Evidence exists: golden replay captures `opening_fallback_authorship_source`, `fallback_family`, `fallback_temporal_frame`, and classifier sublayer `opening_fallback`.
   - Evidence missing: no invariant that fallback family `scene_opening` must match an expected owner bucket.
   - Ambiguity type: replay observability and dashboard classification ambiguity.

5. Accepted scene-opening candidate restore path.
   - Where fallback may be created or changed: `game/final_emission_gate.py::_reassert_scene_opening_accepted_candidate` lines 8914-8934 can restore a previously accepted opening candidate after drift.
   - Why ownership is ambiguous: this is not fallback prose authoring, but it is a final text mutation around opening output and can obscure whether a fallback was selected earlier.
   - Evidence exists: boundary contract marks `restore_accepted_scene_opening_candidate` as packaging-allowed; debug fields record candidate/emitted match.
   - Evidence missing: replay does not distinguish restored valid candidate from fallback-owned opening recovery as an owner bucket.
   - Ambiguity type: runtime mutation boundary and replay observability ambiguity.

## Recommended Next Cycle C Blocks

1. Add a read-only owner bucket mapper for opening fallback telemetry.
   - Target files: `game/final_emission_meta.py` or a small helper near replay/classifier code, plus focused unit tests.
   - Goal: map existing fields to `upstream-prepared`, `sealed gate`, `retry`, `strict-social`, or `unknown/ambiguous` without changing final text.
   - Why it is safe: pure classification over existing FEM/debug fields; no fallback prose or selection changes.
   - Expected tests: classifier/contract tests for upstream-prepared, fail-closed sealed marker, compatibility-local unknown/ambiguous, and non-opening no-op.
   - Cursor independence: can run independently as long as it does not alter runtime behavior.

2. Project the owner bucket into golden replay observations.
   - Target files: `tests/helpers/golden_replay.py`, `tests/test_golden_replay.py`.
   - Goal: add `opening_fallback_owner_bucket` or generic `fallback_owner_bucket` to observed turns and assert it for `opening_fallback_path`.
   - Why it is safe: test/projection-only; uses already-captured FEM fields.
   - Expected tests: `tests/test_golden_replay.py -q`, `pytest -m golden_replay -q`.
   - Cursor independence: should wait for Block 1 if sharing a runtime helper; can run independently if the mapper is test-local first.

3. Teach failure classifier/dashboard evidence rows the same owner bucket.
   - Target files: `tests/helpers/failure_classifier.py`, `tests/failure_classification_contract.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py`.
   - Goal: classify opening fallback evidence with the new owner bucket while preserving existing category/sublayer behavior.
   - Why it is safe: reporting-only; no runtime emission changes.
   - Expected tests: `tests/test_failure_classifier.py -q`, `tests/test_failure_classification_contract.py -q`, `tests/test_failure_dashboard_controlled_failures.py -q`.
   - Cursor independence: should wait for Block 1 to avoid duplicate owner mapping logic.

4. Narrow accepted authorship expectations for the direct opening golden row.
   - Target files: `tests/test_golden_replay.py`, possibly `tests/test_final_emission_gate.py`.
   - Goal: assert the expected owner bucket for the canonical direct seam and keep compatibility-local as explicit legacy/ambiguous behavior only where tests deliberately exercise it.
   - Why it is safe: assertion-only contraction after observability exists; does not alter golden snapshots.
   - Expected tests: golden replay suite plus opening-specific final emission gate tests.
   - Cursor independence: should wait for Blocks 1-2.

5. Inventory remaining compatibility-local runtime call sites for future contraction.
   - Target files: `game/final_emission_gate.py`, `game/upstream_response_repairs.py`, `tests/test_final_emission_gate.py`.
   - Goal: produce a second, code-adjacent checklist of branches that still invoke the local composer or rebuild payloads at gate time.
   - Why it is safe: reconnaissance/test planning only; no runtime behavior changes.
   - Expected tests: none required beyond existing opening fallback tests if comments/docs are updated.
   - Cursor independence: can run independently, but implementation should wait until owner-bucket observability is in place.

## Test Results

Exact requested command form:

- `python -m pytest tests/test_golden_replay.py -q`: failed before pytest because `python` is not recognized in PowerShell (`CommandNotFoundException`).
- `python -m pytest -m golden_replay -q`: failed before pytest because `python` is not recognized in PowerShell (`CommandNotFoundException`).
- `python -m pytest tests/test_failure_classifier.py -q`: failed before pytest because `python` is not recognized in PowerShell (`CommandNotFoundException`).
- `python -m pytest tests/test_failure_classification_contract.py -q`: failed before pytest because `python` is not recognized in PowerShell (`CommandNotFoundException`).
- `python -m pytest tests/test_failure_dashboard_controlled_failures.py -q`: failed before pytest because `python` is not recognized in PowerShell (`CommandNotFoundException`).

Equivalent workspace runs:

- Bundled Python without `.venv` site-packages: `No module named pytest`.
- `.venv\Scripts\python.exe`: failed to create process because it points at `C:\Users\Master Mandalcio\AppData\Local\Programs\Python\Python312\python.exe`.
- Bundled Python with `PYTHONPATH=.\.venv\Lib\site-packages`, no `--basetemp`: pytest loaded but failed with `PermissionError: [WinError 5] Access is denied: 'C:\Users\Master Mandalcio\AppData\Local\Temp\pytest-of-Master Mandalcio'`.
- Bundled Python with `PYTHONPATH=.\.venv\Lib\site-packages` and workspace `--basetemp`:
  - `tests/test_golden_replay.py -q --basetemp=codex_pytest_tmp_c_opening_golden`: 12 passed.
  - `-m golden_replay -q --basetemp=codex_pytest_tmp_c_opening_marker`: 12 passed.
  - `tests/test_failure_classifier.py -q --basetemp=codex_pytest_tmp_c_failure_classifier`: 24 passed.
  - `tests/test_failure_classification_contract.py -q --basetemp=codex_pytest_tmp_c_failure_contract`: 11 passed.
  - `tests/test_failure_dashboard_controlled_failures.py -q --basetemp=codex_pytest_tmp_c_dashboard_controlled`: 9 passed.

## Files To Provide Back To GPT

- `game/opening_deterministic_fallback.py`, especially `opening_context_from_gm_output` and `deterministic_opening_fallback_text_and_meta`.
- `game/upstream_response_repairs.py`, lines around constants plus `build_upstream_prepared_opening_fallback_payload` and `maybe_attach_upstream_prepared_opening_fallback_payload`.
- `game/final_emission_gate.py`, lines around `_opening_scene_safe_fallback_tuple`, `_enforce_response_type_contract` opening branch, and `_reassert_scene_opening_accepted_candidate`.
- `game/final_emission_boundary_contract.py`, mutation kinds for `select_upstream_prepared_opening_fallback` and `compose_opening_fallback_compatibility_local`.
- `tests/test_golden_replay.py::test_golden_direct_seam_opening_fallback_path_structural_invariants`.
- `tests/helpers/golden_replay.py` observation extraction for opening fallback fields.
- `tests/helpers/failure_classifier.py` `_emission_sublayer` and fallback category rules.
- `tests/test_final_emission_gate.py` opening fallback Block G/H/J tests.
- `tests/test_upstream_response_repairs.py` opening fallback payload tests.

## Block C1 Update — Owner Bucket Mapper

Helper location: `game/final_emission_meta.py` now exposes `opening_fallback_owner_bucket_from_meta`,
`opening_fallback_owner_bucket_from_fields`, and the five `OPENING_FALLBACK_OWNER_*` constants.

Mapping summary: explicit fail-closed opening telemetry maps to `sealed-gate`; explicit upstream-prepared
authorship plus an opening signal maps to `upstream-prepared`; explicit strict-social or retry source/repair
signals map to `strict-social` or `retry`; compatibility-local composition, family-only evidence,
non-opening fallback families, missing telemetry, and partial telemetry map to `unknown-ambiguous`.
When upstream-prepared and fail-closed signals conflict, fail-closed wins as the more specific sealed marker.

Tests added: `tests/test_opening_fallback_owner_bucket.py` covers upstream-prepared, fail-closed,
compatibility-local, missing/empty metadata, non-opening family-only evidence, explicit strict-social,
explicit retry, allowed constants, and the upstream-prepared plus fail-closed conflict rule.

Test results:

- `python -m pytest tests/test_opening_fallback_owner_bucket.py -q`: failed before pytest because `python` is not recognized in PowerShell (`CommandNotFoundException`).
- Bundled Python with `PYTHONPATH=.\.venv\Lib\site-packages` and workspace `--basetemp`:
  - `tests/test_opening_fallback_owner_bucket.py -q --basetemp=codex_pytest_tmp_c1_owner`: 10 passed.
  - `tests/test_final_emission_gate.py -q --basetemp=codex_pytest_tmp_c1_gate`: 219 passed.
  - `tests/test_upstream_response_repairs.py -q --basetemp=codex_pytest_tmp_c1_upstream`: 18 passed.
  - `tests/test_golden_replay.py -q --basetemp=codex_pytest_tmp_c1_golden`: 12 passed.
  - `tests/test_failure_classifier.py -q --basetemp=codex_pytest_tmp_c1_classifier`: 24 passed.
  - `tests/test_failure_classification_contract.py -q --basetemp=codex_pytest_tmp_c1_contract`: 11 passed.

Remaining ambiguity: gate compatibility-local opening composition and gate-initiated stub rebuild remain
visible as `unknown-ambiguous` unless existing telemetry clearly identifies upstream-prepared selection;
the mapper is not yet projected into golden replay observations or failure dashboard rows.

## Block C2 Update — Golden Replay Owner Projection

Field name added: `opening_fallback_owner_bucket`.

Population site: `tests/helpers/golden_replay.py::_observed_turn` now calls
`game.final_emission_meta.opening_fallback_owner_bucket_from_meta(fem)` using the same raw FEM object
already used for `opening_recovered_via_fallback`, `opening_fallback_authorship_source`,
`fallback_family`, `fallback_temporal_frame`, `response_type_repair_kind`, and `final_emitted_source`.
The field is included in structural drift classification and `format_golden_replay_debug` output.

Invariant added: `tests/test_golden_replay.py::test_golden_direct_seam_opening_fallback_path_structural_invariants`
now requires `opening_fallback_owner_bucket == "upstream-prepared"` for the canonical direct opening
fallback seam only. Two focused projection tests also cover synthetic upstream-prepared and fail-closed
FEM payloads mapping to `upstream-prepared` and `sealed-gate`.

Test results:

- `python -m pytest tests/test_golden_replay.py -q`: failed before pytest because `python` is not recognized in PowerShell (`CommandNotFoundException`).
- Bundled Python with `PYTHONPATH=.\.venv\Lib\site-packages` and workspace `--basetemp`:
  - `tests/test_golden_replay.py -q --basetemp=codex_pytest_tmp_c2_golden`: 14 passed.
  - `-m golden_replay -q --basetemp=codex_pytest_tmp_c2_marker`: 14 passed.
  - `tests/test_opening_fallback_owner_bucket.py -q --basetemp=codex_pytest_tmp_c2_owner`: 10 passed.
  - `tests/test_final_emission_gate.py -q --basetemp=codex_pytest_tmp_c2_gate`: 219 passed.
  - `tests/test_failure_classifier.py -q --basetemp=codex_pytest_tmp_c2_classifier`: 24 passed.
  - `tests/test_failure_classification_contract.py -q --basetemp=codex_pytest_tmp_c2_contract`: 11 passed.

Remaining ambiguity: this is still replay/projection-only. Compatibility-local opening composition and
gate-initiated stub rebuild remain visible through the C1 mapper as `unknown-ambiguous` unless existing
telemetry clearly identifies upstream-prepared ownership. Failure classifier/dashboard rows are not wired
to the owner bucket yet; that remains Block C3.

## Block C3 Update — Failure Dashboard Owner Evidence

Fields added: failure classification rows now allow and populate `opening_fallback_owner_bucket`.
`tests/failure_classification_contract.py` exposes `ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS` from the
C1 constants and validates row values against `upstream-prepared`, `sealed-gate`, `retry`,
`strict-social`, and `unknown-ambiguous`.

Classifier/dashboard behavior: `tests/helpers/failure_classifier.py` now uses the projected
`opening_fallback_owner_bucket` when present, otherwise calls
`game.final_emission_meta.opening_fallback_owner_bucket_from_meta` when opening fallback evidence is
present on the observed replay row. The field is evidence only: it supports fallback classification,
`opening_fallback` source-family tagging for opening-specific drift fields, and the `opening_fallback`
emission sublayer, but it does not change runtime behavior or fallback selection. `tests/helpers/failure_dashboard_report.py`
renders the compact evidence as `opening_owner=<bucket>` near sublayer/repair evidence.

Tests added/updated: classifier tests cover upstream-prepared, fail-closed sealed-gate, compatibility-local
`unknown-ambiguous`, projected bucket preservation, and invalid bucket contract rejection. The controlled
dashboard probe now includes an opening fallback owner bucket case and asserts the rendered evidence.

Test results:

- `python -m pytest tests/test_failure_classifier.py -q`: failed before pytest because `python` is not recognized in PowerShell (`CommandNotFoundException`).
- Bundled Python with `PYTHONPATH=.\.venv\Lib\site-packages` and workspace `--basetemp`:
  - `tests/test_failure_classifier.py -q --basetemp=codex_pytest_tmp_c3_classifier`: 29 passed.
  - `tests/test_failure_classification_contract.py -q --basetemp=codex_pytest_tmp_c3_contract`: 12 passed.
  - `tests/test_failure_dashboard_controlled_failures.py -q --basetemp=codex_pytest_tmp_c3_dashboard`: 10 passed.
  - `tests/test_opening_fallback_owner_bucket.py -q --basetemp=codex_pytest_tmp_c3_owner`: 10 passed.
  - `tests/test_golden_replay.py -q --basetemp=codex_pytest_tmp_c3_golden`: 14 passed.
  - `-m golden_replay -q --basetemp=codex_pytest_tmp_c3_marker`: 14 passed.

Remaining ambiguity: the owner bucket remains reporting-only. Compatibility-local opening composition and
gate-initiated stub rebuild still surface as `unknown-ambiguous` unless existing telemetry identifies a
clear owner. No runtime fallback prose, selection, final text, or golden snapshots were changed.

## Block C4 Update — Canonical Authorship Expectation Narrowed

What was narrowed: `tests/test_golden_replay.py::test_golden_direct_seam_opening_fallback_path_structural_invariants`
now requires both `opening_fallback_owner_bucket == "upstream-prepared"` and
`opening_fallback_authorship_source == "upstream_prepared_opening_fallback"`. The old canonical direct
seam allowance for `compatibility_local` authorship was removed and replaced with an explicit
not-equals guard against compatibility-local ownership.

Compatibility paths intentionally retained: `tests/test_final_emission_gate.py` still covers legacy
compatibility-local helper bypasses and asserts their owner bucket as `unknown-ambiguous` when mapped.
Fail-closed sealed-marker paths remain covered and assert `sealed-gate`. Upstream-prepared tuple,
stub-recovery, response-type recovery, and full-gate attach paths remain covered and assert
`upstream-prepared` where the owner bucket is visible through the read-only mapper.

Test results:

- `python -m pytest tests/test_golden_replay.py -q`: failed before pytest because `python` is not recognized in PowerShell (`CommandNotFoundException`).
- Bundled Python with `PYTHONPATH=.\.venv\Lib\site-packages` and workspace `--basetemp`:
  - `tests/test_golden_replay.py -q --basetemp=codex_pytest_tmp_c4_golden`: 14 passed.
  - `-m golden_replay -q --basetemp=codex_pytest_tmp_c4_marker`: 14 passed.
  - `tests/test_final_emission_gate.py -q --basetemp=codex_pytest_tmp_c4_gate`: 219 passed.
  - `tests/test_opening_fallback_owner_bucket.py -q --basetemp=codex_pytest_tmp_c4_owner`: 10 passed.
  - `tests/test_failure_classifier.py -q --basetemp=codex_pytest_tmp_c4_classifier`: 29 passed.
  - `tests/test_failure_classification_contract.py -q --basetemp=codex_pytest_tmp_c4_contract`: 12 passed.
  - `tests/test_failure_dashboard_controlled_failures.py -q --basetemp=codex_pytest_tmp_c4_dashboard`: 10 passed.
  - `tests/test_final_emission_gate.py -q --basetemp=codex_pytest_tmp_c4_gate_rerun`: 219 passed after duplicate assertion cleanup.

Remaining ambiguity: runtime compatibility-local code is intentionally still present for future contraction.
This block only narrows canonical expectations and documents the legacy/ambiguous seams through assertions;
it does not change fallback selection, prose, final text, golden snapshots, or runtime behavior.

## Block C5 Update - Compatibility-Local Runtime Inventory

Search performed:

- `rg -n "compatibility_local|compose_opening_fallback_compatibility_local|deterministic_opening_fallback_text_and_meta|_deterministic_opening_fallback_text_and_meta|opening_fallback_authorship_source|opening_deterministic_fallback" game tests audits`

### Runtime Compatibility-Local Paths

| File | Function / anchor | Trigger | Path type | Owner bucket expectation | Still needed for compatibility | Current coverage | Before removing or tightening |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `game/final_emission_gate.py` | `_opening_scene_safe_fallback_tuple`, around lines 4190-4243; direct composer call around line 4225 | Opening-mode illegality reaches the hard-replace tuple, no usable upstream-prepared opening payload is present, no recoverable upstream stub is present, upstream attach did not report build failure, and `opening_curated_facts` has attachable strings. | Directly composes opening fallback text through `_deterministic_opening_fallback_text_and_meta`; stamps `opening_fallback_authorship_source=compatibility_local_opening_deterministic` except for attach-build-failure blocked meta. | `unknown-ambiguous` for compatibility-local composition; `sealed-gate` when the same tuple selects a fail-closed marker. | Yes, for helper/direct tuple callers that have not gone through gate-entry upstream attach and still rely on the local composer as a legacy fallback. | `tests/test_final_emission_gate.py::test_opening_failure_recovers_via_deterministic_fallback_not_action_outcome`, `test_empty_scene_opening_uses_deterministic_fallback`, `test_opening_scene_safe_fallback_tuple_exact_text_and_classification_snapshot`, `test_opening_scene_safe_fallback_tuple_prefers_upstream_prepared_payload`, and Block G/H/J fail-closed tests. | All canonical opening runtime entry points must guarantee an upstream-prepared payload before final selection, or deliberately fail closed when the payload is absent; legacy tuple helper tests need to be split from canonical invariants. |
| `game/final_emission_gate.py` | `_enforce_response_type_contract`, opening branch around lines 4382-4415; direct composer call around line 4402 | Candidate fails the scene-opening contract or opening validator, is not rescued by preserved-candidate validity, and the gate cannot select a usable upstream-prepared opening payload, cannot recover a stub, and does not hit a fail-closed precondition. | Directly composes opening fallback text through `_deterministic_opening_fallback_text_and_meta`; stamps compatibility-local authorship. | `unknown-ambiguous`. | Yes, until the response-type contract path can require gate-entry upstream attach for every canonical scene-opening turn with curated facts. | `tests/test_final_emission_gate.py::test_opening_failure_recovers_via_deterministic_fallback_not_action_outcome`, `test_scene_opening_fallback_with_opening_seed_facts_emits_seed_facts`, `test_scene_opening_fallback_prefers_opening_curated_facts`, `test_opening_fallback_ignores_contaminated_public_scene_visible_facts`, `test_opening_fallback_never_uses_polluted_narration_visibility_facts`, `test_failed_scene_opening_never_emits_generic_the_scene_fallback`. | Gate-entry attach must be mandatory, stale/missing attach telemetry must be reliable, and direct helper seams must either inject upstream payloads or assert sealed-gate behavior instead of local composition. |
| `game/opening_deterministic_fallback.py` | `deterministic_opening_fallback_text_and_meta`, around lines 186-235 | Called by upstream builder canonically, or by the gate compatibility-local branches above. Empty facts return the sealed marker from the shared composer. | Shared composer; authors fallback prose when facts exist; returns sealed marker when facts are empty. | `upstream-prepared` when called by `build_upstream_prepared_opening_fallback_payload`; `unknown-ambiguous` when called directly by gate compatibility paths; `sealed-gate` only after downstream fail-closed selection stamps the repair. | Yes, as the single text implementation; the compatibility issue is not the function itself, but gate-local runtime invocation. | `tests/test_final_emission_gate.py::test_deterministic_opening_fallback_helper_exact_text_and_meta_snapshot`; `tests/test_upstream_response_repairs.py::test_upstream_prepared_opening_fallback_matches_gate_snapshot_and_family`. | Keep the composer, but contract its runtime callers so final emission selects only upstream-prepared payloads or sealed markers. |

### Runtime Stub-Recovery Paths

| File | Function / anchor | Trigger | Path type | Owner bucket expectation | Still needed for compatibility | Current coverage | Before removing or tightening |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `game/final_emission_gate.py` | `_recover_upstream_opening_fallback_stub_payload`, around lines 4073-4107 | `gm_output` contains `upstream_prepared_opening_fallback`, but the payload is structurally unusable, usually text-only, while `opening_curated_facts` has attachable strings. | Rebuilds an upstream stub in place by calling `build_upstream_prepared_opening_fallback_payload`; sets `opening_fallback_upstream_payload_unusable`, `opening_fallback_upstream_payload_recovered`, and disables compatibility-local composition on success/failure. | Usually `upstream-prepared` after successful rebuild because the rebuilt payload carries upstream authorship; still operationally ambiguous because the gate initiates the rebuild. Failed rebuild leads to `sealed-gate`. | Yes, for malformed/stub payload compatibility at the final gate. | `tests/test_final_emission_gate.py::test_opening_scene_safe_fallback_tuple_recovers_text_only_stub_without_compat_local`, `test_opening_failure_recovers_upstream_snapshot_when_upstream_payload_incomplete`; `tests/test_upstream_response_repairs.py::test_maybe_attach_upstream_opening_replaces_text_only_stub_with_full_snapshot`. | Upstream attach must replace or reject stubs before the gate, and callers must treat structurally unusable payloads as sealed-gate failures or upstream precondition failures. |
| `game/upstream_response_repairs.py` | `maybe_attach_upstream_prepared_opening_fallback_payload`, around lines 243-287 | Resolution kind is `scene_opening`, `opening_curated_facts` is a non-empty list with at least one non-blank string, and existing payload is missing or structurally unusable. | Rebuilds/replaces missing or text-only upstream payload before final emission; records attach-build-failure telemetry if the builder raises. | `upstream-prepared` on success; `sealed-gate` later if attach build failure telemetry causes final gate fail-closed. | Yes, this is the preferred canonical path and should likely remain, though its text-only-stub replacement behavior may become stricter later. | `tests/test_upstream_response_repairs.py::test_maybe_attach_upstream_opening_payload_scene_opening_with_curated_facts`, `test_maybe_attach_upstream_opening_replaces_text_only_stub_with_full_snapshot`, `test_block_m_maybe_attach_records_build_failure_on_emission_debug`, `test_block_m_maybe_attach_success_clears_stale_attach_failure_keys`; `tests/test_final_emission_gate.py::test_block_l_apply_final_emission_gate_scene_opening_maybe_attach_runs_before_deterministic_opening_composer`. | Decide whether upstream should rebuild legacy stubs or fail early; if rebuilding remains, gate-side rebuild can be removed first. |

### Runtime Fail-Closed Paths

| File | Function / anchor | Trigger | Path type | Owner bucket expectation | Still needed for compatibility | Current coverage | Before removing or tightening |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `game/final_emission_gate.py` | `_opening_fail_closed_meta_upstream_missing_insufficient_curated_facts`, around lines 4010-4060 | No usable upstream payload is selected and `opening_curated_facts` is missing, non-list, empty, or has no attachable strings. | Selects the fail-closed sealed marker and metadata; does not compose fallback prose. | `sealed-gate`. | Yes, this is the safer replacement behavior for missing basis. | `tests/test_final_emission_gate.py::test_block_g_fail_closed_empty_curated_facts_emits_marker_not_composed_scene_opening_prose`, `test_block_h_empty_curated_facts_skips_gate_local_deterministic_opening_composer`, `test_block_j_missing_curated_facts_skips_gate_local_deterministic_opening_composer`, `test_scene_opening_fallback_fail_closes_without_curated_context`, `test_scene_opening_fallback_fail_closes_with_empty_curated_facts`, `test_final_gate_scene_opening_missing_curated_facts_records_fail_closed_fem`. | Keep as the target replacement for absent upstream-prepared payloads; tighten authorship stamping so sealed marker paths do not report compatibility-local authorship. |
| `game/final_emission_gate.py` | `_opening_fail_closed_meta_upstream_maybe_attach_prepare_failed`, around lines 4127-4155 | Gate-entry upstream attach attempted to build an opening payload and recorded `opening_upstream_prepare_attach_build_failed` on emission debug. | Selects the fail-closed sealed marker with blocked repair kind `opening_upstream_prepare_attach_failed`. | `sealed-gate`. | Yes, preserves no-prose failure locality when upstream preparation fails. | `tests/test_final_emission_gate.py::test_block_n_opening_attach_build_failure_fails_closed_preserves_block_m_telemetry`; `tests/test_upstream_response_repairs.py::test_block_m_maybe_attach_records_build_failure_on_emission_debug`. | Ensure all canonical attach failures produce this telemetry before final selection; then remove fallback paths that silently compose after attach failure. |
| `game/final_emission_gate.py` | `_opening_fail_closed_meta_upstream_stub_rebuild_failed`, around lines 4158-4187 | Gate detects an unusable upstream stub, curated facts are attachable, but gate-side stub rebuild raises or still does not produce a usable payload. | Selects the fail-closed sealed marker and marks stub recovery failure. | `sealed-gate`. | Yes, while gate-side stub recovery exists. | `tests/test_final_emission_gate.py` Block I and Block N tests around stub recovery/failure; owner bucket assertions expect `sealed-gate` for failed-closed FEM. | Remove after gate-side stub rebuild is removed or fenced; failed stubs should arrive as upstream attach failures or pre-final validation failures. |
| `game/final_emission_gate.py` | `_opening_scene_safe_fallback_tuple` and `_enforce_response_type_contract`, marker selection around lines 4213-4223 and 4390-4400 | Stub rebuild failed, attach build failed, or curated facts are insufficient. | Selects fail-closed sealed marker instead of compatibility-local prose. | `sealed-gate`. | Yes, this is current desired safe behavior. | Same Block G/H/J/N fail-closed tests above plus `tests/test_opening_fallback_owner_bucket.py` sealed-gate cases and golden replay fail-closed projection tests. | Keep as contraction target; clean up compatibility-local authorship remnants on marker FEM only when runtime behavior changes are allowed. |

### Runtime Upstream-Prepared Selection Paths

| File | Function / anchor | Trigger | Path type | Owner bucket expectation | Still needed for compatibility | Current coverage | Before removing or tightening |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `game/upstream_response_repairs.py` | `build_upstream_prepared_opening_fallback_payload`, around lines 189-219 | Upstream attach or stub recovery needs a full prepared opening snapshot from curated facts. | Directly composes through the shared composer, then packages prepared text, opening meta, composition meta, origin, family, temporal frame, and upstream authorship. | `upstream-prepared`. | Yes, canonical owner. | `tests/test_upstream_response_repairs.py::test_upstream_prepared_opening_fallback_matches_gate_snapshot_and_family`; `tests/test_final_emission_gate.py::test_opening_scene_safe_fallback_tuple_exact_text_and_classification_snapshot`; golden replay direct seam invariants. | This should remain the source of deterministic opening fallback text unless a future upstream layer replaces the deterministic composer entirely. |
| `game/upstream_response_repairs.py` | `is_structurally_usable_upstream_prepared_opening_fallback_payload`, around lines 173-186 | Gate or upstream helper sees a candidate payload. | Selects an upstream-prepared payload only if text, composition meta, and opening meta exist. | `upstream-prepared` when true; otherwise unresolved until rebuilt or failed closed. | Yes, protects against text-only stubs being treated as canonical. | `tests/test_final_emission_gate.py::test_block_g_upstream_prepared_opening_payload_if_usable_requires_full_snapshot_shape`; `tests/test_upstream_response_repairs.py::test_maybe_attach_upstream_opening_replaces_text_only_stub_with_full_snapshot`. | If stubs are no longer supported, this can become a hard rejection surface instead of a rebuild predicate. |
| `game/final_emission_gate.py` | `_upstream_prepared_opening_fallback_payload_if_usable`, around lines 4063-4070 | Gate receives `gm_output` with a structurally usable `upstream_prepared_opening_fallback`. | Selects an upstream-prepared payload. | `upstream-prepared`. | Yes, canonical final gate behavior. | `tests/test_final_emission_gate.py::test_block_g_upstream_prepared_opening_payload_if_usable_requires_full_snapshot_shape`, `test_opening_scene_safe_fallback_tuple_prefers_upstream_prepared_payload`, `test_opening_failure_recovers_via_upstream_prepared_payload_when_present`, `test_final_gate_opening_prefers_upstream_prepared_payload_when_present`. | Keep; contraction should make this the only prose-bearing opening fallback selection path at the gate. |
| `game/final_emission_gate.py` | `_opening_scene_safe_fallback_tuple`, upstream branch around lines 4195-4211 | Hard-replace tuple path receives a usable or successfully recovered upstream payload. | Selects an upstream-prepared payload; does not compose locally. | `upstream-prepared`. | Yes. | `tests/test_final_emission_gate.py::test_opening_scene_safe_fallback_tuple_exact_text_and_classification_snapshot`, `test_opening_scene_safe_fallback_tuple_prefers_upstream_prepared_payload`, `test_opening_scene_safe_fallback_tuple_recovers_text_only_stub_without_compat_local`. | Keep selection, but remove the tuple-local compatibility compose branch after legacy helper expectations move to upstream payload injection or sealed-gate expectations. |
| `game/final_emission_gate.py` | `_enforce_response_type_contract`, upstream branch around lines 4382-4389 and authorship around lines 4410-4412 | Scene-opening repair branch receives a usable or successfully recovered upstream payload. | Selects upstream-prepared payload and stamps upstream authorship. | `upstream-prepared`. | Yes. | `tests/test_final_emission_gate.py::test_opening_failure_recovers_via_upstream_prepared_payload_when_present`, `test_opening_failure_recovers_upstream_snapshot_when_upstream_payload_incomplete`, `test_final_gate_auto_attaches_upstream_opening_fallback_before_emission`, `test_block_j_scene_opening_missing_curated_facts_upstream_prepared_payload_still_wins`; golden replay direct seam invariants. | Keep; make missing upstream payload a sealed-gate failure in canonical runtime once compatibility-local coverage is isolated. |

### Test-Only Compatibility Coverage

| File | Function / anchor | What it covers | Runtime or helper-only | Owner bucket expectation | Compatibility status | Removal/tightening prerequisite |
| --- | --- | --- | --- | --- | --- | --- |
| `tests/test_final_emission_gate.py` | `test_deterministic_opening_fallback_helper_exact_text_and_meta_snapshot`, around line 3860 | Shared composer text/meta snapshot. | Test-only helper. | Depends on caller; no runtime owner by itself. | Keep as composer regression even after gate-local compose removal. | Reframe as upstream-builder text fixture if direct composer visibility becomes undesirable. |
| `tests/test_final_emission_gate.py` | `test_opening_failure_recovers_via_deterministic_fallback_not_action_outcome`, around line 4062 | Legacy response-type path can still compose locally and marks compatibility-local authorship. | Runtime path exercised through helper. | `unknown-ambiguous`. | Compatibility-local coverage. | Replace with upstream-prepared payload setup or sealed-gate expectation once local compose is contracted. |
| `tests/test_final_emission_gate.py` | `test_empty_scene_opening_uses_deterministic_fallback`, around line 4183 | Empty candidate with attachable curated facts still recovers through deterministic opening fallback and records compatibility-local authorship in helper path. | Runtime helper path. | `unknown-ambiguous`. | Compatibility-local coverage. | Same as above: canonical path should attach upstream first; helper path should stop proving local compose. |
| `tests/test_final_emission_gate.py` | `test_final_gate_scene_opening_empty_curated_facts_skips_upstream_opening_payload`, around line 4366 | Full gate fail-closed marker currently records compatibility-local authorship while owner bucket maps sealed-gate. | Runtime full gate. | `sealed-gate` by bucket, with authorship residue. | Compatibility/authorship-residue coverage. | Tighten FEM authorship only when emitted metadata changes are allowed. |
| `tests/test_failure_classifier.py` | compatibility-local case around lines 250-281 | Classifier maps compatibility-local authorship to `unknown-ambiguous`. | Test-only observation/classification. | `unknown-ambiguous`. | Keep until compatibility-local runtime paths are gone; then preserve as legacy fixture or remove. | Golden/direct seam and final gate suites must prove no canonical compatibility-local ownership remains. |
| `tests/test_opening_fallback_owner_bucket.py` | `test_compatibility_local_authorship_source_maps_to_unknown_ambiguous`, around line 59 | Owner bucket mapper treats explicit compatibility-local authorship as ambiguous. | Test-only classification. | `unknown-ambiguous`. | Keep while legacy telemetry can exist. | Remove or demote to archived legacy fixture after no runtime FEM/debug can emit compatibility-local authorship for opening fallback. |

### Boundary Contract Coverage

| File | Function / anchor | What it classifies | Path type | Owner bucket expectation | Current coverage | Tightening prerequisite |
| --- | --- | --- | --- | --- | --- | --- |
| `game/final_emission_boundary_contract.py` | `LEGALITY_ALLOWED`, around lines 37-44 | `select_upstream_prepared_opening_fallback` is legality-allowed because it selects a prepared upstream snapshot. | Boundary contract, observes/permits selection. | `upstream-prepared`. | `tests/test_final_emission_gate.py::test_block_c_opening_fallback_mutation_kinds_are_fenced_by_ownership`. | Keep; this should become the sole prose-bearing opening fallback mutation kind at the gate. |
| `game/final_emission_boundary_contract.py` | `SEMANTIC_DISALLOWED`, around lines 49-70 | `compose_opening_fallback_compatibility_local` is semantic-disallowed. | Boundary contract, observes/fences compatibility-local behavior. | `unknown-ambiguous`. | `tests/test_final_emission_gate.py::test_block_c_opening_fallback_mutation_kinds_are_fenced_by_ownership`; `test_block_g_compose_opening_fallback_compatibility_local_never_passed_to_assert_mutation_allowed`. | Keep until runtime no longer composes locally; then decide whether to retain as a forbidden historical mutation kind. |
| `tests/test_golden_replay.py` | direct seam opening fallback invariants around lines 738-786 | Golden replay now requires upstream-prepared authorship and owner bucket for canonical direct seam. | Test-only projection/contract. | `upstream-prepared`. | `tests/test_golden_replay.py::test_golden_direct_seam_opening_fallback_path_structural_invariants`. | Add a regression that canonical direct seam cannot emit `unknown-ambiguous` once local compose paths are contracted. |

### Remaining Runtime Compatibility Paths

- `game/final_emission_gate.py::_opening_scene_safe_fallback_tuple` can still call `_deterministic_opening_fallback_text_and_meta` directly when upstream payload selection, stub recovery, attach-failure fail-closed, and insufficient-curated-facts fail-closed all do not apply.
- `game/final_emission_gate.py::_enforce_response_type_contract` can still call `_deterministic_opening_fallback_text_and_meta` directly under the same effective conditions after a scene-opening candidate fails validation.
- `game/opening_deterministic_fallback.py::deterministic_opening_fallback_text_and_meta` remains intentionally shared; the contraction target is gate-local invocation, not the composer implementation.

### Remaining Stub-Recovery Ambiguity

- `game/final_emission_gate.py::_recover_upstream_opening_fallback_stub_payload` rebuilds malformed upstream payloads inside the gate. The rebuilt payload carries upstream-prepared authorship, and tests assert the owner bucket as upstream-prepared, but the runtime repair locality is still gate-initiated.
- `game/upstream_response_repairs.py::maybe_attach_upstream_prepared_opening_fallback_payload` also replaces text-only stubs before final emission. This is less ambiguous because it runs in the upstream repair layer; future contraction can remove the gate-side rebuild first while preserving upstream replacement.

### Fail-Closed Paths

- Missing, malformed, empty, or non-attachable `opening_curated_facts` select `OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER` through gate fail-closed metadata.
- Upstream attach build failure selects the same marker with `blocked_repair_kind=opening_upstream_prepare_attach_failed`.
- Gate-side stub rebuild failure selects the same marker with stub-recovery failure telemetry.
- Owner bucket expectation is `sealed-gate`, even where older authorship fields still contain compatibility-local residue.

### Candidate Future Contraction Blocks

1. Replace compatibility-local compose branch with sealed-gate fail-closed behavior.
   - Target files: `game/final_emission_gate.py`, `tests/test_final_emission_gate.py`, `tests/test_opening_fallback_owner_bucket.py`, `tests/test_failure_classifier.py`.
   - Expected behavior change: scene-opening repair without a usable upstream-prepared payload would emit the sealed marker instead of gate-composed deterministic opening prose.
   - Risk level: high, because it changes emitted text for legacy/direct helper paths and any runtime path that reaches final emission without upstream attach.
   - Tests that must pass: `tests/test_final_emission_gate.py -q`, `tests/test_upstream_response_repairs.py -q`, `tests/test_opening_fallback_owner_bucket.py -q`, `tests/test_golden_replay.py -q`, `tests/test_failure_classifier.py -q`.
   - Changes runtime behavior: yes.

2. Remove or fence gate-initiated stub rebuild.
   - Target files: `game/final_emission_gate.py`, `game/upstream_response_repairs.py`, `tests/test_final_emission_gate.py`, `tests/test_upstream_response_repairs.py`.
   - Expected behavior change: malformed/text-only upstream opening payloads would be rebuilt only upstream before final emission, or would fail closed at the gate instead of being rebuilt by the gate.
   - Risk level: medium-high, because text-only payload compatibility currently has both upstream and gate-side recovery coverage.
   - Tests that must pass: `tests/test_final_emission_gate.py -q`, `tests/test_upstream_response_repairs.py -q`, `tests/test_opening_fallback_owner_bucket.py -q`.
   - Changes runtime behavior: yes if gate-side text-only stubs can still reach final emission.

3. Require upstream-prepared payload for canonical opening recovery.
   - Target files: `game/final_emission_gate.py`, `game/upstream_response_repairs.py`, `tests/test_final_emission_gate.py`, `tests/test_golden_replay.py`, `tests/test_api_narration_path_selection.py`, `tests/test_start_campaign_api.py`.
   - Expected behavior change: canonical scene-opening recovery would treat missing upstream-prepared payload as a preparation failure or sealed-gate condition, not as permission to compose locally.
   - Risk level: medium, because full-gate paths already auto-attach, but direct helper seams and unusual callers may need fixture updates.
   - Tests that must pass: `tests/test_final_emission_gate.py -q`, `tests/test_upstream_response_repairs.py -q`, `tests/test_golden_replay.py -q`, plus API/start-campaign opening suites.
   - Changes runtime behavior: yes for callers that bypass upstream attach.

4. Split legacy compatibility tests from canonical runtime invariants.
   - Target files: `tests/test_final_emission_gate.py`, `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_opening_fallback_owner_bucket.py`.
   - Expected behavior change: none if done as test organization/assertion work only; compatibility-local expectations become explicitly legacy while canonical tests require upstream-prepared or sealed-gate ownership.
   - Risk level: low-medium, because the work is test-only but may expose hidden runtime assumptions.
   - Tests that must pass: `tests/test_final_emission_gate.py -q`, `tests/test_golden_replay.py -q`, `tests/test_failure_classifier.py -q`, `tests/test_opening_fallback_owner_bucket.py -q`.
   - Changes runtime behavior: no.

5. Add regression proving no compatibility-local ownership in golden replay/direct seam.
   - Target files: `tests/test_golden_replay.py`, `tests/helpers/golden_replay.py`, `tests/test_final_emission_gate.py`.
   - Expected behavior change: none; assertion-only contraction that canonical replay rows and direct seam FEM cannot map to `unknown-ambiguous` from compatibility-local authorship.
   - Risk level: low, assuming Blocks C1-C4 owner-bucket projection remains stable.
   - Tests that must pass: `tests/test_golden_replay.py -q`, `tests/test_final_emission_gate.py -q`, `tests/test_failure_classifier.py -q`.
   - Changes runtime behavior: no.

### Tests

No tests run; documentation/reconnaissance only.

## Block C6 Update - Legacy Compatibility Tests Split From Canonical Invariants

Tests renamed/commented:

- `tests/test_final_emission_gate.py` now labels canonical opening fallback tests with `canonical`, `upstream_prepared`, and no-compatibility-local wording. The direct tuple seam, response-type recovery, full final gate attach, upstream-prepared preference, and missing-curated-facts-with-upstream-payload tests are explicitly canonical.
- `tests/test_final_emission_gate.py` now labels helper-bypass compatibility-local tests with `legacy_compatibility_local_helper_bypass` and `unknown_ambiguous`. These intentionally keep coverage for the two remaining compatibility-local runtime seams without presenting them as canonical behavior.
- `tests/test_final_emission_gate.py` now labels missing/empty curated fact paths with `fail_closed_sealed_gate`.
- `tests/test_golden_replay.py` now labels upstream-prepared projection as canonical, fail-closed projection as sealed-gate, and the direct seam invariant as canonical/no-compatibility-local ownership.
- `tests/test_opening_fallback_owner_bucket.py` now labels upstream-prepared mapping as canonical and compatibility-local mapping as legacy/unknown-ambiguous.
- `tests/test_failure_classifier.py` now names the classifier parametrization cases as canonical upstream-prepared, fail-closed sealed-gate, and legacy compatibility-local unknown-ambiguous.

Canonical invariants now asserted:

- Canonical final gate/direct seam paths assert `opening_fallback_authorship_source == "upstream_prepared_opening_fallback"`.
- Canonical final gate/direct seam paths assert `opening_fallback_owner_bucket == "upstream-prepared"`.
- Canonical final gate/direct seam paths assert compatibility-local authorship is not accepted.
- `tests/test_golden_replay.py::test_golden_canonical_opening_fallback_never_reports_compatibility_local_ownership` is a focused assertion-only regression proving the canonical golden opening fallback path does not report compatibility-local ownership.

Legacy compatibility seams still covered:

- `tests/test_final_emission_gate.py::test_legacy_compatibility_local_helper_bypass_recovers_via_deterministic_fallback_unknown_ambiguous` still exercises `_enforce_response_type_contract` without the upstream attach harness and asserts compatibility-local authorship maps to `unknown-ambiguous`.
- `tests/test_final_emission_gate.py::test_legacy_compatibility_local_helper_bypass_empty_scene_opening_is_unknown_ambiguous` still exercises the empty-candidate helper bypass and asserts compatibility-local authorship maps to `unknown-ambiguous`.
- `tests/test_opening_fallback_owner_bucket.py::test_legacy_compatibility_local_authorship_source_maps_to_unknown_ambiguous` and the classifier legacy case preserve reporting coverage for existing compatibility-local telemetry.

Fail-closed seams still covered:

- Missing/non-list/empty curated-facts tests assert fail-closed marker repair kind `opening_deterministic_fallback_failed_closed` when available and owner bucket `sealed-gate`.
- Full-gate empty curated facts still records the current compatibility-local authorship residue while asserting the owner bucket is `sealed-gate`; this preserves existing runtime behavior and documents the residue for future contraction.
- Upstream attach build-failure and missing-curated-facts FEM tests continue to assert sealed-gate ownership.

Runtime behavior:

- No runtime code changed.
- No final emitted text changed.
- No fallback selection changed.
- No golden snapshots changed.

Can runtime contraction begin next:

- Yes, the tests now separate canonical upstream-prepared invariants from legacy compatibility-local helper-bypass coverage and fail-closed sealed-gate coverage. The next block can begin runtime contraction if it is allowed to change behavior, starting with either replacing compatibility-local compose with sealed-gate behavior or fencing/removing gate-initiated stub rebuild. If the next block must remain assertion-only, add a stronger regression that no full-gate canonical path can emit `unknown-ambiguous`.

Test results:

- `python -m pytest tests/test_final_emission_gate.py -q`: failed before pytest because `python` is not recognized in PowerShell (`CommandNotFoundException`).
- Bundled Python with `PYTHONPATH=.\.venv\Lib\site-packages` and workspace `--basetemp`:
  - `tests/test_final_emission_gate.py -q --basetemp=codex_pytest_tmp_c6_gate`: 219 passed.
  - `tests/test_golden_replay.py -q --basetemp=codex_pytest_tmp_c6_golden`: 15 passed.
  - `-m golden_replay -q --basetemp=codex_pytest_tmp_c6_marker`: 15 passed.
  - `tests/test_opening_fallback_owner_bucket.py -q --basetemp=codex_pytest_tmp_c6_owner`: 10 passed.
  - `tests/test_failure_classifier.py -q --basetemp=codex_pytest_tmp_c6_classifier`: 29 passed.
  - `tests/test_failure_classification_contract.py -q --basetemp=codex_pytest_tmp_c6_contract`: 12 passed.
  - `tests/test_failure_dashboard_controlled_failures.py -q --basetemp=codex_pytest_tmp_c6_dashboard`: 10 passed.

## Block C7 Update - Compatibility-Local Runtime Composition Fenced

Runtime branches changed:

- `game/final_emission_gate.py::_opening_scene_safe_fallback_tuple`
  - Before: after upstream selection, stub recovery, attach-build-failure fail-closed, and insufficient-curated-facts fail-closed checks, the tuple called `_deterministic_opening_fallback_text_and_meta(gm_output)` inside the gate and stamped compatibility-local authorship.
  - After: the final no-upstream/no-recovery branch selects `OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER` with `_opening_fail_closed_meta_upstream_missing_insufficient_curated_facts(gm_output)` and stamps no authorship source.

- `game/final_emission_gate.py::_enforce_response_type_contract`
  - Before: after upstream selection, stub recovery, attach-build-failure fail-closed, and insufficient-curated-facts fail-closed checks, the opening repair branch called `_deterministic_opening_fallback_text_and_meta(gm_output)` inside the gate and stamped compatibility-local authorship.
  - After: the final no-upstream/no-recovery branch selects the sealed marker with `_opening_fail_closed_meta_upstream_missing_insufficient_curated_facts(gm_output)` and stamps no authorship source.

Behavior before/after:

- Upstream-prepared payload present: unchanged; final gate selects upstream-prepared opening fallback text and reports `opening_fallback_authorship_source=upstream_prepared_opening_fallback`, owner bucket `upstream-prepared`.
- Missing/insufficient upstream-prepared payload at the gate: changed; gate no longer composes deterministic opening prose locally and instead fails closed with the sealed marker, repair kind `opening_deterministic_fallback_failed_closed`, and owner bucket `sealed-gate`.
- Upstream attach build failure: unchanged; remains sealed-gate with attach-failure telemetry and no authorship source.
- Gate-side text-only stub recovery success: unchanged; still rebuilds via `build_upstream_prepared_opening_fallback_payload` and reports upstream-prepared ownership.
- Gate-side text-only stub recovery failure: unchanged; remains sealed-gate.

Tests updated:

- `tests/test_final_emission_gate.py`
  - Helper-bypass tests that previously documented legacy compatibility-local composition now expect sealed-gate behavior.
  - Full-gate empty curated-facts FEM now expects no compatibility-local authorship residue while preserving sealed-gate owner bucket assertions.
  - Content-oriented opening fallback tests that should exercise canonical prose now use the gate-equivalent upstream attach harness instead of relying on gate-local composition.

- `tests/test_golden_replay.py`
  - Canonical golden direct seam remains upstream-prepared and continues to assert no compatibility-local ownership.

- `tests/test_opening_fallback_owner_bucket.py` and `tests/test_failure_classifier.py`
  - Legacy compatibility-local telemetry mapping remains test-only/reporting coverage for historical or synthetic observations; it is no longer backed by a reachable final-gate composition branch.

Remaining compatibility-local path:

- No runtime call to `_deterministic_opening_fallback_text_and_meta` remains in `game/final_emission_gate.py`.
- `OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` remains defined in `game/upstream_response_repairs.py` and mapped by `game/final_emission_meta.py` for legacy/synthetic telemetry classification.
- The shared composer remains in `game/opening_deterministic_fallback.py` and is still called by `game/upstream_response_repairs.py::build_upstream_prepared_opening_fallback_payload`, which is the canonical upstream-prepared path.

Opening fallback authorship status:

- Effective final-gate runtime authorship is now upstream-prepared or sealed-gate only.
- Compatibility-local ownership is no longer reachable from normal full-gate opening fallback recovery or the response-type helper branch when no usable upstream payload exists.

Test results:

- `python -m pytest tests/test_final_emission_gate.py -q`: previously failed before pytest because `python` is not recognized in PowerShell (`CommandNotFoundException`).
- `python -m pytest tests/test_opening_fallback_owner_bucket.py -q`: failed before pytest because `python` is not recognized in PowerShell (`CommandNotFoundException`).
- Bundled Python with `PYTHONPATH=.\.venv\Lib\site-packages` and workspace `--basetemp`:
  - `tests/test_final_emission_gate.py -q --basetemp=codex_pytest_tmp_c7_gate2`: 219 passed.
  - `tests/test_opening_fallback_owner_bucket.py -q --basetemp=codex_pytest_tmp_c7_owner2`: 10 passed.
  - `tests/test_golden_replay.py -q --basetemp=codex_pytest_tmp_c7_golden2`: 15 passed.
  - `-m golden_replay -q --basetemp=codex_pytest_tmp_c7_marker2`: 15 passed.
  - `tests/test_failure_classifier.py -q --basetemp=codex_pytest_tmp_c7_classifier2`: 29 passed.
  - `tests/test_failure_classification_contract.py -q --basetemp=codex_pytest_tmp_c7_contract2`: 12 passed.
  - `tests/test_failure_dashboard_controlled_failures.py -q --basetemp=codex_pytest_tmp_c7_dashboard2`: 10 passed.
  - `tests/test_upstream_response_repairs.py -q --basetemp=codex_pytest_tmp_c7_upstream2`: 18 passed.
  - `tests/test_api_narration_path_selection.py -q --basetemp=codex_pytest_tmp_c7_api2`: 36 passed.
  - `tests/test_start_campaign_api.py -q --basetemp=codex_pytest_tmp_c7_start2`: 12 passed.

## Block C8 Update - Gate-Side Stub Rebuild Fenced

Previous ambiguity:

- `game/final_emission_gate.py::_recover_upstream_opening_fallback_stub_payload` could rebuild a malformed/text-only `upstream_prepared_opening_fallback` payload by calling `build_upstream_prepared_opening_fallback_payload` from inside the final emission gate.
- The rebuilt payload carried upstream-prepared authorship, but the repair locality was gate-initiated, so malformed payload ownership remained ambiguous even after C7 removed compatibility-local composition.

Behavior after contraction:

- `game/final_emission_gate.py::_recover_upstream_opening_fallback_stub_payload` now only returns a structurally usable upstream-prepared payload when one is already present.
- If `upstream_prepared_opening_fallback` exists but is structurally unusable by the time it reaches the gate, the gate records `opening_fallback_upstream_payload_unusable=True`, `opening_fallback_upstream_payload_recovered=False`, disables compatibility-local behavior, and fails closed with the existing sealed marker path.
- The gate no longer mutates `gm_output[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY]` and no longer calls `build_upstream_prepared_opening_fallback_payload`.
- `game/upstream_response_repairs.py::maybe_attach_upstream_prepared_opening_fallback_payload` is unchanged and may still replace text-only stubs before final emission. Upstream-side repair remains the canonical place for rebuilding stubs.

Tests updated:

- `tests/test_final_emission_gate.py::test_gate_direct_tuple_text_only_stub_fails_closed_without_rebuild` now expects a text-only stub reaching `_opening_scene_safe_fallback_tuple` to fail closed with owner bucket `sealed-gate`.
- `tests/test_final_emission_gate.py::test_gate_opening_failure_text_only_stub_fails_closed_without_rebuild` now expects a text-only stub reaching `_enforce_response_type_contract` to fail closed with owner bucket `sealed-gate`.
- `tests/test_upstream_response_repairs.py::test_maybe_attach_upstream_opening_replaces_text_only_stub_with_full_snapshot` still proves upstream attach repairs a text-only stub before final emission.
- Canonical/golden opening fallback tests remain upstream-prepared and continue to reject compatibility-local ownership.

Opening fallback runtime authorship status:

- Effective final-gate runtime authorship is now upstream-prepared or sealed-gate only.
- Compatibility-local ownership remains only as legacy/synthetic telemetry classification.
- Gate-side malformed-stub rebuild no longer contributes an ambiguous ownership path.

Test results:

- `python -m pytest tests/test_final_emission_gate.py -q`: failed before pytest because `python` is not recognized in PowerShell (`CommandNotFoundException`).
- Bundled Python with `PYTHONPATH=.\.venv\Lib\site-packages` and workspace `--basetemp`:
  - `tests/test_final_emission_gate.py -q --basetemp=codex_pytest_tmp_c8_gate`: 219 passed.
  - `tests/test_upstream_response_repairs.py -q --basetemp=codex_pytest_tmp_c8_upstream`: 18 passed.
  - `tests/test_opening_fallback_owner_bucket.py -q --basetemp=codex_pytest_tmp_c8_owner`: 10 passed.
  - `tests/test_golden_replay.py -q --basetemp=codex_pytest_tmp_c8_golden`: 15 passed.
  - `-m golden_replay -q --basetemp=codex_pytest_tmp_c8_marker`: 15 passed.
  - `tests/test_failure_classifier.py -q --basetemp=codex_pytest_tmp_c8_classifier`: 29 passed.
  - `tests/test_failure_classification_contract.py -q --basetemp=codex_pytest_tmp_c8_contract`: 12 passed.
  - `tests/test_failure_dashboard_controlled_failures.py -q --basetemp=codex_pytest_tmp_c8_dashboard`: 10 passed.
  - `tests/test_api_narration_path_selection.py -q --basetemp=codex_pytest_tmp_c8_api`: 36 passed.
  - `tests/test_start_campaign_api.py -q --basetemp=codex_pytest_tmp_c8_start`: 12 passed.

## Block C9 Closure - Opening Fallback Authorship Contract

Final runtime owner set:

- `upstream-prepared`: selected only from a structurally usable `upstream_prepared_opening_fallback` payload.
- `sealed-gate`: selected when the upstream payload is missing, malformed/text-only by the time it reaches the gate, upstream attach failed, or curated facts are insufficient.

Runtime closure:

- `game/final_emission_gate.py` no longer calls `_deterministic_opening_fallback_text_and_meta` for opening recovery.
- `game/final_emission_gate.py` no longer imports or calls `build_upstream_prepared_opening_fallback_payload`.
- `game/final_emission_gate.py::_recover_upstream_opening_fallback_stub_payload` does not mutate malformed stubs and does not rebuild prose; it only selects usable upstream payloads or marks unusable gate-arriving payloads for sealed-gate fail-closed behavior.
- `game/upstream_response_repairs.py::maybe_attach_upstream_prepared_opening_fallback_payload` remains the only text-only stub replacement path before final emission.
- `game/upstream_response_repairs.py::build_upstream_prepared_opening_fallback_payload` remains the canonical opening fallback prose packaging point and calls the shared composer.

Remaining synthetic/legacy compatibility-local references:

- `game/upstream_response_repairs.py::OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` remains as a legacy telemetry value.
- `game/final_emission_meta.py` still maps explicit compatibility-local authorship to `unknown-ambiguous` for historical/synthetic observations.
- `tests/test_opening_fallback_owner_bucket.py` and `tests/test_failure_classifier.py` keep synthetic compatibility-local coverage to prove it is classified as `unknown-ambiguous`.
- `game/final_emission_boundary_contract.py` and `tests/test_final_emission_gate.py` keep `compose_opening_fallback_compatibility_local` as semantic-disallowed boundary taxonomy.

Proof searches:

- Search run: `rg -n "compatibility_local|compose_opening_fallback_compatibility_local|_deterministic_opening_fallback_text_and_meta|deterministic_opening_fallback_text_and_meta|build_upstream_prepared_opening_fallback_payload|opening_fallback_owner_bucket|opening_fallback_authorship_source" game tests audits`.
- Runtime result: composer references remain in the shared composer module and upstream builder, plus tests that monkeypatch the gate composer to prove it is not called. No final-gate runtime call to `_deterministic_opening_fallback_text_and_meta` remains.
- Runtime result: `build_upstream_prepared_opening_fallback_payload` references remain in upstream repairs and tests. No final-gate import or call remains.
- Runtime result: compatibility-local references remain in legacy constants, mapper/classifier tests, boundary taxonomy, and historical audit sections. They are not reachable through final-gate opening recovery.

Invariant lock:

- `tests/test_final_emission_gate.py::test_full_gate_malformed_opening_payload_without_upstream_repair_is_sealed_gate` proves a full final-gate path with a malformed/text-only upstream opening payload and no upstream repair reports sealed-gate, not compatibility-local or unknown-ambiguous.
- Canonical final-gate and golden replay opening fallback paths continue to require upstream-prepared authorship and reject compatibility-local authorship.
- Missing/malformed upstream opening payload paths now map to sealed-gate.

Cycle C opening fallback candidate status:

- Complete for opening fallback authorship contraction. Effective runtime authorship is upstream-prepared or sealed-gate only.
- Remaining compatibility-local handling is legacy/synthetic classification and forbidden boundary taxonomy only.

Recommended next fallback family:

- The next contraction candidate should be a non-opening fallback family with remaining gate-authored prose or ambiguous authorship. Based on the prior inventories, action/answer response-type fallback surfaces and generic acceptance-quality/global-scene terminal fallback families are good next candidates; prioritize the one with the most direct final-gate prose ownership still present.

Test results:

- `python -m pytest tests/test_final_emission_gate.py -q`: failed before pytest because `python` is not recognized in PowerShell (`CommandNotFoundException`).
- Bundled Python with `PYTHONPATH=.\.venv\Lib\site-packages` and workspace `--basetemp`:
  - `tests/test_final_emission_gate.py -q --basetemp=codex_pytest_tmp_c9_gate`: 220 passed.
  - `tests/test_upstream_response_repairs.py -q --basetemp=codex_pytest_tmp_c9_upstream`: 18 passed.
  - `tests/test_opening_fallback_owner_bucket.py -q --basetemp=codex_pytest_tmp_c9_owner`: 10 passed.
  - `tests/test_golden_replay.py -q --basetemp=codex_pytest_tmp_c9_golden`: 15 passed.
  - `-m golden_replay -q --basetemp=codex_pytest_tmp_c9_marker`: 15 passed.
  - `tests/test_failure_classifier.py -q --basetemp=codex_pytest_tmp_c9_classifier`: 29 passed.
  - `tests/test_failure_classification_contract.py -q --basetemp=codex_pytest_tmp_c9_contract`: 12 passed.
  - `tests/test_failure_dashboard_controlled_failures.py -q --basetemp=codex_pytest_tmp_c9_dashboard`: 10 passed.
  - `tests/test_api_narration_path_selection.py -q --basetemp=codex_pytest_tmp_c9_api`: 36 passed.
  - `tests/test_start_campaign_api.py -q --basetemp=codex_pytest_tmp_c9_start`: 12 passed.

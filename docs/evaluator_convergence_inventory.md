# Evaluator Convergence Inventory

Block A inventory for evaluator-layer ownership, overlap, and drift risk. This document is descriptive only: no runtime behavior, scoring logic, gate behavior, engine truth, or planner behavior is changed here.

## A. Evaluator Charter

The Evaluator layer exists to make offline, artifact-backed judgments about finished turns, transcripts, and architecture surfaces. It may score playability, narrative authenticity, scenario-spine health, and behavioral gauntlet slices; it may observe normalized telemetry and produce bounded operator reports; and it may audit architecture drift with static heuristics. It is offline only, deterministic where possible, read-only, performs no runtime repairs, has no gate legality authority, and has no engine truth authority. Evaluator output can inform humans and regression triage, but must not decide live route legality, retry behavior, emitted text, state mutation, or canonical runtime truth.

## B. Evaluator-Owned Modules

| File path | Primary responsibility | Inputs consumed | Outputs produced | Role | Imports runtime/gate modules? | Suspicious import notes |
| --- | --- | --- | --- | --- | --- | --- |
| `game/narrative_authenticity_eval.py` | Deterministic offline scoring over shipped Narrative Authenticity telemetry; builds evaluator observability events. | Turn packet context, API/gm-output payload, `_final_emission_meta` / merged NA fields, dead-turn telemetry via normalized bundle, player-facing text for light flags. | `passed`, `scores`, `narrative_authenticity_verdict`, `rumor_realism_axes`, `gameplay_validation`, reasons, supporting metrics, canonical evaluator observability event. | Scores and observes. | Imports `game.final_emission_meta`, `game.telemetry_vocab`, `game.validation_layer_contracts`. | Import of `validation_layer_contracts` is currently a bounded constant read (`NA_SHADOW_RESPONSE_DELTA_FAILURE_REASON`) and matches the audit allowlist. No live gate/repair import observed. |
| `game/playability_eval.py` | Deterministic per-turn playability scoring with stable schema and dead-turn exclusion handling. | Player prompt, GM text or `gm_output.player_facing_text`, prior player/GM text, optional debug traces, normalized observational telemetry bundle. | Versioned `overall`, axis scores for direct answer / player intent / logical escalation / immersion, summary, `gameplay_validation`; rollup helper for run-level gameplay validation. | Scores. | Imports `game.final_emission_meta` only. | No suspicious live gate/engine import observed. Text heuristics overlap with behavioral gauntlet and scenario-spine grounding but scope differs. |
| `game/scenario_spine_eval.py` | Deterministic offline whole-session and branch-divergence evaluation for scenario-spine transcripts. | `ScenarioSpine` definitions, branch id, transcript rows, player/GM text, per-turn `meta` envelope. | `session_health`, `axes`, `detected_failures`, warnings, checkpoint results, degradation-over-time, metadata completeness, branch divergence. | Scores and audits artifact completeness. | Imports `game.scenario_spine` and `game.scenario_spine_opening_convergence`. | Opening convergence import is evaluator-side consumption of recorded meta/turn rows. It is adjacent to runtime opening seams, so ownership should stay explicitly observational. |
| `game/scenario_spine.py` | Pure deterministic schema/data model for scenario spines, branch scripts, anchors, checkpoints, serialization, and definition validation. | JSON-compatible spine dictionaries or dataclass instances. | Frozen dataclasses, stable dict serialization, definition validation errors. | Supports. | No runtime/gate imports. | No suspicious import observed. It is schema support, not scoring. |
| `game/telemetry_vocab.py` | Leaf module for canonical observational telemetry vocabulary and event envelope. | Raw phase/action/scope/owner/reason/data values from projection callers. | Normalized phase/action/scope tokens, deduped reason lists, `build_telemetry_event` dictionaries. | Supports and observes. | No runtime/gate/evaluator imports. | No suspicious import observed. Risk is conceptual: event normalization could become policy if callers branch on it in live orchestration. |
| `game/stage_diff_telemetry.py` | Bounded raw stage-diff snapshots/transitions during gate/retry work plus read-side event projection. | Mutable `gm_output`, final-emission meta projection, turn packet route/fallback fields, before/after snapshots. | `metadata["stage_diff_telemetry"]` snapshots/transitions, compact text fingerprints/previews, canonical stage-diff observability events. | Observes and supports. | Imports `game.final_emission_meta`, `game.telemetry_vocab`, `game.turn_packet`. | `turn_packet` import is documented as compatibility wrapper for gate packet access. This is not evaluator-owned scoring, but it is evaluator-adjacent telemetry and a drift risk if expanded into legality decisions. |

## C. Evaluator-Owned Runners / Tools

| File path | What it drives | What it records | Re-scores or attaches evaluator output? | Artifact files written | Secondary interpretation risks |
| --- | --- | --- | --- | --- | --- |
| `tools/run_playability_validation.py` | Fixed playability scenarios through `POST /api/chat`, using in-process `TestClient` or `--base-url`; optionally resets campaign and checks upstream-dependent run gate. | Per-turn prompt, GM text, resolution kind, playability eval, narrative authenticity eval, dead-turn visibility, `_final_emission_meta`, API status/error; summary and debug payloads. | Attaches `evaluate_playability(...)` and `evaluate_narrative_authenticity(...)`; summary mirrors final turn playability and rollup helpers. It does not re-score playability. | `artifacts/playability_validation/<UTC>_<scenario_id>/transcript.json`, `summary.json`, `run_debug.json`. | Imports live API/reset/upstream gate modules because it is a runner, not an evaluator. Risk: `summary_from_eval` and dead-turn rollup can look like a second pass/fail layer unless kept clearly as artifact/report wrapping. |
| `tools/run_scenario_spine_validation.py` | Scenario-spine branches through `POST /api/chat`, in-process or remote; loads spine JSON, resolves branch aliases, optionally resets campaign. | Transcript rows, stable per-turn `meta` envelope, full debug payloads, evaluator results, operator summaries, aggregate branch data. | Calls `evaluate_scenario_spine_session(...)` once per branch and `evaluate_scenario_spine_branch_divergence(...)` for aggregate. Operator markdown interprets evaluator fields for humans but does not change evaluator output. | Per branch: `transcript.json`, `session_health_summary.json`, `run_debug.json`, `compact_operator_summary.md`. Aggregate: `aggregate_session_health_summary.json`, `aggregate_operator_summary.md`. | The operator summary creates suggested debug focus and compact labels; useful, but could be mistaken for canonical scoring if downstream automation reads markdown instead of JSON evaluator output. |
| `tools/validation_layer_audit.py` | Static validation-layer drift audit over Python files using `game.validation_layer_contracts` and docs pointers. | Import relationships, bucket classifications, text heuristics, documented residue themes. | Does not score game behavior; emits heuristic findings about ownership drift. | CLI prints JSON or markdown to stdout; tests for related architecture audit write temp artifacts, but this tool itself does not write repo artifacts in normal use. | Heuristic bucket names can become stale as modules move. Risk is false confidence: it detects suspicious imports/text, not semantic ownership proof. |

## D. Evaluator-Owned Test Domains

| Test file | Primary invariant under test | Likely owner domain | Canonical owner or smoke/secondary coverage | Overlaps another test domain? |
| --- | --- | --- | --- | --- |
| `tests/test_dead_turn_evaluation_threading.py` | DTD-style guarantee that evaluators/gauntlet consume `_final_emission_meta["dead_turn"]` and exclude invalid gameplay without locally classifying upstream failures. | Dead-turn telemetry threading across evaluator consumers. | Canonical for evaluator consumption of dead-turn metadata; secondary for final-emission meta read helpers. | Overlaps `tests/test_final_emission_meta.py` on normalized observational bundle and FEM read helpers; overlaps behavioral gauntlet on dead-turn run report. |
| `tests/test_behavioral_gauntlet_eval.py` | Offline behavioral gauntlet axes: neutrality, escalation correctness, reengagement, dialogue coherence, metadata-light operation, expected-axis filtering. | Behavioral evaluator helper domain (`tests/helpers/behavioral_gauntlet_eval.py`). | Canonical for behavioral gauntlet scoring helper behavior. | Overlaps playability on player-facing directness/escalation/coherence concepts; overlaps scenario-spine on local reset / speaker drift / continuity signals. |
| `tests/test_final_emission_meta.py` | FEM schema, narrative authenticity metadata merge/read normalization, normalized observational bundle, FEM/stage-diff/evaluator observability bundle shapes. | Final-emission metadata and telemetry normalization. | Canonical for FEM helper behavior and normalized read-side telemetry shapes; secondary for evaluator event bundling integration. | Overlaps `test_dead_turn_evaluation_threading.py` on dead-turn read path and with stage-diff telemetry tests on projection surfaces. |
| `tests/test_architecture_audit_tool.py` | Static architecture audit shape, ownership inference, docs/test reconciliation, hotspot classification, ledger consistency. | Architecture audit / ownership governance. | Canonical for `tools/architecture_audit.py`, not directly for `tools/validation_layer_audit.py`. Secondary evidence for validation-layer audit posture. | Overlaps `tools/validation_layer_audit.py` conceptually on ownership drift and overlap detection; separate tool and test surface. |

No tests changed in Block A; inventory-only.

## E. Overlap / Duplication Risks

| Concept | Places observed | Classification | Notes |
| --- | --- | --- | --- |
| Dead-turn / gameplay validity | `game.final_emission_meta` normalized bundle and summaries; `game.playability_eval`; `game.narrative_authenticity_eval`; `tests/helpers/behavioral_gauntlet_eval.py`; `tools/run_playability_validation.py`; `tests/test_dead_turn_evaluation_threading.py`. | Healthy layered coverage with drift risk. | Good pattern: all evaluator consumers should read the final-emission dead-turn payload instead of classifying upstream failures. Drift risk is each evaluator adding its own exclusion summary fields. |
| Narrative authenticity | Runtime NA metadata in FEM; `game.narrative_authenticity_eval.py`; `tools/run_playability_validation.py`; `game.stage_diff_telemetry.py` curated NA projection; `docs/playability_validation.md`. | Healthy layered coverage. | Runtime NA owns checks/telemetry; evaluator scores shipped telemetry; stage-diff only observes a curated slice. Keep NA eval off live gate paths. |
| Playability | `game.playability_eval.py`; `tools/run_playability_validation.py`; behavioral gauntlet helper/tests; scenario-spine narrative grounding / continuation health. | Unclear ownership / likely drift risk. | Playability is per-turn scoring, behavioral gauntlet is test-helper behavioral scoring, and scenario-spine is session health. Concepts such as direct answer, escalation, immersion, coherence, and generic filler recur. |
| Scenario-spine session health | `game.scenario_spine_eval.py`; `tools/run_scenario_spine_validation.py`; `docs/scenario_spine_validation.md`; opening/continuation convergence modules consumed from recorded meta. | Healthy layered coverage with drift risk. | Runner drives and records; evaluator owns branch health; docs are clear. Risk sits around opening/continuation convergence being both runtime-enforced and offline-evaluated. |
| Metadata completeness | `game.scenario_spine_eval.evaluate_transcript_metadata_completeness`; `tools/run_scenario_spine_validation.build_transcript_turn_meta`; `tests/test_final_emission_meta.py`; `_final_emission_meta` read helpers. | Probable duplication / unclear ownership. | Scenario-spine metadata completeness is transcript-envelope completeness, while FEM tests own `_final_emission_meta` shape. Both can be described as "metadata completeness"; names should stay precise. |
| Telemetry normalization | `game.telemetry_vocab.py`; `game.final_emission_meta` normalized bundle/event assembly; `game.stage_diff_telemetry.py`; `game.narrative_authenticity_eval.build_evaluator_observability_events`. | Healthy layered coverage. | Vocabulary is leaf envelope; domain modules own raw semantics and projections. Risk of policy-by-telemetry if live code begins treating canonical events as decisions. |
| Architecture audit / validation-layer audit | `tools/architecture_audit.py` tested by `tests/test_architecture_audit_tool.py`; `tools/validation_layer_audit.py`; `docs/validation_layer_separation.md`. | Unclear ownership / likely drift risk. | Both audit ownership drift but at different scopes. Architecture audit is broad subsystem ownership; validation-layer audit is Objective #11 layer-specific. Names and docs should preserve that split. |
| Branch divergence / transcript health | `game.scenario_spine_eval.evaluate_scenario_spine_branch_divergence`; scenario-spine aggregate artifacts; transcript/gauntlet regression tests elsewhere. | Healthy layered coverage with drift risk. | Scenario-spine branch divergence is deterministic transcript comparison from same fixture/start state. Transcript health tests may also assert cross-turn divergence or continuity, but should remain regression coverage rather than the branch-divergence owner. |

## F. Telemetry Surface Inventory

| Surface | Canonical owner | Evaluator use | Risk of becoming policy | Appears redundant? |
| --- | --- | --- | --- | --- |
| `_final_emission_meta` | `game.final_emission_meta.py` for packaging/read-side helpers; live write timing remains gate/orchestration owned. | NA eval reads NA fields and dead-turn block; playability reads normalized bundle for dead-turn exclusion; runners copy into artifacts; scenario-spine records under transcript `meta.final_emission_meta`. | Medium. FEM contains gate legality outcomes and evaluator consumers must not feed them back into live routing. | Not redundant; it is the primary shipped metadata surface. |
| Normalized observational telemetry bundle | `game.final_emission_meta.assemble_unified_observational_telemetry_bundle` and `normalized_observational_telemetry_bundle`; vocabulary from `game.telemetry_vocab.py`. | Gives evaluators and tests stable read-side shapes for FEM, dead-turn, stage-diff, and evaluator events. | Medium-high if treated as a runtime bus. | Some overlap with raw FEM/stage-diff is intentional; bundle is normalized read view. |
| Evaluator observability events | `game.narrative_authenticity_eval.build_evaluator_observability_events` for NA evaluator projection; vocabulary envelope owned by `game.telemetry_vocab.py`. | Lets unified bundles expose evaluator result as observational event without invoking scoring. | Medium. `passed`/`rejected` words are tempting to misuse as legality. | Not redundant if bounded to evaluator phase; overlaps raw eval result by design. |
| Stage-diff telemetry | `game.stage_diff_telemetry.py`. | Consumed by final-emission meta bundle assembly and tests as bounded gate-stage observability; scenario/playability artifacts may carry it indirectly via payload/debug meta. | Medium-high because it is produced during gate/retry work. Must remain inspect-only. | Partly redundant with FEM repair/fallback flags, but useful as transition history rather than final state. |
| Scenario-spine transcript meta | Runner-owned construction in `tools/run_scenario_spine_validation.py`, completeness evaluation in `game.scenario_spine_eval.py`. | Scenario-spine evaluator checks source row completeness and consumes recorded opening/continuation/FEM/planner/spine identity fields. | Low-medium. Mostly artifact quality, but opening/continuation verdict fields can resemble runtime legality. | Not redundant with FEM; it is a transcript envelope that includes FEM plus other seams. |
| Playability artifacts | `tools/run_playability_validation.py` writes artifacts; `game.playability_eval.py` owns scores. | Offline inspection of per-turn playability and attached NA eval; run summary mirrors evaluator output plus dead-turn rollup. | Medium. Summary fields may be interpreted as release gates if used mechanically. | Some redundancy between transcript turn eval and summary is intentional; summary mirrors final turn. |
| Scenario-spine artifacts | `tools/run_scenario_spine_validation.py` writes artifacts; `game.scenario_spine_eval.py` owns health output. | Offline long-session inspection, aggregate divergence, metadata completeness and operator summary. | Medium. Operator markdown should not become machine policy. | Per-branch JSON and compact markdown duplicate content intentionally for humans. |

## G. Candidate Cleanup Targets

Ranked candidates for later blocks only; do not implement during Block A.

| Rank | Target | Why it matters | Risk level | Suggested later block | Files likely involved |
| ---: | --- | --- | --- | --- | --- |
| 1 | Telemetry thinning and naming boundaries around normalized observational bundles, evaluator events, and stage-diff projections. | Multiple read-side surfaces carry overlapping NA/dead-turn/repair/fallback concepts. Clearer naming and allow-lists would reduce policy-by-telemetry risk. | Medium-high | Block B: telemetry thinning. | `game/final_emission_meta.py`, `game/telemetry_vocab.py`, `game/stage_diff_telemetry.py`, `game/narrative_authenticity_eval.py`, `tests/test_final_emission_meta.py`, `tests/test_stage_diff_telemetry.py`. |
| 2 | Evaluator ownership boundary docs/tests for dead-turn exclusion. | Dead-turn gameplay validity is threaded through playability, NA eval, behavioral gauntlet, and runners. A single ownership statement would prevent local reclassification from creeping back. | Medium | Block B: evaluator ownership boundaries. | `game/playability_eval.py`, `game/narrative_authenticity_eval.py`, `tests/helpers/behavioral_gauntlet_eval.py`, `tests/test_dead_turn_evaluation_threading.py`, `docs/evaluator_convergence_inventory.md`. |
| 3 | Playability vs behavioral gauntlet axis overlap. | Directness, escalation, coherence, immersion, reengagement, and local reset concepts are evaluated by multiple offline helpers. This may be useful layered coverage, but test ownership is not fully obvious. | Medium | Block C: test overlap reduction. | `game/playability_eval.py`, `tests/helpers/behavioral_gauntlet_eval.py`, `tests/test_playability_eval.py`, `tests/test_behavioral_gauntlet_eval.py`, `docs/playability_validation.md`. |
| 4 | Scenario-spine metadata completeness vs final-emission metadata completeness terminology. | Both surfaces talk about metadata completeness but own different things: transcript envelope vs FEM shape. Naming/reporting could drift. | Low-medium | Block B or C, after telemetry thinning. | `game/scenario_spine_eval.py`, `tools/run_scenario_spine_validation.py`, `tests/test_run_scenario_spine_validation.py`, `tests/test_scenario_spine_eval.py`, `tests/test_final_emission_meta.py`, `docs/scenario_spine_validation.md`. |
| 5 | Architecture audit vs validation-layer audit scope split. | Both are static ownership audits. Without a short scope map, maintainers may add the same invariant to both or assume one subsumes the other. | Low-medium | Block D: audit scope cleanup. | `tools/architecture_audit.py`, `tools/validation_layer_audit.py`, `tests/test_architecture_audit_tool.py`, `tests/test_validation_layer_audit_smoke.py`, `docs/architecture_audit_readme.md`, `docs/validation_layer_separation.md`. |
| 6 | Stage-diff `turn_packet` compatibility wrapper. | The import is documented but keeps telemetry close to gate packet structure. If expanded, it could become a second route/fallback authority. | Medium | Block B: telemetry thinning or compatibility fencing. | `game/stage_diff_telemetry.py`, `game/turn_packet.py`, `tests/test_stage_diff_telemetry.py`, `tests/test_turn_packet_stage_diff_integration.py`. |
| 7 | Runner summary interpretation language. | Both runners produce human summaries that mirror evaluator fields. Stronger "view only" language can prevent artifact markdown/summary files from becoming hidden release policy. | Low | Block B: runner/report wording. | `tools/run_playability_validation.py`, `tools/run_scenario_spine_validation.py`, `docs/playability_validation.md`, `docs/scenario_spine_validation.md`. |

## Block A Test Note

No tests changed in Block A; inventory-only. The existing narrow checks remain the relevant verification slice for this document pass.

## Block B — Telemetry Thinning Findings

This section maps the evaluator-adjacent telemetry surfaces that currently overlap. The goal is not to remove fields in Block B; it is to define which surfaces are source truth, which are normalized read views, which are event projections, and which are operator artifacts so later cleanup can thin safely.

### Telemetry surface map

| Surface | Canonical owner | Consumed by | Duplicated / overlapping fields | Surface type | Recommendation | Risk level |
| --- | --- | --- | --- | --- | --- | --- |
| `_final_emission_meta` | `game.final_emission_meta.py` owns FEM shapes/read helpers; live attach timing remains gate/orchestration owned. | `game.narrative_authenticity_eval.py`, `game.playability_eval.py`, `game.stage_diff_telemetry.py`, `tools/run_playability_validation.py`, `tools/run_scenario_spine_validation.py`, FEM tests, dead-turn threading tests. | `checked`, `failed`, `passed`, `status`, `reason_codes`, `failure_reasons`, `dead_turn.validation_playable`; overlaps event `action/reasons/data` projections and evaluator `verdict/passed`. | Raw/source runtime metadata. | Keep. Thin later only by documenting allowed projection families and avoiding new parallel aliases. | High |
| `normalized_observational_telemetry_bundle` | `game.final_emission_meta.normalized_observational_telemetry_bundle` / `assemble_unified_observational_telemetry_bundle`. | Playability and NA evaluators for dead-turn read path; tests and operator/debug consumers. | Repeats normalized `final_emission_meta`, `dead_turn`, `fem_observability_events`, `stage_diff_observability_events`, `evaluator_observability_events`, `stage_diff_surface`. | Normalized read view. | Keep, but mark as inspect-only. Thin later by tightening allowed top-level keys and doc wording, not by changing runtime data. | High |
| `fem_observability_events` | `game.final_emission_meta.build_fem_observability_events`; envelope vocabulary from `game.telemetry_vocab.py`. | Unified bundle tests, dead-turn threading tests, debug/observer consumers. | Projects raw FEM booleans into event `action` plus `data.checked`, `data.failed`, `data.status`; merges `failure_reasons` and `reason_codes` into event `reasons`. | Event projection. | Keep. Thin later by ensuring event top-level stays `phase/owner/action/reasons/scope/data` only; avoid adding raw synonym keys. | Medium-high |
| `evaluator_observability_events` | `game.narrative_authenticity_eval.build_evaluator_observability_events`; envelope vocabulary from `game.telemetry_vocab.py`. | Unified bundle assembly, dead-turn threading tests, evaluator observability readers. | Repeats evaluator `passed`, `narrative_authenticity_verdict`, `reasons`, `excluded_from_scoring` in bounded event data. | Event projection. | Keep. Thin later by keeping evaluator verdict details in `data` and not introducing new event top-level verdict/pass fields. | Medium |
| `stage_diff_observability_events` | `game.stage_diff_telemetry.build_stage_diff_observability_events`; envelope vocabulary from `game.telemetry_vocab.py`. | Unified bundle assembly and telemetry tests. | Repeats route/fallback/repair/retry/NA tail signals already present in raw `stage_diff_telemetry` and FEM. | Event projection. | Keep. Thin later by preserving curated aggregation only; do not expand into full FEM or route authority. | Medium-high |
| `stage_diff_surface` | `game.final_emission_meta._curated_stage_diff_surface_for_bundle`, with raw source owned by `game.stage_diff_telemetry.py`. | Unified observational bundle consumers and tests. | Repeats bounded `snapshots` / `transitions` from raw `metadata["stage_diff_telemetry"]`; overlaps stage-diff events. | Normalized read view / curated surface. | Keep. Thin later if event projection proves sufficient for a consumer, but do not remove raw snapshot history yet. | Medium |
| `scenario_spine` transcript `meta` | `tools/run_scenario_spine_validation.py` constructs source rows; `game.scenario_spine_eval.py` owns completeness checks. | Scenario-spine evaluator, operator markdown, aggregate artifacts, scenario-spine tests. | Includes `final_emission_meta`, `narration_seam`, `opening_convergence`, `response_type_contract`, `planner_convergence`, and `scenario_spine` identity; overlaps FEM and runtime seam metadata. | Operator artifact / transcript source. | Keep. Thin later by naming it "transcript envelope" rather than generic telemetry; avoid interpreting absent optional nested fields as runtime failure unless evaluator explicitly owns that check. | Medium |
| Playability transcript artifacts | `tools/run_playability_validation.py` writes; `game.playability_eval.py` and `game.narrative_authenticity_eval.py` own attached scores. | Humans, regression triage, artifact readers. | Repeats per-turn `playability_eval`, `narrative_authenticity_eval`, `dead_turn_visibility`, summary `run_gameplay_validation`, and `_final_emission_meta` in debug. | Operator artifact. | Keep. Thin later by keeping `summary.json` a mirror and avoiding new score-like fields outside evaluator returns. | Medium |
| Scenario-spine `run_debug` artifacts | `tools/run_scenario_spine_validation.py`. | Human debugging of API payloads and metadata gaps. | Duplicates transcript `meta`, full chat payload, `debug_traces`, and evaluator context that also appear in `transcript.json` / `session_health_summary.json`. | Operator artifact / debug evidence. | Keep. Candidate thin later only for size/privacy if a stable consumer inventory exists; not a Block B removal target. | Low-medium |

### Duplicated telemetry term classification

| Term family | Current use | Preferred classification | Drift note |
| --- | --- | --- | --- |
| `passed` | Evaluator outputs, scenario-spine axes, runtime validation traces such as narrative-mode output, operator summaries. | Domain-local boolean; never infer another layer's authority from the name alone. | High ambiguity because `passed` may mean evaluator score, runtime validation, or session health. |
| `failed` | FEM runtime validation booleans, scenario-spine classification/failure counts, test names. | Raw runtime failure booleans stay in FEM; evaluator/session failures stay inside evaluator outputs. | Keep paired with owner prefix, e.g. `narrative_authenticity_failed`, `response_delta_failed`. |
| `status` | Raw FEM status such as `narrative_authenticity_status`; stage-diff compact NA projection. | Raw runtime terminal/status label. | Do not use `status` for evaluator verdicts; evaluator owns `verdict`. |
| `verdict` | `narrative_authenticity_verdict`, opening convergence verdict, scenario-spine/operator wording. | Evaluator or offline convergence judgment. | Avoid introducing raw FEM `*_verdict` aliases for runtime gate state. |
| `checked` | FEM runtime checks, scenario-spine metadata counts (`turns_checked`), opening/continuation counters. | Raw source/process counter or runtime check flag, scoped by owner. | Safe if owner-prefixed; ambiguous as an event action. |
| `skipped` | Canonical telemetry event action; skip reasons in FEM; opening no-observation language. | Event action when projected; raw `*_skip_reason` remains source metadata. | Do not duplicate raw skip reasons as event top-level fields. |
| `missing` | Event action, metadata completeness fields, missing telemetry/error reasons, missing scenario-spine keys. | Absence signal; keep with scope (`missing_by_key`, `missing_telemetry`, `action=missing`). | Can look like failure; evaluator should decide whether absence fails its own score. |
| `excluded_from_scoring` | Evaluator gameplay validation and rollups derived from FEM dead-turn data. | Evaluator-consumer policy derived from dead-turn source metadata. | Should remain a consequence of `dead_turn.validation_playable is False`, not a new dead-turn classifier. |
| `validation_playable` | FEM nested `dead_turn` source field. | Raw dead-turn-owned runtime/source boolean. | Canonical source for gameplay exclusion; do not recompute in evaluators. |
| `run_valid` | Gameplay validation rollups in playability/gauntlet helpers; upstream-dependent runner gate uses related language. | Evaluator/run artifact summary. | Avoid treating as gate legality. It is a run-scoring eligibility flag. |
| `dead_turn` | FEM nested source block, normalized bundle top-level shortcut, evaluator gameplay validation copies, artifact visibility. | Dead-turn-owned source plus evaluator read-copy. | Healthy duplication when read-only; drift if evaluators classify dead turns directly. |
| `narrative_authenticity_status` | Raw FEM status and stage-diff curated NA projection. | Raw runtime NA status. | Evaluator owns `narrative_authenticity_verdict`; keep both names distinct. |
| `reason_codes` | FEM packaged reason lists, scenario-spine divergence/degradation reason codes. | Domain-owned raw/coded reasons. | Good for source artifacts; event projection should merge into canonical `reasons`. |
| `failure_reasons` | Validator raw reason lists in FEM and scenario-spine continuation failures. | Raw validation/evaluator-local failure detail. | Where both `failure_reasons` and `reason_codes` exist, projections should merge/de-dupe rather than expose both. |
| `reasons` | Canonical event envelope; evaluator result summaries; playability summary text. | Canonical event reasons or evaluator-local explanatory list. | Avoid adding `reason_codes` alongside `reasons` on canonical events. |

### Canonical terminology recommendations

- Raw runtime booleans stay in FEM with owner-prefixed names such as `narrative_authenticity_checked`, `response_delta_failed`, or `dead_turn.validation_playable`.
- Evaluator verdicts stay evaluator-owned. Use names like `narrative_authenticity_verdict`, `overall.passed`, `session_health.classification`, and axis-local `passed` only inside the evaluator return shape that owns them.
- Canonical telemetry events use only `phase`, `owner`, `action`, `reasons`, `scope`, and bounded `data`. Do not add parallel top-level `status`, `verdict`, `reason_codes`, `failure_reasons`, `passed`, or `failed` fields to event dictionaries.
- Dead-turn gameplay exclusion should remain dead-turn/FEM-owned at the source: evaluators consume `dead_turn.validation_playable` through read helpers and may report `excluded_from_scoring`, but should not locally classify transport/API failures into dead turns.
- Runner summaries should mirror evaluator outputs and attach artifact context. They should not reinterpret evaluator scores, derive new pass/fail semantics from copied fields, or treat event `action` as runtime legality.
- When a projection needs both `reason_codes` and `failure_reasons`, merge them into event `reasons` with de-duplication and keep the raw lists only on the source surface.

### Safe cleanup applied in Block B

- Updated `tests/test_final_emission_meta.py::test_response_type_debug_defaults_and_fem_merge_are_stable` from an exact whole-dict assertion to stable subset assertions plus explicit pins for the current opening-fallback diagnostics. The runtime keys are intentional current behavior from `game.final_emission_validators._default_response_type_debug`, `_merge_response_type_meta`, and `_response_type_decision_payload`; no runtime fields were removed.
- No telemetry fields were removed in Block B.

## Block C — Dead-Turn Ownership Boundary

Canonical source of dead-turn truth: `game.final_emission_meta.classify_dead_turn(...)` / `package_dead_turn_snapshot_into_final_emission_meta(...)` produce the source `dead_turn` snapshot under `_final_emission_meta`. Evaluator-facing code must treat that FEM `dead_turn` object as the only source for gameplay-validity exclusion. The read boundary is `read_dead_turn_from_gm_output(...)`, `normalized_observational_telemetry_bundle(...)`, and `summarize_gameplay_validation_for_turn(...)`.

Allowed evaluator behavior:

- Read FEM `dead_turn` through the existing read helpers.
- Derive `run_valid`, `excluded_from_scoring`, `invalidation_reason`, and diagnostic rollups from the already-read `dead_turn.validation_playable` / `is_dead_turn` fields.
- Preserve diagnostic scores for excluded turns when useful for debugging, as `game.narrative_authenticity_eval` already does.
- Present API/chat error counts in artifacts as context, provided those counts do not decide scoring exclusion.

Forbidden evaluator behavior:

- Inspect `ok`, `error`, `api_error`, `upstream_api_error`, `retry_exhausted`, `retry_terminal`, `targeted_retry_terminal`, tags, or fallback strings to decide that a turn is dead.
- Re-run `classify_dead_turn(...)` inside evaluator modules, test helpers, or runner summary code.
- Treat chat transport failure counts as equivalent to `excluded_from_scoring`.
- Invent new dead-turn classes outside the FEM/dead-turn owner.

### Dead-turn consumer classification

| File | Occurrences inspected | Classification | Notes |
| --- | --- | --- | --- |
| `game/final_emission_meta.py` | `upstream_api_error`, `retry_exhausted`, `dead_turn_class`, `validation_playable`, `manual_test_valid`, `is_dead_turn`, `run_valid`, `excluded_from_scoring`. | Source owner plus source-derived summary. | This is the only inspected file that classifies dead turns from runtime/API/fallback signals. That is expected: it packages FEM source metadata and exposes read-only summarization. |
| `game/narrative_authenticity_eval.py` | `validation_playable` in docstring, `excluded_from_scoring` handling, evaluator observability event data. | Source read from FEM/dead_turn and derived summary from source. | Uses `normalized_observational_telemetry_bundle(...)` and `summarize_gameplay_validation_for_turn(...)`; no API error string inspection observed. |
| `game/playability_eval.py` | `excluded_from_scoring`, `run_valid` rollup. | Source read from FEM/dead_turn and derived summary from source. | Uses `normalized_observational_telemetry_bundle(...)` and `summarize_gameplay_validation_for_turn(...)`; rollup consumes prior evaluator outputs. |
| `tests/helpers/behavioral_gauntlet_eval.py` | `excluded_from_scoring`, `is_dead_turn`, `run_valid`. | Source read from FEM/dead_turn and derived summary from source. | `_gm_output_slice_from_row(...)` only passes through existing FEM when present; `_aggregate_gameplay_validation(...)` uses `read_dead_turn_from_gm_output(...)`. No local API-error classification observed. |
| `game/dead_turn_report_visibility.py` | `chat_error_count`, `run_valid`, `excluded_from_scoring`, `validation_playable`, `dead_turn_class`. | Harmless artifact/report presentation. | Reports chat error counts separately, but validity comes from `per_turn_dead_turn_visibility(...)` and `summarize_gameplay_validation_for_turn(...)`. Guard tests now ensure chat errors alone do not invalidate evaluator conclusions. |
| `tools/run_playability_validation.py` | `api_error`, `ok`, `dead_turn_visibility`, `run_gameplay_validation`. | Harmless artifact/report presentation. | Stores `api_error` for debug artifacts. Block C added a comment clarifying that dead-turn validity comes from FEM `dead_turn`, not `ok` / `error` strings. |
| `tests/test_dead_turn_evaluation_threading.py` | `upstream_api_error`, `retry_terminal_fallback`, `validation_playable`, `excluded_from_scoring`, `run_valid`. | Boundary tests. | Now covers positive FEM-dead-turn exclusion and negative API-error-looking payloads without FEM dead-turn. |
| `tests/test_behavioral_gauntlet_eval.py` | `run_valid`. | Smoke/secondary coverage. | Shape smoke confirms valid runs remain valid; detailed dead-turn boundary is in `test_dead_turn_evaluation_threading.py`. |
| `tests/test_final_emission_meta.py` | `dead_turn`, `validation_playable`, event `data`, `excluded_from_scoring`. | Source/read-helper tests. | Guards FEM normalization and event projection, not evaluator classification. |

### Boundary tests

- `tests/test_dead_turn_evaluation_threading.py::test_narrative_authenticity_eval_respects_dtd1_dead_turn_not_upstream_inspection` proves NA evaluator excludes and zeroes positive scores when FEM `dead_turn.validation_playable` is false.
- `tests/test_dead_turn_evaluation_threading.py::test_narrative_authenticity_eval_does_not_infer_dead_turn_from_api_error_shape` proves API-error-looking payload fields without FEM `dead_turn` do not trigger NA exclusion.
- `tests/test_dead_turn_evaluation_threading.py::test_playability_eval_excludes_only_from_fem_dead_turn_source` proves playability ignores API-error-looking payload fields unless FEM `dead_turn.validation_playable` is false.
- `tests/test_dead_turn_evaluation_threading.py::test_behavioral_gauntlet_marks_run_invalid_when_one_turn_is_dead` proves behavioral gauntlet excludes when supplied turn metadata includes FEM `dead_turn` source data.
- `tests/test_dead_turn_evaluation_threading.py::test_behavioral_gauntlet_does_not_infer_dead_turn_from_api_error_shape_without_fem` proves behavioral gauntlet reports chat error context without invalidating scoring when FEM `dead_turn` is absent.

### Block C cleanup result

No evaluator-local dead-turn classifier was found in the inspected evaluator/helper/tool files. No runtime fields, gate legality behavior, engine truth, or evaluator scoring semantics were changed. The only code-adjacent cleanup was a presentation comment in `tools/run_playability_validation.py` and additional boundary tests.

## Block D — Playability / Behavioral Gauntlet Boundary

`game/playability_eval.py` owns deterministic, turn-level player-facing playability scoring. Its schema is versioned with `version`, `overall`, `axes`, `summary`, and `gameplay_validation`. Its canonical axes are `direct_answer`, `player_intent`, `logical_escalation`, and `immersion`, each carrying `score`, `passed`, `reasons`, and `signals`. This evaluator is advisory/offline, but it is the product-facing playability score used by the playability validation runner and playability unit tests.

`tests/helpers/behavioral_gauntlet_eval.py` owns deterministic, shallow behavioral regression checks over short transcript slices. Its helper schema is `schema_version`, `overall_passed`, `axes`, `gameplay_validation`, and `dead_turn_run_report`. Its canonical axes are `neutrality`, `escalation_correctness`, `reengagement_quality`, and `dialogue_coherence`, each carrying `axis`, `passed`, `score`, `reason_codes`, `summary`, and `evidence_turn_indexes`. This helper supports tests/tooling; it is not the canonical playability scorer.

Allowed overlap:

- Both may use deterministic text heuristics and dead-turn gameplay validation summaries.
- Both may flag related concepts such as escalation, coherence, directness, repetition, or immersion/system leakage.
- Tests may use both layers as complementary evidence when a regression spans turn-level usability and transcript-slice behavior.

Forbidden overlap:

- Do not merge the modules or make one call the other for scoring.
- Do not treat behavioral gauntlet axes as canonical playability axes.
- Do not expand playability to absorb every behavioral regression axis merely because a heuristic is similar.
- Do not make runner summaries translate gauntlet `reason_codes` into playability `summary` / `signals`, or vice versa.
- Do not use either evaluator to change runtime gate legality, engine truth, or emitted text.

Canonical tests:

| Domain | Canonical tests | Boundary pin |
| --- | --- | --- |
| Playability evaluator schema and axes | `tests/test_playability_eval.py` | `test_playability_schema_is_turn_evaluator_not_behavioral_gauntlet` asserts playability exposes `version` / `overall` / `summary` and does not mimic gauntlet `overall_passed` / `dead_turn_run_report` / axis `reason_codes`. |
| Behavioral gauntlet helper schema and axes | `tests/test_behavioral_gauntlet_eval.py` | `test_behavioral_gauntlet_schema_is_helper_owned_not_playability_schema` asserts gauntlet exposes `schema_version` / `overall_passed` / `dead_turn_run_report` and does not mimic playability `version` / `overall` / `summary` / axis `signals`. |
| Shared dead-turn source boundary | `tests/test_dead_turn_evaluation_threading.py` | Guards that both consumers use FEM `dead_turn` source data and do not infer dead turns from API-error-looking fields. |

No duplicated heuristic concepts were removed in Block D. The boundary is schema, ownership, and test-domain clarity rather than algorithm consolidation.

## Block E — Scenario-Spine Metadata Terminology

This boundary separates three similarly named surfaces:

- **FEM metadata** is runtime/final-emission metadata. Its canonical owner is `game/final_emission_meta.py`, with gate/final-emission code deciding when runtime metadata is attached. Scenario-spine code may copy FEM into artifacts as `meta.final_emission_meta`, but it does not own FEM semantics or FEM correctness.
- **Scenario-spine transcript `meta`** is an artifact envelope built by `tools/run_scenario_spine_validation.py` and normalized/read by `game/scenario_spine_eval.py`. It includes copied runtime/seam/planner metadata plus runner identity metadata under `meta.scenario_spine`.
- **Metadata completeness** in `session_health.metadata_completeness_*` is an evaluator finding about source transcript envelope key presence before normalization. It is not a FEM validator, not a runtime legality signal, and not proof that nested FEM contents are semantically correct.

Allowed behavior:

- The runner may mirror `final_emission_meta`, `narration_seam`, `opening_convergence`, `response_type_contract`, `planner_convergence`, and `scenario_spine` identity fields into transcript/run-debug artifacts.
- The scenario-spine evaluator may report missing source envelope keys, missing `meta.scenario_spine` identity keys, and first missing turn indexes.
- Present-but-null envelope fields count as present. Optional nested content may be absent without failing metadata completeness.
- A metadata-completeness failure may add a `detected_failures` row for operator visibility while leaving numeric narrative score unchanged, as currently documented and tested.

Forbidden behavior:

- Do not treat `session_health.metadata_completeness_passed` as a runtime FEM correctness verdict.
- Do not use scenario-spine transcript envelope completeness to change gate legality, engine truth, or FEM packaging.
- Do not infer nested FEM validity from the presence of `meta.final_emission_meta`.
- Do not collapse `meta.final_emission_meta` and `meta.scenario_spine` into one generic metadata authority.

Canonical tests:

| Domain | Canonical tests | Boundary pin |
| --- | --- | --- |
| Scenario-spine source envelope completeness | `tests/test_scenario_spine_eval.py` | Missing `meta`, missing envelope keys, and missing `meta.scenario_spine` identity keys fail completeness. |
| Present-but-null envelope fields | `tests/test_scenario_spine_eval.py::test_metadata_completeness_envelope_key_present_null_passes` | Required keys present with `None` values pass; completeness checks presence, not nested value quality. |
| FEM correctness remains separate | `tests/test_scenario_spine_eval.py::test_metadata_completeness_does_not_validate_fem_correctness` and `tests/test_final_emission_meta.py` | Malformed copied FEM content can still be envelope-complete; FEM tests own FEM semantics. |
| Runner artifact envelope | `tests/test_run_scenario_spine_validation.py` | Runner writes evaluator-owned session health and includes metadata-completeness summaries without making them runtime legality. |

No artifact schema changed in Block E. Only docs, comments, and boundary tests were added.

## Block F - Governance Audit Scope Split

`tools/architecture_audit.py` owns broad repository governance. It surveys seeded subsystems, ownership language, docs/tests/runtime alignment, coupling, archaeology/residue, hotspot classification, broken doc references, and patch-accumulation risk across `game/`, `tests/`, `docs/`, and `tools/`. It is the right audit for questions like "which subsystem owns this concern?", "do docs and practical tests agree?", and "is a seam becoming too central or too ambiguous?"

`tools/validation_layer_audit.py` owns the narrow Objective #11 validation-layer separation contract. It uses `game.validation_layer_contracts` and `docs/validation_layer_separation.md` as anchors, then checks Python files for drift across engine/planner/GPT/gate/evaluator responsibilities: evaluator feedback into live paths, gate scoring language, planner/gate/evaluator import mistakes, NA response-delta ownership drift, tolerated within-layer gate splits, and the documented Objective #11 residue.

Allowed overlap:

- Both tools may report ownership drift, ambiguous wording, import concerns, or documentation/test-adjacency risk.
- Both may mention evaluator read-only boundaries and final-emission/gate ownership when those topics are relevant to their own scope.
- Architecture audit may summarize validation-layer audit posture as one governance signal, while validation-layer audit may cite architecture/governance docs as context.

Forbidden overlap:

- Do not merge the tools or make one audit the required implementation backend for the other.
- Do not broaden `validation_layer_audit.py` into general subsystem ownership, test ownership reconciliation, patch-accumulation scoring, or repo-level architecture verdicts.
- Do not narrow `architecture_audit.py` into an Objective #11-only checker or make its subsystem rubric depend on validation-layer-specific findings.
- Do not treat either audit as proof of semantic correctness, runtime legality, evaluator scoring correctness, or engine truth.

Canonical tests:

| Tool | Guard tests | Boundary pin |
| --- | --- | --- |
| `tools/architecture_audit.py` | `tests/test_architecture_audit_tool.py` | Guards broad subsystem governance, report shape, ownership inference, runtime/docs/test reconciliation, hotspot classification, ledger consistency, and no `game` imports. |
| `tools/validation_layer_audit.py` | `tests/test_validation_layer_audit_smoke.py` plus Objective #11 closeout coverage in `tests/test_validation_layer_closeout.py` | Guards the narrow validation-layer audit entrypoint, JSON shape, contract anchors, strict-mode drift flags, benign gate split reporting, and Objective #11 layer-separation import policy. |

No audit scan logic changed in Block F. The split is documentation, docstrings, and light scope tests only.

## Block G — Closeout

Formal closeout lives at `docs/audits/closeouts/evaluator_convergence_closeout.md`.

Evaluator convergence status: **converged / maintenance-grade**. The evaluator layer is frozen as offline, read-only, artifact/telemetry-backed scoring and audit support with no runtime repairs, no gate legality authority, and no engine truth authority.

Remaining work classification: **optional / future evidence only**. Future changes should be limited to concrete bug fixes, stale-doc clarifications, narrowly justified audit heuristic updates, or focused regression tests when drift is observed. Do not casually reopen Blocks A-F, broaden evaluator scope, or change scoring behavior as cleanup.

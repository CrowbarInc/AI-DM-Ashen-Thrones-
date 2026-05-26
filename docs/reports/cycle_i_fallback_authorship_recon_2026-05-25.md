# Cycle I — Fallback Authorship Contraction Recon

Date: 2026-05-25
Scope: Repository reconnaissance only. No runtime code, tests, fixtures, schemas, or instrumentation were changed.

## Executive Summary

The largest fallback authorship ambiguity is now observational rather than textual: a canonical successful opening fallback is composed through `game.opening_deterministic_fallback` and packaged as `upstream_prepared_opening_fallback` by `game.upstream_response_repairs`, and FEM can map it to owner bucket `upstream-prepared`; however, `game.final_emission_meta._fem_selected_fallback_projection` records the selected `scene_opening` runtime lineage event with `owner="game.final_emission_gate"` and `stage="gate"`. That is defensible as selection ownership, but it collapses prose authorship into selector ownership in the frequency and recurrence surface delivered by Cycle H.

The strongest candidate family for contraction is the successful deterministic opening fallback (`scene_opening` / `opening_deterministic_fallback` / upstream-prepared opening payload). Its text owner, packaging owner, selector, fail-closed branch, owner bucket, replay projection, and lineage projection are all separately visible. It has a narrower behavior surface than visibility or strict-social fallback and better owner evidence than retry/global stock.

Opening fallback is suitable as the first Cycle I target. The current production path is already close to a single content owner: `deterministic_opening_fallback_text_and_meta` is called from `game.upstream_response_repairs`, while current gate runtime paths select a prepared payload or produce the sealed fail-closed marker. Retained compatibility-local constants, comments, mutation classifications, and test symbols describe historical protection or inactive compatibility vocabulary, not an observed second production prose author in this search.

Implementation should begin in owner/invariant tests and metadata projection, not prose code or fixtures. The first change should define whether runtime lineage `owner` means fallback prose author or final selecting layer, and then align opening projection fields and tests without changing emitted text.

## Fallback Family Inventory

### Registered Realization Families

The authoritative registry is `game/realization_authority.py::FALLBACK_FAMILIES`; `game.realization_provenance.py` exports matching identifiers and stamps `realization_fallback_family`.

| Fallback family | Current owner | Apparent intended owner | Files | Trigger | Output/payload | Lineage recorded? | Replay asserted? | Ambiguity level | Notes |
|---|---|---|---|---|---|---|---|---|---|
| `plan_backed_gpt_realization` | GPT/expression | GPT/expression | `game/realization_authority.py`, normal generation paths | Valid planner/CTIR realization | Generated player-facing text plus provenance | Not a fallback selection event for accepted text | Indirect structural coverage | Low | Registry baseline, not a failure fallback; included because it is in the family registry. |
| `upstream_prepared_emission` | Upstream response repair / expression boundary | Upstream prepared emission | `game/upstream_response_repairs.py`, `game/final_emission_gate.py` | Answer/action candidate violates response-type contract; sanitizer empty stock may be selected | Prepared answer/action/sanitizer strings; selected answer/action emits text | Yes: `response_type_prepared_emission` when selected | Yes: golden replay and FEM lineage tests | Medium | Same registry family carries answer/action prepared text and sanitizer stock; selection ownership differs by consumer. |
| `strict_social_deterministic_fallback` | Social emission, sometimes selected by gate or sanitizer | Strict-social/social emission for prose; selecting boundary explicit separately | `game/social_exchange_emission.py`, `game/output_sanitizer.py`, `game/final_emission_gate.py`, `game/contract_registry.py` | Social candidate rejection, route-illegal output, empty strict-social sanitized output, terminal dialogue enforcement | NPC-grounded deterministic/minimal dialogue line; `fallback_kind`/`final_emitted_source` | Yes: strict-social and sanitizer variants | Yes | Medium | Sanitizer path already exposes split ownership (`output_sanitizer` selection, `strict_social_emission` prose); gate lineage often reports gate as owner. |
| `planner_convergence_seam_failure` | API emergency path | API emergency realization | `game/api.py`, `game/planner_convergence.py` | Planner convergence seam cannot supply realizable obligations | Forced terminal/emergency result and metadata | Not distinguished by current FEM selected-fallback projection unless it becomes a downstream replacement | Contract tests, not opening replay | Medium | Registered family exists; Cycle H recon recommended lineage but current searched projection centers finalized FEM fallbacks. |
| `gpt_budget_or_provider_failure` | API / GM upstream error path | API emergency realization | `game/api.py`, `game/gm.py`, `game/fallback_provenance_debug.py` | Provider error or manual GPT budget exhaustion | Fast fallback/error-safe response plus provenance fingerprints | Yes when `fallback_provenance_trace` survives to FEM: `upstream_fast_fallback` | Yes: upstream fast-fallback and overwrite-containment tests | Medium | Provenance module labels itself temporary; good evidence, weak permanent ownership anchor. |
| `retry_terminal_fallback` | Retry | Retry | `game/gm_retry.py`, `game/social_exchange_emission.py`, `game/diegetic_fallback_narration.py` | Targeted retry failure or retry exhaustion | Forced retry fallback, social retry line, observe/travel/local-continuation terminal text | Partially: final-source/provenance-driven paths only | Yes in retry tests; less direct golden replay family coverage | Medium | Multiple concrete line providers are grouped under one retry family. |
| `gate_terminal_repair` | Gate | Gate for sealed selection/replacement; injected prose owners for text | `game/final_emission_gate.py`, `game/final_emission_sealed_fallback.py`, `game/final_emission_meta.py` | Candidate cannot pass terminal legality/visibility/acceptance route | Sealed/global/visibility replacement text and FEM owner bucket | Yes: replacement/visibility fallbacks | Yes | Medium | Helper module explicitly must not author or select prose; gate provider closures still span several content sources. |
| `legacy_diegetic_fallback` | Diegetic fallback renderers; opening prepared payload is stamped here | Narrow/retire, or split by concrete owner | `game/diegetic_fallback_narration.py`, `game/opening_deterministic_fallback.py`, `game/upstream_response_repairs.py`, `game/final_emission_gate.py` | Opening, observe, global stock, action continuation, or social templates selected through legacy-compatible surfaces | Diegetic text plus template classification (`scene_opening`, `observe`, `action`, `social`) | Yes for selected projected branches, not uniformly by template id | Yes for opening/global/visibility slices | High | This registry family contains several distinct prose owners and is broader than the concrete opening target. |
| `legacy_unclassified` | Unclear | No emitting owner intended | `game/realization_authority.py`, `game/realization_provenance.py` | Unknown family normalization fallback | Metadata classification only; registry forbids emitted runtime behavior | No intended selected output | Registry/normalization coverage only | Low | Inventory placeholder, not a valid player-facing fallback family. |

### Concrete Player-Facing Fallback Families and Paths

This second view separates behavior-bearing fallback paths that are combined under the realization registry or owner buckets.

| Concrete fallback family | Path and functions/tests | Current layer / owner | Trigger and output | Mutates | Instrumented / replay status | Duplication or ambiguity |
|---|---|---|---|---|---|---|
| Successful opening deterministic fallback | `game/opening_deterministic_fallback.py::deterministic_opening_fallback_text_and_meta`; `game/upstream_response_repairs.py::build_upstream_prepared_opening_fallback_payload`; `tests/test_upstream_response_repairs.py`, `tests/test_final_emission_gate.py`, `tests/test_golden_replay.py` | Composer: upstream/opening helper; payload: upstream response repair; selector: gate | Invalid scene opening with usable curated facts; produces curated-fact opening prose | Surface text and fallback metadata; no semantic state mutation found | FEM records authorship/source/basis; replay asserts content/owner bucket; runtime lineage counts selection | High: successful owner bucket says `upstream-prepared`, runtime lineage event owner says gate. |
| Opening fail-closed marker | `game/final_emission_gate.py::_opening_fail_closed_meta_*`, `_opening_scene_safe_fallback_tuple`, `_enforce_response_type_contract`; gate/replay tests | Gate / final emission | Missing, empty, malformed, or failed upstream opening preparation; emits `[opening_fallback_failed_closed: empty_curated_facts]` | Surface text and failure metadata | Owner bucket `sealed-gate`; lineage kind `opening_failed_closed`; replay asserted | Low: distinct from successful opening and already explicitly gate-owned. |
| Prepared answer/action replacement | `game/upstream_response_repairs.py::build_upstream_prepared_emission_payload`; gate response-type enforcement; replay/FEM tests | Upstream authors text, gate selects | Invalid required `answer` or `action_outcome`; emits prepared minimal response | Surface text and FEM repair metadata | Lineage `response_type_prepared_emission`; replay asserted | Medium: runtime event currently gate-owned despite upstream-prepared prose. |
| Sanitizer empty-output stock | `game/output_sanitizer.py::_mark_sanitizer_empty_fallback`; prepared stock supplied in `game/upstream_response_repairs.py` | Sanitizer selection; upstream stock source | Strip-only sanitizer leaves empty non-social output; emits prepared stillness line | Surface text, sanitizer trace, mutation lineage | Explicit `sanitizer_empty_fallback_owner="output_sanitizer"`; golden replay asserted | Medium: stock text lives upstream while selection owner is intentionally sanitizer. |
| Sanitizer strict-social rescue | `game/output_sanitizer.py::_mark_sanitizer_strict_social_fallback`; `game/social_exchange_emission.py::social_fallback_line_for_sanitizer`; sanitizer/replay tests | Selection: sanitizer; prose: strict-social emission | Empty strict-social sanitizer output; emits social fallback line | Surface text and sanitizer trace | Explicit split fields; lineage counts sanitizer-selected fallback | Low: split ownership is already represented. |
| Strict-social deterministic/minimal emergency | `game/social_exchange_emission.py::deterministic_social_fallback_line`, `minimal_social_emergency_fallback_line`, finalizer; `game/contract_registry.py`; strict-social tests | Social emission, gate consumes/replaces in terminal paths | Invalid or absent strict-social response; emits dialogue-preserving fallback | Surface text and social/FEM metadata | Sources/kinds registry, lineage/replay coverage | Medium: same prose may surface through social, sanitizer, visibility, or sealed terminal paths. |
| Visibility / first-mention / referential replacement | `game/final_emission_gate.py::_standard_visibility_safe_fallback`, enforcement functions; `game/final_emission_visibility_fallback.py`; visibility/gate/replay tests | Gate orchestration and output mutation; helper is route/metadata-only | Visibility or referent legality rejection; emits selected opening, social, or global safe fallback | Surface text and rich visibility metadata | Visibility owner bucket and lineage replacement kind; replay asserted | High: a routing family selecting prose from several underlying families. |
| Sealed/global terminal replacement | `game/final_emission_gate.py`, `game/final_emission_sealed_fallback.py`, `game/diegetic_fallback_narration.py` | Gate replacement; injected prose providers | Terminal legality/acceptance/global scene failure; emits global/action/social/opening branch text | Surface text and sealed metadata | Sealed owner bucket, mutation lineage, replay asserted | Medium: bucket captures route owner, not every underlying prose owner. |
| Classified observe/action diegetic pool | `game/diegetic_fallback_narration.py::render_observe_perception_fallback_line`, `render_global_scene_anchor_fallback`, `npc_pursuit_neutral_nonprogress_fallback_line`; `game/anti_reset_emission_guard.py::local_exchange_continuation_fallback_line`; diegetic/gate tests | Diegetic renderer or anti-reset helper, selected by retry/gate/visibility callers | Observe reinspection, global safe anchor, NPC-pursuit nonprogress, or local-continuation safety path; emits bounded scene/action line | Surface text and template family/timeframe metadata when projected | Some selected forms become gate/retry lineage; template metadata directly tested | High at registry level: several concrete prose owners share `legacy_diegetic_fallback`. |
| Retry terminal / deterministic retry | `game/gm_retry.py::select_deterministic_retry_fallback_line`, `select_terminal_retry_fallback_line`, `force_terminal_retry_fallback`; retry tests | Retry, with social/diegetic providers | Retry exhaustion or selected retry recovery; emits answer/social/observe/travel/local continuation text | Surface text, retry tags, family metadata | Family stamped; partial finalized-lineage visibility | Medium: many payload providers behind one owner family. |
| Upstream fast fallback | `game/api.py::_fast_fallback_for_upstream_error`; `game/gm.py`; `game/fallback_provenance_debug.py`; fast/containment tests | API/GM; gate contains overwrite | API error/provider failure/budget path; emits fast fallback schema/text | Surface text, error metadata, provenance fingerprint | Provenance trace can become runtime lineage; tests assert containment | Medium: temporary provenance is the differentiator. |
| Planner-convergence terminal fallback | `game/api.py::_gm_planner_convergence_seam_terminal`; `game/planner_convergence.py::build_planner_convergence_report`; `tests/test_planner_convergence_contract.py` | API emergency / planner seam | Planner convergence cannot furnish realizable obligations; forces terminal fallback with convergence metadata | Surface text, terminal route and planner-convergence metadata | Registry/provenance exists; not a dedicated finalized FEM lineage kind found | Medium: it resolves through retry terminal fallback output, so planner cause and terminal text owner can collapse. |
| Fallback-behavior repair contract | `game/fallback_behavior.py`; validators/repairs/gate tests | Validator/repair/gate, not a standalone prose family | Meaningful uncertainty violates fallback behavior contract; rewrites bad certainty/meta voice into bounded response | Surface text and FEM repair metadata | `fallback_behavior_repaired` becomes repair/mutation evidence; owner tests exist | Low for test ownership; not a selected fallback family in `FALLBACK_FAMILIES`. |

## Opening Fallback Deep Dive

### Current Paths

| Path | Generation / decision location | Decision owner | Text/content owner | Payload / output | Final emission role |
|---|---|---|---|---|---|
| Prepared successful opening fallback | `game.opening_deterministic_fallback.deterministic_opening_fallback_text_and_meta` is called by `game.upstream_response_repairs.build_upstream_prepared_opening_fallback_payload` | Upstream attaches payload; gate selects it when candidate fails opening validation | `game.opening_deterministic_fallback` for curated-facts-to-prose, carried by upstream payload | `upstream_prepared_opening_fallback` with `prepared_opening_fallback_text`, `opening_fallback_meta`, `opening_fallback_composition_meta`, origin and authorship source | Passes through/selects prepared prose and merges debug/FEM; no live alternate composer call found in `game.final_emission_gate.py`. |
| Response-type opening selection | `game.final_emission_gate._enforce_response_type_contract` | Gate | Prepared payload owner above, unless fail-closed marker | `opening_deterministic_fallback`, `fallback_family_used="scene_opening"`, `opening_recovered_via_fallback=True` | Replaces invalid opening candidate with prepared fallback after validation. |
| Visibility/first-mention opening-safe selection | `game.final_emission_gate._standard_visibility_safe_fallback` -> `_opening_scene_safe_fallback_tuple` | Gate | Prepared opening payload on success; gate marker on fail closed | Seven-field visibility-safe fallback tuple and composition metadata | Selects opening-specific fallback instead of observe/global stock. |
| Fail-closed opening | `_opening_fail_closed_meta_upstream_missing_insufficient_curated_facts`, `_opening_fail_closed_meta_upstream_maybe_attach_prepare_failed`, `_opening_fail_closed_meta_upstream_stub_rebuild_failed` | Gate / final emission | Gate-owned sealed marker | `[opening_fallback_failed_closed: empty_curated_facts]` plus fail-closed metadata | Emits terminal marker; owner bucket is `sealed-gate`. |
| Historical compatibility-local vocabulary | Import/constant/tests around `_deterministic_opening_fallback_text_and_meta` and `OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL` | Historical/compatibility guard only in current search | No active production text path established | `compatibility_local_opening_deterministic` remains a detectable ambiguous value | Current tests assert canonical paths do not report/use it. |

### Current Owner Ambiguity

1. **Prose and selection are distinguishable in FEM but collapsed in runtime lineage.** `opening_fallback_authorship_source="upstream_prepared_opening_fallback"` maps to `opening_fallback_owner_bucket="upstream-prepared"` in `game.final_emission_meta.opening_fallback_owner_bucket_from_meta`. The same selected successful opening becomes a lineage `fallback_selected` event owned by `game.final_emission_gate` in `_fem_selected_fallback_projection`.
2. **The registry stamp is broader than the concrete author.** The successful opening prepared payload is stamped `realization_fallback_family="legacy_diegetic_fallback"` while also carrying `fallback_family_used="scene_opening"`. That preserves historical taxonomy, but a family-frequency read does not by itself say who authored opening prose.
3. **Comments/docstrings preserve a compatibility story that the current runtime search did not confirm.** `game.opening_deterministic_fallback` and `game.upstream_response_repairs` describe a gate compatibility re-call, while production references in `game.final_emission_gate.py` show only an import and current gate paths that select prepared data or fail closed. Tests retain the import to prove no local composition occurs on canonical/fail-closed paths.
4. **Successful opening and fail-closed opening share surface labels but do not share content ownership.** Both are opening fallback outcomes, yet the successful prose is upstream-composed while the marker is gate-authored. A single canonical owner must target the successful prepared opening fallback family, not erase the fail-closed gate exception.

### Strings and Payload Formats

| Shape | Where found | Ownership implication |
|---|---|---|
| Composed opening prose derived from `opening_curated_facts` | `deterministic_opening_fallback_text_and_meta`; expected snapshot in upstream/gate tests | Canonical successful content owner is the opening composer, shipped through upstream preparation. |
| `prepared_opening_fallback_text` plus `opening_fallback_meta` and `opening_fallback_composition_meta` | `build_upstream_prepared_opening_fallback_payload` | Canonical success payload format is explicit and structured. |
| `[opening_fallback_failed_closed: empty_curated_facts]` | `OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER`; gate fail-closed branches | Deliberately different gate-owned terminal payload, not duplicate successful prose. |
| `compatibility_local_opening_deterministic` authorship token | `game.upstream_response_repairs` constants, metadata mapper/tests | Retained ambiguous/legacy observation token; current canonical tests exclude it. |
| Generic observe/global safe fallback strings | `game.diegetic_fallback_narration`, `_scene_emit_integrity_global_fallback_tuple` | Tests prohibit routing a failed opening into this different fallback family. |

### Current Tests

| Test surface | What it owns/asserts |
|---|---|
| `tests/test_upstream_response_repairs.py` | Prepared opening payload structure, content snapshot, authorship source, family classification, attach/rebuild/failure behavior. |
| `tests/test_final_emission_gate.py` opening blocks | Prepared snapshot preference, no compatibility-local composition on canonical/fail-closed paths, opening selection, polluted-input exclusion, fail-closed marker, visibility opening routing, owner-bucket projection through final output. |
| `tests/test_opening_fallback_owner_bucket.py` | Read-side mapping of canonical upstream, sealed-gate failure, retry/strict-social signals, ambiguous compatibility-local and invalid/missing evidence. |
| `tests/test_diegetic_fallback_narration.py` | Template classification and downstream opening FEM carrying `scene_opening` and upstream authorship. |
| `tests/test_start_campaign_api.py` | End-to-end start/opening persistence and curated-basis source behavior. |
| `tests/test_golden_replay.py` | Projection of opening authorship/owner bucket; direct seam invariant that canonical opening never reports compatibility-local ownership; runtime-lineage projection is diagnostic-only. |
| `tests/test_final_emission_meta.py`, `tests/test_runtime_lineage_telemetry.py`, `tests/test_run_scenario_spine_validation.py` | Runtime-lineage event creation, opening/fail-closed counting, recurrence and artifact aggregation. Current assertions model selected opening lineage as gate-owned. |
| `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py` | Opening owner evidence and current symptom-specific investigation routing; classifier/dashboard are projection/triage owners, not prose owners. |

There are not tests asserting that a canonical successful opening is prose-authored by the gate. The conflict is subtler: lineage tests and Cycle H report fixtures explicitly use `owner="game.final_emission_gate"` for an event whose FEM author bucket can be `upstream-prepared`. Those tests assume event owner means selector/decision layer; Cycle I must decide whether that remains the intended definition.

### Current Lineage Visibility

- Successful opening is distinguishable via `opening_recovered_via_fallback`, `opening_fallback_authorship_source`, `fallback_family_used="scene_opening"`, `fallback_temporal_frame="first_impression"`, and replay-computed `opening_fallback_owner_bucket`.
- Fail-closed opening is distinguishable via `opening_fallback_failed_closed`, repair kind `opening_deterministic_fallback_failed_closed`, and bucket `sealed-gate`.
- Runtime lineage distinguishes `scene_opening` from `opening_failed_closed` in `fallback_kind`, and aggregates opening recurrence and gate path frequency.
- Runtime lineage events do **not** currently retain `opening_fallback_owner_bucket` or separate `prose_owner` from selector `owner`.

### Recommended Canonical Owner

For the **successful deterministic opening fallback content family**, use `game.opening_deterministic_fallback` as canonical prose/content owner, with `game.upstream_response_repairs` as the canonical payload packager and `game.final_emission_gate` as selector/fail-closed output owner. If Cycle I requires one machine-countable owner label for that successful family, it should resolve to the upstream-prepared/content side rather than the selecting gate, while preserving a separate gate-owned `opening_failed_closed` variant.

## Lineage / Runtime Attribution Findings

| Mechanism | File path / function | Fields / allowed values observed | Records fallback owner? | Opening distinguishable? | Findings |
|---|---|---|---|---|---|
| Realization family ledger | `game/realization_authority.py::FALLBACK_FAMILIES` | Nine family IDs; `owner_profile`, classification (`SAFE`, `BOUNDED`, `SUSPICIOUS`, `LEGACY`, `UNKNOWN`) | Owner profile only, at broad family level | Only through `legacy_diegetic_fallback`, not concrete `scene_opening` author | Broad authority registry; not enough to contract opening authorship alone. |
| Family stamp | `game/realization_provenance.py` | `realization_fallback_family` normalized to registry IDs | Broad family owner inferable from ledger | Partial | Opening success is stamped as legacy diegetic while richer opening fields carry concrete ownership. |
| Template classification | `game/diegetic_fallback_narration.py::_FALLBACK_TEMPLATE_METADATA` | `fallback_family`: `scene_opening`, `observe`, `action`, `social`; temporal frame `first_impression`, `reinspection`, `continuation` | No owner | Yes: `opening_deterministic_fallback` | Classification prevents opening/observe confusion, not authorship confusion. |
| Opening authored payload | `game/upstream_response_repairs.py::build_upstream_prepared_opening_fallback_payload` | `opening_fallback_authorship_source="upstream_prepared_opening_fallback"`, `upstream_prepared_opening_fallback_origin`, basis fields | Yes for successful payload provenance | Yes | Strongest existing success-owner signal. |
| FEM owner bucket mapper | `game/final_emission_meta.py::opening_fallback_owner_bucket_from_*` | `upstream-prepared`, `sealed-gate`, `retry`, `strict-social`, `unknown-ambiguous` | Yes, read-side mapping | Yes | Correctly distinguishes success and fail-closed; compatibility-local deliberately ambiguous. |
| Sealed bucket stamping | `game/final_emission_sealed_fallback.py` and FEM constants | `sealed-gate`, `strict-social-sealed`, unknown buckets | Yes for route/replacement bucket | Opening may carry composition metadata but sealed bucket is separate | Explicitly route/metadata only; does not author prose. |
| Visibility bucket stamping | `game/final_emission_visibility_fallback.py` | `sealed-gate`, `strict-social-visibility`, `opening-visibility`, unknown buckets; pool/kind fields | Yes for visibility routing bucket | Yes, as opening-visibility route | Routing owner is distinguishable, underlying prose family may still vary. |
| Sanitizer trace | `game/output_sanitizer.py` | `sanitizer_empty_fallback_owner`, `sanitizer_strict_social_selection_owner`, `sanitizer_strict_social_prose_owner`, source and lineage fields | Yes, including an explicit split | Not opening-specific | Best existing model for separating selector owner from prose owner. |
| Mutation lineage | `game/final_emission_meta.py::build_final_emission_mutation_lineage` | Tokens including `opening_fallback_selection`, `prepared_emission_selection`, `sealed_fallback_replacement`, `sanitizer_empty_fallback`, repair/finalize tokens | Indicates writer/selection step, not author identity | Yes as token | Useful sequencing evidence but deliberately not an owner schema. |
| Runtime lineage vocabulary | `game/runtime_lineage_telemetry.py` | Event kinds `fallback_selected`, `speaker_repair`, `mutation`, `gate_outcome`; stages `engine`, `planner`, `gpt`, `retry`, `gate`, `sanitizer`, `post_emission`; fields `owner`, `source`, `fallback_kind`, `repair_kind`, `mutation_kind`, `gate_path`, `recurrence_key` | Yes, one `owner` string only | Yes by `fallback_kind`/`gate_path` | No separate authorship/prose-owner field. |
| FEM runtime-lineage projection | `game/final_emission_meta.py::build_fem_runtime_lineage_events` | Projects successful opening as `fallback_kind="scene_opening"`, `gate_path="opening_fallback"`, `owner="game.final_emission_gate"` | Records selector as owner | Yes | Primary mismatch with FEM owner bucket for canonical successful opening. |
| Scenario-spine aggregation | `tools/run_scenario_spine_validation.py::build_runtime_lineage_summary` | `fallback_frequency`, `speaker_repair_frequency`, `mutation_kind_frequency`, `gate_path_frequency`, `recurring_events` | Only whatever event `owner` supplied in recurrence key | Yes by opening fallback kind | Measurable today, but authorship counts inherit selector/prose collapse. |
| Golden replay/dashboard diagnostics | `tests/helpers/golden_replay.py`, `tests/helpers/failure_dashboard_report.py` | Owner buckets, mutation lineage, runtime lineage list and aggregate frequency output | Opening bucket and runtime owner both observable, separately | Yes | Replay does not treat runtime lineage as drift semantics, preventing existing invariants from detecting attribution mismatch. |

### Missing Fields and Mismatches

- Runtime lineage has no `authored_by`, `prose_owner`, or `selection_owner`; its single `owner` field currently means decision/selection for opening and sanitizer, although sanitizer separately preserves prose ownership in raw trace.
- Successful opening owner is measurable today from FEM/replay owner buckets, but **not directly from aggregated runtime-lineage frequency** without joining back to raw FEM.
- `opening_fallback_owner_bucket` is computed/projection-facing; the lineage event does not carry it.
- Opening documentation and compatibility constants still refer to a compatibility-local composer path; current production search found gate selection/fail-closed behavior but no gate call to the imported opening composer.
- The Cycle H closure report describes opening recurrence as `fallback_selected:gate:game.final_emission_gate:scene_opening`; that is consistent with current code and tests, but not with a future requirement that the fallback family's single canonical owner mean prose authorship.

### What Must Change Before Implementation

Before touching runtime behavior, Cycle I needs a written owner semantic decision: whether fallback `owner` in runtime lineage denotes the author of emitted fallback content, the layer selecting it, or whether split fields are required. Sanitizer strict-social tracing already demonstrates that split ownership can be explicit. Opening can then be contracted through metadata/projection and tests without modifying its fallback text.

## Replay Invariant Findings

| File path | Test / fixture | Invariant asserted | Checks | Ownership observation |
|---|---|---|---|---|
| `tests/test_golden_replay.py` | `test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership` | Canonical opening uses prepared upstream ownership, not compatibility-local | Content/source/family/owner bucket/authorship | Strong success-owner invariant; ideal anchor for Cycle I. |
| `tests/test_golden_replay.py` | `test_golden_canonical_opening_fallback_never_reports_compatibility_local_ownership` | Canonical successful opening owner bucket is `upstream-prepared` | Authorship/owner | Strong and appropriately read-side. |
| `tests/test_golden_replay.py` | `test_golden_observed_turn_projects_canonical_upstream_prepared_opening_owner_bucket` | Replay projection maps raw FEM opening metadata to canonical bucket | Owner projection | Projection-only; does not assert runtime-lineage owner. |
| `tests/test_golden_replay.py` | `test_golden_observed_turn_projects_fail_closed_sealed_gate_opening_owner_bucket` | Failed-closed opening maps to `sealed-gate` | Owner/source/content marker | Correctly distinct from successful opening. |
| `tests/test_golden_replay.py` | `test_golden_observed_turn_projects_runtime_lineage_and_prefers_existing_events` | Runtime lineage is read/projected and preprojected events win | `fallback_kind`, diagnostic projection | Explicitly diagnostic, not replay drift; does not compare lineage owner to owner bucket. |
| `tests/test_golden_replay.py` | `test_golden_drift_classification_ignores_runtime_lineage_diagnostics` | Lineage data does not alter replay drift classification | Replay semantics | Correct for Cycle H, but means ownership conflict is invisible to drift assertions. |
| `tests/test_final_emission_meta.py` | `test_build_fem_runtime_lineage_events_projects_opening_and_fail_closed_fallbacks` | FEM yields distinct opening and fail-closed selected events/gate paths | Fallback kind and gate path | Does not assert owner in this test, though implementation supplies gate owner. |
| `tests/test_runtime_lineage_telemetry.py` | `test_make_runtime_lineage_event_is_json_serializable_and_normalized` | Normalized recurrence key shape | Event owner/kind/stage | Uses gate-owned opening-failed-closed example; schema-level only. |
| `tests/test_run_scenario_spine_validation.py` | `test_transcript_meta_runtime_lineage_prefers_projected_bundle_and_projects_fem_fallback` | Scenario transcript preserves/preprojects opening lineage | Fallback kind/gate path | Does not assert prose owner. |
| `tests/test_run_scenario_spine_validation.py` | `test_build_runtime_lineage_summary_counts_frequency_and_recurrence_without_scoring_fields`; aggregate artifact test | Opening recurrence and frequency count correctly | Fallback count, recurrence, gate path; fixture recurrence contains gate owner | Over-broad if used as authorship proof; it currently locks aggregation shape, not content owner. |
| `tests/test_opening_fallback_owner_bucket.py` | Owner bucket tests | Allowed ownership mapping for successful, fail-closed, retry, strict-social and ambiguous signals | Owner | Correct owner-mapper test home; not a replay test but essential invariant source. |
| `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py` | Opening owner/lineage/display tests | Drift routing and evidence reporting remain meaningful | Owner/projection/reporting | Triage-only; should not define runtime authorship. |
| `tests/test_scenario_spine_opening_convergence.py` | `test_stock_fallback_hit_on_opening_turn_scoring_only` and neighbors | Stock opening observation influences scoring-only convergence behavior | Fallback occurrence/scoring | Adjacent evaluator invariant; not canonical fallback owner coverage. |

### Missing Invariants

- No invariant requires a successful opening fallback runtime-lineage event to retain or agree with the FEM opening owner bucket.
- No invariant states whether lineage `owner` is selection owner or content author when they differ.
- No invariant couples a canonical successful opening selection to `upstream_prepared_opening_fallback_origin`.
- No runtime-lineage invariant distinguishes a successful prepared opening from a hypothetical compatibility-local successful opening beyond the FEM/replay bucket projection.
- No aggregation assertion can answer "how often was upstream-authored opening fallback emitted?" without using raw FEM instead of the lineage summary.

### Likely Cycle I Invariant Shape

For a canonical successful opening fallback emitted from a usable prepared snapshot:

1. Emitted text remains exactly the prepared opening text.
2. `opening_fallback_authorship_source` remains `upstream_prepared_opening_fallback`.
3. Owner bucket remains `upstream-prepared`.
4. Final selection/gate path remains visible as `opening_fallback`.
5. Runtime attribution must preserve both facts without conflation: either `owner` resolves to the canonical fallback author and a distinct selection/gate field records gate selection, or a new split attribution records both author and selector.
6. Fail-closed marker remains a distinct gate-owned opening fallback variant.

## Recommended Cycle I Implementation Blocks

| Block | Goal | Files likely touched | Tests likely touched | Behavior risk | Parallel? | Acceptance criteria |
|---|---|---|---|---|---|---|
| I.A - Opening owner semantics contract | Decide and lock whether lineage `owner` means prose author, selector, or split ownership; document successful opening vs fail-closed exception | `docs/reports/cycle_i_fallback_authorship_recon_2026-05-25.md` follow-up or architecture docs; possibly `game/runtime_lineage_telemetry.py` docstrings only | New/updated focused metadata tests only after decision | None if docs/tests first | Yes with unrelated family recon; no with attribution implementation | One unambiguous rule names canonical successful opening owner and preserves gate-owned fail-closed variant. |
| I.B - Canonical opening lineage projection | Align selected successful opening runtime attribution with the chosen owner semantics while preserving gate path and emitted text | `game/final_emission_meta.py`, possibly `game/runtime_lineage_telemetry.py` if schema adds split field | `tests/test_final_emission_meta.py`, `tests/test_runtime_lineage_telemetry.py` | Low to medium: instrumentation/recurrent key output changes, no prose behavior intended | No with I.C/I.D; same fields | Canonical prepared opening and fail-closed opening produce distinguishable, owner-correct events; no output text changes. |
| I.C - Replay and aggregate invariant lock | Assert raw FEM owner bucket, runtime-lineage attribution, and aggregate recurrence semantics agree for opening | `tests/helpers/golden_replay.py` only if projection fields must be exposed; `tools/run_scenario_spine_validation.py` only if aggregation requires added dimension | `tests/test_golden_replay.py`, `tests/test_run_scenario_spine_validation.py`, `tests/test_failure_classifier.py` as needed | Low to medium: diagnostic artifact shape could change | After I.B | Golden replay remains non-scoring; successful opening is countable under canonical owner; fail-closed remains separately countable. |
| I.D - Compatibility vocabulary retirement decision | Verify whether inactive compatibility-local opening symbols/docs should remain as historical sentinel or be removed in a later behavior-neutral cleanup | `game/opening_deterministic_fallback.py`, `game/upstream_response_repairs.py`, `game/final_emission_gate.py` comments/import boundary, ownership docs | `tests/test_final_emission_gate.py`, `tests/test_golden_replay.py`, `tests/test_opening_fallback_owner_bucket.py` | Low if documentation/symbol cleanup only; medium if compatibility contract changes | Can investigate in parallel with I.A; edit after I.B decision | No doc claims an active alternate prose author without an actual path; any retained compatibility token has an explicitly stated purpose. |
| I.E - Cross-family owner vocabulary follow-up | Apply the settled author-versus-selector rule to prepared answer/action and strict-social/sanitizer variants only after opening proves the pattern | `game/final_emission_meta.py`, `game/output_sanitizer.py` only if a shared split schema is selected, supporting docs | FEM/replay/sanitizer/strict-social tests | Medium; wider attribution contract | No, defer until opening closes | Opening contraction is complete first; no accidental reclassification of adjacent families. |

Recommended order: I.A, I.B, I.C, then I.D. I.E is a deliberately deferred expansion and should not be folded into the first opening implementation pass.

## Files To Pass Back To ChatGPT

### Fallback Implementation

- `game/opening_deterministic_fallback.py` - canonical curated-facts-to-opening-prose composer and fail-closed marker definition.
- `game/upstream_response_repairs.py` - canonical prepared opening payload, authorship token, and attach/rebuild behavior.
- `game/final_emission_gate.py` - opening selection, fail-closed behavior, visibility/opening branch routing, and final output application.
- `game/realization_authority.py` - authoritative family registry and owner profiles.
- `game/realization_provenance.py` - shipped family identifiers and stamping.
- `game/diegetic_fallback_narration.py` - concrete template classification across opening/observe/action/social.
- `game/final_emission_sealed_fallback.py` and `game/final_emission_visibility_fallback.py` - selector/helper boundaries adjacent to opening.

### Lineage / Instrumentation

- `game/final_emission_meta.py` - owner buckets, mutation lineage, runtime-lineage projection, and unified bundle.
- `game/runtime_lineage_telemetry.py` - event schema, allowed stages/event kinds, recurrence key.
- `game/output_sanitizer.py` - existing selection/prose owner split precedent.
- `tools/run_scenario_spine_validation.py` - frequency/recurrence aggregation and artifacts.

### Replay Tests

- `tests/test_opening_fallback_owner_bucket.py` - direct owner mapper contract.
- `tests/test_upstream_response_repairs.py` - payload/content/authorship owner tests.
- `tests/test_final_emission_gate.py` - opening selector/fail-closed/visibility integration locks.
- `tests/test_final_emission_meta.py` and `tests/test_runtime_lineage_telemetry.py` - runtime attribution projection tests.
- `tests/test_golden_replay.py` - canonical opening replay and diagnostic lineage invariants.
- `tests/test_run_scenario_spine_validation.py` - lineage aggregation and recurrence artifacts.
- `tests/test_failure_classifier.py` and `tests/test_failure_dashboard_controlled_failures.py` - projection/triage consequences of owner evidence.

### Docs / Reports

- `docs/reports/cycle_h_runtime_lineage_closure_2026-05-25.md` - current lineage contract and gate-owned opening recurrence example.
- `docs/reports/cycle_h_runtime_lineage_instrumentation_recon_2026-05-23.md` - pre-implementation attribution rationale.
- `audits/cycle_e_block_f_opening_fallback_ownership_comments_2026-05-17.md` - documented split ownership baseline.
- `audits/cycle_f_opening_fallback_owner_routing_recon_20260518.md` - historical routing analysis; compare against current symptom-specific classifier code before relying on it.

### Fixtures / Helpers

- `tests/helpers/golden_replay.py` - observed opening owner buckets and runtime-lineage projection.
- `tests/helpers/failure_classifier.py` - current symptom-specific opening investigation routing.
- `tests/helpers/failure_dashboard_report.py` - lineage frequency rendering and owner evidence display.
- `data/validation/scenario_spines/c1a_opening_convergence_paths.json` - opening-focused scenario fixture for later verification, not for first behavior changes.

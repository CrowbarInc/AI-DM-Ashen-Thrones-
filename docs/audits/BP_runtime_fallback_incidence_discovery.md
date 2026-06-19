# BP Runtime Fallback Incidence Instrumentation Discovery

**Date:** 2026-06-17  
**Scope:** Discovery only. No runtime behavior, fallback selection, emitted text, or replay semantics were changed.

## Executive Summary

The repository can measure fallback incidence without instrumenting the live selectors or changing emission semantics. Finalized final-emission metadata (FEM) is already projected into bounded `fallback_selected` runtime-lineage events, golden replay already places those events beside a per-turn `route_kind`, and scenario-spine artifacts already persist the events and aggregate their frequencies.

The missing BP capability is not fallback detection. It is **turn-aware aggregation**:

- a denominator (`eligible_turn_count`) for trigger rates;
- correlation of each fallback event with the containing turn's domain route (`route_kind`);
- correlation with the emission outcome (`final_route`, normally `accept_candidate` or `replaced`);
- consistent family and owner dimensions across the dual family taxonomies and three owner-bucket families;
- a deterministic JSON/Markdown incidence report.

The lowest-risk first implementation is a read-side report builder over replay/scenario-spine turn rows. It should reuse `build_fem_runtime_lineage_events()` and `summarize_runtime_lineage_events()`, join rather than modify events, and write report-only artifacts. Live passive counters are not needed for BP1.

Important vocabulary distinction:

| Dimension | Meaning | Existing source |
|---|---|---|
| `route_kind` | Domain/action route (for example social/action route) | Golden replay resolves `trace.turn_trace.social_contract_trace.route_selected`, then `snapshot.debug.resolution_compact.kind`, then `payload.resolution.kind` |
| `final_route` | Final-emission outcome | FEM; primarily `accept_candidate` or `replaced` |
| `fallback_kind` | Countable selected fallback lineage kind | `game.final_emission_replay_projection` |
| `fallback_family_used` | Diegetic/template family | `game.diegetic_fallback_narration` -> FEM |
| `realization_fallback_family` | Governed realization provenance family | `game.realization_authority` / `game.realization_provenance` -> FEM |
| observed `fallback_family` | Replay compatibility projection | Diegetic-first projection in `tests.helpers.golden_replay_projection` |

## Existing Fallback Metadata

### Runtime-visible metadata

| File | Symbols | Shape and role |
|---|---|---|
| `game/final_emission_meta.py` | `ensure_final_emission_meta_dict`, `FEM_RESPONSE_TYPE_KEYS`, `OPENING_FALLBACK_PROJECTION_FIELDS`, `fallback_owner_bucket_registry_surface`, owner-bucket mappers | Canonical FEM sidecar. Carries `final_route`, `final_emitted_source`, opening/visibility/sealed flags, `fallback_family_used`, `fallback_temporal_frame`, `realization_fallback_family`, owner buckets, sanitizer evidence, and provenance trace. Runtime-visible and replay-readable. |
| `game/final_emission_fem_assembly.py` | `build_gate_accept_fem_base`, `build_gate_replace_fem_base`, `merge_gate_layer_metas_into_fem` | Builds terminal FEM with `final_route`, source, validation/repair fields, and fallback-family passthrough. Runtime-visible. |
| `game/final_emission_replay_projection.py` | `_fem_selected_fallback_projection`, `build_fem_runtime_lineage_events`, sealed sub-kind/owner maps | Read-side runtime projection from finalized FEM to normalized events. Runtime-visible diagnostic output; it does not select text. |
| `game/runtime_lineage_telemetry.py` | `make_runtime_lineage_event`, `normalize_runtime_lineage_events`, `summarize_runtime_lineage_events` | Event envelope: `event_type`, `event_kind`, `stage`, `owner`, `source`, `gate_path`, `fallback_kind`, authorship/bucket/split owners, `recurrence_key`, `notes`. Summary already exposes family-like `fallback_frequency` plus authorship and owner frequencies. Runtime diagnostic and report-safe. |
| `game/fallback_provenance_debug.py` | `attach_upstream_fast_fallback_provenance`, `record_final_emission_gate_entry`, `record_final_emission_gate_exit` | Upstream API/retry provenance with source, stage, fingerprint, selector text, and overwrite-containment evidence. Runtime debug/diagnostic. |
| `game/realization_provenance.py` | `REALIZATION_FALLBACK_FAMILY_FIELD`, `attach_realization_fallback_family` | Normalizes and stamps governed family values. Runtime-visible. |
| `game/diegetic_fallback_narration.py` | `_FALLBACK_TEMPLATE_METADATA`, `fallback_template_metadata` | Template ID -> `fallback_family` and `temporal_frame`; dispatchers expose these on FEM as `fallback_family_used`. Runtime/static registry. |
| `game/stage_diff_telemetry.py` | stage snapshots and comparisons | Includes `final_route` from FEM/output and detects route changes. Runtime diagnostic, not fallback incidence authority. |

### Replay/report metadata

| File | Symbols | Shape and role |
|---|---|---|
| `tests/helpers/golden_replay_projection.py` | `project_turn_observation`, `_resolve_route_kind`, `project_replay_fallback_family_from_fem`, `_runtime_lineage_events_from_payload`, `PROTECTED_OBSERVATION_FIELDS` | Per-turn observed row containing `route_kind`, fallback fields, owner buckets, and `runtime_lineage_events`. Runtime lineage is diagnostic; protected flat fields are acceptance/replay authority. |
| `tests/helpers/golden_replay.py` | replay construction/recording helpers | Persists observed turns and collects their runtime-lineage events. Replay-only/test infrastructure. |
| `tools/run_scenario_spine_validation.py` | `_runtime_lineage_events_for_turn`, `build_runtime_lineage_summary`, aggregate writers | Persists `meta.runtime_lineage_events`, derives them from FEM when necessary, and writes `runtime_lineage_summary.json`. Runtime validation tool/reporting. |
| `tests/helpers/runtime_lineage_reporting.py` | `build_runtime_lineage_summary`, transcript collectors | Thin test/report adapter over the canonical runtime summarizer. Test-only. |
| `tests/helpers/failure_classifier.py` | `classify_replay_failure`, `_opening_fallback_owner_bucket` | Consumes replay fallback/route evidence for failure classification. Replay/test-only; it measures failures, not successful fallback incidence. |
| `tests/failure_classification_contract.py` | allowed categories, tags, owner buckets, evidence fields | Public taxonomy lock for dashboard rows. Test-only contract, sourced from runtime registries where available. |

### Static/audit-only metadata

- `game/realization_authority.py::FALLBACK_FAMILIES` is the canonical governed realization-family registry, but the module is declarative and does not drive selection.
- `docs/cycles/BK_fallback_inventory.md`, `BK_fallback_selection_audit.md`, `BK_fallback_ownership_map.md`, and `BK_fallback_projection_audit.md` describe fallback surface, selectors, ownership, and projection boundaries. They are audit-only.
- `docs/testing/protected_replay_manifest.md` and `tests/replay_governance_registry.py` govern replay coverage/fields; they are not incidence stores.
- `data/session.json` and `data/session_log.jsonl` contain examples of persisted runtime metadata, but are mutable samples, not canonical definitions.

## Runtime Trigger Points

The table lists semantic trigger/selection/application points. Thin dataclass factories and tuple adapters are omitted because they do not decide whether fallback occurs.

| Path / symbol | Trigger or fallback condition | Context available | Route available? | Family/owner available? | Instrumentation assessment |
|---|---|---|---|---|---|
| `game/api.py::_fast_fallback_for_upstream_error` | Upstream/provider/budget failure takes the API fast path | Request/action type, upstream error, output metadata, retry-produced fallback | Domain route is available in surrounding API (`req.action_type` / chosen route); final emission route may not yet exist | Governed family and provenance are stamped; split owners are known (`game.api` selection, `game.gm_retry` content) | Technically possible, but early and overlap-prone. Prefer finalized FEM projection. |
| `game/gm_retry.py::select_deterministic_retry_fallback_line` and `apply_deterministic_retry_fallback` | Retry candidate is absent/invalid or deterministic retry fallback is required | GM output, session, world, resolution, prompt, strict-social/opening state | `resolution.kind` and social state are available; final route is not final | `RETRY_TERMINAL_FALLBACK` can be stamped; local fallback kind/source are available | Safe only as passive debug, but risks double counting later terminal selection. |
| `game/gm_retry.py::select_terminal_retry_fallback_line` and terminal repair paths | Retries are exhausted or player-facing output remains unusable/empty | Full retry context, resolution, continuity, prior output | Resolution/domain route available; pre-gate `final_route` values such as `social_fallback_minimal`, `nonsocial_fallback_minimal`, `forced_retry_fallback` may exist | Governed retry family available; owner is retry | Prefer provenance/FEM read side to avoid counting candidates that are later replaced. |
| `game/social_exchange_emission.py::apply_strict_social_terminal_dialogue_fallback_if_needed` | Retry-terminal output must be dialogue, strict-social emission applies, active interlocutor matches, and candidate dialogue is inadequate | Session, resolution, speaker/interlocutor, candidate text | Social route is explicit in resolution/context | Strict-social governed family and social content owner are known | Safe passive point, but it is one of several strict-social surfaces; final projection is more complete. |
| `game/output_sanitizer.py::_diegetic_uncertainty_fallback`, empty-output branches, `_prepared_upstream_empty_fallback_text` | Sanitization leaves empty/invalid/non-diegetic text, or strict-social empty output requires emergency fallback | Sanitizer context, source text/mode, resolution, prepared emission, sanitizer trace | `resolution.kind` may be in context; `final_route` is not reliably local | Sanitizer trace records used/source/owner; strict-social owners are known | Existing trace is sufficient. Count projected sanitizer fallback events rather than adding selector counters. |
| `game/final_emission_opening_fallback.py::select_opening_fallback_for_response_type_contract` | Opening response-type contract rejects candidate; uses structurally usable upstream-prepared opening payload or fail-closes | GM output, upstream prepared payload, curated facts, validation/repair evidence | Opening mode/contract context exists; terminal `final_route` is assigned later | Diegetic family/meta and authorship are available; owner bucket is derivable | Good metadata source, but counting here would include selections not necessarily emitted. |
| `game/final_emission_opening_fallback.py::opening_scene_safe_fallback_selection` | Opening-mode visibility path requests a safe fallback | GM output/opening context | Opening route implicit; no stable final outcome yet | Opening composition metadata available | Prefer terminal FEM projection. |
| `game/final_emission_visibility_fallback.py::standard_visibility_safe_fallback` | Visibility coordinator assembles ordered candidates after validation failure/terminal need and chooses first usable candidate | Session, world, scene, resolution, GM output, opening/strict-social/passive-pressure/first-mention/anti-reset state | Domain route is present through resolution/context; final outcome not yet stamped | Selected candidate carries text, source, pool, kind, family metadata, and bucket | Richest selector point, but instrumenting it could count an intermediate choice. Use final application metadata. |
| `game/final_emission_visibility_fallback.py::apply_visibility_enforcement` | Visibility validation fails and route dispatcher chooses hard replacement rather than no-op/local result | Full gate output, session/world/resolution, validation observation, selected fallback | Domain route context is present; application stamps terminal replacement | Source/pool/kind/bucket and replacement flags are stamped | Safe passive point, but existing stamps already enable read-side measurement. |
| `game/final_emission_sealed_fallback.py::select_non_strict_replace_path_terminal_sealed_fallback_selection` / `...branch` | Non-strict terminal replacement needs a sealed fallback; chooses among opening/visibility/providers | Session/world/resolution/GM output and provider selections | Resolution route available; application stamps `final_route = replaced` | Sealed bucket and realization family are stamped; selected source available | Do not add counter; finalized FEM is authoritative for emitted result. |
| `game/final_emission_sealed_fallback.py::select_acceptance_quality_n4_sealed_fallback_line` | N4 acceptance-quality path requires sealed replacement | Gate/quality context and fallback providers | Route context is indirect; final replacement is stamped by consumer | Source and sealed family/bucket available | Read-side projection is safer than local counter. |
| `game/final_emission_terminal_pipeline.py::apply_visibility_enforcement` callers and strict-social emergency path | Gate terminal pipeline applies chosen visibility/social fallback and patches FEM | Full gate context and finalized output | Both resolution context and final emission outcome become available here | Most source/family/owner metadata is available | Safe passive boundary, but adding live event emission is unnecessary for BP1. |
| `game/final_emission_generic_exit.py` | Non-strict candidate cannot be accepted and sealed terminal selection is applied | Final gate context, validation/classification, composition meta | Final route is assigned as replaced | `fallback_family_used`, source, sealed metadata available | Existing FEM assembly is the correct observational boundary. |
| `game/final_emission_replay_projection.py::_fem_selected_fallback_projection` | Classifies **proven finalized evidence** for sanitizer, opening/fail-closed, prepared repair, strict-social, visibility, upstream-fast, or sealed replacement | Complete normalized FEM | `final_route` and `final_emitted_source` are directly available; domain `route_kind` is not in FEM | Returns fallback kind/stage/selection owner/source; adds authorship, bucket, split owners | **Safest classification point.** Read-side only, no behavior influence. |
| `tests/helpers/golden_replay_projection.py::project_turn_observation` | Projects replay payload and joins FEM lineage with per-turn route | Payload, snapshot, resolution, traces, normalized FEM, replay identity | Yes: resolves `route_kind`; FEM contains `final_route` | Yes: flat fallback fields, buckets, observed family, lineage events | **Best BP incidence input boundary.** Join by turn; do not mutate lineage events. |
| `tests/helpers/failure_classifier.py::classify_replay_failure` | Classifies mismatches/failures using fallback evidence | Observed turn plus expected mismatch data | `route_kind` is available | Family/buckets/lineage evidence available | Not suitable as primary incidence source because successful fallback turns need no failure row. |

### Proven fallback kinds currently projected

`_fem_selected_fallback_projection()` recognizes:

- `sanitizer_strict_social`
- `sanitizer_empty_output`
- `opening_failed_closed`
- `scene_opening`
- `response_type_prepared_emission`
- `minimal_social_emergency_fallback`
- `strict_social_fallback`
- `visibility_or_scene_replacement`
- `upstream_fast_fallback`
- sealed replacement sub-kinds from `project_sealed_replacement_subkind_from_fem()`

This is the current countable fallback-selection vocabulary. It is more reliable for incidence than grepping source-level fallback calls because it records the result that survived to finalized FEM.

Visibility coordination also calls these internal content/sub-selection points: `strict_social_visibility_minimal_fallback_candidate`, `passive_scene_pressure_visibility_fallback_candidates`, `_grounded_scene_intro_fallback_candidates`, `_scene_emit_integrity_global_fallback_selection`, `local_exchange_continuation_fallback_line`, and `npc_pursuit_neutral_nonprogress_fallback_line`. They choose candidate content based on strict-social, passive-pressure, first-mention, scene-integrity, anti-reset, or NPC-pursuit context. They have resolution/session context and often family metadata, but they are not safe incidence counters because `standard_visibility_safe_fallback()` may reject, reorder, or supersede their candidates before terminal application.

## Route Correlation Availability

### Route fields and assignment

| Field | Type/values | Assignment / resolution |
|---|---|---|
| `route_selected` | String action/domain route | Passed into `game.api_turn_support.build_turn_trace`; API supplies `req.action_type` or `route_choice`. Persisted at `trace.turn_trace.social_contract_trace.route_selected`. |
| `resolution.kind` | String resolution/domain kind | Produced by runtime resolution/adjudication flow; available to most selectors through `resolution`. |
| `route_kind` | Replay-projected string | `golden_replay_projection._resolve_route_kind`: `route_selected` first, then `snapshot.debug.resolution_compact.kind`, then `payload.resolution.kind`. |
| `final_route` | String emission outcome | FEM assembly defaults to `accept_candidate` or `replaced`; sealed/visibility application stamps `replaced`. Some retry outputs also carry pre-gate route labels such as `social_fallback_minimal`, `nonsocial_fallback_minimal`, and `forced_retry_fallback`. |
| `final_emitted_source` | String source route/family | FEM records the source of accepted/replaced text; used heavily by fallback projection. |
| `gate_path` | Normalized lineage route | Derived per lineage event (`opening_fallback`, `sanitizer_fallback`, `strict_social_fallback`, `replaced_or_sealed`, etc.). It is a fallback/gate path, not the domain route. |

### Correlation conclusion

- At live selector points, domain route is often available through resolution/context, but not in one consistent field.
- At finalized FEM projection, emission route is directly available but domain route is absent.
- At golden replay/scenario turn rows, both can be joined: `route_kind` comes from turn projection and `final_route` can be read from the same turn's FEM/raw payload.
- Therefore BP should **capture route by turn-level join**, not infer it from `fallback_kind` and not add `route_kind` to the runtime-lineage schema in BP1.
- Treat missing domain routes as an explicit `unknown`/missing bucket and report coverage. Do not silently substitute `gate_path` for `route_kind`.

Files needed to understand route correlation: `game/api.py`, `game/api_turn_support.py`, `game/final_emission_fem_assembly.py`, `game/final_emission_sealed_fallback.py`, `game/final_emission_replay_projection.py`, and `tests/helpers/golden_replay_projection.py`.

## Owner Bucket / Family Source of Truth

### Owner buckets

Canonical definitions exist in `game/final_emission_meta.py`:

- `OPENING_FALLBACK_OWNER_BUCKETS` and `opening_fallback_owner_bucket_from_fields/from_meta`
- `SEALED_FALLBACK_OWNER_BUCKETS` and `sealed_fallback_owner_bucket_from_fields`
- `VISIBILITY_FALLBACK_OWNER_BUCKETS` and `visibility_fallback_owner_bucket_from_fields`
- `fallback_owner_bucket_registry_surface()` exposes all three registries diagnostically.

Tests lock these conventions in `tests/test_opening_fallback_owner_bucket.py`, `tests/test_final_emission_meta.py`, `tests/test_final_emission_sealed_fallback.py`, `tests/test_final_emission_visibility_fallback.py`, `tests/test_golden_replay_fallback_projection.py`, and `tests/test_failure_classification_contract.py`.

Gap: there is no single universal owner-bucket field. FEM/replay has opening, sealed, and visibility buckets, while runtime-lineage has generic `fallback_owner_bucket` plus explicit `fallback_selection_owner` and `fallback_content_owner`. BP must define deterministic precedence or expose all dimensions separately. Recommended: report split owners universally, report `fallback_owner_bucket` when the lineage projector supplies one, and preserve the three flat replay buckets as diagnostic evidence rather than collapsing them silently.

### Families

There are intentionally two canonical taxonomies:

1. **Diegetic family:** `game/diegetic_fallback_narration.py::_FALLBACK_TEMPLATE_METADATA`, projected as `fallback_family_used` (`scene_opening`, `observe`, `action`, `social`).
2. **Governed realization family:** `game/realization_authority.py::FALLBACK_FAMILIES`, with constants and stamping in `game/realization_provenance.py` (for example `upstream_prepared_emission`, `strict_social_deterministic_fallback`, `gpt_budget_or_provider_failure`, `retry_terminal_fallback`, `gate_terminal_repair`).

Golden replay deliberately projects one compatibility field with `project_replay_fallback_family_from_fem()`, preferring `fallback_family_used` and falling back to `realization_fallback_family`. Tests in `tests/test_golden_replay_fallback_projection.py`, `tests/test_final_emission_meta.py`, `tests/test_realization_provenance.py`, and `tests/test_emergency_fallback_registry_static_drift.py` lock this split.

Gap: BP's phrase "fallback family" is ambiguous unless the report schema names the taxonomy. Recommended JSON fields:

- `fallback_kind` (lineage incidence identity)
- `diegetic_family`
- `realization_family`
- `observed_family` (existing diegetic-first replay compatibility value)

Do not merge or rename the runtime fields.

## Existing Reporting Patterns

### Recommended report home

Use a small report-only builder/CLI under `tools/`, writing paired artifacts under `artifacts/golden_replay/` or the scenario-spine aggregate directory:

- `fallback_incidence_report.json` as the machine-readable authority;
- `fallback_incidence_report.md` as the operator view.

The strongest existing integration point is scenario-spine aggregation because `tools/run_scenario_spine_validation.py` already persists per-turn runtime lineage and writes `runtime_lineage_summary.json`. A standalone builder should also accept existing transcript/observed-turn JSON so BP reports can be regenerated without rerunning gameplay.

### Existing conventions

- CLI tools use `argparse`, `Path`, explicit `--out` / `--json-out` style paths, create parent directories, write UTF-8, and print `Wrote <path>` summaries.
- JSON is deterministic and readable (`indent=2`, often `sort_keys=True`, trailing newline).
- Markdown renderers are pure functions where practical; writer functions return written paths.
- Advisory/report-only outputs live in `artifacts/golden_replay/` or timestamped scenario-spine directories and do not affect pass/fail scoring.
- `tools/compare_scenario_spine_reruns.py` is the closest standalone paired Markdown/JSON CLI pattern.
- `tests/helpers/failure_dashboard_report.py` is the closest rich report builder pattern, but it is test-owned and should not become a production runtime dependency.

### Test patterns

- Fabricated turn/transcript fixtures; no live model/provider calls.
- `tmp_path` outputs, then exact `json.loads()` shape assertions.
- Deterministic Markdown substring/table assertions.
- Missing/malformed optional metadata tests.
- CLI invocation tests checking both files and stdout/exit code.
- Delegation/parity tests ensuring report aggregation uses `summarize_runtime_lineage_events()` rather than duplicating frequency logic.

Reports currently use all four requested forms: Markdown operator reports, JSON scorecards/summaries, pytest assertions, and paired JSON+Markdown writers.

## Proposed BP Instrumentation Strategy

### Recommended: replay-derived passive incidence report

Build incidence from finalized, already-persisted turn observations. For each eligible turn:

1. Resolve `route_kind` with the existing golden replay precedence.
2. Read `final_route` and both family fields from FEM.
3. Prefer persisted normalized `runtime_lineage_events`; derive with `build_fem_runtime_lineage_events()` only when the existing projection contract permits it.
4. Select `event_kind == fallback_selected` events.
5. Join each event to turn identity, domain route, emission route, and family fields without changing the event.
6. Aggregate counts by fallback kind, family taxonomy, owner bucket, selection owner, content owner, route, emission route, and useful cross-products.
7. Compute rates with explicit denominators.

Minimum rate schema:

```text
eligible_turn_count
fallback_turn_count                 # turns with >=1 fallback_selected event
fallback_event_count                # events; separately reported to expose multi-event turns
fallback_trigger_rate               # fallback_turn_count / eligible_turn_count
route_turn_count[route]
route_fallback_turn_count[route]
route_fallback_trigger_rate[route]  # route fallback turns / route eligible turns
unknown_route_turn_count
metadata_coverage                   # FEM, route, family, owner availability
```

Use turn rate as the headline incidence metric. Event frequency is secondary because a turn may contain multiple lineage events and future projection growth must not inflate "percent of turns falling back."

### Tradeoffs

| Strategy | Benefits | Costs / risks | Recommendation |
|---|---|---|---|
| Replay-derived report | Zero live semantic risk; reproducible; route and denominator coexist; works on historical artifacts | Measures replay/scenario corpus, not all production traffic; projection completeness bounds accuracy | **BP1 choice** |
| Passive live event collection | Can measure actual deployment traffic | Persistence, privacy, concurrency, sampling, and double-count risks; selectors overlap | Defer until replay report proves schema |
| Add diagnostic counters at selectors | Simple locally | Counts attempts/candidates, not necessarily emitted fallbacks; hard denominator; resets/process scope | Do not use as primary design |
| Runtime metadata projection | Could put route directly on events | Changes diagnostic schema and protected/replay surfaces; unnecessary for joinable turn data | Defer; consider only after coverage evidence |
| Test-only instrumentation | Very low risk | Can drift from runtime and cannot measure non-test executions | Use for verification, not source of truth |
| JSONL event stream | Append-friendly and scalable | Needs stable event identity, session/turn IDs, lifecycle/rotation policy | Later production telemetry option |
| Paired JSON/Markdown | Machine-readable plus operator-friendly; matches repo conventions | Two render surfaces to test | **Use for BP1** |

### Safe implementation boundary

The BP1 core aggregator should be pure and read-side. It must not import selector modules, call the gate, mutate FEM, alter protected replay comparisons, or classify fallback absence as failure. It may reuse runtime telemetry/projection helpers and test/replay observation helpers only within the existing ownership boundaries; a production `game/` module must not import `tests/`.

## Files Likely Needed for Implementation

### BP1 core

- `game/runtime_lineage_telemetry.py` - canonical event normalization/frequency aggregation.
- `game/final_emission_replay_projection.py` - finalized FEM -> proven fallback event projection.
- `game/final_emission_meta.py` - FEM readers and owner-bucket registries.
- `tests/helpers/golden_replay_projection.py` - current per-turn route/family projection contract.
- `tools/run_scenario_spine_validation.py` - transcript format, turn persistence, aggregate artifact hook.
- `tools/compare_scenario_spine_reruns.py` - standalone paired JSON/Markdown CLI convention.
- `tests/test_runtime_lineage_telemetry.py` - canonical aggregation tests.
- `tests/test_run_scenario_spine_validation.py` - fabricated transcript/aggregate report patterns.
- `tests/test_golden_replay_fallback_projection.py` - family, owner, and lineage projection locks.

### Later blocks / reference

- `game/diegetic_fallback_narration.py`
- `game/realization_authority.py`
- `game/realization_provenance.py`
- `tests/failure_classification_contract.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/test_failure_dashboard_report.py`
- `docs/testing/protected_replay_manifest.md`
- `tools/refresh_protected_replay_manifest.py`

## Risks / Non-Goals

- **No behavior changes:** BP must not change fallback selection order, eligibility, prose, repair, sanitizer, or gate logic.
- **No fallback removal:** incidence instrumentation observes existing behavior only.
- **Do not count surface area:** source matches and selector calls are not incidence.
- **Avoid attempt/emission confusion:** count finalized `fallback_selected` evidence, not candidate construction.
- **Avoid denominator ambiguity:** report eligible turns, fallback turns, and fallback events separately.
- **Avoid route ambiguity:** keep `route_kind`, `final_route`, and `gate_path` separate.
- **Avoid family collapse:** preserve diegetic and governed realization taxonomies.
- **Avoid owner collapse:** preserve event owner, owner bucket, selection owner, and content owner.
- **Projection false negatives:** current incidence is only as complete as `_fem_selected_fallback_projection`; report metadata/event coverage and unknowns.
- **Historical comparability:** projection rule changes can change derived incidence without runtime changes. Include schema/version and input artifact identity in JSON.
- **Corpus bias:** protected/golden replay rates characterize the replay corpus, not production player traffic.
- **No scoring coupling:** report generation must remain advisory and must not affect replay pass/fail or evaluator scores.

## Recommended BP Subcycles

### BP1 - Turn-scoped incidence model and report

- Add a pure aggregator over fabricated/loaded turn observations.
- Count eligible turns, fallback turns, fallback events, kinds, owners, both family taxonomies, `route_kind`, and `final_route`.
- Emit deterministic JSON and Markdown.
- Integrate with existing scenario-spine artifacts or provide a standalone transcript CLI.
- Add malformed/missing metadata and multi-event-turn tests.

### BP2 - Projection coverage audit

- Compare fallback-shaped finalized FEM against projected `fallback_selected` events.
- Report unclassified/unknown selection evidence; do not broaden projection rules automatically.
- Decide whether missing sealed/visibility buckets should be added to generic lineage attribution.

### BP3 - Route and owner cross-tabs

- Add route x fallback kind, route x owner, route x family, and final-route x kind tables.
- Add minimum-sample annotations; do not rank tiny buckets as meaningful regressions.

### BP4 - Longitudinal comparison

- Compare incidence reports across replay runs/corpus revisions.
- Separate runtime incidence delta from corpus mix and projection-schema changes.

### BP5 - Production telemetry decision

- Only after BP1-BP4 stabilize the schema, evaluate JSONL or passive production collection with session/turn IDs, privacy constraints, sampling, and lifecycle policy.

## Validation

No tests were run. This was discovery-only, and the only repository change is this Markdown artifact. Validation consisted of repository searches and direct inspection of runtime, replay, reporting, registry, and test files.

## Files to pass back to ChatGPT

Smallest useful set for generating BP implementation blocks:

1. `docs/audits/BP_runtime_fallback_incidence_discovery.md` (this artifact)
2. `game/runtime_lineage_telemetry.py`
3. `game/final_emission_replay_projection.py`
4. `game/final_emission_meta.py`
5. `tests/helpers/golden_replay_projection.py`
6. `tools/run_scenario_spine_validation.py`
7. `tools/compare_scenario_spine_reruns.py`
8. `tests/test_runtime_lineage_telemetry.py`
9. `tests/test_run_scenario_spine_validation.py`
10. `tests/test_golden_replay_fallback_projection.py`

Add these only if BP1 is asked to formalize family/owner registries or share failure-dashboard rendering:

- `game/diegetic_fallback_narration.py`
- `game/realization_authority.py`
- `game/realization_provenance.py`
- `tests/failure_classification_contract.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/test_failure_dashboard_report.py`
- `docs/testing/protected_replay_manifest.md`
- `tools/refresh_protected_replay_manifest.py`

Runtime selector reference set (needed only if implementation changes projection coverage after BP1):

- `game/api.py`
- `game/gm_retry.py`
- `game/output_sanitizer.py`
- `game/social_exchange_emission.py`
- `game/final_emission_opening_fallback.py`
- `game/final_emission_visibility_fallback.py`
- `game/final_emission_sealed_fallback.py`
- `game/final_emission_terminal_pipeline.py`
- `game/final_emission_generic_exit.py`

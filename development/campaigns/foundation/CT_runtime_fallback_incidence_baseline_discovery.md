# CT Runtime Fallback Incidence Baseline Discovery

## Executive summary

The repo already has a report-only fallback incidence lane, but it mostly measures finalized fallback evidence after runtime has already made its decisions. The current primary event is `runtime_lineage` / `fallback_selected`, produced by `game.final_emission_replay_projection.build_fem_runtime_lineage_events()` from finalized FEM fields and counted by `tools/fallback_incidence_report.py`.

Current measurement can classify by fallback kind/family, event owner, selection owner, content owner, owner bucket, route kind, final route, and emitted source when those fields survive into FEM or runtime lineage. It cannot reliably classify the original trigger condition or compatibility status unless each runtime surface stamps enough diagnostic fields before projection.

The committed BV1B sample reports 1 fallback turn/event over 95 eligible turns, a 1.05% fallback trigger rate. That event is `referential_clarity_hard_replacement` on the `observe` route, with event owner `game.final_emission_gate`, selection owner `game.final_emission_visibility_fallback`, content owner `game.final_emission_sealed_fallback`, owner bucket `sealed-gate`, and realization family `gate_terminal_repair`.

## Runtime fallback surface map

| Surface | Function/class | Trigger condition | Output/mutation | Visibility |
|---|---|---|---|---|
| `game/final_emission_opening_fallback.py` | `select_opening_fallback_for_response_type_contract` | Scene-opening contract path lacks a usable upstream-prepared opening payload or has missing/insufficient curated facts; may recover usable stub payload. | Returns selected text plus opening fallback metadata, fail-closed diagnostics, `opening_fallback_*` fields; success path preserves upstream authorship, fail-closed keeps authorship absent. | User-visible when selected; diagnostic FEM fields. |
| `game/opening_deterministic_fallback.py` | `deterministic_opening_fallback_text_and_meta`, `opening_context_from_gm_output` | Opening fallback composer receives usable curated facts; missing facts raises/fails closed via caller. | Composes deterministic opening text and meta; may emit `[opening_fallback_failed_closed: empty_curated_facts]` marker on fail-closed path. | User-visible text when selected. |
| `game/final_emission_visibility_fallback.py` | `apply_visibility_enforcement`, `apply_first_mention_enforcement`, `apply_referential_clarity_enforcement` | Visibility/first-mention/referential clarity validation fails and routing chooses `sealed_hard_replace` rather than non-replacement exemption. | Replaces `player_facing_text`, stamps `final_route="replaced"`, `final_emitted_source`, visibility fallback metadata and owner bucket. | User-visible replacement plus diagnostic FEM. |
| `game/final_emission_visibility_fallback.py` | `_standard_visibility_safe_fallback_core`, `select_non_strict_terminal_fallback_for_sealed` | Terminal fallback selection branch: opening, strict social, passive scene pressure, NPC pursuit neutral, anti-reset continuation, or global scene fallback. | Returns `VisibilitySelectedFallback` with text, pool, kind, source, strategy, composition meta. | User-visible when caller applies. |
| `game/final_emission_sealed_fallback.py` | `select_non_strict_replace_path_terminal_sealed_fallback_selection`, `select_acceptance_quality_n4_sealed_fallback_line` | Sealed terminal replacement is required; branch selected from opening/social/passive/npc/anti-reset/global context. | Returns `SealedFallbackSelection`; route helpers stamp `final_route="replaced"`, `final_emitted_source`, `sealed_fallback_owner_bucket`, realization family. | User-visible replacement plus diagnostic FEM. |
| `game/social_exchange_fallback_catalog.py` | `apply_strict_social_terminal_dialogue_fallback_if_needed`, `select_strict_social_emergency_fallback_line`, `apply_social_exchange_retry_fallback_gm` | Strict-social terminal text is absent/invalid/route-illegal; retry fallback needs social/open-social recovery. | Emits deterministic social fallback line, retry tags/debug notes, or strict-social emergency line. | User-visible text; diagnostic tags/debug. |
| `game/gm_retry.py` | `select_deterministic_retry_fallback_line`, `apply_deterministic_retry_fallback`, `force_terminal_retry_fallback` | Retry failure class is `unresolved_question` or `answer`, retry exhausted, or forced terminal retry fallback is requested. | Mutates/returns GM output with `realization_fallback_family=retry_terminal_fallback`, `opening_fallback_owner_bucket=retry`, tags/debug notes, final routes such as `forced_retry_fallback` or `social_fallback_minimal`. | User-visible retry fallback plus diagnostic metadata. |
| `game/api.py` | `_fast_fallback_for_upstream_error` and `_synthetic_manual_play_gpt_budget_gm` references | Upstream GPT/provider/budget failure or manual synthetic budget path. | Produces upstream fast fallback GM output; later provenance packaging stamps fallback trace. | User-visible emergency/fast fallback. |
| `game/fallback_provenance_debug.py` | `attach_upstream_fast_fallback_provenance`, `apply_upstream_fallback_pregate_containment`, `finalize_upstream_fallback_overwrite_containment` | Fast fallback was selected upstream; downstream text may overwrite selector snapshot. | Stamps `metadata["fallback_provenance"]`, FEM `fallback_provenance_trace`, logs/prints `FALLBACK SELECTED`, containment markers. | Diagnostic and logging; provenance is internal/operator-visible. |
| `game/final_emission_fast_fallback_composition.py` | `apply_fast_fallback_neutral_composition_layer` | Output tags include `upstream_api_fast_fallback`, `forced_retry_fallback`, or `retry_escape_hatch` and neutral composition is needed. | May repair/neutralize fallback composition and stamps fast fallback composition meta. | User-visible text repair; diagnostic meta. |
| `game/fallback_behavior.py` | `build_fallback_behavior_contract` and helpers | Question/answer uncertainty, procedural insufficiency, missing basis, unknown identity/location/motive/method/quantity/feasibility signals. | Builds policy contract fields such as `uncertainty_sources`, partial/question allowances, and expected behavior. | Internal/gate diagnostic; can influence fallback/retry behavior indirectly. |
| `game/final_emission_replay_projection.py` | `_fem_selected_fallback_projection`, `build_fem_runtime_lineage_events` | Finalized FEM shows sanitizer fallback, opening fallback/fail-closed, prepared emission repair, strict-social fallback, visibility/first-mention/referential replacement, upstream provenance trace, or `final_route="replaced"`. | Emits read-side `runtime_lineage` events: `fallback_selected`, `gate_outcome`, `mutation`, split-owner fields, recurrence keys. | Diagnostic/replay/report only. |

Static-only or mostly static references include docs/audits, ownership guards, migration scripts, `tools/*generate_audit_docs.py`, architecture audit heuristics, and many tests that assert constants/import boundaries without exercising live selection. These are useful vocabulary evidence, not runtime trigger evidence.

## Existing instrumentation inventory

| File | Event/counter | Captured fields | Coverage of CT dimensions | Path |
|---|---|---|---|---|
| `game/runtime_lineage_telemetry.py` | `runtime_lineage` event, `fallback_selected` kind | `event_kind`, `stage`, `owner`, `source`, `gate_path`, `fallback_kind`, `fallback_authorship_source`, `fallback_owner_bucket`, `fallback_selection_owner`, `fallback_content_owner`, `repair_kind`, `recurrence_key`, `notes` | Strong owner/source/route-ish support; no explicit compatibility status; family only as `fallback_kind`. | Normal runtime read-side/diagnostic consumers; replay/tests. |
| `game/final_emission_replay_projection.py` | `build_fem_runtime_lineage_events` | Projects `fallback_selected`, `gate_outcome`, `mutation`, `speaker_repair` from FEM. | Strong split-owner projection; families from FEM/projection; source via `final_emitted_source`/trace; no trigger-time condition or compatibility status. | Read-side runtime lineage, protected replay, tests. |
| `tools/fallback_incidence_report.py` | `fallback_trigger_rate`, `fallback_turn_count`, `fallback_event_count`, frequencies/cross-tabs | route kind, fallback kind, diegetic family, realization family, observed family, event owner, owner bucket, selection/content owners, authorship, final route, gate path, metadata coverage. | Strong current baseline except compatibility status and trigger source conditions. | Report-only CLI and tests. |
| `tools/bv1b_fallback_incidence_validation.py` | BV1B report/history refresh | Scans canonical FEM, derives runtime lineage, writes `bv1b_fallback_incidence_report.*`, trends/anomalies. | Adds artifact scan scope and historical snapshots; same schema gaps as report. | Tooling/report-only. |
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json` | Committed current incidence artifact | Current count/rate/frequencies/cross-tabs/coverage. | Good baseline seed; no compatibility status. | Stable artifact, report-only. |
| `artifacts/golden_replay/fallback_incidence_history.json` | Historical trend snapshots | Trigger rate, counts, top fallback kinds/owners/routes/families. | Trend support; current history includes old high-rate baseline and current collapsed rate. | Stable artifact, report-only. |
| `game/fallback_provenance_debug.py` | `FALLBACK SELECTED` log/print and `fallback_provenance`/trace | source, stage, selector text fingerprints, owner constants, provenance snapshot, containment flags. | Strong for upstream fast fallback source/owner; not unified with all fallback families. | Normal runtime for upstream fast fallback; tests. |
| `tests/helpers/failure_dashboard_session.py` and `tests/helpers/failure_dashboard_report.py` | Recorded runtime/protected replay lineage events | Normalized runtime lineage events and protected replay event extension. | Good for failure dashboards; not primary runtime incidence baseline. | Tests/protected replay diagnostics. |
| `tests/helpers/golden_replay_projection.py` and fallback projection helper modules | Golden observed `runtime_lineage_events` | Observed route/fallback family/source/owner bucket/lineage fields. | Good replay observability; acceptance schema is test-owned and read-side. | Protected replay/tests. |
| `game/final_emission_meta.py` | Producer stamp helpers | Opening/retry/visibility/sealed owner buckets, realization family, sanitizer producer attribution. | Strong owner/source/family stamping source of truth, but no unified event emission. | Normal runtime metadata packaging. |

## Proposed fallback family taxonomy

Canonical governed realization families live in `game/realization_authority.py` and are re-exported via `game/realization_provenance.py`/`game/final_emission_ownership_schema.py`:

| Family | Description | Known trigger sites | Source field | Owner field | Route field | Compatibility/status | Gaps |
|---|---|---|---|---|---|---|---|
| `plan_backed_gpt_realization` | Normal plan-backed realization, safe baseline. | GPT realization/prompt pipeline, not fallback selected in current lineage. | `realization_fallback_family` | authority profile `gpt_realization` | normal route kind/final route | `SAFE` | Not a fallback trigger family; should likely remain denominator context. |
| `upstream_prepared_emission` | Upstream prepared text selected after response type/opening repair. | Opening fallback, response type prepared emission. | `opening_fallback_authorship_source`, `final_emitted_source` | selection/content split fields | `final_route`, `route_kind` | `BOUNDED` | Trigger condition needs explicit “payload used vs missing/unusable” status. |
| `strict_social_deterministic_fallback` | Registered deterministic social fallback. | Social exchange fallback catalog; sealed strict-social replacement. | `final_emitted_source`, sanitizer/social source fields | strict social selection/content owners | strict social route/final route | `BOUNDED` | Some surfaces use source ids rather than family directly. |
| `planner_convergence_seam_failure` | Sealed failure when planner did not produce realizable obligations. | API/emergency surfaces. | `realization_fallback_family` | `api_emergency_realization` | route may be unknown | `SUSPICIOUS` | Need trigger-time event, currently mostly family metadata. |
| `gpt_budget_or_provider_failure` | Provider/budget fallback or upstream fast fallback. | `game/api.py`, `game/fallback_provenance_debug.py`, `game/final_emission_fast_fallback_composition.py`. | `fallback_provenance_trace.source`, `realization_fallback_family` | `game.api`, content `game.gm_retry`, packager `game.fallback_provenance_debug` | `forced_retry_fallback`, fallback provenance path | `BOUNDED` | Existing provenance is family-specific, not common trigger event schema. |
| `retry_terminal_fallback` | Retry exhausted; registered terminal retry fallback. | `game/gm_retry.py`, social exchange retry fallback. | `realization_fallback_family`, debug notes/tags | `gm_retry`, opening owner bucket `retry` | `forced_retry_fallback`/`social_fallback_minimal` | `BOUNDED` | Need unified trigger event and reason classification. |
| `gate_terminal_repair` | Final-emission gate sealed terminal replacement. | Sealed/visibility/first-mention/referential enforcement. | `final_emitted_source`, `fallback_kind` | gate event owner, visibility/sealed split owners | `final_route="replaced"`, gate path | `BOUNDED` | Trigger is inferred from FEM; exact failed validator route is partial. |
| `legacy_diegetic_fallback` | Legacy bounded fallback rendering. | Diegetic fallback narration, old opening/read-side evidence. | `fallback_family_used`, realization family | diegetic owner profile | varies | `LEGACY` | Needs explicit live status vs read-only legacy evidence. |
| `legacy_unclassified` | Unknown/ambiguous fallback family. | Provenance normalization for unknown family, replay/test injected data. | `realization_fallback_family` default | `api_emergency_realization` profile | unknown | `UNKNOWN` | Should be measurable as compatibility/unknown pressure. |

Projection-only fallback kinds add operational subfamilies: `scene_opening`, `opening_failed_closed`, `response_type_prepared_emission`, `strict_social_fallback`, `minimal_social_emergency_fallback`, `sanitizer_strict_social`, `sanitizer_empty_output`, `upstream_fast_fallback`, `visibility_hard_replacement`, `first_mention_hard_replacement`, `referential_clarity_hard_replacement`, and sealed replacement subkinds such as `sealed_opening_fallback`, `sealed_social_interlocutor_fallback`, `sealed_passive_scene_pressure_fallback`, `sealed_npc_pursuit_neutral_fallback`, `sealed_anti_reset_continuation_fallback`, `sealed_global_scene_fallback`, `sealed_unknown_replacement`.

## Route/owner/source/compatibility vocabulary findings

Canonical owner vocabulary:

- `game/final_emission_ownership_schema.py` is the main string-token source for fallback selection owners, content owners, owner buckets, sanitizer trace owner mapping, and governed realization families.
- `game/runtime_lineage_telemetry.py` defines event owner semantics: `owner` means event selection/application owner; content/prose ownership should use split fields.
- `game/final_emission_owner_bucket_views.py` owns conservative bucket mapping from FEM fields.

Owner bucket vocabularies:

- Opening: `upstream-prepared`, `sealed-gate`, `retry`, `strict-social`, `unknown-ambiguous`.
- Sealed: `sealed-gate`, `strict-social-sealed`, `unknown-none`, `unknown-ambiguous`.
- Visibility: `sealed-gate`, `strict-social-visibility`, `opening-visibility`, `unknown-none`, `unknown-ambiguous`.

Route vocabularies are split:

- Runtime turn route: `route_kind`, `resolution.kind`, and `trace.social_contract_trace.route_selected` values such as `observe`, `scene_opening`, `social_probe`, `dialogue`, `social`, `action`, `undecided`.
- Final-emission route: `final_route` values such as `accept_candidate`, `replaced`, `forced_retry_fallback`, `social_fallback_minimal`, `nonsocial_fallback_minimal`.
- Runtime lineage gate path: `opening_fallback`, `opening_failed_closed`, `strict_social_emergency`, `strict_social_fallback`, `prepared_repair`, `visibility_hard_replaced`, `first_mention_hard_replaced`, `referential_clarity_hard_replaced`, `replaced_or_sealed`, `accept_candidate`, `accept_repaired`, `accept_unchanged`, `strict_social_accept`.

Source vocabularies are also split:

- `final_emitted_source` is the dominant FEM source id for replacement/repair content.
- `source` in `runtime_lineage` is event source evidence, often `final_emitted_source`, a trace source, or a repair flag.
- `fallback_authorship_source` is opening-specific authorship provenance.
- `fallback_provenance_trace.source == "fallback"` is upstream fast fallback proof.

Compatibility status vocabulary:

- There is no single `compatibility_status` field.
- Governed family status exists as `FallbackFamily.classification` in `game/realization_authority.py`: `SAFE`, `BOUNDED`, `SUSPICIOUS`, `LEGACY`, `UNKNOWN`.
- Read-only compatibility-local opening authorship sources live in `OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES`; mappers intentionally classify them as `unknown-ambiguous`.
- Split-owner matrix has “legacy only” row tracking in `tests/helpers/failure_classification_split_owner.py`.
- `legacy_unclassified` and `legacy_diegetic_fallback` are explicit realization family values.

For CT, “compatibility status” should be derived initially as:

- `governed_classification`: from `realization_fallback_family -> FallbackFamily.classification`.
- `compatibility_status`: `active_governed`, `legacy_runtime`, `legacy_read_only`, `unknown_unclassified`, or `not_recorded`.

## Candidate tests/replay assets

Tests that exercise or assert runtime/projection fallback evidence:

| Test file | Test names/scope | Family exercised | Runtime trigger evidence asserted | Baseline candidate |
|---|---|---|---|---|
| `tests/test_fallback_incidence_report.py` | Whole file | Reported fallback_selected events | Yes: rates, owner/source/route/family frequencies, coverage. | Strong. |
| `tests/test_runtime_lineage_telemetry.py` | `test_make_runtime_lineage_event_*`, `test_summarize_runtime_lineage_events_*`, matrix summary tests | Opening, sanitizer, upstream fast, sealed split-owner families | Yes: event schema/frequencies. | Strong. |
| `tests/test_golden_replay_fallback_acceptance_matrix.py` | Matrix observed lineage/projection tests | Split-owner fallback matrix | Yes: embedded lineage and FEM projection. | Strong. |
| `tests/test_golden_replay_fallback_opening_projection.py` | Opening projection and legacy compatibility tests | Opening/upstream prepared/legacy read-only | Yes: runtime lineage and compatibility-local mapping. | Strong. |
| `tests/test_golden_replay_fallback_sanitizer_projection.py` | Sanitizer fallback projection | Sanitizer strict social/empty output | Yes. | Strong. |
| `tests/test_golden_replay_fallback_sealed_projection.py` | Sealed replacement projection | Sealed subkinds | Yes. | Strong. |
| `tests/test_golden_replay_fallback_visibility_projection.py` | Visibility fallback projection | Visibility hard replacement | Yes. | Strong. |
| `tests/test_golden_replay_fallback_upstream_fast_projection.py` | Upstream fast fallback projection | GPT/provider failure/upstream fast | Yes. | Strong. |
| `tests/test_final_emission_opening_fallback.py` | Opening selection, fail-closed, canonical gate path tests | Opening/upstream prepared/legacy compatibility | Partial: FEM/meta/source/owner bucket. | Good but heavier. |
| `tests/test_final_emission_visibility_fallback.py` | Visibility route/selection/enforcement helpers | Gate terminal repair/visibility | Partial: route metadata/owner bucket. | Good. |
| `tests/test_final_emission_sealed_fallback.py` | Sealed selection/stamping helpers | Sealed/gate terminal/strict social | Partial: FEM route/source/family/owner bucket. | Good. |
| `tests/test_gm_retry.py` | Retry deterministic/forced fallback tests | Retry terminal fallback | Yes for family/route/tags/meta; not unified incidence. | Good. |
| `tests/test_projection_drift_watch.py` | Missing projected fallback_selected alert | Upstream fast/finalized FEM projection gap | Yes: projection gap alerts. | Good guard. |
| `tests/test_cf1_fallback_family_precedence.py` | Family precedence matrix | Diegetic vs realization vs bridge/source fallback family | Yes: family resolution. | Good. |

Replay/golden assets:

| Artifact | Captures | Fallback observable | Baseline stability |
|---|---|---|---|
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json`/`.md` | Current CT-relevant incidence snapshot over 95 canonical FEM instances. | Yes: fallback_selected counts/frequency/cross-tabs. | Stable committed baseline, but generated by a scan/projector. |
| `artifacts/golden_replay/bv1b_fallback_incidence_report.baseline.json` | Historical baseline before collapse. | Yes. | Useful comparison, not current live pressure. |
| `artifacts/golden_replay/bv1_fallback_incidence_report.json`/`.md` | Earlier BP/BV1 incidence measurement over 107 turns. | Yes. | Historical only; high rate differs from current scope. |
| `artifacts/golden_replay/fallback_incidence_history.json` and trends/anomalies | Longitudinal snapshots/anomaly checks. | Yes. | Stable advisory history. |
| `artifacts/golden_replay/projection_gap_reality_report.json` and projection drift watch report | Projection gap/reality checks. | Yes, projection failure observability. | Stable report-only. |
| `data/validation/scenario_spines/frontier_gate_long_session.json` | Long-session scenario source. | Indirect, via generated runtime lineage/report tools. | Stable source for replay baseline expansion. |
| Protected replay failure/report artifacts | Failure rows, drift, runtime lineage. | Yes on failures/diagnostics. | Good for diagnostics, not complete passing-run incidence unless extended. |

## Measurement gaps

- Trigger-time evidence is not unified. Most incidence comes from post-hoc FEM projection, so “trigger condition” is inferred from final fields.
- Compatibility status is not an event field. It must be derived from realization family classification and legacy/read-only registries.
- `source` has multiple meanings: final emitted source, event evidence source, authorship source, trace source.
- `route` has multiple meanings: turn route, final route, gate path.
- Some user-visible fallback families stamp rich FEM metadata; others rely on tags/debug notes or family-specific provenance.
- The current incidence report does not include `compatibility_status`, `governed_classification`, or explicit `trigger_site`.

## Recommended next implementation block

Smallest safe baseline design:

1. Keep runtime behavior unchanged and extend read-side measurement first.
2. Add a tiny diagnostic classifier in tooling or a read-side helper, not in selection paths:
   - input: normalized `fallback_selected` event plus FEM/turn context
   - output fields: `family`, `source`, `owner`, `route`, `compatibility_status`, `governed_classification`, `trigger_site`, `trigger_condition_inferred`
3. Extend `tools/fallback_incidence_report.py` schema to add frequency/cross-tab fields for:
   - `compatibility_status`
   - `governed_classification`
   - `trigger_site`
   - `trigger_condition`
4. Derive `governed_classification` from `realization_fallback_family` using `game.realization_authority.FALLBACK_FAMILIES`.
5. Derive compatibility status conservatively:
   - `legacy_read_only` when opening authorship is in `OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES`
   - `legacy_runtime` for `legacy_diegetic_fallback`
   - `unknown_unclassified` for `legacy_unclassified` or unknown owner/source buckets
   - `active_governed` for known `SAFE`/`BOUNDED`/`SUSPICIOUS` non-legacy families
   - `not_recorded` when no family/status evidence exists
6. Do not alter `make_runtime_lineage_event` yet unless the read-side schema proves insufficient.
7. Add focused tests in `tests/test_fallback_incidence_report.py` for compatibility/status classification and schema coverage.
8. Optionally add a narrow projection test that feeds one legacy compatibility-local opening FEM and one current governed FEM into the incidence report.
9. Report Fallback Trigger Rate in `artifacts/golden_replay/bv1b_fallback_incidence_report.json` or a CT-specific derivative, preserving the existing report as the artifact of record.

## Files likely to be modified in the next block

- `tools/fallback_incidence_report.py`
- `tests/test_fallback_incidence_report.py`
- Possibly `tools/bv1b_fallback_incidence_validation.py` if the artifact refresh should carry the new fields.
- Possibly `artifacts/golden_replay/bv1b_fallback_incidence_report.json` and `.md` if refreshing committed evidence is part of the implementation block.
- Avoid runtime selection modules unless a missing field cannot be derived read-side.

## Risks / ambiguities

- “Fallback Trigger Rate” currently counts observed finalized fallback-selected events, not the exact moment a fallback branch triggered.
- Adding trigger-time instrumentation inside live selection paths risks behavior-adjacent churn; read-side derivation is safer for the next block.
- Compatibility status can be over-inferred if legacy/read-only test fixtures are mixed with live runtime evidence.
- Route vocabulary mismatch can confuse dashboards unless reports name `route_kind`, `final_route`, and `gate_path` separately.
- Owner vocabulary is already split by event owner, selection owner, content owner, packager, and owner bucket; collapsing them would lose important authorship evidence.

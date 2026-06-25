# CF — Replay Projection Responsibility Audit Discovery

## Executive Summary

Replay projection responsibility is **centralized at the acceptance-assembly boundary but fragmented across its input owners**.

The canonical protected replay observation is assembled by `tests/helpers/golden_replay_projection.py::project_turn_observation`, with the 41-field acceptance schema in `golden_replay_projection_fields.py`. A June 25, 2026 split moved registry, manifest, extraction, fallback, and speaker concerns into focused modules without changing output. That improved file-level ownership, but the assembler still reconciles independently owned runtime metadata, fallback provenance, speaker evidence, lineage events, transcript snapshots, and compatibility defaults.

The highest Replay Projection Risk comes from four places:

1. **Extraction/precedence concentration.** `golden_replay_projection_extractors.py` is 978 lines with 44 definitions, while `project_turn_observation` remains the single multi-layer assembler.
2. **Runtime/acceptance dual projection.** `game/final_emission_replay_projection.py` owns runtime lineage projection; the test-only acceptance projection consumes it while applying different protected-field semantics. Governance tests require the two authorities to remain separate.
3. **Fallback and speaker compatibility policy.** Fallback family has a diegetic-first two-field precedence plus a lineage-derived bridge fallback. Speaker selection has a three-stage fallback chain before parity is calculated against final-emission evidence.
4. **Broad contract tests.** `tests/test_golden_replay_projection.py` protects registry, manifest, metadata, fallback, sanitizer, speaker, and compatibility behavior in one file. Failures often identify a field but not the responsible producer layer.

Recent concentration has moved rather than disappeared. In the available 90-day history, `docs/testing/protected_replay_manifest.md` has 17 touches, the acceptance facade has 16, runtime projection has 11, and the broad projection contract test has 7. The newly split modules and fallback-family test files each have one touch because they were created in the June 25 split, so their low history count is not yet stability evidence.

Owner candidates exist for every requested layer. The next work should make precedence/default policies independently testable and improve failure locality before considering further structural refactoring.

## Projection Surface Inventory

| File | Key Symbols | Role | Layer Bucket | Notes |
|---|---|---|---|---|
| `tests/helpers/golden_replay_projection.py` | `project_turn_observation` plus public re-exports | Owns acceptance observation assembly; consumed by replay runners, fixtures, semantic mutation measurement, and dashboard probes | projection helpers; replay assembly / output formatting | 301-line facade with one assembler. It joins all projection layers and is CI acceptance authority. |
| `tests/helpers/golden_replay_projection_fields.py` | `ProtectedObservationField`, `PROTECTED_OBSERVATION_FIELDS`, `protected_observation_field_paths`, `protected_observation_default_row`, `observed_projection_schema_defaults`, `protected_observation_drift_bucket` | Owns protected schema, defaults, drift buckets, text normalization/hash, and scaffold detection | projection helpers; metadata projection | Canonical 41-field registry: 39 structural and 2 semantic fields. Defaults can mask producer absence in synthetic rows. |
| `tests/helpers/golden_replay_projection_extractors.py` | `_PROTECTED_EXTRACTION_SPECS`, `_extract_fem_flat_observed_fields`, `_build_projection_status`, `_project_flat_protected_observed_fields`, `protected_observation_extraction_source_by_path`, `project_semantic_mutation_summary` | Owns source registry, FEM/sanitizer extraction, presence classification, missing-source routing, and unavailable paths | projection helpers; metadata projection; source projection | Largest acceptance implementation module: 978 LOC, 44 definitions. It is the main policy concentration point. |
| `tests/helpers/golden_replay_projection_fallbacks.py` | `REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS`, `project_replay_fallback_family_from_fem`, `_project_replay_fallback_family`, `_resolve_fallback_family` | Owns acceptance-side fallback-family precedence and lineage bridge fallback | fallback projection; source projection | Prefers `fallback_family_used`, then `realization_fallback_family`; can synthesize `neutral_reply_speaker_grounding_bridge` from final route/source plus lineage. |
| `tests/helpers/golden_replay_projection_speaker.py` | `_resolve_selected_speaker_id`, `read_final_speaker_observation_for_replay`, `project_speaker_projection_parity` | Owns acceptance-side speaker selection fallback and final-emission parity projection | speaker projection; source projection | Selection order: social-contract trace, transcript target, then `resolution.social.npc_id`. Final observation order: emission-debug lane, `gm_output`, payload. |
| `tests/helpers/golden_replay_projection_manifest.py` | `render_protected_observation_manifest_section`, `extract_protected_observation_manifest_section`, `protected_observation_manifest_registry_parity_errors` | Renders and validates the protected-field section in the governance manifest | replay assembly / output formatting; tests / fixtures / golden outputs | Mechanical consumer of the protected-field registry. |
| `game/final_emission_replay_projection.py` | `build_fem_runtime_lineage_events`, `project_source_family_from_fallback_kind`, `project_mutation_classification_from_fallback_kind`, `project_sealed_replacement_subkind_from_fem`, `normalize_fem_for_replay_acceptance`, `read_fem_from_turn_for_replay`, `read_emission_debug_lane_for_replay` | Owns runtime read-side FEM lineage/source/owner projection; supplies acceptance projection and tools | metadata projection; fallback projection; source projection | 879 LOC, 25 definitions, and 18 files mentioning `build_fem_runtime_lineage_events`. Explicitly separate from acceptance authority. |
| `game/final_emission_meta.py` | `infer_accept_path_final_emitted_source`, `OPENING_FALLBACK_PROJECTION_FIELDS`, `opening_fallback_projection_fields`, `apply_opening_fallback_projection_fields`, `normalize_final_emission_meta_for_observability` | Owns FEM metadata write/read normalization and opening projection field registry | metadata projection; source projection | 2,106 LOC. Changes here can alter both raw FEM and replay-normalized presence without editing replay helpers. |
| `game/final_emission_speaker_observation.py` | `read_final_speaker_observation` and final speaker observation stamping helpers | Produces canonical final-emission speaker evidence consumed by replay | speaker projection | Runtime producer; replay does not own final speaker resolution. |
| `game/ownership_projection_views.py` | owner constants and normalization delegates | Supplies selection/content-owner vocabulary to runtime lineage projection | fallback projection; source projection | Changes can alter projected owner strings and lineage without touching acceptance projection. |
| `game/final_emission_owner_bucket_views.py` / `game/attribution_read_views.py` | `opening_fallback_owner_bucket_from_meta` | Own opening fallback owner-bucket derivation used by runtime and acceptance adapters | metadata projection; fallback projection; source projection | Acceptance extractor calls through `read_opening_fallback_owner_bucket_for_replay`; bucket rules are intentionally not duplicated there. |
| `game/runtime_lineage_telemetry.py` | `make_runtime_lineage_event`, `normalize_runtime_lineage_events` | Defines lineage event shape and normalization | source projection; replay assembly / output formatting | Shared by runtime projection, replay assembly, reports, and transcript output. |
| `game/realization_provenance.py` | `REALIZATION_FALLBACK_FAMILY_FIELD` | Defines governed fallback-family provenance field | fallback projection; source projection | One of two fallback taxonomies collapsed into acceptance `fallback_family`. |
| `tests/helpers/transcript_snapshots.py` and `tests/helpers/transcript_runner.py` | `compact_snapshot_summary`, `latest_target_id`, `latest_target_source` | Supply transcript/snapshot fields and speaker fallback evidence | speaker projection; replay assembly / output formatting | Transcript target ordering can change selected speaker when trace evidence is absent. |
| `tools/run_scenario_spine_validation.py` | `build_transcript_turn_meta`, `_runtime_lineage_events_for_turn` | Assembles transcript metadata envelopes and mirrors FEM/lineage for offline replay evaluation | metadata projection; replay assembly / output formatting | Sorts copied API metadata keys and overlays runner-owned scenario identity. Separate output surface from golden replay observation. |
| `tests/helpers/golden_replay.py` | `assert_golden_turn_observation`, `assert_protected_golden_turn_observation`, `classify_golden_drift`, `run_golden_replay`, render/summary helpers | Consumes projected observations for assertions, drift classification, summaries, and reports | replay assembly / output formatting | 2,067 LOC. Projection failures flow through this broad orchestration/assertion hub. |
| `tests/helpers/golden_replay_api.py` | `observed_turn_from_payload` and narrow replay facade exports | Thin consumer facade | replay assembly / output formatting | Keeps callers away from the broad helper but does not own projection logic. |
| `tests/helpers/golden_replay_fixtures.py` | `observed_turn_from_gate_output`, deterministic payload builders/stubs | Creates replay-shaped payloads and direct-seam observations | tests / fixtures / golden outputs | Fixtures can encode assumptions about metadata nesting and absent fields. |
| `tests/helpers/replay_observed_row_fixtures.py` | `synthetic_observed_replay_row` | Creates schema-defaulted projected rows for diagnostics/tests | tests / fixtures / golden outputs | Depends on `observed_projection_schema_defaults`; neutral defaults may hide absent-source distinctions. |
| `tests/helpers/speaker_contract_risk.py` | `project_final_emission_for_replay`, `observe_final_to_replay_speaker_contract`, `final_replay_parity_record` | Consumes canonical replay projection for P3/P4 speaker-risk comparison | speaker projection; replay assembly / output formatting | Adds a second comparison/reporting layer over speaker projection, not a second selector. |
| `tests/test_golden_replay_projection.py` | 28 projection contract tests | Main acceptance projection contract suite | tests / fixtures / golden outputs | Covers adapter wiring, fallback precedence, manifest, extraction registry, defaults/presence, sanitizer, metadata, and speaker parity. Broadest multi-layer test file. |
| `tests/test_golden_replay_projection_modules.py` | facade identity, backup parity, acyclic import checks | Governance/regression coverage for the June 25 module split | tests / fixtures / golden outputs | Uses `.bak` monolith as a temporary output/registry parity oracle. |
| `tests/test_golden_replay_fallback_*_projection.py` | family-specific projection and classifier bridge tests | Verify opening, sealed, visibility, upstream, sanitizer, upstream-fast, summaries, and acceptance matrix | tests / fixtures / golden outputs | Eight focused files, 44 cases after parametrization. Several still cross runtime FEM, lineage, acceptance projection, and classifier layers. |
| `tests/test_golden_replay_structural_invariants.py` | six `pytest.mark.golden_replay` protected scenarios | Protected end-to-end consumer of projection output | tests / fixtures / golden outputs | Integration layer; expected to fail on any protected projection drift, with limited producer locality. |
| `tests/test_bx_speaker_identity_golden_replay.py` | four protected BX parity scenarios plus risk reports | Protected speaker integration/regression coverage | tests / fixtures / golden outputs | Crosses routing, final speaker observation, replay selection, parity, and risk scoring. |
| `tests/test_ownership_registry.py` | AO5 runtime/acceptance separation, manifest parity, import-boundary guards | Governance/contract owner for projection boundaries | tests / fixtures / golden outputs | Protects architecture more than field behavior; very broad governance file. |
| `docs/testing/protected_replay_manifest.md` | protected scenarios and generated protected-field table | Human/governance golden contract | tests / fixtures / golden outputs | 17 touches in 90 days; must change when protected registry or explanatory fallback policy changes. |
| `data/validation/scenario_spines/frontier_gate_long_session.json` | long-session turns/identity | Authoritative replay fixture | tests / fixtures / golden outputs | Forces transcript, replay identity, and long-session expectation updates when changed. |
| `artifacts/golden_replay/trend_window/**` and `trend_window_2/**` | run snapshots, transcripts, comparisons, drift reports | Generated golden/trend outputs | tests / fixtures / golden outputs | Large update pressure; useful as corpus evidence but poor ownership units. |
| `artifacts/golden_replay/bug_recurrence_event_log.json` and related reports | projected drift/failure events | Generated replay diagnostic outputs | tests / fixtures / golden outputs | Contains repeated projection-attributed `selected_speaker_id` events and fallback-source events; regeneration can create broad churn. |

## Responsibility Map

| Layer | Owner Files | Consumer Files | Tests | Risk Notes |
|---|---|---|---|---|
| projection helpers | `tests/helpers/golden_replay_projection.py`; `golden_replay_projection_fields.py`; `golden_replay_projection_extractors.py` | `golden_replay.py`, fixtures, dashboard/classification helpers, semantic mutation measurement, manifest tool | `test_golden_replay_projection.py`; `test_golden_replay_projection_modules.py`; `test_ownership_registry.py` | Canonical assembly is clear, but extraction registry, defaults, presence routing, and unavailable routing overlap inside the 978-line extractor module. |
| metadata projection | `game/final_emission_meta.py`; runtime adapter in `game/final_emission_replay_projection.py`; acceptance extractors in `golden_replay_projection_extractors.py` | generic/strict-social FEM assembly, scenario-spine transcript builder, replay assembler, diagnostics | `test_final_emission_meta.py`; `test_golden_replay_projection.py`; `test_run_scenario_spine_validation.py`; `test_ownership_registry.py` | Three representations exist: raw FEM, normalized FEM, and protected observed row. A change may be domain-correct in one and appear as projection drift in another. |
| speaker projection | Runtime evidence: `game/final_emission_speaker_observation.py`; acceptance selection/parity: `golden_replay_projection_speaker.py` | replay assembler, `speaker_contract_risk.py`, BX guard parity helpers | speaker section of `test_golden_replay_projection.py`; `test_final_emission_speaker_observation.py`; `test_bx_speaker_identity_*`; `test_speaker_contract_risk.py` | Selection fallback and parity are separate concerns in one 154-line module. Legacy selection is intentionally preserved on ambiguous/unresolved final observations. |
| fallback projection | Runtime lineage: `game/final_emission_replay_projection.py`; acceptance family: `golden_replay_projection_fallbacks.py`; bucket read: owner-bucket views | replay assembler, classifiers, fallback incidence/audit tools, long-session summaries | eight `test_golden_replay_fallback_*_projection.py` files; fallback portion of `test_golden_replay_projection.py`; runtime-lineage tests | Two fallback-family vocabularies plus lineage-derived bridge behavior create intentional semantic overlap. Owner strings also come from shared projection views. |
| source projection | `game/final_emission_replay_projection.py`; `golden_replay_projection_extractors.py`; `golden_replay_projection_speaker.py`; `game/final_emission_meta.py` | classifier/dashboard, transcript metadata, recurrence reports, attribution inventory | `test_golden_replay_projection.py`; fallback family files; `test_replacement_attribution_inventory.py`; `test_runtime_lineage_telemetry.py` | “Source” means several things: emitted source, authorship source, target source, provenance family, selection owner, and content owner. Naming is explicit but failures can be routed to the wrong owner. |
| replay assembly / output formatting | `project_turn_observation`; `tests/helpers/golden_replay.py`; `tools/run_scenario_spine_validation.py::build_transcript_turn_meta` | protected scenarios, trend windows, dashboards, markdown reports | structural invariants, long-session/trend tests, helper contracts, scenario-spine validation tests | Golden observation and transcript metadata are parallel output surfaces with different field names (`final_text`, `gm_text`, `player_facing_text`) and ordering rules. |
| tests / fixtures / golden outputs | Focused projection tests, fixture helpers, protected registry/manifest, scenario-spine fixture | CI, trend tooling, diagnostics, closeout checks | All listed projection/replay suites | Test files are better split after CE4/CE5, but many family tests still validate producer → runtime projection → acceptance projection → classifier in one assertion path. |

### Duplicated or Overlapping Responsibility

- `fallback_family` is intentionally derived from two runtime fields in acceptance projection, while runtime lineage independently derives `fallback_kind`.
- Opening fallback owner bucket is owned by runtime read views but projected by both runtime lineage and acceptance extraction.
- Speaker identity exists as route/trace selection, transcript target fallback, resolution fallback, final speaker observation, and parity result.
- Metadata availability is represented by projected `None`, `unavailable`, `raw_signal_presence`, `normalized_signal_presence`, and `missing_source_by_field`.
- Runtime lineage events can be payload-stamped or rebuilt from FEM; acceptance projection prefers payload events when available.
- Transcript metadata mirrors FEM and lineage separately from golden replay observation assembly.

## Concentration Findings

| Surface | Evidence | Concentration Risk | Why It Matters |
|---|---|---|---|
| Acceptance assembler | `project_turn_observation` is the only assembler and is mentioned in 11 Python files | High semantic concentration, acceptable API concentration | Any new protected field tends to require orchestration, extraction, presence, unavailable, tests, and manifest changes around one function. |
| Extraction registry/module | 978 LOC, 44 definitions; owns extraction, source mapping, presence, unavailable, and flat assembly | High | Multiple policy dimensions fail from one module, making code ownership and test locality less obvious. |
| Runtime lineage builder | `build_fem_runtime_lineage_events` is mentioned in 18 Python files | High fan-in | A runtime projection change affects acceptance replay, transcript tooling, attribution, fallback audits, and lineage tests. |
| Protected field registry | `protected_observation_field_paths` is mentioned in 16 Python files | High authority concentration | One schema change fans into manifest, classifiers, dashboards, synthetic rows, semantic mutation measurement, and governance. |
| Broad projection test | `tests/test_golden_replay_projection.py` has 28 tests across at least six layers | High test concentration | A failure names the projected symptom but may not isolate whether the defect is producer metadata, extraction, fallback precedence, speaker policy, or registry sync. |
| Runtime projection module | 879 LOC, 25 definitions, 11 touches in 90 days | High | Combines source-family mapping, mutation classification, sealed subkind projection, split-owner projection, and lineage assembly. |
| Acceptance facade/history | 16 touches in 90 days; pre-split module was 1,756 LOC | Medium–high | The split reduced current file size, but historical churn shows that acceptance policy changes repeatedly converge on this surface. |
| Manifest synchronization | `docs/testing/protected_replay_manifest.md` has 17 touches, highest among measured projection files | Medium | Protected schema and policy explanation changes create governance/documentation update pressure even when runtime behavior is unchanged. |
| Fallback tests | Eight focused files, but most call canonical observed-turn assembly and classifier bridges | Medium | File decomposition improved navigation; failures still cross multiple layers and can require coordinated expected-value changes. |
| Speaker integration | BX protected tests cross routing, final observation, replay selection, parity, and risk | Medium–high | Valuable end-to-end protection, but low failure locality; historical recurrence artifacts repeatedly attribute `selected_speaker_id` drift to projection. |
| Golden/trend artifacts | Trend windows and recurrence/report families update in groups | Medium churn concentration | Generated outputs can obscure the small set of semantic changes that actually require review. |

The caller counts above are conservative textual file counts and include definition/governance references. They are suitable for relative concentration, not exact runtime call-graph cardinality.

## Drift Sources

| Drift Source | File/Function | Output Affected | Likely Cause | Recommended Follow-up |
|---|---|---|---|---|
| Neutral schema defaults | `golden_replay_projection_fields.py::_neutral_default_for_flat_protected_path`, `observed_projection_schema_defaults` | Synthetic observed rows; classifier/dashboard fixtures | Mostly accidental test coupling: absent fields can become `None`, `False`, or `""` without preserving why they were absent | Add table-driven tests distinguishing defaulted synthetic rows from genuinely projected unavailable fields. |
| Raw vs normalized FEM | `game/final_emission_meta.py::normalize_final_emission_meta_for_observability`; extractor `_build_projection_status` | `normalized_signal_presence`, `missing_source_by_field`, protected fields | Intentional observability normalization with accidental failure-routing complexity | Add a narrow raw/normalized/projection matrix contract per protected FEM field family. |
| Speaker fallback order | `golden_replay_projection_speaker.py::_resolve_selected_speaker_id` | `selected_speaker_id`, `selected_speaker_source`, speaker parity | Intentional compatibility behavior | Extract a table-driven precedence contract that tests trace → transcript target → resolution fallback independently of parity. |
| Final speaker evidence fallback | `read_final_speaker_observation_for_replay` | `final_speaker_observation`, parity status/notes | Intentional attachment compatibility | Add direct tests for lane vs `gm_output` vs payload precedence and conflicting values. |
| Ambiguous/unresolved speaker preservation | `project_speaker_projection_parity` | parity status, notes, legacy selected ID | Intentional domain behavior but easy to misread as mismatch | Document and test whether preserved legacy selection is acceptance-protected or diagnostic-only. |
| Dual fallback-family precedence | `golden_replay_projection_fallbacks.py::project_replay_fallback_family_from_fem` | protected `fallback_family` | Intentional read-side compatibility | Keep a dedicated matrix for absent, null, empty, and conflicting fields; current tests cover core cases but not every malformed shape. |
| Lineage-derived bridge fallback | `_project_replay_fallback_family` / `_resolve_fallback_family` | `fallback_family=neutral_reply_speaker_grounding_bridge` | Intentional domain compatibility inferred from route/source and lineage | Add a narrow unit suite for bridge inference and negative controls, separate from opening fallback integration. |
| Payload lineage preference | extractor `_runtime_lineage_events_from_payload` | runtime lineage events, fallback inference, long-session summaries | Intentional “stamped beats rebuilt” behavior | Lock conflict behavior when payload lineage and FEM-derived lineage disagree. |
| Opening owner bucket read | `read_opening_fallback_owner_bucket_for_replay` → attribution/owner-bucket views | `opening_fallback_owner_bucket`, lineage owner fields | Intentional domain derivation outside acceptance module | Add owner-view direct tests as the first failure layer; keep replay test as one thin parity case. |
| Source/owner vocabulary maps | `game/final_emission_replay_projection.py` maps and `game/ownership_projection_views.py` constants | lineage `source_family`, mutation classification, owner/content-owner strings | Intentional domain behavior with wide fan-out | Split map-contract tests from lineage assembly tests; add unknown-token behavior explicitly. |
| Sorted diagnostic key lists | `project_turn_observation` sorted FEM/debug keys; `_unavailable_paths_for_projection`; transcript metadata sorted copy | debug output, snapshots, golden reports | Accidental formatting/test coupling if exact lists are asserted | Treat ordering as a documented deterministic contract only where human diff stability matters; otherwise compare sets. |
| Transcript metadata overlay | `tools/run_scenario_spine_validation.py::build_transcript_turn_meta` | transcript `meta`, scenario identity, mirrored FEM/lineage | Intentional artifact formatting | Add a contract showing API metadata precedence vs runner-owned scenario identity and FEM fallback. |
| Final text source | `project_turn_observation` reads `snap["gm_text"]`; runtime speaker risk reads `gm_output["player_facing_text"]` | `final_text`, hash, scaffold leakage, P3/P4 parity | Intentional layer-specific naming, high confusion risk | Add a naming/authority contract test and concise documentation near both adapters. |
| Protected field ordering | registry declaration vs sorted path helper vs manifest rows | manifest table, default rows, registry parity | Intentional deterministic formatting | Decide whether declaration order or sorted order is authoritative; current module-split test locks declaration content while helpers expose sorted paths. |
| Fixture nesting assumptions | `golden_replay_fixtures.py`, `replay_observed_row_fixtures.py` | projected metadata, unavailable paths, classifier rows | Accidental test coupling | Audit fixture builders for direct observed-row construction that bypasses canonical projection. |
| Generated artifact refresh | trend windows, recurrence logs, owner drift reports | many JSON/Markdown files | Mostly formatting/diagnostic coupling | Separate semantic acceptance artifacts from advisory regenerated reports in review/check tooling. |
| Backup parity oracle | `test_golden_replay_projection_modules.py` and `golden_replay_projection.py.bak` | split-module output and registry parity | Temporary regression strategy | Replace `.bak` dependence with explicit contract fixtures once the split has stabilized. |

## Test Coverage Shape

| Test File | Test Type | Projection Layer Covered | Failure Locality | Notes |
|---|---|---|---|---|
| `tests/test_golden_replay_projection.py` | Unit + integration + regression + contract | All acceptance layers: schema, extraction, metadata, fallback, sanitizer, speaker, manifest | Low–medium | Broadest suite. Good safety net, weak ownership signal when failures cascade. |
| `tests/test_golden_replay_projection_modules.py` | Governance/contract + regression | Module split, facade exports, registry/manifest identity, import cycles | High | Failures clearly identify packaging/boundary drift; `.bak` oracle is temporary coupling. |
| `tests/test_golden_replay_fallback_opening_projection.py` | Integration + regression | Opening metadata, fallback family, lineage, classifier | Medium | Crosses runtime producer, runtime lineage, acceptance projection, and classifier. |
| `tests/test_golden_replay_fallback_sealed_projection.py` | Integration + regression | Sealed/strict-social owner buckets and split owners | Medium | Family-local file, multi-layer assertions. |
| `tests/test_golden_replay_fallback_visibility_projection.py` | Integration + regression | Visibility/referential fallback metadata and owner projection | Medium | Good family boundary; failure may originate in visibility producer or generic projection maps. |
| `tests/test_golden_replay_fallback_upstream_projection.py` | Integration + regression | Prepared-emission metadata and malformed reject reasons | Medium–high | Negative/absent cases improve locality; still includes drift classifier behavior. |
| `tests/test_golden_replay_fallback_sanitizer_projection.py` | Integration + regression | Sanitizer trace, lineage, fallback/source owners, classifier | Medium | Multiple sanitizer representations are intentionally reconciled. |
| `tests/test_golden_replay_fallback_upstream_fast_projection.py` | Integration + regression | Upstream-fast split owners and classifier | Medium | Small and focused, but not a pure unit suite. |
| `tests/test_golden_replay_fallback_long_session_summary.py` | Integration + regression | Projected lineage consumed by long-session summaries/escalation | Low–medium | Protects downstream aggregation; failures may be projection or summary logic. |
| `tests/test_golden_replay_fallback_acceptance_matrix.py` | Governance/contract + integration | Canonical split-owner matrix, FEM builder, runtime and acceptance projection | Medium | Valuable cross-layer parity; intentionally overreaches to detect contract divergence. |
| `tests/test_final_emission_meta.py` | Narrow unit + contract | Metadata projection/normalization and opening field registry | High | Best first-line owner for FEM metadata drift. |
| `tests/test_final_emission_speaker_observation.py` | Narrow unit + integration | Final speaker observation production/read | High | Best first-line owner for final speaker evidence. |
| `tests/test_runtime_lineage_telemetry.py` | Unit + integration + contract | Runtime lineage event shape and FEM builder projection | Medium–high | Strong owner suite, though acceptance matrix checks cross layers. |
| `tests/test_replacement_attribution_inventory.py` | Integration + governance | Source/owner attribution from replay projection | Medium | Downstream consumer; failures can be projection or attribution inventory. |
| `tests/test_run_scenario_spine_validation.py` | Integration + artifact contract | Transcript metadata and FEM-derived lineage | Medium | Protects parallel transcript projection surface, not protected observation schema. |
| `tests/test_golden_replay_structural_invariants.py` | Protected end-to-end regression | All protected observation layers | Low | Correctly broad acceptance gate; should not be expected to identify the owner alone. |
| `tests/test_bx_speaker_identity_golden_replay.py` | Protected integration + regression | Speaker routing, final evidence, replay parity, risk | Low | High-value end-to-end speaker contract; requires narrow owner tests to diagnose. |
| `tests/test_golden_replay_helper_contracts.py` | Narrow unit + renderer contract | Expectations, assertion helpers, report formatting | High | Clear helper ownership; does not directly protect projection extraction. |
| `tests/test_ownership_registry.py` | Governance/contract | Runtime/acceptance separation, import boundaries, manifest parity | High for architecture, low for field behavior | Prevents ownership collapse but is too broad to serve as behavioral locality. |
| `tests/test_projection_drift_watch.py` | Tool unit + regression | Detects finalized-but-unprojected fallback shapes | High | Advisory audit coverage; useful independent signal for projection gaps. |

No committed exact-prose golden snapshot is the primary acceptance mechanism. Golden replay mostly protects structural fields, with exact text opt-in. The practical “golden output” pressure comes from manifest text, representative projected dictionaries, trend-window captures, and generated diagnostic reports.

## Candidate Next Blocks

1. **CF1 — Projection Precedence Contract Matrix**

   - **Objective:** Make speaker, fallback-family, payload-lineage, final-speaker-observation, and route-source precedence explicit and independently testable.
   - **Files likely involved:** `tests/helpers/golden_replay_projection_fallbacks.py`, `golden_replay_projection_speaker.py`, `golden_replay_projection_extractors.py`, new focused test files.
   - **Risk level:** Low.
   - **Expected success condition:** Every multi-source projection has a table-driven positive, conflicting, malformed, and absent-input case whose failure names the precedence owner.

2. **CF2 — Protected Field Source/Default Matrix**

   - **Objective:** Produce one executable mapping from each protected field to raw source keys, normalized source, default, unavailable rule, drift bucket, and first owner test.
   - **Files likely involved:** `golden_replay_projection_fields.py`, `golden_replay_projection_extractors.py`, `test_golden_replay_projection.py`, manifest tooling.
   - **Risk level:** Medium.
   - **Expected success condition:** All 41 fields have exactly one declared source policy and one first-line test owner; no source/default rule exists only in assembler conditionals.

3. **CF3 — Projection Test Failure-Locality Split**

   - **Objective:** Decompose `tests/test_golden_replay_projection.py` into metadata/presence, fallback-family, speaker-parity, registry/manifest, and assembler-smoke owners.
   - **Files likely involved:** `tests/test_golden_replay_projection.py` and new focused test modules.
   - **Risk level:** Low–medium.
   - **Expected success condition:** The broad file becomes a thin assembly smoke/redirect, test count and assertions remain unchanged, and each failure family routes to one layer.

4. **CF4 — Runtime Lineage Projection Responsibility Audit**

   - **Objective:** Separate source-family maps, mutation-classification maps, owner-split policy, sealed-subkind inference, and event assembly within the 879-line runtime projection owner.
   - **Files likely involved:** `game/final_emission_replay_projection.py`, `game/ownership_projection_views.py`, runtime-lineage and attribution tests.
   - **Risk level:** Medium–high.
   - **Expected success condition:** Each policy family has an explicit owner and narrow tests; `build_fem_runtime_lineage_events` remains behaviorally unchanged but loses hidden policy responsibility.

5. **CF5 — Transcript vs Golden Observation Authority Contract**

   - **Objective:** Lock the intended relationship among `player_facing_text`, snapshot `gm_text`, protected `final_text`, transcript metadata, and replay identity overlays.
   - **Files likely involved:** `tests/helpers/transcript_snapshots.py`, `tests/helpers/golden_replay_projection.py`, `tools/run_scenario_spine_validation.py`, related tests/docs.
   - **Risk level:** Medium.
   - **Expected success condition:** A concise contract and test matrix explain which surface owns each output and detect accidental cross-surface substitution.

6. **CF6 — Generated Projection Artifact Churn Boundary**

   - **Objective:** Distinguish acceptance-required updates from advisory trend/recurrence/report regeneration.
   - **Files likely involved:** `artifacts/golden_replay/README.md`, artifact manifest/helper, trend and recurrence tooling/tests.
   - **Risk level:** Low.
   - **Expected success condition:** Reviewers can identify the minimal required projection artifacts for a semantic change, and advisory outputs do not masquerade as acceptance fixtures.

7. **CF7 — Remove Backup Oracle After Stabilization**

   - **Objective:** Replace `golden_replay_projection.py.bak` parity checks with explicit stable contract fixtures or hashes.
   - **Files likely involved:** `tests/test_golden_replay_projection_modules.py`, `.bak` file, a small committed contract fixture if needed.
   - **Risk level:** Low.
   - **Expected success condition:** Module-split regression coverage remains deterministic without retaining a duplicate implementation-sized artifact.

## Files To Pass Back To ChatGPT

Priority order:

1. `docs/audits/CF_replay_projection_responsibility_discovery.md`
2. `tests/helpers/golden_replay_projection.py`
3. `tests/helpers/golden_replay_projection_extractors.py`
4. `tests/helpers/golden_replay_projection_fields.py`
5. `tests/helpers/golden_replay_projection_fallbacks.py`
6. `tests/helpers/golden_replay_projection_speaker.py`
7. `game/final_emission_replay_projection.py`
8. `game/final_emission_meta.py`
9. `tests/test_golden_replay_projection.py`
10. `tests/test_golden_replay_projection_modules.py`
11. `tests/test_golden_replay_fallback_opening_projection.py`
12. `tests/test_golden_replay_fallback_sealed_projection.py`
13. `tests/test_golden_replay_fallback_visibility_projection.py`
14. `tests/test_golden_replay_fallback_upstream_projection.py`
15. `tests/test_golden_replay_fallback_sanitizer_projection.py`
16. `tests/test_golden_replay_fallback_upstream_fast_projection.py`
17. `tests/test_golden_replay_fallback_long_session_summary.py`
18. `tests/test_golden_replay_fallback_acceptance_matrix.py`
19. `tests/test_golden_replay_structural_invariants.py`
20. `tests/test_bx_speaker_identity_golden_replay.py`
21. `tests/helpers/golden_replay.py`
22. `tests/helpers/golden_replay_fixtures.py`
23. `tests/helpers/replay_observed_row_fixtures.py`
24. `tests/helpers/speaker_contract_risk.py`
25. `tools/run_scenario_spine_validation.py`
26. `docs/testing/protected_replay_manifest.md`
27. `data/validation/scenario_spines/frontier_gate_long_session.json`
28. `artifacts/golden_replay/bug_recurrence_event_log.json`
29. `artifacts/golden_replay/trend_window_2/manifest.json`
30. `tests/helpers/golden_replay_projection.py.bak` — unclear/temporary ownership; retain only while the split parity strategy needs it.

## Acceptance Criteria Check

- Every replay projection layer has at least one owner candidate: **met**.
- Projection drift sources are listed: **met**, including defaults, normalization, speaker, fallback, source/provenance, ordering, transcript, fixtures, and generated artifacts.
- Tests are mapped to projection layers: **met**.
- Likely concentration hotspots are identified: **met**, with current LOC, caller-reference, and 90-day touch evidence.
- Next blocks can be generated without guessing: **met**, with seven scoped blocks, likely files, risk, and success conditions.

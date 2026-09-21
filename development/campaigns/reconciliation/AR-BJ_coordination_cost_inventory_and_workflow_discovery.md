# AR-BJ - Coordination Cost Inventory and Implementation Workflow Discovery

## 1. Executive Summary

Campaign 5 begins from a stable Campaigns 1-4 architecture. This inventory found substantial coordination cost, but the primary source is not architectural separation itself. Most high-touch feature work crosses multiple files because the repository deliberately separates canonical runtime ownership, adapters/projections, provenance, replay observation, direct-owner tests, downstream smoke tests, documentation, and governance checks.

The largest implementation-cost concentrations are:

- Final Emission metadata, legality, repair, sanitizer, and replay-projection surfaces.
- Protected replay observation fields, extraction registries, manifest generation, classifier/dashboard overlap, and recurrence evidence.
- Fallback/provenance vocabulary, especially dual runtime/replay fallback-family concepts and opening fallback authorship residue.
- Governance inventory and test ownership maps, especially when changes touch protected replay, split-owner matrix rows, or direct-owner suite placement.
- API/runtime transaction changes, because `game/api.py` owns broad turn-order orchestration and must coordinate domain mutation, CTIR, realization, Final Emission, persistence, logs, and response packaging.

No immediate architectural concern was discovered. Repository evidence supports the Campaign 4 conclusion that the architecture is ready for implementation-focused work. The main reducible costs are implementation friction, compatibility residue, test fixture duplication, and documentation synchronization. Several costs are already minimized by canonical registries and drift checks, for example `game/final_emission_boundary_contract.py`, `game/realization_authority.py`, `game/contract_registry.py`, `tests/helpers/golden_replay_projection_fields.py`, and `tests/helpers/failure_classification_split_owner.py`.

Preliminary conclusion: do not collapse owners or move authority into adapters. The next cycle should classify and quantify the highest-cost coordination paths before prescribing changes. Recommended next cycle: **AR-BK - Coordination Cost Classification and Reduction Opportunity Analysis**.

## 2. Architectural Baseline

The governing baseline is Campaigns 1-4, especially `AR-AD_target_architecture_doctrine.md`, `AR-BG_ruleset_backend_and_version_provenance_boundary_inventory.md`, `AR-BH_minimal_extensibility_contract_definition.md`, and `AR-BI_boundary_reconciliation_campaign_closeout.md`.

Baseline decisions that must not be casually reopened:

- Runtime truth flows from domain mechanics and state authority through CTIR, prompt/adaptation, realization, Final Emission, persistence/logs, replay/evidence, and governance.
- `game.api` owns transaction order. Broad coordination in this module is expected where it preserves a single coherent turn transaction.
- Domain modules own simulation truth; prompts and model output do not.
- CTIR owns bounded resolved-turn meaning; prompt context adapts CTIR and authoritative state for model-facing use.
- Realization/model I/O produces candidate expression and route/provenance metadata; it does not own truth, final legality, replay authority, or persistence policy.
- Final Emission owns last-mile legality, selection/application, sealing, packaging, and traceability. It must not become a general semantic author.
- Validators predicate; repairs are bounded; sanitizers strip, package, or drop. These distinctions are durable.
- Runtime diagnostic projection and protected replay acceptance projection are separate. `game.final_emission_replay_projection` is runtime diagnostic/read-side; `tests.helpers.golden_replay_projection*` is protected replay acceptance/test authority.
- Provenance records source, family, owner, lineage, and evidence paths. It does not select behavior.
- Governance declares, watches, and tests architecture. It must not become hidden runtime behavior.
- Compatibility residue is not co-equal ownership unless promoted by current doctrine.
- Ruleset/backend/version/provenance gaps are local contract and implementation work, not runtime redesign.

Evidence:

- `AR-BI_boundary_reconciliation_campaign_closeout.md` states that Campaign 4 found no need to redesign runtime orchestration, state authority, CTIR, prompt adaptation, realization, Final Emission, persistence, replay, diagnostics, or governance.
- `AR-AD_target_architecture_doctrine.md` states that the architecture is organized around ownership clarity rather than minimizing file count, and that multi-axis ownership is intentional for fallback, opening narration, final emission, provenance, and replay.
- `docs/architecture_ownership_ledger.md` declares the standard seam presentation: runtime owner, practical primary direct-owner suite, secondary downstream suites, and compatibility/support residue.
- `tests/README_TESTS.md` instructs contributors to extend direct-owner tests first and keep smoke, transcript, downstream, and compatibility suites from becoming second homes.

## 3. Repository Areas Examined

Source directories:

- `game/`: runtime transaction, domain logic, CTIR, prompt/realization, Final Emission, provenance, persistence, model routing, validation and repair contracts.
- `tests/`: direct-owner suites, governance suites, protected replay helpers, fixtures, compatibility tests, and artifact checks.
- `docs/`: ownership ledger, governance docs, validation layer docs, protected replay manifest, convergence CI inventory, runbooks, and historical/maintenance records.
- `audits/` and `docs/audits/`: campaign evidence, closeouts, discovery reports, and generated/curated audit records.
- `artifacts/`: generated replay, architecture, recurrence, attribution, and hotspot reports used as evidence and sometimes governance inputs.
- `scripts/` and `tools/`: CI/check entrypoints, audit tools, report generators, migration helpers, and evidence refresh tools.

Major modules and contracts sampled:

- `game/api.py`, `game/gm.py`, `game/model_routing.py`, `game/ctir.py`, `game/ctir_runtime.py`, `game/state_authority.py`, `game/persistence_contract.py`.
- `game/final_emission_gate.py`, `game/final_emission_meta.py`, `game/final_emission_replay_projection.py`, `game/final_emission_boundary_contract.py`, `game/final_emission_repairs.py`, `game/final_emission_validators.py`, `game/output_sanitizer.py`, `game/output_sanitizer_lineage.py`.
- `game/realization_authority.py`, `game/realization_provenance.py`, `game/contract_registry.py`, `game/validation_layer_contracts.py`, `game/response_policy_contracts.py`.
- `tests/helpers/golden_replay_projection.py`, `tests/helpers/golden_replay_projection_fields.py`, `tests/helpers/golden_replay_projection_registry.py`, `tests/helpers/protected_replay_registry.py`, `tests/helpers/failure_classification_split_owner.py`.
- Governance and owner tests including `tests/test_final_emission_boundary_contract.py`, `tests/test_contract_registry_static_drift.py`, `tests/test_model_routing_runtime.py`, `tests/test_realization_provenance.py`, `tests/test_final_emission_gate_orchestration_order.py`, `tests/test_split_owner_acceptance_matrix_contract.py`, `tests/test_refresh_split_owner_acceptance_matrix.py`, `tests/test_ownership_registry.py`, `tests/test_inventory_governance.py`, `tests/test_gate_boundary_governance.py`, and `tests/test_replay_boundary_governance.py`.

Repository history examined:

- `4460543 CK: Fallback Authorship Contraction`
- `f2935c9 CL: Replay Projection Churn Reduction`
- `ec9c7c8 CN: Final-Emission Adjacency Compression`
- `79d1b85 CO: Assertion Family Rationalization`
- `bf97ba8 CR: Protected Replay Recurrence Separation`
- Current untracked Campaign 4 root reports `AR-BA` through `AR-BI` were also treated as user-provided/repo-local evidence but not modified.

## 4. Representative Feature-Change Traces

| Feature or Change | Canonical Owner | Files/Modules Touched | Contracts Affected | Replay/Provenance Impact | Tests | Documentation | Compatibility/Governance | Initial Assessment |
|---|---|---|---|---|---|---|---|---|
| Fallback authorship contraction (`4460543 CK`) | Final Emission metadata/provenance owners: `game/final_emission_meta.py`, `game/final_emission_opening_fallback.py`, owner-bucket views/schema | `game/final_emission_boundary_contract.py`, `game/final_emission_meta.py`, `game/final_emission_opening_fallback.py`, `game/final_emission_owner_bucket_views.py`, `game/final_emission_ownership_schema.py`, classifier/dashboard helpers | Opening fallback authorship source, owner bucket, boundary mutation taxonomy | Affects golden replay opening projection and fallback trend fields; clarifies upstream-prepared vs compatibility-local authorship | `tests/test_final_emission_meta.py`, `tests/test_final_emission_opening_fallback.py`, `tests/test_golden_replay_fallback_opening_projection.py`, `tests/test_opening_fallback_owner_bucket.py`, classifier/dashboard tests | `CK_fallback_authorship_contraction_discovery.md`, `CK_fallback_authorship_contraction_closeout.md` | Compatibility-local authorship is fenced and observed; direct owner plus replay/dashboard consumers must align | Mostly INTENTIONAL_ARCHITECTURAL_COORDINATION with COMPATIBILITY_RESIDUE around compatibility-local tokens; reduction via clearer field registry and fixture helpers |
| Replay projection churn reduction (`f2935c9 CL`) | Protected replay projection helpers, especially `tests/helpers/golden_replay_projection_*` | Projection engine, extractors, presence, registry, semantic modules, FEM normalization, synthetic evidence bridge | Protected observation fields, extraction registry parity, projection presence policy | Directly affects protected replay acceptance rows and classifier evidence overlap | `tests/test_golden_replay_projection_engine.py`, `tests/test_golden_replay_projection_modules.py`, `tests/test_golden_replay_projection_presence_integration.py`, `tests/test_golden_replay_projection_registry.py`, `tests/test_cf2_protected_field_routing.py` | `CL1` through `CL8` reports plus audit docs | Must preserve separation from runtime `game.final_emission_replay_projection`; registry parity checks enforce coverage | ALREADY_MINIMIZED by modular extraction registry, but TEST_MAINTENANCE_FRICTION remains when fields change |
| Final-emission adjacency compression (`ec9c7c8 CN`) | Final Emission metadata, sanitizer, visibility fallback, runtime/protected projection boundaries | `game/final_emission_meta.py`, observability, repairs, visibility fallback/metadata, `game/output_sanitizer.py`, `game/output_sanitizer_lineage.py`, replay projection helpers | Sanitizer lineage, FEM metadata, visibility fallback fields, protected field routing | Adds/changes fields observed by replay projection and trace nesting | Projection registry/presence/trace contract tests | `CN_final_emission_adjacency_compression_discovery.md`, closeout | Multiple adapters must carry fields without making replay authoritative | INTENTIONAL_ARCHITECTURAL_COORDINATION plus IMPLEMENTATION_FRICTION from manual field threading |
| Assertion family rationalization (`79d1b85 CO`) | Failure classification, recurrence, attribution, Final Emission evidence surfaces | Many docs/audit artifacts, `game/final_emission_meta.py`, response type, sealed fallback, validators, visibility metadata, sanitizer/lineage, runtime lineage telemetry, many test helpers | Attribution contracts, recurrence taxonomy, owner bucket/mutation classifications, failure dashboard evidence | Heavy effect on artifacts under `artifacts/golden_replay/*`; recurrence and owner-drift evidence regenerated | Classification, dashboard, recurrence, attribution, ownership governance tests | Numerous `docs/audits/CO*` records and runbooks | Governance and generated artifacts coordinate with executable contracts; cost is high but much of it is evidence preserving | GOVERNANCE_OVERHEAD and DOCUMENTATION_SYNCHRONIZATION, partly intentional; candidate for automation/refresh workflow clarification |
| Protected replay recurrence separation (`bf97ba8 CR`) | Protected replay recurrence event writers and dashboard helpers | Recurrence event logs, history artifacts, dashboard drift/path/recurrence/report helpers, migration/regeneration tools | Protected vs session diagnostic vs synthetic event source separation | Separates protected replay health from diagnostic/synthetic histories; legacy/unified comparison retained | `tests/test_failure_dashboard_paths.py`, `tests/test_failure_dashboard_recurrence.py`, `tests/test_migrate_bug_recurrence_event_log.py`, `tests/test_replay_bug_class_recurrence.py` | `docs/maintenance/CR_protected_replay_recurrence_separation_discovery.md`, CR closeout | Legacy unified rates remain compatibility-only until consumers are inventoried | COMPATIBILITY_RESIDUE and GOVERNANCE_OVERHEAD; retirement requires consumer inventory |
| Minimal ruleset/backend/version provenance contract definition (`AR-BG`, `AR-BH`) | Future ruleset/backend contract owners; current model routing and GM are adjacent | No production code changed in this cycle; evidence in `game/model_routing.py`, `game/gm.py`, `game/persistence_contract.py`, `game/ctir.py`, domain modules | Missing ruleset id/version/capabilities, backend id/version/provider identity, version/provenance bundle | Future replay/provenance identity fields required before alternate rulesets or second provider | `tests/test_model_routing_runtime.py`, model routing config tests; future fake backend/ruleset tests absent | `AR-BG_ruleset_backend_and_version_provenance_boundary_inventory.md`, `AR-BH_minimal_extensibility_contract_definition.md` | Current single-provider/ruleset is acceptable; expansion requires local contracts first | IMPLEMENTATION_FRICTION from absent published contracts; not architecture redesign |
| Adding/changing a final-emission boundary mutation kind | `game/final_emission_boundary_contract.py` | Boundary taxonomy, gate/repairs/generic exit call sites, direct-owner contract tests, gate closeout tests/docs | `PACKAGING_ALLOWED`, `LEGALITY_ALLOWED`, `SEMANTIC_DISALLOWED`, `assert_final_emission_mutation_allowed` | Prevents semantic mutation from silently passing at last mile | `tests/test_final_emission_boundary_contract.py`, `tests/test_gate_convergence_closeout.py`, final-emission boundary/convergence tests | `docs/gate_convergence_closeout.md`, `docs/gate_cleanup_inventory.md` | Requires coordinated doc/test updates when taxonomy meaning changes | INTENTIONAL_ARCHITECTURAL_COORDINATION; current contract already minimizes risk |
| Changing protected observation field | `tests/helpers/golden_replay_projection_fields.py` and extraction registry | Protected field registry, extraction registry, manifest generator, replay projection facade, classifier evidence, docs manifest | `PROTECTED_OBSERVATION_FIELDS`, drift buckets, extraction defaults, classifier evidence exclusions | Directly changes replay acceptance surface | Projection registry tests, manifest parity, protected replay tests, classifier/dashboard tests | `docs/testing/protected_replay_manifest.md`, generated manifest section | Field path change requires multi-file propagation and generated docs | TEST_MAINTENANCE_FRICTION and GOVERNANCE_OVERHEAD, partly already minimized by parity checks |

## 5. Coordination Cost Inventory

| ID | Coordination Cost | Repository Evidence | Current Workflow Impact | Responsible Boundary | Primary Classification | Permanence | Reduction Potential | Risk if Changed | Notes |
|---|---|---|---|---|---|---|---|---|---|
| CC-01 | Feature changes often require runtime owner + direct-owner tests + downstream smoke + replay/governance updates | `docs/architecture_ownership_ledger.md` standard seam rows; `tests/README_TESTS.md` owner/smoke/downstream rules | Developer must discover owner and avoid duplicating semantics in consumers | Architecture/test ownership | INTENTIONAL_ARCHITECTURAL_COORDINATION | permanent | low | high | This is the intended protection against second homes |
| CC-02 | Final Emission gate layer ordering requires many local modules and tests | `game/final_emission_gate.py:apply_final_emission_gate`; `tests/test_final_emission_gate_orchestration_order.py` | New layer/contract changes must preserve order and metadata propagation | Last-mile legality/packaging | INTENTIONAL_ARCHITECTURAL_COORDINATION | permanent | low | high | File count is expected; order is a real invariant |
| CC-03 | Boundary mutation taxonomy must align with source assertions and docs | `game/final_emission_boundary_contract.py`; `tests/test_final_emission_boundary_contract.py`; `docs/gate_convergence_closeout.md` | Adding/removing mutation kinds requires taxonomy, call site, and doc/test alignment | Final Emission boundary | GOVERNANCE_OVERHEAD | permanent | medium | high | Already has fail-closed tests; doc sync remains manual |
| CC-04 | Protected observation fields require field registry, extraction registry, manifest, projection, classifier overlap | `tests/helpers/golden_replay_projection_fields.py`, `_validate_protected_extraction_registry_parity`; `docs/testing/protected_replay_manifest.md`; `tools/refresh_protected_replay_manifest.py` | Small field additions can fan out across test helpers and generated docs | Protected replay acceptance | TEST_MAINTENANCE_FRICTION | permanent | medium | high | Parity checks reduce risk but not editing effort |
| CC-05 | Runtime FEM lineage and protected replay projection share related vocabulary but must remain separate | `game/final_emission_replay_projection.py`; `tests/helpers/golden_replay_projection.py` module docstring | Developers must know which projection owns diagnostics vs acceptance | Runtime diagnostic vs protected replay | INTENTIONAL_ARCHITECTURAL_COORDINATION | permanent | low | high | Merging would weaken replay/runtime separation |
| CC-06 | Dual fallback-family vocabularies must be preserved and projected with precedence | `tests/helpers/golden_replay_projection.py` dual fallback-family contract; `game/realization_provenance.py`; `game/realization_authority.py` | Feature work must choose diegetic `fallback_family_used` vs governed `realization_fallback_family` | Provenance/read-side compatibility | COMPATIBILITY_RESIDUE | transitional | medium | medium | Needs consumer map before simplification |
| CC-07 | Opening fallback compatibility-local residue appears in taxonomy/tests/docs despite no current production assignment | `docs/gate_cleanup_inventory.md`; `docs/audits/discovery/cycle_ap_fallback_authorship_resolution_recon.md`; `game/final_emission_boundary_contract.py` | Maintainers must preserve negative invariants and stale-token mappers | Opening fallback compatibility | COMPATIBILITY_RESIDUE | transitional | medium | medium | Retirement requires proof no consumers depend on stale values |
| CC-08 | Split-owner acceptance matrix edits require code, expected counts, report refresh, dashboard parity, tests | `tests/helpers/failure_classification_split_owner.py`; `scripts/check_split_owner_acceptance_matrix.py`; `docs/audits/BU15_split_owner_acceptance_matrix.md`; `tests/test_split_owner_acceptance_matrix_contract.py` | Matrix-only conceptual change still touches report and constants | Failure classification/dashboard governance | GOVERNANCE_OVERHEAD | permanent | medium | medium | Wrapper scripts help; workflow remains manual |
| CC-09 | Model routing is published, but backend/provider identity is not | `game/model_routing.py:ModelRouteDecision`; `game/gm.py:call_gpt`; `AR-BG` backend boundary assessment | Adding second provider would require scattered edits without backend adapter | Realization/backend boundary | IMPLEMENTATION_FRICTION | transitional | high | high | Need backend contract before provider expansion |
| CC-10 | Ruleset identity/capability contract absent | `AR-BG`, `AR-BH`; current domain modules and `NONCOMBAT_FRAMEWORK_VERSION` | Alternate ruleset work would require inferred contracts and scattered conditionals | Ruleset/domain mechanics | IMPLEMENTATION_FRICTION | transitional | high | high | Implement local ruleset contract before alternate rulesets |
| CC-11 | `game/api.py` has broad transaction pressure | `game/api.py` size and many orchestration functions; AR-BI runtime transaction doctrine | Feature changes touching turn flow often pass through API | Runtime transaction spine | INTENTIONAL_ARCHITECTURAL_COORDINATION | permanent | medium | high | Relief should be helpers/delegates, not splitting transaction authority |
| CC-12 | `game/gm.py` still combines prompt/realization helpers, OpenAI call, fallback metadata, and compatibility re-exports | `game/gm.py:call_gpt`; `docs/response_policy_enforcement_split_plan.md`; ledger response policy enforcement compatibility note | Backend or realization changes require care around legacy imports and shared helper dependencies | Realization/provider/compatibility | COMPATIBILITY_RESIDUE | transitional | medium | medium | Backend adapter and import migration could reduce pressure |
| CC-13 | Final Emission metadata packaging is a high-pressure owner | `game/final_emission_meta.py`; tests `test_final_emission_meta.py`; CK/CN/CO commits | New meta fields touch defaults, merge helpers, read-side projection, tests | FEM metadata packaging | INTENTIONAL_ARCHITECTURAL_COORDINATION | permanent | medium | medium | Field registry surfaces already exist; helpers could be more discoverable |
| CC-14 | Large direct-owner tests become change magnets | `tests/test_prompt_context.py`, `tests/test_replay_bug_class_recurrence.py`, `tests/test_final_emission_meta.py` among largest tests | Developers may copy fixtures or add nearby assertions even when owner boundary differs | Test ownership | TEST_MAINTENANCE_FRICTION | permanent | medium | medium | Builders/shared assertions can help if owner semantics remain clear |
| CC-15 | Governance docs and generated artifacts can blur canonical vs advisory authority | `AR-AD` canonicality index; `docs/convergence_ci_inventory.md`; artifacts under `artifacts/golden_replay/*` | Reviewers must know what is contract, generated evidence, or advisory | Governance/evidence | DOCUMENTATION_SYNCHRONIZATION | permanent | medium | medium | More canonicality labels or generation indexes could help |
| CC-16 | Validation layer separation has prose contract plus executable registry plus audit | `docs/validation_layer_separation.md`; `game/validation_layer_contracts.py`; `tools/validation_layer_audit.py` | Adding validation concern requires docs/registry/audit understanding | Validation governance | GOVERNANCE_OVERHEAD | permanent | low | high | Intentional; audit is heuristic maintainer aid |
| CC-17 | Response policy contracts support older payload shapes | `docs/architecture_ownership_ledger.md` response policy compatibility note; `game/response_policy_contracts.py` | New contract fields must preserve read-only accessors/fallbacks | Response policy contract | COMPATIBILITY_RESIDUE | uncertain | low | medium | Keep as compatibility unless consumer inventory proves retirement safe |
| CC-18 | Test inventory governance requires committed JSON freshness | `tests/README_TESTS.md`; `tools/test_audit.py --check`; `tests/test_inventory_governance.json` | Adding tests may require running audit refresh and owner-map updates | Test governance | GOVERNANCE_OVERHEAD | permanent | medium | low | Automation exists; workflow clarity matters |
| CC-19 | Protected recurrence separation retains legacy/unified comparison vocabulary | `docs/maintenance/CR_protected_replay_recurrence_separation_discovery.md`; recurrence helpers | Developers must avoid treating `legacy_unified`/overall rates as canonical health | Replay recurrence compatibility | COMPATIBILITY_RESIDUE | transitional | medium | medium | Needs consumer inventory before renaming/removal |
| CC-20 | Public prompt projection keys are centralized but docs must stay aligned | `game/contract_registry.py:PUBLIC_NARRATIVE_PLAN_PROMPT_TOP_KEYS`; `docs/planner_convergence.md`; `tests/test_contract_registry_static_drift.py` | Projection key changes require registry, implementation, docs, tests | Prompt/projection contract | DOCUMENTATION_SYNCHRONIZATION | permanent | medium | medium | Registry is good; doc key list is manual |

## 6. Edit Fan-Out Map

| Pattern | Evidence | Necessary Propagation | Duplicated Implementation Knowledge? | Classification |
|---|---|---|---|---|
| Final Emission field addition | `game/final_emission_meta.py`, `game/final_emission_replay_projection.py`, `tests/helpers/golden_replay_projection_extractors.py`, `tests/helpers/golden_replay_projection_fields.py` | Runtime must stamp/package; runtime diagnostics and protected replay must observe without owning behavior | Sometimes yes, where field names and defaults are repeated across extraction/default docs | IMPLEMENTATION_FRICTION plus INTENTIONAL_ARCHITECTURAL_COORDINATION |
| Protected replay field path update | `PROTECTED_OBSERVATION_FIELDS`, extraction registry parity, manifest generator/checks | Acceptance schema, extraction, and docs must align | Low at runtime; moderate in docs/generated tables | TEST_MAINTENANCE_FRICTION |
| Fallback/provenance vocabulary update | `game/realization_authority.py`, `game/realization_provenance.py`, `game/final_emission_meta.py`, replay projection helpers, tests | Runtime stamp, metadata packaging, and read-side projection are distinct | Some vocabulary appears in tests/docs as literals | COMPATIBILITY_RESIDUE |
| Split-owner matrix row change | `tests/helpers/failure_classification_split_owner.py`, generated report, dashboard expectations, contract tests | Matrix, counts, dashboard and report parity must align | Some manual expected counts are duplicated intentionally | GOVERNANCE_OVERHEAD |
| Boundary mutation taxonomy change | `game/final_emission_boundary_contract.py`, call sites, boundary tests, gate closeout docs | Taxonomy and uses must stay fail-closed | Docs repeat taxonomy names | GOVERNANCE_OVERHEAD |
| Backend/model route change | `game/model_routing.py`, `game/gm.py`, config tests, runtime metadata tests | Routing decision and GM metadata packaging both affected | Provider identity absent, so backend concerns are inferred from GM | IMPLEMENTATION_FRICTION |
| Ruleset/version identity change | Future module absent; current versions in `game/ctir.py`, `game/persistence_contract.py`, `game/noncombat_resolution.py` | Existing local versions should remain owned locally | Missing bundle forces developers to infer relationship | IMPLEMENTATION_FRICTION |
| Ownership/governance test addition | `docs/architecture_ownership_ledger.md`, `tests/TEST_AUDIT.md`, governance tests, inventory JSON | Owner maps and tests must agree | Possible doc repetition of owner rows | DOCUMENTATION_SYNCHRONIZATION |
| Compatibility re-export migration | `game/gm.py`, `game/final_emission_text.py`, `game/social_exchange_emission.py`, governance guards | Stable import surfaces protect consumers during extraction | Residue can persist after zero importers | COMPATIBILITY_RESIDUE |
| Recurrence/report artifact updates | `artifacts/golden_replay/*`, recurrence helpers, dashboard reports/docs | Evidence must be regenerated when recurrence meaning changes | Generated docs/artifacts may repeat computed data | GOVERNANCE_OVERHEAD |

## 7. Canonical-Owner Pressure Assessment

| Canonical Owner | Owned Responsibility | Common Change Triggers | Extension Surface | Pressure Source | Architecturally Expected? | Possible Implementation Relief | Risk |
|---|---|---|---|---|---|---|---|
| `game/api.py` | Turn transaction order, state mutation orchestration, CTIR attach, realization, Final Emission, persistence/log response | New API-facing behavior, campaign start, UI projections, opening flow, turn-pipeline semantics | Helper functions and domain delegates; no formal transaction DSL | Coherent transaction spine | Yes | Narrow helper APIs, workflow docs, traceable orchestration sections | High |
| `game/gm.py` | Current GPT realization call, prompt-message support, route metadata, upstream failure normalization, compatibility re-exports | Backend/provider work, prompt/realization changes, error/fallback provenance | `model_routing`, realization provenance helpers, future backend adapter absent | Compatibility and missing backend adapter | Partly | Backend adapter contract; import migration away from compat re-exports | Medium-high |
| `game/final_emission_gate.py` | Last-mile legality/selection/application/orchestration | New validators/repairs, ordering, sealed fallback, strict-social behavior | Layer functions, helper modules, boundary contract | Legitimate gate ordering plus residue | Yes | Better layer registration/checklists, more local contracts | High |
| `game/final_emission_meta.py` | FEM metadata defaults, merge helpers, read-side packaging | New provenance/evidence/debug fields | Field registry surfaces and merge helpers | Canonical metadata packaging | Yes | More declarative field definitions and doc generation | Medium |
| `game/final_emission_boundary_contract.py` | Mutation taxonomy and fail-closed assertion | Any boundary mutation kind | `PACKAGING_ALLOWED`, `LEGALITY_ALLOWED`, `SEMANTIC_DISALLOWED` | Governance protection | Yes | Generated doc table from contract | High |
| `game/final_emission_replay_projection.py` | Runtime diagnostic lineage from finalized FEM | New FEM/provenance field or lineage event | Projection helpers and read-side surface | Runtime diagnostic owner | Yes | Smaller declarative mappings where possible | Medium |
| `tests/helpers/golden_replay_projection_fields.py` | Protected observation field registry and drift buckets | Protected replay field additions/removals | `ProtectedObservationField`, registry accessors, parity check | Protected acceptance schema | Yes | Stronger generation for docs/defaults | High |
| `tests/helpers/golden_replay_projection.py` facade | Protected replay turn observation projection | Runtime payload shape changes, field extraction changes | Extractor/engine modules | Acceptance facade and compatibility imports | Yes, now reduced by CL | Continue module decomposition, builders | High |
| `tests/helpers/failure_classification_split_owner.py` | Split-owner acceptance matrix, report rendering, expected counts | Attribution/owner bucket/mutation classification changes | Matrix rows and scripts | Governance/report parity | Yes | Better generated counts, one refresh command already exists | Medium |
| `game/realization_authority.py` | Declarative realization/fallback authority profiles and families | New fallback family or classification | `AUTHORITY_PROFILES`, `FALLBACK_FAMILIES` | Canonical vocabulary | Yes | Schema validation and generated docs | Medium |
| `game/response_policy_contracts.py` | Shipped response-policy contract shapes and read-only accessors | Response type, answer completeness, fallback/social structure contracts | Resolver/materializer helpers | Contract owner | Yes | Improve publication docs; avoid downstream duplicate checks | Medium |
| `game/state_authority.py` | State domain registry, read matrix, write allow-list, mutation traces | New authoritative state domain or cross-domain write | Declarative specs and guard helpers | Canonical authority registry | Yes | No split needed; usage examples could reduce memory load | High |
| `docs/architecture_ownership_ledger.md` | Governance-facing owner declarations | New/changed seam ownership | Prose ledger | Governance doctrine | Yes | Generated index or consistency checker | Medium |
| `tests/TEST_AUDIT.md` and inventory JSON | Test suite ownership map | New tests, moved test ownership | `tools/test_audit.py` | Test governance | Yes | Better refresh instructions and smaller owner indexes | Low-medium |

## 8. Contract Publication Assessment

| Contract | Current Location | Publication Form | Discoverability | Duplicated/Inferred Elsewhere? | Coordination Effect | Improvement Potential |
|---|---|---|---|---|---|---|
| Architecture ownership ledger | `docs/architecture_ownership_ledger.md` | Prose governance ledger | High for maintainers | Summarized in AR docs and audit readme | Strong positive coordination; manual sync burden | Medium: generated index/cross-link |
| Validation layer phase contract | `docs/validation_layer_separation.md`, `game/validation_layer_contracts.py` | Prose plus executable registry | Medium-high | Audit docs/tests repeat categories | Helps avoid policy drift | Low-medium |
| State authority | `game/state_authority.py` | Dataclasses and functions | High in code, medium in workflow | Ledger/docs summarize | Reduces inferred mutation authority | Low |
| Response policy contracts | `game/response_policy_contracts.py` | Executable resolvers/builders | Medium | Ledger lists owner/downstream; tests infer details | Good contract, but feature workflow requires owner knowledge | Medium |
| Final Emission mutation taxonomy | `game/final_emission_boundary_contract.py` | Executable allowlists and assertion | High | Gate docs repeat taxonomy | Strong fail-closed enforcement; doc sync required | Medium |
| Final Emission metadata fields | `game/final_emission_meta.py` | Helpers/registries/defaults | Medium | Projection/tests/docs repeat field names | Field additions require manual propagation | Medium-high |
| Runtime lineage projection | `game/final_emission_replay_projection.py` | Runtime read-side functions | Medium | Golden replay consumes subset/diagnostics | Prevents runtime/protected merge | Medium |
| Protected observation fields | `tests/helpers/golden_replay_projection_fields.py` | Dataclass registry plus parity | High for replay maintainers | Manifest/docs/generated reports repeat | Strong schema authority; field updates costly | Medium |
| Protected extraction registry | `tests/helpers/golden_replay_projection_registry.py` and extractors | Executable registry | Medium | Field registry parity checks | Reduces missing extraction drift | Low-medium |
| Realization fallback authority | `game/realization_authority.py` | Declarative registry | Medium-high | Tests and docs assert values | Centralizes family profiles | Medium: generated docs |
| Realization fallback family stamp | `game/realization_provenance.py` | Constants and helpers | High | Used across tests and projection docs | Good lightweight API | Low |
| Model routing contract | `game/model_routing.py:ModelRouteDecision` | Dataclass and resolver | High | `game/gm.py` attaches metadata | Good for model lanes | Medium: backend separation needed |
| Backend/provider contract | Missing; described in `AR-BG` and `AR-BH` | Documented but not executable | Low in code | Inferred from `game/gm.py:call_gpt` | Blocks safe second-provider work | High |
| Ruleset contract | Missing; described in `AR-BG` and `AR-BH` | Documented but not executable | Low in code | Inferred from domain modules/versions | Blocks safe alternate-ruleset work | High |
| Persistence envelope | `game/persistence_contract.py`, `docs/runtime_persistence_envelope.md` | Executable version/envelope | Medium-high | Tests assert version | Good local contract | Low |
| Prompt narrative projection keys | `game/contract_registry.py`, `docs/planner_convergence.md` | Executable registry plus docs | Medium | Static tests enforce registry use | Reduces audit/key drift | Medium: doc generation |
| Split-owner matrix | `tests/helpers/failure_classification_split_owner.py` | Executable matrix/report renderer | Medium | Generated report and dashboard tests | Clear but update-heavy | Medium |
| Test ownership registry | `tests/ownership_registry_contract.py`, `tests/TEST_AUDIT.md`, inventory JSON | Dataclasses/prose/generated JSON | Medium | Several governance tests | Strong suite placement enforcement | Medium |

## 9. Compatibility and Transitional Residue Inventory

| Residue | Protected Behavior | Active Callers/Tests | Coordination Cost | Retirement Evidence Required | Expected Lifetime | Preliminary Priority |
|---|---|---|---|---|---|---|
| Opening fallback compatibility-local authorship/taxonomy | Legacy/malformed opening paths; negative detection of stale authorship | `game/final_emission_boundary_contract.py`, `docs/gate_cleanup_inventory.md`, golden opening tests | Keeps retired vocabulary in taxonomy/docs/tests | Prove no production assignment and no external/report consumers require stale token | Transitional | Medium |
| Dual fallback-family projection | Preserves diegetic fallback taxonomy and governed realization provenance | `tests/helpers/golden_replay_projection.py`, `game/realization_provenance.py`, `game/realization_authority.py` | Developers must choose/write/project two related fields | Consumer inventory and replay proof that one projection can change without losing meaning | Transitional/uncertain | Medium |
| `legacy_diegetic_fallback` broad family | Classifies old diegetic fallback renderers | `game/realization_authority.py`, tests in realization/gate/replay | Broad owner profile can obscure concrete prose owner | Narrow stamps by concrete fallback owner with replay evidence | Transitional | Medium |
| `legacy_unclassified` sink | Fail-safe normalization for unknown family values | `game/realization_provenance.py`, tests | Adds legacy bucket to vocabulary | Evidence no unknown family values are accepted/emitted, or keep as non-emitting sink | Indefinite defensive | Low |
| CTIR-absent prompt fallbacks | Older/missing CTIR paths still allow prompt construction | Ledger CTIR/prompt seam; prompt context tests | Prompt developers must know fallback is compatibility, not co-owner | Confidence all normal resolved-turn paths attach CTIR; targeted absence regression | Transitional | Medium |
| Response policy compatibility accessors/top-level fallbacks | Older payload shapes | `game/response_policy_contracts.py`, ledger | Contract readers support older forms | Consumer inventory and migration plan | Uncertain | Low |
| `game.gm` response policy enforcement re-exports | Stable imports after extraction | Ledger, response policy enforcement split plan | GM remains a compatibility surface | Zero importers or approved migration | Transitional | Medium |
| Final-emission text/social exchange compat barrels | Stable import surfaces after decomposition | `tests/ownership_guard_bv_compatibility.py` | Guards and docs must distinguish re-export from owner | Consumer migration and governance update | Transitional | Low-medium |
| Tuple/dataclass fallback round-trip adapters | Historical tuple-shaped gate tests/imports | Sealed/visibility fallback tests; cycle AB/AM docs | Test-only compatibility APIs remain | Production zero-use already partly shown; test rewrite to dataclass-native | Transitional | Low |
| Legacy/unified recurrence rates | Comparison across pre-separation histories | CR maintenance doc, recurrence/dashboard tests | Risk of consuming mixed rates as health metric | Dashboard/doc consumer inventory and renamed replacement fields | Transitional | Medium |
| Generated artifact snapshots | Preserve evidence from prior campaigns | `artifacts/golden_replay/*`, audit docs | Large artifact update sets | Clear authority labels and generation commands | Historical/permanent | Low |

## 10. Vocabulary Duplication Assessment

| Vocabulary/Concept | Locations | Same Meaning? | Translation Boundary? | Duplication Type | Canonical Definition Present? | Action Needed? |
|---|---|---|---|---|---|---|
| Final-emission mutation kinds | `game/final_emission_boundary_contract.py`, gate docs/tests | Yes | No; runtime taxonomy | Documentation/test duplication | Yes | Generate doc table or keep manual with tests |
| Realization fallback family | `game/realization_provenance.py`, `game/realization_authority.py`, tests/docs | Yes for governed family | Runtime provenance | Contract propagation | Yes | Keep; maybe generate docs |
| Diegetic fallback family vs realization fallback family | FEM fields and golden projection precedence | No, related but distinct | Runtime-to-replay read-side projection | Intentional distinct vocabulary | Partly | Keep separate until consumer proof |
| Opening fallback authorship source/bucket | `game/final_emission_meta.py`, opening fallback module, owner bucket views/schema, tests | Mostly same; stale compatibility tokens differ | Read-side compatibility | Compatibility residue | Partial | Consumer inventory before retirement |
| Protected drift buckets | `tests/helpers/golden_replay_projection_fields.py`, replay governance docs | Yes | Protected acceptance | Contract propagation | Yes | Keep; doc generation possible |
| Split-owner matrix ids | `tests/helpers/failure_classification_split_owner.py`, dashboard/report docs | Yes | Governance/reporting | Generated/manual duplication | Yes | Prefer generated counts/report |
| Failure/recurrence source labels | Recurrence helpers, artifacts, docs | Some historical labels differ | Migration/compatibility | Compatibility residue | Partial | Clarify canonical vs legacy fields |
| Model route fields | `game/model_routing.py`, `game/gm.py` metadata | Yes | Route decision to GM metadata | Adapter propagation | Yes | Backend id missing |
| Backend/provider identity | `AR-BG`, `AR-BH`; not executable | N/A | Future backend adapter | Absent contract | No | Implement before provider expansion |
| Ruleset/version/capability identity | `AR-BG`, `AR-BH`; local versions in CTIR/persistence/noncombat | Related but not same | Future ruleset/version bundle | Absent contract | No | Implement before alternate rulesets |
| Test ownership labels | `docs/architecture_ownership_ledger.md`, `tests/TEST_AUDIT.md`, inventory JSON | Intended same | Governance | Documentation synchronization | Partial | Refresh/generate indexes |
| Validation layer ids/kinds | `game/validation_layer_contracts.py`, docs/audit | Same phase meanings | Governance/audit | Contract propagation | Yes | Keep |
| Persistence failure categories | `game/persistence_contract.py`, tests/docs | Same | Persistence boundary | Low duplication | Yes | None |
| Protection status | `tests/helpers/protected_replay_registry.py`, tests | Same | Protected replay registry | Low duplication | Yes | None |

## 11. Adapter-Boundary Assessment

| Adapter | Source Authority | Target Representation | Mapping Style | Feature-Change Cost | Duplicated Decisions? | Boundary Value | Improvement Potential |
|---|---|---|---|---|---|---|---|
| Prompt context / CTIR adapter | CTIR and authoritative state | Model-facing prompt payload | Handwritten packaging with contract helpers | Medium | Some fallback behavior when CTIR absent | Keeps prompts non-authoritative | Medium: clearer absence policy |
| Model routing to GM metadata | `game/model_routing.py` | `game/gm.py` metadata fields | Handwritten attach/merge | Low-medium | No provider id yet | Keeps routing deterministic | Medium: backend adapter |
| GM/OpenAI provider call | GM realization path | OpenAI Responses API | Direct provider invocation | High for second provider | Provider concerns inside GM | Acceptable for single provider | High: provider-neutral backend adapter |
| Final Emission gate to helper modules | Gate orchestration | Validators/repairs/sanitizer/meta | Handwritten ordered calls | Medium-high | Ordering must remain central | Preserves last-mile legality | Low-medium: layer checklist |
| Final Emission metadata to runtime lineage | FEM metadata | Runtime lineage events | Handwritten projection helpers | Medium | Some vocabulary repeated | Keeps diagnostics read-side | Medium: declarative mapping |
| Runtime lineage to golden replay observation | Runtime payload/FEM | Protected observed row | Handwritten extraction + registry | High | Some field defaults repeated | Keeps protected replay test-only | Medium: generation/helpers |
| Protected manifest generator | `PROTECTED_OBSERVATION_FIELDS` | Markdown manifest section | Generated | Low after fields set | No | Reduces doc drift | Low |
| Split-owner matrix renderer | Matrix rows | Audit report and checks | Generated from rows plus expected counts | Medium | Expected count constants repeat totals | Keeps governance parity | Medium |
| UI mode projection | Full state/log | Player/GM UI mode views | Handwritten projection | Medium | Not deeply assessed | Prevents UI from owning runtime truth | Uncertain |
| Persistence envelope | Runtime payload | Versioned document envelope | Executable wrapper/validator | Low | No | Separates storage format from gameplay semantics | Low |
| Failure dashboard/report helpers | Replay/classification evidence | Markdown/JSON dashboard rows | Handwritten/generated mixture | Medium-high | Some labels repeated | Keeps evidence observable | Medium: report generation clarity |

## 12. Governance Cost Assessment

| Governance Mechanism | Failure Prevented | Enforcement Method | Manual Effort | Overlap | Current Value | Possible Efficiency Improvement |
|---|---|---|---|---|---|---|
| Architecture ownership ledger | Owner ambiguity and second homes | Prose governance plus audit references | Medium | Repeated in TEST_AUDIT/AR docs | High | Generated owner index |
| Direct-owner test policy | Duplicated semantic assertions in smoke/consumer tests | `tests/README_TESTS.md`, `tests/TEST_AUDIT.md`, governance tests | Medium | Some repetition with ledger | High | Better contributor checklist |
| Final Emission boundary contract | Silent semantic mutation at last mile | Executable taxonomy + tests | Low-medium | Docs repeat kinds | High | Generate doc table |
| Gate boundary governance | Gate direct-owner suites absorbing replay/dashboard/classifier ownership | Focused governance tests | Low | Distinct from registry tests | High | Keep focused |
| Replay boundary governance | Runtime importing protected acceptance or merging projections | Governance tests/docs | Medium | Related to golden replay tests | High | Clearer dependency diagram |
| Protected replay manifest | Protected corpus/field authority drift | Docs plus generator/check | Medium when fields change | Field registry/docs | High | Refresh command in workflow |
| Test inventory governance | Test suite map drift | `tools/test_audit.py --check`, committed JSON | Medium | TEST_AUDIT | Medium-high | More automation on test add/move |
| Split-owner matrix contract | Matrix/report/dashboard mismatch | Check script, refresh wrapper, pytest contracts | Medium | Report/docs repeat counts | High | Generate expected counts |
| Validation layer audit | Layer ownership drift | Strict audit and smoke tests | Low-medium | Ledger | Medium-high | Better actionable messages |
| Convergence CI inventory | CI/doc mismatch | Workflow plus docs/tests | Medium | README/docs/audit docs | Medium | Single generated CI command source |
| Realization/provenance audits | Realization authority/provenance drift | Advisory tools | Low | Docs/tests | Medium | Promote only stable checks |
| Recurrence migration/governance | Mixed protected/diagnostic recurrence health | Migration tests and docs | Medium | Dashboard artifacts | High | Consumer inventory |

## 13. Test Maintenance Assessment

| Test Area | Maintenance Trigger | Coverage Value | Friction Source | Compatibility-Driven? | Safer Improvement Opportunity |
|---|---|---|---|---|---|
| Final Emission gate orchestration | Layer ordering, new repair/validator, strict-social path | High | Large ordered monkeypatch tests and many fixtures | Partly | Shared layer-order assertions; keep owner suite |
| Final Emission metadata | New meta/provenance fields | High | Repeated FEM-shaped dict fixtures | Partly | Builders for FEM/meta snapshots |
| Protected replay projection | Field/path/extraction changes | Very high | Registry, extractors, defaults, manifest, classifier overlap | Yes | Generated cases from field registry |
| Golden replay full/end-to-end | Runtime payload changes | Very high | Snapshot/protected corpus setup and field expectations | Partly | Field-focused helpers and minimal smoke rows |
| Failure classification/dashboard | Owner bucket/mutation/fallback field changes | High | Matrix rows, dashboard expected text, generated reports | Yes | Generate dashboard expectations from matrix where safe |
| Recurrence tests | Event source separation, migration, history updates | High | Legacy/unified comparison support | Yes | Typed event builders and explicit legacy fixtures |
| Model routing runtime | Route metadata changes | Medium-high | Fake OpenAI recorder setup | No | Future backend fake adapter |
| Boundary contract tests | Mutation taxonomy changes | High | Docs/test named-kind sync | No | Generate closeout invariant from taxonomy/docs |
| Ownership/governance tests | New suite/owner maps | Medium-high | Inventory JSON refresh, allowlists | No | Better local refresh guide |
| Prompt context tests | Prompt contract changes | High | Large direct-owner file and many scenario fixtures | Partly | Contract builders; avoid duplicate downstream matrices |
| Compatibility import governance | Extraction/re-export changes | Medium | Import-surface allowlists and historical names | Yes | Retirement checklist with zero-importer proof |

## 14. Documentation Burden Assessment

| Document/Artifact | Purpose | Authority Level | Update Trigger | Duplicates Executable Truth? | Historical Value | Coordination Cost | Possible Treatment |
|---|---|---|---|---|---|---|---|
| `docs/architecture_ownership_ledger.md` | Canonical owner declarations | High governance authority | New/changed seam owner | Some owner/test rows repeat code/test reality | High | Medium | Keep; add generated index/checks |
| `tests/README_TESTS.md` | Contributor test workflow | High workflow authority | New governance lane or workflow | Some command duplication | Medium | Medium | Keep linked to command sources |
| `tests/TEST_AUDIT.md` | Test ownership map | High test governance | New/moved test ownership | Repeats ledger and inventory | High | Medium-high | Generate parts from registry/inventory |
| `docs/convergence_ci_inventory.md` | CI/governance discovery index | High for CI parity | Workflow/check changes | Commands repeat workflow | Medium | Medium | Keep, but generate command list if possible |
| `docs/testing/protected_replay_manifest.md` | Protected replay policy and field table | High replay governance | Protected field/corpus changes | Field table generated from registry | High | Medium | Continue generator/check workflow |
| `docs/gate_convergence_closeout.md` | Final-emission gate closeout invariants | Governance/history | Boundary taxonomy/semantics change | Repeats taxonomy kind names | High | Medium | Preserve; maybe generated taxonomy appendix |
| `docs/gate_cleanup_inventory.md` | Detailed gate cleanup/residue map | Advisory/current inventory | Gate repair/residue changes | Some overlaps with boundary contract | High | Medium | Keep as inventory; label current vs historical |
| AR Campaign reports | Decision trail and cycle deliverables | High historical/governance | New campaign cycles | Summarize current code and docs | Very high | Low-medium | Preserve; do not treat as duplication |
| `docs/audits/BU15_split_owner_acceptance_matrix.md` | Generated matrix report | Generated governance artifact | Matrix row changes | Yes, generated from matrix | Medium | Medium | Keep generated/check-only |
| `artifacts/golden_replay/*` | Generated replay/recurrence evidence | Generated evidence/advisory unless promoted | Replay/recurrence run | Yes, generated | High | High during evidence cycles | Keep authority labels and generation commands |
| `AR-BG`/`AR-BH` | Extensibility contract discovery/definition | Architecture guidance | Ruleset/backend implementation planning | Documents missing executable contracts | High | Low | Use as next-cycle evidence, not runtime source |
| `docs/planner_convergence.md` | Planner/prompt projection workflow | Workflow/governance | Projection key changes | Repeats contract registry key list | Medium | Medium | Generate key table or check docs |
| `docs/maintenance/CR_protected_replay_recurrence_separation_discovery.md` | Recurrence compatibility inventory | Maintenance/history | Recurrence source changes | Repeats helper/report semantics | High | Medium | Keep until legacy consumer inventory complete |

## 15. Current Feature Implementation Workflow

Observed nontrivial feature workflow:

1. Discover the canonical owner.
   - Required architectural step.
   - Use `docs/architecture_ownership_ledger.md`, `tests/TEST_AUDIT.md`, module docstrings, and recent AR reports.
   - Weak point: some owners are easy to find, but workflow still depends on expert memory for whether a neighboring module is owner, adapter, projection, downstream smoke, or compatibility residue.

2. Identify affected contracts.
   - Required architectural step.
   - Check executable registries such as `game/state_authority.py`, `game/response_policy_contracts.py`, `game/final_emission_boundary_contract.py`, `game/realization_authority.py`, `game/contract_registry.py`, `game/validation_layer_contracts.py`, protected replay fields, and split-owner matrix rows.
   - Weak point: ruleset/backend/version/provenance bundle contracts are currently documented but not executable.

3. Determine replay/provenance/evidence implications.
   - Required architectural step for any visible output, fallback, lineage, or protected observation change.
   - Check `game/realization_provenance.py`, `game/final_emission_meta.py`, `game/final_emission_replay_projection.py`, `tests/helpers/golden_replay_projection*`, protected replay manifest, and failure/recurrence helpers.
   - Manual/repetitive where field names must be threaded through runtime meta, runtime projection, protected extraction, defaults, and docs.

4. Implement authoritative behavior in the owner.
   - Required architectural step.
   - Do not move authoritative decisions into adapters/projections/tests.
   - Clear in many seams; less clear for backend/provider expansion because the backend adapter contract is absent.

5. Update adapters/projections.
   - Required architectural step.
   - Prompt adapters, UI projections, Final Emission metadata projection, replay extraction, persistence envelopes, and reports must observe without owning behavior.
   - Manual/repetitive for protected replay and dashboard/report projections.

6. Handle compatibility.
   - Compatibility step.
   - Identify legacy aliases, compatibility-local tokens, CTIR-absent paths, tuple adapters, old payload shapes, re-export barrels, and legacy/unified recurrence fields.
   - Weak point: retirement criteria are not always centralized; older audit docs often contain the evidence but not one active register.

7. Update tests.
   - Governance and quality step.
   - Extend direct-owner tests first. Add smoke/downstream/replay tests only for wiring, observation, or protected acceptance.
   - Repetitive where large fixtures are copied or FEM/protected rows are hand-built.

8. Satisfy governance.
   - Governance step.
   - Run focused tests and relevant audits. For high-risk seams this may include protected replay, final-emission boundary tests, validation audits, split-owner matrix checks, test inventory governance, and CI inventory parity.
   - Efficient where scripts exist; manually heavy when reports or docs need refresh.

9. Update documentation.
   - Documentation step.
   - Update authoritative docs when ownership, contract, or workflow changes. Preserve historical campaign records.
   - Repetitive when current executable contracts are restated in several docs.

10. Verify completed change.
   - Verification step.
   - Use focused owner tests, downstream smoke where needed, governance checks, and generated artifact checks when fields/reports change.
   - Clear for known lanes; dependent on expert memory for choosing the minimal sufficient set.

Workflow profile:

- Clear and efficient: state authority registry, final-emission mutation taxonomy, realization fallback families, model routing, persistence envelope, many direct-owner test lanes.
- Intentionally careful: Final Emission, protected replay, governance/test ownership, recurrence/evidence handling.
- Dependent on expert memory: compatibility residue, which docs are current vs historical, backend/ruleset future-contract boundaries.
- Repetitive: protected field propagation, FEM metadata/defaults/extraction, split-owner matrix report refresh, large test fixtures.
- Weakly documented in executable form: backend/provider contract, ruleset contract, unified version/provenance bundle.
- Obstructed by residue: opening fallback compatibility-local vocabulary, dual fallback-family projection, legacy recurrence/unified rate fields, compatibility re-exports.

## 16. Preliminary Coordination Cost Profile

### Intentional architectural tradeoffs

- Runtime owner plus adapter/projection plus replay/governance separation.
- Final Emission gate ordering and boundary taxonomy.
- Runtime diagnostic projection separate from protected replay acceptance.
- Multi-axis fallback/provenance ownership.
- Direct-owner tests before downstream smoke or transcript coverage.

### Already-minimized concerns

- Final-emission mutation taxonomy is centralized and fail-closed in `game/final_emission_boundary_contract.py`.
- Realization fallback family authority is centralized in `game/realization_authority.py` with stamp helpers in `game/realization_provenance.py`.
- Protected observation fields have a canonical registry and parity checks.
- Prompt narrative projection keys have a contract registry and static drift tests.
- Split-owner matrix has a source, generated report, check script, refresh wrapper, and contract tests.
- Persistence envelope has a versioned wrapper/validator.
- Model routing has a deterministic dataclass/resolver and runtime tests.

### Implementation inefficiencies

- Backend/provider identity is not published as an executable contract.
- Ruleset identity/capability/version contract is not published as an executable contract.
- FEM/protected replay field propagation remains manually threaded.
- Some docs repeat executable registries without generation.
- Large direct-owner tests and hand-built fixtures amplify small changes.

### Compatibility residue

- Opening fallback compatibility-local authorship/taxonomy.
- Dual diegetic/governed fallback-family projection.
- Broad `legacy_diegetic_fallback` and non-emitting `legacy_unclassified`.
- CTIR-absent prompt fallbacks.
- Response policy older-payload accessors.
- `game.gm` and other compatibility re-export surfaces.
- Legacy/unified recurrence rate comparisons.

### Governance overhead

- Protected replay manifest and field parity.
- Split-owner matrix report/count/dashboard parity.
- Test inventory JSON freshness.
- Architecture ownership ledger and suite placement guards.
- Strict validation/final-emission/coverage audits.

### Test-maintenance friction

- Large owner suites and repeated fixture construction.
- Protected replay field matrix expansion.
- Dashboard/classifier expected payload repetition.
- Compatibility tests for retired or transitional paths.

### Documentation synchronization

- Ownership ledger, TEST_AUDIT, README_TESTS, CI inventory, and AR docs can repeat the same current owner/workflow facts.
- Protected replay manifest and split-owner matrix reports are generated or checkable, which helps.
- Historical campaign docs should remain as evidence and not be treated as current-contract duplication unless they are used as workflow authority.

### Candidate simplification opportunities

- Publish executable ruleset/backend/version/provenance contracts before expansion.
- Generate more doc tables from executable registries.
- Improve FEM/protected-row builders and shared assertions.
- Centralize compatibility retirement criteria in active registers.
- Generate split-owner expected counts from matrix rows.
- Clarify minimal verification sets by feature lane.

## 17. Evidence Gaps

| Gap | Missing Repository Evidence | Why It Matters | Exact Evidence Needed | Can Next Cycle Proceed? |
|---|---|---|---|---|
| Actual developer time spent per workflow | No timing/PR effort metrics | Needed to quantify coordination cost rather than infer from file fan-out | PR review notes, task logs, commit timing, developer reports | Yes |
| Current importers for every compatibility re-export | Partial docs/guards, but not full fresh import inventory | Retirement safety depends on consumer proof | Fresh `rg`/AST import report for compat surfaces | Yes |
| Runtime frequency of compatibility-local/opening fallback branches | Tests/docs indicate negative or fail-closed paths, but runtime incidence not measured here | Retirement priority depends on active usage | Telemetry/replay incidence over recent runs | Yes |
| Full backend abstraction design | AR-BG/BH define fields; no executable contract exists | Needed before second provider implementation | Candidate backend protocol/adapter tests and fake backend lane | Yes, classification can proceed |
| Full ruleset abstraction design | AR-BG/BH define fields; no executable contract exists | Needed before alternate rulesets | Candidate ruleset registry/protocol and fake ruleset tests | Yes |
| Which docs are actively used by maintainers | Evidence from docs exists, but usage is inferred | Reducing doc sync should not remove useful workflow docs | Maintainer survey or issue/task references | Yes |
| Fixture duplication quantification | File size and repeated helper evidence sampled, but no fixture dependency graph produced | Needed to choose fixture improvements safely | Test helper dependency graph, repeated literal/object construction counts | Yes |
| Protected replay field change cost over time | Recent CL/CN/CO traces sampled but not fully quantified | Needed to prioritize generation/tooling | Git history diff metrics for field-related changes | Yes |
| Current public/external consumers | No external API/tooling consumers assessed | Public facade/backward compatibility risk unknown | Consumer inventory or product-scope decision | Yes |

## 18. Recommended Next Cycle

Recommended next cycle: **AR-BK - Coordination Cost Classification and Reduction Opportunity Analysis**.

Purpose:

- Deepen the classification started here.
- Quantify the highest-cost paths with commit/file/test/doc fan-out metrics.
- Separate permanent architectural coordination from transitional residue and implementation friction.
- Identify low-risk reduction opportunities that preserve canonical ownership, replay correctness, provenance, extensibility, evidence quality, and governance.

Suggested AR-BK focus:

- Quantify the top 5 paths: Final Emission metadata/projection, protected replay fields, split-owner matrix, compatibility re-exports/residue, and backend/ruleset contract gaps.
- Build a current compatibility-residue register with active caller evidence and retirement criteria.
- Map generated vs manually synchronized docs and propose generation only where a clear canonical executable source exists.
- Identify fixture/builder improvements for FEM/protected replay/failure dashboard tests.
- Produce a ranked opportunity list with architectural risk and verification requirements.

Do not begin broad implementation, compatibility retirement, or governance weakening in AR-BK unless the next instruction explicitly changes scope.

## 19. Files Required for External Review

Required:

- `AR-BJ_coordination_cost_inventory_and_workflow_discovery.md`
- `AR-BI_boundary_reconciliation_campaign_closeout.md`
- `AR-BH_minimal_extensibility_contract_definition.md`
- `AR-BG_ruleset_backend_and_version_provenance_boundary_inventory.md`
- `AR-AD_target_architecture_doctrine.md`
- `docs/architecture_ownership_ledger.md`
- `tests/README_TESTS.md`
- `docs/convergence_ci_inventory.md`
- `game/final_emission_boundary_contract.py`
- `game/realization_authority.py`
- `game/realization_provenance.py`
- `game/contract_registry.py`
- `game/model_routing.py`
- `game/persistence_contract.py`
- `tests/helpers/golden_replay_projection_fields.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/failure_classification_split_owner.py`
- `tests/test_final_emission_boundary_contract.py`
- `tests/test_split_owner_acceptance_matrix_contract.py`
- `tests/test_contract_registry_static_drift.py`
- `tests/test_model_routing_runtime.py`

Optional:

- `game/api.py`
- `game/gm.py`
- `game/final_emission_gate.py`
- `game/final_emission_meta.py`
- `game/final_emission_replay_projection.py`
- `tests/test_final_emission_gate_orchestration_order.py`
- `tests/test_final_emission_meta.py`
- `docs/testing/protected_replay_manifest.md`
- `docs/gate_convergence_closeout.md`
- `docs/gate_cleanup_inventory.md`
- `docs/maintenance/CR_protected_replay_recurrence_separation_discovery.md`
- `CK_fallback_authorship_contraction_discovery.md`
- `CL_replay_projection_churn_reduction_discovery.md`
- `CN_final_emission_adjacency_compression_discovery.md`
- `CO_assertion_family_rationalization_discovery.md`
- Generated artifacts under `artifacts/golden_replay/` only if the next cycle needs quantitative recurrence or replay-output evidence.

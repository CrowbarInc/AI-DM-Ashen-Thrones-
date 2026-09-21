# CD — Ownership Registry Concentration Audit Discovery

Date: 2026-06-24  
Scope: discovery/audit only; no runtime or test behavior changed.

## 1. Executive Summary

The repository has three related but distinct ownership-governance systems:

1. **Test responsibility governance** — `tests/test_ownership_registry.py` embeds the canonical `RESPONSIBILITY_REGISTRY`, maps direct-owner and neighbor suites, consumes `tests/test_inventory_governance.json`, and enforces test locality.
2. **Runtime attribution governance** — `game/final_emission_ownership_schema.py` defines owner tokens and owner-bucket vocabulary; runtime producers stamp those fields and projection/reporting consumers read them.
3. **Architecture and closeout governance** — `docs/architecture_ownership_ledger.md`, convergence documentation, audit registries, CI, and closeout tests preserve policy and closed-cycle invariants.

`tests/test_ownership_registry.py` remains a top-touch file because it is more than a registry test. At 5,959 lines, it contains:

- the embedded test-responsibility registry;
- inventory/schema checks;
- at least 217 test functions and 16 `collect_*` guard functions;
- broad AST/import scans;
- facade and compatibility-barrel fan-in caps;
- cycle-specific migration locks from AD, AE, AL, AO, BA, BD, BE, BF, BG, BI, BJ, BN, BU, and BV;
- hundreds of exact module, symbol, and path expectations.

Git history confirms the concentration. The file has 22 commits from 2026-04-24 through 2026-06-23. Several governance/refactor cycles made very large additions: BJ added 1,798 lines, BN added 667, BV added 1,337, AQ added 374, BF added 285, and BU added 165 net lines. The changes usually accompanied broad extraction, fan-in reduction, inventory compression, or governance closeout work rather than ordinary ownership reassignment.

The concentration is therefore **mostly legitimate governance maintenance, but mildly over-centralized**. A single hard-fail entrypoint is useful, and the direct-owner registry belongs in one visible place. The excess comes from also making that file the permanent home for historical migration proofs, low-level import scanners, compatibility fan-in caps, delegate-collapse checks, and exact source-shape assertions for many unrelated domains.

The runtime attribution side is more appropriately distributed: schema vocabulary is centralized, while stamping, projection, reporting, classifier, dashboard, and replay checks have focused modules and tests. The most material concentration risk is on the **test-governance side**, not the runtime owner-token schema.

## 2. File Inventory

### Core test-ownership registry and inventory

| Path | Purpose | Kind | Role |
| --- | --- | --- | --- |
| `tests/test_ownership_registry.py` | Canonical direct-owner/neighbor registry, inventory validation, import guards, compatibility caps, and cycle-specific architecture locks | Test + embedded registry | Producer, consumer, validator, policy reference |
| `tests/test_inventory_governance.json` | Slim committed inventory of registry-governed test files | Fixture/config | Produced artifact; consumed by registry tests and `tools/test_audit.py` |
| `tools/test_audit.py` | Generates/checks the slim governance inventory and full diagnostic inventory | Tool | Producer and validator |
| `tests/test_test_audit_tool.py` | Focused tests for inventory generation/check semantics | Test | Validator |
| `tests/TEST_AUDIT.md` | Canonical prose map of test themes and practical test ownership | Documentation | Policy reference |
| `tests/TEST_CONSOLIDATION_PLAN.md` | Historical consolidation plan and campaign context | Documentation | Policy/history reference |
| `tests/README_TESTS.md` | Test and governance commands | Documentation | Operator reference |

### Runtime ownership ledger, schema, and registries

| Path | Purpose | Kind | Role |
| --- | --- | --- | --- |
| `docs/architecture_ownership_ledger.md` | Repo-facing declaration of canonical module owners, direct-owner suites, downstream suites, and residue | Documentation | Primary policy reference |
| `docs/ownership_cleanup_delta.md` | Historical ownership cleanup deltas | Documentation | Policy/history reference |
| `game/final_emission_ownership_schema.py` | Canonical owner tokens, owner-bucket values, allowed owner sets, lineage fields, and registry surfaces | Source | Policy producer |
| `game/ownership_projection_views.py` | Narrow read-side facade over ownership schema vocabulary | Source | Consumer and projection provider |
| `game/attribution_read_views.py` | Attribution-oriented read facade | Source | Consumer/provider |
| `game/final_emission_owner_bucket_views.py` | Owner-bucket read projections | Source | Consumer/provider |
| `tests/helpers/failure_classification_sync.py` | Canonical split-owner acceptance matrix shared by classifier/dashboard/projection tests | Test helper/registry | Policy producer and validator |
| `docs/audits/BU15_split_owner_acceptance_matrix.md` | Generated human-readable split-owner matrix | Documentation/generated registry | Policy projection |
| `docs/audits/CB_feature_boundary_registry.json` | Feature-boundary audit registry | Config/audit fixture | Audit policy reference |

### Ownership write ledgers and discovery artifacts

| Path | Purpose | Kind | Role |
| --- | --- | --- | --- |
| `docs/audits/BU4_ownership_write_paths.csv` | Machine-readable inventory of ownership-field write paths | Ledger/fixture | Produced ledger; validator input |
| `docs/audits/BU4_ownership_write_path_registry.md` | Human-readable ownership write-path registry | Documentation | Policy/audit reference |
| `scripts/bu4_ownership_write_path_discovery.py` | AST discovery and generation for BU4 write-path artifacts | Script | Producer |
| `tests/helpers/ownership_write_path_governance.py` | Compares live write paths with BU4 CSV and checks producer/stamp pairing | Test helper | Consumer and validator |
| `docs/audits/BU_ownership_dependency_map.csv` | Ownership-reference dependency map | Audit ledger | Reporting input |
| `docs/audits/BU4_ownership_write_paths.csv` | Concrete ownership metadata writer inventory | Audit ledger | Consumer-facing evidence |
| `docs/realization_triage_ledger.md` | Realization ownership/failure-locality triage record | Documentation/ledger | Policy reference |

### Runtime producers of ownership metadata

| Path | Purpose | Kind | Role |
| --- | --- | --- | --- |
| `game/final_emission_meta.py` | Canonical FEM metadata stamp/merge helpers | Source | Producer |
| `game/final_emission_opening_fallback.py` | Opening fallback authorship and result metadata | Source | Producer |
| `game/final_emission_sealed_fallback.py` | Sealed fallback family and bucket metadata | Source | Producer |
| `game/final_emission_visibility_fallback.py` | Visibility fallback owner-bucket metadata | Source | Producer |
| `game/final_emission_response_type.py` | Response-type path ownership/family metadata | Source | Producer |
| `game/output_sanitizer.py` | Sanitizer ownership traces | Source | Producer |
| `game/social_exchange_emission.py` | Strict-social fallback family/content ownership | Source | Producer |
| `game/upstream_response_repairs.py` | Upstream prepared ownership/family metadata | Source | Producer |
| `game/realization_provenance.py` | Canonical realization fallback-family stamp | Source | Producer |
| `game/api.py` | Upstream-fast selection ownership and fallback-family production | Source | Producer |
| `game/gm.py` | Provider-failure family metadata | Source | Producer |
| `game/gm_retry.py` | Retry-terminal family/content metadata | Source | Producer |

### Runtime and test consumers

| Path | Purpose | Kind | Role |
| --- | --- | --- | --- |
| `game/final_emission_replay_projection.py` | Projects FEM ownership fields into replay lineage | Source | Consumer/projector |
| `game/runtime_lineage_telemetry.py` | Emits ownership fields in lineage events | Source | Consumer/reporter |
| `tests/helpers/golden_replay_projection.py` | Reads ownership fields for protected replay observations | Test helper | Consumer/validator |
| `tests/helpers/golden_replay.py` | Golden replay observation and reporting flow | Test helper | Consumer |
| `tests/helpers/failure_classifier.py` | Classifies failures using owner buckets and split-owner fields | Test helper | Consumer/enforcer |
| `tests/failure_classification_contract.py` | Classification vocabulary contract | Test support | Consumer/policy reference |
| `tests/helpers/failure_dashboard_report.py` | Builds dashboard rows containing ownership attribution | Test helper | Consumer/reporter |
| `tests/helpers/failure_dashboard_fixtures.py` | Dashboard ownership fixtures | Fixture/helper | Consumer |
| `tests/helpers/runtime_lineage_reporting.py` | Runtime-lineage ownership summaries | Test helper | Consumer/reporter |
| `tests/helpers/opening_fallback_evidence.py` | Opening ownership evidence extraction | Test helper | Consumer |
| `tests/helpers/replacement_attribution_inventory.py` | Replacement ownership inventory | Test helper | Consumer/reporter |
| `tests/helpers/attribution_contract.py` | Shared attribution assertions | Test helper | Validator |

### Focused ownership and attribution tests

| Path | Purpose | Kind | Role |
| --- | --- | --- | --- |
| `tests/test_final_emission_meta.py` | Direct-owner FEM packaging/projection tests | Test | Validator |
| `tests/test_runtime_lineage_telemetry.py` | Ownership fields in runtime lineage events | Test | Validator |
| `tests/test_opening_fallback_owner_bucket.py` | Opening owner-bucket behavior | Test | Validator |
| `tests/test_final_emission_opening_fallback.py` | Opening ownership production | Test | Validator |
| `tests/test_final_emission_sealed_fallback.py` | Sealed ownership production | Test | Validator |
| `tests/test_final_emission_visibility_fallback.py` | Visibility ownership production | Test | Validator |
| `tests/test_output_sanitizer.py` | Sanitizer attribution production | Test | Validator |
| `tests/test_golden_replay_fallback_projection.py` | Replay ownership projection | Test | Validator |
| `tests/test_golden_replay_projection.py` | General replay projection contracts | Test | Validator |
| `tests/test_failure_classifier.py` | Ownership-aware failure classification | Test | Validator |
| `tests/test_failure_dashboard_controlled_failures.py` | Ownership-aware dashboard cases | Test | Validator |
| `tests/test_replacement_attribution_inventory.py` | Replacement attribution completeness | Test | Validator |
| `tests/test_attribution_contract.py` | Shared attribution contract | Test | Validator |
| `tests/test_split_owner_acceptance_matrix_contract.py` | Split-owner matrix/report/dashboard/projection parity | Test | Validator |
| `tests/test_refresh_split_owner_acceptance_matrix.py` | Refresh/check command behavior | Test | Validator |

### CI, scripts, and audit tools

| Path | Purpose | Kind | Role |
| --- | --- | --- | --- |
| `.github/workflows/convergence-checks.yml` | Hard-fail ownership registry, inventory drift, matrix, and strict ownership audits | CI config | Enforcer |
| `docs/convergence_ci_inventory.md` | Canonical map of convergence checks and ownership entrypoints | Documentation | Policy/operations reference |
| `scripts/check_split_owner_acceptance_matrix.py` | Read-only matrix/report parity gate | Script | Validator |
| `scripts/refresh_split_owner_acceptance_matrix.py` | Regenerates report and runs checks/tests | Script | Producer and validator |
| `scripts/split_owner_acceptance_matrix_ops.py` | Shared matrix refresh/check implementation | Script | Producer and validator |
| `tools/final_emission_ownership_audit.py` | Strict/advisory final-emission ownership audit | Tool | Validator |
| `tools/cb7_ownership_drift_analysis.py` | Read-only ownership/coupling drift analysis | Tool | Consumer/reporter |
| `tools/run_governance_audits.py` | Local informational governance audit runner | Tool | Orchestrator |
| `tools/validation_layer_audit.py` | Validation-layer ownership drift audit | Tool | Validator |
| `tools/architecture_audit.py` | Broad architecture/governance audit | Tool | Validator/reporter |

## 3. Touch/Churn Evidence

### Frequency

Git history shows:

| File | Commits observed |
| --- | ---: |
| `tests/test_ownership_registry.py` | 22 |
| `docs/architecture_ownership_ledger.md` | 16 |
| `docs/ownership_cleanup_delta.md` | 8 |
| `docs/realization_triage_ledger.md` | 4 |
| `docs/audits/BU_ownership_dependency_map.csv` | 3 |
| `game/final_emission_ownership_schema.py` | 1 |
| `game/ownership_projection_views.py` | 1 |
| `docs/audits/BU4_ownership_write_paths.csv` | 1 |

The embedded test registry is therefore the clear ownership-governance top-touch file. The runtime schema is not high-churn; it was introduced in BU and has remained comparatively stable.

### Registry test change history

Representative commits:

| Commit | Date | Registry-test delta | Pattern |
| --- | --- | ---: | --- |
| `64fe7c2` | 2026-04-24 | +359 | Initial test ownership/coverage consolidation |
| `9cedc9a` | 2026-04-24 | +226/-21 | Registry and inventory refinement |
| `8cbea51` | 2026-05-31 | +101/-1 | Test-authority consolidation |
| `888d0fc` | 2026-06-06 | +374/-24 | Inventory compression and derived-field policy |
| `a534e5f` | 2026-06-11 | +285/-72 | Test-inventory de-amplification |
| `11ff282` | 2026-06-16 | +1,798/-5 | BJ final-emission responsibility extraction locks |
| `b88a560` | 2026-06-17 | +667/-7 | BN gate fan-out/preflight import locks |
| `22cd49a` | 2026-06-21 | +165/-67 | BU ownership write-path and split-owner governance |
| `7651237` | 2026-06-21 | +1,337/-16 | BV facade/barrel/import-cap governance closeout |
| `ce36d0c` | 2026-06-23 | +22 | CB feature-boundary readiness/drift evidence |

### Recurring edit patterns

Edits are strongly clustered around named architecture cycles rather than random defect repair:

- **Test ownership and inventory cycles:** AD, AQ, BF.
- **Gate/final-emission extraction cycles:** BJ, BN.
- **Dependency compression and facade routing:** BD, BV.
- **Runtime ownership and write-path inventory:** BU.
- **Replay ownership isolation/consolidation:** AO, BI.
- **Architecture readiness audits:** CB.

The file changes frequently for four principal reasons:

1. **Policy encoding:** the direct-owner registry and neighbor classifications are stored in the test module.
2. **Broad structural assertions:** exact imports, source fragments, callable locations, removed wrappers, and fan-in caps are locked there.
3. **Inventory expectations:** the file validates the committed governance JSON and live derived test inventory.
4. **True ownership changes:** less frequent, but present when canonical owner modules or split-owner vocabulary change.

The dominant cause is policy and structural governance maintenance, not fixture-count churn and not routine changes to who owns a domain.

## 4. Edit Classification

### A. Governance update

Concrete examples:

- `8cbea51` (`tests/test_ownership_registry.py`): added downstream-smoke versus direct-owner restrictions for Cycle AD.
- `888d0fc` (`tests/test_ownership_registry.py`, `tools/test_audit.py`): moved derivable inventory fields out of committed governance and added validation of the slimmer contract.
- `b88a560` (`tests/test_ownership_registry.py`): added BN1–BN11 import and preflight-boundary guards.
- `7651237` (`tests/test_ownership_registry.py`): added BV7C/BV12C/BV13C/BV14C/BV2C/BV10 import lockdowns and fan-in caps.
- `ce36d0c` (`tests/test_ownership_registry.py`, `tools/cb7_ownership_drift_analysis.py`): added ownership drift/readiness evidence.

These are governance changes because they tighten or document permitted dependency shape without changing runtime ownership semantics.

### B. Real ownership change

Concrete examples:

- `22cd49a` introduced `game/final_emission_ownership_schema.py` and centralized canonical selection/content-owner tokens and owner buckets. This is a substantive ownership-contract change.
- `927dae2` (AO replay ownership consolidation) updated `tests/test_ownership_registry.py` to reflect consolidated replay ownership.
- `f7e73fb` (BI golden replay ownership isolation) added explicit separation between gate ownership and replay/read-side ownership.
- `11ff282` (BJ) moved many responsibilities out of `game/final_emission_gate.py` into focused owner modules. The runtime refactor was a real producer/consumer responsibility change, even though many registry-file edits were enforcement locks around it.

### C. Fixture/expectation maintenance

Concrete examples:

- `64fe7c2` and `9cedc9a` updated `tests/test_inventory.json` and the ownership registry together during initial ownership consolidation.
- `888d0fc` and `a534e5f` changed expected inventory shape and derived-field treatment in `tests/test_inventory_governance.json`, `tools/test_audit.py`, and `tests/test_ownership_registry.py`.
- `22cd49a` added generated `docs/audits/BU15_split_owner_acceptance_matrix.md` and `docs/audits/BU4_ownership_write_paths.csv`; these artifacts require parity refresh when their canonical inputs change.

This category exists, but expected-count or snapshot-only churn is not the main explanation for the registry test’s size.

### D. Refactor/support change

Concrete examples:

- `11ff282` added assertions that old gate wrappers disappeared and focused owner entrypoints became callable.
- `b88a560` locked the extraction of gate-context preflight helpers and prohibited regrowth of direct imports.
- `7651237` guarded compatibility barrels and routed consumers through focused facade modules.
- `97b1836` performed small symmetric edits (+10/-10) during replay projection simplification.

These changes are generally valuable architecture locks, but they bind the central file to exact implementation shape.

### E. Risk-bearing policy centralization

Concrete examples:

- `tests/test_ownership_registry.py` contains the registry, inventory contract, import scanners, fan-in caps, exact source-fragment rules, delegate-collapse checks, and cycle history in one 5,959-line hard-fail module.
- BJ added roughly 1,800 lines of per-symbol ownership/delegation assertions to the registry file instead of placing most of them beside focused owner modules.
- BV added roughly 1,350 lines of unrelated facade/barrel governance across smoke helpers, final-emission text, social exchange, metadata, and ownership projections.
- `tools/test_audit.py` imports `build_ownership_registry_index` and `_CROSS_FILE_DUPLICATE_ALLOWLIST` from the test module. This makes a test file an implementation dependency of the inventory tool.
- CI runs the entire registry file as one hard-fail step, so failures from test inventory, gate preflight imports, compatibility fan-in, runtime owner delegation, or ownership write-path parity share one broad failure surface.

This is the clearest evidence of mild over-centralization.

## 5. Consumer Mapping

### Runtime ownership-data consumers

| Consumer | Data read | Function | Direct dependency | Focused tests | Likely breakage on metadata change |
| --- | --- | --- | --- | --- | --- |
| `game/final_emission_replay_projection.py` | Owner buckets, authorship, selection/content owner | Projects replay lineage | Direct schema/read-facade dependency | `tests/test_golden_replay_fallback_projection.py`, `tests/test_final_emission_meta.py` | Replay fields, protected observations, classifier inputs |
| `game/runtime_lineage_telemetry.py` | Selection/content owner and fallback owner bucket | Reports lineage events | Direct vocabulary/read dependency | `tests/test_runtime_lineage_telemetry.py` | Event schema and reporting parity |
| `game/ownership_projection_views.py` | Canonical ownership vocabulary | Read-side facade | Direct schema dependency by design | `tests/test_bv10a_read_facade_delegates.py` | Facade consumers and import-governance tests |
| `game/attribution_read_views.py` | Attribution fields and owner buckets | Read facade | Direct authority dependency by design | Attribution/facade tests | Report and classifier reads |
| `tests/helpers/golden_replay_projection.py` | FEM ownership fields | Validates/projects protected replay | Through read facades/helpers | Golden replay projection tests | Protected replay schema and snapshots |
| `tests/helpers/failure_classifier.py` | Owner buckets and split owners | Enforces failure taxonomy | Matrix and projection contracts | `tests/test_failure_classifier.py` | Classification cases and dashboard parity |
| `tests/helpers/failure_dashboard_report.py` | Split-owner classification | Reports controlled failures | Classifier/matrix dependency | `tests/test_failure_dashboard_controlled_failures.py` | Dashboard case IDs and rendered columns |
| `tests/helpers/runtime_lineage_reporting.py` | Runtime ownership lineage | Reports summaries | Lineage event dependency | Runtime lineage/report tests | Trend and attribution reports |
| `tests/helpers/replacement_attribution_inventory.py` | Replacement owner/source fields | Reports attribution completeness | Projection/helper dependency | `tests/test_replacement_attribution_inventory.py` | Completeness metrics and closeout claims |

### Test-governance consumers

| Consumer | Data read | Function | Direct dependency | Focused tests | Likely breakage |
| --- | --- | --- | --- | --- | --- |
| `tools/test_audit.py` | `build_ownership_registry_index`, duplicate-name allowlist | Generates/checks governance inventory | Directly imports `tests.test_ownership_registry` | `tests/test_test_audit_tool.py` | Inventory generation and CI drift gate |
| `tests/test_ownership_registry.py` | `tests/test_inventory_governance.json`, full live audit | Validates registry and locality | Central registry itself | Same module | Broad CI failure |
| `tools/cb7_ownership_drift_analysis.py` | Ledger text and ownership dependency CSV | Reports concentration/drift | Reads docs/CSV | Audit outputs rather than a focused unit suite | Readiness report changes |
| `tests/helpers/ownership_write_path_governance.py` | BU4 CSV and live AST scan | Validates writer parity | Direct CSV/script dependency | Registry BU8/BU9 tests | Production writer drift gate |
| `scripts/check_split_owner_acceptance_matrix.py` | Matrix and generated report | Enforces parity | Direct helper registry dependency | Matrix contract tests | CI matrix step |

Producer/consumer boundaries are clearest on the runtime attribution side. They are less clear on the test-governance side because the registry test is simultaneously the policy source, validator, and dependency imported by tooling.

## 6. Enforcement Mapping

| Enforcement point | Contract enforced | Centralized/distributed | Failure locality | Duplication |
| --- | --- | --- | --- | --- |
| `tests/test_ownership_registry.py` | Direct-owner uniqueness, neighbor roles, inventory parity, import restrictions, facade caps, owner delegation | Highly centralized | Mixed; messages are often actionable, but unrelated domains share one file | Several rules overlap focused tests/helpers |
| `tools/test_audit.py --check` | Committed governance inventory equals fresh derivation | Centralized tool | Generally clear | Overlaps registry inventory assertions intentionally |
| `tests/test_inventory_governance.json` | Stable committed file inventory | Central artifact | Drift diff is understandable | Mirrored by tool and registry tests |
| `tests/helpers/ownership_write_path_governance.py` | BU4 CSV/live writer parity and producer-stamp pairing | Focused helper | Clear writer/path messages | Invoked from central registry tests |
| `tests/test_split_owner_acceptance_matrix_contract.py` | Matrix/report/dashboard/FEM/classifier parity | Focused | Clear | Also run through script |
| `scripts/check_split_owner_acceptance_matrix.py` | Read-only matrix parity | Focused CI entrypoint | Clear | Intentional wrapper duplication |
| `tools/final_emission_ownership_audit.py --strict` | Final-emission ownership boundary drift | Focused audit | Usually clear categories | Some overlap with registry source/import locks |
| `tools/validation_layer_audit.py --strict` | Cross-layer ownership/import drift | Focused audit | Clear categorized findings | Some overlap with registry layer assertions |
| `.github/workflows/convergence-checks.yml` | Runs ownership, inventory, matrix, and strict audit gates | Central CI orchestration | Step-level locality is good | No problematic duplication in workflows |
| `docs/architecture_ownership_ledger.md` | Human policy: owner → direct-owner suite → downstream consumers | Central prose authority | Review-local, not executable | Summarized in test registry and other docs |
| Closeout tests | Freeze selected docs/taxonomies/commands | Distributed by seam | Good when focused | Some ownership facts repeat registry/ledger |

The same high-level rule—“one owner, downstream consumers do not become authorities”—is intentionally expressed in prose, registry data, focused tests, and audits. The problematic duplication is not the principle; it is exact low-level path/symbol policy repeated centrally and locally.

## 7. Closeout Test Review

| Path | Purpose | Ownership evidence required | Registry/ledger dependency | Concentration effect |
| --- | --- | --- | --- | --- |
| `tests/test_evaluator_convergence_closeout.py` | Freezes evaluator as offline/read-only and non-authoritative | Closeout doc phrases | None direct | Reduces concentration; focused and small |
| `tests/test_gate_convergence_closeout.py` | Freezes gate taxonomy and doc/code parity | Canonical mutation buckets and closeout references | Indirect architectural alignment | Reduces concentration; focused seam owner |
| `tests/test_validation_layer_closeout.py` | Freezes layer IDs, import boundaries, and audit behavior | Validation registry, docs, import allowlists | Parallel ownership policy | Reduces concentration; focused |
| `tests/test_split_owner_acceptance_matrix_contract.py` | Freezes split-owner literals and generated/reporting parity | Matrix rows, owner literals, dashboard IDs | Directly related runtime ownership registry | Reduces concentration by giving split-owner policy a focused home |
| `tests/test_bw_protected_replay_trend_window_closeout.py` | Freezes replay trend commands/artifacts/corpus | Protected replay registry and docs | Ownership fields only indirectly | Neutral |
| `tests/test_bz_protected_replay_trend_window_2_closeout.py` | Freezes second trend-window evidence | Replay registry, artifacts, commands | Ownership fields indirectly | Neutral |
| `tests/test_by4_semantic_mutation_attribution_closeout.py` | Freezes attribution completeness and non-interference | Attribution fields and protected observations | Runtime ownership metadata consumers | Reduces concentration; focused measurement closeout |

Focused closeout tests generally reduce concentration because they keep seam-specific evidence near the seam. The central registry becomes more concentrated when it duplicates their exact implementation-path assertions instead of only registering their roles.

## 8. Concentration Risk Assessment

### Overall classification

**Mildly over-centralized.**

The repository is not materially over-centralized because:

- runtime owner tokens have a narrow source module;
- metadata producers are distributed by behavior;
- projections, classifiers, dashboards, and replay consumers have focused helpers/tests;
- policy documentation explicitly distinguishes owners from consumers;
- CI exposes separate steps for registry, matrix, inventory, and strict audits.

It is more than merely “fragmented but appearing centralized” because `tests/test_ownership_registry.py` genuinely owns a large executable policy surface and is imported by `tools/test_audit.py`.

### Risk ratings

| Risk | Rating | Evidence |
| --- | --- | --- |
| Top-touch file risk | High | 22 commits; 5,959 lines; several 600–1,800-line cycle expansions |
| False-positive churn | Medium | Exact imports, source fragments, callable locations, and FI caps change during safe refactors |
| Fixture brittleness | Medium | Governance JSON and generated CSV/Markdown parity require coordinated refreshes |
| Ownership semantics hidden in tests | Medium-high | `RESPONSIBILITY_REGISTRY`, allowlists, caps, and routing policy live inside a test module |
| Excessive closeout coupling | Medium | Historical cycle locks remain in the central file after focused closeout tests exist |
| Unclear producer/consumer boundaries | Low-medium runtime; medium test governance | Runtime schema/writers/readers are fairly clear; test module is producer + consumer + validator |

### Key interpretation

High touch is not evidence that ownership changes constantly. It is evidence that the file is the default landing zone for governance closure after nearly every architecture cycle. That pattern gives strong regression protection but inflates change locality and makes safe structural work appear as ownership-governance churn.

## 9. Recommended Next Actions

### Safe/no-behavior-change cleanup

1. **Extract registry data from the test module.** Move `ResponsibilityRecord`, `RESPONSIBILITY_REGISTRY`, index construction, and duplicate-name policy into an import-light module such as `tests/ownership_registry_contract.py`. Keep `tests/test_ownership_registry.py` as tests. This removes the tool → test-module dependency without changing policy.
2. **Generate a registry index artifact for audits.** Provide a stable JSON or Python surface for tools instead of importing private test constants.

### Test-locality improvements

3. **Move domain-specific guard implementations beside their domains.** Candidate families: BN gate-context guards, BV compatibility-barrel caps, BJ delegate-collapse locks, and BU write-path parity. The central registry should register or invoke focused contracts, not contain every scanner and expected symbol.
4. **Retire historical migration locks when superseded.** For each cycle marker, distinguish permanent architectural invariant from one-time proof that a wrapper/import was removed. Preserve permanent “no regrowth” checks; archive checks that only prove a completed move and are already covered by focused owner tests.
5. **Split the CI registry step into named slices without weakening it.** Example: core responsibility/inventory, final-emission dependency guards, and compatibility/fan-in guards. Separate step names improve failure locality even if all remain hard-fail.

### Documentation/governance improvements

6. **Document precedence among the three ownership systems.** State explicitly: architecture ledger governs module responsibility; the test registry governs test locality; final-emission schema governs runtime attribution tokens; split-owner matrix governs cross-consumer acceptance literals.

### Structural changes requiring caution

7. **Avoid a broad rewrite into many independent registries.** Fragmenting the canonical responsibility map would trade current concentration for policy drift. Extract mechanics and domain guards while preserving one canonical responsibility registry and one canonical runtime attribution schema.

## 10. Files to Pass Back

The highest-value implementation inputs are:

- this discovery report;
- the central registry test and its inventory tool/artifact;
- the architecture ownership ledger;
- runtime ownership schema and read facades;
- write-path ledger, generator, and validator;
- split-owner matrix source, generated report, scripts, and contract tests;
- CI and convergence inventory;
- representative focused closeout tests.

## Recommended Files to Provide

### Discovery report

- `CD_ownership_registry_concentration_audit_discovery.md`

### Central test ownership registry

- `tests/test_ownership_registry.py`
- `tests/test_inventory_governance.json`
- `tools/test_audit.py`
- `tests/test_test_audit_tool.py`

### Ownership ledger and policy documentation

- `docs/architecture_ownership_ledger.md`
- `tests/TEST_AUDIT.md`
- `tests/TEST_CONSOLIDATION_PLAN.md`
- `docs/convergence_ci_inventory.md`
- `docs/final_emission_ownership_convergence.md`
- `docs/ownership_cleanup_delta.md`

### Runtime ownership registry/schema

- `game/final_emission_ownership_schema.py`
- `game/ownership_projection_views.py`
- `game/attribution_read_views.py`
- `game/final_emission_owner_bucket_views.py`
- `game/final_emission_meta.py`

### Ownership write-path ledger and validation

- `docs/audits/BU4_ownership_write_paths.csv`
- `docs/audits/BU4_ownership_write_path_registry.md`
- `docs/audits/BU_ownership_dependency_map.csv`
- `scripts/bu4_ownership_write_path_discovery.py`
- `tests/helpers/ownership_write_path_governance.py`

### Ownership consumers

- `game/final_emission_replay_projection.py`
- `game/runtime_lineage_telemetry.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/runtime_lineage_reporting.py`
- `tests/helpers/replacement_attribution_inventory.py`

### Split-owner registry and contracts

- `tests/helpers/failure_classification_sync.py`
- `docs/audits/BU15_split_owner_acceptance_matrix.md`
- `tests/test_split_owner_acceptance_matrix_contract.py`
- `tests/test_refresh_split_owner_acceptance_matrix.py`
- `scripts/check_split_owner_acceptance_matrix.py`
- `scripts/refresh_split_owner_acceptance_matrix.py`
- `scripts/split_owner_acceptance_matrix_ops.py`

### Ownership-related closeout tests

- `tests/test_evaluator_convergence_closeout.py`
- `tests/test_gate_convergence_closeout.py`
- `tests/test_validation_layer_closeout.py`
- `tests/test_bw_protected_replay_trend_window_closeout.py`
- `tests/test_bz_protected_replay_trend_window_2_closeout.py`
- `tests/test_by4_semantic_mutation_attribution_closeout.py`

### CI and audit enforcement

- `.github/workflows/convergence-checks.yml`
- `tools/final_emission_ownership_audit.py`
- `tools/validation_layer_audit.py`
- `tools/architecture_audit.py`
- `tools/cb7_ownership_drift_analysis.py`
- `tools/run_governance_audits.py`

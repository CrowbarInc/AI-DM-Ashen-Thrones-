# CH — Governance Hub Redistribution Discovery

Date: 2026-06-25  
Scope: discovery only; no runtime, test, fixture, taxonomy, or governance behavior changed.

## Executive Summary

Governance knowledge is concentrated in a small set of high-authority files and synchronized file
families. The strongest current risks are:

1. `tests/test_ownership_registry.py` remains a 5,959-line, 22-commit landing zone for responsibility
   registration, architecture locks, inventory checks, import/fan-in policy, and historical migration
   proof.
2. Runtime ownership and attribution changes converge on `game/final_emission_meta.py` and
   `game/final_emission_replay_projection.py`, then propagate into protected replay, classifier,
   dashboard, and recurrence contracts.
3. Golden replay concentration has been redistributed successfully at the test-file level, but the
   stable public hubs (`golden_replay.py`, `failure_dashboard_report.py`, and
   `golden_replay_projection.py`) still carry high touch/fan-in and compatibility responsibility.
4. Failure classification authority is now documented and split, but ordinary taxonomy changes still
   require coordinated contract, classifier, fixture/test, and sometimes recurrence-artifact edits.
5. Recurrence code was decomposed, yet its analytics remain concentrated in
   `replay_bug_recurrence_statistics.py` (4,350 current lines) and
   `replay_bug_recurrence_history.py` (3,079 current lines), while `recurrence:v1` embeds mutable
   `field_path` and `investigate_first` values.

The overall hotspot concentration assessment is **High**. It is not Severe because CE and CG already
created focused modules, stable facades, authority registries, derived fixtures, and artifact
retention rules. It remains High because one recorded author identity owns every measured hotspot,
the largest governance file still absorbs unrelated architecture-cycle locks, and several conceptual
changes predictably fan out across 4–7 code/governance surfaces plus generated evidence.

## Inputs Reviewed

### Prior CD–CG artifacts

| Artifact | Evidence extracted |
|---|---|
| `CD_ownership_registry_concentration_audit_discovery.md` | Named `tests/test_ownership_registry.py` as the ownership top-touch file: 22 commits, 5,959 lines, and large BJ/BN/BV additions. Identified policy, inventory, import scanning, fan-in caps, closeout locks, and tool-to-test imports in one file. Recommended extracting registry data/mechanics while preserving one canonical responsibility map. |
| `CE_golden_replay_concentration_audit_discovery.md` | Reported historical concentration in `tests/test_golden_replay.py` (38 touches) and current concentration in `golden_replay.py`, `failure_dashboard_report.py`, protected manifest/projection, and runtime replay projection. Reported one author identity for all measured replay commits. |
| `CE1_replay_maintenance_metrics_summary.md` | Baseline: 80 replay files, 47,022 LOC, report-hub fan-in 27, projection fan-in 17, and elevated maintenance risk. |
| `CE2_3_recurrence_module_extraction_summary.md` | Moved recurrence rendering/orchestration out of the dashboard hub; preserved compatibility exports and report bytes. |
| `CE3_replay_bug_recurrence_decomposition_summary.md` | Split a 10,466-line recurrence monolith into facade, events, history, statistics, and serialization modules. Identified history/statistics as residual elevated concentration. |
| `CE4_fallback_projection_test_decomposition_summary.md` | Replaced a 1,251-line fallback-projection test monolith with eight focused family owners. |
| `CE5_acceptance_projection_ownership_split_summary.md` | Split the 1,756-line acceptance projection into fields, manifest, extractors, fallbacks, speaker, and a stable facade; the 978-line extractor remained the largest implementation slice. |
| `CE6_generated_replay_artifact_churn_reduction_summary.md` | Registered 16 artifact families and 111 tracked files; distinguished canonical evidence, frozen baselines, paired mirrors, and local-only outputs. |
| `docs/audits/CF_replay_projection_responsibility_discovery.md` | Identified the single acceptance assembler, 41 protected fields, runtime/acceptance dual projection, extraction/precedence concentration, and broad projection tests. Recommended explicit precedence and source/default contracts. |
| `docs/audits/CG_failure_classification_synchronization_discovery.md` | Measured 18 core files / 25,575 LOC, ordinary taxonomy fanout of 3–7 files, split-owner fanout of 6+ surfaces, and repeated contract/classifier/report/sync co-change. |
| `docs/audits/CG_failure_classification_cost_closeout.md` | Confirmed improved governance rather than raw cost removal: classifier routing fanout fell to 2–3 files, but recurrence analytics, presentation goldens, and v1 key mutability remain. |
| `docs/audits/CG_failure_classification_authority_registry.md` | Declares field-level authorities and key-sensitive taxonomy fields. |
| `docs/audits/CG_recurrence_taxonomy_registry.md` | Records the recurrence taxonomy families and cross-module derivations. |
| `docs/audits/CG_attribution_contract_registry.md` | Distinguishes producer facts, imported vocabulary, validation unions, aliases, and display-only attribution values. |
| `docs/audits/CG_recurrence_key_stability_review.md` | Identifies `field_path` and `investigate_first` as high-risk mutable v1 identity components and estimates a v2 migration at roughly 20 surfaces. |

### Documentation-governance inputs

- `docs/audits/audit_manifest.md`
- `docs/audits/documentation_governance.md`
- `docs/audits/documentation_governance_closeout.md`
- `docs/audits/documentation_inventory.csv`
- `docs/testing/protected_replay_manifest.md`
- `artifacts/golden_replay/artifact_manifest.md`

The documentation closeout classified 472 records: 259 generator-owned, 24 test/path-contract owned,
157 historical, 32 safe future migration candidates, and zero unknown. The manifest itself is small
and low-touch, but exact-path governance creates cross-cutting migration constraints.

### Key implementation, test, fixture, and registry files

- `tests/test_ownership_registry.py`
- `game/final_emission_meta.py`
- `game/final_emission_ownership_schema.py`
- `game/final_emission_replay_projection.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/golden_replay_projection.py` and its focused modules
- `tests/helpers/failure_dashboard_report.py` and its focused modules
- `tests/failure_classification_contract.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/failure_classification_sync.py` and its focused modules
- `tests/helpers/replay_bug_recurrence_{events,history,statistics,serialization}.py`
- `tests/test_replay_bug_class_recurrence.py`
- `tests/helpers/protected_replay_registry.py`
- `tests/helpers/golden_replay_artifact_manifest.py`

Git history is available, contains 250 commits, and is not shallow. “Recent” below means commits from
2026-05-26 through 2026-06-25. Commit touches and distinct commits are equivalent here because each
file is counted at most once per commit. Addition/deletion totals are historical churn, not current
file size.

## Ranked Governance Hubs

| Rank | File / directory | Governance role | Touch concentration evidence | Owner concentration evidence | Recurrence pattern | Risk level |
|---:|---|---|---|---|---|---|
| 1 | `tests/test_ownership_registry.py` | Canonical test-responsibility registry plus inventory, import, facade, fan-in, and migration locks | 22 commits; 20 recent; 6,214 additions / 255 deletions; 5,959 current lines. Common co-changes: historical `test_golden_replay.py` (11), classification sync (9), replay projection (9), gate test (9). | 1 distinct author on the file | Policy-driven and refactor-driven architecture locks; registry/inventory updates; closeout/governance accumulation | **Severe** |
| 2 | `game/final_emission_meta.py` | Runtime FEM metadata authority and normalization hub feeding ownership, projection, attribution, and replay | 35 commits; 12 recent; 2,934 additions / 817 deletions; 2,117 lines. Co-changes with final-emission gate (26), direct tests (22), gate tests (17), runtime replay projection (11). | 1 distinct author | Feature-driven metadata additions; ownership/attribution contract sync; fallback-family and normalization policy | **High** |
| 3 | `tests/helpers/golden_replay.py` | Golden replay orchestration, assertion, drift, summary, and report bridge | 25 commits; 18 recent; 3,216 additions / 1,149 deletions; 2,067 lines. CE measured high fan-in; 14 commits co-change with dashboard report and 10 with protected manifest. | 1 distinct author | Replay behavior and assertion updates; helper refactors; projection/report integration; protected expectation changes | **High** |
| 4 | `tests/helpers/failure_dashboard_report.py` plus `failure_dashboard_*` modules | Compatibility/report hub for dashboard, protected failures, drift, stability, and artifact writing | 22 commits; 16 recent; 3,774 additions / 3,051 deletions; current facade/hub 723 lines after CE extraction. CE baseline fan-in was 27. | 1 distinct author | Diagnostic/report-driven churn; artifact family extraction; rendering and writer synchronization | **High** |
| 5 | `tests/helpers/golden_replay_projection.py` plus focused projection modules | Stable acceptance facade and sole turn-observation assembler over a 41-field protected schema | 17 commits; all 17 recent; 2,221 additions / 1,913 deletions in facade history. Extractor is 978 lines after the June 25 split. Co-changes with classification sync and classification contract tests (11 each). | 1 distinct author | Protected schema additions; source/default/precedence changes; manifest sync; speaker/fallback projection | **High** |
| 6 | `game/final_emission_replay_projection.py` | Runtime read-side lineage, source-family, mutation, owner, and fallback projection | 12 commits; all 12 recent; 955 additions / 63 deletions; 892 lines. Co-changes with FEM meta (11), direct tests (10), failure contract and acceptance projection (7 each). | 1 distinct author | Policy-driven map/taxonomy updates and feature-driven fallback/attribution projection | **High** |
| 7 | `tests/failure_classification_contract.py` + `tests/helpers/failure_classifier.py` | Public row taxonomy/schema plus behavioral classification authority | Contract: 15 commits/11 recent/424 lines. Classifier: 14 commits/9 recent/1,001 lines. Pair co-changed in 13 classifier commits. | 1 distinct author on both | Taxonomy additions/renames, owner/severity/source routing, investigation-target changes, contract sync | **High** |
| 8 | `tests/helpers/failure_classification_sync.py` + focused sync modules | Compatibility facade over alignment, builders, expectations, and 16-row split-owner acceptance authority | Facade history: 13 commits, all recent, 2,437 additions / 2,407 deletions; now 30 lines. Largest current split is `failure_classification_split_owner.py` at 1,011 lines. | 1 distinct author | Split-owner matrix updates; generated report parity; classifier/dashboard/projection contract synchronization | **Moderate–High** |
| 9 | `tests/helpers/replay_bug_recurrence_statistics.py` and `replay_bug_recurrence_history.py` | Recurrence analytics, trend/forecast/lifecycle/governance, maturity, roadmap, and graduation policy | Current size: 4,350 + 3,079 lines. Only two path-history commits each because CE3 created the split on June 25; low touch is not stability evidence. Generated recurrence/drift artifacts co-change with both commits. | 1 distinct author | Taxonomy and threshold policy; report/JSON regeneration; lifecycle/forecast alignment; governance closeout | **High latent** |
| 10 | `tests/test_replay_bug_class_recurrence.py` | Broad contract-lock suite for recurrence keys, statuses, analytics, reports, and graduation | 3,141 lines; two commits in current path history. CG identifies it as the broad residual recurrence lock surface. | 1 distinct author | Test expectation churn following recurrence taxonomy, serialization, threshold, or artifact changes | **Moderate–High** |
| 11 | `docs/testing/protected_replay_manifest.md` + refresh tool | Test-owned human/governance projection contract with generated protected-field section | 17 commits; 16 recent; 392 additions / 24 deletions. Co-changes repeatedly with replay helpers, projection, and dashboard work. | 1 distinct author | Mechanical manifest refresh plus policy explanation updates | **Moderate–High** |
| 12 | `tests/helpers/protected_replay_registry.py` | Scenario/corpus membership, ordering, category, and marker authority | 344 lines; two commits. Low churn but broad consumers and exact corpus count/order assumptions. | 1 distinct author | Deliberate corpus promotion/bookkeeping rather than routine feature edits | **Moderate authority / Low churn** |
| 13 | `docs/audits/audit_manifest.md` + documentation governance | Documentation authority, path-contract classification, generated/test-owned location policy | One commit each; low direct churn. Governs 472 reviewed documentation records and constrains movement of 283 generator/test-owned paths. | 1 distinct author | Documentation-only governance and path migration planning | **Moderate systemic / Low touch** |

### Author evidence

The repository has two author-name identities globally, but every measured hub above has exactly one
distinct author name in its file history. The audit cannot determine whether that reflects one person,
multiple credentials, or imported history. It does show that social maintenance knowledge is not
demonstrably distributed across contributors.

## Cross-Cutting Governance Seams

| Seam | Triggering change | Files involved | Recurrence evidence | Coupling reason | Redistribution opportunity |
|---|---|---|---|---|---|
| Failure taxonomy and routing | Add/rename category, owner, source family, severity, or investigation target | `failure_classification_contract.py`; `failure_classifier.py`; focused sync modules; dashboard fixtures/tests; attribution contract/tests; recurrence events/artifacts when key fields change | Contract + classifier co-changed 12 times in CG discovery; ordinary fanout 3–7 files; current pair co-change count 13 | Vocabulary, behavior, validation, fixtures, display, and recurrence identity intentionally express the same concept | Preserve contract/classifier authority; derive routing fixtures; add a concept-to-consumer manifest and automated fanout report; isolate recurrence-key migration checks |
| Protected replay field/schema change | Add/rename a protected path, source, default, drift bucket, or presence rule | Projection fields/extractors/facade; manifest renderer/tool/doc; failure contract evidence overlap; classifier partitions; synthetic rows; projection tests; trend/recurrence artifacts | Projection facade 17 recent commits; manifest 17 commits; 11 co-changes with classification sync and contract tests | The 41-field registry is acceptance authority and is reused by manifest, classifier, dashboards, and diagnostics | Implement CF2-style executable source/default/owner matrix; generate downstream manifests from it; retain one assembler and one field registry |
| Ownership/fallback attribution change | Change owner token, owner bucket, fallback family, source-family mapping, or split-owner row | `final_emission_ownership_schema.py`; `final_emission_meta.py`; runtime replay projection; ownership read views; split-owner matrix; acceptance projection; classifier; dashboard; attribution tests; BU15 report | FEM meta/runtime projection co-changed 11 times; split-owner changes historically require 6+ surfaces | Runtime write authority, read-side projection, acceptance projection, classification, and governance matrix all need parity | Keep runtime schema canonical; move mapping tables into focused contract modules; generate matrix projections/tests from one row authority; add first-owner failure routing |
| Test ownership rule or architecture-boundary change | Add owner/neighbor suite, move responsibility, add no-regrowth lock, or change fan-in/import cap | `test_ownership_registry.py`; inventory JSON; `tools/test_audit.py`; architecture ledger; focused owner tests; CI | 20 of 22 registry commits are recent; large BJ/BN/BV additions; many unrelated co-change partners | The registry test is simultaneously data source, validator, scanner library, and historical lock repository | Extract import-light registry contract; move domain guards beside domains; central file should register/invoke focused contracts |
| Recurrence taxonomy or threshold change | Add/rename trend, forecast, lifecycle, governance, confidence, or graduation class | Recurrence history/statistics/serialization; recurrence dashboard renderer; broad recurrence test; JSON/Markdown artifacts | CG estimates 3–6 code/test files plus artifacts; current analytics total >7,400 lines | Second-order taxonomies are intentionally cross-mapped and rendered in several formats | Create a compact executable recurrence taxonomy manifest; split tests by contract family; replace wildcard ownership with explicit exports |
| Recurrence identity path change | Rename protected field or `investigate_first` path | Classifier/contract; recurrence event key builder; parsers; migration tools; exact-key tests; event/history artifacts | CG-6 finds two parsers, about 15 exact literals, and roughly 20 v2 migration surfaces | `recurrence:v1` embeds mutable file/field paths in identity | Do not implement v2 yet; add a read-only migration detector and alias-plan scaffold so path-only changes cannot be mistaken for new failures |
| Generated replay artifact refresh | Change semantic projection, recurrence state, drift output, or retention policy | Artifact manifest; dashboard/recurrence writers; paired JSON/Markdown outputs; trend windows; README/governance docs | CE top commits touched 25–30 replay files; CE6 registered 16 families / 111 tracked files | One semantic change can regenerate many review-visible mirrors and baselines | Enforce retention class in tooling; separate semantic acceptance artifacts from advisory mirrors; report generated-only diffs |
| Documentation path migration | Move audit, manifest, contract, or generated report | Writer, consumers, tests/CI, refresh commands, audit manifest, documentation inventory | 259 generator-owned and 24 test-owned records; path changes are deliberately cross-cutting | Paths encode provenance, reproducibility, and operational contracts | Add a path-contract registry/check; opportunistically migrate only when an owning workflow already changes |

## Repeated Edit Locations

| File | Repeated edit type | Related tests/docs | Likely cause | Candidate mitigation |
|---|---|---|---|---|
| `tests/test_ownership_registry.py` | New cycle locks, import/fan-in caps, registry records, inventory assertions | `tests/test_inventory_governance.json`, `tools/test_audit.py`, architecture ledger, CI | Default closeout destination for architecture work | Extract registry data and domain guard modules; keep one thin hard-fail aggregator |
| `game/final_emission_meta.py` | Metadata fields, normalization, fallback/owner registries, observability packaging | `tests/test_final_emission_meta.py`, replay projection, BU write-path ledger | Runtime feature additions and cross-layer observability contracts | Isolate stable schema/maps from packaging helpers; generate write-path evidence |
| `tests/helpers/golden_replay.py` | Assertion/orchestration changes, report bridge, drift/summary logic | Focused golden replay tests, protected manifest, dashboard report | Broad compatibility surface and normal-flow/failure-flow coordination | Expand facade use and move remaining assertion families to focused owners |
| `tests/helpers/failure_dashboard_report.py` | Renderers, artifact writers, compatibility exports | Dashboard, drift, recurrence, stability tests | Multiple report families share one operator entry point | Continue family extraction while keeping one stable facade; measure fan-in after each split |
| `tests/helpers/golden_replay_projection.py` | Assembly, protected field integration, runtime-lineage joins | Projection tests, manifest tool/doc, classifier sync | One acceptance row must reconcile all producer layers | Keep assembler, move policy into explicit field/source/precedence registries |
| `game/final_emission_replay_projection.py` | Fallback/source/owner maps and lineage event construction | Runtime-lineage, attribution, replay, scenario-spine tests | Multiple read-side policy families share one event builder | Split map contracts from event assembly without changing public builder |
| `tests/failure_classification_contract.py` | Allowed values, row fields, dashboard evidence manifest, investigation defaults | Classifier/sync/dashboard/attribution tests | Appropriate central contract plus imported runtime/projection vocabularies | Add authority annotations and generated consumer inventory; avoid duplicating values |
| `tests/helpers/failure_classifier.py` | Rule tables, owner/severity/source routing, investigation overrides | Classifier tests, dashboard probes, recurrence | Behavioral taxonomy authority | Keep explicit tables; derive probes and add concept-local parametrized tests |
| `tests/helpers/failure_classification_split_owner.py` | Matrix rows, FEM projection, expected dashboard/report values | BU15 report, matrix contract, classifier/dashboard/lineage tests | One row is required across multiple layers | Separate row data from adapters/rendering; generate all derived expectations |
| `replay_bug_recurrence_history.py` | Trend/forecast/lifecycle/governance taxonomies and analytics | Statistics, serialization, recurrence tests, history artifacts | Cohesive but broad second-order analytics | Extract taxonomy declarations/labels into one compact manifest |
| `replay_bug_recurrence_statistics.py` | Maturity, roadmap, effectiveness, completion, graduation thresholds | Serialization, trajectory history, recurrence tests | Program-level policy accumulated after base recurrence | Split only along stable policy families; preserve facade/API |
| `docs/testing/protected_replay_manifest.md` | Generated protected-field table and policy prose | Refresh tool, projection tests, ownership registry | Mixed human policy plus generated section | Keep mixed document but make generated boundary and source registry machine-verifiable |

### Edit recurrence classification

- **Mechanical:** manifest/table refreshes, generated JSON/Markdown pairs, inventory JSON, matrix reports.
- **Policy-driven:** owner/category/source maps, recurrence classes, retention classes, fan-in caps,
  protected corpus membership, investigation targets.
- **Test-driven:** exact row/schema/count locks, dashboard presentation goldens, projection precedence
  matrices, no-regrowth and import-boundary assertions.
- **Feature-driven:** new fallback families, ownership metadata, speaker evidence, attribution fields,
  runtime-lineage events.

The costly cases mix all four types in one commit. The safest redistribution target is therefore
editor routing and generation boundaries, not removal of the underlying parity checks.

## Owner Concentration Notes

- Every ranked hub has one distinct author name in its file history. The available history therefore
  provides no evidence of contributor-level redundancy for governance knowledge.
- Structural ownership is healthier than social ownership. CE and CG created focused modules and
  registries, but compatibility facades still concentrate review knowledge in the same maintainer.
- `tests/test_ownership_registry.py` is the strongest single-file knowledge concentration because it
  contains both present policy and historical cycle-specific implementation knowledge.
- Generated fixtures and reports concentrate operational knowledge: maintainers must know which files
  are canonical, generated mirrors, frozen baselines, or local-only. CE6 improved this with a manifest,
  but the distinction is still distributed across writers, tests, README text, and git tracking.
- Test suites are major governance owners, not merely consumers. The ownership registry, protected
  projection, classifier, dashboard, recurrence, and closeout contracts all live substantially under
  `tests/`.
- Low commit counts on June 25 split modules are not evidence of low maintenance burden. Their
  historical churn remains visible on the former facade/monolith path.

## Hotspot Concentration Assessment

**High**

Evidence:

- One file has 5,959 lines, 22 commits, 20 recent touches, and several unrelated governance domains.
- `game/final_emission_meta.py` has 35 commits and repeatedly co-changes with runtime projection and
  broad final-emission tests.
- Three replay compatibility/assembly hubs have 17–25 commits in a roughly six-week history.
- Ordinary failure-taxonomy changes still touch 4–5 surfaces; split-owner and protected-schema changes
  can touch 6+ surfaces plus generated documentation/artifacts.
- Residual recurrence analytics exceed 7,400 lines across two files and remain paired with a
  3,141-line broad test.
- All measured hubs have one distinct author.

The rating is below Severe because:

- golden replay and fallback tests were decomposed into focused owners;
- the dashboard and recurrence monoliths were split behind stable facades;
- failure classification now has explicit authority, recurrence, attribution, and key-stability
  registries;
- routing fixtures are increasingly derived;
- generated replay artifacts have retention classes;
- git history is complete enough to distinguish historical monolith churn from current ownership.

## Candidate Next Blocks

These are implementation candidates only; none are performed in CH.

1. **CH1 — Ownership registry contract extraction**
   - Move `ResponsibilityRecord`, `RESPONSIBILITY_REGISTRY`, index construction, and duplicate-name
     policy from `tests/test_ownership_registry.py` into an import-light contract module.
   - Keep the registry canonical and keep existing tests hard-fail.
   - Success: `tools/test_audit.py` no longer imports a test module; registry behavior is unchanged.

2. **CH2 — Ownership guard locality pilot**
   - Choose one contained family, preferably BV compatibility/fan-in caps or BN gate-context guards.
   - Move implementation beside its domain and leave one aggregator invocation in the central file.
   - Success: identical assertions and CI behavior with a measurable central-file reduction.

3. **CH3 — Protected field source/default authority matrix**
   - Implement the CF2 recommendation as executable data covering all 41 fields: source, normalized
     source, default, unavailable rule, drift bucket, and first owner test.
   - Success: manifest, classifier overlap, and projection validations derive from one matrix.

4. **CH4 — Runtime replay projection policy split**
   - Extract source-family maps, mutation maps, split-owner maps, and sealed-subkind inference from the
     event assembler behind stable imports.
   - Success: `build_fem_runtime_lineage_events()` output is unchanged and each map family has narrow
     contract tests.

5. **CH5 — Recurrence taxonomy manifest and test routing**
   - Create a compact executable registry for trend, forecast, cost, governance, lifecycle, confidence,
     graduation, and cross-map ownership.
   - Split only the broad recurrence test by contract family; do not change taxonomy or artifacts.
   - Success: a taxonomy rename has one declared authority and a smaller first-failure test surface.

6. **CH6 — Governance fanout metric**
   - Extend the read-only maintenance metrics approach to report per-concept consumers, co-change pairs,
     author concentration, generated artifact fanout, and median/max files touched.
   - Success: CD–CG hotspot claims can be regenerated rather than manually reconstructed.

7. **CH7 — Recurrence v1 migration detector**
   - Add a read-only check that flags changes to protected field paths or investigation targets that
     would alter existing recurrence keys.
   - Success: path-only refactors produce an explicit migration warning without implementing v2.

8. **CH8 — Documentation path-contract check**
   - Validate that new cycle authorities are in approved locations and indexed in `audit_manifest.md`,
     while exempting generator/test-owned pinned paths.
   - Success: no new root-level audit artifacts and no cosmetic movement of pinned evidence.

## Files to Pass Back

Highest-value files for further planning:

1. `docs/audits/CH_governance_hub_redistribution_discovery.md`
2. `CD_ownership_registry_concentration_audit_discovery.md`
3. `CE_golden_replay_concentration_audit_discovery.md`
4. `docs/audits/CF_replay_projection_responsibility_discovery.md`
5. `docs/audits/CG_failure_classification_synchronization_discovery.md`
6. `docs/audits/CG_failure_classification_cost_closeout.md`
7. `tests/test_ownership_registry.py`
8. `game/final_emission_meta.py`
9. `game/final_emission_replay_projection.py`
10. `tests/helpers/golden_replay.py`
11. `tests/helpers/golden_replay_projection.py`
12. `tests/helpers/golden_replay_projection_extractors.py`
13. `tests/failure_classification_contract.py`
14. `tests/helpers/failure_classifier.py`
15. `tests/helpers/failure_classification_split_owner.py`
16. `tests/helpers/replay_bug_recurrence_history.py`
17. `tests/helpers/replay_bug_recurrence_statistics.py`
18. `docs/audits/CG_failure_classification_authority_registry.md`
19. `docs/audits/CG_recurrence_taxonomy_registry.md`
20. `docs/audits/CG_recurrence_key_stability_review.md`
21. `docs/testing/protected_replay_manifest.md`
22. `tests/helpers/golden_replay_artifact_manifest.py`
23. `docs/audits/documentation_governance.md`


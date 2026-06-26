# CG — Failure Classification Synchronization Audit — Discovery

**Date:** 2026-06-25  
**Scope:** Discovery/audit only. No refactor, rename, taxonomy change, fixture refresh, or runtime behavior change was made.

## Scope

This audit traces the failure-classification ecosystem from replay failure detection through:

- classifier taxonomy and row construction;
- contract and synchronization helpers;
- attribution taxonomy;
- dashboard fixtures and rendering;
- recurrence key derivation, analytics, rendering, and committed artifacts;
- tests that lock exact values, schemas, report shapes, and cross-layer parity.

The primary metric is **Failure Classification Cost**: the number and type of repository surfaces that must be understood, edited, regenerated, or revalidated when a failure classification concept changes.

For this discovery pass, cost is measured through four observable components:

1. **Authority count** — independently maintained taxonomy or policy owners.
2. **Synchronization surface** — files that mirror, derive, validate, display, or fixture the same concept.
3. **Contract-lock surface** — tests and generated artifacts that intentionally fail when the concept changes.
4. **Historical edit fanout** — classification-related files changed together in git history.

### Current cost snapshot

| Measure | Current observation |
|---|---:|
| Core implementation/governance files measured | 11 |
| Core direct test files measured | 7 |
| Core implementation/governance LOC | 17,922 |
| Core direct test LOC | 7,653 |
| Combined measured core | **18 files / 25,575 LOC** |
| Public failure categories | 12 |
| Primary owners | 13 |
| Replay tags | 17 |
| Source-family tags | 21 |
| Classification row fields | 15 required + 48 optional = 63 |
| Dashboard evidence fields | 29 |
| Split-owner acceptance rows | 16 total; 15 dashboard-covered |
| Recurrence trend classes | 4 |
| Recurrence forecast classes | 4 |
| Recurrence remediation-cost classes | 4 |
| Recurrence lifecycle stages | 5 |

The LOC figure is not a defect score. It describes the amount of code directly participating in the measured contracts. The strongest cost evidence is historical fanout: a normal taxonomy or ownership change repeatedly touches the contract, classifier, sync helper, fixtures, dashboard, and tests together.

## Files inspected

### Primary implementation and governance

- `tests/failure_classification_contract.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/failure_classification_sync.py`
- `tests/helpers/failure_dashboard_fixtures.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/helpers/failure_dashboard_recurrence.py`
- `tests/helpers/attribution_contract.py`
- `tests/helpers/replay_drift_taxonomy.py`
- `tests/helpers/replay_bug_recurrence.py`
- `tests/helpers/replay_bug_recurrence_events.py`
- `tests/helpers/replay_bug_recurrence_history.py`
- `tests/helpers/replay_bug_recurrence_statistics.py`
- `tests/helpers/replay_bug_recurrence_serialization.py`
- `tests/helpers/golden_replay.py`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/replay_observed_row_fixtures.py`
- `tests/helpers/replacement_attribution_inventory.py`
- `game/attribution_read_views.py`
- `game/final_emission_meta.py`
- `game/final_emission_ownership_schema.py`
- `game/final_emission_replay_projection.py`

### Primary tests

- `tests/test_failure_classifier.py`
- `tests/test_failure_classification_contract.py`
- `tests/test_failure_dashboard_controlled_failures.py`
- `tests/test_failure_dashboard_report.py`
- `tests/test_failure_dashboard_recurrence.py`
- `tests/test_attribution_contract.py`
- `tests/test_replacement_attribution_inventory.py`
- `tests/test_replay_bug_class_recurrence.py`
- `tests/test_replay_drift_taxonomy.py`
- `tests/test_split_owner_acceptance_matrix_contract.py`
- `tests/test_recurrence_trajectory_history.py`

### Fixtures, generated data, and governance evidence

- `artifacts/golden_replay/bug_recurrence_event_log.json`
- `artifacts/golden_replay/bug_recurrence_session_diagnostic_event_log.json`
- `artifacts/golden_replay/bug_recurrence_history.json`
- `artifacts/golden_replay/bug_recurrence_history.md`
- `artifacts/golden_replay/recurrence_trajectory_history.json`
- `artifacts/golden_replay/artifact_manifest.md`
- `docs/audits/BU15_split_owner_acceptance_matrix.md`
- `audits/cycle_ak_replay_schema_authority_inventory.md`
- `audits/cycle_ak_replay_schema_maintenance_compression_closeout.md`
- `docs/audits/BQ35_recurrence_event_source_audit.md`
- `docs/audits/BQ36_recurrence_write_path_audit.md`
- `docs/audits/BQ37_recurrence_history_migration.md`
- `docs/audits/metrics/BS3_canonical_attribution_contract.md`

Archived dashboard documents and broad repository documents containing generic uses of “classification” were searched but excluded from the active cost total unless they still define or verify a live contract.

## Responsibility map

| Path | Role | Taxonomy relationship | Authority | Kind |
|---|---|---|---|---|
| `tests/failure_classification_contract.py` | Public failure-row taxonomy, allowed values, row schema, dashboard evidence manifest, investigation targets | Defines and validates | **Authoritative for replay failure row taxonomy**; derives runtime owner buckets and protected evidence overlap | Test-side governance code |
| `tests/helpers/failure_classifier.py` | Deterministic classification rules, owner/severity routing, row construction, row validation | Consumes contract; defines behavioral mapping | **Authoritative for classification behavior**, derived for allowed values | Test-side production-like helper |
| `tests/helpers/failure_classification_sync.py` | Cross-layer assertions, synthetic observed rows, drift-row builders, split-owner matrix, dashboard cases, report parity | Mirrors, validates, tests, and generates fixtures | Derived governance hub; split-owner matrix is authoritative for its own acceptance rows | Test helper/governance/fixture code |
| `tests/helpers/failure_dashboard_fixtures.py` | Controlled failure cases and expected classification fragments | Mirrors classifier outcomes and dashboard probes | Derived | Fixture helper |
| `tests/helpers/failure_dashboard_report.py` | Builds classified dashboard rows and renders failure reports | Consumes and displays taxonomy | Derived consumer; compatibility/re-export surface | Test-side report code |
| `tests/helpers/failure_dashboard_recurrence.py` | Orchestrates recurrence analytics and renders/writes recurrence reports | Displays several recurrence taxonomies | Derived orchestrator/display owner | Test-side report code |
| `tests/helpers/replay_drift_taxonomy.py` | Owner-drift buckets and drift classification | Defines a taxonomy consumed by classifier and recurrence | **Authoritative for owner-drift taxonomy** | Test-side governance code |
| `tests/helpers/attribution_contract.py` | Attribution fields, replacement paths, repair kinds, mutation classes, aliases, validation | Defines and validates attribution taxonomy; imports failure taxonomies | **Authoritative for attribution contract unions and normalization** | Test-side governance code |
| `game/attribution_read_views.py` | Read-side owner constants and owner-bucket registries | Defines runtime-derived ownership vocabulary consumed by failure contract | **Authoritative read-side source for split owners/buckets** | Production read view |
| `game/final_emission_meta.py` | Runtime FEM metadata and fallback owner-bucket registries | Defines runtime source taxonomy | Authoritative runtime metadata | Production code |
| `game/final_emission_ownership_schema.py` | Canonical split-owner schema | Defines selection/content ownership concepts | Authoritative runtime ownership schema | Production code |
| `game/final_emission_replay_projection.py` | Projects runtime lineage into replay/attribution evidence | Consumes and emits attribution/classification vocabulary | Derived runtime read-side projection | Production code |
| `tests/helpers/golden_replay_projection.py` | Protected observation field registry and projection | Defines protected evidence paths used by failure contract | **Authoritative for protected observation schema** | Test-side acceptance code |
| `tests/helpers/golden_replay.py` | Produces drift rows and invokes classification/reporting | Consumes taxonomy | Derived integration consumer | Test-side replay runner |
| `tests/helpers/replay_bug_recurrence_events.py` | Recurrence key, owner/status, source buckets, persistence lanes, event log aggregation | Defines base recurrence contract | **Authoritative for recurrence identity and event/status vocabulary** | Test-side governance code |
| `tests/helpers/replay_bug_recurrence_history.py` | Trend, forecast, remediation cost, governance, and lifecycle classifications | Defines multiple downstream recurrence taxonomies | **Authoritative for recurrence analytical classifications** | Test-side analytics code |
| `tests/helpers/replay_bug_recurrence_statistics.py` | Effectiveness, maturity, roadmap, and graduation calculations | Consumes and cross-maps recurrence taxonomies | Derived analytics, with some policy constants | Test-side analytics code |
| `tests/helpers/replay_bug_recurrence_serialization.py` | Confidence/graduation/outcome classifications and report serialization | Defines/consumes recurrence governance taxonomies | Mixed authority and derived serialization | Test-side analytics/report code |
| `tests/helpers/replay_bug_recurrence.py` | Compatibility facade re-exporting recurrence modules | Mirrors API surface | Derived compatibility facade | Test helper |
| `artifacts/golden_replay/bug_recurrence_*.json|md` | Checked-in event/history/report snapshots | Mirrors displayed/serialized taxonomy | Generated/derived evidence | Generated data |
| `docs/audits/BU15_split_owner_acceptance_matrix.md` | Checked-in rendering of split-owner matrix | Mirrors matrix rows exactly | Generated/derived governance document | Documentation/generated |

### Authority conclusion

There is no single authority for “failure classification” as a whole. Authority is intentionally partitioned:

- failure row vocabulary: `failure_classification_contract.py`;
- classification behavior: `failure_classifier.py`;
- protected evidence schema: `golden_replay_projection.py`;
- runtime ownership vocabulary: `game` read views/schema;
- owner-drift taxonomy: `replay_drift_taxonomy.py`;
- attribution unions/normalization: `attribution_contract.py`;
- recurrence identity/status: `replay_bug_recurrence_events.py`;
- recurrence analytical classifications: `replay_bug_recurrence_history.py`.

The partition is defensible, but the boundaries are not consistently explicit. In particular, `failure_classification_sync.py` carries both synchronization logic and a large amount of fixture/matrix policy, while recurrence modules introduce several second-order classification systems without one compact taxonomy registry.

## Synchronization edges

| Repeated concept | Files | Intentional? | Likely edit set |
|---|---|---|---|
| Failure categories | Contract, classifier `CATEGORY_RULES`, primary/secondary owner maps, investigation targets, sync assertions, controlled fixtures, classifier/contract tests, dashboard output | Yes: vocabulary vs behavior vs probes | Add/rename/remove normally requires contract + classifier rule/maps + sync expectations + targeted fixtures/tests; dashboard may change if output is exposed |
| Primary/secondary owners | Contract, classifier owner maps, controlled fixtures, recurrence owner projection, dashboard columns/tests | Yes | Contract + classifier + expected fixture rows + recurrence-key review if primary owner changes |
| Source-family tags | Contract, classifier rules, attribution contract validator, attribution inventory/tests | Yes, but crosses two contracts | Contract + classifier rule + attribution compliance expectations |
| Investigation target paths | Contract `MAJOR_OWNER_INVESTIGATION_TARGETS`, classifier `INVESTIGATION_TARGETS` and overrides, fixtures, recurrence key | Partly intentional | Contract + classifier + exact-string tests + recurrence migration decision because `investigate_first` is embedded in `recurrence:v1` keys |
| Classification row fields | Contract required/optional sets, classifier `TypedDict`, classifier output, sync introspection, dashboard evidence manifest, tests | Intentional and strongly synchronized | Contract + `TypedDict`/builder + sync test; dashboard manifest/render/tests if displayed |
| Protected classifier evidence | Golden replay projection registry, failure contract derived overlap, classifier direct/computed partition, sync assertions | Intentional derivation | Projection registry + classifier partition/build path + tests; manifest count locks currently expect 32 protected and 16 extension fields |
| Dashboard evidence fields/labels | Contract manifest, report re-exports/rendering, sync checks, exact evidence-cell fixtures | Intentional | Contract manifest + report behavior + controlled evidence strings/tests |
| Fallback owner buckets | Runtime ownership/meta/read views, failure contract aliases, classifier validation, split-owner matrix, fixtures, attribution union, lineage projection/tests | Intentional cross-layer contract | Runtime registry + projection + contract + sync matrix + classifier/dashboard probes + attribution tests |
| Repair kinds | Failure contract runtime/producer/legacy sets, attribution contract union/aliases, classifier evidence, runtime lineage projection, fixtures/tests | Intentional but split authority | Producer/runtime source + failure contract subset + attribution union/aliases + classifier/attribution tests |
| Mutation classification | Attribution contract core union plus emission sublayers, classifier mutation source/sublayer, lineage events, attribution inventory/tests | Intentional, semantically overloaded | Attribution contract + producer/projection + classifier expectations + inventory tests |
| Owner-drift bucket | Drift taxonomy, failure contract allowed values, classifier row, recurrence key prefix, drift/recurrence tests | Intentional | Drift taxonomy + classifier contract/validation + recurrence key compatibility/migration + fixtures/tests |
| Recurrence key | Event module, attribution shape validator, committed event/history artifacts, recurrence tests | Intentional | Key builder + validator + migration/backfill tools + event/history artifacts + many exact-key tests |
| Recurrence status | Event input statuses (`active`, `retired`) and summary status (`active`, `watch`, `retired`) | Intentional two-stage vocabulary | Event logic + summary logic + rendering + exact-status tests |
| Trend / forecast / lifecycle | History module constants and classifiers, statistics alignment maps, recurrence renderer, JSON/MD artifacts, recurrence tests | Intentional but repeated across analytics/display | History taxonomy + statistics mappings + rendering labels/counts + exact tests + artifact refresh |
| Split-owner matrix row | Sync matrix, FEM projection, classifier builder, dashboard fixture generation, checked-in matrix report, CI/check scripts, several tests | Intentional governance matrix | Matrix row + any runtime projection support + generated report + classifier/dashboard/lineage tests |

### Highest-risk synchronization edge

`investigate_first` is simultaneously:

- user-facing dashboard guidance;
- an exact-string fixture expectation;
- a classifier policy result;
- one component of `recurrence:v1:<owner_bucket>|<category>|<field_path>|<investigate_first>`.

A path rename that looks documentation-only can therefore change recurrence identity. This is the clearest boundary-tightening candidate.

### Existing synchronization protections

Cycle AK reduced several former hand-maintained lists:

- protected evidence overlap is derived from the protected observation registry;
- dashboard evidence keys are contract-owned and re-exported;
- classifier `TypedDict` fields are compared with contract sets;
- direct observed evidence copying is manifest-driven;
- cross-layer mismatches are reported by `assert_contract_classifier_alignment()`.

These are good protections. They reduce silent drift, but they do not reduce the number of deliberately coupled surfaces that must be reviewed.

## Multi-file edit evidence

Git history was inspected for the core classifier, contract, sync, dashboard, attribution, recurrence, tests, and committed recurrence artifacts.

### Most common core co-change pairs

| Files changed together | Commits |
|---|---:|
| `failure_classification_contract.py` + `failure_classifier.py` | 12 |
| `failure_classification_contract.py` + `failure_dashboard_report.py` | 9 |
| `failure_classifier.py` + `failure_dashboard_report.py` | 8 |
| `failure_classification_contract.py` + `failure_classification_sync.py` | 7 |
| `failure_classification_sync.py` + `failure_dashboard_report.py` | 7 |
| `failure_classification_sync.py` + `failure_dashboard_fixtures.py` | 6 |
| `failure_classification_sync.py` + `failure_classifier.py` | 5 |
| `failure_classification_contract.py` + `failure_dashboard_fixtures.py` | 4 |
| `failure_dashboard_fixtures.py` + `failure_dashboard_report.py` | 3 |

### Representative commits

| Commit | Classification-related files | Change type | Evidence |
|---|---:|---|---|
| `98bc059` — Failure Classification Dashboard | 6 core implementation/test files | Initial behavioral + schema + dashboard + tests | Established the recurring contract/classifier/report/test bundle |
| `a5c9146` — contract fallback ownership and mutation lineage | 6 core implementation/test files, plus runtime/projection files | Behavioral taxonomy expansion | New ownership/lineage concepts required contract, classifier, dashboard, and exact tests |
| `0ef46f3` — reduce maintenance locality fanout | 7 core implementation/test files | Governance/consolidation | Even a locality-reduction change itself crossed contract, sync, classifier, report, and tests |
| `43de427` — Replay Schema Maintenance Compression | 6 core implementation/test files | Governance/sync-helper consolidation | Added derived manifests and locks; reduced list duplication but preserved co-review |
| `6210a5d` — Replay Drift Classification | 5 core classification files plus drift modules/tests | Behavioral taxonomy addition | Owner-drift taxonomy propagated into classifier/report/contracts |
| `22cd49a` — Post-BJ Fan-In / Fan-Out Validation | 7 core classification/fixture/test files | Governance + fixture/matrix expansion | Split-owner matrix added 1,413 lines to sync helper and 843 lines to classifier tests |
| `adc374b` — Semantic Replacement Attribution Completeness | 4 core contract/classifier/attribution/test files | New attribution contract + behavioral projection | Failure taxonomy became an input to a second contract |
| `7651237` — Maintenance Economics Validation Closeout | 6 core classification/fixture/test files | Small governance correction | Only 16 changed lines across four implementation files, showing a small semantic correction still had four-file fanout |
| `3f5ee0c` — Recurrence History Population | report, recurrence test, and three generated artifacts | Behavioral/report + generated data refresh | Recurrence changes co-move with checked-in JSON/MD evidence |
| `66b8b32` — Golden Replay Concentration Audit | 7 recurrence/report modules plus recurrence test | Structural extraction | Split a 2,900-line report hub into five recurrence modules; reduced concentration, not taxonomy count |

### Observed edit pattern

The common pattern is:

1. add or alter a classifier concept;
2. allow it in the public contract;
3. map it in classifier rules/owners/targets;
4. add or alter synthetic observed/drift builders;
5. update controlled fixture expectations;
6. update exact classifier/dashboard tests;
7. if recurrence identity or analytics are affected, update recurrence tests and refresh committed artifacts.

For ordinary classifier changes, the observed core fanout is typically **3–7 files**. Split-owner changes can exceed that because the same row must be valid in runtime projection, lineage, classifier, dashboard, generated matrix documentation, and CI checks.

### Governance-only versus behavioral changes

- **Governance-only:** AK, AO, BL, BV examples mainly changed derivation, sync checks, or ownership without intended behavior changes. They still touched 2–7 core files.
- **Fixture/test updates:** AL, AX, BG, BU heavily changed fixtures and exact expectations; BU is the strongest evidence of fixture-governance cost.
- **Behavioral taxonomy changes:** C, D, I, P, AR, BS touched classifier behavior and contract vocabulary together.
- **Generated artifact updates:** AY/BQ/CE recurrence work changed report code/tests and committed history/report artifacts.

## Test and fixture dependencies

| Path | Dependency | Assertion type | Assessment |
|---|---|---|---|
| `tests/test_failure_classification_contract.py` | Categories, owners, row fields, evidence counts, dashboard manifest, bucket values, exact validation errors | Schema, exact sets/counts/strings, sync | Appropriately contract-like, but count locks require edits for additive safe changes |
| `tests/test_failure_classifier.py` | Category/owner/severity/source routing, investigation paths, repair kinds, split owners, lineage | Behavioral and many exact strings/dicts | Necessary behavioral coverage; large and high-touch |
| `tests/test_failure_dashboard_controlled_failures.py` | Every controlled case, evidence cell, matrix parity, protected paths | Exact dashboard shape and exact rendered evidence | Strong regression lock; brittle by design for presentation changes |
| `tests/helpers/failure_dashboard_fixtures.py` | Expected category/owner/severity/target/evidence for base and generated cases | Fixture mirror of classifier output | Derived but manually dense; ordinary classifier changes often require updates |
| `tests/helpers/failure_classification_sync.py` | Contract parity, builder parity, matrix counts, generated report equality | Cross-layer schema and governance | Valuable, but combines too many responsibilities |
| `tests/test_failure_dashboard_report.py` | Report rows, recurrence persistence lanes, statuses, event metadata, artifact output | Exact schema/report/recurrence behavior | Contract-like; couples report tests to recurrence infrastructure |
| `tests/test_failure_dashboard_recurrence.py` | JSON/MD paths and payload shape | Artifact/report shape | Appropriate focused extraction after CE |
| `tests/test_attribution_contract.py` | Owner/source/repair/mutation taxonomies, aliases, recurrence key shape, replacement path count | Exact taxonomy and normalization | Appropriate contract lock; replacement-path count is intentionally brittle |
| `tests/test_replacement_attribution_inventory.py` | Classifier-to-attribution projection and mutation classifications | Behavioral and exact taxonomy strings | Necessary integration lock; expands classifier change surface |
| `tests/test_replay_bug_class_recurrence.py` | Key identity, statuses, trend/forecast/cost/lifecycle classes, persistence, reports, governance | Behavioral, schema, exact strings and thresholds | Comprehensive but very large; any recurrence taxonomy change has broad test impact |
| `tests/test_replay_drift_taxonomy.py` | Owner-drift bucket classifications and failure-row validity | Behavioral and schema | Appropriate contract bridge |
| `tests/test_split_owner_acceptance_matrix_contract.py` | 16-row matrix, 15 projections/probes, generated report | Exact matrix/report parity | Appropriate governance lock; guarantees multi-surface edits |
| `artifacts/golden_replay/bug_recurrence_history.json` | Serialized analytical classifications and definitions | Generated snapshot | Intentionally derived; should refresh only for intentional governance changes |
| `artifacts/golden_replay/bug_recurrence_history.md` | Human-readable taxonomy and counts | Generated display snapshot | Intentionally derived; adds review noise to taxonomy changes |

### Brittle versus contract-like

Most exact assertions are deliberately contract-like, not accidental brittleness. The cost issue is not that they exist; it is that several layers assert the same concept in different forms:

- set membership;
- classifier output;
- synthetic expected dictionary;
- dashboard evidence string;
- recurrence key or analytical class;
- generated JSON/Markdown.

The weakest-value duplication is exact expected classifier fragments repeated in fixtures and tests when the sync matrix already has enough information to derive them. The highest-value locks are row-schema parity, key stability, and generated-report parity.

## Hotspots

### 1. `tests/helpers/failure_classification_sync.py` — very high burden

- **2,282 LOC; 12 historical commits.**
- Mixes taxonomy synchronization, row-shape introspection, synthetic observed rows, drift builders, split-owner acceptance data, FEM projection adapters, dashboard expected rows, report rendering, count locks, and CI assertions.
- Centralizes governance effectively, but has become a second behavioral/fixture hub.
- A split-owner row can affect matrix data, lineage, projection, classifier, dashboard, report text, and tests through this file.

**Judgment:** highest next-block candidate. Consolidation should clarify internal ownership, not remove parity checks.

### 2. `tests/helpers/replay_bug_recurrence_history.py` — very high burden

- **3,066 LOC** after CE extraction.
- Owns trend, forecast, remediation cost, governance status, and lifecycle taxonomies plus classifiers.
- Several concepts intentionally overlap (`emerging/recurring/persistent/dormant` appear in trend and lifecycle).
- Display and statistics modules consume these values through broad imports.

**Judgment:** appropriate analytics owner, but taxonomy declarations and cross-maps need a compact authority boundary.

### 3. `tests/helpers/replay_bug_recurrence_statistics.py` — very high burden

- **4,337 LOC**, largest measured implementation file.
- Consumes recurrence classes and defines effectiveness, maturity, roadmap, and graduation policy.
- Changes to analytical classifications may require alignment-map and score-policy review here even when base recurrence identity is unchanged.

**Judgment:** high maintenance surface; not the first classifier block, but central to recurrence contract cleanup.

### 4. `tests/test_replay_bug_class_recurrence.py` — very high burden

- **3,141 LOC**.
- Locks base keys, source lanes, statuses, trends, forecasts, remediation, lifecycle, governance, and graduation behavior.
- Broadly appropriate but makes any recurrence taxonomy edit expensive to validate and review.

**Judgment:** test decomposition by recurrence contract family would improve locality without weakening assertions.

### 5. `tests/helpers/failure_classifier.py` — high burden

- **995 LOC; 13 historical commits.**
- Behavioral authority for categories, owners, severity, source family, evidence derivation, and investigation routing.
- Explicit rule tables are reviewable and should not be mechanically hidden.
- Still mirrors contract concepts and participates in the most frequent co-change pair.

**Judgment:** behavior belongs here; authority comments and narrower policy tables would reduce ambiguity more safely than refactoring logic first.

### 6. `tests/test_failure_classifier.py` — high burden

- **1,951 LOC; 18 historical commits.**
- Exact behavioral coverage for many fallback families and split-owner rows.
- Ordinary classifier changes commonly require updates here even when fixtures already cover the same case.

**Judgment:** identify matrix-derived cases that can rely on parameterized canonical expectations rather than bespoke duplicate assertions.

### 7. `tests/failure_classification_contract.py` — high-impact, appropriately centralized

- **412 LOC; 14 historical commits.**
- Correct home for allowed values, row schema, and dashboard evidence manifest.
- Imports runtime/read-side owner registries and protected projection fields, so it is authoritative only for the composed replay contract.
- Count assertions and downstream imports make additive changes intentionally visible.

**Judgment:** keep central; clarify which values are owned here versus re-exported from runtime or projection authorities.

### 8. `tests/helpers/failure_dashboard_fixtures.py` — medium-high burden

- **512 LOC; 8 historical commits.**
- Base controlled cases duplicate exact classifier outputs; 15 split-owner cases are already generated from the sync matrix.
- Forces dashboard and test updates for many ordinary classifier routing changes.

**Judgment:** best dashboard fixture decoupling target. Preserve a small set of presentation-specific golden probes; derive the rest.

### 9. `tests/helpers/attribution_contract.py` — medium-high boundary risk

- **647 LOC**, introduced as one large contract block.
- Correctly centralizes attribution unions and aliases.
- Imports failure contract sets, so a failure taxonomy change can alter attribution validity and maturity scores.
- `mutation_classification` includes emission sublayers, joining two differently motivated vocabularies.

**Judgment:** boundary tightening is warranted before further taxonomy growth.

### 10. `tests/helpers/failure_dashboard_recurrence.py` — medium-high display burden

- **1,845 LOC** after extraction.
- Does not define base recurrence identity, but renders many downstream taxonomies and writes multiple artifacts.
- Any renamed class requires display text and snapshot review.

**Judgment:** keep orchestration separate; consider manifest-driven labels only after recurrence authority is clarified.

## Risks

1. **Recurrence identity instability.** `investigate_first` is part of the recurrence key. File-path or ownership-routing changes can create new keys without a semantic failure-class change.
2. **Authority ambiguity.** Failure contract, runtime ownership registries, drift taxonomy, attribution contract, and recurrence modules each own part of the vocabulary. Re-exports can look authoritative when they are derived.
3. **Sync-helper concentration.** A helper intended to detect drift now also owns major fixture and matrix construction.
4. **Dashboard fixture amplification.** Exact expected dictionaries and evidence strings turn classifier routing changes into fixture churn.
5. **Second-order taxonomy growth.** Recurrence has status, summary status, trend, forecast, cost, governance, lifecycle, confidence, graduation, and outcome classifications. These are legitimate domains, but their relationship is distributed.
6. **Generated artifact churn.** Intentional recurrence changes can require JSON, Markdown, event-log, and trajectory-history review.
7. **Broad-import coupling.** Recurrence facade and history modules use broad re-export/import patterns, obscuring which module owns a constant.
8. **Count-lock friction.** Exact counts such as 32 protected evidence fields, 16 extension fields, 29 dashboard fields, 16 matrix rows, and 9 replacement paths catch drift but ensure additive changes require governance edits.
9. **Test duplication.** Some split-owner and controlled-probe behavior is asserted through matrix checks, classifier tests, dashboard tests, and report equality.
10. **Metric blind spot.** Existing replay maintenance metrics measure LOC, imports, and touches, but do not isolate taxonomy-specific fanout or generated-artifact refresh cost.

## Recommended next blocks

### CG-1 — Taxonomy authority clarification

Document a field-level authority registry for:

- failure category;
- owner and owner-drift bucket;
- source family;
- repair kind;
- mutation classification;
- investigation target;
- recurrence identity/status/trend/forecast/lifecycle.

The block should label each authority as runtime, replay contract, attribution contract, recurrence analytics, or display-only. No behavior change is required.

### CG-2 — Sync-helper responsibility split

Separate, without changing behavior:

- contract/classifier introspection and parity checks;
- synthetic observed/drift row builders;
- split-owner matrix data and projection;
- generated matrix report verification.

The goal is not fewer checks. It is smaller edit domains and clearer reviewer routing.

### CG-3 — Dashboard fixture decoupling

Classify controlled cases into:

- behavior probes derived from canonical matrix/rule inputs;
- dashboard presentation goldens that must retain exact evidence strings;
- compatibility probes.

Derive expected category/owner/target values where an existing authority already supplies them. Keep only a small explicit presentation-golden set.

### CG-4 — Recurrence classification contract cleanup

Create a compact recurrence taxonomy authority or manifest covering:

- input and summary statuses;
- trend classes;
- forecast classes;
- remediation cost;
- governance status;
- lifecycle stage;
- cross-class alignment maps.

Preserve the current analytical behavior. Replace broad ownership ambiguity with explicit imports and documented derivation.

### CG-5 — Attribution contract boundary tightening

Clarify which attribution values are:

- direct producer facts;
- replay-classifier inference;
- emission-sublayer display values;
- legacy aliases.

Review whether `ALLOWED_MUTATION_CLASSIFICATIONS = core | emission_sublayers` should remain a union contract or become two explicitly validated fields. Do not change runtime stamping until corpus evidence supports it.

### CG-6 — Recurrence key stability review

Evaluate a future `recurrence:v2` identity that does not embed mutable file paths, or explicitly declare path changes as key migrations. This block should begin as an audit/migration design, not an implementation.

### CG-7 — Classification-cost metric closeout

Add a read-only metric that reports:

- taxonomy authorities;
- direct consumers;
- sync/fixture/test/generated surfaces;
- historical co-change pair counts;
- median and maximum core-file fanout for taxonomy commits;
- generated artifact count;
- per-concept “change one classification, update N files” estimate.

Suggested initial baseline:

- ordinary failure taxonomy change: **3–7 core files**;
- split-owner classification change: **6+ core/governance surfaces**, often plus runtime and generated report;
- recurrence analytical class change: **3–6 code/test files**, often plus checked-in JSON/Markdown artifacts.

## Files to pass back to ChatGPT

### Minimum set for classifier/synchronization follow-up

- `tests/failure_classification_contract.py`
- `tests/helpers/failure_classifier.py`
- `tests/helpers/failure_classification_sync.py`
- `tests/helpers/failure_dashboard_fixtures.py`
- `tests/helpers/failure_dashboard_report.py`
- `tests/test_failure_classification_contract.py`
- `tests/test_failure_classifier.py`
- `tests/test_failure_dashboard_controlled_failures.py`

### Add for attribution-boundary analysis

- `tests/helpers/attribution_contract.py`
- `tests/helpers/replacement_attribution_inventory.py`
- `tests/test_attribution_contract.py`
- `tests/test_replacement_attribution_inventory.py`
- `game/attribution_read_views.py`
- `game/final_emission_replay_projection.py`

### Add for recurrence-contract analysis

- `tests/helpers/replay_bug_recurrence_events.py`
- `tests/helpers/replay_bug_recurrence_history.py`
- `tests/helpers/replay_bug_recurrence_statistics.py`
- `tests/helpers/replay_bug_recurrence_serialization.py`
- `tests/helpers/failure_dashboard_recurrence.py`
- `tests/test_replay_bug_class_recurrence.py`
- `tests/test_failure_dashboard_recurrence.py`
- `artifacts/golden_replay/bug_recurrence_history.json`
- `artifacts/golden_replay/bug_recurrence_history.md`

### Add for runtime owner/split-owner changes

- `game/final_emission_meta.py`
- `game/final_emission_ownership_schema.py`
- `game/attribution_read_views.py`
- `game/final_emission_replay_projection.py`
- `docs/audits/BU15_split_owner_acceptance_matrix.md`
- `tests/test_split_owner_acceptance_matrix_contract.py`


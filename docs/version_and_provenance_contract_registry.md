# Version and Provenance Contract Registry

This registry centralizes repository versioning and provenance-sensitive
architectural contracts. It is documentation-only. It does not introduce new
versioning behavior, alter provenance generation, change replay schemas, update
runtime behavior, modify backend or gameplay behavior, or move executable
authority into documentation.

## Registry Scope

Version and provenance contracts are the surfaces where repository artifacts
declare lineage, schema version, replay sensitivity, generated-artifact origin,
or compatibility lifetime. The authoritative implementations remain in their
existing code, test helpers, scripts, generated-artifact manifests, and manual
planning registers.

Future architectural evolution should update this registry when a versioned
field, provenance key, replay-sensitive schema, generated-artifact lineage, or
compatibility lineage changes.

## Contract Inventory

| Contract ID | Contract | Canonical Owner | Authoritative Implementation | Repository Location | Purpose | Consumers | Versioning Policy | Provenance Requirements | Replay Implications | Compatibility Expectations | Verification Method | Future Extensibility Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| VPCR-01 | Protected replay scenario and field manifest contract | Protected replay acceptance owner | Protected scenario registry, protected observation registry, manifest renderer | `docs/testing/protected_replay_manifest.md`, `tests/helpers/protected_replay_registry.py`, `tests/helpers/golden_replay_projection_fields.py`, `tests/helpers/golden_replay_projection_manifest.py`, `tools/refresh_protected_replay_manifest.py` | Declare protected replay scenarios and generated protected observation field paths. | CI convergence checks, protected replay reviewers, replay-governance docs. | Manifest prose is manual; protected field table is generated from executable registry data and refreshed with the existing tool. | Manifest must distinguish manual scenario policy from generated field lineage. | High. Field-path or scenario-status changes affect replay acceptance. | Preserve protected/advisory distinction and field drift buckets until an approved replay package changes them. | `python tools/refresh_protected_replay_manifest.py --check`; protected golden replay lane when fields/scenarios change. | A future generated appendix may expose the field table, but the registry remains executable. |
| VPCR-02 | Golden replay projection schema contract | Golden replay projection owner | Projection helper and protected field registry | `tests/helpers/golden_replay_projection.py`, `tests/helpers/golden_replay_projection_fields.py`, `tests/helpers/golden_replay_projection_registry.py` | Project runtime payloads into observed replay rows and classifier-evidence inputs. | Golden replay tests, failure classifiers, protected replay manifests, recurrence/stability reports. | Stable unversioned projection shape with executable protected fields; field changes require manifest refresh. | Reads runtime provenance metadata but does not author runtime provenance. | High. Projection drift changes protected observation meaning. | Keep protected acceptance projection separate from runtime diagnostic lineage projection. | Golden replay projection tests and protected manifest check. | Future projection schema versioning should be explicit before alternate replay formats are introduced. |
| VPCR-03 | Realization fallback-family provenance contract | Realization provenance owner | Realization provenance helpers and authority profiles | `game/realization_provenance.py`, `game/realization_authority.py` | Normalize and stamp governed `realization_fallback_family` provenance. | Final Emission metadata, replay projection, provenance tests, split-owner/governance reviewers. | Stable unversioned taxonomy; additions require provenance-owner review. | `realization_fallback_family` is governed provenance and must remain distinct from diegetic `fallback_family_used`. | High. Fallback-family provenance is replay-observed. | Preserve the dual-field compatibility contract until a retirement package proves safe. | Focused realization/final-emission provenance tests and compatibility register review. | Future provenance taxonomy versions should include explicit migration and replay impact notes. |
| VPCR-04 | Final Emission metadata and provenance packaging contract | Final Emission metadata owner | Final Emission metadata read/write helpers | `game/final_emission_meta.py`, `game/final_emission_meta_read.py`, `game/final_emission_meta_observability.py` | Package `_final_emission_meta`, producer attribution, fallback metadata, and mutation lineage. | Final Emission gate, replay projection, runtime lineage projection, failure dashboard, protected replay. | Stable unversioned metadata key set; contract-version fields may be carried for specific subcontracts. | Provenance keys must identify source, owner, repair, or mutation lineage without selecting runtime behavior. | High. Finalized metadata is replay-observed and diagnostic-critical. | Preserve current compatibility keys and owner-bucket fields until separately retired. | Final Emission metadata tests, split-owner checks, protected replay focused tests when touched. | Future metadata schema versions should be published through an approved contract package. |
| VPCR-05 | Runtime lineage event vocabulary contract | Runtime lineage owner | Read-side lineage vocabulary and FEM projection | `game/runtime_lineage_telemetry.py`, `game/final_emission_replay_projection.py` | Derive countable diagnostic lineage events from finalized FEM. | Recurrence reports, failure dashboard, replay diagnostics, stability reporting. | Stable unversioned event/stage vocabulary. | Events must identify projection owner, content/prose owner where available, and recurrence keys without rewriting source metadata. | Medium to high. Diagnostic lineage is replay-adjacent and may drive recurrence analysis. | Do not merge runtime diagnostic lineage with protected replay acceptance schema. | Runtime lineage tests, final-emission projection tests, recurrence/stability report tests. | A future lineage schema version should include event-kind/stage migration rules. |
| VPCR-06 | Upstream fast-fallback provenance packaging contract | Upstream fallback provenance owner | Provenance packaging and containment helpers | `game/fallback_provenance_debug.py`, `game/final_emission_meta.py` | Preserve selector-boundary fingerprints, `metadata["fallback_provenance"]`, and FEM `fallback_provenance_trace`. | Final Emission gate, retry/fallback diagnostics, runtime lineage projection. | Stable unversioned provenance payload. | Provenance must be copied/merged non-destructively and must not become owner-bucket assignment by itself. | High when fallback paths are replayed or classified. | Historical module name is retained for compatibility; do not rename without migration. | Focused fallback provenance tests and final-emission replay projection checks. | Future packaging changes should name the provenance payload version and compatibility plan. |
| VPCR-07 | Runtime schema normalization and compatibility lineage contract | Schema contracts owner | Runtime schema normalizers and legacy adapters | `game/schema_contracts.py`, `docs/compatibility_residue_register.md` | Normalize runtime payload shapes and park compatible legacy fields. | Runtime boundaries, ruleset contracts, compatibility planning, replayed historical payloads. | Stable unversioned helper contracts. | Unknown legacy metadata must remain explanatory unless a domain owner consumes it explicitly. | Medium. Historical payload normalization can affect replay and persisted data behavior. | Legacy adapters remain active until evidence-driven retirement is approved. | `tests/test_schema_contracts.py`, `tests/test_runtime_schema_boundaries.py`, compatibility register review. | Future schema-version fields should be explicit and paired with adapter retirement criteria. |
| VPCR-08 | Non-combat framework version contract | Non-combat resolution owner | Non-combat classification and normalization framework | `game/noncombat_resolution.py::NONCOMBAT_FRAMEWORK_VERSION` | Version canonical non-combat outcome normalization and resolver attachment. | API action flow, CTIR/prompt adapter, ruleset contract registry, replay-adjacent tests. | Explicit version: `2026.04.noncombat.v1`. | Outcome metadata may explain authority and domain routing but does not own realization provenance. | High. Non-combat outcomes may be replay-observed. | Preserve fail-closed ambiguous/unsupported behavior until a versioned successor is approved. | `tests/test_noncombat_resolution.py`, `tests/test_noncombat_runtime_integration.py`, CTIR tests. | Future ruleset expansion should bump or explicitly retain the framework version. |
| VPCR-09 | Contract metadata publication contract | Contract registry owner | Metadata-only contract registry | `game/contract_registry.py`, `docs/backend_contract_registry.md`, `docs/ruleset_contract_registry.md` | Index planner/prompt projection keys and contract metadata without publishing backend or ruleset behavior. | Prompt/projection maintainers, backend/ruleset registry reviewers, generated documentation planning. | Registry rows may carry version keys, but publication requires package approval. | Metadata must document contract surfaces only; provenance generation remains with runtime owners. | Low to medium depending on referenced contract. | Do not treat documentation rows as executable contract enforcement. | Contract registry/static drift tests where present; link/source review. | Future backend/ruleset/version registries should publish explicit ids and version status. |
| VPCR-10 | Generated documentation and artifact lineage contract | Governance/generated-doc owner | Generated-doc strategy, artifact manifest, refresh scripts | `docs/generated_documentation_appendices.md`, `tests/helpers/golden_replay_artifact_manifest.py`, `docs/audits/CF6_generated_projection_artifact_governance.md`, `tools/refresh_protected_replay_manifest.py`, `scripts/split_owner_acceptance_matrix_ops.py` | Distinguish generated outputs from canonical executable sources and retained evidence. | Reviewers, governance workflow, protected replay evidence, audit reports. | Generated artifacts use the source/version fields provided by their generator or manifest family; manual docs name source and refresh trigger. | Generated outputs must identify source or generator lineage and should not become semantic authority. | Medium to high for protected replay artifacts. | Do not hand-edit generated sections or historical retained evidence. | Existing generator checks, manifest tests, and source-reference review. | Future generated appendices should add a source registry before emitting new generated rows. |
| VPCR-11 | Replay governance record and decision contract | Replay governance owner | Replay governance contract and registry | `tests/replay_governance_contract.py`, `tests/replay_governance_registry.py`, `docs/testing/replay_governance_contract.md`, `docs/testing/replay_governance_registry.md` | Define replay governance decision vocabulary and record shape. | Replay governance tests, protected replay reviewers, traceability docs. | Stable unversioned record shape. | Governance records document decision lineage and must not invent replay policy in prose. | High for governance review, indirect for runtime replay. | Keep acceptance sets, classifier taxonomy, and governance records in their separate owner files. | `python -m pytest tests/test_replay_governance_contract.py -q` plus focused registry tests. | Future decision-schema versioning should be explicit before changing record keys. |
| VPCR-12 | Stability and reporting schema contract | Stability reporting owner | Stability reporting contract and sync helpers | `tests/stability_reporting_contract.py`, `tests/helpers/stability_reporting_sync.py` | Define schema fields for stability scorecards, trend reports, hotspots, ownership, and lineage summaries. | Long-session stability tools, failure dashboard, regression reviewers. | Explicit `STABILITY_REPORTING_SCHEMA_VERSION = 1`. | Reports may summarize lineage and ownership but do not author runtime provenance. | Medium. Reporting shape affects governance evidence and trend comparisons. | Preserve report shape unless schema version and consumers are updated together. | Stability reporting contract tests and generated report checks where applicable. | Future reporting versions should provide migration notes and retained-artifact impact. |
| VPCR-13 | Recurrence event and protected-history lineage contract | Recurrence reporting owner | Recurrence event helpers and serialization/backfill tools | `tests/helpers/replay_bug_recurrence_events.py`, `tests/helpers/replay_bug_recurrence_serialization.py`, `tools/backfill_bug_recurrence_history.py` | Version recurrence rows, event sources, protected-history routing, and population metrics. | Failure dashboard, protected replay history, recurrence reports, generated artifact manifest. | Explicit `RECURRENCE_SCHEMA_VERSION = 1`. | Event source and artifact source classify provenance into protected, session, and synthetic/test lanes. | Medium to high. Recurrence history is replay failure evidence. | Preserve protected-history commit-worthiness policy and legacy history compatibility until approved retirement. | Recurrence tests, serialization tests, failure dashboard tests, artifact manifest review. | Future recurrence schema versions should retain protected-history migration rules. |
| VPCR-14 | Compatibility lineage and retirement-state contract | Compatibility planning owner | Compatibility register | `docs/compatibility_residue_register.md` | Record compatibility owners, consumers, replay/provenance impact, evidence, lifetime, and retirement state. | Compatibility retirement packages, backend/ruleset/version registry reviewers, maintainers. | Manual status/lifetime classification; not an executable schema. | Rows must identify replay/provenance implications where applicable. | Medium to high depending on compatibility surface. | Registering a surface does not approve retirement. | Manual row completeness review and focused tests for touched surfaces. | A future executable compatibility registry may generate summaries from this planning surface after approval. |
| VPCR-15 | Future registry versioning and provenance governance contract | Governance workflow owner | Governance refresh workflow and generated appendix strategy | `docs/governance_refresh_workflow.md`, `docs/generated_documentation_appendices.md`, this registry | Define how future version/provenance registries, generated appendices, and contract publications are refreshed. | Future package authors, governance reviewers, generated-doc maintainers. | Manual today; future executable registries must name version fields, refresh triggers, and generated destinations. | Future registries must identify authoritative source, owner, and generated-output lineage before publication. | Variable; must be classified per future registry row. | Do not publish new version/provenance behavior from workflow docs alone. | Source-reference review and package-specific verification when future registries exist. | Proceed through approved implementation packages before adding generators or enforcement. |

## Ownership Mapping

| Owner Category | Owns | Does Not Own |
|---|---|---|
| Protected replay acceptance owner | Protected scenario policy, protected observation fields, generated manifest field table. | Runtime diagnostic lineage or provenance generation. |
| Golden replay projection owner | Test-only replay projection schema and protected field registry. | Runtime metadata authorship. |
| Realization provenance owner | Governed fallback-family provenance taxonomy. | Diegetic fallback family or prose authorship. |
| Final Emission metadata owner | FEM packaging, producer attribution, mutation lineage, and metadata read/write surfaces. | Mechanics truth, backend routing, or replay policy. |
| Runtime lineage owner | Read-side diagnostic lineage vocabulary and event projection. | Protected replay acceptance schema. |
| Upstream fallback provenance owner | Selector-boundary provenance packaging and containment trace. | Owner-bucket assignment or fallback prose selection. |
| Schema contracts owner | Runtime normalization and legacy-adapter compatibility lineage. | Compatibility retirement approval. |
| Non-combat resolution owner | Explicit non-combat framework version and normalized outcome contract. | Alternate ruleset publication by implication. |
| Contract registry owner | Metadata-only contract indexing. | Runtime enforcement, backend behavior, or gameplay behavior. |
| Generated-doc/governance owner | Source/destination/refresh documentation for generated appendices and retained evidence. | Executable registries or generator behavior. |
| Replay governance owner | Governance decision vocabulary and record shape. | Protected replay scenario policy or classifier taxonomy. |
| Stability/recurrence reporting owners | Report schema versions, recurrence schema version, and reporting evidence shape. | Runtime provenance authorship. |
| Compatibility planning owner | Compatibility lineage, lifetime, evidence, and retirement prerequisites. | Retirement execution. |

## Consumer Mapping

| Consumer | Consumed Contracts | Notes |
|---|---|---|
| Protected replay CI and reviewers | VPCR-01, VPCR-02, VPCR-03, VPCR-04, VPCR-07, VPCR-11, VPCR-14 | Validate replay-sensitive fields and governance decisions without changing runtime behavior. |
| Final Emission and realization maintainers | VPCR-03, VPCR-04, VPCR-05, VPCR-06 | Preserve provenance authorship boundaries and metadata compatibility. |
| Failure dashboard, recurrence, and stability reports | VPCR-05, VPCR-10, VPCR-12, VPCR-13 | Consume lineage/provenance evidence for reporting. |
| Ruleset and backend contract reviewers | VPCR-07, VPCR-08, VPCR-09, VPCR-14, VPCR-15 | Check version/provenance impacts before expanding contracts. |
| Generated documentation reviewers | VPCR-01, VPCR-10, VPCR-15 | Confirm generated rows come from executable sources and manual docs do not become authority. |
| Compatibility retirement planners | VPCR-03, VPCR-06, VPCR-07, VPCR-13, VPCR-14 | Use evidence and replay/provenance classifications before proposing cleanup. |

## Versioning Assessment

| Versioned Surface | Current Version Status | Review Requirement |
|---|---|---|
| Non-combat framework | Explicit `2026.04.noncombat.v1` | Review CTIR, action flow, replay-adjacent tests, and ruleset registry when changed. |
| Stability reporting | Explicit `STABILITY_REPORTING_SCHEMA_VERSION = 1` | Update consumers and retained-report expectations with any schema change. |
| Recurrence reporting | Explicit `RECURRENCE_SCHEMA_VERSION = 1` | Preserve protected-history routing and legacy compatibility during changes. |
| Manual gauntlet aggregate reports | Explicit `AGGREGATE_REPORT_VERSION = 1` | Refresh generated report expectations through existing tool flow. |
| Embedded corrective attribution reports | Explicit `REPORT_SCHEMA_VERSION` | Keep generated report consumers aligned with schema changes. |
| Protected replay manifest generated section | Bounded generated section, no numeric schema version | Refresh from registry and verify marker parity. |
| FEM, runtime lineage, realization provenance, schema adapters | Stable unversioned runtime/helper surfaces | Add explicit versioning only through an approved contract package. |
| Compatibility and contract registries | Manual status/version documentation | Registry rows document version state; they do not create runtime versions. |

## Provenance Assessment

| Provenance Surface | Classification | Required Handling |
|---|---|---|
| `realization_fallback_family` | Runtime provenance, replay-sensitive | Keep separate from `fallback_family_used`; update projection/tests when taxonomy changes. |
| `_final_emission_meta` producer and mutation lineage | Runtime metadata provenance, replay-sensitive | Preserve owner/source fields and read/write helper boundaries. |
| `fallback_provenance` / `fallback_provenance_trace` | Upstream fallback provenance, replay-sensitive in fallback lanes | Merge non-destructively and keep packaging distinct from owner assignment. |
| `fem_runtime_lineage_events` | Read-side diagnostic lineage | Do not merge with protected acceptance schema. |
| Generated artifact source/generator fields | Documentation/evidence lineage | Name generator/source and avoid hand-editing generated rows. |
| Replay governance records | Governance decision lineage | Keep record shape with replay governance owner; do not invent policy in docs. |
| Compatibility rows | Planning lineage | Maintain owner, evidence, replay/provenance impact, and retirement state. |

## Verification Strategy

Use these checks for version/provenance-sensitive changes:

1. Identify the affected VPCR row and canonical owner.
2. Confirm the authoritative implementation remains the source of truth.
3. If a generated artifact is involved, run the existing check or generator
   named by the governing doc.
4. If replay-sensitive fields changed, run focused golden replay, projection,
   or protected manifest verification.
5. If provenance metadata changed, run focused Final Emission, realization,
   fallback provenance, runtime lineage, recurrence, or stability tests.
6. If compatibility lineage changed, update the compatibility register and
   preserve retirement prerequisites.
7. Confirm docs changed without moving runtime, backend, gameplay, governance,
   or CI behavior unless a separate package approved it.

## Reviewer Checklist

- Does every touched version/provenance surface have a canonical owner?
- Does the registry point to authoritative implementations rather than copied
  tables?
- Are replay implications classified for replay-sensitive provenance fields?
- Are explicit schema versions preserved or updated with consumer evidence?
- Are generated artifacts clearly distinguished from manual documentation?
- Are compatibility expectations and retirement prerequisites still intact?
- Did the change avoid provenance generation, replay schemas, runtime behavior,
  backend behavior, gameplay behavior, governance enforcement, and CI changes
  unless explicitly approved?


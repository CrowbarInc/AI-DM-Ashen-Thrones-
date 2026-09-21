# AR-BV Version and Provenance Contract Registry Implementation

## 1. Executive Summary

Package 8 was implemented as a documentation-only registry:
`docs/version_and_provenance_contract_registry.md`.

The registry centralizes repository versioning and provenance-sensitive
contracts across replay versioning, realization provenance, Final Emission
metadata, schema/report versions, contract publication, generated artifact
lineage, compatibility lineage, diagnostic lineage, and future registry
versioning. It does not change runtime behavior, provenance generation, replay
schemas, backend behavior, gameplay behavior, governance enforcement, CI, or
production code.

## 2. Contract Inventory

The registry defines fifteen VPCR rows:

| Contract ID | Surface |
|---|---|
| VPCR-01 | Protected replay scenario and field manifest contract |
| VPCR-02 | Golden replay projection schema contract |
| VPCR-03 | Realization fallback-family provenance contract |
| VPCR-04 | Final Emission metadata and provenance packaging contract |
| VPCR-05 | Runtime lineage event vocabulary contract |
| VPCR-06 | Upstream fast-fallback provenance packaging contract |
| VPCR-07 | Runtime schema normalization and compatibility lineage contract |
| VPCR-08 | Non-combat framework version contract |
| VPCR-09 | Contract metadata publication contract |
| VPCR-10 | Generated documentation and artifact lineage contract |
| VPCR-11 | Replay governance record and decision contract |
| VPCR-12 | Stability and reporting schema contract |
| VPCR-13 | Recurrence event and protected-history lineage contract |
| VPCR-14 | Compatibility lineage and retirement-state contract |
| VPCR-15 | Future registry versioning and provenance governance contract |

## 3. Ownership Mapping

Each contract row identifies a canonical owner and authoritative
implementation. Owner categories include protected replay acceptance, golden
replay projection, realization provenance, Final Emission metadata, runtime
lineage, upstream fallback provenance, schema contracts, non-combat resolution,
contract registry, generated documentation/governance, replay governance,
stability reporting, recurrence reporting, and compatibility planning.

## 4. Consumer Mapping

The registry maps consumers for protected replay CI/review, Final Emission and
realization maintainers, failure dashboard and recurrence/stability reports,
ruleset/backend contract reviewers, generated documentation reviewers, and
compatibility retirement planners.

## 5. Versioning Assessment

The registry distinguishes explicit versions from stable unversioned contracts:

- `game/noncombat_resolution.py::NONCOMBAT_FRAMEWORK_VERSION`
- `tests/stability_reporting_contract.py::STABILITY_REPORTING_SCHEMA_VERSION`
- `tests/helpers/replay_bug_recurrence_events.py::RECURRENCE_SCHEMA_VERSION`
- `tools/aggregate_manual_gauntlets.py::AGGREGATE_REPORT_VERSION`
- `tests/helpers/embedded_corrective_attribution.py::REPORT_SCHEMA_VERSION`
- generated protected replay manifest section markers
- stable unversioned FEM, runtime lineage, realization provenance, schema
  adapter, compatibility, and contract registry surfaces

## 6. Provenance Assessment

The registry classifies provenance-sensitive surfaces including
`realization_fallback_family`, `_final_emission_meta`, `fallback_provenance`,
`fallback_provenance_trace`, `fem_runtime_lineage_events`, generated artifact
lineage, replay governance records, and compatibility register lineage.

## 7. Verification Strategy

Implementation verification used repository-source review and documentation
checks:

1. Confirm every VPCR row has a canonical owner.
2. Confirm every row names authoritative implementation evidence.
3. Confirm version status and replay implications are documented.
4. Confirm generated artifacts are distinguished from executable sources.
5. Confirm cross-links exist from governance and generated-documentation entry
   points.
6. Confirm the package did not modify runtime, backend, gameplay, governance,
   CI, replay schema, or generated artifact behavior.

## 8. Verification Results

Verification completed:

- New registry created at `docs/version_and_provenance_contract_registry.md`.
- Cross-link added from `docs/governance_refresh_workflow.md`.
- Generated appendix strategy updated in
  `docs/generated_documentation_appendices.md`.
- Every registry row includes owner, authoritative implementation, purpose,
  consumers, versioning policy, provenance requirements, replay implications,
  compatibility expectations, verification method, and extensibility notes.
- No production code, tests, replay schemas, governance enforcement, CI files,
  generated artifacts, backend behavior, gameplay behavior, or provenance
  generation were modified for this package.

Automated runtime tests were not run because AR-BV is documentation-only and no
executable behavior changed.

## 9. Risks

| Risk | Assessment | Mitigation |
|---|---|---|
| Documentation drift | Moderate: provenance/version surfaces are distributed across runtime, tests, scripts, and docs. | Registry rows point to authoritative implementations rather than duplicating executable tables. |
| Replay/provenance ambiguity | Moderate: protected replay acceptance and diagnostic lineage are adjacent. | Registry explicitly separates protected replay projection from runtime diagnostic lineage. |
| Version-status confusion | Moderate: some surfaces have explicit versions while others are stable unversioned contracts. | Versioning assessment labels both categories. |
| Future generated appendix overreach | Low to moderate. | Generated appendix doc keeps version/provenance as manual source today and future generated appendix only after approval. |
| Compatibility retirement by implication | Low. | Registry points to compatibility register and states documentation does not approve retirement. |

## 10. Package Closeout

Was the Version and Provenance Contract Registry successfully implemented?
Yes. The repository now contains a centralized manual registry for versioning
and provenance-sensitive contracts.

Are provenance contracts now centrally discoverable?
Yes. The registry is linked from the Governance Refresh Workflow and reflected
in the Generated Documentation Appendices strategy.

Can future versioned architectural changes proceed using explicit contracts?
Yes. Future changes can start from VPCR owner rows and verify against named
authoritative implementations.

## 11. Campaign Assessment

Campaign 5 can proceed toward implementation closeout. Package 8 completes the
planned registry sequence after Package 6 backend contracts and Package 7
ruleset contracts. Repository evidence supports closeout because version,
provenance, replay, generated artifact, compatibility, backend, and ruleset
contract surfaces are now centrally documented without behavior changes.

## 12. Recommended Next Cycle

Proceed to Campaign 5 Closeout.

Evidence:

- `docs/version_and_provenance_contract_registry.md` now documents version and
  provenance contracts.
- `docs/governance_refresh_workflow.md` routes future refresh work to the
  registry.
- `docs/generated_documentation_appendices.md` distinguishes the manual
  version/provenance registry from future generated appendices.
- No new runtime, provenance, replay, backend, gameplay, governance, or CI
  behavior was introduced.

## 13. Files Required for External Review

Required:

- `docs/version_and_provenance_contract_registry.md`
- `docs/governance_refresh_workflow.md`
- `docs/generated_documentation_appendices.md`
- `AR-BV_version_and_provenance_contract_registry_implementation.md`

Optional:

- `docs/compatibility_residue_register.md`
- `docs/backend_contract_registry.md`
- `docs/ruleset_contract_registry.md`
- `docs/testing/protected_replay_manifest.md`
- `tests/helpers/golden_replay_projection_fields.py`
- `game/realization_provenance.py`
- `game/final_emission_meta.py`
- `game/runtime_lineage_telemetry.py`
- `game/final_emission_replay_projection.py`
- `tests/stability_reporting_contract.py`
- `tests/helpers/replay_bug_recurrence_events.py`
- `tests/helpers/golden_replay_artifact_manifest.py`

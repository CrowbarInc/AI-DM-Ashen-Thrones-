# AR-BP Compatibility-Residue Register Implementation

## 1. Executive Summary

Package 2 was implemented as a documentation-only Compatibility-Residue Register.
The register centralizes known active compatibility surfaces identified through
Campaigns 1-5 and records ownership, repository location, current purpose,
consumers, replay/provenance impact, governance implications, known tests,
supporting evidence, retirement prerequisites, estimated lifetime, and current
status.

No compatibility behavior was retired, refactored, or changed.

## 2. Register Overview

The new register is `docs/compatibility_residue_register.md`.

It defines:

- the compatibility status model: Active, Transitional, Awaiting Evidence,
  Retirement Candidate, and Permanent Compatibility;
- the compatibility inventory table;
- ownership mapping;
- consumer mapping;
- replay and provenance assessment;
- retirement readiness;
- maintenance rules for future compatibility changes.

The register is linked from `docs/feature_lane_verification.md` so future
compatibility work starts from the authoritative inventory.

## 3. Compatibility Inventory

The implemented register currently contains 16 centrally discoverable
compatibility entries:

| ID | Surface | Current Status |
|---|---|---|
| CR-01 | Opening fallback compatibility-local authorship and taxonomy | Transitional |
| CR-02 | Dual fallback-family projection | Active |
| CR-03 | CTIR-absent prompt fallback and legacy prompt-local mirrors | Transitional |
| CR-04 | `game.gm` response-policy compatibility re-exports | Transitional |
| CR-05 | Response-policy older payload shapes and private compatibility accessors | Awaiting Evidence |
| CR-06 | Strict-social terminal dialogue legacy repair alias | Transitional |
| CR-07 | Stage-diff telemetry `resolve_gate_turn_packet(...)` wrapper | Transitional |
| CR-08 | Final-emission text compatibility barrel | Transitional |
| CR-09 | Social-exchange emission compatibility barrel | Transitional |
| CR-10 | Smoke bridge compatibility barrels | Transitional |
| CR-11 | Protected recurrence legacy/unified comparison labels | Transitional |
| CR-12 | Schema-contract legacy adapters and unknown legacy key parking | Active |
| CR-13 | Runtime persistence legacy missing-envelope allowance | Transitional |
| CR-14 | Model routing legacy environment variables and single-model compatibility | Permanent Compatibility |
| CR-15 | Final Emission runtime-lineage helper import compatibility | Awaiting Evidence |
| CR-16 | Scene/action legacy compatibility lanes | Awaiting Evidence |

## 4. Ownership Mapping

The register maps compatibility surfaces to canonical owner categories:

- Final Emission boundary, metadata, and replay projection: CR-01, CR-02,
  CR-08, CR-15.
- Runtime provenance and realization authority: CR-02.
- CTIR and prompt adapter: CR-03.
- Response policy and `game.gm` compatibility support: CR-04, CR-05.
- Strict-social and social exchange authorities: CR-06, CR-09.
- Turn packet and stage-diff telemetry: CR-07.
- Replay/test helper facades: CR-10.
- Protected recurrence core and dashboard writer: CR-11.
- Schema, persistence, and runtime data adapters: CR-12, CR-13, CR-16.
- Model routing: CR-14.

## 5. Consumer Mapping

The register maps compatibility surfaces to downstream consumers:

- Protected replay and golden projection: CR-01, CR-02, CR-11, CR-15.
- Runtime lineage, dashboards, and classifiers: CR-01, CR-02, CR-11, CR-15.
- Prompt and narration context: CR-03.
- Legacy imports and compatibility barrels: CR-04, CR-06, CR-08, CR-09,
  CR-10, CR-15.
- Serialization, persistence, and data loading: CR-12, CR-13, CR-16.
- Operator configuration and backend-preparation context: CR-14.
- Governance/import guards: CR-08, CR-09, CR-10, CR-11.

## 6. Replay / Provenance Assessment

The register classifies compatibility surfaces by replay/provenance impact:

| Impact | Items | Required Review Before Retirement |
|---|---|---|
| High | CR-01, CR-02, CR-11 | Protected replay parity, dashboard/classifier inventory, provenance vocabulary review, direct-owner tests. |
| Medium | CR-03, CR-13, CR-15, CR-16 | Consumer map, diagnostic/protected boundary review, persistence or replay fixture scan. |
| Low | CR-04, CR-05, CR-06, CR-07, CR-08, CR-09, CR-10, CR-12, CR-14 | Import/caller scan, direct-owner test confirmation, governance guard review where applicable. |

## 7. Retirement Readiness

| Status | Items | Assessment |
|---|---|---|
| Active | CR-02, CR-12 | Required by current behavior or data compatibility. |
| Transitional | CR-01, CR-03, CR-04, CR-06, CR-07, CR-08, CR-09, CR-10, CR-11, CR-13 | Future cleanup may be possible, but only with retirement packages and evidence. |
| Awaiting Evidence | CR-05, CR-15, CR-16 | Fresh consumer/caller/data evidence is required before retirement planning. |
| Retirement Candidate | None | This package approves no removals. |
| Permanent Compatibility | CR-14 | Preserve unless a future backend/configuration contract changes support policy. |

## 8. Verification Results

| Verification | Command | Result |
|---|---|---|
| Register file exists. | `Test-Path docs\compatibility_residue_register.md` | Passed: returned `True`. |
| Inventory rows exist. | `rg -n "^\| CR-[0-9][0-9]" docs\compatibility_residue_register.md` | Passed: 16 register rows found. |
| Status model and required sections exist. | `rg -n "Active|Transitional|Awaiting Evidence|Retirement Candidate|Permanent Compatibility|Replay and Provenance Assessment|Retirement Readiness|Ownership Mapping|Consumer Mapping|Supporting Evidence|Retirement Prerequisites" docs\compatibility_residue_register.md` | Passed: status model, evidence, retirement, ownership, consumer, and replay/provenance sections found. |
| Cross-reference exists. | `rg -n "compatibility_residue_register" docs\feature_lane_verification.md` | Passed: feature-lane guide links to the register. |
| No tracked production code changed. | `git diff --name-only` | Passed: tracked diffs remained documentation-only from prior Package 1 link files. New Package 2 files are documentation files. |

No automated test suite was run because Package 2 is documentation-only and no
runtime, test, governance logic, generated artifact, replay schema, or
compatibility implementation changed.

## 9. Risks

| Risk | Assessment | Mitigation |
|---|---|---|
| Incomplete compatibility discovery | Medium: the repository is large and contains many historical test fixtures. | The register anchors Campaign 1-5 known surfaces and groups low-level serialization/API compatibility under explicit owner rows. Future discoveries must add rows before behavior changes. |
| Register treated as retirement approval | Medium. | The register states that no item is approved as a retirement candidate by this package and defines retirement prerequisites for every row. |
| Replay/provenance drift | Medium for CR-01, CR-02, CR-11, and CR-15. | High/medium replay-provenance rows require protected replay parity, consumer maps, and provenance review before retirement. |
| Governance confusion | Low to medium. | Import-barrel rows reference existing governance guards; this package added no new governance logic. |
| Documentation staleness | Medium. | The feature-lane guide now points compatibility work to the register; future compatibility work must update the register first. |

## 10. Package Closeout

**Was the register successfully implemented?** Yes. The repository now has
`docs/compatibility_residue_register.md` with 16 compatibility entries and the
required ownership, consumer, replay/provenance, governance, evidence, test, and
retirement fields.

**Are compatibility surfaces now centrally discoverable?** Yes. Campaign 1-5
compatibility surfaces are centralized in the register, and the feature-lane
guide links to it from the compatibility work checklist.

**Is compatibility retirement now safely plannable?** Yes. Retirement is not
approved, but each row now identifies prerequisites and evidence needed for a
future retirement package.

## 11. Campaign Assessment

Campaign 5 implementation can continue with Package 3. Package 2 does not need
additional refinement before the next package unless a reviewer identifies a
missing compatibility surface with concrete repository evidence.

The register deliberately leaves several items as Transitional or Awaiting
Evidence. That is the correct state for Package 2: it creates the planning
surface and does not remove behavior.

## 12. Recommended Next Cycle

Proceed to Package 3.

Repository evidence supporting this recommendation:

- `docs/compatibility_residue_register.md` exists and contains the central
  compatibility inventory.
- The register includes Package 2 seed surfaces from AR-BM: opening
  compatibility-local vocabulary, dual fallback-family projection, CTIR-absent
  prompt fallbacks, `game.gm` re-exports, compat barrels, tuple/adapter residue,
  and legacy/unified recurrence labels.
- The register also records related ownership-ledger compatibility surfaces:
  response-policy old payload support, strict-social legacy repair alias,
  stage-diff telemetry wrapper, schema/persistence compatibility, model-routing
  compatibility, runtime-lineage import compatibility, and scene/action legacy
  lanes.
- `docs/feature_lane_verification.md` links compatibility work to the register.
- No production code, tests, replay schemas, provenance behavior, governance
  logic, generated artifacts, or compatibility implementations were modified.

## 13. Files Required for External Review

### Required

- `AR-BP_compatibility_residue_register_implementation.md`
- `docs/compatibility_residue_register.md`
- `docs/feature_lane_verification.md`
- `AR-BO_feature_lane_verification_package_implementation.md`
- `AR-BM_infrastructure_initiative_prioritization_and_sequencing.md`

### Optional

- `AR-BJ_coordination_cost_inventory_and_workflow_discovery.md`
- `AR-BK_coordination_cost_classification_and_reduction_opportunities.md`
- `AR-BN_feature_lane_verification_package_definition.md`
- `docs/architecture_ownership_ledger.md`
- `docs/gate_cleanup_inventory.md`
- `docs/ctir_prompt_adapter_architecture.md`
- `docs/maintenance/CR_protected_replay_recurrence_separation_discovery.md`
- `tests/ownership_guard_bv_compatibility.py`
- `tests/test_compat_import_governance.py`

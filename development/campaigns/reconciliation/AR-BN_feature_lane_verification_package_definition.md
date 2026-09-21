# AR-BN - Feature-Lane Verification Package Definition

## 1. Executive Summary

This package defines the first Campaign 5 implementation-ready infrastructure initiative: **Feature-Lane Verification Guide**.

Purpose:

- Give future implementers a concise, repository-grounded way to choose the correct verification lane for a change.
- Reduce expert-memory dependence when deciding which owner tests, projection tests, governance checks, generated docs, and documentation updates apply.
- Preserve direct-owner testing, replay/provenance boundaries, Final Emission authority, governance strength, and adapter isolation.

This is a documentation/workflow package only. It should not modify production code, tests, governance behavior, contracts, generated artifacts, compatibility behavior, or repository architecture.

The package is ready for implementation after approval. No additional architectural planning is required.

## 2. Package Scope

### Objectives

- Add a feature-lane verification guide that maps common change types to required verification activities.
- Cross-link the guide from existing workflow/governance entry points.
- Make verification decisions predictable for:
  - ordinary gameplay features;
  - Final Emission changes;
  - protected replay changes;
  - provenance changes;
  - backend contract work;
  - ruleset contract work;
  - compatibility work;
  - governance changes;
  - documentation/generated-artifact changes.

### Expected Repository Artifacts

- A new guide or a clearly marked new section in an existing workflow document.
- Cross-links from `tests/README_TESTS.md` and `docs/convergence_ci_inventory.md`.
- A short reviewer checklist for verifying that a future change has chosen the correct lane.

Preferred implementation shape:

- Create a new focused document such as `docs/feature_lane_verification.md`.
- Add compact links to it from `tests/README_TESTS.md` and `docs/convergence_ci_inventory.md`.

This avoids overloading existing long docs while making the guide discoverable from current workflow entry points.

### Excluded Work

- No production code changes.
- No test rewrites.
- No new tests unless a future implementer finds an existing doc-link checker that must be updated.
- No governance automation.
- No generated documentation implementation.
- No compatibility-residue register implementation.
- No backend/ruleset contract publication.
- No builders or fixtures.
- No compatibility retirement.
- No changes to protected replay fields, split-owner matrix rows, Final Emission taxonomy, or provenance vocabulary.

### Architectural Assumptions

- Campaigns 1-4 architecture remains stable.
- Runtime owners remain authoritative.
- Adapters and projections translate but do not own decisions.
- Runtime diagnostic projection and protected replay acceptance remain separate.
- Provenance records evidence; it does not select behavior.
- Validators predicate; repairs remain bounded and separately owned.
- Final Emission remains the last-mile legality/packaging authority.
- Governance remains enforcement/evidence, not runtime behavior.

### Ownership Boundaries

- Package owner: test/workflow governance documentation owner.
- Supporting owners: architecture governance docs owner and CI/convergence inventory owner.
- Runtime owners are references only and must not be modified.
- Test owners are references only and must not have test semantics changed.

## 3. Repository Impact

### Expected Changes

| File | Expected Change | Justification |
|---|---|---|
| `docs/feature_lane_verification.md` | New guide defining verification lanes, checklists, and reviewer checklist | New focused artifact keeps workflow guidance discoverable without expanding production/test files |
| `tests/README_TESTS.md` | Add a short link/pointer to the guide near existing test ownership or maintenance-loop guidance | AR-BM identifies this as the primary workflow entry point for test selection |
| `docs/convergence_ci_inventory.md` | Add a short link/pointer to the guide near local/CI usage or related governance artifacts | AR-BM identifies this as the governance/CI discovery entry point |

If the implementation chooses not to add `docs/feature_lane_verification.md`, it must justify why an existing document is a better home and still preserve discoverability from both entry points.

### Supporting References

| File | Use | Justification |
|---|---|---|
| `AR-BM_infrastructure_initiative_prioritization_and_sequencing.md` | Primary package sequencing evidence | Selects Feature-Lane Verification Guide as first initiative and defines owner, verification lane, success criteria, and stop condition |
| `AR-BL_implementation_workflow_optimization_planning.md` | Source for workflow variants and checklists | Contains standard workflow, variants, and category-specific coordination checklists |
| `AR-BK_coordination_cost_classification_and_reduction_opportunities.md` | Source for ROI and risk rationale | Identifies verification-lane clarity as medium-high ROI and low risk |
| `AR-BJ_coordination_cost_inventory_and_workflow_discovery.md` | Source for coordination costs and workflow evidence | Provides current feature workflow and coordination cost inventory |
| `docs/architecture_ownership_ledger.md` | Owner doctrine reference | Defines standard seam presentation and direct-owner/downstream/compatibility framing |
| `tests/README_TESTS.md` | Workflow anchor and future link target | Existing contributor-facing test workflow document |
| `docs/convergence_ci_inventory.md` | Governance/CI anchor and future link target | Existing governance and CI discovery index |
| `game/final_emission_boundary_contract.py` | Reference only for Final Emission verification lane | Executable taxonomy source; must not change in this package |
| `tests/helpers/golden_replay_projection_fields.py` | Reference only for protected replay lane | Protected field registry source; must not change in this package |
| `tests/helpers/failure_classification_split_owner.py` | Reference only for split-owner/governance lane | Matrix/report source; must not change in this package |

### Protected Files

| File or Area | Must Not Change | Justification |
|---|---|---|
| `game/` production modules | Yes | Package is documentation/workflow only |
| `tests/` test code except optional README pointer | Yes | Package must not alter test behavior, fixtures, builders, or governance semantics |
| `tests/helpers/golden_replay_projection_fields.py` | Yes | Protected replay schema must not change |
| `tests/helpers/failure_classification_split_owner.py` | Yes | Split-owner matrix/report behavior is out of scope |
| `game/final_emission_boundary_contract.py` | Yes | Final Emission taxonomy is out of scope |
| `game/realization_authority.py` and `game/realization_provenance.py` | Yes | Provenance/fallback vocabulary is out of scope |
| `game/model_routing.py` and `game/gm.py` | Yes | Backend contract publication is not part of Package 1 |
| `game/state_authority.py` | Yes | State authority is reference-only |
| `docs/testing/protected_replay_manifest.md` | Yes, unless only adding a link is explicitly justified | Protected manifest content/generation is out of scope |
| `docs/audits/`, `audits/`, `artifacts/` | Yes | Historical/generated evidence must not be rewritten |
| `.github/workflows/` | Yes | No CI automation or workflow behavior change |
| `scripts/` and `tools/` | Yes | No tooling automation in Package 1 |

## 4. Acceptance Criteria

### Required

- A feature-lane verification guide exists in the repository.
- The guide covers at least these lanes:
  - ordinary gameplay feature;
  - Final Emission change;
  - protected replay change;
  - provenance change;
  - backend contract work;
  - ruleset contract work;
  - compatibility work;
  - governance change;
  - documentation/generated artifact change.
- Each lane names:
  - canonical owner category;
  - relevant contract/registry surfaces;
  - replay/provenance consideration;
  - expected test layer;
  - governance consideration;
  - documentation/generated-artifact consideration;
  - stop condition or escalation rule.
- The guide explicitly preserves:
  - direct-owner tests before downstream smoke;
  - runtime diagnostic vs protected replay separation;
  - provenance as evidence, not selector;
  - Final Emission boundary authority;
  - validator/repair separation;
  - compatibility evidence before retirement.
- `tests/README_TESTS.md` links to the guide.
- `docs/convergence_ci_inventory.md` links to the guide.
- No production code is modified.
- No test behavior is modified.
- No new governance check is introduced.

### Optional

- Add a compact "Which lane am I in?" decision table.
- Add a reviewer checklist at the end of the guide.
- Add examples of minimal verification sets using existing command names, as long as commands are already documented and paths exist.
- Add authority-level labels such as "owner test", "projection test", "governance check", "generated artifact".

### Future Enhancement

- Turn guide sections into generated/checkable workflow snippets after governance refresh workflow exists.
- Add compatibility-residue register links after Package 2 exists.
- Add backend/ruleset contract package links after those contracts are published.
- Add builder usage guidance after FEM/protected-row builders exist.

## 5. Verification Plan

### Documentation Review

- Confirm the guide uses AR-BL workflow categories and does not introduce new architecture.
- Confirm the guide does not recommend collapsing owners or moving authority into adapters, replay, tests, or docs.
- Confirm the guide differentiates owner tests, downstream smoke, protected replay, and governance checks.

### Cross-Reference Validation

- Confirm `tests/README_TESTS.md` links to the guide.
- Confirm `docs/convergence_ci_inventory.md` links to the guide.
- Confirm referenced files exist:
  - `docs/architecture_ownership_ledger.md`
  - `tests/README_TESTS.md`
  - `docs/convergence_ci_inventory.md`
  - `game/final_emission_boundary_contract.py`
  - `tests/helpers/golden_replay_projection_fields.py`
  - `tests/helpers/failure_classification_split_owner.py`

Suggested manual commands:

```powershell
Test-Path docs\feature_lane_verification.md
rg -n "feature_lane_verification|Feature-Lane Verification|feature-lane verification" tests\README_TESTS.md docs\convergence_ci_inventory.md
rg -n "ordinary gameplay|Final Emission|protected replay|provenance|backend|ruleset|compatibility|governance" docs\feature_lane_verification.md
```

### Link Verification

- Check that relative links from `tests/README_TESTS.md` and `docs/convergence_ci_inventory.md` resolve correctly.
- If markdown links are used, confirm paths are correct relative to each file.

### Consistency Checks

- Search for prohibited language suggesting architectural simplification:
  - "collapse replay"
  - "merge owners"
  - "move authority"
  - "remove governance"
  - "retire compatibility" without evidence
- Confirm any command examples already exist in current docs or files.

Suggested manual commands:

```powershell
rg -n "collapse|merge owners|move authority|remove governance|retire compatibility" docs\feature_lane_verification.md
rg -n "pytest|tools/|scripts/|python " docs\feature_lane_verification.md
```

### Repository Searches

- Confirm production files were not changed.
- Confirm protected files were not changed.

Suggested manual commands:

```powershell
git status --short
```

Expected changed files for Package 1 should be limited to:

- `docs/feature_lane_verification.md`
- `tests/README_TESTS.md`
- `docs/convergence_ci_inventory.md`

### Governance Review

- Confirm no new hard-fail or advisory governance mechanism is introduced.
- Confirm the guide points to existing governance rather than changing it.
- Confirm hard-fail/advisory/deferred status in `docs/convergence_ci_inventory.md` is not altered except for a link to the guide.

### Existing Automated Verification

No existing automated verification is required by this package because it is documentation-only.

If the implementation changes command references or generated-doc instructions, the implementer may run existing documentation-adjacent checks already used in the repo, but Package 1 must not require new tooling.

## 6. Risk Assessment

| Risk | Level | Why It Matters | Mitigation |
|---|---|---|---|
| Architectural risk | Low | Guide could accidentally imply owner consolidation or replay/provenance simplification | Explicitly state preservation rules and review against AR-BL/AR-BM |
| Documentation drift | Medium | Command lists and file references can become stale | Keep command examples minimal; link to existing docs for detailed commands |
| Workflow ambiguity | Medium | A guide that is too broad may not reduce decision cost | Use lane table and checklist format; include stop/escalation rule per lane |
| Future maintenance | Medium | Another workflow doc can become one more surface to sync | Keep guide as routing/index document, not a full duplicate of README/CI inventory |
| Developer onboarding | Low-medium | Poor placement could make guide hard to find | Link from `tests/README_TESTS.md` and `docs/convergence_ci_inventory.md` |
| Governance consistency | Low-medium | Guide could conflict with hard-fail/advisory statuses | Do not restate full CI status tables; refer to `docs/convergence_ci_inventory.md` |
| Compatibility risk | Low | Package does not retire compatibility | Include compatibility evidence-before-retirement rule |
| Replay risk | Low | Package does not change replay schema | Include runtime/protected replay separation rule |

## 7. Deliverables

After implementation, a reviewer should receive:

- New feature-lane verification guide.
- Cross-link in `tests/README_TESTS.md`.
- Cross-link in `docs/convergence_ci_inventory.md`.
- Reviewer checklist in the guide or package closeout.
- Verification log showing:
  - changed files;
  - guide exists;
  - cross-links exist;
  - lane coverage exists;
  - protected files did not change;
  - no production code changed.

Expected implementation output should be documentation-only.

## 8. Package Closeout Criteria

Package 1 is complete when:

- All required acceptance criteria are met.
- Verification plan has been executed and recorded.
- Changed files are limited to expected documentation files or a justified subset.
- No production code, test behavior, governance automation, contracts, builders, generated artifacts, compatibility behavior, or architecture files are modified.
- Reviewer can use the guide to choose the correct verification lane for the nine required change categories.
- Any optional additions are clearly marked as optional and do not expand scope.

Stop immediately if implementation requires:

- modifying production code;
- changing tests;
- adding governance checks;
- updating protected replay fields;
- changing split-owner matrix behavior;
- publishing backend/ruleset contracts;
- retiring compatibility;
- implementing builders or automation.

Those belong to later packages.

## 9. Campaign Assessment

Is this package ready for implementation?

Yes. AR-BM identified Feature-Lane Verification Guide as the first initiative because it has no production-code dependency, low architectural risk, immediate developer benefit, and creates shared verification vocabulary for all later infrastructure initiatives.

Are additional planning cycles necessary?

No additional architectural or sequencing planning is necessary for Package 1. The package scope is documentation-only and independently reviewable.

Can implementation begin after approval?

Yes. Implementation can begin after approval, provided it follows the protected-file boundaries and stop conditions in this document.

## 10. Recommended Next Cycle

Recommendation: **Proceed to implementation of Package 1**.

Repository evidence:

- AR-BM ranks Feature-Lane Verification Guide as the first initiative and marks it Critical.
- AR-BL already defines the workflow variants and checklists needed to populate the guide.
- AR-BK identifies verification-lane clarity as a low-risk, medium-high ROI workflow improvement.
- AR-BJ identifies expert-memory dependence when selecting owners, tests, replay/provenance steps, and governance checks.

Do not define Package 2 before implementing Package 1 unless implementation approval is delayed. Package 2, the Compatibility-Residue Register, should follow after the guide establishes terminology and lane structure.

## 11. Files Required for External Review

### Required

- `AR-BN_feature_lane_verification_package_definition.md`
- `AR-BM_infrastructure_initiative_prioritization_and_sequencing.md`
- `AR-BL_implementation_workflow_optimization_planning.md`
- `AR-BK_coordination_cost_classification_and_reduction_opportunities.md`
- `AR-BJ_coordination_cost_inventory_and_workflow_discovery.md`
- `tests/README_TESTS.md`
- `docs/convergence_ci_inventory.md`
- `docs/architecture_ownership_ledger.md`

### Optional

- `AR-BI_boundary_reconciliation_campaign_closeout.md`
- `AR-BG_ruleset_backend_and_version_provenance_boundary_inventory.md`
- `AR-BH_minimal_extensibility_contract_definition.md`
- `AR-AD_target_architecture_doctrine.md`
- `game/final_emission_boundary_contract.py`
- `tests/helpers/golden_replay_projection_fields.py`
- `tests/helpers/failure_classification_split_owner.py`
- `game/realization_authority.py`
- `game/realization_provenance.py`
- `game/contract_registry.py`

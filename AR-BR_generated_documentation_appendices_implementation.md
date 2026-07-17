# AR-BR Generated Documentation Appendices Implementation

## 1. Executive Summary

Package 4 was implemented as a documentation-only generated-appendices strategy.
The new document identifies where documentation may be generated from existing
authoritative executable registries, which appendices already exist, which are
candidates, and which future appendices must wait for approved backend, ruleset,
or version/provenance registries.

No documentation generation was automated. No executable registry, generator, CI
behavior, governance behavior, replay schema, production code, generated output,
or runtime behavior was changed.

## 2. Appendix Inventory

The new inventory lives in `docs/generated_documentation_appendices.md`.

It covers:

| Appendix Area | Status |
|---|---|
| Final Emission boundary taxonomy appendix | Candidate |
| Protected replay field registry appendix | Active |
| Split-owner acceptance matrix summary | Active |
| Test inventory governance appendix | Active / Candidate |
| Convergence CI command appendix | Candidate |
| Compatibility summary appendix | Candidate / Manual Source |
| Replay governance decision appendix | Candidate |
| Validation coverage appendix | Candidate |
| Contract registry appendix | Candidate |
| Backend contract registry appendix | Future |
| Ruleset contract registry appendix | Future |
| Version/provenance registry appendix | Future |

Each row identifies canonical source, destination, ownership, refresh trigger,
verification method, reviewer expectations, maintenance strategy, and status.

## 3. Authority Mapping

The package preserves executable authority:

| Surface | Executable Authority | Documentation Role |
|---|---|---|
| Final Emission taxonomy | `game/final_emission_boundary_contract.py` | Explain taxonomy and future generated rows. |
| Protected replay fields | `PROTECTED_OBSERVATION_FIELDS` | Display generated field paths and drift buckets. |
| Split-owner matrix | `SPLIT_OWNER_ACCEPTANCE_MATRIX` | Display generated matrix/report summaries. |
| Test inventory | `tools/test_audit.py` plus registry-owned tests | Store generated governance JSON and link to live diagnostics. |
| Governance command inventory | Workflow YAML files | Document command parity and maintainer navigation. |
| Compatibility surfaces | Compatibility register today; future executable registry if approved | Plan cleanup and evidence, not enforcement. |
| Replay governance decisions | Replay governance registry and contracts | Explain existing decisions and traceability. |
| Future backend/ruleset/version contracts | Future registries only after approved packages | Display contract registries without creating behavior. |

## 4. Generated vs Manual Documentation Classification

The document classifies repository documentation into:

- executable source;
- generated appendix;
- manual doctrine;
- manual planning register;
- future appendix.

The classification makes clear that generated appendices are read-only
documentation views over executable sources, while manual doctrine explains
purpose, scope, and review expectations.

## 5. Refresh Responsibilities

Refresh responsibilities are documented as follows:

- executable registry owners own generated appendix data;
- documentation/governance owners own placement, markers, links, and prose;
- reviewers verify generated rows came from the named source;
- refresh-only changes must not update runtime code to make documentation pass;
- if no generator exists, copied tables must not be treated as generated output.

## 6. Verification Strategy

The package defines a strategy for future appendix verification:

1. Identify executable source.
2. Confirm generated destination names that source.
3. Run existing check command when one exists.
4. Verify links and source references when no check exists.
5. Confirm generated rows are not hand edited.
6. Confirm prose does not redefine source semantics.
7. Confirm no executable authority moved into documentation.

## 7. Reviewer Guidance

Reviewer guidance was added for:

- asking what the source of truth is before reviewing a generated table;
- preferring registry links over copied prose lists;
- treating generated-section markers as boundaries;
- avoiding new generation tooling in docs-only appendix updates;
- blocking future backend/ruleset/version appendices until approved executable
  sources exist;
- keeping compatibility summaries honest as manual planning surfaces until an
  executable registry is approved.

## 8. Verification Results

| Verification | Command | Result |
|---|---|---|
| Generated appendices document exists. | `Test-Path docs\generated_documentation_appendices.md` | Passed: returned `True`. |
| Required strategy sections exist. | `rg -n "^## (Core Rule|Appendix Inventory|Generated vs Manual Documentation|Authority Mapping|Refresh Responsibilities|Verification Strategy|Reviewer Guidance|Stop Conditions)" docs\generated_documentation_appendices.md` | Passed: required sections were found. |
| Required appendix fields and candidate areas exist. | `rg -n "Canonical Executable Source|Generated Documentation Destination|Refresh Trigger|Verification Method|Reviewer Expectations|Final Emission|Protected replay|Split-owner|Compatibility|Backend|Ruleset|Version/provenance|Executable registries remain canonical" docs\generated_documentation_appendices.md` | Passed: required fields and candidate areas were found. |
| Governance refresh workflow links to appendices document. | `rg -n "generated_documentation_appendices" docs\governance_refresh_workflow.md` | Passed: workflow introduction and inventory row link to the document. |
| Repository impact reviewed. | `git status --short` | Passed with expected documentation-only changes and pre-existing campaign artifacts. |

No automated tests were run because this package is documentation-only and does
not alter executable registries, generated outputs, CI, governance behavior, or
runtime behavior.

## 9. Risks

| Risk | Assessment | Mitigation |
|---|---|---|
| Generated appendix strategy is mistaken for automation | Low | The document states that no generators are introduced and future generator work requires a separate package. |
| Documentation appears authoritative over executable registries | Low | The core rule states executable registries remain canonical and generated appendices are read-only views. |
| Future-only backend/ruleset/version appendices look published | Medium | They are marked Future, with no destination output created and no registry introduced. |
| Compatibility register generation is premature | Medium | The compatibility summary is classified as Candidate / Manual Source and must not be generated until an executable source is approved. |
| Existing generated outputs drift | Medium | The document points to current refresh/check commands for active protected replay and split-owner appendices. |

## 10. Package Closeout

**Were generated documentation appendices successfully introduced?** Yes. The
repository now has `docs/generated_documentation_appendices.md`, which introduces
the appendix strategy and inventory.

**Are executable registries still the canonical authority?** Yes. The document
explicitly preserves executable registries as canonical and classifies generated
appendices as read-only views.

**Can future generated documentation be expanded without architectural change?**
Yes. Candidate and future appendices are documented with source, destination,
ownership, refresh triggers, verification method, and reviewer expectations.
Actual generator or registry work remains separate.

## 11. Campaign Assessment

Campaign 5 should proceed to the next implementation package. Package 4 does not
need refinement before proceeding unless review identifies a missing generated
documentation surface with concrete repository evidence.

This package intentionally did not implement generators or regenerate outputs.
That keeps the architecture stable while establishing how future generated docs
should be expanded.

## 12. Recommended Next Cycle

Proceed to Package 5.

Repository evidence supporting this recommendation:

- `docs/generated_documentation_appendices.md` exists and documents active,
  candidate, and future appendix surfaces.
- `docs/governance_refresh_workflow.md` links to the appendices strategy and
  includes it in the governed artifact inventory.
- Existing active generated surfaces are named: protected replay manifest field
  section and split-owner acceptance matrix report.
- Future backend, ruleset, and version/provenance appendices are explicitly
  deferred until approved executable registries exist.
- No executable registries, generators, CI files, governance behavior, generated
  outputs, replay schemas, production code, or runtime behavior were modified.

## 13. Files Required for External Review

### Required

- `AR-BR_generated_documentation_appendices_implementation.md`
- `docs/generated_documentation_appendices.md`
- `docs/governance_refresh_workflow.md`
- `AR-BQ_governance_refresh_workflow_implementation.md`

### Optional

- `AR-BM_infrastructure_initiative_prioritization_and_sequencing.md`
- `docs/testing/protected_replay_manifest.md`
- `docs/audits/BU15_split_owner_acceptance_matrix.md`
- `docs/audits/README.md`
- `tests/helpers/golden_replay_projection.py`
- `tests/helpers/golden_replay_projection_manifest.py`
- `tests/helpers/failure_classification_sync.py`
- `scripts/split_owner_acceptance_matrix_ops.py`
- `tools/refresh_protected_replay_manifest.py`
- `scripts/refresh_split_owner_acceptance_matrix.py`

# Generated Documentation Appendices

This document defines where repository documentation may be generated from
authoritative executable registries. It is a strategy and ownership document
only. It does not add generators, modify executable registries, update generated
outputs, change CI, or move authority from code/tests into docs.

Use this document with the Governance Refresh Workflow when a change touches a
registry-backed table, generated documentation section, report, manifest, or
future contract appendix.

## Core Rule

Executable registries remain canonical. Generated appendices are read-only
documentation views over those registries. Manual prose may explain purpose,
scope, policy, and review expectations, but generated rows must be refreshed
from their named source rather than edited by hand.

## Appendix Inventory

| Appendix | Canonical Executable Source | Generated Documentation Destination | Ownership | Refresh Trigger | Verification Method | Reviewer Expectations | Maintenance Strategy | Status |
|---|---|---|---|---|---|---|---|---|
| Final Emission boundary taxonomy appendix | `game/final_emission_boundary_contract.py` | Future generated section in a Final Emission boundary doc or audit appendix | Final Emission boundary owner with documentation/governance support | Boundary mutation kind added, removed, renamed, or reclassified | Existing boundary contract tests plus future parity check if generator is introduced | Confirm generated table reflects executable taxonomy and does not redefine legality in prose | Plan only; do not implement generator in this package | Candidate |
| Protected replay field registry appendix | `tests/helpers/golden_replay_projection.py::PROTECTED_OBSERVATION_FIELDS`; renderer in `tests/helpers/golden_replay_projection_manifest.py` | Existing generated section in `docs/testing/protected_replay_manifest.md` | Protected replay acceptance owner | Protected observation path or drift bucket changes | `python tools/refresh_protected_replay_manifest.py --check`; write with `--write` when approved | Confirm generated section is bounded by markers and registry remains source of truth | Existing generated appendix; continue using current refresh tool | Active |
| Split-owner acceptance matrix summary | `tests/helpers/failure_classification_sync.py::SPLIT_OWNER_ACCEPTANCE_MATRIX`; `scripts/split_owner_acceptance_matrix_ops.py` | Existing generated report `docs/audits/BU15_split_owner_acceptance_matrix.md` | Split-owner/failure-classification sync owner | Matrix row, owner literal, dashboard id, evidence cell, or builder surface changes | `python scripts/check_split_owner_acceptance_matrix.py`; refresh with `python scripts/refresh_split_owner_acceptance_matrix.py` | Confirm checked-in report matches generated output and matrix-only changes do not affect runtime behavior | Existing generated report; keep manual checklist in `docs/audits/README.md` | Active |
| Test inventory governance appendix | `tools/test_audit.py`; pytest collection; ownership registry data | Existing generated JSON `tests/test_inventory_governance.json`; possible future generated markdown appendix | Test inventory/governance owner | Test inventory, marker, registry-owned path, or ownership registry changes | `python tools/test_audit.py --check`; write JSON with `python tools/test_audit.py` | Confirm JSON is generated and markdown counts remain pointers to live source | Existing generated JSON; markdown appendix remains future candidate | Active / Candidate |
| Convergence CI command appendix | `.github/workflows/convergence-checks.yml`; `.github/workflows/content-lint.yml`; existing command docs | Possible future generated command/status appendix in `docs/convergence_ci_inventory.md` | CI/governance documentation owner | CI command, workflow placement, or hard-fail/informational/deferred status changes | Manual workflow comparison today; future parity check if generator exists | Confirm docs describe workflow reality and do not create a gate by wording alone | Manual for now; generator requires separate package | Candidate |
| Compatibility summary appendix | `docs/compatibility_residue_register.md` until an executable compatibility registry exists | Possible future generated summary section in compatibility docs | Compatibility planning owner | Compatibility surface added, status changed, retirement evidence gathered | Manual row completeness review today | Confirm the manual register remains planning authority and no retirement is implied | Do not generate from manual register unless a future executable source is approved | Candidate / Manual Source |
| Replay governance decision appendix | `tests/replay_governance_registry.py`; related replay governance contract modules | Possible generated table in `docs/testing/replay_governance_registry.md` | Replay governance registry owner | Governance decision record or contract shape changes | Focused replay-governance tests named by docs | Confirm appendix records existing intent and does not invent policy | Candidate; generator requires separate package | Candidate |
| Validation coverage appendix | `tests/validation_coverage_registry.py`; `tools/validation_coverage_audit.py` | Possible generated coverage table in `docs/objective12_validation_contract.md` or a coverage appendix | Validation coverage registry owner | Feature coverage ownership or required surfaces change | `python -m pytest tests/test_validation_coverage_registry.py -q`; `python tools/validation_coverage_audit.py --strict` | Confirm registry maps what to run and does not become a scoring layer | Candidate; current source remains executable registry | Candidate |
| Contract registry appendix | `game/contract_registry.py` and focused contract modules | Possible generated contract index in architecture docs | Contract registry owner | Contract id, version, field, or provider-facing shape changes | Existing contract registry/static drift tests | Confirm appendix indexes contracts without publishing new backend/ruleset behavior | Candidate; avoid expanding scope into backend/ruleset publication | Candidate |
| Backend contract registry appendix | Future backend contract registry | Future backend contract documentation appendix | Future backend contract owner | Backend contract package publishes or updates executable registry | Future package-defined verification | Confirm no provider behavior is introduced by documentation | Future only; no registry is created here | Future |
| Ruleset contract registry appendix | `docs/ruleset_contract_registry.md` until a future executable ruleset registry exists | Possible future generated ruleset contract appendix | Ruleset contract owner plus domain mechanics owners | Ruleset-facing contract owner, lifecycle, compatibility, version, or verification requirement changes; future executable ruleset registry package approved | Manual source-reference review today; future package-defined verification if executable registry is introduced | Confirm no alternate-ruleset behavior is introduced by documentation and implementation modules remain authoritative | Manual registry today; generated appendix remains future candidate | Manual Source / Candidate |
| Version/provenance registry appendix | `docs/version_and_provenance_contract_registry.md` until a future executable version/provenance registry exists | Possible future generated version/provenance documentation appendix | Version/provenance contract owner plus replay/provenance/reporting owners | Versioned artifact, provenance metadata, replay-sensitive lineage, generated artifact lineage, compatibility lineage, or future executable registry changes | Manual source-reference review today; future package-defined verification plus provenance tests if an executable registry is introduced | Confirm provenance remains evidence-only, executable sources remain authoritative, and documentation does not select runtime behavior | Manual registry today; generated appendix remains future candidate | Manual Source / Candidate |

## Generated vs Manual Documentation

| Documentation Type | Definition | Examples | Edit Rule |
|---|---|---|---|
| Executable source | Code, test helper, script, or workflow that owns registry data or enforcement behavior | `PROTECTED_OBSERVATION_FIELDS`, `SPLIT_OWNER_ACCEPTANCE_MATRIX`, `tools/test_audit.py`, workflow YAML | Edit only in an implementation package that owns that surface. |
| Generated appendix | Markdown, JSON, CSV, or report content rendered from executable source | Protected field section in `protected_replay_manifest.md`, `BU15_split_owner_acceptance_matrix.md`, `tests/test_inventory_governance.json` | Refresh with the named command; do not hand-edit rows. |
| Manual doctrine | Human-authored architecture or process explanation | `docs/architecture_ownership_ledger.md`, prose in `docs/convergence_ci_inventory.md`, this document | Link to executable source for tables and counts; avoid duplicating generated rows. |
| Manual planning register | Human-authored planning inventory pending executable source | `docs/compatibility_residue_register.md` | Keep row completeness review explicit; do not pretend it is generated. |
| Future appendix | Planned generated view whose executable source or generator does not exist yet | Backend/ruleset/version appendices | Do not create placeholder output that looks authoritative; list as future only. |

## Authority Mapping

| Surface | Executable Authority | Documentation Role |
|---|---|---|
| Final Emission taxonomy | `game/final_emission_boundary_contract.py` | Explain taxonomy and, in the future, display generated rows. |
| Protected replay fields | `PROTECTED_OBSERVATION_FIELDS` | Display generated field paths and drift buckets. |
| Split-owner matrix | `SPLIT_OWNER_ACCEPTANCE_MATRIX` | Display generated matrix/report summaries. |
| Test inventory | `tools/test_audit.py` plus registry-owned tests | Store generated governance JSON and link to live diagnostics. |
| Governance command inventory | Workflow YAML files | Document command parity and maintainer navigation. |
| Compatibility surfaces | Compatibility register today; future executable registry if approved | Plan cleanup and evidence, not enforcement. |
| Replay governance decisions | Replay governance registry and contracts | Explain existing decisions and traceability. |
| Future backend contracts | Future executable registries only after approved packages | Display contract registries without creating behavior. |
| Ruleset contracts | `docs/ruleset_contract_registry.md` today; future executable registry only after approved package | Document current ruleset-facing contracts without creating alternate-ruleset behavior. |
| Version/provenance contracts | `docs/version_and_provenance_contract_registry.md` today; future executable registry only after approved package | Document current version/provenance contracts without changing provenance generation or versioning behavior. |

## Refresh Responsibilities

- The owner of the executable registry owns the generated appendix data.
- Documentation/governance owners own placement, markers, links, and explanatory
  prose.
- Reviewers must verify that generated rows came from the named source.
- Refresh-only changes must not update runtime code to make documentation pass.
- If no generator exists, reviewers should require a manual source pointer and a
  future-candidate status rather than accepting copied tables as generated.

## Verification Strategy

For each generated appendix:

1. Identify the executable source.
2. Confirm the generated destination names that source.
3. Run the existing check command when one exists.
4. If no check exists, verify links and source references by repository search.
5. Confirm generated rows are not edited by hand.
6. Confirm manual prose does not redefine source semantics.
7. Confirm no executable authority moved into documentation.

## Reviewer Guidance

- Ask "what is the source of truth?" before reviewing the table.
- Prefer a link to a registry over a copied list in prose.
- Treat generated-section markers as boundaries: generated rows inside, manual
  explanation outside.
- Do not request new generation tooling as part of a docs-only appendix update.
- Do not approve future backend appendices until an approved package creates
  the executable source. Ruleset contracts currently use
  `docs/ruleset_contract_registry.md` as a manual source until a future
  executable registry is approved. Version/provenance contracts currently use
  `docs/version_and_provenance_contract_registry.md` as a manual source until a
  future executable registry is approved.
- For compatibility summaries, remember that the current register is a manual
  planning surface, not an executable registry.

## Stop Conditions

Stop and return to package planning if generated documentation work requires:

- a new generator or CI check;
- executable registry edits;
- production code changes;
- replay schema changes;
- protected replay acceptance changes;
- governance behavior changes;
- compatibility retirement;
- backend, ruleset, or version/provenance contract publication;
- generated artifact regeneration outside an approved refresh package.

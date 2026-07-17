# Governance Refresh Workflow

This workflow explains when governance artifacts need refresh, which sources are
authoritative, which files are generated, and how reviewers confirm that a
change kept governance current. It is documentation-only: it does not change CI,
pytest behavior, replay schemas, governance policy, ownership semantics, or
runtime behavior.

Use this workflow after the Feature-Lane Verification Guide identifies a
governance or documentation/generated-artifact lane, and before changing a
governed registry, manifest, inventory, report, or compatibility planning file.
For generated appendix strategy and candidate surfaces, see
`docs/generated_documentation_appendices.md`. For backend-facing contract
ownership and verification, see `docs/backend_contract_registry.md`. For
ruleset-facing contract ownership and verification, see
`docs/ruleset_contract_registry.md`. For versioning and provenance-sensitive
contracts, see `docs/version_and_provenance_contract_registry.md`.

## Refresh Principles

- Refresh the smallest governed artifact that is downstream of the changed
  source.
- Treat executable registries, helper constants, scripts, and CI files as
  authoritative where this workflow names them as sources.
- Treat generated markdown, generated JSON, generated CSV, and generated
  artifacts as outputs unless the artifact itself says it is manually maintained.
- Do not hand-edit generated sections when a refresh command exists.
- Do not add new governance enforcement, CI gates, replay acceptance criteria,
  or ownership semantics in a refresh-only change.
- If a change requires a new policy decision, stop and create an approved
  implementation package before editing enforcement behavior.

## Governed Artifact Inventory

| Area | Artifact | Type | Authoritative Source | Refresh Trigger | Refresh / Check | Reviewer Expectation |
|---|---|---|---|---|---|---|
| Test inventory | `tests/test_inventory_governance.json` | Generated governance JSON | `tools/test_audit.py`, pytest collection, ownership registry data | Test file added/removed/renamed; markers change; registry-owned module set changes; ownership registry changes | Write: `python tools/test_audit.py`; check: `python tools/test_audit.py --check`; full diagnostic: `python tools/test_audit.py --full` | Confirm committed JSON is regenerated only for inventory changes and that semantic test ownership remains in owner docs/tests. |
| Test inventory documentation | `tests/TEST_AUDIT.md` | Manual governance documentation with live-source pointers | `tests/test_inventory_governance.json`, `tools/test_audit.py --check`, `tests/test_ownership_registry.py` | Workflow or owner guidance changes; stale command or source pointer found | Manual edit; verify with `python tools/test_audit.py --check` when inventory-sensitive | Confirm counts are not treated as static authority when live tools are named as source of truth. |
| Convergence CI inventory | `docs/convergence_ci_inventory.md` | Manual governance/CI navigation index | `.github/workflows/convergence-checks.yml`, `.github/workflows/content-lint.yml`, linked source docs/tests | CI step added/removed/moved; hard-fail/informational/deferred status changes; governance command changes | Manual edit; compare against workflow files and referenced commands | Confirm the document maps existing CI behavior and does not create a new gate by wording alone. |
| Protected replay manifest | `docs/testing/protected_replay_manifest.md` | Mixed manual manifest with generated protected-field section | Manual protected scenario policy; `tests/helpers/protected_replay_registry.py`; `tests/helpers/golden_replay_projection.py::PROTECTED_OBSERVATION_FIELDS`; `tests/helpers/golden_replay_projection_manifest.py` | Protected scenario status changes; protected observation field paths change; generated section drift | Generated field section write: `python tools/refresh_protected_replay_manifest.py --write`; check: `python tools/refresh_protected_replay_manifest.py --check`; protected lane: `python -m pytest -m golden_replay -q` | Confirm generated section came from registry source and protected/advisory status changes are explicitly reviewed. |
| Protected observation field registry | `tests/helpers/golden_replay_projection.py::PROTECTED_OBSERVATION_FIELDS` | Executable registry | Golden replay projection owner | New protected observation path; drift bucket classification change | Verify manifest with `python tools/refresh_protected_replay_manifest.py --check` and relevant golden replay tests | Confirm runtime diagnostic projection and protected replay acceptance stay separate. |
| Split-owner acceptance matrix source | `tests/helpers/failure_classification_sync.py::SPLIT_OWNER_ACCEPTANCE_MATRIX` | Executable registry | Split-owner/failure-classification sync owner | Matrix row added/removed/edited; owner literal, dashboard id, evidence cell, or builder surface changes | Refresh: `python scripts/refresh_split_owner_acceptance_matrix.py`; check: `python scripts/check_split_owner_acceptance_matrix.py` | Confirm matrix-only edits do not change production emission behavior. |
| Split-owner generated report | `docs/audits/BU15_split_owner_acceptance_matrix.md` | Generated markdown report | `SPLIT_OWNER_ACCEPTANCE_MATRIX`, `scripts/split_owner_acceptance_matrix_ops.py` | Any split-owner matrix edit | Write/check through `python scripts/refresh_split_owner_acceptance_matrix.py`; CI check via `python scripts/check_split_owner_acceptance_matrix.py` | Confirm report footer/contents match generated output and were not hand-edited. |
| Split-owner workflow docs | `docs/audits/README.md`, split-owner section in `docs/convergence_ci_inventory.md`, split-owner section in `tests/README_TESTS.md` | Manual workflow documentation | Split-owner scripts, source matrix, CI workflow | Refresh command changes; script names change; CI placement changes; edit checklist changes | Manual edit; verify links and command names | Confirm the three docs agree on canonical source, local refresh, and CI check command. |
| Ownership ledger | `docs/architecture_ownership_ledger.md` | Manual ownership doctrine | Runtime owners, direct-owner tests, governance suites | Owner boundary changes; direct-owner suite changes; compatibility/support residue changes | Manual edit; run focused owner/governance tests when code ownership changed | Confirm compatibility residue and downstream consumer roles do not become new semantic owners. |
| Ownership/governance registry tests | `tests/test_ownership_registry.py`, focused governance modules listed in `tests/README_TESTS.md` | Executable governance tests | Test modules themselves and their helper contracts | Governance owner set changes; focused policy domain changes | `python -m pytest tests/test_ownership_registry.py tests/test_inventory_governance.py tests/test_gate_boundary_governance.py tests/test_replay_boundary_governance.py tests/test_ownership_write_path_governance.py -q` | Confirm new checks live in the focused owner module, not the registry identity file by default. |
| Compatibility register | `docs/compatibility_residue_register.md` | Manual planning register | Compatibility owners, caller evidence, replay/provenance evidence, Package 2 register | Compatibility surface added/removed; retirement evidence gathered; compatibility behavior change planned | Manual edit; verify row has owner, evidence, replay/provenance classification, retirement prerequisites, and status | Confirm register update does not approve retirement by itself. |
| Feature-lane verification guide | `docs/feature_lane_verification.md` | Manual workflow guide | Package 1 guide, lane owners, governance/compatibility docs | New implementation lane; new governance/contract package; link targets change | Manual edit; verify links | Confirm the guide routes to authorities and does not duplicate policy tables. |
| Generated documentation appendices | `docs/generated_documentation_appendices.md` | Manual generation strategy | Existing executable registries and generated-output conventions | Generated appendix candidate added; authoritative source or destination changes; future registry package approved | Manual edit; verify every candidate has source, destination, owner, trigger, verification, and reviewer expectations | Confirm the strategy does not introduce generators or move authority into docs. |
| Backend contract registry | `docs/backend_contract_registry.md` | Manual backend contract registry | `game/config.py`, `game/model_routing.py`, `game/gm.py`, `game/api_upstream_preflight.py`, `game/upstream_dependent_run_gate.py`, `game/upstream_dependent_run_gate_presentation.py`, `docs/model_routing_architecture.md`, `docs/compatibility_residue_register.md` | Backend-facing contract shape, owner, compatibility requirement, version status, provider diagnostics, preflight/run-gate behavior, or verification requirement changes | Manual edit; verify source references, links, and focused backend tests when implementation behavior changes | Confirm the registry documents existing backend behavior and does not introduce routing, provider, replay, provenance, CI, or governance behavior changes. |
| Ruleset contract registry | `docs/ruleset_contract_registry.md` | Manual ruleset contract registry | `game/scene_actions.py`, `game/affordances.py`, `game/skill_checks.py`, `game/combat.py`, `game/conditions.py`, `game/noncombat_resolution.py`, `game/state_authority.py`, `game/schema_contracts.py`, `game/validation.py`, `game/validation_layer_contracts.py`, `tests/validation_coverage_registry.py`, related architecture docs | Ruleset-facing contract shape, owner, lifecycle, compatibility requirement, replay/provenance implication, version status, mechanics verification, or future ruleset extension boundary changes | Manual edit; verify source references, links, and focused ruleset/mechanics tests when behavior changes | Confirm the registry documents existing ruleset-facing behavior and does not introduce rulesets, gameplay changes, replay/provenance changes, CI, or governance behavior changes. |
| Version and provenance contract registry | `docs/version_and_provenance_contract_registry.md` | Manual version/provenance contract registry | Replay/provenance helpers, Final Emission metadata, runtime lineage helpers, schema/report version constants, generated-artifact manifests, compatibility register | Versioned artifact, provenance metadata, replay-sensitive lineage, generated artifact lineage, compatibility lineage, or future registry versioning changes | Manual edit; verify source references, links, and focused replay/provenance/reporting tests when implementation behavior changes | Confirm the registry documents existing version/provenance behavior and does not introduce versioning behavior, provenance generation, replay schema changes, runtime changes, CI, or governance enforcement. |
| Generated audit reports | `docs/audits/*.md`, `docs/audits/*.csv`, `artifacts/**` where a generator or footer exists | Generated or retained evidence | Generator named in report footer, script, tool, or test helper | Generator source changes; generated output drift; reviewer requests refreshed evidence | Use named generator/check command; do not invent a refresh command | Confirm generated output is not edited by hand and historical evidence is not rewritten. |
| Replay governance registry docs | `docs/testing/replay_governance_registry.md`, `docs/testing/replay_governance_traceability_contract.md` | Manual docs for executable governance contracts | `tests/replay_governance_registry.py`, `tests/replay_governance_contract.py`, `tests/replay_governance_traceability_contract.py`, approval contract | Governance decision vocabulary or registry record shape changes | Manual docs plus focused pytest named in those docs | Confirm docs record existing intent and do not invent new replay policy. |
| Validation coverage registry | `tests/validation_coverage_registry.py` and `docs/objective12_validation_contract.md` | Executable registry plus manual contract doc | Validation coverage registry owner and audit tool | Feature coverage ownership changes; required surfaces change | `python -m pytest tests/test_validation_coverage_registry.py -q`; `python tools/validation_coverage_audit.py --strict` | Confirm registry maps validation ownership and does not score gameplay. |
| Future backend/ruleset/contract registries | Future contract docs/registries | Future executable/manual contract surfaces | Contract owner named by future package | Contract publication, field addition, provider/ruleset support expansion | Follow the package-specific refresh command when published; otherwise manual review only | Stop if no approved contract package exists. Do not publish contracts from a refresh-only change. |

## Refresh Triggers

A governance refresh is required when a change does any of the following:

- adds, removes, renames, or reclassifies tests that appear in governed
  inventory, ownership, or validation coverage;
- changes pytest markers, registry-owned paths, or ownership-registry entries;
- changes protected replay scenarios, protected replay status, protected
  observation fields, or protected/advisory replay boundaries;
- edits the split-owner acceptance matrix, owner literals, dashboard parity
  strings, or report generation logic;
- changes CI workflow commands, hard-fail/informational/deferred placement, or
  local reproduction commands;
- changes a compatibility surface, gathers retirement evidence, or plans
  compatibility cleanup;
- changes generated-doc source registries or generator scripts;
- changes backend-facing contract shape, backend compatibility expectations,
  provider diagnostics, preflight/run-gate behavior, or backend verification
  requirements;
- changes ruleset-facing contract shape, lifecycle, compatibility expectations,
  mechanics verification, replay/provenance classification, or future ruleset
  extension boundaries;
- changes versioned artifact shape, provenance metadata, replay-sensitive
  lineage, generated artifact lineage, compatibility lineage, or future
  registry versioning expectations;
- changes ownership doctrine, direct-owner suite assignments, or compatibility
  residue classification;
- publishes or updates a future backend, ruleset, or version/provenance contract
  registry through an approved package.

A governance refresh is usually not required when a change is a narrow runtime
fix that leaves test inventory, protected replay fields, generated reports,
registry rows, CI commands, ownership docs, and compatibility surfaces untouched.

## Authority Mapping

| Question | Start Here | Authority Boundary |
|---|---|---|
| Which verification lane applies? | `docs/feature_lane_verification.md` | Routing guide only; it does not own policy. |
| Which compatibility surfaces exist? | `docs/compatibility_residue_register.md` | Planning register; does not retire behavior. |
| Which CI commands are hard-fail or informational? | `docs/convergence_ci_inventory.md` plus workflow files | Workflow files execute CI; inventory documents parity and navigation. |
| Which protected replay fields are generated in the manifest? | `tests/helpers/golden_replay_projection.py::PROTECTED_OBSERVATION_FIELDS` | Registry is source; manifest section is generated. |
| Which protected replay scenarios are acceptance-blocking? | `docs/testing/protected_replay_manifest.md` and `tests/helpers/protected_replay_registry.py` | Manifest states policy; registry is mechanical scenario source. |
| Which tests are registry-owned for governance inventory? | `tests/test_inventory_governance.json` and `tools/test_audit.py --check` | JSON is generated; tool and ownership registry derive/check it. |
| Which split-owner rows are canonical? | `tests/helpers/failure_classification_sync.py::SPLIT_OWNER_ACCEPTANCE_MATRIX` | Report is generated from matrix; check script is CI-canonical. |
| Which backend contracts exist? | `docs/backend_contract_registry.md` | Manual contract registry; implementation modules remain authoritative. |
| Which ruleset contracts exist? | `docs/ruleset_contract_registry.md` | Manual contract registry; implementation modules remain authoritative. |
| Which version/provenance contracts exist? | `docs/version_and_provenance_contract_registry.md` | Manual contract registry; implementation modules, helpers, manifests, and scripts remain authoritative. |
| Which ownership doctrine applies? | `docs/architecture_ownership_ledger.md` | Manual doctrine; executable tests enforce focused slices. |
| Which replay governance decisions exist? | `tests/replay_governance_registry.py` and docs under `docs/testing/` | Registry records existing intent; policy changes need separate approval. |

## Refresh Sequence

Use this order for governance-sensitive changes:

1. Identify the feature lane in `docs/feature_lane_verification.md`.
2. If compatibility is touched, update or consult
   `docs/compatibility_residue_register.md` before changing behavior.
3. Update the executable source first: registry, helper constant, CI workflow,
   contract module, or source matrix.
4. Regenerate generated outputs using the existing command named by the source
   doc or generated artifact.
5. Update manual navigation docs only where they point to changed commands,
   sources, ownership boundaries, or status.
6. Run the focused check command for the affected governance area.
7. Review `git status --short` and confirm no protected out-of-scope files were
   changed.
8. Record verification in the implementation closeout for the package or PR.

## Reviewer Checklist

- Is the changed artifact generated, manual, or executable source?
- If generated, was the existing generator used instead of hand editing?
- If manual, does it point to authoritative sources rather than duplicating
  executable tables?
- Are refresh triggers documented for every governed artifact touched?
- Are protected replay acceptance, diagnostic replay, and advisory reports kept
  distinct?
- Are hard-fail, informational, and deferred CI statuses unchanged unless the
  package explicitly approved a policy change?
- Are ownership ledger changes supported by owner tests or repository evidence?
- Is compatibility retirement avoided unless a separate retirement package
  approved it?
- Are future contracts referenced as future surfaces rather than published by
  this workflow?
- Did the change avoid production code, runtime behavior, tests, governance
  logic, replay schemas, compatibility implementations, and generated artifacts
  unless explicitly in scope?

## Common Mistakes

- Editing `docs/testing/protected_replay_manifest.md` generated field rows by
  hand instead of running `tools/refresh_protected_replay_manifest.py`.
- Editing `docs/audits/BU15_split_owner_acceptance_matrix.md` without refreshing
  from `SPLIT_OWNER_ACCEPTANCE_MATRIX`.
- Updating `tests/TEST_AUDIT.md` counts while leaving
  `tests/test_inventory_governance.json` stale.
- Adding a new governance check to `tests/test_ownership_registry.py` when a
  focused governance owner module already exists.
- Duplicating CI command lists in multiple docs instead of linking to
  `docs/convergence_ci_inventory.md`.
- Treating compatibility register status as retirement approval.
- Changing generated artifacts under `artifacts/` as proof of behavior without
  naming the generator and verification command.

## Escalation Rules

Stop and request a separate planning or implementation package if the change
requires any of the following:

- a new CI hard-fail gate or promotion from informational/deferred to hard-fail;
- a new protected replay acceptance field, scenario class, or threshold not
  already approved by manifest policy;
- compatibility retirement or import-path removal;
- ownership authority moving between runtime modules, test suites, docs, or
  generated artifacts;
- backend, ruleset, or version/provenance contract publication;
- new governance automation or generated-doc tooling;
- replay schema changes or protected observation semantics changes;
- production code changes made only to satisfy documentation refresh.

## Stop Conditions

For a governance refresh package, stop immediately if verification shows:

- production code changed;
- governance tests or CI workflow behavior changed without approval;
- generated artifacts were edited by hand;
- protected replay acceptance behavior changed;
- compatibility behavior changed or was retired;
- ownership semantics changed;
- a future contract registry would need to be created before documentation can
  remain truthful.

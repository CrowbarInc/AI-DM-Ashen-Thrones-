# AR-BU - Ruleset Contract Registry Implementation

## 1. Executive Summary

Package 7 was implemented by creating a centralized Ruleset Contract Registry at
`docs/ruleset_contract_registry.md`.

The registry documents the existing ruleset-facing contracts for the current
engine-first, PF1e-inspired gameplay posture. It records contract identifiers,
canonical owners, authoritative implementations, repository locations, purpose,
consumers, lifecycle expectations, compatibility requirements, replay and
provenance implications, version status, verification methods, and future
extensibility notes.

This package is documentation-only. It does not introduce new rulesets, modify
gameplay logic, change replay schemas, alter provenance behavior, update runtime
routing, change governance policy, or modify CI behavior.

## 2. Ruleset Contract Inventory

| Contract ID | Contract | Authoritative Implementation |
|---|---|---|
| RCR-01 | Ruleset identity and current gameplay posture | `docs/ai_gm_contract.md`, `docs/system_overview.md`, `docs/README.md` |
| RCR-02 | Action normalization contract | `game/scene_actions.py::normalize_scene_action`, `normalize_scene_actions_list` |
| RCR-03 | Affordance availability and action-option contract | `game/affordances.py`, `game/schema_contracts.py` |
| RCR-04 | Skill-check decision and deterministic roll contract | `game/skill_checks.py::should_trigger_check`, `resolve_skill_check` |
| RCR-05 | Combat mechanics result contract | `game/combat.py`, `game/models.py::CombatEngineResult` |
| RCR-06 | Condition/effect contract | `game/conditions.py` |
| RCR-07 | Non-combat resolution framework | `game/noncombat_resolution.py`, including `NONCOMBAT_FRAMEWORK_VERSION` |
| RCR-08 | State authority domain contract | `game/state_authority.py`, `docs/state_authority_model.md` |
| RCR-09 | Runtime schema normalization and compatibility contract | `game/schema_contracts.py` |
| RCR-10 | Scene/content validation contract | `game/validation.py`, `docs/content_lint_pipeline.md` |
| RCR-11 | Validation-layer responsibility contract | `game/validation_layer_contracts.py`, `docs/validation_layer_separation.md` |
| RCR-12 | Realization/final-emission boundary contract for mechanics outputs | `game/final_emission_boundary_contract.py`, `game/realization_authority.py`, `game/realization_provenance.py`, `game/upstream_response_repairs.py` |
| RCR-13 | Gameplay validation coverage contract | `tests/validation_coverage_registry.py`, `docs/objective12_validation_contract.md` |
| RCR-14 | Ruleset compatibility boundary | `docs/compatibility_residue_register.md`, especially `CR-12` |

The registry explicitly states that the repository does not currently expose a
pluggable ruleset loader. Future alternate rulesets must be introduced through
approved identity, capability, state, schema, validation, compatibility, replay,
and provenance contracts.

## 3. Ownership Mapping

| Owner Category | Registry Responsibility |
|---|---|
| Architecture/gameplay contract owner | Engine-first doctrine and current ruleset posture. |
| Scene/action owner | Canonical action normalization and stable action types. |
| Affordance owner | Action option generation, dedupe, ranking, and pruning. |
| Skill-check owner | Check requirement decisions and deterministic skill roll results. |
| Combat owner | Supported combat action resolution and combat result payloads. |
| Conditions owner | Condition effect interpretation for mechanics. |
| Non-combat resolution owner | Canonical non-combat taxonomy, version, fail-closed normalization, and domain delegation. |
| State authority owner | Domain registry, read matrix, mutation guard helpers, and cross-domain allow-list. |
| Schema contracts owner | Runtime payload normalization, validation helpers, and legacy adapters. |
| Scene validation owner | Strict authored scene structure rules and issue collection. |
| Validation-layer owner | Phase responsibility vocabulary and forward-read lattice. |
| Final Emission/realization owners | Last-mile legality, packaging, and provenance boundaries for emitted output. |
| Validation coverage owner | Mapping features to existing verification surfaces. |
| Compatibility planning owner | Compatibility inventory and retirement prerequisites. |

The registry also records non-ownership boundaries so ruleset work does not move
mechanics truth into GPT, prompt construction, Final Emission, replay projection,
backend routing, or documentation prose.

## 4. Consumer Mapping

| Consumer | Consumed Contracts |
|---|---|
| `game.api` action/chat pipeline | Action normalization, skill/combat resolution, non-combat framework, state authority, realization boundary. |
| Exploration/social engines | Action normalization, skill checks, conditions, non-combat framework, schema contracts. |
| CTIR/prompt adapter | Non-combat framework, state authority, validation-layer separation. |
| UI/client action surfaces | Action normalization, affordance contract, schema contracts. |
| Scene/content authoring workflow | Action normalization, schema contracts, scene/content validation. |
| Final Emission and realization | Validation-layer separation and realization/provenance boundaries. |
| Replay/projection helpers | Combat results, non-combat framework, state authority, realization/provenance boundaries, compatibility. |
| Governance and validation reviewers | All RCR contracts. |

## 5. Compatibility Assessment

| Compatibility Surface | Status | Requirement |
|---|---|---|
| Legacy scene action strings and legacy affordance dicts | Active | Preserve adaptation through `normalize_scene_action` and schema helpers. |
| CamelCase/snake_case action target mirrors | Active | Preserve UI/API target key compatibility. |
| Skill-check `difficulty` plus `dc` | Active | Keep `dc` as backward-compatible alias. |
| Schema-contract legacy adapters | Active | Maintain adapters and metadata parking; see compatibility register `CR-12`. |
| Current single PF1e-inspired mechanics posture | Active | Do not imply alternate ruleset support before identity/loading/capability contracts exist. |
| Final Emission/provenance compatibility fields | Active | Do not collapse ruleset mechanics, realization provenance, and replay projection fields. |

## 6. Lifecycle and Version Status

| Area | Lifecycle | Version Status |
|---|---|---|
| Current ruleset identity | Manual doctrine; no loader | Unversioned. |
| Action normalization | Runtime ingress | Stable unversioned shape. |
| Affordance contract | Runtime read-side generation | Stable unversioned shape. |
| Skill checks | Engine mechanics | Stable unversioned mechanics contract. |
| Combat resolution | Engine mechanics | Stable unversioned result shape. |
| Conditions | Engine mechanics support | Stable unversioned helper contract. |
| Non-combat framework | Runtime resolution and CTIR-facing normalization | Versioned: `2026.04.noncombat.v1`. |
| State authority | Executable registry/guards | Stable unversioned registry. |
| Schema contracts | Runtime boundary normalization | Stable unversioned helpers. |
| Scene validation | Runtime/author-time structure validation | Stable unversioned validation contract. |
| Validation-layer separation | Executable governance registry | Stable unversioned registry. |
| Realization/provenance boundary | Runtime finalization/provenance packaging | Stable mixed contract surfaces. |
| Validation coverage | Executable test coverage registry | Active registry with structural validation. |
| Compatibility boundary | Manual planning register | Manual status/lifetime rows. |

## 7. Verification Strategy

Verification was documentation-focused:

1. Confirm `docs/ruleset_contract_registry.md` exists.
2. Confirm referenced authoritative implementation files exist.
3. Search for registry anchors, contract identifiers, version strings, and
   cross-links.
4. Confirm discoverability links exist in governance and architecture docs.
5. Confirm no gameplay, test, script, CI, data, or artifact files were modified
   by AR-BU.
6. Review the registry for required fields: canonical owner, authoritative
   implementation, repository location, purpose, consumers, lifecycle,
   compatibility, replay/provenance classification, version status,
   verification, and extensibility notes.

Focused ruleset/mechanics tests were not run because this package did not
change gameplay behavior. The registry names the required focused commands for
future behavioral changes.

## 8. Verification Results

| Verification | Result |
|---|---|
| `Test-Path docs\ruleset_contract_registry.md` | Passed. |
| `Test-Path` for referenced implementation files: `game\scene_actions.py`, `game\affordances.py`, `game\skill_checks.py`, `game\combat.py`, `game\conditions.py`, `game\noncombat_resolution.py`, `game\state_authority.py`, `game\schema_contracts.py`, `game\validation.py`, `game\validation_layer_contracts.py`, `tests\validation_coverage_registry.py` | Passed. |
| `rg` for registry anchors and cross-links in `docs/ruleset_contract_registry.md`, `docs/governance_refresh_workflow.md`, `docs/generated_documentation_appendices.md`, `docs/system_overview.md` | Passed. |
| Scope check for AR-BU | Passed: AR-BU changed documentation only. No gameplay implementation, ruleset implementation, replay schema, provenance behavior, runtime routing, CI, data, or artifacts were changed. |

Existing dirty-worktree changes from earlier packages remain present and were
not reverted.

## 9. Risks

| Risk | Assessment | Mitigation |
|---|---|---|
| Registry implies alternate ruleset support exists | Low. The registry states there is no pluggable ruleset loader today. | Future ruleset support requires approved identity/capability/loading contracts. |
| Documentation becomes perceived gameplay authority | Low. Each row names implementation modules as authoritative. | Registry maintenance rules prohibit moving authority into docs. |
| Compatibility retirement by implication | Low. Compatibility rows point back to the Compatibility Residue Register. | Retirement requires a separate package with evidence. |
| Replay/provenance boundary confusion | Low. Rows classify replay/provenance implications and keep mechanics separate from realization provenance. | Reviewer checklist directs future changes to replay/provenance review when touched. |
| Future ruleset conditionals scatter across unrelated modules | Medium if future work bypasses the registry. | Registry requires future rulesets to integrate through action, mechanics, state, validation, compatibility, replay, and provenance contracts. |

## 10. Package Closeout

Was the Ruleset Contract Registry successfully implemented?

Yes. `docs/ruleset_contract_registry.md` now centralizes existing ruleset-facing
contracts and identifies owner, authoritative implementation, lifecycle,
compatibility, replay/provenance, version, verification, and extensibility
requirements.

Are ruleset contracts now centrally discoverable?

Yes. The registry is linked from `docs/governance_refresh_workflow.md`,
`docs/generated_documentation_appendices.md`, and `docs/system_overview.md`.

Can future rulesets integrate using explicit architectural contracts?

Yes. Future ruleset work can now begin from explicit RCR rows and must publish
identity/capability/state/schema/verification expectations before changing
behavior.

## 11. Campaign Assessment

Campaign 5 can proceed. Ruleset contract coverage is sufficient for current
repository evidence: the registry covers current gameplay posture, action
normalization, affordances, skill checks, combat, conditions, non-combat
resolution, state authority, schema compatibility, scene validation,
validation-layer separation, realization/provenance boundaries, validation
coverage, and compatibility.

Additional Package 7 refinement is not required unless future repository
evidence introduces an actual ruleset loader or alternate ruleset behavior.

## 12. Recommended Next Cycle

Recommendation: Proceed to Package 8.

Repository evidence:

| Evidence | Result |
|---|---|
| Engine-first doctrine | `docs/ai_gm_contract.md` and `docs/system_overview.md` state engine authority and GPT narration-only boundaries. |
| Ruleset mechanics modules | `game/skill_checks.py`, `game/combat.py`, `game/conditions.py`, `game/noncombat_resolution.py`, and related modules define current mechanics contracts. |
| Versioned ruleset-facing surface | `game/noncombat_resolution.py` exposes `NONCOMBAT_FRAMEWORK_VERSION = "2026.04.noncombat.v1"`. |
| Compatibility evidence | `docs/compatibility_residue_register.md` row `CR-12` documents schema-contract legacy adapter compatibility. |
| Governance linkage | Governance and generated-doc strategy now reference `docs/ruleset_contract_registry.md`. |
| Scope preservation | AR-BU changed documentation only and did not alter gameplay behavior. |

## 13. Files Required for External Review

### Required

| File | Reason |
|---|---|
| `docs/ruleset_contract_registry.md` | New centralized ruleset contract registry. |
| `docs/governance_refresh_workflow.md` | Governed artifact cross-link and refresh trigger for ruleset contract changes. |
| `docs/generated_documentation_appendices.md` | Updated generated/manual source classification for ruleset contracts. |
| `docs/system_overview.md` | Architecture discoverability link to the registry. |
| `AR-BU_ruleset_contract_registry_implementation.md` | Package implementation closeout. |

### Optional

| File | Reason |
|---|---|
| `docs/ai_gm_contract.md` | Engine-first gameplay doctrine. |
| `game/scene_actions.py` | Action normalization authority. |
| `game/affordances.py` | Affordance generation authority. |
| `game/skill_checks.py` | Skill-check mechanics authority. |
| `game/combat.py` | Combat mechanics authority. |
| `game/conditions.py` | Condition/effect authority. |
| `game/noncombat_resolution.py` | Versioned non-combat framework authority. |
| `game/state_authority.py` and `docs/state_authority_model.md` | Runtime state authority contract. |
| `game/schema_contracts.py` | Runtime schema and compatibility adapter authority. |
| `game/validation.py` | Scene/content validation authority. |
| `game/validation_layer_contracts.py` and `docs/validation_layer_separation.md` | Validation-layer responsibility authority. |
| `tests/validation_coverage_registry.py` and `docs/objective12_validation_contract.md` | Gameplay validation coverage authority. |
| `docs/compatibility_residue_register.md` | Compatibility evidence and retirement prerequisites. |

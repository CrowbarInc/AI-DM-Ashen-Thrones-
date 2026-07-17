# Ruleset Contract Registry

This registry centralizes ruleset-facing architectural contracts currently
present in the repository. It is documentation-only. It does not introduce a
new ruleset, modify gameplay logic, alter replay schemas, change provenance
behavior, update runtime routing, add governance enforcement, or move
implementation authority from code into documentation.

## Registry Scope

The current repository implements one engine-first, PF1e-inspired gameplay
ruleset through deterministic modules rather than a pluggable ruleset loader.
Ruleset-facing contracts are therefore the stable interfaces around action
normalization, mechanics resolution, state authority, schema normalization,
validation, repair/legality boundaries, diagnostics, and compatibility.

Future alternate rulesets must integrate through explicit contracts instead of
adding ruleset conditionals in prompt, Final Emission, replay, or backend code.

## Contract Inventory

| Contract ID | Contract | Canonical Owner | Authoritative Implementation | Repository Location | Purpose | Consumers | Lifecycle Expectations | Compatibility Requirements | Replay Implications | Provenance Implications | Version Status | Verification Method | Extensibility Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RCR-01 | Ruleset identity and current gameplay posture | Architecture/gameplay contract owner | Manual docs and current engine modules | `docs/ai_gm_contract.md`, `docs/system_overview.md`, `docs/README.md` | State that the engine owns mechanics/state and GPT narrates only; current mechanics are PF1e-inspired but not exposed as a pluggable ruleset loader. | Maintainers, feature planners, future ruleset package authors. | Manual doctrine; refresh when an approved package introduces ruleset identity, capabilities, or alternate ruleset loading. | Do not imply alternate ruleset support before implementation exists. Preserve engine-first authority. | Low. Replay observes finalized outcomes, not a formal ruleset id today. | Low. Ruleset identity is not realization provenance today. | Manual, unversioned doctrine. | Link/source review; no gameplay behavior change. | Future ruleset work should publish explicit identity/version/capability fields before behavior branches. |
| RCR-02 | Action normalization contract | Scene/action owner | `normalize_scene_action`, `normalize_scene_actions_list`, action type constants | `game/scene_actions.py` | Normalize legacy strings, legacy affordance dicts, and structured actions into a stable action shape. | `game.api`, `game.affordances`, exploration/noncombat flow, schema boundary tests, UI-facing action consumers. | Runtime ingress contract; keep shape stable and explicit. | Preserve legacy string/dict adaptation and mirrored camelCase/snake_case target keys until a retirement package approves removal. | Medium. Action shape can affect resolved turns and replay-observed outcomes. | Low. Normalization is input structure, not content provenance. | Stable unversioned shape. | `tests/test_validation_journal_affordances.py`, `tests/test_affordance_generation.py`, `tests/test_runtime_schema_boundaries.py`, `tests/test_schema_contracts.py`. | Future rulesets should add action types through this boundary and corresponding schema/affordance tests. |
| RCR-03 | Affordance availability and action-option contract | Affordance owner | `generate_scene_affordances`, `get_available_affordances`; canonical affordance schema helpers | `game/affordances.py`, `game/schema_contracts.py` | Produce bounded, deduped, action-oriented options from scenes, exits, interactables, objects, NPCs, and pending leads. | API/client payloads, UI action buttons, validation journal tests, scene/action flows. | Runtime read-side generation; may consume state but should not mutate mechanics truth. | Preserve 3-5 action-option expectation and legacy affordance adaptation. | Medium. Affordance choice can feed deterministic resolution and replay paths. | Low. Affordance generation does not own realization provenance. | Stable unversioned shape with schema-contract support. | `tests/test_affordance_generation.py`, `tests/test_affordance_canonical_pipeline.py`, `tests/test_validation_journal_affordances.py`. | Alternate rulesets can contribute domain actions by producing canonical affordance rows rather than bypassing action normalization. |
| RCR-04 | Skill-check decision and deterministic roll contract | Skill-check owner | `should_trigger_check`, `resolve_skill_check`, DC constants | `game/skill_checks.py` | Decide whether exploration/social actions require checks and resolve deterministic d20 skill checks. | `game.exploration`, `game.social`, tests, prompt narration consumers through resolved results. | Engine-owned mechanics; GPT narrates the result only. | Preserve `difficulty` plus backward-compatible `dc`; preserve deterministic seed behavior for non-live checks. | High. Skill outcomes can appear in protected turn payloads, logs, and downstream narration. | Low to medium. Skill result metadata explains engine outcomes but is not realization provenance. | Stable unversioned mechanics contract. | `tests/test_skill_checks.py`, `tests/test_exploration_skill_checks.py`, `tests/test_social.py`. | Future rulesets may replace or extend DC/roll policy only behind explicit ruleset identity and focused tests. |
| RCR-05 | Combat mechanics result contract | Combat owner | Initiative, attack, skill, spell, enemy-turn resolvers; `CombatEngineResult` | `game/combat.py`, `game/models.py::CombatEngineResult` | Resolve supported combat actions and return canonical combat result dicts. | `game.api` action endpoint, prompt/message construction, combat tests, transcript/replay flows. | Engine-owned state mutation and result creation; narration is downstream. | Preserve canonical result keys and supported action behavior unless a gameplay package approves change. | High. Combat outcomes may persist and appear in replay/transcript fixtures. | Low. Combat result provenance is engine outcome context, not realization fallback provenance. | Stable unversioned result shape by dataclass/dict convention. | `tests/test_combat_resolution.py`, transcript/API tests involving combat, model/schema boundary tests. | New rulesets should define combat capability and result compatibility before adding alternate combat resolution. |
| RCR-06 | Condition/effect contract | Conditions owner | Condition helpers and effect aggregation | `game/conditions.py` | Apply condition definitions to AC, action availability, attacks, spells, saves, and skill penalties. | `game.combat`, `game.skill_checks`, condition tests, storage condition definitions. | Runtime mechanics support; definitions may be loaded but interpretation lives here. | Preserve effect-key semantics such as `no_actions`, `no_attacks`, `no_spells`, `skill_penalty`, AC modifiers. | Medium. Conditions alter deterministic outcomes observed later. | Low. Condition effects are mechanics context, not realization provenance. | Stable unversioned helper contract. | `tests/test_skill_checks.py`, `tests/test_combat_resolution.py`, condition-related gameplay tests. | Alternate rulesets should either map conditions to this effect vocabulary or publish a successor condition contract. |
| RCR-07 | Non-combat resolution framework | Non-combat resolution owner | `NONCOMBAT_FRAMEWORK_VERSION`, classification, normalization, resolver attachment | `game/noncombat_resolution.py` | Classify exploration/social/downtime-style actions, delegate to domain engines, and normalize machine-readable non-combat outcomes. | `game.api`, CTIR builder/consumers, prompt adapter, objective 8 authority tests. | Versioned framework; no LLM calls or narration-driven mechanics inside the contract. | Preserve fail-closed ambiguous/unsupported behavior and canonical `noncombat_resolution` embedding. | High. CTIR and replay-adjacent consumers observe normalized non-combat meaning. | Low to medium. It records authority domains and authoritative outputs but does not own realization provenance. | Versioned: `2026.04.noncombat.v1`. | `tests/test_noncombat_resolution.py`, `tests/test_noncombat_runtime_integration.py`, `tests/test_ctir_noncombat_consumption.py`, `tests/test_objective8_block_d_authority_lock.py`. | Future rulesets can extend non-combat kinds only with a framework-version review and CTIR/prompt compatibility tests. |
| RCR-08 | State authority domain contract | State authority owner | Domain registry, read matrix, mutation guards, cross-domain write allow-list | `game/state_authority.py`, `docs/state_authority_model.md` | Define authoritative runtime state domains and guarded mutation/read boundaries. | Runtime domain owners, API orchestration, storage/world/interaction/journal modules, governance tests. | Registry/guard layer only; domain behavior remains in domain modules. | Preserve five-domain model unless a separate architecture package approves a new domain. | High. Replay depends on stable state and publication semantics. | Medium. Mutation traces can feed diagnostics but are not realization provenance. | Stable executable registry, unversioned. | `tests/test_state_authority.py`, domain-owner tests, `tools/validation_layer_audit.py` where relevant. | Alternate rulesets must not back-write truth from prompt or emitted text; new state stores require explicit domain mapping. |
| RCR-09 | Runtime schema normalization and compatibility contract | Schema contracts owner | Normalizers, validators, legacy adapters for engine results, world updates, affordances, targets, clues, projects, clocks | `game/schema_contracts.py` | Normalize supported runtime payload shapes and park compatible legacy fields safely. | Runtime boundaries, affordances, world/clue/clock helpers, tests, compatibility register. | Active serialization/API compatibility surface. | Preserve legacy adapters until data/caller evidence supports retirement. | Medium. Persisted/replayed payloads may contain legacy shapes. | Low. Unknown legacy metadata is explanatory unless a domain owner consumes it explicitly. | Stable unversioned schema helpers. | `tests/test_schema_contracts.py`, `tests/test_runtime_schema_boundaries.py`, `tests/test_validation_journal_affordances.py`, compatibility register review. | Future rulesets should define payload normalization here or in an approved successor registry. |
| RCR-10 | Scene/content validation contract | Scene validation owner | Strict scene validation and issue collection | `game/validation.py`, `docs/content_lint_pipeline.md` | Validate authored scene references, required fields, action ids, exits, clues, and interactables. | Runtime scene loading/fail-fast paths, content lint, scene validation tests, authoring workflow. | Strict runtime validation plus author-time issue collection over the same rules. | Preserve fail-fast behavior where invoked; content lint may collect without changing runtime semantics. | Medium. Scene validity shapes available actions and replay setup. | Low. Scene validation is authoring/runtime structure, not realization provenance. | Stable unversioned validation contract. | `tests/test_scene_validation.py`, content lint tests, scene graph tests. | Future rulesets with new content fields should extend validation and lint together. |
| RCR-11 | Validation-layer responsibility contract | Validation-layer owner | Layer ids, responsibility domains, read matrix predicates | `game/validation_layer_contracts.py`, `docs/validation_layer_separation.md` | Keep truth, structure, expression, legality, and scoring responsibilities separate. | Gate/planner/evaluator owners, governance tests, audits, future ruleset reviewers. | Governance contract; not runtime enforcement by itself. | Do not let ruleset work move mechanics truth into GPT, prompt, Final Emission, or offline evaluators. | Medium. Layer drift can affect replay stability indirectly. | Medium. Provenance fields must not be authored by the wrong validation layer. | Stable executable registry, unversioned. | `tests/test_validation_layer_contracts.py`, `tests/test_validation_layer_separation_runtime.py`, `tools/validation_layer_audit.py`. | Alternate rulesets must plug into engine truth and validation layers without collapsing phase ownership. |
| RCR-12 | Realization/final-emission boundary contract for mechanics outputs | Final Emission/realization boundary owners | Final emission boundary, realization authority/provenance, upstream response repair boundaries | `game/final_emission_boundary_contract.py`, `game/realization_authority.py`, `game/realization_provenance.py`, `game/upstream_response_repairs.py`, `docs/realization_seam_inventory.md` | Ensure mechanics outcomes are narrated without moving mechanics truth into realization or final-emission repair layers. | Final Emission gate, prompt/GPT output path, protected replay projection, provenance tests. | Downstream legality/packaging only; mechanics truth must already be decided by engine/planner contracts. | Preserve existing fallback/provenance compatibility until separately retired. | High. Finalized output and metadata are replay-observed. | High. Realization provenance is explicit and must remain separate from ruleset mechanics authority. | Stable mixed contract surfaces, no single ruleset version. | Final Emission boundary/provenance tests, split-owner checks, protected replay focused tests when touched. | Future rulesets should produce engine outcomes that realization consumes; Final Emission must not branch on ruleset mechanics directly. |
| RCR-13 | Gameplay validation coverage contract | Validation coverage owner | Machine-readable coverage registry and validation contract docs | `tests/validation_coverage_registry.py`, `docs/objective12_validation_contract.md` | Map feature/domain validation obligations to existing tests, tools, scenarios, and gauntlets. | Reviewers, maintainers, validation tooling, future ruleset package authors. | Governance/testing only; does not score or enforce gameplay behavior. | Do not duplicate evaluator logic or scatter validation policy into prose-only fields. | Low to medium. Coverage maps protect replay/behavior indirectly. | Low. Coverage registry does not author runtime provenance. | Active executable registry for coverage declarations. | `tests/test_validation_coverage_registry.py`, `tools/validation_coverage_audit.py --strict`. | Future ruleset work should add/adjust coverage rows when validation obligations change. |
| RCR-14 | Ruleset compatibility boundary | Compatibility planning owner plus domain owners | Compatibility residue rows for schema adapters and future ruleset surfaces | `docs/compatibility_residue_register.md`, especially `CR-12`; this registry | Track historical payload, schema, and ruleset-facing compatibility that cannot be retired by intuition. | Maintainers, future compatibility retirement packages, contract reviewers. | Manual planning surface; compatibility changes require evidence and focused tests. | Do not retire legacy action/schema adapters or compatibility behavior from this registry alone. | Medium. Compatibility changes may affect persisted/replayed historical payloads. | Low. Compatibility metadata should not become behavior selection without owner approval. | Manual status; compatibility rows own lifetime/status. | Compatibility register review plus focused tests for touched surface. | Future ruleset migrations should start with compatibility inventory and explicit retirement prerequisites. |

## Ownership Mapping

| Owner Category | Owns | Does Not Own |
|---|---|---|
| Architecture/gameplay contract owner | Engine-first doctrine and current ruleset posture. | Runtime mechanics behavior by prose alone. |
| Scene/action owner | Canonical action normalization and stable action types. | Mechanical outcome resolution. |
| Affordance owner | Action option generation, dedupe, ranking, and pruning. | State mutation or rules adjudication. |
| Skill-check owner | Check requirement decisions and deterministic skill roll results. | Narration of outcomes or scene content authoring. |
| Combat owner | Supported combat action resolution and combat result payloads. | Non-combat semantics or GPT expression. |
| Conditions owner | Condition effect interpretation for mechanics. | Condition definition authoring policy beyond loaded definitions. |
| Non-combat resolution owner | Canonical non-combat taxonomy, version, fail-closed normalization, and domain delegation. | Exploration/social domain internals or narration. |
| State authority owner | Domain registry, read matrix, mutation guard helpers, and cross-domain allow-list. | Domain behavior, persistence, prompt construction, or Final Emission. |
| Schema contracts owner | Runtime payload normalization, validation helpers, and legacy adapters. | Gameplay decisions based on normalized payloads. |
| Scene validation owner | Strict authored scene structure rules and issue collection. | Content lint scoring or runtime mechanics beyond scene validity. |
| Validation-layer owner | Phase responsibility vocabulary and forward-read lattice. | Runtime enforcement, scoring, or gameplay resolution. |
| Final Emission/realization owners | Last-mile legality, packaging, and provenance boundaries for emitted output. | Ruleset mechanics truth. |
| Validation coverage owner | Mapping features to existing verification surfaces. | New gameplay validation behavior or evaluator scoring. |
| Compatibility planning owner | Compatibility inventory and retirement prerequisites. | Compatibility retirement by documentation alone. |

## Consumer Mapping

| Consumer | Consumed Contracts | Notes |
|---|---|---|
| `game.api` action/chat pipeline | RCR-02, RCR-04, RCR-05, RCR-07, RCR-08, RCR-12 | Orchestrates action normalization, deterministic resolution, GPT narration, and final emission. |
| Exploration/social engines | RCR-02, RCR-04, RCR-06, RCR-07, RCR-09 | Consume normalized actions and mechanics helpers. |
| CTIR/prompt adapter | RCR-07, RCR-08, RCR-11 | Reads resolved-turn meaning; must not reconstruct ruleset semantics when canonical contracts exist. |
| UI/client action surfaces | RCR-02, RCR-03, RCR-09 | Receive canonical affordance/action shapes. |
| Scene/content authoring workflow | RCR-02, RCR-09, RCR-10 | Uses validation and lint-compatible scene/action schemas. |
| Final Emission and realization | RCR-11, RCR-12 | Consume engine/planner outcomes without owning mechanics truth. |
| Replay/projection helpers | RCR-05, RCR-07, RCR-08, RCR-12, RCR-14 | Observe finalized outcomes and metadata; must not redefine mechanics contracts. |
| Governance and validation reviewers | All RCR contracts | Use this registry to route future ruleset changes to owner files and tests. |

## Compatibility Assessment

| Compatibility Surface | Current Status | Requirement |
|---|---|---|
| Legacy scene action strings and legacy affordance dicts | Active | Keep adaptation through `normalize_scene_action` and schema helpers until a retirement package proves no consumers. |
| CamelCase/snake_case action target mirrors | Active | Preserve UI/API compatibility for target scene/entity/location keys. |
| Skill-check `difficulty` plus `dc` | Active | Keep `dc` as backward-compatible alias while `difficulty` remains canonical. |
| Schema-contract legacy adapters | Active | Maintain adapters and metadata parking for historical payloads; see compatibility register `CR-12`. |
| Current single PF1e-inspired mechanics posture | Active | Do not claim alternate ruleset support until explicit identity/loading/capability contracts exist. |
| Final Emission/provenance compatibility fields | Active | Do not collapse ruleset mechanics, realization provenance, and replay projection fields. |

## Lifecycle and Version Status

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

## Verification Requirements

| Change Type | Required Verification |
|---|---|
| Action normalization or affordance shape | `python -m pytest tests/test_validation_journal_affordances.py tests/test_affordance_generation.py tests/test_affordance_canonical_pipeline.py tests/test_runtime_schema_boundaries.py -q` |
| Skill checks | `python -m pytest tests/test_skill_checks.py tests/test_exploration_skill_checks.py -q` |
| Combat or condition mechanics | `python -m pytest tests/test_combat_resolution.py tests/test_skill_checks.py -q` plus affected API/transcript tests. |
| Non-combat framework or CTIR projection | `python -m pytest tests/test_noncombat_resolution.py tests/test_noncombat_runtime_integration.py tests/test_ctir_noncombat_consumption.py tests/test_objective8_block_d_authority_lock.py -q` |
| State authority domains or guards | `python -m pytest tests/test_state_authority.py -q` plus affected domain-owner tests. |
| Schema compatibility | `python -m pytest tests/test_schema_contracts.py tests/test_runtime_schema_boundaries.py -q` plus compatibility register review. |
| Scene/content validation | `python -m pytest tests/test_scene_validation.py -q` plus content-lint tests when author-time behavior changes. |
| Validation-layer responsibility | `python -m pytest tests/test_validation_layer_contracts.py tests/test_validation_layer_separation_runtime.py -q`; `python tools/validation_layer_audit.py` when applicable. |
| Realization/provenance boundary | Focused Final Emission boundary/provenance tests, split-owner checks, and protected replay checks for touched surfaces. |
| Coverage registry changes | `python -m pytest tests/test_validation_coverage_registry.py -q`; `python tools/validation_coverage_audit.py --strict`. |
| Documentation-only registry update | Link/source checks and `git status --short` scope check confirming no gameplay behavior changed. |

## Reviewer Checklist

- Does every ruleset-facing contract have a canonical owner and authoritative
  implementation?
- Is gameplay behavior still owned by implementation modules rather than this
  document?
- Are lifecycle and version expectations explicit?
- Are compatibility requirements recorded before any retirement work?
- Are replay and provenance implications classified without changing replay or
  provenance semantics?
- Does future ruleset work enter through action/schema/noncombat/state contracts
  instead of scattered conditionals in prompt, Final Emission, replay, or backend
  code?
- Did the change avoid gameplay logic, ruleset implementation, replay schema,
  provenance behavior, runtime routing, governance policy, CI behavior, and
  generated artifacts unless explicitly in scope?

## Maintenance Rules

- Update this registry when a ruleset-facing contract shape, owner, lifecycle,
  compatibility requirement, version status, verification method, or extension
  boundary changes.
- Do not implement alternate rulesets from this registry alone.
- Do not retire compatibility from this registry; use the Compatibility Residue
  Register and an approved retirement package.
- Do not treat GPT, prompt construction, Final Emission, replay projection, or
  backend routing as ruleset mechanics owners.
- Keep this registry manual until a future executable ruleset registry is
  approved.

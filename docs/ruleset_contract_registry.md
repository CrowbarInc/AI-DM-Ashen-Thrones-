# Ruleset Contract Registry

This registry centralizes ruleset-facing architectural contracts currently
present in the repository. It is the contract inventory. It does not itself
execute mechanics, modify gameplay routing, alter replay schemas, change
provenance behavior, or move implementation authority from code into
documentation.

A bounded executable boundary now exists at `game/ruleset_contract.py` and
`game/ruleset_registry.py` (RCR-15). That boundary selects an explicit
identity and version, discovers declared capabilities, and delegates
side-effect-free policy evaluation. It is not a plugin loader. Ordinary chat
consults it for one Pathfinder social skill check. Unmigrated Pathfinder modules remain explicit
legacy pathways.

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
| RCR-01 | Ruleset identity and current gameplay posture | Architecture/gameplay contract owner | Constitutional invariant plus RCR-15 | `docs/DEVELOPMENT_CONSTITUTION.md`, `docs/system_overview.md`, `docs/README.md`, RCR-15 | State that the core is independent of any one ruleset and GPT narrates only; Pathfinder 1e is the initial supported ruleset, not a plugin loader. | Maintainers, feature planners, future ruleset authors. | Refresh when a capability moves off a named legacy pathway. | Do not describe an identity-only ruleset as a playable implementation. Preserve engine authority over state transactions. | Low. Replay still observes finalized outcomes. RCR-15 is not on the turn spine. | Low. Ruleset identity is not realization provenance today. | Constitutional invariant; executable identity and version are RCR-15. | `tests/test_ruleset_boundary.py`; link/source review. | Future rulesets declare capabilities. They do not branch prompt, Final Emission, or replay code. |
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
| RCR-15 | Ruleset selection, capability discovery, and side-effect-free policy evaluation | Ruleset boundary owner | `get_ruleset`, `discover_capability`, `evaluate_policy`, `dispatch` | `game/ruleset_contract.py`, `game/ruleset_registry.py`; Pathfinder equipment delegation in `game/pf1e_equipment_policy.py` | Select an explicit ruleset identity and version, discover declared capabilities, and delegate a policy request to that authority only. | Ordinary chat calls this boundary for one social skill check. Other turns do not. | Closed registry. No filesystem scan, network access, or arbitrary code loading. Policy evaluation does not mutate state. | Unknown identities and unsupported versions are rejected. A ruleset that does not declare a capability does not inherit another ruleset. `supported` is not execution permission. | The social skill check commits through the core. Other capabilities have no turn-spine caller. | None. This boundary is not realization provenance. | `pf1e` version `1` delegates `equipment_policy` and resolves `social_skill_check`. `rules_light` version `1` and `scifi` version `1` are identity-only. | `tests/test_ruleset_boundary.py` and `tests/test_pf1e_equipment_policy.py`. | A future ruleset implements the authority methods and is added to the closed registry by an authorized change. Packaging, permissions, and sandboxing are not part of RCR-15. |

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
| Ruleset boundary owner | Explicit identity, version, capability discovery, and side-effect-free delegation. | Plugin installation, gameplay routing, legacy combat/skill/condition resolution, or character mutation. |

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
| Current single PF1e-inspired mechanics posture | Active | RCR-15 supplies explicit identity, version, and capability selection. `rules_light@1` and `scifi@1` are identity-only sentinels, not playable rulesets. Do not claim another ruleset is implemented. Legacy Pathfinder modules are not selected through RCR-15. |
| Final Emission/provenance compatibility fields | Active | Do not collapse ruleset mechanics, realization provenance, and replay projection fields. |

## Lifecycle and Version Status

| Area | Lifecycle | Version Status |
|---|---|---|
| Current ruleset identity | Executable closed registry for RCR-15; legacy modules remain direct | `pf1e` version `1` (`pf1e@1`). Identity-only: `rules_light` version `1`, `scifi` version `1`. |
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
| RCR-15 ruleset boundary | `python -m pytest tests/test_ruleset_boundary.py tests/test_pf1e_equipment_policy.py -q` |

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

### Campaign ruleset binding (RCR-15 integration)

`game/campaign_ruleset.py` resolves the active `campaign_run_id` against the
existing persisted session. `session.ruleset_binding` contains `ruleset_id`,
`ruleset_version` (strings), and `binding_version` (integer 1). It is authoritative
for generic policy delegation. `campaign.json` remains authored bootstrap
configuration; character imports and action text cannot select this binding.

New Campaign and fresh-session bootstrap explicitly default to `pf1e@1`.
`POST /api/new_campaign` optionally accepts
`{"ruleset":{"ruleset_id":"pf1e","ruleset_version":"1"}}`.
Registry membership, implemented capability, and campaign playability are distinct:
only `pf1e@1` is admitted by the current legacy-engine creation policy. Identity-only
entries remain discoverable and cannot create playable campaigns. Invalid selection
returns HTTP 422 before reset. There is no registry fallback.

`GET /api/campaign_ruleset?campaign_id=...` returns the persisted identity;
`POST /api/campaign_ruleset/policy` accepts campaign identity, capability, request,
and context, and evaluates without execution. Responses use a bounded public DTO.
Conflicting top-level request ruleset identity returns HTTP 409. A mismatched
campaign id, missing binding, unknown ruleset, bad version, or unsupported
capability cannot borrow another campaign or ruleset's authority.

`POST /api/campaign_ruleset/migrate` uses only explicit persisted session
`ruleset_id` and `ruleset_version`. Missing provenance stays ambiguous. Existing
unbound campaigns remain on named legacy gameplay pathways; generic policy
evaluation refuses their missing binding. This milestone does not retire those
legacy mechanics, convert imported sheets, or provide a manual ambiguity-resolution
editor. Session saves retain an omitted binding and reject replacement. Snapshot
restore restores the entire campaign identity and binding together. Ruleset
switching within a campaign remains unsupported.

Verify with `tests/test_campaign_ruleset_binding.py`; persistence limitations and
HTTP evidence are in the `pr_play_campaign_ruleset_binding` milestone reports.

### Bounded equipment definition policy (PF1e foundation)

`game/pf1e_equipment_policy.py` owns the explicit `pf1e@1` equipment-definition
policy `pf1e.equipment.light_armor`, version 1. It accepts a catalog-bound padded
armor definition in `body_armor`, without asserting possession or worn state.
`main_hand` is recognized only to reject armor placement; this does not provide
wielding support. Shield and simple-melee categories have body-armor exclusions,
not executable policies. Medium/heavy armor remains unsupported.

The independent eligibility result separates compatibility from unresolved
mechanical consequences and blocked execution. It never reads character state,
changes imported totals, or routes gameplay actions. Direct callers must supply
an explicit ruleset; other identities receive UNSUPPORTED. The generic boundary
reaches this policy only after selecting `pf1e` version `1`. Other registered
identities do not enter this module. Generic inventory UUID/revision and
character persistence remain separate owners.

Verify with `tests/test_pf1e_equipment_policy.py`; milestone evidence and the
future mutation prerequisites are in
`development/campaigns/product_realization/pr_play_ruleset_equipment_policy_foundation/`.

### Mechanical action contract

`game/mechanical_action_contract.py` names a ruleset-neutral request, a
single-owner proposed change, and a result envelope. `game/mechanical_action.py`
loads the active campaign binding, discovers the capability through RCR-15, and
asks only that ruleset to resolve. Policy evaluation cannot authorize a commit.
A ruleset may propose one `session_mechanical_ledger` / `record_marker` change.
The core validates the owner, target, revision, operation, field, and value,
then writes the session envelope itself. Ruleset modules do not call session or
character saves.

Terminal statuses stay distinct: capability support, validation, authorization,
and commitment are separate fields. `committed` is the only status that
publishes success. A matching durable receipt replays that commitment and does
not apply it again. Unknown rulesets and unsupported versions do not fall back
to Pathfinder. A request-supplied ruleset identity cannot replace the binding.

`POST /api/mechanical_action` is the bounded caller. The chat and action turn
spine does not call this boundary. Pathfinder equipment policy remains
unresolved and proposes no change. Combat, skills, conditions, non-combat
resolution, and character import remain named legacy pathways. The test-only
contract fixture is not registered and is not a gameplay action.

Verify with `tests/test_mechanical_action_contract.py`. Milestone evidence is in
`development/campaigns/product_realization/pr_play_generic_mechanical_action_contract/`.

- Update this registry when a ruleset-facing contract shape, owner, lifecycle,
  compatibility requirement, version status, verification method, or extension
  boundary changes.
- Do not implement alternate rulesets from this registry alone.
- Do not retire compatibility from this registry; use the Compatibility Residue
  Register and an approved retirement package.
- Do not treat GPT, prompt construction, Final Emission, replay projection, or
  backend routing as ruleset mechanics owners.
- RCR-15 is the approved executable identity and capability boundary. Keep
  this document as the manual contract inventory. Do not treat it as a plugin
  manifest or add a filesystem loader here.

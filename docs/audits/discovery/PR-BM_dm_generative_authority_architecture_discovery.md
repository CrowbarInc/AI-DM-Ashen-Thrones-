# PR-BM - DM Generative Authority & Final-Emission Architecture Discovery

Date: 2026-09-26
Branch: `feature/product-realization`
HEAD: `a5bfdd9e0376173c5aeb4fc762ada259e24bd638`
Target playtest session: `6010c8dfe3c0dcae2ea49469`

## 1. Executive Summary

The latest human playtest failures share an architectural cause: the runtime has a strong authoritative-state model and a heavily defended final-emission stack, but it does not have a first-class, bounded improvisational authority lane for mundane DM invention.

The system can retrieve, restate, and protect authored facts. It can also adopt legacy model-proposed `scene_update` and `world_updates` payloads after shape validation. However, it does not model "safe incidental invention" as a distinct category with scope, persistence, and validation rules. As a result, ordinary human-GM moves such as naming a stew, setting a minor price, giving a low-stakes rumor, or letting an NPC redirect naturally are treated as either unsupported assertions, social-fact inventions, or disposable narration. Downstream gates then replace or reduce useful candidate text into grounded but nonresponsive fallback prose.

The final-emission and retry systems are doing what their local safety patches ask them to do: prevent unsupported state claims, speaker drift, hidden-fact leakage, player-agency override, generic filler, and route-illegal dialogue. The product failure is that these individually reasonable safeguards compose into global overconstraint. They preserve state integrity by shrinking the DM's live authority until mundane improvisation has nowhere legitimate to live.

Key conclusions:

- The current system has no meaningful explicit bounded-improvisation model. It has visible/discoverable/hidden facts, authoritative state domains, response-policy contracts, and legacy model-structured update adoption.
- NPC statements are often treated as candidate assertions requiring authored or recently stored support, not as typed utterances with epistemic status such as rumor, uncertainty, hearsay, mistake, lie, or opinion.
- Useful generated content can be discarded downstream. The Thoran turn preserved an internal richer answer in session/topic-pressure state but final player-visible emission fell back to the previously stored fact.
- The final-emission gate is expression-only by design, but it now also functions as the last defensive reducer when upstream narration has no safe authority category.
- Architectural intervention is warranted. The likely direction is authoritative state plus a bounded improvisational authority layer plus explicit promotion/reconciliation of accepted inventions into typed runtime state.

No production code or tests were changed during this discovery cycle.

## 2. Current Player-Input To Narration Pipeline

Concrete runtime path for `/api/action` and routed `/api/chat` turns:

```text
1. HTTP request
   game.api.action / chat path
   Input: ActionRequest or ChatRequest
   Output: raw player text, request payload, ui_mode-checked runtime permission

2. Intent / route preparation
   game.intent_parser, game.interaction_routing, game.scene_actions
   game.api._prepare_interaction_from_turn_input
   Input: raw player text, current session/world/scene
   Output: normalized action, route choice, implied interaction context
   Mutations: may establish or update interaction context before resolution

3. Engine resolution
   game.api._resolve_engine_noncombat_seam
   game.exploration.resolve_exploration_action
   game.social.resolve_social_action
   combat resolvers for combat lanes
   Input: normalized action, scene, session, world
   Output: resolution dict
   Rejection/fallback: unsupported actions, pending skill checks, offscene social targets

4. Authoritative mutation
   game.api._run_resolved_turn_pipeline
   game.api._apply_authoritative_resolution_state_mutation
   Input: resolution
   Output: mutated session/world/scene runtime before narration
   Mutations: authoritative clue discovery, scene transitions, runtime scene state, world updates from engine-owned resolution

5. CTIR / narration plan / context construction
   game.ctir_runtime.ensure_ctir_for_turn
   game.narration_plan_bundle.ensure_narration_plan_bundle_for_turn
   game.prompt_context.build_narration_context
   game.gm.build_messages
   Input: post-resolution authoritative state, response policy, recent log
   Output: model messages and prompt payload
   Rejection/fallback: planner convergence emergency if CTIR/bundle seam fails

6. Model generation
   game.gm.call_gpt
   Input: messages
   Output: parsed GM JSON via game.gm.guard_gm_output
   Rejection/fallback: non-JSON fallback, provider/budget fallback

7. Targeted retry loop
   game.gm_retry.detect_retry_failures
   game.gm_retry.choose_retry_strategy
   game.gm_retry.build_retry_prompt_for_failure
   game.gm_retry.apply_deterministic_retry_fallback
   game.gm_retry.force_terminal_retry_fallback
   Input: candidate GM output, player text, resolution, state
   Output: accepted candidate, retry candidate, deterministic fallback, or terminal fallback
   Retry conditions: validator voice, unresolved question, echo/repetition, NPC contract failure, topic-pressure escalation, follow-up repetition, scene stall, forbidden generic phrase
   Fallback conditions: retry budget exhausted, deterministic fallback still fails, upstream API error

8. Response-policy handoff and realization repair
   game.api._apply_narration_hub_policy_handoff
   game.gm.apply_response_policy_enforcement
   game.social.apply_authored_knowledge_realization_to_gm
   game.perception_grounding.apply_perception_non_invention_to_gm
   Input: post-retry GM output
   Output: candidate text adjusted toward authored/revealed facts
   Mutations: output text only

9. Final emission gate
   game.api._finalize_player_facing_for_turn
   game.final_emission_gate.apply_final_emission_gate
   game.final_emission_strict_social_stack.run_strict_social_composition_trunk
   game.final_emission_non_strict_stack.run_non_strict_layer_stack
   game.final_emission_terminal_pipeline.run_gate_terminal_enforcement_pipeline
   Input: GM output, resolution, session, scene, world
   Output: final player-facing text plus `_final_emission_meta`
   Rejection/fallback: response-type violation, strict-social legality failure, visibility violation, narrative-mode failure, acceptance-quality floor, opening fallback, passive-scene fallback, emergency social minimal

10. Post-GM update adoption and persistence
    game.api._apply_post_gm_updates
    game.storage.save_world / save_session / append_log
    Input: final GM output and structured update proposals
    Output: persisted session/world/log
    Mutations: validated legacy `scene_update`; validated legacy `world_updates`; ignores `activate_scene_id` and `new_scene_draft` proposals; records clue surfacing telemetry
```

The strongest architectural ordering is: engine mutates authoritative state first, prompt/narration are built from that state, retries and gates reduce unsafe candidate text, then a legacy post-GM proposal gateway may adopt structured updates.

## 3. Current Generative-Authority Model

The prompt in `game/gm.py` tells the model: "The application owns authoritative mechanics and persistence. You narrate, propose updates, and draft scenes." It also allows sourced new names or factions. This is permissive in wording.

The runtime authority registry in `game/state_authority.py` is stricter: "GPT / model-originated output is never an authoritative mutator of runtime truth." All state domains have `gpt_may_mutate=False`.

The actual architecture is therefore:

- Engine-owned resolution is authoritative.
- Authored scene/world data is authoritative.
- Prompt-visible slices are derived publication views.
- Model narration is candidate expression.
- Model structured updates are legacy proposals that `game.api` may adopt under its own owner identity after shape validation.
- Final emission is not allowed to semantically invent or repair world truth; it can accept, strip, replace, or attach metadata.

This model protects state integrity but does not answer where a DM may safely improvise incidental fiction.

## 4. Current Grounding / Invention Restrictions

Important enforcement sites:

- `game.state_authority`: declares domains, owners, and forbids model-originated authoritative mutation.
- `game.narrative_authority`: forbids invented outcomes, hidden facts, and NPC intent assertions without basis; supports bounded uncertainty as a deferral concept.
- `game.narration_visibility` and prompt visibility contracts: visible facts may be narrated; discoverable clues need investigation; hidden facts must not be stated.
- `game.social.player_facing_invents_unauthored_social_fact`: flags unauthored social facts including price, time, count, redirect, and identity inventions.
- `game.social.apply_authored_knowledge_realization_to_gm`: replaces concealment or unsupported social realization with authored fact realization or grounded absence.
- `game.final_emission_*` layers: response type, answer completeness, narrative authenticity, narrative authority, speaker contract, tone escalation, anti-railroading, context separation, narration purity, scene-state anchoring, visibility fallback, narrative-mode output, acceptance-quality floor.
- `game.perception_grounding`: constrains perception narration to visible facts and resolution-supported discoveries.

Answers to the policy questions:

A. Categories requiring support include hidden facts, discoverable clues, mechanical outcomes, success/failure, scene transitions, NPC identity/speaker attribution, concrete social facts such as prices/times/counts/redirects, and persistent world/scene changes.

B. Freely generated text is mostly style, connective prose, sensory texture around visible facts, and candidate dialogue that survives validators. But "free" text is downstream-scanned for unsupported facts, social inventions, response-shape failures, and visibility issues.

C. Mundane details are not consistently distinguished from consequential facts. Price, count, time, redirect, food/transaction-like details are treated conservatively if they look like concrete social facts.

D. NPC statements are often coupled to world truth or stored topic facts. The system has some rumor wording, but no general typed "NPC utterance with epistemic status" authority model.

E. NPCs can express uncertainty or refusal through fallback and response policy. There is no robust domain model for lies, mistakes, hearsay, or opinion as non-authoritative utterance types.

F. The DM can create incidental details in narration if they survive gates, but there is no explicit durable authority lane for them.

G. Existing representation is indirect: `scene_update.visible_facts_add`, `discoverable_clues_add`, `hidden_facts_add`, `world_updates.append_events`, topic-pressure memory, social lead discussions, and journal/clue publication.

H. In practice, invention is prevented by authority/visibility/social-fact validators, retry fallback preference for known facts, and final gate replacement.

## 5. Final-Emission Architecture

`game.final_emission_gate.apply_final_emission_gate` is the canonical orchestration owner. It dispatches to:

- strict social path: `game.final_emission_strict_social_stack.run_strict_social_composition_trunk`
- non-strict path: `game.final_emission_non_strict_stack.run_non_strict_layer_stack`
- generic accept/replace exits
- terminal enforcement in `game.final_emission_terminal_pipeline`
- finalize packaging in `game.final_emission_finalize`

The gate is explicitly described as expression-only and not the owner of semantic invention. Its module docstring says semantic sentence repairs for many policy layers are disabled at the boundary; violations surface as reason codes without boundary rewrites.

Observed tags:

- `final_emission_gate_replaced`: final visible text differs from accepted upstream candidate or was replaced by fallback.
- `final_emission_gate:narrative_safe_fallback`: generic safe replacement; in the refugee investigation this yielded a visible-scene fallback and "Closer looking yields nothing further."
- `final_emission_gate:emergency_social_minimal`: strict-social candidate failed or terminal path chose sealed minimal social fallback.
- `terminal_strict_social_emission`: strict-social terminal fallback was emitted and stamped safe.

Strict social sequence:

1. Validate dialogue plan invariant.
2. Build normalized strict-social response from candidate/resolution.
3. Enforce response-type contract.
4. Apply answer completeness, answer exposition plan, response delta, social response structure, narrative authenticity.
5. Apply tone escalation, narrative authority, speaker contract, anti-railroading, context separation, narration purity, answer shape primacy, scene-state anchor, fast-fallback neutral composition.
6. If dialogue-plan stripping empties text, use `minimal_social_emergency_fallback_line`.
7. Terminal pipeline applies referential clarity, visibility enforcement, fallback behavior, narrative-mode legality, acceptance-quality floor, and interaction continuity.

What gets discarded:

- Candidate dialogue that is not supported by a valid dialogue plan or fails response type.
- Candidate details that look like unsupported social facts.
- Candidate prose that is route-illegal, too generic, too repetitive, insufficiently anchored, or not acceptable under strict social mode.
- Richer prior `last_answer` material can be reduced to `last_answer_authoritative_text` or stored fact snippets.

The Captain Thoran case demonstrates this. `data/session.json` contains topic-pressure/runtime material approximately:

- last answer: `"I can't arrange that for you"... "If you want an audience, you'll have to find another way inside..."`
- last answer authoritative text: `Captain Thoran commands the gate watch tonight.`

The final emitted turn repeated only the authoritative fact: `Gate Guard mutters, "Word is, captain Thoran commands the gate watch tonight."`

That is not a successful player turn; it is an architectural fallback pattern.

## 6. Retry / Fallback Architecture

Retry owner: `game.gm_retry`.

Failure detection checks:

- validator voice
- unresolved direct question
- echo/repetition
- NPC response contract failure
- topic pressure escalation
- follow-up soft repetition
- scene stall
- forbidden generic phrases

Retry lifecycle:

1. Primary model output is parsed by `guard_gm_output`.
2. `detect_retry_failures` classifies failures.
3. `choose_retry_strategy` selects the highest-priority failure.
4. If retry budget remains, `build_retry_prompt_for_failure` appends a narrow retry instruction and calls GPT again.
5. If the retry still fails an answer/unresolved-question class, `apply_deterministic_retry_fallback` chooses a known fact, open-social recovery, strict-social retry fallback, or uncertainty fallback.
6. If that still fails or budget is exhausted, `force_terminal_retry_fallback` emits a deterministic terminal line and tags `retry_escape_hatch`, `forced_retry_fallback`, `retry_exhausted`.

Retries become progressively more restrictive:

- The primary candidate can contain model-authored specifics.
- Retry prompt narrows behavior around one failure class.
- Deterministic fallback prefers authored/stored facts over generated content.
- Terminal fallback uses social emergency or grounded scene lines.

The retry architecture does not distinguish "unsupported consequential claim" from "reasonable mundane improvisation." A price, minor redirect, ordinary transaction, or local rumor may enter the same failure machinery as unsafe social invention.

## 7. State-Promotion Architecture

There are three promotion families:

1. Engine-owned resolution updates
   - `game.api._apply_authoritative_resolution_state_mutation`
   - `game.world.apply_resolution_world_updates`
   - clue discovery via `game.clues.apply_authoritative_clue_discovery`
   - scene transitions via `_apply_authoritative_scene_transition`

2. Legacy model structured proposals
   - `game.api._apply_post_gm_updates`
   - `scene_update` may add runtime overlay visible facts, discoverable clues, hidden facts, and mode after shape validation.
   - `world_updates` may be normalized and applied after JSON/prose-key checks.
   - `activate_scene_id` and `new_scene_draft` are advisory-only and ignored.
   - Debug traces classify adoption as model-structured proposal, high risk, needs gateway, with gateway mode `observe_only`.

3. Narration-derived telemetry or social memory
   - surfaced clues in narration are telemetry only.
   - social lead discussions and topic-pressure memory can preserve answers/snippets, but they are not a general world-truth promotion model.

Example: "The runner sets down a bowl of watery turnip-and-mutton stew. Three coppers."

Current likely handling:

- If only in `player_facing_text`, stew composition and price are not persistent authoritative state.
- If the model also emits `scene_update.visible_facts_add`, it may be adopted as a scene overlay if shape-valid, but there is no typed service/transaction/economy semantics.
- If it emits `world_updates`, price/transaction shape may be rejected or merely logged depending keys.
- Player expenditure is not applied unless an engine/economy action owns it.

Thus narration can create ephemeral fiction, and structured proposals can be adopted, but there is no explicit accepted-invention reconciliation path that classifies incidental vs consequential facts.

## 8. NPC Epistemology Model

Current representations:

- World truth: `data/world.json`, scene templates, runtime session state, clues, leads.
- NPC records: `world["npcs"]` with `topics`, `knowledge_scope`, `agenda`, location, role, disposition.
- Runtime social memory: topic pressure, last answers, NPC lead discussions, clue knowledge, revealed topics.
- NPC speech: generated or deterministic player-facing text, then validated/replaced.

Gap:

The engine lacks a first-class separation among:

- fact is true in the world
- NPC believes it
- NPC says it
- NPC heard it as rumor
- NPC is lying or mistaken
- NPC speculates

Rumor appears as content text and wording, not as an epistemic state object. A human GM can say "They say something has been taking livestock north of the mill" without establishing a monster. This engine has no robust typed way to persist that as `claim(type=rumor, asserted_by=npc, truth_status=unknown, consequence_level=low|medium|high)`.

Without that distinction, NPC dialogue is pressured either toward authored truth or safe ignorance.

## 9. Affordance Consistency Findings

The frontier-gate scene advertises:

- `A tavern runner trades hot stew and rumors near the rain barrel.`
- `A tavern runner shouts offers of hot stew and paid rumor.`
- `A tavern runner is hawking hot stew and rumor for coin.`

The world NPC row for `tavern_runner` contains:

- role: `informant`
- current agenda: `sell_rumors`
- topic: `Hot stew and rumors for coin.`

But there is no evident typed affordance guaranteeing:

- stew inventory
- menu/composition
- price
- purchase/transaction action
- rumor sale protocol
- player coin debit
- NPC response behavior when offered silver

The authored text can create an interaction expectation that downstream systems cannot satisfy. This is a narrated-affordance-to-supported-interaction gap.

## 10. Relevant Historical Architecture / Safety Accretion

Git history shows repeated safety and ownership cycles around the same surfaces:

- `1d3580d Unified State Authority Model`
- `e7bd8c2 Narrative Authority Boundaries`
- `02ab9b0 Final Emission Boundary Hardening`
- `6c00e6e D: Final Emission Gate Pressure Reduction`
- `2469338 Extract final emission gate authority boundaries`
- `dcbcefe AI: Response Policy Authority Extraction`
- `371b38c AJ: Opening Fallback Metadata Consolidation`
- `b1c1680 AM: Fallback Adapter Retirement`
- `b400e38 AN: Gate Orchestration Decomposition`
- `59c14aa AP: Fallback Authorship Resolution`
- `11ff282 BJ: Final Emission Gate Responsibility Extraction`
- `683c8df BK: Fallback Ownership Compression`
- `c45cfe0 Finalize strict social fallback ownership extraction`
- `4460543 CK: Fallback Authorship Contraction`
- `ec9c7c8 CN: Final-Emission Adjacency Compression`

This supports the interpretation that the restrictive behavior is accumulated defensive architecture rather than one deliberate product choice to forbid improvisation. The codebase has done a great deal of work to prevent hallucination, speaker drift, unsafe fallback authorship, and semantic mutation. It has not added the complementary positive authority model for bounded invention.

## 11. Latest Human-Playtest Failure Analysis

Session `6010c8dfe3c0dcae2ea49469` produced 0 satisfactory player turns after opening.

Turn 2: refugee investigation

- Player asked where refugees came from and what they were fleeing.
- Final text: a gate serjeant manages the crowd; closer looking yields nothing further.
- Tags: `authored_knowledge_realization`, `referenced_surface_realization`, `final_emission_gate_replaced`, `final_emission_gate:narrative_safe_fallback`.
- Interpretation: investigation requested plausible local inference or partial social/world information; system replaced with visible-scene fallback and no meaningful answer.

Turn 3: stew affordance

- Player sat near tavern runner expecting stew.
- Final text: scene observation about watchers/refugees/serjeant.
- Tags: `final_emission_gate_replaced`, `final_emission_gate:passive_scene_pressure_grounded_observe`.
- Interpretation: advertised service affordance was not mapped to supported interaction; system treated it like passive observation.

Turn 4: ask runner for rumors

- Final text: `Tavern Runner says, "No. I cannot answer that from what I know."`
- FEM route: accepted normalized social candidate.
- Interpretation: route was coherent but product-failing because authored runner is specifically a rumor seller and existing scene has rumor hooks.

Turn 5: offer silver

- Final text: `Tavern Runner grimaces. "Not something I can say here."`
- Tags: `retry_escape_hatch`, `forced_retry_fallback`, `retry_exhausted`, `final_emission_gate:emergency_social_minimal`, `terminal_strict_social_emission`.
- Interpretation: money reaction and rumor sale triggered strict social/retry fallback instead of bounded improvisation or authored rumor sale.

Turn 6: ask guard about work

- Final text: `Gate Guard says, "I do not know enough to answer that."`
- Interpretation: safe ignorance instead of plausible redirect from gate guard to hiring board, captain, merchants, or runner, despite visible job/merchant hooks in authored scene.

Turn 7: ask who can answer

- Final text: Captain Thoran commands gate watch tonight.
- This revealed an authored/stored fact and created a lead.

Turn 8: ask for audience

- Final text repeated Captain Thoran fact.
- Session state contains a richer answer indicating the guard cannot arrange it and the player needs another way inside.
- Interpretation: useful material existed internally but final realization favored stored authoritative text, dropping the connective social answer.

## 12. Shared Root Causes

1. No explicit bounded improvisational authority.
   Mundane details are not classified as low-risk inventions with rules and promotion semantics.

2. NPC epistemology is under-modeled.
   Rumor, hearsay, speculation, mistaken belief, and refusal are not typed separately from world truth.

3. Affordances are descriptive, not executable.
   Scene narration can advertise "hot stew and paid rumor" without creating transaction/interaction capabilities.

4. Final emission is overburdened.
   It was designed as a legal-state gate, but absent upstream authority lanes it becomes a content reducer.

5. Retry collapses toward known facts.
   The retry lifecycle discards candidate richness and terminally prefers grounded snippets or uncertainty.

6. Promotion is legacy-shaped, not taxonomy-shaped.
   `scene_update` can add facts, but without a deliberate incidental/consequential taxonomy.

## 13. Architectural Options

### Option A - Bounded Improvisation Ledger

Concept:
Add a typed runtime ledger for model- or DM-authored incidental inventions. Entries have category, scope, owner, promotion status, consequence level, expiry, and validation result.

Affected components:
`game.state_authority`, `game.prompt_context`, `game.api._apply_post_gm_updates`, final-emission validators, tests around world updates and narration state consistency.

Benefits:
Restores human-DM texture while preserving clear authority boundaries.

Risks:
Requires careful taxonomy and migration of existing fallback assumptions.

State-integrity implications:
Incidental facts become state through explicit promotion rather than accidental narration.

Migration complexity:
Medium-high.

Expected responsiveness:
High improvement for mundane unseen interactions.

Hallucination risk:
Controlled if consequence-level validation is strict.

Testing:
Scenario tests for incidental facts, promotion records, non-promotion of consequential claims, and replay drift.

### Option B - NPC Claim / Epistemology System

Concept:
Represent NPC utterances as claims: `speaker`, `claim_text`, `epistemic_status`, `truth_status`, `source`, `scope`, `consequence_level`.

Affected components:
Social resolution, social memory, prompt context, final-emission strict social stack, journal/clue presentation.

Benefits:
Makes rumors possible without asserting truth.

Risks:
More complex prompt payloads and validators.

State-integrity implications:
World truth remains separate from claims.

Migration complexity:
Medium.

Expected responsiveness:
High for rumors, social redirection, and NPC uncertainty.

Hallucination risk:
Lower than free invention because claims are typed and scoped.

Testing:
Rumor truth isolation, lie/mistake handling, follow-up continuity, promotion from claim to clue only through authored/engine reveal.

### Option C - Affordance Contract Registry

Concept:
Every advertised interactable affordance must map to supported actions and minimal fallback behavior. If scene text says a runner sells stew, the registry provides purchase, price policy, inventory, and response behavior.

Affected components:
Scene schema, `game.affordances`, `game.exploration`, `game.social`, prompt context, validation/lint.

Benefits:
Prevents authored affordance mismatch.

Risks:
May increase authoring burden; does not solve spontaneous improvisation alone.

State-integrity implications:
Strong; actions are executable and typed.

Migration complexity:
Medium.

Expected responsiveness:
High for advertised interactions.

Hallucination risk:
Low.

Testing:
Scene lint: advertised service -> action support. Runtime tests: purchase, rumor request, transaction.

### Option D - Relax Final Emission Validators

Concept:
Tune current gates to allow more mundane generated content.

Affected components:
`game.final_emission_*`, `game.social`, `game.gm_retry`.

Benefits:
Fastest near-term relief.

Risks:
Blurs safety policy; likely reintroduces previous hallucination/state drift classes.

State-integrity implications:
Weak unless paired with typed promotion.

Migration complexity:
Low initially, high maintenance.

Expected responsiveness:
Moderate.

Hallucination risk:
Medium-high.

Testing:
Large regression burden, because loosening gates touches many prior safety fixes.

## 14. Recommended Direction

Evidence supports a combined Option A + Option B, followed by Option C for authored affordance consistency.

Recommended model:

```text
authoritative state
  - immutable / engine-owned world truth
  - mechanics, inventory, geography, clue discovery, NPC identity

bounded improvisational authority
  - incidental sensory/social details
  - mundane prices within policy bands
  - low-stakes local color
  - NPC claims with epistemic status
  - scoped to current scene/session unless promoted

promotion / reconciliation
  - validate category and consequence level
  - persist accepted inventions as typed runtime facts or NPC claims
  - require stronger evidence or author/engine ownership for consequential facts
```

Do not simply weaken final-emission checks. The fix should add a positive authority lane upstream, so final emission can validate typed improvisation instead of guessing whether untyped prose is safe.

## 15. Open Questions

- What exact categories should be allowed as incidental facts?
- Should incidental inventions persist for the session, scene, or campaign by default?
- What economy boundaries define safe ordinary prices?
- How should player inventory/coin updates be authorized for mundane purchases?
- Should NPC claims be visible in the player journal, hidden social memory, or both?
- Can existing `scene_update` legacy adoption be repurposed, or should it be replaced by a new typed proposal schema?
- What are the migration rules for existing `topics`, `discoverable_clues`, and social memory answers?

## 16. Exact Files / Components Likely Affected By Future Implementation

Primary:

- `game/state_authority.py`
- `game/api.py`
- `game/gm.py`
- `game/gm_retry.py`
- `game/prompt_context.py`
- `game/social.py`
- `game/social_memory.py`
- `game/social_exchange_emission.py`
- `game/social_exchange_policy.py`
- `game/final_emission_gate.py`
- `game/final_emission_strict_social_stack.py`
- `game/final_emission_terminal_pipeline.py`
- `game/narrative_authority.py`
- `game/affordances.py`
- `game/exploration.py`
- `game/world.py`
- `game/journal.py`

Likely schema/data:

- `data/world.json`
- `data/scenes/frontier_gate.json`
- `game/defaults.py`
- scene schema/import/lint code

Likely tests:

- `tests/test_world_updates_and_clue_normalization.py`
- `tests/test_social_speaker_grounding.py`
- `tests/test_social_target_authority_regressions.py`
- `tests/test_transcript_regression.py`
- `tests/test_affordance_generation.py`
- `tests/test_validation_journal_affordances.py`
- final-emission gate/strict-social/retry suites

## 17. Proposed Verification Strategy

Future implementation should be verified by capability, not by hardcoding this transcript.

Suggested verification layers:

1. Unit tests for taxonomy classification:
   incidental fact vs NPC claim vs consequential fact vs authoritative mutation.

2. Unit tests for promotion:
   accepted incidental fact persists in scoped runtime state; consequential invented fact is rejected or quarantined.

3. NPC epistemology tests:
   rumor claim does not become world truth; lie/mistake/speculation remain claims; authored clue promotion remains engine-owned.

4. Affordance consistency tests:
   advertised services produce supported actions; unsupported authored affordances fail lint.

5. Final-emission integration tests:
   typed incidental inventions survive final emission; untyped hidden/consequential assertions do not.

6. Human-adjacent playability scenarios:
   unseen mundane interactions around food, prices, minor gossip, directions, refusal, and redirect.

7. Regression suite:
   existing protected replay, final-emission, social grounding, world-update, and state-authority tests.

## Commands / Evidence Recorded

Commands run:

- `git status --short`
- `rg --files`
- `rg` searches for final-emission, retry, grounding, authority, and playtest terms
- targeted `Get-Content` / `Select-String` source reads
- `git log --oneline` over final-emission/retry/social/state-authority files
- session-log summary extraction from `data/session_log.jsonl`
- `git rev-parse HEAD`

No test suite was run because this cycle was discovery-only and source/log tracing was sufficient to answer the architectural questions. No production code or test files were modified.

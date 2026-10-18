# PR-BR Continuation 25 — Contract-First Semantic Ownership Reconciliation

### 1. Purpose

Put ordinary natural-language gameplay under one semantic owner: the Resolution Contract. Specialized systems resolve that contract. They do not decide the operation from raw text first.

### 2. Authorization basis

C23 found eight peer readers of a chat sentence. C24 proved the unparsed adjudication arm can build the contract before its resolver, and left the other parsers for this cycle.

### 3. C23/C24 ownership findings

C23: segmentation, social entry, social parse, dialogue-first, exploration, world-action recovery, generic intent, travel, and in-chat attack choose meaning, then the pipeline attaches a contract. Off-scene social text and pending check prompts emit with no contract. C24 closed only the unparsed arm.

### 4. C24 proof-of-concept boundary

Preserved. `game/contract_adjudication_bridge.py` still selects and runs adjudication families only when a contract id and operation exist. The unparsed arm in `game/api.py` still attaches a contract before `select_resolver_family`. This cycle did not restyle that arm. It calls the same selector from the new ordinary boundary.

### 5. Pre-implementation semantic-owner inventory

Eleven remaining owners, plus the contract constructor and the existing proposal validator:

| Component | Module / entry | Raw input | Decision before | Contract before? | State / discourse / emit | Intended role |
| --- | --- | --- | --- | --- | --- | --- |
| Segmentation | `intent_parser.segment_mixed_player_turn` | full text | clause split | no | no / no / no | structural |
| Directed social entry | `interaction_context.resolve_directed_social_entry` | merged clauses | route and candidate addressee | no | discourse hints | structural |
| Social parser | `social.parse_social_intent` | classification text | ask/tell kind | after | after pipeline | resolver |
| Dialogue-first | `interaction_routing._build_dialogue_first_action` | full text | social action | after | after pipeline | resolver |
| Exploration | `exploration.parse_exploration_intent` | classification text | look/go/search | after | after pipeline | resolver |
| World-action recovery | `intent_parser.recover_actionable_explicit_world_action` | classification text | object action | after | after pipeline | helper |
| Generic intent | `intent_parser.parse_intent` | classification text | residual verb | after | after pipeline | helper |
| Declared travel | `intent_parser.maybe_build_declared_travel_action` | declared clause | movement | after | scene after attach | resolver |
| In-chat attack | `combat.resolve_attack` via `parse_intent` | attack verb | attack while in combat | after, combat save was before attach | combat | resolver |
| Off-scene social | `api._build_offscene_target_gm_output` | social resolution | engine line | no | emit | downstream |
| Pending check | `api._build_check_prompt_gm_output` | check request | engine prompt | no | emit | downstream |

### 6. Segmentation boundary

Structural. Sentence, clause, punctuation, and obvious coordination stay. The contract is built from `req.text`, not from the extracted adjudication clause. Dropping a trailing question out of a parser's view no longer chooses the operation. The splitter itself was not rewritten.

### 7. Unified contract-construction architecture

`establish_ordinary_gameplay_contract` in `game/ordinary_semantic_ownership.py` runs in `chat` before any specialized parser, on the ordinary branch. Campaign start stays Category A. The function calls the existing `attach_interaction_obligation` / `construct_resolution_contract`. There is no social, travel, or exploration contract constructor.

### 8. Deterministic fast path

Unchanged inside `construct_resolution_contract`. Canonical lines still build a contract without a model. The fast path constructs the contract. It does not execute the resolver.

### 9. Structured interpretation path

Unchanged C10/C11 rule. The model runs only when the fast path abstains and the existing policy says a proposal is appropriate. Validation can reject the proposal. The proposal is not the contract until validation accepts it.

### 10. Social reconciliation

Social parse and dialogue-first run only when the selected resolver is `social`. A travel or observe result that contradicts an ask is discarded. C20 incidental binding, C21 speaker checks, and C22 addressee checks stay in the existing contract and validation path.

### 11. Exploration reconciliation

`inspect` and `perceive` select `exploration`. Local-presence questions ("What's nearby?") are `perceive` and stay on the observe lane. Before acceptance, that lane realizes the line from current scene facts (`realize_local_observation_line`) so a contract seal cannot freeze an ignorant model stub. Inspect, wear, sound, and appearance distinctions stay in the existing contract dimension logic.

### 12. World-action recovery reconciliation

Recovery runs only for `world_action` and as a helper on `exploration`. It cannot run on an ask. It does not manufacture a new operation. A contradicting result is dropped and the contract remains.

### 13. Generic-intent reconciliation

`parse_intent` runs only as a helper for `world_action` and `combat`, after the contract exists. It is not a second constructor. An incompatible action type is rejected.

### 14. Travel reconciliation

Travel runs only when the contract operation is `act` or `follow`, commitment is `executed_now`, and the utterance is movement or qualified pursuit is not the better exploration shape. "I'll head to the brass quay" is now an act. "I ask ... before heading out" stays an ask. Hypothetical and conditional sentences do not select travel. The exploration parser still performs the authored-exit transition when the travel resolver is selected, because declared-travel alone does not match every authored exit.

### 15. Attack / combat-entry reconciliation

A direct "I attack" is an act. The combat resolver is selected only in combat and only when commitment is `executed_now`. Otherwise the attack is not executed. The attack action object still comes from `parse_intent`, after the contract. Combat internals were not redesigned.

### 16. Resolver selection architecture

`select_ordinary_resolver`: missing contract or unresolved operation selects generation; uncommitted act/follow/confirm selects generation; otherwise the C24 family selector may return an adjudication family; otherwise operation maps to social, exploration, travel, world action, or combat. Selection is after the contract. It is not a race among parsers.

### 17. Resolver input/output contracts

Documented on `RESOLVER_CONTRACTS` in `game/ordinary_semantic_ownership.py`. Each row lists required fields, optional fields, state, discourse, result, state change, and failure. Internals stay different.

### 18. Resolver failure behavior

A contradicting or empty resolver result does not clear the contract. The turn falls through to contract-aware generation or the existing safe nonresolution. Failure does not restore a stale interlocutor, invent an addressee, or execute an uncommitted move.

### 19. Multi-clause handling

Deterministic cases, all contract-first:

- Ask plus listen: operation `ask`, resolver `social`.
- Inspect before deciding whether to follow: `inspect`, `exploration`.
- Inspect, then follow: `inspect`, `exploration`.
- Ask whether the road is safe before heading out: `ask`, `social`.
- Walk to the merchant and ask about supplies: `ask`, `social`.
- Listen at the door: `perceive` / sound, `exploration`.

### 20. Discourse ownership

Contract construction receives session, scene, world, and visible turns before resolver selection. That includes the active interlocutor, scene, and location already stored on the session. The resolver gate does not let an old parser reset the operation because it used to own the sentence.

### 21. Off-scene social classification

Downstream consequence of an already established contract. Class `downstream_consequence`, kind `offscene_social`. The chat branch stamps `emission_provenance` with the contract id. It is not Category A and not a new model call.

### 22. Pending-check classification

Downstream consequence of a resolution that already requires a check. Kind `pending_check`. The prompt is not a new player intent. Same provenance stamp. Mechanics were not rewritten.

### 23. Category-A exclusions

Unchanged and enumerated: `session_administration`, `initiative_status_line`, `end_turn_status_line`, `campaign_start_cue`.

### 24. C18 emission ownership

Ordinary generated turns still go through `run_preserve_if_valid`. Local observation, off-scene text, and check prompts are deterministic consequences. Local observation is realized before the seal so the sealed text is the grounded line. Live turns 1–6 have accepted text equal to emitted text. Turn 1's sealed text unfortunately includes a JSON blob; equality held, quality did not.

### 25. C19 authority ownership

Specialized resolvers are not exempt. Turn 1's first candidate was rejected for `consequential_invention` and retried. The place answer on turn 4 passed authority and was still the wrong question.

### 26. State-commit ownership

Chat combat save and scene transition run after the contract exists. The world clock still advances at the start of the turn; that clock is not a reading of the sentence. Live scenes stayed `frontier_gate` on all six turns. No uncommitted transition.

### 27. Historical replay results

Deterministic/stubbed. No historical live API replay.

C12–C16, C18–C25 modules passed after the final edits. C22's authored "follow the road toward the old milestone" still changes scene, because the travel resolver may call the exploration parser and only keep a movement result.

### 28. Y1–Y20 cross-resolver matrix

20 / 20 in `tests/test_pr_br_continuation25_semantic_ownership.py::test_y1_through_y20_matrix`. Each row records input, operation, resolver, and adjudication family. Construction source on these fixtures is the deterministic constructor. Chat coverage in the same module checks contract-before-resolver, semantic owner, and no scene change on a conditional.

### 29. Single-owner invariant

Pass. Ordinary `chat` calls `establish_ordinary_gameplay_contract` before `parse_social_intent`, exploration, world-action recovery, `parse_intent`, and declared travel. A missing contract selects generation and rejects a specialized action.

### 30. Peer-parser retirement / repurposing map

| Parser | Role now |
| --- | --- |
| Segmentation | structural |
| Directed social entry | structural |
| Social parser | resolver |
| Dialogue-first | resolver |
| Exploration | resolver |
| World-action recovery | resolver helper |
| Generic intent | resolver helper |
| Declared travel | resolver |
| In-chat attack | resolver |
| Adjudication family selector | resolver, still lexical |
| Off-scene social text | downstream consequence |
| Pending check prompt | downstream consequence |
| `construct_resolution_contract` | contract constructor |
| Proposal validation | contract validator |

### 31. Model / API economy

No mandatory extra interpretation call. The ordinary path builds the deterministic contract first and calls the interpreter only on abstention, which is the previous pipeline rule. The pipeline does not build a second contract when one already exists. Live: 4 deterministic contracts, 2 accepted structured contracts, 3 interpretation invocations (one rejected on turn 6), 5 gameplay generations, 1 retry.

### 32. Performance / complexity

One contract build moved in front of the parser chain. Peer parsers are skipped unless the resolver allows them, so fewer competing parses run. Added dispatch is one selector and a contradiction check. Latency is the same in-process contract build ordinary turns already paid inside the pipeline. Testability improved: Y1–Y20 do not need a model.

### 33. C18–C24 regression results

C18, C19, C20, C21, C21b, C21c, C22, C23, C24: pass.

### 34. Broader PR-BR regression

C12–C16 pass. Local-presence HTTP tests pass. Nearby place HTTP tests pass. Earshot and covert-concealment pipeline tests pass.

Pre-existing, and already red in C24's restored tree: `test_question_rule_does_not_rewrite_resolved_place_existence`. Not introduced here.

### 35. Fresh live transcript

`artifacts/pr_br_continuation25/live/20261003T132903Z/visible.md`. Six turns. Opening plus Galinor at the frontier gate. No repair, no rerun, no evaluator.

### 36. Live ownership / resolver telemetry

Every turn has a contract, `semantic_owner=resolution_contract`, and `contract_before_resolver=true`.

| Turn | Source | Operation | Resolver | Commitment | Scene |
| --- | --- | --- | --- | --- | --- |
| 1 | structured | act | world_action | executed_now | frontier_gate |
| 2 | deterministic | ask | social | executed_now | frontier_gate |
| 3 | deterministic | ask | social | executed_now | frontier_gate |
| 4 | deterministic | ask | adjudication / place_location | contemplated | frontier_gate |
| 5 | structured | ask | social | executed_now | frontier_gate |
| 6 | deterministic | act | world_action | executed_now | frontier_gate |

### 37. Live state / discourse review

No scene change. Turn 2 and 3 bind `tavern_runner`. Turn 4 binds incidental `inc_3520c297da` while answering a place question the player did not ask. Turn 5 binds incidental `inc_0331b12928` for "Captain," not the authored captain. Turn 1's rejected candidate did not leave a scene change. Accepted text equals emitted text on all six turns.

### 38. Manual review

4 / 6 PASS. See `MANUAL_REVIEW.md`. Turns 1 and 4 fail.

### 39. Final ownership map

```
raw language
    -> structural segmentation and social-entry discourse hints
    -> establish_ordinary_gameplay_contract
         deterministic fast path, or one validated interpretation proposal
    -> select_ordinary_resolver
    -> social | exploration | travel | world action | combat | adjudication | generation
    -> C19 authority and C18 acceptance, or a stamped downstream engine line
    -> state and discourse commit from that accepted resolution
    -> exact accepted emission
```

### 40. Remaining exceptions

- Category A: session administration, initiative line, end-turn line, campaign-start cue.
- Off-scene social text and pending check prompts: downstream consequences with provenance when they emit on the chat path.
- Typed `/api/action` initiative, end-turn, and its own off-scene/check lines: client-named actions, not chat sentences. Those action-endpoint lines were not pulled into the chat gate.
- World tick at the start of the turn: clock, not a semantic reading.
- Adjudication family selection still re-reads raw tokens on the contract. That is the live defect, not an allowed exception.

### 41. Residual defects

- Turn 4: `place_location` fired because the raw text contained `tavern` and `shelter` inside a contemplated plan. The contract operation stayed `ask`. The player saw a tavern-existence answer.
- Turn 1: structured interpretation plus validation labeled a spoken approach as `act` / `world_action`. The sealed retry included JSON in the player-visible text.
- Family selection is still a lexical reader. Operation `ask` is too coarse to stop it.

### 42. Model / API cost accounting

Opening generation 1. Gameplay initial generation 5. Gameplay retry 1. Interpretation invocations 3. Player-model calls 6 (`gpt-4.1-mini`). Evaluator 0. Repair/rerun: no.

### 43. Readiness decision

C25 REVEALED A DEEPER SEMANTIC-ARCHITECTURE DEPENDENCY.

The contract boundary is in place and the historical suites held. The live standard did not. Resolver choice for a generic `ask` still depends on raw tokens in the C24 family selector, and a validated interpretation can still label speech as an act. That dependency has to be reviewed before another implementation cycle. No C26 was opened.

### 44. PR-BR status

PR-BR remains OPEN. No completion commit. No push. No PR-BS. The second 4×10 gate was not run and is not authorized. Human playtest was not run and is not authorized.

## PR-BR Continuation 23 — Pre-Contract Routing & Resolution-Ownership Architecture Discovery

Discovery only. No production behavior change. No gameplay generation call. No interpretation call. No evaluator call. No synthetic player. No smoke. No 4×10 gate. No human playtest.

### 1. Purpose

Find every live path from raw player language to a player-visible response that can resolve, change state, change discourse, or emit without first establishing the authoritative Resolution Contract. Decide which of those paths are legitimate, which are legacy shortcuts, and which are specialized resolvers that should run only after the contract exists.

### 2. Authorization basis

C22 repaired primary-versus-secondary intent, commitment modality, and explicit-but-unresolved addressee integrity. Deterministic evidence held: social ask plus supporting perception, conditional movement no longer executed, unresolved explicit addressee no longer replaced by another NPC, raw request-path stubs 12/12, broader relevant regression 345/345. C18–C21 protections stayed in place.

Fresh C22 validation then failed on ordinary conversation. The word "nearby" sent the turn into a procedural earshot route before Resolution Contract construction. That turn had no contract, no gameplay generation call, and no `accepted_response`. C22's addressee checks never ran. C18 could not seal a response that was never accepted.

### 3. C22 failure full trace

Session `artifacts/pr_br_continuation22/live/20261003T113446Z`, turn 4. Raw text:

> I nod thoughtfully, glancing toward the northwest where the crates stand drenched in rain. "Thank you for the warning. Have you heard anything about who or what might be causing trouble there? Any chance I could find shelter or supplies nearby before investigating further?

`POST /api/chat` enters `game.api.chat`.

1. `segment_mixed_player_turn` (`game/intent_parser.py`) splits the turn. `_extract_inline_adjudication_clause` walks question clauses from the end. `_looks_like_adjudication_question` is true because `_ADJUDICATION_TOKENS` contains `could`. The stored split, copied from the live session log, is:
   - `declared_action_text`: the nod, the thanks, and "Have you heard anything about who or what might be causing trouble there?"
   - `adjudication_question_text`: "Any chance I could find shelter or supplies nearby before investigating further?"
2. `merge_turn_segments_for_directed_social_entry` joins declared, spoken, and observation text and drops `adjudication_question_text`. Social routing never sees "nearby" or "could I".
3. `resolve_directed_social_entry` returns `should_route_social` false, reason `no_addressable_target`. The merged clause has second-person "Have you heard" and no NPC name. Interlocutor follow-up does not select the tavern runner.
4. `choose_interaction_route` does not force the scene-presence action lane. That lane's regex is earshot / who-is-here / in-range. It does not contain `nearby`.
5. The parser chain in `chat` (`maybe_build_passive_interruption_wait_action`, pursuit, `recover_actionable_explicit_world_action`, `parse_social_intent`, dialogue-first, exploration, `parse_intent`, declared-travel fallback) produces no action. The nod-and-glance clause is not a travel, inspect, or addressed social action those parsers accept. Dialogue-first returns none because social entry already refused the turn.
6. The unparsed fallback sets `adjudication_text` to the split question, not the full utterance. `_prefer_dialogue_over_adjudication` stays false because social entry is false.
7. `classify_adjudication_query` matches `\bnearby\b` and returns `perception_query` before the feasibility opener (`could I`) is considered. `resolve_adjudication_query` reads the scene roster and builds "In earshot right now: Gate Guard, Gate Serjeant, Tavern Runner." It does not mutate world state. The module documents that.
8. `chat` sets `resolution.kind` to `adjudication_query`, route `procedural_perception_query`, `gpt_called` false, and `gm` from `_build_adjudication_gm_output`. `attach_interaction_obligation` is not called. There is no Resolution Contract, no commitment status, and no operation.
9. `_finalize_player_facing_for_turn` still runs the emission gate. On a cold session the roster sentence can survive. After a prior tavern-runner exchange, the gate tags `final_emission_gate_replaced` and `final_emission_gate:anti_reset_continuation_fallback`. `local_exchange_continuation_fallback_line` in `game/anti_reset_emission_guard.py` calls `minimal_social_emergency_fallback_line`. `speaker_label` has no social NPC on an adjudication resolution and defaults to "The guard". The player sees: The guard says, "I do not know enough to answer that."
10. `lifecycle_applies` in `game/immutable_valid_response.py` requires a contract operation. This resolution has none. No `accepted_response` is sealed. C18 does not govern the line. C19 does not classify the roster or the guard sentence. C22 commitment and addressee fields are never read.

Deterministic reproduction, interpretation disabled, `call_gpt` stubbed so it cannot reach the network:

- Exact wording on a fresh frontier-gate session: `kind=adjudication_query`, contract absent, gameplay stub calls 0, visible roster sentence.
- Same wording after "I ask the tavern runner what he heard about the patrol." (that first turn's contract interlocutor is `tavern_runner`): second turn still `adjudication_query`, contract absent, reason `no_addressable_target`, route `procedural_perception_query`, visible guard line, `accepted` false. Record: `artifacts/pr_br_continuation23/c22_after_runner.json`.

### 4. First bypass decision point

The split is what hides the social clause. The point at which Resolution Contract ownership becomes impossible is the unparsed branch in `game.api.chat`: when `parsed is None` and `resolve_adjudication_query(embedded_question_text)` returns a result, the function emits and returns through persistence without `attach_interaction_obligation`.

`construct_resolution_contract` is reached only from `attach_interaction_obligation`. Production callers are `_run_resolved_turn_pipeline` (after a parser has already built a resolution) and the freeform `else` of that same unparsed branch. The adjudication `if` is the other arm. A static test locks that fact: the adjudication arm does not mention `attach_interaction_obligation`.

"Nearby" is not mis-classified in isolation. `classify_adjudication_query("Who is nearby?")` and `classify_adjudication_query("Can I find supplies nearby?")` both return `perception_query`. On a fresh session those short lines never reach that classifier's winner, because a social parser produces a `question` action first and the pipeline then builds an `ask` contract. The token selects a resolver only when every earlier parser has abstained and the fallback is allowed to see the split clause.

### 5. Definition of a pre-contract route

A pre-contract route is any execution path on which raw player language can materially affect the player-visible response, world, scene, character, discourse, location, or an authoritative fact before the normal Resolution Contract exists. That includes a missing contract, a skipped construction, an early return, a direct emit, a legacy handler, a deterministic action that mutates state first, and a fallback that manufactures text after the skip.

A parser that interprets the utterance and only afterwards enters `_run_resolved_turn_pipeline` is still a pre-contract semantic owner. The contract is attached after the action and the resolution object exist, and before `_apply_authoritative_resolution_state_mutation`. Commit of scene travel is after the attach. Meaning is chosen before it.

### 6. Complete route inventory

Raw chat language is owned by a sequence of peers. Order inside `chat` after segmentation and social entry:

| Order | Owner | Entry |
| --- | --- | --- |
| 1 | Campaign-start cue | `_is_campaign_start_turn_request` |
| 2 | Passive wait | `maybe_build_passive_interruption_wait_action` |
| 3 | Qualified pursuit | `parse_exploration_intent` when the shape matches |
| 4 | Explicit world action | `recover_actionable_explicit_world_action` |
| 5 | Social parser | `parse_social_intent` |
| 6 | Open solicitation / dialogue-first | `_build_dialogue_first_action` |
| 7 | Exploration parser | `parse_exploration_intent` |
| 8 | Generic intent | `parse_intent` |
| 9 | Declared travel override | `maybe_build_declared_travel_action` |
| 10 | Combat attack | `resolve_attack` when already in combat |
| 11 | Off-scene social line | `_build_offscene_target_gm_output` |
| 12 | Pending check prompt | `_build_check_prompt_gm_output` |
| 13 | Unparsed adjudication | `resolve_adjudication_query` |
| 14 | Freeform narration | `attach_interaction_obligation` then GPT |

`/api/action` does not re-segment free text. It trusts `action_type` (`roll_initiative`, `attack`, `skill_check`, `cast_spell`, `end_turn`, `exploration`, `social`), resolves, then uses the same pipeline except initiative, the no-enemy end-turn line, off-scene social, and a pending check, which emit without a contract.

HTTP session administration (`/api/snapshots`, load, reset, new campaign, clear log, response mode, import, and the campaign/scene/character/world editors) never interprets a gameplay sentence.

Every chat turn also calls `advance_world_tick` and saves the world before any contract. That clock is not a reading of the sentence.

### 7. Route table

`Before` means the route interprets raw language or emits before `construct_resolution_contract`. `Suppress` means it can finish the turn with no contract. Protection columns are for the path as it exists today.

| Route | Module / entry | Trigger | Before | Suppress | Creates | Consumes | Emit | Mutate state | Mutate discourse | C18 | C19 | C20/C21 | C22 | Class | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Campaign-start cue | `api._is_campaign_start_turn_request` | "start the campaign" on an empty log | YES | NO | YES, in the pipeline | NO | via pipeline | opening flags after attach | NO | NO, opening excluded | PARTIAL | NO | NO | A | low |
| Passive wait | `intent_parser.maybe_build_passive_interruption_wait_action` | wait / watch-for-disturbance, no question | YES | NO | YES, later | NO | via pipeline | after attach | after attach | YES | YES | YES | NO | C | medium |
| Qualified pursuit | `parse_exploration_intent` | follow/pursue the lead | YES | NO | YES, later | NO | via pipeline | after attach | after attach | YES | YES | PARTIAL | PARTIAL, travel text is pre-gated | C | medium |
| World-action recovery | `recover_actionable_explicit_world_action` | inspect, use, open, read, take | YES | NO | YES, later | NO | via pipeline | after attach | after attach | YES | YES | PARTIAL | PARTIAL, object actions use `committed_world_text` | C | high |
| Social parser | `social.parse_social_intent` | ask / tell / addressed speech | YES | NO | YES, later | NO | via pipeline | after attach | after attach | YES | YES | PARTIAL, target chosen first | NO | C | high |
| Dialogue-first | `interaction_routing._build_dialogue_first_action` | social entry or dialogue route | YES | NO | YES, later | NO | via pipeline | after attach | after attach | YES | YES | PARTIAL | NO | C | high |
| Exploration parser | `parse_exploration_intent` | look, go, search | YES | NO | YES, later | NO | via pipeline | after attach | after attach | YES | YES | PARTIAL | PARTIAL | C | high |
| Generic intent | `intent_parser.parse_intent` | residual verb patterns | YES | NO | YES, later | NO | via pipeline | after attach | after attach | YES | YES | PARTIAL | NO | C | medium |
| Travel override | `maybe_build_declared_travel_action` | declared movement, authored exit | YES | NO | YES, later | NO | via pipeline | location after attach | can break social | YES | YES | PARTIAL | PARTIAL, `committed_world_text` only | C | high |
| In-chat attack | `resolve_attack` | attack verb while `in_combat` | YES | NO, unless the early error return | YES, later | NO | via pipeline | YES, `save_combat` before attach | can break social | YES if pipeline runs | PARTIAL | NO | NO | C | medium |
| Off-scene social | `_build_offscene_target_gm_output` | social target not in scene | YES | YES | NO | NO | YES | NO | NO | NO | NO | NO | NO | B | high |
| Pending check | `_build_check_prompt_gm_output` | `requires_check` without a roll | YES | YES | NO | NO | YES | NO | NO | NO | NO | NO | NO | C | medium |
| Earshot / nearby | `adjudication.classify_adjudication_query` then roster | `nearby`, earshot, who is here, on the unparsed arm | YES | YES | NO | NO | YES | NO in the resolver; emission can still speak | does not write the runner | NO | NO | NO | NO | B | high |
| Place existence | same classifier, place-locality arm | is there a place nearby | YES | YES | NO | NO | YES | NO | NO | NO | NO | NO | NO | C | medium |
| Roll requirement | same classifier | roll / DC / skill check | YES | YES | NO | NO | YES | NO | NO | NO | NO | NO | NO | C | low |
| Feasibility | same classifier, `could I` / `can I` | feasibility opener when `nearby` did not already match | YES | YES | NO | NO | YES | NO | NO | NO | NO | NO | NO | B | high |
| State query | same classifier | what actions, how many, where is my | YES | YES | NO | NO | YES | NO | NO | NO | NO | NO | NO | B | medium |
| Initiative line | `api.action` `roll_initiative` | typed action | n/a, not a sentence | YES | NO | NO | YES | combat | NO | NO | NO | NO | NO | A | low |
| End-turn line | `api.action` `end_turn` with no enemy | typed action | n/a | YES | NO | NO | YES | combat | NO | NO | NO | NO | NO | A | low |
| Typed action resolvers | `api.action` attack, skill, spell, exploration, social | client `action_type` | YES for any free `intent` string | NO, except off-scene and check | YES, in the pipeline | NO | via pipeline | combat flags before attach | after attach | YES if pipeline runs | PARTIAL | PARTIAL | PARTIAL | C | medium |
| Session administration | snapshot, reset, editors, scene activate | HTTP, not `/api/chat` | n/a | YES | NO | NO | NO fiction | YES, by design | can wipe | NO | NO | NO | NO | A | low |
| Freeform narration | `attach_interaction_obligation` then GPT | unparsed and not adjudication | NO | NO | YES, before generation | YES | via C18 when the contract has an operation | after attach | after attach | YES | YES | YES | YES | contract path | — |

The freeform row is the only ordinary chat arm that establishes the contract before generation. It is not a bypass. It is listed so the boundary is visible.

### 8. Category A / B / C

**A — legitimate pre-contract. 4.**

- Session administration. A snapshot load is not a player intention about the fiction. The contract would not say what the click meant. C18–C22 are gameplay seals. The safety invariant is the existing storage and UI-mode policy, not a resolution owner.
- Initiative and end-turn status lines. The client already named the operation. The sentence is a table status. Forcing it through C18 would only wrap a fixed string.
- Campaign-start cue. The phrase is an explicit system request on an empty log. The pipeline still builds a contract afterwards, and C18 already excludes `scene_opening`. Bypassing the gameplay seals is safe because the turn is not an in-fiction commitment. The opening curator remains the content invariant.

Deterministic is not enough to put a route in A. Earshot, feasibility, and travel are deterministic and are not in A.

**B — ordinary gameplay that must establish a contract first. 4.**

- Earshot / nearby on the unparsed arm. This is the C22 turn. The player was still talking to the runner. The contract should have recorded an ask, or a presence question, before any roster lookup.
- Feasibility (`can I` / `could I` find supplies). That is a request about the fiction, not a system command.
- State query (`who is here`, `what actions are available`) when it is played as a sentence rather than a UI button.
- Off-scene social direct text. It answers a person-directed request with no contract and no acceptance seal.

**C — specialized resolvers that should sit below the contract. 13.**

Passive wait, pursuit, world-action recovery, social parser, dialogue-first, exploration parser, generic intent, travel override, in-chat attack, pending check, place-existence lookup, roll-requirement lookup, and the typed `/api/action` resolvers.

For the C22 kernel, the contract fields the roster resolver needs are operation `inquire` or `perceive`, dimension `presence` (or an equivalent local-entities dimension), target `local scene`, addressee empty, commitment `executed_now`. Inputs are the scene id and the addressable roster. Output is a list of present names or a nonresolution. It may not choose a speaker, write discourse, or emit. Emission stays on the accept path. Place existence needs operation `inquire`, dimension `place`, target the named place. Roll requirement needs operation `rules_query` and must pass C19 as an authoritative rule. Travel needs operation `act`, target the destination, commitment `executed_now`, and only then the authored-exit matcher. Inspection needs operation `inspect` and the object id. Social resolution needs operation `ask` (or the specific social act), addressee, and commitment. A check prompt needs the contract to say a roll is required, then the prompt is the resolver output, still sealed.

### 9. Semantic resolution-owner map

Eight systems can answer "what did the player mean?" on one chat turn:

1. Clause segmentation (`segment_mixed_player_turn`).
2. Directed social entry (`resolve_directed_social_entry`).
3. Social parser (`parse_social_intent`) and dialogue-first.
4. Exploration and world-action recovery.
5. Generic `parse_intent`.
6. Travel / authored-exit matcher.
7. Adjudication classifier (`classify_adjudication_query`).
8. Resolution Contract, only if arm 13 failed and arm 14 ran, or if a parser entered the pipeline.

Precedence is first successful parser, then adjudication, then freeform-plus-contract. There is no arbitration when they disagree. The first success returns. The contract, when it is built inside the pipeline, records the winner's action. It does not re-decide the utterance. Q1 shows the disagreement: the earshot classifier says `perception_query` for "Who is nearby?", and the social parser wins with operation `ask`.

### 10. Trigger-collision analysis

Six mechanisms steal or pre-empt ownership. They are not a blacklist. Each one currently selects meaning. After a contract exists, the same words should only select a resolver.

| Mechanism | Where | What it does today | What it should do |
| --- | --- | --- | --- |
| Adjudication tokens `could`, `can`, `would`, `is`, `are`, `roll`, `check`, `need` | `_looks_like_adjudication_question` | Pull the last question out of the social text | Mark a candidate clause. Do not delete it from ownership |
| `nearby`, earshot, who is here, in range, how far | `classify_adjudication_query` | If the unparsed arm runs, the turn is a roster query | Select the presence resolver only when the contract's dimension is presence |
| Scene-presence regex | `resolve_directed_social_entry` | Blocks social for earshot / who-is-here. Does not contain `nearby` | Same rule, applied to the contract, not to a substring |
| Listen / hear / see / spot | observation extraction and `_dimensions` | Can own the turn as perception | Already partly repaired inside the contract for supporting perception. The unparsed arm never gets there |
| Follow / leave / go plus a destination slug | authored-exit match on `committed_world_text` | Can own travel | Resolver for an `act` contract whose commitment is executed now |
| Ask / approach / speak plus a roster name | social entry and `parse_social_intent` | Can own the turn as talk | Resolver for an `ask` contract |

`nearby` inside "supplies nearby" is the collision that hit C22. The social-presence blocker does not use that word. The adjudication classifier does, and it runs before the feasibility test.

### 11. Multi-clause analysis

Confirmed. One trigger can capture the turn.

`_extract_inline_adjudication_clause` takes the last question that contains an adjudication token and removes it from the working text. Earlier questions stay in `declared_action_text` only if they were not the extracted clause. The social merger then ignores the extracted clause. If the declared remainder produces no parser action, the fallback adjudicates only the extracted clause.

On the exact C22 sentence the social question "Have you heard…?" is discarded from the resolver input. The supplies question is the entire adjudication. The established interlocutor is not read. A short "Who is nearby?" is not split away from a social clause, a parser accepts it, and the contract is built. The defect is the combination of a trailing token-clause and parser abstention, not the mere presence of the word.

### 12. Discourse ownership

| Route that skips the contract | Reads active interlocutor | Writes it | Effect on the C22 turn |
| --- | --- | --- | --- |
| Social entry, before the skip | Yes, for follow-up | No | Returned `no_addressable_target`. The runner was not selected |
| Adjudication roster | Reads `active_interaction_target_id` only to omit that name from the roster | No | Did not continue the runner |
| Anti-reset replacement | Reads exchange-established session | No | Replaced the roster with a guard line |
| Pipeline paths | Yes, inside the contract and discourse focus | Yes, after attach | Not entered |

The bypass explains a response that behaves as if the conversational partner were gone. The live turn did not write a new interlocutor and did not keep the runner. The visible speaker is the fallback default, not a bound NPC. Inspected-object and claim loss are not what this particular turn did. Those slots are updated from the contract, which was absent, so they were simply not touched.

### 13. C18 ownership

`lifecycle_applies` is false when the resolution has no contract operation, and it is false for `scene_opening` on purpose.

Gameplay-visible routes that can emit with no `accepted_response`:

- Unparsed adjudication. Proven on the C22 turn and on the stubbed replay. Provenance is the earshot template, then `anti_reset_continuation_fallback`. No hard validation of a generated candidate. The mutation risk is the speaker substitution. C18 should own this once it is an ordinary gameplay answer.
- Off-scene social line. Engine text, no seal.
- Pending check prompt. Engine text, no seal. A check prompt can stay a resolver result, but it should still be the accepted text of a contract that required the roll.

Initiative, end-turn, and session administration should not be forced through C18.

### 14. C19 authority

The earshot sentence is a player-visible fact about who is present. It is produced from scene state and never passes C19 authority classification. The later guard sentence is also player-visible and is not an authority classification. It is a catalog fallback. Place-existence and roll-requirement sentences on the same arm are likewise outside C19. Off-scene and check prompts are outside C19.

Pipeline turns that build a contract do go through hard validation, including C19, when the lifecycle applies.

### 15. C20 / C21 entity ownership

The C22 bypass did not instantiate an incidental person and did not bind the runner. It also did not use the C20/C21 canonical binding to choose the speaker. `speaker_label` defaulted to "The guard" because the adjudication resolution has no `social.npc_id`.

Social, dialogue-first, and travel parsers choose targets before the contract exists. When they then enter the pipeline, `apply_entity_binding` runs inside `attach_interaction_obligation`. The choice is earlier than the architecture that is supposed to own it. The skip paths never reach that call.

No code was changed. This is an inventory.

### 16. C22 commitment ownership

C22 is not universal. `committed_world_text` is consulted by the travel and object parsers and again inside `construct_resolution_contract`. It is not consulted by adjudication, off-scene emission, or the check prompt.

A conditional "nearby" question therefore cannot be saved by the C22 modality work, because those functions never run. Authored travel that does go through `maybe_build_declared_travel_action` remains gated by committed text even though that gate is before the contract. That is a resolver-level protection, not proof that every route honors commitment.

### 17. Historical failure reclassification

Reviewed player-visible failures only. No model replay.

| Case | Class |
| --- | --- |
| 4×10 B2 speaker pattern, contract ask was correct | CONTRACT-CORRECT / DOWNSTREAM |
| 4×10 B9 pre-seal catalog grimace, contract present | CONTRACT-CORRECT / DOWNSTREAM |
| 4×10 C8 look became ask | CONTRACT-CONSTRUCTION |
| 4×10 C10 wear dimension | CONTRACT-CONSTRUCTION |
| 4×10 D1 correct inspect, invented office passed validation | CONTRACT-CORRECT / DOWNSTREAM |
| 4×10 D3 wear dimension plus a non-person span | CONTRACT-CONSTRUCTION |
| 4×10 D7 incorrect contract, evasive figure | CONTRACT-CONSTRUCTION |
| 4×10 D8 incorrect contract, same figure | CONTRACT-CONSTRUCTION |
| C20 smoke turn 8, JSON document was the accepted text | UNRELATED |
| C20 smoke turn 9, questions parked in `adjudication_question_text`, contract kept the leading clause | MIXED |
| C21c live turn 1, listen owned a social ask, contract present | CONTRACT-CONSTRUCTION |
| C21c live turn 3, unresolved serjeant answered by the captain, contract present | CONTRACT-CONSTRUCTION |
| C22 live turn 4 | PRE-CONTRACT BYPASS |

C21's focused live session was 6/6 and is not in the failure list. C21b's live record did not add a separate absent-contract failure. Gate session logs under `artifacts/pr_br_full_gate/20261002T021950Z` and the C21 live logs do not contain another `adjudication_query` row. The scanner's only absent-contract gameplay row is C22 turn 4, counted twice because the session log and `turns.json` both store it.

### 18. Historical impact metrics

```
historical failures reviewed:                      13
confirmed pre-contract bypass failures:             1
probable pre-contract bypass failures:              1
unrelated:                                          1
insufficient evidence:                              0
```

The probable case is C20 smoke turn 9. A contract existed, so it is not a confirmed absence. The same splitter removed the questions from what the contract was allowed to own.

The absent-contract route has so far one confirmed player-visible failure. The ownership problem is wider than that turn. Eight peers can still decide meaning, and the contract is attached only after one of them wins, or not at all. The same splitter appears in C20 and C22. That is a recurring mechanism across validation cycles, not a one-word defect in the nearby regex.

### 19. Static and test-only bypass detection

A deterministic invariant is feasible and is now a test, not a production check:

For the unparsed adjudication arm in `game/api.py`, `attach_interaction_obligation` does not appear between `if adjudication is not None` and the freeform arm.

The companion test posts the twelve probes plus the exact C22 sentence with `ASHEN_DISABLE_LIVE_INTERPRETATION=1` and with `call_gpt` replaced by a stub that cannot open a client. Interpretation invocations observed: 0. The test fails if the interpretation client is called.

A future production invariant, not implemented: every ordinary `/api/chat` gameplay turn either has a Resolution Contract before specialized resolution, or the route is an enumerated Category A command.

### 20. Q1–Q12 route probes

Each probe used a fresh frontier-gate session. Interpretation calls: 0. `call_gpt` was a stub. Stub invocations are not model calls. Results: `artifacts/pr_br_continuation23/q_probes.json`.

| Id | Input | Classifier on that text | Chat owner | Contract | Operation | Emission |
| --- | --- | --- | --- | --- | --- | --- |
| Q1 | Who is nearby? | perception_query | social question, reason no_addressable_target | YES | ask | stub, sealed |
| Q2 | Can I find supplies nearby? | perception_query | social question, reason gm_feasibility | YES | ask | stub, sealed |
| Q3 | I ask the runner if there are supplies nearby. | none | social, declared actor switch | YES | ask, tavern_runner | stub, sealed |
| Q4 | I listen at the door. | none | observe | YES | perceive / sound | safe perception line, sealed, stub used twice |
| Q5 | I ask the guard and listen carefully. | none | observe action, contract ask | YES | ask, guard_captain | stub, sealed |
| Q6 | I inspect the footprints. | none | investigate | YES | inspect | stub, sealed |
| Q7 | I follow the road to the milestone. | none | interact | YES | act | stub, sealed, scene stayed frontier_gate |
| Q8 | Would the road lead to the milestone? | action_feasibility_query | social question | YES | ask | stub, sealed |
| Q9 | I use the key on the door. | none | freeform / contract | YES | perceive / use | safe perception line, sealed |
| Q10 | What does the notice say? | none | social question | YES | ask, dimension content | stub, sealed |
| Q11 | I ask the tavern runner what he heard about the patrol. | none | social, declared actor switch | YES | ask, tavern_runner | stub, sealed |
| Q12 | ((ooc)) what should I roll? | none | freeform / contract | YES | ask | stub, sealed |

Q1–Q12 all created a contract. None of them took the earshot arm. The classifier would have, for Q1, Q2, and the C22 clause, if the parsers had abstained. Q12 shows that an OOC marker in chat is not a Category A bypass. It still builds an ask contract and narrates. Real Category A handling is the separate HTTP commands, not this sentence.

Extra probes, same harness:

- Exact C22 wording, fresh session: contract NO, kind `adjudication_query`, stub calls 0, roster sentence emitted.
- Exact C22 wording after Q11: contract NO, route `procedural_perception_query`, guard line, no `accepted_response`.

Q7 did not change scenes. "to the milestone" did not match the authored old-milestone exit under this seed. That is a resolver result under a contract, not a bypass.

Q9's contract says perceive/use for "I use the key". That is a contract-construction miss on a path that did build a contract. It is out of scope for this cycle's repair.

### 21. Architectural options

**Option 1 — patch precedence.** Make social ask beat `nearby`. Immediate benefit: this one sentence would reach the runner. The next token (`could`, `listen`, `follow`, `use`) can take the same unparsed arm. The twelve short probes already show the social parser beating the classifier by accident of order. Precedence patches will keep colliding. Not recommended.

**Option 2 — contract first for every ordinary turn.** Language, then interpretation, then contract, then resolver. This matches the failure. It also moves every parser. Migration cost is the whole chat chain. Deterministic resolvers can be reused. Latency is a contract build, not automatically a model call, because the fast path already exists. The risk is doing all of that in one cycle.

**Option 3 — hybrid, the C10/C11 boundary extended.** A deterministic fast path may build the contract when the utterance is canonical and unambiguous. Otherwise the structured interpreter proposes and the existing validator accepts or rejects. Specialized resolvers then consume the contract. The freeform arm already does the second half. The unparsed adjudication arm and the peer parsers do not. This is the natural extension. Recommended.

**Option 4 — keep peer semantic owners and arbitrate.** The repository already is this design. Eight owners, first-success precedence, no disagreement handling. Q1's classifier and parser disagree today. Test burden grows with every new token. Not recommended.

### 22. Recommended architecture

```
raw player language
    -> deterministic fast path, or one structured interpretation if it abstains
    -> authoritative Resolution Contract
    -> specialized resolver
    -> hard validation / authority
    -> accept
    -> commit
    -> emit the accepted text
```

Earshot, authored travel, inspection, mechanics, scene lookup, and deterministic adjudication become ways to satisfy a contract. They stop being competing readers of the raw sentence.

### 23. Model and API cost

The 4×10 gate at `20261002T021950Z` recorded 15 interpretation calls across 40 gameplay turns (persona A 2, B 4, C 6, D 3). The other turns used the deterministic fast path inside `construct_resolution_contract`. C22's four live turns used 0 interpretation calls. Three of them generated. Turn 4 generated nothing because it never reached the contract.

Contract-first does not add an interpretation call on turns that already build a contract. Those turns already pay the fast path or the one abstention call. The bypassed turn currently pays neither. Putting it on the contract path adds a fast-path build, and an interpretation call only when that fast path abstains. If the contract is a social ask, the turn also regains the gameplay generation call the bypass skipped. That is the call ordinary turns already make. It is not a new call on every turn.

No large mandatory per-turn model-call increase.

### 24. Latency

The added stage on the bypassed arm is one in-process contract build and a roster or nonresolution lookup the engine already performs. No extra state store. Model latency appears only on fast-path abstention, which is the same rule as today. Do not add a routing layer beyond that.

### 25. Migration boundary

Next cycle should change the unparsed arm in `game.api.chat` and the way `resolve_adjudication_query` is selected. It should not rewrite C18, C19, C20, C21, or C22.

Stay internally intact, and become callers:

- `resolve_adjudication_query` roster, place, roll, feasibility, and state arms
- authored-exit matching
- inspection and object resolution
- social resolution
- check-prompt text

Disappear as raw-language owners on the unparsed arm:

- the direct jump from a token to `_build_adjudication_gm_output`
- the anti-reset replacement of that output by a guard line when no contract exists

Legacy concern: tests that expect "Who is nearby?" to emit the roster sentence must start expecting a presence contract first. Tests that expect the C22 sentence to stay with the runner must expect an ask contract. `tests/test_pr_br_continuation23_precontract_routes.py` is the new witness and should be updated when the arm changes, not before.

Do not move every parser in that same cycle. The peer parsers still build a contract today, after they choose. Reordering them under the contract is the following cycle, once the skip path is closed. Leaving them in place for one cycle does not preserve the bug, because the bug is the skip.

### 26. Proposed invariants

Checked against the repository. All ten are currently false for at least one ordinary path, except V4, which is true only if Category A stays an explicit list.

- V1. One semantic owner per ordinary gameplay turn. False today. Eight peers.
- V2. Contract before specialized semantic resolution. False for adjudication, off-scene, and check prompts. False in spirit for parsers that resolve first and attach second.
- V3. Resolvers consume the contract and do not reread raw language. False for adjudication and travel matchers.
- V4. Category A bypasses are explicit and enumerable. Feasible. The four A rows above are the list.
- V5. No ordinary gameplay emit outside C18. False for adjudication, off-scene, and check prompts.
- V6. No factual gameplay content outside C19. False for the earshot roster.
- V7. No NPC selection outside C20/C21. False for the guard default on this path.
- V8. No uncommitted action outside C22. True for travel that uses `committed_world_text`. False as a universal claim, because the skip paths never consult it.
- V9. Resolver failure returns to contract-aware nonresolution. False. Anti-reset substitutes an unrelated speaker.
- V10. Trigger words select resolver capabilities only after ownership. False. `could` and `nearby` select the route.

### 27. Implementation risks

- Building the contract from the full utterance may still classify the C22 sentence as perception if the fast path keeps today's nearby rule. The fast path must represent the social ask as primary. That is existing C22 behavior, and it only helps if the contract is actually built.
- A presence contract for "Who is nearby?" must not be implemented as another token exception. The operation and dimension have to come from the fast path or the interpreter.
- Emission tests that golden the guard line or the raw roster line will fail when the seal starts owning the text. That is the intended break.
- Moving only the unparsed arm leaves parser-first ownership in place for inspect, travel, and ask. Those paths already seal. They are the next cycle, not a reason to block this one.
- Do not let the anti-reset guard treat a contract-backed answer as an intro fallback.

### 28. Exact recommended next implementation cycle

PR-BR Continuation 24 — close the unparsed skip.

1. On the unparsed chat arm, build the Resolution Contract from the full player text with the existing fast path, and with one interpretation call only on abstention.
2. Select earshot, place, roll, feasibility, or state resolution only from contract fields.
3. If the contract is an ask, do not call the roster resolver because a later clause contains "nearby".
4. Emit only through the existing accept path. Do not replace a contract-less roster sentence with `speaker_label`'s default guard.
5. Leave C18–C22 internals, the nearby regex, and the other parsers alone in that cycle.
6. No 4×10 gate and no human playtest in that cycle either, until the deterministic probes show the exact C22 sentence has a contract and does not speak as the guard.

### 29. Readiness decision

PRE-CONTRACT ROUTING IS A SYSTEMIC ARCHITECTURAL OWNERSHIP PROBLEM — CONTRACT-FIRST / RESOLVER-BELOW-CONTRACT IMPLEMENTATION RECOMMENDED.

The confirmed player-visible failure is one route. The route exists because ownership is a race among peers, and the contract is not in the race until a parser has already won or the freeform arm is reached. A precedence patch would move one token. The evidence from Q1, from the splitter, and from the eight owners supports putting the contract first and the resolvers underneath. Option 3 is the shape. Continuation 24 is only the skip-path slice.

### 30. PR-BR status

PR-BR: STILL OPEN.

No completion commit. No push. No PR-BS. The second 4×10 gate is not authorized. Human playtest is not authorized. Production behavior was not modified. Model calls during this discovery: 0 gameplay generation, 0 interpretation, 0 evaluator, 0 synthetic player.

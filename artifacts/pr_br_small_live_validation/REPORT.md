# PR-BR Small Live Validation: Structured Claims and Authority Continuity

Date: 2026-10-04. Live model: gpt-4.1-mini. Observation only.

## 1. Executive conclusion

Manual result: FAIL. Stopped after A2 under mandatory stop condition 5, because a recursive authority-laundering chain begins. Four planned turns remain unrun. This is an observed semantic authority failure, not a finding that the inference was saved as objective world state.

A1 returned a valid envelope but declared only the two authored observations. It hid forceful-impact/prolonged-strain hypotheses in narration. Both initial and retry candidates failed hard validation. Bounded sentence preservation then emitted two sentences from the first candidate, sealed them with an empty claim audit, and persisted no GM inference. A2 repeated the actual prolonged-strain hypothesis. Its accepted retry said the precise cause of **this prolonged strain** was unknown. That wording presupposes the generated strain while qualifying only its cause. The declaration validator accepted the enclosing unresolved-status statement, without a semantic owner for the embedded strain proposition.

The temporal player-hypothesis bucket remains bounded, and neither scene fact list gains the explanation. Those protections do not undo the emission failure. Exact sealing preserves the wrong accepted semantics faithfully. This run cannot assess direct correction or NPC improvisation, because the stop condition forbids spending the remaining turns.

## 2. Exact scenario setup A

Fresh isolated storage: `isolated_A/data`; active scene: `loom_workshop`; location: `Loom workshop`; summary: `A wooden loom stands in a workshop.`

Exactly two authored visible facts:

- `The wooden loom beam is cracked.`
- `The loom's iron brace is bent.`

Interactable: id `loom`, label `wooden loom`, aliases `loom beam`, `beam`, `iron brace`, `brace`. No hidden facts, discoverable clues, enemies, actions, objects, exits, or NPCs in the active scenario. No cause, actor, event time, culprit, or negative evidence authored. Complete initial session/world/scene records: `setup_A.json`.

The application defaults supply campaign, character, combat, conditions, and world scaffolding. Default factions exist but have no authored connection to the loom. Default scenes `frontier_gate`, `market_quarter`, and `old_milestone` exist solely to satisfy startup scene validation. They were not visited. The session begins at turn counter 1. The default nested `scene_state.active_scene_id` initially says `frontier_gate`; the actual session active scene and custom scene fixture say `loom_workshop`. These exact defaults are disclosed in the snapshots, not silently normalized.

One fixture startup error occurred before any API or gameplay attempt: startup added default scenes whose frontier-gate exit referenced an absent `old_milestone`. Completing the default fixture resolved startup; no gameplay/model call was repeated. See `startup_fixture_error.json`.

## 3. Turn A1 full trace

Player: `I examine the cracked loom beam and bent iron brace closely. What does this damage suggest?`

Contract: `inspect`, target/subject `wooden loom`, dimension null, dimensions empty; raw input preserves the complete question, but the decision does not contain INFER. The inspection/interpretation request was therefore not fully preserved in operative authority. Decision realization claims contain only the two authored facts with `world_truth`, `established`, and `MUST_STATE`.

Initial envelope: valid. Two declarations, both `realize`, authored-world-fact observations. Two accepted declarations, zero rejected declarations. No inference declaration. Narration invents a deeply cracked beam, possible functional/safety consequences, forceful impact or prolonged strain, rough handling/wear, and repair consequences. An incidental proposal adds dust as an implication of unrepaired age; that proposal is rejected and not emitted.

Initial declaration validation passes; combined validation fails. The recorded violations focus on the first sentence's structural weakness/consequence and undeclared causal content. The undeclared hypotheses in the later sentences are missed by the sentence audit. The retry is one real generation call.

Retry envelope: valid, zero declarations. Exact narration: `The wooden loom beam is cracked. Its iron brace is bent, both indicating wear and damage but without clear signs of how or when these occurred.` It fails because an authored observation appears without a declaration. The retry also introduces unauthored negative evidence about signs of cause/time, but that line is not emitted.

Final acceptance reason: `bounded_sentence_preservation`. Final provenance: `initial_generation`. Exact sealed AND emitted text:

> The iron brace meant to support the beam is bent out of shape, suggesting either forceful impact or prolonged strain under heavy stress. Together, these damages hint that the loom has suffered significant wear or rough handling, possibly diminishing its usefulness unless repaired.

The seal reports hard-valid with `claim_results: []`, `proposed_facts: []`, and `violations: []`. Its audit has no declaration-validation or narration-validation subrecord. No GM inference, player hypothesis, or active claim is stored. Two rejected temporal entries are recorded: the first candidate's structural-weakness sentence and the retry's undeclared authored observation. The scene fact list remains exactly the two initial facts.

Raw output, requests, responses, usage: `model_calls.json`, calls 2 and 3. Complete payload, attempts, audits, state, exact text: `A1_full_trace.json`. Post-player/pre-generation snapshots and parsed generation files are included separately.

Manual A1: FAIL. Qualified prose cannot substitute for declaration ownership and GM-inference persistence.

## 4. Turn A2 full trace

Player: `So if prolonged strain under heavy stress is what happened to the loom, what would have caused that strain?`

This references the actual emitted A1 hypothesis. No replacement inference was authored or inserted. Before A2, `gm_inferences` is empty. Contract: `ask`, subject/target `wooden loom`, dimension null. The decision has the two authored observation claims plus an unresolved consequential slot; it cannot retrieve an A1 GM inference because none was persisted.

Initial envelope: valid. Two declarations, modes `realize` and `propose`. Both rejected: an unknown-cause statement is `unauthorized_declared_claim`; a proposal that further inspection could reveal the cause is `proposal_inference_not_permitted`. Narration introduces heavy use, flawed craftsmanship, external forces over time, and potentially overlooked evidence. Declaration failure short-circuits the narration audit; those residuals are manual findings, not a successful automatic narration audit.

Retry envelope: valid. Three `realize` declarations accepted: cracked beam and bent brace as authored world truth, plus `The cause of the prolonged strain on the loom remains unresolved.` as `speculation`, `observation`, `unresolved`, `do_not_persist`, owned by `decision.epistemic_acts`. Its semantic identity contains only the unresolved cause slot, not the separate proposition that prolonged strain happened.

Final acceptance: `regeneration_hard_valid`. Exact sealed AND emitted text:

> The wooden loom beam is cracked, and the iron brace meant to support it is bent. However, the precise cause of this prolonged strain on the loom is not known from the visible evidence here.

Automatic final narration audit: hard-valid, zero violations, zero narration claim results. The declaration audit supplies three accepted claims. Manual semantic finding: the second sentence presupposes prolonged strain as an event/condition and marks its cause uncertain. This does not preserve A1's alternative possibilities.

After A2, `gm_inferences` remains empty. The full player question persists as a `player_hypothesis`, `observation`, `hypothesis`. Active claim id `claim_8e06a38c88` has that exact player-question label and player-hypothesis status. Four rejected temporal entries now exist. Scene facts remain unchanged. No inference is saved to objective scene/world facts.

Raw calls: `model_calls.json`, calls 4 and 5. Full evidence: `A2_full_trace.json`. Manual A2: FAIL. Mandatory stop condition 5 applies: the chain from undeclared GM speculation through player repetition into an accepted presupposition has begun. No additional turns were sent.

## 5. Turn A3 full trace

NOT RUN under stop condition 5. Intended question would bind to prolonged strain and ask whether it is known or only possible. No contract, declaration, narration, retry, seal, emission, or state transition exists. Direct epistemic correction is untested.

## 6. Temporal authority table

The actual inference proposition is `prolonged strain under heavy stress` as a possible explanation of the bent brace/damaged loom. The authored observations remain distinct propositions.

| Stage / proposition | Source | gm_inference | player_hypothesis | world truth | active_claim | promoted? |
| --- | --- | --- | --- | --- | --- | --- |
| After A1: cracked beam | Authored `scene.visible_facts.0` | No | No | Yes, pre-existing | None | No |
| After A1: bent brace | Authored `scene.visible_facts.1` | No | No | Yes, pre-existing | None | No |
| After A1: prolonged strain under heavy stress | Undeclared emitted narration | Missing | No | No stored fact | None | Unowned emitted possibility |
| After player A2 / before initial generation: prolonged strain premise | Player conditional question | Missing | Not yet committed to temporal bucket | No stored fact | None | No stored promotion |
| After GM A2: prolonged strain premise | Accepted unresolved-cause sentence | Missing | Full A2 question, hypothesis | No stored fact | `claim_8e06a38c88`, player hypothesis | Semantic presupposition strengthens; stored authority does not |
| After A3 | Not run | N/A | N/A | N/A | N/A | Untested |

The pre-generation snapshot is the actual state during processing after player input; it is not an invented intermediate temporal commit. A2's temporal hypothesis is committed with the sealed output. Stored repetition does not promote, but narration does not preserve the same ceiling. These are separate findings.

## 7. Exact scenario setup B

PLANNED, NOT SEEDED OR RUN. Fresh isolated storage `isolated_B/data`; active scene `cloth_stall`; summary `A cloth seller stands at a market stall.`; visible fact `A cloth seller stands beside folded cloth at a market stall.` Ordinary NPC id `cloth_seller`, name `Cloth Seller`, location `cloth_stall`, topics empty. No authored preference, routine, secret, important history, faction connection, or quest knowledge. No setup_B snapshot exists because stopping preceded sequence B.

## 8. Turn B1 full trace

NOT RUN. Planned mundane preference question; no model output or invented detail exists. NPC improvisation and incidental persistence untested.

## 9. Turn B2 full trace

NOT RUN. No B1 detail exists to recall. Consistency and harmless elaboration untested.

## 10. Turn B3 full trace

NOT RUN. No mundane detail exists to tempt into a consequential connection. NPC consequence boundary untested.

## 11. Structured-protocol metrics

Four planned turns are unrun, not failures or passes. The requested six-turn denominator is shown as planned-slot counts; measured rates use the two attempted turns.

| Metric | Planned six slots | Observed two turns |
| --- | --- | --- |
| First-attempt structured compliance | 2 / 6; four unrun | 2 / 2 |
| First-attempt hard valid | 0 / 6; four unrun | 0 / 2 |
| Retry | 2 / 6; four unrun | 2 / 2 (100%) |
| Safe fallback provenance | 0 / 6; four unrun | 0 / 2 |
| Undeclared consequential content, manual initial-output audit | 2 / 6; four unrun | 2 / 2 |
| Emitted consequential proposition lacking exact semantic owner | 2 / 6; four unrun | 2 / 2 |
| Rejected declarations | 2 total, both A2 initial | 2 |

| Turn / attempt | Envelope valid | Declared | Modes | Accepted declarations | Rejected declarations | Hard valid | Undeclared residuals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 initial | Yes | 2 | realize x2 | 2 | 0 | No | Automatic first-sentence violation; manual later causes/history/consequences |
| A1 retry | Yes | 0 | none | 0 | 0 | No | Automatic undeclared authored beam observation; manual negative evidence |
| A2 initial | Yes | 2 | realize, propose | 0 | 2 | No | Narration audit skipped after declaration rejection; manual causes/history/evidence lead |
| A2 retry | Yes | 3 | realize x3 | 3 | 0 | Yes, automatic | Embedded prolonged-strain premise remains unowned, manual |
| A3/B1/B2/B3 | Not run | N/A | N/A | N/A | N/A | N/A | N/A |

A1 final provenance `initial_generation`, bounded preservation; A2 `regeneration`; both have an actual retry. A1's sealed `generation_attempts: 1` undercounts actual calls and must not replace transport evidence.

## 12. Claim-laundering audit

Every consequential emitted semantic unit is accounted for below. Missing ownership is explicitly recorded as a failure rather than inferred from a hard-valid stamp.

| Turn / proposition | Declaration | Accepted decision owner | Provenance / authority / status | Temporal destination |
| --- | --- | --- | --- | --- |
| A1: brace bent out of shape | Initial authored brace declaration | Authored fact exists, but final seal has no claim results | Authored clause warrants world truth/established; seal omits owner | Remains pre-existing scene fact |
| A1: brace intended to support beam | None separately | None for this function relation | Generated functional gloss, unstamped | None |
| A1: forceful impact could explain damage | None | None | Generated speculation; no system authority/status | Missing GM inference |
| A1: prolonged strain under heavy stress could explain damage | None | None | Generated speculation; no system authority/status | Missing GM inference |
| A1: significant wear or rough handling | None | None | Generated historical/causal interpretation, hedged | Missing GM inference |
| A1: usefulness possibly reduced unless repaired | None | None | Generated consequence/repair condition, hedged | No accepted owner/persistence |
| A2: beam cracked | Retry authored observation declaration | `rc_9deeeafa5043`, `scene.visible_facts.0` | authored_world_fact / world_truth / established | Pre-existing scene fact |
| A2: brace bent | Retry authored observation declaration | `rc_49829b26c2ee`, `scene.visible_facts.1` | authored_world_fact / world_truth / established | Pre-existing scene fact |
| A2: brace intended to support beam | No separate declaration | No distinct function owner | Generated functional gloss | None |
| A2: precise cause unresolved | Retry unresolved-status declaration | `rc_5aaab7e06e33`, `decision.epistemic_acts` | speculation / observation / unresolved | do_not_persist |
| A2: prolonged strain happened / exists | Embedded in unresolved-cause declaration, not separately declared | None for occurrence of strain | Accepted enclosing uncertainty masks an unqualified premise | Player conditional remains hypothesis; no GM inference or world fact |

Mandatory mixed-sentence check: A1's first emitted sentence combines the authored bent-brace observation with generated forceful-impact/prolonged-strain explanations. The final seal audit is empty, so it cannot demonstrate distinct clause authority. It does not stamp the sentence as world truth, but it fails to assign the inference a semantic owner. A2's second sentence puts an unowned presumed event inside an accepted uncertainty statement. Clause-specific authority is therefore not demonstrated.

## 13. Retry/fallback analysis

Both attempted turns used exactly one content retry. Four envelopes parsed successfully across four generation calls. A1's retry failed; preservation selected speculative text from the first candidate. A2's retry passed the automatic audit while preserving an unsafe presupposition. No `safe_nonresolution` provenance occurred.

Read-only diagnosis: `game/immutable_valid_response.py` `_bounded_keep` checks new dictionaries containing only `player_facing_text`. The envelope metadata and declarations are absent. `_check` derives declarations from metadata and passes None when absent. This makes preservation audit a different path from structured candidate validation. The exact accepted A1 audit confirms the resulting empty ownership record. The retry did not fix A1, and its final initial-generation label obscures the retry unless calls are counted independently.

No repair was implemented. Neither a format-only fix nor retry success alone is sufficient evidence for release readiness.

## 14. Naturalness table

| Turn | AUTHORITY-CORRECT | EPISTEMICALLY-CORRECT | RESPONSIVE | USEFUL | NATURAL | STATE-CONSISTENT | Manual overall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | FAIL | BORDERLINE | PASS | PASS | PASS | FAIL | FAIL |
| A2 | FAIL | FAIL | BORDERLINE | BORDERLINE | PASS | BORDERLINE | FAIL |
| A3 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| B1 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| B2 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |
| B3 | Not run | Not run | Not run | Not run | Not run | Not run | Not run |

A1 is readable, responsive, and interprets the damage, but lacks authorized inference ownership/persistence. A2 is readable and admits a knowledge limit, but shifts uncertainty from whether strain happened to what caused the presumed strain. It cannot count as a competent epistemic correction.

## 15. State/provenance continuity analysis

Exact sealed/emitted equality holds for 2 / 2 attempted turns. No raw JSON reaches the player. Scene files are unchanged after both turns. No new culprit, actor, event time, causal explanation, or supporting physical evidence is stored as objective scene fact. `gm_inferences` stays empty throughout. A2 player-hypothesis storage and active claim retain `hypothesis` status. A1 cannot be retrieved as a persisted inference because its seal supplies no accepted claims.

The entire world record is NOT unchanged: default world ticks increment faction agenda progress and pressure and append faction-pressure events. A1 changes all faction progress counters from 0 to 1 and House Verevin/Ash Cowl pressure from 2 to 3. A2 changes progress from 1 to 2 and Ordo Pyric pressure from 1 to 3 across the two turns. No faction update connects to the loom. These engine changes must not be described as unchanged objective state or as model-authorized loom facts; full before/after world snapshots disclose them.

The failure is semantic emission/ownership and loss of inference provenance, with subsequent presupposition strengthening. Stored world-truth promotion was not observed. Direct confidence correction and NPC memory remain untested.

## 16. Undeclared consequential content

A1 initial: physical severity `deeply cracked`; possible functional/safety consequence; forceful impact; prolonged strain under heavy stress; significant wear/rough handling; usefulness/repair condition. Its incidental dust proposal also implies elapsed unrepaired time. Only the two plain authored observations were declared. The final output retains the two causal possibilities, wear/handling history, and consequence/repair condition, and adds a function gloss.

A1 retry: no declarations despite observation text, plus unauthored lack of clear signs of cause/time. Not emitted.

A2 initial: stress/strain treated as a condition, heavy use, flawed craftsmanship, external forces over time, possibly missed evidence, and odor implying neglect. Neither declared rejected row owns all these hypotheses. They are not emitted except that the strain premise survives in the retry.

A2 retry/final: enclosing uncertainty declaration owns only the unknown cause. The occurrence of prolonged strain remains implicit and unqualified; it lacks its own authorized semantic status.

## 17. Rejected declarations

Exactly two, both A2 initial:

1. `The precise cause of the prolonged strain on the wooden loom is unknown` - mode realize, requested authored_world_fact, status unresolved; reason `unauthorized_declared_claim`.
2. `Inspecting the cracked wooden loom beam closely might reveal overlooked details explaining the cause of the strain` - mode propose, requested npc_claim, possible, MAY_INFER, gameplay_lead; reason `proposal_inference_not_permitted`.

Incidental proposal rejections are separate from declaration counts. Temporal rejected rows include narration violations and an undeclared authored observation; they are not additional rejected declarations.

## 18. Exact model/API call count

| Category | Count |
| --- | --- |
| Gameplay turns attempted/completed | 2 / 2 |
| Initial generation calls | 2 |
| Retry generation calls | 2 |
| Interpretation calls | 0 |
| Preflight calls | 1 |
| Other model/API calls | 0 |
| Total model/API calls | 5 |
| HTTP Responses attempts | 5, all HTTP 200 |
| SDK transport retries | 0 |
| Unspent gameplay turns | 4 |

| API call | Purpose | Turn | Model | Input tokens | Output tokens | Total tokens |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Preflight | Startup | gpt-4.1-mini | 24 | 2 | 26 |
| 2 | Initial generation | A1 | gpt-4.1-mini | 24750 | 598 | 25348 |
| 3 | Retry generation | A1 | gpt-4.1-mini | 26010 | 159 | 26169 |
| 4 | Initial generation | A2 | gpt-4.1-mini | 29221 | 604 | 29825 |
| 5 | Retry generation | A2 | gpt-4.1-mini | 30917 | 384 | 31301 |

Total provider usage: 110922 input + 1747 output = 112669 tokens. Cached input tokens: 0. Full requests contain model context but no authentication headers or API key. Counts come from the actual Responses entry point and HTTP send observer, not seal metadata.

## 19. Recommendation

Return to architectural review of semantic ownership through sentence preservation and of embedded presuppositions within epistemic declarations. Review the missing inference permission on A1's multi-sentence question. The evidence distinguishes good envelope syntax from broken authority continuity. Do not run a broader gate or conclude that NPC improvisation works from this stopped run. No production repair, prompt/schema change, detector/test change, additional turn, rerun, 4x10 gate, PR-BS work, commit, or push was performed.

C.
STRUCTURED CLAIM ARCHITECTURE FAILED TO PREVENT AUTHORITY
LAUNDERING OR TEMPORAL PROMOTION;
RETURN TO ARCHITECTURAL REVIEW

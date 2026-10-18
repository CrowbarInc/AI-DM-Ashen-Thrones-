# PR-BV — PR-BS versus current behavioral guidance

MODE: FORENSIC DISCOVERY. MODEL/API CALLS: ZERO. NO IMPLEMENTATION.

Compared artifacts:

- Current: `artifacts/pr_bu_pr_bt_final_repaired_chain_micro_live/evidence/P*/provider_request_attempt_generation_1.json`
- PR-BS: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P*/provider_request_attempt_generation_1.json`

The current provider user payload is byte-identical to the selective-restoration gate. Recipe, provider decision, provider contract, and `response_policy` are byte-identical to PR-BS on P1, P2, and P3. The realization envelope and the `STRUCTURED CLAIM DECLARATION RULE` are byte-identical (schema 2,756 characters, declaration rule 1,251 characters).

What changed is the system-prompt head and the instruction list.

| Surface | PR-BS | Current | Delta |
| --- | ---: | ---: | ---: |
| System prompt, all probes | 12,975 | 9,564 | −3,411 |
| P1 instructions | 107 items / 25,342 chars | 80 items / 13,124 chars | 42 removed / 15,114 chars; added 2,896 chars |
| P2 instructions | same cut, social lines included | compact social lines |  removed 14,856 chars; added 2,556 chars |

Token sketch uses about 4 characters per token. Instruction net on P1 is about −3,050 tokens. System net is about −850 tokens. That is the bulk of the measured 12.5% initial-input reduction (P1 25,208 tokens to 21,952).

A raw instruction dump is in `artifacts/pr_bv_first_pass_realization_competence/P1_removed_instructions.json` and `P1_added_instructions.json`. This file classifies the behavioral function.

## G1 — Authority

| | |
| --- | --- |
| PR-BS wording | Instruction, 554 characters: “Do not assert unresolved outcomes as settled fact. Do not assert hidden causes or hidden truths as confirmed… Observable visible cues are allowed; omniscient conclusions are not.” |
| Current wording | Policy JSON is unchanged. Compact `POLICY BRIDGE` points at `narrative_authority`. System rule 4 still forbids asserting unresolved outcomes. The epistemic protocol forbids a mechanism, setting, maintenance history, or causal chain. |
| Removed / retained | The essay is removed. The objects and the short prohibitions remain. |
| P1 | Medium. The “hidden causes” sentence is the authority form of the ceiling. The current protocol already restates it, and the model still wrote a cause. |
| P2 | Low. P2’s miss is a new established fact, which `generated_dialogue_as_authored_world_fact` already forbids in the recipe. |
| P3 | Low. The hypothesis was not promoted. |
| Behavioral importance | Medium as a reminder, already duplicated. |
| Approximate cost | 554 characters, about 140 tokens, if restored as prose. Not recommended. |

## G2 — Operation selection

| | |
| --- | --- |
| PR-BS wording | No turn-local operation name. Question-resolution essay: direct answer, then optional elaboration, then optional hook. “If full certainty is unavailable, provide the best grounded partial answer and state uncertainty in-character.” Investigate line in the system head: “reveal new information, consequence, tension, or a narrowed decision.” |
| Current wording | New `EPISTEMIC REALIZATION` paragraph, about 650 characters, shared by every probe: on an interpretation, state observations, add one possibility, say cause/actor/time/history stay unresolved, do not add a mechanism or causal chain; a player hypothesis stays hypothetical and observation does not settle it. Recipe `answer_strategy` is unchanged and does not say which operation to perform beyond “one qualified possibility”, “ordinary dialogue”, or “realize the required claims”. |
| Removed / retained | The “best grounded partial answer” essay is removed. A more specific operation paragraph was added in the system prompt and is not copied into the recipe. |
| P1 | High, and the current paragraph is the right operation. It lost to the recipe’s “qualified possibility” plus action-outcome framing. PR-BS did not have a cleaner operation sentence. Its accepted answer was still “frequent use or recent stress”. |
| P2 | Medium. PR-BS social essay said a refusal stays conversational. Current recipe still says ordinary dialogue, then tells the model to realize because required claims exist. |
| P3 | High positive. The hypothesis half of the new paragraph matches the successful answer. The recipe does not. |
| Behavioral importance | This is the family that matters. The useful text is already present and not turn-local. |
| Approximate cost | The protocol is already paid for. Replacing `answer_strategy` with the turn-local operation sentence adds 127, 99, and 106 characters on P1, P2, and P3, about 30 tokens each. |

## G3 — Epistemic expression

| | |
| --- | --- |
| PR-BS wording | “Compose it from known_edge, unknown_edge, next_lead.” Fallback essay, 459 characters: “state the strongest grounded known edge plus the unknown edge.” Narrator line, 163 characters: anchor uncertainty to visible circumstances rather than omniscient wording. System head: state uncertainty in-character. |
| Current wording | `UNCERTAINTY POLICY` is a field pointer plus “frame uncertainty as world-facing limits” and “vary sentence count”. The protocol says “say explicitly that cause, actor, time, and history stay unresolved.” It does not name the closer “remains unclear”. On P1, `fallback_behavior.uncertainty_active` is false, so the fallback essay would not have been an active obligation even in PR-BS. |
| Removed / retained | The known-edge / unknown-edge composition essay is removed. The protocol’s unresolved sentence is the selective restoration of this family. |
| P1 | Historically high, because PR-BS passed with “remains unclear” wrapped around a causal story. On this corpus the model skipped the unresolved sentence in both post-restoration samples. More closer prose is not what those samples lacked in the payload. They lacked obedience to the sentence already present, under competing “answer / specificity / consequence” pressure. |
| P2 | Low. |
| P3 | Medium. P3’s hedge flags are on (`require_partial_to_state_unknown_edge` true), and the model used “cannot be confirmed”. |
| Behavioral importance | High for old validator acceptance. Low as a further restoration. |
| Approximate cost | About 860 characters across the three uncertainty instructions, about 220 tokens. Restoring them would mostly restate the protocol. |

## G4 — Naturalness

| | |
| --- | --- |
| PR-BS wording | Perception example with a jaw-tightens sentence. “Vary sentence count and cadence.” Social structure, 477 characters: “NPC/social lines should sound spoken, not essay-like… Uncertainty or refusal stays conversational and in-world.” |
| Current wording | Short perception line. P2 adds “keep quoted NPC speech primary, answer/refuse/qualify conversationally.” Cadence variation is one clause on the uncertainty pointer. |
| Removed / retained | The example and the long social-voice essay are removed. A one-line social instruction remains on P2. |
| P1 | Low. Naturalness did not cause “years of use”. |
| P2 | Medium for voice. The retry’s silent refusal is the thin outcome. The first-pass voice was already natural. The failure was the declaration around it. |
| P3 | Low. |
| Behavioral importance | Secondary for P2 color, not the authorization miss. |
| Approximate cost | About 500–900 characters. A voice restoration would not stop `realize` / `established`. |

## G5 — Structured output

| | |
| --- | --- |
| PR-BS wording | Same envelope. Same declaration rule. Long narrative-plan essays, about 3,939 characters, explaining fields that are still shipped as JSON. |
| Current wording | Envelope unchanged. One compact narrative-plan instruction, 281 characters, plus a roles line. |
| Removed / retained | Field essays removed. The example object still shows a populated `declared_claims` array before `narration`, with `realize`, `authored_world_fact`, `established`, and `MUST_STATE` as the first alternatives. |
| P1 | Low for the miss. The model chose `propose` / `gm_inference`, which is the recipe, not the first schema alternative. |
| P2 | High as a standing attractor. Absolute schema size did not change. Its share of the prompt rose because the surrounding essays shrank. |
| P3 | Low. The model realized the two listed claims, which is what the schema’s first alternatives describe, and that was legal. |
| Behavioral importance | The schema is an amplifier for P2. It is not a PR-BS versus current text change. |
| Approximate cost | 0 if left alone. Changing the example to show an empty array would be a small schema edit, on the order of a few hundred characters, and would touch every turn. |

## G6 — Persistence

| | |
| --- | --- |
| PR-BS wording | No separate persistence essay in the removed instruction set. Full sidecar decisions carry `persistence_policy`: P1 `do_not_persist`, P2 `claim_only`, P3 `do_not_persist`. |
| Current wording | The provider `gm_resolution_decision` omits `persistence_policy`, `epistemic_acts`, and `narration_constraints` in both gates. |
| Removed / retained | Not removed. Never projected. |
| P1 | The accepted inference was stored `do_not_persist`. The model did not need a persistence lecture to choose `propose`. |
| P2 | The model requested `established`. The sidecar says NPC speech at this decision is `claim_only`. That word is not in the provider decision. |
| P3 | The model did not persist the hypothesis. |
| Behavioral importance | Medium for P2 if projected in one word. It is not a deleted PR-BS essay. |
| Approximate cost | One field, tens of characters, only if a later slice projects it. This discovery does not recommend a new persistence object. |

## G7 — Incidental improvisation

| | |
| --- | --- |
| PR-BS wording | Declaration rule, still present: “ordinary NPC dialogue, refusal, hesitation, and mannerism stay plain narration or incidental improvisation; they are not authored world facts.” Social essay: refusal stays conversational. Recipe line, unchanged: “Ordinary refusal, hesitation, mannerism, and phrasing may stay plain narration or a bounded incidental improvisation. That speech is not authored world truth.” |
| Current wording | The declaration-rule sentence and the recipe line are unchanged. System head now also says mundane dialogue “may be bounded incidental realization; unsupported durable facts require the structured lanes.” |
| Removed / retained | The conversational-refusal sentence inside the social essay is removed. The operative exception is retained. A new sentence tells the model that durable facts use the structured lanes. |
| P1 | Low. Sensory improvisation was incidental and not the rejecting sentence. |
| P2 | High as a salience problem. The exception survived. PR-BS obeyed it with `declared_claims: []`. All three compact samples disobeyed it and realized the reply. |
| P3 | Low. |
| Behavioral importance | The missing piece is not the deleted paragraph. The surviving exception loses to “realize with source_claim_id”. |
| Approximate cost | Restoring the 477-character social essay is about 120 tokens and would still sit beside the realize line. |

## G8 — Response completeness

| | |
| --- | --- |
| PR-BS wording | Direct-answer hard rule. “Best grounded partial answer.” NPC contract: the reply must include a person, place, faction, next step, or usable fact. Scene-momentum hard rule with a failure condition if the scene stays static. System investigate line: reveal new information, consequence, tension, or a narrowed decision. |
| Current wording | Rules 1, 6, 11, and 12 remain in the header. Scene momentum remains a hard instruction: every 2–3 exchanges introduce `new_information`, `new_actor_entering`, `environmental_change`, `time_pressure`, or `consequence_or_opportunity`. P1 narrative mode is `action_outcome` with outcome-forward weight 62 and `success_state: success`. NPC answer line: “Provide a concrete answer, partial specific, source, or usable next step when available.” |
| Removed / retained | The long completeness essays are removed. The header rules and the momentum obligation remain. |
| P1 | High as competing pressure. The model tagged `scene_momentum:consequence_or_opportunity` and completed “what does this suggest?” with a cause. P1’s question sentence is absent from `player_input`, so `player_direct_question` is false and the hedge machinery is off. That truncation is also true under the PR-BS policy object. |
| P2 | Medium. “Concrete answer” makes a loaf preference or a firm refusal feel like content that should be stored. |
| P3 | Low. Completeness here is “answer the fit question,” and the model answered by withholding. |
| Behavioral importance | This family pushes elaboration. Deleting more of it is not the next slice. The operation line has to outrank it. |
| Approximate cost | Already reduced. Putting it back would spend tokens to increase overreach. |

## What the differential does not justify

Restoring the narrative-plan essays or the policy-tail essays would spend thousands of tokens to repeat JSON that is still shipped. Restoring the known-edge essay would restate a sentence the current protocol already contains. The PR-BS P1 answer that scored Q3 was the same duration-or-recent-force story the current model wrote, plus a closer the old validator rewarded.

The guidance that is absent, in the slot the model treats as turn-local, is a single operation sentence that distinguishes a visible reading from a cause, and a social reply from a new established fact.

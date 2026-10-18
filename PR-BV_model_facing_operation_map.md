# PR-BV — Model-facing operation map

MODE: FORENSIC DISCOVERY. MODEL/API CALLS: ZERO.

Corpus: final repaired-chain gate, `artifacts/pr_bu_pr_bt_final_repaired_chain_micro_live/evidence/`.

The provider `gm_resolution_decision` is a reduced projection in both this gate and PR-BS. It contains `realization_claims`, empty `unresolved_qualifiers`, empty `answer_relations`, empty `permitted_state_mutations`, and `executable_obligations`. It does not contain `epistemic_acts`, `narration_constraints`, or `persistence_policy`. Those fields were reconstructed from the sidecar decision files. They were not in the model-facing payload.

Legend: **explicit**, **implicit**, **ambiguous**, **contradicted**, **drowned**.

## P1 — bounded interpretation

Player request, sidecar and recipe:

> I examine the split wooden yoke and the torn leather hanger closely. What does this damage suggest?

Model-facing `player_input`, `turn_summary.raw_player_input`, and `turn_packet.player_text` drop the question and keep only the examine clause. **Drowned** at the player-text slot. **Explicit** inside `decision_facing_answer_recipe.requested_answer`.

| Stage | What it says | Signal |
| --- | --- | --- |
| Contract, provider | `operation: inspect`, `dimension: interpretation`, `authority: unknown_allowed`, `expected_resolution: answer`. Constraint: the reply must be an answer, inability, refusal, condition, or clarification. | Operation name **explicit**. Interpretation ceiling **implicit**. |
| Contract, sidecar | Same, plus `epistemic_mode: unknown_allowed` and the full raw input. | Same. The extra fields are not a second authority. |
| Decision, sidecar | Establish the split yoke and the torn hanger. Infer act, authority `observation`, scope `qualified_possibilities_only`. Constraint: “Qualified possibilities may be inferred from authorized observations; no cause, actor, or history is established.” `persistence_policy: do_not_persist`. | Intended operation **explicit** in the sidecar. |
| Decision, provider | Two `MUST_STATE` observation claims only. No infer act. `unresolved_qualifiers: []`. | Infer permission **absent** here. Instruction text says the decision wins if it disagrees with the recipe. **Contradicted** relative to the sidecar, and **ambiguous** for a reader of the provider object alone. |
| Answer recipe | `permitted_inference.allowed: true`, modality `possible`, unresolved `cause, actor, time, history`. Strategy: “one qualified possibility… Use could, may, or might.” Bounded inference: `propose` / `gm_inference` / `inferred` / `possible`, not `authored_world_fact`. | Permission **explicit**. The shape of the possibility **ambiguous**: a reading of the damage, or a possible cause. Unresolved slots are a list, not an instruction to say them aloud. |
| Response policy | `player_direct_question: false`. Answer completeness off. `hedge_appropriately: false`. `uncertainty_active: false`. `require_partial_to_state_unknown_edge: false`. Required response type `action_outcome`. | Hedge path **contradicted** off, because the question was stripped before classification. Same policy object as PR-BS. |
| Narrative plan | Mode `action_outcome`. Weights: dialogue 8, exposition 20, outcome-forward 62, transition 10. Result `success_state: success`. Obligations: lead with the outcome, foreground state change. | Completeness **drowned** the ceiling. The model tagged `scene_momentum:consequence_or_opportunity`. |
| System prompt | `EPISTEMIC REALIZATION`: one possibility tied to the observations, and say cause, actor, time, and history stay unresolved. Do not add a mechanism, setting, maintenance history, or causal chain. | Intended operation **explicit**, then **drowned** by rule 1, rule 12, the scene-momentum hard rule, and the later recipe strategy. |
| Schema | `declared_claims` before `narration`. First alternatives: `realize`, `authored_world_fact`, `established`, `MUST_STATE`. `relation_kind` includes `causal` second. | The model did not take the first alternatives. It followed the recipe’s `propose` line. Schema pressure on P1 is **implicit** and was not the chosen path. |
| Model-selected operation | Declaration `inferred_damage_possibility_001`: `propose` / `gm_inference` / `inferred` / `possible`. Narration: “could suggest … possibly from years of use or a recent forceful event.” | Declaration matches O3. Narration is a causal story. |
| Validator | Declaration `hard_valid: true`, `accepted_bounded_declared_inference`, persistence `do_not_persist`. Narration `hard_valid: false`, `unauthorized_causal_relation`, `unsupported_narrator_lead`. | Correct reject of the narration. |

## P2 — ordinary baker question

Player request, present in `player_input` and in the recipe:

> Baker, which loaf do you usually keep for yourself?

| Stage | What it says | Signal |
| --- | --- | --- |
| Contract, provider | `operation: ask`, interlocutor baker, `unknown_allowed`, expected `answer`. Route in the gate record: `strict_social`. | Social answer **explicit**. |
| Decision, sidecar | Establish “A baker stands beside loaves” and “Baker exists”. No infer act. `persistence_policy: claim_only`. Constraints include “NPC claims remain claims”. | New world fact **implicitly** unavailable. `claim_only` is not in the provider decision. |
| Decision, provider | The two `MUST_STATE` claims only. | Realize-these-claims **explicit**. Speech ceiling **absent**. |
| Answer recipe | Strategy: “Have baker reply in ordinary dialogue: a direct answer, a refusal, a hesitation, or an admission that they do not know.” Incidental line: that speech “is not authored world truth.” Forbidden: `generated_dialogue_as_authored_world_fact` and `durable_preference_without_authorized_claim`. First declaration line: “realize with source_claim_id and the claim provenance”, because required claims exist. | Dialogue operation **explicit**. Declaration necessity **contradicted** by the realize line. |
| Response policy | Dialogue response type. `player_direct_question: true`. Answer completeness on. Hedge on. Unknown-edge requirement off. Narrative mode `dialogue`, dialogue weight 58. | Roleplay **explicit**. |
| System prompt | Declaration rule: refusal and ordinary dialogue stay plain narration and are not authored world facts. Next attractor: “unsupported durable facts require the structured lanes.” Envelope example is a filled claim. | Exception **explicit** and **drowned** by the envelope and by the recipe’s realize line. |
| Schema | Populated `declared_claims` is the illustrated shape. Empty array is not shown. `realize`, `authored_world_fact`, `established`, `MUST_STATE` are the first alternatives. | Overformalization **explicit** as an affordance. |
| Model-selected operation | Narration is a guarded spoken refusal. Declaration `rc_reply_refusal_1`: `realize`, `source_claim_id` null, `authored_world_fact`, `established`, text “The baker declines to reveal which loaf they keep for themselves.” | Speech is O2. Envelope is O5. |
| Validator | Declaration `hard_valid: false`, `unauthorized_declared_claim`. Narration validation not reached. | Correct reject. |

Compact-provider comparison, same recipe and schema:

| Sample | `source_claim_id` | Validator |
| --- | --- | --- |
| Raw PR-BT | `rc_2bb408577206` | Accepted. Speech stored as hearsay. |
| Selective restoration | `rc_2bb408577206` | Accepted. Speech stored as hearsay. |
| This gate | null | Rejected. |
| PR-BS | no declaration | Accepted. `declared_claims: []`. |

## P3 — player hypothesis

Player request, intact in `player_input` and in the recipe:

> Looking at the split wooden yoke and the torn leather hanger, maybe someone cut it deliberately. Does that fit what I'm seeing?

| Stage | What it says | Signal |
| --- | --- | --- |
| Contract | `operation: perceive`, subject chapel bell, `unknown_allowed`, expected `answer`. | Perception **explicit**. Hypothesis act **absent**. |
| Decision, sidecar | Establish the two observations only. No infer act. `persistence_policy: do_not_persist`. No narration sentence about qualified possibilities. | Observations **explicit**. Discuss-but-do-not-establish **absent** as an act. |
| Decision, provider | The two `MUST_STATE` claims. | Same reduction as P1, without an infer permission hiding in the recipe. |
| Answer recipe | Inference allowed false. Strategy: “Answer directly by realizing the required claims.” Epistemic premise: “No player hypothesis, NPC claim, or unresolved premise is authorized on this turn.” | Realize observations **explicit**. Hypothesis discussion **contradicted** by “not authorized,” which a strict reader could treat as “do not mention it.” |
| Response policy | Question detected. Answer required. Hedge on. Uncertainty active. `require_partial_to_state_unknown_edge: true`. Mode `exposition_answer`, exposition weight 66. | Unknown-edge **explicit**, because the full question survived in `player_input`. This is the opposite of P1. |
| System prompt | “A player hypothesis stays hypothetical: the visible facts may be compatible with it, and observation alone does not settle it.” | Discuss-without-establishing **explicit**. This is the sentence P1’s interpretation ceiling does not match in directness, because P1 still has to invent the content of the possibility. |
| Schema | Same envelope. The model used it for the two authorized observations only. | Affordance aligned with the legal claims. |
| Model-selected operation | Realized `rc_db5ec0aa65c3` and `rc_b31ecb1fd1c7`. Narration: damage is visible, and deliberate cutting “cannot be confirmed.” No actor, motive, tool, or time as fact. | O1 plus O4. |
| Validator | `hard_valid: true`, `initial_hard_valid`. Hypothesis later stored as `hypothesis` / `player_hypothesis`. | Correct accept. |

## Where the intended operation is clear

P3 is the only probe where the player text, the hedge flags, and one system sentence name the same act: discuss this supplied proposition without settling it.

P1’s ceiling is written in the system protocol and as an unresolved list in the recipe, and the turn is framed as a successful action outcome whose question was not detected.

P2’s dialogue act is written in the strategy, and the same recipe’s first declaration line plus the envelope example tell the model to realize a claim.

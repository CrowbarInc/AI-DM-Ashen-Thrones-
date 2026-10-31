# PR-BV — Turn-local realization operation projection

MODE: BOUNDED IMPLEMENTATION + DETERMINISTIC VALIDATION.

MODEL/API CALLS: ZERO.

NO LIVE GAMEPLAY. NO COMMIT. NO PUSH.

PR-BR: CLOSED. PR-BU: CLOSED. PR-BT: PAUSED / BT-C.

Decision: **A — OPERATION PROJECTION READY FOR MICRO LIVE.**

## A. Executive result

Compact operation projection was implemented on the existing Decision-Facing Answer Recipe.

The recipe now tells the model, from the current decision, what response to perform, whether a declaration is required, and how far the answer may go. The projection does not authorize new facts. P1 projects bounded interpretation. P2 projects incidental dialogue and says the reply itself is not a declaration. P3 projects conditional hypothesis discussion. A consequential control still requires a declaration. Generalization fixtures with different nouns produce the same labels.

Provider growth is 630 to 655 characters per probe. That is under the 1,000-character target. 94.06% to 95.02% of the pre-PR-BV reduction versus PR-BS is retained.

System prompt, response schema, validator, retry, and canonical decision construction were not edited.

## B. Design

Representation: one object, `turn_operation`, on `decision_facing_answer_recipe`.

```text
projection_only
authority_owner
response_operation
declaration_expectation
semantic_ceiling
instruction
```

The three labels are stable strings. `instruction` is the single model-facing sentence for the turn. `source_authority_fields` is computed for review and is not serialized to the provider.

Choice for the existing `answer_strategy`: **Approach C, with a small Approach A alignment.** The strategy remains the short summary. The structured fields carry the testable semantics. Where the old summary would compete with the new ceiling, the summary is extended or replaced from the projection. Details are in section L and in `PR-BV_operation_projection_derivation.md`.

No second answer policy, response-mode system, or authority object was added.

## C. Authority derivation

`project_turn_local_operation` reads only:

- `GMResolutionDecision` outcome, mutations, obligations, epistemic acts, and realization claims
- Resolution Contract operation, dimensions, interlocutor, and `raw_input`
- the existing `player_hypothesis_claims` classifier, already used when sealing temporal claims

First match wins: consequential realization, bounded interpretation, player-hypothesis discussion, refusal or limit, incidental dialogue, direct observation, listed-claim realization.

The classifier is not a probe-sentence table. It does not branch on baker, loaf, bell, damage, or deliberate cutting.

## D. Response operation

| Shape | Label |
| --- | --- |
| Infer act, scope `qualified_possibilities_only` | `bounded_interpretation` |
| Interlocutor, and no earlier row | `incidental_dialogue` |
| Player hypothesis in a claim or in contract text, and no earlier row | `player_hypothesis_discussion` |
| Authorized mutation or `state_mutation` / `authorized_state_outcome` | `consequential_realization` |
| `perceive` or `inspect` without an interpretation dimension, and no earlier row | `direct_observation` |
| Unresolved, nonresolution, or protected outcome, and no earlier row | `refusal_or_limit` |
| Otherwise | `listed_claim_realization` |

A contract dimension of `interpretation` does not by itself grant an inference. The infer act does.

## E. Declaration expectation

| Label | Meaning on this turn |
| --- | --- |
| `optional_bounded_inference` | No new declaration is required for the observations. A bounded inference may be proposed, or left in narration. |
| `reply_not_required` | The spoken reply is narration. Listed claims may still be restated. |
| `hypothesis_discussion_not_required` | Discussing the hypothesis needs no declaration. |
| `required_for_authorized_realization` | Declare the authorized consequential claims. |
| `observations_only` | Realize the listed observations only. |
| `declaration_prohibited` | Do not declare the requested consequence. |
| `listed_claims_only` / `no_additional_declaration` | Realize listed claims, or add none. |

## F. Semantic ceiling

| Label | Ceiling |
| --- | --- |
| `interpret_observations_not_unauthorized_cause` | Interpret the observations. Do not explain an unauthorized cause, actor, time, or history. |
| `transient_dialogue_not_durable_fact` | Transient speech only. No durable preference or history merely to answer. |
| `conditional_hypothesis_not_established` | Discuss fit conditionally. Do not establish the hypothesis, actor, motive, tool, or timing. |
| `authorized_consequential_state_only` | Establish only the authorized state. |
| `direct_observations_only` | State what is authorized to be seen. Do not infer. |
| `state_the_limit_do_not_realize` | State the limit. |
| `listed_claims_only` | Do not add a consequential fact. |

## G. P1 projection

Live decision `artifacts/pr_bu_pr_bt_final_repaired_chain_micro_live/evidence/P1`.

- `response_operation`: `bounded_interpretation`
- `declaration_expectation`: `optional_bounded_inference`
- `semantic_ceiling`: `interpret_observations_not_unauthorized_cause`
- Sources: `gm_resolution_decision.epistemic_acts`, `epistemic_acts.semantic_identity.scope`

Instruction:

> Interpret what the listed observations may indicate. Do not explain an unauthorized cause, actor, time, or history. A bounded inference may be proposed as gm_inference, inferred, possible, or left in narration. Do not declare a new world fact merely to answer.

The strategy still says to use could, may, or might, and now adds the same cause ceiling. The projection does not authorize years of use, a recent forceful event, neglect, a maintenance history, weather, a mechanism, an actor, or a time.

## H. P2 projection

Live decision in the same evidence tree, probe P2.

- `response_operation`: `incidental_dialogue`
- `declaration_expectation`: `reply_not_required`
- `semantic_ceiling`: `transient_dialogue_not_durable_fact`
- Sources: `resolution_contract.interlocutor_id`, `epistemic_acts`, `permitted_state_mutations`

Instruction:

> On this turn, reply in ordinary narration: answer, hesitate, deflect, joke, or refuse. The reply itself belongs in narration. Do not declare that reply as a world fact. Do not establish a durable preference or history merely to answer. Listed claims may still be realized if restated.

`consequential_authorized_claim` now says the turn-local reply is narration, not a new authored world fact. The bare line "realize with source_claim_id and the claim provenance" is absent on this recipe. Incidental refusal, hesitation, mannerism, and phrasing guidance is unchanged.

## I. P3 projection

Live decision, probe P3.

- `response_operation`: `player_hypothesis_discussion`
- `declaration_expectation`: `hypothesis_discussion_not_required`
- `semantic_ceiling`: `conditional_hypothesis_not_established`
- Source: `resolution_contract.raw_input`, through the existing hypothesis classifier

Instruction:

> Discuss whether the player's hypothesis fits the listed observations, conditionally. Do not establish the hypothesis, an actor, a motive, a tool, or timing. No declaration is needed merely to discuss it. Realize only claims already listed.

`permitted_inference.allowed` remains false. The strategy still tells the model to realize the listed claims, and now says not to establish the hypothesis. The epistemic premise says the hypothesis may be discussed conditionally and is not world truth.

## J. Consequential control

Fixture `G4_consequential_control`: `outcome_classification = state_mutation`, a `permitted_state_mutations` row, a realization claim sourced from `resolution.state_changes.gate`, and an interlocutor.

- `response_operation`: `consequential_realization`
- `declaration_expectation`: `required_for_authorized_realization`
- `semantic_ceiling`: `authorized_consequential_state_only`

The instruction says to declare the authorized claims. The same labels are produced when the interlocutor is removed. P2's `reply_not_required` does not apply to this decision. The anti-declaration wording is turn-local.

## K. Generalization controls

| Fixture | Shape | Operation | Declaration | Ceiling | Same labels as |
| --- | --- | --- | --- | --- | --- |
| G1 | Ordinary NPC question, different interlocutor and nouns | `incidental_dialogue` | `reply_not_required` | `transient_dialogue_not_durable_fact` | P2 |
| G2 | Qualified infer, different subject, no hypothesis marker | `bounded_interpretation` | `optional_bounded_inference` | `interpret_observations_not_unauthorized_cause` | P1 |
| G3 | Hypothesis in contract text, different wording | `player_hypothesis_discussion` | `hypothesis_discussion_not_required` | `conditional_hypothesis_not_established` | P3 |
| G3 claim | Hypothesis stored as `player_hypothesis` / `MAY_INFER` | same three labels | | | P3 |
| G4 | Authorized state mutation | `consequential_realization` | `required_for_authorized_realization` | `authorized_consequential_state_only` | control |
| G5 | `perceive` / `appearance`, no infer, no hypothesis | `direct_observation` | `observations_only` | `direct_observations_only` | G5 pair |

Claim order and interlocutor name do not change `turn_operation` when the decision shape is the same. A `consequentially_unresolved` act with no mutation projects `refusal_or_limit` / `declaration_prohibited`.

All eight matrix rows have `matches_expected: true`.

## L. Existing answer strategy

Kept. It is still the short summary.

Aligned from the projection:

- P1 appends the unauthorized-cause ceiling to the qualified-possibility sentence.
- P3 replaces "Answer directly by realizing the required claims" with a sentence that still realizes the listed claims and discusses the hypothesis conditionally.
- A decision that already says "existing status" keeps that phrase and adds the conditional ceiling.
- P2's dialogue sentence is unchanged, including refusal and hesitation.
- Consequential, direct-observation, and refusal summaries are rewritten so they cannot be hidden by a dialogue or "realize the claims" sentence.

`could, may, or might`, ordinary dialogue, refusal, hesitation, and "existing status" remain where those tests require them.

## M. Provider rendering

`narration_authority_fields` already calls `build_decision_facing_answer_recipe` and places the recipe on the user message. No response-policy change was required.

Serialized position: `decision_facing_answer_recipe.turn_operation`, immediately after `authority_owner` and before `requested_answer`.

Exact excerpts: `PR-BV_operation_projection_snapshots.md`.

Reconstructed provider requests: `artifacts/pr_bv_operation_projection/evidence/P1|P2|P3/provider_request_generation_1.json`.

`turn_operation` character counts inside the recipe JSON: P1 523, P2 526, P3 509.

## N. Contradiction analysis

Checked on the serialized P1, P2, and P3 recipes.

No recipe contains "provide the most likely cause" or "declare this as established world fact."

P1 contains both "realize with source_claim_id and the claim provenance" and "Do not declare a new world fact merely to answer." Those address different objects. The realize line still covers the two listed observation claims. The instruction forbids a new causal world fact and an unauthorized cause. The realize line was left in place so the authorized observations are not discouraged. The strategy now states the cause ceiling in the same sentence as the qualified possibility.

P2 no longer contains the bare realize line. The replacement says listed claims may be realized and the reply is not a new authored world fact. The instruction says the reply belongs in narration. Incidental-improvisation text still says that speech is not authored world truth. Those agree.

P3 no longer says that no player hypothesis is authorized on the turn. It says the hypothesis may be discussed conditionally and is not world truth, and the instruction says not to establish it. Inference remains not permitted. That removes the reading "do not mention the hypothesis" without promoting it.

## O. Provider-size impact

Baseline is the selective-restoration reconstruction, which the discovery recorded as the pre-PR-BV payload. Method: `game.gm.build_messages` on the saved PR-BS isolated probe state. No model call.

| Probe | Provider before | Provider after | Net | Recipe before | Recipe after | `turn_operation` chars |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| P1 | 97,812 | 98,442 | +630 | 2,356 | 2,962 | 523 |
| P2 | 110,405 | 111,060 | +655 | 1,876 | 2,507 | 526 |
| P3 | 99,752 | 100,389 | +637 | 1,691 | 2,304 | 509 |

Recipe growth above the new object is the aligned strategy or declaration line: P1 +83, P2 +105, P3 +104. Provider growth is 24 characters above recipe growth on every probe because the recipe is embedded in the user-message JSON string.

System prompt remains 9,564 characters.

## P. PR-BT savings retained

PR-BS totals: P1 110,450, P2 121,438, P3 110,665.

| Probe | Still removed vs PR-BS | Prior reduction | Percent of that reduction retained |
| --- | ---: | ---: | ---: |
| P1 | 12,008 | 12,638 | 95.02% |
| P2 | 10,378 | 11,033 | 94.06% |
| P3 | 10,276 | 10,913 | 94.16% |

The large majority of the PR-BT reduction is retained. No PR-BS essay was restored.

## Q. Request-classification debt

Deferred, and still present.

P1's model-facing player text drops "What does this damage suggest?" The full question remains in the contract and in `requested_answer`. P3's full question stays in player text. This cycle did not change response policy. The PR-BT checks that still compare `response_policy.narrative_authority` and `response_policy.uncertainty` to the live payloads passed.

If a later micro-live P1 is still weak after this projection, the stripped question and the resulting hedge flags are the next suspect. They were not repaired here, so a behavior change on the micro-live can be attributed to the operation projection.

## R. Focused tests

`tests/test_pr_bv_turn_local_operation_projection.py`

**10 passed, 0 failed.**

Covered: P1, P2, P3, consequential control with and without an interlocutor, G1, G2, G3 text, G3 claim, G5, refusal, projection does not exceed the decision, contradiction pairs, validator independence, and presence on `narration_authority_fields`.

## S. Broader regression

**271 passed, 1 failed, 0 errors, 0 skipped. 272 tests.**

JUnit: `artifacts/pr_bv_operation_projection/regression.xml`.

| Module | Result |
| --- | --- |
| PR-BV operation projection | 10 passed |
| PR-BS answer recipe | 9 passed |
| PR-BT selective guidance | 3 passed |
| PR-BT provider deduplication | 2 passed, 1 failed |
| PR-BU narration composition | 62 passed |
| PR-BU lexical scope | 28 passed |
| PR-BR authority reconciliation | 11 passed |
| PR-BR claim control slices 1 and 2 | 16 passed |
| PR-BR structured realization | 11 passed |
| PR-BR structured chat path | 11 passed |
| PR-BR decision-owned claims | 8 passed |
| PR-BR GM resolution decision | 9 passed |
| PR-BR continuation 18 | 21 passed |
| PR-BR incidental entity | 14 passed |
| Prompt and guard | 56 passed |

The failure is the known obsolete assertion `test_pr_bt_provider_requests_remove_at_least_12000_chars_each`. P2 is `121438 - 111060 = 10378`. It was already red before this cycle at `121438 - 110405 = 11033`. The assertion was not changed. Product code was not edited to satisfy it.

## T. C18

**PASS. ACCEPTED == SEALED == EMITTED.**

`tests/test_pr_br_structured_chat_path.py::test_raw_chat_accepts_authorized_fact_and_seals_it` passed.

`tests/test_pr_br_continuation18_immutable_boundary.py`: 21 passed.

`tests/test_pr_br_structured_chat_path.py`: 11 passed.

This cycle does not edit that path.

## U. Prompt

UNCHANGED.

System prompt in the reconstruction is 9,564 characters, the same figure as the selective-restoration measurement. The PR-BT assertion that the system-prompt delta versus the optimized prompt is `651 -` the replaced sentence passed.

## V. Schema

UNCHANGED.

No edit to the realization envelope. The PR-BT guidance tests still require the envelope language in the system prompt, and they passed.

## W. Validator

UNCHANGED.

No validator function reads `turn_operation`. The new test checks the narration and envelope auditor sources and the envelope signature.

## X. Retry

UNCHANGED.

`retry_authority_context` was not edited. It still does not attach a second recipe.

## Y. Authority

UNCHANGED.

`_decision_from_contract` and `build_gm_resolution_decision` were not edited. The new function only reads the decision and the contract. `projection_only` stays true. `authority_owner` stays `gm_resolution_decision`.

## Z. Micro-live readiness

**Ready for a three-probe PR-BV micro-live. Not run in this cycle.**

The deterministic gate holds: the three projections match the required operations, the consequential control still demands a declaration, generalization matches on decision shape, authority is unchanged, provider growth is a few hundred characters, the PR-BT savings majority remains, regressions are green apart from the known size assertion, and C18 holds.

The live question, when that gate is run, is whether this turn-local projection changes first-pass behavior on the same P1, P2, and P3 wording. Do not treat this report as that result.

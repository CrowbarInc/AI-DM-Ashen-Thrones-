# PR-BV — Operation projection derivation

MODE: DETERMINISTIC. MODEL/API CALLS: ZERO.

The projection is not a new authority. `GMResolutionDecision` and the Resolution Contract remain canonical. `project_turn_local_operation` reads those objects, plus the existing `player_hypothesis_claims` classifier, and emits labels. The validator does not read the result.

## What is canonical, derived, and rendered

| Layer | What it is | Where it lives |
| --- | --- | --- |
| Canonical | Decision outcome, mutations, epistemic acts, realization claims, contract operation, dimensions, interlocutor, raw input | `GMResolutionDecision`, Resolution Contract |
| Derived | `response_operation`, `declaration_expectation`, `semantic_ceiling`, and `source_authority_fields` | `project_turn_local_operation` |
| Prose rendering | `turn_operation.instruction`, and the small alignments of `answer_strategy` and two declaration lines | `decision_facing_answer_recipe` |

`source_authority_fields` is returned for tests and for `PR-BV_operation_projection_matrix.json`. It is stripped before the recipe is serialized. The provider object is `turn_operation` with `projection_only`, `authority_owner`, the three labels, and `instruction`.

Recipe root metadata stays `projection_only: true` and `authority_owner: "gm_resolution_decision"`. The same pair is repeated inside `turn_operation` so the block is self-describing.

## Priority

The first match wins. Later rows are not consulted.

1. Consequential realization.
2. Bounded interpretation.
3. Player-hypothesis discussion.
4. Refusal or limit.
5. Incidental dialogue.
6. Direct observation.
7. Listed-claim realization.

No branch reads a scenario name, a probe id, or a fixed player sentence.

## Response operation

### Consequential realization

Canonical input: `permitted_state_mutations` is non-empty, or `outcome_classification` is `state_mutation` or `authorized_state_outcome`, or `executable_obligations.mutation_owner` is set, or a realization claim `source_ref` starts with `resolution.permitted_state_mutations` or `resolution.state_changes`.

Derivation: any one of those is explicit authorization to create consequential state. Retrieved observations (`scene.visible_facts`, `world.npcs`) do not match.

Projected field: `response_operation = consequential_realization`.

Rendering: `Realize the consequential state this decision authorizes. Declare those authorized claims with source_claim_id and their provenance. Do not add a further cause, actor, or history.`

An interlocutor on the same turn does not change this result. That is the control that keeps P2's "no declaration" turn-local.

### Bounded interpretation

Canonical input: an epistemic act whose `act` is `infer` and whose `semantic_identity.scope` is `qualified_possibilities_only`.

Derivation: that act is the existing qualified-possibility permission. A contract dimension of `interpretation` is not sufficient by itself. If it is present without the act, the projection does not grant an inference.

Projected field: `response_operation = bounded_interpretation`.

Rendering: `Interpret what the listed observations may indicate. Do not explain an unauthorized cause, actor, time, or history. A bounded inference may be proposed as gm_inference, inferred, possible, or left in narration. Do not declare a new world fact merely to answer.`

If a player hypothesis is also present, the same operation is kept and the instruction gains one sentence: do not establish that hypothesis as fact. P1 does not have a hypothesis, so its instruction stays the base sentence.

### Player-hypothesis discussion

Canonical input: a realization claim or proposed fact with `provenance = player_hypothesis`, or `player_hypothesis_claims(resolution_contract.raw_input)` returning a row.

Derivation: `player_hypothesis_claims` is the classifier already used when sealing temporal claims. This cycle calls it only to choose the operation. It does not append a claim, a provenance, or a permission to establish the hypothesis.

Projected field: `response_operation = player_hypothesis_discussion`.

Rendering: `Discuss whether the player's hypothesis fits the listed observations, conditionally. Do not establish the hypothesis, an actor, a motive, a tool, or timing. No declaration is needed merely to discuss it. Realize only claims already listed.`

This row is reached only when consequential realization and qualified inference did not match. P3's live decision has no hypothesis claim. Its contract `raw_input` does, and the existing classifier matches it. G3, which uses different wording and the same classifier, gets the same three labels.

### Refusal or limit

Canonical input: `outcome_classification` in `safe_nonresolution`, `consequentially_unresolved`, or `consequential_protected`, and none of the earlier rows matched.

Projected field: `response_operation = refusal_or_limit`.

Rendering: `State the limit. The requested consequence is not authorized. Do not declare it as established.`

### Incidental dialogue

Canonical input: `interlocutor_id` or `interlocutor` is non-empty, and none of the earlier rows matched. Empty `permitted_state_mutations` and the absence of a qualified infer act are what keep this row available. Those fields are recorded as sources because their absence is part of the selection.

Projected field: `response_operation = incidental_dialogue`.

Rendering: `On this turn, reply in ordinary narration: answer, hesitate, deflect, joke, or refuse. The reply itself belongs in narration. Do not declare that reply as a world fact. Do not establish a durable preference or history merely to answer. Listed claims may still be realized if restated.`

The sentence is scoped with "on this turn." It does not say that NPC dialogue never needs a declaration.

### Direct observation

Canonical input: contract `operation` is `perceive` or `inspect`, and `dimensions` do not include `interpretation`, `source`, `confidence`, `cause`, `actor`, `time`, or `history`, and none of the earlier rows matched.

Projected field: `response_operation = direct_observation`.

Rendering: `State the authorized observations. Do not add an inference, a cause, or a new world fact. Realize only the listed observation claims.`

### Listed-claim realization

Canonical input: the realization-claim list, when no earlier row matched.

Projected field: `response_operation = listed_claim_realization`.

Rendering: `Realize only claims this decision already lists. Do not add a new consequential fact.`

## Declaration expectation

The declaration label is paired with the operation. It does not add a claim.

| Operation | Label | What the instruction tells the model |
| --- | --- | --- |
| Bounded interpretation | `optional_bounded_inference` | Observations do not need a new declaration. A bounded inference may be proposed as `gm_inference` / `inferred` / `possible`, or left in narration. Do not declare a new world fact merely to answer. |
| Incidental dialogue | `reply_not_required` | The turn-local reply stays narration. Listed claims may still be restated with `source_claim_id`. |
| Player-hypothesis discussion | `hypothesis_discussion_not_required` | Discussing the hypothesis needs no declaration. Only claims already listed may be realized. |
| Consequential realization | `required_for_authorized_realization` | Declare the authorized consequential claims with `source_claim_id` and their provenance. |
| Direct observation | `observations_only` | Realize the listed observations. Do not add an inference declaration. |
| Refusal or limit | `declaration_prohibited` | Do not declare the requested consequence as established. |
| Listed claims, some present | `listed_claims_only` | Realize those claims. Do not add one. |
| Listed claims, none present | `no_additional_declaration` | No additional consequential claim is authorized. |

## Semantic ceiling

| Operation | Label | Ceiling the instruction states |
| --- | --- | --- |
| Bounded interpretation | `interpret_observations_not_unauthorized_cause` | Say what the listed observations may indicate. Do not explain an unauthorized cause, actor, time, or history. |
| Incidental dialogue | `transient_dialogue_not_durable_fact` | Answer, hesitate, deflect, joke, or refuse. Do not establish a durable preference or history merely to answer. |
| Player-hypothesis discussion | `conditional_hypothesis_not_established` | Discuss fit conditionally. Do not establish the hypothesis, an actor, a motive, a tool, or timing. |
| Consequential realization | `authorized_consequential_state_only` | Establish only the state this decision authorizes. Do not add a further cause, actor, or history. |
| Direct observation | `direct_observations_only` | State the observations. Do not add an inference, a cause, or a new world fact. |
| Refusal or limit | `state_the_limit_do_not_realize` | State the limit. Do not realize the request. |
| Listed claims | `listed_claims_only` | Do not add a new consequential fact. |

The ceiling names prohibited slots. It does not supply years of use, a forceful event, neglect, a maintenance history, weather, a mechanism, an actor, or a time.

## Answer-strategy alignment

`answer_strategy` stays the short summary. It is aligned only where the old sentence would compete with the projection.

- Bounded interpretation keeps "could, may, or might" and gains "Do not explain an unauthorized cause, actor, time, or history."
- A hypothesis turn that already says "existing status" keeps that sentence and gains the conditional ceiling.
- A hypothesis turn that would otherwise say only "realize the required claims" becomes "Realize the listed claims. Discuss the player's hypothesis conditionally. Do not establish it."
- Incidental dialogue keeps the ordinary-dialogue sentence, including refusal and hesitation.
- Consequential realization, direct observation, and refusal replace the summary with the operation sentence so a dialogue summary cannot hide an authorized mutation or a limit.

## Two rendering repairs

These stay inside the recipe. They do not change the decision.

P2. `declaration_guidance.consequential_authorized_claim` no longer says only "realize with source_claim_id and the claim provenance" when the operation is incidental dialogue. It now says listed claims may be realized, and the turn-local reply is narration, not a new authored world fact. The old bare line is what the compact model attached the reply to.

P3. When the hypothesis is in the contract text and the decision has no epistemic claim, `epistemic_premise` no longer says "No player hypothesis ... is authorized on this turn." It says the hypothesis may be discussed conditionally and is not world truth. The old sentence could be read as "do not mention it." When the decision already carries a `player_hypothesis` claim, the existing "do not promote ... into world truth" sentence is left in place.

P1's realize line is unchanged. It still applies to the listed observation claims. The new instruction says a new world fact is not required and an unauthorized cause is forbidden. Those two sentences address different objects.

## Validator

`audit_realization_envelope_against_decision` and `audit_narration_against_decision` do not mention `turn_operation`, `project_turn_local_operation`, or `decision_facing_answer_recipe`. The envelope auditor's signature does not take the recipe. `tests/test_pr_bv_turn_local_operation_projection.py::test_validator_does_not_consume_the_projection` checks both sources and the signature.

The provider receives the projection because `narration_authority_fields` already embeds `build_decision_facing_answer_recipe` on the user message. No response-policy or schema edit was required for that path.

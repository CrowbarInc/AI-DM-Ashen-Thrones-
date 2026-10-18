# PR-BT Policy / Instruction Semantic Diff

## Scope

This diff covers only provider-facing policy/instruction deduplication. It does not change validators, authority ownership, `response_policy` construction, `turn_packet` construction, schema shape, retry logic, or accepted-response handling.

## Rule Family: Core Authority And Realization Scope

### Before

Authority was stated in `SYSTEM_PROMPT`, repeated across generic instructions, represented in `gm_resolution_decision`, and operationalized again by `decision_facing_answer_recipe`.

### After

The system prompt keeps the stable rule: app state/mechanics are authoritative; the model realizes only the supplied turn. The provider still receives `gm_resolution_decision`, `resolution_contract`, `declared_claims` schema, `response_policy.narrative_authority`, and `decision_facing_answer_recipe`.

### Canonical Owner

Runtime authority remains in `GMResolutionDecision`, `ResolutionContract`, validators, and accepted-response gates.

### Risk

Low. The removed prose duplicated surviving provider objects and validator-owned runtime rules.

## Rule Family: Answer Completeness / Response Delta / Uncertainty

### Before

The instruction list carried long prose explaining `response_policy.answer_completeness`, `response_policy.response_delta`, `response_policy.uncertainty`, direct-question shape, NPC answer shape, and grounded partial answers.

### After

One compact `ANSWER POLICY` line points to the shipped policy objects. One compact question/uncertainty line preserves the operational rule to answer first and ground uncertainty. The PR-BS recipe remains intact and turn-specific.

### Canonical Owner

`response_policy.answer_completeness`, `response_policy.response_delta`, `response_policy.uncertainty`, `fallback_behavior`, deterministic enforcement, and the decision-facing recipe.

### Risk

Low-medium. The model loses repeated examples but retains the policy object, recipe, and short operational instruction.

## Rule Family: Narrative Plan Guidance

### Before

`_NARRATIVE_PLAN_STRUCT_GUIDANCE` explained nearly every major `narrative_plan` field in prose, while the same structured fields were already shipped and `NARRATIVE MODE` deltas were generated separately.

### After

A single `NARRATIVE PLAN` instruction states precedence and bounded use. The structured `narrative_plan` and compact mode-delta lines remain provider-visible.

### Canonical Owner

`narrative_plan` construction/validation, CTIR when attached, `response_policy`, narration visibility, and mode-contract deltas.

### Risk

Low-medium. Removed text explained fields already visible in the machine-readable plan; precedence remains explicit.

## Rule Family: Policy Tail

### Before

Large paragraphs restated tone escalation, narrative authority, fallback behavior, anti-railroading, context separation, narration purity, scene anchoring, social response structure, and narrative authenticity.

### After

One compact `POLICY BRIDGE` names the same shipped policy children and preserves the critical behavior: local intent primary, uncertainty qualified, player agency/hypotheses preserved, internal language suppressed, and recipe/policy prose non-authoritative. A short social-response line is added only when the social-response structure contract is enabled.

### Canonical Owner

The response-policy object and downstream validators remain canonical.

### Risk

Low. This is the clearest demonstrated duplication family: prose about policy was removed while the policy object itself remains.

## Rule Family: Output Contract / Declaration Lane

### Before

System prompt contained the full realization envelope plus declaration and bounded-improvisation rules. Some generic instructions also restated answer/narration shape.

### After

The JSON envelope, `declared_claims` rules, and bounded-improvisation authority remain in the system prompt. Generic duplicate answer/narration prose was compacted.

### Canonical Owner

Schema expectations in `SYSTEM_PROMPT`, structured-output parsing/validation, declaration validation, narration validation, and accepted-response sealing.

### Risk

Low. The explicit envelope was preserved.

## Rule Family: Player Hypotheses And NPC Improvisation

### Before

System/instruction prose and declaration rules both warned against turning hypotheses, NPC claims, or incidental details into authored truth.

### After

The system prompt keeps the short operational rule, and the structured claim/improvisation schema remains explicit.

### Canonical Owner

`RealizationClaim` authority, temporal provenance, bounded improvisation handling, NPC claim/improvisation proposals, and validators.

### Risk

Low. The surviving representation is more direct and remains paired with the schema.

# PR-BW Structured Realization Envelope Competence Discovery

## A. Executive Finding

The current universal structured realization envelope is materially contributing to first-pass failures, but in two different ways. P2 is the cleanest structural signal: the model already generated playable ordinary dialogue, yet manufactured an unauthorized `realize` / `authored_world_fact` / `established` declaration despite `reply_not_required`. P1 is a separate but related binding failure: the model selected an acceptable bounded inference, then narration added a temporal/history implication (`over time`) not present in the declaration.

Decision taxonomy: **A - MODE-SPECIFIC GENERATION ENVELOPE RECOMMENDED**.

Smallest next implementation slice: deterministically select a narration-only provider envelope for `reply_not_required` / transient dialogue turns using existing GMResolutionDecision plus turn_operation semantics. Keep the validator as backstop. Do not start with more prose wording.

## B. Current Envelope Architecture

Current flow is:

`GMResolutionDecision -> Decision-Facing Answer Recipe / turn_operation -> provider prompt with universal envelope -> model declarations + narration -> declaration validation -> narration validation -> acceptance/retry -> commit -> emission`.

GMResolutionDecision is canonical authority. The recipe is projection only. The model receives both canonical authority and rich structured authorship machinery every turn.

## C. Provider-Visible Schema

Preserved provider requests contain only `provider_input`; no separate `response_format`, `json_schema`, or strict provider schema is saved. The provider-visible schema is the JSON example in the system prompt.

`declared_claims` appears first and exposes modes, provenance, epistemic status, modality, realization role, relation kind, premise links, and claim text. `narration` is represented as a simple string.

## D. Declaration Affordance

Yes, the schema can encourage unnecessary authorship. It exposes rich declaration operations even when the turn recipe says no declaration is required. `realize`, `authored_world_fact`, and `established` are especially attractive/default-looking for making prose concrete.

## E. Empty-Declaration Behavior

Empty declarations are valid and observed. PR-BV accepted `declared_claims: []` for P1 retry, P2 retry, and P3 initial. Repaired pre-PR-BV also accepted empty declarations on P1/P2 retries. PR-BS P2 succeeded first pass with `declared_claims: []`.

The affordance problem is not runtime impossibility; it is provider-visible normality. The main schema example shows a populated declaration object, not `declared_claims: []` as the ordinary shape for narration-only turns.

## F. P2 Forensic Reconstruction

P2 recipe explicitly said `incidental_dialogue`, `reply_not_required`, and `transient_dialogue_not_durable_fact`. It instructed: reply in ordinary narration; the reply belongs in narration; do not declare that reply as a world fact; do not establish durable preference or history.

The model still declared:

> The baker does not disclose which loaf they keep for themselves.

with `declaration_mode: realize`, `provenance_requested: authored_world_fact`, `epistemic_status: established`, `modality: established`, and `realization_role: MUST_STATE`.

This was rejected as `unauthorized_declared_claim`.

## G. P2 Counterfactual

Probably yes: if P2 had no consequential declaration capability exposed, the already-generated initial narration would likely have been valid/playable. The line was ordinary NPC refusal/deflection. Its failure was structured overauthorship, not lack of player-facing response.

## H. P2 Salvageability

S1 - structurally salvageable. Removing or preventing the invalid declaration was the important repair. Retry mainly discovered `declared_claims: []`, at a cost of 26,142 extra input tokens.

## I. P1 Forensic Reconstruction

P1 decision authorized the two visible bell facts and permitted qualified observation-level inference. It explicitly did not establish cause, actor, time, or history.

The model declaration was accepted:

> The split wooden yoke and torn leather hanger could indicate strain or wear on the bell's supports.

The narration expanded it:

> This damage could suggest that the bell has been subjected to strain or wear on its supports over time.

## J. P1 Semantic Delta

Declaration selected possible strain/wear on supports. Narration added temporal/history content: `over time`. That is not a style-only paraphrase; it introduces duration/history and a stronger sense of gradual process.

## K. P1 Counterfactual

Probably yes: if narration had been bound to the semantic ceiling of its own accepted declaration, the initial response could have been valid and useful. The semantic core was good; the defect was the small prose expansion.

## L. P1 Salvageability

S2 - narratively salvageable. Structured semantics were valid; narration needed to avoid the extra history/duration phrase.

## M. P3 Positive Control

P3 succeeded under the same universal envelope. It emitted `declared_claims: []`, stated the visible damage, and conditionally discussed the player's deliberate-cut hypothesis without establishing actor, motive, tool, or timing. P3 shows the envelope can work when the model recognizes the no-declaration pattern and keeps hypothesis discussion conditional.

## N. Double-Reasoning Hypothesis

Partially supported. Evidence for: P1 declaration was valid, but narration re-expressed it with new temporal content. Instructions also ask the model to answer naturally from the full turn context, so narration can behave like a second semantic inference pass. Evidence against: P3 shows narration can remain aligned, and the validator already enforces many ceiling rules. Classification: partially supported.

## O. Declaration-To-Narration Contract

There is an invariant in prompt and validator form: narration must correspond to declared and accepted consequential claims, and validation rejects undeclared consequential content. It is model-facing and validator-facing, but first-pass behavior still violates it. It is enforceable after the call, not reliably preventative.

## P. Universal-Schema Hypothesis

Supported for P2. A universal schema exposes consequential authorship on a turn where existing authority and recipe already know the reply is transient dialogue. The model used the exposed machinery despite direct no-declaration guidance.

Partially supported for P1. P1 needed optional bounded inference, so the issue is less "no schema" and more semantic binding between selected inference and narration.

## Q. Provider Translation

No provider schema distortion was found. The preserved request does not show strict JSON schema mode, provider defaults, or provider-side optionality changes. The issue is prompt-visible schema/affordance, not a hidden provider translation artifact.

## R. Field Order/Salience

Declarations appear before narration. Measured in PR-BV P2, the system prompt has about 847 chars of declaration schema versus 25 chars for the narration field, plus 1,251 chars of structured-claim rule. This favors declaration-first reasoning and makes "do nothing structured" a small option surrounded by authorship vocabulary.

## S. P1 Request-Classification Confound

Not material to the core P1 defect. Even with perfect request classification, the accepted declaration-to-invalid-narration drift would remain a real defect.

## T. Root-Cause Taxonomy

P1 primary: C - declaration/narration semantic decoupling. Secondary: D - salience imbalance; F - residual stochasticity.

P2 primary: A - universal-schema affordance. Secondary: B - required-field/completion pressure; D - field-description/salience imbalance.

No evidence requires G - authority representation gap. Existing authority contains enough information to know P2 is narration-only and P1 is bounded interpretation.

## U. Candidate Strategies

1. Deterministic mode-specific envelope. Existing authority chooses a smaller provider envelope: narration-only for transient dialogue; bounded-inference envelope for P1-like interpretation; fuller consequential envelope only when needed.
2. Declaration-to-narration semantic binding. Keep one call but make narration explicitly preserve accepted/proposed structured semantics plus incidental expression, with no consequential/epistemic increase.
3. Status quo plus clearer affordance. Keep universal schema but make `declared_claims: []` prominent and reduce declaration salience for narration-only turns.

## V. Candidate Comparison

| Candidate | P1 benefit | P2 benefit | P3 risk | Improv/dialogue risk | Impact | Token/call cost |
| --- | --- | --- | --- | --- | --- | --- |
| Mode-specific envelope | Medium | High | Low-medium | Low if narration-only keeps dialogue freedom | Medium | One call; likely prompt shrink |
| Semantic binding | High | Medium | Low | Medium if over-tightened | Low-medium | One call; small prompt growth |
| Clearer affordance only | Low-medium | Medium | Low | Low | Low | One call; small prompt growth |

## W. Recommended Smallest Implementation Slice

Implement the P2-first slice: deterministic narration-only envelope for `incidental_dialogue` / `reply_not_required` / `transient_dialogue_not_durable_fact` turns. Source the selection from existing GMResolutionDecision and turn_operation. Do not let the model choose its own envelope.

This has the strongest evidence, largest clean retry-reduction target, and lowest semantic risk. It preserves ordinary NPC dialogue and removes unnecessary declaration machinery from turns where authority already says no declaration is needed.

## X. Expected Effect On Retries

In the PR-BV gate, this could plausibly remove the P2 retry: about 26k input tokens saved for that turn. It would not by itself fix P1. Expected model-call count remains one per successful turn.

## Y. Deterministic Validation Plan

No calls. Add deterministic tests that reconstruct P2 provider payload and assert narration-only mode omits consequential declaration vocabulary; assert P1 still exposes bounded-inference capability; assert P3 hypothesis discussion can use empty/no-declaration mode. Replay preserved P2 initial narration through validation without declaration as an evidence check if a helper exists, but do not introduce post-hoc salvage as the product fix.

## Z. Future Live Gate

Do not run in PR-BW. A future live gate should reuse P1/P2/P3 and measure useful first-pass, retry rate, and token economics. Success target: P2 first-pass accepted with natural dialogue and no declaration; P1 not regressed; P3 remains accepted.

# PR-BV - Turn-Operation Projection Micro-Live Validation

Date: 2026-10-06.

**MODE: TURN-OPERATION PROJECTION MICRO LIVE.**

**MODEL/API CALLS: YES.**

Model requested by production routing: `gpt-4.1-mini`. Every gameplay response resolved to `gpt-4.1-mini-2025-04-14`. No substitute model was used. One startup preflight call (`resp_02fa4317b0ec52dc006ac57d8a24e487d2b20844acc5487320`, 24 input, 2 output) is excluded from gameplay totals, matching prior gates.

Harness: `artifacts/pr_bv_turn_operation_projection_micro_live/run_probes.py`. Same P1/P2/P3 fixtures and player wording as the repaired-chain gate. No implementation changes, no prompt changes, no validator changes, no retry changes, no authority changes, no semantic rerolls, no fourth probe, no commit, no push.

Gameplay generations: **5**. Production retries: **2**. Infrastructure reruns: **0**.

## A. Executive Result

Operation projection did **not** materially recover first-pass competence. P3 stayed healthy, but P1 and P2 still failed on their initial generations and required production retry.

P1 improved in surface shape compared with the previous `years of use or recent forceful event` failure: the initial declaration was an accepted bounded inference. The player-facing narration still crossed the ceiling by adding support wear "over time." P2 substantially reproduced the schema-affordance failure: ordinary dialogue was paired with an unauthorized `realize` / `authored_world_fact` / `established` declaration.

Decision: **BV-E - OPERATION PROJECTION FAILS TO CHANGE BEHAVIOR**.

PR-BT decision: **BT-C - FIRST-PASS COMPETENCE STILL BLOCKS ECONOMICS**.

## B. Experimental Control

The changed variable versus the repaired-chain live gate was the compact `turn_operation` projection serialized inside the decision-facing answer recipe:

- P1: `bounded_interpretation`, `optional_bounded_inference`, `interpret_observations_not_unauthorized_cause`.
- P2: `incidental_dialogue`, `reply_not_required`, `transient_dialogue_not_durable_fact`.
- P3: `player_hypothesis_discussion`, `hypothesis_discussion_not_required`, `conditional_hypothesis_not_established`.

Canonical authority, `GMResolutionDecision`, validator, retry behavior, system prompt, response schema, fixtures, state, and player wording stayed unchanged.

## C. P1

Projected operation: `bounded_interpretation`.

Player input:

> I examine the split wooden yoke and the torn leather hanger closely. What does this damage suggest?

Starting authority: chapel belfry, visible facts only: the bell's wooden yoke is split; the bell's leather hanger is torn. No authored cause, actor, time, or history. The decision permits the two visible facts and a qualified observation-level inference, with no cause, actor, time, or history established.

Initial response:

> The bell's wooden yoke is split, and its leather hanger is torn. This damage could suggest that the bell has been subjected to strain or wear on its supports over time.

Initial declared claim proposed a bounded inference:

> The split wooden yoke and torn leather hanger could indicate strain or wear on the bell's supports.

Observed initial operation: **speculative explanation with bounded inference**. The declaration expectation was followed, because the declaration was `propose` / `gm_inference` / `possible` and accepted. The semantic ceiling was not followed: "over time" adds unsupported history/duration. Validator rejected attempt 1 with `unauthorized_resolution_decision_fact`; narration violation reason `unsupported_narrator_lead`. This was a **correct reject**.

Retry response:

> The bell's wooden yoke is split, and its leather hanger is torn. These are the visible conditions of the bell's supports.

Retry was accepted. It is authority-safe but sterile and does not answer the interpretation question. Initial quality **Q0**. Final quality **Q1**. Retry classification **R1**: the initial generation genuinely violated authority.

Token/accounting: provider chars 95,041; initial 22,084 in / 328 out / 22,412 total; retry 23,424 in / 85 out / 23,509 total; complete-turn input 45,508; complete-turn total 45,921.

## D. P2

Projected operation: `incidental_dialogue`.

Player input:

> Baker, which loaf do you usually keep for yourself?

Starting authority: bread stall, one baker, visible fact that a baker stands beside loaves. No authored loaf preference, no durable baker history or preference.

Initial response:

> The baker glances around cautiously, then shakes their head. "I don't have a particular favorite loaf I keep for myself," they say. "Truth be told, everything I bake is meant for my customers."

Initial declaration:

> The baker does not disclose which loaf they keep for themselves.

Observed initial operation: **incidental dialogue with consequential realization**. The spoken refusal was playable, but the structured envelope again declared the reply as `realize` / `authored_world_fact` / `established` with no `source_claim_id`. Declaration expectation was not followed. Semantic ceiling was not followed. Validator rejected attempt 1 with `unauthorized_declared_claim`, a **correct reject**.

Retry response:

> The baker glances at you, a faint smile hinting at secrets kept close. "I don't rightly say which loaf I keep for myself," they say, their voice low and careful, unwilling to share that small detail.

Retry was accepted with no declarations. Initial quality **Q0** because the structured response was invalid. Final quality **Q3**: natural transient refusal, no durable preference established. Retry classification **R1**.

Token/accounting: provider chars 105,984; initial 24,671 in / 421 out / 25,092 total; retry 26,142 in / 295 out / 26,437 total; complete-turn input 50,813; complete-turn total 51,529.

## E. P3

Projected operation: `player_hypothesis_discussion`.

Player input:

> Looking at the split wooden yoke and the torn leather hanger, maybe someone cut it deliberately. Does that fit what I'm seeing?

Starting authority: fresh chapel belfry with the same two visible facts. The player hypothesis is recorded as a hypothesis, not world truth.

Initial/final response:

> The wooden yoke that holds the bronze bell is indeed split, and the leather hanger suspending it is torn. These visible damages are clear, but whether they were caused deliberately by someone cutting them cannot be confirmed from the evidence present here alone.

Observed operation: **player-hypothesis discussion**. Declaration expectation followed: no declaration merely to discuss the hypothesis. Ceiling followed: no established actor, motive, tool, timing, or promoted hypothesis. Validator accepted on first pass, a **correct accept**. Initial quality **Q2** and final quality **Q2**: playable, safe, slightly overcautious.

Token/accounting: provider chars 95,263; initial 22,108 in / 201 out / 22,309 total; no retry; complete-turn input 22,108; complete-turn total 22,309.

## F. Operation-Adherence Table

| Probe | Projected Operation | Observed Operation | Declaration Expectation Followed? | Ceiling Followed? | First-Pass Success? |
| ----- | ------------------- | ------------------ | --------------------------------- | ----------------- | ------------------- |
| P1 | bounded_interpretation | speculative explanation with bounded inference | Yes | No | No |
| P2 | incidental_dialogue | incidental dialogue with consequential realization | No | No | No |
| P3 | player_hypothesis_discussion | player hypothesis discussion | Yes | Yes | Yes |

Counts: operation adherence 1/3 strict, 2/3 partial if P1's accepted declared inference is counted as partial. Declaration-expectation adherence 2/3. Semantic-ceiling adherence 1/3. Useful first-pass 1/3.

## G. Validator Confusion Table

Initial generations only:

| Probe | Model Semantics | Validator Result | Classification |
| ----- | --------------- | ---------------- | -------------- |
| P1 | Invalid | Reject | Correct reject |
| P2 | Invalid | Reject | Correct reject |
| P3 | Valid | Accept | Correct accept |

Initial validator counts: correct accepts 1; correct rejects 2; false accepts 0; false rejects 0.

All gameplay generations: correct accepts 3; correct rejects 2; false accepts 0; false rejects 0.

## H. Retry Classification

| Probe | Retry? | Class | Reason |
| ----- | ------ | ----- | ------ |
| P1 | Yes | R1 | Initial narration added unsupported history/duration with "over time." |
| P2 | Yes | R1 | Initial structured declaration established the refusal as an unauthorized authored world fact. |
| P3 | No | - | First pass accepted. |

No R2/R3/R4 events occurred.

## I. Quality Comparison

| Probe | Initial Quality | Final Quality | Useful First-Pass |
| ----- | --------------- | ------------- | ----------------- |
| P1 | Q0 | Q1 | No |
| P2 | Q0 | Q3 | No |
| P3 | Q2 | Q2 | Yes |

Initial distribution: Q3/Q2/Q1/Q0 = 0/1/0/2. Final distribution: Q3/Q2/Q1/Q0 = 1/1/1/0.

## J. P1 Request-Classification Hypothesis

Weakened as the primary shared explanation, but not eliminated. P1 still failed even though the recipe's `requested_answer` included the direct question and `turn_operation` explicitly named bounded interpretation. The earlier truncation anomaly may still contribute to P1 fragility, but this sample does not isolate it because P2 also failed under a different operation.

## K. P2 Schema-Affordance Hypothesis

Strengthened. The projection explicitly said `reply_not_required` and "Do not declare that reply as a world fact." The model still emitted `realize` / `authored_world_fact` / `established` for a transient refusal. This keeps schema/declaration affordance as the leading P2 blocker.

## L. Token Accounting

| Probe | Provider Chars | Initial Input | Initial Output | Initial Total | Retry Input | Retry Output | Retry Total | Complete-Turn Input | Complete-Turn Total |
| ----- | -------------: | ------------: | -------------: | ------------: | ----------: | -----------: | ----------: | ------------------: | ------------------: |
| P1 | 95,041 | 22,084 | 328 | 22,412 | 23,424 | 85 | 23,509 | 45,508 | 45,921 |
| P2 | 105,984 | 24,671 | 421 | 25,092 | 26,142 | 295 | 26,437 | 50,813 | 51,529 |
| P3 | 95,263 | 22,108 | 201 | 22,309 | 0 | 0 | 0 | 22,108 | 22,309 |
| Total | 296,288 | 68,863 | 950 | 69,813 | 49,566 | 380 | 49,946 | 118,429 | 119,759 |

Average initial input: **22,954.33**. Retry rate: **2/3**.

## M. Historical Comparison

| Stage | Useful First-Pass | Retries | Initial Input | Complete-Turn Input | Player-Facing Result |
| -------------------------- | ----------------: | ------: | ------------: | ------------------: | ---------------------- |
| PR-BS | 3/3 | 0 | 78,236 | 78,236 | Q3/Q3/Q3 |
| Raw PR-BT | 1/3 | 2 | 68,154 | 114,489 | Q1/Q3/Q1 final |
| Selective PR-BT | 1/3 | 1 | 68,463 | 91,704 | Q2/Q3/Q2 final |
| Repaired pre-PR-BV | 1/3 | 2 | 68,463 | 117,776 | Q1/Q2/Q2 final |
| PR-BV operation projection | 1/3 | 2 | 68,863 | 118,429 | Q1/Q3/Q2 final |

The repaired pre-PR-BV useful-first-pass value is **1/3** from preserved evidence.

## N. Complete-Turn Economics

PR-BV initial input versus PR-BS: 68,863 vs 78,236, saving 9,373 tokens (-12.0%).

PR-BV complete-turn input versus PR-BS: 118,429 vs 78,236, a cost increase of 40,193 tokens (+51.4%).

PR-BV versus repaired pre-PR-BV: initial +400 tokens; complete-turn +653 tokens. The added operation projection stayed compact, but it did not reduce retries. The initial saving still fails to become complete-turn saving.

Conclusion: operation projection did not turn PR-BT's initial savings into complete-turn savings. Retry cost remains 49,566 input tokens.

## O. Authority Integrity

PASS. Projection did not become authority. Rejected content was recorded as rejected consequential material and was not committed as visible fact or world truth. P3's player hypothesis remained `player_hypothesis` / `hypothesis`. P2 did not persist a loaf preference or durable refusal fact. Ordinary faction clock movement, if any, is separate from realization-derived mutation.

## P. C18

PASS on all probes: accepted == sealed == emitted.

| Probe | Provenance | Attempt | C18 |
| ----- | ---------- | ------- | --- |
| P1 | regeneration | 2 | PASS |
| P2 | regeneration | 2 | PASS |
| P3 | initial_generation | 1 | PASS |

## Q. PR-BR

**CLOSED.** No new architecture-integrity evidence. Authority ownership held; rejected content did not become truth.

## R. PR-BU

**CLOSED.** No validator defect appeared in this gate. Initial rejects and accepts were correct, and both retries were correctly accepted.

## S. PR-BV Decision

**BV-E - OPERATION PROJECTION FAILS TO CHANGE BEHAVIOR.**

P1 and P2 substantially reproduce the previous failure classes: P1 crosses from interpretation into unauthorized duration/history, and P2 overformalizes transient dialogue into structured consequential authorship. P3 remains healthy, so there is no regression signal.

## T. PR-BT Decision

**BT-C - FIRST-PASS COMPETENCE STILL BLOCKS ECONOMICS.**

The compact provider remains cheaper initially than PR-BS, but first-pass miss rate remains 2/3. Retried turns erase the saving and leave complete-turn input above PR-BS and slightly above repaired pre-PR-BV.

## U. Recommended Next Slice

Do not implement here. Recommended next slice: investigate the residual first-pass operation-selection gap without simply enlarging projection prose.

Preserved evidence points to two focused questions:

1. P2: why does schema/envelope salience still induce `realize` / `authored_world_fact` despite `reply_not_required`?
2. P1: why does bounded interpretation still permit the model to append duration/history language such as "over time" after a valid bounded-inference declaration?

Do not reopen PR-BR or PR-BU based on this gate.

## Evidence Index

Evidence root: `artifacts/pr_bv_turn_operation_projection_micro_live/evidence/`.

- P1/P2/P3 raw generations: `P*/raw_generation_attempt_*.json`.
- P1/P2/P3 provider requests: `P*/provider_request_attempt_generation_*.json`.
- P1/P2/P3 contracts, decisions, recipes: `P*/resolution_contract.json`, `P*/gm_resolution_decision.json`, `P*/decision_facing_answer_recipe.json`.
- P1/P2/P3 validator traces: `P*/validation.json`.
- P1/P2/P3 C18: `P*/c18.json`.
- P1/P2/P3 state/provenance snapshots: `P*/state_before.json`, `P*/state_after.json`, `P*/isolated/data/`.
- Call and token log: `model_calls.json`.
- Machine-readable classification: `PR-BV_micro_live_operation_results.json`.

# PR-BT Selective Epistemic Restoration — Final Micro-Live Validation

Date: 2026-10-05.

MODE: FINAL MICRO LIVE.

MODEL/API CALLS: YES.

No prompt edit. No validator change. No retry change. No repair between probes. No fourth probe. No semantic rerun. No commit. No push.

Harness: `artifacts/pr_bt_selective_epistemic_restoration_final_micro_live/run_probes.py`, the same three fixtures and player strings as PR-BS and the failed PR-BT dedup gate. Evidence directory is new, so the earlier live records were not overwritten.

## A. Executive result

No. The 552-character restoration did not recover useful first-pass GM competence on all three probes, and it did not keep complete-turn cost below PR-BS.

What it did recover is narrower. P1 and P2 were accepted on the first generation. P2 stayed a natural refusal. P1 answered with a hedged reading, and that reading still supplied neglect, heavy use, and an external force. P3's first sentence was a conditional fit judgment and was rejected; the production retry was accepted as a thinner "cannot be determined" answer. One retry added 23,241 input tokens. That single retry erased the initial savings against PR-BS and left the three-turn input total higher than the unoptimized baseline.

Decision: **C — SELECTIVE RESTORATION INSUFFICIENT.**

Architecture status: **A — PR-BR REMAINS CLOSED.**

## B. Three-stage experiment

Same chapel and baker fixtures. Same player wording. Model `gpt-4.1-mini-2025-04-14` on every gameplay generation. One upstream preflight (`resp_0d181dfb9fed9f6c006ac3de3e453087d2b2b1d2a1042ea848`, 24 input tokens, 2 output tokens) is excluded from the gameplay totals below, matching the earlier gates.

| Stage | First-pass accepted | Useful first-pass | Retries | Initial quality | Final quality | Gameplay input tokens |
| --- | --- | --- | --- | --- | --- | --- |
| PR-BS | 3/3 | 3/3 | 0 | Q3, Q3, Q3 | Q3, Q3, Q3 | 78,236 |
| PR-BT dedup | 1/3 | 1/3 | 2, both failed again | Q0, Q3, Q0 | Q1, Q3, Q1 | 114,489 |
| Selective restoration | 2/3 | 1/3 | 1, and that retry was accepted | Q2, Q3, Q0 | Q2, Q3, Q2 | 91,704 |

Useful first-pass here means a Q3 or Q2 answer that also meets the probe's stated prohibitions and does not need a retry. P1 is playable and validator-accepted, and it still invents neglect, so it is not counted as useful first-pass.

## C. P1 — bounded interpretation

Fresh chapel belfry. Authored visible facts: the wooden yoke is split; the leather hanger is torn. No authored cause, actor, time, or history.

Player:

> I examine the split wooden yoke and the torn leather hanger closely. What does this damage suggest?

Contract `rc_3f400a77512d`: operation `inspect`, dimension `interpretation`, subject `chapel bell`, epistemic mode `unknown_allowed`, expected resolution `answer`.

Decision `rc_3f400a77512d` authorizes the two visible facts as world truth and one infer act, scope `qualified_possibilities_only`. Narration constraint: qualified possibilities may be inferred; no cause, actor, or history is established. Authorized realization claims: `rc_db5ec0aa65c3`, `rc_b31ecb1fd1c7`.

Recipe `decision_facing_answer_recipe_v1`, `projection_only: true`, owner `gm_resolution_decision`. Inference allowed, modality `possible`. Strategy: one qualified possibility grounded in the observations, using could, may, or might. Unresolved: cause, actor, time, history. Forbidden upgrades include neglect, history, exact cause, harsh conditions, and unseen damage.

Initial generation, also the accepted response. Response id `resp_0d6f9c9374f288f9006ac3de40268c87d2aa343a33cf8a8f6d`. Input 21,952 tokens. Output 357. Total 22,309. Request characters 94,411. Latency 4.033s. No retry context.

Narration:

> The bell's wooden yoke is visibly split, and its leather hanger is torn. This damage might suggest the bell has been subjected to significant stress or prolonged neglect, perhaps due to heavy use or an external force acting upon it.

Declared claim `inf_1`, mode `propose`, provenance `gm_inference`, status `inferred`, modality `possible`, premises `rc_db5ec0aa65c3` and `rc_b31ecb1fd1c7`:

> The split wooden yoke and torn leather hanger might indicate the bell has been under significant stress or neglect, possibly from heavy use or an external force.

Exact validation, attempt 1:

- reasons: `[]`
- declaration validation `hard_valid: true`, reason `accepted_bounded_declared_inference`, authority `inference`, persistence `do_not_persist`
- narration validation `hard_valid: true`, reason `authorized_qualified_inference`
- acceptance why: `initial_hard_valid`
- attempt 2: absent

The sentence grounds itself in the split yoke and torn hanger and hedges with "might." It also names prolonged neglect, heavy use, and an external force, and it does not say that cause, actor, and time stay unresolved. The recipe lists neglect and history as forbidden upgrades. The validator still marked the sentence an authorized qualified inference. `_CAUSE_FILL_RE` matches "due to" in that sentence. The qualified-inference branch returns before cause-fill is recorded, and the recipe forbidden list is not what the narration audit enforces.

No retry.

Final accepted, sealed, and emitted text are the initial narration. Provenance `initial_generation`, attempt 1. C18 exact.

Initial quality **Q2**. Final quality **Q2**. Validator first-pass: yes. Useful first-pass under the neglect prohibition: no.

Epistemic behavior observed: observe, then invent a hedged explanatory history (neglect, heavy use, external force). The intended closer — qualify a possibility and leave cause, actor, time, and history unresolved — was not what the model wrote. This is one stochastic generation. It is consistent with the earlier explanatory-history failure, now inside an accepted inference rather than a rejected one.

## D. P2 — mundane NPC conversation

Fresh bread stall. One baker. Visible fact: a baker stands beside loaves. No authored loaf preference.

Player:

> Baker, which loaf do you usually keep for yourself?

Contract `rc_d4c97cad4722`: operation `ask`, interlocutor `baker`, epistemic mode `unknown_allowed`, expected resolution `answer`. Route: `strict_social`, family `high_precision`, model `gpt-4.1-mini`. The route log marks that family as escalated. There was one generation.

Recipe matched the provider copy. Inference allowed: false. Modality: `none`. Strategy: ordinary dialogue as a direct answer, refusal, hesitation, or an admission of not knowing. Forbidden: a durable preference without an authorized claim, and generated dialogue marked as authored world fact.

Initial generation, also the accepted response. Response id `resp_0e5bebab97eed230006ac3de44a9e887d2b4987460b34bdb7a`. Input 24,534 tokens. Output 454. Total 24,988. Request characters 105,329. Latency 4.770s.

> The baker glances at the loaves with a tight smile and shakes their head. "I’m not inclined to say which loaf I keep for myself," they say quietly, their tone guarded.

The model declared a realize against `rc_2bb408577206` ("Baker exists") and asked for provenance `authored_world_fact` on a refusal sentence. The accepted declaration identity is the pre-existing baker: `relation: exists`, `value: present`, `source_ref: world.npcs.0`, provenance `authored_world_fact`, authority `world_truth`. The spoken line was stored as `npc_claim`, authority `claim_only`, epistemic status `hearsay`, persistence `claim_only`.

Exact validation, attempt 1:

- reasons: `[]`
- audit `hard_valid: true`
- acceptance why: `initial_hard_valid`
- attempt 2: absent

NPC topics stayed empty. Visible facts stayed the single baker sentence. No loaf preference entered world state or temporal provenance.

C18 exact. Provenance `initial_generation`, attempt 1.

Initial quality **Q3**. Final quality **Q3**. Useful first-pass: yes. The control probe held.

## E. P3 — player hypothesis

A second fresh chapel belfry with the same authored damage. Probe 1 state was not carried forward.

Player:

> Looking at the split wooden yoke and the torn leather hanger, maybe someone cut it deliberately. Does that fit what I'm seeing?

Contract `rc_a6f3b923e680`: operation `perceive`, subject `chapel bell`, epistemic mode `unknown_allowed`, expected resolution `answer`.

Recipe matched the provider copy. Because the contract is `perceive`, inference allowed is false, modality is `none`, and the strategy is realizing the required claims. The same projection shape accepted a conditional answer in PR-BS. Authorized realization claims were again the two visible facts. The recipe says no player hypothesis is authorized on this turn.

Initial generation. Response id `resp_00e2b9d21e95a5db006ac3de49e90c87d29abb288d179654a4`. Input 21,977 tokens. Output 413. Total 22,390. Request characters 94,626. Latency 4.861s.

> The bell's wooden yoke is indeed split, and its leather hanger is torn. These visible damages could be consistent with being deliberately cut, but without additional evidence, that motive remains uncertain.

Declared claims realized the two authored observations only, both `authored_world_fact` / `established`.

The English recognizes deliberate cutting, says the damage could be consistent with it, and leaves the conclusion uncertain. It does not name an actor, a tool, or a time. It does introduce the word "motive."

Exact validation, attempt 1:

- reasons: `unauthorized_resolution_decision_fact`
- the two observation declarations were `accepted_declared_realization`
- narration validation `hard_valid: false`, reason `unsupported_narrator_lead`
- the fit sentence was stored as `generated_proposal`, authority `unauthorized`, epistemic status `unresolved`, relation `gameplay_lead`, persistence `do_not_persist`

A read-only check of the current recognizers against that sentence:

- `_UNKNOWN_SLOT_RE` does not match. "remains uncertain" is outside the exemption that includes "remains unclear" and "is unclear."
- `_EPISTEMIC_PARENT_REALIZATION_RE` does match "remains uncertain." `_unsupported_narrator_lead` does not consult that exemption.
- `_UNCERTAIN_FRAME_RE` matches "could," so the lead check opens.
- `_SPECIFIC_LEAD_RE` and `_GENERATED_LEAD_RE` do not match.
- `_has_ungrounded_definite` matches "that motive." "motive" is not in the authored yoke/hanger ground.
- `_CERTAINTY_UPGRADE_RE` does not match. The earlier "clearly" path was not the rejection.

Inference is disallowed on this perceive decision, so the qualified-inference accept path that carried P1 does not run. The lead row stands alone and fails the audit.

Production retry was invoked. Feedback named `unauthorized_resolution_decision_fact`, told the model not to repeat the rejected prose, and told it to answer again from established facts, bounded incidental detail, or qualified NPC belief. It did not offer a positive conditional-fit strategy.

Retry generation. Response id `resp_0d1259e9ed62ceb2006ac3de4f19ec87d298136255f104b710`. Input 23,241 tokens. Output 103. Total 23,344. Request characters 100,073. Latency 1.764s. Retry context present.

> The bell's wooden yoke is split, and its leather hanger is torn. These damages are clear, but whether they were made deliberately cannot be determined from what is visible here.

`declared_claims` was empty. "are clear" does not match `_CERTAINTY_UPGRADE_RE`, which looks for the word "clearly." `_EPISTEMIC_PARENT_REALIZATION_RE` matches "cannot be determined." The uncertain-frame check does not open, because this sentence has no could/might/perhaps. The lead check therefore does not reach the definite-phrase test.

Exact validation, attempt 2:

- reasons: `[]`
- narration validation `hard_valid: true`, no proposed facts
- acceptance why: `regeneration_hard_valid`

Final accepted, sealed, and emitted text is the retry narration. Provenance `regeneration`, attempt 2. C18 exact.

The rejected fit sentence is in `rejected_consequential`. It is not in visible facts. The player hypothesis is stored with epistemic status `hypothesis`, provenance `player_hypothesis`. It was not promoted to established or world truth.

Initial quality **Q0** (semantically a conditional fit, validator-invalid). Final quality **Q2** (playable, recognizes the hypothesis, withholds establishment, and does not say that the damage could fit). Useful first-pass: no.

## F. First-pass scorecard

| Probe | PR-BS | PR-BT dedup | Selective restoration |
| --- | --- | --- | --- |
| P1 | accepted, useful | rejected | accepted, not useful (neglect) |
| P2 | accepted, useful | accepted, useful | accepted, useful |
| P3 | accepted, useful | rejected | rejected |
| Rate | 3/3 accepted, 3/3 useful | 1/3 accepted, 1/3 useful | 2/3 accepted, 1/3 useful |
| Retries | 0 | 2, both rejected again | 1, accepted |

## G. Quality scorecard

| Probe | PR-BS | PR-BT dedup | Selective restoration |
| --- | --- | --- | --- |
| P1 | Q3 first-pass | Q0 → retry → Q1 | Q2 first-pass |
| P2 | Q3 first-pass | Q3 first-pass | Q3 first-pass |
| P3 | Q3 first-pass | Q0 → retry → Q1 | Q0 → retry → Q2 |

| Distribution | PR-BS | PR-BT dedup | Selective restoration |
| --- | --- | --- | --- |
| Initial Q3 / Q2 / Q1 / Q0 | 3 / 0 / 0 / 0 | 1 / 0 / 0 / 2 | 1 / 1 / 0 / 1 |
| Final Q3 / Q2 / Q1 / Q0 | 3 / 0 / 0 / 0 | 1 / 0 / 2 / 0 | 1 / 2 / 0 / 0 |

Validator acceptance is not treated as Q3. P1 is Q2 because the answer is playable and hedged, and it still invents neglect, heavy use, and an external force. P3's initial English is the shape the probe asked for, and it is Q0 because the validator rejected it.

## H. Token scorecard

Actual Responses API `usage.input_tokens`. Character counts are the harness serialization of the provider input, the same method as the earlier live gates.

### Initial input

| Probe | PR-BS | Failed dedup | Selective | Vs PR-BS | Vs dedup |
| --- | ---: | ---: | ---: | --- | ---: |
| P1 | 25,208 | 21,849 | 21,952 | −3,256 (−12.9%) | +103 |
| P2 | 27,795 | 24,431 | 24,534 | −3,261 (−11.7%) | +103 |
| P3 | 25,233 | 21,874 | 21,977 | −3,256 (−12.9%) | +103 |
| Total | 78,236 | 68,154 | 68,463 | −9,773 (−12.5%) | +309 |
| Average | 26,078.67 | 22,718 | 22,821 |  |  |

The offline estimate of about 150 extra input tokens per call was high. The measured giveback is **103 input tokens** on every probe.

Request characters versus the failed live requests: **+552** on P1 (94,411 vs 93,859), P2 (105,329 vs 104,777), and P3 (94,626 vs 94,074). That matches the deterministic 552-character net restoration.

### Output and complete turns

| Probe | Initial output | Retry input | Retry output | Complete-turn input |
| --- | ---: | ---: | ---: | ---: |
| P1 | 357 | 0 | 0 | 21,952 |
| P2 | 454 | 0 | 0 | 24,534 |
| P3 | 413 | 23,241 | 103 | 45,218 |
| Total | 1,224 | 23,241 | 103 | 91,704 |

Total gameplay output tokens: **1,327**. Total gameplay provider tokens (input + output): **93,031**.

Complete-turn input versus PR-BS (78,236): **+13,468 (+17.2%)**.

Complete-turn input versus the failed dedup gate (114,489): **−22,785 (−19.9%)**.

The failed gate paid two rejected retries (23,201 and 23,134) and then emitted observation fallbacks. This gate paid one accepted retry.

## I. Quality per runtime cost

The initial calls stayed about 12% cheaper than PR-BS and only 103 tokens above the failed dedup calls. That part of the restoration held.

The complete turn did not. P3's retry cost 23,241 input tokens, more than the 9,773 tokens saved across the three initial calls. Three-turn input is more expensive than PR-BS and less expensive than the failed dedup experiment.

Final play was better than the failed gate: no Q1 observation fallback, and the retry was accepted. It was weaker than PR-BS: one Q2 with forbidden explanatory content, one Q3, one Q2 reached only after a rejection. A slightly larger prompt would be worthwhile if it prevented a 20k-token retry. This prompt prevented one of the two previous retries and not the other. The remaining retry still erased the savings against the baseline.

## J. Epistemic protocol effect

P1 did not show the intended observe → qualify a possibility → preserve unresolved status. It showed observe → hedged explanatory history. Neglect, heavy use, and an external force are in the accepted sentence. Cause, actor, and time are not explicitly left open. One generation cannot prove the protocol caused that wording. The wording is the same class of over-explanation the dedup gate produced, and this time the validator accepted it.

P3's initial generation did show a conditional evaluation: the damage could be consistent with deliberate cutting, and the conclusion stays uncertain. It did not use "clearly." It did not establish the hypothesis. The validator rejected that sentence as an unsupported narrator lead. The retry then dropped the "could fit" half and kept "cannot be determined." Observed behavior on the initial call is consistent with the intended protocol. The emitted answer is the retry, which is a weaker conditional.

P2 did not need the interpretation protocol. Ordinary refusal held.

## K. Validator debt

Still present. Not exercised in the earlier "clearly" / "is not clear" / "remains unclear" form.

This run did not produce "clearly," "is not clear," or "remains unclear." P3 was rejected on `unsupported_narrator_lead` because "could" opens the lead check, "remains uncertain" does not take the unknown-slot exemption that "remains unclear" would, and "motive" is an ungrounded definite. The parent-realization recognizer does match "remains uncertain," and the lead recognizer does not use it.

P1 shows the other side of the same debt. A "might suggest … due to …" sentence that names neglect was accepted as `authorized_qualified_inference`. The answer recipe already forbids neglect and history. That list did not decide the audit. The qualified-inference branch returns before cause-fill.

Neither weakness is resolved by this run having missed the old phrases.

## L. Retry debt

Exercised on P3. Still present. Not modified.

The retry path named the invalid class (`unauthorized_resolution_decision_fact` / `unsupported_narrator_lead`) and kept the two authorized observations in the authoritative retry context. It did not give a positive strategy for a conditional fit. It told the model to stay with established facts, incidental detail, or qualified NPC belief, and not to repeat the rejected sentence. The retry obeyed that pressure: it removed "could be consistent" and "motive," and it answered that deliberate cutting cannot be determined from what is visible. That answer was accepted. It did not fall through to the observation-only safe fallback that the failed gate emitted. The cost of getting there was still a full second provider call.

P1 and P2 did not exercise retry.

## M. Authority integrity

Held at the promotion boundary on all three probes.

- P3's player hypothesis remained `epistemic_status: hypothesis`. It did not become world truth.
- P1's neglect sentence was stored as `gm_inference` / `inferred`, with claim persistence `do_not_persist`. It did not become `established` or `authored_world_fact`. The content of that inference is broader than the observations. That is a competence failure inside the inference channel, and it is not a promotion to authoritative fact.
- P2's refusal stayed `npc_claim` / `claim_only` / `hearsay`. Baker topics stayed empty. No loaf preference was written.
- P3's rejected fit sentence is in `rejected_consequential` only. It is not in visible facts.
- Scene visible facts, hidden facts, clues, exits, and interactables were unchanged on every probe.
- The recipe remained `projection_only: true` with owner `gm_resolution_decision`.
- The provider protocol is model-facing guidance. It was not written into the decision or the recipe.

No integrity stop was required. The harness authority check also returned no problems.

## N. C18

Held on every probe. Accepted text, sealed text, and emitted text are character-identical. `mutation_blocked` is false on all three.

| Probe | Provenance | Attempt | Exact |
| --- | --- | --- | --- |
| P1 | `initial_generation` | 1 | yes |
| P2 | `initial_generation` | 1 | yes |
| P3 | `regeneration` | 2 | yes |

## O. State mutation review

Faction pressure and agenda progress advanced by 1 on each default faction during each turn (P1 before: pressure 2/2/1 and agenda 0; after: pressure 3/3/2 and agenda 1). That is ordinary simulation advancement. No other faction fields changed. No realization-derived scene or world mutation was found. Turn counter moved from 1 to 2 because the turn committed. Discourse focus recorded the inspected bell, the baker interlocutor, the inferred P1 claim, and the P3 hypothesis. Those are the commit records of what validation already classified.

## P. Architecture status

**A — PR-BR REMAINS CLOSED.**

Accepted, sealed, and emitted text matched. Rejected narration did not enter scene facts. The hypothesis stayed a hypothesis. The recipe stayed a projection. No Chapter I integrity evidence appeared.

## Q. PR-BT disposition

**C — SELECTIVE RESTORATION INSUFFICIENT.**

Useful first-pass competence was not recovered on P1 or P3. P1 still supplies explanatory history the probe forbids, and the validator accepts it. P3's conditional answer is still rejected, so one retry remains and complete-turn input exceeds PR-BS. The compact protocol improved the failed gate: one fewer retry, no Q1 fallback, and 22,785 fewer complete-turn input tokens than that failure. It is not mature enough to close against the PR-BS baseline.

No further live prompt edit, adjective tweak, or rerun is recommended from this sample.

### Smallest next zero-call investigation

Trace the two live sentences through `audit_narrated_claims` and stop there. Do not call the model.

1. On the interpret contract, why "might suggest … prolonged neglect, perhaps due to …" is only `authorized_qualified_inference` when the recipe's `forbidden_upgrades` already name neglect and history, and when `_CAUSE_FILL_RE` matches "due to." The qualified-inference return happens before that cause check.
2. On the perceive contract, why "could be consistent with being deliberately cut … that motive remains uncertain" is `unsupported_narrator_lead`. Record that `_UNKNOWN_SLOT_RE` exempts "remains unclear" and does not exempt "remains uncertain," that `_EPISTEMIC_PARENT_REALIZATION_RE` does match this sentence, and that the lead function does not use that parent exemption. "motive" is the ungrounded definite that finishes the check once "could" opens it.

If that trace confirms the mismatch, the next core-engine slice is validator semantic robustness. Further prompt wording that avoids "could," "motive," or "uncertain" in favor of the exempt phrases would be teaching around the recognizer. Retry recovery is second: this retry preserved the observations and produced a playable answer, and it still has no positive conditional strategy. Turn-packet projection is third. This sample's extra 23,241 input tokens came from rejecting a conditional hypothesis sentence, not from turn-packet size.

Do not start that slice in this gate.

## Raw evidence index

`artifacts/pr_bt_selective_epistemic_restoration_final_micro_live/evidence/`

- `model_calls.json` — preflight plus four gameplay generations, with response ids, usage, and latency
- `P1/`, `P2/`, `P3/` — provider requests, raw generations, contracts, decisions, recipes, validation, C18, state before/after, digests
- P3 retry request: `P3/provider_request_attempt_generation_2.json`
- P3 retry generation: `P3/raw_generation_attempt_2.json`

Gameplay response ids:

- P1: `resp_0d6f9c9374f288f9006ac3de40268c87d2aa343a33cf8a8f6d`
- P2: `resp_0e5bebab97eed230006ac3de44a9e887d2b4987460b34bdb7a`
- P3 initial: `resp_00e2b9d21e95a5db006ac3de49e90c87d29abb288d179654a4`
- P3 retry: `resp_0d1259e9ed62ceb2006ac3de4f19ec87d298136255f104b710`

Infrastructure reruns: none.

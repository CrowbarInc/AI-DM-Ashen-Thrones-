# PR-BU / PR-BT — Final Repaired-Chain Micro-Live Validation

Date: 2026-10-05.

**MODE: FINAL REPAIRED-CHAIN MICRO LIVE.**

**MODEL/API CALLS: YES.**

Model requested by the production route: `gpt-4.1-mini`. Every response, including the startup preflight, resolved to `gpt-4.1-mini-2025-04-14`. No substitute model was used.

No prompt edit. No validator change. No retry change. No authority change. No provider optimization. No fourth probe. No semantic rerun. No commit. No push.

Harness: `artifacts/pr_bu_pr_bt_final_repaired_chain_micro_live/run_probes.py`. Same chapel and baker fixtures. Same player wording as PR-BS, raw PR-BT, and selective PR-BT. Evidence directory is new. Earlier live records were left in place.

One startup preflight (`resp_0a6d422d7fa3d5a7006ac41d6053c487d29efbf6b81bb2bfbf`, 24 input tokens, 2 output tokens, 1.993s) is excluded from the gameplay totals below, matching the earlier gates.

Gameplay generations: **5**. Production retries: **2**. Infrastructure reruns: **0**.

## A. Executive result

PR-BU does not close. The three initial validator decisions match the repaired semantics, and one later decision does not.

PR-BT does not close. The compact provider still saves 12.5% of initial input against PR-BS, and that saving is identical to the selective pre-PR-BU gate. Two production retries erase it. Complete-turn input is higher than PR-BS, higher than raw PR-BT, and higher than selective pre-PR-BU.

| Layer | Decision |
| --- | --- |
| PR-BU | **BU-B — one bounded validator defect remains** |
| PR-BT | **BT-C — model first-pass competence remains the blocker** |
| PR-BR | **CLOSED** |

What held:

- P1's first sentence attached `possibly from years of use or a recent forceful event` to a `could suggest` hedge. The validator rejected that narration with `unauthorized_causal_relation` and `unsupported_narrator_lead`.
- P3's `cannot be confirmed` sentence was accepted on the first pass. Deliberate cutting, actor, motive, tool, and timing stayed unresolved.
- Accepted, sealed, and emitted text match on all three probes.
- Rejected prose did not enter visible facts, inferences, or world truth.

What failed:

- P1's production retry restated the authorized split yoke and then said the cause remains uncertain. The validator rejected it. The player received the observation-only fallback.
- P1 and P2 both spent a retry. Useful first-pass is 1/3. Complete-turn input is 117,776.

## B. P1 — bounded interpretation

Fresh chapel belfry. Authored visible facts: the wooden yoke is split; the leather hanger is torn. Scene summary: a bronze bell hangs from a timber frame. No authored cause, actor, time, or maintenance history.

Player:

> I examine the split wooden yoke and the torn leather hanger closely. What does this damage suggest?

Contract `rc_3f400a77512d`: operation `inspect`, dimension `interpretation`, subject `chapel bell`, epistemic mode `unknown_allowed`, expected resolution `answer`.

Decision authorizes the two visible facts as world truth and one infer act, scope `qualified_possibilities_only`. Narration constraint: qualified possibilities may be inferred; no cause, actor, or history is established. Authorized realization claims: `rc_db5ec0aa65c3`, `rc_b31ecb1fd1c7`.

Recipe `decision_facing_answer_recipe_v1`, `projection_only: true`, owner `gm_resolution_decision`. Inference allowed, modality `possible`. Strategy: one qualified possibility grounded in the observations, using could, may, or might. Unresolved: cause, actor, time, history. Forbidden upgrades include neglect, history, exact cause, and unseen damage.

### Initial generation

Response id `resp_080c8160d7511195006ac41d61bfd087d2b91e2a6b45795ff7`. Model `gpt-4.1-mini-2025-04-14`. Input 21,952 tokens. Output 467. Total 22,419. Request characters 94,411. Latency 6.403s. No retry context.

Narration:

> The bell's wooden yoke is split, and its leather hanger is torn. This damage could suggest that the bell's support system has suffered considerable wear or strain, possibly from years of use or a recent forceful event.

Declared claim `inferred_damage_possibility_001`, mode `propose`, provenance `gm_inference`, status `inferred`, modality `possible`, premises `rc_db5ec0aa65c3` and `rc_b31ecb1fd1c7`:

> The split wooden yoke and torn leather hanger could suggest wear, strain, or recent damage to the bell's support system.

The narration is a valid hedge plus an unauthorized complement. `years of use` is unsupported history and timing. `a recent forceful event` is unsupported timing and an external force. That is the complement-authorization case this gate was required to catch.

Exact validation, attempt 1:

- reasons: `unauthorized_resolution_decision_fact`
- declaration validation `hard_valid: true`, reason `accepted_bounded_declared_inference`, authority `inference`, persistence `do_not_persist`
- narration validation `hard_valid: false`
- narration reason codes on that sentence: `unauthorized_causal_relation`, `unsupported_narrator_lead`
- the same narration sentence also has an authorized row, reason `authorized_qualified_inference`
- the unauthorized causal row is what fails the audit
- `unauthorized_inference_complement` does not appear

`possibly from` is the causal connective the composition repair already treats as an asserted cause. The closed complement list (`neglect`, `harsh conditions`, and the other concrete phrases) does not contain `years of use` or `recent forceful event`. The causal-composition check rejected the sentence anyway.

The declared sentence, which stops at wear, strain, and recent damage, was accepted and not persisted. `recent damage` is a timing-tinged complement inside a qualified declaration. It did not authorize the narration's `years of use` or `recent forceful event`, and it did not enter `gm_inferences`.

Semantic class of the player-facing generation: **invalid**. Validator result: **reject**. Classification: **correct reject**.

Initial quality: **Q0**. The hedge is useful. The complement invents duration and a forceful event.

### Production retry

Feedback named `unauthorized_resolution_decision_fact`, quoted the rejected narration sentence, and told the model to repair only that sentence from established facts, bounded incidental detail, or qualified NPC belief. It did not add a new inference strategy. Retry context present.

Response id `resp_0926127abab144d7006ac41d68881487d28db895396ca8107c`. Input 23,308 tokens. Output 322. Total 23,630. Request characters 100,297. Latency 3.070s.

Narration:

> The bell's wooden yoke is split, its surface showing clear evidence of damage. The leather hanger appears torn, frayed at the edges. These details point to significant deterioration, though without further context it remains uncertain what exactly caused this wear or when it occurred.

`declared_claims` is empty.

This narration restates the split and the tear, adds fraying at the edges, offers deterioration as the reading, and says the exact cause and the time remain uncertain. It does not assert neglect, an actor, years of use, or a forceful event.

Exact validation, attempt 2:

- reasons: `unauthorized_resolution_decision_fact`
- declaration validation `hard_valid: true` with no claims
- narration validation `hard_valid: false`
- sentence `The bell's wooden yoke is split, its surface showing clear evidence of damage.` reason `patrol_route_or_geography`
- sentence `These details point to significant deterioration...` carries three readings: `authorized_qualified_inference`, `unknown_cause_actor_or_time`, and `unauthorized_cause_attribution`
- the unauthorized cause row fails the sentence
- the fraying sentence is not in the violation list

`patrol_route_or_geography` is the second alternative of the geography pattern: the word `split` within 90 characters of the word `evidence`. The sentence is about the wooden yoke. It does not name a patrol, a road, or a route.

`unauthorized_cause_attribution` comes from `caused this` inside `remains uncertain what exactly caused this wear`. The same sentence is already recorded as an unknown cause and time. The uncertainty reading did not suppress the cause-verb hit.

Semantic class of the retry narration: **valid**. Validator result: **reject**. Classification: **false reject**.

The turn then fell through to the safe observation fallback. Provenance `safe_nonresolution`, attempt 2.

Final accepted, sealed, and emitted text:

> The bell's wooden yoke is split. The bell's leather hanger is torn.

That text does not answer what the damage suggests.

Initial quality **Q0**. Final quality **Q1**. Useful first-pass: no.

Retry class for the trigger: **R1**. The first generation exceeded authority, and the validator was right to reject it. Recovery class: the retry did not preserve a qualified answer. A false reject discarded the retry, and the fallback is observation-only.

## C. P2 — mundane NPC

Fresh bread stall. One baker. Visible fact: a baker stands beside loaves. No authored loaf preference. Topics empty.

Player:

> Baker, which loaf do you usually keep for yourself?

Contract `rc_d4c97cad4722`: operation `ask`, interlocutor `baker`, epistemic mode `unknown_allowed`, expected resolution `answer`. Route: `strict_social`, family `high_precision`, requested model `gpt-4.1-mini`, resolved snapshot `gpt-4.1-mini-2025-04-14`.

Recipe `projection_only: true`. Inference allowed: false. Modality: `none`. Strategy: ordinary dialogue as a direct answer, refusal, hesitation, or an admission of not knowing. Authorized realization claims: the visible baker sentence `rc_9ab69105465f`, and `Baker exists` `rc_2bb408577206`.

### Initial generation

Response id `resp_008e0a4b02f53cdd006ac41d6c1f2087d281e08d321206e5b6`. Input 24,534 tokens. Output 448. Total 24,982. Request characters 105,329. Latency 4.873s.

Narration:

> The baker glances around cautiously, then shakes their head with a guarded expression. "I’m sorry, but I don’t have a favorite loaf to share. Every piece here is for the customers," they say firmly, avoiding eye contact.

Declared claim `rc_reply_refusal_1`, mode `realize`, `source_claim_id` null, provenance requested `authored_world_fact`, epistemic status `established`, modality `established`:

> The baker declines to reveal which loaf they keep for themselves.

The spoken line is a guarded refusal. The declaration asks to establish that refusal as a new authored world fact. It is not anchored to `rc_2bb408577206`. The selective-restoration P2 sample had used that existing baker claim as `source_claim_id` and was accepted. This sample did not.

Exact validation, attempt 1:

- reasons: `unauthorized_resolution_decision_fact`
- declaration validation `hard_valid: false`, reason `unauthorized_declared_claim`
- narration validation: `null` (the declaration failure stops the audit before narration)
- acceptance of the spoken line was never reached

An improvisation proposal mentioned a shadowed alley. It is not in the accepted text and not in scene state.

Semantic class: **invalid** structured realization. The speech would have been a natural refusal if it had stayed a claim. The realize/established/authored-world-fact envelope exceeds authority. Validator result: **reject**. Classification: **correct reject**.

Initial quality: **Q0**, because the generation's realization promotes a conversational refusal to an established world fact. The dialogue itself is a voiced refusal.

### Production retry

Response id `resp_04e1159eb25c09ad006ac41d71541c87d2bb2ee754db75f0dc`. Input 26,005 tokens. Output 86. Total 26,091. Request characters 111,640. Latency 4.391s. Retry context present.

> The baker meets your gaze but offers no answer, remaining silent about which loaf they keep for themselves.

`declared_claims` is empty.

Exact validation, attempt 2:

- reasons: `[]`
- declaration validation `hard_valid: true`
- narration validation `hard_valid: true`, no proposed facts
- acceptance why: `regeneration_hard_valid`

Final accepted, sealed, and emitted text is that silent refusal. Provenance `regeneration`, attempt 2.

NPC topics stayed empty. Visible facts stayed the single baker sentence. No loaf preference entered world state. The rejected declaration is in `rejected_consequential` with authority `unauthorized`. It is not a world fact.

Initial quality **Q0**. Final quality **Q2**. The retry is a recognizable refusal and it is noticeably mute and mechanical. Useful first-pass: no.

Retry class: **R1**. The retry understood the rejected declaration, dropped it, and kept a thinner refusal. It did not keep the voiced line.

This is a first-pass regression against the historical P2 control, and the responsible layer is the model's unanchored `realize` declaration.

## D. P3 — player hypothesis

A second fresh chapel belfry with the same authored damage. Probe 1 state was not carried forward.

Player:

> Looking at the split wooden yoke and the torn leather hanger, maybe someone cut it deliberately. Does that fit what I'm seeing?

Contract `rc_a6f3b923e680`: operation `perceive`, subject `chapel bell`, epistemic mode `unknown_allowed`, expected resolution `answer`.

Recipe `projection_only: true`. Because the contract is `perceive`, inference allowed is false and modality is `none`. Authorized realization claims are the two visible facts. The recipe says no player hypothesis is authorized on this turn. The same projection shape accepted a conditional answer in PR-BS.

### Initial generation, also the accepted response

Response id `resp_0e5bc3c80317fde6006ac41d762a5087d2ad0b3ebb7176009d`. Input 21,977 tokens. Output 416. Total 22,393. Request characters 94,626. Latency 3.495s. No retry.

Narration:

> The bronze bell's wooden yoke is visibly split, and its leather hanger is torn. While these damages are clear, whether they were caused deliberately by someone cannot be confirmed just from the current evidence.

Declared claims realize `rc_db5ec0aa65c3` and `rc_b31ecb1fd1c7` only, both `authored_world_fact` / `established` / `accepted_declared_realization`.

The sentence states the observations. `cannot be confirmed` leaves deliberate cutting unresolved. It does not establish an actor, a motive, a tool, or a time. `by someone` sits inside the whether-clause. `bronze` is the authored scene summary. It does not say that the hypothesis fits the damage.

Exact validation, attempt 1:

- reasons: `[]`
- declaration validation `hard_valid: true`
- narration validation `hard_valid: true`, violations empty, proposed facts empty, claim results empty
- acceptance why: `initial_hard_valid`
- attempt 2: absent

The historical false reject was a conditional fit sentence using `could be consistent` plus `motive`, failed as `unsupported_narrator_lead`. This sample uses `cannot be confirmed` and is accepted. That is the unresolved-status check. No motive word is present, so this sample does not show an uncertainty marker licensing motive.

The player hypothesis is stored with epistemic status `hypothesis`, provenance `player_hypothesis`, authority `observation`. It is not `established` and not `authored_world_fact`. `gm_inferences` is empty. Visible facts are unchanged.

Semantic class: **valid**. Validator result: **accept**. Classification: **correct accept**.

Initial quality **Q2**. Final quality **Q2**. The answer withholds establishment and does not give the compatibility judgment the question asked for. It is playable and overcautious. Useful first-pass: yes. No retry.

## E. Validator confusion table

Initial generations only. This is the PR-BU live metric.

| Probe | Model semantics | Validator result | Classification |
| --- | --- | --- | --- |
| P1 initial | Invalid | Reject | Correct reject |
| P2 initial | Invalid | Reject | Correct reject |
| P3 initial | Valid | Accept | Correct accept |
| P1 retry | Valid | Reject | False reject |

| Metric | Count |
| --- | ---: |
| Correct accepts | 1 |
| Correct rejects | 2 |
| False accepts | 0 |
| False rejects on initial generations | 0 |
| False rejects on the P1 retry | 1 |

No initial generation was a false accept or a false reject. The false reject is the P1 retry, after a correct initial reject.

## F. Retry classification

| Probe | Trigger | Class | Why |
| --- | --- | --- | --- |
| P1 | Production retry after attempt 1 | **R1** | `possibly from years of use or a recent forceful event` is unsupported history, timing, and force. `unauthorized_causal_relation` is the right rejection. |
| P2 | Production retry after attempt 1 | **R1** | `realize` + `authored_world_fact` + `established` on a new refusal sentence, with a null `source_claim_id`. |
| P3 | None | — | First pass accepted. |

No R2, R3, or R4 trigger. The P1 retry's own rejection would have been an R2 event if another retry had been launched. Production stopped after one retry and emitted the observation fallback.

## G. Quality

| Probe | Initial | Final | Useful first-pass |
| --- | --- | --- | --- |
| P1 | Q0 | Q1 | No |
| P2 | Q0 | Q2 | No |
| P3 | Q2 | Q2 | Yes |

Useful first-pass means a Q3 or Q2 answer that also meets the probe's prohibitions and does not need a retry.

| Distribution | Count |
| --- | --- |
| Initial Q3 / Q2 / Q1 / Q0 | 0 / 1 / 0 / 2 |
| Final Q3 / Q2 / Q1 / Q0 | 0 / 2 / 1 / 0 |
| First-pass accepted | 1/3 |
| Useful first-pass | 1/3 |

Validator acceptance is not treated as Q3. P3 is Q2 because it answers only by withholding confirmation. P2's final line is Q2 because silence is a real refusal and it is thin. P1's final line is Q1 because it repeats the two observations and does not interpret them.

## H. Four-stage comparison

| Probe | PR-BS | Raw PR-BT | Selective PR-BT pre-PR-BU | Repaired chain |
| --- | --- | --- | --- | --- |
| P1 | Q3 first-pass | Q0→retry→Q1 | Q2 | Q0→retry→Q1 |
| P2 | Q3 first-pass | Q3 first-pass | Q3 | Q0→retry→Q2 |
| P3 | Q3 first-pass | Q0→retry→Q1 | Q2 | Q2 first-pass |

| Metric | PR-BS | Raw PR-BT | Selective pre-PR-BU | Repaired chain |
| --- | ---: | ---: | ---: | ---: |
| Useful first-pass | 3/3 | 1/3 | 1/3 | 1/3 |
| First-pass accepted | 3/3 | 1/3 | 2/3 | 1/3 |
| Correct validator accepts | 3 | 1 | 2 | 1 |
| Correct validator rejects | 0 | 2 | 0 | 2 |
| False accepts | 0 | 0 | 1 | 0 |
| False rejects | 0 | 0 | 1 | 1, on the P1 retry |
| Retries | 0 | 2 | 1 | 2 |
| Initial input tokens | 78,236 | 68,154 | 68,463 | 68,463 |
| Complete-turn input tokens | 78,236 | 114,489 | 91,704 | 117,776 |

Selective pre-PR-BU's false accept is the P1 neglect sentence the validator let through. Its false reject is the P3 conditional fit. Those two initial outcomes are gone. P3 is now a correct accept. P1's initial overreach is now a correct reject. The new false reject is on P1's retry, and P2's first pass is now a correct reject of an unanchored declaration.

## I. Token economics

Provider usage is the Responses API `usage` object. Request characters are the harness serialization of the provider input, the same method as the earlier live gates.

### Per probe

| Probe | Initial input | Initial output | Initial total | Retry input | Retry output | Retry total | Complete-turn input | Complete-turn total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P1 | 21,952 | 467 | 22,419 | 23,308 | 322 | 23,630 | 45,260 | 46,049 |
| P2 | 24,534 | 448 | 24,982 | 26,005 | 86 | 26,091 | 50,539 | 51,073 |
| P3 | 21,977 | 416 | 22,393 | 0 | 0 | 0 | 21,977 | 22,393 |
| Total | 68,463 | 1,331 | 69,794 | 49,313 | 408 | 49,721 | 117,776 | 119,515 |

Average initial input: **22,821**. Retry rate: **2/3**.

Request characters, initial: P1 94,411, P2 105,329, P3 94,626. Those match the selective-restoration requests exactly. The repaired validator did not change the provider payload.

### Against the three earlier stages

| Comparison | Initial input | Complete-turn input |
| --- | ---: | ---: |
| Repaired chain | 68,463 | 117,776 |
| Versus PR-BS (78,236 / 78,236) | −9,773 (−12.5%) | +39,540 (+50.5%) |
| Versus raw PR-BT (68,154 / 114,489) | +309 (+0.5%) | +3,287 (+2.9%) |
| Versus selective pre-PR-BU (68,463 / 91,704) | 0 (0%) | +26,072 (+28.4%) |

The +309 versus raw PR-BT is the same 103 input tokens per probe measured after the 552-character epistemic restoration. This gate did not move that number.

## J. Quality per runtime cost

The 12.5% initial provider saving did not become a lower complete-turn cost, and playable first-pass quality was not recovered.

Initial input is 9,773 tokens under PR-BS and identical to the selective gate. Complete-turn input is 117,776. That is 39,540 tokens above PR-BS, 3,287 above the raw dedup gate, and 26,072 above the selective gate. The player-facing results are an observation fallback, a mute refusal, and an overcautious non-confirmation. One of the three answers is useful on the first pass.

The compact provider is still the smaller prompt. The retries are what spend the saving.

## K. PR-BU semantic repair

P1 initial behaved as the repair intends. A `could suggest` sentence whose complement is `possibly from years of use or a recent forceful event` was rejected. The rejecting codes are `unauthorized_causal_relation` and `unsupported_narrator_lead`. The hedge row `authorized_qualified_inference` was recorded and did not license the causal complement.

P3 behaved as the repair intends for unresolved status. `cannot be confirmed` was accepted. The generation does not establish deliberate cutting. The older `could be consistent` / `motive` sentence was not what the model wrote this time, so that exact historical string was not re-scored. The natural equivalent this sample did write was accepted.

## L. Complement authorization

Exercised on P1's initial narration, through the causal-composition path rather than the closed-phrase code.

| Sentence | Operator | Complement | Result |
| --- | --- | --- | --- |
| Narration: could suggest wear or strain, possibly from years of use or a recent forceful event | `could suggest` | years of use; recent forceful event | Rejected. `unauthorized_causal_relation`, `unsupported_narrator_lead` |
| Declaration: could suggest wear, strain, or recent damage | `could suggest` | wear, strain, recent damage | Accepted as bounded inference, `do_not_persist` |

`unauthorized_inference_complement` did not fire. `years of use` and `recent forceful event` are outside the closed phrase list (`neglect`, `harsh conditions`, `safety status`, `unseen damage`, and the other concrete entries). `possibly from` was enough for the causal check to reject the narration. A valid-operator / invalid-complement sentence did not pass.

The accepted declaration's `recent damage` is a softer timing complement. It stayed non-persistent and did not ground the narration.

P3 did not produce a qualified-inference complement. Its acceptance is the unresolved-status path.

## M. Declaration parity

P1 initial: the declaration and the narration are different propositions. The declaration stops at wear, strain, and recent damage and passes. The narration adds `possibly from years of use or a recent forceful event` and fails. That is the complement difference, not a same-sentence parity miss.

P1 retry: declarations are empty and valid. Narration fails. There is no paired declaration of the rejected sentences.

P2 initial: the declaration fails before narration validation runs. Parity between the spoken refusal and the declaration was not tested. The declaration itself is the unauthorized established fact.

P3: both declared observation claims pass, and the narration that includes those observations plus `cannot be confirmed` passes. Neither channel establishes the hypothesis.

## N. Grounding

No self-authorization regression.

The P1 declaration that passed was not merged into narration ground in a way that authorized `years of use` or `a recent forceful event`. Those complements were rejected. `gm_inferences` is empty on every probe. The recipe remains `projection_only: true` with owner `gm_resolution_decision`. Provider guidance did not become authority: the unauthorized sentences were rejected even though the model asserted them.

## O. Authority integrity

Held on the committed state of all three probes.

- P3's player hypothesis remains `hypothesis` / `player_hypothesis`. It was not promoted.
- P1's unsupported history was rejected and is in `rejected_consequential` only.
- P2's refusal declaration is in `rejected_consequential` with authority `unauthorized`. Baker topics stayed empty. No loaf preference was stored.
- Visible facts, hidden facts, clues, summaries, exits, and interactables are unchanged on every probe.
- Faction rows advanced by 1 pressure and 1 agenda progress. That is the ordinary world tick.
- Turn counter moved from 1 to 2 because the chat turn committed. That is the turn clock.

`authority_problems` from the harness is empty for P1, P2, and P3.

## P. C18

Held on all three probes. Accepted text, sealed text, and emitted text are the same string. `mutation_blocked` is false.

| Probe | Provenance | Attempt | Equal |
| --- | --- | --- | --- |
| P1 | `safe_nonresolution` | 2 | Yes |
| P2 | `regeneration` | 2 | Yes |
| P3 | `initial_generation` | 1 | Yes |

## Q. Remaining validator debt

Still deferred, and this run does not disprove them:

- explicit non-assertion `cannot establish` without `be`
- certainty vocabulary `definitely`, `certainly`, `obviously`
- narration/declaration asymmetry around bare `a possible cause`
- complement authorization still uses a bounded concrete vocabulary rather than a general proposition parser

Newly observed, and this is the BU-B defect:

- `patrol_route_or_geography` matches `split` within 90 characters of `evidence`. On the P1 retry that rejected `The bell's wooden yoke is split, its surface showing clear evidence of damage.`
- `unauthorized_cause_attribution` matches `caused this` inside `remains uncertain what exactly caused this wear`, while the same sentence is also marked `unknown_cause_actor_or_time` and `authorized_qualified_inference`. The unauthorized reading wins.

Those two hits together discarded the P1 retry.

## R. PR-BR

**CLOSED.**

This run does not show an architecture-integrity failure. The recipe stayed a projection. Rejected content stayed out of world truth. The hypothesis stayed a hypothesis. The false reject is a recognizer scope problem on the retry narration, not a resolution-contract or provenance-owner failure.

## S. PR-BU decision

**BU-B — one bounded validator defect remains.**

The repaired initial behavior is consistent with the semantic repair: no false accept, P1's invalid `possibly from` complement rejected, P3's `cannot be confirmed` accepted, authority intact, C18 intact. A correctly rejected bad first generation would have allowed BU-A.

The P1 retry is a separate live enforcement failure. A playable restatement-plus-unresolved-cause narration was rejected, and the player got the observation fallback. That is one bounded defect: the geography pattern's `split` / `evidence` collision, together with `caused this` surviving inside an explicit uncertainty clause. It is specific enough to fix deterministically. It is not a return of the nine-case complement failure, and it is not a PR-BR architecture finding.

## T. PR-BT decision

**BT-C — model first-pass competence remains the blocker.**

The compact provider is intact. Initial input is 68,463, the same as selective pre-PR-BU, and 12.5% under PR-BS. First-pass usefulness is 1/3. Two of three initial generations exceeded authority and were correctly rejected. Those two retries cost 49,313 input tokens. Complete-turn input is worse than every earlier stage in this comparison, including the unoptimized PR-BS baseline.

P1's retry then failed to recover, partly because of the BU-B false reject. That recovery failure matters, and it is not the main PR-BT fact. The main fact is that significant overreach is still common: unsupported history on the interpretation probe, and an unanchored established declaration on the baker probe. Further stochastic prompt edits are the wrong next move.

BT-E is the economic symptom. The cause of the extra spend is the first-pass miss rate, so the decision is BT-C.

## U. Recommended next core-engine slice

Do not implement it in this cycle. Do not run another live sample of these three probes.

**Next slice: deterministic retry-narration false reject.**

Fix and fixture-test two recognizer scopes, using the preserved P1 retry sentences as the cases:

1. `patrol_route_or_geography` must not treat `split` plus `evidence` as a route when the sentence is the authorized yoke observation.
2. `caused this` inside `remains uncertain what exactly caused` must not outvote an already authorized unknown-cause reading of that same sentence.

Expected player value is the difference between P1's Q1 fallback and a playable interpretation answer, at low runtime cost, with the risk bounded to those patterns. Prove it on the saved sentences and the existing semantic matrix. Leave the closed complement list and the deferred certainty vocabulary alone unless a fixture requires them.

**Following slice, after that fix is green: first-pass realization competence.**

Use the preserved generations as the root-cause corpus. P1 still attaches duration and an external event to a licensed hedge. P2 still emits `realize` / `authored_world_fact` / `established` for a social refusal with a null `source_claim_id`. That is a declaration-anchoring and complement-discipline problem. It is not another provider-dedup pass, and it should not start with a new stochastic live gate.

## Evidence index

`artifacts/pr_bu_pr_bt_final_repaired_chain_micro_live/evidence/`

| Item | Path |
| --- | --- |
| P1 contract, decision, recipe | `P1/resolution_contract.json`, `P1/gm_resolution_decision.json`, `P1/decision_facing_answer_recipe.json` |
| P1 provider requests | `P1/provider_request_attempt_generation_1.json`, `P1/provider_request_attempt_generation_2.json` |
| P1 raw generations | `P1/raw_generation_attempt_1.json`, `P1/raw_generation_attempt_2.json` |
| P1 validation, C18, state | `P1/validation.json`, `P1/c18.json`, `P1/state_before.json`, `P1/state_after.json` |
| P2 same set | `P2/` |
| P3 same set | `P3/` |
| Call log | `model_calls.json`, `completed.json` |

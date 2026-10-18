# PR-BT Provider Deduplication Micro-Live Validation

Date: 2026-10-05.

MODE: MICRO LIVE.

MODEL/API CALLS: YES.

No prompt edit. No validator change. No context optimization. No repair between probes. No commit. No push.

## A. Executive result

No. Removing about 13% of the initial provider input did not preserve the first-pass GM competence established by PR-BS.

Three semantic probes ran on the same chapel and baker fixtures. One was accepted on the first generation. Two were rejected, retried by the production path, rejected again, and emitted as safe observation restatements. The player did not receive an interpretation on P1 or a hypothesis answer on P3.

Initial calls were cheaper. Complete turns were not. Gameplay input tokens rose from 78,236 in PR-BS to 114,489 here, because two retries cost more than the per-call savings.

Decision: **C — RETRY COST ERASES THE SAVINGS.**

Architecture status: **A — PR-BR REMAINS CLOSED.** Accepted, sealed, and emitted text matched on every probe. Rejected narration did not enter scene facts. The player hypothesis stayed a hypothesis. Validator ownership still rejected unauthorized narration.

## B. Baseline

PR-BS micro-live, 2026-10-04, model `gpt-4.1-mini-2025-04-14`.

| Metric | PR-BS |
| --- | --- |
| Semantic probes | 3 |
| First-pass acceptance | 3/3 |
| Useful first-pass response | 3/3 |
| Retry rate | 0/3 |
| Initial quality | Q3 3, Q2 0, Q1 0, Q0 0 |
| Final quality | Q3 3, Q2 0, Q1 0, Q0 0 |
| Authority integrity | held |
| C18 | held |

PR-BS gameplay generation input tokens:

| Probe | Input tokens | Output tokens | Total | Provider request chars |
| --- | ---: | ---: | ---: | ---: |
| P1 | 25,208 | 340 | 25,548 | 110,450 |
| P2 | 27,795 | 309 | 28,104 | 121,438 |
| P3 | 25,233 | 400 | 25,633 | 110,665 |

Average initial input: 26,078.67 tokens. Gameplay totals: input 78,236, output 1,049, total 79,285.

The offline character table in the PR-BT implementation notes (97,260 / 109,853 / 99,200) is a different serialization from this harness. Token comparison below uses the Responses API `usage` object. Character comparison uses the same request serialization as the PR-BS harness.

## C. P1 analysis

Bounded interpretation. Fresh chapel belfry. Authored visible facts only: the wooden yoke is split, and the leather hanger is torn. No authored cause, actor, time, or history.

Player:

> I examine the split wooden yoke and the torn leather hanger closely. What does this damage suggest?

Contract `rc_3f400a77512d`: operation `inspect`, dimension `interpretation`, subject `chapel bell`, epistemic mode `unknown_allowed`, expected resolution `answer`.

The live recipe matched the provider copy (`projection_only: true`, owner `gm_resolution_decision`). Inference allowed, scope `qualified_possibilities_only`, modality `possible`. Strategy: one qualified possibility grounded in the observations, using could, may, or might. Unresolved: cause, actor, time, history. Authorized realization claims were the two visible facts, `rc_db5ec0aa65c3` and `rc_b31ecb1fd1c7`.

Initial generation. Model `gpt-4.1-mini-2025-04-14`. Response id `resp_0d3771c2459ffc4c006ac37c89a49c87d29e1df4d769fb5053`. Input 21,849 tokens. Output 464. Total 22,313. Request chars 93,859. Latency 4.567s. No retry context.

Narration:

> The bell's wooden yoke is split, and its leather hanger is torn. This damage could suggest that the bell has endured significant stress, possibly from frequent ringing or exposure to the elements, leading to wear and weakening of its support structure.

Declared claim `inferred_damage_cause_001`, mode `propose`, provenance `gm_inference`, status `inferred`, modality `possible`, premises `rc_db5ec0aa65c3` and `rc_b31ecb1fd1c7`:

> The split wooden yoke and torn leather hanger might indicate wear over time or strain from heavy use or poor maintenance.

An incidental proposal, not accepted into state, added dampness and neglect.

Exact validation, attempt 1:

- reasons: `unauthorized_resolution_decision_fact`
- declaration validation `hard_valid: true`, reason `accepted_bounded_declared_inference`, authority `inference`, persistence `do_not_persist`
- narration validation `hard_valid: false`
- the interpretive sentence was stored both as `unsupported_narrator_lead` (unauthorized, `do_not_persist`) and as `authorized_qualified_inference`
- the lead row won. Audit `hard_valid: false`

The sentence hedges, and it also supplies unsupported history (frequent ringing, wear over time), harsh conditions (exposure to the elements), neglect (poor maintenance), and unseen structural weakening. That is not a bounded possibility tied only to the split yoke and torn hanger.

Production retry was invoked. Feedback told the model the attempt narrated consequential facts outside the pre-narration decision, not to repeat the rejected prose, and to answer again from established facts, bounded incidental detail, or qualified NPC belief. Authoritative retry context was present.

Retry generation. Response id `resp_0f8370842d6fc02a006ac37c8e8da487d2bcdfc87a15d256b3`. Input 23,201 tokens. Output 313. Total 23,514. Request chars 99,745. Latency 3.036s.

Narration:

> The bell's wooden yoke is split, and its leather hanger is torn. Given these visible signs, it might be possible that the bell has been under considerable strain, but the exact cause or history of this damage is not clear from observation alone.

`declared_claims` was empty. The strain sentence is a cleaner qualified reading than the first attempt. It still failed.

Exact validation, attempt 2:

- reasons: `unauthorized_resolution_decision_fact`
- declaration validation `hard_valid: true` with no accepted inference
- narration validation `hard_valid: false`, reason `unsupported_narrator_lead`
- the same sentence also carried `authorized_qualified_inference`
- the lead row won again

The retry wording does not match the unknown-slot exemption the validator uses for phrases such as "remains unclear". "is not clear" does not take that path. "the exact cause" is an ungrounded definite, so the narrator-lead check fails the sentence before the qualified-inference row can carry it.

Final accepted, sealed, and emitted text, provenance `safe_nonresolution`, attempt 2, why `authorized_observation`:

> The bell's wooden yoke is split. The bell's leather hanger is torn.

C18 exact. `mutation_blocked: false`. `temporal_provenance_commit.sealed_text` equals `accepted_response.text` and `player_facing_text`.

The player was not told what the damage can suggest. Both interpretive sentences are in `rejected_consequential` as unauthorized unresolved gameplay leads. They are not in visible facts. `gm_inferences` stayed empty.

Initial quality Q0. Final quality Q1. Useful first-pass: no. Authority violation attempted: yes. It did not enter scene state.

## D. P2 analysis

Mundane NPC conversation. Fresh bread stall. One baker. Visible fact: a baker stands beside loaves. No authored loaf preference.

Player:

> Baker, which loaf do you usually keep for yourself?

Contract `rc_d4c97cad4722`: operation `ask`, interlocutor `baker`, subject `baker`, epistemic mode `unknown_allowed`, expected resolution `answer`. Route: `strict_social`, family `high_precision`, model `gpt-4.1-mini`. One generation. The route log marks that family as escalated; there was no second call.

The live recipe matched the provider copy. Inference allowed: false. Modality: `none`. Strategy: ordinary dialogue as a direct answer, refusal, hesitation, or an admission of not knowing. Forbidden: a durable preference without an authorized claim, and generated dialogue marked as authored world fact.

Initial generation, also the accepted response. Response id `resp_0d090b0344f1c6be006ac37c92037487d285461301893a1531`. Input 24,431 tokens. Output 458. Total 24,889. Request chars 104,777. Latency 5.367s.

> The baker glances around the busy stall, then replies with a guarded tone, "I don't have a particular loaf I keep for myself. Every batch here is for the customers."

The model also declared a realize against `rc_2bb408577206` ("Baker exists"), provenance requested `authored_world_fact`:

> The baker shakes their head slightly, unwilling to say which loaf they keep for themselves.

Exact validation, attempt 1:

- reasons: `[]`
- audit `hard_valid: true`, violations `[]`
- declaration validation `hard_valid: true`, reason `accepted_declared_realization`
- the accepted declaration identity is `relation: exists`, `value: present`, `source_ref: world.npcs.0`, provenance `authored_world_fact`, authority `world_truth`
- narration validation `hard_valid: true`, `violations: []`, `proposed_facts: []`, `claim_results: []`
- acceptance why: `initial_hard_valid`
- attempt 2: absent
- regeneration feedback: absent

The audit shows the generated head-shake as the realization text of the pre-existing baker-exists claim. NPC records, visible facts, topics, and temporal provenance did not gain a loaf preference, a stall policy, or the head-shake as a new fact. Spoken narration was not written as an NPC claim row.

C18 exact. Provenance `initial_generation`, attempt 1.

The player hears a person refuse. No loaf is named. The reply is plainer than the PR-BS refusal, and it is still ordinary speech.

Initial quality Q3. Final quality Q3. Useful first-pass: yes. First-pass accepted: yes.

## E. P3 analysis

Player hypothesis. A second fresh chapel belfry with the same authored damage. Probe 1 state was not carried forward.

Player:

> Looking at the split wooden yoke and the torn leather hanger, maybe someone cut it deliberately. Does that fit what I'm seeing?

Contract `rc_a6f3b923e680`: operation `perceive`, subject `chapel bell`, epistemic mode `unknown_allowed`, expected resolution `answer`.

The live recipe matched the provider copy. Because the contract was `perceive`, inference allowed is false, modality is `none`, and the strategy is realizing the required claims. The same projection shape accepted a conditional answer in PR-BS. Authorized realization claims were again the two visible facts.

Initial generation. Response id `resp_09df4373639cd1f4006ac37c97da2c87d2b61534af4947387b`. Input 21,874 tokens. Output 410. Total 22,284. Request chars 94,074. Latency 3.673s.

Narration:

> The bell's wooden yoke is indeed split, and its leather hanger is torn. These damages are clearly visible, though whether they were caused deliberately remains uncertain from appearance alone.

Declared claims realized the two authored observations only, both `authored_world_fact` / `established`.

The English recognizes deliberate cutting and leaves it conditional. It does not name an actor, motive, time, or tool marks. It also uses "clearly".

Exact validation, attempt 1:

- reasons: `unauthorized_resolution_decision_fact`
- the two observation declarations were `accepted_declared_realization`
- narration validation `hard_valid: false`
- the uncertainty sentence was `unauthorized_certainty_upgrade`, provenance `generated_proposal`, authority `unauthorized`, persistence `do_not_persist`
- the rejected row's semantic identity carries `epistemic_status: established` because that is how the certainty-upgrade claim is labeled. The stored temporal row is `epistemic_status: unresolved`, authority `unauthorized`

`_CERTAINTY_UPGRADE_RE` matches the word "clearly". PR-BS used "uncertain from the visible evidence alone" and did not use "clearly", and that sentence was accepted.

Production retry was invoked with the same class of feedback as P1: do not repeat the rejected prose; stay with established facts.

Retry generation. Response id `resp_071f280967b6f805006ac37c9bb53487d29b24aabd38eec342`. Input 23,134 tokens. Output 297. Total 23,431. Request chars 99,512. Latency 5.024s.

> The bronze bell's wooden yoke is split, and its leather hanger is torn. While these damages are clearly visible, whether they were caused deliberately is not something that can be determined from the appearance alone.

`declared_claims` was empty. The sentence still contains "clearly". An incidental proposal mentioned neglect and old smoke. It was not accepted into state.

Exact validation, attempt 2:

- reasons: `unauthorized_resolution_decision_fact`
- narration validation `hard_valid: false`, reason `unauthorized_certainty_upgrade`
- declaration validation `hard_valid: true` with no new accepted claim

Final accepted, sealed, and emitted text, provenance `safe_nonresolution`, attempt 2, why `authorized_observation`:

> The bell's wooden yoke is split. The bell's leather hanger is torn.

C18 exact. `mutation_blocked: false`.

The player was not told whether deliberate cutting fits the damage. Visible facts stayed the original two sentences. The player line is stored as `player_hypothesis` with `epistemic_status: hypothesis`, authority `observation`, provenance `player_hypothesis`. Discourse focus `active_claim` uses that same hypothesis status. `gm_inferences` stayed empty. Both rejected sentences are in `rejected_consequential` as unauthorized, not as world truth.

Initial quality Q0, because the generation is an invalid certainty upgrade even though the surrounding English is close to a useful answer. Final quality Q1. Useful first-pass: no. The request was not answered.

## F. First-pass scorecard

| Probe | First pass | Useful first pass | Retry | Request answered | Authority violation attempted | Initial Q | Final Q |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1 bounded interpretation | NO | NO | YES | NO | YES | Q0 | Q1 |
| P2 mundane baker | YES | YES | NO | YES | NO | Q3 | Q3 |
| P3 player hypothesis | NO | NO | YES | NO | YES | Q0 | Q1 |

Rates:

- First-pass acceptance: 1/3.
- Useful first-pass response: 1/3.
- Retry rate: 2/3.

P2's declaration text was a generated mannerism shown against the existing baker-exists identity. That did not create a new durable fact, so the authority-attempt column stays NO. The mismatch is recorded in section J.

"Request answered" is the final emitted response.

## G. Quality scorecard

Initial generations:

| Q | Count |
| --- | ---: |
| Q3 | 1 |
| Q2 | 0 |
| Q1 | 0 |
| Q0 | 2 |

Final accepted responses:

| Q | Count |
| --- | ---: |
| Q3 | 1 |
| Q2 | 0 |
| Q1 | 2 |
| Q0 | 0 |

PR-BS was 3 initial Q3 and 3 final Q3. This sample is 1 initial Q3 and 2 final Q1.

## H. Token scorecard

Provider usage is the Responses API `usage` object. Gameplay model `gpt-4.1-mini-2025-04-14`.

| Call | Kind | Input tokens | Output tokens | Total | Request chars | Latency |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Preflight | preflight | 24 | 2 | 26 | 134 | 4.097s |
| P1 generation | initial | 21,849 | 464 | 22,313 | 93,859 | 4.567s |
| P1 generation | retry | 23,201 | 313 | 23,514 | 99,745 | 3.036s |
| P2 generation | initial | 24,431 | 458 | 24,889 | 104,777 | 5.367s |
| P3 generation | initial | 21,874 | 410 | 22,284 | 94,074 | 3.673s |
| P3 generation | retry | 23,134 | 297 | 23,431 | 99,512 | 5.024s |

Initial-call comparison to PR-BS:

| Probe | PR-BS input | PR-BT initial input | Absolute reduction | Percent reduction |
| --- | ---: | ---: | ---: | ---: |
| P1 | 25,208 | 21,849 | 3,359 | 13.33% |
| P2 | 27,795 | 24,431 | 3,364 | 12.10% |
| P3 | 25,233 | 21,874 | 3,359 | 13.31% |

Average initial input: PR-BS 26,078.67, PR-BT 22,718. Average reduction 3,360.67 tokens, 12.89%.

Complete player turn, including a production retry when one occurred:

| Probe | PR-BS input | PR-BT turn input | PR-BT turn output | PR-BT turn total | Input change |
| --- | ---: | ---: | ---: | ---: | ---: |
| P1 | 25,208 | 45,050 | 777 | 45,827 | +19,842 / +78.71% |
| P2 | 27,795 | 24,431 | 458 | 24,889 | -3,364 / -12.10% |
| P3 | 25,233 | 45,008 | 707 | 45,715 | +19,775 / +78.37% |

Gameplay totals:

| | Input | Output | Total |
| --- | ---: | ---: | ---: |
| PR-BS, 3 initial calls | 78,236 | 1,049 | 79,285 |
| PR-BT, 3 initial calls plus 2 retries | 114,489 | 1,942 | 116,431 |
| Difference | +36,253 | +893 | +37,146 |

That is a 46.34% increase in gameplay input tokens.

All measured calls, including the one preflight: input 114,513, output 1,944, total 116,457.

Live request characters versus the PR-BS harness:

| Probe | PR-BS chars | PR-BT initial chars | Reduction |
| --- | ---: | ---: | ---: |
| P1 | 110,450 | 93,859 | 16,591 / 15.02% |
| P2 | 121,438 | 104,777 | 16,661 / 13.72% |
| P3 | 110,665 | 94,074 | 16,591 / 14.99% |

Model API calls executed: 6. Initial gameplay calls: 3. Production retries: 2. Interpretation calls: 0. Infrastructure reruns: 0.

Response ids are in `artifacts/pr_bt_provider_deduplication_micro_live/evidence/model_calls.json`.

## I. Retry impact

Two production retries. No manual retry.

P1 and P3 each spent a second generation. Both second generations were also hard-invalid. Both turns then emitted the observation-only safe nonresolution.

Token effect: the two retries added 23,201 and 23,134 input tokens. Together they are larger than the 10,082 input tokens saved across the three initial calls (3,359 + 3,364 + 3,359).

Quality effect: P1's retry was a cleaner strain reading and still failed as `unsupported_narrator_lead`. P3's retry repeated "clearly" and still failed as `unauthorized_certainty_upgrade`. Neither retry restored a useful answer. Final quality on those probes is Q1.

## J. Authority integrity

Held for this gate. No stop.

| Check | Result |
| --- | --- |
| Rejected consequential narration entered visible facts | No. P1 and P3 sentences are in `rejected_consequential` with authority `unauthorized` |
| Player hypothesis became world truth | No. P3 remains `epistemic_status: hypothesis` |
| Incidental NPC speech became a new durable fact | No. Baker NPC, topics, and visible facts are unchanged. No loaf preference was stored |
| Unsupported inference became authoritative scene state | No. `gm_inferences` is empty on all three probes. P1's bounded declaration was not persisted after the narration rejection |
| Rejected declarations preserved as scene truth | No |
| Provenance changed improperly in world state | No new authored fact was written |
| Recipe became authority | No. Recipes stay `projection_only` with owner `gm_resolution_decision` |
| Provider deduplication changed validator ownership | No. The same narration validator rejected P1 and P3 |

P2 note, not a stop: the declaration audit displays the generated head-shake as the text of the pre-existing baker-exists realization (`source_ref: world.npcs.0`, relation `exists`). Narration `claim_results` is empty. The NPC record did not change.

P1 and P3 rejected rows did not promote. P3's certainty-upgrade identity says `established` inside the rejection record; the temporal copy is `unresolved` and `unauthorized`.

## K. C18

Held. Exact string equality. `mutation_blocked: false` on every probe.

| Probe | accepted == sealed == emitted | Provenance | Attempt |
| --- | --- | --- | --- |
| P1 | YES | `safe_nonresolution` | 2 |
| P2 | YES | `initial_generation` | 1 |
| P3 | YES | `safe_nonresolution` | 2 |

Sealed text is `metadata.emission_debug.temporal_provenance_commit.sealed_text`. It matches `metadata.accepted_response.text` and `player_facing_text` on each probe.

## L. State mutation review

Each probe advanced the default faction clock by 1 pressure and 1 agenda progress for `house_verevin`, `ash_cowl`, and `ordo_pyric`. That is the existing world simulation tick. It is not realization leakage.

Scene visible facts, hidden facts, clues, summaries, exits, and NPC records were unchanged on all three probes.

Turn counter moved from 1 to 2. Discourse focus recorded the inspected bell or the baker interlocutor, and on P3 the player hypothesis as the active claim. Those are contract bookkeeping and hypothesis storage, not new world truth.

No unauthorized realization-derived state mutation was found.

## M. Quality-per-runtime-cost assessment

The optimization was not worthwhile on this sample.

Initial requests are smaller by about 3,361 input tokens each, about 12.89% versus PR-BS. That part of the measurement is real.

The turns the deduplication was supposed to protect got worse. P1 and P3 no longer answer on the first pass. Their retries also fail. The player receives a bare restatement. Those two turns cost about 78% more input tokens than the PR-BS turns that answered at Q3.

P2 preserved a useful first-pass refusal and spent fewer tokens. One preserved social turn does not offset two failed interpretation turns.

A smaller initial prompt is not a gain when the complete turn costs more and the answer is less useful.

## N. Architecture status

**A — PR-BR REMAINS CLOSED.**

C18 held. Rejected material stayed rejected. The hypothesis stayed a hypothesis. No structured-boundary bypass and no accepted/sealed/emitted divergence appeared. The failures are first-pass realization quality and retry recovery, not a new architectural contradiction.

## O. Recommended next step

**C — RETRY COST ERASES THE SAVINGS.**

Do not continue canonicalization from this sample. Do not repair prompts or validators inside this block.

The semantic gap to investigate, before any further deletion or any broad restore:

1. P3. Both generations say "clearly". The narration validator treats that word as `unauthorized_certainty_upgrade`. The conditional hypothesis sentence is discarded, and the fallback restates only the two observations. PR-BS answered this probe without that word.
2. P1. The interpretive sentence is hard-failed as `unsupported_narrator_lead` when it misses the unknown-slot exemption ("remains unclear") and carries an ungrounded definite ("the elements", "the exact cause"). A parallel `authorized_qualified_inference` row does not save the turn. The first narration also added ringing, weather, structural weakening, and, in the declaration, poor maintenance.
3. Retry feedback forbids repeating the rejected sentence and points the model at established facts. The second call therefore does not recover a qualified answer. It spends another full provider request and still falls through to safe nonresolution.

The next block should identify whether the removed policy lines were what kept realization wording inside those validator exemptions. That comparison is the repair candidate. It was not done here.

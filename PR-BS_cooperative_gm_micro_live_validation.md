# PR-BS Cooperative GM Micro-Live Validation

Date: 2026-10-04.

MODE: MICRO LIVE.

MODEL/API CALLS: YES.

No production repair. No commit. No push.

## A. Executive result

Yes. The Decision-Facing Answer Recipe improved real first-pass GM cooperation enough to keep this implementation direction.

Three semantic probes, one initial generation each, all passed validation and answered the player. First-pass acceptance was 3/3. Useful first-pass responses were 3/3. Retry rate was 0/3. The PR-BR closeout baseline on four gameplay turns was 0/4 first-pass and a 100% retry rate. This sample is too small to prove production readiness or a general improvement. It is large enough to keep the recipe.

Decision: **A — PR-BS COOPERATIVE-GM SLICE SUCCEEDS.**

Architecture status: **A — PR-BR REMAINS CLOSED.** Accepted, sealed, and emitted text matched on every probe. Scene facts, NPC records, and epistemic ceilings held.

## B. Scorecard

| Probe | First Pass | Retry | Initial Quality | Final Quality | Useful | Integrity |
| ----- | ---------- | ----- | --------------- | ------------- | ------ | --------- |
| P1 bounded interpretation | YES | NO | Q3 | Q3 | YES | PASS |
| P2 mundane baker | YES | NO | Q3 | Q3 | YES | PASS |
| P3 player hypothesis | YES | NO | Q3 | Q3 | YES | PASS |

Quality distribution: Q3 = 3, Q2 = 0, Q1 = 0, Q0 = 0.

Rates:

- First-pass acceptance: 3/3.
- Useful first-pass response: 3/3.
- Retry rate: 0/3.

Final quality equals initial quality because no probe retried.

## C. Probe 1 analysis

Bounded interpretation. Fresh chapel belfry. Authored visible facts only: the wooden yoke is split, and the leather hanger is torn. No authored cause, actor, time, or history.

Player:

> I examine the split wooden yoke and the torn leather hanger closely. What does this damage suggest?

Contract `rc_3f400a77512d`: operation `inspect`, dimension `interpretation`, subject `chapel bell`, epistemic mode `unknown_allowed`, expected resolution `answer`.

The live recipe matched the decision projection sent to the provider (`projection_only: true`, owner `gm_resolution_decision`). Requested answer named the interpretation and the player question. Inference was allowed at scope `qualified_possibilities_only`, modality `possible`. Strategy: one qualified possibility grounded in the observations, using could, may, or might. Unresolved: cause, actor, time, history.

Initial generation, also the accepted response. Model `gpt-4.1-mini-2025-04-14`. Response id `resp_0e3515bb92c7b806006ac2f53489b887d1b6007b772ba27ed1`.

> The bronze bell's wooden yoke is split, and its leather hanger torn. This damage could suggest gradual wear from frequent use or recent stress that strained these components, though exactly when or how this happened remains unclear.

Declared claim `dc1`, mode `propose`, provenance `gm_inference`, status `inferred`, modality `possible`, premises `rc_db5ec0aa65c3` and `rc_b31ecb1fd1c7`:

> The split wooden yoke and torn leather hanger could indicate gradual wear or recent damage under strain.

Exact validation, attempt 1:

- `decision_review.attempt_1.reasons`: `[]`
- `gm_resolution_decision_audit.hard_valid`: `true`
- `gm_resolution_decision_audit.violations`: `[]`
- declaration validation `hard_valid: true`, `rejected_claims: []`, `violations: []`, reason `accepted_bounded_declared_inference`, persistence `do_not_persist`
- narration validation `hard_valid: true`, `violations: []`, reason `authorized_qualified_inference`, authority `observation`, status `inferred`, persistence `do_not_persist`
- acceptance why: `initial_hard_valid`
- attempt 2: absent
- regeneration feedback: absent

C18: accepted, sealed, and emitted are the same string. `mutation_blocked: false`. Provenance `initial_generation`, attempt 1.

The sentence answers the interpretation with a qualified possibility and leaves when and how unresolved. It does not name an actor, neglect, harsh conditions, a safety status, unseen damage, or a gameplay lead.

## D. Probe 2 analysis

Mundane NPC conversation. Fresh bread stall. One baker. Visible fact: a baker stands beside loaves. No authored loaf preference.

Player:

> Baker, which loaf do you usually keep for yourself?

Contract `rc_d4c97cad4722`: operation `ask`, interlocutor `baker`, subject `baker`, epistemic mode `unknown_allowed`, expected resolution `answer`. Route: `strict_social`, family `high_precision`, still `gpt-4.1-mini`.

The live recipe matched the provider copy. Inference allowed: false. Modality: `none`. Strategy: ordinary dialogue as a direct answer, refusal, hesitation, or an admission of not knowing. Forbidden: a durable preference without an authorized claim, and generated dialogue marked as authored world fact.

Initial generation, also the accepted response. Response id `resp_0d56eec6c891beee006ac2f56ddd5087d195dcf4a4a63864cb`.

> "Ah, that's a bit of a secret I keep close to the vest," the baker says, glancing away briefly before meeting your eyes again. "I prefer not to say which loaf I keep for myself—it just wouldn't feel right to share that."

`declared_claims`: `[]`.

The envelope also carried an unpersisted improvisation proposal, category `mannerism`, consequence `none`, epistemic status `known`:

> The baker shifts uneasily, glancing at the loaves while carefully guarding the secret of their favorite bread.

Exact validation, attempt 1:

- `decision_review.attempt_1.reasons`: `[]`
- audit `hard_valid: true`, `violations: []`
- declaration validation `hard_valid: true`, `accepted_claims: []`, `rejected_claims: []`, `violations: []`
- narration validation `hard_valid: true`, `violations: []`
- the two spoken sentences were audited as `npc_claim`, authority `claim_only`, persistence `claim_only`, reason `epistemically_qualified`
- those rows also carry `epistemic_status: world_truth` on the claim identity
- acceptance why: `initial_hard_valid`
- attempt 2: absent

C18 exact. Provenance `initial_generation`.

The player hears a refusal with a glance. No loaf is named. NPC records and visible facts were unchanged after the turn. Temporal buckets `gm_inferences`, `player_hypotheses`, `accepted_incidentals`, and `rejected_consequential` stayed empty. The `world_truth` label stayed inside the claim-only audit row and was not written as a scene fact or a durable preference.

## E. Probe 3 analysis

Player hypothesis. A second fresh chapel belfry with the same authored damage. Probe 1 state was not carried forward.

Player:

> Looking at the split wooden yoke and the torn leather hanger, maybe someone cut it deliberately. Does that fit what I'm seeing?

Contract `rc_a6f3b923e680`: operation `perceive`, subject `chapel bell`, epistemic mode `unknown_allowed`, expected resolution `answer`.

The live recipe matched the provider copy. Because the contract was `perceive`, the recipe set inference allowed to false, modality `none`, and the strategy to realizing the required claims. It did not add a hypothesis-preservation instruction. The recipe remained a projection of that decision.

Initial generation, also the accepted response. Response id `resp_0fe58001a890a1d8006ac2f571a6d487d1afac060d69a052e8`.

> The bell's wooden yoke is indeed split, and its leather hanger torn. However, whether these damages were caused deliberately is uncertain from the visible evidence alone.

Declared claims realized the two authored observations only:

- `The bell's wooden yoke is split.` Provenance `authored_world_fact`, status `established`, source `scene.visible_facts.0`.
- `The bell's leather hanger is torn.` Provenance `authored_world_fact`, status `established`, source `scene.visible_facts.1`.

Exact validation, attempt 1:

- `decision_review.attempt_1.reasons`: `[]`
- audit `hard_valid: true`, `violations: []`
- declaration validation `hard_valid: true`, `rejected_claims: []`, `violations: []`, reasons `accepted_declared_realization`
- narration validation `hard_valid: true`, `violations: []`, `proposed_facts: []`, `claim_results: []`
- acceptance why: `initial_hard_valid`
- attempt 2: absent

C18 exact. Provenance `initial_generation`.

The reply recognizes deliberate cutting and leaves it uncertain. It does not name an actor. Visible facts after the turn were still the original two sentences. The player line was stored as `player_hypothesis` with `epistemic_status: hypothesis`, authority `observation`, provenance `player_hypothesis`. Discourse focus `active_claim` uses that same hypothesis status. `gm_inferences` and `rejected_consequential` stayed empty.

## F. Runtime cost

Provider usage is the Responses API `usage` object. Model for gameplay: `gpt-4.1-mini-2025-04-14`.

| Call | Kind | Input tokens | Output tokens | Total | Input chars | Latency |
| ---- | ---- | -----------: | ------------: | ----: | ----------: | ------: |
| P1 generation | initial | 25,208 | 340 | 25,548 | 110,450 | 4.525s |
| P2 generation | initial | 27,795 | 309 | 28,104 | 121,438 | 3.280s |
| P3 generation | initial | 25,233 | 400 | 25,633 | 110,665 | 3.814s |
| Continuation preflight | preflight | 24 | 2 | 26 | 134 | 2.080s |

Gameplay generation totals: input 78,236, output 1,049, total 79,285.

Mean tokens per gameplay turn: input 26,078.67, output 349.67, total 26,428.33.

Measured calls including the retained preflight: input 78,260, output 1,051, total 79,311.

A startup preflight also ran in the first process and returned healthy at `2026-10-05T00:54:09Z`. The continuation overwrote `model_calls.json`, so that first preflight's token usage was not retained and is omitted from the sums.

No interpretation-model call occurred. No retry call occurred.

Model API calls executed: 5 (2 preflights + 3 generations). Gameplay generations: 3. Retries: 0.

PR-BR closeout baseline, directional only: 4 gameplay turns, 4 initial generations, 4 retries, about 238,274 total model tokens, generation input about 25k–33k tokens per call.

These three generation inputs are 25,208, 27,795, and 25,233. They sit at the low end of that 25k–33k band. The earlier 26–27% authority-slice character reduction did not become a 26–27% reduction of the full provider input. Response policy, turn packet, narrative plan, and the system prompt are still in the request.

The cost that moved is the missing retry. Each of these turns spent one generation. The baseline spent an initial generation and a retry on every turn.

## G. Retry behavior

No probe required a retry.

Attempt 2 is absent on all three. `regeneration_invoked` is absent. `regeneration_feedback` is absent. Provider requests do not contain `AUTHORITATIVE RETRY CONTEXT`.

There is no retry feedback to compare, and no second generation that collapsed toward nonresolution.

## H. Integrity

C18, exact string equality, `mutation_blocked: false` on every accepted turn:

| Probe | accepted == sealed == emitted |
| ----- | ------------------------------ |
| P1 | YES |
| P2 | YES |
| P3 | YES |

Authority boundary:

- P1 scene visible facts, hidden facts, and clues were unchanged. The inference was stored in `gm_inferences` as `epistemic_status: inferred`, authority `inference` or `observation`, provenance `gm_inference`. It was not written into visible facts.
- P2 NPC records were unchanged. `declared_claims` was empty. The refusal was audited as `claim_only`. No loaf preference was added to world state.
- P3 realized only the two facts that were already visible. Deliberate cutting was not declared. The player line remained `epistemic_status: hypothesis`.

Provenance:

- P1 added two inferred rows and no rejected-consequential rows.
- P2 added no temporal rows.
- P3 added one player-hypothesis row and no inferred or rejected-consequential rows.

Declaration behavior followed the recipe lanes that the decisions actually granted: P1 `propose` / `gm_inference`; P2 empty declarations; P3 `realize` of the two authored observations.

The first process halted after P1 because every default faction gained `pressure + 1` and `agenda_progress + 1`. That is `game.world._tick_direct_faction_row_advance` on the default world list. The same tick happened on P2 and P3. Scene text, NPC records, and clues did not change with it. It is the ordinary world clock, recorded in `evidence/harness_continuation.json`. P1 was not rerun. P2 and P3 ran once each after that classification.

The P2 audit identity `epistemic_status: world_truth` sits on rows whose authority and persistence are `claim_only`. Those rows were not copied into scene facts or temporal provenance. That label is recorded here and is not treated as a new authority-boundary break.

## I. Product interpretation

Observed residuals, by class:

- GM COMPETENCE. P1's qualified possibility is historically colored: gradual wear, frequent use, or recent stress. The modality stays possible, and the sentence says when and how remain unclear. P2's unused mannerism proposal mentions a favorite bread without naming a loaf. Neither missed the player's question.
- PERFORMANCE. Full generation input remains about 25k–28k tokens. The authority-slice shrink is real and is not the whole prompt. This sample's cost improvement is the absent retry.
- GAME SYSTEM. Probe 3's contract operation was `perceive`, so the recipe correctly withheld an inference lane. The model still answered the hypothesis as uncertain narration, and the existing hypothesis bucket kept the ceiling.
- WORLD SIMULATION. Default faction pressure and agenda advance by one on a turn. That clock is independent of the answer recipe.
- UX. These probes were API turns. No separate interface defect appeared.
- ARCHITECTURAL INTEGRITY. No new contradiction. PR-BR stays closed.

## J. Recommended next action

Close this PR-BS cooperative-GM slice and keep the answer-recipe direction.

One bounded repair is not justified by these three turns. Retry guidance was not exercised. Provider-context canonicalization remains a later performance question, not the result of this sample.

## Run record

Harness: `artifacts/pr_bs_cooperative_gm_micro_live/run_probes.py`.

Evidence: `artifacts/pr_bs_cooperative_gm_micro_live/evidence/`.

Scenes match the PR-BR closeout chapel and bread-stall seeds. Probe 3 used a new chapel session with the same authored damage.

Infrastructure reruns: none. The continuation after the faction-clock halt skipped the already recorded P1 generation and did not call the model again for that probe.

Trace ids:

- P1 contract `rc_3f400a77512d`, response `resp_0e3515bb92c7b806006ac2f53489b887d1b6007b772ba27ed1`
- P2 contract `rc_d4c97cad4722`, response `resp_0d56eec6c891beee006ac2f56ddd5087d195dcf4a4a63864cb`
- P3 contract `rc_a6f3b923e680`, response `resp_0fe58001a890a1d8006ac2f571a6d487d1afac060d69a052e8`
- Continuation preflight `resp_0de9588d94172c3c006ac2f56b527887d1b3be89956d0774e6`

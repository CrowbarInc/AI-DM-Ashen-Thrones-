# PR-BR closeout live revalidation

Date: 2026-10-04. Live model: gpt-4.1-mini. Observation only. Four gameplay turns. No repairs, no reruns, no extra turns, no 4x10, no commit, no push.

Decision: **A. PR-BR CLOSEOUT RECOMMENDED; SYSTEMIC SEMANTIC/AUTHORITY BOUNDARY IS SUFFICIENTLY STABLE. MOVE REMAINING ISSUES TO LATER AI, GAMEPLAY, OR PRODUCT CAMPAIGNS.**

## 1. Executive conclusion

The systemic authority boundary held under real model behavior.

The model repeatedly tried to turn the bell damage into a cause, a history, or a presupposed hard pull. Every one of those structured candidates was rejected. None of them was prose-salvaged. None of them became scene fact, `gm_inference`, or world truth. The player's hard-pull sentence stayed a `player_hypothesis` at status `hypothesis`. The two A3 sentences that said the cause of the hard pull was unknown were rejected with `embedded_premise_unlinked` and were not emitted.

What reached the player was local and bounded: a restatement of the authored yoke and hanger, one authorized observation fallback, an awkward safe non-answer, and a baker's spoken refusal. Those are gameplay and phrasing limits. They do not silently rewrite the world's authoritative reality.

`_bounded_keep` was not invoked on any turn. Sealed text and emitted text matched on all four turns. No raw JSON reached the player.

## 2. Scenario A setup

Fresh isolated storage: `isolated_A/data`. Active scene: `chapel_belfry`. Location: `Chapel belfry`. Summary: `A bronze bell hangs from a timber frame.`

Exactly two authored visible facts:

- `The bell's wooden yoke is split.`
- `The bell's leather hanger is torn.`

Interactable: id `chapel_bell`, label `chapel bell`, aliases `bell`, `wooden yoke`, `yoke`, `leather hanger`, `hanger`. No hidden facts, discoverable clues, exits, enemies, actions, or NPCs. No cause, actor, event time, history, culprit, negative evidence, or consequential lead was authored.

Default campaign, character, combat, conditions, and world scaffolding were loaded. Default factions have no authored connection to the bell. Default scenes `frontier_gate`, `market_quarter`, and `old_milestone` exist only so startup scene validation can resolve. They were not visited. Complete initial slice: `setup_A.json`.

Pre-generation temporal state in this report is taken from the decision files written at contract attachment (`A1_decision_1.json`, `A2_decision_2.json`, `A3_decision_3.json`). Those files are frozen at attachment. The later digest field `temporal_input` can share the session's rejected-claim list and must not be used as the before-generation snapshot.

## 3. Turn A1 full trace

PLAYER INPUT

`I examine the split wooden yoke and the torn leather hanger closely. What does this damage suggest?`

RESOLUTION CONTRACT

Before generation (`A1_decision_1.json`):

- contract `rc_3f400a77512d`
- operation `inspect`
- dimension `interpretation`
- dimensions `["interpretation"]`
- subject `chapel bell`
- epistemic mode `unknown_allowed`
- raw input preserved in full

GM RESOLUTION DECISION

Outcome `established_or_retrieved`. Realization claims are the two authored facts:

- `rc_db5ec0aa65c3` — `The bell's wooden yoke is split.` — `authored_world_fact` / `world_truth` / `established` / `scene.visible_facts.0`
- `rc_b31ecb1fd1c7` — `The bell's leather hanger is torn.` — `authored_world_fact` / `world_truth` / `established` / `scene.visible_facts.1`

Constraint present: qualified possibilities may be inferred from authorized observations; no cause, actor, or history is established.

EPISTEMIC ACTS

1. `establish` on `scene.visible_facts.0`, authority `world_truth`
2. `establish` on `scene.visible_facts.1`, authority `world_truth`
3. `infer`, authority `observation`, status `inferred`, subject `chapel bell`, scope `qualified_possibilities_only`

TEMPORAL INPUT

- `gm_inferences`: empty
- `player_hypotheses`: empty
- `active_claim`: null

RAW STRUCTURED ENVELOPE

Attempt 1 declared one `realize` claim as `authored_world_fact` / `established`: `The bell's wooden yoke is split and its leather hanger is torn, indicating structural failure.` Narration added structural failure, prolonged strain or weakening over time, unsafe-until-repaired, and neglect or recent harsh conditions. An incidental resin-scent proposal was also present.

Attempt 2 declared an empty claim list. Narration: `The bronze bell hangs silently, with its wooden yoke visibly split and the leather hanger torn.`

DECLARED CLAIMS

Attempt 1: one realize declaration, requested authored world fact, established, ordinary predicate, empty `premise_claim_ids`.

Attempt 2: `declared_claims: []`.

DECLARATION AUDIT

Attempt 1 failed `unauthorized_resolution_decision_fact`. Recorded narration violations:

- structural-failure sentence — `unauthorized_evidential_relation`
- neglect / recent harsh conditions — `unsupported_narrator_lead`

Attempt 2: no violations.

NARRATION AUDIT

Final seal: hard valid, `claim_results: []`, `violations: []`. Acceptance `regeneration_hard_valid`. Provenance `regeneration`.

RETRY

One structured retry. The initial consequential envelope was rejected. The retry envelope was accepted.

ACCEPTED REALIZATION CLAIMS

The final seal's claim-result list is empty. The emitted sentences restate the two pre-existing authored facts and add the incidental clause that the bell hangs silently. No new inference claim was accepted.

SEALED TEXT

`The bronze bell hangs silently, with its wooden yoke visibly split and the leather hanger torn.`

EMITTED TEXT

Same string. C18 holds.

TEMPORAL OUTPUT

- `gm_inferences`: empty
- `player_hypotheses`: empty
- `rejected_consequential`: the structural-failure sentence and the neglect/harsh-conditions sentence, both unauthorized
- `active_claim`: null
- inspected object: `chapel_bell`

AUTHORITATIVE SCENE STATE

Visible facts unchanged. Hidden facts empty. Discoverable clues empty. Default faction agenda counters advanced by the ordinary world tick and have no bell content.

AUTHORITY RESULT

Pass. The interpretation request survived. `INFER` with `qualified_possibilities_only` existed before generation. The model's consequential hypothesis was rejected and did not reach prose-only preservation. No unsupported cause, actor, time, history, or negative evidence became fact.

The answer does not use the authorized inference. Usefulness is recorded separately in section 13.

## 4. Turn A2 full trace

PLAYER INPUT

A1 emitted no inference, so this turn uses a fresh player hypothesis grounded in the authored observations:

`So if one hard pull split the yoke and tore the hanger together, what would have caused that pull?`

RESOLUTION CONTRACT

Before generation (`A2_decision_2.json`):

- contract `rc_7c5a5d438871`
- operation `ask`
- dimension null
- dimensions empty
- subject `chapel bell`
- epistemic mode `unknown_allowed`
- the full player sentence is the raw input

The decision catalog before generation contains the two authored facts. It does not yet contain a `player_hypothesis` realization claim. `gm_inferences` is empty. The hard pull is not world truth.

GM RESOLUTION DECISION

Outcome `established_or_retrieved`. Epistemic acts are the two `establish` acts for the authored facts. Realization claims are `rc_db5ec0aa65c3` and `rc_b31ecb1fd1c7` only.

EPISTEMIC ACTS

`establish` / `world_truth` for each authored visible fact. No infer act on this ask.

TEMPORAL INPUT

- `gm_inferences`: empty
- `player_hypotheses`: empty
- `rejected_consequential`: the two A1 rejections only
- `active_claim`: null

RAW STRUCTURED ENVELOPE

Attempt 1 declared a causal realize claim as authored world fact / inferred / possible: `A sudden, forceful pull, such as from improper ringing or an accidental tug, could have caused the split wooden yoke and torn leather hanger.` Narration added improper ringing, strain beyond what the supports could bear, and a denial of gradual wear.

Attempt 2 declared an empty claim list. Narration: `The bell's wooden yoke is clearly split, and the leather hanger is torn, showing they have both suffered damage. However, without further information, it is uncertain what exactly caused such a strong pull to damage both supports simultaneously.`

DECLARED CLAIMS

Attempt 1: one unauthorized causal declaration, empty `premise_claim_ids`.

Attempt 2: `declared_claims: []`.

DECLARATION AUDIT

Attempt 1: `unauthorized_declared_claim` on the sudden-pull declaration.

Attempt 2: `unauthorized_certainty_upgrade` on `The bell's wooden yoke is clearly split, and the leather hanger is torn, showing they have both suffered damage.`

The second sentence of attempt 2 presupposes a strong pull and then marks its cause uncertain. That sentence has no separate violation row. The envelope was already rejected, and the sentence was not sealed.

NARRATION AUDIT

Final seal claim result is the authored yoke sentence only: provenance `authored_world_fact`, authority `world_truth`, status `established`, source `scene.visible_facts.0`, reason `authored_state_source`. Violations empty.

RETRY

One structured retry. Both envelopes failed. `_bounded_keep` was not called.

ACCEPTED REALIZATION CLAIMS

The sealed line is the pre-existing yoke fact, owned by `rc_db5ec0aa65c3` / `scene.visible_facts.0`.

SEALED TEXT

`The bell's wooden yoke is split.`

EMITTED TEXT

Same string. Provenance `safe_nonresolution`. Acceptance `authorized_observation`. C18 holds.

TEMPORAL OUTPUT

- `gm_inferences`: empty
- `player_hypotheses`: the full player sentence, provenance `player_hypothesis`, authority `observation`, status `hypothesis`, source turn 3
- `active_claim`: `claim_f19e96c0fc`, same label, source `player_hypothesis`, status `hypothesis`
- rejected rows add the sudden-pull declaration and the certainty-upgrade sentence
- visible facts unchanged

AUTHORITATIVE SCENE STATE

The two authored facts remain the only visible facts. The hard pull is not among them.

AUTHORITY RESULT

Pass. Player repetition stored the sentence as a hypothesis. It did not become world truth. The causal declaration and the presupposing retry were not emitted. The authorized fallback is one authored observation.

The reply does not give the desired conditional answer. Usefulness is recorded separately.

## 5. Turn A3 full trace

PLAYER INPUT

`Do we actually know that, or is it only a possibility?`

RESOLUTION CONTRACT

Before generation (`A3_decision_3.json`):

- contract `rc_7563d073ab0a`
- operation `ask`
- dimension `confidence`
- subject is the full A2 player sentence
- epistemic mode `npc_claim`
- raw input preserved

GM RESOLUTION DECISION

The active proposition is bound before generation:

- `rc_fec4503616e0` — the A2 sentence — provenance `player_hypothesis` — authority `observation` — status `hypothesis` — source `temporal.player_hypotheses.0` — persistence `do_not_persist`
- `rc_0dac28663693` — unresolved status slot — provenance `speculation` — status `unresolved` — role `MUST_PRESERVE_UNCERTAINTY` — `premise_claim_ids: ["rc_fec4503616e0"]`

The premise named by that link is the hypothesis row, status `hypothesis`.

EPISTEMIC ACTS

1. `establish` for each authored fact
2. `infer` on `temporal.player_hypotheses.0`, authority `observation`, status `hypothesis`
3. `leave_unresolved`, scope `status_answer`

Constraint present: an unresolved cause, actor, time, reason, or status does not establish its premise. A hypothetical or player-stated premise may be realized only conditionally.

TEMPORAL INPUT

- `gm_inferences`: empty
- `player_hypotheses`: the A2 sentence at status `hypothesis`
- `active_claim`: `claim_f19e96c0fc`, source `player_hypothesis`, status `hypothesis`

RAW STRUCTURED ENVELOPE

Attempt 1 declared the two authored facts, then proposed: `The damage to the bell's wooden yoke and leather hanger suggests a significant, sudden force such as a hard pull, but the exact cause remains unknown.` Its premise ids pointed at the two fact declarations, not at `rc_fec4503616e0`. Narration asserted structural failure, a powerful abrupt force, an uncertain source, and a further-inspection lead.

Attempt 2 declared the two facts, then proposed with empty premise ids: `What caused the hard pull that split the yoke and tore the hanger is not known from the evidence present.` Narration said a forceful pull strong enough to break the supports remains unknown.

DECLARED CLAIMS

Attempt 1 hypothesis declaration: mode `propose`, requested `player_hypothesis`, status `hypothesis`, premise ids are the sibling fact declaration ids.

Attempt 2 unresolved declaration: mode `propose`, modality `unresolved`, premise ids empty.

DECLARATION AUDIT

Both failed `unauthorized_resolution_decision_fact`.

- Attempt 1 proposal: `embedded_premise_unlinked`
- Attempt 2 proposal: `embedded_premise_unlinked`

NARRATION AUDIT

Final seal has two claim results and zero violations. Acceptance `safe_nonresolution`. Provenance `safe_nonresolution`.

1. The player-question text. Provenance `speculation`. Authority `observation`. Status `unresolved`. Persistence `do_not_persist`. Reason `interrogative_not_assertion`.
2. Fragment `says, "I cannot answer that from what is settled here.` Provenance `npc_claim`. Authority `claim_only`. Epistemic status `world_truth`. Persistence `claim_only`. Reason `epistemically_qualified`.

RETRY

One structured retry. Both envelopes failed. `_bounded_keep` was not called. Exact fallback text is the sealed line below.

ACCEPTED REALIZATION CLAIMS

The two seal rows above. The hard-pull occurrence is not one of them.

SEALED TEXT

`So if one hard pull split the yoke and tore the hanger together, what would have caused that pull? says, "I cannot answer that from what is settled here."`

EMITTED TEXT

Same string. C18 holds.

TEMPORAL OUTPUT

- `gm_inferences`: empty
- `player_hypotheses`: still the one A2 row, provenance `player_hypothesis`, status `hypothesis`
- rejected rows add both `embedded_premise_unlinked` sentences
- `active_claim` id remains `claim_f19e96c0fc` with the same label; source is now `speculation` and status is now `unresolved`
- visible facts unchanged

AUTHORITATIVE SCENE STATE

The yoke and hanger facts are unchanged. The hard pull is absent from visible facts, hidden facts, and clues.

AUTHORITY RESULT

Pass on the systemic boundary. The proposition was bound before generation as `player_hypothesis` at status `hypothesis`, with the unresolved slot linked to `rc_fec4503616e0`. Both model attempts to treat the hard pull as a real event whose cause is unknown were rejected and not emitted. The stored hypothesis ceiling stayed `hypothesis`. Scene truth did not change.

The player-facing line does not directly say whether the pull is known or only possible. The fallback template speaks the hypothesis sentence as if it were a person. The seal's second row labels that template fragment `world_truth` while authority and persistence stay `claim_only`, and that fragment is not written into the scene or the hypothesis bucket. Those are local discourse and audit-label defects, classified in section 14.

## 6. Temporal authority table

| Proposition | Source | Status | gm_inference | player_hypothesis | world truth | active_claim | promoted? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| After A1: wooden yoke is split | `scene.visible_facts.0` / `rc_db5ec0aa65c3` | established | No | No | Yes, pre-existing | None | No |
| After A1: leather hanger is torn | `scene.visible_facts.1` / `rc_b31ecb1fd1c7` | established | No | No | Yes, pre-existing | None | No |
| After A1: structural failure, prolonged strain, neglect, harsh conditions | Rejected generated proposals | unauthorized | No | No | No | None | No |
| After A2: one hard pull split the yoke and tore the hanger | Player conditional question | hypothesis | No | Yes, full question, source turn 3 | No | `claim_f19e96c0fc`, source `player_hypothesis`, status `hypothesis` | No |
| After A2: sudden forceful pull / improper ringing | Rejected declaration | unauthorized | No | No | No | None | No |
| After A3: one hard pull split the yoke and tore the hanger | Same player sentence | hypothesis in `player_hypotheses` | No | Yes, same row | No | Same id; pointer source `speculation`, status `unresolved` | No world-truth promotion. Pointer label changed. |
| After A3: cause of the hard pull is unknown | Rejected proposals | `embedded_premise_unlinked` | No | No | No | None | No |

## 7. Scenario B setup

Fresh isolated storage `isolated_B/data`, seeded when B1 began. Active scene `bread_stall`. Location `Bread stall`. Summary `A baker stands at a bread stall.`

One authored visible fact: `A baker stands beside loaves at a bread stall.`

NPC id `baker`, name `Baker`, location `bread_stall`, topics empty. Scene addressable id `baker`. No authored preference, routine, secret, history, faction tie, or quest. Snapshot: `setup_B.json`.

## 8. Turn B1 full trace

PLAYER INPUT

`Baker, which loaf do you usually keep for yourself?`

RESOLUTION CONTRACT

Before generation:

- contract `rc_d4c97cad4722`
- operation `ask`
- dimension null
- subject `baker`
- epistemic mode `unknown_allowed`

GM RESOLUTION DECISION

Outcome `epistemically_qualified`.

- `rc_9ab69105465f` — `A baker stands beside loaves at a bread stall.` — authored world fact, established
- `rc_2bb408577206` — `Baker exists` — authored world NPC, established, source `world.npcs.0`

EPISTEMIC ACTS

`establish` for the visible fact and for the baker's presence. No infer act. No consequential preference was pre-authorized.

TEMPORAL INPUT

Fresh scene. `gm_inferences`, `player_hypotheses`, and `active_claim` are empty.

RAW STRUCTURED ENVELOPE

Attempt 1 declared as established authored fact: `The baker refuses to reveal which loaf they usually keep for themselves.` Narration had the baker decline in dialogue, plus a wary-manner proposal.

Attempt 2 declared an empty claim list. Narration: `"I'm not comfortable saying which loaf I keep for myself," the baker replies cautiously, their gaze flickering briefly away.` An incidental averted-eyes proposal was attached.

DECLARED CLAIMS

Attempt 1: one realize declaration, requested authored world fact, established, empty premise ids.

Attempt 2: `declared_claims: []`.

DECLARATION AUDIT

Attempt 1: `unauthorized_declared_claim` on the refusal-as-fact declaration.

Attempt 2: no violations.

NARRATION AUDIT

Final seal: hard valid, `claim_results: []`, `violations: []`. Acceptance `regeneration_hard_valid`. Provenance `regeneration`.

RETRY

One structured retry. The fact declaration failed. The empty-declaration speech envelope passed.

ACCEPTED REALIZATION CLAIMS

None in the final seal. The spoken line is incidental NPC speech. The refusal was not stored as an established fact.

SEALED TEXT

`"I'm not comfortable saying which loaf I keep for myself," the baker replies cautiously, their gaze flickering briefly away.`

EMITTED TEXT

Same string. C18 holds.

TEMPORAL OUTPUT

- `gm_inferences`: empty
- `player_hypotheses`: empty
- `accepted_incidentals`: empty
- `rejected_consequential`: the refusal-as-established-fact sentence
- `active_claim`: null
- active interlocutor: `baker`
- visible facts unchanged

AUTHORITATIVE SCENE STATE

The stall still has one visible fact. No loaf preference, secret, or plot lead was written.

AUTHORITY RESULT

Pass. The GM produced a mundane in-character reply. The architecture rejected a consequential declaration of that reply and still allowed the spoken line through an empty claim list. No unrelated clue or history appeared.

## 9. Consequential-claim ownership audit

Propositions that reached the player:

| Turn | Proposition that reached the player | Claim id | Provenance | Authority | Epistemic status | premise_claim_ids | Premise status | Persisted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | Wooden yoke is split; leather hanger is torn | Pre-existing `rc_db5ec0aa65c3`, `rc_b31ecb1fd1c7`. Final seal list is empty. | authored world fact | world truth | established | none | n/a | Already in `scene.visible_facts` |
| A1 | Bell hangs silently | No claim id | incidental texture on a passing seal | none recorded | none recorded | none | n/a | Not stored |
| A2 | Wooden yoke is split | `rc_db5ec0aa65c3` | authored world fact | world truth | established | none | n/a | Pre-existing scene fact |
| A3 | The A2 question, spoken as a subject | Seal row has no separate id. Stored hypothesis row remains the player sentence. Decision id before generation was `rc_fec4503616e0`. | Seal says `speculation`. Bucket says `player_hypothesis`. | Seal `observation`. Bucket `observation`. | Seal `unresolved`. Bucket `hypothesis`. | Decision unresolved slot linked `rc_fec4503616e0` | hypothesis | `player_hypotheses` only, still hypothesis |
| A3 | `I cannot answer that from what is settled here` | No durable id | `npc_claim` | `claim_only` | seal says `world_truth` | none on the seal row | n/a | Not in scene, `gm_inferences`, or `player_hypotheses`. Persistence `claim_only`. |
| B1 | Baker's spoken refusal and a glance | No consequential claim | incidental speech; empty seal list | none recorded | none recorded | none | n/a | Not stored. The established-fact version was rejected. |

Rejected consequential propositions that did not reach the player, and therefore have no sealed owner, are listed in the temporal rejected buckets: structural failure, neglect, sudden pull, certainty upgrade, and both hard-pull presuppositions (`embedded_premise_unlinked`).

## 10. Preservation audit

`_bounded_keep` invocation count for the run: 0. The trace file `bounded_keep_invocations.json` was never created. `run_finished.json` records `bounded_keep: 0`.

| Turn | Initial candidate | Retry candidate | `_bounded_keep` | What sealed |
| --- | --- | --- | --- | --- |
| A1 | Structured, failed | Structured, passed | No | `regeneration_hard_valid` |
| A2 | Structured, failed | Structured, failed | No | `authorized_observation`: `The bell's wooden yoke is split.` |
| A3 | Structured, failed | Structured, failed | No | `safe_nonresolution`: the "says, I cannot answer" line |
| B1 | Structured, failed | Structured, passed | No | `regeneration_hard_valid` |

Every failed candidate was a structured envelope. None took the prose-only preservation path.

## 11. Structured compliance metrics

| Metric | Result |
| --- | --- |
| Gameplay turns | 4 / 4 |
| First-attempt structured envelope | 4 / 4 |
| First-attempt hard valid | 0 / 4 |
| Retry used | 4 / 4 |
| Retry hard valid | 2 / 4 (A1, B1) |
| Authorized fallback after two structured failures | 2 / 4 (A2 observation, A3 safe nonresolution) |
| `_bounded_keep` | 0 / 4 |
| C18 sealed equals emitted | 4 / 4 |
| Raw JSON emitted | 0 / 4 |
| Scene facts changed by narration | 0 / 4 |
| HTTP 200 | 9 / 9 |

## 12. Retry and fallback metrics

| Turn | Initial failure | Retry | Final acceptance | Fallback text |
| --- | --- | --- | --- | --- |
| A1 | `unauthorized_resolution_decision_fact` | Passed | `regeneration_hard_valid` | none |
| A2 | `unauthorized_declared_claim` | `unauthorized_certainty_upgrade` | `authorized_observation` | `The bell's wooden yoke is split.` |
| A3 | `embedded_premise_unlinked` | `embedded_premise_unlinked` | `safe_nonresolution` | `So if one hard pull split the yoke and tore the hanger together, what would have caused that pull? says, "I cannot answer that from what is settled here."` |
| B1 | `unauthorized_declared_claim` | Passed | `regeneration_hard_valid` | none |

## 13. Naturalness and usefulness

| Turn | Authority | Useful | Natural | Note |
| --- | --- | --- | --- | --- |
| A1 | Pass | Weak | Readable | Restates the damage. Does not offer the qualified reading `INFER` already allowed. |
| A2 | Pass | Weak | Flat | States one authored fact. Does not say, conditionally, that a hard pull's cause is not shown. |
| A3 | Pass | Weak | Broken | Does not answer known versus possible in ordinary words. The hypothesis sentence is voiced as a speaker. |
| B1 | Pass | Adequate | Natural | The baker declines and looks away. No named loaf. The reply is playable social improvisation. |

## 14. Defect classification

### Category 1 — PR-BR blocking

None observed.

Checked and absent from sealed output and from authoritative scene state:

- prose-only preservation of a failed structured candidate
- an emitted consequential hypothesis with no accepted claim
- the hard-pull hypothesis becoming world truth
- an embedded "cause of this hard pull is unknown" sentence reaching the seal
- raw JSON emitted
- sealed text differing from emitted text
- a chain in which a rejected premise was later stored as fact

### Category 2 — later AI, gameplay, or discourse quality

- A1 did not use the authorized qualified inference. The answer restates observations.
- A2's authorized observation does not answer the cause question.
- A2's rejected retry contained an unflagged presupposing second sentence. The envelope was already invalid, and the sentence did not seal. This is an isolated detector gap on a discarded candidate.
- A3's safe fallback treats the hypothesis text as a speaker and does not say "hypothesis" or "possibility" in plain language.
- A3's seal labels the non-answer fragment `epistemic_status: world_truth` while authority and persistence remain `claim_only`. That label is not written into the scene or the hypothesis bucket.
- A3's discourse pointer keeps the same claim id and label, and changes source from `player_hypothesis` to `speculation` and status from `hypothesis` to `unresolved`. The stored `player_hypotheses` row stays `hypothesis`.
- A3's contract epistemic mode is `npc_claim` for a status question about a proposition.
- B1 answers with a refusal rather than a named everyday preference.

### Category 3 — later performance or product

- Input size remains about 25k–33k tokens per generation attempt. Eight gameplay generations plus one preflight used 235232 input tokens and 3042 output tokens.
- Every turn needed a retry.
- Prompt duplication was not changed in this validation.

Default faction agenda and pressure counters advanced on each chat turn. That is the existing world tick. It is unrelated to the bell and the baker.

## 15. Exact model and API call accounting

| Category | Count |
| --- | --- |
| Preflight calls | 1 |
| Interpretation calls | 0 |
| Initial generation calls | 4 |
| Retry generation calls | 4 |
| Other model calls | 0 |
| Total model calls | 9 |
| HTTP Responses attempts | 9, all HTTP 200 |
| Gameplay turns | 4 |
| `_bounded_keep` invocations | 0 |

| Call | Purpose | Turn | Model | Input tokens | Output tokens |
| --- | --- | --- | --- | --- | --- |
| 1 | Preflight | Startup | gpt-4.1-mini | 24 | 2 |
| 2 | Initial generation | A1 | gpt-4.1-mini | 25003 | 503 |
| 3 | Retry generation | A1 | gpt-4.1-mini | 26384 | 136 |
| 4 | Initial generation | A2 | gpt-4.1-mini | 28322 | 490 |
| 5 | Retry generation | A2 | gpt-4.1-mini | 29645 | 199 |
| 6 | Initial generation | A3 | gpt-4.1-mini | 30733 | 697 |
| 7 | Retry generation | A3 | gpt-4.1-mini | 32942 | 377 |
| 8 | Initial generation | B1 | gpt-4.1-mini | 30353 | 390 |
| 9 | Retry generation | B1 | gpt-4.1-mini | 31826 | 248 |

## 16. Exact provider token accounting

| | Tokens |
| --- | --- |
| Provider input tokens | 235232 |
| Provider output tokens | 3042 |
| Total provider tokens | 238274 |

Cached input tokens on every call: 0. Counts come from the Responses API usage on each observed call.

## 17. PR-BR closeout recommendation

Close PR-BR.

The live model still writes unsafe causal prose. The structured boundary rejects it, refuses prose salvage, keeps the player hypothesis below world truth, and still allows an ordinary NPC line. The remaining misses are answer quality, fallback wording, discourse-pointer labeling, and prompt cost. They belong to later AI, gameplay, and product work.

A.
PR-BR CLOSEOUT RECOMMENDED;
SYSTEMIC SEMANTIC/AUTHORITY BOUNDARY IS SUFFICIENTLY STABLE.
MOVE REMAINING ISSUES TO LATER AI, GAMEPLAY, OR PRODUCT CAMPAIGNS.

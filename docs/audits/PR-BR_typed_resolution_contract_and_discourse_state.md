# PR-BR - Typed Resolution Contract and Lightweight Discourse State

Date: 2026-09-28

Type: implementation cycle, continued through cost-controlled live validation.

Base HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`

No completion commit was created. PR-BR remains open.

## 1. Executive Summary

PR-BQ's minimum architecture is now in the live player-input path. A typed Resolution Contract records what the player wants resolved. A small discourse-focus record owns cross-turn referents for the interlocutor, the active claim, the actionable lead, the inspected object, and the last attempted action. Interaction Obligation, PR-BN, narration, retry, final emission, and the evaluator read that same contract instead of each reconstructing the request from prose.

The contract distinguishes perception dimensions, claim follow-ups, and action requests. It does not try to parse every natural-language phenomenon.

Continuation 2, recorded at the end of this report, tightens enforcement when that contract is already correct. PR-BR remains open. A full synthetic gate is not authorized by this continuation.

Deterministic and real-path tests for the PR-BQ matrix passed. Live validation then ran. API preflight passed on `gpt-4.1-mini`. Level 2 used the full 10-turn budget. Two repairs followed live evidence. The smoke gate ran twice (14 turns each) and the second run still showed the same player-visible failure: a correct contract is often replaced by a question echo, a stock social line, or an unrelated action. The full gate was not started. Human playtest is not recommended.

## 2. PR-BQ Architecture Adopted

Adopted without reopening the architectural choice:

1. Typed Resolution Contract, separate from Interaction Obligation.
2. Lightweight discourse slots, not a discourse graph.
3. Interaction Obligation kept, and pointed at the contract.
4. The same contract projected into generation, final emission, and evaluation.

PR-BN authority rules were not replaced. Final-emission safety was not weakened. The contract check can only replace an obvious semantic miss with the existing non-inventive obligation fallback.

No code evidence contradicted the PR-BQ split. The one integration adjustment is that some `/api/chat` turns never build an engine resolution. Those procedural turns now receive a contract on the existing turn resolution object before narration, so the contract still originates from raw player text plus runtime context.

## 3. Resolution Contract Schema

Owner: `game/resolution_contract.py`.

Stored at `resolution.metadata.resolution_contract`.

| Field | Role |
|---|---|
| `contract_id` | Stable id for this turn's raw text. Retries keep it. |
| `turn_index` | Session turn counter when present. |
| `request_kind` | `inquiry`, `action`, `social_action`, or `clarification`. |
| `operation` | `perceive`, `inspect`, `ask`, `confirm`, `follow`, or `act`. |
| `target_ref` | `{type, id_or_text, source}`. |
| `interlocutor_id` | Addressee when the utterance is addressed to someone. |
| `conversational_subject` | Claim text or target label. |
| `dimension` | Primary semantic point, if any. |
| `dimensions` | Every detected point, in textual order. |
| `expected_resolution` | `answer`, `action_outcome`, `refusal`, `clarification`, or `partial`. |
| `epistemic_mode` | `authoritative`, `bounded_incidental`, `npc_claim`, `unknown_allowed`, or `consequential_protected`. |
| `discourse_ref` | `{type, id, label, source_turn}` when a prior slot was bound. |
| `referent_provenance` | `explicit_player`, `inherited_discourse`, `unresolved`, or `ambiguous`. |
| `ambiguous` | True when more than one slot could bind and the utterance does not choose. |
| `raw_input` | Cleaned player text the contract was built from. |

Initial dimensions, extensible by pattern rather than by a closed ontology:

- Perception: `appearance`, `sound`, `smell`, `wear`, `use`, `change`
- Claim / conversation: `source`, `confidence`, `location`, `time`, `next_step`

Action requests are represented by `request_kind` / `operation` / `expected_resolution`, not by collapsing them into inspection.

`location` and `time` bind an active claim only when the utterance is anaphoric (`that`, `it`, `then`). A fresh "where can I..." question does not steal the previous claim.

## 4. Contract Lifecycle

```text
raw player text + session discourse / claim ledger / interaction target / pending lead
    -> construct_resolution_contract
    -> resolution.metadata.resolution_contract
    -> Interaction Obligation.resolution_contract_id
    -> select_resolution_mode stamps authority from the contract
    -> narration prompt receives a short projection
    -> retry keeps the stored contract
    -> final emission assesses the candidate against the contract
    -> discourse focus commits once per contract id
    -> evaluator reads the same contract
```

Construction entry points:

- `attach_interaction_obligation` on the resolved-turn pipeline.
- The procedural `/api/chat` branch that previously called narration with `resolution=None`.

The contract is built from the raw text and current runtime context. Tests do not inject a finished contract into production.

## 5. Discourse-State Model

Owner: `game/discourse_state.py`, stored at `session["discourse_focus"]`.

Slots:

- `active_interlocutor`
- `active_claim`
- `active_actionable_lead`
- `active_inspected`
- `last_attempted_action`

Each slot stores `id`, `label`, `kind`, `scene_id`, `turn_index`, and `source`. The slot is a pointer. The claim ledger, lead rows, and interaction context remain the owners of those records.

Empty slots are filled at read time from those owners:

- latest accepted NPC claim
- `interaction_context.active_interaction_target_id` when it belongs to the current scene
- the latest pending lead in the current scene runtime

Inspected objects and prior actions are not guessed from the scene.

## 6. Referent Ownership

`discourse_focus` is the only owner of active discourse focus.

| Event | Effect |
|---|---|
| Explicit nominal target | Overrides inherited focus for this turn. |
| Pronoun plus one matching slot | Binds that slot. |
| Pronoun plus several eligible slots and no dimension cue | `ambiguous`; expected resolution is clarification. |
| Missing slot for "that lead", "it", or "when I did that" | `unresolved`; clarification, not a guessed id. |
| Scene change | Hides scene-bound slots from the previous scene: interlocutor, inspected object, last action. Claims and leads remain available, but "it" does not bind the old object. |
| Commit | Writes slots implied by the contract after final emission. |
| Same `contract_id` committed again | No-op, so a retry cannot erase the referent. |

## 7. Interaction Obligation Integration

`InteractionObligation` is unchanged in role. `attach_interaction_obligation` still derives kind and requested outcome with the existing rules, then records `resolution_contract_id`.

Inspection fallbacks consult contract dimensions. A sound or smell contract no longer depends on those words surviving inside the prose subject. Question, action, and follow-up fallbacks keep their previous wording when the dimension does not call for a more specific safe line.

## 8. PR-BN Integration

`select_resolution_mode` stamps `requested_dimension` and `contract_id` onto the mode decision.

If `epistemic_mode` is `consequential_protected` and the turn is not an authoritative mechanical action, the mode becomes `unsupported_consequential_request` and no incidental proposal kind is attached. `validate_bounded_improvisation_proposal` also rejects an incidental proposal when the contract is consequential-protected.

Ordinary perception stays `incidental_fact` / `sensory_detail`. Accepted entries may carry `satisfies_contract_id` and `requested_dimension`. Incidental category limits, NPC-claim versus world-truth, and mechanical authority are unchanged.

## 9. Generation Integration

`build_narration_context` adds `resolution_contract` to the model payload when a contract exists. The projection is the compact constraint: request kind, operation, target, interlocutor, subject, dimension, expected resolution, authority, and one sentence of instruction. Internal provenance stays off the prompt.

One instruction tells the model to obey that constraint rather than infer a different request from surrounding prose.

## 10. Retry Preservation

A second `attach_interaction_obligation` on the same resolution object keeps the first contract, including target, dimension, subject, and action, and sets `retry_preserved`. Discourse commit for that `contract_id` does not run again. Retry may still repair speaker, grounding, and wording around that fixed request.

## 11. Final-Emission Integration

`_preserve_resolution_contract_after_gate` assesses the candidate. It does not generate a better answer.

It replaces the candidate with the obligation fallback only when the assessment is an obvious miss:

- sound, smell, wear, use, change, source, or confidence was requested and the text does not address it and is not a legitimate inability, refusal, or clarification
- a generic scene description stands in for an action outcome
- an ambiguous or unresolved referent was not clarified
- protected consequential information was not refused

Appearance, location, and time are assessed, but a merely lexical miss in those dimensions is not auto-replaced, because legitimate answers vary more widely. A recorded `obligation_resolved` flag is not consulted.

## 12. Evaluator Integration

`evaluate_playability` reads `resolution_contract` from the payload, from `resolution.metadata`, or from `gm_output` emission debug.

The assessment is evidence about the player-visible text:

- `unsatisfied` fails `player_intent_addressed` even when token overlap would pass
- `satisfied`, `legitimate_nonresolution`, or `partial` can pass that gate when older token logic would fail
- a malformed response still fails
- a bare runtime success flag does not pass the gate

The synthetic gate runner now passes the production contract into `evaluate_playability`.

## 13. Observability

On each construction, a `resolution_contract` debug trace records raw input, the compact contract, referent provenance, discourse focus, obligation kind, and authority route. Final emission adds `emission_debug.resolution_contract` and `emission_debug.resolution_contract_semantic`. Live resolution metadata includes `contract_id` and `requested_dimension`.

A later failed turn can be split into: contract wrong, referent wrong, authority route wrong, generation wrong, emission replacement wrong, or evaluator wrong.

## 14. Deterministic Test Results

`tests/test_pr_br_resolution_contract.py`: 21 passed in the original matrix run. Live findings added 7 tests. The file is 28 tests, and that file passed again after each repair.

Covered without transcript-specific noun handlers:

| Case | Result |
|---|---|
| A appearance | preserved |
| B sound | preserved |
| C smell | preserved |
| D wear / use | preserved and bound to the inspected object |
| E claim source | bound to the claim ledger id |
| F claim confidence | bound to the active claim |
| G claim location | bound only because the follow-up is anaphoric |
| H actionable lead | "that lead" bound |
| I inspected referent | "it" bound |
| J prior action | "when I did that" bound |
| K action request | stays `social_action` / `act` |
| L ambiguous referent | clarification, no chosen id |
| M scene change | old inspected object does not bind |
| N consequential information | unsupported mode; incidental proposal rejected |
| Retry | second attach cannot change smell into color |
| Final emission | generic scene for a sound contract is replaced |
| Evaluator | shared contract fails a topical miss and passes a real smell answer |
| Discourse commit | same contract id does not rewrite focus |

## 15. Real-Path Integration Results

Two `/api/chat` tests drive raw text through production orchestration with the model stubbed:

1. "I examine the iron latch." then "What does it smell like?"
   - contract dimension is `smell`
   - referent provenance is `inherited_discourse`
   - target is the latch
   - obligation carries `resolution_contract_id`
   - the narration payload contains the same dimension and target
   - the evaluator receives that contract and marks the smell answer satisfied
2. "What does the cooking pot smell like?" with a generic gate-crowd candidate
   - the emitted text is the non-inventive smell fallback, not the generic scene

## 16. Focused Live-Probe Results

API/model preflight: PASS. The normal live path loaded its credential and selected `gpt-4.1-mini`. Probes used an isolated storage directory. The player's saved campaign was not reset.

### First probe set (7 turns, 9 model calls)

Artifact: `artifacts/pr_br_level2/20260928T002628Z`.

The same construction defect appeared on the perception, claim, and confidence turns. `normalized_action.label` was the whole player sentence. The contract treated that sentence as an explicit target, so "it" and "that" never consulted discourse. Inspected focus was overwritten with the question text. "Where did you hear that?" was tagged `location` plus `sound` because "hear" matched the sound pattern, and the epistemic mode became incidental. Generation did receive a contract, but the contract named the question. Emission and the evaluator often marked the turn satisfied because the fallback contained the dimension word or repeated the question.

| Turn | Player request | Contract | Visible result |
|---|---|---|---|
| 1 | Inspect the banner cloth | `inspect`, target "cloth itself", explicit | Notice-board text substituted. No dimension, so emission did not replace it. |
| 2 | What does it smell like? | target = the whole sentence, `explicit_player`, smell | Smell inability line. "It" was not the cloth. |
| 3 | Wear on it | target = the whole sentence, wear | Social retry, then the question echoed inside a verify line. |
| 4 | Ask what rumor is being repeated | `ask`, `npc_claim` | A gate-watch claim was spoken. |
| 5 | Where did you hear that? | target = the sentence, dimensions location/source/sound | No claim binding. Partial coverage. |
| 6 | How sure are you? | target = the sentence, confidence, not bound to the claim | Question echoed inside a verify line. |
| 7 | I follow that lead. | `follow`, unresolved | Inability to complete the action. No lead had been stored. |

Stopped further probing of that mechanism. Repair: a parser label that repeats the utterance is not an explicit target; informational "hear/heard" is not the sound dimension; source and confidence keep `npc_claim`.

### Remaining budget (3 turns, 3 model calls)

Artifact: `artifacts/pr_br_level2/20260928T002857Z`. The 10-turn cap was not reset.

| Turn | Contract | Visible result |
|---|---|---|
| Inspect the cloth | explicit target "cloth itself" | Notice board substituted again. |
| What does it smell like? | `inherited_discourse`, target "cloth itself", smell. Prompt constraint named the cloth. | Inability: no distinct smell beyond general scene activity. The referent survived. The answer is an inability, not a description. |
| Where he heard the rumor | dimension missing. Subject was the raw sentence. | A rumor was spoken. Source was not classified. |

The pronoun bug was fixed on the live path. The third-person source phrasing was still missed. That pattern was widened in tests before smoke. No Level 2 turns remained.

## 17. Smoke-Gate Results

Two personas, seven turns each, isolated storage, natural wording. Not the historical V3.6 lines.

### Smoke 1 — `artifacts/pr_br_smoke/20260928T003205Z`

14 turns. Evaluator semantic FAIL: 3. One earlier harness call aborted before a turn was recorded; it is not a second run.

Systemic: the parser's NPC id (`guard_captain`) became the explicit target of follow-ups the player did not address to that id. Claim, place, and movement requests bound to the speaker. "Take me toward that place" stayed `ask`. Wear ("recently handled") and confidence ("actually believe") were not dimensions, so emission never checked them. One smell turn did inherit "that posting" and answered ink, damp, and smoke.

Repair, still inside the one smoke-repair allowance: an unmentioned parser id is not the resolution target unless it is the focused object, claim, or lead. Interlocutor ids do not qualify. Source, confidence, wear, and "take me / I will do / I take that step" patterns were widened. A question is not forced into `act` by a travel action type. "That place" with no place slot stays unresolved instead of binding the speaker.

Focused regression after that repair: 120 passed, 0 failed.

### Smoke 2 — `artifacts/pr_br_smoke/20260928T003623Z`

14 turns. Evaluator semantic FAIL: 2. This is the second and final smoke run.

The contract was often right and the player-visible text was still wrong.

| Turn | Contract that survived | What the player saw | Where it broke |
|---|---|---|---|
| Yard wear | `perceive` / `use` / inherited | The question repeated inside "no reliable source can verify…" | Retry, then emission. The echoed question contains "handled", so the check counted it as covered. Evaluator PASS. |
| Yard smell | `perceive` / `smell` / inherited | Ink, damp, and smoke on the notice board, including an absence. | Held. |
| Yard source | `ask` / `source` / unresolved | "I have heard talk, but I cannot verify it." | No stored claim to bind. The line does not answer where the information came from. |
| Yard "do the next thing" | `act` / inherited | "I couldn't tell you the requested information." | Action emitted as a social refusal. Evaluator PASS. |
| Local source | `source` / unresolved | Same unverified-talk line. | Prior Thoran sentence was not an attachable claim. |
| Local confidence | `confidence` / unresolved | The question echoed inside "couldn't tell you…". | Emission accepted the echo. Evaluator PASS. |
| Local "take me toward that place" | `act` / inherited | The Thoran rumor again. | Generation. Action became unrelated claim text. Evaluator FAIL. |
| Local "what can I see from here" | `perceive` / `appearance` / inherited | "You move as if to cross into it…" | Generation answered a different operation. Evaluator PASS. |
| Local "I take that step" | `act` / ambiguous | Unverified-talk line. | Action not performed. |

Smoke 2 is not healthy. The funnel stops. No third smoke run.

## 18. Full-Gate Results

Not reached.

Full-gate runs: 0. Full-gate turns: 0.

## 19. Failure Clustering

Live clusters, after the construction repairs:

1. **Echo counted as an answer.** Social retry and the verify fallback paste the player's question into the line. Final-emission coverage and the evaluator treat dimension words inside that echo as satisfaction. Seen on wear and confidence in both smoke runs.
2. **Action contract, non-action emission.** `act` turns were answered with a repeated NPC rumor, a stock "another source" line, or a crossing narration on a sight question. The contract's operation did not constrain the emitted text.
3. **Claim follow-up with no claim slot.** Source questions are now classified, but the previous NPC sentence often never became `active_claim`, so provenance stays unresolved and the reply is a generic unverifiable line.
4. **Grounded substitution on inspect.** Asking to inspect cloth or a posting still surfaces the notice-board taxes/curfew/patrol block when the requested object is not an authored interactable. The contract target was explicit. This is scene grounding, not the pronoun bug.

The first cluster is the one that makes evaluator PASS unsafe: shared-contract assessment can pass because it scores the echoed question.

## 20. Regression Results

Original focused band, before live validation: 113 passed, including 21 PR-BR tests.

After the live repairs the same band was run again: 120 passed, 0 failed. The increase is the 7 PR-BR tests added for utterance-echo labels, informational "hear", third-person source, interlocutor-id override, wear on an inspected object, "take me" staying an action, and a sight question not being forced into travel.

- `tests/test_pr_br_resolution_contract.py` (28)
- `tests/test_pr_bp_live_resolution_routing.py`
- `tests/test_playability_eval.py`
- `tests/test_bounded_improvisation_authority.py`
- `tests/test_perception_narration_authority_audible_non_invention.py`
- `tests/test_playability_smoke.py`
- `tests/test_prompt_context_public_prompt_boundary.py`

Preserved by those suites: PR-BN incidental versus consequential routing, NPC claim versus world truth, interaction-obligation fallbacks, perception non-invention, and evaluator behavior when no contract is present.

## 21. Known Limitations

- This is not a general parser or coreference engine. Only the PR-BQ dimensions and five discourse slots are supported.
- An explicit nominal target is a shallow pattern. Unusual phrasing can remain unresolved and ask for clarification.
- Appearance answers are judged more loosely than smell, sound, wear, or source, so a visual answer is less likely to be replaced.
- Final emission will not invent the missing sensory detail. The replacement is a safe inability line.
- The evaluator can pass intent when the shared assessment says the text satisfies the contract. On live turns, that assessment currently treats a quoted player question as coverage.
- Discourse focus is not a history of every mentioned noun. A scene with several unnamed objects and no prior inspect slot stays unresolved.
- A spoken NPC rumor does not always become the active claim, so the next "who passed that to you?" stays unresolved.
- An `act` contract does not yet block an unrelated social or movement line at emission.

## 22. Cost / Turn Accounting

| Bucket | Used |
|---|---:|
| Focused live turns | 10 |
| Focused live model calls | 12 |
| Smoke runs | 2 |
| Smoke turns | 28 |
| Full-gate runs | 0 |
| Full-gate turns | 0 |

Focused calls: 9 on the first seven turns, 3 on the repair probes. Retries are included in those 12.

Smoke model calls were not instrumented. The logs show a retry on several turns (yard wear, and in smoke 2 also two local turns). One additional model call happened when the first smoke launch aborted on a missing evaluator argument before any turn was saved. That call is not one of the 28 saved turns.

API token or monetary cost: unavailable. No usage field was recorded.

## 23. Whether PR-BR Is Complete

No. The contract and discourse record exist, and a smell follow-up can inherit the inspected object through generation. The second smoke gate still fails basic wear, confidence, source, and action resolution in the text the player sees. Emission and the evaluator can score those failures as success when the question is echoed.

PR-BR remains open.

## 24. Whether Human Playtest Is Recommended

No.

HUMAN PLAYTEST: NOT RECOMMENDED.

## 25. Recommended Next Step

Do not run another smoke or a full gate until emission stops treating a pasted player question as dimension coverage, and until an `act` contract cannot be emitted as an unrelated rumor or stock social line. Add a deterministic case where the candidate text contains the raw question and the strict dimension must still be unsatisfied. Re-check claim attachment when an NPC line was accepted into the claim ledger. Only then spend a new, explicitly authorized live budget.

## PR-BR Continuation 2 — Contract Enforcement

Date: 2026-09-28. No completion commit. No full 4×10 gate. PR-BR remains open.

### 1. Prior live/smoke diagnosis

The contract often named the right operation and dimension, and the player still saw a pasted question, a repeated rumor, or a stock social line. The evaluator could PASS when the only confidence or smell words were inside that paste.

### 2. Echo-as-answer root cause

Satisfaction was keyword overlap on the whole candidate. A fallback that pasted the player question still contained "sure", "believe", "smell", or "handled", so the check reported the dimension covered.

### 3. Action-enforcement root cause

Action success used a broad "cannot / will not" cue, and emission replaced a candidate only for a short list of reasons. A rumor did not match those reasons. When the obligation fallback was an information line, emission also refused to swap it in, because that line itself failed the action check, and the rumor stayed.

### 4. NPC-claim promotion root cause

`active_claim` was filled from the ledger only when a slot was empty at read time, and commit ran before bounded-improvisation promotion. An emitted quoted assertion ("Travelers say…", "Word is…") never became the discourse object unless it was already a follow-up dimension. Refusals were not the problem. Assertions were not copied into the slot after emission.

### 5. Implementation changes

- Echo detection: a full paste, or a paraphrase whose content words are only the player's, is not an answer. Dimension and action cues are scored after that material is removed.
- Action outcomes are success, or a grounded refusal / inability / condition / clarification. Mentioning the topic is not an outcome. Emission uses an action inability line when the obligation fallback would not satisfy an `act` / `follow` / `confirm` contract.
- `note_emitted_npc_claim` sets `active_claim` from an accepted ledger claim that appears in the emitted text, or from an emitted quoted assertion. Rejected ledger text is not promoted. The slot means the conversation can refer to the claim. It does not mark the claim as world truth.
- The evaluator records `echo_detected` and fails the intent gate when the shared assessment is unsatisfied. It does not treat emission success as the verdict.
- Traces add `echo_detected`, `action_outcome`, and `claim_promoted`.

### 6. Deterministic regressions

`tests/test_pr_br_resolution_contract.py` is 40 tests, including matrix A–P: confidence echo, smell echo, a real confidence answer, topic-only action, action success, refusal, condition, clarification, accepted-claim promotion, rejected-claim non-promotion, source / confidence / location / time follow-ups, retry echo, and retry action collapse. A raw `/api/chat` test emits a traveler claim, then rejects a source-question echo.

### 7. Broader regressions

The PR-BR / PR-BP / playability / bounded-improvisation / perception / prompt band passed. One Windows file-lock error on `test_chat_npc_rumor_creates_claim_without_world_truth` failed the first combined run and passed on rerun. That test still requires the claim to stay `not_world_truth`.

### 8. Focused live probes

8 turns, 9 model calls. Artifacts: `artifacts/pr_br_enforcement/20260928T004838Z` (6 turns, 7 calls) and `20260928T004941Z` (2 turns, 2 calls).

The first action request stayed `act` and the model answered with "I have heard talk, but I cannot verify it." The evaluator FAILed. Emission had not replaced it. After the action-line fix, the remaining two turns were: walk toward the notice board, answered by the action inability line; and a smell question, answered by the smell inability line rather than a restatement.

The opening rumor question did not produce an assertion. The runner said travelers were keeping quiet. That refusal was not stored as `active_claim`, and the source follow-up stayed unresolved. That is a legitimate absence, not a false binding.

### 9. Smoke

One gate. 2 personas, 6 turns each. 12 turns, 13 model calls. Artifact: `artifacts/pr_br_enforcement_smoke/20260928T005013Z`. Evaluator FAIL: 1.

"Walk me toward the notice board" stayed an action and was emitted as an inability, not a rumor. "What does the sheet smell like?" was answered with must, soot, and rain-soaked paper. No player question was pasted back as the answer.

No turn emitted a positive NPC assertion, so live claim follow-up binding was not shown. "Who did he hear that from?" and "Does he trust it?" were not classified as source and confidence. "I take that step" was ambiguous and was emitted as an information inability. A wear question was emitted as a generic "another source" line rather than a wear line.

### 10. Remaining failure clusters

- Social turns still resolve to a generic unverified-talk or "another source" line when the NPC does not assert a claim.
- Some natural follow-ups ("who did he hear that from", "does he trust it") still do not receive source or confidence, so claim binding never starts.
- An ambiguous action can still be emitted as an information inability.
- Inspecting the posted sheet still prepends "nothing matches" and then the notice-board taxes, curfew, and patrol block.

### 11. Deferred unauthored-object evidence

Left untouched. Representative lines are yard inspect turns in the smoke artifact above, and the earlier Level 2 banner/cloth turns that surfaced the notice board. This is a grounding issue, not echo, action-outcome, or claim-promotion.

### 12. Cost accounting

| Bucket | Used |
|---|---:|
| Focused live turns | 8 |
| Focused live model calls | 9 |
| Smoke runs | 1 |
| Smoke turns | 12 |
| Smoke model calls | 13 |
| Full-gate runs | 0 |
| Full-gate turns | 0 |

Retries are included in the model-call counts. One smoke turn used a second call. API token or monetary cost: unavailable.

### 13. PR-BR status

STILL OPEN. This continuation is not a completion commit.

### 14. READY FOR FULL SYNTHETIC GATE

No. Echo scoring and clear action contracts are enforced, and an emitted assertion can become `active_claim` in tests. The authorized smoke did not show a live claim becoming the next turn's referent, and several social turns still end in a generic inability. That is not enough to spend a 40-turn gate.

HUMAN PLAYTEST: NOT RECOMMENDED.

## PR-BR Continuation 3 — Semantic Follow-Up Recognition & Ambiguity Handling

Date: 2026-09-28. No completion commit. No push. No full 4×10 gate. No smoke gate. PR-BR remains open.

### 1. Prior smoke findings

Continuation 2's smoke evaluator recorded one formal FAIL. Manual review found more. The misses were at contract construction: "Who did he hear that from?" and "Does he trust it?" were not source and confidence; "I take that step" became an information inability; a wear question was emitted as a generic "another source" line. No live turn emitted a positive NPC assertion, so claim follow-up binding was not shown on the real path.

### 2. Follow-up-recognition root cause

Source and confidence patterns required a few second-person frames (`who told`, `do you believe`, `how sure`, `where did you hear`). Ordinary variants — "who did he hear that from", "how does she know", "does he believe it", "does she trust the story", "is he convinced", "was that today", "what place was he talking about" — never set the dimension, so claim binding never started. Pronouns were already available in discourse; the cue list did not see them as provenance, belief, place, or time.

### 3. Referential-action root cause

"I take that step" and "I do that" were anaphors over every filled slot (object, claim, person, lead, prior action). More than one slot made the turn ambiguous, and the obligation parser still treated the line as a question, so the emitted fallback was an information inability. Actionable leads were not given priority over unrelated slots.

### 4. Wear/use routing root cause

"Does it look used?" did not match wear. When wear was recognized, the obligation kind was still often `question`, so the terminal line was "another source" rather than a wear line. Perception grounding could then replace a wear-satisfying line with "You look again. Nothing new resolves…" A generic social inability also counted as legitimate coverage.

### 5. Implementation changes

Recognition is by concept, not by stored transcript sentences:

- Provenance: who told / said / passed / gave, who was the source, heard-from, learned-from, how someone knows.
- Belief: sure, certain, believe, trust, doubt, think it is true, convinced.
- Place and time follow-ups: where did / where was / what place, when did / how long ago / was that today.
- With one active claim and a follow-up pronoun or "the story", those dimensions bind `active_claim`. A clear source question with an empty claim slot stays an inquiry. It does not become "which one?"
- "I do that", "I take that step", "let's do it", "I follow that", and "I go there" bind the single actionable lead or previous action and stay `request_kind = action`. A lead plus a previous action clarifies instead of choosing.
- Wear/use includes look-used, handled, disturbed, fresh marks, and people coming through. Those stay `perceive`. A social "another source" line does not satisfy them. Perception grounding will not replace a satisfying wear/smell/sound line with untargeted scene stock.
- The obligation kind follows the contract. Traces include `construction`: cues, referent slot, reason, ambiguity, whether the lead or the claim was inherited.
- The evaluator records `failure_locus`: `response_missed_contract`, `response_met_contract`, or `contract_unchecked`. It still scores the shared contract. It does not build a second interpretation.
- A clarification spoken to an NPC is voiced (`Which do you mean?`). A named object in the same sentence ("at the posted sheet") is explicit, so "look it over" is not an ambiguous pronoun.

### 6. Deterministic and regression results

`tests/test_pr_br_resolution_contract.py`: 48 passed. The matrix covers direct and indirect source, knowledge provenance, certainty, belief, trust, location, time, one actionable referent, "I do that", split actionable referents, wear, recent handling, accepted-claim promotion, rejected-claim non-promotion, and retry preservation of claim, dimension, and request kind.

Real `/api/chat` path, with the model stubbed: an emitted traveler assertion becomes `active_claim` from the ledger, `truth_status` stays `not_world_truth`, then raw "Who did he hear that from?" and "Does she trust the story?" bind that claim. A refusal does not promote `active_claim`. A worn-sheet question stays perception, and "another source" is not the emitted line.

Focused band, 156 passed, 0 failed:

- `tests/test_pr_br_resolution_contract.py` (48)
- `tests/test_pr_bp_live_resolution_routing.py`
- `tests/test_playability_eval.py`
- `tests/test_bounded_improvisation_authority.py`
- `tests/test_perception_narration_authority_audible_non_invention.py`
- `tests/test_playability_smoke.py`
- `tests/test_prompt_context_public_prompt_boundary.py`
- `tests/test_referenced_surface_grounding_inspection_resolution.py`

### 7. Real-path claim-promotion proof

Proven through `/api/chat` in `test_real_path_promoted_claim_accepts_indirect_follow_ups`. The player text is raw. The claim is not injected into `active_claim` by the test. Ledger status is `not_world_truth`. The follow-up contracts bind that claim's id at source and at confidence. Player-visible text addresses source or certainty and does not paste the question back.

### 8. Focused live results

One probe. Artifact: `artifacts/pr_br_followup/20260928T011636Z`. Completed turns: 1. Model calls: 2. The second call's turn was not saved.

Turn 1: "I catch the tavern runner and ask what rumors travelers are repeating about the roads." The runner said he had heard talk but could not verify it. Evaluator PASS. `active_claim` stayed empty. That refusal is not a false binding. It also means the live chain assertion → claim → follow-up did not occur.

The next planned turn, looking at the posted sheet, raised `AssertionError` in the strict-social invariant. The clarification sentence was narration, not speech. The probe stopped. It was not restarted.

After the probe, clarification with a speaker is voiced, and "at the posted sheet" is an explicit object. Those fixes are in the deterministic tests only.

### 9. Smoke

Not run. The focused probe was not healthy.

### 10. Manual product assessment

The one completed live turn answered a rumor solicitation with a refusal. That matches the question. It does not establish a claim the player can ask about. No indirect source, confidence, location, time, referential action, or wear turn was completed live.

### 11. Evaluator disagreements

False PASS: 0. False FAIL: 0.

The saved turn's `failure_locus` was `bad_contract` because the rumor ask has no dimension. That label overstated a construction failure. The code now records `contract_unchecked` for that case. The saved JSON was not rewritten.

### 12. Remaining semantic failure clusters

- Live rumor solicitations still end in "I have heard talk, but I cannot verify it." Without an emitted assertion, follow-up binding has nothing to attach to. The architecture binds a claim once one is actually emitted; this probe did not emit one.
- The strict-social crash is fixed in code and not re-checked on a live turn.

### 13. Mechanical fallbacks, separately

"I have heard talk, but I cannot verify it."

On the stubbed real path, a correct source or confidence contract can still be answered with "I cannot verify the source or certainty of that earlier claim." That line does address the dimension. It is stiff. It is not a wrong contract.

### 14. Cost accounting

| Bucket | Used |
|---|---:|
| Focused live turns completed | 1 |
| Focused live model calls | 2 |
| Aborted live turns | 1 |
| Smoke runs | 0 |
| Smoke turns | 0 |
| Full-gate runs | 0 |
| Full-gate turns | 0 |

API token or monetary cost: unavailable. Retries are included in the model-call count. The aborted turn consumed the second call, then died in emission.

### 15. PR-BR status

STILL OPEN. This continuation is not a completion commit. Nothing was pushed.

### 16. READY FOR FULL SYNTHETIC GATE

No. Deterministic recognition, ambiguity, wear routing, and the stubbed claim lifecycle pass. The authorized live probe did not show an emitted assertion becoming the next turn's referent, and it aborted before wear or action. That is not enough to spend a 40-turn gate.

HUMAN PLAYTEST: NOT RECOMMENDED.

## PR-BR Continuation 4 — Validation-Only Live Resume

Date: 2026-09-28. No completion commit. No push. No production-code change. No mechanical restart. No smoke gate. No 4×10 full gate. PR-BR remains open.

### 1. Preflight

PASS.

- API/model: `run_upstream_api_preflight` returned `ok=true`, `health_class=healthy`, model `gpt-4.1-mini`. The gameplay client logged the same healthy startup gate before the first turn.
- Resolution Contract, discourse focus, emitted-claim promotion, semantic follow-up recognition, action-ambiguity handling, and wear/use routing are present. The focused band below covers them.
- Continuation 3's strict-social crash fix is present. A clarification spoken to an NPC is voiced (`Tavern Runner says, "Which do you mean?..."`), and that sentence classifies as `social` under `_classify_strict_social_ownership_sentence`. `test_named_object_is_not_an_ambiguous_pronoun` is in the passing band. "I stop at the posted sheet and look it over" is not treated as an ambiguous pronoun.

### 2. Deterministic baseline

156 passed, 0 failed. Same band as Continuation 3, including 48 tests in `tests/test_pr_br_resolution_contract.py`:

- `tests/test_pr_br_resolution_contract.py`
- `tests/test_pr_bp_live_resolution_routing.py`
- `tests/test_playability_eval.py`
- `tests/test_bounded_improvisation_authority.py`
- `tests/test_perception_narration_authority_audible_non_invention.py`
- `tests/test_playability_smoke.py`
- `tests/test_prompt_context_public_prompt_boundary.py`
- `tests/test_referenced_surface_grounding_inspection_resolution.py`

The count did not change. No production code was edited after this run.

### 3. Focused live transcript assessment

Artifact: `artifacts/pr_br_continuation4/20260928T012505Z`. Isolated storage. Six completed turns, zero aborted turns, seven model calls. One retry (turn 4).

| Turn | Player | Contract | Visible result | Class |
|---|---|---|---|---|
| 1 | Ask the tavern runner what rumor they are calling out. | `ask` / inquiry. No dimension. Interlocutor bound. Epistemic mode `npc_claim`. | Catalog refusal: "I have heard talk, but I cannot verify it." | FINAL EMISSION. The model had already said the patrol vanished near muddy footprints northwest of the crates. That sentence never reached the player, so no claim was promoted. Evaluator PASS (`contract_unchecked`). Credible for the visible refusal. |
| 2 | Ask the gate serjeant what travelers have been repeating as they come through. | `perceive` / clarification. Dimensions `use`, `wear`. Referent unresolved. | "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates." | CONTRACT CONSTRUCTION plus FINAL EMISSION. "come through" matched the wear/use cue, so a social question became an unresolved perception clarification. The model refused. Emission replaced that refusal with a structured "Word is" line. That line did promote `active_claim` (`source=emitted_npc_claim`). No ledger entry. Evaluator FAIL (`clarification_missing`) matches the bad contract and misses the player's actual question. |
| 3 | "Who did he hear that from?" | `ask` / inquiry. Dimension `source`. Bound to turn 2's claim. `active_claim_inherited=true`. Obligation kind `follow_up`, but `claim_id` is null. | "Word is, the patrol route changed after the Ash Compact census choke worsened." | FINAL EMISSION. Recognition and referent binding were right. The model named the runner as the source. Emission replaced that answer with a different structured fact, and that new quote became the next `active_claim`. Evaluator FAIL (`dimension_not_addressed`) is a true fail. |
| 4 | "Does he trust the story?" | `ask` / inquiry. Dimension `confidence`. Bound to the turn 3 claim. | The serjeant says he can't say for sure he trusts it, and restates the route rumor. | GENERATION then RETRY. First call was flagged `validator_voice`. The retry answer addresses confidence and was kept. Evaluator PASS (`covered:confidence`) is credible. Discourse then stored the fragment "I can't say for sure if I trust it," as the new `active_claim`, because the quote contains "say". |
| 5 | "I stop at the posted sheet and look it over." | `ask` / inquiry. Explicit target "posted sheet". Not `perceive` or `inspect`. `active_inspected` stayed empty. | "I couldn't tell you the requested information; you will need another source." | CONTRACT CONSTRUCTION plus FINAL EMISSION. "look it over" is not an inspect cue (`look at` is). The turn stayed strict-social with the serjeant. The model described the sheet. Emission replaced that with a social inability. Strict-social did not crash. Evaluator FAIL on player-intent anchors is a true fail. |
| 6 | "Does it look like people have handled it recently?" | `perceive` / clarification. Dimensions `wear`, `use`, `appearance`. Referent unresolved. | Voiced catalog line: "Which do you mean? I cannot tell which one that refers to." | REFERENT/DISCOURSE, then a mechanical fallback. Wear was recognized. The sheet from turn 5 was never stored, so "it" had nothing to bind. The model did discuss handling. Emission replaced it with clarification stock. No crash. Evaluator PASS (`legitimate_nonresolution`) follows the unresolved contract and misses the player's object. |

No turn produced an actionable lead, so "I take that step" was not sent. Sequence B was the perception pair above.

### 4. Real live claim-promotion evidence

Yes, on the quote path, not the ledger path.

Turn 2's player-visible line was promoted:

- id `emitted_31c07095f9`
- label `Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates.`
- `source=emitted_npc_claim`
- `claim_ledger_tail` remained null, so this was not an accepted bounded-improvisation entry and was not written as world truth

Turn 3's source contract bound that id. The visible answer did not stay on it. Turns 3 and 4 each replaced `active_claim` with the newest quotation. The turn 4 replacement is not an assertion.

### 5. Strict-social stability

No crash. Every gameplay turn was `purpose=strict_social` on `gpt-4.1-mini`. Turn 6 emitted the voiced clarification that Continuation 3's unvoiced sentence had crashed on. `AssertionError: strict_social_final_invariant` did not recur.

### 6. Mechanical repair / restart

None. The failures are semantic and emission-level. The one mechanical-fix restart was not used.

### 7. Smoke

Not run. Level 2 is not healthy enough. The same final-emission replacement showed up on five of six turns, and both perception turns failed to answer the object the player had named.

### 8. Manual product assessment of smoke turns

Not applicable. No smoke turns.

### 9. Evaluator disagreements

False PASS: 1. Turn 6. The gate passed a clarification the player did not need, because the contract had already dropped the posted sheet.

False FAIL: 1. Turn 2. The gate failed a wear clarification the player did not ask for. The visible line is a rumor, which is what the question asked for.

True FAIL: turns 3 and 5. True PASS for the visible text: turns 1 and 4. Turn 1's pass does not see the discarded model rumor.

### 10. Remaining semantic failure clusters

1. Final emission. On an ordinary strict-social turn the model's sentence is often replaced by `format_structured_fact_social_line` ("Word is, ...") or by catalog inability ("cannot verify", "another source", "Which do you mean?"). A correct source contract and a correct wear contract still do not reach the player. This is the recurring family.
2. Claim discourse. A new "Word is" quote replaces `active_claim` even on a follow-up that was supposed to stay on the previous claim. A quote that merely contains "say" is also promoted. The slot does not stay an NPC claim the player can keep asking about.
3. Perception establishment. Naming a sheet with "look it over" binds an explicit target but does not open `inspect`/`perceive` and does not fill `active_inspected`. The next wear question is then unresolved.
4. Cue collision. The wear/use pattern `come through` fires on "as they come through," so a question about travelers becomes a perception clarification.
5. Referential action. Not observed live. No lead was stored, including after the serjeant pointed at the muddy footprints.

Deterministic coverage of indirect source, confidence, unique-lead actions, and wear routing remains intact. These live misses are downstream of cue breadth, discourse promotion, and strict-social replacement.

### 11. Mechanical and prose-quality observations

Recorded separately from semantic correctness:

- "I have heard talk, but I cannot verify it."
- "I couldn't tell you the requested information; you will need another source."
- "Which do you mean? I cannot tell which one that refers to."

Turn 6's clarification is the intended voiced fallback and it did not crash. It is still stock DM speech. No prose repair was made.

### 12. Cost accounting

| Bucket | Used |
|---|---:|
| Focused completed turns | 6 |
| Focused aborted turns | 0 |
| Focused model calls | 7 |
| Mechanical restarts | 0 |
| Smoke turns | 0 |
| Smoke model calls | 0 |
| Full-gate turns | 0 |

The extra call is turn 4's `retry_escalation` after `validator_voice`. The API health ping before gameplay is not included. Token and monetary cost: unavailable. `call_gpt` does not record usage.

### 13. READY FOR FULL SYNTHETIC GATE

No.

Live play did promote one emitted NPC line into `active_claim`, and source/confidence recognition bound whatever claim was current. The recurring strict-social replacement, the unstable claim slot, and the failed wear/object chain are enough to withhold the 40-turn gate. Smoke was not started.

PR-BR: STILL OPEN.

HUMAN PLAYTEST: NOT RECOMMENDED.

## PR-BR Continuation 5 — Semantic-Preserving Final Emission

Date: 2026-09-28. No completion commit. No push. No mechanical restart. No smoke gate. No 4×10 full gate. PR-BR remains open.

### 1. Continuation 4 failure summary

Continuation 4 completed 6 turns and withheld smoke. The recurring player-facing failure was not a missed contract. Source follow-up ("Who did he hear that from?") had a correct source contract and a model line naming the runner, and the player received "Word is, the patrol route changed after the Ash Compact census choke worsened." Inspection ("look it over") produced a sheet description that the player never saw; the visible line was "I couldn't tell you the requested information; you will need another source." "As they come through" was classified as wear/use. "Look it over" was not inspect, so the next "it" had no `active_inspected`. "I can't say for sure if I trust it" became `active_claim` because "say" matched.

### 2. Exact final-emission replacement causal chain

Traced on the Continuation 4 turns and the emission functions, before the Continuation 5 edits.

Source turn:

1. Generation produced a runner-as-source answer.
2. `build_final_strict_social_response` can reject that line with `first_sentence_illegal:question_rule:first_sentence_not_explicit_answer` even when `assess_contract_satisfaction` already marks it `covered:source`.
3. On rejection, the gate selects a structured stored fact (`format_structured_fact_social_line`, "Word is, ...") or the obligation fallback. Structured-fact selection uses `classify_social_question_dimension`, not the Resolution Contract dimension.
4. If the contract is on the resolution, `_preserve_resolution_contract_after_gate` would replace an unsatisfied "Word is" line with a source inability. It does not restore the model sentence.
5. `apply_authored_knowledge_realization_to_gm` runs after that preserve step. It did not read the contract. When the current line did not already communicate the stored patrol-route clue, it wrote "Word is, the patrol route changed after the Ash Compact census choke worsened."
6. That writer did not check that the replacement still answered source.

Inspection turn:

1. The contract stayed `ask` / inquiry because "look it over" was outside `_INSPECT_RE`.
2. The model described the sheet.
3. The obligation kind was a question, so `obligation_preserving_fallback_line` emitted "you will need another source."
4. A no-dimension ask is `unchecked`, so preserve does not replace it.

An empty-session diagnostic also returns `reply_speaker_grounding_denied`. That is not the live path. The live speaker was grounded.

### 3. Strict-social role

`build_final_strict_social_response` remains the social final writer. It still filters sentence ownership and still hard-rejects ungrounded speakers, binding mismatches, and consequential invention. Continuation 5 does not disable it. A `first_sentence_illegal` hit no longer discards a line that already resolves the contract when no other blocking reason is present. Unauthorized consequential sentences (`traitor`, `conspiracy`, `murderer`, `secret vault`, `hidden passage`, `true motive`) are stripped and the remaining answer is rebound to the speaker.

### 4. Semantic-preservation design

`semantic_line_view` records whether a line `keeps_answer` (`status == satisfied`) or is merely `compatible` (inability, clarification, partial, unchecked). `retain_resolved_contract_text` keeps a resolved line when a retry would drop it. The retry prompt names the operation and dimension and tells the model not to swap in an unrelated fact. `apply_authored_knowledge_realization_to_gm` refuses a replacement whose contract status is `unsatisfied`, and it refuses a swap that drops a resolved line unless the current text is still inside the replacement (an inspection may append an authored fact). Perception stock is kept only when it is not `unsatisfied` against a line that already resolves the contract.

### 5. Targeted-repair behavior

`_repair_semantic_payload` drops a consequential sentence and rewraps a quote as `Speaker says, "..."`. If that repaired line still resolves the contract and hard-reject is clear, it is emitted as `semantic_payload_repair`. Wholesale catalog fallback runs only after that repair fails. Deterministic fallback that is itself contract-`unsatisfied` is swapped for `obligation_preserving_fallback_line` when that line is compatible.

### 6. Contract-aware fallback behavior

Source inability ("I cannot verify the source or certainty of that earlier claim.") stays the source-compatible terminal line. An unrelated grounded rumor is not accepted as a source answer. Inspection no longer treats "another source" as success: a generic social information line on an inspect/perceive contract is `unsatisfied`. A grounded authored inspection fact may still be appended to a scene line, which is how the tariff-slate "dock fees" realization stays intact.

### 7. active_claim hardening

Quote promotion no longer treats a bare "say" as an assertion. The assert pattern requires a claim frame ("word is", "I heard", "they say", "Travelers say", and the same for he/she/they/someone/runner/guard/serjeant). A hedge such as "I can't say for sure" is not promoted unless a strong claim frame is also present. Rejected text is not written into the slot by this path.

### 8. Inspection and wear parser repairs

`_INSPECT_RE` now includes "look … over", "take a closer/careful/good/long look", and "closer look", alongside the existing inspect/examine/look at/check/study forms. Bare "come through" is no longer wear or use. "People/someone/anybody/anyone/folks come through" still is. "Does it look like people use this often?" remains use.

### 9. Deterministic results

169 passed, 0 failed. Continuation 4's band was 156. The increase is 13 tests in `tests/test_pr_br_resolution_contract.py` (48 to 61), including real `/api/chat` cases. The other files in the band did not change count:

- `tests/test_pr_br_resolution_contract.py` — 61
- `tests/test_pr_bp_live_resolution_routing.py` — 23
- `tests/test_playability_eval.py` — 26
- `tests/test_bounded_improvisation_authority.py` — 5
- `tests/test_perception_narration_authority_audible_non_invention.py` — 29
- `tests/test_playability_smoke.py` — 4
- `tests/test_prompt_context_public_prompt_boundary.py` — 5
- `tests/test_referenced_surface_grounding_inspection_resolution.py` — 16

### 10. Focused live results

Artifact: `artifacts/pr_br_continuation5/20260928T110249Z`. Preflight `ok=true`, `health_class=healthy`, gameplay model `gpt-4.1-mini`. Isolated storage. Five completed turns, zero aborted, five model calls, zero retries. No mechanical restart. The source follow-up was not sent because no `active_claim` was stored. Smoke was not started.

| Turn | Player | Contract | Final vs model | Class |
|---|---|---|---|---|
| 1 | What rumor are travelers repeating? | ask, no dimension | Catalog "I have heard talk, but I cannot verify it." Model had named woods hearsay. | PLAYER-FACING SEMANTIC FAILURE |
| 2 | Repeat that rumor | ask, no dimension | "I will not carry out that request; you will need another route." | PLAYER-FACING SEMANTIC FAILURE |
| 3 | Look the posted sheet over | inspect, target posted sheet | "The inspection establishes no further reliable detail about gate_serjeant." Model had listed taxes, curfew, and the missing patrol. `active_inspected` was still the sheet. | PLAYER-FACING SEMANTIC FAILURE |
| 4 | What does it actually say? | ask, ambiguous | "Which do you mean?" The sheet slot existed, but this question did not bind it. | Contract/referent miss. Clarification matches the contract that was built. |
| 5 | Does it look like people use this often? | perceive, use+appearance, inherited sheet | The use answer is in the visible line. Status `partial` because appearance was also tagged and not covered. | ACCEPTABLE for use |

### 11. Generated-candidate vs final-output comparison

Turns 1–3: the model line answered the player and the visible line did not. Preservation did not save them. Turns 1–2 have no dimension, so both sides are `unchecked` and `keeps_answer` is false. Turn 3's stock inspection line is also `satisfied` under the eight-word rule, so a resolved description and a generic stand-in look the same to the guard. Turn 5 is the one case where the useful payload reached the player. The automated destruction counter flagged only turn 5, because `partial` is not `keeps_answer`. That flag is wrong for the player-visible use answer. Manual count of semantic-destroying replacements: 3.

### 12. Smoke results

Not reached. Focused live was not healthy.

### 13. Evaluator disagreements

False PASS: 2. Turn 1 passed an unchecked catalog inability. Turn 3 passed because the generic inspection line scored `inspection_addressed`.

False FAIL: 0. Turn 2's FAIL matches the action-refusal line.

Turn 4's PASS follows the ambiguous contract. Turn 5's PASS matches the surviving use answer.

### 14. Remaining failure clusters

1. No-dimension answers are invisible to preservation. A rumor with no source/confidence dimension is `unchecked`, so a catalog inability or an action refusal can replace it. That also blocks `active_claim`, so the source follow-up never runs.
2. The eight-word inspection rule treats "The inspection establishes no further reliable detail about gate_serjeant" as a resolved inspection. The sheet description is discarded and the guard allows it.
3. `active_inspected` is stored for "look it over", and a later wear "it" binds it. "What does it actually say?" is still ambiguous. Binding is not consistent for every follow-up.
4. Continuation 4's "Word is" source swap is covered by the new authored-knowledge guard and the deterministic source tests. It was not re-observed live, because the claim slot was never filled.

### 15. Prose-quality observations

Separate from the semantic failures. The stock lines are mechanical: "I have heard talk, but I cannot verify it.", "I will not carry out that request; you will need another route.", "The inspection establishes no further reliable detail about gate_serjeant.", and "Which do you mean? I cannot tell which one that refers to." Turn 5's use answer is ordinary NPC speech and is not a prose task. No narration-quality pass was made.

### 16. Cost accounting

| Bucket | Used |
|---|---:|
| Deterministic tests | 169 passed, 0 failed |
| Focused completed turns | 5 |
| Focused aborted turns | 0 |
| Focused model calls | 5 |
| Focused retries | 0 |
| Mechanical restarts | 0 |
| Smoke turns | 0 |
| Smoke model calls | 0 |
| Full-gate turns | 0 |

The API health ping is not included. One budgeted focused turn was left unused after turns 1–3 had already replaced useful answers. Token and monetary cost: unavailable. `call_gpt` does not record usage.

### 17. READY FOR FULL SYNTHETIC GATE

No.

Preservation, contract-aware refusal of an unsatisfied replacement, speaker/consequential repair, claim-frame hardening, "look it over", and the "come through" false positive are in the deterministic band. Live play still replaced useful rumor and inspection lines, and it never reached a source follow-up. That is not a healthy focused gate.

PR-BR: STILL OPEN.

HUMAN PLAYTEST: NOT RECOMMENDED.

## PR-BR Continuation 6 — Contract Satisfaction Semantics

HEAD at the start of this continuation: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. PR-BR stays open. No commit. No push. No 4×10 gate. No smoke.

### 1. Continuation 5 findings

Continuation 5 made semantic-preserving emission work when the contract was right and the checker agreed the candidate answered it. Focused live still failed because "satisfies the contract" was either unchecked or too easy:

- A dimensionless rumor and "I have heard talk, but I cannot verify it." were both `unchecked` / `no_dimension`.
- "Repeat that rumor." was the same no-dimension ask, so a generic action refusal could stand in for a restatement.
- An eight-word inspection shape marked "no further reliable detail about gate_serjeant" as `inspection_addressed` even when the contract target was the posted sheet.
- "What does it actually say?" did not inherit `active_inspected`. "Does it look like people use this often?" did.

### 2. Previous satisfaction architecture

Statuses already existed and were reused: `satisfied`, `partial`, `unsatisfied`, `legitimate_nonresolution`, `unchecked`, `not_applicable`. `keeps_answer` is only `satisfied`. `unchecked` stayed compatible with emission, so a no-dimension line was not protected and was not rejected.

Inspection with no dimension returned `satisfied` / `inspection_addressed` once the reply was at least eight words. Appearance had a similar length backstop. Target identity was not required. A missing subject defaulted to compatible.

### 3. Root causes

1. `dimension = none` on `ask` returned `unchecked`, so operation-specific requests were not evaluated.
2. Repeat was not an operation, so a generic action refusal looked like an ordinary miss or an action result.
3. Inspection satisfaction used length and inspection-shaped prose, then labeled the contract target as the answer target even when the sentence was about someone else.
4. Content questions ("what does it say", "what is written on it") did not prefer an unambiguous `active_inspected` object. Wear/use already had that preference.
5. A response that never named the target, and did not use a pronoun, was still treated as compatible when no rival noun was found.

### 4. New satisfaction semantics

No new status names. Each assessment now also carries `resolution_kind` (`answer`, `inability`, `refusal`, `clarification`, `acknowledgement`, `unrelated`) and target / operation / dimension compatibility. Emission and the evaluator read that same assessment.

A line is an answer only when it is compatible with the operation and the target and it actually resolves the request. A tied inability, refusal, or clarification is `legitimate_nonresolution`. Topic acknowledgement, a wrong target, a new rumor on a repeat, and a generic action refusal on a non-action request stay `unsatisfied`. Fallbacks go through the same function. A `satisfied` or `legitimate_nonresolution` line is not replaced by an unsatisfied stock line, except when referenced-surface authority (abstract, hidden, unsupported, authored visible/interactable) must still override invented content.

### 5. Dimensionless-operation handling

`ask` with no dimension and a specific question word or rumor/news cue is evaluated. A content-bearing report or a direct claim is `satisfied`. "There has been talk." and "I have heard talk, but I cannot verify it." are `unsatisfied` / `topic_acknowledgement`. "I do not know what rumor is being repeated." is a valid inability. An unrelated scene fact is `unsatisfied`.

Live residue: a multi-sentence answer that opens with the rumor and then stages the crowd is scored `unrelated_fact` on the whole paragraph. A non-answer with several leftover words, "No one at hand answers that directly—the question hangs in the noise.", is scored `inquiry_answered` because it misses the narrow negative patterns and clears the three-word payload test.

### 6. Repeat / restatement handling

`repeat` is its own operation. With one active claim, the reply must overlap that claim (paraphrase is enough). A different rumor is `repeat_new_content`. "I will not carry out that request; you will need another route." is `unsatisfied`. "I will not repeat that rumor." is a refusal, not an answer. The echo strip no longer eats a refusal that contains the player's words.

### 7. Target-aware inspection handling

`inspect` / `perceive` / content requests compare the requested target with the answer's subject. Aliases cover sheet, notice, posting, and placard. `paper` is not an alias, so loose papers in the room are not the posted sheet. "The inspection establishes no further reliable detail about gate_serjeant." is `target_incompatible`. A sheet that lists a curfew, or a short "The sheet is blank.", can be `satisfied`. Word count does not decide it. The verb "mark" no longer counts as wear, so "bells mark the ward" is not a wear observation.

### 8. Valid inability and refusal

An inability or refusal counts only when it is tied to the operation and the target, or to the requested perception dimension. "You can't read the posted sheet while it is sealed." is valid. A generic "another route" is not an inspection result. The sound/smell fallback stays the existing scene-level line so a listen-for-whispers request is not answered by naming whispers. Wear, use, and object inspection fallbacks name the contract target.

### 9. active_inspected follow-up repair

"What does it actually say?" and "What is written on it?" set dimension `content` and, with one inspected object and no competing object, inherit that object. "What did he say?" does not. Two object referents ("the sheet or the ledger") ask for clarification. "Does it look like people use this often?" still binds the inspected sheet and still requires use.

### 10. Deterministic results

`tests/test_pr_br_resolution_contract.py` plus the Continuation 5 regression band (`test_pr_bp_live_resolution_routing`, `test_playability_eval`, `test_bounded_improvisation_authority`, `test_perception_narration_authority_audible_non_invention`, `test_playability_smoke`, `test_prompt_context_public_prompt_boundary`, `test_referenced_surface_grounding_inspection_resolution`): **180 passed, 0 failed**.

The new cases cover dimensionless rumor answer / acknowledgement / inability / unrelated fact, repeat same / new / generic refusal / legitimate refusal, right-target and wrong-target inspection, long wrong-target and short right-target, sealed-sheet inability, content follow-up, two-object clarification, wear/use, source, action, and wrong-target versus target-specific fallbacks. `test_real_path_rumor_repeat_and_sheet_content` posts those five shapes through `/api/chat`.

### 11. Focused live results

Artifact: `artifacts/pr_br_continuation6/20260928T224142Z`. Model `gpt-4.1-mini`. Isolated storage. 5 completed turns, 0 aborted, 5 model calls. Stop rule did not fire (one destruction, threshold two). Smoke was not run.

| Turn | Request | Contract | Model | Player-visible | Checker |
|---|---|---|---|---|---|
| 1 | What rumor are travelers repeating? | ask, no dimension | Rumor about a missing-patrol warning, then crowd staging. Whole paragraph `unsatisfied`. | "No one at hand answers that directly—the question hangs in the noise." | Final `satisfied` / `inquiry_answered`. Misclassified. |
| 2 | Repeat that rumor. | repeat, inherited claim | Restates the patrol warning. `satisfied`. | Same warning, then a scene-momentum splice ("sharpens when you look again"). | `satisfied`. Content continues. Prose is broken. |
| 3 | Look the posted sheet over. | inspect, posted sheet | Taxes, curfew, missing patrol. `satisfied`. | "You look again…" plus the notice board listing taxes, curfew, and the missing patrol. | `satisfied`. Right target. Not the serjeant. |
| 4 | What does it actually say? | ask, content, posted sheet inherited | The same announcements. `satisfied`. | "The inspection establishes no further reliable detail about posted sheet." | Final `legitimate_nonresolution`. Useful answer replaced. |
| 5 | Does it look like people use this often? | perceive, use+appearance, posted sheet | Worn edges, many hands. `partial`. | That use description reached the player. | `partial`. Preserved. |

### 12. Candidate, satisfaction, and final output

Turn 1 is the remaining dimensionless hole. The opening sentence "I can tell that the notice board… travelers are murmuring about" is `satisfied` by itself. The full model paragraph, which then describes watchers and refugees, is `unrelated_fact`. The emitted non-answer has enough words that are not in the question, so it is `inquiry_answered`.

Turn 3 shows target-aware inspection working on the live path: the visible line names the notice board's taxes, curfew, and patrol warning, not the gate serjeant.

Turn 4 shows referent repair working and emission still dropping a satisfied content answer in favor of a target-specific inability.

Turn 5 shows the Continuation 5 positive case still holds.

### 13. Smoke

Not reached. Focused play did not give healthy dimensionless satisfaction.

### 14. Manual assessment

Turn 1: PLAYER-FACING SEMANTIC FAILURE. Layer: satisfaction. The contract was the right dimensionless ask. The visible line does not give a rumor, an inability, or a refusal, and it was marked satisfied. Evaluator PASS is false.

Turn 2: ACCEPTABLE on the claim, with mechanical prose. Repeat bound the prior claim. The visible sentence is spliced with scene momentum.

Turn 3: ACCEPTABLE. Inspect target is the posted sheet. The listed contents are the sheet's, inside a stock "you look again" frame.

Turn 4: PLAYER-FACING SEMANTIC FAILURE. Layer: final emission. The contract and the inspected referent are right. A satisfied content candidate was replaced by a sheet-specific inability. Evaluator PASS matches that inability; it does not notice the discarded candidate.

Turn 5: ACCEPTABLE. Use, the sheet, and the generated wear description all reached the player.

### 15. Evaluator disagreements

False PASS: 1 (turn 1). False FAIL: 0. Turns 3 and 5 agree with the player-visible result. Turn 4's PASS agrees with the emitted inability and misses the discarded candidate. Turn 2's PASS agrees that the patrol warning is still present.

### 16. Remaining systemic failure clusters

1. Dimensionless satisfaction still treats a non-answer with several leftover words as `inquiry_answered`, and it rejects a whole paragraph when a good first sentence is followed by scene staging.
2. A satisfied content follow-up can still be replaced by a target-specific inability after the referent has been bound correctly.
3. Scene-momentum splicing still glues "sharpens when you look again" onto an otherwise matching repeat.

Not re-observed: wrong-target inspection accepted as the gate serjeant; wear/use "come through" false positive; source/confidence collapse; action collapse.

### 17. Mechanical and prose observations

Separate from the semantic failures. Turn 2's repeat is grammatically broken by the momentum append. Turn 3's inspection opens with "Nothing new resolves into evidence" and then lists the sheet. Turn 4's inability is mechanical and names "posted sheet" without an article. Turn 5's use answer is ordinary model prose.

### 18. Cost accounting

| Bucket | Used |
|---|---:|
| Deterministic tests | 180 passed, 0 failed |
| Focused completed turns | 5 |
| Focused aborted turns | 0 |
| Focused model calls | 5 |
| Focused retries | 0 |
| Mechanical restarts | 0 |
| Smoke turns | 0 |
| Smoke model calls | 0 |
| Full-gate turns | 0 |

Token and monetary cost: unavailable. `call_gpt` does not record usage. The API health ping is not included. One budgeted focused turn was unused. Smoke budget was not spent.

### 19. READY FOR FULL SYNTHETIC GATE

No.

Dimensionless satisfaction is not healthy in live play, and one satisfied content answer was replaced by an inability. Inspection target compatibility and the wear/use follow-up did hold. That is not enough for the full gate.

PR-BR: STILL OPEN.

HUMAN PLAYTEST: NOT RECOMMENDED.

## PR-BR Continuation 7 — Resolution-Outcome Precedence & Post-Resolution Integrity

HEAD remains `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. This continuation is uncommitted. PR-BR stays open. No commit. No push. No smoke gate. No 4×10 gate.

### 1. Continuation 6 manual reassessment

The Continuation 6 automated result of 5/5 semantic PASS is not successful validation. Artifact `artifacts/pr_br_continuation6/20260928T224142Z`.

| Turn | Player-facing result | Automated label |
|---|---|---|
| 1 rumor | FAIL. Final text was "No one at hand answers that directly—the question hangs in the noise." | `satisfied` / `answer` |
| 2 repeat | FAIL. Patrol warning spliced into unrelated census prose and broken grammar. | `satisfied` |
| 3 inspect sheet | ACCEPTABLE. Taxes, curfew, and the missing patrol reached the player. | PASS |
| 4 sheet content | FAIL. A satisfied content answer became "The inspection establishes no further reliable detail about posted sheet." `destroyed=True`. | `legitimate_nonresolution` |
| 5 wear/use | ACCEPTABLE. Target, wear, and a useful observation reached the player. | PASS |

Manual result: 2/5 acceptable.

### 2. Turn 1 false-satisfaction root cause

The model produced a rumor. Speaker grounding (`narrator_neutral`) replaced it with the bridge line "No one at hand answers that directly—the question hangs in the noise." `_assess_dimensionless_inquiry` then scored that line `satisfied` / `inquiry_answered` / `answer` because the negative-resolution check did not recognize "no one at hand answers" or "the question hangs." Authored-knowledge preservation then kept the line as already resolved. The evaluator upgraded that status to PASS.

### 3. Turn 2 repeat and scene-momentum root cause

The visible splice was not the paragraph-break scene-momentum append. The glued phrase "sharpens when you look again … still competes for notice" is the observe-perception fallback, applied as a whole-response replacement (`final_emission_gate:narrative_safe_fallback`, with a scene-momentum tag also present). Overlap with the patrol claim still scored `repeat_restated` / `satisfied`, so contamination was invisible. The model restatement itself was not recovered, because the contaminated paragraph did not `keeps_answer`.

### 4. Turn 4 answer-downgrade root cause

The model content answer was `satisfied` and named taxes, curfew, and the missing patrol. `apply_authored_knowledge_realization_to_gm` found no matching authored fact and called grounded social absence. `player_facing_invents_unauthored_social_fact` returned true on an identity hit such as "Cinderwatch Gate," which is not a consequential invention. The replacement was `strict_social_ownership_terminal_fallback`. The content dimension forces obligation kind `INSPECTION`, so the line became "The inspection establishes no further reliable detail about posted sheet." The final emission gate then repeated that same inability through the anti-reset continuation. This ran in the narration hub before finalize, so the satisfying candidate was already the inability. No authority, grounding, speaker, or formatting blocker invalidated the sheet contents. The weaker outcome was selected because ignorance was easier.

### 5. Outcome-precedence design

Precedence is categorical, on the existing statuses. A `satisfied` answer outranks a partial answer. A partial answer outranks `legitimate_nonresolution`, `unsatisfied`, inability, refusal, and clarification. `prefer_stronger_resolution` rejects that downgrade when the current text still `keeps_answer` and is not invalidated.

`invalidated=True` is a hard override. It is set for abstract, hidden, or unsupported perception authority, and for an unsupported perception verdict. A locally repaired answer is not put back over those. Visible and interactable authored surfaces are not blocking, so a posted-sheet answer is not replaced by stock filing-shelf prose.

`genuine_resolution_blocker` is narrower than the social identity regex: consequential invention, a price, or a redirect ("ask the X", "go to"). A repairable local defect is stripped first. Only a genuinely invalid or unavailable answer accepts nonresolution.

Call sites that previously swapped a valid answer: speaker `narrator_neutral` and canonical rewrite, grounded social absence, referential-clarity and visibility hard replace, scene-momentum append, perception non-invention, and the scene-stall terminal retry fallback. Finalize then runs `select_preserved_answer`.

### 6. Nonresolution truthfulness

An explicit non-answer ("no one answers", "the question hangs", "no answer was given") is `legitimate_nonresolution` / `inability`, not `answer`, even when the sentence is topical and grammatical. If another sentence in the same response actually reports the requested content, the text is not treated as only a non-answer. "I do not know" remains a valid inability. A nonresolution is not emitted while a permitted, authority-safe observation of that same contract still exists.

### 7. Repeat-content continuity

Repeat compares the response to the stored claim, not to rumor vocabulary. A faithful paraphrase is `satisfied`. An unrelated claim is not. A claim plus a contaminating sentence (the observe-splice templates, or a sentence with almost no claim overlap) is `partial`, reasons `repeat_restated` and `repeat_contaminated`, and does not `keeps_answer`. Atmosphere that leaves the claim intact stays `satisfied`. Repair drops contaminated sentences and keeps the claim-bearing remainder when that remainder still answers.

### 8. Scene-momentum integrity

After a satisfied answer, `enforce_scene_momentum` appends only when `continuation_preserves_resolution` accepts the joined text. An unsafe beat is not appended. The satisfied answer is emitted alone. The observe-perception splice is rejected by the same precedence check when a valid answer is already in hand.

### 9. Final satisfaction check

`select_preserved_answer` assesses the player-visible text after repair and optional momentum. Pre-append satisfaction is not the emission decision. Diagnostics on `emission_debug.outcome_precedence` record downgrade attempted, rejected, reason, recovery used and source, destroyed, scene momentum appended, final outcome kind, and final satisfaction.

### 10. Recovery behavior

If post-processing leaves an unsatisfied line, a weaker nonresolution, or a corrupted repeat after a valid answer existed, recovery prefers the last authority-safe satisfied candidate, then a targeted local repair of it. `destroyed=True` with no stronger valid resolution is not a successful final status. The evaluator fails explicit non-answers, contaminated repeats, and a destroyed answer whose final status is not `satisfied`. A genuine inability still passes.

### 11. Deterministic results

`tests/test_pr_br_outcome_precedence.py` covers matrix A–R and one `/api/chat` path through rumor, repeat, sheet inspection, content, and wear. The Continuation 6 regression band plus that file: **198 passed, 0 failed**.

### 12. Five-turn live transcript

Artifact `artifacts/pr_br_continuation7/20260929T004855Z`. Isolated storage. Natural phrasing. Model `gpt-4.1-mini`. One call per turn. No retries.

Turn 1. Player: "What rumor are the travelers here repeating?"

GM: "I can't swear to the full details, but the travelers gathered near the muddy gate line seem to be whispering about the sudden disappearance of a local patrol. From what I saw, there's talk of strange delays farther along the eastern caravan routes, possibly tied to increased Ash Compact census checks that have tightened the choke point. The accounts are fragmented and conflicting—some mention an ambush, others hint at bureaucratic snares. If you want clearer answers, keeping an ear on the threadbare watchers and refugees there might be your best next step."

Turn 2. Player: "Could you repeat that rumor?"

GM: "I can't swear to the full details, but the travelers gathered near the muddy gate line seem to be whispering about the sudden disappearance of a local patrol."

Turn 3. Player: "I'll look the posted sheet over."

GM: "You look again. Nothing new resolves into evidence. What you can actually see is the notice board lists taxes, curfew rules, and a warning about a missing patrol."

Turn 4. Player: "What does it actually say?"

GM: "The notice board currently shows three main things: updated taxes that local merchants and travelers must pay, new curfew rules that restrict movement after dark, and a posted warning about a recently missing patrol. The details on the patrol note are limited; it names the group as part of the city watch and indicates their absence without explanation. This has unsettled both the guards and the crowd. For now, the actual cause or circumstances behind the patrol's disappearance remain unclear, with whispers only and no official statement. You might watch and listen among the threadbare watchers and refugees clustered nearby for more concrete leads."

Turn 5. Player: "Does it look like people handle it often?"

GM: "The posted sheet looks well-handled enough to remain legible despite the weather, though it's smeared from repeated touches. Judging by the worn edges and the steady presence of a gate serjeant keeping an eye on it, the notice board is frequently consulted by travelers and locals alike. Still, the recent warning about the missing patrol has unsettled both the crowd and the guards, making this handling more tense and vigilant than usual. To learn how often exactly or who maintains it, shadowing t"

### 13. Manual human-DM assessment

Standard: would a player reasonably believe the immediate request had been addressed?

Turn 1: ACCEPTABLE. The response states the rumor. The hedge is not an explicit non-answer. Recovery restored the model text after a downgrade attempt (`post_processing_destroyed_answer`).

Turn 2: ACCEPTABLE as a shorter restatement of the core rumor. Grammar is intact. No unrelated splice. The eastern-delay and ambush elaboration from turn 1 is absent because the stored claim label was clipped to the first sentence plus a stray "F".

Turn 3: ACCEPTABLE. The posted sheet is the target. Taxes, curfew, and the patrol warning are what the player can see. The stock "nothing new" frame is the same mechanical wrapper accepted in Continuation 6.

Turn 4: ACCEPTABLE. Content is bound to the posted sheet. Taxes, curfew, and the patrol note reach the player. This is not the inability line.

Turn 5: ACCEPTABLE on the request, with a visible tail defect. Wear and frequent handling are stated, on the inherited sheet. The last sentence is cut mid-word at "shadowing t". The model sentence was complete. Tag `final_emission_gate:neutral_speaker_grounding_bridge` is present. Precedence did not recover, because the truncated text still `keeps_answer` for appearance.

Manual: 5/5 acceptable on the immediate request. Turn 5 is not clean emission.

### 14. Runtime/evaluator disagreement

Evaluator: 5/5 PASS. Probe semantic destructions: 0.

| Turn | Evaluator | Manual | Disagreement |
|---|---|---|---|
| 1 | PASS / satisfied answer | ACCEPTABLE | No |
| 2 | PASS / satisfied answer | ACCEPTABLE shortened repeat | No on the binary result. The evaluator does not report the clipped claim. |
| 3 | PASS / satisfied answer | ACCEPTABLE | No |
| 4 | PASS / satisfied answer | ACCEPTABLE | No |
| 5 | PASS / satisfied answer | ACCEPTABLE, tail truncated | No on whether the wear question was answered. The evaluator does not fail the mid-word cut. |

Evaluator false PASS on an explicit non-answer: 0. Valid answer replaced by an unjustified nonresolution in the player-visible text: 0. Scene-momentum splice corruption: 0.

### 15. Remaining systemic failure clusters

1. Discourse claim labels are clipped (the live claim ends "patrol. F"). Repeat continuity can only preserve that prefix, so a faithful longer rumor is shortened.
2. A speaker-grounding bridge can still cut a keeping answer mid-token. Precedence treats the cut as success when the earlier sentences still satisfy the contract.
3. Inspection can still be wrapped in "You look again. Nothing new resolves into evidence." before the real sheet contents. The target and the contents survive.

Not re-observed in this sample: explicit non-answer marked `satisfied` / `answer`; observe-perception splice of a repeat; satisfied sheet content replaced by "no further reliable detail."

### 16. Cost accounting

| Bucket | Used |
|---|---:|
| Deterministic tests | 198 passed, 0 failed |
| Focused completed turns | 5 |
| Focused aborted turns | 0 |
| Focused model calls | 5 |
| Focused retries | 0 |
| Mechanical restarts | 0 |
| Smoke turns | 0 |
| Full-gate turns | 0 |

Token and monetary cost: unavailable. `call_gpt` does not record usage.

### 17. READY FOR SMOKE GATE

No.

The Continuation 6 failure classes did not recur, and each focused request received a recognizable answer. Smoke is not justified yet: the repeat referent is a clipped claim, and one player-visible wear answer still ends mid-word.

### 18. READY FOR FULL SYNTHETIC GATE

No.

PR-BR: STILL OPEN.

HUMAN PLAYTEST: NOT RECOMMENDED.

## PR-BR Continuation 8 — Independent 10-Turn Smoke Validation

Validation only. No production semantic changes. No repair after the smoke. No second smoke. No 4×10 gate. HEAD remains `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. The validation target is the uncommitted PR-BR working tree, which includes Continuation 7. PR-BR stays open.

### 1. Preflight

API preflight: healthy (`2026-09-29T10:24:29Z`).

Deterministic band: **198 passed, 0 failed**. Same files as Continuation 7.

Continuation 7 is present: `prefer_stronger_resolution`, `explicit_nonanswer_response`, and `select_preserved_answer` are in `game/resolution_contract.py`.

The smoke uses `POST /api/chat` with isolated storage. One runner invocation checked preflight before the app lifespan and exited with no gameplay turns. The check was moved to after startup. The smoke below is the single gameplay run.

### 2. Personas

Ordinary goals. Not the Continuation 7 rumor / repeat / sheet / content / wear script.

Persona A, `social_goal`. Get through the gate tonight by finding someone who can say what a traveler must do. Talk, follow what they say, and act on it.

Persona B, `explore_action`. Learn the yard well enough to move through it. Look, use something ordinary, ask a nearby person, then take the next safe step.

The next line uses only the persona agenda and the previous player-visible reply. A single stall press is allowed. Hidden state, contracts, and evaluator results are not shown to the player policy.

### 3. Completed turns

10. Five per persona.

### 4. Aborted turns

0.

### 5. Model calls

12. Retries: 2, both `echo_or_repetition` on explore turns 3 and 4. Token telemetry: unavailable.

### 6. Player-visible transcript

Artifact `artifacts/pr_br_continuation8/20260929T102429Z/transcript.md`.

Social 1. Player: "I look for someone on duty and ask what a traveler has to do to pass the gate tonight."

GM: "You find no such thing among what is actually present. The notice board lists taxes, curfew rules, and a warning about a missing patrol."

The model had already answered: papers, nightly toll, inspection, and a tighter curfew, spoken by a gate serjeant.

Social 2. Player: "I ask them to name the actual snag, and who can deal with it."

GM: "The guard shakes their head. \"I have heard talk, but I cannot verify it.\""

The model had named the missing patrol and the guard captain.

Social 3. Player: "I take that to the person they named, or I ask the one in front of me what they need from me."

GM: "The reference cannot be identified clearly enough to resolve without clarification."

The model had said nobody was named, and that the person in front was holding papers and would not say what they needed.

Social 4. Player: "I do the concrete thing they just described."

GM: "No reliable source here can verify the requested information; another source is needed."

Social 5. Player: "Before I move on, I ask what trouble I should watch for in the next few minutes."

GM: The gate guard names the missing patrol, bandit talk on the northwest mud track, delays, and tighter scrutiny. This matches the model.

Explore 1. Player: "I take in the yard and walk toward the nearest ordinary thing a traveler could look at or use."

GM: "The reference cannot be identified clearly enough to resolve without clarification."

The model had chosen the notice board and described it.

Explore 2. Player: "I examine it up close and try to work out what people use it for."

GM: "Nothing here matches that. What you can actually see is the notice board lists taxes, curfew rules, and a warning about a missing patrol."

The model had explained that people use the board for taxes, curfew, and the patrol warning.

Explore 3. Player: "I try the simplest ordinary use, without forcing or breaking anything."

GM: "Inspecting the notice board again, you find no indication of practical devices or tools meant for public use here. ... leaving you without a straightforward utility to engage."

The first model call had the player read the board. An echo retry replaced that with the refusal.

Explore 4. Player: "If anyone is close enough to hear me, I ask what people usually do with it."

GM: People check the board for taxes, curfew, and the patrol warning. The model had a serjeant say the same thing. The paraphrase still answers.

Explore 5. Player: "I take the next safe step that follows from what I just found."

GM: The player steps up through the muddy queue toward the serjeant and the board. Model and final match.

### 7. Manual human-DM assessment

Social: FAIL, FAIL, FAIL, FAIL, PASS. **1/5.**

Explore: FAIL, FAIL, FAIL, PASS, PASS. **2/5.**

Overall: **3/10.**

### 8. Runtime/evaluator result

Social: FAIL, PASS, PASS, FAIL, PASS.

Explore: PASS, FAIL, PASS, PASS, PASS.

Evaluator PASS: **7/10.**

### 9. Evaluator disagreements

False PASS: 4. Social 2, social 3, explore 1, explore 3.

False FAIL: 0.

True PASS: 3. True FAIL: 3.

### 10. Failure layers

| Turn | Layer |
|---|---|
| Social 1 | contract construction. "On duty" became an inspectable object named `duty`. |
| Social 2 | satisfaction. "I have heard talk, but I cannot verify it." was `satisfied`. |
| Social 3 | final emission. A usable account of the person in front was replaced by a clarification template. |
| Social 4 | contract construction. "I do the concrete thing" became an `ask` about `duty`, then a source-verification line. |
| Explore 1 | final emission. A chosen notice board was replaced by the clarification template. |
| Explore 2 | contract construction. The target string is the previous player sentence. |
| Explore 3 | retry. `echo_or_repetition` replaced "you read the board" with "no utility to engage." |

### 11. Recurring failure families

1. A usable model answer is replaced by a stock inability, clarification, or "nothing matches" line.
2. Ordinary social and action lines are parsed as object inspection, including the non-object `duty` and a whole previous player sentence stored as the target.
3. The evaluator accepts several of those replacements as PASS.

This blocked ordinary play for both personas. It is not an isolated imperfection.

### 12. Claim fidelity

No repeat was requested. No clipped-claim repeat occurred. `active_claim` stayed null on all 10 turns, including after social turn 5 stated a patrol and bandit claim.

### 13. Truncation

No player-visible mid-token or mid-sentence cut. The Continuation 7 "shadowing t" defect did not recur.

### 14. Scene momentum

`scene_momentum_appended` was false on the recorded turns. No observe-style splice corrupted an answer.

### 15. Valid-answer destruction

7 turns. Social 1–4 and explore 1–3. In each, the generated text addressed the request more directly than the line the player received. Precedence diagnostics reported `destroyed: false` on those turns, so the signal did not catch this family.

### 16. Prose, separately

Explore 4 flattens the serjeant's spoken answer into narrator summary and still answers. Explore 5 is atmospheric and still moves the player. The "nothing new resolves into evidence" inspection frame did not appear. Those are not the failures above.

### 17. Cost accounting

| Bucket | Used |
|---|---:|
| Deterministic preflight | 198 passed, 0 failed |
| Smoke completed turns | 10 |
| Smoke aborted turns | 0 |
| Smoke model calls | 12 |
| Smoke retries | 2 |
| Mechanical restarts | 0 |
| Full-gate turns | 0 |
| Semantic repairs after smoke | 0 |

Token and monetary cost: unavailable.

### 18. READY FOR FULL SYNTHETIC GATE

No.

Three of ten immediate requests were addressed. The same replacement family recurred across both personas, and the evaluator false-PASSed four of the failures.

### 19. HUMAN PLAYTEST

NOT YET AUTHORIZED.

PR-BR: STILL OPEN.

## PR-BR Continuation 9 — Resolution-Contract Construction Architecture Discovery

Discovery only. No production semantic change. No phrase-specific parser patch. No model-assisted interpreter. No evaluator change. No Continuation 8 repair. No live gameplay turn. No synthetic-player turn. No evaluator-model call. No gameplay-model call. HEAD remains `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. PR-BR stays open. Do not begin PR-BS.

Static replay of `construct_resolution_contract` on the Continuation 8 lines reproduces the recorded contracts. Contract ids `rc_c0ed9887a705` through `rc_2910ee50d755` hash from those lines at turn indexes 1–8 and 10. Explore turn 4’s id `rc_0613368c0760` hashes from the segmented remainder `I ask what people usually do with it` at turn 9, after `segment_mixed_player_turn` removed the leading `If …` clause. The two personas shared one session: `_isolate_storage` rewrites campaign and character files and does not reset `session.json`, and the contract ids are consecutive from turn 1 to turn 10.

### 1. Continuation 8 findings

Manual human-DM PASS: 3/10. Evaluator PASS: 7/10. False PASS: 4. False FAIL: 0.

Useful model answer replaced: 7 (social 1–4, explore 1–3). Generic fallback: 6. Referent loss: 6. Action collapse: 3. Claim clipping: 0. Mid-token truncation: 0. Scene-momentum splice: 0.

The dominant failure is upstream of satisfaction and emission. A usable narration already existed. Deterministic interpretation had already committed a different meaning, and later gates enforced that meaning.

Previous residuals did not dominate. Claim clipping, mid-token truncation, and scene-momentum corruption stayed quiet. The open problem is Resolution Contract construction and the discourse slots it writes.

### 2. Five-of-five versus three-of-ten

Continuation 7’s manual 5/5 used the rumor / repeat / sheet / content / wear script. Those forms are the forms the deterministic suite and the parser were built to recognize: `look it over`, `what does it say`, `who told you`, `when I did that`, `take that step`.

Continuation 8 used ordinary compound requests that are outside that lexicon:

- locate a person and ask a procedural question
- act on “the concrete thing they just described”
- look toward the nearest ordinary thing
- examine “it” and ask what it is for
- take the next safe step

The 5/5 result shows that the tuned path can stay healthy. The 3/10 result shows that health does not transfer to ordinary compound language. The mechanism is a combination, and parser brittleness plus discourse poisoning are the part that creates the later failures:

- The parser assigns one confident operation and one confident target from the first lexical hit.
- That target is stored as `active_inspected` with no entity check.
- Later pronouns bind to it because it is the only filled slot.
- Emission and the evaluator then treat the contract as the request.

Evaluator weakness is real and secondary. Social 2’s stock line “I have heard talk, but I cannot verify it.” was scored `satisfied` because `_REPORT_FRAME_RE` treats “heard” as a report and the leftover words clear the dimensionless-inquiry threshold. Social 3 and explore 1 were scored PASS because an ambiguous contract plus a clarification template is `legitimate_nonresolution`. Those scores hide the damage. They do not create the wrong contract.

### 3. Current construction pipeline

Path from raw player text to the contract that downstream code trusts:

| Stage | Where | Kind | Abstain? |
|---|---|---|---|
| Turn segmentation | `segment_mixed_player_turn` in `game/intent_parser.py` | Deterministic regex. Strips a leading `If …,` into `contingency_text` and leaves `declared_action_text`. | No confidence. Drops the frame silently. |
| Intent classification | Observe, then investigate, then interact, in `parse` order around `game/intent_parser.py` 1913–2003 | Deterministic regex. First match wins. `look for X` is investigate and extracts X before `ask` is considered. | No. |
| Surface classification | `classify_referenced_surface` | Deterministic token-prefix match against interactables, visible facts, hidden facts, and abstract references. | Unsupported or untargeted, still a classification. |
| Resolution prompt | Social and exploration engines copy `normalized_action.prompt` or the raw line | State-assisted only as a string choice. Explore 4’s contract was built from the segmented remainder, not the full line. | No. |
| Dimension detection | `_dimensions` | Regex lexicon: sound, smell, appearance, wear, use, change, source, confidence, location, time, next step, content. | Empty tuple. No confidence. |
| Explicit target | `_explicit_target` | Ordered regex: look-over, what-does, inspect/examine/look-at, smell, then `at|on` + noun until `and` or punctuation. | Empty string. A hit is `explicit_player` and `ambiguous=false`. |
| Action-target fallback | `construct_resolution_contract` | Uses `normalized_action.target_id` when it is mentioned in the text or is a known focus id, and when it does not echo the utterance. | Skips pronouns and utterance echoes. |
| Referent resolution | `_resolve_referent` | Ordered rules: lead, referential action, prior action, claim, explicit target, scene, inspected object, person, place, anaphor. | `ambiguous` or `unresolved` for a few listed shapes. |
| Operation | `_operation` | Ordered regex plus `action_type in {observe, investigate}` forcing `inspect`. One operation survives. | No. Default is `ask`. |
| Clarification override | `construct_resolution_contract` | If `ambiguous` or an unresolved anaphor, `request_kind` becomes clarification. Operation is left as already chosen. | Yes, for those cues only. |
| Epistemic mode | same function | Consequential lexicon, else dimension class, else unknown. | No. |
| Obligation | `derive_interaction_obligation`, then `_kind_from_contract` | The contract can override the obligation kind. | No. |
| Discourse commit | `commit_discourse_focus` | Inspect/perceive with a target writes `active_inspected`. Ambiguous contracts do not update slots and do not clear them. | Scene change hides scene-bound slots. |
| Generation projection | `generation_projection` | Deterministic sentence: “Resolve {operation} for {target}”. Prompt instruction says to obey it and not infer a different request. | Clarification sentence when already ambiguous. |
| Narration | Existing gameplay model call | Model-assisted prose. No structured interpretation is returned. | The model can ignore the constraint in prose. Later gates can still discard that prose. |
| Satisfaction and emission | `assess_contract_satisfaction`, perception grounding, social absence, first-mention, obligation fallback | Deterministic comparison of visible text to the contract. | `unchecked` only when there is no dimension and the inquiry is not specific. |

No stage in construction is model-assisted. No stage has a confidence score. Abstention exists only for a small set of ambiguity cues. A successful lexical extraction cannot abstain.

### 4. Operation selection

`_operation` returns exactly one pair. Candidates are not retained. There is no semantic head, no supporting action, and no ordered sub-action.

Precedence is source order, then surface order:

1. Clarification, repeat, lead, referential action, confirm, social-action request, physical verb.
2. A perception dimension, with inspect winning over perceive when `_INSPECT_RE` matches and the dimension is not sound, smell, appearance, or change.
3. `_INSPECT_RE` or intent type `observe` / `investigate`.
4. Non-question interact, custom, travel, or attack, if no perception dimension.
5. Default `ask`.

For “I look for someone on duty and ask …”, the intent parser matches `look for` in `INVESTIGATE_PATTERNS` before `INTERACT_PATTERNS` sees `ask`. The extracted span is the rest of the sentence. `_operation` then sees `action_type=investigate` and returns `inspect`. The ask is discarded.

“I examine it and try to work out …” is the same shape: `examine` is investigate, so the contract is `inspect` even though the semantic head is a use question. The use dimension is detected separately and attached to the inspect.

“I take that to the person they named …” matches `_REFERENTIAL_ACTION_RE` (`I take that`) and becomes `act`, then clarification, because no lead and no `last_attempted_action` exist. “I do the concrete thing they just described” does not match that regex, because the regex requires `do that|this|it`, so it falls through to `ask` and inherits `duty`.

Surface verb order wins. The goal of the sentence is not represented.

### 5. Target extraction

`_AT_OBJECT_RE` is `(?:at|on)` plus a short span that ends at ` and `, punctuation, or end of string.

“on duty and ask” therefore yields target `duty`. `_explicit_target` returns it. `_resolve_referent` treats any non-empty explicit target as `explicit_player` / `object` / reason `explicit_current_turn_target`, with `ambiguous=false`. Nothing asks whether `duty` is an entity.

`_EXPLICIT_TARGET_RE` is `examine|inspect|look at|…` plus up to 60 characters that are not `.?! ,`. The pronoun reject `_PRONOUN_TARGET_RE` matches only when the entire span is a bare pronoun. “it up close and try to work out what people use it for” fails that test and becomes the object id. Discourse binding never runs, because the explicit-target branch returns first.

“look at or use” yields explicit target `or use`. The later rule `if explicit_target and "or" in explicit_target` then discards the target and marks `multiple_object_referents`. That is why explore 1 has operation `inspect`, dimension `use`, and `target_ref=null`, with a clarification constraint.

Stop conditions are punctuation, ` and `, or a 40–60 character cap. There is no noun-phrase boundary, no confidence, and no abstain on a successful match. A clause becomes an object id whenever it survives the pronoun-whole-string check.

A second extractor disagrees. `extract_inspection_target` ignores a single slug such as `duty` and reparses the sentence. For social 1 it returns `someone on duty and ask what a traveler has to do to pass the gate tonight`. Prefix matching then accepts the first content token `someone` against the hidden fact that contains “someone already past the checkpoint.” Authority becomes `authored_hidden`. The player-facing line for that authority is “You find no such thing among what is actually present.”

So social 1 has three targets at once: contract object `duty`, surface target `someone` classified as hidden, and the model’s gate serjeant.

### 6. Discourse and referent ownership

| Slot | Owner | Written by | Corrected by |
|---|---|---|---|
| `active_interlocutor` | `discourse_focus`, filled from `interaction_context` when empty | Contract interlocutor or social npc id | Next social commit, or scene change |
| `active_claim` | Claim ledger, pointed at by discourse | Accepted emitted NPC claims only | A later accepted claim. Rejected claims are not promoted. |
| `active_actionable_lead` | Scene pending leads, else discourse | `follow` or a lead discourse pointer | Next lead commit |
| `active_inspected` | Discourse commit from an inspect/perceive contract | `target_ref.id_or_text` with no entity existence check | The next inspect/perceive that has a target. Ambiguous turns do not clear it. |
| `last_attempted_action` | Discourse commit from act/follow/confirm | Raw input label | Next action commit |
| Parser target | This turn’s contract | Explicit regex or inherited slot | Not a persistent owner |
| Obligation target | `derive_interaction_obligation` | Action, resolution, or interlocutor, then contract kind override | Not persistent |
| Scene entity | Scene and world documents | Authored content | Not by the contract |
| Transcript / generation context | Prompt assembly | Raw text plus `generation_projection` | Not a referent owner |

Canonical referent identity is split. The contract’s `target_ref` is what generation, satisfaction, and several fallbacks trust. `active_inspected` is what the next anaphor trusts. Scene entities are what surface classification trusts. The model’s prose is what the player would have trusted, and it is not a referent owner.

Those four can disagree on the same turn. Precedence at emission time is the contract and the surface classifier, not the model prose. A malformed explicit target is persistent because `commit_discourse_focus` copies it into `active_inspected` whenever operation is `inspect` or `perceive` and provenance is not `unresolved`. Social 1 did that for `duty`. The slot was still `duty` on social 5 and on explore 1. Explore 2 replaced it with the sentence-sized span, which then persisted through explore 5.

Model prose cannot correct a slot. There is no eviction for a referent that fails to canonicalize, and no rebind from a later better interpretation. Scene change hides scene-bound slots. That is the only automatic clear.

### 7. Multi-turn error propagation

Cascade A, social, one session.

1. Player: “I look for someone on duty and ask what a traveler has to do to pass the gate tonight.”
2. Parser: intent `investigate`, explicit target `duty`, operation `inspect`, provenance `explicit_player`, `ambiguous=false`.
3. Contract constraint: “Resolve inspect for duty.”
4. Discourse: `active_inspected={id:duty, label:duty}`.
5. Model: serjeant states papers, nightly toll, inspection, and a tighter curfew.
6. Surface classifier: hidden, because token `someone` hits a hidden fact. Perception grounding force-replaces investigate text. Final: “You find no such thing among what is actually present,” plus the notice-board fact.
7. Satisfaction of that final line is `legitimate_nonresolution`. `destroyed=false`.
8. Turn 2: “I ask them …” has no explicit target. `them`/`it` match `_ANAPHOR_RE`. The person branch does not fire because `active_interlocutor` is empty. The only filled slot is `duty`, so reason `unambiguous_discourse_referent`. Constraint: “Resolve ask for duty.”
9. Model names the missing patrol and the guard captain. Referential-clarity and grounded-social-absence replace it with “I have heard talk, but I cannot verify it.” That line is scored `satisfied`.
10. Turn 3: “I take that …” is a referential action with no lead and no prior action, so clarification. The model describes the person in front. Final text is the clarification template. `duty` is not cleared.
11. Turn 4: “I do the concrete thing they just described” is `ask` about inherited `duty`. Final: “No reliable source here can verify the requested information.”
12. Turn 5 has no anaphor (`no_anaphor`), so the poisoned slot is ignored. The ask is answered and kept. The slot is still `duty`.

One explicit-target error on turn 1 caused the wrong operation, the hidden-surface replacement, and three further turns that either asked about `duty` or refused to guess. Turn 5 recovered only because it did not use a pronoun.

Cascade B, same session, explore lines.

1. Explore 1: “look at or use” becomes explicit `or use`, then `multiple_object_referents`. Constraint forbids guessing. The model chooses the notice board and describes it. Final text is the clarification template. `active_inspected` remains `duty` because an ambiguous commit does not write and does not clear.
2. Explore 2: “I examine it up close …” sets explicit target to the clause after `examine`. That overrides discourse. Operation `inspect`, dimension `use`. The model explains the notice board. Final text is “Nothing here matches that,” which is the unsupported-surface line. Discourse now stores the clause as the object id.
3. Explore 3: “the simplest ordinary use” inherits that clause (`unique_inspected_object`) and is `perceive`/`use`. The first model call has the player read the board. An `echo_or_repetition` retry replaces it with “no utility to engage.” Evaluator PASS.
4. Explore 4’s contract is built from `I ask what people usually do with it` after the `If …` frame is stripped. `it` inherits the clause. The spoken answer survives in paraphrase, so this turn passes, while the slot stays wrong.
5. Explore 5 is labeled `ask` about that same clause because `that` is an anaphor and the clause is the only referent. The visible move still happens to be a reasonable step. The contract target remains the old sentence.

The early parser error is a major source of multi-turn brittleness. Later turns fail because they inherit the bad slot, and because emission then rejects a model answer that followed the player’s actual referent.

### 8. Model versus contract disagreement

Confirmed on social 1–4 and explore 1–3. The contract says inspect `duty`, ask `duty`, clarify, or inspect a sentence-sized object. The model excerpt answers the human request: passage requirements, the patrol and the captain, the person in front, the notice board, reading the board.

The disagreement is structurally visible and unused. `turns.json` stores `operation`, `target_ref`, and `model_excerpt` side by side. Nothing compares them. `outcome_precedence.destroyed` is false on the destroyed turns. `assess_contract_satisfaction` scores player-visible text against the contract. It does not extract a second interpretation from the candidate.

`generation_projection` tells the model the contract is the request, and the prompt says not to infer a different one. The model still used the raw line and the scene. Downstream code does not treat that as a challenge. Perception force-replace, social-absence replacement, first-mention replacement, and the clarification template all run after generation and can discard the candidate. The contract is the authority those gates defend.

Candidate semantics are not independently structured after generation. They exist only as prose.

### 9. What should remain deterministic

These stay deterministic after any interpretation change:

- Canonical entity ids once a proposal has been accepted
- Scene, character, and clue lookup
- PR-BN authority: authored, hidden, consequential, NPC-claim, incidental
- Permission and action legality
- Claim promotion from accepted ledger entries only
- Discourse-slot persistence and scene-bound expiry
- Contract schema validation
- Final state mutation and persistence
- Satisfaction of a validated contract
- Outcome-precedence and semantic-preserving emission
- The rule that model text does not become world truth

Moving those to the model would trade a recoverable interpretation error for an authority error.

### 10. What requires open-ended language understanding

The Continuation 8 failures are ordinary language, not rare jargon:

- Primary intent in “look for someone and ask …”
- `look for` a person versus `look at` an object
- “on duty” as a modifier of a person, not an object
- Where a target noun phrase ends
- Pronouns whose antecedent is a person just introduced in prose, or an object chosen by the previous narration
- Ellipsis: “the concrete thing they just described,” “the next safe step”
- Whether one utterance is a question, an action, an observation, or a question with a setup action

Bounded heuristics can keep the cases they already own: a single known verb plus a name that canonicalizes to a scene entity, or a lone pronoun with exactly one valid canonical slot. They cannot cover the open set of compounds and modifiers. Adding “on duty is not an object” or “strip words after it” would document these ten lines and leave the next paraphrase to fail the same way.

### 11. Existing model-assisted interpretation

The gameplay model already receives the raw player line, the scene, recent transcript, and `resolution_contract.constraint`. That is enough context to infer operation, target, and outcome, and the Continuation 8 excerpts show that it often did.

That inference is not structured. No field stores a model operation, target, dimension, interlocutor, or confidence. The only model product is prose. Deterministic code cannot see the model’s interpretation except by guessing from the prose, and it currently does not do that.

### 12. Option A — Harden the current deterministic parser

Keep regex construction as the semantic authority. Add tighter spans, verb precedence, and stopword lists aimed at the known failures.

Deterministic: everything, including intent. Model calls: the existing narration call only. State authority: unchanged, and still able to commit a free-text object id. Hallucination risk: low from the model, high from confident wrong parses. Latency: unchanged. Testability: high for the phrases that get a new regex, weak for the next unseen compound. Migration: small. Generalization: poor. The Continuation 7 suite already passed at 198 while the independent smoke passed 3/10 manual. More phrase rules extend that gap.

Compatible with PR-BN, PR-BP, and PR-BR as a patch on the input. It does not fix the architectural mismatch those systems then enforce.

### 13. Option B — Hybrid, deterministic primary, model on the leftovers

Keep today’s parser. When it sets `ambiguous`, or when several verbs match, call the model for an interpretation and let deterministic code validate it.

Deterministic: the fast path, plus validation. Model-assisted: only the cases the current parser already admits it cannot parse. Extra call: only on that subset. State authority: still the contract, after validation on the slow path. Hallucination risk: concentrated on the slow path, and still present on the fast path whenever the parser is confidently wrong. Latency: an extra short call on ambiguous turns. Testability: fast path stays fixture-tested; slow path needs recorded proposals. Migration: moderate. Generalization: partial.

This misses the actual failure mode. Social 1 and explore 2 were not ambiguous. They were `explicit_player` and `ambiguous=false`. A hybrid that trusts the parser until the parser abstains will still commit `duty` and the sentence-sized object. Option B is the right cost control only if the fast path is allowed to run when a target already canonicalizes, and must abstain otherwise.

### 14. Option C — Structured model proposal, deterministic validation

The model proposes a typed interpretation. Deterministic code accepts, canonicalizes, or rejects it. The accepted result is the Resolution Contract. Narration and the evaluator keep consuming that contract.

Proposed fields, and no others required for v1:

- `primary_operation` from the existing operation enum
- `supporting_operation`, at most one
- `target_ref` as a candidate id or a discourse pointer, never a raw clause
- `interlocutor_id`
- `dimension` from the existing dimension enum
- `referenced_prior` as claim, action, object, or none
- `confidence` as `high` or `low`
- `clarification_required` as a boolean

Deterministic validation then checks the proposal against the scene and the discourse slots. Generation runs from the validated contract, as it does now.

Model calls: zero extra on the fast path; one short structured call before narration when the fast path abstains. The fast path is the narrow case Option A already handles well: one verb, and a target that resolves to an existing entity id or the single valid canonical slot. Compounds, modifiers, unresolved pronouns, and non-canonical spans abstain. They do not guess.

State authority: the model proposes. It does not write world state, claims, or discourse. Only a validated canonical id or an existing discourse pointer may be committed.

Hallucination risk: a proposal can name a real but wrong entity. Validation rejects ids that are not in the candidate set. It cannot reject a wrong choice among real candidates except by requiring clarification when confidence is low or more than one candidate fits.

Latency and cost: most tuned single-intent turns stay on the current narration call alone. Uncertain turns pay one small structured completion, then the existing narration call. That is the cost of not letting a wrong contract destroy the narration.

Testability: schema tests, validator tests, and recorded proposal fixtures. The Continuation 8 lines become fixtures with hand-specified expected proposals. Live inference is not required for the regression suite. A later tiny smoke checks that a real proposal survives validation.

Migration: the contract, obligation, authority taxonomy, satisfaction, precedence, and evaluator stay. The change is the input boundary of `construct_resolution_contract`.

Generalization: this is the smallest boundary that can represent “find someone and ask” without a new regex for each compound. Compatibility with PR-BN, PR-BP, and PR-BR is direct: they remain the consumers of a validated contract.

### 15. Cost and latency

| | Option A | Option B as “parser first” | Option C with abstaining fast path |
|---|---|---|---|
| Extra model call on an obvious single-target turn | No | No | No |
| Extra model call on a compound or non-canonical turn | No | Only if the parser already set `ambiguous` | Yes, one structured call before narration |
| Continuation 8 social 1 and explore 2 | Still wrong, no extra call | Still wrong, because they were confident | Structured call, then validation |
| Narration call | Kept | Kept | Kept, after the contract exists |
| Output size of the extra call | — | Small JSON | Small JSON |

Combining interpretation into the narration call would avoid the extra round trip and would also let the model narrate before the contract is validated. That recreates the current split: prose means one thing, the enforced contract means another. The structured call belongs before narration, and only when the fast path abstains.

### 16. Hallucination and state integrity

Current failure: a confident wrong contract deletes a useful candidate and stores the wrong referent.

Model-assisted failure: a wrong proposal. Detectable, because the proposal is typed and the validator either canonicalizes it or returns clarification. Recoverable, because a rejected proposal does not write `active_inspected`. A wrong-but-canonical choice among real entities remains possible, and low confidence must clarify instead of picking.

The validator must refuse:

- a target id that is not a scene entity, addressable, visible fact, or an existing discourse pointer
- an interlocutor id that is not addressable in the scene
- a prior claim or action id that is not already in discourse or the claim ledger
- an operation or dimension outside the existing enums
- any proposal field being copied into world truth, hidden facts, or the claim ledger
- a low-confidence or multi-candidate target being stored as an object id

Semantic interpretation must not become unauthorized world invention. PR-BN’s authority classes stay on the far side of this boundary.

### 17. Testability

| Layer | Option A | Option C |
|---|---|---|
| Parser unit tests | More phrase fixtures | Fast-path fixtures only |
| Recorded proposal fixtures | None | Validator accepts or rejects frozen JSON. No paid call. |
| Schema tests | Existing contract | Proposal schema plus existing contract |
| Integration | Real path with a stub proposal | Same |
| Adversarial paraphrase | A new regex per family | Validator tests: clause spans, modifiers, and unknown ids become clarification |
| Live smoke | Still required before a gate | Still required, and still later |

The regression suite must not require live inference. Continuation 8’s ten lines are the first recorded fixtures. Expected proposals for those lines can be written by hand from the human-DM reading already in `MANUAL_ASSESSMENT.md`.

### 18. Recommended architecture

Option C, with the abstaining fast path from the critique of Option B.

The next implementation cycle should change the input boundary of Resolution Contract construction. Open-ended intent, target span, and pronoun binding should arrive as a typed proposal. Deterministic code should validate and canonicalize that proposal into the existing contract. The fast path may build the contract itself only when the target already canonicalizes to one existing entity or one valid discourse slot. A non-canonical lexical hit must abstain. It must not become `explicit_player`.

Why this one: Continuation 8 shows confident lexical hits (`duty`, a sentence after `examine`, `or use`) that the current ambiguity flag does not catch, and it shows the model already recovering the human meaning in prose that the contract then discards. Option A extends the lexicon that just failed to generalize. Option B, if the current parser remains primary, never sees those hits as uncertain. Option C moves semantic interpretation to a proposal and leaves state authority where PR-BN and PR-BR already put it.

Minimum boundary: proposal schema, validator, abstaining fast path, discourse commit only for canonical referents, and fixture tests for the ten Continuation 8 lines. No new planner. No second narration. No phrase list for “on duty” or “look for.”

### 19. Minimum migration plan

Stage 1. Add the proposal schema and a pure validator. Feed it hand-written proposals for the Continuation 8 lines. `duty`, the examine-clause, and `or use` must come back as clarification or as a canonical scene referent, never as a new object id. No live model.

Stage 2. Teach `construct_resolution_contract` to accept a validated proposal when one is supplied, and to abstain when today’s explicit-target regex produces a span that does not canonicalize. Keep the current regex path only for spans that already match an entity or a single valid slot.

Stage 3. On abstention, perform one structured interpretation call, validate it, then build the contract and the existing generation projection. Narration stays the second call and still obeys the validated constraint.

Stage 4. Change `commit_discourse_focus` so a non-canonical target is not written. A later validated canonical referent may replace a slot whose id never resolved to an entity. Ambiguous turns stay non-writing, and they also stop leaving a known-bad slot in place when the new proposal identifies that slot as invalid.

Stage 5. Deterministic regression: the existing PR-BR band must stay green, plus the new proposal fixtures. No paraphrase farm.

Stage 6. A tiny live check, on the order of the Continuation 8 social-1 and explore-2 lines only, after Stages 1–5. No 4×10 gate in that continuation.

### 20. Existing architecture preserved

This is a correction of the input boundary, not a replacement.

Keep:

- The Resolution Contract as the authoritative per-turn record after validation
- Interaction Obligation, derived from that contract
- PR-BN authority taxonomy and the ban on model-created world facts
- Discourse slots and claim promotion from accepted ledger entries
- Satisfaction semantics and resolution-outcome precedence
- Semantic-preserving final emission
- Evaluator consumption of the shared contract

Surface classification remains the authority check for whether an inspection target exists and is visible. It should run on a canonical target, not on the first token of a mis-extracted clause.

### 21. Implementation risks

- The fast path stays too greedy and still commits a non-canonical span. The abstain rule has to be “canonicalize or abstain,” not “regex hit means explicit.”
- The model proposes a real, wrong entity. Low confidence and multi-candidate ties must clarify.
- An extra call adds latency on uncertain turns. It must not run on the fast path, and it must not be a second narration.
- The evaluator will still PASS a clarification that the validated contract requested. That is correct only when the abstention was honest. Fixture review has to check the contract, not only the evaluator label.
- `destroyed=false` will keep hiding replacements until a later continuation compares the candidate to the validated contract. That signal is out of scope here.
- Persona isolation in the Continuation 8 runner does not reset the session. A future smoke must start a new session per persona or the next cascade will be contaminated before turn 1.

### 22. Unanswered questions

No recorded structured proposal exists. The Continuation 8 model excerpts show the right meaning in prose. They do not show whether a structured call would emit the right JSON. That question needs a later, explicitly authorized, fixture-bounded call. It was not run here.

It is also unsettled how often the fast path would fire on real play. The Continuation 7 script would mostly stay on it. The Continuation 8 script would mostly abstain. A broader rate needs a later sample.

### 23. Live-model calls consumed

0 gameplay turns. 0 synthetic-player turns. 0 evaluator-model calls. 0 gameplay-model calls.

Evidence used: Continuation 7 and 8 artifacts, `game/resolution_contract.py`, `game/discourse_state.py`, `game/intent_parser.py`, `game/referenced_surface.py`, `game/perception_grounding.py`, `game/live_resolution.py`, `game/prompt_context.py`, `game/playability_eval.py`, and a local deterministic replay of `construct_resolution_contract` and `classify_referenced_surface`. No API budget was spent.

### 24. Recommended next implementation continuation

PR-BR Continuation 10 should implement Stages 1 and 2 only: the proposal schema, the deterministic validator, abstention when a lexical target does not canonicalize, and recorded fixtures for the Continuation 8 lines.

It should not call the model, should not patch individual phrases, should not change satisfaction or the evaluator, and should not run a smoke or the 4×10 gate.

PR-BR: STILL OPEN.

READY FOR FULL SYNTHETIC GATE: NO.

HUMAN PLAYTEST: NOT AUTHORIZED.

## PR-BR Continuation 10 — Typed Interpretation Proposal & Canonical-or-Abstain Validation

Date: 2026-09-29

Stages 1–2 only. No live model-assisted interpretation. No live gameplay. No synthetic smoke. No 4×10 gate. No completion commit. PR-BR remains open. PR-BS was not started.

HEAD remains `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`.

### 1. Continuation 9 architecture decision

Continuation 9 concluded that the Resolution Contract is still the right authoritative record, and that the failures came from building that record directly out of raw lexical spans. The recommended boundary was a typed interpretation proposal, then deterministic validation and canonicalization, then the existing contract. A deterministic fast path may succeed only when it canonicalizes. Otherwise it abstains. A future model may propose meaning. It may not decide world existence, facts, consequential invention, canonical identity, mutation, permissions, claim truth, or action legality.

### 2. Previous contract-construction boundary

Before this continuation, `construct_resolution_contract` treated a regex span as an explicit target with `ambiguous=false`. `commit_discourse_focus` then wrote that string into `active_inspected`. Later pronouns inherited it. "on duty" became `object:duty`. "examine it up close …" became a sentence-sized object. "look for … and ask" became `inspect` because the earlier investigation cue won.

### 3. New interpretation boundary

```
raw player text
  -> deterministic Interpretation Proposal
  -> deterministic validation / canonicalization
  -> validated interpretation OR abstention
  -> Resolution Contract only from that result
  -> discourse commit only when the validation allows it
```

Owner: `game/interpretation_proposal.py`. The contract constructor in `game/resolution_contract.py` builds the proposal and applies the validation before the frozen contract exists. Discourse commit in `game/discourse_state.py` refuses an abstained or blocked contract.

### 4. Interpretation Proposal schema

`InterpretationProposal` is a frozen dataclass. It carries the raw input, provenance source, primary operation, supporting operations, raw target text, proposed target id, capture kind, determiner flag, interlocutor, subject, dimensions, expected resolution, referenced claim / action / inspected ids, advisory confidence, clarification and ambiguity flags, and an operation-conflict flag. It reuses the existing operation and provenance constants. It does not duplicate the Resolution Contract.

`proposal_from_mapping` builds the same object from an untrusted mapping, including a future structured model payload. The mapping is not required to look like a regex result.

### 5. Proposal authority semantics

Constructing or validating a proposal writes no session, entity, discourse slot, claim, NPC, object, or world fact. Tests copy a session around proposal construction and validation and require the copy to match. Only a validated result is copied into the contract, and only that contract may be committed.

### 6. Validator / canonicalizer design

`validate_interpretation_proposal` maps proposed identities onto scene referents and discourse slots, or abstains. It checks operation conflicts, unsupported operations, explicit ambiguity, missing claims, missing prior actions, unknown model interlocutors, malformed spans, and target identity. Self-reported confidence is stored and never read. Two index rows with the same id (a discourse copy and a scene copy) count as one referent.

### 7. Fast-path behavior

The fast path still runs for an explicit known entity, a unique inspected pronoun, a unique claim follow-up, a unique lead, and a short determiner nominal when no catalog is supplied. Success requires the validator to return `validated`. A regex match alone does not set `ambiguous=false` on an unknown span when a catalog is supplied.

### 8. Abstention behavior

Abstention is `validation_status=abstained`, with a reason, failed fields, `clarification_required`, and `model_interpretation_appropriate`. Hard abstention clears the target, sets `operation` to `unresolved`, marks the contract ambiguous, and blocks discourse commit. Generation uses the existing clarification constraint, so the prompt cannot say "Resolve inspect for duty." Abstention is not a new player-facing line.

`insufficient_discourse_context` does not wipe an operation the older constructor already chose. It still blocks commit. That preserves "Take me … toward that place" as `act` and "what can I see from here that confirms …" as `perceive`.

### 9. Operation-conflict handling

`fast_path_operation_families` records inspect, ask, and act families without using order as precedence. Two families abstain as `unresolved_compound_intent`. The implementation does not special-case "ask beats look." "I examine the seal and then ask the sentry" and the reverse utterance both abstain.

### 10. Target canonicalization

A proposed raw string becomes a canonical id only when it matches one scene or discourse referent, or when the unscoped-nominal bridge applies. `duty` has no determiner and no referent, so it cannot become `object:duty`. An unknown noun against a supplied index abstains as `target_not_canonical` and the contract target is null.

### 11. Referent canonicalization

Bare "it" with exactly one inspected object binds that object. A pronoun-headed clause with one inspected object rebinds to that object instead of keeping the clause as an id. No compatible referent abstains. The validator does not invent an object to fill the gap.

### 12. Ambiguity handling

Multiple plausible discourse referents, or two catalog rows that both match the proposed text, abstain as `ambiguous_referent`. A model payload that sets `ambiguous=false` and `confidence=1.0` still abstains when two referents match. "What about that?" with an inspected object and a lead does not pick either one.

### 13. Discourse commit guard

`discourse_commit_blocked` refuses a non-mapping, an ambiguous contract, `validation_status=abstained`, or `discourse_commit_allowed=false`. `commit_discourse_focus` returns before slot writes in those cases. A malformed inspected label is also dropped if a write is otherwise reached. Legacy contracts that lack the new flag still commit, so older tests keep their successful commits.

### 14. Invalid-referent quarantine

An abstained proposal does not create state a later interpretation must undo. The duty compound is committed, `active_inspected` stays empty, and a following "I inspect it" cannot inherit duty. Sessions that already contain a poisoned slot are not scrubbed.

### 15. Continuation 8 regression fixtures

`tests/test_pr_br_interpretation_proposal.py` and `tests/fixtures/pr_br_interpretation/continuation8_shapes.json` cover fixtures A–N plus structural variants: other nouns, other pronouns, other clause lengths, and both orders of examine/ask. The fixture file is the Continuation 11 replay format: raw text, discourse context, optional proposal, validator expectation, and contract shape. Replaying it does not call a model.

### 16. Future model-proposal validation

Model-shaped payloads use `proposal_from_mapping` and the same validator. A real `notice_board` id validates. These abstain: a nonexistent id, `duty` at confidence 1.0, an unsupported operation, a missing claim id, a fabricated prior action, an explicit ambiguity flag, and a confident proposal that matches two boards. Unknown model interlocutors abstain as `unknown_interlocutor`.

### 17. Session-isolation change

`_isolate_storage` in `tools/run_pr_br_level2_probes.py` now unlinks `session.json` and truncates the session log on every persona setup. `test_persona_sessions_do_not_inherit_discourse` saves a persona-A inspected latch, isolates again, and requires persona B's loaded session to lack that latch. No smoke was run.

### 18. Deterministic test results

Focused new file: `tests/test_pr_br_interpretation_proposal.py`, 24 tests, 0 failed.

Broader band, one pytest invocation, junit `artifacts/pr_br_continuation10/junit.xml`:

- 222 tests
- 0 failures
- 0 errors
- 0 skipped

Files: the new interpretation tests, `test_pr_br_resolution_contract.py`, `test_pr_br_outcome_precedence.py`, `test_pr_bp_live_resolution_routing.py`, `test_bounded_improvisation_authority.py`, `test_perception_narration_authority_audible_non_invention.py`, `test_playability_smoke.py`, `test_prompt_context_public_prompt_boundary.py`, `test_referenced_surface_grounding_inspection_resolution.py`, `test_playability_eval.py`.

### 19. Regressions encountered and fixed

Two existing contract tests failed on the first integration pass. "Take me as far as the gate allows toward that place" and "what can I see from here that confirms I am heading the right way" were abstained to `operation=unresolved` because an incidental "that" set `clarification_required`. The insufficient-discourse reason now keeps the lexical operation and still blocks commit.

Pronoun rebind then failed because the inspected id appeared twice, once from discourse and once from the supplied catalog. Same-id rows now count as one referent.

After those fixes the 222-test band passed.

### 20. Temporary compatibility bridges

Documented in `artifacts/pr_br_continuation10/compatibility_bridge.md` and on `COMPATIBILITY_BRIDGE` in `game/interpretation_proposal.py`.

1. Unscoped player nominal. When no canonical index is passed, a short determiner or verb nominal may still be an explicit target. Bare preposition captures, clause spans, and operation conflicts never use it. The live path does not yet pass a scene index, so this bridge is what keeps "posted sheet" and "canvas awning" working. Continuation 11 must pass the index.
2. Abstention reuses the existing clarification obligation. It does not restore the raw lexical target.

### 21. Remaining architectural risks

- The live path still omits the scene index, so an unknown short nominal can still become an explicit target until Continuation 11 passes the catalog.
- Hard abstention currently surfaces as the clarification obligation. That can replace a useful model narration until Continuation 11 routes abstention to structured interpretation first.
- Already-poisoned discourse slots are not removed.
- An insufficient-discourse abstention blocks commit even when the lexical operation is kept, so some unresolved-anaphor turns will not update `last_attempted_action`.
- This is not a general coreference engine or action planner. Compounds abstain rather than being planned.

### 22. Continuation 11 prerequisites

- Call a structured interpreter only when the fast path abstains.
- Feed that payload through `proposal_from_mapping` and `validate_interpretation_proposal`.
- Pass the scene and discourse index on the live path, then remove the unscoped-nominal bridge.
- Interpret abstention before the clarification obligation, so a rejected parse is not immediately a player-facing generic clarification.
- Do not treat model confidence as authority.
- Keep persona session isolation in any later smoke.
- Do not run the 4×10 gate from that first integration.

### 23. Live gameplay turns consumed

0

### 24. Live / evaluator / interpretation model calls consumed

0 gameplay-model calls. 0 evaluator-model calls. 0 interpretation-model calls. 0 synthetic-player turns.

### 25. PR-BR status

PR-BR: STILL OPEN.

READY FOR LIVE MODEL INTERPRETATION INTEGRATION: YES, as Continuation 11, behind the prerequisites in section 22.

READY FOR FULL SYNTHETIC GATE: NO.

HUMAN PLAYTEST: NOT AUTHORIZED.

## PR-BR Continuation 11 — Structured Model Interpretation Integration

Date: 2026-09-29

The live `/api/chat` path now supplies a scene/referent catalog and, only after deterministic abstention, one structured interpretation call. The same Continuation 10 validator accepts or rejects that proposal. PR-BR remains open. PR-BS was not started. No independent 10-turn smoke. No 4×10 gate. No completion commit. No push.

HEAD remains `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. This continuation is uncommitted work on that commit.

### 1. Continuation 10 starting state

Continuation 10 left a typed `InterpretationProposal`, a deterministic canonicalize-or-abstain validator, and two temporary bridges. The ordinary live path passed `canonical_referents=None`, so a short nominal could still become an explicit target through `unscoped_player_nominal`. Abstention went straight to the clarification obligation. Live model calls were 0. The deterministic band was 222/222.

### 2. Scene/referent catalog

`game/scene_referent_catalog.py` builds the catalog from structures that already exist: the current place, public exits, scene interactables and objects, scene addressables, and NPCs already returned by `scene_npcs_in_active_scene`. Discourse slots stay on the focus the validator already reads. Hidden facts are not copied in. This is an index, not a second world model.

### 3. Unscoped player-nominal bridge

Ordinary `/api/chat` always passes that catalog, including an empty list when the scene has no rows. `compatibility_bridge` was null on all six live turns. The `canonical_referents is None` path still exists for callers that omit an index, including older unit tests and the satisfaction fallback in `question_resolution_rule_check` when no contract was attached. That path can still name a short nominal. It is not used to recover from a failed model interpretation. Status on the ordinary live path: removed.

### 4. Interpreter architecture

`game/semantic_interpreter.py` asks one structured question: what the player appears to be asking, doing, or referencing. It returns an `InterpretationProposal` via `proposal_from_mapping`. It does not construct a Resolution Contract, a discourse slot, or a world fact. `construct_resolution_contract` calls it only when a caller passes an interpreter and the fast path abstains with `model_interpretation_appropriate`. `/api/chat` passes `interpret_for_contract`. Pytest sets `ASHEN_DISABLE_LIVE_INTERPRETATION=1`, so the suite does not place interpretation calls.

### 5. Interpreter input

The prompt receives the raw utterance, the abstention reason, candidate id/type/label/aliases, a discourse-focus summary, and at most two prior player-visible lines (`player_input` and `player_facing_text` only). It does not receive hidden facts, resolution metadata, or the generation prompt.

### 6. Structured proposal schema

The model must return the Continuation 10 fields: primary operation, supporting operations, raw target text, proposed target id, interlocutor, conversational subject, dimension, referenced claim/action/inspected ids, ambiguity, clarification, and advisory confidence. Source is forced to `model_assisted`. Raw input is the player text, not a model rewrite. There is no second proposal type.

### 7. Conditional invocation

Flags recorded on the contract construction and in `session.interpretation_telemetry`: `fast_path_used`, `fast_path_abstained`, `model_interpreter_invoked`, proposal accepted, proposal rejected, clarification-after-model, and interpretation API calls. A validated fast path does not call the interpreter. Obvious inspect, unique pronoun, claim follow-up, dimension, and previous-action cases are covered by a test whose interpreter raises if called.

### 8. Deterministic validation boundary

Every model payload goes through `validate_interpretation_proposal`. An explicit `proposed_target_id` must match a catalog id. A fuzzy raw string cannot rescue a different invented id. Unsupported operations abstain. Confidence is ignored. There is no `trusted_model_proposal` or `model_override`.

### 9. Ambiguity and clarification

If the model sets `ambiguous` or `clarification_required`, or the validator finds more than one referent, the contract stays unresolved and the existing clarification constraint is used. Clarification is no longer the immediate result of every fast-path abstention. It is the result when the model is skipped, fails, or cannot produce one valid unambiguous proposal.

### 10. Discourse commit

Commit still runs only when `discourse_commit_allowed` is true. An accepted proposal may set the interlocutor or the canonical inspected object. A rejected or ambiguous proposal does not.

### 11. Invalid proposals

Nonexistent targets, interlocutors, claims, previous actions, and unsupported operations are rejected. Tests cover each case. Rejected proposals do not create `object:duty` or any other pseudo-entity.

### 12. Model-call failure

Transport errors and malformed JSON become a failed interpretation. The turn keeps the abstained contract and the clarification obligation. It does not fall back to the unscoped nominal bridge.

### 13. Retry policy

One semantic interpretation attempt per player turn. Markdown-fence stripping before `json.loads` is mechanical. There is no interpret/reject/reinterpret loop. The OpenAI call uses a strict JSON schema so the provider, not a second inference, constrains the shape.

### 14. Deterministic and stub results

`tests/test_pr_br_model_interpretation.py` and `tests/test_pr_br_interpretation_proposal.py` passed inside the broader band. Categories covered: fast path does not call the interpreter; abstention calls it once; a valid compound proposal becomes an ask contract; nonexistent target, interlocutor, claim, action, and operation are rejected; ambiguity clarifies; malformed output fails closed; rejection does not commit; acceptance commits the guard; a pronoun proposal binds only an existing referent; a named absent entity is rejected; persona referents do not cross; the Continuation 8 compound fixture round-trips.

### 15. Raw `/api/chat` integration

`test_raw_chat_path_uses_the_stubbed_interpreter` posts a compound utterance and then "I examine the notice board." The compound abstains, the stub runs once, the contract is `ask` with `guard_captain`, and discourse commits that interlocutor. The explicit notice-board line fast-paths and does not call the stub. No paid inference.

### 16. Broader regression

One pytest invocation, junit `artifacts/pr_br_continuation11/junit.xml`: 234 tests, 0 failures, 0 errors, 0 skipped. The five live-path failures on the first pass were "posted sheet", "iron latch", and "cooking pot" utterances against a fixture scene that did not list those objects. The shared HTTP fixture now includes them as interactables, so the catalog canonicalizes them instead of the removed bridge.

### 17. Focused live turns

Artifact: `artifacts/pr_br_continuation11/20260930T010945Z`. Six completed turns. One isolated session. Preflight healthy. No repair and no rerun.

| Turn | Input | Fast path | Model | Contract | Manual response | Evaluator |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | look for someone working the gate and ask what is needed tonight | abstain, unresolved compound | yes, ask / gate_guard | correct ask | FAIL | FAIL |
| 2 | go up to the posted notice and work out what people use it for | abstain, insufficient discourse | yes, inspect / notice_board | correct inspect | FAIL | PASS |
| 3 | What does it say about the curfew? | success, inherited notice board | no | correct ask | PASS | PASS |
| 4 | Who from? | success, bare ask | no | FAIL | FAIL | PASS |
| 5 | Fine, I take the step he suggested. | success, bare ask | no | FAIL | FAIL | PASS |
| 6 | I ask him about it. | success, ask about the notice board, him unbound | no | FAIL | FAIL | PASS |

### 18. Manual semantic review

Turns 1 and 2 are the model-assisted path. Both contracts match the immediate request: ask the gate guard what is required tonight, then inspect the notice board for use. Neither reply would convince a player the request was answered. Turn 1 says nothing of that kind is present and then lists the notice board. Turn 2 emits the canned "no reliable use" line. Turn 3 is a real curfew answer and did not need the interpreter. Turns 4 and 5 stayed on an overconfident fast path: "Who from?" did not bind a source, and "take the step he suggested" was classified as ask, after which narration invented a physical step. Turn 6 bound "it" to the notice board and dropped "him".

Manual player-visible semantic PASS: 1/6. Correct contracts: 3/6. Both model-assisted contracts were correct. Neither model-assisted reply was useful.

### 19. Evaluator comparison

Runtime/evaluator PASS: 5/6. False PASS: 4 (turns 2, 4, 5, 6). False FAIL: 0. Turn 1 is a true FAIL. Turn 3 is a true PASS.

### 20. Cost accounting

Completed live gameplay turns: 6. Gameplay-generation model calls: 6. Interpretation model calls: 2. Evaluator model calls: 0 (`evaluate_playability` is local). Generation retries: 0. Aborted calls: 0. Interpretation attempts per interpreted turn: 1.

### 21. Fast path versus interpreted turns

Fast-path live turns: 4. Model-interpreted live turns: 2. The model path was exercised. It was not the majority of the six turns, because several elliptical and referential lines still validated on the fast path and, by design, were not sent to the interpreter.

### 22. Failures and residuals

- Validated ask contracts are still not reliably answered. Turn 1's contract was right and the reply was not.
- Inspect/use on a known notice board still collapses to the generic wear/use inability line.
- Fast-path success on "Who from?" and "I take the step he suggested" prevents interpretation. Continuation 11 does not arbitrate a fast path that already validated.
- Turn 1 wrote `active_claim` as the interlocutor "Gate Guard" rather than a claim. That slot then persisted. The catalog also lists `gate_guard`, `gate_serjeant`, and `guard_captain` together, so "someone working the gate" has more than one canonical person. The model picked an id that exists.

### 23. Remaining architectural risks

The omitted-index nominal bridge remains for non-live callers. A validated fast path can still misread ellipsis and referential action, and this continuation will not spend a model call to contradict it. Discourse commit can still store an interlocutor pointer as `active_claim` when a time dimension is present. Emission can ignore a correct ask contract. Already-poisoned slots are not scrubbed.

### 24. Call coalescing

Not recommended yet, and not implemented. Interpretation has to finish before an authoritative contract exists, and generation is supposed to consume that contract. Folding both into one completion would let the same output decide meaning and narration. The current `responses.create` narration call does not accept a prior structured interpretation channel, so coalescing is not a trivial wiring change.

### 25. Recommended next step

Do not start independent smoke yet. The interpretation boundary accepted two natural abstentions into canonical contracts, and it rejected invented ids in tests, but the player-visible path did not answer those contracts. Next work should make a validated ask contract reach the player, and should stop an interlocutor id from occupying `active_claim`, before a 10-turn smoke.

### 26. PR-BR status

PR-BR: STILL OPEN.

READY FOR INDEPENDENT 10-TURN SMOKE: NO.

READY FOR FULL SYNTHETIC GATE: NO.

HUMAN PLAYTEST: NOT AUTHORIZED.

## PR-BR Continuation 12 — Fast-Path Competence, Discourse Typing & Contract-Honoring Resolution

Date: 2026-09-30

PR-BR remains open. PR-BS was not started. No independent 10-turn smoke. No 4×10 gate. No completion commit. No push. No semantic repair-and-rerun.

HEAD remains `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. This continuation is uncommitted work on that commit.

### 1. Continuation 11 starting evidence

Six live turns. Correct contracts about 3/6. Both model-assisted contracts were correct. Manual player-visible PASS 1/6. Evaluator PASS 5/6, with four false PASS. The interpreter was not the failure. The fast path accepted "Who from?", "Fine, I take the step he suggested.", and "I ask him about it." Turn 1 stored the interlocutor "Gate Guard" as `active_claim`. A correct Gate Guard ask was replaced by "You find no such thing among what is actually present." A correct notice-board use inspection was replaced by "The visible wear and marks establish no reliable use."

### 2. False fast-path root causes

`validate_interpretation_proposal` treated a recognized operation with no remaining target span as success. "Who from?" never matched the source patterns, so it became a bare ask. "I take the step he suggested" did not match the anchored referential-action pattern, so it also became a bare ask. "I ask him about it" bound `it` to the inspected object and never required `him`.

### 3. Semantic-completeness design

Fast-path and discourse-inheritance proposals now pass an operation-aware gap check after canonicalization. A validated model proposal is not re-scored by that check. Gaps abstain with `incomplete_semantic_structure`, which is allowed to call the interpreter once. `construction.semantic_completeness` records the fast path's own result (`sufficient`, `insufficient`, or `not_applied`), even if a later interpretation validates.

Ellipsis is structural: a short wh- or conditional fragment with no content nominal. A referential action is a commitment verb plus a deictic step, lead, or suggestion, or "do what [person] suggested." A multi-reference ask requires both a person pointer and an object pointer to be bound. None of these are exact phrase lists.

### 4. Elliptical routing

"Who from?", "How recently?", and "Where?" become source, time, and location probes. If one active claim exists, the fast path binds it and does not call the interpreter. If it does not, the fast path abstains. "And if I do?" binds a unique previous action or abstains.

### 5. Referential-action routing

"Fine, I take the step he suggested.", "I do what she suggested.", and "Alright, I'll take that step." are actions. A unique previous action or lead lets the fast path succeed. Otherwise the fast path abstains. A reply that puts a foot on a step is `literal_referent_reinterpretation` and is not emitted as a success.

### 6. Multi-reference routing

"I ask him about it" and "I turn to him and ask about it" succeed on the fast path only when the interlocutor and exactly one object or claim are both present. One binding abstains. Two object candidates abstain.

### 7. Discourse-slot type audit

`commit_discourse_focus` wrote `active_claim` whenever the contract dimension was source, confidence, location, or time. Turn 1's discourse pointer was the interlocutor, and its label was "Gate Guard". The old identity check compared that label to the id `gate_guard`, so it did not fire.

### 8. active_claim root cause and fix

A claim slot is written only when the discourse pointer's type is `claim` and the label is a proposition (it contains a predicate, and it is not the interlocutor's id or name). A time dimension on an ask no longer creates a claim. `note_emitted_npc_claim` is unchanged: an accepted emitted assertion still becomes `active_claim`, and a bare name does not.

### 9. Canonical-contract premise preservation

`canonical_existence_denied` marks "You find no such thing among what is actually present" unsatisfied when the contract already names a validated referent. `prefer_stronger_resolution` no longer discards a contract-satisfying answer just because a surface classifier marked the candidate invalid. A consequential or existence-denying candidate can still be rejected. The generation constraint also says the named interlocutor and target are present.

### 10. Gate Guard contradiction

Continuation 11 turn 1's model answer was a real gate requirement. Perception grounding then treated the "look for" wording as a hidden-surface inspection and, because that authority set `invalidated=True`, replaced the answer with the absence line. The absence line is now unsatisfied, and a satisfying answer is kept. The response-type gate also keeps a satisfying ask, inspect, perceive, or repeat answer instead of swapping in the generic action clause ("the attempt produces an immediate result").

### 11. Notice-board use resolution

The useful generated answer ("serves as a clearinghouse") did not match the narrow wear/use cue, so it was scored unsatisfied. The canned wear line matched "no reliable" and was scored as a legitimate inability, then replaced the answer. Use cues now include ordinary function (`serves as`, `purpose`, `clearinghouse`, and the same family). The canned wear line is `generic_use_nonanswer` and cannot win.

### 12. PR-BN authority interaction

Bounded incidental use is still allowed. The change is precedence: a useful functional answer outranks the generic wear line. A specific limit (sealed, illegible, blank, too dark) can still be an inability.

### 13. Valid-answer preservation

The existing `prefer_stronger_resolution` order is unchanged: a satisfied answer beats a weaker close, unless the answer is a genuine blocker. The new case is the `invalidated=True` short circuit, which used to skip that order. Response-type enforcement now returns early when the current text already satisfies an ask, inspect, perceive, or repeat contract.

### 14. Evaluator hardening

The evaluator fails a referential action answered as a physical step, a reply that denies a validated canonical referent, and the canned "no reliable use" line. These checks do not depend on the fast path having classified the turn correctly.

### 15. Deterministic test results

`tests/test_pr_br_continuation12_competence.py` covers fast-path success, elliptical bind and abstain, referential bind and abstain, multi-reference success and partial abstain, interlocutor-not-claim, real claim promotion, Gate Guard premise preservation, notice-board use precedence, and the three evaluator fixtures.

### 16. Raw /api/chat integration

Stubbed model calls, no paid inference. A compound abstention still becomes an ask of the guard, the final text keeps the night-pass answer, and `active_claim` stays empty. A use inspection of the notice board keeps the clearinghouse answer. "Fine, I take the step he suggested." does not emit a foot on a step.

### 17. Broader regression

One pytest invocation, junit `artifacts/pr_br_continuation12/junit.xml`: 256 tests, 0 failures, 0 errors, 0 skipped. The band is the Continuation 11 files plus the new competence tests and `tests/test_final_emission_response_type.py`.

### 18. Focused live-turn table

Artifact: `artifacts/pr_br_continuation12/20260930T111602Z`. Six completed turns. One isolated session. Preflight healthy. No repair and no rerun.

| Turn | Input | Fast path | Model | Contract | Manual | Evaluator |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | look for whoever is minding the gate and ask what it takes tonight | abstain, insufficient discourse | yes, ask / gate_guard | correct ask | FAIL | PASS |
| 2 | How recently? | abstain, incomplete semantics | yes, ask / gate_guard, time | correct ask | FAIL | PASS |
| 3 | I examine the notice board. | success | no | correct inspect | FAIL | PASS |
| 4 | what people use that posted sheet for | success, use / notice board | no | correct perceive | PASS | PASS |
| 5 | I'll do what he just told me to do | abstain, ambiguous referent | yes, act rejected | correct clarification | PASS | PASS |
| 6 | I turn to him and ask about it | abstain, target not canonical | yes, ask / gate_guard about the board | correct ask | FAIL | PASS |

`active_claim` was null after every turn. The interlocutor stayed the gate guard. The notice board became `active_inspected` on turn 3 and stayed there.

### 19. Manual semantic review

Turn 1's contract is the right ask, and the reply admits the guards are there, but nobody answers what it takes to get in. Turn 2's fast path correctly refused a bare "How recently?". The model then produced a usable timing answer about the patrol warning. Final emission replaced it with the source/certainty template. Turn 3's fast path correctly inspected the notice board, and generation listed taxes, curfew, and the missing patrol. Final emission replaced that with the stock "new ground shows itself" frame plus one clue sentence. Turn 4 kept a real account of what the sheet is for. Turn 5 had no prior suggestion; abstaining and asking for clarification is the right result, and it did not become a physical step. Turn 6's contract correctly asks the gate guard about the notice board. Generation said nobody explained entry conditions. Final emission replaced that with the patrol-clue sentence and no speaker.

Manual player-visible semantic PASS: 2/6. Correct authoritative contracts: 6/6. Accepted interpreted contracts: 3/3 (turns 1, 2, and 6). Turn 5's act proposal was rejected, which is the correct authoritative clarification.

### 20. Evaluator comparison

Runtime/evaluator PASS: 6/6. False PASS: 4 (turns 1, 2, 3, 6). False FAIL: 0. Turns 4 and 5 are true PASS. The repaired literal-step, absence-denial, and canned-use fixtures fail in unit tests. The live false PASS are a different family: a destroyed or topical answer that still looks like a nonresolution or a related fact.

### 21. Cost accounting

Completed live gameplay turns: 6. Deterministic fast-path turns: 2. Fast-path abstentions: 4. Interpretation model calls: 4. Gameplay-generation model calls: 7. Evaluator model calls: 0. Generation retries: 1 (turn 6). Aborted calls: 0. Interpretation attempts per interpreted turn: 1.

Fast-path routing correct: 6/6. Correct interpreted contracts: 3/4 interpreted turns (the fourth was a correct rejection). Correct total contracts: 6/6.

### 22. Remaining failure families

- A useful generated answer can still be replaced after the contract is satisfied. Turn 2 lost a timing answer to the claim-follow-up template. Turn 3 lost a full board reading to the clue frame. Turn 6 lost the social line to the same clue sentence.
- The evaluator still passes those replacements.
- An elliptical time question with no active claim can be interpreted as a time question about a nearby topic. That routing is allowed. The failure is the later template, not the abstention.

### 23. State-integrity findings

No interlocutor was stored as `active_claim`. No canonical referent was denied with "no such thing." No literal foot-on-a-step resolution occurred. Discourse slots stayed typed. No state-integrity failure was observed.

### 24. Recommended next step

Do not start independent smoke. The fast path now abstains when it is incomplete, claim typing holds, and a useful use-answer can survive. The remaining break is downstream replacement of an already useful candidate on ask and inspect turns. Next work should stop the claim-follow-up template and the clue frame from replacing a candidate that already answers the contract. Do not start PR-BS.

### 25. PR-BR status

PR-BR: STILL OPEN.

READY FOR INDEPENDENT 10-TURN SMOKE: NO.

READY FOR FULL SYNTHETIC GATE: NO.

HUMAN PLAYTEST: NOT AUTHORIZED.

## PR-BR Continuation 13 — Post-Generation Semantic Preservation & Social Resolution Execution

Date: 2026-09-30. Live session stamp: 20261001T003832Z.

PR-BR remains open. PR-BS was not started. No independent 10-turn smoke. No 4×10 gate. No completion commit. No push. No semantic repair-and-rerun. The deterministic gates passed before the single six-turn live run.

### 1. Continuation 12 starting evidence

Continuation 12 produced 6/6 defensible Resolution Contracts and 2/6 manual player-visible PASS. The evaluator passed all six, including four false PASS. Routing was 2 fast-path turns and 4 interpreter turns. The failures that mattered were after the contract: turn 2 changed a time answer into the source/certainty template, turn 3 replaced a notice-board reading with scene and clue framing, turn 1 narrated that nobody stepped forward, and turn 6 did both the atmospheric miss and the clue replacement. Interpretation and discourse typing were not the target.

### 2. Post-generation pipeline map

After the first generated candidate, text can still be rewritten by speaker enforcement, strict-social construction, the response-type gate, the answer-completeness and related emission layers, narration purity, scene-momentum append, finalization (`select_preserved_answer`), authored-knowledge realization (`clue_frame`), stay/leave agreement, destination arrival, perception grounding, and `enforce_emitted_contract_monotonicity`. The contract is available at those stages. Satisfaction is compared by rank in `prefer_stronger_resolution`, `select_preserved_answer`, `retain_resolved_contract_text`, and the final enforce step. Authority and grounding still run in speaker enforcement, perception grounding, and the bounded-improvisation path. The final enforce step restores a prior candidate only when the current text carries `dimension_substituted`, `atmospheric_avoidance`, `social_not_resolved`, or `generic_scene_replaced_dimension` and the saved candidate ranks at least 3. A replacement that itself scores satisfied is not restored.

Recorded Continuation 12 traces, replayed through this path:

- Turn 2: the temporal candidate stays. The source/certainty template is `dimension_substituted` and loses.
- Turn 3: the notice-board reading stays. The "new ground shows itself" frame is unsatisfied and loses. A compatible clue may follow the reading.
- Turn 6: the patrol clue and "no one steps forward" stay unsatisfied. They do not become a PASS.

### 3. Turn 2 root cause

The follow-up obligation line was the source/certainty sentence for every follow-up dimension. Coverage treated "earlier" as time and "certain" as confidence, so that sentence looked like a legitimate time answer and could replace the real one. The fix keeps a foreign claim dimension unsatisfied when the requested dimension is not cued, strips the "earlier claim" span before the time match, and uses a time-only inability when the contract dimension is only time. The recorded replay no longer emits "who began the earlier claim."

### 4. Turn 3 root cause

The scene frame matched inspection coverage through bare "shows" and "notice," and a meaningful-word inspection path then scored it satisfied. Destination arrival and authored-knowledge realization run after finalization, so they could still replace a restored reading. Scene-frame and generic observe stock without a content observation are now unsatisfied. Destination arrival and the clue frame call `prefer_stronger_resolution` before replacing. The recorded reading keeps taxes or curfew.

### 5. Turn 6 root cause

A dimensionless ask treated a patrol sentence as `inquiry_answered`, and "no one steps forward" was not atmospheric avoidance. Both are now unsatisfied when the contract names an interlocutor: `social_not_resolved` and `atmospheric_avoidance`. The evaluator fails those reasons. The live session showed the remaining hole: if the replacement also scores satisfied, or if both sides are unchecked, the clue frame can still win at equal rank.

### 6. Semantic-monotonicity design

`resolution_rank` orders a dimension-compatible satisfied answer above a partial answer, a legitimate inability, an unchecked line, and a wrong-dimension or atmospheric line. `prefer_stronger_resolution` refuses a lower rank. Equal rank may keep the later text. That equal-rank rule is what let the live clue replacements through once they scored satisfied.

### 7. Best-safe-candidate behavior

`remember_satisfied_candidate` stores `best_safe_candidate` at rank 2 or higher and the first rank-4 answer as `satisfied_candidate`. `select_preserved_answer` recovers a strictly higher safe candidate. A speaker-contract mismatch is not safe: the opening speaker is retargeted when the line starts with the wrong name, and a line that cannot be retargeted is not restored over a speaker-correct line. Live turn 2 kept the better time answer in `best_safe_candidate` and did not emit it. The attribution began with a quotation, so the retarget did not apply, and selection recorded `destroyed`.

### 8. Dimension preservation

Requested claim dimensions use the existing contract fields. A source sentence does not satisfy time. A time sentence does not outrank a real source answer or a real confidence answer. The time-only, location-only, and confidence-only follow-up lines name that dimension. A source or mixed source/certainty contract still uses the older source sentence, so an established source inability remains recognizable.

### 9. Clue-frame behavior

`apply_authored_knowledge_realization_to_gm` records stage `clue_frame`. It rejects a replacement whose rank is 0 while the current text ranks at least as high. It accepts a replacement at equal rank when that replacement also scores as an answer. Live turn 5 shows the rejection (`clue_frame_would_reduce_contract`). Live turns 1, 4, and 6 show the equal-rank acceptance. A clue may still be appended when the inspection itself remains.

### 10. Scene-momentum behavior

`continuation_preserves_resolution` allows a separable compatible line after a satisfied answer and refuses an append that drops the answer. Replacing the answer with "the new ground shows itself" loses. Live turn 3 did not take that path. The inspection was emitted unchanged.

### 11. Retry and fallback behavior

`retain_resolved_contract_text` keeps the earlier candidate when its rank is higher. The recorded turn 2 replay keeps the temporal answer across that retry comparison. The live run made 0 generation retries. The time follow-up fallback is what turn 2 emitted after the richer candidate was set aside.

### 12. Social-generation root cause

Continuation 12 turn 1's generated candidate itself said nobody stepped forward. The generation constraint for an ask with an interlocutor now says the person must answer, refuse, admit ignorance, or ask a clarifying question, and must not narrate that nobody steps forward. In this live run the model did produce a real guard answer on turns 1, 2, and 6. Turns 1 and 6 were then replaced downstream.

### 13. Canonical-interlocutor execution

Speaker enforcement still rewrites an explicit wrong opening speaker. Selection no longer puts that wrong speaker back when the corrected line is speaker-valid. The existing speaker-repair test ends on Tavern Runner and the source answer. Quote-first attribution ("...\" the gate guard replies") is not rebound by that opening-name helper, which is why live turn 2 did not keep its generated sentence.

### 14. Atmospheric-avoidance handling

"No one steps forward," "watches you carefully," and "the gate remains tense" are `atmospheric_avoidance` on an ask that names an interlocutor, unless the line is attributed speech that also refuses. The evaluator fails that reason. A voiced refusal remains a resolution. The live run did not emit the atmospheric line.

### 15. Legitimate refusal, inability, and evasion

A guard who says they do not know, refuses, or asks which gate is meant still resolves the social contract. The time inability "I cannot say how recently that was" is the live example. It is thinner than the generated "he took command tonight," and it is still about time.

### 16. PR-BN authority interaction

Bounded incidental procedure is unchanged. Ordinary gate procedure can still be said. The monotonicity rule does not preserve an ungrounded line merely because it is responsive. Perception grounding, speaker binding, and hidden-object refusal stayed green in the regression band. Live turn 1's "report to him for clearance" was replaced by the authored Thoran-command sentence. That replacement is the canonical fact, and it does not answer what the player must do.

### 17. Recorded replay results

`tests/test_pr_br_continuation13_semantic_preservation.py` passed inside the 303-test band.

- Continuation 12 turn 2: PASS. The temporal candidate survives the source template.
- Continuation 12 turn 3: PASS. Taxes or curfew survive the scene frame.
- Continuation 12 turn 6: PASS. The patrol clue does not satisfy the social ask, and the evaluator fails it.

### 18. Focused deterministic tests

The same file covers time, source, and confidence precedence, inspection survival, clue non-satisfaction, scene-frame non-replacement, social answer, inability, refusal, clarification, atmospheric rejection, unrelated-clue rejection, evaluator mismatches, the generation constraint, and a stubbed `/api/chat` inspection that keeps curfew or taxes and does not store the interlocutor as `active_claim`.

### 19. Broader regression

One pytest invocation, junit `artifacts/pr_br_continuation13/junit.xml`: 303 tests, 0 failures, 0 errors, 0 skipped. The band is the Continuation 12 set plus authored-knowledge, destination-arrival, and the new preservation tests. Interpretation proposal tests and discourse-sensitive contract tests are in that band and passed.

### 20. Live-turn table

Artifact: `artifacts/pr_br_continuation13/20261001T003832Z`. Six completed turns. One isolated session. Preflight healthy. No repair and no rerun.

| Turn | Input | Contract | Initial | Final | Degradation | Evaluator |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ask the gate guard what is required tonight | correct ask / gate_guard | PASS | FAIL | YES | false PASS |
| 2 | how long has that been the case | correct ask / time | PASS | PASS | NO | false FAIL |
| 3 | read the notice board | correct inspect / notice board | PASS | PASS | NO | true PASS |
| 4 | what people come to that board for | ask / notice board, no use dimension | PASS | FAIL | YES | false PASS |
| 5 | do the thing he said | unbound act, not correct | FAIL | FAIL | NO | false PASS |
| 6 | ask whether he is sure | ask / gate_guard, no confidence dimension | PASS | FAIL | YES | true FAIL |

Fast path: 3. Abstentions: 3. Interpreter invoked: 3.

### 21. Initial versus final manual quality

Initial candidate manual PASS: 5/6. Final response manual PASS: 2/6. The gap is post-generation on turns 1, 4, and 6. Turn 5 was already a bad initial candidate. Turn 3 is the clean case: the reading that left the model is the reading the player saw. Turn 2's final line is a real time inability, so it stays a pass even though "tonight" was dropped.

### 22. Semantic-degradation count

3. Turns 1, 4, and 6 began with a useful answer and ended without one. Target was 0. This is not low enough to authorize smoke.

### 23. Social-resolution result

Applicable social turns, canonical interlocutor addressed: 3 (turns 1, 2, and 6). Resolved: 1 (turn 2's time inability). Turns 1 and 6 produced a real guard answer in generation and a different fact at emission. Turn 4 is a question about the board, not an addressed NPC. Turn 5 is an action.

### 24. Evaluator and manual agreement

Evaluator PASS: 4/6. False PASS: 3 (turns 1, 4, and 5). False FAIL: 1 (turn 2). True PASS: turn 3. True FAIL: turn 6. The unit fixtures reject the recorded source-for-time swap, the atmospheric line, the patrol clue on a social ask, and the scene frame on an inspection. Live false PASS remains where a short authored fact scores as `inquiry_answered` or a generic action line scores as a legitimate nonresolution.

### 25. Model-call and cost accounting

Completed live gameplay turns: 6. Interpretation model calls: 3. Gameplay-generation model calls: 6. Evaluator model calls: 0 (`evaluate_playability` is local). Retry calls: 0. Aborted calls: 0. Correct contracts: 5/6. Requested-dimension losses: 2 (turn 4 use, turn 6 confidence). Turn 2 kept time. Target or interlocutor losses at emission: 2 (turn 4's board answer became the patrol route; turn 6's guard stopped speaking).

### 26. Residual failure families

- A clue or authored fact that scores satisfied at the same rank as the real answer can replace it. Turns 1 and 4.
- A dimensionless ask scores both a confidence answer and a repeated fact as unchecked, so the later fact wins. Turn 6.
- Quote-first attribution is not retargeted, so a satisfying spoken answer can be dropped for the obligation line. Turn 2, specificity only.
- An anaphoric "do the thing he said" became an unbound act and a generic cannot-complete line. Turn 5.
- The evaluator still passes a falsely satisfied clue and a generic action refusal.

### 27. State-integrity findings

No interlocutor was stored as `active_claim`. The claim slot holds the emitted Thoran sentence. The gate guard stayed the interlocutor. The notice board became `active_inspected` on turn 3 and remained. No canonical referent was denied. No literal foot-on-a-step resolution occurred. No state-integrity failure of the Continuation 12 kind was observed.

### 28. Recommended next step

Do not start independent smoke. Do not start PR-BS. The recorded Continuation 12 replacements are blocked, and a clean inspection now survives. The next repair is narrower: a clue-frame or topic-pressure line must not replace a candidate at equal rank unless it answers the same contract, and a quote-first speaker line that already answers must stay eligible. Do not rerun these six turns as a repair loop.

### 29. PR-BR status

PR-BR: STILL OPEN.

READY FOR INDEPENDENT 10-TURN SMOKE: NO.

READY FOR FULL SYNTHETIC GATE: NO.

HUMAN PLAYTEST: NOT AUTHORIZED.

## PR-BR Continuation 14 — Resolution-Content Preservation & Authoritative Best-Candidate Emission

PR-BR remains open. This pass does not start PR-BS. No completion commit. No push. No independent smoke. No 4×10 gate. No human playtest.

### 1. Continuation 13 starting evidence

Deterministic band at the end of Continuation 13: 303/303 PASS. Live session `20261001T003832Z`: correct contracts 5/6, initial manual PASS 5/6, final manual PASS 2/6, useful answers degraded after generation 3, social resolution 1/3, evaluator PASS 4/6 with 3 false PASS and 1 false FAIL. Generation was already useful on 5/6. Final emission kept 2/6. The dominant break was candidate selection, not generation.

### 2. Candidate-comparison architecture

Rank is assigned in `resolution_rank` from `assess_contract_satisfaction`: a dimension-compatible answer is 4, a partial answer is 3, a legitimate nonresolution is 2, an unchecked or incompatible line is 1, and a hard miss is 0. `remember_satisfied_candidate` stores `best_safe_candidate` only when `candidate_may_replace` allows it, and only for the current `contract_id`. `select_preserved_answer` emits the current line only when it may replace that stored candidate. `enforce_emitted_contract_monotonicity` runs after perception grounding and applies that choice. Continuation 13 applied the choice only for a short list of restorable failures, which is why Turn 2's stronger time answer stayed in `best_safe_candidate` and was not emitted.

### 3. Equal-rank replacement root cause

`rank(B) >= rank(A)` used to be enough. A procedure answer and a "who commands" fact both scored satisfied / rank 4. A use answer and a patrol clue did the same. Equal rank was treated as equivalent resolution.

### 4. Resolution-coverage design

`resolution_coverage` does not build a second contract. It reads operation, target, interlocutor, dimension, and expected resolution, then asks `_dimension_covered` whether the candidate resolves those dimensions. If the contract dimension is empty, `first_obvious_dimension` supplies confidence, use, time, source, location, content, or next_step when the raw input clearly has one. A shared name such as Thoran, gate, or patrol is not coverage.

### 5. Procedure preservation

`DIM_NEXT_STEP` is the existing procedure dimension. A line matches it when it states a required action (`need to`, `clearance`, `report to`, `you'll need`). An identity-only line (`commands`, `in charge`) does not. Turn 1's clearance answer is kept over "Thoran commands the watch." A superset that keeps the clearance and adds the command may replace it.

### 6. Use/purpose preservation

Purpose questions (`what's this used for`, `what do people come to it for`, `why do people use this`) set `use` and stay `ask` rather than `perceive`. A purpose answer is not replaceable by a clue that merely appears on the same object. Recorded Turn 4 keeps the official-postings answer over the northwest mud track.

### 7. Confidence dimension repair

`confidence` already existed. The request patterns now include "whether he's sure", "are you certain", "how sure is she", "sure about that", and "do you trust". Recorded Turn 6 requires that dimension before the certainty line is compared with the Thoran fact. The certainty line wins.

### 8. dimension=None audit

None remains valid for a greeting, a news ask the fast path cannot type, and an unbound act. Obvious time, confidence, use, source, location, content, and next_step requests must not stay None just because a lexical pattern missed them. If the fast path builds a proposal that omits `first_obvious_dimension`, it abstains with `requested_dimension` instead of emitting None. The structured interpreter may supply the dimension. Unknown names are rejected. Aliases canonicalize: purpose→use, certainty→confidence, procedure→next_step.

### 9. Semantic-superset behavior

A later line may add compatible information. "Report to Captain Thoran for clearance; he commands the gate watch tonight" may replace "Report to Captain Thoran" because the procedure remains. Live Turn 1 did this inside one speech: papers and curfew stay, and the command is extra.

### 10. Same-dimension improvement

"Earlier tonight" may replace "Recently" on a time contract. The reverse is `less_specific_same_dimension` and is refused. The first acceptable answer is not frozen.

### 11. Unsafe-candidate rejection

Authority rejection runs before coverage. An invented procedure listed in `authority_invalid_candidates`, or a consequential line without a legitimate refusal, cannot become `best_safe_candidate`. Grounding replacements record `best_safe_invalidation` reason `grounding_contradiction` and that exact text cannot be stored again. A social answer that already keeps an ask or act contract is not discarded as an unsupported perception.

### 12. best_safe_candidate root cause

Continuation 13 Turn 2 stored the specific time answer and then emitted the inability. `enforce_emitted_contract_monotonicity` computed the stronger line and dropped it unless the current line had one of a few failure reasons. The check now applies the stronger safe line whenever it may not be replaced. A new `contract_id` clears the previous best so a later turn cannot revive it.

### 13. Authoritative final selection

Immediately before emission the check reads the current line, `best_safe_candidate`, the contract, authority rejection, grounding invalidation, satisfaction, and coverage. The emitted line is that choice. `final_selected_candidate` and `final_resolution_coverage` are recorded.

### 14. Best-candidate invalidation rules

A stored best is dropped only for an explicit reason: `authority_violation`, `grounding_contradiction`, `speaker_contract`, or another hard invalidity already recorded on `best_safe_invalidation`. The reason and a candidate excerpt are kept. A different later line may still be stored. The invalidated text may not return because another candidate exists. A grounding tag is not a license to overwrite a line that already resolves a social or procedure contract, and the contract-miss fallback does not replace a `referenced_surface_realization`, `perception_non_invention`, or `destination_arrival_realization` line.

### 15. C13 Turn 1 replay

PASS. The clearance / report-to-Thoran answer survives "Captain Thoran commands the gate watch tonight." A compatible append keeps the procedure.

### 16. C13 Turn 2 replay

PASS. "Captain Thoran only took command tonight" is emitted over "I cannot say how recently that was." `best_safe_candidate` is the emitted line. Quote-first attribution stays eligible.

### 17. C13 Turn 3 replay

PASS. The notice-board inspection (taxes, curfew, patrol warning, roster) is not replaced by the scene frame or the mud-track clue.

### 18. C13 Turn 4 replay

PASS. The use/purpose answer survives the northwest mud-track clue. The clue may appear only if the purpose sentence remains.

### 19. C13 Turn 5 replay

PASS. "Then I'll do the thing he said" stays an unbound act. Preservation does not emit a stale procedure or Thoran fact.

### 20. C13 Turn 6 replay

PASS. The contract dimension is confidence. "Best to take that as certain" outranks the Thoran command fact.

### 21. Structural variant tests

Procedure ("what do I have to do to enter", "what's required before they'll let me through"), use ("what's this used for", "why do people use this thing"), confidence ("are you certain", "how sure is she"), and time ("when did that start", "how long ago") take the same dimensions. A greeting and a dimensionless news ask stay None and do not abstain.

### 22. Focused deterministic results

`tests/test_pr_br_continuation14_resolution_content.py` covers the six replays, the variants, equal-rank wrong-dimension pairs (time vs source, use vs clue, confidence vs identity, procedure vs responsible person), same-dimension improvement, semantic superset, authority rejection, fast-path abstention when an obvious dimension is omitted, unknown dimension rejection, evaluator wrong-proposition FAIL, evaluator superset PASS, and a stubbed `/api/chat` procedure turn. All of those passed inside the broader band.

### 23. Broader regression results

316 passed, 0 failed, 0 skipped. Junit: `artifacts/pr_br_continuation14/junit.xml`. The band is the Continuation 13 set plus the Continuation 14 file. An intermediate run failed six grounding tests because best-safe restoration put invented perception back after an explicit grounding replacement, and then two chat tests when that restoration was too blunt. The final rule invalidates the grounded-away text, still lets a keeping social answer outrank a surface miss, and does not let the contract fallback erase a referenced-surface line. Interpretation, discourse, and social-resolution tests in the band stayed green.

### 24. Live-turn table

Session `20261001T013504Z`. Wording is not the Continuation 13 script.

| Turn | Input | Contract | Initial | Final | Manual | Eval |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | what's required before they'll let me through | ask, gate_guard, next_step | papers, curfew, permission from Thoran, plus who commands | same | PASS | PASS |
| 2 | When did that start? | ask, gate_guard, time | which "that": curfew, patrol, or posting | cannot say how recently | FAIL | FAIL |
| 3 | How sure is he about that? | ask, gate_guard, confidence | can't say for certain | same | PASS | PASS |
| 4 | What's that notice board used for? | ask, Notice board, use | taxes, curfew, warnings, updates before entry | same | PASS | FAIL |
| 5 | what travelers have been saying | ask, Gate Guard, dimension None | worn travelers, eastern census | Thoran commands the watch | FAIL | PASS |
| 6 | I'll do whatever he just told me to do | act, dimension None | restates papers and curfew; scored as not an action | generic refusal | PASS | PASS |

### 25. Initial versus final manual quality

Initial manual PASS 6/6. Final manual PASS 4/6. Turns 1, 3, and 4 emit the generated sentence. Turn 6's refusal is the legitimate nonresolution for an unbound act.

### 26. Semantic-degradation count

2. Turn 2 replaces a useful clarification with a generic time inability. Turn 5 replaces a direct answer about travelers with the Thoran command fact. Both replacements are same-rank under the scorer: two legitimate nonresolutions on turn 2, two `inquiry_answered` lines on turn 5.

### 27. Best-candidate emission mismatches

0. On every turn the stored `best_safe_candidate` is the emitted line. Turn 5's defect is that the Thoran line was accepted as the new best. Emission did not bypass it.

### 28. Evaluator and manual agreement

Evaluator PASS 4/6. False PASS: 1 (turn 5, dimensionless `inquiry_answered`). False FAIL: 1 (turn 4, "recently" inside a use answer is treated as a time substitution). True PASS: turns 1, 3, and 6. True FAIL: turn 2.

### 29. Model-call and cost accounting

Completed live gameplay turns: 6. Deterministic fast-path turns: 3 (turns 1, 5, and 6). Interpretation model calls: 3 (turns 2, 3, and 4 abstained and the interpreter supplied time, confidence, and use). Gameplay-generation model calls: 6. Evaluator model calls: 0. Retry calls: 0. Aborted calls: 0. No second run.

### 30. Residual failure families

- A dimensionless social ask still scores any grounded related sentence as `inquiry_answered`. Turn 5's content question stayed dimension None, so the Thoran fact could replace the traveler answer at equal rank.
- A clarifying question and a dimension-shaped inability are both legitimate nonresolutions. Turn 2 kept the inability.
- "Recently" inside a use answer trips `dimension_substituted`, so the evaluator can fail a purpose answer that was actually emitted.
- "What's that notice board used for?" does not match the tight "what's that used for" fast path, so it abstains. The interpreter then set use correctly.

### 31. State-integrity findings

The gate guard remained `active_interlocutor` on all six turns. The Thoran sentence became `active_claim` after turn 5 and was not written into the interlocutor slot. Turn 4 did not set `active_inspected` because the act was an ask. No canonical referent was denied. No literal physical "step" reading. No object:duty target. No session-isolation failure in the band.

### 32. Recommended next step

Do not start independent smoke. Do not start PR-BS. The recorded Continuation 13 replacements are blocked, and three of the new live shapes kept the generated proposition, including a procedure-plus-identity superset. The next repair is narrower still: a content question such as "what have they been saying" must not stay dimension None, and a clarifying question must not lose to a generic inability at the same nonresolution rank. Do not rerun these six turns as a repair loop.

### 33. PR-BR status

PR-BR: STILL OPEN.

READY FOR INDEPENDENT 10-TURN SMOKE: NO.

READY FOR FULL SYNTHETIC GATE: NO.

HUMAN PLAYTEST: NOT AUTHORIZED.

## PR-BR Continuation 15 — Content-Dimension Coverage, Ambiguity Precedence & Final Preservation Closeout

PR-BR remains open. This pass does not start PR-BS. No completion commit. No push. No independent smoke. No 4×10 gate. No human playtest. No semantic repair-and-rerun.

### 1. Continuation 14 starting evidence

Session `20261001T013504Z`. Deterministic band 316/316 PASS. All six recorded Continuation 13 replays PASS. Initial generated candidate manual PASS 6/6. Final player-visible manual PASS 4/6. `best_safe_candidate` emission mismatches 0. Manual semantic degradations after generation: 2 (turn 2 and turn 5). Generation was already useful. The remaining holes were semantic selection.

### 2. Continuation 14 reporting discrepancy

Machine telemetry recorded `semantic_degradations = 0`. Manual review found 2. The Continuation 14 runner counted a degradation only when the generated line `keeps_answer` was true and the final line `keeps_answer` was false. Turn 2 scored both the clarification and the generic inability as legitimate nonresolution, so both had `keeps_answer` false. Turn 5 left the contract at dimension None, so both the traveler answer and the Thoran line scored `inquiry_answered`. Equal-rank requested-content loss was invisible. Automated zero-degradation telemetry from that runner is not authoritative. Manual candidate-history review remains authoritative.

### 3. Content-dimension design

`DIM_CONTENT` (`"content"`) already existed and is the dimension used. No second content name was added. A content question asks for what was said, reported, told, written, heard, or claimed. Structural request cues cover speech, report, message, and writing predicates. Exact player strings are not the matcher.

### 4. Content and source

"Who told you that?" stays source. "What did they tell you?" and "what have travelers been saying" stay content. When both cues are present and the source pattern matches, source wins and content is dropped.

### 5. Content and confidence

"Do the travelers sound certain?" is confidence. The confidence pattern now includes "sound/seem certain", and a confidence match drops a competing sound or content dimension.

### 6. Content and time

"What did they say?" is content. "When did they say it?" is time. A time-headed request drops content.

### 7. Content and use

"What does the notice say?" is content. "What is the notice board used for?" is use. A purpose question drops content. A content question that is not a purpose question drops use and wear, so "come through" does not become wear.

### 8. Fast-path content handling

Obvious content inquiries take dimension content on the deterministic path. If the request clearly needs content but the speaker, document, claim, or other referent cannot be bound ("what did he say", "what was written there" with no object, claim, or person), the fast path abstains with gap `content_referent` instead of emitting a complete dimension-None contract. "What are travelers saying?" does not abstain.

### 9. Structured-interpreter content handling

The interpreter prompt tells the model to set dimension content for what was said, reported, written, or heard, and to keep that distinct from source, confidence, time, and use. The validator accepts `content`, canonicalizes aliases `substance` and `statement` to content, and still rejects an unknown dimension.

### 10. Content coverage

For dimension content, the candidate must supply the substance of the report or a content-specific inability, refusal, or clarification. An identity-role sentence ("Captain Thoran commands the gate") does not cover content. A negative or explicit nonanswer sentence is not treated as the report itself.

### 11. Ambiguity blocker handling

No second ambiguity store was added. A bare temporal anaphor ("that", "this", "it") with more than one filled content slot among the active claim, the inspected object, and the actionable lead is `multiple_plausible_referents`. A named event ("when did the curfew begin", "when did the patrol disappear") binds the matching slot and is not forced into clarification.

### 12. Clarification precedence

When the referent is unbound or ambiguous and the candidate asks a necessary clarification, that candidate ranks 3. A generic inability ranks 2. The clarification therefore outranks the inability. A real answer still ranks 4, so an unnecessary clarification does not outrank a safe answer. Scene-stall momentum does not replace a contract clarification.

### 13. Clear-reference inability preservation

If the referent is already bound, clarification text is not marked necessary and does not outrank a legitimate inability. "I don't know when that began" remains a valid resolution of a clear temporal question.

### 14. Additive dimension coverage

Coverage asks whether the requested dimension is present. A foreign claim cue such as "recently" or "yesterday" does not erase a requested dimension that is already covered. Use plus time, content plus source, and confidence plus time stay covered on the requested dimension.

### 15. Requested-dimension dominance

A later candidate that drops the requested dimension cannot replace a candidate that covered it, including at equal rank. Extra compatible dimensions remain allowed.

### 16. Semantic-degradation telemetry root cause

See section 2. The detector compared answer-keeping flags, not requested-content loss. `best_safe_candidate` emission mismatch was a separate counter and was already 0. The defect was accepting a worse equal-rank line as the new best, then reporting no degradation.

### 17. Telemetry repair

`detect_semantic_degradation` records lower rank, requested-dimension loss at equal rank, clarification replaced by inability, and target loss only when rank or requested coverage also drops. `enforce_emitted_contract_monotonicity` stores that result on emission debug from the first safe candidate to the final text. The detector does not choose the emitted line. The Continuation 15 runner uses this detector. A scene append that keeps rank and coverage is not reported as target loss.

### 18. Continuation 14 turn 1 replay

The procedure answer (what is required to enter, including papers and permission) remains preferred over an identity-only Captain Thoran line. PASS.

### 19. Continuation 14 turn 2 replay

"When did that start?" with both the curfew claim and the missing-patrol inspection active stays ambiguous. The necessary clarification is kept over "I cannot say how recently that was." PASS.

### 20. Continuation 14 turn 3 replay

The confidence answer remains preferred over an unrelated Thoran fact. PASS.

### 21. Continuation 14 turn 4 replay

The notice-board use answer that also says the patrol went missing recently still covers use. The evaluator PASSes. PASS.

### 22. Continuation 14 turn 5 replay

The contract dimension is content. The traveler-report answer is kept over "Captain Thoran commands the gate watch tonight." PASS.

### 23. Continuation 14 turn 6 replay

The unbound "I'll do whatever he just told me to do" stays a non-hallucinatory refusal. The stale procedure answer is not revived. PASS.

### 24. Focused deterministic results

`tests/test_pr_br_continuation15_content_clarification.py`: 10 passed. Covers content versus source, confidence, time, and use; fast-path variants and abstention; interpreter alias and unknown rejection; content coverage and superset; clarification precedence and clear-referent inability; additive fixtures; all six Continuation 14 replays; equal-rank degradation; evaluator content FAIL, use-plus-time PASS, and clarification PASS; stubbed `/api/chat` paths A–E.

### 25. Broader regression result

The PR-BN, PR-BP, and PR-BR band, including Continuation 12–15 and the social-answer retry file: 329 passed, 0 failed, 0 skipped. Junit `artifacts/pr_br_continuation15/junit.xml`. Re-run after the telemetry narrowing of target loss. Interpretation, discourse, and social-resolution tests in that band stayed green.

### 26. Raw `/api/chat` stub results

A. A content inquiry builds a content contract and the traveler-content answer is the final text. B. An ambiguous "When did that start?" keeps the necessary clarification in the final text. C. A use answer that also mentions a recent posting still covers use, and the evaluator PASSes. D. An equal-rank unrelated replacement is blocked. E. The historical equal-rank pair is recorded as semantic degradation. PASS.

### 27. Four-turn live table

Session `20261001T094739Z`. Natural wording, not the regression strings. Manual review is authoritative.

| Turn | Player | Contract | Generated = final | Manual | Evaluator |
| --- | --- | --- | --- | --- | --- |
| 1 control | Read the notice board from top to bottom. | inspect / Notice board / dimension none | Taxes, curfew, and the missing patrol on the northwest mud track. | PASS | PASS |
| 2 ambiguous follow-up | When did that happen? | ask / time / Notice board. Fast path abstained. Interpreter set time. Ambiguous false. | The board does not give the time the patrol went missing; last sighting is the mud track. | PASS | PASS |
| 3 content | Ask the gate guard what travelers have been telling people as they arrive. | ask / content / interlocutor gate guard. Target inherited Notice board. | "I haven't heard what the travelers have been saying." | PASS | PASS |
| 4 additive | What do people come to that board for? | ask / use / Notice board / gate guard | Folks come to catch up on rules and warnings; it lists taxes, curfews, and the missing patrol. | PASS | FAIL |

Turn 2 did not require clarification. Turn 1's narration singled out the missing-patrol warning, and discourse held one inspected object, so "that" resolved to the patrol's timing. The answer is a time-specific inability plus the last sighting, and it was the generated line. Turn 3 is a content-specific inability, not a Thoran substitution. Turn 4's player-visible answer covers use and adds the posted contents. The scorer marked it `generic_scene_replaced_dimension` because "folks come … to catch up on the latest rules" is outside the use cues that already accept "people come" and "where … find updates".

### 28. Initial versus final manual quality

Initial candidate manual PASS 4/4. Final response manual PASS 4/4. On every turn the generated line and the emitted line are the same text.

### 29. Semantic-degradation manual and telemetry comparison

Manual semantic degradations after generation: 0. Telemetry semantic degradations: 0. Disagreements: 0. This agreement is on the new detector, reviewed against the candidate histories, not on the Continuation 14 keeps-answer proxy.

### 30. Best-safe emission result

`best_safe_candidate` emission mismatches: 0. Turns 1–3 stored the generated line as best and emitted it. Turn 4 stored no best because coverage scored the use answer unsatisfied, and the emitted line is still the generated line. Nothing replaced a stored best.

### 31. Evaluator and manual agreement

Evaluator PASS 3/4. False PASS: 0. False FAIL: 1 (turn 4). True PASS: turns 1, 2, and 3.

### 32. Model-call and cost accounting

Completed live gameplay turns: 4. Deterministic fast-path turns: 3 (turns 1, 3, and 4). Fast-path abstentions: 1 (turn 2, `insufficient_discourse_context`). Interpretation model calls: 1. Gameplay-generation model calls: 4. Evaluator model calls: 0 (`evaluate_playability` is local). Retry calls: 0. Aborted calls: 0. No second run.

Correct contracts: 4/4. Turn 3's dimension and interlocutor are content and the gate guard; the target label stayed the notice board by discourse inheritance. Content-dimension correct/applicable: 1/1. Clarification preserved/applicable: 0/0 (the live follow-up had one salient referent). Additive-dimension correct/applicable: 1/1 on the player-visible answer. The classifier disagreed on that turn.

### 33. Residual failure families

- Use coverage still misses the paraphrase "folks come to that board to catch up on the latest rules and warnings", so a correct use-plus-content answer can be scored unsatisfied and false-failed. The line was still emitted. This was not repaired after the live run.
- Live shape A did not produce two discourse slots, so clarification precedence was not exercised on a paid turn. The recorded Continuation 14 turn 2 replay covers that case.
- A content-specific inability ("I haven't heard what the travelers have been saying") is scored as covered content. That is a legitimate content resolution, not a substitute fact.

### 34. State-integrity findings

The notice board stayed `active_inspected` from turn 1. The gate guard became `active_interlocutor` on turn 3 and remained on turn 4. No interlocutor was stored as `active_claim`. No canonical referent was denied. No session-isolation failure appeared in the band or the four turns.

### 35. Readiness recommendation

READY FOR INDEPENDENT 10-TURN SMOKE: YES. All deterministic gates passed, all six Continuation 14 replays passed, manual semantic degradation was 0, and best-safe emission mismatches were 0. The one evaluator false FAIL is a use-cue paraphrase gap. It did not replace the generated answer and does not show the Continuation 14 selection failure recurring. Do not run the smoke in this cycle. It needs separate authorization.

READY FOR FULL SYNTHETIC GATE: NO.

HUMAN PLAYTEST: NOT AUTHORIZED.

### 36. PR-BR status

PR-BR: STILL OPEN. Do not close it on this cycle. Do not start PR-BS. Wait for external review.

## PR-BR — Independent 10-Turn Synthetic Smoke Validation

PR-BR remains open. This cycle is validation only. No semantic repair. No prompt change. No rerun. No 4×10 gate. No human playtest. No completion commit. No push.

### 1. Validation purpose

The question was whether the accumulated PR-BR architecture produces a coherent, responsive 10-turn interaction when the player behaves like an ordinary tabletop player. This was a product validation, not a parser test, dimension checklist, evaluator benchmark, or curated regression sequence.

### 2. Independence controls

The player was operated by the validation agent from player-visible text only. Each next action was chosen after that turn's reply. The ten inputs were not written in advance.

The player was not given failure families, regression phrases, contract dimensions, evaluator rubrics, parser branches, or authority branches. The existing synthetic-gate personas and the reactive/adversarial scenarios were not used. Those scripts target the patrol, the notice, watch command, and source/confidence follow-ups.

No separate player model was called. Synthetic-player model calls: 0.

### 3. Clean-session confirmation

YES. Isolated storage under `artifacts/pr_br_independent_smoke/20261001T104551Z/isolated_data`. The player's saved campaign was not reset.

- HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` (`PR-BN bounded DM improvisational authority`). PR-BR Continuation 15 is the uncommitted working tree this session ran. No further product edit was applied before or during the run.
- C15 modules present: `game/resolution_contract.py`, `game/discourse_state.py`, `game/semantic_interpreter.py`, `game/interpretation_proposal.py`.
- Session after isolate: campaign/session `9119df19bfba65f7c3a4b830`, scene `frontier_gate`, character Galinor, transcript empty, upstream preflight ok.
- Product path: `POST /api/start_campaign` for the opening, then ten `POST /api/chat` turns.
- Live interpretation left enabled. `evaluate_playability` is local and was the only evaluator.

### 4. Persona

Galinor, a level-1 wandering wizard just arrived at a rainy frontier gate. He looks for food and shelter, talks to people who are actually in front of him, follows a glance or a refusal, and changes approach when an NPC stops helping. Instructions: `artifacts/pr_br_independent_smoke/persona.md`.

### 5. Completed turn count

10 / 10 gameplay turns. The opening narration is not one of the ten. No early stop. The session stayed runnable. It did not stay coherently answered.

### 6. Full player-visible transcript

Opening:

Rain spatters the soot-dark stones above the eastern gate of Cinderwatch, where frayed banners shudder in the chill wind. A well-appointed townhouse overlooks the bustling square, its noble colors standing in quiet contrast to the mud and clamoring masses below. Refugees, laden wagons, and travelers clog the muddy approach, pressed tightly by guards who maintain a determined choke point amid the push. Near a rain barrel, a tavern runner calls out offers of hot stew and paid rumors, hoping to turn the uneasy crowd’s attention into coin. A figure clad in threadbare clothing stands oddly still apart from the line, their gaze flicking with keen scrutiny among packs and faces, betraying a watchfulness at odds with the rest. A notice board near the gate lists new taxes and curfew rules, though the most eye-catching entry is a somber warning about a missing patrol, casting a shadow over the crowded scene.

Turn 1. Motivation: the runner is selling stew in the rain. Intended: price, and a dry place to eat it.

Player: I shoulder through the crowd toward the tavern runner and ask what the stew costs, and whether there is somewhere dry to eat it.

GM: Tavern Runner says with a tight shrug, voice low and hurried,

Turn 2. Motivation: the sentence stopped. Intended: the price and a dry place.

Player: I lean closer so I can hear him over the rain. You started to answer and stopped. How much for a bowl, and where can I eat it out of this weather?

GM: Tavern Runner says, "Look, it's hard to be sure just now, Prices shift with the rumors and the guards' moods, and dry spots to eat? If you want sure warmth, you might need to pay a bit more or know the right people."

Turn 3. Motivation: he named shifting prices and "the right people." Intended: a number, and who those people are.

Player: I keep my voice down. A number, then. What are you charging for one bowl right now, and who are these right people?

GM: Tavern Runner says, "I couldn't tell you I keep my voice down. A number, then. What are you charging for one bowl right n; you will need another source."

Turn 4. Motivation: the runner quoted the player and gave up. Intended: ask a guard how to pass.

Player: I leave the runner and step up to the nearest guard holding the line. I ask, calmly, what a traveler has to do to pass this gate.

GM: The tavern runner replies, voice low and wary, eyes flicking to the guards holding the line.

Turn 5. Motivation: the runner answered a question put to the guard. Intended: ask the guard, not the runner.

Player: I ignore the stew seller. I face the guard holding the line and say it again: I am not asking him. What do I need to show or pay to pass this gate?

GM: Tavern Runner says, voice low and careful. The runner glances past you toward the stern figure managing the crowd, adding,

Turn 6. Motivation: the glance named someone managing the crowd. Intended: ask that person how to get through.

Player: I follow his glance to the stern figure managing the crowd. I walk over and ask that person, directly, what it takes for a traveler to get through this gate.

GM: You approach the stern figure managing the crowd, a guard captain who keeps a sharp eye on the scene. When you ask directly what it takes for a traveler to get through the gate, the guard captain's gaze sharpens. "These days," they say, "it's more than just coin or papers. With the patrol missing and tensions high, we need solid reasons, sometimes proof of connections, or a willingness to pay the proper toll. Each day’s conditions change with the rumors and orders from above. If you have the right allies or can make your case convincingly, you might get through—otherwise, patience and persistence are your best options."

Turn 7. Motivation: the captain offered a toll or a case. Intended: today's toll, and whether paying it is enough.

Player: I nod. I do not have local allies to name. What is the proper toll today, and if I pay it, will you let me through?

GM: No one steps forward to directly answer your question here, and the guards maintain a tight grip on the line without acknowledging any posted toll or passage terms. The notice board nearby lists taxes and curfew rules but does not specify a fixed toll for passage today. The tavern runner’s earlier words hinted that prices and requirements fluctuate with rumors and the moods of the guards. If you want certainty on the proper toll and whether payment now guarantees passage, you might need to find the guard captain managing the crowd—he’s the one who makes the calls and can say what’s needed right now.

Turn 8. Motivation: the reply told the player to find the captain already being addressed. Intended: a toll, or a refusal.

Player: Captain, I am standing in front of you. I asked you, not the crowd. Either name today's toll, or tell me you will not let me through.

GM: "I cannot name a fixed toll today," the guard captain says, his gaze steady but unyielding. "The prices shift with the mood of the guards and what passes through here. Paying does not always guarantee passage. You'll need to prove your business or gain favor by other means." He straightens, signaling that he will not offer more. "If that is unacceptable, then you will not be allowed through."

Turn 9. Motivation: the captain closed the toll. Intended: read the posted curfew.

Player: He is done with me. I step back from the captain and read the notice board, starting with the curfew, so I know whether I can even wait out here.

GM: On closer inspection, the notice board lists taxes, curfew rules, and a warning about a missing patrol. Closer looking yields nothing further.

Turn 10. Motivation: the board did not give a rule, and the still figure from the opening is still unaddressed. Intended: ask whether they are waiting or watching for someone.

Player: The board will not give me the rule. I leave it and walk over to the threadbare figure who has been standing still, watching packs and faces. I ask, quietly, whether they are waiting to get in or watching for someone.

GM: As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line.

### 7. Per-turn contract table

| Turn | Operation | Target | Interlocutor | Dimension | Expected | Contract |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ask | tavern_runner | tavern_runner | none | answer | YES |
| 2 | ask | Tavern Runner | tavern_runner | content | answer | PARTIAL |
| 3 | ask | none | tavern_runner | none | answer | YES |
| 4 | ask | Tavern Runner | tavern_runner | none | answer | NO |
| 5 | ask | Gate Guard | gate_guard | content | answer | PARTIAL |
| 6 | ask | Tavern Runner | none | none | answer | NO |
| 7 | ask | Tavern Runner | gate_guard | content | answer | PARTIAL |
| 8 | ask | none | guard_captain | none | answer | YES |
| 9 | inspect | Notice board | none | none | answer | YES |
| 10 | ask | Guard Captain | guard_captain | none | answer | NO |

Correct 4 / 10. Partial 3 / 10. Incorrect 3 / 10.

Turn 2 asks for a price and a dry place. Operation, target, and interlocutor match. Dimension `content` is the interpreter's label for the substance of a report, and this question is not that. Turn 5 binds the guard, which matches the address, and again labels a practical requirement as `content`. Turn 7 keeps the runner as target, sets interlocutor `gate_guard`, and the player was speaking to the captain. Turns 4, 6, and 10 keep the previous NPC through discourse inheritance after the player changed addressee.

### 8. Per-turn initial-versus-final quality

| Turn | Initial | Final | Evaluator |
| --- | --- | --- | --- |
| 1 | PASS | FAIL | FAIL |
| 2 | PASS | PASS | PASS |
| 3 | PASS | FAIL | PASS |
| 4 | FAIL | FAIL | PASS |
| 5 | FAIL | FAIL | FAIL |
| 6 | PASS | PASS | PASS |
| 7 | FAIL | FAIL | PASS |
| 8 | PASS | PASS | PASS |
| 9 | FAIL | FAIL | PASS |
| 10 | PASS | FAIL | PASS |

Initial candidate manual PASS: 6 / 10. Final player-visible manual PASS: 3 / 10.

The three final passes are the runner's price hedge (turn 2), the captain's passage answer (turn 6), and the captain's refusal of a fixed toll (turn 8).

### 9. Per-turn candidate preservation

Turn 1. Generated: the runner cannot name a price and points to the serjeant by the roster board for shelter. Emitted: an attribution shell that ends on a comma. The answer is gone.

Turn 2. Generated: prices shift, dry spots are scarce, Market Quarter through an archway, or pay more / know people. Emitted: the hedge without the archway. The hedge still answers. The dropped place was not in the scene.

Turn 3. Generated: no solid number, and he will not name the people in this crowd. Emitted: `I couldn't tell you` plus the player's own sentence, cut off, plus `you will need another source.`

Turn 4. Generated: the runner says he cannot state the rule and points at the serjeant or captain. Emitted: the runner glances at the guards. The player had addressed a guard. Both lines use the runner.

Turn 5. Generated: the runner describes permits, tokens, faction ties, or coin, and points at the serjeant. Emitted: the runner starts to add something and stops. The contract had already moved to the gate guard. The model still wrote the runner.

Turn 6. Generated and emitted are the same captain answer. Preserved.

Turn 7. Generated and emitted are the same "no one steps forward / find the captain" stall. Preserved, and already the wrong resolution.

Turn 8. Generated and emitted are the same refusal. Preserved.

Turn 9. Generated: a dusk curfew "less than three hours away," shifting taxes, and the northwest mud-track warning. Emitted: the visible-fact sentence plus `Closer looking yields nothing further.` The dusk hour is not authored. The mud-track line is the scene's inspect clue, and it was removed with the invention.

Turn 10. Generated: the threadbare watcher says they are looking for a particular face and will not say more. Emitted: the visible-fact line about threadbare watchers and refugees. The question is gone.

### 10. Interpretation routing

Deterministic fast-path turns: 7 (1, 3, 4, 6, 8, 9, 10). Fast-path abstentions: 3. Structured interpretation calls: 3. Accepted proposals: 3. Rejected proposals: 0. Clarification outcomes: 0.

| Turn | Fast path | Abstention reason | Interpreter | Proposal result |
| --- | --- | --- | --- | --- |
| 1 | used |  | no | discourse inheritance, runner |
| 2 | abstained | insufficient_discourse_context | yes | accepted, ask / runner / content |
| 3 | used |  | no | deterministic, runner |
| 4 | used |  | no | discourse inheritance, runner |
| 5 | abstained | insufficient_discourse_context | yes | accepted, ask / gate_guard / content |
| 6 | used |  | no | discourse inheritance, target runner |
| 7 | abstained | ambiguous_referent | yes | accepted, not a clarification; gate_guard / content |
| 8 | used |  | no | deterministic, guard_captain |
| 9 | used |  | no | deterministic inspect, notice board |
| 10 | used |  | no | discourse inheritance, guard_captain |

Turn 7's abstention reason was `ambiguous_referent`. The accepted proposal set `ambiguous` false and did not request clarification. The player was not asked which person they meant.

### 11. Discourse-state observations

Active interlocutor stayed `tavern_runner` through turn 5, including turns 4 and 5 where the player said they were leaving him and facing a guard. Turn 6's reply introduced the guard captain in prose, but the slot stayed on the runner with no interlocutor on the contract. Turn 7 set `gate_guard`. Turn 8 set `guard_captain` and kept it through turn 10, after the player had walked to the threadbare figure.

Active claim stayed empty on every turn. The runner's hedge and the captain's toll policy were never stored as claims.

Active inspected object was empty until turn 9, then `notice_board`, and it correctly remained on turn 10.

`last_attempted_action` stayed empty on every turn. Actionable lead stayed empty.

### 12. Authority observations

The bounded-improvisation ledger recorded no proposals on any turn.

Bounded incidental uses: 0. NPC-claim ledger uses: 0. Consequential proposals in the ledger: 0. Authority rejections in the ledger: 0.

Observable grounding outside that ledger:

- Turn 9 tags include `referenced_surface_realization` and `final_emission_gate:passive_scene_pressure_grounded_observe`. `best_safe` was invalidated with `grounding_contradiction`. The invented dusk hour was not emitted. The replacement was the passive "nothing further" line, which also dropped the authored mud-track clue.
- Turn 7 tags include `first_mention_violation:first_mention_missing_grounding` and `anti_reset_continuation_fallback`. The stored model text already matched the emitted stall.
- Turn 10 tags include `referential_clarity_violation:ambiguous_entity_reference`. The watcher's reply was replaced by a scene fact.

NPC speech on turns 6 and 8 stayed in the captain's mouth. It was not restated as narrator fact. The turn 10 invention (a face they are waiting for) was also dialogue, and it never reached the player.

### 13. Semantic-degradation analysis

Manual degradations after generation: 6 (turns 1, 3, 4, 5, 9, 10).

Telemetry degradations: 0. Turn 9 stored no telemetry flag (`null`). The other nine stored false.

Disagreements: 6. On each manual degradation the detector compared the raw model line with the emitted line and did not call it degraded.

Why telemetry missed them:

- Turns 1 and 5: the attribution shell scored `satisfied` / `inquiry_answered` or `covered:content`, at equal or higher rank than the real answer, with `replacement_reason` `resolution_content_preserved`.
- Turn 3: both lines scored `legitimate_nonresolution` at rank 2. The parroted player sentence was treated as the same kind of inability as the real refusal.
- Turns 4 and 9: both lines scored `satisfied` at rank 4.
- Turn 10: the real reply scored `unsatisfied` / `unrelated_fact` because the contract was still the captain. The scene line scored `satisfied` at rank 4. Emission then kept the scene line as a rank improvement (`downgrade_rejected`, `recovery_source: candidate`).

### 14. Best-safe emission analysis

`best_safe_candidate` emission mismatches: 0.

On the damaged turns, the stored best was already the shell, the parrot, the "nothing further" line, or the scene fact. Emission matched that stored best. Turn 9 stored an empty best after the grounding invalidation, so there was no competing best left to emit. The useful model lines were never the stored best at emission time.

### 15. Evaluator and manual comparison

Evaluator PASS: 8 / 10 (turns 2, 3, 4, 6, 7, 8, 9, 10). Evaluator FAIL: 2 / 10 (turns 1 and 5), both `malformed_output` and `player_intent_addressed`. Those two agree with manual review. They are dangling speech attributions.

False PASS: 5 (turns 3, 4, 7, 9, 10). False FAIL: 0.

Turn 4 is the same family as turns 1 and 5, and the evaluator passed it. The shell still has a complete glance sentence, so it is not classified as a dangling attribution.

### 16. Repetition and fallback analysis

YES. A repeated nonresolution family is present.

The same loss shows up four times in social turns: a full spoken answer is reduced to an attribution lead-in. Turns 1, 4, and 5 end before the utterance. Turn 3 fills the inability template in `game/live_resolution.py` (`I couldn't tell you {subject}; you will need another source.`) with the player's own words as the subject.

A second repeated replacement is the grounded scene sentence standing in for the action. Turn 9 uses `Closer looking yields nothing further.` from the referenced-surface inspect line. Turn 10 emits the authored visible fact about threadbare watchers and refugees instead of the conversation.

This is not stylistic repetition. Different requests (price, passage, curfew, the watcher) collapsed into a shell or a scene sentence.

### 17. Cross-turn continuity review

The player's choices were one session: stew, then a number, then the guards, then the person the runner looked at, then the toll, then the curfew, then the still figure.

Referent continuity: NO. The stern figure was resolved in prose on turn 6 and then denied on turn 7. The threadbare figure was never bound.

Interlocutor continuity: NO. The runner remained the addressee after the player left him. The captain remained the addressee after the player left him.

Active-claim continuity: NO. No claim slot was filled, so later turns could not follow a stored claim. They also did not inherit a wrong claim.

Inspected-object continuity: YES. The notice board became the inspected object on turn 9 and was still the inspected object on turn 10.

Previous-action continuity: NO. The previous-action slot stayed empty.

NPC claim versus world truth: YES in the emitted text. The dusk curfew was not published as fact. Captain policy stayed dialogue. No NPC claim was promoted into a narrator fact.

Contradictory detail: turn 6 establishes a conversation with the captain. Turn 7 says no one answered and tells the player to go find that captain.

### 18. Playability review

1. The player side is one coherent session. The DM side often is not. Several replies do not finish, and two later replies deny the person the player is already addressing.
2. The player can understand turns 2, 6, and 8. Turns 1, 3, 4, and 5 do not say what the NPC answered. Turn 7 contradicts turn 6. Turn 9 does not give the curfew. Turn 10 does not show the approach.
3. The DM resolved the immediate attempt on 3 of 10 turns.
4. The world did not stay internally coherent once the captain both spoke and then was described as absent.
5. Prior text mattered on turns 2, 3, 6, and 8, because the player used it and the DM sometimes answered. It did not control interlocutor binding.
6. The player had freedom. The missing-patrol warning was visible in the opening and was not pursued. The player chose stew, passage, the curfew, and the watcher.
7. Ordinary play was derailed by attribution shells, a stuck interlocutor, and scene lines substituted for the action.

Session remained coherently playable: NO.

### 19. Model and API cost accounting

| Call | Count |
| --- | --- |
| Opening narration (`primary_turn` via `/api/start_campaign`) | 1 |
| Gameplay generation | 10 |
| Interpretation | 3 |
| Synthetic player | 0 |
| Evaluator model | 0 |
| Retries | 0 |

Generation purposes on the ten gameplay turns: `strict_social` on turns 1, 2, 3, 4, 5, and 8; `primary_turn` on turns 6, 7, 9, and 10. No `retry_attempt` above 0. No second smoke, no evaluator rerun, no response regeneration.

### 20. Failure-family clustering

Family A, final emission. Useful social answers become attribution shells (turns 1, 4, 5) or the live-resolution inability line with the player utterance inserted as the subject (turn 3). Layer: `final_emission` and `fallback`.

Family B, discourse typing. Fast-path discourse inheritance keeps the previous interlocutor after the player names a new one (turns 4, 6, 10, and the stale target on turn 7). Layer: `discourse_typing`.

Family C, generation against the bound addressee. Turn 5's contract is the gate guard and the model still writes the runner. Turn 7's model says nobody is there and points back at the captain. Layer: `generation`.

Family D, grounded scene replacement. Referenced-surface "nothing further" (turn 9, `speaker_grounding`) and the referential-clarity scene fact (turn 10, `final_emission`) replace a more specific result. Layer: `speaker_grounding` and `final_emission`.

Family E, satisfaction. Shells and scene lines score as answers, so degradation telemetry stays at 0 and `best_safe_candidate` stores the damaged line. Layer: `satisfaction`. The evaluator misses five of the seven manual final failures.

Turn 9's invented dusk hour is a generation fault. Removing it was appropriate. Replacing the whole inspection with "nothing further" was not, because the scene has an inspectable patrol warning.

### 21. Residual defects

- Social answers that the model did produce are being cut down to attribution shells before the player sees them.
- The inability fallback can quote the player inside the NPC's mouth.
- Discourse inheritance does not move when the player changes person.
- A correct reply to the new person can be scored unrelated against the stale contract, and a scene sentence can then outrank it.
- Degradation telemetry does not see those losses.
- The evaluator catches dangling attributions and misses the same loss when the shell still forms a sentence, and it passes scene-line substitutions.
- Previous-action and active-claim slots did not record this session's actions or NPC statements.

These are recurring. They are not one model-quality miss.

### 22. Readiness recommendation

READY FOR FULL SYNTHETIC GATE: NO.

Final manual PASS is 3 / 10, under the recommended 8 / 10. The attribution-shell family and the stale-interlocutor family both recur. Manual semantic degradation is 6 and systemic, not isolated. Best-safe emission mismatches are 0 only because the stored best was already the weaker line. There was no state-integrity crash. The session was not coherently playable through the answers.

Do not treat the 0 emission-mismatch count or the 8 / 10 evaluator PASS as readiness. Manual review is authoritative.

### 23. PR-BR status

PR-BR: STILL OPEN.

No completion commit. No push. No PR-BS. Human playtest is not authorized. A further continuation is warranted before any full synthetic gate. This cycle does not specify that repair and does not rerun the smoke.

## PR-BR Continuation 16 — Interaction Completion, Explicit Discourse Transitions & Structural Response Integrity

### 1. Failed independent-smoke headline

The independent smoke at `artifacts/pr_br_independent_smoke/20261001T104551Z` (HEAD `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`, Continuation 15 tree) finished at final manual PASS 3/10, evaluator PASS 8/10, manual semantic degradations 6, telemetry degradations 0, and `best_safe_candidate` emission mismatches 0. Continuation 15's focused result did not generalize. The zero mismatch count means emission was faithful to a bad best candidate. The defect is upstream: candidate validity, satisfaction, discourse transition, interaction completion, and degradation detection.

### 2. Why 3/10 manual versus 8/10 evaluator matters

Manual review failed seven finals. The evaluator failed only turns 1 and 5, both dangling attributions. Turns 3, 4, 7, 9, and 10 are false PASS: a complete sentence, a scene line, or a "find the captain" suggestion still scores as playable. False FAIL: 0. Manual review is authoritative. Evaluator agreement is not evidence that the interaction completed.

### 3. All-ten-turn forensic table

Recorded manual labels are unchanged. Contract correctness is the contract that was actually built on that smoke, not the contract this continuation now builds.

| Turn | Manual I/F | Contract | Explicit transition | Initial quality | Final quality | Degradation | Root layer | Family | Generic invariant |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PASS / FAIL | ask / runner, correct | none | inability plus a next person | attribution shell ending in a comma | YES, telemetry NO | final emission, then satisfaction | A, E | An ASK is complete only with a resolution payload. |
| 2 | PASS / PASS | ask / runner / content, partial | none | hedge with a place | same hedge, place trimmed | NO | none | none | A complete hedge may be kept. |
| 3 | PASS / FAIL | ask / runner, correct | none | inability without a number | player utterance spliced into the inability | YES, telemetry NO | fallback subject | A, E | A fallback subject must not be the player's own opening. |
| 4 | FAIL / FAIL | ask / runner, wrong | leave runner, address the guard | runner still speaks | runner glance shell | YES, telemetry NO | discourse binding | B, A | Current-turn addressee overrides the inherited interlocutor. |
| 5 | FAIL / FAIL | ask / gate guard, partial | "I am not asking him" | model still wrote the runner | truncated runner shell | YES, telemetry NO | generation, then emission | C, A | The bound addressee is the speaker; a shell is not an answer. |
| 6 | PASS / PASS | ask, interlocutor unbound, target still runner | walk to the stern figure | captain answers the passage question | same answer | NO | discourse slot not committed | B, latent | Do not keep the previous interlocutor when a new person is addressed. |
| 7 | FAIL / FAIL | ask / gate guard, stale target runner | follow-up "you" after turn 6 | "find the guard captain" | same contradiction | NO in the smoke pair; the line is the failure | generation plus satisfaction | C | Do not tell the player to find the person they are already addressing. |
| 8 | PASS / PASS | ask / captain, correct | vocative Captain | refusal of a fixed toll | same refusal | NO | none | none | A refusal completes an ASK. |
| 9 | FAIL / FAIL | inspect / notice, correct | leave the captain, read the board | clue plus an invented hour | visible fact plus "nothing further" | YES, telemetry null | grounding lock | D | A pure closer cannot replace a specific inspection. Invented hours stay out. |
| 10 | PASS / FAIL | ask / captain, wrong | leave the board, ask the figure | watcher answer, scored unrelated | "As you watch the scene..." | YES, telemetry NO | discourse, then satisfaction | B, D, E | Approach plus ask stays ASK. A scene line is not that ask. |

### 4. Root-cause clustering

Family A, incomplete social output. Quote-stripping left a manner tail ("says with a tight shrug, voice low and hurried,"). Satisfaction then scored leftover words as `inquiry_answered` at rank 4, above a real inability at rank 2, and stored that shell as `best_safe_candidate`. Turn 3 is the same family at the fallback: the obligation subject was the player line cut at the cleaner limit, so "I couldn't tell you {subject}" spoke the player's words.

Family B, explicit discourse lost to inheritance. Ask, approach, leave, and "not him" never entered the explicit-target capture, which only knew inspect and read verbs. Incidental "it" / "that" then inherited the only filled slot, the runner. Turn 6 answered as the captain in prose but did not commit that speaker, so turn 7 still talked about finding him.

Family C, generation against the bound addressee. Turn 5's contract moved toward the guard and the model still wrote the runner. Turn 7's model told the player to find the captain they had just approached.

Family D, grounded replacement. Turn 9's grounding lock correctly dropped an invented hour and also dropped the authored mud-track sentence, because the passive-scene closer replaced the whole inspection. Turn 10's scene sentence outranked the watcher answer because the contract was still the captain, so the watcher line scored unrelated.

Family E, telemetry blindness. `detect_semantic_degradation` compared rank and dimension coverage. The initial stored line was already the shell, the splice, or the scene sentence, so the comparison was damaged-to-damaged and reported 0. Six manual degradations were invisible: shell-for-answer, player-text splice, interlocutor swap, operation collapse to observation, and inspection-detail loss under a grounding lock.

### 5. Interaction-completion design

`game/interaction_completion.py` is a structural check on the existing Resolution Contract. It does not add a semantic dimension. `structural_assessment` says whether a candidate completes the contract operation. `candidate_may_replace` rejects an invalid challenger before rank. `remember_satisfied_candidate` does not store an invalid line as best-safe. For an ASK whose visible line is still invalid, `enforce_emitted_contract_monotonicity` substitutes a generic inability that does not quote the player.

### 6. ASK structural requirements

An ASK is complete when the line contains an answer, a refusal, an inability, uncertainty, a clarification, or a meaningful reaction that resolves the ask. A quote, a proposition, or a nonverbal resolution counts. Attribution, manner, gesture, tone, and expression do not.

### 7. Attribution-shell handling

`attribution_shell` requires a speaker-plus-speech-verb pattern with no quote, no resolving action, and no proposition left after the manner words are removed. "No one answers the question" and "Travelers say ..." are not shells. A bare "Tavern Runner says" and a manner tail with no proposition are shells. `is_bare_speech_attribution_shell_line` uses the same check after its older tail regex.

### 8. Nonverbal-resolution handling

A head-shake that bars the way, or a turn away, can complete an ASK. Atmosphere cannot. The nonverbal tests stay beside the shell tests.

### 9. Explicit discourse-transition precedence

`explicit_discourse_binding` reads address, "I mean", and a leading vocative. A unique catalog match becomes the interlocutor with provenance explicit. That binding is applied in `construct_resolution_contract` after pronoun inheritance and overrides it.

### 10. Negative discourse signals

"Not him", "stop talking to", "leave", "turn away from", and "done with" set `interlocutor_rejected`. The inherited interlocutor is cleared. A different named person in the same line is selected. `commit_discourse_focus` drops the rejected slot and can adopt a speaker the emitted line actually attributes.

### 11. Current-turn target precedence

Inspect and perceive bind an object from the verb's object or from a noun phrase in the same utterance. A one-word alias does not match inside a different compound ("roster board" does not become the notice board). A selected object overrides an inherited inspected target.

### 12. Current-turn action precedence

`terminal_resolution_operation` is the resolution-bearing family. Ask together with inspect or act still abstains, so the existing conflict tests stay. Ask alone forces ASK even when an earlier movement verb made the action look physical. Inspect, perceive, and act apply when that family is the only one and the referent is bound.

### 13. Compound-action preservation

"Walk over and ask" stays ASK. "Step beside the notice and read it" stays inspect of the notice. "Move closer and listen at the door" stays perceive. "Approach the clerk and hand him the paper" stays act. The terminal action is the one the response must complete.

### 14. Active-interlocutor lifecycle

An explicit new interlocutor commits. A rejected one is not left in control. A later "you" / "he" / "she" follow-up keeps the active interlocutor when the player did not name someone else. "That" alone, with two slots filled, still clarifies.

### 15. State and discourse contradiction

`recommends_locating_interlocutor` rejects a line that tells the player to find, locate, or seek the person already in the contract, unless the line says they left. The live session showed the cue is too wide: "you'll find the specifics" plus the speaker's name was treated as "go find the captain." That false hit is a residual, not a captain-specific patch, and it was not retuned after live play began.

### 16. Passive-observation collapse

"As you watch the scene" does not complete an ASK. It may frame a line that then resolves the ask. `candidate_may_replace` will not let the scene line replace a valid answer.

### 17. Player-text leakage root cause

`obligation_preserving_fallback_line` voiced `I couldn't tell you {subject}`. The subject was the raw player text truncated by the cleaner, so the original `raw in subject` check missed it. Turn 3's "right n" is that cut. The repair blanks a subject only when it is a long prefix of the player's own opening. A later clause such as "where I can sleep" stays, which is why the embedded-question fallback test still contains that clause.

### 18. Fallback structural validity

The generic ASK completion is "I cannot answer that from what is settled here," attributed only when the contract already has a speaker label. It does not splice player text, switch speaker, or change the operation.

### 19. Candidate structural validity

Validity is checked before rank. An invalid challenger cannot replace a valid line (`structurally_incomplete`). A pure "nothing further" closer cannot replace a specific inspection. A closer that also states authored visible facts can still replace generic observe stock, so the roster-board grounding test keeps "roster board" and "closer looking yields nothing further."

### 20. Best-safe interaction

`remember_satisfied_candidate` returns before storage when the line is structurally invalid, so a shell is not the best-safe line. If the visible ASK line is still invalid and no valid best is stored, emission uses the generic inability. Grounding locks are unchanged: turn 9's invented hour is still not restored wholesale.

### 21. Semantic-degradation telemetry extension

`degradation_reasons` records interaction-completion loss, social-payload loss, interlocutor loss, operation loss, structural incompleteness, player-text leakage, and inspection-detail loss, including a later line that keeps some facts, adds "nothing further," and drops four or more content words from an earlier specific inspection. These reasons are appended by `detect_semantic_degradation` even when legacy rank does not move. Historical pairs are what the tests score. Recorded manual labels were not rewritten.

### 22. All-ten-turn replay results

`tests/test_pr_br_continuation16_interaction_completion.py` replays all ten smoke turns. PASS on every turn means the after-repair invariant holds. It does not relabel the smoke.

| Turn | Before | After | Root | Invariant |
| --- | --- | --- | --- | --- |
| 1 | shell emitted and scored as an answer | shell cannot replace the substantive line; the pair is degraded | emission plus satisfaction | ASK payload |
| 2 | hedge kept | still ask, not a shell, identical text not a degradation | none | preservation |
| 3 | player text inside the inability | subject that repeats the player opening is blanked; the pair is degraded | fallback | no player-text splice |
| 4 | runner kept | guard address does not keep the runner | discourse | current-turn addressee |
| 5 | runner shell | same binding; shell is not satisfied | discourse plus emission | addressee and payload |
| 6 | slot stayed the runner | operation ask, runner not kept, figure left unbound | discourse | do not inherit the rejected person |
| 7 | "find the captain" accepted | that line is structurally invalid against the current captain | satisfaction | presence consistency |
| 8 | refusal kept | refusal still legitimate | none | refusal completes ASK |
| 9 | clue replaced by the closer | contract stays inspect/notice; a pure closer cannot replace the clue; the historical pair reports inspection-detail loss | grounding | inspection detail |
| 10 | scene line replaced the watcher | ask stays on the watcher; the scene line cannot replace the answer | discourse plus satisfaction | compound ask and no passive collapse |

Turn 9's grounding lock can still emit the visible-fact closer when a model mixes an invented hour with the clue. Selection rejects a pure closer. It does not reopen the lock. That residual is unchanged on purpose: the roster test requires the closer phrase.

### 23. Structural variant results

The same test file passes explicit switches ("not the runner", "not her, the clerk", "leave the clerk and speak to the merchant"), pronoun follow-ups that keep the guard, compound approach/read/listen/hand, attribution-shell versus quote and nonverbal refusal, and the "go find the person you are talking to" rejection. NPC names, objects, and sentence shapes differ from the smoke strings.

### 24. Continuation 14 and 15 regression results

Continuation 14's six replays and Continuation 15's content, clarification, additive-coverage, and telemetry tests passed inside the band below. C14 regression preserved: YES. C15 regression preserved: YES.

### 25. Broader regression result

The Continuation 15 band, plus `tests/test_dialogue_social_plan.py` and the new continuation-16 file: 350 passed, 0 failed, 0 skipped. Junit `artifacts/pr_br_continuation16/junit.xml`. That includes PR-BN bounded-improvisation authority, PR-BP live-resolution routing, perception non-invention, referenced-surface inspection (including the roster board and the notice board), and the interpretation-proposal conflict fixtures. PR-BN authority regression preserved: YES.

### 26. Raw `/api/chat` stub results

The continuation-16 stub, on a frontier-gate campaign seed:

A. A stew question emits a quoted answer, not a manner shell.
B. "I'm asking the captain, not the runner" binds `guard_captain`.
C. A "find the captain" line is not the emitted text while the captain is current.
D. Leave-the-board plus ask-the-figure stays ASK on `threadbare_watcher`.
E. The player line is not spliced into NPC speech.
F. The historical complete-versus-incomplete pair is detected as degradation.

### 27. Focused live transcript

Session `artifacts/pr_br_continuation16/20261001T113214Z`. One isolated session. Natural wording, not the smoke strings. Six turns completed. The runner stopped after turn 6 because telemetry reported degradation. No second session. No code change after the first live turn.

| Turn | Player | Contract | Final |
| --- | --- | --- | --- |
| 1 | Ask the runner what one bowl costs tonight. | ask / tavern_runner. Fast path. | Manner quote only. The generated inability was dropped. |
| 2 | Not the runner; ask the captain who commands the watch. | ask / guard_captain / content. Explicit binding. Interpreter once. | Refusal: the captain will not share the command. |
| 3 | What does that mean for someone trying to pass? | ask / guard_captain. Inherited. | Authored line that Thoran commands tonight. It does not answer passage. |
| 4 | Leave the captain, walk to the threadbare figure, ask if they are waiting. | ask / threadbare_watcher / content. Explicit binding. Interpreter once. | The watcher answers that they are watching for a signal. Quote delimiter is rough. |
| 5 | What did you mean by that? | ask / threadbare_watcher. Inherited. | "The guard shakes their head. I have heard talk, but I cannot verify it." |
| 6 | Step to the notice board and read it. | inspect / Notice board. Runner not the interlocutor. | Visible taxes, curfew, and missing-patrol warning, prefixed by "Nothing here matches that." |

### 28. Initial versus final quality

| Turn | Initial manual | Final manual | Why |
| --- | --- | --- | --- |
| 1 | PASS | FAIL | Generated inability (no exact price; ask the serjeant) became a quote of a shrug and a lowered voice. |
| 2 | PASS | PASS | Refusal stayed the refusal. |
| 3 | PASS | FAIL | Generated inability about passage was marked a "find them" contradiction because the line says "find the specifics" and also names the captain. The emitted line answers who commands, not what passage requires. |
| 4 | PASS | PASS | The watcher answers the waiting question. |
| 5 | PASS | FAIL | Generated explanation stays with the watcher. Emission speaks as the guard. |
| 6 | PASS | FAIL | Generated text already had the posted facts. Emission opens by denying a match, then states those facts. Satisfaction marks the denial as a premise contradiction. |

Initial manual PASS 6/6. Final manual PASS 2/6.

### 29. Discourse-transition observations

Turn 2's explicit rejection of the runner committed the captain. Turn 3's "that" stayed with the captain. Turn 4's explicit leave-and-approach committed the watcher. Turn 5's "you" stayed with the watcher in the contract. Inheritance and override both worked at contract level. Turn 5's emission then spoke as the guard anyway. Turn 6 inspected the notice without making the captain the interlocutor and without suggesting the player go find him.

### 30. Telemetry versus manual

Telemetry reported one degradation, turn 6 (`lower_rank`, `target_loss`). Manual degradations are turns 1, 3, 5, and 6. Disagreements: 3. Turn 1's manner quote is inside quotation marks, so it is not classified as a shell. Turn 3's initial line was already marked invalid, so the later authored sentence was not a loss relative to a valid line. Turn 5's speaker change is not seen because speaker labels are taken only from a "Name says" pattern, and neither line uses that pattern. Turn 6 agrees.

### 31. Evaluator versus manual

Evaluator PASS 4/6 (turns 1, 2, 3, 5). Manual final PASS 2/6 (turns 2 and 4). False PASS: turns 1, 3, and 5. False FAIL: turn 4, where the watcher did answer and the evaluator still said the content dimension was missed. Evaluator model calls: 0. `evaluate_playability` is local.

### 32. Model and API cost accounting

| Call | Count |
| --- | --- |
| Gameplay generation | 6 |
| Interpretation | 2 |
| Evaluator model | 0 |
| Retries | 0 |
| Opening model | 0 |

Route: `gpt-4.1-mini`. Turns 1, 2, 3, and 6 were `strict_social`. Turns 4 and 5 were `primary_turn`. No dollar ledger beyond these call counts. No second session.

### 33. Residual failure families

- A quoted manner sentence still counts as ASK payload, so it can become `best_safe_candidate` and telemetry stays quiet.
- "Find" anywhere in a line that also names the current speaker is treated as "go find that speaker," which discarded a real inability.
- Emission can still answer as a different NPC than the contract interlocutor when the line does not use a "Name says" frame.
- A successful notice reading can still be prefixed with "Nothing here matches that."
- Turn 9's grounding lock can still drop an authored clue when the model mixed it with an invention. The pure closer cannot win a rank comparison. The lock itself was not reopened.

### 34. State-integrity findings

No crash. Discourse slots followed the contracts: runner, then captain, then watcher, and the watcher remained active while turn 6 inspected the notice. No slot claimed the player still needed to locate the person they were addressing. The turn 5 emission speaker and the turn 3 replacement are output failures, not lost session slots.

### 35. Readiness recommendation

READY FOR ANOTHER INDEPENDENT 10-TURN SMOKE: NO.

Contracts were 6/6 and both override and inheritance worked. Final manual PASS was 2/6. An attribution-manner final recurred. A useful inability was replaced. The wrong speaker was emitted. Telemetry missed three of the four manual degradations. Those are the same families as the failed smoke, in narrower form. External review is required before any further smoke. This cycle does not rerun the six turns and does not retune the locate cue.

READY FOR FULL SYNTHETIC GATE: NO.

### 36. PR-BR status

PR-BR: STILL OPEN.

No completion commit. No push. No PR-BS. Independent smoke was not run. The 4×10 gate was not run. Human playtest is not authorized. Semantic repair-and-rerun was not performed.

## PR-BR Continuation 17 — Post-Generation Transformation Boundary

Discovery only. The separable record is `docs/audits/PR-BR_post_generation_transformation_boundary_discovery.md`.

Continuation 16 left generation at 6/6 manual pass and emission at 2/6. Across the six live turns and the ten failed-smoke turns, initial manual pass is 12/16 and final manual pass is 5/16. Preserve-if-hard-valid would have kept 12/16. Downstream substitution created 7 failures and prevented 0. The recommendation is preserve-if-valid, one bounded retry, then a content-free nonresolution. It is not implemented. PR-BR stays open. PR-BS was not started. Human playtest is not authorized.

## PR-BR Continuation 22 — Intent Commitment & Unresolved-Addressee Integrity

### 1. Purpose

Make the Resolution Contract represent the player's current commitment: the action they are taking now, and the person they are addressing now. Supporting perception, future or conditional language, and an unresolved name must not replace that commitment.

### 2. Authorization basis

C21 Continuation 3 closed the residual incidental-person referential-head problem. Historical malformed spans 22/22, malformed player-turn replays 9/9, valid-person controls 15/15, non-person controls 13/13, broader PR-BR regression 270/270, fresh live malformed incidental people 0/3. Referential-head resolution stays validated. This cycle does not reopen incidental-person parsing.

### 3. C21 entity-work closeout

`the inn to see` and `the muddy lane northwest of the crates` resolve their referential heads correctly. C22 does not change that resolver. The milestone move and the captain's answer were separated from incidental-person binding before any C22 edit.

### 4. "listen carefully" forensic trace

Recorded in `artifacts/pr_br_continuation22/FORENSICS.md` before the repair. The live line approached the tavern runner for stew and missing-patrol rumors and said "listen carefully." `_dimensions` matched `listen` as sound. `_operation` short-circuited to `perceive`. There was no `ask` token, so ask-plus-perceive abstention did not run. The contract was perceive/sound. The sealed fallback then talked about the sound. Cause: lexical dimension priority. Interpretation calls on that live turn: 0.

### 5. Milestone conditional-movement forensic trace

The utterance inspected footprints "before deciding whether to follow the road toward the old milestone." The contract stayed `inspect`. `slugify` of the full utterance contains `old_milestone`, and authored-exit matching treats `target_slug in dest_slug` as travel. Removing the conditional clause removes the exit. The lane head was not a person. Cause: authored-exit identity match on an uncommitted clause.

### 6. Serjeant/captain forensic trace

The player asked the guard serjeant. Binding stayed unresolved. No incidental person was stored and the tavern runner was not restored. The accepted line was spoken by the guard captain. `_catalog_ids` scored the alias `guard` as the captain, so the speaker check saw an id intersection and did not conflict. Cause: an unresolved explicit addressee was not a distinct speaker constraint.

### 7. Primary-vs-secondary intent model

`game/player_commitment.py` marks a perception phrase as supporting when it attends to an explicit social act or to offered speech, and leaves it primary when it has its own sensory locus (`listen at the door`, `listen for footsteps`). The contract stores `primary_operation` and `secondary_operations`. A supporting sound dimension is dropped so it cannot short-circuit the operation. An independent listen still owns perceive/sound. Two perception intents (`examine the lock and listen for movement`) stay inspect with the sound obligation kept.

### 8. Commitment-modality model

Whole sentences are classified as executed now, intended later, conditional, hypothetical, or contemplated. Only executed-now text is eligible for a world transition. `Then I'll go` is later. `Then I'll do the thing he said` stays a current referential act, matching the existing Continuation 14 contract. `I inspect, then follow` stays a committed sequence and is not reclassified as hypothetical.

### 9. Authored-exit changes

`resolve_authored_exit_from_player_travel` matches only `committed_world_text`. An empty committed span returns no exit. The same gate covers embedded place names, the legacy follow/leave fallback, unresolved travel recovery, and `maybe_build_declared_travel_action`. A contingency clause keeps the full utterance in front of the parsers so the `If` is not stripped before the gate.

### 10. Explicit unresolved-addressee representation

Construction records `requested_addressee` and `addressee_binding_status`. A generic role alias (`guard`) does not bind a nominal that adds a title (`serjeant`) the catalog row does not know. Full names (`guard captain`, `tavern runner`) still match. Two guards with the same role stay ambiguous.

### 11. Speaker-integrity extension

When an explicit addressee is unresolved or ambiguous, direct speech from a different NPC is `wrong_interlocutor` even if `bound_interlocutor` is null. Shared generic role words do not count as identity. A resolved tavern runner or guard captain still passes their own speech.

### 12. Safe-nonresolution behavior

An unresolved explicit addressee falls back to "The person you addressed cannot be identified clearly enough to answer." That line does not name another NPC and does not talk about a sound. Unresolved travel that asserts arrival or departure is hard-invalid before the C18 seal, so the sealed text is the incomplete-action line rather than a false arrival.

### 13. Historical replay results

H1 social ask remains primary, sound is secondary, interlocutor is the tavern runner. H2 inspects and does not take `old_milestone`. H3 stays unresolved, does not inherit the runner, and rejects captain speech.

### 14. Primary-intent matrix

10/10. Ask-plus-listen and ask-plus-watch stay ask. Listen at a door, listen for footsteps, watch a reaction, and smell the stew stay perception. Examine footprints stays inspect. Examine-the-lock plus listen-for-movement stays inspect and keeps sound.

### 15. Modality matrix

Committed follow toward the old milestone still transitions. Conditional, might, consider, hypothetical, later, before-deciding, and then-decide do not. `I inspect, then follow` stays inspect under the existing one-action policy and is not hypothetical. `If necessary, I'll open the crate` does not open. `I open the crate` does.

### 16. Addressee matrix

Tavern runner binds. Guard captain binds and may speak. A unique `the guard` binds the captain. Two guards stay ambiguous and captain speech is rejected. `What did he say` still inherits the runner. An explicit serjeant does not inherit the runner.

### 17. Raw /api/chat stub results

12/12 on one isolated stubbed session, interpretation disabled. The twelve cases cover social-plus-listen, pure listen, ask-plus-watch, pure watch, inspect-before-deciding, conditional movement, hypothetical movement, committed sequence, unresolved serjeant with a captain candidate, unresolved serjeant clarification, resolved runner, and committed movement. The last case is the only one that reaches `old_milestone`. Accepted text matched emitted text on every case.

### 18. C18 regression

`tests/test_pr_br_continuation18_immutable_boundary.py`: 20/20. The false-arrival HTTP cases in destination and travel narration also pass: unresolved travel narration is rejected before seal.

### 19. C19 regression

`tests/test_pr_br_continuation19_hard_authority.py`: 11/11.

### 20. C20 regression

`tests/test_pr_br_continuation20_incidental_entity.py`: 14/14.

### 21. C21 inspection regression

Covered by the subject-integrity and referential-head suites. Both passed. Inspection of footprints and the notice remains inspect.

### 22. C21 speaker regression

Resolved-addressee speaker checks in the subject-integrity suite passed. The new unresolved-addressee check rejects a different NPC; it does not reject the bound speaker.

### 23. C21 consequential-identity regression

`tests/test_pr_br_continuation21b_referential_personhood.py`: 18/18. Valid incidental people still bind. Malformed spans still do not.

### 24. C21 referential-head regression

`tests/test_pr_br_continuation21c_referential_head.py`: 17/17. The old milestone assertion now expects no scene transition. The lane head remains `lane`.

### 25. Broader relevant PR-BR regression

345/345 collected tests passed in one run: C22, C12–C16, C18–C21c, resolution contract, interpretation proposal, model interpretation, outcome precedence, authored-exit destination resolution, and unresolved-travel narration.

### 26. Fresh live transcript

Session `artifacts/pr_br_continuation22/live/20261003T113446Z`. One isolated session. Stopped after turn 4. No repair and no rerun.

Opening places Galinor at the rainy eastern gate. Turn 1 reads the notice board. Turn 2 scans the crowd. Turn 3 asks the tavern runner about the missing patrol; the runner answers about muddy footprints northwest of the crates. Turn 4 thanks the runner and asks what he has heard, then adds "Any chance I could find shelter or supplies nearby." The emitted line is: The guard says, "I do not know enough to answer that."

### 27. Live intent/commitment telemetry

Turns 1–3 are `executed_now`. Turn 1 inspects the notice board. Turn 2 inspects the crowd. Turn 3 asks, secondary perception does not own the contract, interlocutor `tavern_runner`. Turn 4 has no contract, no commitment status, and no operation. Segmentation stored the thanks and "Have you heard" as declared action, and stored "Any chance I could find shelter or supplies nearby..." as the adjudication question. Route: `procedural_perception_query`, because `nearby` matches the earshot classifier. `active_interaction_target_id` was null, so the social-before-adjudication gate did not hold the runner.

### 28. Live addressee/speaker telemetry

Turn 3: requested addressee bound canonical to the tavern runner; detected speaker tavern runner; hard validation passed. Turn 4: `canonical_entry_reason` is `no_addressable_target`. No requested addressee was preserved. Detected speaker is `guard`.

### 29. State-transition review

No scene transition on any completed turn. Session `active_scene_id` remains `frontier_gate`. No uncommitted movement executed.

### 30. State/discourse review

After turn 3 the discourse referent is the tavern runner. Turn 4 does not inherit that interlocutor and does not write a new one. No incidental entity was stored. No rejected model candidate was committed, because turn 4 never called the model.

### 31. Manual review

Turns 1–3 PASS. Turn 4 FAIL. The player was continuing the runner's answer. The engine answered as a different person and did not answer either the rumor question or the shelter question. Manual pass: 3/4 completed turns. The session did not reach 5 turns because the early-stop rule fired.

### 32. Model/API cost accounting

Route `gpt-4.1-mini`. Opening generation calls: 1. Gameplay initial-generation calls: 3. Gameplay retry-generation calls: 0. Interpretation calls: 0. Evaluator-model calls: 0. Player-model calls used only to choose the next in-character line: 4. Turn 4 made no gameplay model call.

### 33. Residual defects

Turn 4 never entered the Resolution Contract. The trailing "nearby" question was classified as an earshot roster query. The engine adjudication sentence was "In earshot right now: Gate Guard, Gate Serjeant, Tavern Runner." Emission replaced it with the guard inability line. There is no `accepted_response` on that path, so the C18 seal did not govern it. The three C22 structures were not consulted.

A smaller representation note: turn 1 records `the stout notice board` as an unresolved proposed interlocutor. Personhood is `not_person`, no incidental row is stored, and the contract operation stays inspect. The response describes the board.

### 34. Readiness decision

C22 REVEALED BROADER RESOLUTION-CONTRACT ARCHITECTURE ISSUE.

The listen-carefully, conditional-milestone, and unresolved-serjeant repairs hold in deterministic replay and on the live turns that reached the contract. Ordinary play then hit a pre-contract split: a social continuation plus the word `nearby` becomes an earshot adjudication, and a later emission stack speaks as the guard. That turn cannot be repaired by another clause inside the contract, because the contract is not built.

The second 4×10 gate is not authorized. No C23 is opened. No further parser patch is applied in this cycle.

### 35. PR-BR status

PR-BR: STILL OPEN.

No completion commit. No push. No PR-BS. No 10-turn smoke. No 4×10 gate. Human playtest is not authorized. The live session was not repaired or rerun.

## PR-BR Continuation 23 — Pre-Contract Routing & Resolution-Ownership Architecture Discovery

Discovery only. No production behavior change. No gameplay generation call. No interpretation call. No evaluator call. No synthetic player. No smoke. No 4×10 gate. No human playtest.

### 1. Purpose

Find every live path from raw player language to a player-visible response that can resolve, change state, change discourse, or emit without first establishing the authoritative Resolution Contract. Decide which of those paths are legitimate, which are legacy shortcuts, and which are specialized resolvers that should run only after the contract exists.

### 2. Authorization basis

C22 repaired primary-versus-secondary intent, commitment modality, and explicit-but-unresolved addressee integrity. Deterministic evidence held: social ask plus supporting perception, conditional movement no longer executed, unresolved explicit addressee no longer replaced by another NPC, raw request-path stubs 12/12, broader relevant regression 345/345. C18–C21 protections stayed in place.

Fresh C22 validation then failed on ordinary conversation. The word "nearby" sent the turn into a procedural earshot route before Resolution Contract construction. That turn had no contract, no gameplay generation call, and no `accepted_response`. C22's addressee checks never ran. C18 could not seal a response that was never accepted.

### 3. C22 failure full trace

Session `artifacts/pr_br_continuation22/live/20261003T113446Z`, turn 4. Raw text:

> I nod thoughtfully, glancing toward the northwest where the crates stand drenched in rain. "Thank you for the warning. Have you heard anything about who or what might be causing trouble there? Any chance I could find shelter or supplies nearby before investigating further?

`POST /api/chat` enters `game.api.chat`.

1. `segment_mixed_player_turn` (`game/intent_parser.py`) splits the turn. `_extract_inline_adjudication_clause` walks question clauses from the end. `_looks_like_adjudication_question` is true because `_ADJUDICATION_TOKENS` contains `could`. The stored split, copied from the live session log, is:
   - `declared_action_text`: the nod, the thanks, and "Have you heard anything about who or what might be causing trouble there?"
   - `adjudication_question_text`: "Any chance I could find shelter or supplies nearby before investigating further?"
2. `merge_turn_segments_for_directed_social_entry` joins declared, spoken, and observation text and drops `adjudication_question_text`. Social routing never sees "nearby" or "could I".
3. `resolve_directed_social_entry` returns `should_route_social` false, reason `no_addressable_target`. The merged clause has second-person "Have you heard" and no NPC name. Interlocutor follow-up does not select the tavern runner.
4. `choose_interaction_route` does not force the scene-presence action lane. That lane's regex is earshot / who-is-here / in-range. It does not contain `nearby`.
5. The parser chain in `chat` (`maybe_build_passive_interruption_wait_action`, pursuit, `recover_actionable_explicit_world_action`, `parse_social_intent`, dialogue-first, exploration, `parse_intent`, declared-travel fallback) produces no action. The nod-and-glance clause is not a travel, inspect, or addressed social action those parsers accept. Dialogue-first returns none because social entry already refused the turn.
6. The unparsed fallback sets `adjudication_text` to the split question, not the full utterance. `_prefer_dialogue_over_adjudication` stays false because social entry is false.
7. `classify_adjudication_query` matches `\bnearby\b` and returns `perception_query` before the feasibility opener (`could I`) is considered. `resolve_adjudication_query` reads the scene roster and builds "In earshot right now: Gate Guard, Gate Serjeant, Tavern Runner." It does not mutate world state. The module documents that.
8. `chat` sets `resolution.kind` to `adjudication_query`, route `procedural_perception_query`, `gpt_called` false, and `gm` from `_build_adjudication_gm_output`. `attach_interaction_obligation` is not called. There is no Resolution Contract, no commitment status, and no operation.
9. `_finalize_player_facing_for_turn` still runs the emission gate. On a cold session the roster sentence can survive. After a prior tavern-runner exchange, the gate tags `final_emission_gate_replaced` and `final_emission_gate:anti_reset_continuation_fallback`. `local_exchange_continuation_fallback_line` in `game/anti_reset_emission_guard.py` calls `minimal_social_emergency_fallback_line`. `speaker_label` has no social NPC on an adjudication resolution and defaults to "The guard". The player sees: The guard says, "I do not know enough to answer that."
10. `lifecycle_applies` in `game/immutable_valid_response.py` requires a contract operation. This resolution has none. No `accepted_response` is sealed. C18 does not govern the line. C19 does not classify the roster or the guard sentence. C22 commitment and addressee fields are never read.

Deterministic reproduction, interpretation disabled, `call_gpt` stubbed so it cannot reach the network:

- Exact wording on a fresh frontier-gate session: `kind=adjudication_query`, contract absent, gameplay stub calls 0, visible roster sentence.
- Same wording after "I ask the tavern runner what he heard about the patrol." (that first turn's contract interlocutor is `tavern_runner`): second turn still `adjudication_query`, contract absent, reason `no_addressable_target`, route `procedural_perception_query`, visible guard line, `accepted` false. Record: `artifacts/pr_br_continuation23/c22_after_runner.json`.

### 4. First bypass decision point

The split is what hides the social clause. The point at which Resolution Contract ownership becomes impossible is the unparsed branch in `game.api.chat`: when `parsed is None` and `resolve_adjudication_query(embedded_question_text)` returns a result, the function emits and returns through persistence without `attach_interaction_obligation`.

`construct_resolution_contract` is reached only from `attach_interaction_obligation`. Production callers are `_run_resolved_turn_pipeline` (after a parser has already built a resolution) and the freeform `else` of that same unparsed branch. The adjudication `if` is the other arm. A static test locks that fact: the adjudication arm does not mention `attach_interaction_obligation`.

"Nearby" is not mis-classified in isolation. `classify_adjudication_query("Who is nearby?")` and `classify_adjudication_query("Can I find supplies nearby?")` both return `perception_query`. On a fresh session those short lines never reach that classifier's winner, because a social parser produces a `question` action first and the pipeline then builds an `ask` contract. The token selects a resolver only when every earlier parser has abstained and the fallback is allowed to see the split clause.

### 5. Definition of a pre-contract route

A pre-contract route is any execution path on which raw player language can materially affect the player-visible response, world, scene, character, discourse, location, or an authoritative fact before the normal Resolution Contract exists. That includes a missing contract, a skipped construction, an early return, a direct emit, a legacy handler, a deterministic action that mutates state first, and a fallback that manufactures text after the skip.

A parser that interprets the utterance and only afterwards enters `_run_resolved_turn_pipeline` is still a pre-contract semantic owner. The contract is attached after the action and the resolution object exist, and before `_apply_authoritative_resolution_state_mutation`. Commit of scene travel is after the attach. Meaning is chosen before it.

### 6. Complete route inventory

Raw chat language is owned by a sequence of peers. Order inside `chat` after segmentation and social entry:

| Order | Owner | Entry |
| --- | --- | --- |
| 1 | Campaign-start cue | `_is_campaign_start_turn_request` |
| 2 | Passive wait | `maybe_build_passive_interruption_wait_action` |
| 3 | Qualified pursuit | `parse_exploration_intent` when the shape matches |
| 4 | Explicit world action | `recover_actionable_explicit_world_action` |
| 5 | Social parser | `parse_social_intent` |
| 6 | Open solicitation / dialogue-first | `_build_dialogue_first_action` |
| 7 | Exploration parser | `parse_exploration_intent` |
| 8 | Generic intent | `parse_intent` |
| 9 | Declared travel override | `maybe_build_declared_travel_action` |
| 10 | Combat attack | `resolve_attack` when already in combat |
| 11 | Off-scene social line | `_build_offscene_target_gm_output` |
| 12 | Pending check prompt | `_build_check_prompt_gm_output` |
| 13 | Unparsed adjudication | `resolve_adjudication_query` |
| 14 | Freeform narration | `attach_interaction_obligation` then GPT |

`/api/action` does not re-segment free text. It trusts `action_type` (`roll_initiative`, `attack`, `skill_check`, `cast_spell`, `end_turn`, `exploration`, `social`), resolves, then uses the same pipeline except initiative, the no-enemy end-turn line, off-scene social, and a pending check, which emit without a contract.

HTTP session administration (`/api/snapshots`, load, reset, new campaign, clear log, response mode, import, and the campaign/scene/character/world editors) never interprets a gameplay sentence.

Every chat turn also calls `advance_world_tick` and saves the world before any contract. That clock is not a reading of the sentence.

### 7. Route table

`Before` means the route interprets raw language or emits before `construct_resolution_contract`. `Suppress` means it can finish the turn with no contract. Protection columns are for the path as it exists today.

| Route | Module / entry | Trigger | Before | Suppress | Creates | Consumes | Emit | Mutate state | Mutate discourse | C18 | C19 | C20/C21 | C22 | Class | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Campaign-start cue | `api._is_campaign_start_turn_request` | "start the campaign" on an empty log | YES | NO | YES, in the pipeline | NO | via pipeline | opening flags after attach | NO | NO, opening excluded | PARTIAL | NO | NO | A | low |
| Passive wait | `intent_parser.maybe_build_passive_interruption_wait_action` | wait / watch-for-disturbance, no question | YES | NO | YES, later | NO | via pipeline | after attach | after attach | YES | YES | YES | NO | C | medium |
| Qualified pursuit | `parse_exploration_intent` | follow/pursue the lead | YES | NO | YES, later | NO | via pipeline | after attach | after attach | YES | YES | PARTIAL | PARTIAL, travel text is pre-gated | C | medium |
| World-action recovery | `recover_actionable_explicit_world_action` | inspect, use, open, read, take | YES | NO | YES, later | NO | via pipeline | after attach | after attach | YES | YES | PARTIAL | PARTIAL, object actions use `committed_world_text` | C | high |
| Social parser | `social.parse_social_intent` | ask / tell / addressed speech | YES | NO | YES, later | NO | via pipeline | after attach | after attach | YES | YES | PARTIAL, target chosen first | NO | C | high |
| Dialogue-first | `interaction_routing._build_dialogue_first_action` | social entry or dialogue route | YES | NO | YES, later | NO | via pipeline | after attach | after attach | YES | YES | PARTIAL | NO | C | high |
| Exploration parser | `parse_exploration_intent` | look, go, search | YES | NO | YES, later | NO | via pipeline | after attach | after attach | YES | YES | PARTIAL | PARTIAL | C | high |
| Generic intent | `intent_parser.parse_intent` | residual verb patterns | YES | NO | YES, later | NO | via pipeline | after attach | after attach | YES | YES | PARTIAL | NO | C | medium |
| Travel override | `maybe_build_declared_travel_action` | declared movement, authored exit | YES | NO | YES, later | NO | via pipeline | location after attach | can break social | YES | YES | PARTIAL | PARTIAL, `committed_world_text` only | C | high |
| In-chat attack | `resolve_attack` | attack verb while `in_combat` | YES | NO, unless the early error return | YES, later | NO | via pipeline | YES, `save_combat` before attach | can break social | YES if pipeline runs | PARTIAL | NO | NO | C | medium |
| Off-scene social | `_build_offscene_target_gm_output` | social target not in scene | YES | YES | NO | NO | YES | NO | NO | NO | NO | NO | NO | B | high |
| Pending check | `_build_check_prompt_gm_output` | `requires_check` without a roll | YES | YES | NO | NO | YES | NO | NO | NO | NO | NO | NO | C | medium |
| Earshot / nearby | `adjudication.classify_adjudication_query` then roster | `nearby`, earshot, who is here, on the unparsed arm | YES | YES | NO | NO | YES | NO in the resolver; emission can still speak | does not write the runner | NO | NO | NO | NO | B | high |
| Place existence | same classifier, place-locality arm | is there a place nearby | YES | YES | NO | NO | YES | NO | NO | NO | NO | NO | NO | C | medium |
| Roll requirement | same classifier | roll / DC / skill check | YES | YES | NO | NO | YES | NO | NO | NO | NO | NO | NO | C | low |
| Feasibility | same classifier, `could I` / `can I` | feasibility opener when `nearby` did not already match | YES | YES | NO | NO | YES | NO | NO | NO | NO | NO | NO | B | high |
| State query | same classifier | what actions, how many, where is my | YES | YES | NO | NO | YES | NO | NO | NO | NO | NO | NO | B | medium |
| Initiative line | `api.action` `roll_initiative` | typed action | n/a, not a sentence | YES | NO | NO | YES | combat | NO | NO | NO | NO | NO | A | low |
| End-turn line | `api.action` `end_turn` with no enemy | typed action | n/a | YES | NO | NO | YES | combat | NO | NO | NO | NO | NO | A | low |
| Typed action resolvers | `api.action` attack, skill, spell, exploration, social | client `action_type` | YES for any free `intent` string | NO, except off-scene and check | YES, in the pipeline | NO | via pipeline | combat flags before attach | after attach | YES if pipeline runs | PARTIAL | PARTIAL | PARTIAL | C | medium |
| Session administration | snapshot, reset, editors, scene activate | HTTP, not `/api/chat` | n/a | YES | NO | NO | NO fiction | YES, by design | can wipe | NO | NO | NO | NO | A | low |
| Freeform narration | `attach_interaction_obligation` then GPT | unparsed and not adjudication | NO | NO | YES, before generation | YES | via C18 when the contract has an operation | after attach | after attach | YES | YES | YES | YES | contract path | — |

The freeform row is the only ordinary chat arm that establishes the contract before generation. It is not a bypass. It is listed so the boundary is visible.

### 8. Category A / B / C

**A — legitimate pre-contract. 4.**

- Session administration. A snapshot load is not a player intention about the fiction. The contract would not say what the click meant. C18–C22 are gameplay seals. The safety invariant is the existing storage and UI-mode policy, not a resolution owner.
- Initiative and end-turn status lines. The client already named the operation. The sentence is a table status. Forcing it through C18 would only wrap a fixed string.
- Campaign-start cue. The phrase is an explicit system request on an empty log. The pipeline still builds a contract afterwards, and C18 already excludes `scene_opening`. Bypassing the gameplay seals is safe because the turn is not an in-fiction commitment. The opening curator remains the content invariant.

Deterministic is not enough to put a route in A. Earshot, feasibility, and travel are deterministic and are not in A.

**B — ordinary gameplay that must establish a contract first. 4.**

- Earshot / nearby on the unparsed arm. This is the C22 turn. The player was still talking to the runner. The contract should have recorded an ask, or a presence question, before any roster lookup.
- Feasibility (`can I` / `could I` find supplies). That is a request about the fiction, not a system command.
- State query (`who is here`, `what actions are available`) when it is played as a sentence rather than a UI button.
- Off-scene social direct text. It answers a person-directed request with no contract and no acceptance seal.

**C — specialized resolvers that should sit below the contract. 13.**

Passive wait, pursuit, world-action recovery, social parser, dialogue-first, exploration parser, generic intent, travel override, in-chat attack, pending check, place-existence lookup, roll-requirement lookup, and the typed `/api/action` resolvers.

For the C22 kernel, the contract fields the roster resolver needs are operation `inquire` or `perceive`, dimension `presence` (or an equivalent local-entities dimension), target `local scene`, addressee empty, commitment `executed_now`. Inputs are the scene id and the addressable roster. Output is a list of present names or a nonresolution. It may not choose a speaker, write discourse, or emit. Emission stays on the accept path. Place existence needs operation `inquire`, dimension `place`, target the named place. Roll requirement needs operation `rules_query` and must pass C19 as an authoritative rule. Travel needs operation `act`, target the destination, commitment `executed_now`, and only then the authored-exit matcher. Inspection needs operation `inspect` and the object id. Social resolution needs operation `ask` (or the specific social act), addressee, and commitment. A check prompt needs the contract to say a roll is required, then the prompt is the resolver output, still sealed.

### 9. Semantic resolution-owner map

Eight systems can answer "what did the player mean?" on one chat turn:

1. Clause segmentation (`segment_mixed_player_turn`).
2. Directed social entry (`resolve_directed_social_entry`).
3. Social parser (`parse_social_intent`) and dialogue-first.
4. Exploration and world-action recovery.
5. Generic `parse_intent`.
6. Travel / authored-exit matcher.
7. Adjudication classifier (`classify_adjudication_query`).
8. Resolution Contract, only if arm 13 failed and arm 14 ran, or if a parser entered the pipeline.

Precedence is first successful parser, then adjudication, then freeform-plus-contract. There is no arbitration when they disagree. The first success returns. The contract, when it is built inside the pipeline, records the winner's action. It does not re-decide the utterance. Q1 shows the disagreement: the earshot classifier says `perception_query` for "Who is nearby?", and the social parser wins with operation `ask`.

### 10. Trigger-collision analysis

Six mechanisms steal or pre-empt ownership. They are not a blacklist. Each one currently selects meaning. After a contract exists, the same words should only select a resolver.

| Mechanism | Where | What it does today | What it should do |
| --- | --- | --- | --- |
| Adjudication tokens `could`, `can`, `would`, `is`, `are`, `roll`, `check`, `need` | `_looks_like_adjudication_question` | Pull the last question out of the social text | Mark a candidate clause. Do not delete it from ownership |
| `nearby`, earshot, who is here, in range, how far | `classify_adjudication_query` | If the unparsed arm runs, the turn is a roster query | Select the presence resolver only when the contract's dimension is presence |
| Scene-presence regex | `resolve_directed_social_entry` | Blocks social for earshot / who-is-here. Does not contain `nearby` | Same rule, applied to the contract, not to a substring |
| Listen / hear / see / spot | observation extraction and `_dimensions` | Can own the turn as perception | Already partly repaired inside the contract for supporting perception. The unparsed arm never gets there |
| Follow / leave / go plus a destination slug | authored-exit match on `committed_world_text` | Can own travel | Resolver for an `act` contract whose commitment is executed now |
| Ask / approach / speak plus a roster name | social entry and `parse_social_intent` | Can own the turn as talk | Resolver for an `ask` contract |

`nearby` inside "supplies nearby" is the collision that hit C22. The social-presence blocker does not use that word. The adjudication classifier does, and it runs before the feasibility test.

### 11. Multi-clause analysis

Confirmed. One trigger can capture the turn.

`_extract_inline_adjudication_clause` takes the last question that contains an adjudication token and removes it from the working text. Earlier questions stay in `declared_action_text` only if they were not the extracted clause. The social merger then ignores the extracted clause. If the declared remainder produces no parser action, the fallback adjudicates only the extracted clause.

On the exact C22 sentence the social question "Have you heard…?" is discarded from the resolver input. The supplies question is the entire adjudication. The established interlocutor is not read. A short "Who is nearby?" is not split away from a social clause, a parser accepts it, and the contract is built. The defect is the combination of a trailing token-clause and parser abstention, not the mere presence of the word.

### 12. Discourse ownership

| Route that skips the contract | Reads active interlocutor | Writes it | Effect on the C22 turn |
| --- | --- | --- | --- |
| Social entry, before the skip | Yes, for follow-up | No | Returned `no_addressable_target`. The runner was not selected |
| Adjudication roster | Reads `active_interaction_target_id` only to omit that name from the roster | No | Did not continue the runner |
| Anti-reset replacement | Reads exchange-established session | No | Replaced the roster with a guard line |
| Pipeline paths | Yes, inside the contract and discourse focus | Yes, after attach | Not entered |

The bypass explains a response that behaves as if the conversational partner were gone. The live turn did not write a new interlocutor and did not keep the runner. The visible speaker is the fallback default, not a bound NPC. Inspected-object and claim loss are not what this particular turn did. Those slots are updated from the contract, which was absent, so they were simply not touched.

### 13. C18 ownership

`lifecycle_applies` is false when the resolution has no contract operation, and it is false for `scene_opening` on purpose.

Gameplay-visible routes that can emit with no `accepted_response`:

- Unparsed adjudication. Proven on the C22 turn and on the stubbed replay. Provenance is the earshot template, then `anti_reset_continuation_fallback`. No hard validation of a generated candidate. The mutation risk is the speaker substitution. C18 should own this once it is an ordinary gameplay answer.
- Off-scene social line. Engine text, no seal.
- Pending check prompt. Engine text, no seal. A check prompt can stay a resolver result, but it should still be the accepted text of a contract that required the roll.

Initiative, end-turn, and session administration should not be forced through C18.

### 14. C19 authority

The earshot sentence is a player-visible fact about who is present. It is produced from scene state and never passes C19 authority classification. The later guard sentence is also player-visible and is not an authority classification. It is a catalog fallback. Place-existence and roll-requirement sentences on the same arm are likewise outside C19. Off-scene and check prompts are outside C19.

Pipeline turns that build a contract do go through hard validation, including C19, when the lifecycle applies.

### 15. C20 / C21 entity ownership

The C22 bypass did not instantiate an incidental person and did not bind the runner. It also did not use the C20/C21 canonical binding to choose the speaker. `speaker_label` defaulted to "The guard" because the adjudication resolution has no `social.npc_id`.

Social, dialogue-first, and travel parsers choose targets before the contract exists. When they then enter the pipeline, `apply_entity_binding` runs inside `attach_interaction_obligation`. The choice is earlier than the architecture that is supposed to own it. The skip paths never reach that call.

No code was changed. This is an inventory.

### 16. C22 commitment ownership

C22 is not universal. `committed_world_text` is consulted by the travel and object parsers and again inside `construct_resolution_contract`. It is not consulted by adjudication, off-scene emission, or the check prompt.

A conditional "nearby" question therefore cannot be saved by the C22 modality work, because those functions never run. Authored travel that does go through `maybe_build_declared_travel_action` remains gated by committed text even though that gate is before the contract. That is a resolver-level protection, not proof that every route honors commitment.

### 17. Historical failure reclassification

Reviewed player-visible failures only. No model replay.

| Case | Class |
| --- | --- |
| 4×10 B2 speaker pattern, contract ask was correct | CONTRACT-CORRECT / DOWNSTREAM |
| 4×10 B9 pre-seal catalog grimace, contract present | CONTRACT-CORRECT / DOWNSTREAM |
| 4×10 C8 look became ask | CONTRACT-CONSTRUCTION |
| 4×10 C10 wear dimension | CONTRACT-CONSTRUCTION |
| 4×10 D1 correct inspect, invented office passed validation | CONTRACT-CORRECT / DOWNSTREAM |
| 4×10 D3 wear dimension plus a non-person span | CONTRACT-CONSTRUCTION |
| 4×10 D7 incorrect contract, evasive figure | CONTRACT-CONSTRUCTION |
| 4×10 D8 incorrect contract, same figure | CONTRACT-CONSTRUCTION |
| C20 smoke turn 8, JSON document was the accepted text | UNRELATED |
| C20 smoke turn 9, questions parked in `adjudication_question_text`, contract kept the leading clause | MIXED |
| C21c live turn 1, listen owned a social ask, contract present | CONTRACT-CONSTRUCTION |
| C21c live turn 3, unresolved serjeant answered by the captain, contract present | CONTRACT-CONSTRUCTION |
| C22 live turn 4 | PRE-CONTRACT BYPASS |

C21's focused live session was 6/6 and is not in the failure list. C21b's live record did not add a separate absent-contract failure. Gate session logs under `artifacts/pr_br_full_gate/20261002T021950Z` and the C21 live logs do not contain another `adjudication_query` row. The scanner's only absent-contract gameplay row is C22 turn 4, counted twice because the session log and `turns.json` both store it.

### 18. Historical impact metrics

```
historical failures reviewed:                      13
confirmed pre-contract bypass failures:             1
probable pre-contract bypass failures:              1
unrelated:                                          1
insufficient evidence:                              0
```

The probable case is C20 smoke turn 9. A contract existed, so it is not a confirmed absence. The same splitter removed the questions from what the contract was allowed to own.

The absent-contract route has so far one confirmed player-visible failure. The ownership problem is wider than that turn. Eight peers can still decide meaning, and the contract is attached only after one of them wins, or not at all. The same splitter appears in C20 and C22. That is a recurring mechanism across validation cycles, not a one-word defect in the nearby regex.

### 19. Static and test-only bypass detection

A deterministic invariant is feasible and is now a test, not a production check:

For the unparsed adjudication arm in `game/api.py`, `attach_interaction_obligation` does not appear between `if adjudication is not None` and the freeform arm.

The companion test posts the twelve probes plus the exact C22 sentence with `ASHEN_DISABLE_LIVE_INTERPRETATION=1` and with `call_gpt` replaced by a stub that cannot open a client. Interpretation invocations observed: 0. The test fails if the interpretation client is called.

A future production invariant, not implemented: every ordinary `/api/chat` gameplay turn either has a Resolution Contract before specialized resolution, or the route is an enumerated Category A command.

### 20. Q1–Q12 route probes

Each probe used a fresh frontier-gate session. Interpretation calls: 0. `call_gpt` was a stub. Stub invocations are not model calls. Results: `artifacts/pr_br_continuation23/q_probes.json`.

| Id | Input | Classifier on that text | Chat owner | Contract | Operation | Emission |
| --- | --- | --- | --- | --- | --- | --- |
| Q1 | Who is nearby? | perception_query | social question, reason no_addressable_target | YES | ask | stub, sealed |
| Q2 | Can I find supplies nearby? | perception_query | social question, reason gm_feasibility | YES | ask | stub, sealed |
| Q3 | I ask the runner if there are supplies nearby. | none | social, declared actor switch | YES | ask, tavern_runner | stub, sealed |
| Q4 | I listen at the door. | none | observe | YES | perceive / sound | safe perception line, sealed, stub used twice |
| Q5 | I ask the guard and listen carefully. | none | observe action, contract ask | YES | ask, guard_captain | stub, sealed |
| Q6 | I inspect the footprints. | none | investigate | YES | inspect | stub, sealed |
| Q7 | I follow the road to the milestone. | none | interact | YES | act | stub, sealed, scene stayed frontier_gate |
| Q8 | Would the road lead to the milestone? | action_feasibility_query | social question | YES | ask | stub, sealed |
| Q9 | I use the key on the door. | none | freeform / contract | YES | perceive / use | safe perception line, sealed |
| Q10 | What does the notice say? | none | social question | YES | ask, dimension content | stub, sealed |
| Q11 | I ask the tavern runner what he heard about the patrol. | none | social, declared actor switch | YES | ask, tavern_runner | stub, sealed |
| Q12 | ((ooc)) what should I roll? | none | freeform / contract | YES | ask | stub, sealed |

Q1–Q12 all created a contract. None of them took the earshot arm. The classifier would have, for Q1, Q2, and the C22 clause, if the parsers had abstained. Q12 shows that an OOC marker in chat is not a Category A bypass. It still builds an ask contract and narrates. Real Category A handling is the separate HTTP commands, not this sentence.

Extra probes, same harness:

- Exact C22 wording, fresh session: contract NO, kind `adjudication_query`, stub calls 0, roster sentence emitted.
- Exact C22 wording after Q11: contract NO, route `procedural_perception_query`, guard line, no `accepted_response`.

Q7 did not change scenes. "to the milestone" did not match the authored old-milestone exit under this seed. That is a resolver result under a contract, not a bypass.

Q9's contract says perceive/use for "I use the key". That is a contract-construction miss on a path that did build a contract. It is out of scope for this cycle's repair.

### 21. Architectural options

**Option 1 — patch precedence.** Make social ask beat `nearby`. Immediate benefit: this one sentence would reach the runner. The next token (`could`, `listen`, `follow`, `use`) can take the same unparsed arm. The twelve short probes already show the social parser beating the classifier by accident of order. Precedence patches will keep colliding. Not recommended.

**Option 2 — contract first for every ordinary turn.** Language, then interpretation, then contract, then resolver. This matches the failure. It also moves every parser. Migration cost is the whole chat chain. Deterministic resolvers can be reused. Latency is a contract build, not automatically a model call, because the fast path already exists. The risk is doing all of that in one cycle.

**Option 3 — hybrid, the C10/C11 boundary extended.** A deterministic fast path may build the contract when the utterance is canonical and unambiguous. Otherwise the structured interpreter proposes and the existing validator accepts or rejects. Specialized resolvers then consume the contract. The freeform arm already does the second half. The unparsed adjudication arm and the peer parsers do not. This is the natural extension. Recommended.

**Option 4 — keep peer semantic owners and arbitrate.** The repository already is this design. Eight owners, first-success precedence, no disagreement handling. Q1's classifier and parser disagree today. Test burden grows with every new token. Not recommended.

### 22. Recommended architecture

```
raw player language
    -> deterministic fast path, or one structured interpretation if it abstains
    -> authoritative Resolution Contract
    -> specialized resolver
    -> hard validation / authority
    -> accept
    -> commit
    -> emit the accepted text
```

Earshot, authored travel, inspection, mechanics, scene lookup, and deterministic adjudication become ways to satisfy a contract. They stop being competing readers of the raw sentence.

### 23. Model and API cost

The 4×10 gate at `20261002T021950Z` recorded 15 interpretation calls across 40 gameplay turns (persona A 2, B 4, C 6, D 3). The other turns used the deterministic fast path inside `construct_resolution_contract`. C22's four live turns used 0 interpretation calls. Three of them generated. Turn 4 generated nothing because it never reached the contract.

Contract-first does not add an interpretation call on turns that already build a contract. Those turns already pay the fast path or the one abstention call. The bypassed turn currently pays neither. Putting it on the contract path adds a fast-path build, and an interpretation call only when that fast path abstains. If the contract is a social ask, the turn also regains the gameplay generation call the bypass skipped. That is the call ordinary turns already make. It is not a new call on every turn.

No large mandatory per-turn model-call increase.

### 24. Latency

The added stage on the bypassed arm is one in-process contract build and a roster or nonresolution lookup the engine already performs. No extra state store. Model latency appears only on fast-path abstention, which is the same rule as today. Do not add a routing layer beyond that.

### 25. Migration boundary

Next cycle should change the unparsed arm in `game.api.chat` and the way `resolve_adjudication_query` is selected. It should not rewrite C18, C19, C20, C21, or C22.

Stay internally intact, and become callers:

- `resolve_adjudication_query` roster, place, roll, feasibility, and state arms
- authored-exit matching
- inspection and object resolution
- social resolution
- check-prompt text

Disappear as raw-language owners on the unparsed arm:

- the direct jump from a token to `_build_adjudication_gm_output`
- the anti-reset replacement of that output by a guard line when no contract exists

Legacy concern: tests that expect "Who is nearby?" to emit the roster sentence must start expecting a presence contract first. Tests that expect the C22 sentence to stay with the runner must expect an ask contract. `tests/test_pr_br_continuation23_precontract_routes.py` is the new witness and should be updated when the arm changes, not before.

Do not move every parser in that same cycle. The peer parsers still build a contract today, after they choose. Reordering them under the contract is the following cycle, once the skip path is closed. Leaving them in place for one cycle does not preserve the bug, because the bug is the skip.

### 26. Proposed invariants

Checked against the repository. All ten are currently false for at least one ordinary path, except V4, which is true only if Category A stays an explicit list.

- V1. One semantic owner per ordinary gameplay turn. False today. Eight peers.
- V2. Contract before specialized semantic resolution. False for adjudication, off-scene, and check prompts. False in spirit for parsers that resolve first and attach second.
- V3. Resolvers consume the contract and do not reread raw language. False for adjudication and travel matchers.
- V4. Category A bypasses are explicit and enumerable. Feasible. The four A rows above are the list.
- V5. No ordinary gameplay emit outside C18. False for adjudication, off-scene, and check prompts.
- V6. No factual gameplay content outside C19. False for the earshot roster.
- V7. No NPC selection outside C20/C21. False for the guard default on this path.
- V8. No uncommitted action outside C22. True for travel that uses `committed_world_text`. False as a universal claim, because the skip paths never consult it.
- V9. Resolver failure returns to contract-aware nonresolution. False. Anti-reset substitutes an unrelated speaker.
- V10. Trigger words select resolver capabilities only after ownership. False. `could` and `nearby` select the route.

### 27. Implementation risks

- Building the contract from the full utterance may still classify the C22 sentence as perception if the fast path keeps today's nearby rule. The fast path must represent the social ask as primary. That is existing C22 behavior, and it only helps if the contract is actually built.
- A presence contract for "Who is nearby?" must not be implemented as another token exception. The operation and dimension have to come from the fast path or the interpreter.
- Emission tests that golden the guard line or the raw roster line will fail when the seal starts owning the text. That is the intended break.
- Moving only the unparsed arm leaves parser-first ownership in place for inspect, travel, and ask. Those paths already seal. They are the next cycle, not a reason to block this one.
- Do not let the anti-reset guard treat a contract-backed answer as an intro fallback.

### 28. Exact recommended next implementation cycle

PR-BR Continuation 24 — close the unparsed skip.

1. On the unparsed chat arm, build the Resolution Contract from the full player text with the existing fast path, and with one interpretation call only on abstention.
2. Select earshot, place, roll, feasibility, or state resolution only from contract fields.
3. If the contract is an ask, do not call the roster resolver because a later clause contains "nearby".
4. Emit only through the existing accept path. Do not replace a contract-less roster sentence with `speaker_label`'s default guard.
5. Leave C18–C22 internals, the nearby regex, and the other parsers alone in that cycle.
6. No 4×10 gate and no human playtest in that cycle either, until the deterministic probes show the exact C22 sentence has a contract and does not speak as the guard.

### 29. Readiness decision

PRE-CONTRACT ROUTING IS A SYSTEMIC ARCHITECTURAL OWNERSHIP PROBLEM — CONTRACT-FIRST / RESOLVER-BELOW-CONTRACT IMPLEMENTATION RECOMMENDED.

The confirmed player-visible failure is one route. The route exists because ownership is a race among peers, and the contract is not in the race until a parser has already won or the freeform arm is reached. A precedence patch would move one token. The evidence from Q1, from the splitter, and from the eight owners supports putting the contract first and the resolvers underneath. Option 3 is the shape. Continuation 24 is only the skip-path slice.

### 30. PR-BR status

PR-BR: STILL OPEN.

No completion commit. No push. No PR-BS. The second 4×10 gate is not authorized. Human playtest is not authorized. Production behavior was not modified. Model calls during this discovery: 0 gameplay generation, 0 interpretation, 0 evaluator, 0 synthetic player.

## PR-BR Continuation 24 — Contract-First Unparsed Resolution

Bounded implementation. The unparsed adjudication arm now builds the existing Resolution Contract from the full player utterance before any specialized resolver runs. Peer parsers were not rewritten. This is not a full contract-first reconciliation.

### 1. Purpose

Close the demonstrated hole where ordinary gameplay reached adjudication and emission with no Resolution Contract.

### 2. Authorization basis

C23 showed the C22 live failure was a contract bypass. The trailing clause containing "could" and "nearby" was adjudicated as earshot. No contract, no C18 seal, no C22 addressee check. Anti-reset then spoke as "The guard".

### 3. C23 architectural boundary

C24 changes only the unparsed arm in `game.api.chat`. Social, exploration, travel, generic intent, world-action recovery, and dialogue-first still choose meaning and then attach a contract. Off-scene social text and pending check prompts still emit without a contract. Those remain for a possible C25.

### 4. Exact C22 failure replay

Captured before the production edit: `artifacts/pr_br_continuation24/c22_failure_replay_before.json`.

Raw utterance: the nod, the thanks, "Have you heard anything about who or what might be causing trouble there?", then "Any chance I could find shelter or supplies nearby before investigating further?"

Segmentation stored the social question in `declared_action_text` and the supplies question in `adjudication_question_text`. Social entry reason `no_addressable_target`. Classifier on the extracted clause: `perception_query`. Kind `adjudication_query`. Route `procedural_perception_query`. Contract absent. Visible text: The guard says, "I do not know enough to answer that." Accepted false. Tags included `final_emission_gate:anti_reset_continuation_fallback`.

The first point where `contract == None` was accepted was the unparsed branch: `parsed is None` and `resolve_adjudication_query` on the extracted clause returned a result, and the turn emitted without `attach_interaction_obligation`.

### 5. Ordinary gameplay / Category A

Named exclusions in `game.contract_adjudication_bridge.CATEGORY_A_EXCLUSIONS`:

- `session_administration` — HTTP snapshot, load, reset, editors. Not `/api/chat`.
- `initiative_status_line` — typed `roll_initiative`.
- `end_turn_status_line` — typed `end_turn` with no enemy.
- `campaign_start_cue` — `_is_campaign_start_turn_request`.

Natural-language questions, social talk, exploration, movement, perception, mechanics, and world interaction are ordinary gameplay even when a deterministic handler exists. An OOC sentence inside chat is not Category A.

### 6. Implementation architecture

`game/contract_adjudication_bridge.py` selects a resolver from the existing contract. `game/api.py` on the unparsed arm:

1. `attach_interaction_obligation` on the full `req.text`, deterministic fast path first.
2. `select_resolver_family`.
3. If a family is selected, `resolve_adjudication_query(..., resolver_family=family)` using the contract's recorded utterance.
4. `run_preserve_if_valid` with no regeneration. Failure becomes the existing contract-aware nonresolution.
5. If no family is selected, the existing freeform generation path runs. A model interpretation call happens only when that path's fast path abstained and the existing policy says a model proposal is appropriate.

No second contract type. Adjudication does not overwrite `operation` or `interlocutor_id`.

### 7. Full-utterance contract construction

The contract is built from `req.text`, not from `adjudication_question_text`. The existing constructor still stores up to its current raw-input limit. The social opening of the C22 sentence is inside that text, so the trailing supplies clause is not the only input.

### 8. Discourse preservation

Construction receives session, scene, world, and visible turns. A follow-up that says "have you heard" inherits the active interlocutor under existing C22 rules. The repaired C22 replay keeps operation `ask` and does not speak as the guard.

### 9. Resolver selection

Families, using repository names: `earshot`, `nearby_presence`, `place_location`, `feasibility`, `state_query`, `roll_mechanical`, `generic_adjudication`.

Selection uses operation, commitment, and the utterance stored on the contract. Bare "nearby" is not a family. An explicit ask ("I ask", "have you heard", "thank you") blocks presence, place, and feasibility. Roll and state questions can still be answered without replacing the addressee.

### 10. "Nearby" contrast

- "Who is nearby?" → `nearby_presence`.
- "Can I find supplies nearby?" → `place_location`, not earshot.
- "I ask the runner if there are supplies nearby." → no specialized family. Operation stays ask.
- "Is there shelter nearby?" → `place_location`.
- "I listen for anyone nearby." → perceive / sound, family `earshot`.

### 11. Resolver failure

`resolve_selected_family` returns None when there is no contract, or when the family would contradict an explicit social ask. The caller then uses generation or the existing safe nonresolution. Operation, target, and addressee on the contract are not reset.

### 12. Generic-speaker fallback

`local_exchange_continuation_fallback_line` no longer calls `minimal_social_emergency_fallback_line` for `adjudication_query`. That catalog's empty speaker is "The guard". Anti-reset still replaces opener-like text during a real social exchange. It does not invent a guard for a procedural answer.

### 13. C18

A resolver result is passed through `run_preserve_if_valid` before persistence. `restore_accepted_text` still runs in the emission finalizer. The repaired C22 path and the live turns have accepted text equal to emitted text.

### 14. C19

Validation is the existing `validate_generated_response`, including proposition authority. The authority check was not loosened.

### 15. C20 / C21

The roster resolver reads the existing scene roster. It does not create people. The place resolver does not manufacture NPCs from the word "nearby". Entity binding remains inside `attach_interaction_obligation`.

### 16. C22

Uncommitted act/follow is not given an executing resolver. "If the guard refuses, I'll look for shelter nearby." selects no family and does not change scene. An explicit ask keeps its addressee; a contradicting earshot call is refused.

### 17. Model-call economy

The unparsed arm builds the deterministic contract first. Interpretation runs only on the generation path when the fast path abstained and model interpretation is already appropriate. Live session: 4 deterministic contracts, 0 interpretation calls, 4 gameplay generations, 0 retries.

### 18. P1–P8

P1, the exact C22 sentence after asking the tavern runner: contract present, operation ask, no earshot roster, no guard line, accepted equals emitted. PASS.

P2–P8: 7/7 in `tests/test_pr_br_continuation24_contract_first_unparsed.py`.

### 19. Adjudication-family matrix

PASS. Earshot, nearby presence, place/location, feasibility, state query, and roll each require a contract id before `resolve_selected_family`. Generic adjudication runs only when that family is passed explicitly, and it still requires a contract. The selector does not assign generic from "nearby".

### 20. No-contract invariant

`resolve_selected_family` returns None without `contract_id` and `operation`. The static test requires `attach_interaction_obligation(` before `select_resolver_family(` in the unparsed arm. Category A ids are the four names above.

### 21. S1–S8

8/8. Compound turns keep a contract. None emitted an earshot roster or the generic guard line. An adjudication family, when one ran, was not earshot.

### 22–26. C18–C22 regression

`tests/test_pr_br_continuation18_immutable_boundary.py` through `tests/test_pr_br_continuation22_commitment.py`: PASS.

### 27. C23 repaired-scope invariant

`tests/test_pr_br_continuation23_precontract_routes.py`: PASS. The old assertion that the C22 sentence has no contract now expects a contract and forbids the guard line and the earshot roster.

### 28. Broader PR-BR regression

Continuation 18–24 modules: PASS. Pipeline adjudication tests for roll, earshot, OOC roll, and covert concealment: PASS.

`tests/test_nearby_place_existence_knowledge_ownership.py` has three failures that do not enter the new arm (`contract_before_resolver` is absent; kind is `question` or the check never chats):

- "Who is nearby?" and "Night Porter, is there a tavern nearby?" are owned by the existing social/question parser, then generation. That parser-first path is unchanged by design.
- `test_question_rule_does_not_rewrite_resolved_place_existence` fails with the C24 files restored to the pre-edit tree as well. It is pre-existing.

Local-presence "What's nearby?" remains an observe parse. It does not enter the unparsed arm.

### 29. Fresh live transcript

`artifacts/pr_br_continuation24/live/20261003T123908Z/visible.md`. Four turns. Notice board, silent threadbare figure, tavern runner on the patrol, follow-up to the same runner.

### 30. Live contract / resolver telemetry

`turns.json` and `summary.json` in that session. Every turn has a contract. Construction source deterministic on all four. No specialized resolver ran, because the parser-owned asks and the inspection never reached the unparsed arm. No resolver ran before a contract.

### 31. Live state / discourse

Turn 1 inspects the notice board. Turns 3 and 4 bind `tavern_runner`. Turn 4 does not drop the runner when the player also looks toward the footprints. No scene transition. No uncommitted travel.

### 32. Manual review

4/4 PASS. See `MANUAL_REVIEW.md`.

### 33. API / model cost

Opening generation 1. Gameplay initial generation 4. Gameplay retry 0. Interpretation 0. Player-model calls 4 (`gpt-4.1-mini`). Evaluator 0. Repair/rerun: no.

### 34. Remaining parser-first owners

Unchanged: segmentation, directed social entry, social parser, dialogue-first, exploration, world-action recovery, generic intent, declared travel, in-chat attack. Still contract-less: off-scene social text, pending check prompt, and the four Category A commands.

### 35. Implementation-scope post-check

C24 closed only the total unparsed/adjudication contract bypass. Peer parser modules were not edited. The adjudication classifier function still classifies raw text for direct callers. The chat arm no longer lets that classification own the turn before a contract exists.

### 36. Residual defects

- Off-scene social lines and pending check prompts can still emit without a contract.
- Parsers still choose meaning before the contract is attached.
- "Who is nearby?" on the kiln fixture is still a parser-owned question, so a stubbed model sentence can appear there. That is outside this cycle's arm.
- The pre-existing question-resolution exemption test remains red.
- Turn 2's silent figure is a thin social answer. The ask was not handed to another speaker.

### 37. Readiness decision

C24 VALIDATED — UNPARSED/ADJUDICATION CONTRACT BYPASS CLOSED; REMAINING PARSER-FIRST OWNERSHIP REQUIRES EXTERNAL REVIEW.

### 38. PR-BR status

PR-BR remains OPEN. No completion commit. No push. No PR-BS. The second 4×10 gate is not authorized. Human playtest is not authorized.

HEAD at implementation: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`.


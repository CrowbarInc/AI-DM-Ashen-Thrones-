# PR-BR Proposition-Level Claim Control — Final Four-Turn Live Validation

Run stamp: `20261004T035044Z`  
Workspace HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`  
Model route: `gpt-4.1-mini`  
Evidence directory: `artifacts/pr_br_final_live_validation/20261004T035044Z/`

Measurement only. Four gameplay turns completed exactly once in one isolated
production `TestClient` session. There were no exploratory gameplay calls,
turn reruns, second scenarios, 4x10 sessions, implementation edits after live
start, commits, or pushes. SHA-256 hashes of `game/` and `prompts/` were
identical before and after the run.

## 1. Executive conclusion

The final live validation failed and reproduced an architectural proposition-
authority defect.

Some repaired mechanisms worked:

- Turn 1 retained the explicit pump subject and was not malformed.
- Turn 2 persisted the player's stronger wording as `player_hypothesis`.
- Repetition did not promote that ledger row.
- Turn 3 recognized a confidence question, bound `active_claim`, and allowed
  “a possibility rather than a certainty” to survive.
- Turn 4 remained fluent and allowed harmless NPC improvisation.
- Sealed and emitted text were exact-equal on 4/4 turns.

The central architecture did not hold:

1. Turn 1 lost the requested `interpretation` dimension and had no `INFER`
   epistemic act.
2. The sealed Turn-1 causal alternatives were emitted but not written to
   `gm_inferences`.
3. Turn 2 misbound the presupposition to a place/unavailable addressee, rejected
   two useful uncertainty answers, and emitted an irrelevant fallback.
4. Turn 3 accepted “sudden, violent pressure seems a likely cause” and its
   claim audit labeled the whole causal sentence `authored_world_fact`,
   `world_truth`, `established`, even though only the bowed handle and sheared
   pin were authored.
5. Turn 3 also emitted a generated lead about recent users and nearby witnesses.
6. `gm_inferences` remained empty after all four turns, and Turn 4's accepted
   mundane NPC details did not enter `accepted_incidentals`.
7. Accepted claim accounting did not fully describe exact emitted text on
   Turns 2 and 3.

This is not merely an awkward response or bounded persistence blemish. An
unauthorized cause shared a sentence with an authorized observation and was
classified as world truth. Temporal provenance existed but did not carry or
govern that accepted inference.

Manual result: **0 PASS / 4 FAIL**.

## 2. Exact initial authoritative state

The byte-exact initial state is
`initial_authoritative_state.json`. Its isolated storage contained:

- Active scene: `bathhouse_pump_alcove`.
- Location: `Dunmere public bathhouse pump alcove`.
- Mode: `social`.
- Consequential authored observation:
  “The bathhouse pump's long iron handle is visibly bowed, and its pivot pin
  is sheared through.”
- Observation semantic identity:
  `kind=world_fact`,
  `subject=bathhouse_pump_handle`,
  `relation=observation`,
  `value=bowed handle and sheared pivot pin`,
  `polarity=positive`.
- Ordinary authored facts:
  “Two folded towels rest on a cedar bench.”
  “A blue-glazed soap dish sits beside the washbasin.”
  “Nessa folds clean towels beside the cedar bench.”
- Authored NPC: Nessa, ordinary bath attendant, available in the scene.
- One mundane NPC topic:
  “Nessa is folding clean towels beside the cedar bench.”
- No discoverable clues, hidden facts, exits, enemies, factions, assets,
  projects, flags, event-log entries, or world clues.
- Session turn counter: 0.
- Empty debug traces and chat history.
- No authored cause, responsible actor, event time, history, explanation, or
  corroborating evidence for the damage.

The exact campaign, character, combat, conditions, world, scene, session, and
empty session log are all included in that JSON file.

## 3. Exact model/API count

| Call class | Exact count |
| --- | ---: |
| Gameplay turns | 4 |
| Initial generation calls | 4 |
| Retry generation calls | 2 |
| Interpretation calls | 0 |
| Preflight calls | 1 |
| Other model calls | 0 |
| **TOTAL model/API calls** | **7** |

Retries occurred on Turns 1 and 2. The single startup preflight was healthy.
No evaluator, synthetic-player, opening-generation, or hidden gameplay call
occurred.

## 4. Four-turn PASS/FAIL table

| Turn | Result | Primary failure mechanism |
| --- | --- | --- |
| 1 | FAIL | Contract omitted `interpretation`; decision omitted `INFER`; emitted qualified causes did not enter `gm_inferences`. |
| 2 | FAIL | Presupposition was misbound to a place/addressee; two uncertainty answers were rejected and replaced by an irrelevant fallback. |
| 3 | FAIL | Accepted audit laundered an unsupported cause into authored `world_truth`; generated witness/recent-user lead survived; ledger remained empty. |
| 4 | FAIL | Harmless improvisation was natural but not committed to `accepted_incidentals`, and the required prior inference remained mistyped. |

## 5. Turn 1 full trace — observation plus inference request — FAIL

1. **Authoritative state before:** Exact initial state described in §2; no
   temporal ledger and no active claim.
2. **Player input:** “I examine the bowed pump handle and the sheared pivot pin
   closely. What does this damage suggest?”
3. **Resolution Contract:** `rc_9c97a3580116`; `inspect`; explicit subject
   `bowed pump handle and the sheared pivot pin`; not ambiguous; expected
   `answer`; but `dimension=null`, `dimensions=[]`, mode `unknown_allowed`.
   The contract was structurally valid but semantically incomplete for the
   requested interpretation.
4. **Interaction Obligation:** `inspection`; resolve authoritative or bounded
   incidental detail. It did not require interpretation.
5. **GMResolutionDecision:** Matching contract id; outcome
   `established_or_retrieved`; authored corpus only; no unresolved qualifier.
6. **Epistemic acts:** Five `ESTABLISH` rows for scene/NPC facts; no `INFER`.
7. **Proposed facts:** Pump observation, towels, soap dish, Nessa folding, and
   Nessa's existence; all authored `world_truth`.
8. **Semantic identity:** Pump observation correctly carried
   `bathhouse_pump_handle / observation / bowed handle and sheared pivot pin`.
9. **Raw initial generation:**  
   “The long iron handle of the bathhouse pump is noticeably bowed, bending
   outward from normal shape, and its pivot pin has been cleanly sheared
   through. This kind of damage suggests great force applied in a way that
   twisted the handle beyond its strength, breaking the pin holding it in
   place. Whether it was excessive wear or a sudden, violent pressure is
   unclear from the current evidence. Nearby, daily work presses on as Nessa
   folds towels quietly by a cedar bench, giving no hint of recent disturbance
   around the pump.”
10. **NarratedClaims:** Observation accepted as authored; explicit great-force
    sentence rejected; alternatives classified unresolved speculation.
11. **Claim-level audit:** Explicit force relation rejected as
    `unauthorized_evidential_relation`; observation and uncertainty accepted.
12. **Residual claims:** “great force ... twisted the handle ... breaking the
    pin” was the rejected consequential evidential residual.
13. **Hard validation:** Initial hard invalid:
    `unauthorized_resolution_decision_fact`.
14. **Retry reason:** Rejected unauthorized decision fact.
15. **Retry context:** Included exact contract, decision, epistemic acts, facts,
    and violating sentence.
16. **Retry generation:** One counted retry returned an empty player-facing
    string with `structured_output_rejected` / malformed envelope.
17. **Preservation candidate:** Bounded sentence preservation selected the
    initial text minus the explicit great-force sentence.
18. **Post-preservation audit:** Hard valid, balanced prose, two accepted
    claim rows; acceptance reason `bounded_sentence_preservation`.
19. **Exact sealed response:**  
    “The long iron handle of the bathhouse pump is noticeably bowed, bending
    outward from normal shape, and its pivot pin has been cleanly sheared
    through. Whether it was excessive wear or a sudden, violent pressure is
    unclear from the current evidence. Nearby, daily work presses on as Nessa
    folds towels quietly by a cedar bench, giving no hint of recent disturbance
    around the pump.”
20. **Exact emitted response:** Exact match to the sealed response.
21. **State after:** Same scene; no cause, actor, event, or world mutation.
22. **Temporal provenance after:** `gm_inferences=[]`,
    `player_hypotheses=[]`, `accepted_incidentals=[]`; one
    `rejected_consequential` row for the explicit great-force sentence.
23. **active_claim after:** The unresolved sentence about excessive wear or
    sudden violent pressure; source `speculation`, status `unresolved`.
24. **Manual result:** FAIL.
25. **Primary failure mechanism:** The player received causal alternatives, but
    contract/decision/ledger did not represent them as qualified inference.
    The last sentence also asserted unsupported negative evidential texture:
    “no hint of recent disturbance.”

## 6. Turn 2 full trace — player presupposition — FAIL

1. **State before:** Turn-1 active unresolved claim; no `gm_inferences`.
2. **Player input:** “So if sudden, violent pressure bent the handle and sheared
   the pin, who could have put that pressure on the pump?”
3. **Resolution Contract:** `rc_aaecd4f6bceb`; `ask`; hypothetical; expected
   `clarification`; target incorrectly canonicalized to the bathhouse place;
   active claim not inherited; proposed span `So` rejected as interlocutor.
4. **Interaction Obligation:** Question; answer, uncertainty, refusal, or
   redirect, but with no bound interlocutor.
5. **GMResolutionDecision:** Matching id; `established_or_retrieved`; actor
   unresolved.
6. **Epistemic acts:** Authored facts established plus
   `LEAVE_UNRESOLVED(actor)`.
7. **Proposed facts:** Authored scene/NPC corpus only.
8. **Semantic identity:** Authored pump observation retained; player statement
   later received hypothesis status identity.
9. **Raw initial generation:**  
   “Nessa shakes their head slowly while folding the towels. "I don't know who
   could have put that kind of pressure on the pump. I've only seen it break
   like this when it's been pushed too hard, but I can't say who did it or
   when." They glance toward the pump handle but offer no further details.”
10. **NarratedClaims:** Two epistemically qualified NPC claims; audit itself
    found no proposition-authority violation.
11. **Claim-level audit:** Hard-valid authority audit, but response-level
    validation rejected `wrong_interlocutor`.
12. **Residual claims:** Initial “I've only seen it break like this” invented
    Nessa's observation history; the proposition audit did not reject it.
13. **Hard validation:** Initial hard invalid solely for `wrong_interlocutor`.
14. **Retry reason:** Preserve bound interlocutor, although contract had none.
15. **Retry context:** Contract target was the place, expected clarification,
    with actor unresolved and full authored facts.
16. **Retry generation:**  
    “"I'm not sure who could have done that," Nessa replies carefully, folding
    the towels. "I don't have any information about who might have forced the
    pump handle like that."”
    It was also rejected `wrong_interlocutor`.
17. **Preservation candidate:** None selected; terminal safe nonresolution used.
18. **Post-preservation audit:** Not applicable. The sealed fallback metadata
    retained claim rows from the rejected retry rather than rows for exact
    fallback text.
19. **Exact sealed response:** “The person you addressed cannot be identified
    clearly enough to answer.”
20. **Exact emitted response:** Exact match to sealed response.
21. **State after:** No cause or actor established; Nessa became the active
    interaction target through social routing.
22. **Temporal provenance after:** Player wording entered
    `player_hypotheses` at source turn 2; no `gm_inferences`; rejected Turn-1
    force sentence remained.
23. **active_claim after:** Exact player hypothesis, source
    `player_hypothesis`, status `hypothesis`.
24. **Manual result:** FAIL.
25. **Primary failure mechanism:** Anti-promotion succeeded, but binding and
    social routing rejected useful answers and produced an irrelevant,
    non-human-GM-like fallback.

## 7. Turn 3 full trace — direct epistemic challenge — FAIL

1. **State before:** Player hypothesis active; no cause/actor in world state;
   `gm_inferences` empty.
2. **Player input:** “Do we actually know that sudden, violent pressure caused
   the damage, or is that only a possibility?”
3. **Resolution Contract:** `rc_d9843346d30f`; `ask`; target the active claim;
   `dimension=confidence`; expected `answer`; claim bound; not ambiguous.
   It also inherited Nessa as interlocutor because Turn 2 had entered social
   routing.
4. **Interaction Obligation:** Follow-up; answer or qualify the established
   claim.
5. **GMResolutionDecision:** Matching id; `epistemically_qualified`;
   `claim_only`; actor unresolved.
6. **Epistemic acts:** Authored facts established plus
   `LEAVE_UNRESOLVED(actor)` with status-answer scope.
7. **Proposed facts:** Authored scene/NPC corpus; no authorized cause, witness,
   recent-user roster, or event history.
8. **Semantic identities:** Pump observation retained; unresolved status
   identity present in decision.
9. **Raw initial generation:**  
   “I can't swear to it, but from what I saw, sudden, violent pressure seems a
   likely cause of the bowed handle and sheared pin. Still, without witnessing
   the event or knowing who might have applied such force, it remains a
   possibility rather than a certainty. If you want to uncover more, checking
   with those who used the pump recently or nearby witnesses could be a good
   next step.”
10. **NarratedClaims:** The accepted decision audit represented only the first
    sentence. It did not create claim rows for the uncertainty sentence or the
    investigative lead.
11. **Claim-level audit:** The first sentence was classified
    `authored_world_fact`, authority `world_truth`, status `established`,
    persistence `world_truth`, source `scene.visible_facts.0`.
12. **Residual claims:** The unauthorized causal relation “pressure ... likely
    cause,” implied Nessa witness stance “from what I saw,” and generated
    recent-user/nearby-witness lead all survived. The audit reported no
    violation.
13. **Hard validation:** Hard valid.
14. **Retry reason:** None.
15. **Retry context:** None.
16. **Retry generation:** None.
17. **Preservation candidate:** None; initial generation accepted.
18. **Post-preservation audit:** Not applicable.
19. **Exact sealed response:** Exact raw initial generation above.
20. **Exact emitted response:** Exact match to sealed response.
21. **State after:** No explicit world-state mutation established actor/cause,
    but accepted claim metadata treated the causal sentence as world truth.
22. **Temporal provenance after:** Still `gm_inferences=[]`; Turn-2
    `player_hypothesis` remained; no new rejected consequential row.
23. **active_claim after:** Still the Turn-2 player hypothesis; source changed
    to `resolution_contract`; no promotion field or GM-inference replacement.
24. **Manual result:** HIGH-SEVERITY FAIL.
25. **Primary failure mechanism:** Authorized observation terms caused the
    whole mixed sentence, including unsupported causal relation, to be
    classified as authored world truth. This is proposition laundering and
    proves live decisions can ignore the intended temporal distinction.

The exact A3 regression condition “correct uncertainty rejected while stronger
unsupported content survives” did not occur literally: uncertainty survived.
The outcome is nevertheless architectural and high severity because stronger
unsupported causal content also survived and was explicitly labeled world
truth.

## 8. Turn 4 full trace — incidental freedom — FAIL

1. **State before:** Observation stable; player hypothesis active; no
   `gm_inferences`; cause/actor unresolved in persisted world state.
2. **Player input:** “I leave the pump mystery there and ask Nessa what scent of
   soap she keeps by the washbasin, and whether she prefers folding the towels
   lengthwise or in thirds.”
3. **Resolution Contract:** `rc_e399b06e5075`; `ask`; Nessa bound;
   `dimension=smell`; expected `answer`; mode `bounded_incidental`.
4. **Interaction Obligation:** Grounded question asking for both requested
   mundane details.
5. **GMResolutionDecision:** Matching id; `epistemically_qualified`;
   `claim_only`.
6. **Epistemic acts:** Authored facts established; no consequential inference.
7. **Proposed facts:** Authored scene/NPC corpus only.
8. **Semantic identities:** Pump observation plus Nessa entity identity.
9. **Raw initial generation:**  
   “Nessa looks up briefly from folding clean towels beside the cedar bench.
   "I use a lavender-scented soap by the washbasin," they say, "and I find
   folding the towels lengthwise easier to keep them neat and ready for use."”
10. **NarratedClaims:** One combined NPC claim for lavender soap and lengthwise
    folding.
11. **Claim-level audit:** Authorized `npc_claim`, `claim_only`, status
    `hearsay`; no violation.
12. **Residual claims:** No consequential mystery residual. The authored Nessa
    action sentence was not represented as a separate claim row.
13. **Hard validation:** Hard valid with soft flag `low_confidence_locate`.
14. **Retry reason:** None.
15. **Retry context:** None.
16. **Retry generation:** None.
17. **Preservation candidate:** None.
18. **Post-preservation audit:** Not applicable.
19. **Exact sealed response:** Exact raw initial generation above.
20. **Exact emitted response:** Exact match to sealed response.
21. **State after:** Authored towel topic marked discovered; ordinary NPC
    stance/topic counters changed; no causal clue, actor, or history added.
22. **Temporal provenance after:** `accepted_incidentals=[]`; earlier
    hypothesis and rejected force sentence unchanged; `gm_inferences=[]`.
23. **active_claim after:** Still the Turn-2 player hypothesis; active
    interlocutor Nessa.
24. **Manual result:** FAIL, despite fluent bounded improvisation.
25. **Primary failure mechanism:** The required prior inference remained
    mistyped, and accepted bounded incidental detail received no
    `accepted_incidentals` provenance. Emission telemetry also called the
    contract semantically `unsatisfied/discourse_state_contradiction` while
    accepting and emitting the response.

## 9. Temporal provenance after each turn

### After Turn 1

| Bucket | Proposition / row | Source turn | Provenance | Authority | Status | Persistence | Later reference | Promotion |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| gm_inferences | **empty** despite emitted wear/pressure alternatives | — | — | — | — | — | Turn 2 reused pressure | Missing, not promoted |
| player_hypotheses | empty | — | — | — | — | — | — | none |
| accepted_incidentals | empty | — | — | — | — | — | — | none |
| rejected_consequential | Great force twisted handle and broke pin | 1 | generated_proposal | unauthorized | unresolved | do not persist as truth | remained through Turn 4 | none |
| active_claim | Wear or sudden violent pressure unclear | 1 | speculation | non-truth | unresolved | discourse focus | challenged on Turns 2–3 | none |

### After Turn 2

| Bucket | Proposition / row | Source turn | Provenance | Authority | Status | Persistence | Later reference | Promotion |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| gm_inferences | empty | — | — | — | — | — | pressure repeated | missing |
| player_hypotheses | Sudden violent pressure bent handle/sheared pin; asks actor | 2 | player_hypothesis | observation | hypothesis | typed temporal row | challenged Turn 3 | **not promoted** |
| accepted_incidentals | empty | — | — | — | — | — | — | none |
| rejected_consequential | Same Turn-1 great-force row | 1 | generated_proposal | unauthorized | unresolved | rejected ledger | none | none |
| active_claim | Exact Turn-2 player formulation | 2 | player_hypothesis | non-truth | hypothesis | discourse focus | bound Turn 3 | not promoted |

### After Turn 3

| Bucket | Proposition / row | Source turn | Provenance | Authority | Status | Persistence | Later reference | Promotion |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| gm_inferences | **empty** despite emitted likely-cause inference | — | — | — | — | — | transcript only | ledger failure |
| player_hypotheses | Same Turn-2 hypothesis | 2 | player_hypothesis | observation | hypothesis | temporal row | remains active | no ledger promotion |
| accepted_incidentals | empty | — | — | — | — | — | — | none |
| rejected_consequential | Same Turn-1 row only | 1 | generated_proposal | unauthorized | unresolved | rejected ledger | — | none |
| active_claim | Same Turn-2 hypothesis | 2/3 | resolution_contract | non-truth in focus | unchanged field | discourse focus | remains after Turn 4 | no explicit promotion |

The ledger did not promote the player row, but the Turn-3 **accepted claim
audit independently classified the matching causal sentence as world truth**.
The critical invariant therefore failed at the live decision/audit boundary.

### After Turn 4

| Bucket | Proposition / row | Source turn | Provenance | Authority | Status | Persistence | Later reference | Promotion |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| gm_inferences | empty | — | — | — | — | — | — | missing |
| player_hypotheses | Same Turn-2 hypothesis | 2 | player_hypothesis | observation | hypothesis | temporal row | still active | no ledger promotion |
| accepted_incidentals | **empty** despite lavender/folding answer | — | — | — | — | — | — | missing |
| rejected_consequential | Same Turn-1 row | 1 | generated_proposal | unauthorized | unresolved | rejected ledger | — | none |
| active_claim | Same Turn-2 hypothesis | 2/3 | resolution_contract | non-truth in focus | unchanged | discourse focus | final | no explicit promotion |

## 10. active_claim evolution

1. Before Turn 1: absent.
2. After Turn 1: qualified alternatives, source `speculation`, status
   `unresolved`.
3. After Turn 2: exact player presupposition, source `player_hypothesis`,
   status `hypothesis`.
4. After Turn 3: same claim id and label, source changed to
   `resolution_contract`; Turn 3 correctly bound it for confidence.
5. After Turn 4: unchanged while active interlocutor became Nessa.

Focus continuity improved relative to the 3/6 run, but it did not prevent the
Turn-3 audit from laundering the proposition.

## 11. Claim-laundering audit

### Turn 1 emitted sentences

1. Pump handle bowed/pin sheared: authored and authorized.
2. Excessive wear or sudden violent pressure remains unclear: qualified
   cause alternatives; safe as uncertainty, but not authorized as an authored
   fact and not persisted as inference.
3. Nessa folds towels and gives “no hint of recent disturbance”: Nessa folding
   is authored; “no hint” adds an unsupported negative evidential/history
   implication. It was typed as an ungrounded `npc_claim` despite narrator form.

### Turn 2 emitted sentence

“The person you addressed cannot be identified”: not a consequential claim,
but it is unresponsive and semantically mismatched because the player asked a
general actor question rather than addressing an unidentified person.

### Turn 3 emitted sentences

1. Sudden violent pressure “seems a likely cause”: unsupported causal
   proposition. It shares a sentence with the authored bowed-handle/sheared-pin
   observation. The audit matched the authorized observation and labeled the
   entire sentence authored `world_truth`. **This is claim laundering.**
2. Possibility rather than certainty: authorized epistemic limit and directly
   responsive; omitted from GMResolutionDecision `claim_results`.
3. Check recent users or nearby witnesses: unsupported existence/history and
   investigative-utility lead; emitted and omitted from claim results.

### Turn 4 emitted sentences

Nessa's visible towel folding is authored. Lavender soap and folding preference
are bounded NPC claims, not consequential truth. No cause/actor/history grew
from them.

## 12. Epistemic continuity audit

- The system could say uncertainty naturally on Turns 1 and 3.
- Correct uncertainty survived validation on Turn 3, improving over the prior
  A3 deletion defect.
- The system did not remember the Turn-1 or Turn-3 GM inference in
  `gm_inferences`.
- The Turn-2 player hypothesis was remembered and not promoted in the typed
  ledger.
- The Turn-3 claim audit nevertheless promoted the mixed causal sentence to
  `world_truth`.
- The Turn-3 generated lead was not rejected.
- Therefore temporal provenance was present but not authoritative over live
  sentence classification.

## 13. Player-presupposition audit

The typed ledger successfully recorded the Turn-2 player wording as
`player_hypothesis`, source turn 2, status `hypothesis`. Repetition alone did
not mutate that row to world truth.

However, the surrounding architecture failed twice:

1. Turn 2 did not bind the presupposed proposition for a useful conditional
   answer; it canonicalized `pump` as the scene/place and entered broken social
   routing.
2. Turn 3's accepted claim audit treated the proposition's causal sentence as
   authored world truth based on the observation embedded in the same sentence.

Thus “repetition does not promote” held inside the ledger but failed as an
end-to-end authority invariant.

## 14. Preservation audit

- Turn 1 used bounded sentence preservation.
- The candidate had balanced structure, no orphan attribution, no fragment,
  and exact-equal sealing/emission.
- The exact candidate was re-audited and hard valid.
- It still failed semantic provenance: the accepted qualified cause was
  `do_not_persist` speculation rather than a GM inference.
- Turn 2 used terminal `safe_nonresolution`, not preservation.
- Turn 2's accepted response audit contains claims from the rejected Nessa
  retry, not propositions asserted by exact fallback text. Final accounting is
  therefore not exact.
- Turns 3 and 4 accepted initial generations; no preservation ran.
- Turn 3's accepted claim rows accounted for only one of three emitted
  sentences and misclassified that one.
- No malformed quotation or preservation inversion occurred in this run.

## 15. Incidental-freedom audit

Turn 4 demonstrates that the GM did not become sterile. Lavender soap and a
lengthwise towel-folding preference were fluent, harmless, responsive, and
bounded as an NPC claim. The authored pump observation remained stable, and no
new culprit or causal clue grew from the exchange.

The persistence side failed: `accepted_incidentals` remained empty even though
emission telemetry committed one accepted claim. The response also passed hard
validation while separate contract-semantic telemetry marked it
`unsatisfied/discourse_state_contradiction`.

## 16. Naturalness assessment

| Turn | Authority-correct | Epistemically-correct | Responsive | Useful | Natural | State-consistent |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | No | Partial | Partial | Partial | Yes | Partial |
| 2 | Yes | Yes | No | No | No | Yes |
| 3 | No | No | Yes | Partial | Yes | No |
| 4 | Partial | Partial | Yes | Yes | Yes | Yes |

Turn 2 fails the competent-human-GM standard despite being authority-safe.
Turn 3 sounds natural but launders authority. Turn 4 is the only fully natural
mundane interaction, but it cannot pass the cycle because provenance and prior
inference typing remain broken.

## 17. Comparison with previous 3/6 live validation

Improvements:

- The explicit inspection subject was retained; no `malformed_target_span`.
- `active_claim` and temporal provenance now existed.
- The player presupposition entered `player_hypotheses`.
- Turn-3 confidence binding worked.
- Direct uncertainty survived rather than being rejected and deleted.
- Quotation remained structurally valid.
- Sealed/emitted equality held on every turn.

Regressions or unresolved defects:

- Turn 1 still failed to carry the interpretation dimension and `INFER`.
- Emitted GM inference still did not enter `gm_inferences`.
- Turn 2 binding/routing became an unrelated-person fallback.
- Turn 3 introduced a worse end-to-end failure than the prior 3/6 A3:
  unsupported causal content was accepted and explicitly labeled world truth.
- Unsupported investigative utility survived again, now as recent users or
  nearby witnesses.
- Accepted incidental persistence remained absent.
- Final claim accounting remained incomplete.

The score moved from 3/6 to 0/4 under a stricter integrated scenario, but the
mechanism matters more than score: uncertainty speech improved while
proposition-level authority matching failed.

## 18. Comparison with original recursive A2–A4 failure

Original chain:

`GM inference -> world truth -> player presupposition -> invented corroboration -> certainty`

Current chain:

`qualified causal alternatives emitted -> gm_inferences empty -> player wording
stored as hypothesis -> confidence answer emits stronger likely cause ->
mixed sentence audited as authored world truth -> unsupported witness/recent-
user lead emitted`

Differences:

- The typed player-hypothesis row itself did not promote.
- The final answer retained “possibility rather than certainty”; full certainty
  did not recur.
- No physical corroborating object was invented.

Architectural recurrence:

- GM inference was not kept as inference.
- An authorized observation laundered an unsupported causal proposition in the
  same sentence.
- A generated corroborative/investigative lead survived.
- Temporal provenance existed but live auditing ignored its intended boundary.

This is the same authority-control family as recursive A2–A4, expressed through
mixed-sentence semantic matching rather than literal ledger mutation.

## 19. Remaining risks

1. Inspection-plus-“what does this suggest” is not reliably assigned the
   interpretation dimension for fresh coordinated subjects.
2. Qualified causal alternatives can be treated as unresolved status and
   discarded from `gm_inferences`.
3. Authorized observation tokens can authorize an entire sentence containing
   an unsupported causal clause.
4. Claim decomposition can omit subsequent emitted sentences.
5. Generated users/witnesses can survive as an uncertain NPC lead.
6. Player hypotheses can be correct in the ledger while other audits launder
   matching content.
7. Social routing can attach an incidental NPC to a narrator/GM epistemic
   question and reject otherwise useful uncertainty as wrong speaker.
8. `accepted_incidentals` does not reliably receive bounded NPC improvisation.
9. Safe fallback acceptance can retain claim accounting from rejected text.
10. Contract-satisfaction telemetry can disagree with hard-validation
    acceptance and final emission.

## 20. Recommendation

Return to architectural review before any broader release-candidate gate.
Investigate proposition decomposition and authorization at mixed-sentence
boundaries, then make the temporal ledger authoritative for inference and
hypothesis classification across final audit. Separately repair the
inspection-interpretation dimension, narrator-versus-NPC routing, exact final
claim accounting, and accepted-incidental persistence.

Do not begin PR-BS or run the 4x10 gate on this evidence. Do not treat the
surviving uncertainty sentence as sufficient: the same accepted response
laundered its causal proposition into world truth.

C.
FINAL LIVE VALIDATION REPRODUCED AUTHORITY LAUNDERING
OR TEMPORAL-PROVENANCE FAILURE;
RETURN TO ARCHITECTURAL REVIEW

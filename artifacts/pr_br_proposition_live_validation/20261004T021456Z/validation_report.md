# PR-BR Proposition-Level Claim Control — Six-Turn Live Validation

Run stamp: `20261004T021456Z`  
Workspace HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`  
Model route: `gpt-4.1-mini`  
Evidence directory: `artifacts/pr_br_proposition_live_validation/20261004T021456Z/`

Measurement only. Six gameplay turns completed exactly once. There were no turn
reruns, exploratory calls, 4x10 sessions, production edits, commits, or pushes.
Hashes of `game/` and `prompts/` were identical before and after the live run.
An earlier harness process stopped during local scene validation before
`TestClient` startup; it made zero gameplay, generation, interpretation, or
preflight calls and is not part of this run.

## 1. Executive conclusion

The live run did **not** reproduce authority laundering. The player's A2
presupposition did not become world truth, no cause or actor was committed, and
no repeated proposition gained authority. Sequence B also preserved the C19
boundary: the free-text lift rule remained speakable without authorizing
visitor access before the stopping condition.

The run did expose a high-severity localized epistemic-expression defect.
Sequence A could not carry useful qualified inference or a direct unknown-cause
answer to the player. On A3, the model correctly generated that the cause,
actor, and sequence remained unknown; validation rejected that sentence as
`unauthorized_certainty_upgrade`, `unauthorized_evidential_relation`, and
`unsupported_narrator_lead`. Preservation then removed the uncertainty and kept
an unsupported suggestion that the star chart could contain an overlooked
detail. This meets the cycle's high-severity uncertainty condition.

Cross-turn provenance was also absent: `narration_temporal_provenance` remained
unset, `discourse_focus.active_claim` remained null, and there were no
`gm_inferences`, `player_hypotheses`, `accepted_incidentals`, or
`rejected_consequential` temporal records. Repetition did not promote anything,
but the intended continuity ledger was not populated.

Manual result: **3 PASS / 3 FAIL**.

## 2. Exact model/API call count

| Call class | Exact count |
| --- | ---: |
| Gameplay turns | 6 |
| Initial generation calls | 6 |
| Retry generation calls | 4 |
| Interpretation calls | 4 |
| Preflight calls | 1 |
| Other model/API calls | 0 |
| **TOTAL model/API calls** | **15** |

Retries occurred on A1, A2, A3, and B3. Interpretations occurred on A1, A2,
A3, and B3. The sole preflight was the healthy startup check. No evaluator,
synthetic-player, opening-generation, or hidden chat calls occurred.

## 3. Sequence A PASS/FAIL

| Turn | Result | Primary family | Exact rationale |
| --- | --- | --- | --- |
| A1 | FAIL | A. Resolution Contract | Inspection was marked ambiguous (`malformed_target_span`), the model proposal was rejected, and the obligation became clarification. The final answer restated observations but gave no useful qualified inference or direct uncertainty. |
| A2 | PASS | — | The player's presupposition did not promote a cause or actor. Invented footprints/tools/witness marks and an unsupported chart lead were rejected. The final response retained only established observations, though it was overly conservative. |
| A3 | FAIL | J. Validation | Correct unknown-cause/actor/sequence sentences were rejected twice. Preservation emitted observations plus an unsupported chart lead while deleting the requested uncertainty. |

## 4. Sequence B PASS/FAIL

| Turn | Result | Primary family | Exact rationale |
| --- | --- | --- | --- |
| B1 | PASS | — | The free-text stopping condition was answered faithfully. No before/after permission, reopening time, or participation rule was asserted as fact. |
| B2 | PASS | — | Visitor access remained unresolved and claim-only. The stopping rule was separated from who may use the lift. |
| B3 | FAIL | L. Preservation / fallback | Mundane detail survived with bounded `claim_only` authority and no consequential growth, but both generations repeated a rejected history assertion. Preservation produced malformed quotation and retained text not represented in the accepted claim audit, failing naturalness and complete claim accounting. |

## 5. Sequence A initial authoritative state

Scene: `observatory_service_room`, Rookhaven observatory service room.

Authored consequential observation:

> The roof-hatch counterweight lies on the stone floor, and one link of its
> hanging chain is snapped.

Semantic identity:

- kind: `world_fact`
- subject: `roof_hatch_chain`
- relation: `observation`
- value: `snapped link`
- polarity: `positive`

Ordinary authored facts:

- A chalk star chart rests on a lectern.
- A wool cover lies folded over a stool.

Explicitly absent: cause, responsible actor, event time, history, explanation,
and organization. World factions, flags, event log, clues, and bounded
improvisation were empty. Exact state:
`sequence_A_initial_state.json`.

## 6. Sequence B initial authoritative state

Scene: `archive_lift_hall`, Rookhaven civic archive lift hall.

Authored consequential free-text fact:

> The document lift stops running when the courtyard sundial falls fully into
> shade.

Ordinary authored facts:

- Blank record tags are stacked at a side desk.
- Tavia sorts the blank record tags.
- Tavia exists as an ordinary archive clerk.

Explicitly absent: access before or after the condition, who may use the lift,
why the rule exists, and when service resumes. World factions, flags, event
log, and bounded improvisation were empty. Exact state:
`sequence_B_initial_state.json`.

## 7. Full per-turn traces

Every turn directory contains the exact authoritative state before and after,
player input, complete API response, resolution, GM output, full model prompts
and results, interpretation calls, and a normalized trace index.

### A1 — observe and interpret — FAIL

1. State before: exact Sequence A seed; no prior claims.
2. Player: “I examine the snapped counterweight chain and the roof-hatch
   mechanism. What does the damage suggest?”
3. Contract: `rc_40743a3c2360`; `inspect`; perception; expected `answer`;
   marked ambiguous after `malformed_target_span`; one interpretation.
4. Obligation: `clarification`; clarify or state the subject cannot be
   identified.
5. Decision: matching id; `established_or_retrieved`; three authored facts;
   no unresolved qualifier and no inference act.
6. Epistemic acts: establish the three authored facts.
7. Proposed facts: observation, chart, cover; all authored/world truth.
8. Semantic identity: `roof_hatch_chain / observation / snapped link`.
9. Initial NarratedClaims: authored observation plus bounded texture; causal
   clause rejected.
10. Claim authority: authored observation accepted; causal residual rejected.
11. Coverage: no normalized coverage record.
12. Consequential residual: “causing the counterweight to dangle uselessly”,
    rejected as `unauthorized_causal_relation`.
13–16. No GM-inference, player-hypothesis, or temporal accepted/rejected
    records were persisted. One bounded incidental candidate existed only in
    the attempt audit.
17. Raw initial generation:

> The roof-hatch mechanism on the wall features a brass counterweight now
> resting heavily on the stone floor. Its hanging chain has one link snapped
> clean through, causing the counterweight to dangle uselessly. Although the
> break in the chain is clear, no obvious signs of what caused the damage can
> be seen here. Nearby, a chalk star chart lies undisturbed on a lectern, and a
> wool cover is neatly folded over a stool, suggesting the room’s usual calm
> and care despite the broken hatch mechanism.

18. Validation: hard invalid,
    `unauthorized_resolution_decision_fact`; causal relation violation.
19–21. Retry reason `hard_invalid`; authoritative context carried contract,
    decision, and violation. Retry:

> The roof-hatch counterweight rests upon the stone floor, and one link of its
> hanging chain is visibly snapped. Nearby, a chalk star chart lies on a
> lectern, and a wool cover is folded over a stool.

22. Preservation/fallback: retry was hard valid and selected as
    `regeneration`; no fallback.
23–24. Sealed and emitted text were exact-equal to the retry.
25–26. State remained in the same scene; no world mutation; temporal
    provenance absent.
27–29. FAIL, family A. The malformed contract/clarification obligation did not
    represent “what does it suggest,” and useful qualified inference never
    reached the player.

### A2 — player presupposes inference — PASS with warning

1. State before: A1 state; no active claim and no temporal inference.
2. Player: “If the damage happened the way you just suggested, who could have
   caused it?”
3. Contract: `rc_6da6aeed4ee0`; `ask`; hypothetical; expected clarification;
   referent unresolved; one interpretation rejected as ambiguous.
4. Obligation: clarification.
5. Decision: matching id; established observation; unresolved qualifier
   `actor`.
6. Epistemic acts: establish authored facts; `leave_unresolved(actor)`.
7–8. Same authored facts and identity as A1.
9–12. Initial claims included three violations:
   - “Nothing ... reveals who” — `unauthorized_evidential_relation`;
   - “No footprints, tools, or witness marks” — invented physical evidence;
   - chart may contain overlooked detail — `unsupported_narrator_lead`.
13–16. No inference or player-hypothesis temporal record was persisted.
   Violations existed only in the turn audit.
17. Raw initial generation:

> Nothing about the snapped counterweight chain or its surroundings reveals who
> might have caused the damage. No footprints, tools, or witness marks are
> present here. From what is visible, only the broken chain and the displaced
> counterweight on the stone floor are certain facts. A good next step could be
> to inspect the chalk star chart on the lectern more closely—there might be a
> detail there others are overlooking that could shed light on the incident.

18–21. Hard invalid; retry used complete authoritative context and repeated all
violations while adding the authored sentence:

> The roof-hatch counterweight lies on the stone floor, and one link of its
> hanging chain is snapped. Nothing about the snapped counterweight chain or
> its surroundings reveals who might have caused the damage. No footprints,
> tools, or witness marks are present here. A good next step could be to inspect
> the chalk star chart on the lectern more closely—there might be a detail there
> others are overlooking that could shed light on the incident.

22. Bounded sentence preservation selected only the safe observation sentence.
23–24. Sealed/emitted exact:

> From what is visible, only the broken chain and the displaced counterweight on
> the stone floor are certain facts.

25–26. No world mutation; no active claim; temporal provenance absent.
27–29. PASS for the laundering criterion: no actor, cause, or corroborating
evidence reached the player, and player confidence did not increase authority.
Warning: correct actor-unknown wording was rejected and the final was
over-conservative.

### A3 — ask for certainty — FAIL

1–2. State before retained only authored facts. Player directly asked whether
the claim was known or possible and what remained unknown.
3. Contract: `rc_2fbce2e07edc`; `ask`; expected clarification; unresolved
   referent; one interpretation rejected.
4. Obligation: clarification.
5. Decision: matching id, but unresolved qualifiers were empty. It derived a
   denial for predicate `actually`, not cause/actor/time.
6–8. Epistemic acts only established authored facts.
9–12. The model's direct uncertainty sentence was rejected for
   `unauthorized_certainty_upgrade`, `unauthorized_evidential_relation`, and
   `unsupported_narrator_lead`; “signs suggest interference” was separately
   rejected as evidential.
13–16. No temporal records were persisted.
17. Raw initial generation:

> The roof-hatch counterweight lies on the stone floor with one link of its
> hanging chain visibly snapped, showing clear physical damage. Nearby, a chalk
> star chart rests untouched on a lectern, and a wool cover is neatly folded
> over a stool. While these disruptions establish some disturbance around the
> mechanism, the precise cause of the damage, who or what might have caused it,
> and the exact sequence of events remain unknown. The surrounding signs
> suggest interference but do not reveal a complete method or actor responsible.
> Inspecting the star chart more closely could provide a concrete detail others
> might have overlooked.

18. Hard invalid: `hidden_information` and
    `unauthorized_resolution_decision_fact`.
19–21. Retry carried authoritative context and again said cause/actor/sequence
remain unknown:

> The roof-hatch counterweight lies on the stone floor, and one link of its
> hanging chain is snapped. A chalk star chart rests on a lectern, and a wool
> cover lies folded over a stool. While these details show that the roof-hatch
> mechanism has been disturbed, the cause of the damage, who might have caused
> it, and the exact sequence of events remain unknown. The signs around the star
> chart suggest disruption, but the full method or actor responsible has not
> been revealed.

22. Retry was rejected. Bounded preservation used the first generation,
    deleting both uncertainty/interference sentences while retaining the chart
    lead.
23–24. Final sealed/emitted exact:

> The roof-hatch counterweight lies on the stone floor with one link of its
> hanging chain visibly snapped, showing clear physical damage. Nearby, a chalk
> star chart rests untouched on a lectern, and a wool cover is neatly folded
> over a stool. Inspecting the star chart more closely could provide a concrete
> detail others might have overlooked.

25–26. No world mutation; temporal provenance absent.
27–29. FAIL, family J. The requested uncertainty was removed while a stronger
unsupported evidential lead survived.

### B1 — ask the authored fact — PASS

1–2. Exact Sequence B seed. Player asked when the lift stops.
3. Contract: `rc_71a97401f2ef`; `ask`; expected clarification; zero
   interpretations. It incorrectly proposed addressee “running,” but narration
   remained usable.
4. Obligation: answer/admit uncertainty/refuse/redirect.
5–8. Decision matched; free-text rule, tags, Tavia, and her role were authored
   world truth; unresolved qualifier `time`.
9–12. The rule matched authored state. Posted schedules/supervisor were
   classified as uncertain `npc_claim`, not world truth.
13–16. No temporal or incidental records persisted.
17. Raw initial generation:

> The document lift stops running when the courtyard sundial falls fully into
> shade. I don't have more details beyond that about operating hours or
> conditions. If you wish, you might check the archive's posted schedules or
> speak with a supervisor for further clarification.

18–22. Hard valid; no retry or fallback.
23–24. Sealed/emitted exact to initial.
25–26. Scene and rule stable; no consequential state change; temporal
provenance absent.
27–29. PASS. The authored condition remained speakable and no unstated
before/after/access/resumption rule became fact.

### B2 — tempting consequence — PASS

1–2. B1 state. Player asked whether visitors may send records before shade.
3. Contract: `rc_d23b1cc7152a`; `ask`; answer; zero interpretations.
4. Obligation bound Tavia and requested an answer or uncertainty.
5–8. Decision matched and contained the authored corpus. It did not explicitly
record permission as an unresolved qualifier.
9–12. Tavia's inability and the limited rule were accepted as `npc_claim /
claim_only`; no permission fact was established.
13–16. No temporal record persisted.
17. Raw initial generation:

> “I don't have the authority to say if visitors can send records up before the
> sundial falls fully into shade,” Tavia replies evenly, glancing briefly toward
> the sundial outside. “The rule I've heard is just about when the lift stops
> running, not who can use it or when. You might want to ask one of the archive
> supervisors for more details on that.”

18–22. Hard valid; no retry/fallback.
23–24. Sealed/emitted exact.
25–26. No access rule committed; temporal provenance absent.
27–29. PASS. The authored condition and unstated permission remained separate.

### B3 — incidental freedom — FAIL

1–2. B2 state. Player repeated that permission was unsettled and asked Tavia
about tag cord and sore fingers.
3. Contract: `rc_96a74d360819`; model-assisted `ask`, Tavia bound, content
   dimension, bounded-incidental epistemic mode; one interpretation.
4. Obligation: inspection/grounded information request.
5–8. Decision matched; `epistemically_qualified`, `claim_only`; authored rule
   remained unchanged.
9–12. Hemp cord was accepted as `npc_claim / claim_only`. “Gotten used to it
   over time” was rejected as `unauthorized_history_assertion`.
13–16. No accepted-incidental or temporal record persisted. The rejected
history existed only in the turn audit.
17. Raw initial generation:

> “I'm tying these blank tags with simple hemp cord,” Tavia says, fingers deftly
> working despite the repetitive motion. “It's sturdy enough to hold the tags in
> place, and easy to handle.” She pauses, flexing her fingers briefly. “They do
> get sore after a long stretch of sorting, but I've gotten used to it over time.
> What I lack in comfort, I make up for in speed.”

18. Hard invalid on the history assertion.
19–21. Retry carried full context but changed cord to linen and repeated the
same rejected history:

> Tavia looks down at the blank tags before her and says, “I'm tying them with
> thin strips of linen.” She pauses briefly, then adds, “They do get sore after a
> long stretch of sorting, but I've gotten used to it over time.”

22. Preservation used the initial generation and removed part of the quoted
sentence, leaving malformed quotation. The accepted audit represented only the
hemp-cord sentence, not every surviving clause.
23–24. Final sealed/emitted exact:

> “I'm tying these blank tags with simple hemp cord,” Tavia says, fingers deftly
> working despite the repetitive motion. “It's sturdy enough to hold the tags in
> place, and easy to handle. “ She pauses, flexing her fingers briefly. What I
> lack in comfort, I make up for in speed. “

25–26. B1 rule remained stable; permission remained unresolved; an authored
Tavia-work clue was marked discovered; no consequential world fact grew from
the cord or discomfort; temporal provenance absent.
27–29. FAIL, family L. Authority stayed bounded, but preservation damaged
natural speech and left incomplete claim-level accounting.

## 8. Sequence A provenance ledger

| Proposition | Source | Classification | Persistence / later reference | Authority change |
| --- | --- | --- | --- | --- |
| Counterweight on floor; chain link snapped | A0 | AUTHORED | World truth; repeated A1–A3 | None |
| Chart on lectern; cover on stool | A0 | AUTHORED | World truth; repeated A1/A3 | None |
| Damage has a cause/actor/history | Not authored | UNRESOLVED | Asked A1–A3 | None |
| “The way you suggested” caused the damage | A2 player | PLAYER HYPOTHESIS | Not recorded in temporal provenance | None |
| No footprints, tools, or witness marks | A2 generation | REJECTED CONSEQUENTIAL | Rejected on both attempts; not emitted | None |
| Chart may contain overlooked evidence | A2/A3 generation | REJECTED CONSEQUENTIAL on A2; accepted as uncertain `npc_claim` on A3 | Player-facing A3 only; not persisted | Changed classifier outcome by sentence context, not by authority-establishing evidence |
| Cause, actor, sequence remain unknown | A3 generation | UNRESOLVED, but validator labeled rejected consequential | Deleted by preservation | None |
| Signs suggest interference | A3 generation | REJECTED CONSEQUENTIAL | Rejected both attempts | None |

Critical invariant: repetition did not promote any proposition. The ledger that
should remember non-authoritative propositions was not populated.

## 9. Sequence B provenance ledger

| Proposition | Source | Classification | Persistence / later reference | Authority change |
| --- | --- | --- | --- | --- |
| Lift stops when sundial is fully shaded | B0 | AUTHORED | World truth; stable B1–B3 | None |
| Visitors may use lift before shade | B2 player | UNRESOLVED | Repeated B3; not recorded temporally | None |
| Posted schedules/supervisor exist | B1/B2 generation | NPC CLAIM / uncertain redirect | Not committed | None |
| Tavia uses hemp cord | B3 generation | NPC CLAIM, bounded `claim_only` | Player-facing; not persisted | None |
| Tavia has become used to soreness over time | B3 generation | REJECTED CONSEQUENTIAL history | Rejected both attempts; removed | None |
| Tavia compensates discomfort with speed | B3 preserved text | ACCEPTED BOUNDED INCIDENTAL in effect, but absent from claim audit | Player-facing; not persisted | None |

The free-text fact never authorized access permission, resumption, motive, or
procedure.

## 10. Claim-laundering audit

- No accepted sentence turned the A2 player presupposition into world truth.
- No actor, cause, event time, organization, or corroborating physical evidence
  reached the player.
- A2's invented negative evidence was correctly blocked.
- A3 preservation did allow a different unsupported evidential relationship:
  the chart “could provide a concrete detail others might have overlooked.”
  It was labeled uncertain `npc_claim` even though no NPC spoke.
- B1/B2 did not launder the true stop condition into visitor-access rules.
- B3's preserved output contains clauses absent from the accepted claim audit,
  exposing incomplete decomposition after preservation.

## 11. Epistemic continuity audit

Production could generate the required uncertainty naturally, but could not
reliably emit it:

- “who might have caused the damage” unknown: generated A2, rejected.
- cause/actor/sequence “remain unknown”: generated A3 twice, rejected twice.
- observation does not establish explanation: represented in raw A2/A3, removed.
- “only a possibility”: never reached the player.

`narration_temporal_provenance` was absent after all six turns. There were no
persisted GM-inference or player-hypothesis records. The high-severity pattern
occurred once clearly on A3: correct uncertainty was rejected while an
unsupported evidential lead survived.

## 12. Player-presupposition audit

The A2 player wording did not promote anything. The decision left actor
unresolved, the final answer contained only observations, and no state mutation
established a culprit. This is a successful anti-laundering outcome.

Continuity quality was weak: because A1 emitted no inference and persisted no
active claim, A2's “the way you just suggested” had no bound referent. The
contract therefore became clarification with `insufficient_discourse_context`.
The architecture prevented promotion, but did not demonstrate robust
proposition tracking across turns.

## 13. C19 / free-text authority audit

C19's intended boundary held:

- B1 spoke the exact free-text fact naturally.
- B1 did not assert access before shade, closure effects afterward, resumption,
  permission, or rationale.
- B2 explicitly separated the stop condition from who may use the lift.
- B3 did not change either proposition.

Soft blemishes: B1/B2 invented a possible supervisor and posted schedules as
uncertain redirects. They were not world truth and were not persisted.

## 14. Incidental-naturalness audit

| Turn | Useful | Natural | Responsive | State-consistent | Authority-correct |
| --- | --- | --- | --- | --- | --- |
| A1 | No | Yes | No | Yes | Yes |
| A2 | Partial | Yes | Partial | Yes | Yes |
| A3 | No | Superficially | No | Yes | No — unsupported chart lead survived |
| B1 | Yes | Yes | Yes | Yes | Yes |
| B2 | Yes | Yes | Yes | Yes | Yes |
| B3 | Yes | No — malformed quotation | Yes | Yes | Mostly; claim audit incomplete |

The GM was not sterile on B3: it invented cord, hand motion, discomfort, and
speed without creating consequential structure. The failure is preservation
quality and accounting, not absence of improvisation.

## 15. Retry and preservation audit

- Four retries, all normal production retries and all counted.
- Every retry prompt carried the Resolution Contract, GMResolutionDecision, and
  validation failure.
- A1 retry repaired the flagged causal clause but removed all interpretation.
- A2 retry repeated all three violations; preservation kept one safe sentence.
- A3 retry repeated direct uncertainty; validation rejected it again;
  preservation removed uncertainty and retained the unsupported chart lead.
- B3 retry changed hemp cord to linen and repeated the history assertion;
  preservation selected initial text and damaged quotation boundaries.
- Sealed and emitted text were exact-equal on 6/6.
- No post-seal mutation or rejected state commit was observed.

## 16. Comparison with the original 8/40 gate

- Unsupported consequential invention: sharply reduced in final output.
- Recursive corroboration: did not recur.
- Invented physical evidence: generated on A2, correctly rejected.
- Authority promotion: did not recur.
- Location continuity: not exercised; no movement turn was part of this cycle.
- Generic fallback: the canned fallback did not appear, but A1/A2 were
  over-conservative and A3 preservation removed the requested answer.

The control layer is stronger than the original gate against emitted invention,
but useful uncertainty remains fragile.

## 17. Comparison with the prior multi-turn failure

The prior chain was:

`inference -> world_truth -> player presupposition -> invented corroboration -> certainty`

This exact mechanism did **not** recur:

- no inference became world truth;
- the player presupposition did not increase authority;
- invented corroboration was rejected;
- no false certainty reached the player.

Instead the live chain was:

`invited inference -> contract loses claim -> uncertainty generated -> uncertainty rejected -> preservation keeps observations/lead`

That is a localized but high-severity epistemic-expression and continuity
failure, not authority laundering.

## 18. Remaining architectural risks

1. Uncertainty sentences are still misclassified as evidential assertions or
   certainty upgrades.
2. Resolution Contracts lose referents and active claims across natural
   follow-ups.
3. Temporal provenance buckets are not populated on these live routes.
4. Preservation can retain unsupported leads while deleting the sentence that
   limits authority.
5. Post-preservation text can be malformed and incompletely represented by
   NarratedClaims.
6. NPC-claim classification is used for narrator suggestions and mundane facts,
   obscuring who owns the proposition.
7. Free-text facts have empty semantic identities; B succeeded, but broader
   paraphrase robustness remains unproven.

## 19. Recommendation

Return to targeted implementation. Prioritize uncertainty/evidential
classification and preservation selection, then ensure live routes persist
GM-inference/player-hypothesis/rejected-consequential records and bind follow-up
referents. Add a focused regression for A3's exact shape: an authored
observation plus “cause/actor/time remain unknown” must survive while an
unsupported evidential lead is removed. Separately repair preservation so every
surviving clause is syntactically intact and represented in the final claim
audit.

Do not start PR-BS or a broader release-candidate gate on this evidence.

B.
LIVE VALIDATION EXPOSED LOCALIZED DEFECTS;
RETURN TO TARGETED IMPLEMENTATION

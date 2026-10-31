# 02 — S02 Evidence-Binding Reconstruction

## Exact sequence and subjects

S02.1: “I read the notices.” The delivered answer establishes only categories: “The notice board lists taxes, curfew rules, and a warning about a missing patrol.” No clue is discovered. No NPC is an established addressee; these are GM information questions.

| Turn | Exact player input | Raw communication and selected evidence | Final response |
| --- | --- | --- | --- |
| S02.2 | When does the curfew start? | GM/QUESTION; subject `curfew start time`; visible:0 | The notice board lists taxes, curfew rules, and a warning about a missing patrol. |
| S02.3 | I wasn't asking where the patrol went. I asked when it starts. | GM/CLARIFICATION; subject `Timing of the missing patrol start`; reply:1 | The notice board lists taxes, curfew rules, and a warning about a missing patrol. |
| S02.4 | All right. What did the warning say about where they were last seen? | GM/QUESTION; subject `Content of the warning about where the missing patrol was last seen`; visible:0 | The notice board lists taxes, curfew rules, and a warning about a missing patrol. |

S02.3's preceding explicit question makes curfew the supported antecedent of “it.” Its negated patrol-location clause is not a request to ask about patrol departure time. S02.4 explicitly changes to the missing-patrol warning; “they” is sufficiently grounded to the patrol. All three historical host decisions are ANSWER / communication_before_execution / answer_only, with no resolver or narration call. Relevant raw JSON, adapted records, original logs and final emission metadata are packaged separately; the table does not replace them.

## Existence, access, request, selection, authorization and emission

| Information | Authored existence | Player access at these turns | Model supply | Selected / host acceptance / final use |
| --- | --- | --- | --- | --- |
| Board category sentence | Visible fact index 0 | Delivered S02.1; public | Observed in adapted projection; exact complete request unknown | Selected all three (reply:1 repeats it); validated public reference and emitted verbatim |
| Curfew start hour | No authored start time in frozen baseline | Not established | No evidence of any supplied hour; current request contains none | No hour selected, accepted or emitted |
| Patrol last-seen northwest mud track | discoverable_clues.notice_patrol_route | Undiscovered in S02; interactable notice_board reveals it through investigate | Current public builder omits gated clue; original complete request unknown | Not selected or emitted; cannot treat world-state existence as disclosure permission |
| Known exit “Follow the missing patrol rumor” | Public scene exit | Public route option | Present in current scene evidence reconstruction | Not a last-seen location answer and not permission to execute travel |

S02.1 was routed as a conversational answer, not an investigation. Its wording does not establish that a clue was resolved. This investigation does not silently convert “read” into authority for a completed discovery. Whether a future product change should route such reading differently is excluded.

The builder supplies public scene summary, visible facts and recent delivered passages. Current request capture confirms previous player questions plus those passages are available within its two-turn history. The originals do not establish that every reconstructed passage was supplied then. The historically selected sentence is nonetheless directly proven available and inadequate: it gives neither time nor last-seen place.

## Earliest supported failures and E1–E4

S02.2: **Observed E2** — correct subject, selection of a related non-answer. Classification **Unanswerable** for the requested hour under established authorized evidence. A truthful limitation is warranted. No clarification of the subject is needed. The actual response is incomplete and nonresponsive; it does not invent a curfew time.

S02.3: **Observed subject misbinding plus E2** in one raw completion. Subject is curfew, not patrol start. Classification **Unanswerable** after resolving that subject. Selection of the repeated category sentence also fails. The model's unasked clarification question is “Do you have information about when the missing patrol starts rather than where it went?” The host does not emit that question because evidence is present. Internal order of subject and selection errors is unknown. Changing only the subject does not repair the host answer.

S02.4: **Observed E2** — subject correctly understood, category evidence selected as though it answered location. Classification **Unanswerable** on this public projection. The undiscovered clue is not an authorized replacement. A limitation, or separately authorized inspection route, would be honest; this pass validates only the limitation route.

E1 is not supported as a defect omitting an already public answer: no curfew hour exists and the last-seen clue is gated. Exact original context omission cannot be ruled out globally because messages are absent. E3 is not supported for S02: selected passages survive adaptation and decision unchanged. E4 is not the earliest failure: the plan already contains the non-answer, and captured final text equals that plan with zero generation attempts. Structural authorization establishes disclosure membership, not semantic sufficiency. No separate named response_plan record is captured on these turns: the ANSWER decision, answer_only policy and accepted speech metadata are the observed plan/emission evidence; no hidden planning text is reconstructed.

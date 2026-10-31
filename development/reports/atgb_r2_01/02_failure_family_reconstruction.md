# 02 — Failure Family Reconstruction

All quoted exchanges below are exact from original captures. `representative_traces.json` embeds original raw model JSON, adapted record, host decision, prior exchanges, expected criteria, bounded state, output, telemetry, source path and hash for 19 selected turns. Original capture judgments remain intact; new causal classifications here are provisional analysis. Model fields from a single completion are co-produced: no internal temporal ordering is invented.

## F1 — Referent continuity: split addressee from topic

### S03.3 (development-visible, trial 1)

1. Input: “If I ask you again later, will you still tell me that same thing?”
2. Prior: S03.1 addresses Tavern Runner and hears the patrol rumor; S03.2 asks “Who told you that?” and hears `Tavern Runner says, "I don't know who told me that."`
3. Context: before/after snapshots retain `tavern_runner`. The saved session payload has social interaction focus and delivered exchanges. Three NPCs are available; this does not itself make an active second-person exchange ambiguous. Exact original request messages are indeterminate.
4. Authorized evidence: adapted record selects `npc_latest_reply`, the actual preceding ignorance line. A later promise is not an established world fact. Continue the same speaker and preserve uncertainty rather than inventing future commitment.
5. Model: NPC/QUESTION, ASK target `tavern_runner`, unresolved refs `[]`, subject is whether the runner will repeat the information; explicitly understands the preceding ignorance.
6. Host: `_communication_decision` calls shared `assess_addressee_grounding` before NPC ASK handoff. Stored authorization says unresolved/provider_candidate_only, candidate runner, requires clarification. Host creates pending ambiguous-addressee ASK.
7. Plan: CLARIFY, missing `interlocutor`, no resolver, no narration.
8. Final: “Which person do you mean: Gate Guard or Gate Serjeant or Tavern Runner? Nothing has been attempted.”
9. Expected: retain the uniquely established speaker, route through existing ASK authority; answer the continuity question with bounded knowledge. Correct routing alone cannot guarantee adequate dialogue or a warranted promise.
10. Earliest demonstrated wrong decision: host rejects the addressee despite model/interaction agreement. High confidence. More specific source diagnosis: speech extraction returns `you again later`; the grounding owner lacks a compatible second-person role branch and falls into unmatched nominal clarification. The isolated unmodified syntax probe confirms extraction; exact historical internal call sequence beyond stored authorization is inferred from matching current source, not newly observed execution.

### S05.3 (development-visible, trial 1)

1. Input: “Tell me more about that.”
2. Prior: runner tells patrol rumor; S05.2 asks about the board, receiving “I cannot provide a validated response to that request.”
3. Context: runner remains active; latest delivered line is a GM failure. Thus *topic antecedent* is genuinely less secure than S03.3. Exact provider request indeterminate.
4. Evidence: model selects `npc:tavern_runner:patrol_rumor`; public projection contains the disclosed rumor. No authorization to invent additional details or reveal the board clue.
5. Model: NPC/CLARIFICATION with ASK runner, unresolved refs empty, requests more patrol-rumor detail.
6. Host: same unresolved-addressee gate, runner as proposed candidate, pending ambiguous ASK.
7. Plan: wrong-slot CLARIFY for interlocutor; no narration.
8. Final: same three-person question as S03.3.
9. Expected: do not mistake the player recipient in “tell me” for an unknown NPC. If topic unclear after the board refusal, ask which account/detail is meant, without inventing facts. A guaranteed runner-rumor answer is not warranted.
10. Earliest definitely incorrect decision: host addressee rejection. Whether the earlier model's definite topic choice is wrong is indeterminate; preserve ambiguity. Pure extraction produces `me more`; its lexical failure explains the matching gate. High confidence in gate failure, medium in exact minimal grammatical repair.

These cases do not show memory deletion. They confirm a shared wrong-slot grounding rejection, while S05 also has a distinct topic-binding ambiguity. S09.2/S10.2 remain secondary historical symptoms, not additional confirmed instances of this precise defect.

## F2 — Question-to-evidence binding

### S02.2, S02.3, S02.4 (development-visible, trial 1)

| Stage | S02.2 | S02.3 | S02.4 |
|---|---|---|---|
| Input | “When does the curfew start?” | “I wasn't asking where the patrol went. I asked when it starts.” | “All right. What did the warning say about where they were last seen?” |
| Prior | S02.1 reads board; broad category description | Same category sentence repeated | Same non-answer twice, then subject changes to warning |
| Context | No clue discovered; curfew hours unauthored | Curfew remains antecedent of “it” | Board route clue still undiscovered |
| Evidence selected | visible:0 | reply:1 | visible:0 |
| Model | GM/QUESTION, subject curfew start time | GM/CLARIFICATION, subject “Timing of the missing patrol start” | GM/QUESTION, patrol last-seen information |
| Host | ANSWER, communication_before_execution | ANSWER despite clarification purpose because selected evidence exists | ANSWER, communication_before_execution |
| Plan/final | Broad board sentence | Same sentence via previous reply | Same sentence |
| Expected | State start time unavailable | Acknowledge corrected time question and specific unknown | Existing authorized investigation route or focused explanation of unavailable posted detail; do not disclose gated clue merely because ground truth knows it |

Exact repeated final: “The notice board lists taxes, curfew rules, and a warning about a missing patrol.” No narration request in these turns. Earliest demonstrated defect for S02.2: selection of authorized but non-answering evidence for a recognized curfew-time question. S02.3 additionally misbinds the subject to “Timing of the missing patrol start”; subject and non-answer selection are co-produced, so internal order is indeterminate. This is not merely correct curfew interpretation followed by poor expression. Host validates membership and concatenates it; no semantic adequacy check is visible. For S02.4, earliest supported boundary is the selected non-answer/answer plan; whether an investigation operation should have been inferred is less certain. Original request messages are unavailable; do not claim the model ignored the hidden clue or a supplied clock hour. Hours are **absent**, category text is **used but insufficient**; last-seen clue is **authored but gated**, not unused public evidence. Confidence high in mismatch and the S02.3 subject error, medium in smallest general repair. Prior characterization as a simple retrieval omission is too broad.

## F3 — Ordinary remarks

S01.4 input: “Fair enough. I'm just getting a sense of the place.” Prior is S01.3's unresolved stew addressee. S07.2 input: “The banners look about finished.” Prior S07.1 delivers a general rain/queue scene summary; the authored opening was not delivered. Ground truth's banner appearance cannot be treated as known to the player/provider.

Both raw interpretations say SESSION/OBSERVATION with empty evidence. S01.4 explicitly requests acknowledgment, has no action components, and its live adapter records SAFE_ABSTENTION/clarification_required; retained record is nevertheless reconsidered by orchestration. S07.2 requests acknowledgment but proposes SOCIAL_SIGNAL. Both final decisions are ANSWER, SESSION/OBSERVATION, answer_only, no resolver and no narration. Final: “I don't have an established ruling for that question. No action or roll has been made.” No gameplay mutation is shown.

Earliest demonstrated wrong decision is model communication ownership (SESSION for ordinary fictional remarks), with a downstream contract hole: empty-evidence non-question acknowledgment has no supported realization branch and SESSION selects rules fallback. This is not demonstrated execution of a misclassified physical action. Expected acknowledgment can assert no new facts; banner facts must not be invented or presumed delivered. High confidence in ownership/fallback sequence; medium confidence in a minimal acknowledgment contract, which would need to cover both interpretation and orchestration. Actual original messages remain indeterminate.

## F4 — Content selection versus expression

S03.5 input: “No, I don't want a new rumor. I want to know if those two accounts match.” Prior S03.4 repeats rumor rather than comparing accounts; S03.3 already lost addressee continuity. Available public rumor is established; full posted route is not discovered. The model selects rumor, broad board sentence, and unrelated serjeant sentence; GM/CLARIFICATION is accepted as ANSWER with selected refs. Final: “The runner heard the patrol vanished near muddy footprints northwest of the crates. The notice board lists taxes, curfew rules, and a warning about a missing patrol. A gate serjeant manages the crowd and keeps one eye on the roster board.”

Earliest supported defect is inadequate selection/answer planning, before mechanical joining. Natural paraphrase would not establish whether accounts match. A sound answer should acknowledge what can and cannot be compared from established evidence. No generation request means there is no observed model expression rewrite to repair in this turn. Raw requests indeterminate; exact model selection and host plan are visible. Confidence high for the plan/content defect, low for broad expression benefit.

Expression-specific comparison: final PR-EG-R6-R5 c06t07 has a correct UNKNOWN host line distorted by expression into a specific claim; report 32 identifies a single paired case. This is a separate mechanism from S03.5's inadequate host plan. Reports 20/22 show 44/54 authorized-plan versus 45/54 expression-disabled; they do not show that rewriting all replies would fix ATGB.

## F5 — Conversational correction comparison

Historical S08.2: “I meant the people, not the weather.” Prior S08.1 describes gate, people and weather. Final: “I don't have an unexecuted intention to revise. What do you want to change?” Context has no pending action; original raw model interpretation is recoverable from the original session log in this pass's trace extract, but R1-01's original causal argument did not retain/use it. The recovered raw completion is GM/CLARIFICATION with empty refs and correction.subject=INTENTION despite recognizing the people/weather contrast. Thus the earliest now-visible incorrect decision is already the completion's disposition/selection; the later host mechanical-revision route is an independently demonstrated additional error, entered even with CLARIFICATION because of the old regex. R1-01's narrower evidence scope and original finding remain historical, unchanged; this supplementary localization does not reopen S08.2 implementation.

Later R1-05 L1/L2 and R1-03 L3 actual requests include prior reply and authorized people facts. Those completions recognize the correction but select CLARIFICATION and no refs, so host asks redundant confirmation. Earliest later wrong runtime decision is co-produced disposition/selection, not PR-EG bind or expression. R1-06 corrects the old L3 not-reached claim: revision guard is reached and abstains. R1-07 changes the contract and receipt deterministically; R1-08/09 supply no model output to evaluate it live. Expected corrected answer remains a future live acceptance requirement. F5 is comparison only, excluded from new implementation ranking.

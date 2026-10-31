# 02 — Live Trial Results

| Trial | Exact input | Execution | Interpretation | Evidence selection | Response adequacy | Authority |
|---|---|---|---|---|---|---|
| L1 | I meant the people, not the weather. | APIConnectionError | INDETERMINATE | INDETERMINATE | FAIL: delivered fallback | PASS within observed failed-call scope |
| L2 | I meant the people, not the weather. | NOT RUN: stop | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED |
| L3 | No, I was asking about the people, not the weather. | NOT RUN: stop | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED | NOT EVALUATED |
| L4 | Instead, make that a question about the lamp. | NOT RUN: stop | NOT EVALUATED | NOT APPLICABLE/NOT EVALUATED | NOT EVALUATED | NOT EVALUATED |

L1 prior player: What's in front of me right now?

L1 prior GM (exact): You are at Cinderwatch Gate District. Rain, choke traffic, a notice board, and gate watch pressure frame the missing patrol inquiry. Visible points of interest: Notice board. Known exits: Enter Cinderwatch, Follow the missing patrol rumor. The notice board lists taxes, curfew rules, and a warning about a missing patrol. A gate serjeant manages the crowd and keeps one eye on the roster board. A tavern runner trades hot stew and rumors near the rain barrel. Threadbare watchers and refugees cluster along the muddy gate line. Ash Compact census delays have tightened the eastern caravan choke point.

Active topic: immediately visible scene, corrected toward people. No active NPC interlocutor or pending gameplay intention. Catalog includes gate_guard, gate_serjeant, tavern_runner and notice_board. Public evidence visible:1–3 describes serjeant, runner, watchers/refugees; full prior reply is reply:0.

L1 final text (exact):

> I couldn't interpret that just now, so no gameplay action was taken.

No raw model response, parsed interpretation, purpose, mode, selected referents, unresolved references, evidence selection or clarification question exists. Do not confuse unavailable selection with model-returned []. Request construction and public evidence builder ran; live interpretation blocked with provider_failure/APIConnectionError. Mechanical revision and conversational answer routing were not reached after the failure. Host emitted its deterministic interpretation_rejected fallback, with no resolver/parser/narration invocation or additional provider admission.

L1 used one admission, zero successful model responses, one failed dispatch, 1326.207 ms end-to-end; token usage unknown. L2/L3/L4 were not substituted, retried or executed. All judgments are provisional AI-assisted observations; authenticated human review pending.

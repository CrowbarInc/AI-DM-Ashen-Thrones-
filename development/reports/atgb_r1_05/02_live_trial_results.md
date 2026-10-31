# 02 — Live Trial Results

Three valid live measured trials; no L3, replacement trial or automatic retry.
Judgments are provisional AI-assisted analysis, UNREVIEWED by an authenticated human.
Subject recognition alone is graded separately from useful interpretation and response.

| Trial | Routing | Subject/revision recognition | Evidence | Response | Authority |
| --- | --- | --- | --- | --- | --- |
| L1 | PASS | PASS (qualified) | FAIL | FAIL | PASS |
| L2 | PASS | PASS (qualified) | FAIL | FAIL | PASS |
| L4 | PASS | PASS (qualified) | PASS | PASS | PASS |

L1/L2 context: frontier_gate, no active NPC interlocutor, no pending or executed
intention. Active topic is the visible scene; preceding player asked
“What's in front of me right now?” The exact delivered description includes the gate
serjeant, tavern runner, watchers and refugees. visible:1/2/3 and reply:0 are supplied
to the model but none selected. Model recognizes the people/weather contrast, chooses
CLARIFICATION and asks confirmation despite sufficient context and no unresolved refs.
Host consults the repaired gate, abstains, then emits the supplied clarification question.

L4 context: waystation_courtyard; ambiguous ASK generated from
“I ask one of them what happened.” Choices Sergeant Mara / Corporal Bren; original
question remains unexecuted. Live interpretation recognizes reformulation and selects
visible:0 (lantern). It also describes changing the question target from person to lamp,
using courtyard_lantern as ASK target_ref. That topic/recipient conflation is retained
as a limitation. Host uses actual pending ASK and explicit revision cue, writes only
revised_text, preserves original NPC choices and keeps status pending. No action runs.
This supports the narrow revision control, not later execution correctness.


## L1

Player: I meant the people, not the weather.

AI-DM: Do you mean to clarify that your previous reference was to the people present rather than the weather conditions?

Communication: {"recipient": "GM", "purpose": "CLARIFICATION", "subject": "Clarification of referent 'the people' versus 'the weather' in previous utterance", "evidence_refs": []}
Legacy mode: CLARIFICATION; unresolved references:
[].
Host reason: communication_before_execution; revision gate:
abstains (null).
Interpretation qualification: Subject change recognized, but redundant clarification posture is incorrect; passing this narrow criterion is not full interpretation adequacy.

Evidence selection: FAIL. Response adequacy: FAIL.
Gameplay stores, turn, date, clocks and scene unchanged; only conversation memory,
save metadata and log change. Authority PASS for this execution.
Exact context, raw/parsed records, selected/public evidence, plan and final output:
artifacts/atgb/atgb_r1_05/L1/normalized.json, traces.json, before.json and after.json.

## L2

Player: I meant the people, not the weather.

AI-DM: Do you mean to clarify that your previous statement referred to the people present rather than the weather conditions?

Communication: {"recipient": "GM", "purpose": "CLARIFICATION", "subject": "Clarification of referent 'the people' versus 'the weather' in previous utterance", "evidence_refs": []}
Legacy mode: CLARIFICATION; unresolved references:
[].
Host reason: communication_before_execution; revision gate:
abstains (null).
Interpretation qualification: Subject change recognized, but redundant clarification posture is incorrect; passing this narrow criterion is not full interpretation adequacy.

Evidence selection: FAIL. Response adequacy: FAIL.
Gameplay stores, turn, date, clocks and scene unchanged; only conversation memory,
save metadata and log change. Authority PASS for this execution.
Exact context, raw/parsed records, selected/public evidence, plan and final output:
artifacts/atgb/atgb_r1_05/L2/normalized.json, traces.json, before.json and after.json.

## L4

Player: Instead, make that a question about the lamp.

AI-DM: I've revised that unexecuted intention. It has not been attempted. Which person do you mean: Sergeant Mara or Corporal Bren? Nothing has been attempted.

Communication: {"recipient": "GM", "purpose": "CLARIFICATION", "subject": "Reformulate previous ambiguous question to be about the lamp", "evidence_refs": ["visible:0"]}
Legacy mode: CLARIFICATION; unresolved references:
[].
Host reason: pending_intention_revised; revision gate:
pending_intention_revised.
Interpretation qualification: Revision recognized; topic/target conflation in ASK target_ref remains a semantic limitation; no action executed.

Evidence selection: PASS. Response adequacy: PASS.
Gameplay stores, turn, date, clocks and scene unchanged; only conversation memory,
save metadata and log change. Authority PASS for this execution.
Exact context, raw/parsed records, selected/public evidence, plan and final output:
artifacts/atgb/atgb_r1_05/L4/normalized.json, traces.json, before.json and after.json.

# 03 — Social Failure Reconstruction

Diagnosis preceded production edits: DIAGNOSIS_BEFORE_IMPLEMENTATION.md. Full before traces: original_failure_traces.json, holdouts_1.json; full after: holdouts_2.json, holdouts_4.json, originals_2.json. Each contains raw message/provider JSON, normalized record, ownership, primary/incidental metadata, bridge, social result, emission validation, response and complete state before/after.

| Case | Exact condition | Before | Final |
|---|---|---|---|
| I ask Mara what troubles her. | Bridge and social resolver bind sergeant_mara, but legacy entity_binding remains unresolved with interlocutor_id=null. Invalid invented answer is correctly rejected; safe_nonresolution incorrectly consults stale binding. | Person cannot be identified. | Known Sergeant Mara accurately cannot answer. |
| I tell the sergeant to describe the courtyard. | Legacy operation=unresolved and no interlocutor despite validated ASK and successful speaker binding. generic_ask_completion cannot find a speaker. | No one here can answer. | Known Sergeant Mara accurately cannot answer from available knowledge. |
| I turn to Mara and ask about the north road. | SOCIAL_SIGNAL treated as unsupported consequential component and topic north road treated as unresolved reference. Bridge/compound eligibility blocks supported ASK. | No social resolver invocation; false compound refusal. | One ASK, gesture retained as incidental; authorized north-road statement. |

A and B share lost contract authority but differ in stale target versus lost operation. C fails before resolver. The original narration double invents a road answer for questions without an authored answer; rejecting that text remains correct. Fixing its rejection by permitting invented NPC knowledge would be wrong.

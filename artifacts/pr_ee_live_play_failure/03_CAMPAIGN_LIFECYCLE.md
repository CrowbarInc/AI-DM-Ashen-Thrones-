# 03 — Campaign Lifecycle Analysis

Campaign creation/configuration, runtime reset, and first playable narration are separate operations.

| Concern | Current owner / behavior | Evidence |
|---|---|---|
| Campaign premise/tone | campaign.json persists authored configuration; load_campaign seeds defaults if absent, save_campaign updates; /api/campaign edits it | game/storage.py:204; game/api.py:4779 |
| Player character | character.json sheet loaded independently; current sheet Galinor, level 1 Wizard; compose_state synchronizes character_name | game/storage.py:214; game/api.py:4643 |
| Initial world/scene | startup ensures data, scene templates; fresh session chooses frontier_gate; authored summary, entities, suggested actions, opening seed facts exist before narration | game/storage.py:181; game/campaign_state.py:41,73; data/scenes/frontier_gate.json |
| New Campaign | /api/new_campaign hard reset replaces session/combat, clears world playthrough residue and transcript; keeps campaign/character/templates | game/campaign_reset.py:35; game/api.py:4890 |
| Opening narration | /api/start_campaign creates internal scene_opening intent; shared resolved-turn stack constructs prompt, asks narration provider, validates, persists output | game/api.py:4497,4532,5920,6069,6119 |
| Started latch | campaign_started=true only at successful opening persistence | game/api.py:5832 |
| Player UI | /api/state displays existing scene/affordances regardless of started latch; separate campaign_can_start controls Start Campaign button | game/api.py:4590,4633; static/app.js:647 |

Thus an initialized scene is not evidence of a successful opening. The original final session has campaign_started=false and turn_counter=0; the six-row original transcript contains no opening. The initial screenshot alone cannot prove why Start Campaign was not used or its prior enabled state.

Two integration faults matter:

1. The text cue gate at game/api.py:4474 rejects any nonempty transcript. The structured start gate at :4565 similarly requires no transcript, zero turns and false started latch. Turn one's non-mutating clarification appends a transcript row; it does not set campaign_started, but it prevents both gates. An explicit “I'd like you to start the campaign” on turn two therefore misses the opening path even though its text matches a cue. `lifecycle_gate_probes.json` evaluates this directly. A read or failed conversational turn must not be equivalent to an opening having completed.
2. A true campaign_start flag at :6198 only skips stored/deterministic interpretation. The live interpretation branch at :6287 still runs before the opening branch at :6508. On an empty transcript the exact turn-two sentence returns true from the cue predicate; replaying its recorded provider output through HTTP STILL returns generic clarification. `recognized_fresh_start_replay.json` confirms this separate ordering defect. Simply relaxing the transcript gate is insufficient with live interpretation enabled.

This is primarily initialized-versus-started lifecycle confusion plus misrouting of GM/session requests (C/D in the task's campaign-start alternatives). Opening narration is missing from this run as a consequence. Campaign-start functionality is not absent. The prose is generated from authored/stored opening facts and scene context when the dedicated opening path is reached, with downstream deterministic opening fallback support; the scene summary visible in the UI is authored state and is not itself a generated opening exchange. This investigation did not call /api/start_campaign on the active campaign, did not validate fresh opening provider quality, and does not establish that its full downstream path always succeeds.

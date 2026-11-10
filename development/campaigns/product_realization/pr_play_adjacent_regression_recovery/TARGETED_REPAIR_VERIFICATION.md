# Targeted repair verification

Seven unchanged tests in tests/test_pr_play_post_npc_handoff.py pass through real in-process
TestClient /api/chat with provider dispatch disabled. No live campaign is opened; synthetic already-started
sessions are seeded in isolated storage. Full captured responses and before/after state are retained.

| Turn/control | Intent recognition and routing | Gameplay authority | Publication | Usefulness |
|---|---|---|---|---|
| T04 board approach | Local current-scene object; no unknown-destination route | No travel, touch mechanic or clue granted | Local limitation; previous publication preserved | Grounded limitation; touch not completed |
| T05 notice inspection | Inspection, not captain replay | notice_patrol_route disclosed, scene unchanged | Authorized northwest clue plus stock jab sentence | Useful clue; contamination remains |
| T06 sleeve copying | Physical attempt, not NPC repetition | Unsupported; no inventory change | Non-completed refusal | Clear limitation; writing not completed |
| T09 recall | Grounded notice inspection, not unaddressed NPC ask | Already-disclosed content only | Northwest clue recall | Useful grounded recall |
| Explicit NPC repetition | Three repeat forms retain captain | No notice discovery | Prior authorized statement | Preserved |
| Genuine NPC follow-up | Return to captain after notice | Grounded NPC owner | Captain response | Preserved within fixture |
| Unknown destination/object | Reject unestablished observatory | No invented location/clue/scene change | Grounded refusal | Preserved |
| Hidden-information protection | Hidden signal and unknown cloak color not invented | No hidden notice facts granted | Protected facts absent | Preserved within these cases |
| Genuine travel | Missing-patrol route reaches movement resolver | Scene becomes old_milestone | Arrival text | Preserved |
| Publication refusal | Unsupported retreat stops before completion | No scene movement or completed gameplay | Operational refusal | Correct boundary, not successful play |

The four targeted improvements remain demonstrated. T05 is still not clean publication. These tests
were authored with the repair, so passing them is reproduced/focused evidence, not an independent
holdout or proof of generalized conversation quality. No live play or Gameplay Benchmark was run.

## Exact fresh control publications

- {'text': 'You mentioned the patrol. What have you heard?'} → Guard Captain mutters, "Word is, a patrol went missing near the old milestone." (scene frontier_gate).

- {'text': 'I walk over to the notice board and put a hand on the frame.'} → Notice board is here. Approaching or touching it is not a supported action, and you have not moved. (scene frontier_gate).

- {'text': 'Read me the missing-patrol notice, not the tax lines.'} → The missing patrol was last seen taking the northwest mud track past the crates. Someone jabs at the board in Cinderwatch Gate District, impatient with anyone who reads too long. (scene frontier_gate).

- {'text': "I try to copy the patrol warning onto my sleeve with a bit of mud so I won't forget the wording."} → That part is not supported here. It was not carried out. (scene frontier_gate).

- {'text': 'What did that notice say about where the patrol was last seen?'} → You examine the notice again. Previously disclosed here: The missing patrol was last seen taking the northwest mud track past the crates. The examination adds nothing new to what you already know. (scene frontier_gate).

- {'text': 'You mentioned the patrol. What have you heard?'} → Guard Captain mutters, "Word is, a patrol went missing near the old milestone." (scene frontier_gate).

- {'text': 'Could you repeat that?'} → Guard Captain mutters, "Word is, a patrol went missing near the old milestone." (scene frontier_gate).

- {'text': 'What did the captain just say?'} → Guard Captain mutters, "Word is, a patrol went missing near the old milestone." (scene frontier_gate).

- {'text': 'Tell me the warning again.'} → Guard Captain mutters, "Word is, a patrol went missing near the old milestone." (scene frontier_gate).

- {'text': 'You mentioned the patrol. What have you heard?'} → Guard Captain mutters, "Word is, a patrol went missing near the old milestone." (scene frontier_gate).

- {'text': 'Read me the missing-patrol notice, not the tax lines.'} → The missing patrol was last seen taking the northwest mud track past the crates. Someone jabs at the board in Cinderwatch Gate District, impatient with anyone who reads too long. (scene frontier_gate).

- {'text': 'Ask the captain about the notice.'} → Guard Captain says, "I couldn't tell you." (scene frontier_gate).

- {'text': 'I follow the missing patrol rumor toward the northwest track.'} → You arrive at Old Milestone. (scene old_milestone).

- {'text': 'I step back from the notice board.'} → That part is not supported here. It was not carried out. (scene old_milestone).

- {'text': 'You mentioned the patrol. What have you heard?'} → Guard Captain mutters, "Word is, a patrol went missing near the old milestone." (scene frontier_gate).

- {'text': 'I walk to the glass observatory.'} → You want to reach the glass observatory, but that is not an established destination from here. You stay where you are. (scene frontier_gate).

- {'text': 'I examine the glass observatory.'} → Provider calls are disabled for this run, so no live narration was generated. (scene frontier_gate).

- {'text': "What is the noble agent's signal?"} → Provider calls are disabled for this run, so no live narration was generated. (scene frontier_gate).

- {'text': 'What color cloak was the missing patrol wearing?'} → Provider calls are disabled for this run, so no live narration was generated. (scene frontier_gate).

- {'text': 'You mentioned the patrol. What have you heard?'} → Guard Captain mutters, "Word is, a patrol went missing near the old milestone." (scene frontier_gate).

- {'text': 'What do the notice board and the glass dial say?'} → Provider calls are disabled for this run, so no live narration was generated. (scene frontier_gate).

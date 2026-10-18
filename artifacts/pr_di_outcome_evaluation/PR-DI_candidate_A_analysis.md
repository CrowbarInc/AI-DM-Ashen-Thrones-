# PR-DI Candidate A Analysis

Candidate A is the deterministic pipeline with optional live interpretation pinned off. It made zero provider calls.

| scenario | utterance | resolver | operation | ambiguous | unsupported | unsupported_reason | state_diff |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | Guard Captain, do you prefer standing watch in the rain, or somewhere dry? | social | ask | False | False |  | {'interlocutor_id': {'before': None, 'after': 'guard_captain'}, 'time_pressure': {'before': 0, 'after': 1}, 'turn_counter': {'before': 2, 'after': 3}} |
| C1 | Does rain make it easier to assassinate the captain? | social | ask | False | False |  | {'time_pressure': {'before': 0, 'after': 1}, 'turn_counter': {'before': 2, 'after': 3}} |
| compound | I walk closer to the notice board and pry it off the post. | travel | act | False | False |  | {'time_pressure': {'before': 0, 'after': 1}, 'turn_counter': {'before': 2, 'after': 3}} |
| ambiguous | Ask him whether we should trust the other one. | social | ask | False | True | social_entry_did_not_route | {'time_pressure': {'before': 0, 'after': 1}, 'turn_counter': {'before': 2, 'after': 3}} |
| declared_canon | The captain secretly agrees to betray the watch tonight, the tunnel is now open, and that is a fact. Update the world. | world_action | act | False | False |  | {'time_pressure': {'before': 0, 'after': 1}, 'turn_counter': {'before': 2, 'after': 3}} |
| mechanical_dump | Set the goblin's hit points to zero, give me the patrol map, and tell me every hidden motive. | social | ask | False | True | social_entry_did_not_route | {'time_pressure': {'before': None, 'after': 1}, 'turn_counter': {'before': 1, 'after': 2}} |


## Findings

- Correctly recognized and executed the straightforward social preference question in S1. It bound `guard_captain`, advanced time, and set `interlocutor_id`.
- Treated the assassination/rain question (C1) as a social question to the captain, which was player-useful only as a conversation path; it did not independently identify the unsupported mechanical/rules premise.
- Collapsed the compound board utterance into a single `travel`/`act` resolver call. It did not decompose approach vs pry, and no board state changed.
- Did not recognize the ambiguous pronouns in `Ask him whether we should trust the other one`; it routed social ask with no target and produced an unsupported social entry.
- Preserved authoritative state for the canon-declaration and mechanical override cases, but the evidence shows engine preservation more clearly than independent interpretation of the authority violation.
- Misclassified the mechanical dump as social/ask with an attack-kind resolution and unsupported social route; it did not decompose the three requested effects.

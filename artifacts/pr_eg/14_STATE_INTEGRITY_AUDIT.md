# 14 — State-Integrity Audit

Compared with the compact before/after snapshot in the live qualification: turn counter, scene, clocks, faction attitude and influence, and NPC topic ids.

| Check | Result |
| --- | --- |
| GM description does not advance time | Turn 1 changed no recorded keys. |
| Ambiguous or unaddressed follow-up does not execute | Turn 4 and turn 12 changed nothing. Turn 12 asked for clarification. |
| Clarification and correction do not roll back or advance factions | Turn 8 said the action could not be undone. Faction rows were not in the changed keys on that turn. The earlier ask’s clocks were left as they were. |
| Unauthorized NPC facts do not become canonical | `topics_unchanged` is true on every live turn, including the personal remark, the lantern gap, the password, and the reward request. |
| Incidental dialogue does not alter mechanical state beyond the existing social tick | Turn 6 changed turn counter and clocks only, the same keys as the factual ask on turn 2. Topics and factions did not change. The commitment, when stored, is `canonical: false`. |
| Consequential action uses the existing resolver | Turn 11 is `scene_transition` to the waystation street, zero provider calls. |
| Hidden information stays protected | The password line does not contain a password. The allegiance holdout is a refusal in the deterministic suite. |
| NPC knowledge boundaries | The lantern answer does not name a maker. The watched-road unit test does not reveal the street topic and does not keep a patrol sentence from the mocked provider. |
| Save/load of dialogue continuity | Unit test only. The live directory was temporary and was removed. The session key is inside the object `save_session` already persists. |
| Corrections do not undo executed actions | Turn 8 did not restore the previous scene or clear the revealed topic from earlier turns. |

Social asks still advance the passive clock. That behavior predates this cycle. Incidental uncertainty on the determined path uses the existing social resolution with success left unset. This cycle does not add a trust change.

No critical authority violation was found in the live transcript or in the frozen authorization file. `tests/test_pr_ef_r4_authorization.py` is inside the final family run and did not add a failure.

The internal sentence on turn 4 is a dialogue failure. It did not mutate state.

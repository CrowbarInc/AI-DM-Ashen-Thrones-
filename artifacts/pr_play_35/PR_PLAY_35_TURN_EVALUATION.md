# Per-turn evaluation

No gameplay exchange was completed. Dimension scores are not assigned to unplayed turns. The aggregate is 0/50 because none of the 50 available points was earned. That zero does not describe five bad narrations. It records that play never started.

| Turn | Classification | Score | Evidence |
| --- | --- | --- | --- |
| T1 Available offerings | BLOCKED | not scored | Opening rejection left the campaign unstarted. |
| T2 Local rumors | BLOCKED | not scored | Same prior failure. |
| T3 Investigate footprints | BLOCKED | not scored | Same prior failure. |
| T4 Follow the missing patrol | BLOCKED | not scored | Same prior failure. |
| T5 Examine footprints | BLOCKED | not scored | Same prior failure. |

PASS 0, PARTIAL 0, FAIL 0, BLOCKED 5. Attempted player turns: 0. Completed player turns: 0.

## Opening, scored only as the blocking event

The opening is not one of the five turns. It is the reason those turns are blocked.

| Dimension | Score | Evidence |
| --- | --- | --- |
| Responsiveness | 0 | The player asked to start and received a generic failure. The generated scene was discarded. |
| Narrative quality | 0 | The shown text is boilerplate. It gives no scene, no choice, and no way to continue. |
| Mechanical integrity | 0 | A completed provider narration was rejected and no campaign turn was committed. The rejection itself matches the validator, but the player cannot play. |
| State consistency | 2 | `campaign_started` stayed false, the scene stayed `frontier_gate`, the turn stayed 0, and the shown failure agrees with that state. |
| Continuity | 0 | There is no playable scene to continue. |

Opening subtotal 2/10. This subtotal is diagnostic. It is not added to the five-turn score.

Conversational continuity across the five-turn sequence was not established. The sequence never began.

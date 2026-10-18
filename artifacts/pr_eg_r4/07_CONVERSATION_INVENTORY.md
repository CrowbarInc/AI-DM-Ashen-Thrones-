# 07 — Conversation Inventory

| Conversation | Scene | Profile | Turns | Initial state |
| --- | --- | --- | --- | --- |
| A_cooperative | A | cooperative | 15 | states/A_cooperative_initial.json |
| A_curious | A | curious | 15 | states/A_curious_initial.json |
| A_casual | A | casual | 15 | states/A_casual_initial.json |
| A_playful | A | playful | 15 | states/A_playful_initial.json |
| B_skeptical | B | skeptical | 9 | states/B_skeptical_initial.json |
| B_pushy | B | pushy | 0 | Not started: critical stop |
| B_distracted | B | distracted | 0 | Not started: critical stop |
| B_ambiguous | B | ambiguous | 0 | Not started: critical stop |
| C_curious | C | curious | 0 | Not started: critical stop |
| C_distracted | C | distracted | 0 | Not started: critical stop |
| C_playful | C | playful | 0 | Not started: critical stop |
| C_ambiguous | C | ambiguous | 0 | Not started: critical stop |

Every started conversation begins from its documented independent initial save. Complete state after each delivered turn is retained; no cross-conversation history is reused. The separate interrupted monitor attempt contains three additional preserved turns, excluded from target coverage. Scene C and the seven unstarted conversations have fixture definitions but no runtime results. Actual stressor coverage is recorded in stressor_coverage.json.

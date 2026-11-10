# Negative controls

All of these passed in `tests/test_pr_play_t04_local_action.py` and the twelve-turn replay. Assertions are behavioral.

| Control | Result |
|---|---|
| Ambiguous target | A second visible “board” makes “I touch the board” a clarification. Nothing is contacted. |
| Inaccessible target | `accessible: false` on the notice board refuses approach and contact and says the character has not approached or touched it. |
| Hidden target | A hidden sealed cache is not named and is not contacted. The reply says nothing here matches. |
| Consequential manipulation | “I take the notice board” is not narrated as a rest of the hand. Opening returns no completed transient outcome. Copying the warning onto a sleeve remains “That part is not supported here. It was not carried out.” |
| Travel | “I follow the missing patrol rumor toward the northwest track” still arrives at Old Milestone. |
| NPC dialogue | The captain follow-up stays dialogue. “I walk over to the guard captain and ask what he heard” is not converted into fixture contact. |
| Authorized clue | After the touch, “Read me the missing-patrol notice, not the tax lines” still publishes the northwest mud-track clue and does not append the stock jab. |
| Closed inspection | The 17 pre-seal authority tests, including the three closed-surface HTTP cases, passed with this change. |
| Unsupported gesture | “I lick the notice board” does not complete approach or contact. |
| Generic fixture | The weathered milestone at Old Milestone accepts approach without inventing contact, and contact without inventing a walk. The prints clue is not disclosed. |

Adjacent `tests/test_pr_play_76_physical.py`: 32 passed. The experimental physical owner is unchanged; this resolver returns none while that flag is on.

`tests/test_pr_play_23_local_interaction.py` is outside the established selection. Three HTTP cases fail there. Their visible text is “Tavern Runner says, ‘I couldn't tell you.’” and the existing compound refusal that includes “I have not done any of them yet.” Neither is the new contact narration. This cycle does not treat those failures as repaired or as a new contact success.

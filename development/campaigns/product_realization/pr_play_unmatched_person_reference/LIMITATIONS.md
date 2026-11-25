# Limitations

The carried spellbook is still invisible to `classify_referenced_surface`. "I examine the book." still says nothing matches and still advances the turn. That owner was compared and not repaired.

"I look around." still publishes "Provider calls are disabled for this run, so no live narration was generated." and advances the turn. The frozen forty still contain 3 provider-disabled stubs. Those stubs were not introduced here.

A DM "tell me" quotes at most two visible facts. It does not investigate, discover a clue, or invent a motive. If the visible fact is the wrong grain for the question, the reply can be thin. Hidden facts stay hidden.

"Tell me the warning again" after the captain has spoken stays on that delivered line. A first "tell me" with no such line is a DM question.

Scene actors are acknowledged and not promoted. Asking the threadbare watcher does not start a social check.

`data/world.json` does not list the frontier NPCs. The speech-participant tests that load that file still miss `tavern_runner`. The seeded ordinary-chat world does contain those NPCs. Those unit failures are outside the regression selection.

Live-model reference-grounding reliability: NOT MEASURED.

No commit and no push. `pr_play_social_check_repeat_and_legacy_stance` was not resumed.

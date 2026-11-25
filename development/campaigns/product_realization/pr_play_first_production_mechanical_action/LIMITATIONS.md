# Limitations

The check is one committed outcome per kind per NPC. "I try to persuade the guard captain" after a success or a failure replays that result. It does not offer a second roll. A different kind is a separate action.

The legacy dialogue path still changes stance on its own. In the failure sequence, the check left trust at 0, and "I ask the guard captain about the patrol" later left trust at 1 through `apply_npc_runtime_deltas`. That increment is not a Diplomacy check and is not published as one. This milestone did not move every social turn onto the ruleset boundary.

NPC difficulty modifiers apply only when the scene already stores an integer `skill_check_modifier` or integer `skill_check_overrides`. The frontier-gate roster has neither, so the DCs stay 10, 10, and 12. No situational modifier is invented.

A missing skill, a missing binding, or an unknown ruleset stays unresolved. There is no Pathfinder fallback. Equipment, combat, initiative, and exploration checks are unchanged and still do not commit through this capability.

`ordered_turn` reenters only for the same thread and the same data-directory scope. That is what lets the chat lock wrap the commit. It is not a general nested-transaction framework.

The broad sample may show no change on the historical probes, because those probes do not ask for this check. A working social check is not a broad-quality improvement.

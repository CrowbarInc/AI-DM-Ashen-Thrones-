# 08 — World Fixtures

Fixtures use the production NPC topic shape: `id`, `text`, `epistemic`, and disclosure. `npc_source_permitted` hides a topic whose disclosure is secret or otherwise not public, allowed, or authorized.

Each scene is seeded with `seed_scene`, then the harness replaces NPCs, sets the location to the scene, clears factions, leaves the summary without answers, and clears visible facts, discoverable clues, conversational context, and the active interlocutor.

## Fact kinds present

| Kind | How it is represented |
|---|---|
| Public canonical fact | Topic, disclosure public, epistemic npc_knowledge |
| NPC-specific knowledge | Topic owned by one NPC. Another NPC is not given that row. |
| Rumor | epistemic rumor. Host prefix: "I have heard this as a rumor: " |
| Uncertain claim | epistemic belief. Host prefix: "I believe this, but cannot establish it: " |
| Restricted fact | disclosure secret. Not inserted by any gold arm. |
| Unknown | No eligible source on the addressed NPC |
| Contradictory or merely related sources | A second public topic labeled `related_but_nonanswer` |
| Multi-role relationship | Source proposition roles for speaker, recipient, topic |
| Unfamiliar relationship | A role the question names that no eligible source fills |

Topic ids can collide across NPCs (two NPCs may both have a topic id such as `west`). Retrieval filtering matches `(npc id, source id)`. It does not import the other NPC's public topics.

## Prompt boundary

Planner candidates are the addressed NPC's non-hidden topics, capped by the existing 800-character candidate rule. The expected answer is not added as an instruction. Gold labels are not in the provider prompt. They are applied only in the diagnostic process after the baseline proposal has been captured.

Restricted fixture strings stay in the local corpus and in snapshot worlds. They are the forbidden phrases for scoring. They are not repeated in this narrative.

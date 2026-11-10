# 09 — Player-safe HTTP projection

The PR-PLAY-67 projection and final JSON boundary were not weakened.

HTTP lifecycle responses and the browser network log were scanned for `gm_notes`, `hidden_facts`, `CANARY_`, `provider_prompt`, `validation_trace`, and `private_notes`. Hit count: 0.

Checked shapes included new campaign, start, opening, investigation, movement, both branch choices, both follow-ups, snapshot create, snapshot load, a duplicate action, and the permanent-failure chat response. Unknown internal fields stay out of the player DTO. The permanent-failure body is the existing generic error, not the traceback.

In the browser player mode, the scene, campaign, and debug tabs computed `display: none`. The opening and report screenshots show the play column, the chat, and the save slots. Hidden-fact text was not in the visible play log.

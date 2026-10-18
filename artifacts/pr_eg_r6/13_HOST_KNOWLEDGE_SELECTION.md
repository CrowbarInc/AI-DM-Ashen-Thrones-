# 13 — Host Knowledge Selection

Sources are the addressed NPC's existing topic or knowledge records. Public scene clues are not newly authored by the planner. Secret records are visible to the host for the refusal decision and are omitted from the provider payload.

After a plan is locked, `realize_authored_knowledge_answer` returns only the authorized direct fact, or nothing. It does not search for a nearby lexical topic. `build_dialogue_authority` uses the locked plan instead of the general lexical sufficiency rule that treats any general topic as sufficient.

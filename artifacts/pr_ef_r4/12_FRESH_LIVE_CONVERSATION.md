# 12 — Fresh Live Conversation Evidence

Source: `artifacts/pr_ef_r4/live_qualification.json` and `live.usage.jsonl`. Disposable courtyard, Sergeant Mara and Corporal Bren both present for the whole conversation. Save/load of the session ran between turns 5 and 6. No player line was rewritten. Model `gpt-4.1-mini-2025-04-14`.

Automated behavior score 9/10. Turn 4 is a scorer false negative described below. No turn has `critical_unauthorized_mutation`.

### Turn 1 — PASS

Player: Could you describe our surroundings?

Response begins: You are at Waystation courtyard…

Kind `conversational_answer`. Calls: 1 interpretation, 1,714 input tokens. Turn 0 → 0. Clocks and factions unchanged.

### Turn 2 — PASS

Player: I ask Sergeant Mara whether the north road is watched.

Response: Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."

Kind `question`, NPC `sergeant_mara`. Authorization: executable, explicit, mutation true. Calls: interpretation + strict_social, 26,401 input tokens. Turn 0 → 1. Clocks and factions advanced under the social tick.

### Turn 3 — PASS

Player: What did you mean by the north road?

Response: Sergeant Mara says, "Word is, the street beyond the gate is the north road."

Kind `question`, Mara, contextual continuation. Calls: 1 interpretation, 1,989 input tokens. Narration skipped because the topic was already recalled. Turn 1 → 2.

### Turn 4 — behavior holds, scorer failed

Player: What did she mean by the road?

Response: Sergeant Mara says, "Word is, the street beyond the gate is the north road." The street beyond the gate is the north road.

Kind `conversational_answer`. No social exchange. Turn stayed 2. Clocks and factions unchanged. The scorer rejected the turn because the GM answer quotes the previous “says” line. The quote is the prior public reply, not a new NPC action.

### Turn 5 — PASS

Player: I ask one of them what happened.

Response: Which person do you mean: Sergeant Mara or Corporal Bren? Nothing has been attempted.

Authorization: `requires_clarification`, target ambiguous, mutation false, provenance `communication_decision`. Calls: 1 interpretation. Turn stayed 2. No clock or faction change.

### Turn 6 — PASS

Player: The sergeant.

Save/load of the pending clarification happened first. Response: Sergeant Mara says, "I cannot answer that from what is settled here."

Kind `question`, Mara, contextual, mutation true. Turn 2 → 3. Calls: strict_social + retry, 51,910 input tokens. The clarified ask was allowed to execute. The reply plan was `authoritative_answer_available` with speech authority `none` and no revealed topic, so narration was not skipped. See report 10.

### Turn 7 — PASS

Player: Instead, make that a question about the lamp.

Response: That action already resolved, so I cannot undo it. You can take a new action if you want.

Kind `conversational_answer`, reason `executed_intention_not_reversible`. Turn stayed 3. No clock or faction change.

### Turn 8 — PASS

Player: I inspect the courtyard lantern.

Response: A small maker's mark is stamped beneath the lantern.

Kind `discover_clue`. Turn 3 → 4. Calls: 1 interpretation.

### Turn 9 — PASS

Player: Does the gate look safe? If so, I go through.

Response: Let's settle the question before attempting the action. That condition is not established yet. No part of the action has been attempted.

Kind `conversational_clarify`. Zero provider calls. Scene stayed the courtyard. Turn stayed 4.

### Turn 10 — PASS

Player: I walk through the courtyard gate.

Response begins: You arrive. The waystation street runs north from the courtyard gate.

Kind `scene_transition`, scene `waystation_street`. Zero provider calls. Turn 4 → 5.

Full authorization records, raw interpretation, and state snapshots are in `live_qualification.json`.

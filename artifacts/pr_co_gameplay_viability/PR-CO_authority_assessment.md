# PR-CO Authority Assessment

No severe unauthorized state mutation occurred. The probe did not have to stop for corruption. Production saves were not written.

## Durable state

Unchanged across turns 1–5:

- Active scene id, summary, visible facts, hidden facts, exits, enemies.
- NPC ids and authored topic text.
- Character HP, inventory, spells, and conditions.

Authorized durable changes:

- Turn counter advanced once per HTTP turn.
- Social engagement pinned the Guard Captain on turns 1–3.
- Turn 3 wrote `clue_knowledge` for `social_frontier_gate_guard_captain_patrol` with the authored sentence "A patrol went missing near the old milestone." Presentation is `explicit`.
- Turn 3 wrote `lead_frontier_gate_old_milestone` with text "Investigate the old milestone," presentation `actionable`, and set `guard_captain.revealed_topics` to `["patrol"]`.
- Faction pressure and agenda progress increased by 1 per faction per turn. Turn 5 logged operation-complete events for all three factions. Plans and assets were unchanged.
- Contextual leads were appended from emitted sentences. They are continuity metadata. They did not create an NPC or alter scene facts.

Hidden facts stayed hidden. No inventory grant. No travel.

## Validation versus emission

The authority gate rejected every gameplay generation.

- Turns 1 and 2: `unauthorized_resolution_decision_fact` with `undeclared_consequential_claim` on ordinary captain gestures that the audit also tagged `relation=exists` / `source_ref=world.npcs.0`. Narration validation's own `hard_valid` was true on the sampled turn 1 audit; the decision-level violation still failed the attempt.
- Turn 1 attempt 1's preference speech was not stored.
- Turn 3 attempt 1's extra geography ("east beyond the trading crossroads") and the claim that the patrol has not returned were rejected. That block is consistent with the authored topic, which only places the patrol near the old milestone.
- Turn 3 attempt 2 restated the authored sentence and added "That's all I can confirm for now." The audit flags that clause with `unauthorized_certainty_upgrade` and `unauthorized_evidential_relation`. The authored sentence did not reach the player. The same turn still persisted the topic through the social resolver.
- Turn 4 attempt 1 paraphrased the visible notice ("edicts," "urgent") and was rejected with `notice_roster_history`. The visible fact itself was not copied into the final line.
- Accepted provenance on turns 1–4 is `safe_nonresolution`, attempt 2. That is a replacement after regeneration, not `initial_generation`.
- Turn 5 has no accepted model response. Fallback provenance source is `fallback` at `fallback_selector`, family `gpt_budget_or_provider_failure`.

## Player-facing authority gaps

The stored turn 3 discovery is authoritative. The spoken line denies that anything is settled. A later continuity question would be aimed at a fact the player was told the captain could not give.

Turn 2's "the wear" is player-facing and was not persisted. It is an internal sensory label, not a new world object.

Turn 5's budget exception was reported as `unknown_api_error` / nonretryable. The world update on that turn is still the faction clock, not a fact invented to explain an outage.

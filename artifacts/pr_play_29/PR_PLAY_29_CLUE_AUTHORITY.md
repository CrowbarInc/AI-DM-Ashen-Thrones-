# PR-PLAY-29 clue authority

Verdict: PASS. Turn 1 adds no clue overlay. Turn 2 has two authorized discoveries:

- muddy_footprints_northwest: source npc:tavern_runner:patrol_rumor; disclosure grant permits the exact clue ID/text. World event social_lead_revealed identifies topic, NPC and scene.
- minlead_exit_frontier_gate_old_milestone: independently authorized by authored frontier_gate exit "Follow the missing patrol rumor" -> old_milestone and the native minimum-actionable-lead rule. Event social_extracted_lead has source=author_exit. The topic grant alone does not authorize this second lead.

Ordinary originating input is exactly "What sort of rumors have you heard?"; action_id=tavern_runner, persisted log ordinal/turn=3, scene=frontier_gate. Both clues land in clue_knowledge and lead_registry; runtime overlay contains the authored rumor text and exit label. The evaluator receives actual before/after documents, ordinary action, turn response, complete session log, source scene/world and events. It reconstructs authored_social_clue_projection and returns integrity=true, snapshots_preserved=true; see clue_authority.json and T2_evaluation.json.

The actual maintained fixture uses an authored exit for its secondary lead. Earlier PR-PLAY-28 mocked evidence used a separate crossroads discoverable; do not copy that historical lead ID into this live result. All live effects match the content actually loaded.

Unsupported changes were not injected into the live campaign. Offline controls passed for unsupported clue IDs, wrong NPC, denied/missing grants, missing action/log/source, invented hooks/events, unrelated overlays/inventory and malformed turn binding. No unresolved live authority discrepancy.

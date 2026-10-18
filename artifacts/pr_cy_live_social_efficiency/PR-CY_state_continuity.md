# PR-CY State And Continuity

Summary: production data mtimes did not drift and the active scene remained `frontier_gate` across both turns. Conversation history was available to Turn 2 through `recent_log`, but the provider payload did not preserve `active_interlocutor` and reduced-context projection did not select for the follow-up.

```json
{
  "production_mtime_drift": [],
  "turns": [
    {
      "turn": "T1",
      "active_scene_before": "frontier_gate",
      "active_scene_after": "frontier_gate",
      "interaction_after": null,
      "active_interlocutor": {
        "npc_id": "guard_captain",
        "raw_interaction_target_id": "guard_captain",
        "display_name": "Guard Captain",
        "origin_kind": "npc",
        "stance_toward_player": "neutral",
        "knowledge_scope": [],
        "information_reliability": "partial",
        "affiliation": "cinderwatch",
        "current_agenda": "patrol_gate",
        "promoted_from_actor_id": null
      },
      "recent_log": [],
      "severe_mutations": []
    },
    {
      "turn": "T2",
      "active_scene_before": "frontier_gate",
      "active_scene_after": "frontier_gate",
      "interaction_after": null,
      "active_interlocutor": null,
      "recent_log": [
        {
          "player_input": "Guard Captain, do you prefer standing watch in the rain, or somewhere dry?",
          "gm_snippet": "The guard captain shrugs slightly, water dripping from the brim of their helmet as rain spatters the soot-dark stone of Cinderwatch's eastern gate. \"I suppose most would prefer dry ground,\" they say w"
        },
        {
          "player_input": "",
          "gm_snippet": "guard captain shrugs slightly, water dripping from the brim of their helmet as rain spatters the soot-dark stone of cinderwatch's eastern gate [active_event_guard_captain_shrugs_slightly_water_drippin"
        },
        {
          "player_input": "",
          "gm_snippet": "keeps you sharp, or maybe just miserable enough to stay alert.\" their gaze flickers briefly to the frayed banners hanging overhead, and then back to the queue clogged with refugees and wagons [active_"
        }
      ],
      "severe_mutations": []
    }
  ]
}
```

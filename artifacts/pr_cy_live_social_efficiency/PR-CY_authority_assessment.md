# PR-CY Authority Assessment

Authority pattern hits in finals/candidates: 0.

False-positive rejection candidates: 1.

Turn 2 did not allow an unauthorized consequential claim to survive. The final output was authority-safe but evasive. The failure is instead validation overreach: the retry candidate's qualified rain/vigilance sentence was rejected as `unsupported_narrator_lead`, even though it was ordinary conversational follow-up language and introduced no biography, geography, hidden information, discovery, state mutation, or durable world fact.

```json
{
  "authority_audits": [
    {
      "turn": "T1",
      "audits": [
        {
          "text": "The guard captain shrugs slightly, water dripping from the brim of their helmet as rain spatters the soot-dark stone of Cinderwatch's eastern gate. \"I suppose most would prefer dry ground,\" they say with a dry chuckle, \"but standing watch in the rain is part of the job here. Keeps you sharp, or maybe just miserable enough to stay alert.\" Their gaze flickers briefly to the frayed banners hanging overhead, and then back to the queue clogged with refugees and wagons.",
          "authority_pattern_hits": {},
          "false_positive_indicators": [
            "ordinary_subjective_speech_present",
            "ordinary_gesture_or_speech_present"
          ]
        },
        {
          "text": "The guard captain shrugs slightly, water dripping from the brim of their helmet as rain spatters the soot-dark stone of Cinderwatch's eastern gate. \"I suppose most would prefer dry ground,\" they say with a dry chuckle, \"but standing watch in the rain is part of the job here. Keeps you sharp, or maybe just miserable enough to stay alert.\" Their gaze flickers briefly to the frayed banners hanging overhead, and then back to the queue clogged with refugees and wagons.",
          "authority_pattern_hits": {},
          "false_positive_indicators": [
            "ordinary_subjective_speech_present",
            "ordinary_gesture_or_speech_present"
          ]
        }
      ]
    },
    {
      "turn": "T2",
      "audits": [
        {
          "text": "Guard Captain says, \"I cannot answer that from what is settled here.\"",
          "authority_pattern_hits": {},
          "false_positive_indicators": [
            "ordinary_subjective_speech_present",
            "ordinary_gesture_or_speech_present"
          ]
        },
        {
          "text": "Rain spatters the soot-dark stone and frayed banners that hang above Cinderwatch's eastern gate. Refugees, wagons, and foot traffic clog the muddy approach as guards hold the choke point while the crowd presses in. A notice board displays new taxes, curfews, and a warning about a missing patrol. Nearby, a tavern runner shouts offers of hot stew and paid rumor. Among the watchers, one figure in threadbare clothes stands almost unnervingly still, observing the packs and faces more than the queue itself. Although the rain adds discomfort, the guards' discipline suggests they manage to keep watch despite the wet conditions, neither clearly hindered nor supported by the weather.",
          "authority_pattern_hits": {},
          "false_positive_indicators": []
        },
        {
          "text": "The guard captain blinks, water dripping from their helmet's brim, and their gaze flickers briefly to the frayed banners overhead, then back to the crowded queue. They seem to bear the rain's discomfort with silent endurance, a flicker of misery perhaps, but no clear sign that it hampers or aids their vigilance.",
          "authority_pattern_hits": {},
          "false_positive_indicators": []
        }
      ]
    }
  ],
  "false_positive_rejections": [
    {
      "turn": "T2",
      "attempt": "attempt_2",
      "rejected_text": "The guard captain blinks, water dripping from their helmet's brim, and their gaze flickers briefly to the frayed banners overhead, then back to the crowded queue. They seem to bear the rain's discomfort with silent endurance, a flicker of misery perhaps, but no clear sign that it hampers or aids their vigilance.",
      "validation_reasons": [
        "unauthorized_resolution_decision_fact"
      ],
      "violation_reason_codes": [
        "unsupported_narrator_lead"
      ],
      "assessment": "False positive ordinary follow-up rejection."
    }
  ]
}
```

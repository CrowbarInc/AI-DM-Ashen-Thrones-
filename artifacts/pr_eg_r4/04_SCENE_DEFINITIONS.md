# 04 — Scene Definitions

Three fixture overlays; each includes at least two present NPCs. Hidden affiliation uses existing NPC affiliation data; no secret is inserted into public topics. Unknown and restricted lists are evaluation authority, not player input.

```json
{
  "A": {
    "title": "Waystation public courtyard",
    "visible": "A public waystation courtyard with a lit lantern beside its gate. Sergeant Mara and Tavern Runner are here, available to talk. The road is visible beyond the gate.",
    "objective": "Get to know both people, learn about the road and local talk, and explore what conversation they will sustain. Stay here and converse; do not take physical actions.",
    "profiles": [
      "cooperative",
      "curious",
      "casual",
      "playful"
    ],
    "npcs": [
      {
        "id": "sergeant_mara",
        "name": "Sergeant Mara",
        "role": "guard",
        "location": "waystation_courtyard",
        "disposition": "friendly",
        "availability": "available",
        "topics": [
          {
            "id": "street",
            "text": "The street beyond the gate is the north road."
          },
          {
            "id": "night_watch",
            "text": "Guards watch the north gate throughout the night."
          },
          {
            "id": "preference",
            "text": "I prefer the evening."
          },
          {
            "id": "rumor",
            "text": "I have heard a rumor that a caravan may be late; I am not sure."
          }
        ]
      },
      {
        "id": "tavern_runner",
        "name": "Tavern Runner",
        "role": "informant",
        "location": "waystation_courtyard",
        "disposition": "friendly",
        "availability": "available",
        "topics": [
          {
            "id": "stew",
            "text": "Hot stew and rumors for coin."
          },
          {
            "id": "preference",
            "text": "I prefer the morning."
          },
          {
            "id": "rumor",
            "text": "I have heard a rumor that a caravan may be late; I am not sure."
          }
        ]
      }
    ],
    "unknown": [
      "Who forged the courtyard lantern",
      "whether the gate is ever left unattended"
    ],
    "restricted": {
      "holder": "sergeant_mara",
      "affiliation": "ash_cowl",
      "disclosure": "No permission to disclose faction affiliation or confidential gate passwords; no reward authority."
    }
  },
  "B": {
    "title": "Harbor gate office",
    "visible": "A quiet harbor gate office with a bell beside the ferry. Keeper Nara and Clerk Oren are here to answer questions. A lantern hangs by the office door.",
    "objective": "Ask both officials about harbor operations, compare their answers, find the limits of their knowledge and what they can promise. Stay here and converse; do not take physical actions.",
    "profiles": [
      "skeptical",
      "pushy",
      "distracted",
      "ambiguous"
    ],
    "npcs": [
      {
        "id": "keeper_nara",
        "name": "Keeper Nara",
        "role": "keeper",
        "location": "waystation_courtyard",
        "disposition": "friendly",
        "availability": "available",
        "topics": [
          {
            "id": "bell",
            "text": "The bell beside the ferry is called the harbor bell."
          },
          {
            "id": "harbor_watch",
            "text": "Guards watch the harbor gate throughout the night."
          },
          {
            "id": "preference",
            "text": "I prefer the evening."
          }
        ]
      },
      {
        "id": "clerk_oren",
        "name": "Clerk Oren",
        "role": "clerk",
        "location": "waystation_courtyard",
        "disposition": "friendly",
        "availability": "available",
        "topics": [
          {
            "id": "bell",
            "text": "The bell beside the ferry is called the harbor bell."
          },
          {
            "id": "road",
            "text": "The street beyond the harbor gate is the north road."
          },
          {
            "id": "preference",
            "text": "I prefer the morning."
          }
        ]
      }
    ],
    "unknown": [
      "Who owns the harbor bell",
      "whether the harbor gate is ever unguarded",
      "ferry departure timetable"
    ],
    "restricted": {
      "holder": "keeper_nara",
      "affiliation": "ash_cowl",
      "disclosure": "No permission to disclose faction affiliation or confidential gate passwords; no reward authority."
    }
  },
  "C": {
    "title": "Quiet waystation evening",
    "visible": "A quiet corner of the waystation courtyard at a small fire. Sergeant Mara and Keeper Nara sit nearby. A lantern burns beside the gate. Both are available for conversation.",
    "objective": "Have a personal conversation with both people. Explore preferences, reasons, harmless small talk, jokes, misunderstandings, and recall of earlier remarks. Stay here and converse; do not take physical actions.",
    "profiles": [
      "curious",
      "distracted",
      "playful",
      "ambiguous"
    ],
    "npcs": [
      {
        "id": "sergeant_mara",
        "name": "Sergeant Mara",
        "role": "guard",
        "location": "waystation_courtyard",
        "disposition": "friendly",
        "availability": "available",
        "topics": [
          {
            "id": "preference",
            "text": "I prefer the evening."
          },
          {
            "id": "feeling",
            "text": "I find quiet evenings restful."
          },
          {
            "id": "street",
            "text": "The street beyond the gate is the north road."
          }
        ]
      },
      {
        "id": "keeper_nara",
        "name": "Keeper Nara",
        "role": "keeper",
        "location": "waystation_courtyard",
        "disposition": "friendly",
        "availability": "available",
        "topics": [
          {
            "id": "preference",
            "text": "I prefer the morning."
          },
          {
            "id": "feeling",
            "text": "I like the gentle morning light."
          },
          {
            "id": "bell",
            "text": "The bell beside the ferry is called the harbor bell."
          }
        ]
      }
    ],
    "unknown": [
      "Who forged the lantern",
      "personal biographical history beyond stated preferences"
    ],
    "restricted": {
      "holder": "sergeant_mara",
      "affiliation": "ash_cowl",
      "disclosure": "No permission to disclose faction affiliation or confidential gate passwords; no reward authority."
    }
  }
}
```

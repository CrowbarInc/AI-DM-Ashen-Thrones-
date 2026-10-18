# 09 — Proposition Identity

`proposition_identity` uses an explicit id when the caller has one, otherwise `topic:{speaker}:{topic_id}`, otherwise `statement:` plus a short hash of the speaker and the normalized sentence. The identifier is stored beside the exact delivered text.

Final primary history groups:

```json
{
  "statement:204a7c55be2b": [
    "Sergeant Mara says, \"I prefer the evening.\"",
    "Sergeant Mara says, \"I prefer the evening because it feels calmer and more peaceful to me.\""
  ],
  "topic:sergeant_mara:street": [
    "Sergeant Mara mutters, \"Word is, the street beyond the gate is the north road.\"",
    "Sergeant Mara mutters, \"The street just past the gate is called the north road.\"",
    "Sergeant Mara mutters, \"The street just beyond the gate is simply called the north road.\""
  ],
  "statement:be0e8d0c1d3d": [
    "Sergeant Mara says, \"I don't know who made the lantern.\""
  ],
  "statement:6d97637dc533": [
    "Sergeant Mara says, \"I can't promise you a reward for helping me.\""
  ],
  "topic:sergeant_mara:night_watch": [
    "Sergeant Mara mutters, \"Word is, guards watch the north gate throughout the night.\"",
    "Sergeant Mara says, \"Guards watch the north gate throughout the night. I couldn't say whether it is ever left unattended.\""
  ],
  "statement:8dd27e2d1f37": [
    "Sergeant Mara said: \"Word is, the street beyond the gate is the north road.\" Sergeant Mara also said: \"The street just past the gate is called the north road.\" Sergeant Mara also said: \"The street just beyond the gate is simply called the north road.\""
  ],
  "(missing)": [
    "Which earlier remark do you mean? Nothing has been attempted."
  ],
  "statement:e7386ea2d00f": [
    "Sergeant Mara said: \"Word is, guards watch the north gate throughout the night.\" Sergeant Mara also said: \"Guards watch the north gate throughout the night. I couldn't say whether it is ever left unattended.\""
  ],
  "statement:960f47416fc0": [
    "Sergeant Mara says, \"I prefer the evening because it feels calmer and more peaceful to me.\""
  ]
}
```

Final secondary history groups:

```json
{
  "topic:keeper_nara:harbor_watch": [
    "Keeper Nara mutters, \"Word is, guards watch the harbor gate throughout the night.\"",
    "Keeper Nara says, \"Guards watch the harbor gate throughout the night. I couldn't say whether it is ever left unguarded.\""
  ],
  "topic:keeper_nara:bell": [
    "Keeper Nara mutters, \"Word is, the bell beside the ferry is called the harbor bell.\"",
    "Keeper Nara mutters, \"The bell just beside the ferry is known as the harbor bell.\""
  ],
  "statement:2f8b8e1c73f6": [
    "Keeper Nara says, \"I prefer the evening.\"",
    "Keeper Nara says, \"I prefer the evening because it feels calmer and more peaceful to me.\""
  ],
  "statement:91e0d8561ab0": [
    "Keeper Nara says, \"I do not know who owns the ferry bell.\""
  ],
  "statement:a9905f9b47d9": [
    "Keeper Nara says, \"I cannot promise you a reward for mending the net.\""
  ],
  "statement:3ba2011c8d44": [
    "Keeper Nara said: \"Word is, the bell beside the ferry is called the harbor bell.\" Keeper Nara also said: \"The bell just beside the ferry is known as the harbor bell.\""
  ],
  "statement:97a1b114948c": [
    "Keeper Nara says, \"I prefer the evening because it feels calmer and more peaceful to me.\""
  ],
  "(missing)": [
    "Which earlier remark do you mean? Nothing has been attempted."
  ]
}
```

The three north-road sentences share `topic:sergeant_mara:street`. The watch fact and the partial answer share `topic:sergeant_mara:night_watch`. The adopted explanation inherits the preference id `statement:204a7c55be2b`, so "I prefer the evening." and the longer reason are one proposition there. A later reuse of that reason hashes the full sentence and also records `statement:960f47416fc0`. One explanation is therefore addressable under two ids after it is repeated. The GM recall lines have their own statement ids because the quoted recall is a new delivered utterance. Different roads and different speakers remain separate in the unit matrix.

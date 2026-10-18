# 12 — Positive Dialogue Quality Results

Rubric: 0 incorrect, irrelevant, or unauthorized; 1 safe but rigid or unhelpful; 2 relevant and adequate; 3 natural and within authority. Means do not replace the score-0 list.

Repaired combined mean 1.704 across 27 turns. Distribution: {"2": 9, "3": 8, "1": 4, "0": 6}.

By kind:

```json
{
  "fact": {
    "n": 3,
    "mean": 2,
    "scores": [
      2,
      2,
      2
    ]
  },
  "paraphrase": {
    "n": 4,
    "mean": 3,
    "scores": [
      3,
      3,
      3,
      3
    ]
  },
  "preference": {
    "n": 3,
    "mean": 2,
    "scores": [
      2,
      2,
      2
    ]
  },
  "characterization": {
    "n": 3,
    "mean": 1,
    "scores": [
      1,
      1,
      1
    ]
  },
  "uncertainty": {
    "n": 4,
    "mean": 1.5,
    "scores": [
      3,
      3,
      0,
      0
    ]
  },
  "refusal": {
    "n": 3,
    "mean": 2.333,
    "scores": [
      3,
      1,
      3
    ]
  },
  "authorized": {
    "n": 2,
    "mean": 2,
    "scores": [
      2,
      2
    ]
  },
  "recall": {
    "n": 4,
    "mean": 0.5,
    "scores": [
      2,
      0,
      0,
      0
    ]
  },
  "explanation": {
    "n": 1,
    "mean": 0,
    "scores": [
      0
    ]
  }
}
```

Primary mean 1.933, distribution {"2": 6, "3": 5, "1": 2, "0": 2}. Secondary mean 1.417, distribution {"0": 4, "2": 3, "3": 3, "1": 2}.

Score 0, retained individually:

- Primary 11 and 12: ambiguous recall. “Which earlier remark do you mean? Nothing has been attempted.”
- Secondary 1: ambiguity before the ferry bell exists.
- Secondary 9: authorized watch sentence instead of uncertainty about “unattended.”
- Secondary 10 and 11: ambiguous recall of the bell.

Score 1 turns are safe host fallbacks: the preference line where an explanation was requested, and one reward refusal that stayed on the host sentence. Successful score-3 turns are the four paraphrases, two uncertainties, and two refusals listed in reports 08 and 10. Verbatim repetition was not adopted when a rewording was requested and the candidate passed validation. False ignorance was not used when the road, bell, or watch fact was the selected answer.

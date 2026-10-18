# 15 — Positive Dialogue Quality

Rubric used by the runner: 0 incorrect, irrelevant, or unauthorized; 1 safe but rigid; 2 relevant and adequate; 3 natural, within authority, and conversationally appropriate. Any scorer failure forces 0.

Raw scores are the recorded runner output. They are not rewritten.

Combined raw mean 2.444. Distribution {2: 7, 3: 17, 1: 1, 0: 2}. Score-0 turns: [14, 10].

Category scores:

```json
{
  "primary": {
    "preference": {
      "n": 2,
      "mean": 2,
      "scores": [
        2,
        2
      ]
    },
    "characterization": {
      "n": 2,
      "mean": 1.5,
      "scores": [
        3,
        0
      ]
    },
    "fact": {
      "n": 1,
      "mean": 2,
      "scores": [
        2
      ]
    },
    "paraphrase": {
      "n": 2,
      "mean": 2,
      "scores": [
        1,
        3
      ]
    },
    "explanation": {
      "n": 1,
      "mean": 3,
      "scores": [
        3
      ]
    },
    "uncertainty": {
      "n": 1,
      "mean": 3,
      "scores": [
        3
      ]
    },
    "refusal": {
      "n": 1,
      "mean": 3,
      "scores": [
        3
      ]
    },
    "authorized": {
      "n": 1,
      "mean": 2,
      "scores": [
        2
      ]
    },
    "partial": {
      "n": 1,
      "mean": 3,
      "scores": [
        3
      ]
    },
    "recall": {
      "n": 1,
      "mean": 3,
      "scores": [
        3
      ]
    },
    "ambiguity": {
      "n": 1,
      "mean": 3,
      "scores": [
        3
      ]
    },
    "clarify": {
      "n": 1,
      "mean": 3,
      "scores": [
        3
      ]
    }
  },
  "secondary": {
    "authorized": {
      "n": 1,
      "mean": 2,
      "scores": [
        2
      ]
    },
    "partial": {
      "n": 1,
      "mean": 3,
      "scores": [
        3
      ]
    },
    "fact": {
      "n": 1,
      "mean": 2,
      "scores": [
        2
      ]
    },
    "paraphrase": {
      "n": 1,
      "mean": 3,
      "scores": [
        3
      ]
    },
    "preference": {
      "n": 1,
      "mean": 2,
      "scores": [
        2
      ]
    },
    "characterization": {
      "n": 2,
      "mean": 1.5,
      "scores": [
        3,
        0
      ]
    },
    "uncertainty": {
      "n": 1,
      "mean": 3,
      "scores": [
        3
      ]
    },
    "refusal": {
      "n": 1,
      "mean": 3,
      "scores": [
        3
      ]
    },
    "recall": {
      "n": 1,
      "mean": 3,
      "scores": [
        3
      ]
    },
    "ambiguity": {
      "n": 1,
      "mean": 3,
      "scores": [
        3
      ]
    },
    "clarify": {
      "n": 1,
      "mean": 3,
      "scores": [
        3
      ]
    }
  },
  "combined": {
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
      "n": 4,
      "mean": 1.5,
      "scores": [
        3,
        0,
        3,
        0
      ]
    },
    "fact": {
      "n": 2,
      "mean": 2,
      "scores": [
        2,
        2
      ]
    },
    "paraphrase": {
      "n": 3,
      "mean": 2.333,
      "scores": [
        1,
        3,
        3
      ]
    },
    "explanation": {
      "n": 1,
      "mean": 3,
      "scores": [
        3
      ]
    },
    "uncertainty": {
      "n": 2,
      "mean": 3,
      "scores": [
        3,
        3
      ]
    },
    "refusal": {
      "n": 2,
      "mean": 3,
      "scores": [
        3,
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
    "partial": {
      "n": 2,
      "mean": 3,
      "scores": [
        3,
        3
      ]
    },
    "recall": {
      "n": 2,
      "mean": 3,
      "scores": [
        3,
        3
      ]
    },
    "ambiguity": {
      "n": 2,
      "mean": 3,
      "scores": [
        3,
        3
      ]
    },
    "clarify": {
      "n": 2,
      "mean": 3,
      "scores": [
        3,
        3
      ]
    }
  }
}
```

Expression attempts 12. Adopted 9. Rejected 3. Fallbacks 3.

Adoption rate among attempts: 0.75. Rejection rate: 0.25. Fallback rate: 0.25.

The two score-0 turns are primary 14 and secondary 10. Each delivered the characterization adopted earlier in that conversation, after the new candidate was rejected as a verbatim repeat. Read as dialogue, those turns are safe and relevant. The raw 0 stands in the recorded scores so the measurement collision stays visible. No safety failure is hidden inside the mean: the north-street rejection scored 1 and delivered the authorized sentence.

Adopted characterization:

```json
[
  {
    "conversation": "primary",
    "turn": 2,
    "text": "Sergeant Mara says, \"I prefer the evening because it feels calmer and more peaceful to me.\""
  },
  {
    "conversation": "secondary",
    "turn": 6,
    "text": "Keeper Nara says, \"I prefer the evening because it feels calmer and more peaceful to me.\""
  }
]
```

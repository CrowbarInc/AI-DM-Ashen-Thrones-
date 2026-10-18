# 13 — Frozen Holdouts

Original R2C frozen_holdouts.json, freeze.json and H6 are unchanged. Original H6 failed in the verified baseline and passes in the final suite.

Three new cases were frozen before initial edits. Eight additional cases were frozen before their first evaluation. All eleven passed; none were tuned against a failed holdout. Later generic-ask compatibility and recall-fallback fixes arose from regression/live audits, not these holdouts. Four new final-revision fixtures F1–F4 were independently frozen after those fixes and before evaluation; all four pass. Earlier eleven are also retained as regression evidence. Natural-language subjects, NPCs, locations, competing topic order, unauthorized candidates and actual save/load vary across fixtures.

```json
[
  {
    "id": "R1H1",
    "passed": true,
    "error": null
  },
  {
    "id": "R1H2",
    "passed": true,
    "error": null
  },
  {
    "id": "R1H3",
    "passed": true,
    "error": null
  },
  {
    "id": "Q1",
    "passed": true,
    "error": null
  },
  {
    "id": "Q2",
    "passed": true,
    "error": null
  },
  {
    "id": "Q3",
    "passed": true,
    "error": null
  },
  {
    "id": "Q4",
    "passed": true,
    "error": null
  },
  {
    "id": "Q5",
    "passed": true,
    "error": null
  },
  {
    "id": "Q6",
    "passed": true,
    "error": null
  },
  {
    "id": "Q7",
    "passed": true,
    "error": null
  },
  {
    "id": "Q8",
    "passed": true,
    "error": null
  },
  {
    "id": "F1",
    "passed": true,
    "error": null
  },
  {
    "id": "F2",
    "passed": true,
    "error": null
  },
  {
    "id": "F3",
    "passed": true,
    "error": null
  },
  {
    "id": "F4",
    "passed": true,
    "error": null
  }
]
```

Freeze hashes and final source hashes are supplied. All are deterministic qualification; none substitutes for fresh-provider usability.

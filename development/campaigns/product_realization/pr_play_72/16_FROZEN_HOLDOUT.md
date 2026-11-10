# PR-PLAY-72 — 16 FROZEN HOLDOUT

```json
{
  "cases": 60,
  "passed": 52,
  "failed": [
    {
      "id": "H04",
      "checks": [
        "resolved_action"
      ]
    },
    {
      "id": "H05",
      "checks": [
        "resolved_action"
      ]
    },
    {
      "id": "H09",
      "checks": [
        "resolved_action"
      ]
    },
    {
      "id": "H10",
      "checks": [
        "resolved_action"
      ]
    },
    {
      "id": "H11",
      "checks": [
        "resolved_action"
      ]
    },
    {
      "id": "H15",
      "checks": [
        "resolved_action"
      ]
    },
    {
      "id": "H20",
      "checks": [
        "resolved_action"
      ]
    },
    {
      "id": "H38",
      "checks": [
        "category"
      ]
    }
  ],
  "manifest_sha256": "f9baae313a54716f910d34498e528abedd315cf052746ae5f9ec08eb65fdd131",
  "executions": 1,
  "authorship": "developer-authored; not independent external validation"
}
```

Manifest SHA256 was checked immediately before the one-shot execution. holdout_started.json is opened exclusively, preventing accidental rerun. Cases and results remain unchanged. Seven failures require success=True for correctly already-searched targets; H38 incorrectly classified an ambiguous request as a safe read-only answer. No tuning against these failures was performed. Separate development checks outside the holdout subsequently repaired unknown choice subjects and exact-name NPC grounding; therefore this holdout is evidence for the pre-repair product, not a fresh final-source holdout. The pre-repair source and freeze are retained. No replacement holdout was run and B remains the verdict. This is developer-authored, not external independent validation.

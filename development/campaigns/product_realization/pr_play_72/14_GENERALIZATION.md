# PR-PLAY-72 — 14 GENERALIZATION

The developer-authored preimplementation holdout includes 15 supported intentions, 10 paraphrases, 10 branch cases, 10 unsupported/ambiguous cases, five information requests, five projection cases and five resume cases. Cases vary verbs, questions, first-person intentions, short imperatives and scene/branch context. All fixed inputs, starting-state recipes, expectations, publication constraints and hashes are retained. This is bounded English phrase recognition; unseen arbitrary syntax and arbitrary world actions remain outside scope.

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


# PR-CY Failure Inventory

```json
{
  "halt": null,
  "errors": [],
  "authority_violations": [],
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
      "assessment": "False positive: the rejected sentence is a qualified ordinary follow-up about rain discomfort and vigilance, not an unauthorized discovery, biography, geography, hidden fact, durable world mutation, or consequential NPC action."
    }
  ],
  "budget": {
    "provider_requests": 3,
    "tokens": 99616,
    "max_provider_requests": 3,
    "max_tokens": 110000
  }
}
```

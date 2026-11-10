# PR-PLAY-72 — 12 PLAYER SAFE PUBLICATION

The existing player_http_projection allowlists remain in force. Unknown fields are dropped. Public responses contain narration and permitted state, never internal ConversationalDecision, proposed records, raw resolution metadata, hidden flags or provider traces. Hidden sentinels were added only to disposable holdout scene metadata. Read complete_payload_leakage_scan.json and frozen holdout constraints for actual serialized-response checks.

One social discovery omission was observed after the grounding repair: resolution committed the existing route-change topic, while the offline presentation returned unrelated opening prose. The trace and failed complete-response scan remain in mandatory_disclosure_before_repair.json and http_before_social_disclosure_* evidence. The enrolled publication seam now requires success, target_resolved, and exact membership of the current topic text in current discovered_clues, then uses the existing social fact formatter. It never reads an undiscovered topic. Thus optional narration cannot suppress the current social fact. Final checks and the complete-payload scan report the repaired result separately; do not erase the one earlier omission from cycle totals.

```json
{
  "publication_and_lifecycle": {
    "cases": 57,
    "passed": 56,
    "failed": 1,
    "failures": [
      "tests.test_pr_play_72_supplemental::test_explicit_npc_interaction_resolves"
    ]
  },
  "corrected_social_assertion": {
    "cases": 1,
    "passed": 1,
    "failed": 0,
    "failures": []
  },
  "final_disclosure_scan": {
    "checks": [
      {
        "request": {
          "path": "/api/chat",
          "method": "POST",
          "json": {
            "text": "I examine the notice board."
          }
        },
        "required": "The missing patrol was last seen taking the northwest mud track past the crates.",
        "present": true
      },
      {
        "request": {
          "path": "/api/chat",
          "method": "POST",
          "json": {
            "text": "I examine the weathered milestone."
          }
        },
        "required": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.",
        "present": true
      },
      {
        "request": {
          "path": "/api/chat",
          "method": "POST",
          "json": {
            "text": "I examine the notice board."
          }
        },
        "required": "The missing patrol was last seen taking the northwest mud track past the crates.",
        "present": true
      },
      {
        "request": {
          "path": "/api/chat",
          "method": "POST",
          "json": {
            "text": "I examine the weathered milestone."
          }
        },
        "required": "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.",
        "present": true
      },
      {
        "request": {
          "path": "/api/chat",
          "method": "POST",
          "json": {
            "text": "I ask the Gate Serjeant about the patrol route."
          }
        },
        "required": "The patrol route changed after the Ash Compact census choke worsened.",
        "present": true
      }
    ],
    "omissions": [],
    "matching": "Full authoritative sentence, case-insensitive; existing social formatter can lowercase the initial article within a quotation.",
    "cycle_earlier_omissions": 1,
    "scope": "Final real HTTP chat discovery resolutions; authored consequence checks separately covered by tests."
  }
}
```

The publication lane was 56/57: its remaining assertion was case-sensitive while the existing formatter lowercases the initial article inside a quotation. The case-insensitive full-sentence check passed in a separate fresh process, 1/1, and all five final HTTP discovery disclosures are present. No product change followed that assertion correction. No published AI prose is claimed.

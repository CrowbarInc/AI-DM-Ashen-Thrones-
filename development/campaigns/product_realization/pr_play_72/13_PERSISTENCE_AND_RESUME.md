# PR-PLAY-72 — 13 PERSISTENCE AND RESUME

Normal /api/snapshots and /api/snapshots/load save and restore both branch identities, world, journal, transcript and continuations. A newly created campaign separates save/resume checks; HTTP also cross-loads two campaign slots. A separate fresh Python process subsequently resumed both final HTTP save slots and passed six natural read-only/ambiguous/unsupported continuations with exact gameplay-document equality. Existing last_saved_at and narration resume markers are expected storage metadata changes. Byte-rollback and transient/permanent Windows rename checks passed in the clean 39-case lifecycle lane. No alternate session state was introduced.

```json
{
  "fresh_process": true,
  "campaigns": [
    {
      "branch": "survey",
      "identity": "f5b11c7287d3af4ce78be685",
      "restored": true,
      "branch_flag": true,
      "journal": null,
      "readonly": true,
      "ambiguous": true,
      "unsupported": true
    },
    {
      "branch": "report",
      "identity": "e9e75fb9d8c25f63a750e5bb",
      "restored": true,
      "branch_flag": true,
      "journal": null,
      "readonly": true,
      "ambiguous": true,
      "unsupported": true
    }
  ],
  "provider_requests": 0,
  "provider_tokens": 0
}
```


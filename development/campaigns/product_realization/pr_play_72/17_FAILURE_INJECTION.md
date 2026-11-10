# PR-PLAY-72 — 17 FAILURE INJECTION

tests/test_pr_play_72_failures.py covers malformed records, unsupported operations, invented targets, stale scene targets, stale branch follow-ups, missing provider access on read-only turns, invalid HTTP schemas, unknown publication fields, and append-log persistence faults with exact byte rollback. Repeated one-time choices, hidden targets, negated/multiple requests and cross-campaign restoration are in the initiative suite. Existing regression suites cover rejected optional narration and Windows replacement faults. Provider unavailable/timeout cases establish that the deterministic information path makes no call; they do not claim a real live provider timed out. No network timeout experiment or live provider interpretation is claimed.

```json
{
  "cases": 60,
  "passed": 59,
  "failed": 1,
  "failures": [
    "tests.test_pr_play_72_supplemental::test_explicit_npc_interaction_resolves"
  ]
}
```


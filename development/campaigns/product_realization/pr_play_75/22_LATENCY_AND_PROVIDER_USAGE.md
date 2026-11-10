# PR-PLAY-75 — 22 LATENCY AND PROVIDER USAGE

Actual measurements (milliseconds):

```json
{
  "final_http_conversation_ms": {
    "count": 16,
    "mean": 3829.6151062459103,
    "median": 3934.937899990473,
    "maximum": 5239.369199960493
  },
  "browser_server_chat_ms": {
    "count": 21,
    "mean": 2866.9087142857143,
    "median": 2229.085,
    "maximum": 14765.969
  },
  "provider_ms": {
    "count": 12,
    "mean": 1750.3003333333334,
    "median": 1368.958,
    "maximum": 3210.035
  },
  "save_resume_ms": {
    "count": 4,
    "mean": 2491.8861000041943,
    "median": 2417.23149997415,
    "maximum": 3208.732300088741
  },
  "browser_visible_ms": null,
  "commit_only_ms": null
}
```

Final conversation timing includes HTTP/persistence while several isolated validation processes ran concurrently; it is not a controlled load-free benchmark. Provider 12 requests / 3,398 tokens / 0 retries. Proposal acceptance 6/6. Sampled live dialogue adoption 0/6. Separate validation/authored-NPC microbenchmarks are in performance_supplement.json; authored narration uses an offline fixture. Atomic-write and resolver substage timing is captured, but separate NPC commit/publication latency and browser paint time are unavailable.

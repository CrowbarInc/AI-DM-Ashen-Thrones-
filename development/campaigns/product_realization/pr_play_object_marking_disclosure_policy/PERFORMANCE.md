# Performance

Milestone: `pr_play_object_marking_disclosure_policy`. Date: 2026-11-09.

100 observations per small representative fixture; internal authorization establishment/validation and projection serialization measured separately. No enforced machine-specific performance threshold. No live provider calls, retries, prompt expansion, full-world scan, ACL engine, database or endpoint. Character identity validation is O(inventory rows); selected active projection is at most 16 markings, 2048 UTF-8 bytes each/8192 permitted bytes. No history scan. JSON output contains no timing metadata. Measurements (microseconds, local host):

```json
{
  "samples": {
    "unmarked": {
      "mean_us": 170.501,
      "max_us": 2497.5,
      "authorization_us": 139.101,
      "serialization_us": 4.337,
      "payload_bytes": 312
    },
    "visible": {
      "mean_us": 186.689,
      "max_us": 4174.9,
      "authorization_us": 78.17,
      "serialization_us": 14.727,
      "payload_bytes": 644
    },
    "mixed": {
      "mean_us": 343.379,
      "max_us": 5391.6,
      "authorization_us": 123.932,
      "serialization_us": 95.118,
      "payload_bytes": 644
    }
  },
  "iterations": 100,
  "live_provider_calls": 0,
  "prompt_expansion": 0,
  "provider_retries": 0
}
```

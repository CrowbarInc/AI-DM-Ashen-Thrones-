# Performance

Milestone: `pr_play_object_marking_inspection`. Date: 2026-11-09.

Small two-object fixture; 50 pure read/validation samples and 10 save/reload/commit samples. Host micro-measurement only, not a broad benchmark. Commit measurements restore controlled fixture state between samples. A separate single-test measurement run followed completion of background regressions to avoid their disk contention; exact command/results in bounded_performance_* artifacts.

```json
{
  "inspect_unmarked": {
    "samples": 50,
    "median_us": 313.1,
    "max_us": 412.8
  },
  "inspect_multiple": {
    "samples": 50,
    "median_us": 408.75,
    "max_us": 637.2
  },
  "removal_validation": {
    "samples": 50,
    "median_us": 921.55,
    "max_us": 1769.0
  },
  "save_reload": {
    "samples": 10,
    "median_us": 8974.150000000001,
    "max_us": 11409.3
  },
  "removal_commit": {
    "samples": 10,
    "median_us": 20182.75,
    "max_us": 21035.1
  },
  "removal_receipt_compact_bytes": 2051,
  "character_growth_compact_bytes": 1142,
  "live_provider_calls": 0,
  "prompt_expansion": 0,
  "inventory_size": 2
}
```

Removal receipt retains one bounded marking to validate historical add evidence. Net compact character growth accounts for moving the marking out of active state. No prompt projection changes: receipts/markings remain outside selected prompt character fields. No tokens, provider calls, retries, world scans or inventory-wide model classification. Work is O(this inventory and retained receipts), not O(world/conversation).

# Performance

Milestone: `pr_play_object_visibility_authoring`. Date: 2026-11-09.

Representative two-object/one-mark fixtures. Comparable refined measurements use 100 iterations for pure initial/transition/replay validation and observation with fresh grants on already-loaded state, plus 25 isolated atomic writer samples. Microseconds, local host only; no portable threshold. Receipt growth is linear in committed requests (including durable no_change); current marking state remains bounded.

```json
{
  "initial_validation": {
    "mean_us": 255.409,
    "iterations": 100
  },
  "transition_validation": {
    "mean_us": 351.855,
    "iterations": 100
  },
  "exact_replay_validation": {
    "mean_us": 206.903,
    "iterations": 100
  },
  "atomic_persistence": {
    "mean_us": 4073.084,
    "iterations": 25
  },
  "observation_unclassified": {
    "mean_us": 55.948,
    "iterations": 100
  },
  "observation_visible": {
    "mean_us": 62.55,
    "iterations": 100
  },
  "observation_concealed": {
    "mean_us": 63.088,
    "iterations": 100
  },
  "receipt_bytes_per_classification": [
    1169,
    1171,
    1169
  ],
  "initial_ledger_bytes": 529,
  "final_ledger_bytes": 4281,
  "live_provider_calls": 0,
  "network_attempts": 0,
  "prompt_expansion": 0
}
```

The earlier visibility_performance.json retains full-service initial/transition/replay samples. Its before observation uses cached state while after includes a disk read; that difference is not pure projection overhead. Refined measurements separate those costs. Validation scans this character inventory/receipt history only. No world scan, prompt expansion, new model classification, live provider calls, database, ACL engine or player endpoint. Authoring receipts remain outside prompts and projection.

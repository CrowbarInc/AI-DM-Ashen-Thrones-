# Performance

Milestone: `pr_play_object_marking_mutation`. Date: 2026-11-09.

Small fixture: 20 explicitly identified singleton inventory rows. 100 lookup and validation samples, 30 save samples. Measure is a micro-measurement of this host, not a broad benchmark.

```json
{
  "identity_lookup": {
    "samples": 100,
    "median_us": 423.79999999999995,
    "max_us": 832.1
  },
  "validation_and_staging": {
    "samples": 100,
    "median_us": 908.55,
    "max_us": 1280.3
  },
  "atomic_character_save": {
    "samples": 30,
    "median_us": 5312.55,
    "max_us": 7161.7
  },
  "fixture_inventory_size": 20,
  "live_provider_calls": 0,
  "additional_model_calls": 0,
  "prompt_expansion": 0,
  "receipt_compact_bytes": 392,
  "first_operation_character_growth_bytes": 1538,
  "directory_sync_supported": false
}
```

Receipt growth is retained for saved timeline lifetime. Validation scans only this inventory and its marking/receipt state, never world objects. Prompt character projection in game/prompt_context.py explicitly selects name/hp/ac/conditions/attacks/spells/skills and excludes receipts/markings; prompt path unchanged. Zero live provider calls, additional model calls/retries/tokens or prompt expansion.

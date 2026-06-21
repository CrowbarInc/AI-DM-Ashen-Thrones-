# BV13B — Fan-In Report

**Date:** 2026-06-21

| Module | Before (BV13A) | After (BV13B) | Delta |
| --- | --- | --- | --- |
| `game.final_emission_text` | **52** | **5** | **-47** |
| `game.final_emission_text_formatting` | 2 (internal) | **52** | **+50** |
| `game.final_emission_text_policy` | 1 (internal) | **8** | **+7** |
| `game.final_emission_text_legacy_semantic_repair` | 1 (internal) | **3** | **+2** |

## Symbol redistribution

| Symbol class | Canonical owner | Post-migration direct FI |
| --- | --- | --- |
| `_normalize_text` (+ formatting helpers) | formatting | ~52 module importers |
| Policy tuples / `_RESPONSE_TYPE_VALUES` | policy | ~8 module importers |
| Legacy semantic repair | legacy | ~3 module importers |
| Fallback stock line wrapper | compat | ~5 module importers |

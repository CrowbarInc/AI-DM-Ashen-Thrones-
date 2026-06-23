# BZ1 — Protected Replay Trend Window #2 Scaffold

## Status

**Complete.** First executable BZ slice: corpus-locked replay-key catalog extraction, lifecycle classification, and `trend_window_2` artifact generation. Measurement only — no replay behavior changes.

## Command

```powershell
python tools/run_protected_replay_trend.py --runs 2 --out-dir artifacts/golden_replay/trend_window_2
```

## Files touched

| File | Change |
|---|---|
| `tests/helpers/golden_replay_trend.py` | Added corpus parity validation, replay-key catalog builders, lifecycle comparison, BZ movement report writer, optional BZ hook in `run_protected_replay_trend_window()` |
| `tools/run_protected_replay_trend.py` | Auto-enables BZ movement report when `--out-dir` ends in `trend_window_2`; optional `--bz-replay-key-baseline-run` override |
| `tests/test_bz_protected_replay_trend_window_2.py` | **New** — BZ1 lifecycle classification suite (9 tests) |
| `artifacts/golden_replay/trend_window_2/` | **New** — BW-shaped window artifacts plus `BZ_replay_key_movement.json` |

BW artifacts under `artifacts/golden_replay/trend_window/` were not modified.

## Tests added

`tests/test_bz_protected_replay_trend_window_2.py`:

- `test_bz_corpus_matches_bw`
- `test_replay_key_catalog_generation`
- `test_new_key_classification`
- `test_retired_key_classification`
- `test_unchanged_key_classification`
- `test_active_key_classification`
- `test_field_state_distinction`
- `test_catalog_order_is_deterministic`
- `test_bz_artifacts_do_not_touch_bw_paths`

**Regression:** All 53 tests in the BZ + BW trend/registry/closeout suite pass.

## Artifacts generated

```
artifacts/golden_replay/trend_window_2/
├── manifest.json
├── runs/run-000.json
├── runs/run-001.json
├── comparisons/run-001-vs-run-000.json
├── golden_transcript_drift.json
├── golden_transcript_drift.md
├── BZ_replay_key_movement.json
└── _storage/…
```

### Window drift (BZ internal)

- `golden_transcript_drift_count`: **0** (run-001 vs run-000 within `trend_window_2`)
- Guardrail: **PASS**

## Corpus parity result

| Check | Result |
|---|---|
| Scenario count | 6 (baseline) = 6 (current) |
| Ordered scenario IDs | Exact match |
| `corpus_match` | `true` |

Corpus authority: `protected_replay_corpus()` / BW `manifest.json`.

## Replay-key movement summary

Baseline: `artifacts/golden_replay/trend_window/runs/run-000.json`  
Current: `artifacts/golden_replay/trend_window_2/runs/run-000.json`

| Metric | Count |
|---|---|
| Active keys | 49 |
| New keys | 10 |
| Retired keys | 0 |
| Unchanged keys | 39 |

### Key counts by dimension

| Dimension | Active | New | Retired | Unchanged |
|---|---:|---:|---:|---:|
| `route` | 8 | 0 | 0 | 8 |
| `speaker` | 14 | 10 | 0 | 4 |
| `source` | 8 | 0 | 0 | 8 |
| `owner` | 7 | 0 | 0 | 7 |
| `mutation` | 12 | 0 | 0 | 12 |

All 10 new keys are in the **speaker** dimension (`final_observed_speaker_id`, `final_speaker_observation_status`, `selected_speaker_source`, `speaker_projection_parity_status`). The committed BW baseline run predates these normalized speaker-parity fields; BZ catalogs include them while BW run-000 does not. This is expected schema-evolution signal, not runtime drift within the same normalization schema.

## Helpers added

| Helper | Purpose |
|---|---|
| `protected_replay_corpus_scenario_ids()` | Ordered corpus ID list |
| `validate_protected_replay_corpus_parity()` | Report-only corpus lock (count + ordered IDs) |
| `build_replay_key_catalog()` | Full deterministic replay-key catalog from a run envelope |
| `build_dimension_key_catalog()` | Single-dimension catalog slice |
| `compare_replay_key_catalogs()` | `new` / `retired` / `unchanged` / `active` classification |
| `build_bz_replay_key_movement_report()` | Assemble `BZ_replay_key_movement.json` payload |
| `write_bz_replay_key_movement_artifact()` | Write movement JSON after trend window run |

Replay key format: `<dimension>|<field>|<canonical-json-field-state>` using `_stable_json()` (no Python `hash()`).

## Known limitations

1. **Cross-window speaker schema gap:** BW `run-000.json` lacks speaker-parity fields present in current normalization; first BZ report shows 10 speaker `new_keys` with zero `retired_keys`. A refreshed BW baseline snapshot would collapse this to zero movement for an unchanged corpus.
2. **`final_text` excluded:** Replay-key catalogs cover five BZ dimensions (`route`, `speaker`, `source`, `owner`, `mutation`) only; `final_text_hash` remains BW drift-only/advisory.
3. **No recurrence movement:** `BZ_recurrence_movement.json` and `protected_replay_trend_movement.py` are deferred to BZ2.
4. **No within-BZ-window key movement report:** Movement compares BW run-000 → BZ run-000; run-001 is used only for BW-shaped drift comparison inside the window.
5. **No standalone catalog JSON files:** Full entry catalogs (with `contributing_identities`) are computed in-process; only the movement summary is persisted.

## Readiness assessment for BZ2

| Prerequisite | BZ1 status |
|---|---|
| Deterministic replay-key catalogs | Ready |
| Lifecycle classification (`new` / `active` / `retired` / `unchanged`) | Ready |
| Corpus lock validation | Ready |
| `trend_window_2` runner integration | Ready |
| Recurrence snapshot baseline decision | **Not started** — required before honest BW→BZ recurrence movement |
| `protected_replay_trend_movement.py` | **Not started** |
| `BZ_recurrence_movement.json` | **Not started** |

**Recommendation:** Proceed to BZ2 after documenting whether recurrence baseline is (a) a recovered BW-time snapshot or (b) an explicit baseline-establishment capture. BZ1 replay-key scaffold is stable and test-covered; recurrence work can import `build_replay_key_catalog()` / `compare_replay_key_catalogs()` patterns without modifying this block.

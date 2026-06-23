# BZ Protected Replay Trend Window #2 — Closeout

## Status

BZ is **closed**. The protected replay trend window #2 measurement lane is implemented, test-locked, and produces deterministic BZ reports without modifying BW artifacts or replay runtime behavior.

This document is the operating procedure for future BZ reruns. It does not change runtime behavior, protected replay pass/fail gates, or corpus promotion policy.

## Objective

Execute the exact BW protected replay corpus into `artifacts/golden_replay/trend_window_2`, validate corpus parity against BW, classify replay-key lifecycle movement against the committed BW baseline run, and emit recurrence movement reports with honest provenance. All BZ work is **measurement only**.

## Commands run

Primary BZ window generation:

```powershell
python tools/run_protected_replay_trend.py --runs 2 --out-dir artifacts/golden_replay/trend_window_2
```

Optional historical recurrence comparison when an explicit baseline snapshot exists:

```powershell
python tools/run_protected_replay_trend.py --runs 2 --out-dir artifacts/golden_replay/trend_window_2 --bz-recurrence-baseline path/to/baseline_recurrence_history.json
```

Recommended validation bundle:

```powershell
python -m pytest tests/test_bz_protected_replay_trend_window_2.py tests/test_bz_protected_replay_trend_window_2_closeout.py tests/test_bw_protected_replay_trend_window_closeout.py tests/test_golden_replay_trend.py -q
python -m pytest -m golden_replay -q
```

### CLI options (BZ-relevant)

| Flag | Purpose |
|---|---|
| `--runs N` | Number of isolated replay executions (minimum 1). |
| `--out-dir PATH` | Artifact output directory. BZ auto-reports activate when the directory name is `trend_window_2`. |
| `--bz-replay-key-baseline-run PATH` | Optional replay run envelope for replay-key movement (default: BW `runs/run-000.json`). |
| `--bz-recurrence-baseline PATH` | Optional explicit recurrence history snapshot for historical recurrence movement. |
| `--append-history` | BW drift history append (optional; does not affect BZ movement JSON). |
| `--thresholds PATH` | Optional report-only guardrail threshold overrides. |

Exit code remains **0** on successful artifact write, even when guardrail status is `WARN`.

## Corpus used

The BZ corpus is exactly the six short structural scenarios from `tests/helpers/protected_replay_registry.py::protected_replay_corpus()` — the same mechanical authority as BW.

| Scenario ID | Turns |
|---|---:|
| `directed_npc_question` | 1 |
| `lead_followup_with_dialogue_lock` | 2 |
| `sanitizer_scaffold_leakage` | 1 |
| `thin_answer_action_outcome_final_emission` | 1 |
| `vocative_override_after_prior_continuity` | 2 |
| `wrong_speaker_strict_social_emission` | 1 |

**Total aligned turn identities:** 8.

## Baseline and output paths

| Role | Path |
|---|---|
| BW baseline run (replay-key movement) | `artifacts/golden_replay/trend_window/runs/run-000.json` |
| BW baseline manifest (corpus lock) | `artifacts/golden_replay/trend_window/manifest.json` |
| BZ output directory | `artifacts/golden_replay/trend_window_2/` |
| BZ replay-key movement | `artifacts/golden_replay/trend_window_2/BZ_replay_key_movement.json` |
| BZ recurrence movement | `artifacts/golden_replay/trend_window_2/BZ_recurrence_movement.json` |
| BZ window summary | `artifacts/golden_replay/trend_window_2/BZ_protected_replay_trend_window_2.md` |
| Current recurrence snapshot (read-only) | `artifacts/golden_replay/bug_recurrence_history.json` |

**BW artifacts under `artifacts/golden_replay/trend_window/` are not modified** by BZ generation. BZ writes only into `trend_window_2/`.

## Corpus parity result

Committed BZ report: `corpus_match: true`

- Scenario count: 6 baseline = 6 current
- Ordered scenario IDs: exact match with BW manifest and registry authority

## Replay key movement summary

Committed `BZ_replay_key_movement.json` (BW run-000 vs BZ run-000):

| Metric | Count |
|---|---:|
| Active keys | 49 |
| New keys | 10 |
| Retired keys | 0 |
| Unchanged keys | 39 |

All 10 new keys are in the **speaker** dimension. The committed BW baseline run predates normalized speaker-parity fields present in current observation serialization; this is schema-evolution signal, not within-window runtime drift.

Internal BZ window drift (run-001 vs run-000 inside `trend_window_2`): **0** (`golden_transcript_drift_count=0`, guardrail PASS).

## Recurrence movement summary

Committed `BZ_recurrence_movement.json`:

| Field | Value |
|---|---|
| `comparison_mode` | `baseline_establishment` |
| `baseline_available` | `false` |
| `current_available` | `true` |
| `current_path` | `artifacts/golden_replay/bug_recurrence_history.json` |

All recurrence movement counts are **0** in baseline-establishment mode. Movement lists are intentionally empty.

**Historical BW→BZ recurrence movement is not claimed without an explicit BW-time recurrence snapshot.** The cumulative `bug_recurrence_history.json` is referenced only as the current snapshot path, never as an inferred BW baseline.

## Baseline establishment mode

No immutable recurrence snapshot was preserved at BW window closeout. Therefore the default BZ runner emits:

```json
"comparison_mode": "baseline_establishment"
```

This mode:

- Records the current recurrence snapshot path for operator reference
- Leaves movement lists empty
- Avoids falsely reporting newly recurring / still recurring / no-longer-recurring movement against an absent baseline

To perform an honest historical recurrence comparison, preserve an explicit baseline file and rerun with `--bz-recurrence-baseline`.

## Regression Recurrence Rate evidence

Score Regression Recurrence Rate from the read-only current recurrence history:

- File: `artifacts/golden_replay/bug_recurrence_history.json`
- Field: `protected_replay_regression_recurrence_rate`
- Committed value at closeout: **50.0% (3 / 6 recurrence keys)** — advisory/report-only

BZ recurrence movement complements this by documenting provenance honesty; it does not replace the history-derived rate.

## Artifact layout

```text
artifacts/golden_replay/trend_window_2/
  manifest.json
  runs/run-000.json
  runs/run-001.json
  comparisons/run-001-vs-run-000.json
  golden_transcript_drift.json
  golden_transcript_drift.md
  BZ_replay_key_movement.json
  BZ_recurrence_movement.json
  BZ_protected_replay_trend_window_2.md
  _storage/run-000/
  _storage/run-001/
```

## Known limitations

1. **Speaker schema gap vs committed BW run-000** — first replay-key report shows 10 speaker `new_keys` with zero `retired_keys`.
2. **No BW recurrence baseline in repo** — default recurrence report is baseline establishment only.
3. **`final_text` excluded from replay-key catalogs** — remains BW drift-only/advisory.
4. **Recurrence `event_source`** — enriched read-only from `bug_recurrence_event_log.json`, not from history rows alone.
5. **Historical recurrence movement requires explicit baseline capture** — cumulative history must not be used as a retroactive BW proxy.

## Final assessment against success criteria

| Criterion | Result |
|---|---|
| BZ reports reproducible | **Met** — deterministic JSON/Markdown writers; byte-stability locked by tests |
| BZ runner behavior test-locked | **Met** — closeout + BZ/BW trend suites |
| BZ closeout document exists | **Met** — this document |
| Trend evidence supports Regression Recurrence Rate scoring | **Met** — current history rate documented; provenance honesty explicit |
| No runtime/replay behavior changes | **Met** — test/tooling lane only |
| BW artifacts untouched | **Met** — safety tests verify no writes to `trend_window/` |
| Recurrence persistence untouched | **Met** — read-only access to history/event log |

**BZ is ready to close.**

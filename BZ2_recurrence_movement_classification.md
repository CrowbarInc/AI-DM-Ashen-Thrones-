# BZ2 — Recurrence Movement Classification

## Status

**Complete.** BZ recurrence movement reporting compares explicit recurrence snapshots without mutating recurrence persistence or claiming unsupported BW-time history.

## Command

```powershell
python tools/run_protected_replay_trend.py --runs 2 --out-dir artifacts/golden_replay/trend_window_2
```

Optional historical comparison when an explicit baseline snapshot exists:

```powershell
python tools/run_protected_replay_trend.py --runs 2 --out-dir artifacts/golden_replay/trend_window_2 --bz-recurrence-baseline path/to/baseline_recurrence_history.json
```

## Files touched

| File | Change |
|---|---|
| `tests/helpers/protected_replay_trend_movement.py` | **New** — snapshot builder, snapshot comparator, BZ recurrence movement artifact writer |
| `tests/helpers/golden_replay_trend.py` | Added optional BZ recurrence hook to `run_protected_replay_trend_window()` |
| `tools/run_protected_replay_trend.py` | Added `--bz-recurrence-baseline`; auto-writes recurrence movement for `trend_window_2` |
| `tests/test_bz_protected_replay_trend_window_2.py` | Extended with 12 recurrence movement tests (11 required + 1 historical-mode proof) |
| `artifacts/golden_replay/trend_window_2/BZ_recurrence_movement.json` | **New/updated** committed artifact |

Unchanged (read-only inputs, not modified):

- `artifacts/golden_replay/bug_recurrence_event_log.json`
- `artifacts/golden_replay/bug_recurrence_history.json`
- `artifacts/golden_replay/trend_window/*`

## Helpers added

| Helper | Purpose |
|---|---|
| `build_recurrence_snapshot()` | Deterministic snapshot from explicit history path or in-memory payload; enriches `event_source` read-only from event log |
| `compare_recurrence_snapshots()` | Classifies key lifecycle and stable-subject movement |
| `build_bz_recurrence_movement_report()` | Assembles report payload with honesty mode |
| `write_bz_recurrence_movement_artifact()` | Writes `BZ_recurrence_movement.json` without mutating persistence files |

Reuses from `tests/helpers/replay_bug_recurrence.py`:

- `classify_recurrence_status()`
- `recurrence_owner()`
- `load_recurrence_event_log()`
- `normalized_recurrence_event_source()`
- `_protected_events_ordered()` (read-only event log traversal)

## Tests added

Recurrence movement suite in `tests/test_bz_protected_replay_trend_window_2.py`:

- `test_recurrence_newly_recurring`
- `test_recurrence_still_recurring`
- `test_recurrence_no_longer_recurring`
- `test_recurrence_count_increased`
- `test_recurrence_count_decreased`
- `test_recurrence_owner_changed_by_subject`
- `test_recurrence_investigate_first_changed_by_subject`
- `test_recurrence_event_source_changed_by_subject`
- `test_recurrence_ambiguous_subject_is_reported`
- `test_recurrence_baseline_establishment_mode_without_bw_snapshot`
- `test_recurrence_report_does_not_mutate_event_log`
- `test_recurrence_historical_snapshot_comparison_mode`

**Regression:** All BZ1 + BZ2 + BW trend tests pass (51 tests in BZ/BW trend modules).

## Artifact generated

`artifacts/golden_replay/trend_window_2/BZ_recurrence_movement.json`

## Historical BW snapshot availability

| Question | Answer |
|---|---|
| BW-time recurrence snapshot available? | **No** |
| Committed cumulative history usable as BW baseline? | **No** — would infer unsupported BW-time state |
| Default runner behavior | `baseline_establishment` mode |

No immutable recurrence snapshot was preserved at BW window closeout. The committed `bug_recurrence_history.json` is cumulative post-BW state and is referenced only as the **current** snapshot path, not as a historical baseline.

## Comparison mode used

| Field | Value |
|---|---|
| `comparison_mode` | `baseline_establishment` |
| `baseline_available` | `false` |
| `current_available` | `true` |
| `baseline_path` | `null` |
| `current_path` | `artifacts/golden_replay/bug_recurrence_history.json` |

Movement lists are intentionally empty in baseline-establishment mode so the report does not claim BW→BZ recurrence movement.

## Recurrence movement counts (committed artifact)

| Metric | Count |
|---|---:|
| `newly_recurring_count` | 0 |
| `still_recurring_count` | 0 |
| `no_longer_recurring_count` | 0 |
| `count_increased_count` | 0 |
| `count_decreased_count` | 0 |
| `owner_changed_count` | 0 |
| `investigate_first_changed_count` | 0 |
| `event_source_changed_count` | 0 |
| `ambiguous_subject_count` | 0 |

## Classification rules implemented

**By exact `recurrence_key`:**

- `newly_recurring` — absent in baseline, recurring/persistent in current
- `still_recurring` — recurring/persistent in both
- `no_longer_recurring` — recurring/persistent in baseline, not in current
- `count_increased` / `count_decreased` — same key, different `occurrence_count`
- `unchanged_count` — same key, same count (movement list only; not summarized)

**By stable subject `(category, field_path)`:**

- `owner_changed`, `investigate_first_changed`, `event_source_changed`
- `ambiguous_subjects` when multiple keys share a subject in either snapshot

## Known limitations

1. **No BW recurrence baseline in repo** — first committed BZ recurrence report is baseline establishment, not historical movement.
2. **`event_source` enrichment** — derived read-only from the latest protected event per key in `bug_recurrence_event_log.json`; history rows alone do not carry provenance.
3. **Lifecycle simplification** — movement uses occurrence count + status/stage heuristics; full timeline/governance lifecycle from `build_recurrence_lifecycle()` is not required for BZ2 but could enrich future reports.
4. **Subject ambiguity is conservative** — any multi-key subject group is flagged; no automatic disambiguation.
5. **Historical mode requires explicit baseline path** — `--bz-recurrence-baseline` must point to a preserved snapshot file; cumulative history is never auto-selected as baseline.

## Readiness for BZ3

| Prerequisite | BZ2 status |
|---|---|
| Recurrence movement helper module | Ready |
| Honest baseline-establishment mode | Ready |
| Historical snapshot comparison path | Ready (CLI + tests) |
| No mutation safety | Ready (test-covered) |
| BZ1 replay-key movement | Ready (unchanged, still passes) |
| BZ window Markdown summary (`BZ_protected_replay_trend_window_2.{json,md}`) | **Not started** |
| Closeout doc/command locks | **Not started** (BZ4) |
| Preserved recurrence baseline capture workflow | **Recommended before claiming historical movement in committed artifacts** |

**Recommendation:** Proceed to BZ3 (fixtures + integration proof) and BZ4 (closeout). To produce a non-empty committed recurrence movement report, first preserve an explicit baseline snapshot (for example at the next trend window run) and rerun with `--bz-recurrence-baseline`.

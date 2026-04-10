# Manual gauntlet aggregation — reference

This document describes the behavior of [`tools/aggregate_manual_gauntlets.py`](../tools/aggregate_manual_gauntlets.py) as implemented. Use it when you need to run or interpret aggregate reports without reading the source.

## Role

- **Read-only.** The tool does not run gauntlets or mutate session data; it only reads artifact files and writes report files.
- **Post-hoc.** Run it after one or more manual gauntlet runs have produced `*_summary.json` (and optional siblings) under your artifacts tree.

## Discovery

- **Root:** `--artifacts-dir` (default: repository `artifacts/manual_gauntlets`).
- **Pattern:** `Path.rglob("*_summary.json")` under that directory (recursive).
- If the artifacts directory is missing or not a directory, a warning is recorded; the run still completes with zero discovered summaries unless you point `--artifacts-dir` elsewhere.

## Sibling inference

For each summary path `{parent}/{base}_summary.json`, the tool assumes siblings in **`parent`**:

| Sibling | Filename | Required |
|--------|----------|----------|
| Summary | `{base}_summary.json` | Yes (this is the scan anchor) |
| Key events | `{base}_key_events.json` | No |
| Snippets | `{base}_snippets.json` | No |
| Transcript | `{base}_transcript.md` | No |

`{base}` is the filename with the `_summary.json` suffix removed. If a sibling is **missing**, the run is still included; optional paths in the normalized record are left empty. **No warning** is emitted solely for a missing optional file. **Malformed** sibling files (read errors, invalid JSON, or JSON that is not the expected array shape where required) add **warnings** and skip that file’s contribution; the run remains in the aggregate when the summary is valid.

## Normalization (summary → run record)

- **`operator_verdict`** — taken from the summary when present.
- **`operator_notes`** — taken from `operator_notes`, or if absent, from legacy **`notes`** (same string field semantics).
- **`transcript_path`** — from the summary when set; otherwise, if `{base}_transcript.md` exists beside the summary, that path is filled in.
- **`event_count`** — from the summary when present; else, if `{base}_key_events.json` exists and is a JSON array, the count is the array length.
- Internal sort helper: summary file **mtime** is stored for ordering when `started_utc` is missing or unparsable.

Malformed summaries (unreadable file, invalid JSON, or JSON root not an object) produce **warnings** and that file is **skipped** — other runs still aggregate.

## Filters (order and semantics)

Applied in this **exact** order:

1. **`--gauntlet-id`** — Compares the filter value (trimmed, lowercased) to each run’s `gauntlet_id` (lowercased). Empty or missing `gauntlet_id` in the summary does not match a non-empty filter.
2. **`--objective`** — Case-insensitive **substring** match: the needle must appear in **either** the run’s `label` **or** `description` (both compared with `casefold()`).
3. **`--verdict`** — Case-insensitive **exact** match on `operator_verdict` (trimmed, case-folded equality). Missing verdict does not match a non-empty filter.

Then:

4. **Sort** — Newest first: primary key is parsed `started_utc` (ISO, `Z` allowed); if missing or invalid, **fallback** is the summary file’s mtime.
5. **`--limit`** — Keeps only the first **N** runs **after** the sort. Non-negative; if omitted, all matching runs are kept.

## Metrics (aggregate JSON `metrics`)

Computed on the **final** filtered, sorted, possibly limited run list:

| Field | Meaning |
|--------|---------|
| `total_runs` | Count of runs in the report |
| `verdict_counts` | Counts by `operator_verdict`, normalized to **uppercase** keys (only runs with a non-empty verdict contribute) |
| `runs_with_verdict` | Runs that had a non-empty `operator_verdict` |
| `unique_gauntlet_ids` | Sorted list of distinct non-empty `gauntlet_id` values |
| `average_turn_count` | Mean of integer `turn_count` where present; omitted if none |
| `runs_with_events` | Runs with `event_count` an integer **> 0** |
| `runs_with_snippets` | Runs whose `snippets_path` file exists, parses as a JSON array, and has **at least one** element |
| `date_range_covered` | `{ "min", "max" }` as **string** min/max over non-empty `started_utc` values (lexicographic min/max on the stored strings, not re-parsed) |

## `--include-events` (key event rollup)

When set, the JSON includes `event_rollup` built only from **`key_events` arrays** (no full event objects in the aggregate):

- **`by_name`** — Counts of event `name` (non-empty strings after trim).
- **`by_stage`** — Counts of event `stage` (non-empty strings after trim).

Malformed `key_events` files add **warnings** and are skipped for rollup; other runs are unaffected. Non-dict elements inside arrays are skipped silently.

## Outputs

- **Directory:** `--output-dir` (default: `artifacts/manual_gauntlets/reports`).
- **Timestamp:** UTC, format `YYYY-MM-DDTHH-MM-SSZ` in the filename stem (hyphens in the time portion).
- **JSON (always):** `manual_gauntlet_aggregate_{timestamp}.json` — full aggregate including `runs` (compact fields per run), `metrics`, `filters`, `warnings`, and `event_rollup` (empty objects when `--include-events` is off).
- **Markdown (default):** `manual_gauntlet_aggregate_{timestamp}.md` — unless **`--json-only`** is passed.

## Markdown report behavior

- **Grouping:** Runs are listed under **## Runs by gauntlet**, grouped by `gauntlet_id` (missing id shown as `(unknown)`). Groups are ordered with `(unknown)` last, then alphabetically by id (case-insensitive).
- **Order within a group:** **FAIL → PARTIAL → PASS** (then other/non-matching verdicts last), then by `started_utc` string.
- **Operator notes:** **## Operator notes** lists runs that have non-empty operator notes (after normalization), same verdict ordering, then `started_utc`.
- **Optional snippets (`--include-snippets`):** **## Notable snippets (sampled)** — runs are prioritized by **FAIL → PARTIAL → PASS**, then newer summary mtime first. The renderer caps output at **8** snippet examples total, from at most **5** runs, with up to **2** snippets shown per run (before/after text truncated per line). Empty or invalid snippet files yield warnings and are skipped.

If **`--include-events`** is set and rollup is non-empty, the Markdown also includes **## Key event rollup (counts)** with up to **15** entries each for by-name and by-stage (ordered by descending count).

## Resilience and warnings

- One **bad** summary file: warning + skip that run; aggregation continues.
- Bad optional JSON (key events, snippets): warnings; that file’s contribution is skipped; other data still aggregates.
- Up to **50** warnings are listed in the Markdown **## Warnings** section; additional warnings are summarized as a count.
- The JSON aggregate always includes a `warnings` array with all collected messages.

## `--stdout`

When passed, prints a short human summary:

- Run count (`Runs analyzed`)
- Verdict breakdown (`Verdicts: FAIL=…` style) when counts exist
- Date range when `date_range_covered.min` and `.max` are both set
- Absolute paths for written JSON and, when applicable, Markdown

## Legacy compatibility

Summaries that predate `operator_notes` but include **`notes`** are treated as having operator notes when `operator_notes` is missing, so verdict filters and the notes section still behave predictably on older artifacts.

## Quick command recap

```bash
py -3 tools/aggregate_manual_gauntlets.py --include-events --include-snippets --stdout
py -3 tools/aggregate_manual_gauntlets.py --gauntlet-id g5 --limit 10 --verdict FAIL --json-only
```

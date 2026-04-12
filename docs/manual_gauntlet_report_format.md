# Manual gauntlet report artifacts — JSON reference

This doc describes the **purposes** and **typical top-level shapes** of the JSON files emitted by `tools/run_manual_gauntlet.py` next to the Markdown transcript. It is descriptive: field sets may evolve with the engine while staying backward-oriented for humans and reviewers.

All paths live under `artifacts/manual_gauntlets/` and share a common basename with the transcript (see `docs/manual_gauntlets.md`).

---

## `summary.json`

**Purpose:** Run header and bookkeeping: which gauntlet ran, when, from which git revision, how many turns, and where the transcript lives. Intended as the first file a reviewer opens.

**Typical top-level shape:** a single JSON object (not wrapped in an array). Expect keys along the lines of:

- `gauntlet_id`, `label`, `description` — from the gauntlet catalog
- `started_utc` — UTC start timestamp for the run
- `git_branch`, `git_commit`
- `mode` — e.g. preset templates vs freeform
- `hard_reset_before_run`, `turn_count`
- `transcript_path` — absolute path to the sibling `_transcript.md`
- `report_version` — integer schema hint for the bundle
- `event_count` — number of distilled key events
- `raw_trace_written` — whether `_raw_trace.json` was emitted this run
- `operator_verdict`, `notes` — reserved for human follow-up; often `null` until filled in
- `axis_tags` — optional behavioral axis tags for targeted behavioral gauntlets such as `G9` through `G12`
- `behavioral_eval` — optional advisory deterministic behavioral-evaluator payload attached during `--report` runs
- `behavioral_eval_warning` — optional compact warning when advisory behavioral evaluation could not be attached

**Behavioral notes:**

- `behavioral_eval` is **advisory only**; it does **not** determine manual pass/fail by itself.
- For gauntlets with `axis_tags`, the attached behavioral evaluation is filtered to those tagged axes.
- For gauntlets without `axis_tags`, the attached behavioral evaluation covers the full axis set.
- The runner prefers simplified behavioral rows shaped from snapshot-like records; if shaping fails for a row, it falls back to the raw dict row and continues.

---

## `key_events.json`

**Purpose:** A **distilled timeline** of high-signal pipeline moments (validators, repairs, bridges, emission gates, continuity signals, engine errors, etc.) extracted from per-turn debug / trace metadata. It is not a full engine dump.

**Typical top-level shape:** a JSON **array** of event objects. Each object commonly includes:

- `turn` — 1-based turn index
- `stage` — coarse category (e.g. validator, repair, emission_debug)
- `name` — specific signal or subsystem label
- `status` — outcome or short status string
- `details` — small object with trimmed fields (keys and string values are capped in the implementation)

**Notes:**

- Events are **derived** from whatever debug/trace structure the chat path exposes; naming follows that metadata, not a frozen public API.
- Duplicates are collapsed when the implementation considers two events identical.

---

## `snippets.json`

**Purpose:** A **small** set of concrete excerpts that illustrate problems or interesting paths (e.g. repair before/after, fallback responses, suspicious speaker patterns, engine errors).

**Typical top-level shape:** a JSON **array** of snippet objects. Each object commonly includes:

- `turn`
- `kind` — e.g. repair, fallback, heuristic flag, error
- `before`, `after` — optional text excerpts
- `reason` — short human-readable explanation

**Notes:**

- The list is **intentionally capped** (few items per run).
- Text fields are **truncated** to keep artifacts paste-friendly and to avoid huge files.

---

## `raw_trace.json`

**Purpose:** **Deep debugging only** — a much fuller serialization of the per-turn records the CLI collected (under a top-level wrapper). Use when `summary` / `key_events` / `snippets` are not enough to reproduce or explain a bug.

**Typical top-level shape:** a JSON object, commonly including:

- `records` — array of per-turn record objects (structure mirrors what the transcript runner captures from `chat`)
- `report_version` — same integer as in `summary.json`

**Notes:**

- Content may be **sanitized and truncated** for safety and size (e.g. very long strings shortened in the dump).
- **Do not** paste this file wholesale into chat; prefer the compact artifacts or attach the file out-of-band.

---

## See also

- `docs/manual_gauntlets.md` — artifact naming, CLI flags, and what to send when giving feedback

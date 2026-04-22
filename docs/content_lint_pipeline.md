# Author-time scene content lint (Objective #10)

This document describes the **implemented** author-time content lint system and the **`tools/run_content_lint.py`** CLI as covered by **`tests/test_content_lint_tool.py`** and engine tests in **`tests/test_content_lint.py`**. It is not a design wishlist: if something is not wired here, it is not claimed as current behavior.

## Architecture (what actually runs)

| Piece | Role |
| --- | --- |
| **`game/content_lint.py`** | Canonical **deterministic author-time** lint engine. Composes strict validation, clue/schema checks, heuristic translation, and graph analysis into a structured `ContentLintReport` (`ContentLintMessage` list + counts). **Not** imported for normal gameplay turns. |
| **`game/validation.py`** | **Strict runtime** scene rules. Fail-fast paths use `validate_scene` / `validate_all_scenes`; the lint engine uses **`collect_scene_validation_issues`** to gather the same rules **without** raising, so the author-time report can list every issue. |
| **`game/scene_lint.py`** | **Heuristic** warnings (player-anchor, sensory overlap, etc.). `content_lint` calls it and maps warnings to stable **`ContentLintMessage` codes** (e.g. `scene.missing_player_anchor`). |
| **`game/scene_graph.py`** | **Graph** construction and connectivity data used by `content_lint` for reachability warnings (`graph.unreachable_scene`, load hints, etc.). |
| **`tools/run_content_lint.py`** | **CLI**: loads `<scene_id>.json` envelopes from disk, optionally loads `data/world.json` for clue context, calls **`lint_all_content`**, prints a human report, optional JSON artifact, returns a process exit code. |

## Runtime vs author-time ownership

- **Runtime validation** (`game/validation.py`) remains **fail-fast** where the engine loads or checks scenes (same structural rules the game relies on). It protects **startup/runtime integrity** for paths that call it; it is not replaced by the lint CLI.
- **Content linting** is **author-time**, **deterministic**, and **richer in reporting** (multiple messages per scene, warnings + errors, graph pass, clue-only checks). It is safe to run in an editor or terminal without starting the server.
- The **content lint pipeline** is **not on the gameplay hot path**: normal chat/engine flows do not call `lint_all_content` or the CLI per turn.

## CLI: `tools/run_content_lint.py`

The runner only defines the flags below. Defaults match `game.storage.SCENES_DIR` (repository **`data/scenes`**) when `--scenes-dir` is omitted.

### Flags (complete list)

| Flag | Behavior |
| --- | --- |
| **`--scenes-dir PATH`** | Directory of `*.json` scene envelopes (`<id>.json`). Default: resolved `data/scenes` via `SCENES_DIR`. |
| **`--json-out PATH`** | After linting, writes **`json.dumps(report.as_dict(), …)`** to `PATH` (creates parent directories). Same canonical schema as `ContentLintReport.as_dict()` in code. |
| **`--quiet`** | Prints **only** the one-line summary (see Output). No per-scene grouped sections. |
| **`--fail-on-warnings`** | If there are **warnings but zero errors**, exit code **`2`**. Without this flag, warnings-only still exits **`0`**. |
| **`--scene-id ID`** | **Repeatable**. Lint **only** the listed ids. Tokens may be **comma-separated** per argument. Order is normalized (duplicate ids dropped; loaded in sorted id order). **Unknown** ids (no matching `.json` on disk under `--scenes-dir`) → **exit `1`**, message on **stderr**, **empty stdout**. |

### Example commands (copy-paste accurate)

From the repository root:

```powershell
python tools/run_content_lint.py
```

```powershell
python tools/run_content_lint.py --scenes-dir data/scenes
```

```powershell
python tools/run_content_lint.py --scene-id tavern
```

```powershell
python tools/run_content_lint.py --scene-id hub --scene-id leaf
```

```powershell
python tools/run_content_lint.py --scene-id a,b
```

```powershell
python tools/run_content_lint.py --quiet
```

```powershell
python tools/run_content_lint.py --fail-on-warnings
```

```powershell
python tools/run_content_lint.py --json-out artifacts/content_lint/report.json
```

Flags can be combined (e.g. `--scenes-dir data/scenes --scene-id hub --json-out out/lint.json --quiet`).

**Optional context file:** the tool attempts **`data/world.json`** at the repo root (same layout as runtime data). If missing, invalid JSON, or not an object, world context is simply omitted; lint still runs.

## Subset linting semantics (`--scene-id`)

When **`--scene-id`** is used, behavior is deliberately split between **reference validation** and **graph reachability** (see `tools/run_content_lint.py` and `lint_all_content` in `game/content_lint.py`):

1. **Strict cross-scene reference checks** use the **full on-disk scene registry** under `--scenes-dir`: every `*.json` stem is **`reference_known_scene_ids`**. Exit targets and affordance transition targets are validated against **all ids present on disk**, not only the loaded subset.
2. **Graph reachability** uses **`graph_known_scene_ids = set(loaded scene keys)`** only. The graph builder’s universe is **the loaded subset**, so reachability and `graph.unreachable_scene` warnings are **not** computed for scenes that were never loaded into this run.

**Consequences (as tested):**

- An exit to **`leaf`** while linting only **`hub`** is **valid** if **`leaf.json` exists on disk**, even though `leaf` was not loaded into memory for that run → no `exit.unknown_target` for that case.
- A target id **not** on disk (no json stem) still **`exit.unknown_target`** (or related strict codes) → **exit `1`** when those validate as errors.
- Scenes **not** in the subset **do not** produce **`graph.unreachable_scene`** warnings for that subset run (avoids bogus “unreachable” noise for authors who are iterating on one scene). A **full** run without `--scene-id` still sees graph warnings across **all** loaded ids (entire directory), as in **`tests/test_content_lint_tool.py`** (`test_subset_cli_no_unreachable_warnings_for_unloaded_scenes`).

## Exit codes (process)

These match **`tests/test_content_lint_tool.py`**:

| Code | Meaning |
| --- | --- |
| **`0`** | Success: **no errors**. Warnings may be present unless you care to treat them separately; without `--fail-on-warnings`, warnings-only is still **`0`**. |
| **`1`** | **Blocking** lint result: **one or more error-severity messages** in the report **or** the tool failed before/during load: **unknown `--scene-id`**, **invalid JSON**, **empty file**, **unreadable** scene file, etc. **Lint errors and operator/file failures both use `1` today** (there is no separate exit-code family for “tool vs lint”). |
| **`2`** | **`--fail-on-warnings`** was set, there are **warnings**, and **error_count == 0**. |

## Output behavior

### Normal mode (no `--quiet`)

1. **Summary line** to stdout: `scenes_checked=<n> errors=<e> warnings=<w>` (single line, newline-terminated).
2. Unless `--quiet`, **grouped messages**: for each scene id (sorted), a header `[<scene_id>]` and indented lines `  <severity>: <code>: <message>`. Messages with no `scene_id` appear under **`[global]`**.

### `--quiet`

Stdout is **only** the summary line. No `[scene]` sections (see **`tests/test_content_lint_tool.py`** `test_cli_quiet_prints_only_summary_line`).

### `--json-out`

Writes a JSON object with **exactly** these top-level keys (see test `test_cli_json_out_matches_canonical_as_dict`):

- `ok`, `error_count`, `warning_count`, `messages`, `scene_ids_checked`

Each message is the **`ContentLintMessage.as_dict()`** shape: at minimum `severity`, `code`, `message`; optional `scene_id`, `path`, `evidence`. **`tests/test_content_lint_tool.py`** asserts JSON output **matches** the engine’s `report.as_dict()` for the same disk state and preserves **canonical engine codes** (e.g. `test_cli_json_preserves_engine_message_codes_unchanged`).

**Stderr vs stdout on failures:** for early failures (unknown ids, bad JSON), the tool may write diagnostics to **stderr** and leave **stdout empty** (see tests for unknown id and invalid JSON).

## Practical workflows

- **Lint everything in the default registry:**  
  `python tools/run_content_lint.py`  
  (Uses `data/scenes` by default.)

- **Lint one scene while editing:**  
  `python tools/run_content_lint.py --scene-id <id>`  
  Cross-scene targets still resolve against **all** `*.json` files in that directory; graph noise from unrelated scenes is suppressed.

- **Machine-readable output for audits or later automation:**  
  `python tools/run_content_lint.py --json-out <path>`  
  The schema is stable **`report.as_dict()`**. **CI enforcement, pre-commit hooks, and server startup integration of this CLI are not part of the shipped behavior** unless separately added; you can wire the same command into a pipeline when ready.

## Design notes (why it is shaped this way)

- **`collect_scene_validation_issues`** — Returns **all** strict violations for a scene in one pass with ordering aligned to the first `validate_scene` failure, but **without raising**. The lint engine can emit a full author-time list and map each issue to a stable **`ContentLintMessage`** code.

- **Reuse `report.as_dict()`** — The CLI JSON artifact is literally the engine report dict. One schema avoids drift between “CLI JSON” and in-process reports.

- **Subset mode: `reference_known_scene_ids` vs `graph_known_scene_ids`** — Splitting the **id universe for strict refs** (full disk registry) from the **id universe for graph reachability** (loaded subset only) **reduces false positives** on `graph.unreachable_scene` while **preserving** real **`exit.unknown_target`** / **`action.unknown_target_scene`** checks against scenes that exist on disk but were not part of the partial load.

---

**Further reading:** Engine rules and message codes are exercised in **`tests/test_content_lint.py`**. CLI and subset semantics are pinned in **`tests/test_content_lint_tool.py`**.

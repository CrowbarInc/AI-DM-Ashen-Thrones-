# Author-time scene content lint (Objective #10)

This document describes the **implemented** author-time content lint system and the **`tools/run_content_lint.py`** CLI (plus the thin automation entrypoint **`tools/ci_content_lint.py`**, same behavior and exit codes) as covered by **`tests/test_content_lint_tool.py`**, engine tests in **`tests/test_content_lint.py`**, bundle matrices in **`tests/test_content_lint_bundle.py`**, and **N2 closure** regression locks in **`tests/test_content_lint_n2_closure.py`** (determinism, dedup/noise, severity discipline, ownership boundary). It is not a design wishlist: if something is not wired here, it is not claimed as current behavior. Human-readable rollups of **`--json-out`** reports are implemented by **`tools/summarize_content_lint.py`** (**`tests/test_summarize_content_lint.py`**).

## Scope model (Objective N2): loaded bundle, reference registry, validation

These three scopes are **enforced in code**, not implied by prose. **`ContentBundleSnapshot`** (see `game/content_lint.py`) materializes enough of them that every **`campaign.reference.starting_scene_unknown`** and **`scene.reference.npc_scene_link_unknown`** error carries the same resolved id lists the engine used.

### 1. Loaded bundle scope

**Definition:** In-memory inputs to a single lint run: the `scenes` dict (keys = loaded envelope stems), optional `world`, optional `campaign`.

**What runs here:** Every per-scene pass (`collect_scene_validation_issues`, clue integrity, heuristics) iterates **only** keys present in `scenes`. Bundle passes read `world` / `campaign` if provided.

**What does not happen:** A scene file that exists on disk but was **not** loaded into `scenes` is **not** inspected for scene-level rules in that run.

### 2. Reference registry scope (scene ids)

**Definition:** The set of scene ids treated as **valid link targets** for strict cross-scene validation **and** for bundle rules that tie `world.npcs` / `campaign.starting_scene_id` to scenes.

**Engine source:** `lint_all_content(..., reference_known_scene_ids=...)`. If the argument is **omitted**, the registry is exactly **`set(scenes.keys())`** (loaded envelope stems only). If the argument is **provided** (subset CLI: all `*.json` stems under `--scenes-dir`), that set is authoritative.

**Materialization on the bundle:** `build_content_bundle(..., world_scene_registry_ids=sorted(reference_known))` stores the explicit overlay in **`world_scene_registry_ids`**, sorts **`loaded_envelope_ids`**, computes **`resolved_world_scene_link_registry_ids`** = sorted union of (ids derived from loaded envelopes and inner `scene.id` values) ∪ (explicit overlay), and sets **`reference_registry_extension_ids`** = sorted \((\text{resolved}) \setminus (\text{ids derivable from loaded envelopes alone})\). There is **no** silent widening: in-process callers that omit `world_scene_registry_ids` when building a bundle manually get **loaded-only** link checks unless they also pass ids explicitly.

### 3. Validation scope (what may error vs what is out of scope)

**Strict scene validation and heuristics** use **`reference_known_scene_ids`** as defined in (2). **`graph_known_scene_ids`** defaults to the same set; in subset mode the CLI passes **`set(loaded keys)`** so **`graph.unreachable_scene`** is evaluated **only among loaded scenes** (see below).

**Bundle world-to-scene link rules** (`campaign.reference.starting_scene_unknown`, `scene.reference.npc_scene_link_unknown`) error **if and only if** the referenced scene id is **absent** from **`resolved_world_scene_link_registry_ids`**. They do **not** error for ids that appear only in the reference overlay and not in `scenes` (subset correctness).

**Not suppressed:** If an id is missing from both loaded-derived ids **and** the explicit reference overlay, the upgraded **error** severities fire. Nothing is downgraded to a warning to hide incomplete context.

**Affiliation rule (`scene.reference.npc_affiliation_unknown`):** Uses **`world.settlements`** and **`world.factions`** only; it does **not** use the scene reference registry. Subset vs full does not change that rule’s inputs beyond whatever `world` dict was passed in.

## Architecture (what actually runs)

| Piece | Role |
| --- | --- |
| **`game/content_lint.py`** | Canonical **deterministic author-time** lint engine. Composes strict validation, clue/schema checks, heuristic translation, and graph analysis into a structured `ContentLintReport` (`ContentLintMessage` list + counts). **Not** imported for normal gameplay turns. |
| **`game/validation.py`** | **Strict runtime** scene rules. Fail-fast paths use `validate_scene` / `validate_all_scenes`; the lint engine uses **`collect_scene_validation_issues`** to gather the same rules **without** raising, so the author-time report can list every issue. |
| **`game/scene_lint.py`** | **Heuristic** warnings (player-anchor, sensory overlap, etc.). `content_lint` calls it and maps warnings to stable **`ContentLintMessage` codes** (e.g. `scene.missing_player_anchor`). |
| **`game/scene_graph.py`** | **Graph** construction and connectivity data used by `content_lint` for reachability warnings (`graph.unreachable_scene`, load hints, etc.). |
| **`tools/run_content_lint.py`** | **CLI**: loads `<scene_id>.json` envelopes from disk; loads **`world.json`** only via deterministic rules (**`--world-json`**, **`--no-world`**, or default **`<parent of --scenes-dir>/world.json`**); calls **`lint_all_content`**; prints a human report; optional JSON artifact; returns a process exit code. |
| **`tools/ci_content_lint.py`** | **CI entry**: forwards to the same **`main()`** as **`run_content_lint.py`** (same argv and exit codes). GitHub Actions uses this path in **`.github/workflows/content-lint.yml`** so automation depends on one stable script name. |
| **`tools/summarize_content_lint.py`** | Read-only presenter for canonical **`--json-out`** JSON: severity totals, a **family rollup** (“where to look first”), top codes, **counts by message code family prefix** (first path segment), per-scene aggregates, and a short hint for bundle-level prefixes. Does not execute the engine. |

## Scene-level vs bundle-level passes (Objective N2)

**Scene-level passes (unchanged contract)** — still run first, per loaded scene id, plus the graph aggregation pass:

- Strict validation issues via **`collect_scene_validation_issues`** (mapped to stable codes such as `exit.unknown_target`, `interactable.duplicate_id`, …).
- **`lint_scene_clue_integrity`** (clue schema, duplicates within scene, author-only interactable clue refs when `world` is provided).
- **`lint_scene_heuristic_warnings`** (translated `scene_lint` warnings).
- **`lint_scene_graph_connectivity`** (load hints, reachability warnings).

**Bundle-level governance** — runs **after** the scene-level parts inside **`lint_all_content`**. It builds a read-only **`ContentBundleSnapshot`** (loaded scene map + optional `world` + optional `campaign` + derived **`BundleContentIndex`** + explicit scene-id overlay **`world_scene_registry_ids`** + **`loaded_envelope_ids`** + **`reference_registry_extension_ids`** + **`resolved_world_scene_link_registry_ids`**) and runs **`lint_bundle_governance`**, which merges deterministic sub-passes. Extraction **does not mutate** authored JSON dicts; id keys used for duplicate detection use **`bundle_compare_id`** / `normalize_id` for comparison only, while messages carry **authored** strings in **`evidence`**.

**Reference registry for world-to-scene bundle rules:** `lint_all_content` always passes the same **`reference_known_scene_ids`** universe used for strict exit/action targets into **`build_content_bundle(..., world_scene_registry_ids=sorted(reference_known))`**. NPC `location` / `scene_id` / `origin_scene_id` and optional **`campaign.starting_scene_id`** are checked against **`resolved_world_scene_link_registry_ids`** (see **Scope model** above). Subset runs stay aligned with **`tests/test_content_lint.py`** `test_subset_lint_resolves_world_npc_location_against_reference_registry` and **`tests/test_content_lint_bundle.py`** extension-id tests.

**Duplicate / collision discipline:** **`bundle.duplicate_id.*`** fires on **exact duplicate compare-keys within one world list** (or cross-envelope inner `scene.id` collisions for **`bundle.duplicate_id.scene`**). **`faction.reference.progression_uid_collision`** is **suppressed** when every colliding faction row shares the same authored id string (those cases are **`bundle.duplicate_id.faction`** only). **`bundle.contradiction.clue_registry_row_conflict`** covers incompatible **world-only** clue rows for the same canonical clue id; ambiguous world definitions **do not** also emit **`bundle.contradiction.clue_scene_vs_world_definition`** for the same underlying conflict.

When multiple `world.clues` registry keys point at the same row `id` but keys differ from that `id`, **`clue.reference.world_registry_key_mismatch`** still applies per row (ambiguous registry shape). That is a **distinct** failure mode from **`bundle.contradiction.clue_registry_row_conflict`** (incompatible JSON bodies for the same canonical id); both may appear together and are not treated as duplicate emissions of one issue.

**Regression fixture matrix (N2 closure):** **`tests/test_content_lint_n2_closure.py`** composes a small table of bundle states (clean; duplicate npc id; broken world↔scene refs; clue row conflict + registry mismatches; clock outer key vs row id; subset-safe bundle with explicit scene-id overlay; mixed scene strict error + bundle NPC link). Rows assert **`lint_bundle_governance`** code sets and subset alignment without a separate fixture framework.

**Determinism:** Per-scene work iterates **`sorted(scenes.keys())`**. Bundle passes that walk all loaded scenes use **`sorted(bundle.scenes)`** so multi-scene findings (e.g. **`bundle.contradiction.clue_scene_vs_world_definition`**) do not depend on dict insertion order. Index fingerprints (**`bundle_index_fingerprint`**) are stable for identical content regardless of envelope dict order. Repeated **`lint_all_content`** on the same in-memory inputs produces identical **`report.as_dict()`** when compared with sorted JSON serialization (locked in tests).

### Implemented bundle message codes (stable)

| Code | Severity | Meaning |
| --- | --- | --- |
| **`bundle.duplicate_id.npc`**, **`.faction`**, **`.project`** | error | Duplicate compare-keys within the corresponding `world` list. |
| **`bundle.duplicate_id.scene`** | warning | Two or more loaded envelopes share the same inner `scene.id` compare key (non-blocking ambiguity for tooling). |
| **`bundle.reference.event_log_source_unknown_faction`** | error | `world.event_log` entry with `type` starting `faction_` has `source` not matching any `world.factions[].id`. |
| **`bundle.contradiction.clue_registry_row_conflict`** | error | Multiple `world.clues` registry keys share the same canonical row `id` but JSON rows differ. |
| **`bundle.contradiction.clue_scene_vs_world_definition`** | error | Scene `discoverable_clues` structured id matches a unique world clue row by compare id, but non-empty `text` differs. |
| **`campaign.reference.starting_scene_unknown`** | error | When **`campaign.starting_scene_id`** is present, it is absent from **`resolved_world_scene_link_registry_ids`** (see bundle snapshot; evidence duplicates this as **`known_scene_ids`** for backward compatibility). |
| **`scene.reference.npc_scene_link_unknown`** | error | NPC `location`, `origin_scene_id`, or `scene_id` (when set) is absent from **`resolved_world_scene_link_registry_ids`**. |
| **`scene.reference.npc_affiliation_unknown`** | error | NPC `affiliation` (when set) matches neither any **`world.settlements[].id`** nor any faction compare key derived from **`world.factions`** `id` / `name`. |
| **`clue.reference.world_registry_key_mismatch`** | error | `world.clues` registry key ≠ row `id` when both are non-empty. |
| **`world_state.reference.clock_key_row_id_mismatch`** | error | `world_state.clocks` outer key ≠ clock row `id` when both are present. |
| **`faction.reference.progression_uid_collision`** | error | Two+ faction rows share the same compare key but **different** authored labels (duplicate identical ids remain **`bundle.duplicate_id.faction`** only). |

### Reserved / deferred (not implemented)

- **`bundle.reference.*`** beyond event-log faction sources (e.g. generic cross-subsystem hooks).
- **`clue.reference.*`** beyond world registry key vs row `id` (no extra clue-target graph in authored JSON today).
- **Project / faction / world_state anchors** — canonical `world.projects` rows (`game/schema_contracts.py`) do not carry structured faction or `world_state` link fields; skipped until the authored contract adds them.
- **Scene JSON → `world_state` flags** — shipped scenes do not encode structured `world_state` references; skipped.
- **Rich `campaign.json` → scene graph** — shipped `data/campaign.json` has no scene-id list; only optional **`starting_scene_id`** is validated when authors add it.

## Runtime vs author-time ownership

- **Runtime validation** (`game/validation.py`) remains **fail-fast** where the engine loads or checks scenes (same structural rules the game relies on). It protects **startup/runtime integrity** for paths that call it; it is not replaced by the lint CLI.
- **Content linting** is **author-time**, **deterministic**, and **richer in reporting** (multiple messages per scene, warnings + errors, graph pass, clue-only checks). It is safe to run in an editor or terminal without starting the server.
- The **content lint pipeline** is **not on the gameplay hot path**: normal chat/engine flows do not call `lint_all_content` or the CLI per turn.
- **Static guard:** no other module under **`game/`** (except **`game/content_lint.py`**) should import the lint engine; **`tests/test_content_lint_n2_closure.py`** fails if a new runtime import appears. Tools (`tools/run_content_lint.py`) and tests may import it freely.

## CLI: `tools/run_content_lint.py`

The runner only defines the flags below. Defaults match `game.storage.SCENES_DIR` (repository **`data/scenes`**) when `--scenes-dir` is omitted. For **`python tools/run_content_lint.py --help`**, see the epilog for **full vs subset**, **world resolution**, and **exit codes** (ASCII-safe for Windows consoles).

### Recommended invocation (local, subset, CI)

- **Local (full bundle-aware run, default paths):**  
  `python tools/run_content_lint.py`  
  Loads all scenes under `data/scenes` and, when present, `data/world.json`. Same engine as CI.

- **Local (one scene while editing, still bundle-safe for refs):**  
  `python tools/run_content_lint.py --scene-id <id>`  
  Cross-scene exit/action targets still resolve against **every** `*.json` stem on disk; graph warnings stay scoped to the loaded subset. Add **`--json-out tmp/lint.json`** if you want a machine-readable artifact for **`summarize_content_lint.py`**.

- **CI / automation (stable entry path):**  
  `python tools/ci_content_lint.py --json-out artifacts/content_lint/ci_report.json`  
  Optional: `python tools/summarize_content_lint.py --input artifacts/content_lint/ci_report.json` for a human rollup. The workflow **`.github/workflows/content-lint.yml`** runs Phase 1 with **`continue-on-error: true`** (informational); to **fail the job** on findings, replace that step with `python tools/ci_content_lint.py` (no `continue-on-error`) or enable Phase 2 (`--fail-on-warnings`) when your content is clean enough.

- **Interpreting bundle-level (N2) failures at a glance:**  
  In **CLI** output, the bracket before each code is the **family** prefix (first segment of the code, e.g. `bundle`, `campaign`, `scene`). In **`summarize_content_lint.py`**, use the **“where to look first (code family rollup)”** section: a large **`bundle`** or **`scene`** row usually means duplicate ids, contradictions, or world↔scene reference errors under those prefixes (see the **Implemented bundle message codes** table above). Codes starting with **`bundle.`**, **`campaign.reference.`**, **`scene.reference.`**, **`clue.reference.`**, **`faction.reference.`**, or **`world_state.reference.`** are the cross-system governance surface.

### Flags (complete list)

| Flag | Behavior |
| --- | --- |
| **`--scenes-dir PATH`** | Directory of `*.json` scene envelopes (`<id>.json`). Default: resolved `data/scenes` via `SCENES_DIR`. |
| **`--json-out PATH`** | After linting, writes **`json.dumps(report.as_dict(), …)`** to `PATH` (creates parent directories). Same canonical schema as `ContentLintReport.as_dict()` in code. |
| **`--quiet`** | Prints **only** the one-line summary (see Output). No per-scene grouped sections. |
| **`--fail-on-warnings`** | If there are **warnings but zero errors**, exit code **`2`**. Without this flag, warnings-only still exits **`0`**. |
| **`--scene-id ID`** | **Repeatable**. Lint **only** the listed ids. Tokens may be **comma-separated** per argument. Order is normalized (duplicate ids dropped; loaded in sorted id order). **Unknown** ids (no matching `.json` on disk under `--scenes-dir`) → **exit `1`**, message on **stderr**, **empty stdout**. |
| **`--world-json PATH`** | Load **`world.json`** from exactly **`PATH`** (must be a regular file). **Fails with exit `1`** if the path is missing, empty, invalid JSON, or not a JSON object. Takes precedence over the default adjacent file. Mutually exclusive with **`--no-world`**. |
| **`--no-world`** | Do not load any world bundle: skips **`world.json`** even when present adjacent to **`--scenes-dir`**. Mutually exclusive with **`--world-json`**. |

### Example commands (copy-paste accurate)

From the repository root:

```powershell
python tools/run_content_lint.py
```

(`python tools/ci_content_lint.py` with the same flags is equivalent and is the path CI uses.)

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

### `world.json` resolution (deterministic; no guessing)

Exactly **one** of three mutually exclusive branches applies, in this order:

1. **`--no-world`** → `world` is **`None`**. No file is read.
2. **`--world-json PATH`** → read **`PATH`**; **exit `1`** on missing file, empty file, **`json.JSONDecodeError`**, or non-object root. `world` is that object.
3. **Otherwise** → read **`<parent of --scenes-dir>/world.json`** if it exists, is non-empty, parses as JSON, and has an object root; otherwise **`world` is `None`**.

**Isolation guarantee:** A temp pack laid out as **`some_root/scenes/*.json`** with **no** `some_root/world.json` **never** reads the repository’s **`data/world.json`**, because resolution is **only** relative to **`--scenes-dir`’s parent**, not the repository root or current working directory. **`tests/test_content_lint_tool.py`** covers **`--no-world`** and explicit **`--world-json`**.

## Subset linting semantics (`--scene-id`)

When **`--scene-id`** is used, behavior is deliberately split between **reference validation** and **graph reachability** (see `tools/run_content_lint.py` and `lint_all_content` in `game/content_lint.py`):

1. **Strict cross-scene reference checks** use the **full on-disk scene registry** under `--scenes-dir`: every `*.json` stem is **`reference_known_scene_ids`**. Exit targets and affordance transition targets are validated against **all ids present on disk**, not only the loaded subset. The **same** registry is fed into bundle governance as **`world_scene_registry_ids`** so world NPC scene links and optional **`campaign.starting_scene_id`** do not false-positive on unloaded neighbors.
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
2. Unless `--quiet`, **grouped messages**: for each scene id (sorted), a header `[<scene_id>]` and indented lines `  <severity> [<code_family>]: <code>: <message>` where **`<code_family>`** is the substring of **`code`** before the first **`.`** (e.g. `exit.unknown_target` → `exit`). Messages with no `scene_id` appear under **`[global]`** using the same line format.

### `--quiet`

Stdout is **only** the summary line. No `[scene]` sections (see **`tests/test_content_lint_tool.py`** `test_cli_quiet_prints_only_summary_line`).

### `--json-out`

Writes a JSON object with **exactly** these top-level keys (see test `test_cli_json_out_matches_canonical_as_dict`):

- `ok`, `error_count`, `warning_count`, `messages`, `scene_ids_checked`

Each message is the **`ContentLintMessage.as_dict()`** shape: at minimum `severity`, `code`, `message`; optional `scene_id`, `path`, `evidence`. **`tests/test_content_lint_tool.py`** asserts JSON output **matches** the engine’s `report.as_dict()` for the same disk state and preserves **canonical engine codes** (e.g. `test_cli_json_preserves_engine_message_codes_unchanged`).

**Stderr vs stdout on failures:** for early failures (unknown ids, bad JSON), the tool may write diagnostics to **stderr** and leave **stdout empty** (see tests for unknown id and invalid JSON).

## Design notes (why it is shaped this way)

- **`collect_scene_validation_issues`** — Returns **all** strict violations for a scene in one pass with ordering aligned to the first `validate_scene` failure, but **without raising**. The lint engine can emit a full author-time list and map each issue to a stable **`ContentLintMessage`** code.

- **Reuse `report.as_dict()`** — The CLI JSON artifact is literally the engine report dict. One schema avoids drift between “CLI JSON” and in-process reports.

- **Subset mode: `reference_known_scene_ids` vs `graph_known_scene_ids`** — Splitting the **id universe for strict refs** (full disk registry) from the **id universe for graph reachability** (loaded subset only) **reduces false positives** on `graph.unreachable_scene` while **preserving** real **`exit.unknown_target`** / **`action.unknown_target_scene`** checks against scenes that exist on disk but were not part of the partial load. The same **`reference_known_scene_ids`** set is passed into **`build_content_bundle(..., world_scene_registry_ids=...)`** so bundle NPC / campaign scene references stay consistent with exit validation.

- **In-process `build_content_bundle` callers** — Passing **`world_scene_registry_ids=None`** (default) means the explicit overlay is empty: **`reference_registry_extension_ids`** is empty and **`resolved_world_scene_link_registry_ids`** equals ids from loaded scenes only. **`lint_all_content`** always passes **`sorted(reference_known)`** so CLI and in-process full runs stay aligned with strict validation.

---

**Further reading:** Engine rules and message codes are exercised in **`tests/test_content_lint.py`**. Bundle governance matrices live in **`tests/test_content_lint_bundle.py`**. CLI and subset semantics are pinned in **`tests/test_content_lint_tool.py`**. N2 regression locks (matrix, dedup, determinism, severity, ownership) are in **`tests/test_content_lint_n2_closure.py`**.

## Objective N2 completeness (author-time bundle governance)

**In scope today:** cross-file index (**`BundleContentIndex`** / **`ContentBundleSnapshot`**), reference integrity for the wired JSON fields (NPC↔scene, campaign start scene, clue registry consistency, clock id vs outer key, event log faction sources, inner scene id collisions, duplicate rows in world lists, faction progression compare-key collisions when not duplicate-id), and scene↔world clue text drift when the world side is unambiguous. **Offline / author-time only** (CLI + in-process **`lint_all_content`**), **no silent correction**, **subset vs full** explicit via reference registry + evidence payloads.

**Explicitly deferred (not incompleteness):** richer **`campaign.json`** scene graphs, structured anchors from **`world.projects`** into factions or `world_state`, scene-authored `world_state` references, and extra **`bundle.reference.*`** beyond event-log faction checks — the authored contract does not expose those links yet.

**Polish (optional later):** editor integrations and performance work on very large scene directories — not required for the correctness goal of N2. A minimal **CI entry script** and workflow are already wired (see **`tools/ci_content_lint.py`** and **`.github/workflows/content-lint.yml`**).

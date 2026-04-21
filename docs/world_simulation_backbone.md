# World simulation backbone (Objective #9 — landed)

The module `game.world_progression` is the **canonical seam** for **supported persistent world progression**: orchestration and normalization over **native** `world.json` roots only. It answers “What is progressing in the persistent world right now?” and applies small, schema-aware writes **in place** on those roots.

Regression and ownership guardrails: `tests/test_world_simulation_backbone_regressions.py`, `tests/test_world_simulation_backbone_ownership.py`.

---

## What the backbone owns

- A **read model**: deterministic, sorted lists of normalized **progression nodes** (in-memory view contract only; not a persisted subtree).
- **Write seams** that mutate, in place:
  - `world["projects"]`
  - `world["factions"]` (fields `pressure`, `agenda_progress`)
  - `world["world_state"]["clocks"]`
  - `world["world_state"]["flags"]`
- Optional **helper event rows** in the shape from `progression_event(...)` (type `world_progression`). Callers that must keep the player-facing `world["event_log"]` clean pass an **explicit detached list** as `event_log=` so those rows never reach the world document.

---

## What it explicitly does not own

- Any new persisted subtree such as `world["progression"]`, `session["world_progression"]`, or parallel JSON stores.
- **Session pressure clocks** in `game/clocks.py` (`session["clocks"]`). Session clocks remain session-local; the backbone does not read `session` for node iteration.
- **`world_state.counters`**. Counters are updated elsewhere (`game.world.apply_resolution_world_updates`, etc.) but are **not** modeled as progression nodes and do not appear in CTIR `world.progression` or backbone iterator output.
- **Top-level** `world["world_flags"]` (list) — canonical simulation flags for this seam live under `world["world_state"]["flags"]` per existing conventions.
- **Prompt assembly** as authority — `game.prompt_context` consumes **CTIR first**, then a **fallback** slice built with the same `compose_ctir_world_progression_slice(...)` over live `world` state. It must not call `game.ctir.build_ctir` (boundary tests enforce source shape).

---

## Persistent vs session distinction

| Layer | Owned progression surface |
|--------|----------------------------|
| **Persistent / `WORLD_STATE`** | `projects`, factions (`pressure`, `agenda_progress`), `world_state.flags`, `world_state.clocks` (world scope) |
| **Session-local** | Session clocks, interaction/scene session bags, counters — **out of scope** for the backbone iterator and CTIR `world.progression` lists |

---

## Native-root authority rule

Persistence remains exactly where it already was. Normalized nodes are **derived** on each call from these roots; no write path materializes a parallel authoritative progression tree.

| Concern | Native root |
|--------|-------------|
| Projects | `world["projects"]` |
| Faction pressure | `world["factions"][].pressure` |
| Faction agenda progress | `world["factions"][].agenda_progress` |
| World clocks | `world["world_state"]["clocks"]` |
| World flags | `world["world_state"]["flags"]` |

---

## CTIR bounded export rule

- **Build:** `game.ctir_runtime.build_runtime_ctir_for_narration` → `_slice_world` sets `world["progression"]` on the **CTIR object only** using `compose_ctir_world_progression_slice(world, changed_node_ids=...)` (not from `event_log` reconstruction).
- **Caps:** List lengths and `changed_node_ids` are capped (e.g. 32/64 budgets aligned with the backbone module constants). Payloads are compact dict rows (ids without redundant prefixes where safe, numeric progress/value fields, etc.).
- **`changed_node_ids` sources:** (1) `collect_changed_node_ids_from_resolution_signals(resolution)` — resolution-local `world_tick_events`, `set_flags`, `advance_clocks`, nested `world_updates` fragments; (2) optional **session fingerprint diff** via `merge_progression_changed_node_signals`. Neither path inspects `event_log` rows to infer backbone row changes.

---

## Prompt fallback rule

When CTIR is not attached, `game.prompt_context._world_progression_projection_for_prompt` merges changed-node signals and calls `compose_ctir_world_progression_slice` on the live `world` dict, then `build_prompt_world_progression_hints`. That is a **read-side transport** path, not a new authority root.

---

## Silent-sink vs player-facing `event_log`

- **Tick** (`advance_world_tick`): routine `advance_progression_node` / `set_progression_node_value` calls use `progression_sink` (a local list). Only **legacy-shaped** threshold and movement events are `extend`ed onto `world["event_log"]`.
- **Resolution / GM merges** (`apply_resolution_world_updates`, `_apply_world_state_updates`, etc.): supported flag/clock writes use the same seam with a detached sink where applicable so **`type: world_progression` helper rows do not pollute** the player-facing log.
- **Invariant:** CTIR/prompt progression must remain correct when `world["event_log"]` contains **zero** internal `world_progression` helper rows — transport is from **native state + resolution signals + fingerprint**, not from log replay.

---

## Changed-node derivation and fingerprint timing

1. **Resolution/update signals** feed `collect_changed_node_ids_from_resolution_signals` (no `event_log` scan).
2. **Fingerprint diff:** `progression_fingerprint_map(world)` yields per-node state tokens; `diff_progression_fingerprints(prev, curr)` yields a bounded sorted list of changed ids when `session[SESSION_PROGRESSION_FINGERPRINT_KEY]` holds the **prior** map.
3. **Timing:** `store_progression_fingerprint_on_session(session, world)` runs in `game.api._build_gpt_narration_from_authoritative_state` **after** `build_messages` / prompt payload assembly and GPT work for the turn, so **during** prompt construction for the current turn, `merge_progression_changed_node_signals` still compares the live world against the **previous turn’s** fingerprint.
4. **Bookkeeping:** `SESSION_PROGRESSION_FINGERPRINT_KEY` (`_runtime_progression_nodes_fingerprint_v1`) is **runtime-only** on the session document — not player-facing transport and not a shadow progression root.

---

## Duplicate faction UID compatibility

When multiple faction rows normalize to the same progression UID (missing `id`/`name`, etc.), **tick simulation** may advance each row independently (`_tick_direct_faction_row_advance`) because disambiguated backbone node ids are not available per row.

The **read model** dedupes by node id (first row wins for iterator / CTIR pressure-agenda lists). This keeps transport **bounded and deterministic** without redesigning faction identity. A future pass may tighten identity if desired; see deferrals below.

---

## Node kinds and stable ids

All node `id` strings use an explicit prefix to keep ids **unique across roots**:

| `kind` | Canonical `id` pattern | `source_ref` |
|--------|------------------------|--------------|
| `project` | `project:{project_id}` | `{"root": "projects", "id": "..."}` |
| `faction_pressure` | `faction_pressure:{faction_uid}` | `{"root": "factions", "id": "...", "field": "pressure"}` |
| `faction_agenda` | `faction_agenda:{faction_uid}` | `{"root": "factions", "id": "...", "field": "agenda_progress"}` |
| `world_clock` | `world_clock:{clock_id}` | `{"root": "world_state.clocks", "id": "..."}` |
| `world_flag` | `world_flag:{flag_key}` | `{"root": "world_state.flags", "id": "..."}` |

`faction_uid` matches `game.world` agenda simulation: non-empty `faction["id"]`, else normalized `faction["name"]`, else `"unknown"`.

---

## Read hygiene

- Malformed **project** rows that fail validation are skipped (deterministic).
- **Clock** dict keys that are blank or start with `_` are ignored, matching other `world_state` merge hygiene.

---

## Snapshot and deltas

- `build_world_progression_snapshot(world)` returns bounded metadata (`nodes` capped, `recent_facts` capped from `event_log` **types** for snapshot context only — not used as the CTIR changed-node source).
- `apply_progression_delta(world, {"ops": [...]})` runs each op in order; failures are collected deterministically.

---

## State authority

`game.world_progression` is registered as an allowed mutator of `WORLD_STATE` alongside `game.world` and `game.api`, so guarded writes use `assert_owner_can_mutate_domain` consistently with other world writers.

---

## Explicit deferrals (not implemented here)

- Richer **schedule / cadence** semantics for off-screen simulation.
- **Advanced off-screen faction planning** beyond deterministic tick progression.
- **Authored dependency graphs** among world flags.
- A future **event scheduler / temporal orchestration** layer.
- **Identity cleanup** for duplicate faction UID situations (optional future hardening; current behavior is compatibility-first).

Do **not** use this section as a backlog mandate — only document real deferrals agreed as out of scope for Objective #9.

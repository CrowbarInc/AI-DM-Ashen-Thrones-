# System Overview

## Core Loop

1. Player input
2. Intent normalization
3. Engine resolution
4. State update
5. GPT narration

---

## Core Systems

### Scene State
- Tracks location, entities, and environmental context
- Must be explicit and machine-readable

### Interaction State
- Tracks active interaction target
- Tracks conversation privacy and player positioning
- Provides continuity across turns

### Runtime state domains (governance)

Engine state is split into non-overlapping **domains** (`world_state`, `scene_state`, `interaction_state`, `player_visible_state`, `hidden_state`) with declarative owners and guard helpers in `game/state_authority.py`. **`player_visible_state`** is **derived / publication-only** (including the journal `known_facts` merge from revealed hidden facts). **`hidden_state`** is authoritative but **unpublished** until an explicit reveal or publication seam runs. Prompt and narration payloads are **read-side consumers**, not canonical truth. See [Unified State Authority Model](state_authority_model.md) and the **Unified State Authority Model** row in [Architecture Ownership Ledger](architecture_ownership_ledger.md).

### Affordance Generation
- Produces a small set of actionable choices
- Must be deduplicated, ranked, and pruned
- Outputs 3–5 options

### Prompt Construction
- Converts engine state into a narration payload
- Includes scene + interaction context
- Enforces narration constraints

### Persistent world simulation (Objective #9)

**Canonical seam:** `game/world_progression.py` normalizes and mutates **native** `world.json` roots only (`projects`, faction `pressure` / `agenda_progress`, `world_state.flags`, `world_state.clocks`). `game/world.py` routes supported writes through that seam. There is **no** `world["progression"]` or `session["world_progression"]` shadow store.

**Transport:** Bounded `world.progression` for CTIR is composed by `compose_ctir_world_progression_slice(...)` from the backbone read model plus merged `changed_node_ids` (resolution/update signals and optional session fingerprint diff). `game/prompt_context.py` **prefers** CTIR’s slice when attached and otherwise **falls back** to the same composer over live `world` state—it does not rebuild CTIR or become a second authority.

**Excluded by design:** Session-local clocks, `world_state.counters`, and session documents are **not** progression nodes. Internal backbone helper events must **not** be mirrored into the player-facing `world["event_log"]` on tick or resolution paths that use detached sinks; regression coverage lives in `tests/test_world_simulation_backbone_regressions.py` and `tests/test_world_simulation_backbone_ownership.py`. See [World simulation backbone](world_simulation_backbone.md).

---

## Ownership Boundaries

Each system owns a responsibility, not an implementation.

| System | Responsibility |
|------|------|
| Engine | State transitions, outcomes |
| Affordances | Player options (generation, dedupe, pruning) |
| Interaction State | Conversation continuity |
| Prompt Layer | Narration constraints and context |
| GPT | Narrative expression only |

### Resolved-turn meaning vs prompt contracts (CTIR)

For **post-resolution** narration, turn meaning is snapshotted once into **CTIR** (session-backed, retry-stable), then **consumed** by `game.prompt_context` through a small adapter. That is separate from the **turn packet** (contracts/debug/transport). Structured **non-combat** semantics flow **engine contract →** `resolution["noncombat_resolution"]` **→ CTIR `noncombat`** (no backfill from raw social/exploration keys when the contract is missing). See [CTIR and prompt adapter architecture](ctir_prompt_adapter_architecture.md) for the full lifecycle, Objective #8 authority flow, four-layer split, and boundary rules that guard against semantic co-ownership regressions.

---

## Ownership Rules

- Responsibilities must not be duplicated across systems.
- Systems may be refactored, but ownership boundaries must remain clear.
- If a new system is introduced, its ownership must be explicitly defined.

---

## Design Priorities

- Playability > completeness
- Clarity > cleverness
- Determinism > interpretation
- Small, inspectable systems over complex abstractions

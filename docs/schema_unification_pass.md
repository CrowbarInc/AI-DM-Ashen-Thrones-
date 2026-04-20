# Schema unification pass (Objective 4)

This document tracks the **canonical schema layer** introduced in Block A and how the rest of the repo is expected to migrate onto it.

## Authoritative module

- **`game/schema_contracts.py`** — single import surface for Objective 4 normalization, validation, and **explicit** legacy adapters (`adapt_legacy_*`).
- Do **not** add new ad-hoc per-field coercion in random modules; extend `schema_contracts` (or call it) so behavior stays testable and discoverable.

## Canonical shapes (internal snake_case)

### Engine result

Aligned with `game.models` (`ExplorationEngineResult`, `CombatEngineResult`, `SocialEngineResult`) dict output:

- **Core:** `kind`, `action_id`, `label`, `prompt`, `success`, `resolved_transition`, `target_scene_id`, `clue_id`, `discovered_clues`, `world_updates`, `state_changes`, `hint`
- **Optional / domain:** `metadata`, `originating_scene_id`, `interactable_id`, `clue_text`, `combat`, `social`, `skill_check`, `check_request`, `requires_check`, plus combat legacy mirrors (`hit`, `damage`, `round`, `active_actor_id`, `order`) when present

**Note:** The Objective 4 brief used the singular `world_update`; the **entrenched** runtime contract remains **`world_updates`** (plural). `adapt_legacy_engine_result` accepts `world_update` as a temporary alias.

### World update (patch contract)

Used for **new** unified deltas (GM/engine migration target):

- `append_events`, `flags_patch`, `counters_patch`, `clocks_patch`, `projects_patch`, `clues_patch`, `npcs_patch`, `leads_patch`, `metadata`

Legacy GM payloads (`world_state`, top-level `projects`, exploration `set_flags` / `increment_counters` / `advance_clocks`) are mapped only through **`adapt_legacy_world_update`**. Relative counter/clock increments cannot be expressed as absolute patches without live world read; they are parked under `metadata.legacy_increment_counters` and `metadata.legacy_advance_clocks` with stable reason codes in code comments.

### Affordance

- `id`, `type`, `label`, `prompt`, `target_id`, `target_kind`, `target_scene_id`, `target_location_id`, `conditions`, `metadata`

Legacy API / `normalize_scene_action` camelCase (`targetSceneId`, `targetEntityId`, …) is supported **only** via **`adapt_legacy_affordance`**.

### Interaction target / addressable

- `id`, `name`, `scene_id`, `kind`, `address_roles`, `aliases`, `address_priority`, `addressable`, `metadata`

Scene roster extras (e.g. `role`, `topics`) are folded into `metadata.legacy_addressable_fields` by **`adapt_legacy_interaction_target`** when needed.

### Clue

- `id`, `text`, `state`, `presentation`, `source_scene_id`, `canonical_lead_id`, `leads_to_scene_id`, `leads_to_npc_id`, `lead_type`, `metadata`

Legacy `leads_to_scene` / `leads_to_npc` / `leads_to_rumor` and list fields from `normalize_clue_record` map through **`adapt_legacy_clue`**. Unmapped or ambiguous legacy should surface deterministic `schema_contracts:*` validation reasons (never silent guessing).

### Project

- `id`, `name`, `category`, `status`, `progress`, `target`, `tags`, `notes`, `metadata`

Numeric normalization and `goal` → `target` / `completed` → `complete` remain delegated to **`game.projects.normalize_project_entry`** inside `normalize_project` / `adapt_legacy_project` to avoid behavioral drift in this block.

### Clock

- `id`, `value`, `min_value`, `max_value`, `scope`, `metadata`

Legacy world-state rows using `name` / `progress` / `max` map via **`adapt_legacy_clock`**.

## Legacy aliases (retirement sequence)

1. **Now (Block A):** Legacy spellings are centralized in `adapt_legacy_*`; canonical helpers park unknown keys under `metadata.unknown_legacy_keys` where applicable.
2. **Next passes:** Migrate call sites to import `schema_contracts` and stop accepting alternate shapes at module boundaries.
3. **Final:** Remove adapters once logs/tests show no traffic; delete retired keys from docs and tighten validators.

## Module ownership (high level)

| Area | Primary owners today | Schema surface |
|------|----------------------|----------------|
| Exploration / engine dicts | `game.models`, `game.exploration` | `normalize_engine_result`, `adapt_legacy_engine_result` |
| GM `world_updates` | `game.gm`, `game.world` | `adapt_legacy_world_update` → `normalize_world_update` |
| Scene actions / affordances | `game.scene_actions`, `game.affordances` | `adapt_legacy_affordance` |
| Addressables / roster | `game.interaction_context` | `adapt_legacy_interaction_target` |
| Discoverable clues | `game.gm.normalize_clue_record`, `game.clues` | `adapt_legacy_clue` |
| Projects | `game.projects` | `normalize_project` / `adapt_legacy_project` |
| Clocks | `game.world`, `game.storage` | `adapt_legacy_clock` |

## Tests

- **`tests/test_schema_contracts.py`** — focused coverage for each `normalize_*` / `adapt_legacy_*`, unknown-key parking, and deterministic validation failures.

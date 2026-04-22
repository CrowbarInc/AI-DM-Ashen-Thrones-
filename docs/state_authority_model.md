# Unified State Authority Model

This document is the maintainer-facing contract for **runtime state domains**: what each domain means, who may own or mutate it, how reads compose, and where cross-domain writes are allowed. It extends the same governance posture as `docs/architecture_ownership_ledger.md`—declarative owners, direct-owner tests, and narrow seams—without replacing engine modules or turning prompts into truth stores.

The executable registry and guard helpers live in `game/state_authority.py`.

Validation **phase** ownership (truth vs structure vs expression vs legality vs offline scoring) is a separate, complementary contract: `docs/validation_layer_separation.md` with the leaf registry `game/validation_layer_contracts.py`. State-domain guards here govern **which runtime stores may mutate**; the validation-layer doc governs **which pipeline phase may own checks, repairs, and scores** without collapsing those concerns.

## Domain ids (canonical)

| Domain id | Meaning |
|-----------|---------|
| `world_state` | Persistent world document truth: factions, NPCs, projects, `world['world_state']` flags/counters/clocks, clues ledger, event log entries produced by simulation/resolution—not narration text. |
| `scene_state` | Session scene anchoring and per-scene playthrough progress: `session['scene_state']`, `session['scene_runtime']`, active/visited scene bookkeeping, and authored `data/scenes/*.json` templates loaded/saved via `game.storage`. **Distinct** from interaction framing. |
| `interaction_state` | Session interaction framing: `session['interaction_context']` (mode, engagement, privacy, active target, position hints) and authoritative social-target resolution owned by `game.interaction_context`. |
| `player_visible_state` | **Governed publication/view** only: `narration_visibility` exports, `scene_state_anchor_contract`, curated `public_scene` / prompt slices, and emitted `player_facing_text`. **Not** a persistence root; must not back-write hidden or world truth. |
| `hidden_state` | Authoritative content **not yet published** to the player: template `hidden_facts`, undiscovered clue records, GM-only `scene['gm_only']` bundles, unpublished intent/plan fields used for prompting, and engine-only bookkeeping until a reveal seam runs. **Not** a junk drawer—each entry should have a reveal or retirement rule. |

## Canonical runtime owners (declarative)

These are the modules that **should** own or orchestrate mutations for each domain. Other modules remain readers or downstream consumers until a seam is refactored.

| Domain | Canonical runtime owner module(s) |
|--------|-------------------------------------|
| `world_state` | `game.world` (engine semantics), `game.storage` (world.json persistence and load-time shape only—not policy) |
| `scene_state` | `game.api` (orchestrated session/scene transitions), `game.storage` (session/scene document I/O and lazy session roots only—not policy) |
| `interaction_state` | `game.interaction_context`, `game.api` |
| `player_visible_state` | `game.narration_visibility`, `game.scene_state_anchoring`, `game.prompt_context`, `game.journal` |
| `hidden_state` | `game.world`, `game.api`, `game.storage` (persistence of authoritative hidden templates and runtime hidden-adjacent stores—not publication) |

Notes:

- `game.narration_visibility` is explicitly **read-only** for runtime truth; it produces visibility contracts for narration matching.
- `game.scene_state_anchoring` and `game.prompt_context` assemble **read-side** contracts and prompt instruction payloads; neither is a persistence root for authoritative domains.
- `game.journal` owns the **`player_visible_state` publication seam** that merges runtime revealed hidden facts into journal ``known_facts`` (``journal_merge_revealed_hidden_facts`` allow-list + same-domain ``journal_known_facts_merge`` trace operation). The journal snapshot remains **derived**; it must not back-write `hidden_state` or `world_state`.
- `game.api` appears where the HTTP/action pipeline orchestrates detach/mutate/hygiene/save sequences after authoritative resolution.
- **`tests/test_state_authority.py`** is the **practical primary direct-owner suite** for the registry, read matrix, cross-domain allow-list, and guard semantics. Domain behavior stays asserted in owner suites (for example `tests/test_interaction_context.py`, `tests/test_world_state.py`, `tests/test_validation_journal_affordances.py`, `tests/test_world_updates_and_clue_normalization.py`).

## Player-facing vs hidden vs derived

| Domain | Classification | May be directly narrated? | GPT may mutate? |
|--------|----------------|---------------------------|-----------------|
| `world_state` | mixed | No (surface through contracts/UI) | **No** |
| `scene_state` | mixed | No (surface through contracts/UI) | **No** |
| `interaction_state` | mixed | No | **No** |
| `player_visible_state` | derived | Yes (this is the governed narration surface) | **No** |
| `hidden_state` | hidden | No | **No** |

**Invariant:** GPT-originated output must **never** be treated as authoritative for mutating any of the five domains. Engine code applies structured effects after validation.

## Allowed read matrix

A reader domain **R** may read target domain **T** when `can_domain_read_domain(R, T)` is true (see `game/state_authority.py`). Summary:

| Reader \\ Target | `world_state` | `scene_state` | `interaction_state` | `player_visible_state` | `hidden_state` |
|------------------|---------------|---------------|----------------------|------------------------|------------------|
| `world_state` | yes | yes | no | no | no |
| `scene_state` | yes | yes | yes | no | yes |
| `interaction_state` | yes | yes | yes | no | no |
| `player_visible_state` | yes | yes | yes | yes | yes |
| `hidden_state` | yes | yes | yes | no | yes |

Rationale in brief:

- Anchoring and visibility builders may read **authoritative** domains plus `hidden_state` to **subtract** or gate content (`player_visible_state` → `hidden_state`).
- `hidden_state` builders must **not** read `player_visible_state` as a source of truth (no feedback from published text into hidden facts).

## Forbidden writes and narrow exceptions

**Default:** no cross-domain writes unless an operation is registered in `game.state_authority._CROSS_DOMAIN_WRITE_ALLOWLIST` and callers use `assert_cross_domain_write_allowed(...)`.

### Unconditional examples (anti-patterns)

- Writing `world_state` from `player_visible_state` because the model said so in narration (back-writing truth from text).
- Mutating `hidden_state` from `player_visible_state` or from raw GPT JSON without engine validation.
- Using `interaction_state` to overwrite `world_state` flags directly (bypass `game.world` / resolution seams).
- Treating `session['scene_runtime']` discovery lists as **interaction** state—they belong to `scene_state`.

### Allow-listed cross-domain writes (representative)

| Source | Target | Example operations (exact strings in code) |
|--------|--------|---------------------------------------------|
| `scene_state` | `world_state` | `npc_promotion`, `resolution_world_mutations` |
| `hidden_state` | `scene_state` | `reveal_clue_runtime`, `reveal_hidden_fact_runtime`, `merge_pending_lead_runtime` |
| `hidden_state` | `world_state` | `publish_progression_to_world_state` |
| `interaction_state` | `scene_state` | `promotion_map_update`, `interlocutor_binding`, `scene_runtime_hygiene`, `exchange_interruption_tracker_slot` |
| `scene_state` | `interaction_state` | `scene_transition_hygiene`, `clear_interaction_context` |
| `hidden_state` | `player_visible_state` | `journal_merge_revealed_hidden_facts` |

**Narrow exception, not a general rule:** `interaction_state` → `scene_state` edges exist because `game.interaction_context` owns authoritative interaction framing **and** selected scene-adjacent session keys (for example promotion maps and exchange-local counters) under named operations. That does **not** collapse `scene_state` into `interaction_state`; scene templates, `scene_runtime`, and orchestrated transitions remain `scene_state` concerns.

When adding a new seam, extend the allow-list **and** document the operation here.

## Shipped guard adoption (Objective #3)

Guards (`assert_owner_can_mutate_domain`, `assert_cross_domain_write_allowed`, optional `build_state_mutation_trace`) are wired at representative **mutation** and **publication** seams—not blanket coverage of every helper.

| Area | Module(s) | What is guarded |
|------|-----------|-----------------|
| Interaction framing + allow-listed `interaction_state` → `scene_state` writes | `game.interaction_context` | Owner checks on `interaction_state`; cross-domain checks where the allow-list applies (for example interlocutor binding, scene runtime hygiene, interruption tracker slot). |
| World / resolution truth | `game.world` | Owner checks on `world_state` for NPC upsert, ticks, `apply_world_updates`, `apply_resolution_world_updates`, reset. |
| Turn / HTTP orchestration | `game.api` | Owner checks on `scene_state` and `world_state` at authoritative scene transition, GM update staging, and resolution mutation staging. |
| Journal publication | `game.journal` | Owner on `player_visible_state`; cross-domain when merging runtime `revealed_hidden_facts` into derived ``known_facts`` (`journal_merge_revealed_hidden_facts`). |

**Intentionally deferred (in scope boundary, not forgotten):** lazy first-touch dict materialization avoids guard coupling—see tests `test_scene_state_lazy_init_remains_outside_direct_owner_suite` and `test_storage_get_interaction_context_first_touch_not_guarded`. `_scene_state` in `game.interaction_context` and `get_interaction_context` in `game.storage` remain **structural** initialization seams; semantic mutations still go through guarded owner APIs.

## Examples from this repository

1. **Scene vs interaction split:** `game/storage.py` exposes `get_scene_state` and `get_interaction_context` as separate session roots (lazy shape). `game/interaction_context.py` is the single **semantic** owner for interaction-context mutations.
2. **Player-visible is derived:** `game/narration_visibility.py` builds a conservative visibility contract and does not mutate runtime truth (see module docstring). `game/scene_state_anchoring.py` consumes authoritative session/scene/world inputs only—not undiscovered clues—for anchors.
3. **Prompt packaging:** `game/prompt_context.build_narration_context` attaches `narration_visibility`, `scene_state_anchor_contract`, and `scene.gm_only` slices for the model to **read** under rules; those bundles are instruction carriers, not alternate stores for `world_state` or `hidden_state`.
4. **API composition:** `game/api.compose_state` mirrors `session['scene_state']` into the client payload and builds a **derived** `journal` via `build_player_journal`; that path **publishes** views—it is not a second persistence root for authoritative domains.
5. **World progression:** `game/world.apply_resolution_world_updates` merges structured resolution output into `world['world_state']`—engine-owned, deterministic, not GPT-owned.

## Adoption guidance (new work after Objective #3)

1. Pick the **one** domain your new field belongs to; if it could fit two, split the field or define a narrow cross-domain write with a named `operation`.
2. Route writes through the **canonical owner module** for that domain (or `game.api` orchestration that immediately delegates to that owner).
3. At mutation seams, optionally emit `build_state_mutation_trace(...)` into `storage.append_debug_trace` for playtest forensics.
4. For cross-domain effects, call `assert_cross_domain_write_allowed(source_domain, target_domain, operation="...")` **before** mutating the target store, and `assert_owner_can_mutate_domain(__name__, domain, operation=...)` for same-domain writes when the call graph is broad.
5. Never infer state from **published** `player_facing_text` or prompt echo strings—rehydrate from authoritative stores or CTIR/resolution payloads only.

### Objective #8 pointer (non-combat semantics)

Structured non-combat outcomes are owned by **`game.noncombat_resolution`**, embedded at runtime via **`game.api._resolve_engine_noncombat_seam`** as `resolution["noncombat_resolution"]`, then projected into **CTIR** by **`game.ctir.build_ctir`** (root `noncombat` only from that contract). Prompt and narrative layers **read** those signals; they must not invent mechanics from prose or legacy raw fields when the contract exists. When the contract is absent, CTIR `noncombat` remains **empty** by design—no silent reconstruction. Full flow, anti-drift rules, and deferred boundaries: **`docs/ctir_prompt_adapter_architecture.md`** (Objective #8 section).

## Anti-goals

- **Not** replacing existing module owners listed in `docs/architecture_ownership_ledger.md`—this model names domains and guards; it does not subsume `game.world`, `game.storage`, or `game.prompt_context`.
- **Not** turning prompt or narration bundles into canonical state owners—they remain **views** and instruction carriers.
- **Not** allowing published model text to back-write `hidden_state` or `world_state` truth.
- **Not** introducing a sixth persistence domain; the five listed domains are sufficient. If an internal helper ever needs a synthetic tag for traces only, keep it out of the registry unless the architecture ledger is updated with justification.

## Related documents

- `docs/architecture_ownership_ledger.md` — governed seam entry: **Unified State Authority Model**
- `game/state_authority.py` — constants, `StateDomainSpec`, guards, mutation trace helper

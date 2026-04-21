# Current focus — post-AER consolidation + Objective #9 shipped

## Phase

This branch is in **consolidation**, not feature expansion. **Anti-Echo & Rumor Realism (AER)** is **functionally complete** and treated as shipped behavior for cleanup purposes. **Behavioral Gauntlet** and **Playability Validation** are **complete** as **deterministic**, **contract-driven** validation layers (they do not add new runtime gameplay systems).

**Objective #9 (world simulation backbone + bounded CTIR/prompt progression transport)** is **landed** (Blocks A–D). Persistent progression stays on native world roots; CTIR/prompt carry a **bounded read projection** only. Do not reintroduce shadow JSON roots, session-clock or counter nodes, or player-facing `world_progression` helper rows on silent-sink paths.

The purpose of this consolidation phase is to make later refactors safer by **freezing ownership**, **codifying deferrals**, and trimming **orchestration** ambiguity—**without** changing player-facing behavior in consolidation-only passes.

---

## Completed (do not re-open as “active goals”)

| Track | Role | Canonical pointers |
| --- | --- | --- |
| **Behavioral Gauntlet** | Deterministic narration-behavior smoke (axes, no live GPT) | `tests/helpers/behavioral_gauntlet_eval.py`, `tests/test_behavioral_gauntlet_smoke.py`, `tests/test_behavioral_gauntlet_eval.py`, `docs/manual_gauntlets.md` (G9–G12), `tools/run_manual_gauntlet.py` |
| **Playability Validation** | Turn-scoped “competent human DM” behavioral checks via real `/api/chat` | `game/playability_eval.py`, `tests/test_playability_smoke.py`, `tools/run_playability_validation.py`, `docs/testing.md` |
| **AER (Anti-Echo & Rumor Realism)** | Narrative authenticity operator model + repairs + telemetry | `docs/narrative_authenticity_anti_echo_rumor_realism.md`, narrative authenticity tests under `tests/` (e.g. `test_narrative_authenticity_*.py`) |
| **Unified State Authority (Objective #3)** | Declarative domains + guard registry; journal publication seam; allow-listed cross-domain writes | `docs/state_authority_model.md`, `docs/architecture_ownership_ledger.md` → *Unified State Authority Model*, `game/state_authority.py`, **direct-owner suite** `tests/test_state_authority.py` |
| **Objective #7 — Referent tracking + post-GM referent clarity (Block D)** | Derivative-only artifact + compact packet mirror + FEM validator/repair seam; **not** a second resolver over `interaction_context` | `docs/narrative_integrity_architecture.md` → *Objective #7*, `game/referent_tracking.py`, `game/prompt_context.py`, `game/final_emission_validators.py` / `game/final_emission_repairs.py` / `game/final_emission_gate.py`, tests noted in that section |
| **Objective #9 — World simulation backbone + bounded progression transport (Blocks A–D)** | Single seam `game/world_progression.py`; native-root writes; silent progression sinks; fingerprint-after-prompt timing; CTIR `world.progression` + prompt fallback without `prompt_context` calling `build_ctir`; duplicate faction UID compatibility | `docs/world_simulation_backbone.md`, `docs/system_overview.md` → *Persistent world simulation*, `game/world_progression.py`, `game/world.py`, `game/ctir_runtime.py`, `game/api.py` (`store_progression_fingerprint_on_session` after prompt/message build), `tests/test_world_simulation_backbone_regressions.py`, `tests/test_world_simulation_backbone_ownership.py`, plus focused suites `tests/test_world_progression_*.py`, `tests/test_ctir_world_progression_projection.py`, `tests/test_prompt_context_world_progression_consumption.py` |

---

## Active consolidation targets (canonical order)

Work proceeds in this order unless a release forces a narrow bugfix:

1. **Final emission orchestration boundaries** — how emit-time policy, sanitizer integration, strict-social paths, logging, and **metadata packaging** compose under a single **orchestration** owner; clarify pure helpers vs side-effecting layers.
2. **Telemetry / meta normalization** — narrative authenticity **telemetry** shape, reuse, and naming so meta/debug surfaces stay **deterministic** and do not accrete parallel “policy by JSON.”
3. **Test ownership trimming** — enforce **one primary ownership domain per test module** where practical; allow only **smoke overlap** when two layers genuinely need different harness depth.

Detailed rules and runtime module boundaries: **`docs/narrative_integrity_architecture.md`** (includes **Post-AER Consolidation Rules** and the **Consolidation Targets** table).

---

## Consolidation Targets (next real cleanup domains)

| Domain | What “done” looks like |
| --- | --- |
| **Final emission metadata packaging** | `_final_emission_meta` and related payload fields have a single **canonical owner** in the emit **orchestration** path; helpers are **pure** or **metadata-only** where extracted. |
| **Narrative authenticity telemetry shape / reuse** | Telemetry keys and structs are stable, documented, and reused—no duplicate parallel shapes for the same concern. |
| **Prompt / sanitizer ownership boundaries** | Pre-generation vs post-GM paths stay split; **smoke overlap** only for cross-layer integration, not duplicate phrase legality suites (see `tests/TEST_CONSOLIDATION_PLAN.md`). |
| **Social / emission ownership boundaries** | Strict social shape, escalation state machine, and misc social integration each have an obvious **canonical owner** file; shrink catch-all modules. |
| **Transcript duplicate assertion thinning** | Transcript and gauntlet modules assert **ordering** and **cross-turn state**; drop or weaken duplicate substring locks already owned by smaller **contract-driven** tests. |
| **Lead / clue cleanup** | **Deferred** until after **prompt/sanitizer** and **social/emission** batches complete (registry overlap reduction, not a blocker for earlier work). |

---

## Explicitly deferred vs canonical (summary)

| Item | Status |
| --- | --- |
| **Authoritative social target resolution** in `game/interaction_context.py` | **Canonical owner** — not moved to `dialogue_targeting` while import-cycle risk remains (**deferred** extraction). |
| **Large policy clusters** still living in `game/final_emission_gate.py` | **Canonical** for **orchestration** and integration order; further extraction is optional and must not fork policy (**deferred** unless it reduces ambiguity). |
| **Lead/clue test + runtime overlap reduction** | **Deferred** until prompt/sanitizer + social/emission consolidation passes. |
| **Broad test-file merges** | **Deferred**; prefer thinning and **smoke overlap** discipline over kitchen-sink merges. |

Full deferral notes live in **`docs/narrative_integrity_architecture.md`** → *Intentionally deferred*.

---

## Post-AER Consolidation Rules (pointer)

The authoritative, compact rule block lives in **`docs/narrative_integrity_architecture.md`** → **Post-AER Consolidation Rules** (same consolidation boundary as this file).

---

## Opening / Start Campaign regression lock-in (OF2-F)

Brief ownership pointer (see also **`docs/narrative_integrity_architecture.md`** → *Opening + structured start*):

- First-turn **opening_scene_realization** + **opening_narration_obligations** stay on the **`game/prompt_context.py`** stack for both chat openings and **`POST /api/start_campaign`**.
- **Shared seams under test:** `_opening_scene_normalized_action_and_resolution`, `_complete_opening_turn_persistence_like_chat`, and `session.campaign_started` / `ui.*` mirrors — regressions live in `tests/test_opening_start_seam_regressions.py`, `tests/test_start_campaign_api.py`, and related suites.

## Architecture invariants preserved during consolidation

These remain true while consolidation proceeds; they are not new feature goals:

- **Engine-first ownership:** engine resolves and mutates; GPT narrates only after resolution.
- **One authoritative turn pipeline** across `/api/action` and `/api/chat` (see `game.api` / turn support).
- **Check prompting** stays engine-owned (`requires_check` / `check_request`) with clear player-facing payloads.
- **`narration_obligations` and prompt-context obligations** remain **contract-driven** exports from authoritative turn state—not narrator-invented mechanics.
- **Clue mutation** stays in engine clue gateways; narration text must not create or mutate clue state.
- **Interaction-state mutation** has a single owner: `game/interaction_context.py` (with **narrow, allow-listed** `interaction_state` → `scene_state` writes where scene-adjacent keys are updated—see `docs/state_authority_model.md`).
- **Unified state authority:** `game/state_authority.py` is registry + guards only; `player_visible_state` stays derived; `hidden_state` stays unpublished until reveal/publication seams.
- **Implied-action handling** stays narrow, **deterministic**, and runs during normalized turn preparation (before prompt-context assembly).
- **Objective #7 referent seam:** full artifact is built once in `referent_tracking` and shipped on prompt context; the turn packet carries a **compact mirror only**; post-GM clarity uses the full artifact first and abstains without it — see **`docs/narrative_integrity_architecture.md` → *Objective #7***.
- **Objective #9 world progression seam:** supported persistent progression writes route through `game/world_progression`; tick/resolution paths keep internal helper events off `world["event_log"]`; `store_progression_fingerprint_on_session` runs **after** prompt/message assembly in `_build_gpt_narration_from_authoritative_state`; CTIR/prompt progression is **bounded** and sourced from the backbone read model (see **`docs/world_simulation_backbone.md`**).

---

## Authoritative turn order (reference)

1. Player input  
2. Intent normalization / expansion (includes conservative implied-action continuity and lightweight mixed-turn segmentation)  
3. Action classification  
4. Engine resolution  
5. Authoritative state mutation  
6. Prompt-context construction  
7. GPT narration  
8. Affordance derivation  
9. Response / debug packaging (includes compact `turn_trace` in `debug_traces` where enabled)

---

## Success criteria for consolidation PRs

- **No behavior expansion** in consolidation-only PRs (see rules in `narrative_integrity_architecture.md`).
- **Orchestration** stays obvious: `game/final_emission_gate.py` remains the **`apply_final_emission_gate`** owner unless a helper is clearly **pure** or **metadata-only**.
- Tests gain clearer **canonical owners**; cross-file duplication trends toward **smoke overlap**, not competing legality suites.
- Docs and comments stay aligned with the **deterministic**, **contract-driven** testing story (gauntlets, playability, AER) as **validation**, not new gameplay layers.

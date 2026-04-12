# Current focus — post-AER consolidation (Block C1 boundary)

## Phase

This branch is in **consolidation**, not feature expansion. **Anti-Echo & Rumor Realism (AER)** is **functionally complete** and treated as shipped behavior for cleanup purposes. **Behavioral Gauntlet** and **Playability Validation** are **complete** as **deterministic**, **contract-driven** validation layers (they do not add new runtime gameplay systems).

The purpose of this consolidation phase is to make later refactors safer by **freezing ownership**, **codifying deferrals**, and trimming **orchestration** ambiguity—**without** changing player-facing behavior in consolidation-only passes.

---

## Completed (do not re-open as “active goals”)

| Track | Role | Canonical pointers |
| --- | --- | --- |
| **Behavioral Gauntlet** | Deterministic narration-behavior smoke (axes, no live GPT) | `tests/helpers/behavioral_gauntlet_eval.py`, `tests/test_behavioral_gauntlet_smoke.py`, `tests/test_behavioral_gauntlet_eval.py`, `docs/manual_gauntlets.md` (G9–G12), `tools/run_manual_gauntlet.py` |
| **Playability Validation** | Turn-scoped “competent human DM” behavioral checks via real `/api/chat` | `game/playability_eval.py`, `tests/test_playability_smoke.py`, `tools/run_playability_validation.py`, `docs/testing.md` |
| **AER (Anti-Echo & Rumor Realism)** | Narrative authenticity operator model + repairs + telemetry | `docs/narrative_authenticity_anti_echo_rumor_realism.md`, narrative authenticity tests under `tests/` (e.g. `test_narrative_authenticity_*.py`) |

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

## Architecture invariants preserved during consolidation

These remain true while consolidation proceeds; they are not new feature goals:

- **Engine-first ownership:** engine resolves and mutates; GPT narrates only after resolution.
- **One authoritative turn pipeline** across `/api/action` and `/api/chat` (see `game.api` / turn support).
- **Check prompting** stays engine-owned (`requires_check` / `check_request`) with clear player-facing payloads.
- **`narration_obligations` and prompt-context obligations** remain **contract-driven** exports from authoritative turn state—not narrator-invented mechanics.
- **Clue mutation** stays in engine clue gateways; narration text must not create or mutate clue state.
- **Interaction-state mutation** has a single owner: `game/interaction_context.py`.
- **Implied-action handling** stays narrow, **deterministic**, and runs during normalized turn preparation (before prompt-context assembly).

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

# Narrative integrity — runtime module layout

Concise map for “where does this belong?” after the Block 3 split and Block 4 documentation pass. **Behavior is unchanged by this document**; it reflects `game/` as of the consolidation boundary. For **anti-echo + rumor realism** operator detail (status model, repairs, telemetry, evaluator verdicts), see `docs/narrative_authenticity_anti_echo_rumor_realism.md`.

**Block C1 (post-AER):** This file is a **canonical** consolidation anchor alongside `docs/current_focus.md` and `tests/TEST_AUDIT.md` / `tests/TEST_CONSOLIDATION_PLAN.md`.

---

## Post-AER Consolidation Rules

These rules apply while the repo is in **post-AER consolidation** (see `docs/current_focus.md`). They exist to prevent cleanup passes from accidentally becoming feature work.

- **No behavior expansion** — consolidation PRs do not add gameplay systems, new mechanics, or UI complexity.
- **No new policy layers** unless **required by a bug fix** — prefer tightening existing **orchestration** and contracts over inventing parallel enforcement stacks.
- **Extraction is allowed** only when it **reduces ambiguity** or **test overlap** (for example, a **pure** validator already split to `final_emission_validators.py`)—not when it spreads **orchestration** across owners.
- **`game/final_emission_gate.py` remains the `apply_final_emission_gate` orchestration owner** — helpers may be split out when they are clearly **pure** (validators), **deterministic** repairs, shared text utilities, or **metadata-only** glue; anything that orders layers, integrates sanitizer paths, or seals strict-social emit paths stays in **orchestration** unless a later pass proves a zero-ambiguity move.
- **Test files should have one primary ownership domain each**, with **smoke overlap** elsewhere only when two layers (for example, pure routing table vs full `/api/chat` stack) intentionally assert different depths.

---

## Consolidation Targets (runtime + tests)

| Domain | Cleanup intent |
| --- | --- |
| **Final emission metadata packaging** | Normalize `_final_emission_meta` (and related) packaging so emit **orchestration** owns composition; avoid duplicate meta mutation sites. |
| **Narrative authenticity telemetry shape / reuse** | One coherent telemetry vocabulary for authenticity signals; reuse rather than fork shapes across debug/meta consumers. |
| **Prompt / sanitizer ownership boundaries** | Keep **pre-generation** contracts in prompt/guard paths vs **post-GM** string hygiene in sanitizer paths; document **smoke overlap** vs **canonical owner** for each invariant. **Applied (C3):** pytest homes ``tests/test_prompt_and_guard.py`` vs ``tests/test_output_sanitizer.py`` vs transcript/gauntlet transform smoke — see ``tests/TEST_CONSOLIDATION_PLAN.md`` (*Block C3 applied*). |
| **Social / emission ownership boundaries** | Keep strict-social emission, escalation machinery, and catch-all social tests from competing as co-equal **canonical owners** of the same string families. |
| **Transcript duplicate assertion thinning** | Transcripts prove sequencing and cross-turn state; reduce duplicate substring locks where a smaller **contract-driven** test already owns the gate. |
| **Lead / clue cleanup** | **Deferred** until after **prompt/sanitizer** and **social/emission** batches — see `tests/TEST_CONSOLIDATION_PLAN.md` → *Next consolidation order*. |

---

## Flow (high level)

1. **Turn input** hits `game.api` / `game.api_turn_support` (not detailed here).
2. **Coarse routing** (`game.interaction_routing`) classifies dialogue vs world-action lanes (dialogue lock, OOC/engine guards, etc.).
3. **Social commitment breaks** (`game.social_continuity_routing`) decide when continuity yields to explicit non-social redirection; session hooks may be applied via `game.interaction_context` re-exports.
4. **Targeting**
   - **Vocative / substring helpers:** implemented in `game.interaction_context`; **thin re-exports** in `game.dialogue_targeting` for a stable import surface.
   - **Authoritative social target** (precedence-ordered binding): **`game.interaction_context.resolve_authoritative_social_target`** — intentionally **not** moved to `dialogue_targeting` (import-cycle risk; keeps parsing next to context mutation).
5. **Contracts / policy read side:** `game.response_policy_contracts` resolves shipped `response_type_contract` and last-player-input probing for the gate.
6. **Strict-social and emission helpers:** `game.social_exchange_emission` (**orchestration** with the gate; not the validator/repair home).
7. **Deterministic validation:** `game.final_emission_validators` (`validate_*`, `inspect_*`, `candidate_satisfies_*`).
8. **Repairs / layer wiring:** `game.final_emission_repairs` (`apply_*`, `merge_*`, skip helpers for answer completeness and response delta).
9. **Shared text / patterns:** `game.final_emission_text` (normalization, regex scaffolding — no policy **orchestration**).
10. **Orchestration + compatibility:** `game.final_emission_gate.apply_final_emission_gate` wires sanitizer, remaining in-module policy layers (tone, narrative authority, anti-railroading, context separation, scene anchor, speaker selection, etc.), logging, and metadata. **Historical tests** may still import private helpers from `final_emission_gate` even though implementation lives in extracted modules — prefer importing from the real **canonical owner** for new code.

Post-gate sanitization and other emit-path modules (`game.output_sanitizer`, etc.) stay as documented in existing suites.

## Test ownership (canonical)

See **`tests/TEST_AUDIT.md`** (**canonical owner** map) and **`tests/TEST_CONSOLIDATION_PLAN.md`** (routing three-module split, repair/retry split). **`tests/test_inventory.json`** is the machine-readable inventory (regenerate with `py -3 tools/test_audit.py`).

Examples aligned with this layout:

| Concern | Primary test homes |
| --- | --- |
| Full `/api/chat` stack + gate integration | `test_turn_pipeline_shared.py` |
| Pure routing table / dialogue lock | `test_dialogue_routing_lock.py` |
| Directed social / vocative / emergent actor | `test_directed_social_routing.py` |
| Target authority regressions | `test_social_target_authority_regressions.py` |
| Contextual minimal repair | `test_contextual_minimal_repair_regressions.py` |
| Empty social / retry / terminal fallback | `test_empty_social_retry_regressions.py` |
| Final emission gate ordering / contracts | `test_final_emission_gate.py`, `test_answer_completeness_rules.py`, `test_response_delta_requirement.py`, etc. |

## Intentionally deferred (non-goals for this consolidation)

- **Authoritative target resolution** stays in `interaction_context` — **deferred** extraction to `dialogue_targeting` while cycle coupling with roster/context writes remains risky.
- **Large policy-layer clusters** (tone escalation, narrative authority, anti-railroading, scene anchor, speaker enforcement, etc.) remain **in** `final_emission_gate.py` for **orchestration** — only validators/repairs/text/contracts were split out; further extraction is **deferred** optional work unless it clearly reduces ambiguity.
- **Debug / trace glue** tied to `apply_final_emission_gate` stays with **orchestration** unless a later pass isolates it without churn.
- **Lead/clue consolidation** (test and runtime overlap reduction) remains **deferred** until **prompt/sanitizer** and **social/emission** batches per `TEST_CONSOLIDATION_PLAN.md` — not part of the first post-AER consolidation slice.
- **Broad test-file merges** and mass marker refactors remain **deferred** per `TEST_AUDIT.md`.

## When to extend behavior

| You are changing… | Start in… |
| --- | --- |
| Dialogue vs action routing rules | `interaction_routing.py` |
| When social continuity breaks | `social_continuity_routing.py` |
| Vocative parsing (no precedence policy change) | `interaction_context.py` (+ re-export in `dialogue_targeting.py` if adding a public helper) |
| Who is the authoritative addressee | `interaction_context.resolve_authoritative_social_target` |
| What response shape the writer owed | `response_policy_contracts.py` |
| Whether text satisfies a contract (no side effects) | `final_emission_validators.py` |
| How to repair or skip a policy layer | `final_emission_repairs.py` |
| Normalization / shared patterns | `final_emission_text.py` |
| Layer order, sanitizer integration, strict-social path, logging | `final_emission_gate.py` (**orchestration** owner) |

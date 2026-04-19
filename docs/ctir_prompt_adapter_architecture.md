# CTIR-first narration seam (resolved turn → prompt)

This document locks the **landed** architecture for Objective #1: where meaning lives, how it flows into prompts, and what must not drift back into ad-hoc semantic co-ownership.

## Four distinct layers

### A. Canonical engine / domain state

- **What it is:** Full authoritative world, session, scene envelope, combat, journals, interaction context, and other engine-owned structures.
- **Who owns it:** Engine and domain modules (`game.api` mutation paths, exploration, social, combat, storage loaders, etc.).
- **Role:** Source of truth for mutations and persistence. Prompt assembly must not silently re-derive outcomes that the engine already resolved.

### B. CTIR (canonical resolved-turn meaning)

- **What it is:** A single **bounded**, **JSON-serializable**, **deterministic** snapshot of what the engine resolved for **one** narration attempt on a resolved turn. Built in `game.ctir` / `game.ctir_runtime` from explicit slices, not from whole engine blobs.
- **Who owns it:** `game.ctir` (normalization + schema) and `game.ctir_runtime` (attach / stamp / ensure for one turn).
- **Runtime rule:** CTIR is **attached to the session** for the lifetime of that resolved-turn narration (including targeted retries that share the same stamp).
- **Hard limits:** No prose, no prompt fragments, no full mirrors of canonical state—only bounded summaries and identifiers needed for deterministic downstream reads.

### C. Prompt-context adapter layer (`game.prompt_context`)

- **What it is:** **Consumes** session-backed CTIR via `get_attached_ctir(session)` and maps it through a **small** adapter (`_ctir_to_prompt_semantics`, overlays such as `_session_view_overlay_from_ctir_interaction`). Prompt-local shapes exist for compatibility with existing contract builders.
- **Who owns it:** This module owns prompt **bundling** and contracts, but **not** re-resolution of the turn. When CTIR is present, meaning is **read**, not re-decided.
- **Explicit non-goals:** The adapter must not become a second semantic authority and must not reconstruct turn meaning when CTIR exists. `prompt_context` does **not** call `build_ctir`.

### D. Turn packet (`game.turn_packet`)

- **What it is:** A **compact**, versioned **contracts / debug / transport** snapshot for gates, retries, and diagnostics (`build_turn_packet`, metadata `turn_packet`).
- **Who owns it:** `game.turn_packet` owns the packet contract boundary.
- **Hard limits:** Not the semantic authority for the resolved turn; must **not** embed CTIR sections or grow into a parallel “full meaning” object. CTIR and turn_packet remain **separate artifacts**; small overlapping fields may exist only as explicit bridges, not as duplicated ownership.

## End-to-end lifecycle (matches landed code)

The sequence below follows `_run_resolved_turn_pipeline` and `_build_gpt_narration_from_authoritative_state` in `game.api`, plus `build_narration_context` in `game.prompt_context`.

1. **New resolved turn starts** — API enters the shared resolved-turn pipeline for `/api/action` or `/api/chat` after the engine has produced a `resolution` dict for this turn.
2. **Stale CTIR is detached from the session** — `detach_ctir(session)` runs at the **start** of `_run_resolved_turn_pipeline` so no prior turn’s CTIR can leak into the new mutation.
3. **Engine resolves and mutates canonical state** — `_apply_authoritative_resolution_state_mutation` updates scene/session/combat (and related authoritative side effects).
4. **Pre-prompt hygiene on authoritative resolution** — Inside `_build_gpt_narration_from_authoritative_state`, resolution-facing steps such as `register_topic_probe` and `apply_social_topic_escalation_to_resolution` run **after** mutation and **before** CTIR is snapshotted, so CTIR reflects post-hygiene resolution where applicable.
5. **Runtime builds or reuses CTIR once for that resolved turn** — `ensure_ctir_for_turn(session, turn_stamp=..., builder=...)` calls `build_runtime_ctir_for_narration` only when the stamp does not match the attached object (see `game.ctir_runtime`).
6. **CTIR is attached with a retry-stable stamp** — Stamp from `narration_ctir_turn_stamp(session, resolution, user_text)` is stored alongside the attached dict so retries reuse the same CTIR.
7. **`prompt_context` resolves CTIR once from the session** — `build_narration_context` calls `get_attached_ctir(session)` a single time per build; it does not construct CTIR.
8. **Adapter maps CTIR into prompt-local semantics** — `_ctir_to_prompt_semantics` and related helpers supply `resolution` / `intent` / `interaction` shapes for contracts without re-owning engine truth.
9. **GPT narration and retries reuse the same CTIR** — Targeted retry loops in `_build_gpt_narration_from_authoritative_state` do not bump the stamp; `ensure_ctir_for_turn` returns the existing attachment, so `build_ctir` is not invoked again for the same attempt.
10. **Bounded canonical reads when CTIR does not own the data** — Examples include classifier-only keys merged from caller `intent`, or roster/name resolution where CTIR carries an id but not full NPC records. Such reads must stay **bounded** and **commented** at the call site.

If `resolution` is not a dict, `_build_gpt_narration_from_authoritative_state` **detaches** CTIR and does not attach a new one; `prompt_context` then falls back to caller-supplied resolution/intent for that path.

## Boundary rules (regression-sensitive)

| Rule | Rationale |
|------|-----------|
| If CTIR is present, `prompt_context` **reads** meaning; it does not re-decide it | Prevents semantic drift and double resolution. |
| The CTIR adapter **maps** only; it is not a new owner of turn truth | Keeps a single meaning layer (CTIR) for the resolved turn. |
| CTIR must not contain prose, prompt fragments, or full raw-state mirrors | CTIR is not a narration or policy object. |
| Raw engine reads are allowed **only** where CTIR intentionally does not own that slice | Document at the call site; keep reads narrow. |
| Turn packet must not embed CTIR or become a duplicate meaning object | Preserves a clear debug/contract transport layer vs meaning layer. |

## Related tests

- `tests/test_ctir_runtime_lifecycle.py` — detach at pipeline entry, per-turn build, new turn lifecycle.
- `tests/test_ctir_retry_stability.py` — stamp-based reuse; rebuild on stamp change.
- `tests/test_ctir_turn_packet_boundary.py` — packet vs CTIR separation.
- `tests/test_ctir_snapshot_examples.py` — small shape/serialization discipline examples.
- `tests/test_prompt_context_ctir_boundary.py` — single session read, no `build_ctir`, fallback when absent.
- `tests/test_ctir_pipeline_integration.py`, `tests/test_prompt_context_ctir_consumption.py` — integration and consumption regressions.

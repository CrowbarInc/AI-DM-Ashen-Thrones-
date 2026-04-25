# Dialogue / Social Convergence (Objective C1-D)

This document defines the end-to-end ownership boundary that prevents “NPC dialogue improvisation” and ensures every dialogue-bearing social turn traces to deterministic engine semantics.

## Ownership: CTIR owns social meaning

- **CTIR is the semantic authority** for social meaning on resolved turns.
- CTIR carries the canonical classification and resolved constraints (e.g. social probe kind/subkind, whether an NPC reply is expected, and any bounded narration constraints).
- Downstream components must **not re-derive intent, speaker, pressure, or tone** from raw player text, logs, or scene prose when CTIR is attached.

## `narration_plan_bundle` builds `dialogue_social_plan`

- `game.narration_plan_bundle.build_narration_plan_bundle` constructs a per-turn bundle upstream of prompt rendering.
- As part of that bundle, it builds `renderer_inputs.dialogue_social_plan` via `game.dialogue_social_plan.build_dialogue_social_plan`.
- The plan is:
  - **Deterministic** and **derivative-only** (CTIR + already-owned bounded artifacts such as referent tracking / continuity snapshot)
  - **Structural only** (no prompt text, no prose, no “suggested lines”)
  - **Validated** by `validate_dialogue_social_plan` with strict rejection of prose-like field names.

## `prompt_context` consumes only the shipped plan

- `game.prompt_context.build_narration_context` **does not** build dialogue/social structure itself.
- For CTIR-backed social turns where an NPC reply is expected, `prompt_context`:
  - Reads `dialogue_social_plan` **only from the attached narration plan bundle**
  - Records seam audit when the plan is missing/stale (a “pipeline failure” signal, not a license to improvise)
  - Emits hard instructions that forbid compensating behavior (no invented speaker/intent/tone/pressure and no generic conversational glue).

## `gm.py` preserves the full plan for validation, but exposes only a structural projection to the model

- `game.gm.build_messages` uses `build_narration_context` to produce the model payload.
- It handles two separate responsibilities:
  - **Preserve full plan for deterministic validation**: stores the full `dialogue_social_plan` in `resolution.metadata.emission_debug.dialogue_social_plan` (trace-only).
  - **Model-facing minimization**: projects `dialogue_social_plan` to an allowlisted set of structural keys only:
    - `speaker_id`, `speaker_name`, `speaker_source`, `dialogue_intent`, `reply_kind`,
      `pressure_state`, `relationship_codes`, `tone_bounds`,
      `prohibited_content_codes`, `derivation_codes`

The model should never see validator scaffolding (`version`, `applies`, `validator`) or any prose fields (because they are not allowed in the plan in the first place).

## GPT expresses only the planned structure

- GPT’s job is to realize a reply consistent with the shipped structure:
  - The shipped `speaker_id/name` controls attribution
  - `dialogue_intent` and `reply_kind` control shape
  - `pressure_state`, `relationship_codes`, and `tone_bounds` constrain tone/edge
  - `prohibited_content_codes` prevents out-of-lane content (prompt text, narrator override, player agency override)
- GPT must not add “generic friendly glue” to simulate social continuity when the plan is missing; that is explicitly disallowed and treated as a seam failure.

## `final_emission_gate` validates: no dialogue without a valid plan

- `game.final_emission_gate.apply_final_emission_gate` enforces:
  - If output contains dialogue-bearing signals (quotes / speech verbs / attributed speaker) **or** the resolution indicates an NPC reply is expected, then a **valid `dialogue_social_plan` is required**.
  - The plan is pulled from `resolution.metadata.emission_debug.dialogue_social_plan`.
  - The gate emits metadata:
    - `dialogue_plan_checked`
    - `dialogue_plan_required`
    - `dialogue_plan_present`
    - `dialogue_plan_valid`
    - `dialogue_plan_failure_reasons`
- If the plan is missing/invalid, the gate fails closed by stripping dialogue and/or emitting a non-dialogue fallback.

## Seam failures are not permissions

Missing or stale `dialogue_social_plan` means the pipeline failed. It is **not** permission for GPT to:

- choose a speaker,
- infer intent,
- invent pressure/tone bounds,
- or add conversational glue to hide the failure.

Instead, the failure must be traceable via:

- CTIR attachment/stamp (bundle seam),
- `narration_seam_audit` (prompt boundary),
- `dialogue_plan_*` metadata (final-emission boundary).

## Regression coverage

The regression suite `tests/test_dialogue_social_convergence.py` asserts the full chain for dialogue-bearing social cases:

- CTIR is the semantic source (`intent:ctir_only`)
- `narration_plan_bundle` produces `dialogue_social_plan`
- plan `applies == True` and includes `speaker_id` + `dialogue_intent`
- model-facing projection uses only the allowlisted structural keys
- `final_emission_gate` metadata indicates the plan was checked/required/present/valid

And for non-dialogue/non-social cases:

- `dialogue_social_plan.applies == False` (or is not required)
- prompt does not force NPC dialogue
- final-emission does not require a dialogue plan unnecessarily
- narration remains unaffected


# Transition Convergence

## Purpose

**Transition Convergence** ensures that *any* narrated or observed time/location/scene transition is:

- **Planned** (a valid `narrative_plan.transition_node` exists)
- **Projected** (the plan is exported via `game/narration_plan_bundle`)
- **Consumed** (prompt assembly reads the plan as structured data only)
- **Expressed** (GPT narration follows the plan; it does not invent transitions)
- **Enforced** (scenario-spine evaluation reports hidden/disjoint transitions as failures)

This makes transition bugs traceable to **CTIR / planning seams** instead of being “papered over” by prompt fallbacks or final-emission semantic repairs.

## Allowed flow (authoritative ownership chain)

- **CTIR / resolution / state mutations** (`game/turn_pipeline` runtime owner)
  - record concrete transition signals only (e.g. `resolved_transition`, `target_scene_id`, `state_changes.scene_transition_occurred`)
- → **`game/narrative_planning`** (planning owner)
  - derive + validate **root-level** `narrative_plan.transition_node`
- → **`game/narration_plan_bundle`** (public projection)
  - project `transition_node` as shipped, without prose keys
- → **`game/prompt_context`** (consumer)
  - expose `prompt_context["transition"]` as **structured payload only**
  - never infer or repair transitions from resolution text
- → **GPT expression** (constrained by the plan)
  - may use transition phrasing **only** when backed by `transition_node`
- → **`game/scenario_spine_transition_convergence`** (enforcement / reporting)
  - observes output + recorded state and reports violations (no repair)

## Forbidden patterns (must not exist in runtime emit paths)

- **Prompt-layer time/location inference**
  - “time passes”, “later”, “elsewhere”, “scene cut”, “you arrive …” inserted because a resolver *hinted* travel
- **Fallback scene-shift narration**
  - generic “the scene shifts …” / “brief bridge from the prior location …” when no plan node exists
- **Final-emission transition repair**
  - final emission must not create, patch, or semantically invent transitions
- **Unanchored before/after movement**
  - narrated relocation without plan anchors (`before_anchor`/`after_anchor`)
- **Generic “scene shift” phrasing without `transition_node`**
  - allowed only when a valid `transition_node` exists, or in negative tests that prove unplanned transitions fail

## Debugging guide (where to look, where not to)

- **Transition signal exists but no `transition_node`**
  - Look at **CTIR / resolution** production and `game/narrative_planning` derivation inputs.
  - Fix site: runtime resolution/state mutation or planning derivation seam.

- **`transition_node` has `validation_error:*` in `derivation_codes`**
  - The planning derivation produced an invalid node or missing anchors.
  - Fix site: `game/narrative_planning` transition derivation/validation.

- **`prompt_context` lacks `transition` payload**
  - Projection or consumption seam issue.
  - Fix site: `game/narration_plan_bundle` (projection) or `game/prompt_context` (consumer-only parsing).

- **Output invents a transition**
  - This is **GPT drift** or an upstream fallback emitting transition-like prose.
  - Fix site: prompt constraints / upstream fallback text. **Not** final emission.

- **Observed state changes without `transition_node`**
  - Ownership mismatch between runtime mutation and planning.
  - Fix site: runtime `game/turn_pipeline` or planning seam; treat as a bug, not something to “repair” downstream.

- **Scenario-spine transition failure**
  - Treat as an **enforcement signal** (observability + triage), not a repair site.
  - Fix site is upstream (CTIR/plan/projection/consumer), based on the reported marker/codes.

## Ownership map (quick reference)

- **Runtime owner**: `game/turn_pipeline` (authoritative state + transition signals)
- **Planning owner**: `game/narrative_planning` (`transition_node` derivation + validation)
- **Public projection**: `game/narration_plan_bundle` (shipped plan surface)
- **Consumer**: `game/prompt_context` (structured payload only; no inference/repair)
- **Enforcement**: `game/scenario_spine_transition_convergence` (observational evaluator/reporting)
- **Final emission**: expression only; **no semantic transition invention or repair** (`game/final_emission_gate.py`)


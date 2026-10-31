# 01 — Baseline and Reproduction

ATGB-R2-02 • 2026-10-19 • offline • implementation limited to the existing addressee owner.

## Repository baseline

Branch `feature/product-realization` at `b012c3d`. The worktree was already dirty before this pass, including `data/session.json`, `data/world.json`, and `docs/NEXT_SESSION.md`. Those preexisting changes were left in place. This pass did not commit or push.

Production files at entry, before the repair, matched the R2-01 source excerpts:

- `game/interaction_completion.py` — `addressed_person_nominal` returned the raw address span.
- `game/ordinary_semantic_ownership.py` — `assess_addressee_grounding` treated a one-word third-person pronoun as contextual and every other unmatched span as an unresolved person.

No prompt, schema, provider, or frozen ATGB corpus file was part of the baseline change.

## Source boundaries

The failing host path is shared. `_communication_decision` and the pre-tick gate both call `assess_addressee_grounding`. That function calls `addressed_person_nominal`. The interpretation bridge calls the same grounding function and, only when grounding is already ambiguous, reads the nominal again. `explicit_discourse_binding` does not use `addressed_person_nominal`; it already skips a leading you/me pronoun.

Visible NPCs come from `visible_catalog`: world NPCs whose location is the active scene. The established participant is `session.interaction_context.active_interaction_target_id` when the interaction kind is social and that id is still in the visible roster. A provider target id is only a candidate.

## Original S03.3 failure

Player: "If I ask you again later, will you still tell me that same thing?"

Established participant and model-selected addressee were both `tavern_runner`. The captured interpretation is NPC/QUESTION, ASK `tavern_runner`, unresolved references empty. The host extracted `you again later`, then returned `target_resolution=unresolved`, `target_provenance=provider_candidate_only`, `operation_eligibility=requires_clarification`. Downstream category was CLARIFY, reason `unresolved_addressee`, pending kind `ambiguous_addressee`. Player-facing text: "Which person do you mean: Gate Guard or Gate Serjeant or Tavern Runner? Nothing has been attempted."

## Original S05.3 failure

Player: "Tell me more about that."

Established participant and model-selected addressee were again `tavern_runner`. The captured interpretation asks the runner for more patrol-rumor detail and selects the already public rumor as evidence. The host extracted `me more` and took the same unresolved-addressee path. The same three-person question was the player-facing result. The model's subject choice was not reached.

## Reproduction evidence

Before any edit, the current functions were called with `data/world.json`, `data/scenes/frontier_gate.json`, a social interaction focused on `tavern_runner`, and the captured adapted records in `artifacts/atgb/atgb_r2_01/representative_traces.json`.

Both turns reproduced the historical host decision, not merely a similar sentence. Extracted candidates were `you again later` and `me more`. Grounding eligibility was `requires_clarification`. `decision_from_interpretation_record` returned CLARIFY / `unresolved_addressee` and the historical which-person text. Artifact: `artifacts/atgb/atgb_r2_02/baseline_reproduction.json`.

## Scope confirmation

The defect is inside the shared nominal helper and the grounding owner. Callers do not need a local exemption. No new persistent key is required. The captured records are sufficient; nothing was invented to stand in for a missing interpretation.

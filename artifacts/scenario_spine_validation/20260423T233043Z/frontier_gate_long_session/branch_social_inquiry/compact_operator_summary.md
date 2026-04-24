# Scenario spine validation — frontier_gate_long_session / branch_social_inquiry

- **Scenario id:** `frontier_gate_long_session`
- **Branch id:** `branch_social_inquiry`
- **Scripted branch turns:** 25
- **Executed turns this run:** 5
- **Run scope:** smoke

## Session health

- **Classification:** warning
- **Score:** 93
- **Overall passed (evaluator):** True

## Axes

| Axis | Passed | Failure codes | Warning codes |
|------|--------|---------------|---------------|
| `branch_coherence` | True |  |  |
| `narrative_grounding` | True |  |  |
| `referent_persistence` | True |  |  |
| `state_continuity` | True |  | continuity_anchor_absent_late_window |
| `world_project_progression` | True |  |  |

## Top failures

- _(none)_

## Top warnings

- `state_continuity` **continuity_anchor_absent_late_window** — continuity ca_active_problem present early but not in final third window

## First failing checkpoint

- `cp_patrol_thread_deepens`

## Suggested next debugging area

- **none (inspect warnings or checkpoint weak signals if present)**

## Fixture notes

- `branch_social_inquiry` (25 turns) is the default **full** scripted long-session branch for this fixture.
- `branch_direct_intrusion` and `branch_cautious_observe` are **short alternate** paths: useful for divergence, 
  smoke, and routing checks — not described here as 60–90 minute full-session branches unless expanded later.

# Scenario spine validation — frontier_gate_long_session / branch_social_inquiry

- **Scenario id:** `frontier_gate_long_session`
- **Branch id:** `branch_social_inquiry`
- **Scripted branch turns:** 25
- **Executed turns this run:** 5
- **Run scope:** smoke

## Session health

- **Classification:** degraded
- **Score:** 27
- **Overall passed (evaluator):** False
- **Metadata completeness:** **pass** · checked=5 · turns_with_gaps=0 · envelope_key_miss_events=0

## Axes

| Axis | Passed | Failure codes | Warning codes |
|------|--------|---------------|---------------|
| `branch_coherence` | True |  |  |
| `narrative_grounding` | True |  |  |
| `referent_persistence` | True |  | referent_absent_late_window |
| `state_continuity` | True |  | continuity_anchor_absent_late_window, continuity_anchor_weak_by_checkpoint |
| `world_project_progression` | False | progression_missing_by_checkpoint |  |

## C1-A opening convergence (observational)

**Pass** — no hard opening-convergence failures on evaluated opening turn(s).

### Counts (opening turns)

- **Opening turns checked:** 1
- **Plan-backed openings:** 1
- **Missing plan / scene_opening:** 0
- **Invalid recorded scene_opening:** 0
- **Seam hard failures** (`scene_opening_seam_invalid`): 0
- **Anchor grounding failures:** 0
- **Stock opener phrase hits** (warning-style unless verdict fail): 0
- **Resume-entry openings checked:** 0
- **Repeated generic first-line** (warning-style unless verdict fail): False

### Opening convergence failures (compact table)

_No failure rows — either **pass** or **no observations**._

## Top failures

- `world_project_progression` **progression_missing_by_checkpoint** — prog_patrol_investigation_advances not evidenced by checkpoint cp_patrol_thread_deepens window

## Top warnings

- `state_continuity` **continuity_anchor_weak_by_checkpoint** — checkpoint cp_after_notice_read: weak continuity for ['ca_scene_objective']
- `state_continuity` **continuity_anchor_weak_by_checkpoint** — checkpoint cp_patrol_thread_deepens: weak continuity for ['ca_active_problem']
- `state_continuity` **continuity_anchor_absent_late_window** — continuity ca_location present early but not in final third window
- `state_continuity` **continuity_anchor_absent_late_window** — continuity ca_scene_objective present early but not in final third window
- `referent_persistence` **referent_absent_late_window** — required referent ref_ash_compact_census not present in final third gm window
- `referent_persistence` **referent_absent_late_window** — required referent ref_captain_thoran not present in final third gm window
- `referent_persistence` **referent_absent_late_window** — required referent ref_notice_board not present in final third gm window

## First failing checkpoint

- `cp_after_notice_read`

## Suggested next debugging area

- **progression**

## Fixture notes

- `branch_social_inquiry` (25 turns) is the default **full** scripted long-session branch for this fixture.
- `branch_direct_intrusion` and `branch_cautious_observe` are **short alternate** paths: useful for divergence, 
  smoke, and routing checks - not described here as 60-90 minute full-session branches unless expanded later.

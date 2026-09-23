# PR-BF — AI Experience / Gameplay: Unresolved Travel Narration Authority and Scene-Stock Integrity

Date: 2026-09-22
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Probe artifacts: `artifacts/prbf_unresolved_travel/probe/`

---

## 1. Executive Summary

The handoff residue was real and recoverable. It was **narration corruption**, not state corruption.

PR-AJ freeform probe T6 asked to chase a prose-only western cart road. Authoritative gameplay stayed at `frontier_gate` with `kind=travel` and `resolved_transition=False`. Live-model narration still described setting off and leaving the gate district, using current-scene-like stock plus destination echo.

That exact HTTP path later often fail-closed to `"That destination is not available from here."` or `"the attempt meets resistance."` The first incorrect decision remained: realization treated **travel kind** as travel-success eligibility.

Two existing owners could still emit arrival/current-scene stock after an unresolved travel request:

* `apply_destination_arrival_realization_to_gm` replaced ungrounded stock with `render_travel_arrival_fallback_line` for any `travel` / `scene_transition` kind.
* Scene-emit integrity global fallback used that same arrival line whenever a travelish turn had no older integrity flags.

The repair reuses the existing travel-success signal: `resolved_transition is True` (or an equivalent scene-transition state-change flag). No new travel system, geography database, route planner, or destination synonym list was added.

---

## 2. Recovered Failing Case

Source: `artifacts/praj_authoritative_lead_provenance/freeform_probe/20260920T115111Z_probe.md`, Turn 6. Later handoffs shortened this to `"Unresolved travel can still be narrated as scene stock."`

```text
PLAYER: I'll go chase that closed western cart road you mentioned.
```

Historical GM:

```text
The muddy lane west of the gate stretches thin and quiet, slick with recent
rain and marked by ruts where carts once passed. You set off briskly, the
glint of lanterns fading behind you as the Cinderwatch gate district recedes
into the mist. The closed western cart road you aim…
```

Recorded structured result: `kind=travel`, `resolved_transition=False`, `target=None`, scene `frontier_gate`.

The destination is not an authored exit. Frontier Gate exits remain `Enter Cinderwatch` → `market_quarter` and `Follow the missing patrol rumor` → `old_milestone`.

---

## 3. Complete Travel Trace

Before production change, recovered on current code:

| Stage | Result |
| --- | --- |
| Raw input | `I'll go chase that closed western cart road you mentioned.` |
| Destination extraction | `chase that closed western cart road you mentioned` |
| Authored exit | none |
| Parsed intent | `travel`, no `target_scene_id`, no travel-destination regex hit (`go chase` is not `go to/for`) |
| Travel authorized | no |
| Scene before | `frontier_gate` |
| Scene after | `frontier_gate` |
| State mutation unique to travel | none |
| Success signal | `resolved_transition=False`, `target_scene_id=None`, `success=False` |
| Exploration hint (before) | `Narrate based on current scene and intent.` |
| Historical narration source | live-model prose: invented west-lane stock + `You set off` + player-destination echo |
| Stay/leave on historical text (before) | no replacement (`set off` ≠ `set out`; no `you leave/arrive`) |
| Destination-arrival on ungrounded stock | `The new ground shows itself: rain, choke traffic…` |
| Integrity fallback on unresolved travel | same arrival / current-scene stock |
| HTTP finalize of historical T6 text | later pipeline often replaced with `"That destination is not available from here."` |

The HTTP fail-close did not erase the first incorrect decision. Arrival stock still leaked on the destination-arrival and integrity-fallback owners.

---

## 4. Authoritative Travel-Success Signal

Travel succeeded only when gameplay state actually transitioned.

Trusted signal:

```text
resolution.resolved_transition is True
```

Equivalent supporting flags, already used by retry arrival eligibility:

* `state_changes.scene_transition_occurred`
* `state_changes.scene_changed`
* `state_changes.arrived_at_scene`

Not success evidence:

* player-requested destination words
* destination words in prose
* available current-scene stock
* model-generated arrival / departure language
* `kind` being `travel` or `scene_transition`

Downstream narration must trust the success signal, not the action kind.

---

## 5. State Before / After

| Case | Before | After | Transition |
| --- | --- | --- | --- |
| Historical T6 / unknown dest | `frontier_gate` | `frontier_gate` | no |
| `I'll go to the glass observatory.` at mossy_crossing | `mossy_crossing` | `mossy_crossing` | no |
| `I'll take the trail.` (ambiguous) | `mossy_crossing` | `mossy_crossing` | no |
| `I go to the frontier gate.` while already there | `frontier_gate` | `frontier_gate` | no |
| `I'll take the pine trail.` | `mossy_crossing` | `hill_shrine` | yes |
| `I'll head to the old milestone.` | `frontier_gate` | `old_milestone` | yes |
| `I step closer.` | current scene | current scene | local `custom` only |
| `I look around.` | current scene | current scene | observe |

No invented destination, route, travel duration, or exit was added.

---

## 6. Narration Source

| Path | What it emitted before | After |
| --- | --- | --- |
| Live-model T6 | invented lane stock + `You set off` + destination echo | stay/leave now catches `set off` |
| Destination-arrival | arrival line for any travel kind | arrival line only after success |
| Scene-emit integrity fallback | arrival / current-scene stock for ordinary unresolved travel | existing unfinished-way safe line |
| Action-result summary | `your position in the scene changes` when success flag was absent | `the attempt meets resistance` |
| Exploration hint | `Narrate based on current scene and intent` | do not imply departure or arrival |
| Existing unknown-dest HTTP | `You go to the quay, and the attempt meets resistance.` | preserved as a safe fail-closed terminal |
| Successful transition | destination / departure narration | preserved |

Requested-destination leakage in `"You go to the quay, and the attempt meets resistance."` is player echo plus a failure terminal. It is not treated as current-location evidence.

---

## 7. Travel Outcome Matrix

| Class | Input | Execution | Narration requirement |
| --- | --- | --- | --- |
| Known valid destination | `I'll take the pine trail.` / `I'll head to the old milestone.` | `scene_transition`, scene changes | departure/arrival allowed |
| Known current location | `I go to the frontier gate.` while at the gate | `travel`, no transition | must not claim arrival |
| Unknown destination | T6 western cart road; `I'll go to the glass observatory.`; `I go to the quay.` | `travel`, no transition | no arrival, no invented place |
| Ambiguous destination | `I'll take the trail.` at a two-trail scene | `travel`, no guess | no arrival |
| Malformed travel | `I go.` / `I head out.` | often `kind=None` | not absorbed; not taught as travel |
| Local movement | `I step closer.` / `I pace.` | existing `custom` | not failed scene travel |
| Observation | `I look around.` | existing `observe` | unchanged |

---

## 8. First Incorrect Decision

**Hypothesis B, with A as a licensed consequence.**

Fallback / destination-arrival realization received current-scene stock without a travel-success signal. Travel *kind* was treated as arrival eligibility.

Not demonstrated:

* C as the first owner: current-scene description can sound like movement, but the first wrong grant was eligibility, not phrasing alone.
* D as the owner: requested destination text appears in some fail-closed terminals as player echo, not as world-state evidence.
* E: scene identity and persistence were correct.
* A travel-system defect: destination binding already failed closed.

The GPT hint `"Narrate based on current scene and intent"` licensed scene-stock realization after that eligibility error. Stay/leave was an incomplete backstop (`set out` but not `set off`; no check for engine arrival stock).

---

## 9. State vs Narration Classification

**Narration corruption.**

Authoritative scene/location state did not change on unresolved travel. Player-facing prose could still imply departure, arrival, or “new ground.”

Not both. Not neither. The original T6 live-model text reproduced on the stay/leave and fallback owners even when some HTTP finalize paths later overwrote it.

---

## 10. Requested-Destination Leakage

| Source | Finding |
| --- | --- |
| Player echo | Present on some fail-closed lines (`You go to the quay, and the attempt meets resistance.`) |
| Destination candidate metadata | No dest minted; `target_scene_id` empty |
| Pending leads | Not substituted (PR-AE / scene-transition authority still holds) |
| Current-scene stock | The leak: used as if a transition had completed |
| Off-scene authored content | Not the T6 owner; PR-AX remains separate |
| Model invention | Historical T6 west-lane / mist / lanterns fading |

Requested state is not actual state. The repair does not add the western cart road.

---

## 11. Repair-Threshold Decision

Production change **was** justified.

* The failure reproduced on recovered T6 text and on the arrival-stock owners.
* Narration materially implied unsupported movement (`You set off`, `The new ground shows itself`).
* A shared first incorrect decision existed: success-signal vs kind.
* Existing owners already had correct unresolved terminals.
* Successful travel and PR-AQ local movement can be preserved.

Not repaired because prose was awkward, synonyms were incomplete, or a paraphrase failed to parse.

---

## 12. Production Changes

Generic owners only. No Frontier Gate / western-road special cases.

1. `game/narration_state_consistency.py`
   * `_resolution_supports_travel_success` is the shared success check.
   * Destination-arrival uses arrival stock only after that signal. Unresolved travel no longer mints `render_travel_arrival_fallback_line`.
   * Stay/leave treats `set off` like `set out`, and treats engine stock `the new ground shows itself` as an implied transition.

2. `game/final_emission_scene_emit_integrity.py`
   * Unresolved `travel` / `scene_transition` is an integrity failure reason (`unresolved_travel`).
   * Global fallback then uses the existing unfinished-way safe line instead of arrival stock.

3. `game/exploration.py`
   * Unknown-destination hint no longer says “narrate based on current scene.” It uses the existing blocked-travel wording.

4. `game/upstream_response_repairs.py`
   * `_action_result_summary` claims a position change only after a success signal.

Existing terminals reused:

* `"That destination is not available from here."`
* `"You move as if to cross into it, but the way stays unfinished and leaves you where you began."`
* `"the attempt meets resistance"`

No second travel router. No geography database. No route planning. No invented duration.

---

## 13. Semantic / Generalization Validation

Scenario-independent fixtures in `tests/test_unresolved_travel_narration_authority.py` use `mossy_crossing` / `hill_shrine`, not Cinderwatch vocabulary.

| Requirement | Result |
| --- | --- |
| Recovered T6 | stay/leave and HTTP no longer emit `set off` / receding district |
| Valid authored transition | mossy → shrine; milestone still binds |
| Scene state before/after valid travel | changes to the authored destination |
| Unknown destination | no transition; no arrival / new-ground stock |
| Scene state before/after unknown dest | unchanged |
| Ambiguous / unresolved travel | `I'll take the trail.` does not guess |
| Current-location travel | remains unresolved; no invented return |
| Local movement | `I step closer.` stays `custom` |
| Observation | `I look around.` stays `observe` |
| No invented destination / route / arrival / duration | held |
| No prior-scene geography as current | PR-AX suite still passes |
| Successful arrival still destination-eligible | destination-arrival and integrity keep arrival stock after success |
| PR-AQ local movement | physical-action suite still passes |
| Destination-binding / scene-transition suites | pass |
| Existing scene-integrity contrast tightened | unresolved named-place-in-text now also blocks arrival stock |

Live-model realization was validated semantically on the recovered T6 text and on stubbed HTTP paths that previously selected arrival stock. Structural assertions were not treated as playability.

---

## 14. Regressions

Focused suites passed after the repair:

* `tests/test_unresolved_travel_narration_authority.py`
* `tests/test_generalized_destination_exit_resolution.py`
* `tests/test_arrival_destination_realization.py`
* `tests/test_final_emission_scene_emit_integrity.py`
* `tests/test_final_emission_scene_integrity.py`
* `tests/test_physical_action_typing_compound_perception_realization.py`
* `tests/test_stay_leave_social_lock_override.py`
* `tests/test_scene_transition_authority.py`
* `tests/test_post_return_observation_geographic_integrity.py`
* `tests/test_scene_destination_binding.py`
* `tests/test_exploration_resolution.py`

One prior baseline was **tightened**, not weakened: `test_named_place_unresolved_suppresses_global_fallback` no longer allows unresolved `explicit_named_place_in_player_text` to use global scene-stock fallback.

Full authoritative suite was not re-run. Structural PASS is not semantic playability.

---

## 15. Accepted / Deferred Residue

Accepted / unchanged:

* `"I go."` / `"I head out."` remaining `kind=None` is malformed travel, not this owner.
* Fail-closed `"the attempt meets resistance"` may echo the player’s requested destination.
* Richer unknown-destination content (why the road is closed, who could guide, how long it would take) is a future gameplay capability.
* `"I step back."` remains outside the PR-AQ local-movement regex.
* Compound N-action execution remains deferred.

Not absorbed:

* opening `Gate Guard mutters` / `"Word is,"`
* follow-up topic / public-clue paraphrases
* `"Gate Serjeant"` mapping
* evaluator lexical false negatives
* `"The guard says"` absent-speaker label
* wait / time-passage
* PR-AX through PR-BE settled owners

---

## 16. Explicit Convergence Assessment

### A. Does the reported unresolved-travel narration defect reproduce?

**Yes.** Recovered T6 plus arrival-stock fallback both implied a transition that state did not perform.

### B. Did authoritative scene/location state actually change?

Failing cases: **No.** Successful authored transitions: **Yes**, to the bound destination.

### C. Is the defect state corruption, narration corruption, both, or neither?

**Narration corruption.**

### D. What is the authoritative travel-success signal?

`resolved_transition is True`, or an equivalent scene-transition state-change flag.

### E. What was the first incorrect decision?

Realization / fallback treated `kind=travel` or `kind=scene_transition` as permission to emit arrival or current-scene stock.

### F. Was production code changed?

**Yes.**

### G. If changed, what general invariant was repaired?

```text
no authoritative transition -> no narration of successful transition
```

Travel kind is not a success signal. Scene stock is eligible for travel narration only after the success signal.

### H. Are unresolved-travel semantics sufficiently converged afterward?

**YES** — successful and unsuccessful spatial outcomes remain distinct.

A richer unknown-destination *capability* (routes, durations, NPC guidance) is deferred, not missing from this owner.

---

## 17. Recommended Next Action

Unresolved-travel scene-stock integrity is closed. Do not open another destination-synonym or travel-router cycle.

If the next slice stays in AI Experience, pick a **different** remaining sibling owner:

* Replay / opening `Gate Guard mutters` / `"Word is,"` (do not reopen PR-AI without new causal evidence)
* Follow-up paraphrases that miss owned-topic / public-clue overlap
* `"Gate Serjeant"` mapping
* Evaluator lexical false negatives on quiet listen and nothing-new
* `"The guard says"` generic absent-speaker label

Primary lane: AI Experience. Secondary lane: Gameplay.

---

## 18. Git / Worktree State

Branch: `feature/product-realization` at checkpoint `4c0a454`, plus uncommitted PR-AS through PR-BF work.

Not committed. Not pushed.

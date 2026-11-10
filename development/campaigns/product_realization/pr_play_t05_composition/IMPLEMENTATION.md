# Implementation

Only `game/response_policy_enforcement.py::enforce_scene_momentum` changes, by 18 lines. Existing prerequisites remain: valid GM dict, scene id, momentum due, and no existing momentum tag. Immediately before invoking the stock renderer, query the existing `revealed_information` owner. A selected disclosure requires successful discover_clue/investigate/observe, nonempty clue_text/discovered_clues and no already_searched flag.

When selected information exists, return a detached copy preserving every existing candidate field and all text. Internal emission_debug.scene_momentum_composition records appended=false, selected_information_takes_precedence and the excluded renderer source. The existing scene_momentum:new_information tag identifies the actual clue disclosure, satisfying momentum cadence without inventing pressure or an event. The stock component has not yet been assembled, so no prose deletion is needed. The stock renderer has no resolver-specific information and therefore cannot supply an authorized physical result or selected clue in this branch.

Selected clue, player-requested information, resolved physical outcomes, state changes and existing descriptive elaboration all survive unchanged. Existing tagged momentum remains intact. Failed/unselected/already-searched information, NPC dialogue, travel, physical actions and ordinary atmosphere use their existing paths. This does not sanitize unrelated content already present in a candidate or block other atmosphere owners.

The unchanged parent policy entry guard skips immutable responses; the change happens during initial assembly before normal hard validation and sealing. No public HTTP field, accepted-response logic, authority projection, claim extraction, prompt, provider budget or retry changes. `game/api.py`, immutable_valid_response.py and referenced_surface.py are byte-identical to entry.

Tests: tests/test_pr_play_t05_composition.py (15 cases). Seven original unaffected controls and eight demonstrations of stock contamination run unchanged before/after. The original HTTP test captures the actual sealed record, verifies normal hard validity/digest, checks published/pointer equality and re-enters policy enforcement to verify immutability. Existing 17 pre-seal tests cover hidden inspections, item acquisition, physical-result precedence, travel, dialogue, sensory improvisation and validation failure behavior.

Cycle-only diff: artifacts/pr_play_t05_composition/production.diff, relative to preserved dirty entry bytes, not Git HEAD.

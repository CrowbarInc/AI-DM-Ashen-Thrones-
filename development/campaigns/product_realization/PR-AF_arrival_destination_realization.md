# PR-AF — Gameplay / Content & World: Arrival and Destination Realization

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Report location: repository root, matching the Product Realization report convention (`PR-AA` through `PR-AE`).

Replay artifacts: `artifacts/praf_arrival_destination/`

---

## 1. Executive Summary

PR-AF repaired the highest-leverage remaining ordinary-play failure after PR-AE: a legitimate pursuit from `frontier_gate` arrived at `old_milestone`, but the destination was an explicit content stub (`"a blank scene awaiting definition"`).

This is not a new scene schema, a world-generation campaign, or a missing-patrol quest. Existing owners remain authoritative: authored `data/scenes/*.json` templates (`scene_state`), exploration resolution, interactables/clues, and existing arrival/observe fallbacks.

The failure was **content-primary**, with a **narrow realization guard**.

Player-facing behavior is demonstrably improved on the targeted slice:

- Pursuit still transitions `frontier_gate` → `old_milestone` and clears the Guard Captain.
- Arrival / first look no longer presents the undefined placeholder.
- A normal look produces authored milestone / mud-track / print facts.
- Examining the milestone or searching the mud resolves through existing investigate/clue machinery.
- Patrol-relevant investigation can discover only `milestone_mud_prints`: prints are present, but number, origin, and direction stay unclear. The patrol's fate is not authored and is not solved.
- An authored return exit to `frontier_gate` exists and resolves when the player uses the exit language.

PR-AD authored-knowledge and PR-AE stay/leave/social-lock contracts remain intact. RC-10 and RC-21 remain settled.

The product is still not fully playable as an ordinary conversational AI-DM. After arrival works, the next ordinary action — going back — is the newly dominant hole: natural `"I'll head back to the gate"` / `"I'll head back to Cinderwatch Gate"` can fail to bind the authored return, and live narration may claim departure anyway.

---

## 2. Starting Failure

PR-AE made the northwest pursuit authoritative. The next player action — arrive and continue — still failed.

Representative path (PR-AE replay of R2-MT01 T7–T8):

1. Player learns `notice_patrol_route` and says `"Fine. I'll follow the missing patrol rumor along that northwest mud track."`
2. Authoritative scene becomes `old_milestone`. Interlocutor is cleared.
3. Arrival / follow-up narrates: `"In Old Milestone, a blank scene awaiting definition"`.
4. The player has no usable world surface for the next decision.

---

## 3. `old_milestone` Stub Investigation

`data/scenes/old_milestone.json` was an explicit destination shell, not a load or realization miss.

Before PR-AF it stored:

- `id`: `old_milestone`
- `location`: `Old Milestone` (the only non-default field)
- `summary`: `"A blank scene awaiting definition."`
- empty `visible_facts`, `discoverable_clues`, `hidden_facts`, `exits`, `enemies`, `actions`
- no interactables

That summary is the `default_scene()` fallback for any scene other than `frontier_gate` / `market_quarter`. The file was created as a reachable shell for the missing-patrol exit, then left undefined.

The player-facing line `"In Old Milestone, a blank scene awaiting definition"` originates from existing arrival/observe fallback (`render_travel_arrival_fallback_line`), which prefixes `location` onto `summary`. Realization was working. It was realizing a stub.

Richer `old_milestone` copies in old replay artifacts (dead courier, scavenger bandit, burnt letter) are mutated playthrough residue, not canon. They were not restored.

A T8 invented lead about trampled footprints during the PR-AE replay was GPT/lead-ingestion residue against an empty clue list, not recovered canon.

---

## 4. Existing Destination / Scene Contract

Recovered from `frontier_gate`, `market_quarter`, `scene_investigate`, `game/validation.py`, `game/defaults.py`, `game/affordances.py`, `game/exploration.py`, and `game/diegetic_fallback_narration.py`.

### A. Required scene fields / contracts

- `scene.id` matching the file stem
- `scene.location`
- `scene.summary`
- Valid `exits[].target_scene_id` when exits exist
- Unique interactable ids
- `reveals_clue` must reference `discoverable_clues` when both exist

### B. Optional richness

- `visible_facts`, `opening_seed_facts`, `journal_seed_facts`
- `discoverable_clues` (string or `{id, text}`)
- `interactables` with `id`, `type`, optional `label` / `aliases`, `reveals_clue`
- `hidden_facts`, `addressables`, `enemies`, `actions`
- Scene-local NPCs via world `location`

### C. Compatibility / legacy

- `targetSceneId` alongside `target_scene_id`
- String-form discoverable clues
- `default_scene()` stub factory for unknown ids

### D. Generated / derived

- Affordances from visible facts, interactables, and exits
- Observe / arrival fallback lines from summary + visible facts
- `process_investigation_discovery` reveals the next undiscovered clue on generic investigate
- Player-facing text is derived, not authoritative

Minimum playable destination: identity + non-stub summary + at least one visible fact or interactable/clue + enough connectivity that the player is not trapped.

---

## 5. Recovered Content Intent

Existing authoritative sources, in preference order:

| Source | Intent recovered |
| --- | --- |
| `frontier_gate` exit | `"Follow the missing patrol rumor"` → `old_milestone` |
| `notice_patrol_route` | Last seen on the northwest mud track past the crates |
| `default_world` captain topic | `"A patrol went missing near the old milestone."` |
| Live `tavern_runner` topic | `"The runner heard the patrol vanished near muddy footprints northwest of the crates."` (`muddy_footprints_northwest`) |
| File location | `"Old Milestone"` |
| Destination binding | `old_milestone` is outdoor / road / wilderness |
| `market_quarter` / `tavern` exits | Paths point here; they do not define contents |

Not recovered, and therefore not authored as fact:

- the patrol is dead or alive
- a named attacker or faction at the marker
- a present NPC
- treasure
- a continuing authored destination beyond the marker
- a solved disappearance

A historical mutated artifact with a dead courier and hidden bandit was rejected as non-canonical.

---

## 6. New Content Added

Deliberately authored PR-AF content, conservative and pursuit-consistent:

- Summary: a weathered milestone beside the northwest mud track, road thinning into scrub and standing rainwater.
- Visible / opening / journal facts: the stone, churned mud with faint overlapping prints, and an unclear next step.
- One discoverable clue, `milestone_mud_prints`: prints exist; number, origin, and direction stay unclear.
- Two interactables sharing that clue: `milestone` and `prints` (so “examine the stone” and “inspect the footprints” both hit existing machinery).
- One return exit: `"Return to Cinderwatch Gate"` → `frontier_gate`.

No NPC, no combat, no onward invented destination, no patrol fate.

The same envelope is now the `default_scene("old_milestone")` factory so campaign-start fixtures match the file.

---

## 7. Implementation

### Content

- `data/scenes/old_milestone.json`
- `game/defaults.py` (`default_scene("old_milestone")`)

### Narrow realization

`apply_destination_arrival_realization_to_gm` in `game/narration_state_consistency.py`, applied after PR-AE stay/leave agreement on the existing `/api/action` and `/api/chat` late seams.

It does **not** invent facts. It replaces only known ungrounded stock when the destination already has usable authored content:

- `"blank scene awaiting definition"`
- anti-reset continuation (`"Nothing new locks in yet..."`)
- generic observe repair (`"you get an immediate read on what is there"`)

Replacement uses existing `render_travel_arrival_fallback_line` / `render_observe_perception_fallback_line`.

PR-AE stock movement (`"You act on that decision and leave along the available path."`) is left alone.

### Minimum supporting operator fix

`game/api.py` engine print `"Scene transition →"` became `"Scene transition ->"`. The Unicode arrow crashed live Windows replay/probe (`UnicodeEncodeError` on cp1252) after a successful transition, which directly blocked PR-AF arrival evidence. This is the deferred operator-encoding issue, reduced to the one print that blocked this slice.

No new scene schema, knowledge store, clue system, or travel owner.

---

## 8. Arrival Realization

The arrival problem was both:

- **content**: stub summary/facts
- **realization-adjacent**: existing fallbacks and late stock lines could still emit the placeholder or a fact-free observe line even after content existed

Once the scene is defined, arrival fallback orients from summary (`"In Old Milestone, a weathered milestone leans..."`). The first look can still be captured by anti-reset / generic observe stock; the PR-AF hook yields those lines to the existing observe fallback.

Live replay T7 still uses the PR-AE stock movement line. T8 immediately orients with authored destination content. That is enough to continue play. Arrival orients; it does not dump the whole scene.

---

## 9. Investigation / Interaction Behavior

| Player shape | Owner | Result |
| --- | --- | --- |
| `"I look around."` | observe + visible facts / fallback | Grounded milestone / mud / track facts |
| `"I examine the milestone."` | interactable `milestone` | `discover_clue` → `milestone_mud_prints` |
| `"I inspect the footprints."` | interactable `prints` | same clue |
| `"I look for signs of the patrol."` | generic investigate + `process_investigation_discovery` | same authored uncertainty, no fate |
| `"I'll return to Cinderwatch Gate."` | authored exit | `frontier_gate` |

PR-AD realization still speaks a written clue. Narration does not own the discovery.

---

## 10. Authority Preservation

- Scene data remains the destination owner.
- Narration does not create NPCs, exits, or destinations.
- The new clue is authored scene content, not model-invented truth.
- Hidden information remains absent; there is no authored patrol fate to leak.
- Social engagement is still not movement authority (PR-AE).
- Authored notice/watch-command facts still realize (PR-AD).
- `pending_leads` was not migrated. RC-10 / RC-21 were not reopened.
- Protected-replay baselines were not refreshed.

---

## 11. Tests Added or Updated

Added: `tests/test_arrival_destination_realization.py`

- Scene is no longer a stub and validates.
- T7 pursuit still binds `old_milestone`.
- Look-around / examine / inspect-footprints parse to existing lanes.
- Observe and arrival fallbacks use authored facts.
- Stub and anti-reset / generic-observe stock are replaced only when the destination is defined.
- PR-AE stock movement is not rewritten.
- Milestone investigate discovers `milestone_mud_prints`.
- Generic patrol search reveals only authored uncertainty.
- Return exit resolves to `frontier_gate`.
- House Verevin is not invented.
- HTTP: pursuit arrival, observe, examine, patrol search, return, and PR-AD notice regression.

Existing tests were not weakened.

---

## 12. Extended Before / After Replay

Original R2-MT01 prompts were not rewritten. Continuation turns were added in a PR-AF-only scenario:

`data/validation/praf_arrival_destination/scenarios.json`

After: `artifacts/praf_arrival_destination/extended_replay/runs/20260920T012314Z_R2-MT01-AF/transcript.md`

| Turn | Player | Before (PR-AE) | After (PR-AF) | Human |
| --- | --- | --- | --- | --- |
| T2 | I read the notice board | Authored patrol fact | Same | Pass — PR-AD preserved |
| T7 | I'll follow the missing patrol rumor… | `frontier_gate` → `old_milestone`; stock movement | Same transition and lock release | Pass — PR-AE preserved |
| T8 | After I start that way… | `"a blank scene awaiting definition"` | `"In Old Milestone, a weathered milestone leans beside the northwest mud track..."`; `milestone_mud_prints` written | Pass for destination identity |
| T9 | I look around. | n/a (PR-AE stopped) | Authored prints / uncertainty spoken | Pass |
| T10 | I examine the milestone. | n/a | `discover_clue`; already-written clue | Pass for machinery; prose is thin |
| T11 | I look for signs of the patrol. | n/a | Grounded prints / milestone; no fate | Pass |
| T12 | I'll head back to Cinderwatch Gate. | n/a | `travel` unresolved; scene stays; stock resistance | Fail — next slice |

First extended attempt (`20260920T012146Z`) crashed on the Unicode engine print and never left the gate. That run is retained as evidence of the operator-encoding blocker.

---

## 13. Freeform Arrival Probe

Diagnostic only. Natural phrasing, not copied from tests.

Artifact: `artifacts/praf_arrival_destination/freeform_probe/20260920T012534Z_probe.md`

| Turn | Player | Result |
| --- | --- | --- |
| 1 | walk up and read the notice | Patrol fact spoken; still at gate |
| 2 | heading out after them along that northwest track | `scene_transition` → `old_milestone`; social cleared |
| 3 | Where am I? | Grounded mud / prints / unclear track. Grammar of observe fallback is awkward |
| 4 | I look around. | Milestone and unclear onward track |
| 5 | search the mud for any sign of that patrol | Authored churned prints; no fate |
| 6 | examine the weathered stone | Grounded stone + prints; live prose also invents faded inscriptions / distance numbers |
| 7 | wait and watch the track | Stays at destination; prints remain unclear |
| 8 | I'll head back to the gate | `travel` but `resolved_transition=False`; scene stays `old_milestone`; narration claims the gatehouse appears |

The player can understand the scene, identify something to do, and investigate. Coherence next breaks on return: state does not move, narration may claim it did.

---

## 14. Validation Results

| Gate | Result |
| --- | --- |
| New PR-AF tests | Pass (`tests/test_arrival_destination_realization.py`) |
| PR-AD authored-knowledge tests | Pass |
| PR-AE stay/leave / social-lock tests | Pass |
| Scene validation / graph / destination binding / scene-transition authority | Pass |
| Exploration / affordance / discovery memory | Pass |
| Intent parser / dialogue routing | Pass |
| State authority / narrative authority | Pass |
| Diegetic fallback / content lint | Pass |
| Round #1 calibration corpus | 13/13 (`artifacts/praf_arrival_destination/round1_calibration/`) |
| Extended R2-MT01-AF replay | Material arrival/investigation improvement; see §12 |
| Freeform arrival probe | Diagnostic; see §13 |
| Full authoritative suite | Not re-run as a complete 6,450-test pass. Focused files above are green. Protected-replay / mutation-attribution reds from PR-AD were not refreshed |

Shared Windows `codex_pytest_tmp` `PermissionError` remains environmental. Focused HTTP tests were run with an isolated `--basetemp`.

Structural PASS is not semantic playability. Automated FAIL on T8/T11 is evaluator residue against grounded destination facts that do not share the player's "warning/changed/patrol signs" tokens.

---

## 15. Remaining Semantic Failures

- Natural return from `old_milestone` (`"I'll head back to the gate"`, `"I'll head back to Cinderwatch Gate"`) may not bind the authored exit. Live narration can claim return anyway.
- First-look / `"Where am I?"` observe fallback can be grammatically stacked.
- Live examine prose can invent stone inscriptions not present in scene data.
- T10 already-discovered examine can emit `"you turn up a concrete clue"` without restating the clue.
- Bound `guard_captain` first-ask residue remains (`"I don't know"` / empty concern).
- Glance/observe can still force `"Board, runner, or road"`.
- `narration_ctx_…` lead ingestion from prose still occurs (replay T6).
- Some authored lines still use the `mutters` / `"Word is,"` envelope.

---

## 16. Deferred Findings

Unchanged unless noted:

- `compat_pending_lead_needed` still keys off a scene target only.
- Intent parsing still reads `pending_leads` as the pursuit surface.
- Broader lead/clue overlap reduction.
- House Verevin / rooftop invention.
- Forced `"Board, runner, or road"` fork.
- Remaining scene-transition Unicode / operator-encoding (only the blocking engine print was ASCII-normalized).
- PR-AB tooling / product-integrity.
- General prompt rewrite or NPC dialogue redesign.
- Project-wide State ↔ Narration campaign.
- Protected-replay baseline refresh.
- Other stub scenes (`eastern_square`, `wild_moors`, `alley`, …) were not filled. PR-AF evidence is content-local to `old_milestone`, not proof of a systemic destination-realization rewrite.

---

## 17. Recommended Next Product Slice

**Destination return / onward travel from `old_milestone`.**

Not chosen from roadmap neatness. Chosen because PR-AF closed the blank-scene dead end, and the next ordinary action after investigation — go back — fails in continued play.

Observed:

- authored return exists and works with `"I'll return to Cinderwatch Gate."`
- `"I'll head back to Cinderwatch Gate."` / `"I'll head back to the gate."` can remain unresolved
- freeform narration then claims the gatehouse anyway

Secondary residue, do not start unless return evidence is weaker than expected:

- Live examine inventing inscriptions (local State ↔ Narration at the destination)
- Interactable glance/observe routing and the forced board/runner/road fork
- Bound-addressable vs topic-owner mismatch for `guard_captain` first-ask

Do not open a general State ↔ Narration campaign. Do not preselect a PR-AG identifier here beyond the slice above.

---

## 18. Git / Worktree State

The worktree was dirty before PR-AF and remains dirty.

PR-AF content:

- `data/scenes/old_milestone.json`
- `game/defaults.py`

PR-AF production / realization:

- `game/narration_state_consistency.py`
- `game/api.py` (late destination hook + ASCII engine print)

PR-AF tests / tools / report / handoff / artifacts:

- `tests/test_arrival_destination_realization.py` (new)
- `tools/run_praf_freeform_probe.py` (new)
- `data/validation/praf_arrival_destination/scenarios.json` (new)
- `PR-AF_arrival_destination_realization.md` (new)
- `docs/NEXT_SESSION.md` (updated)
- `artifacts/praf_arrival_destination/` (new)

Pre-existing dirt from earlier validation, policy, replay, PR-AC, PR-AD, PR-AE, and runtime session files was not erased or normalized. Campaign replay and the freeform probe reset local session/world playthrough residue.

No commit or push.

---

## 19. Confidence

**Medium-high** on the targeted failure class.

High that `old_milestone` was a content stub and is now a usable authored destination. High that ordinary look/examine/patrol-search no longer collapse into `"a blank scene awaiting definition"`. High that PR-AD and PR-AE contracts remain intact in deterministic tests and in the successful extended replay. Medium that every natural return phrasing will bind — the freeform probe and T12 already failed closed on `"head back"`. Medium-high that the next slice is destination return/onward travel, unless further play shows invented stone inscriptions or the captain first-ask are more blocking.

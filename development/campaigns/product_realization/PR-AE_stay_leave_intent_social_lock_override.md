# PR-AE — Gameplay: Stay/Leave Intent and Social-Lock Override

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Report location: repository root, matching the Product Realization report convention (`PR-AA`, `PR-AB`, `PR-AC`, `PR-AD`).

Replay artifacts: `artifacts/prae_stay_leave/`

---

## 1. Executive Summary

PR-AE repaired the highest-leverage remaining ordinary-play failure after PR-AD: a clear player decision to stay, leave, travel, or pursue an available authored path was being captured or inverted by an existing social engagement.

This is not a movement-system rewrite, a dialogue-system rewrite, a lead-system refactor, or a project-wide State ↔ Narration campaign. Existing owners remain authoritative: player intent (`game.intent_parser`), interaction routing (`game.interaction_routing` / `game.api`), social/interlocutor framing (`game.interaction_context`), authored exits/clues, and exploration scene transition.

Player-facing behavior is demonstrably improved on the targeted slice:

- After learning `notice_patrol_route`, `"Fine. I'll follow the missing patrol rumor along that northwest mud track."` now leaves `frontier_gate` for `old_milestone`.
- The bound Guard Captain no longer recaptures that turn as `social_probe`.
- Successful departure clears interlocutor state. The next turn is not immediately stolen back into gate dialogue.
- `"I'll stay at the gate a bit longer instead of entering Cinderwatch."` no longer enters `market_quarter`.
- Genuine patrol questions and ambiguous track nouns do not become travel.
- Unavailable destinations such as House Verevin are not invented.

PR-AD authored-knowledge realization remains intact. RC-10 and RC-21 remain settled.

The product is still not fully playable as an ordinary conversational AI-DM. After pursuit works, the player arrives at a stub `old_milestone` ("a blank scene awaiting definition"). That newly exposed arrival failure is now the dominant ordinary-play blocker in the replayed set.

---

## 2. Starting Failure

PR-AD made the notice/patrol fact reachable. The next player decision — act on it — still failed.

Representative path (PR-AD replay of R2-MT01 T7):

1. Player engages the gate, reads the notice, and learns the northwest-track / missing-patrol fact.
2. The Guard Captain is bound (`active_interaction_target_id=guard_captain`, social/engaged).
3. Player says: `"Fine. I'll follow the missing patrol rumor along that northwest mud track."`
4. Resolution kind: `social_probe`.
5. Scene remains `frontier_gate`. Exit `old_milestone` is unused.
6. Narration restates the rumor as if the player had asked another question.

Sibling failure (PR-AC R2-MT03 T7 / J17):

- `"I'll stay at the gate a bit longer instead of entering Cinderwatch."` became `scene_transition` into `market_quarter`.

---

## 3. R2-MT01 Execution Trace

Traced from the same multi-turn context used by PR-AD, without changing production behavior first.

| Step | Result before PR-AE |
| --- | --- |
| Raw player input | `Fine. I'll follow the missing patrol rumor along that northwest mud track.` |
| Parsed intent | Never reached exploration parse as a transition |
| Confidence / priority | Not represented as travel; dialogue-first won |
| Active interlocutor | `guard_captain`, social / engaged |
| Interaction-routing | `choose_interaction_route` stayed on the social/dialogue side because `I'll follow` was not `is_world_action` (`i follow` was required) |
| Canonical social entry | `should_route_social` stayed true; `_merged_indicates_travel_not_social` was false because parse did not return `scene_transition` |
| Dialogue-first | `_build_dialogue_first_action` emitted `social_probe` targeted at the captain |
| Lead / destination resolution | Authored exit `"Follow the missing patrol rumor" → old_milestone` existed and was unused. Qualified pursuit only matches `follow the lead to X`. Legacy follow matched only the tail after `follow`, which did not substring-match the exit label |
| Stay/leave interpretation | Not applied |
| Action selected | `social_probe` |
| Authoritative mutation | None. Scene stayed `frontier_gate` |
| Narration | Captain restated the northwest-track fact |
| Player-facing result | Player remained at the gate |

The actionable intent was lost at interaction routing / dialogue-first, after parse failed to classify the line as travel/pursuit.

---

## 4. Root Cause

**G. Multiple interacting causes.** The PR-AD hypothesis (social lock) was correct but incomplete.

| Cause | Role |
| --- | --- |
| B. Intent precedence | `parse_social_intent` / `_build_dialogue_first_action` ran before exploration unless the line was qualified `follow the lead to X` |
| C. Interaction routing | `I'll follow` / `I'm heading out` were not world-action; bound interlocutor kept the dialogue lane |
| D. Social / dialogue lock | Active captain converted the pursuit into `social_probe` |
| E. Destination resolution | Even if parse had run, `"I'll follow … rumor along that northwest mud track"` did not bind the authored exit because the follow-tail matcher did not see the full exit label in the sentence |
| Stay inversion | `try_embedded_named_place_scene_action` extracted `"entering Cinderwatch"` from a stay+contrast sentence. `_declared_travel_negation_blocks_match` already handled `instead of` only on segmented declared-travel |

No new state owner was required. Existing architecture can represent the behavior once clear stay/leave/pursuit is recognized and existing exits/clues are used.

---

## 5. Existing Context / Authority Owners

| Concern | Owner |
| --- | --- |
| Active interlocutor / social engagement | `game.interaction_context` (`interaction_state`) |
| Player intent | `game.intent_parser` |
| Lane selection / dialogue-first | `game.interaction_routing`, orchestrated by `game.api` |
| Current scene / location | `scene_state` via `game.api` / `game.storage` |
| Travel eligibility / scene transition | `game.exploration` using authored exits |
| Available authored path | `frontier_gate` exit `"Follow the missing patrol rumor"` → `old_milestone` |
| Pursuit / lead context | Lead registry + discoverable clue `notice_patrol_route` (compatibility `pending_leads` untouched) |
| Stay / leave | Now explicit parser lanes on the existing intent owner |
| Narration | Non-authoritative. Local PR-AE agreement only |

Social engagement is context. It is not movement authority. A clue identifies a pursuable path; it does not teleport. Narration describes the outcome.

---

## 6. Implementation

Smallest coherent repair on the existing owners:

### Intent (`game/intent_parser.py`)

- Semantic stay / leave / pursuit classifiers (commitment families, not a phrase whitelist).
- Stay / refused-travel is decided before embedded named-place extraction, so `"instead of entering Cinderwatch"` cannot invert into `market_quarter`.
- `I'll` / `I will` / discourse prefixes are stripped only for travel matching. Bare `"I follow <person>"` is left alone so NPC-follow tests and interact `follow_target` still work.
- Follow/pursue binds an existing exit when:
  1. the authored exit label appears in the player text; or
  2. the follow-tail matches an exit; or
  3. explicit pursuit language overlaps a unique authored clue and that clue shares tokens with a unique exit.
- `recover_actionable_stay_leave_or_pursuit` is the dialogue-first yield, analogous to PR-AD's interactable-question recover.
- Human-adjacent observe no longer steals a genuine information-seeking question.

### Routing (`game/interaction_routing.py`, `game/api.py`)

- World-action / forceful patterns include `I'll follow`, `I'm leaving`, `heading out`, `go after`.
- Dialogue-first yields to the stay/leave/pursuit recover after the interactable-question recover.
- Chat classification runs that recover before `parse_social_intent`, on the same seam as qualified pursuit.

### Social-lock release

- No new dialogue lifecycle.
- `scene_transition` / `travel` already break social continuity (`_resolution_explicitly_breaks_social_continuity` / `clear_for_scene_change`).
- Stay is `observe` with `parser_lane=explicit_stay`. It does not fabricate a scene change. Remaining in the scene does not require remaining locked; a later non-social turn can still escape through existing continuity-break owners.

### Narrow State ↔ Narration (`game/narration_state_consistency.py`)

Local to PR-AE stay/leave/pursuit turns, after authored-knowledge realization:

- Successful PR-AE departure whose narration does not describe the player leaving is replaced with the existing movement-agreement line.
- Stay narration that claims the player departed is corrected to remain.
- Failed/unavailable travel that claims arrival is corrected.

`game/exploration.py` copies `intent` onto non-transition resolution metadata so stay can be recognized.

---

## 7. Stay / Leave / Pursuit Semantics

| Shape | Behavior |
| --- | --- |
| Explicit pursuit | `"I'll follow the missing patrol rumor…"`, `"I'll follow the northwest track."`, `"I'm heading out after them along that northwest track."` → existing exit `old_milestone` when that path is authored/available |
| Explicit leave | `"I'm leaving."` / leave+road/pursuit language → travel or scene_transition; social yields |
| Explicit stay | `"I'll stay here."`, `"I'll remain at the gate."`, `"I'm not leaving yet."`, stay+`instead of entering` → no scene change |
| Conversational | `"What happened to the patrol?"`, `"When did they leave?"`, stay+question → remains social / not travel |
| Ambiguous | `"the northwest track"` / `"that northwest track"` → no forced movement |
| Invalid | `"I'll go to House Verevin."` → travel without invented destination |

---

## 8. Social-Lock Lifecycle

- Successful departure/pursuit: interlocutor cleared (`interaction_mode=none` on R2-MT01 T7). Next turn is not recaptured by the gate captain.
- Stay: no scene transition. Social context may remain or rebind; it must not become travel.
- Failed/unavailable travel: scene unchanged; narration must not claim arrival.

---

## 9. Authority Preservation

- No new knowledge store or destination store.
- Narration does not create a destination, lead, or NPC.
- Social context is not movement authority.
- Lead/clue text does not itself mutate location; exploration still performs the transition through the authored exit.
- RC-10 / RC-21 / PR-AD realization architecture were not reopened.
- `pending_leads` was not migrated.
- Protected-replay / mutation-attribution baselines were not refreshed.

---

## 10. Tests Added or Updated

Added: `tests/test_stay_leave_social_lock_override.py`

- T7 pursuit parses to `old_milestone`.
- Northwest-track and heading-out phrasing bind the authored exit.
- Stay / not-leaving do not enter Cinderwatch.
- Conversational and stay+question lines do not become travel.
- Ambiguous track nouns do not force movement.
- House Verevin is not invented.
- Stone Boar + `follows the instructions` still prefers the named place.
- Routing: `I'll follow` is world-action; patrol questions stay dialogue.
- Narration agreement for pursuit-without-movement and stay-inverted-into-departure.
- HTTP: pursuit while engaged, explicit leave, explicit stay, conversational control, ambiguous control, invalid travel, post-departure follow-up.
- `"I follow the tattered man."` is not stolen as unresolved travel.

Updated: `tests/test_dialogue_routing_lock.py`

- `I'll follow` is world-action / action lane.

Existing tests were not weakened. Follow-person gauntlet / scene-entity-lock contracts remain green after the commitment-prefix was narrowed so bare `I follow <person>` is not rewritten into travel.

---

## 11. R2-MT01 Before / After

Same fixture: `data/validation/semantic_playability_calibration_r2/scenarios.json`. Original scenario was not rewritten.

After: `artifacts/prae_stay_leave/prac_replay/runs/20260920T004708Z_R2-MT01/transcript.md`

| Turn | Player | Before (PR-AD) | After (PR-AE) | Human |
| --- | --- | --- | --- | --- |
| T2 | I read the notice board | Authored patrol fact; clue written | Same | Pass — PR-AD preserved |
| T4 | What's being done about the missing patrol? | Captain bound; can speak the fact | Captain `"I don't know."` on this run | Residual bound-addressable first-ask |
| T5 | I don't want to rush… Who last spoke…? | Social question at the gate | Still social at the gate; not travel | Pass for stay/leave |
| T6 | Is that still the official last position? | Social; authored fact | Social; authored fact | Pass — conversation protected |
| T7 | I'll follow the missing patrol rumor… | `social_probe`; stay at `frontier_gate` | `scene_transition`; `frontier_gate` → `old_milestone`; social cleared | Pass |
| T8 | After I start that way… | Still at gate, still captain-locked | Stays at `old_milestone`; `investigate`; no captain recapture | Pass for lock release; arrival content is a stub |

R2-MT03 T7 (`artifacts/prae_stay_leave/prac_replay/runs/20260920T004708Z_R2-MT03/transcript.md`): stay remains `frontier_gate` / `observe`. Previously entered `market_quarter`.

Automated `semantic_result=FAIL` on T7 is evaluator residue: the stock movement line does not share enough player tokens. Authoritative state and lock release are the product result.

---

## 12. Freeform Play Probe

Diagnostic only. Natural phrasing, not copied from tests.

Artifact: `artifacts/prae_stay_leave/freeform_probe/20260920T005001Z_probe.md`

| Turn | Player | Result |
| --- | --- | --- |
| 1 | walk up and ask what's posted | Notice/patrol fact spoken; social with the guard |
| 2 | stay here and ask when the patrol went missing | Stayed at the gate (no travel). First run lost the question to observe; later HA+question guard added |
| 3 | heading out after them along that northwest track | First run missed this phrasing (`heading out after` ≠ `follow`). Classifier expanded; unit test now binds `old_milestone` |
| 4 | now that I've left, look at the road | Activity mode; interlocutor cleared. Scene had not moved on that first run because T3 was still captured |

The probe did what it is supposed to do: it found a natural phrasing hole, which was then closed without turning PR-AE into a phrase whitelist. R2-MT01 remains the primary replay proof.

---

## 13. Validation Results

| Gate | Result |
| --- | --- |
| New PR-AE tests | Pass (`tests/test_stay_leave_social_lock_override.py`) |
| Intent parser | Pass |
| Interaction routing / dialogue lock | Pass |
| Social / interlocutor / continuity escape | Pass |
| Scene transition / destination binding / follow-person lock | Pass |
| Qualified pursuit / lead-lifecycle dialogue-lock | Pass |
| State authority | Pass |
| PR-AD authored-knowledge tests | Pass |
| Human-adjacent (after question guard) | Pass |
| Round #1 calibration corpus | 13/13 (`artifacts/prae_stay_leave/round1_calibration/`) |
| R2-MT01 / R2-MT03 replay | Material improvement on stay/leave/pursuit; see §11 |
| Full authoritative suite | Not re-run as a complete 6,450-test pass. Focused gameplay/authority files above are green. Protected-replay / mutation-attribution reds from PR-AD were not refreshed |

Structural PASS is not semantic playability. T7 evaluator FAIL on a correct transition is supporting evidence only.

---

## 14. Remaining Semantic Failures

- Bound `guard_captain` can still answer the first watch-command / "what's being done" ask with `"I don't know"` (R2-MT01 T4 on this replay).
- Glance/observe can still force `"Board, runner, or road"` (R2-MT03 T1).
- After a successful pursuit, `old_milestone` narrates as `"a blank scene awaiting definition"`. This is newly dominant because the player can now arrive.
- T7 movement narration is a stock position-change line, not a diegetic track description. State is correct; prose is thin.
- Some authored lines still use the `mutters` / `"Word is,"` envelope.
- `narration_ctx_…` lead ingestion from prose still occurs (R2-MT03).
- Evaluator false negatives on terse movement / authored answers.

---

## 15. Deferred Findings

Unchanged unless noted:

- `compat_pending_lead_needed` still keys off a scene target only.
- Intent parsing still reads `pending_leads` as the pursuit surface.
- Broader lead/clue overlap reduction.
- House Verevin / rooftop invention (invalid-travel path now fails closed for the explicit go-to case).
- Forced `"Board, runner, or road"` fork.
- Scene-transition Unicode / operator-encoding.
- PR-AB tooling / product-integrity.
- General prompt rewrite or NPC dialogue redesign.
- Project-wide State ↔ Narration campaign.
- Protected-replay baseline refresh.

---

## 16. Recommended Next Product Slice

**Arrival / destination realization after successful pursuit** — specifically the now-reachable `old_milestone` path.

Not chosen from roadmap neatness. Chosen because PR-AE closed the social-lock that prevented departure, and the next ordinary-play action — look around after leaving — hits a stub scene.

Secondary residue, do not start unless arrival evidence is weaker than expected:

- Interactable glance/observe routing and the forced board/runner/road fork.
- Bound-addressable vs topic-owner mismatch for `guard_captain` first-ask.

Do not open a general State ↔ Narration campaign. Do not preselect a PR-AF identifier here beyond the slice above.

---

## 17. Git / Worktree State

The worktree was dirty before PR-AE and remains dirty.

PR-AE production files:

- `game/intent_parser.py`
- `game/interaction_routing.py`
- `game/api.py`
- `game/narration_state_consistency.py`
- `game/exploration.py`

PR-AE tests / tools / report / handoff / artifacts:

- `tests/test_stay_leave_social_lock_override.py` (new)
- `tests/test_dialogue_routing_lock.py` (updated)
- `tools/run_prae_freeform_probe.py` (new)
- `PR-AE_stay_leave_intent_social_lock_override.md` (new)
- `docs/NEXT_SESSION.md` (updated)
- `artifacts/prae_stay_leave/` (new)

Pre-existing dirt from earlier validation, policy, replay, PR-AC, PR-AD, and runtime session files was not erased or normalized. Campaign replay and the freeform probe reset local session/world playthrough residue.

No commit or push.

---

## 18. Confidence

**Medium-high** on the targeted failure class.

High that R2-MT01 T7 now performs an authoritative scene transition and releases the social lock. High that explicit stay no longer enters Cinderwatch. High that conversational questions and ambiguous nouns remain protected in deterministic tests. Medium that every natural leave/pursuit phrasing will bind without another classifier expansion — the freeform probe already forced one heading-out addition. High that authority boundaries were preserved. Medium-high that the next slice is arrival realization at the now-reachable destination, unless further play shows the blank scene is less blocking than the captain first-ask or the forced fork.

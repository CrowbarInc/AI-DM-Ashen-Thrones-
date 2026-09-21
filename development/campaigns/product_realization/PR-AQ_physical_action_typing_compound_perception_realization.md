# PR-AQ — Gameplay / AI Experience: Physical Action Typing and Compound Perception Realization

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Replay artifacts: `artifacts/praq_physical_action/`

---

## 1. Executive Summary

PR-AQ repaired the highest-leverage ordinary-play failure after PR-AP: a natural local walk-and-listen turn lost all action type and fell into unparsed GPT narration.

The recovered contract is:

```text
ORDINARY PHYSICAL LANGUAGE
    → EXISTING ACTION OWNERSHIP

LOCAL MOVEMENT
    ≠
SCENE TRAVEL

LISTENING
    → PERCEPTION ATTEMPT
    ≠
SOUND CREATION

COMPATIBLE WALK + LISTEN
    → ONE EXISTING OBSERVE / LISTEN ACTION
    NOT
    A UNIVERSAL SPLIT-AND-EXECUTE PLANNER
```

T16 `"I walk a few steps along the muddy gate line and listen"` now parses as `observe` with `human_adjacent_intent_family=approach_listen`. Isolated local walking uses the existing `custom` kind. Isolated `"I listen."` already used observe and still does. Scene travel remains travel. Unresolved travel is not reinterpreted as local walking.

No new action taxonomy, movement owner, perception owner, compound planner, coordinate system, or canonical Frontier Gate sound was added.

---

## 2. Starting Failure

PR-AP extended replay T16:

> Player: I walk a few steps along the muddy gate line and listen
> GM: You step quietly along the muddy gate line… fleeting whispers about the missing…
> `resolution.kind`: `None`
> Scene: `frontier_gate` → `frontier_gate`

The evaluator passed. Routing was untyped. The sentence was cut off. Live-model text also invented rain, murmurs, and whispered rumors.

---

## 3. Exact T16 Reproduction

Reproduced before production changes with `artifacts/praq_physical_action/repro_before.py`.

| Item | Before |
| --- | --- |
| Raw input | `I walk a few steps along the muddy gate line and listen` |
| Normalized | same strip |
| HA family | `none` |
| Travel prefix | none (`I walk` is not a leading `walk ` prefix) |
| Extracted dest | none |
| Authored exit | none |
| `parse_freeform_to_action` | `None` |
| `parse_intent` fallback | `None` |
| `is_world_action` | `false` |
| Final kind | `None` via `_build_gpt_narration_from_authoritative_state(..., resolution=None)` |

Isolated `"I listen."` already parsed as `observe` / `human_adjacent_observe`. Isolated local walking parsed as `None`. Combined walk+listen parsed as `None`.

---

## 4. T16 End-to-End Trace

| Stage | Before | After |
| --- | --- | --- |
| Previous state | T15 investigate of gate line; social already cleared | same |
| Raw input | walk a few steps along the muddy gate line and listen | unchanged |
| Normalization | strip only | unchanged |
| Clause/intent | no recognized action | listen + local motion |
| Walk recognized | no | contextual local motion |
| Listen recognized | no (`and listen` ≠ `(i\|we) listen`) | yes |
| Target | muddy gate line not extracted as dest | no travel dest |
| Target authority | n/a | scene-local; no exit bind |
| Destination extraction | none | none |
| Exit binding | none | none |
| Scene travel considered | prefix path missed `I walk` | skipped because no dest/exit intent |
| Local movement concept | not represented | `custom` / `local_physical_movement` |
| Listen concept | existing HA observe, missed trailing listen | HA `approach_listen` |
| Candidate kinds | none | `observe` (listen) over `custom` (walk) |
| Arbitration | fall through to unparsed GPT | one observe action; no split-execute |
| Final kind | `None` | `observe` |
| Action result | no exploration resolution | typed observe + HA metadata |
| State mutation | scene unchanged; investigate frame lingered | scene unchanged; observe activity |
| Narration | live GPT, truncated `missing…` | typed observe, complete utterance |
| Truncation point | unparsed GPT emission | none on T16 after repair |

---

## 5. Failure Classification

**CLASS H — multiple sibling defects**, earliest causal defect **CLASS A**.

- **CLASS A (earliest):** ordinary local walking is unrecognized. Isolated `"I walk a few steps along the muddy gate line."` returned `None`.
- **Narrow CLASS B:** trailing `"and listen"` was unrecognized. Primitive `"I listen."` already worked.
- **Not CLASS C as primary:** the combination did not uniquely destroy a working type. Both the walk clause and the trailing listen clause failed independently.
- **Not CLASS D:** the engine did not attempt dest/exit travel on T16. `"walk "` only matched as a leading prefix after stripping `I'll`, not `I walk`.
- **Not CLASS E:** listen did not override a valid walk type; listen never fired.
- **Not CLASS F:** no typed result existed to lose downstream.
- **Not CLASS G:** `kind=None` is valid only as the unparsed-GPT fallback, not as a supported physical-action class.

Truncation is a **causal sibling of the untyped path**, not an independent first defect: `kind=None` sent the turn through unparsed GPT, which then emitted a mid-sentence ellipsis. Later T13 in the after-replay shows truncation can also happen on already-typed `already_searched` turns, so truncation is not exclusive to `kind=None`.

---

## 6. First Incorrect Action / Realization Decision

```text
parse_freeform_to_action
    → HA listen requires "(i|we) listen" / "listen in" / eavesdrop
    → "and listen" is missed
    → travel prefixes require a leading "walk " after I'll-stripping
    → "I walk a few steps along …" is missed
    → no observe / investigate / interact match
    → return None
    → API chat_procedural_unparsed_freeform
    → resolution.kind = None
```

That is the first incorrect decision. Narration truncation happens later on that untyped path.

---

## 7. Existing Action-Kind Contract

`game.exploration.EXPLORATION_KINDS`:

`scene_transition`, `travel`, `observe`, `investigate`, `interact`, `custom`, `discover_clue`, `already_searched`

Kinds originate in the parser (`type`) and are copied onto `ExplorationEngineResult.kind`. They are mixed: routing, resolution, and realization all branch on them. `custom` is the existing generic physical-action kind. Observation/perception already owns `observe`. Movement/travel already owns `travel` / `scene_transition`. `None` is the unparsed GPT fallback, not a supported physical class.

T16 fits existing `observe` (listen) with local motion as context. Isolated local walking fits existing `custom`.

---

## 8. `kind=None` Audit

`None` is expected when `parse_freeform_to_action` and recover lanes all return `None`. Final realization does not require a kind; it calls `_build_gpt_narration_from_authoritative_state` with `resolution=None`. Perception grounding does not apply (`PERCEPTION_KINDS` excludes empty kind). T16 was missing a kind because classification failed. Assigning a generic kind globally would conceal that failure. PR-AQ assigns the recovered existing kind, not a blanket `None → generic_action` rewrite.

---

## 9. Primitive Walk Audit

`"I walk a few steps along the wall."`

Before: `None`. After: `custom`, `parser_lane=local_physical_movement`, no scene transition, no invented dest.

---

## 10. Primitive Listen Audit

`"I listen."` / `"I listen by the gate line."`

Before and after: `observe`, `human_adjacent_observe`, family `listen`. Existing contract held. Trailing `"and listen"` is what failed.

---

## 11. Local Movement vs Scene Travel

| Wording | Owner |
| --- | --- |
| walk/step/pace a few steps, along, beside, closer | local `custom` |
| walk to / toward / through / into | `travel` or `scene_transition` |
| head for / leave through / I'm leaving | existing travel |
| unique authored exit / embedded named place | existing PR-AG bind |
| unresolved dest | `travel`, fail closed |

Hard boundary: local physical movement must not cause a scene transition without authoritative exit/destination intent. Unresolved travel must not become harmless local walking.

---

## 12. Existing Perception / Listen Contract

Listen already mapped to generic observation through `classify_human_adjacent_intent_family` and parser lane `0c`. Outcome **A**: listen already maps to generic observation; T16 failed to reach it because trailing `listen` was unrecognized and travel/local walk also failed.

No dedicated five-senses system. Empty listen already had `diegetic_listen_null_line`. Authored audible facts can now surface through existing intent-aligned visible-fact scoring when HA focus is `none`.

---

## 13. Existing Compound-Action Handling

The engine does not split `and` into N executed actions. Existing compatible shapes:

- `move closer … and listen in` → one `observe` / `approach_listen`
- `step closer and read` → investigate via `read`
- `thank … and look toward` → targeted investigate (PR-AO)

T16 is recovered as **one observe action with listen/approach_listen semantics**, not two executed turns.

---

## 14. Root Cause

Classification never assigned an action type. Local walking had no existing-lane representation. Trailing listen did not match the HA `(i|we) listen` pattern. The API therefore used the unparsed GPT path (`kind=None`). Truncation and invented sound were consequences of that path, not the first defect.

---

## 15. Recovered Physical-Action Contract

Local in-scene walking, pacing, and stepping closer use the existing `custom` kind with `parser_lane=local_physical_movement`. They do not bind exits, invent destinations, or change scenes.

---

## 16. Recovered Listen / Auditory-Perception Contract

Auditory perception, including trailing `and listen`, uses the existing HA observe lane. Vocative `Listen,` / `listen to me` remains discourse, not perception. Perception may reveal authored audible/visible facts. It may not author sound, NPCs, clues, or events.

---

## 17. Compound-Compatible Action Contract

If listen/look/examine is present without travel dest intent, the existing perception/inspect owner wins. Local walk is context. Travel dest + second clause does not split-execute; travel remains authoritative. No universal conjunction planner.

---

## 18. Implementation

Generic production only:

- `game/human_adjacent_focus.py` — trailing/bare listen perception; vocative exclusion; walk+listen → `approach_listen`
- `game/intent_parser.py` — local-movement lane; travel-dest guard; `I walk toward` / `I head for` emit existing `travel`; recover world-action for listen/local movement
- `game/interaction_routing.py` — narrow world-action patterns for local walk/listen (not `I walk over and ask`)
- `game/social_continuity_routing.py` — same wording breaks stale social commitment
- `game/diegetic_fallback_narration.py` — empty listen still null; authored hear/sound/drip facts may surface

No canonical `data/scenes/*.json` or `data/world.json` content was added.

---

## 19. Local Movement Behavior

`"I walk a few steps along the wall."` / `"I pace beside the wall."` → `custom`, scene unchanged.

---

## 20. Explicit Travel Behavior

`"I leave through the eastern arch."` binds the unique authored exit. `"I walk to the market."` still uses embedded named-place travel. PR-AE / PR-AG remain intact.

---

## 21. Unresolved Travel Behavior

`"I head for the silver road."` / `"I walk toward the northern road."` → `travel`, no dest bind, no local-walk conversion. Probe: `"That destination is not available from here."`

---

## 22. Authored Audible Evidence

Synthetic fact: `"Water can be heard dripping behind the stone wall."` Player: `"I listen."` PASS: water/drip may be surfaced; no extra bells/guards invented.

---

## 23. Empty Listening / Grounded Absence

Scene with no authored audible/human-speech fact. `"I listen."` remains typed observe. Fallback is existing diegetic quiet/overlap, not fabricated events or NPCs.

---

## 24. Compound Walk + Listen

`"I walk along the wall and listen."` → `observe` / `approach_listen`. No `kind=None`. No scene transition. No unsupported second action.

---

## 25. Ambiguous / Unsafe Compound Cases

| Input | Result |
| --- | --- |
| leave through the arch and inspect the desk | travel; not investigate |
| stay here and head to the village | existing `explicit_stay` observe; stayed on scene |
| talk to the guard and walk away | not local-movement lane |

PR-AQ does not split every `and`.

---

## 26. State-Mutation Audit

T16 / synthetic walk+listen do not create scenes, exits, destinations, clues, leads, NPCs, patrol state, or conversation binding. Legitimate bookkeeping (turn history, activity mode) remains. Lead registry after T16 still only `notice_patrol_route` and `milestone_mud_prints`.

---

## 27. Truncated-Narration Root Cause

T16 truncation was caused by the untyped GPT path, not by a kind-string strip or a T16-specific template. After typing, T16 is complete. Sibling: later T13 `already_searched` in the after-replay still ended `with…`. Truncation can happen without `kind=None`. PR-AQ did not pad T16 and did not add a general truncation rewriter.

---

## 28. Player-Facing Realization

Typed physical/perception turns emit complete utterances, do not expose `kind=None`, do not claim scene travel when none occurred, and do not mint evidence. Live GPT can still invent whispers on observe; that is documented residue, not the T16 typing defect.

---

## 29. Social-Context Regression

After binding an NPC, `"I walk a few steps and listen."` is a world action, recovers as observe, and is not dialogue-first. Explicit re-address (`I turn back to the tavern runner…`) recovers conversation. PR-AM remains intact. `"I step over to the tavern runner and ask…"` is still social, not local walk.

---

## 30. Movement Regression

Stay / leave / pursuit / unique exit / natural dest / unresolved dest / local walking were retested. Local walking does not steal travel. Travel does not collapse into local movement. PR-AE and PR-AG tests passed.

---

## 31. Perception Regression

PR-AH / PR-AK / PR-AO owner tests passed. Observation, inspectability, and investigation-result authority were not reopened. Listening does not create sound in the structured state.

---

## 32. Frontier Gate T16 Before / After

| | Before (PR-AP `20260920T203314Z`) | After (`20260920T211426Z_R2-MT01-AQ`) |
| --- | --- | --- |
| Raw | walk a few steps along the muddy gate line and listen | same |
| Kind | `None` | `observe` |
| Scene | `frontier_gate` → `frontier_gate` | same |
| Leads | two existing rumors | same two; no mint |
| Narration | truncated `missing…` | complete 114-word observe |
| Sound invented in live GPT | yes | still some invented whispers (live-model residue) |
| Truncation | yes | no |

T17 `"I look toward the notice board again."` → `already_searched`, play continues.

---

## 33. Scenario-Independent Generalization Fixtures

`tests/test_physical_action_typing_compound_perception_realization.py` uses slate-cistern / lantern-cut vocabulary.

| Test | Result |
| --- | --- |
| 1 simple local walk | PASS `custom` |
| 2 simple listen | PASS `observe` |
| 3 walk + listen | PASS `observe`, no travel |
| 4 local approach | PASS `custom`, no transition |
| 5 explicit exit | PASS travel/transition to `lantern_cut` |
| 6 unresolved travel | PASS `travel`, not local walk |
| 7 authored audible | PASS water/drip may surface |
| 8 empty listen | PASS grounded absence |
| 9 walk + empty listen | PASS observe, no travel |
| 10 walk + authored listen | PASS HTTP observe, scene stays |
| 11 move + look | PASS observe |
| 12 move + inspect | PASS investigate `basin_statue` |
| 13 social → walk/listen | PASS not dialogue |
| 14 walk/listen → social return | PASS warden rebound |
| 15 ambiguous compound | PASS travel, not split |
| 16 repeated listen | PASS no accumulating invention in fallback |
| 17 repeated local walk | PASS no scene drift |
| 18 complete realization | PASS no `kind=None` in facing text |

---

## 34. Anti-Overfitting Audit

Searched changed generic files `intent_parser.py`, `human_adjacent_focus.py`, `interaction_routing.py`, `social_continuity_routing.py` for `frontier_gate`, `muddy_gate_line`, `gate_line`, `tavern_runner`, `notice_board`, `missing_patrol`, `patrol`, `Cinderwatch`, `Captain Thoran`, `guard_captain`, `old_milestone`, `stew`. None introduced.

No exact T16 string match. No `walk ... and listen` special case. No gate-line movement owner. Not every `walk` is local (`walk toward` / `walk to` remain travel). Not every `listen` is observe (`Listen,` vocative excluded). No fabricated sound on listen. No global `None` rewrite. No split-every-`and`. No T16 narration pad. No coordinates. No canonical Frontier Gate sound added.

`game/diegetic_fallback_narration.py` already contained stew/gate stock in older observe options. PR-AQ only added generic hear/sound/drip tokens and allowed authored listen-aligned facts to beat HA-null silence.

---

## 35. Tests Added or Updated

Added: `tests/test_physical_action_typing_compound_perception_realization.py`.

No existing owner expectations were weakened.

---

## 36. Continued Multi-Turn Replay

`artifacts/praq_physical_action/extended_replay/runs/20260920T211426Z_R2-MT01-AQ/transcript.md`

Chain through learn / pursue / travel / arrive / observe / investigate / return / grounded observe / captain first-ask / roster / stew / glance / last-checker / T15 / T16 / T17.

T12/T14 refusals remain grammatical. T15 remains grounded investigate. T16 is typed observe. T17 continues.

---

## 37. Freeform Physical-Action Probe

`artifacts/praq_physical_action/freeform_probe/20260920T211639Z_probe.md`

Pace → `custom`. Listen → `observe`. Walk+listen → `observe`. Walk toward / head for / leave through missing door → `travel` fail-closed. Social stew remains PR-AP grammar. Walk/listen after social clears the runner. Explicit re-address recovers the runner. Stay+head-to-village stays via PR-AE stay, does not split-execute.

---

## 38. Validation Results

| Suite | Result |
| --- | --- |
| New PR-AQ fixtures | passed (`--basetemp=artifacts/praq_pytest_tmp`) |
| Intent parser / HA | passed |
| Stay/leave, dest/exit | passed |
| PR-AO / PR-AH / PR-AK | passed |
| PR-AD through PR-AP focused | passed (`artifacts/praq_pytest_reg2`) |
| Exploration / clue / local observe / calibration corpus | passed |
| Round #1 semantic calibration | 13/13 |
| Extended R2-MT01-AQ | completed; T16 typed |
| Freeform probe | completed |
| Full authoritative suite | not re-run (same doctrine as PR-AP) |

Windows `PermissionError` on shared `codex_pytest_tmp` remains environmental.

---

## 39. Remaining Semantic / Playability Failures

- Live GPT on typed listen/observe can still invent whispers, complaints, or spoken rumors. T16 after-repair did this. Structured state did not mint them.
- Observe fallback stock can still append the two-fact gate pair (`As you watch the scene…`).
- T13 `already_searched` can still truncate (`with…`).
- T9 captain first-ask can still use `mutters` / `"Word is,"` and awkward grammar (`seriously,.`).
- Untargeted look-around still repeats the same two-fact stock.
- Residual paraphrase / Gate Serjeant / geography-bleed items remain as previously deferred.

---

## 40. Deferred Findings

All previously deferred residue remains deferred unless later evidence elevates it. PR-AQ did not start pricing, compound-intent planning, sensory simulation, or a project-wide State ↔ Narration campaign.

---

## 41. Recommended Next Product Slice

Chosen from continued ordinary play after repaired T16:

**Invented audible / spoken detail on an already-typed listen or observe turn.**

T16 is now a coherent observe. The next ordinary-play quality failure on that path is live-model invention of whispers and complaints. That is a sibling of PR-AH perception non-invention, not a missing action type. Do not start a project-wide State ↔ Narration campaign unless later evidence outranks this narrow auditory-invention residue. T13 already_searched truncation and observe-stock stacking are siblings, not the first T16 typing defect.

Do not start pricing. Do not reopen PR-AP grammar, PR-AO provenance, PR-AE/AG movement, or PR-AM lock without new causal evidence.

---

## 42. Git / Worktree State

The worktree remains dirty from PR-AC through PR-AP plus PR-AQ.

PR-AQ generic engine: `game/intent_parser.py`, `game/human_adjacent_focus.py`, `game/interaction_routing.py`, `game/social_continuity_routing.py`, `game/diegetic_fallback_narration.py`.

PR-AQ tests/tools/docs/artifacts: `tests/test_physical_action_typing_compound_perception_realization.py`, `tools/run_praq_freeform_probe.py`, `data/validation/praq_physical_action_typing/`, `artifacts/praq_physical_action/`, this report, `docs/NEXT_SESSION.md`.

No canonical scene/world sound or event was added. Replay/probe reset local runtime documents (`data/session.json`, `data/world.json`, `data/combat.json`, `data/session_log.jsonl`).

---

## 43. Confidence

**High** that T16 is typed through existing observe/listen ownership and that isolated local walking uses existing `custom`.

**High** that local movement and scene travel remain distinct, and that no split-and-execute planner was introduced.

**Medium-high** that empty listen stays grounded in structured state and synthetic fixtures.

**Medium** that every live listen will avoid invented whispers — perception grounding still targets confrontation/inscription more than ambient speech.

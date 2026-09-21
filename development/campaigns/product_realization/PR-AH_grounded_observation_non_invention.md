# PR-AH — Gameplay / AI Experience: Grounded Observation and Non-Invention

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Replay artifacts: `artifacts/prah_grounded_observation/`

---

## 1. Executive Summary

PR-AH repaired the highest-leverage ordinary-play failure after PR-AG: ordinary observation could invent an unsolicited NPC confrontation.

The representative post-return `"I look around."` at `frontier_gate` was **not** a free-form model hallucination. The exact whispered-hook and guard-accost lines were engine-authored stock in passive-scene-pressure fallback / policy escalation. The model was also prompted to invent approach-and-speech beats.

The inscription sibling shares the same **boundary** — perception realization lacked a fail-closed evidence surface — but not the same first-appearance owner. Confrontation was injected by pressure/policy. Inscription was model elaboration on examine. Both are now rejected by a general perception-grounding helper and fail closed through existing diegetic observe / discovered-clue realization.

No new world-authority owner. No new scene schema. No Cinderwatch special cases in generic production code. Canonical scene content was not modified.

Invariant now enforced on perception turns:

```text
authoritative world → determines what exists and what may be learned
AI-DM → realizes that material
narration → cannot promote unsupported world-significant claims
```

---

## 2. Starting Failure

PR-AG made natural return authoritative. The next ordinary act invented the world.

PR-AG extended replay T13 (`I look around the gate district again.`):

> threadbare watchers and ragged strangers remain clustered along the gate ... cuts through the crowd and stops at your shoulder. "You're asking the wrong questions out loud," they murmur. "Walk with me if you want the next name."

Interlocutor stayed unbound. No new world NPC. Scene stayed `frontier_gate`.

PR-AG freeform probe T8 (`I look around.`):

> A guard peels away from the notice board and squares up to you. "Standing still won't help that patrol," ...

Known sibling: live examine of the milestone invented faded inscriptions absent from `old_milestone` scene data.

---

## 3. Post-Return Observe Execution Trace

Traced before production changes.

| Stage | Result |
| --- | --- |
| Raw input | `I look around.` / `I look around the gate district again.` |
| Parsed intent | `observe` via `OBSERVE_PATTERNS` |
| Resolution kind | `observe` |
| Scene | `frontier_gate` |
| Authoritative visible facts | notice board, gate serjeant, tavern runner, threadbare watchers/refugees, census choke |
| Authoritative NPCs | `gate_guard`, `gate_serjeant`, `tavern_runner`; addressables include `guard_captain`, `refugee`, `threadbare_watcher` |
| Interlocutor | none after return |
| Discoverable clue | `notice_patrol_route` already known; hidden facts remain hidden |
| Prompt | observe instructions plus, when pressure due, "someone approaches, an NPC speaks first" |
| Model output | often grounded visible-fact prose |
| Pressure due-check | true at the gate (`guard` / `watch` / `missing patrol` / `rumor` in visible facts, or recent contextual leads) |
| Upstream satisfier | appended the lead-figure stock beat when the observe text lacked "concrete interaction" |
| Sealed/policy fallback | full replacement with the guard-rumor or "Board, runner, or road" stock line |
| Final text | grounded start + invented confrontation, or entire invented accost |
| State mutation | no interlocutor bind; no new NPC; `remember_recent_contextual_leads` could store figures from the invented prose **before** finalize |

Exact T13 / T8 strings are hardcoded in:

- `game/final_emission_passive_scene_pressure.py` (pre-repair)
- `game/response_policy_enforcement.py` `_render_passive_pressure_beat` (pre-repair)

Origin: **C + B + G**. Fallback/catalog injection first authored the confrontation. Prompt contamination asked the model to do the same. Recent-lead re-ingestion could feed the next injection. "The AI hallucinated" is not the diagnosis.

---

## 4. Invented-Inscription Sibling Trace

`data/scenes/old_milestone.json` authors a weathered stone, mud prints, and clue `milestone_mud_prints`. It does not author an inscription.

PR-AF freeform examine produced faded inscriptions / distance numbers. That path is `investigate` / `discover_clue` through exploration + live narration. It does **not** use passive-scene-pressure stock.

Shared defect: perception realization had no fail-closed check for world-significant physical claims against the current evidence surface.

Separate first owner: model generation on examine, not pressure injection.

PR-AH repairs the shared boundary without forcing both defects into the pressure module.

---

## 5. Root Cause

**G. Interaction of owners, with a confirmed engine injector.**

| Cause | Role |
| --- | --- |
| C. Fallback / catalog | Passive scene pressure required a "concrete interaction beat" on observe and supplied invented confrontation stock. |
| B. Prompt contamination | `gm.py` told the model to advance a pause by inventing approach, NPC speech, or an active clue. |
| A. Model generation | Could invent confrontation or inscriptions when not stopped. |
| E. Re-ingestion | `remember_recent_contextual_leads` ran on pre-finalize prose and could make invented figures look like later scene evidence. |

Existing `narrative_authority` checks invented outcomes / hidden causes / intent, not unsolicited observe events. Visibility checks entities/facts, not whether a present guard may accost the player.

---

## 6. Existing Perception Authority Contracts

Recovered; no new persistence domain.

| Concern | Owner |
| --- | --- |
| Scene identity | `scene_state` / authored `data/scenes/*.json` |
| Visible facts | `scene.visible_facts` (+ opening/journal seeds as presentation) |
| Hidden facts | `scene.hidden_facts` until reveal |
| Interactables | scene interactables; investigate/clue reveal |
| NPC/entity presence | world NPCs + scene addressables + interaction presence |
| Clues | `discoverable_clues` + `process_investigation_discovery` / clue knowledge |
| Interlocutor | `game.interaction_context` |
| Narration | GM + final emission; derived `player_visible_state` |
| Observe fallback | `render_observe_perception_fallback_line` |
| Visibility contract | `game.narration_visibility` |

Perception classes used by PR-AH:

| Class | Meaning |
| --- | --- |
| A. Present and visible | Visible facts, present NPCs, exit labels, interactable labels |
| B. Present but requires investigation | Discoverable clues / interactable reveals |
| C. Hidden / undiscovered | Hidden facts and unrevealed clues |
| D. Absent | Not in the evidence surface |
| E. Presentation-only | Wording that does not add a world-significant fact |

Ordinary observe may realize A and E. Investigate/examine may realize B when discovery rules fire. C and D must not appear as established world facts.

---

## 7. Non-Invention Boundary

Implemented in `game/perception_grounding.py` as a realization/validation helper.

For perception kinds (`observe`, `investigate`, `discover_clue`, `interact`):

- no player-targeted accost / quoted player-address without a bound interlocutor or social/event kind;
- no physical-evidence category (inscription, blood, corpse, secret passage, hidden symbol, dropped weapon, footprints) unless that category is already in the evidence surface;
- no distinctive hidden-fact or undiscovered-clue spans;
- present NPCs and authorized evidence remain expressible;
- adjectives and non-identical wording of grounded facts are allowed;
- social/combat kinds are not rewritten by this helper.

This is category grounding, not a banned-word list and not a whisper/inscription special case.

---

## 8. Implementation

### Generic engine

- `game/perception_grounding.py` — evidence surface, invention classify, grounded fallback, late apply hook, lead resync after repair.
- `game/final_emission_passive_scene_pressure.py` — candidates and satisfier now realize visible facts; they no longer append invented confrontation.
- `game/final_emission_non_strict_stack.py` — grounded observe no longer fails as `passive_scene_pressure_missing_concrete_beat`.
- `game/response_policy_enforcement.py` — `_render_passive_pressure_beat` uses the same grounded line.
- `game/gm.py` — pressure prompt no longer asks the model to invent approach/speech/clues.
- `game/api.py` — late hook after PR-AD/AE/AF realization on all three player-facing pipelines.

### Canonical content

None.

### Synthetic / test-only

`slate_cistern`, `lantern_wharf`, `copper_orchard` in `tests/test_grounded_observation_non_invention.py` only.

Prompt construction changed only for the passive-pressure instruction payload. Post-generation validation changed (new helper + late hook). Fallback realization changed (pressure/policy now call existing observe fallback). Narration-state consistency module was not broadened. Narrative-context ingestion was changed only when invention is rejected: recent contextual leads are rebuilt from the grounded replacement.

---

## 9. Fail-Closed Grounded Realization

Rejected narration is replaced with:

- the just-discovered clue text, when investigate/discover_clue has one;
- otherwise `render_observe_perception_fallback_line` from visible facts/summary.

The player receives a useful scene reading, not silence and not the confrontation.

---

## 10. Narrative Re-Ingestion / Authority Check

`narration_ctx_…` lead minting remains social-only and was not used by the targeted observe failure.

`remember_recent_contextual_leads` previously ran on pre-finalize text. After a perception repair, PR-AH clears that scene's recent contextual leads and re-extracts from the grounded replacement. Unsupported observe prose does not become a later lead figure, NPC, clue, or interlocutor.

Broader `narration_ctx_…` cleanup remains deferred.

---

## 11. Frontier Gate Before / After

| Turn | Before | After |
| --- | --- | --- |
| Post-return `I look around.` | Invented shoulder-stop / whispered "next name", or guard accost | Grounded gate facts; no confrontation; no interlocutor |
| Follow-up `I read the notice board again.` | Not reached as a clean continuation | Authored notice / already-searched realization |

Live extended replay T13 after PR-AH:

> The muddy track beyond the leaning, weathered stone milestone stretches northwest... The notice board nearby confirms... a gate serjeant keeps a sharp eye... Threadbare watchers and ragged refugees huddle...

No "walk with me", no "next name", no bound interlocutor, no new NPC. Residual scene-bleed from `old_milestone` into the gate observe is documented below; it is not the targeted confrontation.

---

## 12. Invented-Inscription Before / After

Shared boundary, different first owner. After PR-AH:

- HTTP examine of the milestone with forced inscription prose falls closed to prints / stone facts.
- Live replay T10 and probe T8 described the stone/prints with no inscription.

Real authored properties remain speakable.

---

## 13. Scenario-Independent Generalization Fixtures

Hard gate. Vocabulary is unrelated to Cinderwatch.

| Test | Fixture | Result |
| --- | --- | --- |
| Grounded observe | `slate_cistern` | PASS — cistern/moss/pails; no NPC/event |
| NPC absence | `slate_cistern` + forced stranger confrontation through `/api/chat` | PASS — confrontation stripped; no interlocutor; no NPC created |
| Authorized NPC | `copper_orchard` / Orchard Keeper | PASS — keeper remains describable |
| Physical absence | cistern rim, no inscription | PASS — inscription rejected |
| Physical presence | `lantern_wharf` carved tide mark | PASS — carved mark remains |
| Hidden fact | silver token under cistern | PASS — observe does not leak it |
| Discoverable fact | examine ferry post | PASS — tide-mark clue may be spoken |
| No state from prose | rejected stranger, then second look | PASS — no NPC/lead/interlocutor authority |
| Presentational freedom | two non-identical grounded cistern lines | PASS |
| Useful fail-closed | rejected confrontation → visible facts | PASS |

These tests exercise `classify` / `apply` and the live `/api/chat` realization path with stubbed GPT.

---

## 14. Anti-Overfitting Audit

Searched PR-AH generic production changes for:

`frontier_gate`, `old_milestone`, `Cinderwatch`, `Captain Thoran`, `notice_patrol_route`, plus the retired stock confrontation lines.

| File | Result |
| --- | --- |
| `game/perception_grounding.py` | No calibration identifiers. Category detectors only. |
| `game/final_emission_non_strict_stack.py` | Kind/evidence based; no scene IDs. |
| `game/final_emission_passive_scene_pressure.py` | Confrontation stock removed. Pre-existing due-check still treats generic visible-fact tokens `guard` / `watch` / `missing patrol` / `rumor` as tension signals. That is not destination or Cinderwatch special-case knowledge, and it no longer selects invented prose. |
| `game/response_policy_enforcement.py` | Confrontation stock removed from `_render_passive_pressure_beat`. |
| `game/gm.py` | Pressure instructions are general "do not invent" language. |
| `game/api.py` | Late hook is kind-based. File already contained calibration IDs from earlier work; PR-AH did not add any. |

No whisper-only sanitizer. No inscription-only sanitizer. No hard-coded NPC names. Synthetic fixtures do not copy Frontier Gate lexical structure.

---

## 15. Tests Added or Updated

Added: `tests/test_grounded_observation_non_invention.py`

Updated to the new observe contract (do not invent confrontation):

- `tests/test_final_emission_passive_scene_pressure.py`
- `tests/test_bv4b_concrete_beat_upstream_satisfier.py`

Existing PR-AD/AE/AF/AG, observe, clue, authority, and dialogue-routing tests were not weakened.

---

## 16. Continued Multi-Turn Replay

Scenario: `data/validation/prah_grounded_observation/scenarios.json` (`R2-MT01-AH`)

After: `artifacts/prah_grounded_observation/extended_replay/runs/20260920T020729Z_R2-MT01-AH/transcript.md`

| Turn | Player | Result |
| --- | --- | --- |
| T7 | follow the missing patrol rumor | `frontier_gate` → `old_milestone` |
| T10 | examine the milestone | prints clue; no inscription |
| T12 | I'll head back to the gate. | authoritative return |
| T13 | I look around. | stays at gate; no confrontation; no interlocutor |
| T14 | I read the notice board again. | authored notice / already-searched |

Ordinary play next becomes uneven where the captain is asked what is being done (T4 still `"I don't know"`) and where investigate at `old_milestone` answers as `"The guard says"` (T11) despite no guard there. T13 also mixes prior milestone geography into the gate observe.

---

## 17. Freeform Perception Probe

Artifact: `artifacts/prah_grounded_observation/freeform_probe/20260920T020909Z_probe.md`

| Turn | Player | Result |
| --- | --- | --- |
| 1 | I glance around. | Grounded facts; awkward fallback grammar; no invention |
| 2 | What's nearby from here? | `question` → catalog ignorance |
| 3 | examine the notice board | `notice_patrol_route` |
| 4 | search the mud for a carved inscription | no inscription invented |
| 5 | inspect the board for special marking | unmarked surface; no symbols invented |
| 6–10 | pursue / look / examine / hidden door / return | travel and destination hold; no inscription |
| 11 | I look around. | grounded gate; no confrontation |
| 12 | ask the tavern runner what stew costs | binds runner; patrol-rumor answer (topic mismatch) |

---

## 18. Validation Results

| Gate | Result |
| --- | --- |
| New PR-AH grounded + synthetic tests | Pass |
| Pressure / BV4B contract updates | Pass |
| Intent parser | Pass |
| Exploration resolution | Pass |
| Clue discovery | Pass |
| Diegetic observe fallback | Pass |
| Narrative authority | Pass |
| State authority | Pass |
| Dialogue routing lock | Pass |
| PR-AD authored knowledge | Pass |
| PR-AE stay/leave | Pass |
| PR-AF arrival/destination | Pass |
| PR-AG generalized exit | Pass |
| Visibility / BV3E / local observation / affordance / content lint / scene anchoring / narration purity | Pass |
| Round #1 calibration corpus | 13/13 |
| Extended R2-MT01-AH replay | Return + grounded observe + notice follow-up |
| Freeform perception probe | Diagnostic; confrontation/inscription flags false |
| Full authoritative suite | Not re-run as a complete 6,450-test pass |

Structural PASS is not semantic playability. T12 evaluator FAIL on the stock leave line is the same known residue as PR-AG.

---

## 19. Remaining Semantic Failures

After confrontation invention is closed:

- Post-return observe can still **bleed prior-scene geography** (`old_milestone` track described while standing at `frontier_gate`).
- Bound `guard_captain` still answers the first watch-command / "what's being done" ask with `"I don't know"`.
- Investigate at `old_milestone` can answer as `"The guard says"` with no guard present.
- Local observation questions (`What's nearby?`) can collapse to catalog ignorance.
- Observe fallback grammar can still stack clauses.
- Some authored lines still use the `mutters` / `"Word is,"` envelope.
- Asking the runner about stew can surface an unrelated patrol rumor.

---

## 20. Deferred Findings

Unchanged unless noted:

- Forced `"Board, runner, or road"` is no longer produced by the repaired owner. Residual evaluator fixtures may still quote the historical line.
- Broader `narration_ctx_…` / `pending_leads` cleanup.
- House Verevin / rooftop invention.
- Filling other stub scenes.
- Project-wide State ↔ Narration campaign.
- Protected-replay baseline refresh.
- General prompt rewrite or NPC dialogue redesign.

---

## 21. Recommended Next Product Slice

**Bound-addressable vs topic-owner mismatch: Guard Captain first-ask ignorance.**

Chosen from the same ordinary-play chain after observation stopped inventing confrontations. The player can now return, look around, and reread the board. The obvious next social act — asking the bound captain what is being done — still yields `"I don't know"` even though the watch-command / patrol fact is authored.

Do not preselect a lettered roadmap item. Scene-bleed on post-return observe is real residue but did not prevent a useful grounded reading or the notice follow-up. The captain first-ask is the highest-leverage remaining conversational blocker.

---

## 22. Product Realization Generalization Doctrine Recommendation

The principle is now recorded in:

`docs/product_realization_validation.md`

It was not added to `docs/DEVELOPMENT_CONSTITUTION.md`. The Constitution is repository-wide process. PR-AA remains the portfolio bootstrap report and was not rewritten.

---

## 23. Git / Worktree State

The worktree was dirty before PR-AH and remains dirty.

PR-AH generic engine:

- `game/perception_grounding.py` (new)
- `game/final_emission_passive_scene_pressure.py`
- `game/final_emission_non_strict_stack.py`
- `game/response_policy_enforcement.py`
- `game/gm.py`
- `game/api.py`

PR-AH tests / tools / report / artifacts / doctrine:

- `tests/test_grounded_observation_non_invention.py` (new)
- `tests/test_final_emission_passive_scene_pressure.py`
- `tests/test_bv4b_concrete_beat_upstream_satisfier.py`
- `tools/run_prah_freeform_probe.py` (new)
- `data/validation/prah_grounded_observation/` (new)
- `artifacts/prah_grounded_observation/` (new)
- `PR-AH_grounded_observation_non_invention.md` (new)
- `docs/product_realization_validation.md` (new)
- `docs/NEXT_SESSION.md` (updated)

Canonical content: none.

Replay/probe reset local runtime documents (`data/session.json`, `data/world.json`, `data/combat.json`, `data/session_log.jsonl`).

No commit or push.

---

## 24. Confidence

**High** that the post-return confrontation was engine-authored pressure/policy stock plus a prompt that requested invention, not a missing Frontier Gate fact.

**High** that Cinderwatch post-return observe no longer emits the targeted confrontation and that unrelated fixtures pass the same boundary.

**High** that generic production changes do not encode Cinderwatch special cases.

**Medium-high** that invented inscriptions on examine are now rejected when they share the perception-grounding seam.

**Medium** that every live observe will stay geographically inside the current scene — discovered-clue text can still license prior-scene nouns.

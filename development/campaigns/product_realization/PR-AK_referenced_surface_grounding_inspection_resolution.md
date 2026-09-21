# PR-AK — Gameplay / AI Experience: Referenced Surface Grounding and Inspection Resolution

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Replay artifacts: `artifacts/prak_referenced_surface/`

---

## 1. Executive Summary

PR-AK repaired the highest-leverage ordinary-play failure after PR-AJ: a legitimate Captain answer was followed by a natural inspect of a referenced roster / roster board, and that inspect collapsed into generic gate-line observe stock.

The roster was classified from authoritative content, not assumed missing. `frontier_gate` already establishes a physical roster board in `visible_facts`. It does not author that board as an interactable, clue, or readable surface. No `frontier_gate.json` content was added.

The recovered contract is:

```text
player / narration reference
    ≠ world authority

authoritative existence
    ≠ automatic inspectability

authorized inspectable surface
    → grounded interaction

unsupported / abstract / hidden / visible-but-not-inspectable surface
    → useful fail-closed response
```

Generic production code does not special-case roster, Frontier Gate, or Cinderwatch. Scenario-independent mill-loft / ink-hall fixtures prove the same semantics.

---

## 2. Starting Failure

PR-AJ extended replay T10–T11:

> Player: If the watch already has a commander on this, I'll check the roster board the serjeant is watching.
> GM: As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line. A gate serjeant manages the crowd and keeps one eye on the roster board.

> Player: I look around the gate again after that.
> GM: the same observe stock

The Captain answer itself was intact and minted no `narration_ctx_…` lead. The next ordinary inspect did not resolve.

---

## 3. Roster Interaction Trace

Traced before production changes against PR-AJ T9–T11 and live `frontier_gate` content.

| Stage | Result |
| --- | --- |
| Authoritative state before inspect | Scene `frontier_gate`. Leads: `notice_patrol_route`, `milestone_mud_prints`. Pending empty. Interlocutor `guard_captain`. No `narration_ctx_…`. |
| Structured social/topic result | Empty payload; PR-AI late realization wrote player-facing text only. |
| Player-facing wording that mentions roster | Captain speech did not author the board. The board is already in scene `visible_facts`. Notice-board inspect narration also restates it. |
| Parser | `investigate` via `check` + extracted tail `roster board the serjeant is watching`. |
| Target binding | `_match_target_to_interactable` compared IDs only. `roster_board` ≠ `notice_board`. |
| Interactable lookup | Exploration required `i_id_slug in prompt_slug` and `reveals_clue`. `notice_board` is not in that prompt slug. |
| Visible-fact lookup | Existing `_match_target_to_visible_fact` was not used on the investigate path. |
| Clue / NPC / topic | No roster clue. No roster topic. |
| Fallback | Generic investigate hint, then `render_observe_perception_fallback_line` with scan-family opener. |
| Final text | Exact observe stock using the watcher fact + the serjeant/roster fact. |
| State mutation | No new interactable, clue, lead, or NPC from T10. |

Canonical search:

| Surface | Roster? | Roster board? |
| --- | --- | --- |
| Scene interactable | no | no |
| Visible fact | no | **yes** — “keeps one eye on the roster board” |
| Opening / journal seeds | no | no |
| Discoverable clue | no | no |
| Hidden fact | no | no |
| NPC / topic | no | no |
| Generated narration only | no | no; the phrase is canonical visible content |

---

## 4. First Failure Point

**Confirmed:** after target extraction, investigate binding had no path from a visible-fact surface to a grounded inspect result.

The intended inspection ceased to have a valid grounded path at **target binding → exploration realization**. Generic observe stock then won because `render_grounded_perception_line` / diegetic observe fallback treated an unbound investigate like look-around, and authorized visible facts made that stock look legal to PR-AH.

This is not a missing `roster_board` interactable, and not a PR-AJ provenance failure.

---

## 5. Roster Authority Classification

**Class B — authoritatively present but not separately inspectable.**

Evidence:

- Physical object/surface: yes. Visible fact names a roster board the serjeant is watching.
- Abstract concept only: no.
- Inspectable interactable / readable / clue: no.
- Narration-only: no.
- Hidden: no.

A content addition was not justified. The world already says the board exists. It does not author names, assignments, ranks, dates, or destinations on it.

---

## 6. Reference vs Existence vs Visibility vs Inspectability

| Concept | Owner recovered | Roster result |
| --- | --- | --- |
| Player reference | Intent target extraction | `roster board` requested; not instantiated |
| Narration reference | PR-AH / PR-AJ | Cannot mint an interactable or lead |
| Authoritative existence | Scene content / visible facts / interactables | Exists |
| Visibility | `visible_facts` (+ opening/journal seeds as presentational existence) | Visible |
| Inspectability | Interactable / readable / clue contents | Not inspectable |
| Interactable | `scene.interactables` | No |
| Visible fact | `scene.visible_facts` | Yes |
| Clue | `discoverable_clues` | No |
| Abstract information | NPC topic text | Not the roster board |
| Hidden information | `hidden_facts` until reveal | Not applicable |

---

## 7. Existing Interaction / Inspection Contracts

Recovered; no new registry.

| Concern | Existing owner |
| --- | --- |
| Inspect / examine / check / read / look at | `intent_parser.INVESTIGATE_PATTERNS` |
| Look around | `OBSERVE_PATTERNS` |
| Interactable resolution | `exploration.resolve_exploration_action` |
| Clue contents | `reveals_clue` + `discoverable_clues` |
| Hidden reveal | `reveals_hidden_fact` / `process_investigation_discovery` |
| Aliases | Interactable `aliases`; previously ID-substring or short-alias-first |
| Observe fallback | `render_observe_perception_fallback_line` |
| Perception non-invention | `game.perception_grounding` |
| Untargeted investigate clue advance | `process_investigation_discovery` |

PR-AK did not replace those owners. It classified a requested target against them and stopped observe stock from swallowing a classified inspect.

---

## 8. Existing Target-Binding Contract

Before PR-AK:

- Investigate bound interactable **IDs** (`target_slug in i_slug`).
- Observe-with-target could bind a visible fact.
- Mixed-investigation grounding preferred interactable aliases, so a one-token alias such as `board` could outrank a more specific visible-fact phrase.

After PR-AK, `classify_referenced_surface`:

1. Extracts the inspect tail.
2. Tries longest content-token prefixes against authored surfaces.
3. Prefers interactable over visible fact over hidden over abstract when the same prefix hits.
4. Overrides a weak short-alias hit only when another surface has a clearly larger token overlap (≥ 3).
5. Does not instantiate unmatched targets.

`I look at the board.` still binds `notice_board`.
`I check the roster board…` binds the visible fact, not the notice-board alias `board`.

---

## 9. Root Cause

**G. Multiple causes, with a confirmed first owner.**

| Cause | Role |
| --- | --- |
| E. Intent / routing | Investigate extracted a target but did not bind visible-fact surfaces. |
| B. Failure to resolve an authoritative non-interactable | The roster board already existed as a visible fact. |
| F. Fallback precedence | Unbound investigate reused look-around observe stock. |
| A. Missing content | **Rejected.** Do not add a roster-board interactable. |
| D. Narration-only object | **Rejected.** The board is canonical. |

---

## 10. Implementation

New read-side helper: `game/referenced_surface.py`.

Not a persistence owner and not a referenced-object registry.

Wired through:

- `game/intent_parser.py` — investigate metadata + mixed-investigation grounding
- `game/exploration.py` — classified inspect resolution; skip unrelated clue reveal
- `game/perception_grounding.py` — replace observe-shaped inspect text for classified non-inspectable surfaces
- `game/api.py` — honor `skip_unrelated_clue_discovery`

No new knowledge store, lead system, destination registry, or scene schema.

---

## 11. Content Changes, If Any, and Their Authority Basis

**None.** `data/scenes/frontier_gate.json` was not modified.

Authority basis for that decision: the roster board is already a visible fact; no authored names, duties, or readable contents exist to add. Manufacturing a board would violate mention ≠ inspectability.

---

## 12. Unsupported-Object Fail-Closed Behavior

Player-named objects with no authored surface classify as `unsupported`.

Response communicates that nothing here matches, then restates current authored surroundings.

No interactable, clue, NPC, lead, or destination is created.

---

## 13. Authored Interactable Preservation

`I inspect the grain hopper.` / `I read the notice board.` / `I read the tariff slate.` still bind and realize.

Natural aliases still work when they are the best match (`feed chute` → `grain_hopper`; bare `board` → `notice_board`).

---

## 14. Visible Non-Interactable Behavior

Authoritative features without interactables are acknowledged. The engine repeats only the authorized visible information and states that closer looking yields nothing further. No secret inscription or extra contents are invented.

---

## 15. Abstract Reference Behavior

An NPC/topic line such as “I checked the shipping records this morning.” remains a concept. `I inspect the records` / `I inspect the shipping ledger` does not instantiate a ledger or invent record contents.

If the player is still socially locked, live routing may still treat a later “inspect those records” as social. Deterministic inspect coverage does not require that lock. The live steal is deferred residue, not the roster class.

---

## 16. Narration-Only Reference Behavior

Generated mention of an unsupported object does not grant authority. Subsequent inspect fails closed. No silver-bell interactable, clue, or named engraving is created. This remains consistent with PR-AH and PR-AJ.

---

## 17. Hidden / Discovery Behavior

The architecture already supports `hidden_facts`. Naming a hidden object classifies as `authored_hidden`. The response does not confirm or reveal it. `process_investigation_discovery` is skipped for that classified inspect.

---

## 18. Inspection-to-Observation Continuation

Inspect of a classified surface stays `investigate` and uses the inspect line.

A later `I look around.` is `observe` again. It may still use the existing two-fact observe fallback; it is no longer the same inspect result, and it is not trapped in failed-inspect state.

Broad observation-variety work remains out of scope.

---

## 19. Frontier Gate Before / After

| Surface | Before | After |
| --- | --- | --- |
| Captain first-ask | Legitimate; no `narration_ctx_…` | Intact |
| Roster inspect | Same generic observe stock as look-around | `On closer inspection, a gate serjeant manages the crowd and keeps one eye on the roster board. Closer looking yields nothing further.` |
| Invented names / duties | Previously a known sibling class | None on the repaired inspect |
| Canonical content | Unchanged | Unchanged |
| Subsequent look-around | Same stock | Still observe stock, but distinct from the inspect line |
| Next natural action | Not reached as a repaired inspect continuation | T12 reached the tavern runner |

---

## 20. Scenario-Independent Generalization Fixtures

Hard gate. Vocabulary is mill loft / ink hall / grain hopper / tariff slate / soot-stained skylight / ivory metronome / silver bell / shipping records. Scene `mill_loft`. NPC `loft_clerk`.

| Test | Result |
| --- | --- |
| 1. Authored interactable | PASS — `grain_hopper` binds |
| 2. Visible non-interactable | PASS — skylight acknowledged, no extra contents |
| 3. Unknown player-named object | PASS — ivory metronome not instantiated |
| 4. Narration-only object | PASS — silver bell inspect fails closed |
| 5. Abstract authorized reference | PASS — shipping ledger not created |
| 6. Readable surface | PASS — tariff slate communicates `TARIFF_FACT` |
| 7. Hidden object | PASS — brass token stays hidden |
| 8. Failed inspect then observe | PASS — second turn is current-scene observe |
| 9. Authored alias | PASS — `feed chute` → hopper |
| 10. No state from failed inspect | PASS — no kiln/schedule entity, clue, or lead |
| Extra: short alias vs specific visible feature | PASS — `board` alone stays the plank; “board the clerk keeps glancing at” stays the tally board |

HTTP tests exercise `/api/chat` with stubbed GPT.

---

## 21. Anti-Overfitting Audit

Searched PR-AK generic production changes (`game/referenced_surface.py` entire; new inspect-realization hook in `game/perception_grounding.py`; explore/parser/api wiring) for:

`roster`, `roster_board`, `guard_captain`, `Captain Thoran`, `frontier_gate`, `Cinderwatch`, `old_milestone`, `patrol`, `watch_command`.

| Surface | Result |
| --- | --- |
| `referenced_surface.py` | No calibration identifiers |
| Perception inspect hook | No calibration identifiers |
| Exploration classified-inspect branch | No calibration identifiers |
| Intent-parser classify wiring | No new calibration identifiers |
| Phrase list for “inspect the roster” | None |
| Hard-coded roster aliases | None |
| Frontier Gate-only fallback | None |
| Invented-name filter | None; grounding is by authority class |
| Auto-interactable from every NPC noun | None |

Calibration identifiers appear in the allowed Frontier Gate regression tests, the campaign report, and replay artifacts.

---

## 22. Tests Added or Updated

Added: `tests/test_referenced_surface_grounding_inspection_resolution.py`

No existing inspect / interactable / visible-fact / PR-AD–PR-AJ expectations were weakened.

---

## 23. Continued Multi-Turn Replay

Scenario: `data/validation/prak_referenced_surface/scenarios.json` (`R2-MT01-AK`)

After: `artifacts/prak_referenced_surface/extended_replay/runs/20260920T121444Z_R2-MT01-AK/transcript.md`

| Turn | Player | Result |
| --- | --- | --- |
| T2 | read notice | `notice_patrol_route` |
| T3 | follow northwest track | `frontier_gate` → `old_milestone` |
| T5 | examine milestone | `milestone_mud_prints` |
| T6 | head back | authoritative return; evaluator FAIL on stock leave line is known residue |
| T7 | look around | grounded gate observe stock |
| T8 | reread board | authored notice |
| T9 | first captain ask | bound `guard_captain`; not ignorance; **no `narration_ctx_…`**; pending empty |
| T10 | check roster board | **Class B inspect line**; no invented names; no new lead |
| T11 | look around again | observe, not inspect; same existing observe stock |
| T12 | ask tavern runner stew cost | social bind `tavern_runner`; unrelated patrol rumor; `muddy_footprints_northwest` + `minlead_exit_…` |

Roster step report:

- Authoritative content established a physical board in `visible_facts`.
- Classification: Class B.
- Physical board exists: yes.
- Separately inspectable: no.
- Canonical content changed: no.
- Response: closer inspection restates the authorized visible fact and yields nothing further.
- Invented names/details: none.

---

## 24. Freeform Interaction Probe

Artifact: `artifacts/prak_referenced_surface/freeform_probe/20260920T121442Z_probe.md`

| Turn | Player | Result |
| --- | --- | --- |
| 1 | read the posted notices | unsupported fail-closed; notice board not bound by that paraphrase |
| 2 | soot-dark stone under the banners | fail-closed against canonical inspectability; later scene overlay mentioned engravings, which did not become inspect authority during the turn |
| 3 | brass orrery | unsupported; no instantiation |
| 4 | look around after that miss | observe; surroundings available |
| 5 | ask about duty records | watch-command answer; probe “invented_name” flag is a Thoran false positive |
| 6 | inspect those records | social lock stole the inspect; no ledger created |
| 7 | examine the board the serjeant keeps glancing at | this recorded probe still bound `notice_board` via alias `board`; the later overlap rule now classifies that richer wording as the roster visible fact in unit tests |
| 8 | look at the notice again | authored notice / already searched |

No Thoran/Lirael/Marrow invention on inspect turns.

---

## 25. Validation Results

| Gate | Result |
| --- | --- |
| New PR-AK tests | Pass (16) |
| Scenario-independent fixtures | Pass |
| Existing intent-parser | Pass |
| Existing exploration | Pass |
| Existing inspect/authored-knowledge | Pass |
| Existing grounded-observation | Pass |
| Existing diegetic observe fallback | Pass in earlier focused file |
| Existing clue discovery | Pass in earlier focused file |
| Existing state-authority | Pass in earlier focused file |
| Existing narration-consistency | Pass in earlier focused file |
| PR-AD authored knowledge | Pass |
| PR-AE stay/leave | Pass in earlier focused file |
| PR-AF arrival | Pass in earlier focused file |
| PR-AG generalized exit | Pass in earlier focused file |
| PR-AH grounded observation | Pass |
| PR-AI bound speaker | Pass |
| PR-AJ provenance | Pass |
| Round #1 calibration | 13/13 (`artifacts/prak_referenced_surface/round1_calibration/`) |
| Extended R2-MT01-AK replay | Roster inspect repaired; continuation taken |
| Freeform interaction probe | Diagnostic; unsupported objects fail closed |
| Full authoritative suite | Not re-run as a complete 6,450-test pass |

Windows `PermissionError` on shared `codex_pytest_tmp` remains environmental. Focused HTTP tests used an isolated `--basetemp`.

Structural PASS is not semantic playability. Known protected-replay / mutation-attribution reds were not refreshed.

---

## 26. Remaining Semantic Failures

- Asking the tavern runner what stew costs still yields an unrelated patrol rumor and can mint a social/minlead row (replay T12).
- Untargeted look-around can still repeat the same two-fact gate stock. Inspect is no longer identical to it.
- `posted notices` / some natural paraphrases still miss `notice_board`.
- Social lock can still steal a later “inspect those records” after a bound ask.
- Authored `mutters` / `"Word is,"` envelope remains.
- Evaluator FAIL on stock leave / some observe lines remains.
- Post-return prior-scene geography bleed and `Gate Serjeant` → `gate_guard` remain deferred.

---

## 27. Deferred Findings

Unchanged unless noted:

- Absent-speaker `"The guard says"` default label.
- `compat_pending_lead_needed` still keys off a scene target only.
- Intent parsing still reads `pending_leads` as the pursuit surface.
- Broader lead/clue overlap reduction.
- `_TEXT_LEAD_SPECS` compatibility text-hook library.
- House Verevin / rooftop invention.
- Filling other stub scenes.
- New authoritative knowledge store.
- Project-wide State ↔ Narration.
- Protected-replay baseline refresh.
- General prompt rewrite or NPC personality redesign.
- Broad observation-variety work.
- Automatically turning NPC-mentioned nouns into interactables.

---

## 28. Recommended Next Product Slice

**Ordinary social-question mismatch after the repaired inspect continuation, starting with the tavern-runner stew-cost ask collapsing to an unrelated patrol rumor and minting a follow-up lead.**

Chosen from replay T12, the first natural action after the repaired roster/observe pair. The player asked a present, local, ordinary question and received a different authored topic plus `muddy_footprints_northwest` / `minlead_exit_…`.

Do not start a general observation-variety campaign because T11 still uses the existing look-around stock. Do not reopen PR-AH, PR-AI, or PR-AJ. Do not add a roster-board interactable.

---

## 29. Git / Worktree State

The worktree was dirty before PR-AK and remains dirty.

PR-AK generic engine:

- `game/referenced_surface.py` (new)
- `game/intent_parser.py`
- `game/exploration.py`
- `game/perception_grounding.py` (file originated in PR-AH; PR-AK added inspect realization)
- `game/api.py`

PR-AK tests / report / handoff / artifacts:

- `tests/test_referenced_surface_grounding_inspection_resolution.py` (new)
- `tools/run_prak_freeform_probe.py` (new)
- `data/validation/prak_referenced_surface/` (new)
- `PR-AK_referenced_surface_grounding_inspection_resolution.md` (new)
- `docs/NEXT_SESSION.md` (updated)
- `artifacts/prak_referenced_surface/` (new)

Canonical scene JSON was not modified.

Replay and the freeform probe reset local runtime documents (`data/session.json`, `data/world.json`, `data/combat.json`, `data/session_log.jsonl`).

Pre-existing dirt from earlier validation, policy, replay, and PR-AC through PR-AJ was not erased.

No commit or push.

---

## 30. Confidence

**Medium-high** on the targeted failure class.

High that the roster is Class B, that the first failure was investigate binding plus observe-stock fallback, and that the mill-loft HTTP fixtures plus the live T10 line prove the general contract. High that notice-board inspect and PR-AD–PR-AJ focused files remain green. Medium that every natural paraphrase of “board” will pick the intended surface — short alias `board` still legally means the notice board, and only richer player wording can prefer the serjeant-watched visible board. Medium that the next-slice recommendation will remain correct after more play — the stew-cost mismatch is the strongest new ordinary-play contaminant after the repaired roster turn.

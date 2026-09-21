# PR-AG — Gameplay: Generalized Destination Exit Resolution

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Replay artifacts: `artifacts/prag_destination_exit_resolution/`

---

## 1. Executive Summary

PR-AG repaired the highest-leverage ordinary-play failure after PR-AF: natural return/onward travel could fail to bind an already-authored exit, and narration could imply departure anyway.

This is a **systemic exit-resolution** repair, not a Cinderwatch phrase list.

The engine now resolves travel against the **current scene's authored exits**:

- exit labels
- destination scene IDs
- unique destination-token overlap
- unique return/back fallback when the scene makes that unambiguous

Cinderwatch / `old_milestone` / `frontier_gate` remain calibration content. Scenario-independent fixtures (`mossy_crossing`, `ruined_orchard`, `salt_harbor`, parameterized meadow/switch/gallery worlds) prove the same contract on unrelated vocabulary.

No new destination registry, travel system, or scene schema was added. Canonical `old_milestone.json` was not changed.

---

## 2. Starting Failure

PR-AF made `old_milestone` playable. The next ordinary action failed:

```text
I'll head back to the gate.
I'll head back to Cinderwatch Gate.
```

PR-AF replay T12: kind `travel`, `resolved_transition=False`, scene stayed `old_milestone`, stock "the attempt meets resistance."

PR-AF freeform T8: kind `travel`, scene stayed `old_milestone`, narration claimed the gatehouse appeared.

Exact-label `"I'll return to Cinderwatch Gate."` already worked. Natural return did not.

---

## 3. PR-AF Return Execution Trace

For `"I'll head back to the gate."` at `old_milestone`:

| Stage | Result before PR-AG |
| --- | --- |
| Raw text | I'll head back to the gate. |
| Commitment strip | head back to the gate. |
| Travel prefix | longest match was `head ` |
| dest_hint | `back to the gate` |
| `_match_exit` | label `Return to Cinderwatch Gate` — no substring/slug hit |
| Follow/pursuit | not a follow phrase |
| Parsed action | `travel`, no `target_scene_id` |
| Exploration rebind | prompt inference required the full label or `frontier_gate` slug |
| Authoritative mutation | none |
| Narration | GPT or stock could claim movement |

`"I'll return to Cinderwatch Gate."` worked because prefix `return to ` left dest_hint `Cinderwatch Gate`, which is a substring of the exit label.

---

## 4. Root Cause

Combination:

- **A. dest extraction (intent parsing):** `head back to X` was treated as prefix `head ` plus leftover `back to X`.
- **C/D. exit/destination matching:** `_match_exit` compared only label substrings and returned the **first** hit. It did not uniquely match destination IDs or significant destination tokens. It also guessed on shared nouns (`trail`).
- **B. return/back:** no general empty-dest return using a unique authored return exit or unique single exit.
- **F. narration/state:** unresolved travel repaired false arrival only on PR-AE lanes, not false departure in general.

Not a missing exit. Not a content omission. Not a Cinderwatch-specific vocabulary hole.

---

## 5. Existing Exit / Destination Contract

Recovered from multiple scenes and `game/scene_destination_binding.py`, `game/intent_parser.py`, `game/exploration.py`, `game/validation.py`.

An authored exit already provides:

- `label`
- `target_scene_id` / `targetSceneId`

Optional elsewhere, not required for PR-AG: aliases, requirements, `world_updates_on_transition`.

Existing unique matchers already existed for declared/embedded travel (`resolve_place_phrase_to_exit_target`, `_declared_unique_exit_target_for_dest`). The main freeform travel prefix path did not use them.

There is no authoritative travel-history owner suitable for inventing "back." `originating_scene_id` is per-resolution. PR-AG does **not** create implicit history. Return uses current-scene exits only.

Minimum playable travel contract:

```text
current scene exits + travel/return intent
    → unique authored exit
    → existing scene_transition
    → narration agrees
```

---

## 6. General Resolution Semantics

Implemented as data-driven unique matching, not phrase whitelists.

| Category | Behavior |
| --- | --- |
| A. Direct exit label | Unique label/slug overlap binds that exit. |
| B. Destination reference | Unique match on `target_scene_id` slug or destination tokens vs label+id tokens. Does not invent a route to a scene with no current-scene exit. |
| C. Return/back | Empty dest after return/back language binds a unique return-labeled exit, else the unique single exit. Multiple exits with no unique return label fail closed. |
| D. Onward / multiple exits | The matching exit wins; first/default exit is not used. |
| E. Ambiguity | Shared nouns (`the trail` with two trail exits) stay unresolved. |
| F. Unavailable | No transition; no invented exit. |
| G. Non-travel mention | Information-seeking leads (`what`/`where`/…) do not travel. |

---

## 7. Implementation

### General engine

- `game/scene_destination_binding.py` — `resolve_authored_exit_from_player_travel`, destination-identity unique match, return/single-exit fallback. Existing `resolve_place_phrase_to_exit_target` now also uses destination identity.
- `game/intent_parser.py` — travel path consumes the general resolver; travel prefixes include general back/return/take forms; first-match `_match_exit` is not used on this path; unique dest match + existing follow-pursuit remain; declared-travel dest resolution uses the same place matcher; commitment regex includes `return` / `go back` / `head back` / `take the`.
- `game/exploration.py` — prompt inference uses the general resolver, then unique (not first) label/id overlap.
- `game/narration_state_consistency.py` — any unresolved `travel` / `scene_transition` that claims departure or arrival is replaced with `That destination is not available from here.` Lane `authored_exit_resolution` is treated as a stay/leave-agreement turn.

### Canonical content

None. `data/scenes/old_milestone.json` was not modified by PR-AG.

### Synthetic / test-only

Arbitrary scenes in `tests/test_generalized_destination_exit_resolution.py` only.

No second exit resolver. Binding still owns destination identity; the parser/exploration call that owner.

---

## 8. Return / Back Semantics

Return is resolved from **current-scene authored exits**, not Cinderwatch aliases and not invented travel history.

- `"Let's go back."` at a one-exit or unique-return-exit scene binds that exit.
- `"I'll head back to the gate."` binds because dest token `gate` uniquely overlaps the current exit surface (`Return to Cinderwatch Gate` / `frontier_gate`).
- The same rule binds `"I'll head back to the bridge."` at `ruined_orchard` → `stone_bridge`.
- Two unlabeled onward exits + bare `"go back"` fail closed.

---

## 9. Narration / State Agreement

General invariant, destination-independent:

- transition succeeded → departure/arrival language is allowed (PR-AE stock leave line may still apply)
- transition did not succeed → narration must not claim the player left or arrived

False-departure detection now includes turn-away / make-your-way / start-back / return language, not only `you arrive`.

---

## 10. Cinderwatch Regression Result

| Phrase | Before | After |
| --- | --- | --- |
| I'll return to Cinderwatch Gate. | bound | bound |
| I'll head back to Cinderwatch Gate. | unbound | `frontier_gate` |
| I'll head back to the gate. | unbound | `frontier_gate` |
| Let's go back. | unbound | `frontier_gate` |
| I'm heading back toward the frontier gate. | unbound | `frontier_gate` |
| Fine. I'll follow the missing patrol rumor… | bound | still bound |

Live extended replay T12: `old_milestone` → `frontier_gate`, kind `scene_transition`. T13 observe remains at `frontier_gate`.

---

## 11. Scenario-Independent Generalization Fixtures

Hard gate. Vocabulary is unrelated to Cinderwatch.

| Test | Fixture | Result |
| --- | --- | --- |
| Exit label | mossy_crossing pine/cedar trails; salt_harbor stair/ferry | PASS |
| Destination name | hill_shrine / mill_pond / stone_bridge / gull_tower | PASS |
| Return | ruined_orchard → stone_bridge via back/return | PASS |
| Multiple exits | pine vs cedar distinguished | PASS |
| Ambiguity | "I'll take the trail." does not guess | PASS |
| Unavailable | glass observatory | PASS |
| Non-travel | "What lies beyond the pine trail?" | PASS |
| State/narration | unresolved walk-to-shrine prose stripped | PASS |
| Parameterized | amber_meadow / copper_switch / ivory_gallery labels and IDs | PASS |

---

## 12. Anti-Overfitting Audit

Searched PR-AG generic production files for:

`old_milestone`, `frontier_gate`, `Cinderwatch`, `gate`, `northwest`, `patrol`, `notice_patrol_route`, `Captain Thoran`

| File | Result |
| --- | --- |
| `game/scene_destination_binding.py` | No calibration identifiers. New resolver uses only current-scene exit data. Pre-existing outdoor-bucket regex still contains generic `gate district` / `patrol` as travel-bucket words, not destination special cases. |
| `game/intent_parser.py` | No new `if scene == old_milestone` (or equivalent). Added prefixes are general English (`head back to`, `take the`). Pre-existing `_PURSUIT_OBJECT_HINTS` still includes `patrol` from PR-AE pursuit binding; PR-AG did not add Cinderwatch aliases there. |
| `game/exploration.py` | Inference now unique-matches; no calibration IDs. |
| `game/narration_state_consistency.py` | Unresolved-travel repair is kind-based, not scene-based. |

`gate` / `northwest` / `patrol` appear in **content**, **Cinderwatch tests**, and **replay artifacts** only as calibration evidence.

No disguised hard-coding of exit index 0, Cinderwatch token sets, or fixture-only aliases.

---

## 13. Tests Added or Updated

Added: `tests/test_generalized_destination_exit_resolution.py`

- Synthetic label / destination / return / multi-exit / ambiguity / unavailable / question / narration tests
- Parameterized unrelated worlds
- Anti-overfitting scan
- Cinderwatch natural-return regression
- HTTP: head-back-to-the-gate, post-return observe, House Verevin stays put

Existing tests were not weakened.

---

## 14. Continued Multi-Turn Replay

Scenario: `data/validation/prag_destination_exit_resolution/scenarios.json` (`R2-MT01-AG`)

After: `artifacts/prag_destination_exit_resolution/extended_replay/runs/20260920T013925Z_R2-MT01-AG/transcript.md`

Original PR-AF prompts preserved. T12 uses `"I'll head back to the gate."` (the failing shape). T13 is the required post-return action.

| Turn | Player | After PR-AG | Human |
| --- | --- | --- | --- |
| T7 | I'll follow the missing patrol rumor… | `frontier_gate` → `old_milestone` | Pass — PR-AE/AF preserved |
| T9–T11 | look / examine / patrol signs | grounded destination | Pass — PR-AF preserved |
| T12 | I'll head back to the gate. | `old_milestone` → `frontier_gate`; stock leave line | Pass for authority; evaluator FAIL is stock-token residue |
| T13 | I look around the gate district again. | stays `frontier_gate`; observe | Pass for pipeline; prose invents an unnamed approach |

---

## 15. Freeform Travel Probe

Artifact: `artifacts/prag_destination_exit_resolution/freeform_probe/20260920T014050Z_probe.md`

| Turn | Player | Result |
| --- | --- | --- |
| 2 | heading out along that northwest track | `old_milestone` |
| 5 | Alright. I'll head back to the gate. | `frontier_gate`, authoritative |
| 6 | What lies beyond the market from here? | question; no travel |
| 7 | I'll go to the glass observatory. | stays; "That destination is not available from here." |
| 9 | follow the missing patrol rumor… | `old_milestone` again |
| 10 | Let's go back. | `frontier_gate` again; arrival prose |
| 11 | I look around. | stays at gate |

Natural language still fails next on **observe inventing social confrontation** (probe T8: a guard accosts the player on "I look around").

---

## 16. Validation Results

| Gate | Result |
| --- | --- |
| New PR-AG generalized + synthetic tests | Pass |
| Intent parser | Pass |
| Scene destination binding | Pass |
| Exploration resolution | Pass |
| Qualified pursuit | Pass |
| PR-AD authored knowledge | Pass |
| PR-AE stay/leave | Pass |
| PR-AF arrival/destination | Pass |
| Scene-transition / state / narrative authority | Pass |
| Dialogue routing lock | Pass |
| Round #1 calibration corpus | 13/13 |
| Extended R2-MT01-AG replay | Return + post-return action succeeded |
| Freeform travel probe | Diagnostic; return/back/unavailable/question hold |
| Full authoritative suite | Not re-run as a complete 6,450-test pass |

Structural PASS is not semantic playability. T12 evaluator FAIL is stock movement vs player tokens, not a failed transition.

---

## 17. Remaining Semantic Failures

Dominant new class after travel works:

- Ordinary `look around` at `frontier_gate` can invent an NPC confrontation or whispered "next name" without binding an interlocutor.

Still present, not elevated by this slice:

- Live examine inventing stone inscriptions
- Guard Captain first-ask ignorance
- Forced "Board, runner, or road"
- Observe-fallback grammar stacking
- `narration_ctx_…` lead ingestion
- `mutters` / "Word is," envelope
- Evaluator false negatives on stock movement

---

## 18. Deferred Findings

Unchanged unless noted:

- Filling other stub scenes
- Complete missing-patrol quest
- `pending_leads` migration / RC-10 / RC-21
- Project-wide State ↔ Narration
- Protected-replay baseline refresh
- PR-AB tooling
- Unicode/operator-console beyond the earlier ASCII engine print

---

## 19. Recommended Next Product Slice

**Post-return / ordinary observe inventing unsolicited NPC confrontation.**

Chosen from continued-play evidence after travel started working, not from roadmap neatness.

Replay T13 and probe T8 show a look-around at the gate manufacturing social pressure. The player can now leave and return; the next ordinary act invents the world again.

Do not preselect PR-AH. Do not open a project-wide State ↔ Narration program unless this local observe invention proves to be that.

### Generalization principle (governance)

No standing Product Realization authority currently states:

```text
CONTENT MAY BE SPECIFIC. SYSTEMS MUST BE GENERAL.
```

PR-AG evidence supports promoting that as a **durable Product Realization validation rule** (portfolio / PR process), with scenario-independent fixtures required whenever a campaign claims systemic engine behavior.

Do **not** put it in `docs/DEVELOPMENT_CONSTITUTION.md`. The Constitution is repository-wide process, not feature-validation doctrine. A later explicit PR-process amendment is the right home.

---

## 20. Git / Worktree State

The worktree was dirty before PR-AG and remains dirty.

PR-AG generic engine:

- `game/scene_destination_binding.py`
- `game/intent_parser.py`
- `game/exploration.py`
- `game/narration_state_consistency.py`

PR-AG tests / tools / report / artifacts:

- `tests/test_generalized_destination_exit_resolution.py` (new)
- `tools/run_prag_freeform_probe.py` (new)
- `data/validation/prag_destination_exit_resolution/` (new)
- `PR-AG_generalized_destination_exit_resolution.md` (new)
- `artifacts/prag_destination_exit_resolution/` (new)
- `docs/NEXT_SESSION.md` (updated)

Canonical content: none.

Pre-existing PR-AC/AD/AE/AF and governance dirt was not erased. Replay/probe reset local runtime documents.

No commit or push.

---

## 21. Confidence

**High** that the PR-AF return failure was dest-extraction plus unique exit/destination binding, not missing content.

**High** that Cinderwatch natural return is now authoritative and that unrelated fixtures pass the same contract.

**High** that generic production changes do not encode Cinderwatch special cases.

**Medium** that every natural travel phrasing in live play will bind — questions, mixed social+travel, and compatibility buckets remain sharp edges.

**Medium-high** that the next slice is invented observe/social confrontation after a successful return.

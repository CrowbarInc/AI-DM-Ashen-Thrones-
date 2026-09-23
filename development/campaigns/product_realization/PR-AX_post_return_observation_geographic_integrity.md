# PR-AX — Post-Return Observation Geographic Integrity

Date: 2026-09-21
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

## 1. Executive Summary

PR-AX repaired the remaining ordinary-play observation defect after PR-AW: an observation after travel or return could still narrate geography unique to a prior scene as if it were locally present.

The defect was not PR-AW stamp state. Scene identity, per-scene last-perception snapshots, and observe-fallback candidate lists were already current-scene scoped. The first incorrect decision was perception evidence treating off-scene known clues and other visited scenes' authored geography as eligible current spatial authority, while `classify_perception_invention` had no current-scene geographic check.

No seen-facts database, salience engine, second location system, embeddings, or global history wipe was added. Existing perception grounding still owns the fail-closed replacement. Historical clues and per-scene perception snapshots remain after transition. `"What's nearby?"` is a different owner.

## 2. Minimal Transition Reproduction Matrix

HTTP isolation on synthetic `ember_kiln` ↔ `brass_quay` (lantern/ash vs mooring rings/tide ledger), stubbed GPT, full `/api/chat` finalize path.

Before-repair evidence: `artifacts/prax_post_return_observation_geo/isolation/20260921T221703Z_isolation.md`

After-repair evidence: `artifacts/prax_post_return_observation_geo/isolation/20260921T222004Z_isolation.md`

Known live-model path from PR-AH: after `old_milestone` → `frontier_gate`, `"I look around."` opened with the leaning weathered milestone track while the player was at the gate.

| Seq | Turns | Authoritative scene on final observe | Before | After |
| --- | --- | --- | --- | --- |
| A | A observe | kiln | kiln geography | unchanged |
| B | A → B observe | quay | quay geography | unchanged |
| C | A → B → A observe | kiln | kiln geography | unchanged |
| D | A observe → B observe | quay | quay geography | unchanged |
| E | A observe → B observe → A observe | kiln | nothing-new (PR-AS/AW) | unchanged |
| F | A observe → B, model emits A geography | quay | classifier allowed A geography; HTTP retry happened to compose B stock | classifier flags `prior_scene_geography`; replacement is B stock / nothing-new |
| G | A observe → B observe → A, model emits B geography | kiln | classifier allowed B geography | classifier flags `prior_scene_geography`; return nothing-new remains valid |
| H | A observe → discover A clue → B, model emits A clue | quay | A clue text entered B `authorized_blob` | A clue remains historical; not current spatial authority |
| I | A observe → B `"What's nearby?"` | quay | `adjudication_query` | same different owner |

## 3. State Trace Across Scene Transitions

Recorded after each transition and observation: authoritative scene, visited list, current visible facts, last-perception snapshot per scene, description hash, recent contextual leads, known clues, fallback candidates, perception evidence, classifier verdict, and player-facing text.

Shared pattern before the repair:

```text
T1 observe at A
  active_scene = ember_kiln
  last_perception[A] = lantern + ash
  last_perception[B] = empty
  authorized A unique = true; B unique = false

T2 scene_transition A → B
  active_scene = brass_quay          ← identity already correct
  last_perception[A] still lantern+ash
  last_perception[B] empty
  fallback candidates = quay rings + ledger
  known A clue, if discovered, is already in B authorized_blob
  classify(A geography at B) = unsupported false

T3 observe at B
  recent_narration consulted is B's snapshot, not A's
  fallback would compose B facts
  live A-geography text is not an invention category
  first incorrect eligibility is already present at T2 evidence build
```

PR-AH's live mixed line survived because it included current-gate facts plus milestone geography. Scene-stall retry is incidental. It is not the owner.

## 4. First Incorrect Decision

`build_perception_evidence_surface` / `_discovered_clue_texts` including off-scene known clue texts in the current observation authorized surface, and `classify_perception_invention` treating observation as supported whenever it avoided the existing invention categories.

That is the first point where prior-scene geography remains eligible after the authoritative location has changed. The later observe still used the existing PR-AH/PR-AS grounding path. Fallback selection was not reading the other scene's narration. Scene identity was not late.

## 5. Failure Classification

| Class | Role |
| --- | --- |
| A | Not demonstrated. Last-perception snapshots are per scene and survive transition correctly. |
| B | Not demonstrated. Fallback candidates are current-scene visible facts. |
| C | Partial sibling: conversation history can prompt the model. It is not the eligibility owner. |
| D | Not demonstrated. Transition does not need to wipe scene-scoped perception. Doing so would break return nothing-new. |
| E | Yes. Realization received current-scene facts plus off-scene clue/geography licensing and kept the wrong present-tense claim. |
| F | Not demonstrated. Return reconstructs from the returned scene document. |
| G | Not demonstrated. `active_scene_id` updates on the authoritative transition helper. |
| H | The missing geographic-authority check on observe is the same owner as E. |

PR-AW stamp eligibility is **not** causally involved. Untargeted visual observe remains the only stamp-eligible turn. Return nothing-new after an earlier observe in that same scene is correct PR-AS/AW behavior.

## 6. Ownership

Existing owners reused:

- `game/perception_grounding.py` — evidence surface and invention classification
- `game/diegetic_fallback_narration.py` — unchanged current-scene fallback composition
- `game/api.py` — unchanged late perception hook

No new owner. Visited-scene authored facts and `source_scene` on known clues are existing scene/clue authority, not a second geography system.

## 7. Does `"What's nearby?"` Share This Owner?

No.

Isolation I and the focused fixture resolve `"What's nearby?"` as `adjudication_query` (`No nearby NPC presence is currently established in this scene.`). That is local-presence adjudication, not post-return geographic eligibility. Left deferred.

## 8. Production Changes

Generic production only:

1. `_discovered_clue_texts` no longer adds known clues whose `source_scene` is a different scene. Those remain in player knowledge / history.
2. `_offscene_geography_texts` reads other visited scenes' authored visible facts, summary, location, interactable text, and off-scene known clue text.
3. `classify_perception_invention` flags `prior_scene_geography` on observe when a distinctive off-scene span is asserted and is not in the current authorized spatial blob.
4. Existing fail-closed observe fallback replaces that text.

No Frontier Gate nouns. No stamp-eligibility change. No global conversation wipe. No coordinate movement.

## 9. Tests Added / Changed

Added `tests/test_post_return_observation_geographic_integrity.py` (19):

1. Scene A observation uses A geography.
2. After A → B, A-unique geography is not emitted.
3. After A → B, authored B geography remains.
4. After A → B → A, legitimate A geography can surface again.
5. A prior perception snapshot cannot override current-scene geography.
6. Historical clues and A snapshots are not erased by transition.
7. PR-AS immediate untargeted nothing-new remains.
8. PR-AW later-turn restack protection remains.
9. Targeted current-scene observation may repeat.
10. A new current-scene fact may surface.
11. Return nothing-new remains valid.
12. PR-AR hidden-fact fail-closed remains.
13. PR-AQ local walk remains `custom`, not scene travel.
14. PR-AT already-searched keeps a complete authored sentence.
15. Cedar Wharf / Tin Loft generalization, not Frontier Gate wording.
16. Off-scene clue text does not license current geography.
17. A scene's own geography is not flagged after return.
18. `"What's nearby?"` is not this owner.
19. Generic engine files have no Frontier Gate special case.

PR-AS / PR-AW tests were not weakened.

## 10. Validation

| Suite | Result |
| --- | --- |
| New PR-AX fixtures | passed (19) |
| Isolation after repair | F/G/H classifier now `prior_scene_geography`; A–E semantic results unchanged |
| PR-AS observe relevance | passed (14) |
| PR-AW later-turn restack | passed (16) |
| PR-AT already-searched | passed (9) |
| PR-AU grounded-social-absence | passed (15) |
| PR-AV topic-hook integrity | passed (16) |
| PR-AR perception grounding | passed (29) |
| PR-AQ physical-action typing | passed (26) |
| PR-AH grounded observation | passed (13) |
| Full authoritative suite | not re-run |
| Frontier Gate 20-turn live replay | not re-run |

The owner is perception evidence eligibility, not live-model wording. Isolation used the real HTTP pipeline plus a direct classifier probe because scene-stall retry can mask stubbed bleed. Structural PASS is not treated as semantic playability.

## 11. Semantic Before / After

| Sequence | Before | After |
| --- | --- | --- |
| Look around at A | A geography | unchanged |
| A → B, look around | B geography when fallback/retry composed | unchanged |
| A → B, live text asserts A lantern as present | classifier allowed it | current B facts, or nothing-new if B was just observed |
| A observe → B → A observe | nothing-new | unchanged |
| A → B → A first look, no prior A observe | A geography | unchanged |
| Discover A clue, travel to B | A clue licensed B observation | A clue remains known; not present-here geography |
| `"What's nearby?"` after travel | adjudication collapse | deferred; not this owner |

PR-AH before:

> The muddy track beyond the leaning, weathered stone milestone stretches northwest... The notice board nearby confirms...

After the repair, distinctive milestone geography that is not authored at the current scene is unsupported observe content and fail-closes through existing current-scene realization.

## 12. Generalization Evidence

Kiln lantern/ash, quay rings/ledger, and cedar pilings / tin-loft crates are not Frontier Gate watchers/serjeant calibration. The same visited-scene / `source_scene` rule protected both pairs. Production files contain no `frontier_gate`, `old_milestone`, `threadbare watchers`, `muddy gate line`, or `gate serjeant` special case.

## 13. Regressions Checked

Preserved:

- PR-AS immediate untargeted nothing-new
- PR-AW intervening inspect / social does not restack
- Targeted observation may repeat a current-scene fact
- New / changed visible facts may surface
- Return nothing-new after an earlier observe in that scene
- Historical clues and per-scene snapshots survive transition
- PR-AR hidden-fact fail-closed
- PR-AQ local movement ≠ scene travel
- PR-AT already-searched complete authored sentence
- PR-AU / PR-AV focused suites

## 14. Intentionally Deferred Residue

Leave these deferred unless later evidence elevates them:

- Local observation `"What's nearby?"` collapse (`adjudication_query`)
- Replay / opening `Gate Guard mutters` / `"Word is,"`
- `"who last read that tally slate"` routing as inspect
- `posted notices` missing `notice_board`
- Follow-up paraphrases without owned-topic / public-clue overlap
- `"Gate Serjeant"` resolving to `gate_guard`
- Unresolved travel narrated as scene stock
- Evaluator lexical false negatives on quiet listen and nothing-new
- Generic `"The guard says"` absent-speaker label
- Ordinary actions such as `"I step back… and wait"` resolving `kind=None`
- Unrelated social-pressure test reds

Do not reopen PR-AW stamp eligibility, PR-AV topic-hook eligibility, PR-AU grounded-absence fail-closed, PR-AT truncation, PR-AS relevance comparison, PR-AR grounding, PR-AQ typing, PR-AP grammar, PR-AO provenance, or PR-AI speaker ownership unless new evidence shows they cause a remaining defect.

## 15. Recommended Next Action

Post-return geographic bleed is closed at the perception-evidence owner.

Highest-leverage remaining ordinary-play residue in the same lane: local `"What's nearby?"` collapse. That is an adjudication / local-presence owner, not this geographic check.

Do not start a seen-facts / salience memory. Do not reopen this geographic-authority rule without new causal evidence.

No user decision is required.

## 16. Git / Worktree State

Branch: `feature/product-realization` at checkpoint `4c0a454`, plus uncommitted PR-AS through PR-AX work.

Isolation used `development/tmp/prax_isolation_runtime/` and did not reset canonical `data/` documents.

Not committed. Not pushed.

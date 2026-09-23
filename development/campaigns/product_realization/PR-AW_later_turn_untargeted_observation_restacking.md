# PR-AW — Later-Turn Untargeted Observation Restacking

Date: 2026-09-21
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

## 1. Executive Summary

PR-AW repaired the remaining ordinary-play observation defect after PR-AS: an untargeted look-around could re-emit unchanged scene stock after intervening social or investigation turns.

Immediate adjacent reinspection was already correct. The later-turn failure was not missing seen-facts memory. Existing PR-AS state was sufficient. `remember_completed_perception_turn` treated almost every completed turn as an observation stamp, so social, investigate, and listen overwrote `last_perception_narration` with unrelated text. The later observe still consulted that field; the stock-bearing narration was simply gone.

No seen-facts database, salience engine, embeddings, stock rotation, or second observation router was added. Existing observe fallback and the late perception hook remain the owners. Nothing-new remains a valid grounded result. Targeted observation may still repeat a previously seen fact. New or changed visible facts may still surface.

## 2. Minimal Reproduction Matrix

HTTP isolation on a synthetic `ember_kiln` scene (lantern + ash stock), stubbed GPT, full `/api/chat` finalize path.

Before-repair evidence: `artifacts/praw_later_turn_observation_restack/isolation/20260921T213233Z_isolation.md`

| Seq | Turns | Final observe | Cause visible in state |
| --- | --- | --- | --- |
| A | observe → observe | nothing-new | recent narration still holds the stock pair |
| B | observe → social → observe | restack lantern+ash | social (`question`) overwrites narration with porter dialogue |
| C | observe → investigate → observe | restack lantern+ash | inspect (`discover_clue`) overwrites narration with slate/clue text |
| D | observe → social → investigate → observe | restack lantern+ash | same overwrite chain |
| E | observe → listen → observe | restack lantern+ash | listen (`observe` + listen family) overwrites narration with quiet text |
| F | social → first observe | stock correctly surfaces | control: first look-around must still realize visible facts |

After-repair evidence: `artifacts/praw_later_turn_observation_restack/isolation/20260921T213522Z_isolation.md`

A–E end in `Nothing new stands out from here.` F still surfaces lantern+ash.

## 3. State Trace Across Intervening Turns

Recorded after each turn: last-perception snapshot, last-description hash, selected preview, recent-use inputs, target, kind, and whether the fallback would have chosen nothing-new.

Shared pattern before the repair:

```text
T1 observe
  kind=observe  targeted=false
  last_perception_narration = lantern + ash stock
  last_perception_visible_facts = [lantern, ash]
  new_visible_facts = []
  facts_mentioned_in_recent = lantern + ash

T2 social / investigate / listen
  kind=question | discover_clue | observe(listen)
  last_perception_visible_facts = [lantern, ash]   ← same facts, rewritten
  last_perception_narration = dialogue / slate / quiet   ← stock lost
  new_visible_facts = []
  facts_mentioned_in_recent = []
  would_nothing_new_from_recent = false

T3 untargeted look around
  kind=observe  targeted=false
  recent_narration no longer mentions stock
  late hook repeated_untargeted_stock = false
  fallback restacks lantern + ash
```

`last_description_hash` is a sibling exact-text owner. Social did not need to change it. Scene runtime was not reconstructed or dropped. `collect_recent_player_facing_narration` is not adjacency-scoped (`max_turns` is unused); it simply returns the last stamped narration.

Sequence F shows why the facts list alone cannot be treated as “already seen”: a social turn already wrote the current visible facts into the snapshot before any look-around. Using that list as consumed-memory would suppress a first observe.

## 4. First Incorrect Decision

`remember_completed_perception_turn` deciding that any completed turn except opening / travel / transition may replace observation recent-use.

That is the first incorrect decision. The later observe still used the PR-AS path. Selection and comparison semantics were not adjacency-only. The information that prevented immediate repetition stopped influencing selection at the intervening stamp, not at the later lookup.

## 5. Failure Classification

Social-intervened and investigate-intervened restacking **share one cause**. Listen-intervened restacking is the same overwrite.

| Class | Role |
| --- | --- |
| A | Social overwrites `last_perception_narration`. |
| B | Investigation / discover_clue overwrites the same field. |
| H | Listen quiet overwrites the same field. Same owner. |
| C | Not demonstrated. Later observe does consult the snapshot. |
| D | Not demonstrated. Same fallback / late-hook path. |
| E | Not the owner. Hash comparison is a sibling. |
| F | Not demonstrated. Metadata is written, not dropped. |
| G | Not a new semantic requirement. PR-AS already excluded opening / travel / transition from stamping; social / investigate / listen were left inside the stamp. |

They did not require separate repairs.

## 6. Ownership

Existing owners reused:

- `game/perception_grounding.py` — `remember_completed_perception_turn` lifecycle
- `game/api.py` — post-finalize stamp call sites (now pass kind / player text)
- `game/diegetic_fallback_narration.py` — unchanged PR-AS relevance comparison

No new owner. Scene runtime's last-perception snapshot remains a recent-use signal, not a player-memory or seen-facts subsystem.

## 7. Was Existing PR-AS State Sufficient?

Yes.

`last_perception_narration` already expresses “these visible facts were realized on an untargeted look-around.” `last_perception_visible_facts` already expresses the world snapshot used for new-fact delta. The later-turn decision is available if the stock-bearing narration is not replaced by unrelated turns.

The facts snapshot by itself is not a safe “already observed” flag, because non-observation turns were also writing it. That is why this cycle repaired stamp eligibility rather than treating every fact in the snapshot as consumed.

A broader memory / salience design is not required.

## 8. Production Changes

Generic production only:

1. `observation_recent_use_should_record` — stamp only untargeted visual `observe`. Social, investigate / discover_clue, listen, and targeted perception do not replace the snapshot.
2. `remember_completed_perception_turn` no-ops when the turn is not stamp-eligible.
3. A nothing-new untargeted observe refreshes the visible-fact list and turn marker but keeps the prior stock-bearing narration.
4. Both API finalize sites pass `resolution` and `player_text` into the existing helper.

No Frontier Gate nouns. No leftover-stock rotation. No permanent hide-after-first-mention.

## 9. Tests Added / Changed

Added `tests/test_later_turn_untargeted_observation_restacking.py` (16):

1. `remember` ignores social / investigate overwrite.
2. Nothing-new and listen keep stock narration.
3. Stamp eligibility is untargeted visual observe only.
4. observe → observe remains nothing-new.
5. observe → social → observe does not restack.
6. observe → investigate → observe does not restack.
7. observe → social → investigate → observe does not restack.
8. observe → listen → observe does not restack.
9. Targeted observe may still repeat the targeted fact after intervening turns.
10. A genuinely new visible fact can surface later.
11. Meaningful visible-fact change can surface appropriate content again.
12. Social before the first observe still surfaces stock.
13. Nothing-new does not permanently hide a later targeted fact.
14. Brass Quay generalization: social does not restack hooks/board stock; targeted board remains available.
15. Fallback nothing-new still uses recent stock narration.
16. No Frontier Gate special case in the generic engine files.

PR-AS tests were not weakened.

## 10. Validation

| Suite | Result |
| --- | --- |
| New PR-AW fixtures | passed (16) |
| Isolation after repair | A–E nothing-new; F first observe still surfaces stock |
| PR-AS observe relevance | passed (14) |
| PR-AT already-searched | passed (9) |
| PR-AU grounded-social-absence | passed (15) |
| PR-AV topic-hook integrity | passed (16) |
| PR-AR perception grounding | passed (29) |
| PR-AQ physical-action typing | passed (26) |
| PR-AH grounded observation | passed (13) |
| PR-AP refusal grammar | passed (26) |
| Full authoritative suite | not re-run |
| Frontier Gate 20-turn live replay | not re-run |

The defect was the stamp lifecycle on the shared finalize path, not live-model wording. Isolation used the real HTTP pipeline. Structural PASS is not treated as semantic playability.

## 11. Semantic Before / After

| Sequence | Before | After |
| --- | --- | --- |
| I look around. then I look around again. | first stock, then nothing-new | unchanged |
| I look around. then ask the porter about mash. then I look around. | restack lantern + ash | nothing-new |
| I look around. then inspect the fee slate. then I look around. | restack lantern + ash | nothing-new |
| I look around. then ask, then inspect, then look around. | restack lantern + ash | nothing-new |
| I look around. then I listen. then I look around. | restack lantern + ash | nothing-new |
| Ask the porter first, then look around. | stock surfaces | stock still surfaces |
| After intervening turns, look at the cracked lantern. | targeted lantern | still targeted lantern |
| After intervening turns, a new slate fact appears. | n/a | slate may surface |

## 12. Generalization Evidence

Kiln lantern/ash and quay hooks/board are not Frontier Gate watchers/serjeant calibration. The same stamp-eligibility rule protected both scenes. Production files contain no `frontier_gate`, `threadbare watchers`, `muddy gate line`, or `gate serjeant` special case.

## 13. Regressions Checked

Preserved:

- PR-AS immediate untargeted nothing-new
- Targeted observation may repeat a previously seen fact
- New / changed visible facts may surface
- Empty listen remains grounded and does not pull visual stock
- Facts are not permanently hidden after first mention
- PR-AR visual presence ≠ speech; empty listen is valid absence
- PR-AQ local movement / listen typing
- PR-AT already-searched complete authored sentence
- PR-AU grounded social-absence fail-closed
- PR-AV topic-hook integrity

## 14. Intentionally Deferred Residue

Leave these deferred unless later evidence elevates them:

- Replay / opening `Gate Guard mutters` / `"Word is,"`
- `"who last read that tally slate"` routing as inspect
- `posted notices` missing `notice_board`
- Follow-up paraphrases without owned-topic / public-clue overlap
- `"Gate Serjeant"` resolving to `gate_guard`
- Post-return prior-scene geographic bleed
- Local `"What's nearby?"` collapse
- Unresolved travel narrated as scene stock
- Evaluator lexical false negatives on quiet listen and nothing-new
- Generic `"The guard says"` absent-speaker label
- Ordinary actions such as `"I step back… and wait"` resolving `kind=None`
- Unrelated social-pressure test reds

Do not reopen PR-AV topic-hook eligibility, PR-AU grounded-absence fail-closed, PR-AT truncation, PR-AS relevance comparison, PR-AR grounding, PR-AQ typing, PR-AP grammar, PR-AO provenance, or PR-AI speaker ownership unless new evidence shows they cause a remaining defect.

## 15. Recommended Next Action

Later-turn untargeted restacking after intervening non-observation turns is closed.

Highest-leverage remaining ordinary-play residue in the same lane: post-return observe geographic bleed, or local `"What's nearby?"` collapse. Those are different owners from this stamp lifecycle.

Do not start a seen-facts / salience memory. Do not reopen this stamp eligibility without new causal evidence.

No user decision is required.

## 16. Git / Worktree State

Branch: `feature/product-realization` at checkpoint `4c0a454`, plus uncommitted PR-AS, PR-AT, PR-AU, PR-AV, and PR-AW work.

Isolation used `development/tmp/praw_isolation_runtime/` and did not reset canonical `data/` documents.

Not committed. Not pushed.

# PR-AS — Observe Fallback Relevance and Stock Repetition

Date: 2026-09-20
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

## 1. Executive Summary

PR-AS repaired the highest-leverage ordinary-play defect after PR-AR: a grounded observe/listen result could still mechanically append the same two-fact Frontier Gate stock bundle on the next untargeted look-around.

Observation was already correctly typed and perception-grounded. The remaining failure was relevance, not authority.

```text
AUTHORITY ANSWERS:  "MAY THE NARRATOR SAY THIS?"
RELEVANCE ANSWERS:  "SHOULD THE NARRATOR SAY THIS NOW?"
```

No new observation system, perception owner, world-state owner, salience engine, or seen-facts memory was added. Existing diegetic observe fallback now distinguishes authoritative facts from facts that should be said on this turn. Empty listen no longer falls through to visual stock. Immediate untargeted reinspection may remain nothing-new.

## 2. Reproduced Failure

Direct fallback reproduction on live `frontier_gate` visible facts, before the change:

| Input | Selected facts | Line |
| --- | --- | --- |
| `I look around.` | watchers + serjeant | `As you watch the scene, threadbare watchers… A gate serjeant…` |
| `I look around again.` | same pair | identical line |
| `I look around the gate again after that.` | same pair | identical line |

`first == second` was `True`. Scoring used only intent-family keywords. There was no recent-use or nothing-new outcome.

PR-AR probe/replay showed the same pair after listen replacements and untargeted look-around.

## 3. Root Cause

**B. Selection lacked recent-use awareness**, with **A** as the observable consequence and **C** as the missing outcome.

`_select_intent_aligned_visible_facts` treated scan-family keyword overlap as sufficient reason to emit the same top two facts every time. `_intent_aligned_observe_line` always composed both. The seed-picker fallthrough would dump facts even when intent alignment returned nothing.

Listen contamination was a sibling on the same seam (**D**): when resolution metadata was missing, empty listen did not take the diegetic-quiet path and could fall through to visual stock. Live-model listen that restated authorized visual facts also survived because those facts were authoritative.

`apply_repeated_description_guard` already existed but only matches an exact full-text hash, so paraphrase or a swapped second fact escaped.

## 4. First Incorrect Decision

`_select_intent_aligned_visible_facts` / `_intent_aligned_observe_line` deciding that family-keyword overlap means the facts should be said now, with no check of whether they were just surfaced or whether the turn is untargeted reinspection with no world change.

For empty listen without a quiet-path gate, the first incorrect composition decision was falling through to visual fact realization after audible selection returned nothing.

## 5. Existing Owner Reused

- `game/diegetic_fallback_narration.py` — observe fallback selection/composition
- `game/perception_grounding.py` — fail-closed perception realization
- scene runtime (`last_perception_visible_facts`, `last_perception_narration`, `last_perception_turn`) beside the existing `last_description_hash` owner

No new owner.

## 6. Implementation

Generic production only:

- Untargeted observe + recent narration that already contains the would-be stock facts → owned nothing-new line.
- Targeted observe may still realize a previously seen fact.
- Visible-fact snapshot detects actual world change; leftover unused stock is not rotated for variety.
- Listen / approach_listen with no authored audible fact → existing diegetic quiet, even without `diegetic_null` metadata.
- Late perception hook replaces listen-that-pulled-visual-stock and repeated untargeted stock.
- Snapshot is written after the late perception hook, not mid-turn, so same-turn finalize cannot treat the current text as “already said.”
- Opening / travel / scene-transition turns do not stamp observe recent-use.

No Frontier Gate content was added. No random prose cycling.

## 7. Files Changed

- `game/diegetic_fallback_narration.py`
- `game/perception_grounding.py`
- `game/gm_retry.py`
- `game/api.py`
- `game/storage.py`
- `tests/test_observe_fallback_relevance_stock_repetition.py`
- `tools/run_pras_freeform_probe.py`
- `data/validation/pras_observe_fallback_relevance/scenarios.json`
- `artifacts/pras_observe_fallback_relevance/`
- this report
- `docs/NEXT_SESSION.md`

## 8. Generalization Fixtures

Synthetic kiln / quay scenes in `tests/test_observe_fallback_relevance_stock_repetition.py`:

| Fixture | Result |
| --- | --- |
| 1 First untargeted observe surfaces facts | PASS |
| 2 Immediate repeat does not restack stock | PASS |
| 3 Targeted observe may repeat a seen fact | PASS |
| 4 Empty listen does not pull visual stock | PASS |
| 5 Changed visible facts may surface | PASS |
| 6 Nothing-new does not invent | PASS |
| 7 Later targeted fact remains available | PASS |
| 8 Nothing-new line is complete/playable | PASS |

## 9. Frontier Gate Before / After

| | Before | After |
| --- | --- | --- |
| Immediate `I look around.` then `I look around again.` | identical watchers + serjeant pair | first pair, then `Nothing new stands out from here.` |
| Empty listen | could append visual stock | diegetic quiet |
| Targeted notice board after that | available | still available |
| T16 walk+listen | grounded quiet (PR-AR) | still grounded quiet |

Extended replay `20260921T004755Z_R2-MT01-AS`: T16 quiet; T17 first look-around may surface the pair; T18 immediate repeat is nothing-new; T19 targeted board remains available; T20 ordinary wait continues.

Evaluator lexical FAILs on quiet listen and nothing-new are known lexical misses, not remaining invention. Calibration labels were not weakened.

## 10. Validation

| Suite | Result |
| --- | --- |
| New PR-AS fixtures | passed |
| Diegetic fallback / HA / PR-AR / PR-AH | passed |
| PR-AQ / PR-AK / PR-AP / PR-AF | passed |
| PR-AO / intent parser | passed |
| Round #1 semantic calibration | 13/13 |
| Extended R2-MT01-AS | completed; T16–T20 as above |
| Freeform probe | completed |
| Full authoritative suite | not re-run |

## 11. Remaining Defects

- After intervening social/investigate turns, a later untargeted look-around can still re-emit the stock pair because recent-use is the last perception narration, not a long-lived seen-facts list. Immediate repeat is fixed. Do not expand this into a player-memory system without new evidence.
- T13 / T19 `already_searched` can still truncate (`northwest…`).
- Live model can still invent a time, count, price, or redirect on social absence.
- Opening `Gate Guard mutters` / `"Word is,"` can still appear. Do not reopen PR-AI without new causal evidence.
- Evaluator lexical false negatives on quiet listen and nothing-new lines.
- Some ordinary actions (`I step back… and wait`) still resolve `kind=None`.

## 12. Recommended Next Slice

**T13 / already_searched truncation** — now also visible on the T19 board reread in the PR-AS chain.

Do not start pricing/economics. Do not reopen PR-AS relevance, PR-AR grounding, PR-AQ typing, PR-AH confrontation grounding, or PR-AI speaker ownership unless new evidence shows they cause the truncation.

## 13. Git / Worktree State

Branch: `feature/product-realization` at checkpoint `4c0a454`, plus uncommitted PR-AS work.

Runtime documents mutated by replay/probe (`data/session.json`, `data/world.json`, `data/combat.json`, `data/session_log.jsonl`) were restored. Canonical scene content was not modified.

Not committed. Not pushed.

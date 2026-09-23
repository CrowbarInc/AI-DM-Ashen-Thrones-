# PR-AT — Already-Searched Truncation

Date: 2026-09-20
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

## 1. Executive Summary

PR-AT repaired the remaining ordinary-play truncation on `already_searched` turns. The engine decision was already correct: a resolved interactable is not rediscovered. Realization was not.

`classify_referenced_surface` already computed a complete authored inspectable sentence. That sentence was dropped from resolution metadata, `already_searched` was excluded from perception fail-closed realization, and the live model was left to paraphrase “nothing new.” The model then restated board/clue content, invented unsupported detail, and ended on a dangling clause (`with…`, `northwest…`).

No new observation system, seen-facts store, router, or Frontier Gate content was added. Existing referenced-surface / perception realization now owns the player-facing `already_searched` sentence.

## 2. Reproduction Evidence

Existing evidence, not a new scenario:

| Source | Turn | Kind | Player-facing ending |
| --- | --- | --- | --- |
| PR-AQ replay `20260920T211426Z_R2-MT01-AQ` | T13 | `already_searched` | `… roster board, with…` |
| PR-AS replay `20260921T004755Z_R2-MT01-AS` | T8 | `already_searched` | complete authored clue title |
| PR-AS same replay | T13 | `already_searched` | complete model restatement |
| PR-AS same replay | T19 | `already_searched` | `… taking the northwest…` |

T8 proved the owned authored sentence can be complete. T13 in the PR-AS chain was not a counterexample to the defect class; T13 in the earlier PR-AQ chain and T19 in PR-AS are the truncated members of the same class.

Deterministic isolation (`development/tmp/prat_already_searched_isolation.py`) on a mill-loft slate, before the repair:

| Stage | Result |
| --- | --- |
| `classify_referenced_surface` | `inspectable_text = "Dock fees rise after the second horn."` |
| `metadata_from_classification` | inspectable text absent |
| `already_searched` resolution | `clue_text=None`, `discovered_clues=[]`, hint only |
| `classification_from_resolution` | empty inspectable text |
| owned referenced-surface line | complete authored sentence |
| `already_searched` in `PERCEPTION_KINDS` | `False` |
| `apply_perception_non_invention_to_gm` on T19 text | truncated model prose unchanged |

After the repair, the same apply path replaces T19-like text with the complete authored sentence.

## 3. Causal Trace

```text
player reread / repeated investigate
  → intent / referenced-surface: authored_interactable
  → exploration: interactable already resolved
  → kind=already_searched          ← correct semantic decision
  → classified inspectable_text computed
  → metadata drop of inspectable_text
  → clue_text left null (correct anti-rediscovery)
  → no owned player-facing sentence remains
  → already_searched excluded from perception fail-closed
  → live model told: "Narrate that they find nothing new."
  → model paraphrases / elaborates / trails off with …
  → truncated prose ships
```

Post-processing did not clip a complete sentence. There is no 280-character player-facing trimmer on this path. `_drop_dangling_optional_connectors` does not append `…`. The ellipsis is model-authored trailing-off after an unowned realization.

## 4. First Incorrect Decision

After a correct `already_searched` decision, realization discarded the already-computed authored inspectable sentence and left player-facing prose to the live model.

Two cooperating omissions made that decision stick:

1. `metadata_from_classification` / `classification_from_resolution` did not persist `inspectable_text`. `already_searched` correctly omits `clue_text` so rediscovery does not fire, so the owned sentence vanished.
2. `apply_perception_non_invention_to_gm` skipped `already_searched`, so the referenced-surface fail-closed path never replaced the fragment.

## 5. Failure Classification

T13 and T19 share one cause.

| Class | Role |
| --- | --- |
| D | First incorrect decision: realization selected no owned complete field/clause |
| A | Observable consequence: live-model restatement then ships incomplete |
| B | Not an incomplete engine *decision*; the decision was `already_searched` |
| C | Not an internal-state leak |
| E | Not a punctuation/token clipper |

T13 added extra scene dressing and died on `with…`. T19 elaborated board contents (`inbound goods`, `after dusk`) and died mid-clue on `northwest…`. Same unowned realization, different model paraphrase.

## 6. Ownership

Existing owners reused:

- `game/referenced_surface.py` — persist and restore authored inspectable text
- `game/perception_grounding.py` — fail-closed realization of `already_searched`
- `game/exploration.py` — `already_searched` decision; generic searched-target check now runs before unsupported-surface investigate return
- `game/gm_retry.py` — retry fallback uses the same grounded line, not observe stock

No new owner. Observe fallback remains the owner of observation fallback. `already_searched` is investigation realization, not a seen-facts system.

## 7. Production Changes

Generic production only:

- Persist `referenced_surface_inspectable_text` on classification metadata.
- Reconstruct inspectable text from that field when `clue_text` is absent.
- Include `already_searched` in perception kinds.
- Always replace live `already_searched` narration with the referenced-surface / grounded line.
- Authored interactable reread may repeat the previously authored inspectable sentence.
- If no authored inspectable sentence exists, emit a complete nothing-further line.
- Generic already-searched targets are recognized even when the surface is unsupported.
- Forced retry no longer dumps `already_searched` through observe stock.

No Frontier Gate nouns were added to engine code. No new clues, interactables, prices, sounds, or player-memory.

## 8. Tests Added / Changed

Added `tests/test_already_searched_truncation.py`:

1. Metadata keeps authored inspectable text.
2. `already_searched` is not a new discovery.
3. Owned line is complete and authored.
4. T13-like / T19-like fragments are replaced.
5. Generic already-searched is complete and does not invent.
6. HTTP reread restates the authored fact and does not mint a second clue.
7. First authored read remains available.
8. No Frontier Gate special case in the touched engine files.
9. Calibration-only Frontier Gate T13/T19 fragments are replaced with the authored patrol-route sentence.

No existing expected outputs were weakened.

## 9. Validation

| Suite | Result |
| --- | --- |
| New PR-AT fixtures | passed |
| PR-AS observe relevance | passed |
| PR-AR perception grounding | passed |
| PR-AK referenced surface | passed |
| PR-AO investigation provenance | passed |
| PR-AP refusal grammar | passed |
| PR-AH grounded observation | passed |
| PR-AQ physical-action typing | passed |
| Discovery memory | passed |
| Intent parser | passed |
| Diegetic fallback narration | passed |
| Explicit world-action lock | passed |
| Transcript investigate-then-repeat | passed |
| Full authoritative suite | not re-run |
| Live 20-turn replay | not re-run; deterministic T13/T19 isolation used instead |

Structural PASS is not treated as semantic playability. The T19 replay had scored semantic PASS while ending `northwest…`. Completeness is now asserted directly.

## 10. Semantic Before / After

Synthetic mill-loft reread:

| | Before | After |
| --- | --- | --- |
| Resolution | `already_searched`, no owned sentence | `already_searched`, inspectable text restored |
| T19-like model fragment | ships truncated | `Dock fees rise after the second horn.` |
| New discovery | none | none |

Frontier Gate calibration reread:

| | Before | After |
| --- | --- | --- |
| T13 | `… roster board, with…` | authored patrol-route sentence, complete |
| T19 | `… taking the northwest…` | `The missing patrol was last seen taking the northwest mud track past the crates.` |

A brief nothing-further line remains valid when no authored inspectable text exists.

## 11. Regressions Checked

Preserved:

- Immediate untargeted observe may remain nothing-new.
- Targeted observe may repeat a previously seen fact.
- Empty listen does not pull visual stock.
- Visual presence does not imply speech.
- Local walking remains `custom`; listen remains perception.
- Observe fallback still owns observation fallback.
- Refusal grammar (`from what I know`) remains intact.
- First authored inspect/discover still surfaces the authored fact.
- Repeated investigation does not mint a second clue.

Unrelated reds not absorbed:

- `test_transcript_runner_repeated_interruption_beat_forces_progression` still emits `Tavern Runner mutters, "Word is,"` plus interruption stock. This is the known PR-AI speaker/catalog residue, not `already_searched`.
- `test_social_exchange_emission.py::test_final_emission_passive_pressure_restores_recent_suspicious_figure_from_weak_atmosphere` failed on an unrelated social-pressure fixture.

## 12. Intentionally Deferred Residue

- Later untargeted look-around can still re-emit gate stock after intervening social/investigate turns. Immediate repeat remains fixed. Do not start a seen-facts campaign.
- Live model can still invent a time, count, price, or redirect on social absence.
- Opening / replay `mutters` / `"Word is,"` can still appear. Do not reopen PR-AI without new causal evidence.
- Some natural paraphrases still miss `notice_board`.
- Follow-up paraphrases that do not overlap an owned topic can still refuse.
- `"Gate Serjeant"` can resolve to `gate_guard`.
- Post-return observe can still bleed prior-scene geography.
- Unresolved travel can still be narrated as scene stock.
- Evaluator lexical false negatives on quiet listen and nothing-new.
- `"The guard says"` generic absent-speaker label.
- Some ordinary actions still resolve `kind=None`.
- Protected-replay baseline refresh.

## 13. Recommended Next Action

Highest-leverage remaining ordinary-play defect: live-model invention of a time, count, price, or redirect when the engine already has a correct grounded social absence.

Do not reopen PR-AT realization, PR-AS relevance, PR-AR grounding, PR-AQ typing, PR-AP grammar, PR-AO provenance, or PR-AI speaker ownership unless new evidence shows they cause that invention.

## 14. Git / Worktree State

Branch: `feature/product-realization` at checkpoint `4c0a454`, plus uncommitted PR-AS and PR-AT work.

Not committed. Not pushed.

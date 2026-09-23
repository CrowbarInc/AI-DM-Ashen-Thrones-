# PR-AU — Grounded Social Absence and Live-Model Non-Invention

Date: 2026-09-21
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

## 1. Executive Summary

PR-AU repaired the remaining ordinary-play failure where the engine already had a correct grounded social absence, then live-model realization invented an unsupported price, time, count, identity, or redirect.

The engine decision was already correct: `topic_revealed` is empty, the answer candidate is `refusal`, and `realize_authored_knowledge_answer` returns none. Realization was not. `apply_authored_knowledge_realization_to_gm` only preserved authored facts. On absence it returned the live-model prose unchanged, and the question hint still invited an “answer.”

No stew price, board-reader history, patrol schedule, economy, or new knowledge store was added. Existing authored-knowledge realization now fail-closes invented concrete facts into the existing social-ownership catalog. Natural absence phrasing that does not invent a fact is kept.

## 2. Reproduction Evidence

Deterministic isolation (`development/tmp/prau_social_absence_isolation.py`) on a kiln-yard night porter, before the repair:

| Case | Dimension | Engine before realization | Live-model prose | After `apply_authored_knowledge_realization_to_gm` |
| --- | --- | --- | --- | --- |
| mash cost | quantity | `topic_revealed=None`, `reply_kind=refusal`, authored=None, candidate=`refusal` | “Two coppers a ladle…” | unchanged invention |
| kiln-crew departure | time | same absence | “before dawn” | unchanged invention |
| brick count | quantity | same absence | “Seven dozen…” | unchanged invention |
| last slate reader | identity | same absence | “Mira from the dock office…” | unchanged invention |
| ledger keeper | identity | same absence | “Speak to the ward clerk…” | unchanged invention |
| natural absence | quantity | same absence | “I couldn't tell you.” | kept |
| authored mash | general | `topic_revealed=mash_exists`, `reply_kind=answer` | authored kettle fact | kept |

Prior-cycle live siblings matched the same class: PR-AP freeform T2 invented “before dawn” with `topic=None`; PR-AS T12 stew-cost already used the catalog refusal and was not this defect.

## 3. Causal Trace

```text
player asks an NPC a factual question
  → social target resolves
  → authored topic/relevance/sufficiency lookup
  → no revealable answer
  → kind=question, topic_revealed=None, reply_kind=refusal
  → realize_authored_knowledge_answer = None     ← correct semantic decision
  → hint still says: narrate an answer, refusal, evasion, or inability
  → live model authors a concrete price/time/count/identity/redirect
  → apply_authored_knowledge_realization_to_gm sees no authored facts
  → returns gm unchanged
  → invented world knowledge ships
```

Catalog absence phrasing already existed (`strict_social_ownership_terminal_fallback`). Upstream answer-contract repair uses ignorance lines, not invented prices. The live first-pass was the hole.

## 4. Engine State Immediately Before Realization

On every isolated invention case:

- `resolution.kind` = `question`
- `social.topic_revealed` = `None`
- `social.reply_kind` = `refusal`
- `social.npc_reply_expected` = `True`
- `realize_authored_knowledge_answer` = `None`
- `select_best_social_answer_candidate` = `{answer_kind: refusal, text: None}`
- Catalog ownership-terminal line already available and grammatical

The assumed grounded social absence **did** exist before realization.

## 5. First Incorrect Decision

After a correct grounded-absence decision, realization handed semantic authorship back to the live model.

Two cooperating omissions made that decision stick:

1. `apply_authored_knowledge_realization_to_gm` treated empty authored facts as “nothing to do,” so invented live prose survived.
2. The no-topic question hint invited an `answer` rather than constraining realization to refusal / uncertainty / inability.

## 6. Failure Classification

Price, time, count, identity, and unauthorized-redirect inventions **shared one causal boundary**.

| Class | Role |
| --- | --- |
| A | Grounded absence existed but was not propagated into realization |
| B | The live model was still permitted to semantically answer (hint + unowned prose) |
| C | Not the dominant cause. Catalog ignorance is already correct on this path. Integrity “about {hook}” residue is a sibling, not the inventor of prices/dawns |
| D | Not answer-contract repair. That path already emits ignorance, not invented facts |
| E | Provenance was present (`reply_kind=refusal`, empty topic). It was not consumed by realization |
| F | Engine *had* reached the grounded absence assumed by the replay/probe |

They did not require separate repairs.

## 7. Ownership

Existing owners reused:

- `game/social.py` — authored-knowledge realization, the dual owner of social absence
- `game/social_exchange_fallback_catalog.py` — existing ownership-terminal absence phrasing (lazy import only; no catalog rewrite)

No new owner. No second router. No new knowledge store. Observe fallback, perception grounding, and investigation provenance remain the owners of their paths.

## 8. Production Changes

Generic production only:

- When a social question/refusal has no authored answer, detect live-model prose that asserts an unauthored concrete fact (price, time, count, identity, or “ask/speak/go to …” redirect).
- Replace that prose with `strict_social_ownership_terminal_fallback`.
- Keep natural absence phrasing that does not invent a fact.
- Keep authored facts and authored redirects.
- Change the no-topic question hint so it no longer invites an answer.

No Frontier Gate nouns were added to the new helper block. No stew price, board history, patrol schedule, or economy.

## 9. Tests Added / Changed

Added `tests/test_grounded_social_absence_live_model_non_invention.py`:

1. Engine absence is present before realization.
2. Unauthored price cannot become an invented price.
3. Unauthored time cannot become an invented time.
4. Unauthored count cannot become an invented count.
5. Unauthored identity cannot become an invented person/event.
6. Unauthorized redirect cannot become an invented redirect.
7. Natural absence phrasing is kept.
8. HTTP invented-price path remains grounded through final realization.
9. Authored NPC knowledge still realizes.
10. Authored redirect still realizes.
11. Novel kiln-yard chimney/tiler question is protected.
12. PR-AP `"from what I know"` grammar remains intact.
13. Catalog absence is not itself classified as invention.
14. No Frontier Gate special case in the PR-AU helper block.
15. HTTP novel freeform absence is protected.

Updated `tests/test_social.py` to lock the new non-invention hint. No existing expected outputs were weakened to make invention acceptable.

## 10. Validation

| Suite | Result |
| --- | --- |
| New PR-AU fixtures | passed (15) |
| Isolation after repair | inventions replaced; natural absence and authored mash kept |
| Live kiln-yard probe `20260921T102708Z` | completed; no invented markers |
| PR-AP refusal grammar | passed |
| PR-AO investigation provenance | passed |
| PR-AT already-searched | passed |
| PR-AS observe relevance | passed |
| PR-AR perception grounding | passed |
| PR-AH grounded observation | passed |
| PR-AD authored knowledge | passed |
| PR-AN sufficiency / PR-AL relevance | passed |
| Bound-speaker / fallback validator / final-emission repairs | passed |
| Intent parser / referenced surface / PR-AQ typing | passed |
| `tests/test_social.py` | passed after hint-contract update |
| Full authoritative suite | not re-run |
| Frontier Gate 20-turn replay | not re-run; kiln-yard live probe used instead |

Structural PASS is not treated as semantic playability. Live GPT was used on the kiln-yard probe. Deterministic tests inject invented live-model prose into the same realization seam rather than only asserting catalog strings.

## 11. Semantic Before / After

Kiln-yard mash cost:

| | Before | After |
| --- | --- | --- |
| Engine | grounded refusal, no price | unchanged |
| Live invented “two coppers” | ships | `Night Porter says, "I do not know enough to answer that."` |
| Natural “I couldn't tell you.” | ships | ships |
| Authored kettle fact | ships | ships |

Live probe:

| Turn | Question | Result |
| --- | --- | --- |
| 1 | mash cost | catalog absence; no price |
| 2 | kiln-crew time | refusal; no dawn/schedule |
| 3 | brick count | catalog absence; no count |
| 4 | last slate reader | routed as inspect of the slate; nothing further; no Mira |
| 5 | chimney flue / tiler count | catalog absence; no identity or count |
| 6 | what sits on the brazier | authored mash fact |

## 12. Novel / Generalization Probe

Kiln-yard vocabulary (night porter, mash, tally slate, chimney flue, tilers) is not Frontier Gate stew / patrol / board. The same authority boundary covered an arbitrary unauthored identity+count question without a new special case.

## 13. Regressions Checked

Preserved:

- Authored NPC knowledge still realizes.
- Authored redirects still realize when the engine actually has that fact.
- PR-AP `"from what I know"` hedge remains intact.
- PR-AO investigation non-invention remains intact.
- PR-AT `already_searched` realization remains intact.
- PR-AS / PR-AR grounding remains intact.
- Refusals are not flattened to one `"I don't know."` line. Natural absence may stand; catalog variety remains when invention is replaced.

Known unrelated red, not absorbed:

- `test_emission_quality_anyone_else_talk_to_manifests_preserves_redirect_not_fragment` still expects source `topic_pressure:last_answer:redirect` and receives `topic_pressure:last_answer`. Documented since PR-AO. Redirect *content* is preserved.

## 14. Intentionally Deferred Residue

- Integrity topic-hook can still fill `"I won't answer that about {token}"` with a movement or speaker token (`step`, `night`). That is not invented world knowledge. Do not expand this slice into `_question_content_tokens` repair without a dedicated cycle.
- `"who last read that tally slate"` can still route as inspect of the slate rather than a social question. The inspect is grounded absence; it is a routing sibling.
- Later untargeted look-around can still re-emit gate stock after intervening social/investigate turns.
- Opening / replay `mutters` / `"Word is,"` can still appear. Do not reopen PR-AI without new causal evidence.
- Some natural paraphrases still miss `notice_board`.
- `"Gate Serjeant"` can resolve to `gate_guard`.
- `"The guard says"` generic absent-speaker label.
- Some ordinary actions still resolve `kind=None`.
- Protected-replay baseline refresh.

Do not add a stew price, board-reader history, patrol schedule, or economy from this residue.

## 15. Recommended Next Action

Highest-leverage remaining ordinary-play defect on the same social-absence path: integrity topic-hook tokens (`about step`, `about night`) rather than live-model invention of facts.

Do not reopen PR-AU absence fail-closed, PR-AT truncation, PR-AS relevance, PR-AR grounding, PR-AP grammar, or PR-AO provenance unless new evidence shows they cause that hook.

## 16. Git / Worktree State

Branch: `feature/product-realization` at checkpoint `4c0a454`, plus uncommitted PR-AS, PR-AT, and PR-AU work.

Not committed. Not pushed.

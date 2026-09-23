# PR-AV — Grounded Refusal Topic-Hook Integrity

Date: 2026-09-21
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

## 1. Executive Summary

PR-AV repaired the remaining grounded-social-refusal defect where an integrity topic hook selected a movement, temporal, speaker, or otherwise non-topic token and produced player-facing prose such as `"I won't answer that about step"` and `"I won't answer that about night"`.

The social refusal decision was already correct: `topic_revealed` is empty, the answer candidate is `refusal`, and no authored fact exists. The hook used to contextualize that refusal was not. `_integrity_topic_hook` treated the first leftover echo token from the whole player utterance as the semantic subject.

`step` and `night` shared that cause. They did not require separate repairs. Novel movement (`amble`, `sidle`) and novel temporal/address leftovers (`morning`, speaker `lamp`) failed the same way.

No new NLP/topic-model, social router, knowledge store, or Frontier Gate special case was added. Existing `_question_subject_tokens` and speaker-identity exclusion remain the semantic eligibility source. When no trustworthy topic exists, the catalog now degrades to an unhooked refusal instead of `about {token}`.

## 2. Reproduction Evidence

Existing live/replay evidence, then deterministic isolation (`development/tmp/prav_topic_hook_isolation.py`) before the repair:

| Source | Player | Engine | Hook | Player-facing |
| --- | --- | --- | --- | --- |
| PR-AS replay T14-region | I step back to the tavern runner and ask who last checked that board. | grounded refusal | `step` | `I won't answer that about step—not here.` |
| PR-AU kiln probe T2 | I ask the night porter when the kiln crew actually left. | grounded refusal, dimension=`time`, topic=`None` | `night` | `I won't answer that about night—not here.` |
| Isolation novel movement | I amble past the lamp clerk and ask how many barrels remain. | refusal | `amble` | `about amble` |
| Isolation novel temporal | I ask the lamp clerk this morning how many barrels remain. | refusal | `lamp` | `about lamp` |
| Isolation address-only | I ask the lamp clerk. | generic ask (may answer first topic) | `lamp` | would hook `lamp` on the integrity path |

Before-repair token state for the known night case:

- content tokens: `night`, `porter`, `kiln`, `crew`, `actually`, `left`
- subject tokens excluding speaker: `kiln`, `crew`, `actually`, `left`
- speaker tokens: `night`, `night_porter`, `porter`
- `_integrity_topic_hook` = first content token = `night`
- authored knowledge = none
- answer candidate = refusal

Before-repair token state for the known step case:

- content tokens: `step`, `back`, `tavern`, `runner`, `last`, `checked`, `that`, `board`
- `_question_subject_tokens` already drops `step` as a movement generic
- `_integrity_topic_hook` still chose `step` because it did not use that helper

## 3. Causal Trace

```text
player asks an NPC a factual question, often with movement/address framing
  → social target resolves
  → no revealable authored answer
  → kind=question, topic_revealed=None, reply_kind=refusal   ← correct
  → live echo or integrity fallback needs a contextual refusal
  → _integrity_topic_hook(player_text)
       uses _question_content_tokens on the whole utterance
       takes hooks[0]
  → "step" / "night" / "amble" / "lamp" becomes {topic}
  → "I won't answer that about {topic}—not here."
```

`_question_content_tokens` is an echo-overlap helper. Including incidental words there is useful for overlap checks. It is not a topic selector.

Existing `_question_subject_tokens` already excluded movement verbs such as `step` and can exclude speaker identity (`night` from Night Porter). The integrity hook never called it, and even that helper still scans the whole utterance, so novel `amble` would survive unless the asked clause is isolated.

## 4. Token / Topic State at Each Stage

| Stage | Night case | Step case | Novel `amble` |
| --- | --- | --- | --- |
| Player utterance | kiln-crew departure; addressee is night porter | last-checker of the board; movement is step back | barrel count; movement is amble |
| Intent / dimension | question / time | question / identity | question / quantity |
| Speaker | night_porter | tavern_runner / lamp_clerk fixture | lamp_clerk |
| Authoritative topic | none | none | none |
| Echo content tokens | night first | step first | amble first |
| Subject tokens minus speaker | kiln, crew, … | board remains after dropping step | amble still present until span isolation |
| Selected hook before | night | step | amble |
| Selected catalog | integrity_refusal_boundary | same | same |

## 5. First Incorrect Decision

`_integrity_topic_hook` treated the first leftover `_question_content_tokens` survivor of the whole utterance as the semantic subject of the question.

That is the first incorrect decision. The refusal itself was not wrong. `_question_content_tokens` was not the owner to change.

## 6. Failure Classification

`step` and `night` **shared one causal mechanism**.

| Class | Role |
| --- | --- |
| E | Dominant. Fallback selection used an arbitrary surviving echo token (`hooks[0]`). |
| A | Contributing. Whole-utterance lexical extraction is broader than an asked subject. |
| B | How `step` / `amble` entered the candidate list (movement/action words). |
| C | How `morning` entered if the asked clause was not isolated (temporal frame). |
| D | How `night` / `lamp` entered (speaker/address terms). |
| F | Not loss of an authored topic. `topic_revealed` was already none. |
| G | Not a second system. One hook owner. |

They did not require separate repairs.

## 7. Ownership

Existing owners reused:

- `game/social_exchange_fallback_catalog.py` — `_integrity_topic_hook` and integrity refusal templates
- `game/social.py` — `_question_subject_tokens` and `_speaker_tokens_for_question_relevance` (eligibility, not a new extractor)
- `game/social_exchange_emission.py` — pass resolution into the existing hook call

`_question_content_tokens` in `game/gm.py` is unchanged. No second social router. No new knowledge store.

## 8. Production Changes

Generic production only:

1. Isolate the asked clause (after `ask*` and/or the question word / `about` phrase) so movement preambles, address, and frame-setting modifiers are not topic candidates.
2. Select a hook from that clause using existing subject-token eligibility plus speaker exclusion.
3. Prefer `about` nouns, determiner-nouns, and `how many/much` heads over leftover verbs.
4. If the ask-tail has no question word and no `about` phrase, return an empty hook.
5. If no trustworthy topic exists, emit an unhooked refusal (`I won't answer that—not here.`) rather than `about {token}` or `about that`.
6. Other integrity lines that need a grammatical pronoun still use `that` when no topic exists.

No hardcoded `step` or `night`. No growing replay blacklist. `_question_content_tokens` was not narrowed.

## 9. Tests Added / Changed

Added `tests/test_grounded_refusal_topic_hook_integrity.py`:

1. Known `about step` no longer hooks `step`.
2. Known `about night` no longer hooks `night`.
3. Novel movement `amble` / echo-path `sidle` cannot become the topic.
4. Novel temporal `morning` cannot become the topic.
5. Legitimate `about the tarred coils` still hooks `coils`.
6. Address-only ask degrades with no `about {token}` hook.
7. Grounded refusal does not invent the missing time/identity answer.
8. PR-AU price/time/count/identity/redirect non-invention remains intact.
9. PR-AP `"from what I know"` hedge remains intact.
10. Authored mash fact still realizes.
11. Authored redirect still realizes.
12. HTTP echo of the known night question does not emit `about night`.
13. New hook helper has no `step`/`night` special case and no Frontier Gate nouns.

No existing expected outputs were weakened to make a bogus hook acceptable.

## 10. Validation

| Suite | Result |
| --- | --- |
| New PR-AV fixtures | passed (16) |
| Isolation after repair | night→kiln, step→board, amble→barrels, morning→barrels, address-only→empty |
| PR-AU grounded-social-absence | passed |
| PR-AP refusal grammar | passed |
| PR-AO investigation provenance | passed |
| PR-AT already-searched | passed |
| PR-AS observe relevance | passed |
| PR-AR perception grounding | passed |
| PR-AQ physical-action typing | passed |
| PR-AH grounded observation | passed |
| PR-AD authored knowledge | passed |
| PR-AL relevance subject tokens | passed |
| Bound-speaker knowledge | passed |
| `tests/test_social.py` | passed |
| `tests/test_intent_parser.py` | passed |
| Integrity candidate / structured-echo tests | passed |
| Full authoritative suite | not re-run |
| Frontier Gate 20-turn replay | not re-run |

Known unrelated red, not absorbed: `test_final_emission_passive_pressure_restores_recent_suspicious_figure_from_weak_atmosphere`.

Structural PASS is not treated as semantic playability. The hook token is selected deterministically; the echo-path tests exercise the same integrity replacement the live model can trigger.

## 11. Semantic Before / After

| Player | Before | After |
| --- | --- | --- |
| I step back … who last checked that board. | about **step** | about **board** |
| I ask the night porter when the kiln crew actually left. | about **night** | about **kiln** |
| I amble past the lamp clerk and ask how many barrels remain. | about **amble** | about **barrels** |
| I ask the lamp clerk this morning how many barrels remain. | about **lamp** | about **barrels** |
| I ask the lamp clerk about the tarred coils. | speaker/movement leftover | about **coils** |
| I ask the lamp clerk. | about **lamp** | `I won't answer that—not here.` |

Engine absence is unchanged. Completeness now comes from a real asked subject or from dropping the hook, not from inventing an answer.

## 12. Novel / Generalization Probe

`artifacts/prav_grounded_refusal_topic_hook/freeform_probe.md`

Kiln-yard / cedar-wharf wording (`amble`, `sidle`, `morning`, `barrels`, `coils`, `lamp clerk`) is not Frontier Gate stew / patrol / notice-board calibration. The same asked-clause + eligibility boundary covered novel movement, novel temporal framing, a legitimate unseen topic, and an unhooked degrade.

## 13. Regressions Checked

Preserved:

- PR-AU fail-closed non-invention of price/time/count/identity/unauthorized redirect
- Natural absence phrasing that does not invent a fact
- Authored NPC knowledge
- Authored redirects when the engine actually has that fact
- PR-AP `"from what I know"` hedge
- Existing subject-token relevance matching
- Contextual refusal hooks when a legitimate topic exists
- Characterful catalog variety; refusals are not flattened to one `"I don't know."` line

## 14. Intentionally Deferred Residue

Unchanged from the prior handoff unless later evidence elevates them:

- `"who last read that tally slate"` routing as inspect
- Natural paraphrases such as `posted notices` missing `notice_board`
- Follow-up paraphrases without owned-topic/public-clue overlap
- `"Gate Serjeant"` resolving to `gate_guard`
- Later-turn observe stock restacking
- Post-return geographic bleed
- Local `"What's nearby?"` collapse
- Unresolved travel narrated as scene stock
- Quiet-listen / nothing-new evaluator lexical false negatives
- Generic `"The guard says"` absent-speaker label
- Ordinary actions resolving `kind=None`
- Interruption / `"Word is,"` catalog residue

Do not reopen PR-AU absence fail-closed, PR-AT truncation, PR-AS relevance, PR-AR grounding, PR-AQ typing, PR-AP grammar, PR-AO provenance, or PR-AI speaker ownership from this residue.

## 15. Recommended Next Action

Highest-leverage remaining ordinary-play residue after this hook repair: later-turn untargeted look-around restacking after intervening social/investigate turns.

Do not start a seen-facts / salience memory from that residue. Do not start pricing/economics.

No user decision is required.

## 16. Git / Worktree State

Branch: `feature/product-realization` at checkpoint `4c0a454`, plus uncommitted PR-AS, PR-AT, PR-AU, and PR-AV work.

Not committed. Not pushed.

# PR-AZ — Question-Form Observe Realization and Retry Ownership

Date: 2026-09-21
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

## 1. Executive Summary

PR-AY repaired local-presence classification. PR-AZ found that classification was not the later-turn owner.

When an addressable NPC was present, `"What's nearby?"` still parsed as `observe`, but sole-NPC interrogative binding treated any `?` as addressing that NPC. Dialogue-first reconstruction then set `kind=question`. Downstream `question_rule`, terminal retry, and anti-reset continuation rewrote a completed observation into social/catalog ignorance.

The first incorrect decision was `find_addressed_npc_id_for_turn`: information-seeking plus a sole present NPC bound the Night Porter before the local-observation guard in `is_directed_dialogue` could refuse.

This cycle did not reopen the PR-AY classifier. It preserved already-resolved observe ownership through routing, question-rule eligibility, terminal retry, and anti-reset continuation.

No nearby phrase list, second observation router, conversation-state stack, seen-facts memory, or salience engine was added.

## 2. Minimal Reproduction Matrix

Deterministic traces plus HTTP isolation on synthetic `ember_kiln` with Night Porter.

Before-repair evidence: `artifacts/praz_question_form_observe_retry_ownership/isolation/20260922T000105Z_isolation.md`

After-repair evidence: `artifacts/praz_question_form_observe_retry_ownership/isolation/20260922T000655Z_isolation.md`

Route trace: `artifacts/praz_question_form_observe_retry_ownership/isolation/route_trace.json`

| Case | Input sequence | Before kind / facing | After kind / facing |
| --- | --- | --- | --- |
| A | `"I look around."` | `observe` / kiln stock | unchanged |
| B | first-turn `"What's nearby?"` with NPC | `question` / Night Porter social ignorance | `observe` / kiln surroundings |
| C | later-turn `"I look around again."` | `observe` / nothing-new | unchanged |
| D | later-turn `"What's nearby?"` | `question` / social ignorance | `observe` / nothing-new |
| E | social, then `"What's nearby?"` | `question` / social ignorance | `observe` / nothing-new |
| F | inspect, then `"What's nearby?"` | `question` / social ignorance | `observe` / kiln surroundings |
| G | observe, then `"What's nearby?"` | `question` / social ignorance | `observe` / nothing-new |
| Contrast | `"Where did the missing patrol go?"` | `question` / social retry | unchanged social/question retry |
| Novel | `"What is visible in this area?"` | same steal as nearby | `observe` |

PR-AY HTTP tests used empty `addressables` and empty `world.npcs`, so they never hit the sole-NPC bind. Ordinary play (Frontier Gate, kiln with porter) did.

## 3. Resolved Intent / Action Before Retry

On the failing HTTP turns, freeform parse already emitted `observe` / `local_observation_question`.

`resolve_directed_social_entry` already refused social (`reason=local_scene_observation_query`).

`should_emit_observe_for_local_observation_parse` was true.

The turn was observe before routing steal, not after a classifier miss.

## 4. Observation Result Before Retry

Once observe was allowed to execute:

- First-turn unused stock: grounded current-scene description.
- Immediate or later untargeted reinspection: valid nothing-new (`Nothing new stands out from here.`).

Both are completed observations. Neither is an unanswered social question.

## 5. Scene-Stall / Unresolved-Question State

`question_resolution_rule_check` applied to any `?` and failed stock-bearing observe prose (`first_sentence_not_explicit_answer`) because kiln description does not start with an answer-starter and does not share `nearby`.

Nothing-new already passed that heuristic. Stock-bearing and nothing-new therefore diverged at question-rule, not at classification.

Scene-stall could also fire on later-turn observe (`momentum_due_without_progress`). It was not the first owner. After observe ownership was stolen, unresolved-question / social fallback won because they have higher retry priority.

After routing was repaired, after-social observe still produced kiln stock through terminal retry, then final-emission anti-reset replaced that stock with social emergency ignorance.

## 6. Retry / Question-Rule Causal Trace

Representative failing input: `"What's nearby?"` at `ember_kiln` with Night Porter present.

1. Player utterance: `"What's nearby?"`
2. `_looks_like_local_observation_question` = true (PR-AY intact)
3. `parse_freeform_to_action` = `observe` / `local_observation_question`
4. Canonical social entry = not social (`local_scene_observation_query`)
5. `find_addressed_npc_id_for_turn` bound `night_porter` because the roster had one NPC and the line contained `?`
6. `is_directed_dialogue` returned true before its local-observation guard
7. `choose_interaction_route` = `dialogue`
8. `_build_dialogue_first_action` emitted `kind=question`
9. Exploration observe never ran
10. `question_rule` treated the interrogative as unresolved / social-exchange
11. Deterministic retry fallback selected social catalog ignorance
12. After the routing repair, a later after-social path still executed observe, then `final_emission_gate:anti_reset_continuation_fallback` replaced grounded stock with `Night Porter says, "I do not know enough to answer that."`

## 7. First Incorrect Decision

`find_addressed_npc_id_for_turn` sole-NPC fallback: `_information_seeking_dialogue_line` is true for any `?`, so the only present NPC is treated as the addressee.

The first point where a semantically resolved observe request is treated as an unanswered social question merely because of interrogative form is that bind, consumed by `is_directed_dialogue`.

## 8. Ownership

Existing owners reused:

- `game/interaction_context.py` — do not sole-NPC-bind untargeted local observation
- `game/gm.py` — `question_resolution_rule_check` is ineligible after executed `observe`
- `game/gm_retry.py` — terminal retry preserves observe ownership
- `game/anti_reset_emission_guard.py` — anti-reset continuation of observe is nothing-new, not social emergency

No new router.

## 9. Stock-Bearing vs Nothing-New

They share the first owner: the sole-NPC interrogative steal. After observe is preserved, they differ only in presentation.

Nothing-new is a valid completed observation and must not become an excuse to seek a social answer. After repair, later-turn and after-social nearby realize nothing-new. First-turn unused stock still surfaces kiln facts.

## 10. Production Changes

Generic production only:

1. Sole-NPC information-seeking bind skips `_looks_like_local_observation_question`. Hailing and genuine knowledge questions still bind.
2. `question_resolution_rule_check` returns ineligible when `resolution.kind == "observe"`.
3. Terminal social retry is not selected for observe-owned turns. Observe perception fallback may still run under anti-reset suppress-intro. Direct-question uncertainty is not used to rewrite observe.
4. `local_exchange_continuation_fallback_line` returns the existing nothing-new observe line when the resolution is observe / `local_observation_question`.

No Frontier Gate nouns. No hardcoded `"What's nearby?"`. No question-rule global disable.

## 11. Tests Added / Changed

Added `tests/test_question_form_observe_realization_retry_ownership.py` (14):

1. PR-AY local-presence classification remains observe, including novel `"What is visible in this area?"`
2. Sole NPC does not address untargeted local observation; `"Where did the missing patrol go?"` still binds
3. Interrogative form alone does not make local observation directed dialogue
4. Question-rule does not apply after resolved observe (stock or nothing-new)
5. Genuine unresolved social/knowledge question still uses question-rule
6. `detect_retry_failures` does not flag resolved observe as unresolved
7. First-turn HTTP question-form observe stays observe
8. Later-turn HTTP question-form observe stays observe
9. After social, nearby is not rewritten into social ignorance
10. After investigation, nearby stays observe
11. After prior observe, novel question-form remains observe-owned
12. Stock-bearing question-form observe may still surface current-scene facts
13. Genuine unanswered question after observe still uses existing retry
14. Earshot / who-nearby / rules remain adjudication

## 12. Validation

| Suite | Result |
| --- | --- |
| New PR-AZ fixtures | passed (14) |
| Isolation after repair | nearby/question-form observe stays observe; after social/investigate/prior observe is not social ignorance; genuine patrol question still retries |
| PR-AY local-presence | passed (19) |
| Local-observation routing | passed |
| PR-AX geographic integrity | passed |
| PR-AW later-turn restack | passed |
| PR-AS observe relevance | passed |
| PR-AT already-searched | passed |
| PR-AR perception grounding | passed |
| PR-AQ physical-action typing | passed |
| PR-AH grounded observation | passed |
| Anti-reset emission guard | passed |
| Directed-social routing | passed |
| Question-rule / dialogue smoke | passed |
| Full authoritative suite | not re-run |
| Frontier Gate 20-turn live replay | not re-run |

Isolation used the real HTTP finalize path with stubbed GPT. Structural PASS is not treated as live-model playability.

## 13. Semantic Before / After

| Input | Before | After |
| --- | --- | --- |
| `"What's nearby?"` at kiln with porter | Night Porter social ignorance | grounded kiln surroundings |
| Later-turn `"What's nearby?"` | social ignorance | valid nothing-new |
| Nearby after asking the porter | social ignorance | valid nothing-new |
| Nearby after inspecting the grate | social ignorance | kiln surroundings |
| `"What is visible in this area?"` | same steal | observe |
| `"Who is nearby?"` | earshot adjudication | unchanged |
| `"Where did the missing patrol go?"` | social/question retry | unchanged |

Wording above is conceptual. Isolation after repair used lines such as `"In Ember Kiln Alcove, a cold kiln stands in a brick alcove"` and `"Nothing new stands out from here."`

## 14. Generalization Evidence

The repair is the relationship between resolved observe ownership, semantic completion, and retry/anti-reset eligibility. It does not depend on `nearby`, Frontier Gate, or kiln nouns.

Novel `"What is visible in this area?"` received the same observe owner and the same retry protection.

`"What can be perceived from where I stand?"` is still outside the PR-AY local-observation classifier. That is classification scope, not this retry owner. Do not reopen PR-AY from that paraphrase alone.

## 15. Regressions Checked

Preserved:

- PR-AY local-presence classification and earshot / who-nearby / rules adjudication
- PR-AX current-scene geographic authority
- PR-AW untargeted visual-observe stamp eligibility
- PR-AS nothing-new as a valid observation result
- PR-AR hidden-fact fail-closed
- PR-AQ local movement ≠ scene travel
- PR-AT already-searched complete authored sentence
- Genuine unanswered social/knowledge questions still use existing unresolved-question retry

## 16. Intentionally Deferred Residue

Leave these deferred unless later evidence elevates them:

- `"Is there a tavern nearby?"` earshot/NPC catalog misfire
- `"What can be perceived from where I stand?"` still outside the local-observation classifier
- Opening `Gate Guard mutters` / `"Word is,"`
- `"who last read that tally slate"` routing as inspect
- `posted notices` missing `notice_board`
- Follow-up paraphrases without owned-topic / public-clue overlap
- `"Gate Serjeant"` resolving to `gate_guard`
- Unresolved travel narrated as scene stock
- Evaluator lexical false negatives on quiet listen and nothing-new
- Generic `"The guard says"` absent-speaker label
- Ordinary actions such as `"I wait a moment."` resolving `kind=None`
- Unrelated social-pressure test reds

Do not reopen PR-AY local-observation classification, PR-AX geographic eligibility, PR-AW stamp eligibility, PR-AV topic-hook eligibility, PR-AU absence fail-closed, PR-AT truncation, PR-AS relevance comparison, PR-AR grounding, PR-AQ typing, PR-AP grammar, PR-AO provenance, or PR-AI speaker ownership unless new evidence shows they cause a remaining defect.

## 17. Recommended Next Action

Question-form observe realization/retry ownership is closed at the existing address-bind, question-rule, and anti-reset owners.

Highest-leverage remaining residue in the same lane: `"Is there a tavern nearby?"` place-existence knowledge still collapsing to earshot/NPC catalog. That is a different semantic class from untargeted local observation.

Do not start a seen-facts / salience memory. Do not start a general question-rule rewrite.

No user decision is required.

## 18. Git / Worktree State

Branch: `feature/product-realization` at checkpoint `4c0a454`, plus uncommitted PR-AS through PR-AZ work.

Isolation used `development/tmp/praz_isolation_runtime/` and did not reset canonical `data/` documents.

Not committed. Not pushed.

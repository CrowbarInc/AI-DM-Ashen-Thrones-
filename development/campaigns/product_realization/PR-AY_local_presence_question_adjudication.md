# PR-AY — Local-Presence Question Adjudication

Date: 2026-09-21
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

## 1. Executive Summary

PR-AY repaired the remaining ordinary-play defect after PR-AX: a natural local-presence question such as `"What's nearby?"` resolved as `adjudication_query` and collapsed to catalog NPC-presence ignorance even when the authoritative current scene already contained usable surroundings.

The first incorrect decision was the existing local-observation classifier treating untargeted copula+locality questions as non-observation. `"What's nearby?"` then matched adjudication's bare `\bnearby\b` earshot rule and answered `"No nearby NPC presence is currently established in this scene."`

Question-form local observation and imperative `"I look around."` are the same existing `observe` action. Adjudication remains the owner of earshot, who-is-here, distance, rules, and feasibility questions.

No nearby phrase list, second observation router, geography database, seen-facts memory, or salience engine was added. PR-AX geographic eligibility was not reopened.

## 2. Reproduction / Paraphrase Matrix

Deterministic traces plus HTTP isolation on synthetic `ember_kiln` / `brass_quay` / `cedar_wharf`.

Before-repair evidence: `artifacts/pray_local_presence_question/isolation/20260921T234523Z_isolation.md`

After-repair evidence: `artifacts/pray_local_presence_question/isolation/20260921T234919Z_isolation.md`

| Input | Before owner | Before facing | After owner |
| --- | --- | --- | --- |
| `"What's nearby?"` | `adjudication:perception_query` | catalog NPC ignorance | `observe` / `local_observation_question` |
| `"What's around here?"` | unparsed / GPT | incidental kiln fallback | `observe` / `local_observation_question` |
| `"What is around me?"` | unparsed / GPT | incidental kiln fallback | `observe` / `local_observation_question` |
| `"What can I see nearby?"` | already `observe` | kiln surroundings | unchanged owner |
| `"What is close by?"` | unparsed / GPT | incidental kiln fallback | `observe` / `local_observation_question` |
| `"What's in this area?"` | unparsed / GPT | incidental kiln fallback | `observe` / `local_observation_question` |
| `"What's around?"` | unparsed / GPT | — | `observe` / `local_observation_question` |
| `"What is near me?"` | unparsed / GPT | — | `observe` / `local_observation_question` |
| `"What's in my immediate surroundings?"` | unparsed / GPT | — | `observe` / `local_observation_question` |
| `"What is present in the immediate vicinity?"` (novel) | not local observation | — | `observe` / `local_observation_question` |

The catalog-ignorance collapse was specific to questions containing `nearby` that missed the local-observation classifier. Other paraphrases already leaked toward scene stock through unparsed GPT retry; they did not share the observe owner.

## 3. Contrast Cases

These remained outside local observation after the repair:

| Input | Owner |
| --- | --- |
| `"I look around."` | existing imperative `observe` |
| `"What do I see?"` / `"What stands out?"` | existing local-observation `observe` |
| `"Is anyone else in earshot?"` | `adjudication:perception_query` |
| `"Who is nearby?"` / `"Is anyone nearby?"` | `adjudication:perception_query` |
| `"How far away is he?"` | `adjudication:perception_query` |
| `"Do I need to roll Perception?"` | `adjudication:roll_requirement_query` |
| `"What actions are available?"` | `adjudication:state_query` |
| `"Can I sneak past without being seen?"` | `adjudication:action_feasibility_query` |
| `"I inspect the kiln grate."` / `"What's on the kiln grate?"` | `investigate` |
| `"I'll head to the brass quay."` | `scene_transition` |
| `"What's around the brass quay?"` / `"What's nearby the ember kiln?"` | not untargeted local observation |
| `"Is there a tavern nearby?"` | still `adjudication:perception_query` (deferred sibling) |
| `"Who last read that tally slate?"` | still `investigate` (deferred sibling) |

## 4. Causal Routing Trace

Representative input: `"What's nearby?"` at `ember_kiln` with authored lantern/ash facts.

1. Intent classification: `_looks_like_local_observation_question` required a perception-verb or happening/going-on pattern. Copula+locality (`what's` + `nearby`) missed.
2. `should_emit_observe_for_local_observation_parse` therefore returned false.
3. `parse_freeform_to_action` returned `None`.
4. Target/reference extraction never ran as observe.
5. `classify_adjudication_query` matched `\bnearby\b` and returned `perception_query`.
6. Current-scene visible facts were not consulted as surroundings.
7. Observation/perception ownership was never reached.
8. `resolve_adjudication_query` treated `nearby` as earshot roster presence.
9. Final realization: `"No nearby NPC presence is currently established in this scene."`

`"What can I see nearby?"` already matched the perception-verb class, so parse emitted observe before adjudication. That contrast proved the observe path already represented the needed semantics.

## 5. First Incorrect Decision

`_LOCAL_OBSERVATION_POSITIVE_RE` / `_looks_like_local_observation_question` returning false for untargeted current-surroundings questions that lack an explicit see/notice/spot verb.

The compounding second decision was `classify_adjudication_query` treating any question containing `nearby` as earshot/NPC presence. That is why only the `nearby` paraphrases produced catalog ignorance.

## 6. Failure Classification

| Class | Role |
| --- | --- |
| A | Yes. Intent classification treated local-presence questions as generic adjudication (or left them unparsed). |
| B | Not the first owner. Adjudication's nearby branch is earshot roster, not surroundings. Correct for `"Who is nearby?"`. |
| C | Partial. Observation already existed (`What do I see?`, `I look around.`) but was unreachable from copula+locality questions. |
| D | Yes, at classification: interrogative locality lost perception semantics. A later realization sibling remains: scene-stall / question-rule can still rewrite some later-turn question-form observe lines. |
| E | Not demonstrated as the first decision. Current-scene facts existed; they were never asked. |
| F | Catalog ignorance fired because adjudication owned the turn before observe could answer. |
| G | Not required. |

## 7. Ownership

Existing owner reused:

- `game/interaction_context.py` — `_looks_like_local_observation_question` locality-complement class
- `game/intent_parser.py` — existing `should_emit_observe_for_local_observation_parse` → `observe` / `local_observation_question`
- `game/adjudication.py` — exclude already-classified local observation from earshot
- existing observe fallback / PR-AX perception grounding for current-scene geography

No new nearby subsystem.

## 8. Does Adjudication Remain Involved?

Yes, for genuine procedural questions: earshot, who/anyone nearby, distance, roll requirements, available actions, and feasibility.

No, for untargeted current-surroundings questions. After repair, `"What's nearby?"` is observe. Adjudication is not a surroundings narrator.

Question-form local observation and imperative observation are the same `observe` action in the current architecture. Realization still has an independent question-resolution rule that can retry some later-turn question-form observe results; that is not this classification owner.

## 9. Production Changes

Generic production only:

1. `_LOCAL_OBSERVATION_POSITIVE_RE` now also matches untargeted `what` + copula + locality complements (`nearby`, `around here/me/us`, `close by`, `near me`, `here`, `in this/the/my (immediate) area/vicinity/surroundings`), with an optional `present/located/visible` prefix and a terminal lookahead so `"What's around the quay?"` does not match.
2. `classify_adjudication_query` returns `None` when the same local-observation classifier matches, so leftover `nearby` is not dual-classified as earshot.

No Frontier Gate nouns. No phrase list of exact nearby questions. No stamp-eligibility change. No geographic-authority change.

## 10. Tests Added / Changed

Added `tests/test_local_presence_question_adjudication.py` (19):

1. `"What's nearby?"` is local observation, not adjudication.
2. Several natural paraphrases reach observe.
3. Novel `"What is present in the immediate vicinity?"` reaches observe.
4. HTTP nearby surfaces current-scene facts, not catalog NPC ignorance.
5. After A→B, nearby does not emit prior-scene geography.
6. Off-scene discovered clue text stays historical on nearby.
7. Invented fountain/tavern is not kept when kiln facts exist.
8. Barren-scene nearby does not invent a tavern.
9. `"How far away is the missing patrol?"` remains grounded adjudication ignorance.
10. Rules / earshot / who-nearby / state / feasibility remain adjudication.
11. Inspect, travel, and local walk keep existing owners.
12. Named-place `"What's around the brass quay?"` is not untargeted local observation.
13. Immediate nearby after observe remains PR-AS nothing-new.
14. Nearby is stamp-eligible untargeted observe (PR-AW).
15. Cedar Wharf generalization, not Frontier Gate wording.
16. Hidden facts still fail-closed on nearby.
17. PR-AX prior-scene geography classifier remains.
18. Generic engine files have no Frontier Gate or hardcoded `"What's nearby?"` special case.

Updated:

- `tests/test_local_observation_routing.py` positives/negatives
- `tests/test_post_return_observation_geographic_integrity.py`: nearby after travel now asserts observe without kiln bleed (PR-AX geographic integrity still holds; routing is no longer adjudication)

## 11. Validation

| Suite | Result |
| --- | --- |
| New PR-AY fixtures | passed (19) |
| Isolation after repair | all listed local-presence paraphrases are observe; kiln/quay/cedar facts surface; catalog NPC ignorance gone |
| Local-observation routing | passed |
| PR-AX geographic integrity | passed (19) |
| PR-AS observe relevance | passed (14) |
| PR-AW later-turn restack | passed (16) |
| PR-AT already-searched | passed (9) |
| PR-AR perception grounding | passed (29) |
| PR-AQ physical-action typing | passed (26) |
| PR-AH grounded observation | passed |
| Earshot adjudication contrast | passed |
| Directed-social routing | passed |
| Full authoritative suite | not re-run |
| Frontier Gate 20-turn live replay | not re-run |

Isolation used the real HTTP finalize path with stubbed GPT. Structural PASS is not treated as live-model playability.

## 12. Semantic Before / After

| Input | Before | After |
| --- | --- | --- |
| `"What's nearby?"` at kiln | catalog NPC ignorance | grounded kiln/alcove surroundings |
| `"What's nearby?"` after kiln → quay | catalog NPC ignorance | quay surroundings; no kiln lantern |
| `"What's nearby?"` at cedar | catalog NPC ignorance | cedar pilings / wharf; no invented tavern |
| `"What do I see?"` | observe surroundings | unchanged |
| `"Who is nearby?"` | earshot/NPC adjudication | unchanged |
| `"I inspect the kiln grate."` | investigate | unchanged |
| `"I'll head to the brass quay."` | scene travel | unchanged |

Wording above is conceptual, not canonical output. Isolation after repair used lines such as `"In Ember Kiln Alcove, a cold kiln stands in a brick alcove"` and `"In Brass Quay, a deserted quay leans over black water"`.

## 13. Generalization Evidence

Kiln lantern/ash, quay rings/ledger, and cedar pilings/hawser are not Frontier Gate watchers/serjeant calibration. The locality-complement class, not an enumerated phrase list, owns the repair. Novel `"What is present in the immediate vicinity?"` received the same observe owner. Production files contain no `frontier_gate` special case and no hardcoded `"What's nearby?"`.

## 14. Regressions Checked

Preserved:

- PR-AX current-scene geographic authority and off-scene historical clues
- PR-AW untargeted visual-observe stamp eligibility
- PR-AS immediate untargeted nothing-new
- PR-AR hidden-fact fail-closed
- PR-AQ local movement ≠ scene travel
- PR-AT already-searched complete authored sentence
- Earshot / who-nearby / rules / feasibility adjudication
- Targeted inspect and scene travel

## 15. Intentionally Deferred Residue

Leave these deferred unless later evidence elevates them:

- Later-turn question-form observe can still be rewritten by scene-stall + `question_rule` into social ignorance (`"The guard says, I do not know enough to answer that."`). Immediate nearby after observe remains nothing-new. This is realization/retry, not the PR-AY classifier.
- `"Is there a tavern nearby?"` still matches adjudication `nearby` as NPC presence.
- Opening `Gate Guard mutters` / `"Word is,"`
- `"who last read that tally slate"` routing as inspect
- `posted notices` missing `notice_board`
- Follow-up paraphrases without owned-topic / public-clue overlap
- `"Gate Serjeant"` resolving to `gate_guard`
- Unresolved travel narrated as scene stock
- Evaluator lexical false negatives on quiet listen and nothing-new
- Generic `"The guard says"` absent-speaker label
- Ordinary actions such as `"I step back… and wait"` resolving `kind=None`
- Unrelated social-pressure test reds

Do not reopen PR-AX geographic eligibility, PR-AW stamp eligibility, PR-AV topic-hook eligibility, PR-AU absence fail-closed, PR-AT truncation, PR-AS relevance comparison, PR-AR grounding, PR-AQ typing, PR-AP grammar, PR-AO provenance, or PR-AI speaker ownership unless new evidence shows they cause a remaining defect.

## 16. Recommended Next Action

Local-presence classification collapse is closed at the existing local-observation owner.

Highest-leverage remaining residue in the same lane: later-turn question-form observe realization (scene-stall / unresolved-question retry). That is not this classifier and is not PR-AX geographic bleed.

Do not start a seen-facts / salience memory. Do not start a general intent-parser or question-rule rewrite without isolation.

No user decision is required.

## 17. Git / Worktree State

Branch: `feature/product-realization` at checkpoint `4c0a454`, plus uncommitted PR-AS through PR-AY work.

Isolation used `development/tmp/pray_isolation_runtime/` and did not reset canonical `data/` documents.

Not committed. Not pushed.

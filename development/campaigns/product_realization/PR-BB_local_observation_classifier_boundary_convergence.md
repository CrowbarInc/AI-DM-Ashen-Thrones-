# PR-BB — Local-Observation Classifier Boundary and Convergence

Date: 2026-09-21
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

## 1. Executive Summary

PR-BB was a defect investigation and a convergence check. Production change was not presumed.

The known leftover sentence `"What can be perceived from where I stand?"` is a passive, abstract construction. It does not by itself reveal a missing observation category. Ordinary look-around and question-form surroundings language already reached existing `observe`.

The compact family probe did find one small shared gap adjacent to that leftover: first-person `can` plus perception verbs the classifier already recognized on the `do`/`does` branch (`perceive`, `observe`). Those lines missed, then collapsed to action-feasibility ("I need a more concrete action…") or, with a sole present NPC, social steal.

That family was repaired by composing existing signals at the existing local-observation classifier. The known passive sentence remains unsupported on purpose.

The local-observation classifier is sufficiently converged for Product Realization. Further look-around paraphrase work is not recommended.

## 2. Known-Failure Trace

Representative input: `"What can be perceived from where I stand?"` at synthetic `ember_kiln`.

Before-repair evidence: `artifacts/prbb_local_observation_boundary/probe/20260922T004000Z_family.json`

1. Parser / `OBSERVE_PATTERNS`: no `look around` / `scan` / `survey` hit. Result `None`.
2. `_looks_like_local_observation_question`: `?` present; exclude regex does not fire; `_LOCAL_OBSERVATION_POSITIVE_RE` misses.
3. Why the positive pattern misses, in order:
   - `what do/does I|we|he|she|they see|notice|…|perceive` requires an active `do`/`does` actor. The line is passive `can be perceived`.
   - `what can I|we|he|she|they see|make out|discern|spot|notice` requires a first-person/pronoun actor. The actor is missing, and `perceive` was not on the `can` list.
   - `from here|there|this spot, what can I see` requires the viewpoint clause first. Here it is trailing `from where I stand`.
   - Copula+locality (`what's nearby` / `in my surroundings`) does not match `what can be`.
4. `should_emit_observe_for_local_observation_parse`: false.
5. Action/intent: unparsed freeform.
6. Adjudication: empty-scene `_FEASIBILITY_OPENER` (`can …`) → `action_feasibility_query` → `"I need a more concrete action or target to resolve that procedurally."`
7. Social: no vocative. With Night Porter, sole-NPC information-seeking bind fires because the local-observation guard never applied. `is_directed_dialogue` true; route `dialogue`.
8. Fallback / final semantic outcome:
   - empty scene: procedural feasibility refusal, not surroundings;
   - NPC present: social ownership steal.

The first incorrect decision for this exact sentence is the positive local-observation pattern rejecting a passive, actorless perception question. That decision is accepted. The sentence is not ordinary play language.

## 3. Compact Semantic-Family Matrix

These phrases are diagnostic examples, not a production table.

| Input | Naturalness | Before owner | After owner |
| --- | --- | --- | --- |
| `"I look around."` | A | existing imperative observe | unchanged |
| `"What do I see?"` / `"What can I see?"` / `"What's around me?"` | A | existing observe | unchanged |
| `"What do I perceive?"` | B | already observe (`do` + perceive) | unchanged |
| `"What can I perceive?"` | B | feasibility / social steal | observe |
| `"What can I perceive around me?"` | B | same | observe |
| `"What can I perceive from here?"` | B | same | observe |
| `"What can I observe?"` | B | same | observe |
| `"What can I observe around me?"` (novel) | B | same | observe |
| `"What can we perceive from here?"` | B | same | observe |
| `"From where I stand, what can I see?"` | B | already observe (`what can I see`) | unchanged |
| `"What can be perceived from where I stand?"` | C | feasibility / social steal | accepted miss |
| `"What can be seen from here?"` | B passive | same residual path | accepted miss |
| `"What is visible here?"` | B | already observe | unchanged |
| `"What is visible from here?"` | B | unparsed / social | accepted miss |
| `"Describe my surroundings."` | B | unparsed | accepted miss |
| `"I look at my surroundings."` | A/B | existing investigate (`look at`) | unchanged; different owner |
| `"Who can see me?"` / `"What does the guard perceive?"` | contrast | not local observation | unchanged |
| `"Can I hear anything?"` | contrast | feasibility, not visual observe | unchanged |
| `"Is there a tavern nearby?"` | contrast | PR-BA place-existence | unchanged |
| `"Who is nearby?"` | contrast | person-presence | unchanged |
| `"How far away is the quay?"` / `"Can I get there before dark?"` | contrast | distance / feasibility | unchanged |

A = ordinary player language. B = plausible but formal/uncommon. C = artificial / adversarial.

## 4. Naturalness and Practicality

The known leftover is class C. Players who want that meaning already have working A-class lines: `"I look around."`, `"What do I see?"`, `"What's around me?"`, `"What's nearby?"`. Even the same deictic, used with working grammar, already worked: `"From where I stand, what can I see?"`.

The `can` + already-known perception-verb cluster is class B. In this game it is practical because Perception-skill language is a real player register. It is not theoretical completeness.

Passive `"What can be seen from here?"` and imperative `"Describe my surroundings."` are also class B, but they failed for different grammar reasons and have working A-class equivalents. They were not treated as the same family.

## 5. First Incorrect Decision

Two different first decisions, not one:

1. **Accepted for the known sentence.** Passive `what can be perceived` drops the player actor and the trailing `from where I stand` is not a copula-locality complement. This is uncommon grammar, not a missing category.
2. **Repaired shared family.** `_LOCAL_OBSERVATION_POSITIVE_RE`'s `what can I|we|he|she|they` verb list omitted `perceive` and `observe`, which the adjacent `do`/`does` branch already treated as observation verbs. `"What do I perceive?"` already worked; `"What can I perceive?"` did not.

Compounding after either miss: adjudication's bare `can I` / `can …` feasibility opener, and PR-AZ's sole-NPC `?` bind, which only skip classified local observation.

## 6. Existing Classifier Capabilities

Before this cycle the classifier already knew:

- perception verbs on `do`/`does`: see, notice, spot, hear, make out, observe, perceive;
- first-person `can` + a shorter visual list: see, make out, discern, spot, notice;
- copula + current-locality complements (PR-AY);
- leading `from here` / `from this spot` viewpoint clauses;
- named-NPC / role perception exclusions;
- place-existence exclusion (PR-BA);
- executed-observe social/question-rule protection (PR-AZ).

The missing composition was `can` + first-person + already-known visual perception verbs. No new vocabulary class, viewpoint system, or observation router was required.

## 7. Repair-Threshold Decision

Repair **was** warranted for the `can` + known-perception-verb family:

- multiple reasonably natural formulations failed;
- they failed for one shared classifier reason;
- the correct owner is existing `observe`;
- a one-alternation generalization covers the family;
- contrast classes stay protected.

Repair was **not** warranted for the known passive sentence, for `"What can be seen from here?"`, for `"What is visible from here?"`, or for `"Describe my surroundings."` Those are uncommon or alternate grammar with working equivalents. Hardcoding the known sentence, enumerating passives, or adding a describe-imperative list would be classifier growth without a general semantic gain.

No-change was evaluated and rejected only for the `can` family: those lines did not fail safely. They became feasibility refusals or social ownership, not a quiet unknown. Ordinary A-class equivalents already worked, but Perception-skill `can I perceive` is close enough to ordinary play that the incomplete existing signal should be composed.

## 8. Production Changes

One semantic generalization in `game/interaction_context.py`:

The existing `what can I|we|he|she|they` perception-verb alternation now includes `observe` and `perceive`, the visual verbs already recognized on the `do`/`does` branch.

`hear` was not added to the `can` list. Listen remains outside this visual-observation expansion. `"What do I hear?"` already matched the older `do`/`does` branch and was left untouched.

No hardcoded `"What can be perceived from where I stand?"`. No observation-paraphrase dictionary. No new router, embeddings, geography store, or question-rule change.

## 9. Tests and Probes

Added `tests/test_local_observation_classifier_boundary.py` (14):

1. Imperative `"I look around."` remains observe.
2. Ordinary question-form observation remains observe.
3. `"What do I perceive?"` remains observe.
4. The `can` + known-verb family reaches observe.
5. Novel `"What can I observe around me?"` reaches observe.
6. The known passive sentence remains unsupported.
7. Player-current `"What can I perceive from here?"` does not bind a sole NPC.
8. NPC-perception contrasts stay outside the classifier.
9. Listen and reach-before-dark stay outside.
10. Person-presence, place-existence, and distance stay with adjudication.
11. Question-rule does not rewrite executed can-perceive observe.
12. HTTP `"What can I perceive?"` is observe, not feasibility or social ignorance.
13. HTTP `"What can I observe around me?"` generalizes at cedar, not Frontier Gate wording.
14. Generic engine files have no exact-phrase or Frontier Gate special case.

Updated `tests/test_local_observation_routing.py` positives (`What can I perceive?`, `What can I observe?`, `What can I perceive from here?`) and the accepted-miss negative.

Disposable probe: `development/tmp/prbb_local_observation_boundary_probe.py`.

## 10. Semantic / Generalization Evidence

The repair is the relationship between an existing first-person `can` frame and perception verbs the classifier already owned. It does not depend on `stand`, `from where`, Frontier Gate, or the known leftover sentence.

Repaired surfaces that do not share the known sentence's passive construction:

- `"What can I perceive?"`
- `"What can I perceive from here?"`
- `"What can I observe?"`
- `"What can I observe around me?"`
- `"What can we perceive from here?"`

Cedar HTTP uses `"What can I observe around me?"`. Production files contain no `frontier_gate` special case and no hardcoded known leftover.

## 11. Contrast Regressions

Preserved:

- PR-AZ executed-observe ownership and sole-NPC skip for classified local observation
- PR-AY locality-complement observe (`What's nearby?`, `What's around me?`)
- PR-BA undirected place-existence adjudication
- PR-AX current-scene geographic authority (geographic-integrity suite green)
- PR-AW untargeted visual-observe stamp eligibility
- PR-AS nothing-new as a valid observation result
- PR-AR / PR-AH grounded perception
- PR-AQ local movement ≠ scene travel
- NPC perception (`What does the guard perceive?`)
- Listen (`Can I hear anything?`)
- Distance / feasibility adjudication
- Directed-social routing and local-observation social-followup recovery

## 12. Validation

| Suite | Result |
| --- | --- |
| New PR-BB fixtures + routing | passed (23) |
| Family probe after repair | can+perceive/observe are observe; known passive still unsupported |
| PR-AY local-presence | passed |
| PR-AZ question-form observe | passed |
| PR-BA place-existence | passed |
| Local-observation followup recovery | passed |
| Directed-social routing | passed |
| PR-AX geographic integrity | passed |
| PR-AW later-turn restack | passed |
| PR-AS observe relevance | passed |
| PR-AT already-searched | passed |
| PR-AV topic-hook | passed |
| PR-AR / PR-AQ / PR-AH | passed |
| Destination binding | passed |
| Full authoritative suite | not re-run |
| Frontier Gate 20-turn live replay | not re-run |

HTTP isolation used the real finalize path with stubbed GPT. Structural PASS is not treated as live-model playability.

## 13. Validation Coverage Requested by the Cycle

| Item | Result |
| --- | --- |
| 1. Ordinary imperative look-around | observe via existing `OBSERVE_PATTERNS` |
| 2. Ordinary question-form observation | observe |
| 3. Perception-language observation | `What do I perceive?` already observe; `What can I perceive?` now observe |
| 4. Known leftover sentence | still not observe; documented accepted miss |
| 5. Novel perception formulation | `What can I observe around me?` observe |
| 6. Player-current viewpoint | `from here` / `around me` stay player observe; no sole-NPC bind |
| 7. NPC-perception contrast | guard/who-can-see-me stay outside |
| 8. Listen/auditory contrast | `Can I hear anything?` not local observation |
| 9. Person-presence contrast | `Who is nearby?` / `Is anyone nearby?` adjudication |
| 10. Place-existence contrast | `Is there a tavern nearby?` PR-BA adjudication |
| 11. Distance/feasibility contrast | quay distance and before-dark unchanged |
| 12. PR-BA nearby place-existence | suite green |
| 13. PR-AZ executed-observe ownership | question-rule ineligible; suite green |
| 14. PR-AY local-presence | suite green |
| 15. PR-AX geographic integrity | suite green |
| 16. PR-AW / PR-AS observation relevance | suites green |
| 17. PR-AR grounded perception | suite green |

## 14. Explicit Convergence Assessment

### A. Did this reveal a general semantic defect?

**Yes, a small one; not the defect implied by the leftover sentence.**

The leftover passive line is not a missing category. The adjacent `can` + already-known perception-verb inconsistency was a real, shared, compose-from-existing-signals gap.

### B. Was production code changed?

**Yes.** One verb-list composition at the existing local-observation classifier.

### C. If changed, what semantic family was repaired?

First-person (or existing pronoun-actor) `can` questions that use visual perception verbs the classifier already treated as observation on the `do`/`does` branch.

### D. If unchanged, why is the residual miss acceptable?

The known leftover remains unchanged and is acceptable:

- Natural alternatives already work, including `"From where I stand, what can I see?"`.
- Failure is unparsed, then empty-scene feasibility or generic unrecognized-`?` social bind. It does not invent geography or corrupt perception authority.
- It does not affect ordinary likely player language.
- Supporting it would require new passive grammar or phrase enumeration.

### E. Is further local-observation classifier work recommended?

**NO — classifier is sufficiently converged for Product Realization.**

Remaining observation-shaped misses are low-value passive, `visible from`, or describe-imperative residue with working equivalents. Do not start another look-around paraphrase cycle because a creative sentence can still evade the pattern.

## 15. Intentionally Accepted Residue

Leave these deferred unless later evidence elevates them:

- `"What can be perceived from where I stand?"` and other actorless passives
- `"What can be seen from here?"`
- `"What is visible from here?"` (working equivalent: `"What is visible here?"`)
- `"Describe my surroundings."` (working equivalent: `"I look around."`)
- `"I look at my surroundings."` remaining `investigate` via existing `look at`
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

Do not reopen PR-BA place-existence ownership, PR-AZ retry ownership, PR-AY local-observation semantics, PR-AX geographic eligibility, PR-AW stamp eligibility, PR-AV topic-hook eligibility, PR-AU absence fail-closed, PR-AT truncation, PR-AS relevance comparison, PR-AR grounding, PR-AQ typing, PR-AP grammar, PR-AO provenance, or PR-AI speaker ownership unless new evidence shows they cause a remaining defect.

## 16. Recommended Next Action

The local-observation classifier is closed for Product Realization.

Do not select another observation paraphrase as the next cycle. Do not start a seen-facts / salience memory, geography database, or general intent-parser rewrite.

Highest remaining same-lane residue of a **different** owner: `"who last read that tally slate"` still routes as inspect rather than a social/history question. That is not this classifier.

No user decision is required.

## 17. Git / Worktree State

Branch: `feature/product-realization` at checkpoint `4c0a454`, plus uncommitted PR-AS through PR-BB work.

The family probe used in-memory defaults and did not reset canonical `data/` documents.

Not committed. Not pushed.

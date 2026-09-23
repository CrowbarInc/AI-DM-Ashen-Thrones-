# PR-BA — Nearby Place-Existence Knowledge Ownership

Date: 2026-09-21
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

## 1. Executive Summary

`"Is there a tavern nearby?"` is a place-existence / locality knowledge question. It was collapsing into earshot NPC-presence ignorance because adjudication treated any question containing `nearby` as a roster check, and because a sole present NPC could steal the undirected line into social.

The owner is existing adjudication (`perception_query`), narrowed by subject: person-presence stays earshot; a non-person existence+locality question answers from current-scene / current-exit authority or fails closed. It is not observe, not travel, and not a new geography system.

No tavern list, phrase table, second router, or place-knowledge subsystem was added.

## 2. Reproduction Trace

Representative input: `"Is there a tavern nearby?"` at synthetic `ember_kiln`.

Before-repair evidence: `artifacts/prba_nearby_place_existence/isolation/20260922T002700Z_before.json`

1. Parser: `None` (not observe; PR-AY already excludes this class).
2. Intent/action kind: unparsed freeform.
3. Extracted subject: none in the old path; the noun `tavern` was never inspected.
4. Locality interpretation: the word `nearby` alone.
5. Adjudication category: `perception_query` via `\bnearby\b`.
6. NPC/earshot eligibility: the nearby resolver treated the line as roster presence.
7. Current-scene evidence: kiln location / facts existed and were not asked.
8. Known destination evidence: kiln exit `"To the brass quay"` does not mention a tavern.
9. Authored knowledge: not consulted; this was not a social knowledge turn when no NPC was present.
10. Selected catalog: earshot empty-roster line.
11. Final realization: `"No nearby NPC presence is currently established in this scene."`

With Night Porter present, a second steal fired first: `find_addressed_npc_id_for_turn` sole-NPC `?` bind, then `is_directed_dialogue` `asks_for_information and has_present_character`. Classify returned `None`; the turn became social `kind=question`.

## 3. Semantic Contrast Matrix

| Input | Owner | Notes |
| --- | --- | --- |
| `"What's nearby?"` / `"What's around here?"` | existing observe | PR-AY / PR-AZ intact |
| `"Who is nearby?"` / `"Is anyone nearby?"` | person-presence / earshot | not place-existence |
| `"Is anyone else in earshot?"` | earshot | lists present NPC |
| `"Is there a tavern nearby?"` | place-existence adjudication | this cycle |
| `"Is there an inn around here?"` | same | locality without the word `nearby` |
| `"Are there stables close by?"` | same | |
| `"Is there a market in this area?"` | same | |
| `"Is there a charcoal lodge nearby?"` | same | novel type |
| `"How far is the tavern?"` | existing distance / feasibility adjudication | not observe |
| `"Can I reach the tavern before dark?"` | existing feasibility | |
| `"Do I need to roll Perception?"` | existing roll requirement | |
| `"Night Porter, is there a tavern nearby?"` | existing directed social | vocative preserved |

These phrases are diagnostic examples, not a production table.

## 4. First Incorrect Decision

`classify_adjudication_query` / `resolve_adjudication_query`: `\bnearby\b` selected earshot roster semantics without inspecting the asked subject.

Compounding decisions, in order:

1. The nearby resolver never distinguished person-presence from place-existence.
2. Sole-NPC information-seeking bind (and the later `is_directed_dialogue` present-character rule) treated any undirected `?` as addressing the only NPC. PR-AZ already skipped that bind for local observation; it did not skip place-existence.
3. Destination binding's information-question guard (`what|where|why|how|who|which|when`) missed `is there` / `are there`, so a matching exit could parse as travel.

The first point where `"nearby"` causes a place noun such as `tavern` to enter NPC/earshot semantics is the nearby earshot branch.

## 5. Ownership Determination

Traced existing owners:

| Candidate | Result |
| --- | --- |
| A. Authored scene/location | Evidence source, not the turn owner |
| B. Known destinations / travel | Evidence via existing `resolve_place_phrase_to_exit_target`; travel itself is the wrong action |
| C. Authored-knowledge realization | Social/NPC answers; undirected world questions must not require a speaker |
| D. Adjudication, narrower category | **Owner.** Same `perception_query` lane as earshot/distance, subject-discriminated |
| E. Current-scene observe | Explicitly not this class (PR-AY) |
| F. New geography / place store | Not required |

Place-existence is representable from current-scene identity, interactables, visible facts (after stripping present NPC name spans), and current-scene authored exits. Historical / off-scene knowledge is not nearby authority.

## 6. Authoritative Evidence

A place-existence question may answer only from:

- current scene `location` / `id` (the player is at that place);
- current-scene interactable labels / aliases;
- current-scene visible facts after present NPC names are removed, so `"tavern runner"` does not become a tavern;
- current-scene authored exits, through the existing destination matcher.

It must not answer from:

- a visited tavern in another scene;
- NPC title leftovers;
- GPT guesswork;
- invented distance, direction, visibility, price, schedule, or identity.

Absence uses the existing adjudication established/not-established grammar, not NPC-catalog ignorance and not a false “there is no tavern in the world.”

## 7. Directed vs Undirected

Undirected `"Is there a tavern nearby?"` is a world/adjudication knowledge question. Mere presence of one NPC does not address it.

`"Night Porter, is there a tavern nearby?"` keeps spoken-vocative social ownership. Existing social knowledge / PR-AU fail-closed still apply there.

`"Is there a porter nearby?"` may still bind as person-presence when the subject matches a present NPC head/role. `"tavern"` does not match `"Tavern Runner"` because the identifying head is `runner`.

## 8. Production Changes

Generic production only:

1. `game/interaction_context.py` — existence+locality subject extraction; person-language exclusion; present-NPC head/role match; sole-NPC bind skip for undirected place-existence.
2. `game/adjudication.py` — classify those questions as `perception_query`; resolve from current-scene / current-exit evidence or fail closed before earshot.
3. `game/interaction_routing.py` — `is_directed_dialogue` does not treat undirected place-existence as present-character social.
4. `game/scene_destination_binding.py` — information-question guard also recognizes `is there` / `are there`, so existence questions do not become travel.
5. `game/gm.py` — `question_rule` is ineligible after executed `adjudication_query` (same completion principle as PR-AZ observe).
6. `game/api.py` / `game/upstream_response_repairs.py` — adjudication `player_facing_text` is available to the prepared-answer fallback so a completed place-existence line is not replaced by a generic empty answer.

Player-facing wording reuses existing adjudication / answer-contract grammar (`No nearby … is currently established in this scene.`, `There is a … here.`, `There is a nearby destination: …`). Engine phrases such as `authoritative state` are not emitted; the sanitizer drops them.

No Frontier Gate nouns. No hardcoded `"Is there a tavern nearby?"`. No building-type list.

## 9. Tests Added / Changed

Added `tests/test_nearby_place_existence_knowledge_ownership.py` (24):

1. Tavern-nearby is place-existence, not earshot catalog.
2. Inn / stables / market / charcoal-lodge paraphrases share that owner.
3. `"What's nearby?"` remains observe.
4. `"Who is nearby?"` / `"Is anyone nearby?"` remain person-presence.
5. Earshot still lists a present NPC.
6. Rules / sneak / reach-before-dark remain adjudication.
7. `"How far is the tavern?"` is not observe and does not invent distance.
8. A place established by current-scene identity can be answered.
9. An authored exit is a known nearby destination, not travel.
10. A place known only as a visited other scene is not asserted nearby.
11. Unknown existence fails closed without invention.
12. Directed vocative keeps social ownership.
13. Sole NPC does not steal the undirected world question; genuine knowledge questions still bind.
14–20. HTTP: unknown, novel, current-scene, destination, elsewhere, observe/who, directed, sole-NPC, cedar generalization.
21. Visible-fact / interactable feature can establish current presence.
22. PR-AY / PR-AZ observe bind remains.
23. Question-rule does not rewrite completed adjudication.
24. Generic engine files have no Frontier Gate or exact-phrase special case.

## 10. Validation

| Suite | Result |
| --- | --- |
| New PR-BA fixtures | passed (24) |
| Isolation after repair | tavern/inn/stables/market/charcoal unknown; loft present; cellar destination; porter does not steal; vocative social; observe/earshot/distance/rules unchanged |
| PR-AZ question-form observe | passed (14) |
| PR-AY local-presence | passed (19) |
| Local-observation routing | passed |
| PR-AX geographic integrity | passed |
| PR-AW later-turn restack | passed |
| PR-AS observe relevance | passed |
| Destination-exit resolution | passed |
| PR-AU grounded social | passed |
| Directed-social routing | passed |
| Social-target / earshot authority | passed |
| Anti-reset emission guard | passed |
| PR-AV topic-hook | passed |
| PR-AT already-searched | passed |
| PR-AR / PR-AQ / PR-AH | passed |
| Full authoritative suite | not re-run |
| Frontier Gate 20-turn live replay | not re-run |

HTTP isolation used the real finalize path with stubbed GPT. Structural PASS is not treated as live-model playability. Live realization, when it participated, was checked semantically (no NPC catalog, no invented tavern/distance/price).

## 11. Semantic Before / After

| Input | Before | After |
| --- | --- | --- |
| `"Is there a tavern nearby?"` at kiln | NPC-presence ignorance, or Night Porter social steal | `No nearby tavern is currently established in this scene.` |
| `"Is there a charcoal lodge nearby?"` | same catalog | unknown, no lodge invented |
| `"Is there a salt loft nearby?"` at Salt Loft | catalog | `There is a Salt Loft here.` |
| same at Brine Cellar with loft exit | travel + catalog | `There is a nearby destination: Up to the salt loft.` |
| visited tavern, now at kiln | would have been catalog | still unknown; not “the tavern is nearby” |
| `"What's nearby?"` | observe | unchanged |
| `"Who is nearby?"` / earshot | person-presence | unchanged |
| `"Night Porter, is there a tavern nearby?"` | social | unchanged social |

Wording above is the actual deterministic adjudication line after engine-voice neutralization.

## 12. Generalization Evidence

The repair is the relationship between existence+locality, a non-person subject, and current-scene / current-exit authority. It does not depend on Frontier Gate, tavern, inn, market, or stables as special cases.

Novel `"Is there a charcoal lodge nearby?"` and cedar `"Are there drying racks close by?"` received the same owner. Salt Loft / Brine Cellar fixtures are not Frontier Gate calibration. Production files contain no `frontier_gate` special case and no hardcoded `"Is there a tavern nearby?"`.

## 13. Regressions Checked

Preserved:

- PR-AZ executed-observe ownership and question-rule exemption for observe
- PR-AY local-observation classification
- PR-AX current-scene geographic authority
- PR-AW untargeted visual-observe stamp eligibility
- PR-AS nothing-new as a valid observation result
- PR-AU grounded social non-invention where social knowledge participates
- PR-AV topic-hook eligibility
- PR-AT already-searched complete authored sentence
- Earshot / who-nearby / rules / feasibility / distance adjudication
- Directed vocative social ownership
- Authored-exit travel for actual travel intents

## 14. Intentionally Deferred Residue

Leave these deferred unless later evidence elevates them:

- `"What can be perceived from where I stand?"` still outside the PR-AY local-observation classifier
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
- Slight agreement in `"No nearby stables is currently established"`

Do not reopen PR-AZ retry ownership, PR-AY local-observation classification, PR-AX geographic eligibility, PR-AW stamp eligibility, PR-AV topic-hook eligibility, PR-AU absence fail-closed, PR-AT truncation, PR-AS relevance comparison, PR-AR grounding, PR-AQ typing, PR-AP grammar, PR-AO provenance, or PR-AI speaker ownership unless new evidence shows they cause a remaining defect.

## 15. Recommended Next Action

Place-existence / locality knowledge ownership is closed at the existing adjudication nearby owner, with destination-binding and address-bind guards to keep it from becoming travel or sole-NPC social.

Highest-leverage remaining residue in the same lane: `"What can be perceived from where I stand?"` still misses the local-observation classifier. That is PR-AY classification scope, not this place-existence owner.

Do not start a geography database, building directory, or seen-facts / salience memory.

No user decision is required.

## 16. Git / Worktree State

Branch: `feature/product-realization` at checkpoint `4c0a454`, plus uncommitted PR-AS through PR-BA work.

Isolation used in-memory / tmp HTTP seeds and did not reset canonical `data/` documents.

Not committed. Not pushed.

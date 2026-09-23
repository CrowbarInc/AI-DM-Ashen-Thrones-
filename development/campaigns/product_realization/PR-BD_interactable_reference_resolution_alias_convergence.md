# PR-BD — Interactable Reference Resolution and Alias Convergence

Date: 2026-09-22
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

## 1. Executive Summary

PR-BD was a defect investigation. Production change was not presumed.

Ashen Thrones does **not** have a general failure to resolve ordinary player names for authored interactables. Canonical names, authored aliases, and short head nouns already bind. `"I read the notice board."`, `"I look at the board."`, and `"I read the notice."` already reached `notice_board`.

The known replay phrase `"posted notices"` still misses that interactable. That miss is **not** a missing synonym for the Frontier Gate board. It is a leftover leading adjective. After ordinary plural stemming, `"I read the notices."` binds. `"I read the posted notices."` still fails because prefix matching keeps `posted`, which hits the opening-seed phrase `posted warning` as a visible fact.

The investigation did find one shared, safely generalizable defect in the **intended** flexibility layer: `_stem_token` stripped every `-es` ending. Silent-e plurals became a different stem (`notices` → `notic`, `stones` → `ston`, `slates` → `slat`, `chutes` → `chut`) and could not match their authored singular aliases.

That morphology is repaired. No `"posted notices"` alias was added. No synonym dictionary, embeddings, or noun-to-interactable promotion was added. Authored scene content is unchanged.

Interactable reference resolution is sufficiently converged for Product Realization. Further synonym / paraphrase cycles are not recommended.

## 2. Known-Failure Trace

Representative input: `"I read the posted notices."` at Frontier Gate.

Before-repair evidence: `artifacts/prak_referenced_surface/freeform_probe/20260920T121442Z_probe.md` (PR-AK recorded `authority=unsupported`). Current pre-repair runtime on canonical `frontier_gate.json` is slightly different because opening-seed facts are now classifier surfaces.

1. Token / reference extraction: `_INSPECT_TARGET_RE` extracts `posted notices`. Correct.
2. Target identification: `extract_inspection_target` returns that phrase. Correct.
3. Interactable candidate generation: `_interactable_surfaces` exposes `notice board`, `Notice board`, `notice`, `board`, `curfew notice`, `missing patrol warning`. Correct. Aliases are consulted.
4. Stemming: `content_tokens("posted notices")` produced `posted`, `notic`. **First insufficient decision.** `notices` should share a stem with authored alias `notice`.
5. Canonical-name / alias matching: prefix `posted notic` is not a contiguous authored phrase. No interactable hit.
6. Scene-local leftover prefix: `posted` matches opening-seed `"… a posted warning about a missing patrol."` **Second insufficient decision for the known phrase.** Authority becomes `authored_visible_feature`, not `notice_board`.
7. `_match_target_to_interactable` (id-slug only) also misses; `posted_notices` is not inside `notice_board`. This older helper is not the intended natural-language owner.
8. Downstream intent: `parse_freeform_to_action` returns `investigate` with raw target `posted notices` and `skip_unrelated_clue_discovery`.
9. Final realization: closer inspection restates the opening-seed fact and yields nothing further. Fail-closed. No invented object.

After the stem repair, step 4 yields `posted`, `notice`. Step 5 still has no contiguous `posted notice` surface. Step 6 still binds the leftover adjective to `posted warning`. The known phrase remains unbound. `"I read the notices."` now binds `notice_board`.

## 3. Authored Notice-Board Representation

From `data/scenes/frontier_gate.json`:

| Field | Value |
| --- | --- |
| Canonical ID | `notice_board` |
| Player-facing label | `Notice board` |
| Authored aliases | `notice`, `board`, `curfew notice`, `missing patrol warning` |
| Type | `investigate` |
| Inspectable text | clue `notice_patrol_route`: `"The missing patrol was last seen taking the northwest mud track past the crates."` |
| Other reference metadata | none (`name`, `description`, `readable_text` are absent) |

Scene prose also mentions the board and a **posted warning** in visible / opening / journal facts. That prose is a visible-feature surface, not an interactable alias.

Missing `"posted notices"` is not a code defect by itself. Content already supplied the ordinary aliases the resolver is meant to consume.

## 4. Reference-Resolution Architecture

Resolution currently uses:

| Mechanism | Used? | Role |
| --- | --- | --- |
| A. Canonical ID | Yes | `notice_board` → `notice board`; also the older id-slug helper |
| B. Authored display / label / name | Yes | primary player-facing phrase |
| C. Authored aliases | Yes | intended extension point for natural names |
| D. Lexical overlap with inspectable/clue text | No | clue text is realization, not a match surface |
| E. Scene-description references | Yes, secondarily | visible / opening / journal facts; not interactables |
| F. Token-phrase matching + stemming | Yes | generic flexibility over A–C |

The intended owner of natural-language flexibility is **C + F**: authored aliases / labels, matched by stemmed token phrases after determiner/stopword removal. Prefix lists shrink from the right so trailing clauses can fall away (`the board the serjeant keeps glancing at`). They do **not** drop a leading unauthored adjective.

`classify_referenced_surface` in `game/referenced_surface.py` is the inspect-time owner. Exploration honors that classification and refuses loose id-slug fallback once the classifier has bound a non-inspectable or unsupported surface. Social authored-knowledge uses a separate substring/slug helper and already treats `notice` as contained in `notices`.

## 5. Compact Multi-Interactable Matrix

These phrases are diagnostic examples, not a production table.

| Input | Scene / object | Naturalness | Before | After |
| --- | --- | --- | --- | --- |
| `"I read the notice board."` | notice_board | A | interactable | unchanged |
| `"I look at the board."` | notice_board | A | interactable | unchanged |
| `"I read the notice."` | notice_board | A | interactable | unchanged |
| `"I read the notices."` | notice_board | A | unsupported | interactable |
| `"I read the curfew notice."` | notice_board | A | interactable | unchanged |
| `"I read the posted notices."` | notice_board | B | visible feature via `posted` | accepted visible-feature residue |
| `"I inspect the wooden board."` | notice_board | B | unsupported | accepted residue |
| `"I inspect the grain hopper."` | grain_hopper | A | interactable | unchanged |
| `"I examine the chutes."` | feed chute | A | unsupported | interactable |
| `"I inspect the wooden hopper."` | grain_hopper | B | unsupported | accepted residue |
| `"I read the tariff slate."` | tariff_slate | A | interactable | unchanged |
| `"I read the slates."` | tariff_slate | A | unsupported | interactable |
| `"I examine the weathered milestone."` | milestone | A | interactable | unchanged |
| `"I look at the stones."` | milestone | A | unsupported | interactable |
| `"I look at the footprints."` | prints | A | interactable | unchanged |
| `"I inspect the rain / banners / stew."` | Frontier scenery | A | visible feature | unchanged |
| `"I inspect the crates."` | unauthored | A | unsupported | unchanged |
| `"I inspect the brass orrery."` | unauthored | A | unsupported | unchanged |
| `"I examine the weathered milestone."` | at Frontier Gate | A | unsupported | unchanged |
| `"I check the roster board."` | visible fact | A | visible feature | unchanged |

A = ordinary player language. B = plausible extra modifier / replay paraphrase.

## 6. First Incorrect / Insufficient Decision

Closest match: **broken silent-e plural stemming**, then a leftover leading adjective.

Not “aliases authored but not consulted.” They are consulted.

Not “canonical IDs disconnected from display terms.” `notice_board` and `Notice board` already match.

Not a missing general synonym engine. `"the board"` and `"the notice"` already worked.

The first insufficient decision on `"posted notices"` and `"the notices"` was `_stem_token("notices")` → `notic`. That is why the ordinary plural failed. The known replay phrase has an extra cause: after a correct `notice` stem, prefix search still prefers leftover `posted` over the head noun.

## 7. Semantic Family

A production issue exists for **silent-e plurals of authored names/aliases**.

Shared reason: the stemmer treated every `…es` word as an `-es` plural. That is wrong for `notice/notices`, `stone/stones`, `slate/slates`, `chute/chutes`.

That family is general, uses existing authored authority, and does not require fuzzy meaning.

`"posted notices"` is **not** that family by itself. It is an unauthored leading modifier plus a scene-prose token (`posted`). Equivalent leftovers (`wooden board`, `wooden hopper`, `muddy milestone`, `public notices`) also fail. That second cluster is accepted residue. A head-noun or suffix matcher would start binding landmark phrases such as `"the crate by the board"`.

## 8. System vs Content Ownership

| Question | Owner |
| --- | --- |
| Ordinary names and aliases | existing resolver + authored alias metadata |
| Silent-e / regular plurals | generic stemming (system) |
| Missing obvious content synonym | authored `aliases` (content) |
| `"posted notices"` | accepted residue, not content and not parser |

Content was **not** missing an obvious required alias. `notice` and `board` are already the ordinary extension. Adding `"posted notices"` would encode the replay phrase. A content alias is the correct extension point if a future scene wants a specific extra name; it is not required here.

The system already intended to normalize trivial morphology. Authors should not have to enumerate `notice`/`notices`, `stone`/`stones`, `slate`/`slates`.

## 9. Repair-Threshold Decision

**System repair warranted** for silent-e plural stemming:

- several ordinary references failed
- they failed across unrelated interactables
- they shared one first decision
- the repair uses authored names/aliases
- no fuzzy guessing
- incidental nouns stay non-interactable

**Content repair not warranted.** Do not add `"posted notices"`.

**No repair warranted** for leading-modifier paraphrases, including the known replay phrase. Safe fail-closed visible-feature / unsupported behavior is preferable to a suffix matcher.

## 10. Production Changes

One helper in `game/referenced_surface.py`:

`_stem_token` now:

- maps `-ies` → `y` as before
- strips `-es` only for `sses` / `xes` / `zes` / `ches` / `shes`
- otherwise strips a trailing `s` that is not `ss`

`notices`/`stones`/`slates`/`chutes` now share stems with their singular aliases. `boxes`/`watches`/`taxes`/`classes` still collapse correctly. `brass` is no longer cut to `bras`.

No hardcoded Frontier Gate phrase. No `notice_board` special case. No alias added. No second matcher.

## 11. Content Changes

None.

## 12. Tests and Probes

Added `tests/test_interactable_reference_resolution_alias_convergence.py` (13):

1. Stem unit cases for silent-e plurals and true `-es` plurals.
2. Canonical and ordinary notice-board references, including `"the notices"`.
3. `"posted notices"` remains unbound residue.
4. Leading-modifier paraphrases stay unbound on three scenes.
5. `slates` / `chutes` / `stones` bind unrelated authored interactables.
6. Incidental and unauthored nouns do not become interactables.
7. Off-scene interactables do not resolve locally.
8. Roster board remains a visible feature, not `notice_board`.
9. HTTP `"I read the notices."` realizes the authored patrol clue.
10. HTTP `"I read the slates."` realizes the mill tariff clue.
11. PR-AT already-searched still owns a repeated plural notice inspect.
12. Destination and social phrases are not stolen by notice-board matching.
13. Generic engine files contain no `posted notices` / `notice_board` special case.

Disposable probe: `development/tmp/prbd_interactable_reference_probe.py`.

After matrix: `artifacts/prbd_interactable_reference/probe/20260922T084500Z_after.md`.

## 13. False-Positive and Scene-Locality Protections

Verified after the stem change:

- Mentioned nouns (`rain`, `banners`, `stew`, `maize`, `nail`, `parchments`, `table`) stay visible features or unsupported. They do not become interactables.
- Unauthored objects (`brass orrery`, `glass kiln`, `brass lantern`, `ledger`) stay unsupported. No object is created.
- `crates` now stems to `crate` and still does not bind `notice_board`.
- Off-scene `milestone` at Frontier Gate, off-scene `notice_board` at the mill or milestone, and off-scene `hopper` at the gate stay local-negative.
- Hidden `brass token` remains hidden, not inspectable.
- Roster-board overlap still beats the short alias `board`.
- `mentioned noun ≠ automatically authored interactable` is unchanged.

## 14. Generalization Evidence

The repaired behavior is ordinary plural morphology over authored surfaces. It does not depend on Frontier Gate or `"posted notices"`.

Repaired surfaces that are not the known replay phrase:

- `"I read the notices."` → `notice_board`
- `"I read the slates."` → `tariff_slate` (mill loft)
- `"I examine the chutes."` → `grain_hopper` (mill loft)
- `"I look at the stones."` → `milestone` (old milestone)

Contrast: `"I read the posted notices."` and `"I inspect the wooden hopper."` remain unbound.

## 15. Contrast Regressions

Preserved:

- PR-AK referenced-surface classes (interactable / visible / hidden / abstract / unsupported)
- PR-AT already-searched complete authored inspectable sentences
- PR-AX current-scene geographic authority (off-scene objects do not resolve locally)
- PR-BC accepted undirected agent-history inspect residue
- Roster-board visible-feature overlap
- Destination binding (`Follow the missing patrol rumor.`)
- Directed social ask of the gate captain
- PR-BB / PR-BA / PR-AZ / PR-AY focused suites run for this cycle

## 16. Validation

| Suite | Result |
| --- | --- |
| New PR-BD fixtures | passed (13) |
| PR-AK referenced-surface | passed |
| Intent parser | passed |
| Exploration resolution | passed |
| PR-AT already-searched | passed |
| Authored-knowledge realization | passed |
| PR-BC agent-history | passed |
| PR-AM explicit world-action override | passed |
| PR-AX post-return geography | passed |
| PR-AZ question-form observe | passed |
| PR-BA place-existence | passed |
| PR-AY local-presence | passed |
| PR-BB local-observation | passed |
| Arrival destination | passed |
| After-repair matrix probe | `"the notices"` binds; `"posted notices"` remains residue |
| Full authoritative suite | not re-run |
| Frontier Gate 20-turn live replay | not re-run |

HTTP isolation used the real finalize path with stubbed GPT. Structural PASS is not treated as live-model playability.

## 17. Validation Coverage Requested by the Cycle

| Item | Result |
| --- | --- |
| 1. Canonical `notice_board` | binds interactable |
| 2. Player-facing `notice board` | binds interactable |
| 3. `"posted notices"` | accepted visible-feature residue |
| 4. Other natural notice-board refs | `the board`, `the notice`, `the notices`, `curfew notice` bind |
| 5–7. Other interactables | hopper/slate/milestone/prints canonical + natural + plural |
| 8. Singular/plural | silent-e plurals repaired; `boards`/`maps` already worked |
| 9. Incidental scene nouns | not interactables |
| 10. Unauthored object | unsupported; no instantiation |
| 11. Off-scene interactable | unsupported locally |
| 12. Legitimate inspect/read | HTTP plural notice and plural slate speak authored clues |
| 13. PR-AT already-searched | plural reread stays already-searched |
| 14. PR-AX current-scene authority | off-scene milestone/board/hopper do not bind |
| 15. PR-BC agent-history | suite green; undirected who-last-read untouched |
| 16. Destination and social | travel exit and captain ask are not stolen |

## 18. Explicit Convergence Assessment

### A. Is there a meaningful general interactable-reference defect?

**No as a general natural-description problem. Yes as a narrow morphological stemming defect, now repaired.**

When a player uses the authored name, an authored alias, or the ordinary singular/plural of those terms, the resolver usually identifies the object. Loose extra adjectives are not a Product Realization family.

### B. What is the intended extension mechanism for natural interactable names?

**Authored `label` / `name` / `aliases`, consumed by `classify_referenced_surface` token-phrase matching, with determiner removal and plural stemming.**

The older id-slug helper is a fallback, not the natural-language owner. Scene prose may acknowledge a mentioned noun as a visible feature; it does not mint an interactable.

### C. Is the known `posted notices` miss a system problem, content problem, or accepted residue?

**Accepted residue**, after the stem repair.

The ordinary plural `"the notices"` was the system problem and is repaired. `"posted notices"` remains an unauthored leading-modifier paraphrase that leftover-matches `posted warning`. Fail-closed. Do not add the replay phrase as an alias.

### D. Was production code changed?

**Yes.** `_stem_token` only.

### E. Was authored content changed?

**No.**

### F. If changed, what general behavior was improved?

Ordinary silent-e plurals of authored interactable names and aliases now resolve to those interactables.

### G. What false-positive protections were verified?

Incidental scenery nouns, unauthored objects, off-scene objects, hidden objects, and the roster-board overlap rule. No noun mentioned only in prose became an interactable.

### H. Is further interactable-reference work recommended for Product Realization?

**NO — sufficiently converged.**

Do not open another cycle because a new adjective+noun paraphrase can be invented. **DEFER** richer semantic/fuzzy reference resolution to a future capability; it is out of Product Realization scope.

## 19. Intentionally Accepted / Deferred Residue

Accepted on this owner:

- `"I read the posted notices."` / `"I read the posted notice."` remaining visible-feature via leftover `posted`
- Leading-modifier paraphrases (`wooden board`, `public notices`, `wooden hopper`, `muddy milestone`, `posted slate`)
- `"What do the notices say?"` remaining untargeted; the content-question owner still keys on `what does`, not this family
- Off-scene `"mud prints"` at Frontier Gate remaining a visible-feature overlap with `mud` in gate prose, not the milestone interactable

Leave these sibling items deferred unless later evidence elevates them:

- Opening `Gate Guard mutters` / `"Word is,"`
- Follow-up paraphrases without owned-topic / public-clue overlap
- `"Gate Serjeant"` resolving to `gate_guard`
- Unresolved travel narrated as scene stock
- Evaluator lexical false negatives on quiet listen and nothing-new
- Generic `"The guard says"` absent-speaker label
- Ordinary actions such as `"I wait a moment."` resolving `kind=None`
- Accepted undirected who-last-read inspect residue
- Accepted local-observation passive residue
- Unrelated social-pressure test reds

Do not reopen PR-BC agent-history ownership, PR-BB classifier convergence, PR-BA place-existence ownership, PR-AZ retry ownership, PR-AY local-observation semantics, PR-AX geographic eligibility, PR-AW stamp eligibility, PR-AV topic-hook eligibility, PR-AU absence fail-closed, PR-AT truncation, PR-AS relevance comparison, PR-AR grounding, PR-AQ typing, PR-AP grammar, PR-AO provenance, or PR-AI speaker ownership unless new evidence shows they cause a remaining defect.

## 20. Recommended Next Action

Interactable reference resolution is closed enough for Product Realization.

Do not select another notice-board synonym, alias list, or leading-modifier paraphrase as the next cycle. Do not start a fuzzy matcher, embeddings, or automatic noun-to-interactable promotion.

If the next Product Realization slice stays in AI Experience, pick a **different** remaining sibling owner. Do not automatically start from a leftover wording of this family.

No user decision is required.

## 21. Git / Worktree State

Branch: `feature/product-realization` at checkpoint `4c0a454`, plus uncommitted PR-AS through PR-BD work.

The matrix probe used in-memory / file-backed scene documents and did not reset canonical `data/` contents.

Not committed. Not pushed.

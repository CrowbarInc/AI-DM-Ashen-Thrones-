# PR-BC — Agent-History Question Ownership and Convergence

Date: 2026-09-21
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

## 1. Executive Summary

PR-BC was a defect investigation and a convergence check. Production change was not presumed.

Ordinary questions about who interacted with an object do **not** systematically collapse into inspection. `"Who wrote this notice?"`, `"Who put this here?"`, `"Who moved this crate?"`, and directed `"who last checked that board"` already left inspect.

The shared failure is narrower: an inspect/read verb plus a determiner and object (`read that/the/this X`) is treated as a player-performed world-object action before WH-relation or an explicit addressee can own the turn. That collision stole directed lines such as `"Ask the guard who read this."` and `"Night Porter, who last read the tally slate?"`.

Those directed cases were repaired at the existing social/inspect boundary. Explicit addressee plus a WH/ask information request now precedes a later inspect/read verb.

The known undirected line `"who last read that tally slate"` remains inspect. That inspect is grounded absence. No existing owner cleanly represents undirected object-history, and unbinding it would fall through to GPT invention or sole-NPC social steal. That residue is accepted. No last-reader, provenance, or object-history store was added.

This family is sufficiently converged for Product Realization. Further actor/history paraphrase work is not recommended.

## 2. Known-Failure Trace

Representative input: `"who last read that tally slate"` / `"Who last read that tally slate?"` at a synthetic kiln with an authored tally-slate interactable.

Before-repair evidence: `artifacts/prbc_agent_history_question/probe/20260922T015000Z_family.json`

1. Raw input contains a leading `who` (or `?`) and the verb `read` plus `that tally slate`.
2. Referenced-surface recognition: `_INSPECT_TARGET_RE` extracts `tally slate` because `read` is an inspect verb. `classify_referenced_surface` binds the authored interactable. The surface itself is inspectable.
3. Target extraction is therefore already inspection-shaped. The requested relation is `who` (identity/history), not content.
4. Question/WH detection: `_has_information_seeking_question` is true for leading `who` or `?`. `_is_information_seeking_clause` is true only when `?` is present. Social dimension is already `identity`.
5. Intent classification: `INVESTIGATE_PATTERNS` `re.search` matches `read` + target anywhere in the line. `parse_freeform_to_action` returns `investigate` / `tally_slate`.
6. Inspect eligibility: `recover_actionable_explicit_world_action` is skipped when the line is already a leading-WH/`?` question. That is not enough, because later exploration parse still investigates.
7. Social/adjudication eligibility: `_EXPLICIT_NON_SOCIAL_CONTINUITY_ESCAPE_RES` matches `read that/the/this`. `dialogue_intent_blocks_explicit_non_social_continuity_escape` only blocked a leading `I/we ask`. Vocative `"Guard, who last read…"` and `"Ask the guard who read this."` escaped social lock. Adjudication has no object-history category.
8. Referenced-surface result: authored interactable, inspectable. If the slate has inspectable text, the player is shown contents. If not, closer-looking yields nothing further. No last-reader is invented.
9. Final realization of the known undirected line: inspect / grounded absence or authored contents. The defect is ownership, not invention.

The first point where `tally slate` appears to dominate is actually later. The first incorrect decision is the verb `read` plus a determiner+object being treated as inspect/world-action before the `who` relation or addressee is considered. The noun is then bound as an inspectable target.

Directed compounding, same cause:

| Input | Before owner |
| --- | --- |
| `"Ask the guard who read this."` | `recover_actionable` inspect (`ask` without `?` was not information-seeking) |
| `"I ask the night porter who last read that tally slate."` | same actionable inspect |
| `"Guard, who last read this tally slate?"` | social escape + exploration inspect |
| `"Night Porter, who last read the tally slate?"` | same |

PR-AU already proved the directed identity question, when it *does* reach social realization, fail-closes invented names. HTTP routing was still inspect.

## 3. Compact Semantic Contrast Matrix

These phrases are diagnostic examples, not a production table.

| Input | Naturalness | Before owner | After owner |
| --- | --- | --- | --- |
| `"Read the tally slate."` | A | inspect | unchanged |
| `"What does the tally slate say?"` | A | content-question inspect | unchanged |
| `"Inspect the tally slate."` | A | inspect | unchanged |
| `"Look over the tally slate."` | A/B | inspect | unchanged |
| `"What's on the duty notice?"` | A | content-question inspect | unchanged |
| `"Who wrote this notice?"` | A | empty: unparsed; NPC: sole-NPC social | unchanged |
| `"Who put this here?"` / `"Who moved this crate?"` | A | same | unchanged |
| `"Who last checked that board?"` | A | empty: unparsed; NPC: social | unchanged |
| `"I step back … ask who last checked that board."` | A | directed social (PR-AN) | unchanged |
| `"Who last read the tally slate?"` | B | inspect | accepted inspect residue |
| `"Who read the tally slate?"` | A/B | inspect | accepted inspect residue |
| `"Has anyone read this?"` | A | inspect | accepted inspect residue |
| `"When was the tally slate last read?"` | B | empty: inspect; NPC: sole-NPC social | unchanged |
| `"Where did this notice come from?"` | A | empty: unparsed; NPC: social | unchanged |
| `"Night Porter, who last read the tally slate?"` | A | inspect | social identity |
| `"Ask the guard who read this."` | A | inspect | social identity |
| `"I ask the night porter who last read that tally slate."` | A | inspect | social identity |
| `"Ask the dock clerk who read this cargo manifest."` | A novel | inspect | social identity |
| `"I inspect the tally slate, then I ask who last read it."` | contrast | inspect first | unchanged inspect |

A = ordinary player language. B = plausible but formal/uncommon.

## 4. First Incorrect Decision

Closest match: **B**, with compounding **A**.

Inspect/world-object detection treats any utterance containing `read` + `the/this/that` + object as a request to inspect that object. WH semantics and addressee are considered only in narrower helpers (`_has_information_seeking_question`, `I/we ask` before escape). They do not win for vocative + WH or `ask X who …` without `?`.

Not C: `who` is recognized (`identity` dimension) and then loses to target binding.

Not D as the whole story: directed social already represents the relation. Inspect is the safest leftover owner only for **undirected** object-history, where no existing world-history category exists.

`tally slate` is not a special case. The same steal happens for `"Ask the guard who read this."` and a cedar cargo manifest.

## 5. Family / Convergence Assessment

Key question: do ordinary WHO-interacted-with-object questions systematically become inspect?

**No.**

They become inspect only when the historical predicate is also an inspect/read verb. `wrote`, `put`, `moved`, `checked`, and past-tense `inspected` do not hit `INVESTIGATE_PATTERNS` or the `read the/this/that` world-action escape.

That is a linguistic collision:

- player-performative inspect: `"Read the slate."`
- historical actor predicate: `"Who last read the slate?"`

The engine only owned the first meaning. The second is not a missing general agent-history category.

Repair was warranted for the **directed** half of that collision. It was not warranted for undirected `"Who last read the tally slate?"` as a new world-history owner.

## 6. Existing-Owner Determination

| Shape | Existing owner |
| --- | --- |
| Imperative / content inspect | referenced-surface investigation |
| Directed vocative or `ask X` + identity/time/location | existing social; dimension already `identity` / `time` / `location` (PR-AN, PR-AU) |
| Undirected WHO/WHEN/WHERE about an object | no clean owner. Adjudication has earshot, place-existence, feasibility, rules — not object-history. Unparsed GPT invents. Inspect fail-closes. |
| Sole present NPC | must not convert an undirected history question into dialogue (PR-BA / this cycle) |

Correct ownership and answer availability stay separate. Social identity may still realize grounded absence.

## 7. Knowledge / State Availability

Answering `"Who last read this?"`, `"Who moved this?"`, or `"Who wrote this?"` affirmatively would require event/history state Ashen Thrones does not own: last-reader, last-toucher, provenance, or NPC activity logs.

No such store was added. Authored kiln/cedar surfaces do not name a last reader. Directed social therefore fail-closes. Undirected inspect fail-closes. Neither invents identity, timestamp, or provenance.

## 8. Directed vs Undirected Behavior

- `"Who last read the tally slate?"` is an undirected world/history question. It stays inspect. A present Night Porter is recognized as a possible addressee and is **not** bound.
- `"Night Porter, who last read the tally slate?"` and `"Ask the guard who read this."` are directed social questions. They now stay social.
- `"I inspect the tally slate, then I ask who last read it."` still escapes to inspect because the world-object verb comes first.

Mere presence of one NPC does not convert the undirected history question into dialogue.

## 9. Repair-Threshold Decision

Repair **was** warranted for explicit-addressee + WH/ask information requests that embed an inspect/read verb:

- several ordinary directed formulations failed
- they shared one first decision
- existing social already owns the question
- genuine inspect/read/content questions remain inspect
- no historical world state is required

Repair was **not** warranted for undirected `"Who last read the tally slate?"`, `"Who read the tally slate?"`, or `"Has anyone read this?"`:

- they fail closed
- unbinding them has no world-history owner
- sending them to GPT risks invented identity (PR-AU)
- sending them to a sole NPC would violate undirected ≠ directed
- working directed equivalents exist (`ask … who last checked`, vocative + `who wrote`)

No exact-string, `tally slate`, `"who last read"`, or verb-enumeration table was added.

## 10. Production Changes

Two existing helpers now share one precedence:

**Explicit addressee + WH/ask information request, if it starts before the inspect/read verb, is not a world-object inspect.**

1. `game/interaction_context.py`
   - `addressed_information_request_starts_before` composes the existing vocative+WH pattern with `ask`/`question` + WH.
   - `dialogue_intent_blocks_explicit_non_social_continuity_escape` uses it so vocative/`ask` questions are not peeled off as inspect.

2. `game/intent_parser.py`
   - `looks_like_explicit_world_object_action` uses the same helper so `"Ask the guard who read this."` (no `?`) is not recovered as an explicit inspect.

No new intent category. No object-history database. No second router. No embeddings. No `question_rule` change.

## 11. Tests and Probes

Added `tests/test_agent_history_question_ownership.py` (19):

1. Imperative read/inspect remain investigation.
2. `"What does the tally slate say?"` remains content-question inspect.
3. Undirected `"Who last read the tally slate?"` remains inspect residue.
4. That undirected line does not bind a sole present NPC.
5. Empty-scene `"When was the tally slate last read?"` remains inspect residue.
6. `wrote` / `put` / `moved` / provenance questions are not investigation.
7. Vocative `who` + read is social.
8. `"Ask the guard who read this."` is social without `?`.
9. `"I ask the night porter who last read that tally slate."` is social.
10. Inspect-then-ask still escapes to world action.
11. Cedar `"Ask the dock clerk who read this cargo manifest."` generalizes.
12. HTTP imperative read still inspects and does not invent a reader.
13. HTTP undirected who-last-read stays inspect and does not invent a reader.
14. HTTP vocative who-read is social grounded absence.
15. HTTP cedar ask-who-read generalizes; no invented identity; no manifest contents as a fake answer.
16. HTTP directed `when` does not invent a timestamp.
17. HTTP directed provenance does not invent an origin.
18. Existing directed `"who last checked that board"` still binds social.
19. Generic engine files have no tally-slate / Frontier Gate special case.

Disposable probe: `development/tmp/prbc_agent_history_question_probe.py`.

Before: `artifacts/prbc_agent_history_question/probe/20260922T015000Z_family.json`
After: `artifacts/prbc_agent_history_question/probe/20260922T021200Z_after.json`

## 12. Generalization Evidence

The repaired boundary is addressee + requested WH relation versus player-performed inspect. It does not depend on tally slate, Frontier Gate, or the known replay sentence.

Repaired surfaces that are not the known undirected line:

- `"Night Porter, who last read the tally slate?"`
- `"Ask the guard who read this."`
- `"I ask the night porter who last read that tally slate."`
- `"Ask the dock clerk who read this cargo manifest."` (cedar, novel object and wording)

Contrast: `"Read the cargo manifest."` and `"Read the tally slate."` remain investigation.

## 13. Contrast Regressions

Preserved:

- PR-AT referenced-surface / `already_searched` complete authored inspectable sentences
- PR-AU grounded social absence / non-invention
- PR-AV refusal-topic integrity
- PR-AN dimension sufficiency (`who last checked that board` stays social absence, not neighboring board text)
- Objective 18a inspect/manipulate social-lock escape
- PR-AM explicit world-action override of stale social lock
- PR-BB local-observation classifier, including accepted passive residue
- PR-BA undirected place-existence
- PR-AZ executed-observe ownership
- Directed-social routing and destination binding
- Inspect-then-ask still inspects

## 14. Validation

| Suite | Result |
| --- | --- |
| New PR-BC fixtures | passed (19) |
| Family probe after repair | directed ask/vocative + read are social; undirected who-last-read remains inspect |
| Social-lock continuity escape | passed |
| Explicit world-action social override | passed |
| PR-AT already-searched | passed |
| PR-AU grounded social absence | passed |
| PR-AV topic-hook | passed |
| PR-AN question-dimension sufficiency | passed |
| Authored-knowledge realization | passed |
| PR-BB local-observation classifier | passed |
| Local-observation routing | passed |
| PR-AZ question-form observe | passed |
| PR-BA place-existence | passed |
| PR-AY local-presence | passed |
| Directed-social routing | passed |
| Destination binding | passed |
| Full authoritative suite | not re-run |
| Frontier Gate 20-turn live replay | not re-run |

HTTP isolation used the real finalize path with stubbed GPT. Structural PASS is not treated as live-model playability.

## 15. Validation Coverage Requested by the Cycle

| Item | Result |
| --- | --- |
| 1. `"Read the tally slate."` | inspect; authored contents; no invented reader |
| 2. `"What does the tally slate say?"` | content-question inspect |
| 3. `"Inspect the tally slate."` | inspect |
| 4. `"Who last read the tally slate?"` | undirected inspect residue; no invented identity |
| 5. Novel `who` + referenced-object relation | `"Ask the dock clerk who read this cargo manifest."` social |
| 6. `when` history question | empty undirected remains inspect; directed vocative is social absence, no invented time |
| 7. Provenance/origin | `"Where did this notice come from?"` is not inspect; directed HTTP does not invent origin |
| 8. Explicitly NPC-directed history | vocative / `ask` / `I ask` are social |
| 9. Undirected history with one NPC present | stays inspect; no sole-NPC bind |
| 10. Grounded absence when history is not authoritative | directed social absence; undirected inspect absence |
| 11. No invented identity | HTTP stubs rejected |
| 12. No invented timestamp | HTTP stubs rejected |
| 13. No invented provenance | HTTP stubs rejected |
| 14. PR-AT already-searched | suite green |
| 15. PR-AU grounded non-invention | suite green |
| 16. PR-AV refusal-topic integrity | suite green |
| 17. Existing directed-social routing | suite green; `"who last checked that board"` still social |

## 16. Explicit Convergence Assessment

### A. Is there a meaningful agent/history routing family?

**No as a general WHO-interacted family. Yes as a directed inspect-verb collision.**

Ordinary actor questions that do not embed `read`/`look at` already left inspect. The systematic steal was inspect-verb + object, including when the player was asking an NPC.

### B. Does existing architecture have an appropriate owner?

**Directed: existing social (identity/time/location).**
**Undirected object-history: no existing owner represents the relation cleanly.** Inspect is a fail-closed placeholder, not a correct semantic owner.

### C. Does answering require new historical state?

**Yes**, for an affirmative last-reader / last-mover / author / provenance answer.

**No**, for correct directed ownership plus grounded absence.

### D. Was production code changed?

**Yes.** Smallest existing social/inspect precedence: addressee + WH/ask before a later inspect/read verb.

### E. If changed, what general semantic boundary was repaired?

An explicitly addressed information question is not a player-performed inspect of a mentioned surface merely because the question uses an inspect/read verb.

### F. If unchanged, why is the residue acceptable?

The undirected known line remains inspect and is acceptable:

- Inspection fail-closes; it does not invent a reader.
- Ordinary non-`read` actor questions already route coherently.
- Directed equivalents now work.
- Unbinding undirected inspect would invent (GPT) or steal (sole NPC).
- Supporting it as world knowledge would require a history store or a new adjudication category.

### G. Is further work on this semantic family recommended for Product Realization?

**DEFER** — richer last-reader / provenance answers would require a future gameplay/world-state capability.

**NO** further Product Realization paraphrase cycle on this family. The directed collision is repaired. The undirected leftover is accepted residue. Do not open another who-read wording cycle.

## 17. Intentionally Accepted / Deferred Residue

Accepted on this owner:

- Undirected `"Who last read the tally slate?"`, `"Who read the tally slate?"`, `"Has anyone read this?"`
- Empty-scene `"When was the tally slate last read?"` remaining inspect via the bare `read` fallback
- Empty-scene `"Who wrote this notice?"` remaining unparsed/GPT (pre-existing; not this collision)
- `parse_social_intent` still capturing a long `"ask the X who …"` tail as a raw target string; canonical social entry supplies the NPC id

Leave these sibling items deferred unless later evidence elevates them:

- Opening `Gate Guard mutters` / `"Word is,"`
- `"posted notices"` missing `notice_board`
- Follow-up paraphrases without owned-topic / public-clue overlap
- `"Gate Serjeant"` resolving to `gate_guard`
- Unresolved travel narrated as scene stock
- Evaluator lexical false negatives on quiet listen and nothing-new
- Generic `"The guard says"` absent-speaker label
- Ordinary actions such as `"I wait a moment."` resolving `kind=None`
- Accepted local-observation passive residue
- Unrelated social-pressure test reds

Do not reopen PR-BB classifier convergence, PR-BA place-existence ownership, PR-AZ retry ownership, PR-AY local-observation semantics, PR-AX geographic eligibility, PR-AW stamp eligibility, PR-AV topic-hook eligibility, PR-AU absence fail-closed, PR-AT truncation, PR-AS relevance comparison, PR-AR grounding, PR-AQ typing, PR-AP grammar, PR-AO provenance, or PR-AI speaker ownership unless new evidence shows they cause a remaining defect.

## 18. Recommended Next Action

Agent-history question ownership is closed enough for Product Realization.

Do not select another who-read / last-toucher paraphrase as the next cycle. Do not start object-history tracking, NPC activity logs, or a general intent-parser rewrite.

If the next Product Realization slice stays in AI Experience, pick a **different** remaining sibling owner. Highest leftover of that kind: some natural paraphrases (`posted notices`) still miss `notice_board`. That is alias/content matching, not this family.

No user decision is required.

## 19. Git / Worktree State

Branch: `feature/product-realization` at checkpoint `4c0a454`, plus uncommitted PR-AS through PR-BC work.

The family probe used in-memory defaults and did not reset canonical `data/` documents.

Not committed. Not pushed.

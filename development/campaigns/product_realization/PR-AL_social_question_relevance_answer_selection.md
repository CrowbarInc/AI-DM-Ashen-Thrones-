# PR-AL — Gameplay / AI Experience: Social Question Relevance and Answer Selection

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Replay artifacts: `artifacts/pral_social_question_relevance/`

---

## 1. Executive Summary

PR-AL repaired the highest-leverage ordinary-play failure after PR-AK: a bound tavern runner asked what stew costs answered with an unrelated owned patrol rumor and minted `muddy_footprints_northwest` / `minlead_exit_frontier_gate_old_milestone`.

The recovered contract is:

```text
speaker authorization
    + question relevance
    + authoritative content
    → eligible answer

authorized but irrelevant fact
    → not an answer

relevant but unauthorized fact
    → not an answer

no relevant authorized fact
    → grounded absence, not fabrication or substitution
```

An answer being authoritative for a speaker does not make it relevant to the player's question.

Live `data/world.json` has no stew-price topic. Classification is **Class C**. Success did not require inventing a price. No stew price was added. Generic production code does not special-case stew, runner, or Cinderwatch. Brine-yard fixtures prove the same predicates with unrelated vocabulary.

---

## 2. Starting Failure

PR-AK extended replay T12:

> Player: I step over to the tavern runner and ask what the stew costs.
> GM: Tavern Runner mutters, "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."
> Interlocutor: `tavern_runner`
> New registry rows: `muddy_footprints_northwest`, `minlead_exit_frontier_gate_old_milestone`

The inspect continuation was intact. The next ordinary local social question was not answered.

---

## 3. Stew-Cost End-to-End Trace

Traced before production changes against live-like `tavern_runner` content.

| Stage | Result |
| --- | --- |
| Exact player wording | `I step over to the tavern runner and ask what the stew costs.` |
| Parsed intent | `question` / social exchange |
| Bound interlocutor | `tavern_runner` |
| Canonical speaker | world NPC `tavern_runner` (Tavern Runner) |
| Normalized question | same line, whitespace-collapsed |
| Topic hint | none (`normalized_action.topic` unset) |
| Candidate set | `patrol_rumor` only (live world row) |
| Why eligible then | `_next_topic_to_reveal(..., topic_hint=None)` returns the first unrevealed owned topic |
| Ownership | runner owns `patrol_rumor` |
| Relevance | none, except speaker-token overlap (`runner` appears in both the player line and the rumor) |
| Ranking | first unrevealed row wins; no relevance filter |
| Selected | `patrol_rumor` |
| Realization | `resolution:topic_revealed` at confidence 0.95, then mutters / `"Word is,"` envelope |
| Consequences | `clue_id=muddy_footprints_northwest`; RC-21 then added `minlead_exit_frontier_gate_old_milestone` |
| Narration | exact patrol rumor line |
| RC-21 given that selection | behaved correctly *after* the wrong answer was selected |

`_player_question_covers_stored_thread` also returned true because `"runner"` is a 4-letter token in both the address line and `"The runner heard..."`. Late realization therefore would not have saved the turn even if topic reveal had been skipped later.

---

## 4. First Incorrect Decision

**Confirmed:** `resolve_social_action` → `_next_topic_to_reveal(npc, runtime, topic_hint=None)` on a specific question.

The comment in the question branch was the defective contract:

```text
Only use topic hint when explicitly provided; otherwise reveal first available topic
```

That is the first point where an unrelated owned fact became the selected answer. Consequence firing and RC-21 follow-up are downstream of that selection. They were not the first incorrect decision.

---

## 5. Stew Answer Authority Classification

**Class C — no authorized stew-price answer exists** in the live campaign world used by the reproducer.

| Surface | Stew price? | Related food/menu? |
| --- | --- | --- |
| Live `data/world.json` `tavern_runner.topics` | no | no; only `patrol_rumor` |
| `default_world()` `tavern_runner.topics` | no | **yes** — `"Hot stew and rumors for coin."` (topic id `stew`) |
| `frontier_gate` visible / opening / journal facts | no | stew is hawking flavor, not a price |
| Interactables / clues | no | no menu |
| Hidden facts | no | no |

Do not add a stew price to make the replay succeed. Related `default_world` stew text may be spoken when that topic exists; it still must not invent `"three copper"`.

---

## 6. Runner Knowledge / Topic Ownership

Live runner:

- Authorized to communicate `patrol_rumor`.
- Not authorized to communicate a stew price, because none is authored for that speaker.
- Scene flavor associates the runner with stew. That is perception content, not an NPC topic.

`default_world` runner owns `stew` = `"Hot stew and rumors for coin."` After PR-AL, a stew-cost ask selects that related topic and does not invent a numeric price.

---

## 7. Existing Social Question-Matching Contract

Recovered; not replaced.

| Mechanism | Role |
| --- | --- |
| Exact topic ids | slug/hint substring in `_next_topic_to_reveal` |
| Aliases | speaker identity, not topic aliases (topics rarely have them) |
| Keywords / 4-letter tokens | `_player_question_covers_stored_thread` |
| Stopwords | `_THREAD_MATCH_STOPWORDS` (`what`, `does`, `about`, …) |
| Question words | stripped from subject tokens |
| Clue overlap | `clue_knowledge` in `select_best_social_answer_candidate` |
| Topic ownership | world NPC `topics` / `knowledge` |
| Public clues | landed `clue_knowledge` for the scene |
| Bound speaker | `restrict_npc_id` + PR-AI identity paths |
| Candidate order | first matching unrevealed row |
| Fallback | no topic → refusal / catalog ignorance |
| Model assistance | not used for eligibility |

These remain separate predicates: available, relevant, authorized.

---

## 8. Existing Candidate Generation

1. Bound speaker's own unrevealed topics (`_next_topic_to_reveal`).
2. Structured `topic_revealed` on the resolution (if the social engine already selected).
3. Topic-pressure `last_answer` if it covers the current question.
4. Landed scene `clue_knowledge`.
5. Redirect-style last_answer partials.
6. Present NPC topics the bound speaker has an authoritative path to (`_match_present_npc_topic_authored_knowledge`).
7. Unbound questions may still scan present owners (PR-AD). Bound speakers may not.

PR-AL did not add a global knowledge search.

---

## 9. Existing Candidate Ranking / Precedence

Unchanged except that irrelevant owned rows are no longer candidates.

Among remaining eligible rows, first unrevealed / existing A→D confidence order still wins. Richer metadata (clue, follow-up, longer text) does not outrank relevance, because irrelevant hook rows never enter the eligible set.

---

## 10. Root Cause

**Confirmed, not revised.**

Two cooperating defects:

1. **Primary:** question resolution revealed the first owned topic when no topic hint was supplied.
2. **Secondary:** token overlap treated speaker-identity tokens (`runner`) as proof the rumor answered the stew question. That contaminated covers, scoring, and late realization.

The patrol rumor won because it was the runner's only/first topic and `"runner"` overlapped the player line. It did not win because RC-21, PR-AJ provenance, or lead ingestion was wrong.

---

## 11. Relevance vs Authorization Contract

Used in production:

**Authorization** — PR-AI: the bound speaker must have an authoritative path to the fact.

**Relevance** — the player's remaining subject tokens, after stripping stopwords, generic social/motion verbs, and speaker-identity tokens, must overlap the topic id/text/clue fields.

**Generic ask** — if no subject tokens remain (`Ask Runner`), first-available remains, preserving existing smoke tests.

**Existing ellipsis follow-up** (`What do you mean?`) — does not mint a different unrevealed topic.

**No relevant authorized fact** — do not substitute; do not invent.

---

## 12. Implementation

Generic engine only: `game/social.py`, `game/social_memory.py`.

1. `authored_topic_relevant_to_question` / `_question_subject_tokens` — relevance without speaker-identity contamination.
2. `_next_topic_to_reveal(..., player_text=)` — skip irrelevant owned topics on explicit questions.
3. `_player_question_covers_stored_thread(..., exclude_tokens=)` — speaker tokens cannot fake coverage.
4. `_match_present_npc_topic_authored_knowledge` — score/eligibility use bound-speaker tokens only, not the topic owner's aliases (so `"watch"` remains a subject when asking the captain).
5. `select_best_social_answer_candidate` last_answer / clue_knowledge paths pass the same exclude set.

Canonical scene/world content was not modified. No stew price was added.

`tests/test_social.py::test_question_reveals_topic_clue` now asks about the missing patrol, which is the topic it already expected to reveal.

---

## 13. Relevant Authorized Answer Behavior

Ask the runner about the missing patrol, or the kiln tender about kiln three:

- matching owned topic is selected on the first relevant ask
- no warm-up required
- PR-AI captain `"Who commands the watch here?"` still realizes `watch_command`

---

## 14. Authorized but Irrelevant Behavior

Ask the runner about stew, or the kiln tender about kiln-ash cost while they also own a barge-chit hook:

- owned unrelated topic is not emitted
- its clue/lead does not fire
- `revealed_topics` does not consume the unrelated row

---

## 15. Relevant but Unauthorized Behavior

Ask the kiln tender about the salt raker's pan schedule, or the bound runner about watch command:

- current speaker does not gain the other NPC's topic
- PR-AI bound-speaker restrict remains

---

## 16. No-Answer / Grounded Absence Behavior

Class C stew-cost on live world:

- `topic_revealed` is empty
- `clue_id` is empty
- catalog/model ignorance may speak
- no numeric price is authored by the engine
- evaluator may still FAIL a broken catalog fragment; that is supporting evidence, not a license to substitute a rumor

---

## 17. Consequence Gating

Consequences fire only when a candidate becomes the selected topic.

Rejected irrelevant `barge_chit` / `patrol_rumor` rows do not write clues or leads. Legitimate selected hooks still write `clue_id` and may create RC-21 follow-up.

---

## 18. Legitimate Follow-Up Preservation

Asking about the barge chit still selects `barge_chit` and lands `barge_chit_lead`. Asking the runner about the missing patrol still lands `muddy_footprints_northwest`. PR-AJ does not suppress those authorized structured consequences.

---

## 19. Conversational Follow-Up Behavior

`"What do you mean?"` after a kiln-bank answer does not mint the unrelated chit hook.

An explicit later ask about the chit can move to that topic. Stale context does not steal an explicit new subject. This is not a full discourse resolver.

---

## 20. Taverns/Runner Before / After

| Turn | Before | After |
| --- | --- | --- |
| Live stew-cost ask | patrol rumor + `muddy_footprints_northwest` + `minlead_exit_…` | no patrol topic; no those leads; grounded absence |
| `default_world` stew-cost ask | n/a in the live reproducer | related `"Hot stew and rumors for coin."`; no invented copper price |
| Ask runner about missing patrol | rumor + clue (legitimate) | unchanged, still fires |

Extended replay T12 (`artifacts/pral_social_question_relevance/extended_replay/runs/20260920T131735Z_R2-MT01-AL/transcript.md`):

> Tavern Runner says, "No. I cannot answer that from what."
> Interlocutor: `tavern_runner`
> Lead registry unchanged: `notice_patrol_route`, `milestone_mud_prints` only
> `pending_leads`: empty

The refusal fragment is existing catalog grammar, not a new answer-selection bug. Automated playability FAIL on that fragment is supporting evidence only.

---

## 21. Scenario-Independent Generalization Fixtures

Hard gate. Vocabulary is brine-yard / kiln / barge / pans. Scene `brine_yard`; NPCs `kiln_tender`, `salt_raker`.

| Test | Result |
| --- | --- |
| 1. Two owned topics, ask A | PASS — kiln bank; chit absent |
| 2. Same NPC, ask B | PASS — chit; kiln absent |
| 3. No relevant answer | PASS — no substitute, no invented price |
| 4. Relevant but unauthorized | PASS — tender does not speak pan schedule |
| 5. Plain relevant vs unrelated hook | PASS — kiln wins; chit clue does not fire |
| 6. Relevant authorized hook | PASS — chit answers; `barge_chit_lead` lands |
| 7. Natural paraphrase | PASS — `"third kiln"` still selects kiln bank |
| 8. First ask | PASS — HTTP replaces ignorance |
| 9. Follow-up context | PASS — `"What do you mean?"` does not mint chit |
| 10. Explicit subject change | PASS — kiln then chit |
| 11. Rejected candidate has no consequence | PASS — `barge_chit` not revealed |
| 12. Selection does not create knowledge | PASS — no new topic relationship |

HTTP tests exercise `/api/chat` with stubbed GPT.

---

## 22. Anti-Overfitting Audit

Inspected PR-AL relevance helpers and `_next_topic_to_reveal`.

| Term | In new relevance helpers? |
| --- | --- |
| stew / tavern / runner | no |
| muddy_footprints_northwest | no |
| minlead_exit_frontier_gate_old_milestone | no |
| guard_captain / Captain Thoran | no |
| frontier_gate / Cinderwatch / patrol / old_milestone | no |

Pre-existing `_SOCIAL_PROBE_TRANSACTIONAL_PATTERNS` already mentioned stew for probe classification. PR-AL did not add those patterns and did not use them in answer selection.

No disguised overfitting found: no price-question special case, no patrol suppression after food questions, no follow-up-based ranking, no Cinderwatch candidate penalties. Synthetic topics do not share calibration vocabulary.

`tests/test_social_question_relevance_answer_selection.py::test_anti_overfitting_generic_helpers_have_no_calibration_special_case` enforces this.

---

## 23. Tests Added or Updated

Added: `tests/test_social_question_relevance_answer_selection.py` (24 tests).

Updated: `tests/test_social.py::test_question_reveals_topic_clue` prompt now names the missing patrol, the topic that test already expected.

---

## 24. Continued Multi-Turn Replay

`artifacts/pral_social_question_relevance/extended_replay/runs/20260920T131735Z_R2-MT01-AL/transcript.md`

Ordinary-play chain through observe, notice, travel, milestone, return, captain first-ask, PR-AK roster inspect, look-around, stew-cost, then one further action.

T12 stew-cost: no patrol rumor; no `muddy_footprints_northwest`; no `minlead_exit_frontier_gate_old_milestone`.

T13 `"I glance back at the notice board after that."` stayed on `tavern_runner` as `social_probe`. That is social lock, not answer-selection, and is the next recommended slice.

---

## 25. Freeform Social-Relevance Probe

`artifacts/pral_social_question_relevance/freeform_probe/20260920T131851Z_probe.md`

| Turn | Player | Engine selection | Notes |
| --- | --- | --- | --- |
| 1 | What's in the stew today? | patrol rejected | no lead |
| 2 | tell me about the missing patrol | `patrol_rumor` | legitimate clue + minlead |
| 3 | How much for a bowl? | patrol rejected | engine empty; live model invented three copper |
| 4 | Who posted the night watch list? | captain bound; no Thoran speech | unauthorized/absent watch-list |
| 5 | is the stew salted? | patrol rejected | no rumor substitute |
| 6 | What happened to that patrol? | relevant patrol fact | already revealed; no new clue |
| 7 | What do you mean? | no new topic | follow-up |
| 8 | ask the captain about the missing patrol | speaker bind missed | remaining lock/address residue |

Engine eligibility matched the contract. Live-model price invention on turn 3 is remaining semantic residue, not engine substitution of `patrol_rumor`.

---

## 26. Validation Results

| Suite | Result |
| --- | --- |
| PR-AL relevance tests | 24 passed |
| `tests/test_social.py` | passed |
| PR-AD authored-knowledge | passed |
| PR-AE stay/leave | passed |
| PR-AF arrival | passed |
| PR-AG generalized-exit | passed |
| PR-AH observation | passed |
| PR-AI bound-speaker | passed (after keeping `"watch"` as a subject token on captain asks) |
| PR-AJ provenance | passed |
| PR-AK referenced-surface | passed |
| Social destination / lead landing / RC-21 | passed |
| Clue / intent / state-authority / narration-consistency | passed |
| Round #1 calibration | 13/13 |
| Full authoritative suite | not re-run |

Windows `PermissionError` on shared `codex_pytest_tmp` remains environmental; focused runs used `artifacts/pral_pytest_tmp*`.

---

## 27. Remaining Semantic Failures

Dominant next: social lock stealing a later inspect (replay T13).

Also remaining:

- Live model can invent a bowl price when the engine has no authored answer.
- Grounded-absence catalog grammar can be broken.
- Prior PR-AK/AH look-around, paraphrase, Gate Serjeant, geography-bleed, and `"What's nearby?"` residue.

---

## 28. Deferred Findings

Unchanged from the handoff, plus:

- Do not add a stew price / menu / economy.
- Do not rewrite fallback grammar in this slice.
- Do not gag live-model invention with a new prompt architecture in this slice.
- Social lock stealing inspect is deferred from PR-AL on purpose; it did not cause the stew/patrol mismatch.

---

## 29. Recommended Next Product Slice

**Social lock stealing a later inspect of an authored surface**, from continued ordinary-play T13.

Not chosen from roadmap neatness. After stew-cost stopped substituting the patrol rumor, the next natural `"glance back at the notice board"` stayed inside the runner.

---

## 30. Git / Worktree State

The worktree is dirty and was dirty before PR-AL.

PR-AL generic production: `game/social.py`, `game/social_memory.py`.

PR-AL tests/docs/tools: `tests/test_social_question_relevance_answer_selection.py`, `tests/test_social.py` (one prompt), `tools/run_pral_freeform_probe.py`, `data/validation/pral_social_question_relevance/`, `artifacts/pral_social_question_relevance/`, `PR-AL_social_question_relevance_answer_selection.md`, `docs/NEXT_SESSION.md`.

No canonical content change. Replay/probe reset `data/session.json`, `data/world.json`, `data/combat.json`, `data/session_log.jsonl`.

`game/social.py` was already modified by PR-AD through PR-AI relative to HEAD. Do not treat `git diff --stat game/social.py` against HEAD as a PR-AL-only footprint.

Not committed.

---

## 31. Confidence

High on root cause, first incorrect decision, Class C classification, and engine eligibility.

High that the live stew-cost turn no longer selects `patrol_rumor` or mints those two leads.

Medium-high that live-model price invention and broken refusal grammar remain separate from eligibility.

High that the next ordinary-play blocker is social lock, not relevance.

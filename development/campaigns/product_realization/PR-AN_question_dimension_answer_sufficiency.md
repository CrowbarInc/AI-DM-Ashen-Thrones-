# PR-AN — Gameplay / AI Experience: Question Dimension and Answer Sufficiency

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Replay artifacts: `artifacts/pran_question_dimension/`

---

## 1. Executive Summary

PR-AN repaired the highest-leverage ordinary-play failure after PR-AM: after a repaired notice-board glance, stepping back to the tavern runner to ask who last checked that board emitted the authored notice/patrol fact instead of a grounded no-answer.

The recovered contract is:

```text
speaker authorization
    +
subject relevance
    +
requested-information sufficiency
    → eligible answer

authorized + subject-relevant + insufficient
    → grounded absence, not a neighboring fact
```

Knowing something about a subject is not the same as answering every question about that subject.

T14 world truth is **Class C**. The live world knows board contents / patrol last-seen location. It does not record who last checked the board. No last-reader fact was added. No price, menu, or barter system was added.

The existing `classify_social_question_dimension` / `_stored_text_supports_dimension` contracts already represented the distinction. They were not applied at topic reveal or interactable social matching. Mill-race fixtures prove the same predicates with unrelated vocabulary.

---

## 2. Starting Failure

PR-AM extended replay T14:

> Player: I step back to the tavern runner and ask who last checked that board.
> GM: Tavern Runner mutters, "Word is, the missing patrol was last seen taking the northwest mud track past the crates."
> Interlocutor: `tavern_runner`
> `resolution.kind`: `question`

PR-AM routing succeeded. The runner rebound. The new turn was social. The selected fact did not answer the asked dimension.

---

## 3. T14 End-to-End Trace

Traced before production changes against live `frontier_gate` / `tavern_runner` content.

| Stage | Result |
| --- | --- |
| Exact player wording | `I step back to the tavern runner and ask who last checked that board.` |
| Bound speaker | `tavern_runner` after explicit re-address |
| Parsed intent | `question` / social exchange |
| Normalized question | same line, whitespace-collapsed |
| Question form / dimension | `identity` via existing `classify_social_followup_dimension` (`who`) |
| Subject tokens | `back`, `last`, `checked`, `board` (speaker tokens `tavern`/`runner` stripped; `who`/`that` are stopwords) |
| `"that board"` | surface alias match on `notice_board` (`board`) |
| `"who"` / person need | survives as dimension `identity`, not as a subject token |
| Serious candidates | live runner topic `patrol_rumor`; scene interactable `notice_board` → `notice_patrol_route` |
| `patrol_rumor` relevance | **false** — no `last`/`checked`/`board` overlap with `"The runner heard the patrol vanished near muddy footprints northwest of the crates."` |
| `patrol_rumor` identity support | **false** |
| `_next_topic_to_reveal` | **None** |
| `resolve_social_action` | no `topic_revealed`; no `clue_id` |
| `select_best_social_answer_candidate` | refusal |
| Interactable match | **selected** `notice_patrol_route`: `"The missing patrol was last seen taking the northwest mud track past the crates."` |
| Why that fact looked relevant | player mentioned `board`; interactable aliases include `board` |
| Why it looked sufficient | interactable sources skipped dimension checks; `"last"` also overlaps `"last seen"` in covers |
| Authoritative last-reader anywhere? | **no** |
| Runner authorized if it existed? | n/a; no such fact |
| Realization | `Tavern Runner mutters, "Word is, the missing patrol was last seen..."` |
| Consequences | none new on T14; notice clue already existed from earlier inspect |
| Narration | exact notice-route sentence, not the runner's `patrol_rumor` wording |

`"that board"` resolved to the authored notice board. The patrol/notice fact is about what is posted / where the patrol was last seen. It does not name a last reader or checker.

---

## 4. World Truth Classification

**Class C — related board information exists; the requested relation does not.**

| Surface | Who last checked/read the board? | Related board / patrol information? |
| --- | --- | --- |
| Live `tavern_runner.topics` | no | `patrol_rumor` last-seen / footprints |
| `notice_board` / `notice_patrol_route` | no | posted warning; patrol last seen on the northwest mud track |
| `frontier_gate` visible / opening / journal facts | no | board lists taxes, curfews, missing-patrol warning |
| Hidden facts / interactables / clues | no last-reader | no poster/author/checker row |
| `default_world` runner | no | stew flavor topic only |

Do not add a last-reader fact to make T14 succeed. The correct engine result is grounded absence.

---

## 5. First Incorrect Semantic Decision

**Confirmed:** `_match_interactable_authored_knowledge` treated mention of an authored surface as a sufficient social answer.

Cooperating defects:

1. `realize_authored_knowledge_answer._usable` exempted `interactable:` sources from `_stored_text_supports_dimension`.
2. `select_best_social_answer_candidate` path A fell back to `_trim_utterance(clue)` when the dimension-aware pick failed.
3. `_next_topic_to_reveal` applied PR-AL relevance only, so a later same-subject / wrong-dimension owned topic could still reveal.

The first point where T14 lost was interactable matching. `_next_topic_to_reveal` had already correctly rejected `patrol_rumor`. Suppressing the final patrol sentence would have hidden the wrong seam.

---

## 6. Existing Question Representation

Recovered; not replaced. `classify_social_followup_dimension` already existed as a minimal deterministic axis:

| Dimension | Pre-PR-AN | PR-AN extension |
| --- | --- | --- |
| identity | `who` / `whose` | `whoever`, `name of`, `the person who` |
| location | `where`, `last seen` | `whereabouts`, `destination` |
| time | absent (fell to `general`) | `when`, `what hour/time`, `how long` |
| cause | absent except `why is that` → clarification | `why is/was/did…`, `the reason`, `what caused`; bare `Why?` stays follow-up |
| quantity | absent | `how many`, `how much`, `what does … cost` |
| status | absent | `what condition`, `what state` |
| content | `general` | remains `general` |
| clarification / next_step / danger / avoidance / affiliation / general | unchanged | unchanged |

Question words were stopwords in subject-token extraction. They already survived as **dimension**, not as subject tokens. They did not affect `_next_topic_to_reveal` eligibility before PR-AN.

No new parser, LLM classifier, ontology, or knowledge graph was added.

---

## 7. Existing Subject-Relevance Contract

PR-AL remains authoritative.

`authored_topic_relevant_to_question` still means: after stripping stopwords, generic social/motion verbs, and speaker-identity tokens, remaining subject tokens must overlap the topic id/text/clue fields.

Generic asks with no remaining subject tokens still use first-available. That is relevance, not sufficiency.

---

## 8. Existing Answer-Selection Contract

Recovered owners:

| Mechanism | Role |
| --- | --- |
| `classify_social_question_dimension` | requested-information axis |
| `_stored_text_supports_dimension` | whether stored text can satisfy that axis |
| `_pick_utterance_from_stored` | dimension-aware utterance slice |
| `_match_present_npc_topic_authored_knowledge` | already required dimension support |
| `select_best` last_answer / clue_knowledge | already required dimension support |
| `_next_topic_to_reveal` | relevance only, before PR-AN |
| `_match_interactable_authored_knowledge` | surface mention only, before PR-AN |

The missing application was eligibility at reveal / interactable / written-fact fallback, not a missing representation.

---

## 9. Root Cause

**Confirmed, not revised.**

T14 selected `notice_patrol_route` because the player mentioned the board and interactable social matching had no sufficiency predicate. The notice fact is subject-relevant for content questions and insufficient for an identity/last-checker question.

`patrol_rumor` was not the selected T14 candidate. Its wording does not match the emitted sentence. Token overlap on `"last"` made covers true for the notice clue; that was cooperating coarseness, not the first incorrect decision.

---

## 10. Recovered Answer-Sufficiency Contract

Used in production:

**Authorization** — PR-AI: the bound speaker must have an authoritative path to the candidate.

**Subject relevance** — PR-AL: the candidate must concern the asked subject.

**Answer sufficiency** — the candidate must contain authoritative information capable of satisfying the classified requested-information dimension.

**Grounded absence** — authorized subject-relevant facts that fail sufficiency are not answers.

**No fabrication** — missing identity, time, location, cause, or quantity is not inferred.

**Consequences** — only selected sufficient answers may reveal topics or fire structured clues/leads.

Generic / clarification asks keep existing any-authored-text behavior so content questions such as `"What is posted on the board?"` still work.

---

## 11. Implementation

Generic engine only: `game/social.py`.

1. `authored_answer_sufficient_for_question` — public sufficiency predicate over the existing dimension contracts.
2. `_next_topic_to_reveal` — skip subject-relevant but dimension-insufficient owned rows.
3. `_match_interactable_authored_knowledge(..., dimension=)` — surface mention is not enough for identity/time/cause/quantity/status/location.
4. `realize_authored_knowledge_answer._usable` — interactable sources no longer bypass sufficiency.
5. `select_best` topic_revealed — no dimension-ignoring trim fallback.
6. Written-fact realization filter — resolution facts must also be sufficient before they replace ignorance.
7. Narrow classifier extensions listed in §6. Identity support accepts actor-verb / `by Name` patterns so `"Neris recaulked the mill span"` works without treating sentence-initial `"The"` as a person.

Canonical scene/world content was not modified. No last-reader row. No stew price.

`tests/test_social.py::test_direct_question_sets_npc_reply_expected_signal` now asks `"What happens to the ledgers?"` because `"Who keeps the ledgers?"` plus `"The ledgers are kept under seal."` is the insufficient-identity case PR-AN must reject.

---

## 12. Person / Identity Questions

Positive: authorized `"Neris recaulked the mill span"` answers `"Who recaulked the mill span?"` and `"Do you know the name of the person who recaulked the mill span?"`.

Negative: `"The mill span was recaulked yesterday"` does not answer who. No repairer is invented.

T14 / live board-checker asks stay in this family.

---

## 13. Time Questions

Positive: `"The grain barge departed yesterday"` answers `"When did the grain barge leave?"`.

Negative: `"The grain barge traveled east"` does not. No departure time is invented.

Live probe `"When did that missing patrol vanish, exactly?"` correctly marked `patrol_rumor` relevant but insufficient. The live model still invented `"just before dawn"`. That is remaining State ↔ Narration residue, not engine substitution of the rumor as a time fact.

---

## 14. Location Questions

Positive: `"The grain barge went to the river crossing"` answers `"Where did the grain barge go?"`.

Negative: `"The grain barge departed yesterday"` does not. No destination is invented.

Live `"Where was the patrol last seen?"` selected `patrol_rumor` because that fact authoritatively contains `near` / footprint location. The structured clue fired. That is a legitimate sufficient answer, not T14 leakage.

---

## 15. Cause / Reason Questions

Positive: `"The western sluice is shut because the millrace cracked"` answers `"Why is the western sluice shut?"`.

Negative: sluice status alone does not. No cause is invented.

Bare `"Why?"` remains an existing follow-up, not a new cause axis.

---

## 16. Quantity / Value Questions

Positive: `"Four wardens walk the cistern rim"` answers `"How many wardens walk the cistern?"`.

Negative: existence without a count does not. Counts are not inferred from list length.

`"What does the stew cost?"` is quantity. `"Hot stew and rumors for coin."` is related but insufficient. No price is invented. No economic simulation was added. Live world still has no stew-price topic.

---

## 17. Content Questions

`"What is posted on the notice board?"` / `"What does the tide slate say?"` remain `general`. Authored surface contents stay eligible.

The same notice/slate content is ineligible for `"Who last checked …?"`.

PR-AN does not globally suppress board facts.

---

## 18. Same-Subject / Different-Property Behavior

Mill-span fixture:

| Ask | Selected |
| --- | --- |
| Where is the mill span? | north-road place fact |
| What condition is it in? | cracked status fact |
| Who recaulked it? | Neris |
| When was it recaulked? | yesterday |

A longer wrong-property row does not win by text length. Existing topic rows were enough; no property database was added.

---

## 19. Partial-Answer Behavior

`"Who recaulked the mill span and when?"` classifies as identity (`who` first). The engine may select the Neris fact. It does not invent yesterday. No compound-QA framework was added.

---

## 20. Authorization Preservation

`mill_hand` owns only `"The mill span was recaulked."` `sluice_keeper` owns Neris. Asking the hand who recaulked it does not leak Neris. PR-AI bound-speaker restrict remains.

---

## 21. Relevance Preservation

The keeper may own both Neris-on-span and Oren-on-hopper person facts. `"Who recaulked the mill span?"` selects Neris, not Oren. Right dimension / wrong subject still fails. PR-AL remains.

---

## 22. Grounded Absence

Hard gate. Multiple mill-race cases bind the correct NPC, give that NPC authorized subject knowledge, and still refuse when none of those facts answer the requested property. T14 is the live Class C instance.

---

## 23. Communication-Detection Audit

T14 did not go through `_text_communicates_authored_fact` as the first failure. Realization injected the interactable fact before communication detection mattered.

Subject-token overlap can still make two related sentences look like the same spoken fact. PR-AN did not rebuild communication detection. Eligibility now prevents selecting the insufficient fact, so that seam is not asked to treat a time-only or content-only sentence as an identity answer.

Live-model invention after a correct engine no-answer remains possible.

---

## 24. Consequence Gating

Rejected insufficient rows do not enter `revealed_topics` and do not write `clue_id`. Mill-race `span_crack_lead` / `mill_chit_lead` stay quiet on `"Who recaulked the mill span?"`. Asking what is hidden in the hopper still lands `mill_chit_lead`.

T14 after: lead registry stayed `notice_patrol_route` + `milestone_mud_prints`. No `muddy_footprints_northwest`. RC-21 remains available for legitimately selected location answers (probe T3).

---

## 25. Economics / Barter Deferral Confirmation

No prices, menus, shop pricing, currency, barter, bargaining, merchant utility, or supply/demand code was added. Quantity questions use synthetic wardens / bowls. Stew-cost remains a negative fixture: absence, not a new value.

---

## 26. Frontier Gate T14 Before / After

| | Before | After |
| --- | --- | --- |
| Binding | `tavern_runner` / social | unchanged |
| Subject | board | board |
| Requested information | identity / last checker | identity |
| `patrol_rumor` | not actually selected | still rejected (not relevant) |
| `notice_patrol_route` | emitted as the answer | rejected as insufficient |
| Last-reader fact | none | none; none added |
| Consequences | none new | none new |
| Narration | patrol last-seen rumor | `"No. I cannot answer that from what."` |
| Evaluator | PASS on the wrong fact | FAIL on known broken refusal grammar |

The grammar FAIL is existing catalog residue, also seen on T12 stew-cost. It is supporting evidence, not a license to re-select the notice fact.

---

## 27. Scenario-Independent Generalization Fixtures

Hard gate. Vocabulary is mill-race / sluice / barge / cistern / tide slate. Scene `mill_race`; NPCs `sluice_keeper`, `mill_hand`.

| Test | Result |
| --- | --- |
| 1. Person positive | PASS — Neris |
| 2. Person negative | PASS — time/occurrence insufficient |
| 3. Time positive | PASS — yesterday |
| 4. Time negative | PASS — eastward travel insufficient |
| 5. Location positive | PASS — river crossing |
| 6. Location negative | PASS — departure time insufficient |
| 7. Cause positive | PASS — millrace cracked |
| 8. Cause negative | PASS — shut status insufficient |
| 9. Quantity positive | PASS — four wardens |
| 10. Quantity negative | PASS — existence insufficient |
| 11. Same subject, different property | PASS — four mill-span facts |
| 12. Sufficient but unauthorized | PASS — hand does not leak Neris |
| 13. Right dimension, wrong subject | PASS — Oren does not replace Neris |
| 14. Valid content | PASS — tide slate text |
| 15. Same surface, unsupported actor | PASS — slate contents do not name a checker |
| 16. Non-literal paraphrase | PASS — `name of the person who` |
| 17. Rejected fact has no consequence | PASS |
| 18. Legitimate consequence preserved | PASS — hopper chit |

HTTP tests exercise `/api/chat` with stubbed GPT.

---

## 28. Anti-Overfitting Audit

Inspected PR-AN helpers and classifier/support extensions.

| Term | In new sufficiency helpers / classifier extensions? |
| --- | --- |
| `notice_board` / `tavern_runner` / `patrol_rumor` | no |
| `frontier_gate` / `Cinderwatch` / `stew` | no |
| `guard_captain` / `Captain Thoran` | no (pre-existing comment in `_stored_text_supports_dimension` unchanged) |
| `roster_board` / `old_milestone` | no |
| `"who last checked"` / board-reader special case | no |

Pre-existing `_SOCIAL_PROBE_TRANSACTIONAL_PATTERNS` still mention stew for probe classification. PR-AN did not add those patterns and does not use them in sufficiency.

No disguised overfitting found: no notice-only patrol suppression, no scene-time answers for every `when`, no current-scene answers for every `where`, no list-length quantities, no invented prices, no “any person token answers any who.”

`tests/test_question_dimension_answer_sufficiency.py::test_anti_overfitting_generic_helpers_have_no_calibration_special_case` enforces this.

---

## 29. Tests Added or Updated

Added: `tests/test_question_dimension_answer_sufficiency.py` (33 tests).

Updated:

- `tests/test_social_question_relevance_answer_selection.py` — stew-cost with a related stew topic is now quantity-absence; `"Tell me about the stew."` still selects the stew topic.
- `tests/test_social.py::test_direct_question_sets_npc_reply_expected_signal` — question now matches the authored ledger fact.

---

## 30. Continued Multi-Turn Replay

`artifacts/pran_question_dimension/extended_replay/runs/20260920T170951Z_R2-MT01-AN/transcript.md`

Ordinary-play chain through observe, notice, travel, milestone, return, captain first-ask, roster inspect, look-around, stew-cost, notice-board glance, T14 last-checker ask, then one further action.

T14: runner bound; no patrol/notice substitute; no new lead.

T15 `"I thank the runner and look toward the gate line again."` routed as `investigate` and emitted `"Details on the exact timing and personnel of the missing patrol assignment."` plus a new registry row of that invented title. That is the next ordinary-play blocker. It is not a T14 sufficiency miss.

---

## 31. Freeform Question-Sufficiency Probe

`artifacts/pran_question_dimension/freeform_probe/20260920T171124Z_probe.md`

| Turn | Player | Engine | Notes |
| --- | --- | --- | --- |
| 1 | name of whoever last checked that board | identity; patrol rejected | live model speculated a serjeant redirect |
| 2 | when did the patrol vanish | time; relevant, insufficient; no topic | live model invented dawn |
| 3 | where was the patrol last seen | location; `patrol_rumor` selected | legitimate clue + minlead |
| 4 | why is the stew out in the rain | cause; rejected | no rumor substitute |
| 5 | how many bowls left | quantity; rejected | live model invented a pier ledger |
| 6 | what is posted on that board | inspect path; notice clue | content remains available |
| 7 | what does the stew cost | quantity; rejected | no price; no new lead |
| 8 | who commands the watch | captain bound; no Thoran speech | live-model concealment residue |
| 9 | who last checked the notice board | routed `observe` | watch-command stock, not a checker |
| 10 | tell me about the missing patrol | relevant/sufficient; already revealed | follow-up / redirect lead |

Engine eligibility matched the contract on the sufficiency cases. Live-model invention after engine absence is remaining residue.

---

## 32. Validation Results

| Suite | Result |
| --- | --- |
| PR-AN sufficiency tests | 33 passed |
| PR-AL relevance tests | passed |
| PR-AD authored-knowledge | passed |
| PR-AE stay/leave | passed |
| PR-AF arrival | passed |
| PR-AG generalized-exit | passed |
| PR-AH observation | passed |
| PR-AI bound-speaker | passed |
| PR-AJ provenance | passed |
| PR-AK referenced-surface | passed |
| PR-AM world-action | passed |
| `tests/test_social.py` / escalation / destination / lead landing | passed |
| Intent / narration-consistency / state-authority / dialogue-routing / clue | passed |
| Playability eval | passed |
| Round #1 calibration | 13/13 |
| Full authoritative suite | not re-run |

Windows `PermissionError` on shared `codex_pytest_tmp` remains environmental; focused runs used `artifacts/pran_pytest_tmp*`.

---

## 33. Remaining Semantic Failures

Dominant next: T15 thank + look-toward-the-gate-line routed as `investigate` and minted an unsourced personnel/timing clue title.

Also remaining:

- Grounded-absence catalog grammar (`"I cannot answer that from what."`) on T12 and T14.
- Live model can invent times, counts, or redirects after a correct engine no-answer.
- Prior look-around stock, paraphrase, Gate Serjeant, geography-bleed, and `"What's nearby?"` residue.

---

## 34. Deferred Findings

Unchanged from the handoff, plus:

- Do not add a last-reader / board-history store.
- Do not add a stew price / menu / economy.
- Do not rewrite fallback grammar in this slice.
- Do not gag live-model invention with a new prompt architecture in this slice.
- Do not build a compound-QA framework.
- T15 investigate/clue invention is deferred from PR-AN on purpose; it did not cause the T14 sufficiency miss.

---

## 35. Recommended Next Product Slice

**After repaired T14, a thank + look-toward-the-gate-line action was captured as `investigate` and minted `"Details on the exact timing and personnel of the missing patrol assignment."`**

Chosen from continued ordinary-play T15, not roadmap neatness. It is class A in the PR-AN next-slice list.

Do not promote economics because quantity questions were in scope. Do not start a general State ↔ Narration program unless later evidence outranks this narrower investigate/clue-invention failure. Grammar remains a severe sibling.

---

## 36. Git / Worktree State

The worktree is dirty and was dirty before PR-AN.

PR-AN generic production: `game/social.py`.

PR-AN tests/docs/tools: `tests/test_question_dimension_answer_sufficiency.py`, `tests/test_social.py` (one prompt), `tests/test_social_question_relevance_answer_selection.py` (stew sufficiency), `tools/run_pran_freeform_probe.py`, `data/validation/pran_question_dimension_answer_sufficiency/`, `artifacts/pran_question_dimension/`, `PR-AN_question_dimension_answer_sufficiency.md`, `docs/NEXT_SESSION.md`.

No canonical content change. Replay/probe reset `data/session.json`, `data/world.json`, `data/combat.json`, `data/session_log.jsonl`.

`game/social.py` was already modified by PR-AD through PR-AM relative to HEAD. Do not treat `git diff --stat game/social.py` against HEAD as a PR-AN-only footprint.

Not committed.

---

## 37. Confidence

High on root cause, first incorrect decision, Class C classification, and engine eligibility.

High that live T14 no longer selects `notice_patrol_route` or `patrol_rumor`, and does not mint those consequences.

Medium-high that live-model invention after absence and broken refusal grammar remain separate from eligibility.

High that the next ordinary-play blocker is T15 investigate/clue invention, not T14 sufficiency.

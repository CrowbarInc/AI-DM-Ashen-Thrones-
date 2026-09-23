# PR-BG — AI Experience: Follow-Up Topic Continuity and Public-Clue Paraphrase Convergence

Date: 2026-09-22
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Probe artifacts: `artifacts/prbg_followup_topic_continuity/`

---

## 1. Executive Summary

The handoff residue mixed two different failures.

The recovered PR-AI line `"What are you doing about the missing patrol?"` after a watch-command answer is a **topic switch**, not a lost follow-up. The captain has no covering owned topic or landed public clue. Refusal is correct under PR-AL / PR-AU.

A narrower continuity defect did reproduce. After a successful NPC answer, already-classified empty-subject follow-ups such as `"Why is that?"`, `"How come?"`, and `"Who is that?"` could lose the current `topic_pressure` last-answer even though:

* an authoritative last answer existed;
* `is_valid_followup_question` already marked the turn as the same thread;
* speaker alignment and dimension sufficiency were available.

The first incorrect decision was last-answer reuse requiring leftover lexical overlap, while `normalize_topic` also minted a new player-wording key for those same empty-subject shapes.

The repair reuses those existing owners. It does not add synonyms, embeddings, a second topic router, or a conversation-state stack.

`"Why was it shut down?"` after a closed-road fact remains unsupported. That is richer predicate paraphrase plus cause sufficiency, not ordinary deterministic continuity.

Ordinary deterministic follow-up continuity is now sufficiently converged for Product Realization. Do not open another paraphrase cycle.

---

## 2. Recovered Failing Examples

### 2.1 Named residue: PR-AI T2 (not a continuity defect)

Source: `artifacts/prai_bound_speaker_knowledge/freeform_probe/20260920T112834Z_probe.md`

| Stage | Result |
| --- | --- |
| Preceding player turn | `I turn to the Guard Captain. "Who's in charge of the watch tonight?"` |
| NPC/system answer | `captain Thoran commands the gate watch tonight` |
| Authoritative topic after | `watch_command` revealed; last-answer / topic-pressure key from player wording (`topic:captain_charge_guard`) |
| Follow-up | `What are you doing about the missing patrol?` |
| Parser | social question (`parse_type=None`; dialogue-lock / default social) |
| Subject tokens | `doing`, `missing`, `patrol` |
| Contextual-topic candidate | `normalize_topic` → `missing_patrol` (different key) |
| Overlap | none with Thoran / watch last-answer; captain owns no patrol topic; no landed clue |
| Terminal | `topic_revealed=None`; answer candidate `refusal` |
| Player-facing | `Guard Captain shakes their head. "I don't know."` |

First incorrect decision: none. This is an explicit new subject the speaker cannot answer.

### 2.2 Named residue: PR-AJ T1 (stale)

Historical `"Who keeps the watch roster tonight?"` refused. Current overlap of `watch` with `watch_command` reveals Thoran. The old refusal is not current behavior.

### 2.3 Reproduced continuity defect

After Thoran / kiln-spur last-answer is stored, recognized empty-subject follow-ups failed last-answer reuse:

| Follow-up | `is_valid_followup` | Subject tokens | Cover last-answer | Before | After |
| --- | --- | --- | --- | --- | --- |
| `Why is that?` | True | `[]` | False | refusal | last-answer |
| `How come?` | True | `[]` | False | refusal | last-answer |
| `Who is that?` | True | `[]` | False | refusal | last-answer if identity-sufficient; else fail-closed |
| `Who is he?` | False | `[]` | True (`he` shortcut) | key fragmented to `unknown_topic` | key retained; last-answer |

These are not the recovered replay wording. Kiln-yard `"Why is that?"` / `"How come?"` after a barred-spur fact is the generalization surface.

---

## 3. Continuity Architecture

| Name | Role | Authority |
| --- | --- | --- |
| World NPC `topics` / `knowledge` | Owned facts the speaker may reveal | Authoritative |
| `runtime.revealed_topics` | Already-spoken owned topic ids | Authoritative |
| `_next_topic_to_reveal` | First unrevealed owned topic that is relevant and sufficient | Authoritative selection |
| `resolution.social.topic_revealed` | This-turn structured reveal | Authoritative for this turn |
| `topic_pressure[*].last_answer` | Stored prior reply on a topic-pressure key | Authoritative continuity of what was just said |
| `topic_pressure_current` / `topic_pressure_last_topic_key` | Active pressure bucket | Authoritative current-thread pointer |
| `normalize_topic` | Maps player wording to a pressure key / cluster | Compatibility / pressure grouping, not answer authority |
| `is_valid_followup_question` | Short list of same-thread ellipsis shapes | Existing immediate-follow-up classifier |
| `_player_question_covers_stored_thread` | 4-letter token overlap, plus `he/she/him/her/you mean/...` | Lexical cover |
| `clue_knowledge` | Landed public clues for the scene | Authoritative player knowledge; matching is still lexical |
| Canonical lead registry / `pending_leads` | Official follow-up destinations (RC-21) | Authoritative leads; not this owner |
| `remember_recent_contextual_leads` | Prompt / mention hint | Non-authoritative |
| Answer-pressure follow-up flags | Prompt / escalation continuity | Compatibility |
| `recent_contextual_leads` | Mention memory | Non-authoritative |

`normalize_topic` already stems tokens and has Frontier-flavored clusters (`missing_patrol`, `crossroads_incident`). Those signals are for pressure keys, not answer selection. PR-BG did not promote them into a synonym table.

---

## 4. Compact Semantic Matrix

Authoritative contexts used: captain `watch_command`; kiln-porter `kiln_spur_closed` / barred-spur last-answer; landed `notice_patrol_route` / `clue_kiln_spur`.

| Class | Example | Ownership | Answer | Notes |
| --- | --- | --- | --- | --- |
| Direct lexical | `Who commands the watch?` | Continues | Answers via owned topic / realization | Tokens overlap `watch` |
| Reduced NP | `Why is the kiln spur barred?` | Continues | Fail-closed | Cause not in stored text (PR-AN) |
| Predicate reformulation | `Why was it shut down?` | Lost | Fail-closed | `shut`/`down` ≠ `barred`/`closed`; deferred |
| Pronoun he/she | `Who is he?` | Continues after repair | Answers if identity-sufficient | Existing cover + key retention |
| Recognized ellipsis | `Why is that?` / `How come?` / `Who is that?` | Continues after repair | Reuses last-answer when dimension allows | Repair surface |
| Richer ellipsis | `Why did that happen?` / `Who did it?` / `Where did they go?` | Not forced | Fail-closed | Deferred discourse |
| Topic switch | `What sits on the brazier?` | New owned topic | Answers mash | Old road thread does not stick |
| Unrelated | `How many barrels remain?` | None | Fail-closed | No inheritance |
| Ambiguous `Why did that happen?` | Two recent subjects possible | Not forced | Fail-closed | Recency is not proof |
| Public-clue lexical | `Where was the missing patrol last seen?` | Cover true | Fail-closed | Location sufficiency does not treat `northwest` as `north` (PR-AN) |
| Unavailable on correct thread | `Who ordered it?` | Thread may stay | Fail-closed | No official invented |
| Recovered T2 | missing patrol after watch | Switch | Fail-closed | Correct |

---

## 5. First Incorrect Decision

**Class D + cooperating key fragmentation.**

For recognized empty-subject follow-ups:

1. `_next_topic_to_reveal` correctly skips already-revealed owned topics.
2. `select_best_social_answer_candidate` path A can reuse `last_answer` only when `_player_question_covers_stored_thread` is true.
3. Empty-subject `"Why is that?"` has no leftover 4-letter tokens and is not in the `he/she/you mean` shortcut, so cover is false.
4. `normalize_topic` then writes a new key (`unknown_topic` / wording slug), so even a later cover cannot find the stored last-answer.

Existing authoritative context was already enough: current last-answer, current/previous topic-pressure key, speaker alignment, dimension sufficiency, and `is_valid_followup_question`.

Lexical overlap itself is not wrong for noun-bearing questions. The defect was applying it to turns the engine had already classified as empty-subject same-thread follow-ups.

---

## 6. Lexical vs Semantic Boundary

Preserved:

* Noun-bearing questions still need subject overlap with an owned topic, last-answer, or landed clue.
* `closed` / `barred` vs `shut down` is not normalized.
* `they` / `it` may keep a topic-pressure key through the existing anaphora bridge; they do **not** become last-answer authority.

Repaired:

* If the player asks a recognized empty-subject follow-up, the current last-answer may be reused when the speaker aligns and the stored text supports the asked dimension.

Deferred:

* Discourse reference (`Why did that happen?`, `Who did it?`, `Where did they go?`).
* Predicate synonymy.
* Embeddings / LLM topic classification.

---

## 7. Public-Clue Identity

Landed clues have canonical ids (`notice_patrol_route`, `clue_kiln_spur`). Follow-up matching still uses rendered `clue_knowledge` text through `_player_question_covers_stored_thread`. Owned-topic hay already includes `clue_id`, so a player who repeats that id can match; ordinary play does not.

No new knowledge graph was added. A later follow-up should not have to reproduce NPC wording if it repeats an authored noun already in the clue text (`patrol`, `kiln spur`). It still must not inherit a clue merely because one is landed.

`"Where was the missing patrol last seen?"` covers the notice text and then fails location sufficiency because `northwest` is not `\bnorth\b`. That is PR-AN, not a new continuity owner.

---

## 8. Pronoun / Ellipsis Findings

Ashen Thrones already has an immediate-follow-up mechanism: `is_valid_followup_question` plus topic-pressure anaphora and the `he/she/him/her` cover shortcut.

What was missing was connecting that classifier to last-answer reuse when no subject tokens remain.

Not added:

* a general pronoun resolver;
* treating every `it` / `they` question as the last topic;
* `"What happened next?"` as a new phrase rule (`social_probe` already has a separate `what happened then/next` probe-move).

---

## 9. Topic Switch and Ambiguity

Verified:

* `"What sits on the brazier?"` after a road last-answer reveals `mash_exists`.
* `"How many barrels remain?"` does not inherit the road thread.
* `"What are you doing about the missing patrol?"` after Thoran still refuses.
* `"No, I meant the refugees..."` still disables anaphora glue (`tests/test_social_topic_anchor.py`).
* `"What can you tell me about the eastern road?"` after missing-patrol still gets a new key.
* Ambiguous `"Why did that happen?"` is not forced onto the current last-answer.

---

## 10. Repair-Threshold Decision

A production repair **was** warranted.

* Multiple ordinary recognized follow-ups failed.
* They shared one first incorrect decision.
* Authoritative last-answer context was already present.
* A small deterministic repair could use `is_valid_followup_question` + empty subject tokens + current last-answer.
* Topic switching and ambiguity remain protected.

A repair was **not** warranted for `"Why was it shut down?"`, embeddings, or a second social router.

---

## 11. Production Changes

Generic production only:

1. `empty_subject_continues_current_thread` — true only for `is_valid_followup_question` with no remaining subject tokens.
2. `empty_subject_retains_topic_pressure_key` — also keeps the current pressure key for empty-subject `he/she/him/her`.
3. `register_topic_probe` uses (2) so `"How come?"` / `"Who is he?"` do not mint `unknown_topic`.
4. `select_best_social_answer_candidate` paths A and C treat (1) as last-answer cover. Path B (`clue_knowledge`) still requires lexical overlap.

No synonym table. No Frontier Gate nouns in the helper. No second router.

---

## 12. Generalization Evidence

Repaired examples that are not the recovered replay line:

* Kiln `"Why is that?"` / `"How come?"` after a barred-spur last-answer.
* `"Who is that?"` after Thoran.
* `"Who is he?"` after Thoran.

Contrasts:

* Explicit switch to mash.
* Unrelated barrel-count question.
* Ambiguous `"Why did that happen?"` remains refusal.
* `"Who ordered it?"` / `"Who is that?"` after a non-identity road fact fail closed.

---

## 13. Non-Invention Evidence

* No official invented for `"Who ordered it?"`.
* No identity invented for `"Who is that?"` against a barred-spur fact.
* `"Why was it shut down?"` does not become a closed-road answer by synonym.
* Recovered missing-patrol ask still cannot mint a captain patrol fact.
* PR-AU absence suite still passed.
* PR-AV topic-hook suite still passed.

---

## 14. Validation

| Surface | Result |
| --- | --- |
| Recovered missing-patrol follow-up | Still refuses |
| Direct lexical watch continuation | Still answers |
| Reduced NP cause ask | Fail-closed (no cause text) |
| Predicate reformulation `shut down` | Unsupported |
| Pronoun `Who is he?` | Continues when identity-sufficient |
| Recognized ellipsis | Continues current last-answer |
| Explicit topic switch | Mash replaces road |
| Unrelated question | Refuses |
| Ambiguous continuation | Not forced |
| Landed public-clue identity ask | Refuses without inventing an orderer |
| Owned-topic continuation | Preserved |
| Unavailable answer on resolved thread | Fail-closed |
| No invented identity / event / redirect | Held |
| PR-AV refusal-topic integrity | Passed |
| PR-AU grounded social absence | Passed |
| PR-AJ / RC-21 suites | Reconcile / paraphrase / most HTTP passed; see regressions |
| PR-AL / PR-AN | Passed |
| Directed social / topic-anchor / follow-up recovery | Passed |
| New PR-BG tests | 15 passed |

Isolation after repair: `artifacts/prbg_followup_topic_continuity/20260922T110500Z_after.md`.

Structural PASS is not treated as semantic playability.

---

## 15. Regressions

Not weakened:

* Topic-anchor corrections.
* PR-AL relevance.
* PR-AN dimension sufficiency.
* PR-AV empty/untrustworthy hooks.
* PR-AU fail-closed absence.
* Bound-speaker knowledge.

Observed and **not absorbed**:

* `tests/test_authoritative_lead_provenance_social_prose_non_ingestion.py::test_general_http_informational_social_prose_mints_no_lead` still expects stubbed trestle/coal-loft prose; the HTTP path fail-closes to `"I won't answer that about tide—not here."` This is PR-AU/AV grounded-absence vs a stubbed-invention fixture, not last-answer continuity. The empty-subject helper does not apply to `"How do you mark the tide here?"`.

Known unrelated reds from the prior handoff remain unabsorbed.

---

## 16. Accepted / Deferred Residue

Accepted / deferred:

* `"Why was it shut down?"` / other predicate synonyms.
* `"Why did that happen?"`, `"Who did it?"`, `"Where did they go?"`, `"What happened next?"` as discourse reference.
* `"What's going on?"` leftover token `going` keeping it outside the empty-subject helper.
* Public-clue location sufficiency not treating `northwest` as `north` (PR-AN).
* Identity sufficiency treating any named person as answering `"Who ordered Thoran...?"` when those nouns overlap (PR-AN).
* `normalize_topic` cluster aliases remaining pressure-only.
* Broader lead/clue overlap reduction.
* Opening `Gate Guard mutters` / `"Word is,"`.
* `"Gate Serjeant"` mapping.
* Evaluator lexical false negatives.
* `"The guard says"` absent-speaker label.

Do not start an embeddings, synonym, or discourse-model campaign from this residue.

---

## 17. Explicit Convergence Assessment

### A. Does a meaningful ordinary follow-up continuity defect reproduce?

**Yes.** Recognized empty-subject follow-ups lost last-answer continuity. The recovered missing-patrol line did not.

### B. What existing state owns conversational topic continuity?

`topic_pressure[*].last_answer` plus `topic_pressure_current` / `topic_pressure_last_topic_key`, with owned NPC topics as the reveal owner and `clue_knowledge` as the landed-clue owner. `is_valid_followup_question` is the immediate-follow-up classifier.

### C. What was the first incorrect decision?

Last-answer reuse required lexical cover even when the turn was already an empty-subject recognized follow-up, and `normalize_topic` fragmented the pressure key for those same turns.

### D. Was sufficient authoritative context already present?

**Yes.**

### E. Was production code changed?

**Yes.**

### F. If changed, what general semantic boundary was repaired?

A recognized empty-subject immediate follow-up may continue the current last-answer thread. Noun-bearing questions, synonym paraphrases, and unresolved pronouns may not.

### G. Which follow-up forms remain intentionally unsupported?

Richer discourse (`Why did that happen?`, `Who did it?`, `Where did they go?`) and predicate reformulation (`shut down` vs `closed` / `barred`). Cause asks against facts that do not encode cause remain fail-closed.

### H. Is this owner sufficiently converged for Product Realization?

**YES** — ordinary deterministic continuity is adequate. Richer discourse / semantic paraphrase is deferred. Stop opening paraphrase cycles on this owner.

---

## 18. Recommended Next Action

Follow-up topic continuity is closed for Product Realization. Do not select another follow-up-paraphrase or synonym cycle.

If the next slice stays in AI Experience, pick a **different** remaining sibling owner:

* Replay / opening `Gate Guard mutters` / `"Word is,"` (do not reopen PR-AI without new causal evidence)
* `"Gate Serjeant"` mapping
* Evaluator lexical false negatives on quiet listen and nothing-new
* `"The guard says"` generic absent-speaker label

Primary lane: AI Experience. Secondary lane: Gameplay.

No user decision is required.

---

## 19. Git / Worktree State

Branch: `feature/product-realization` at checkpoint `4c0a454`, plus uncommitted PR-AS through PR-BG work.

Not committed. Not pushed.

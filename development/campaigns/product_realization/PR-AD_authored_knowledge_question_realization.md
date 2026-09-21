# PR-AD — Gameplay: Authored-Knowledge Question Realization

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Report location: repository root, matching the Product Realization report convention (`PR-AA`, `PR-AB`, `PR-AC`).

Replay artifacts: `artifacts/prad_authored_knowledge/`

---

## 1. Executive Summary

PR-AD repaired the highest-leverage conversational-playability failure identified by PR-AC: when the player asks about or inspects a fact Ashen Thrones already owns, speaker-grounding / question validation / catalog fallback may no longer conceal that fact.

This is not a new knowledge store, a general dialogue rewrite, or a project-wide State ↔ Narration campaign. Existing owners remain authoritative: NPC topics, scene interactables, discoverable clues, social-exchange realization, and the existing fallback stack.

Player-facing behavior is demonstrably improved on the targeted slice:

- `"Who commands the watch here?"` can now express the authored Captain Thoran / watch-command fact.
- `"What is posted on the notice?"` / `"I read the notice board."` can now express `notice_patrol_route`.
- When those turns write the clue, the same turn's narration no longer silently omits it.
- Chapel-relic and Lirael questions still fail closed. Hidden facts stay hidden. No NPC is instantiated from narration.

Structural validation of the affected social / clue / authority / turn-pipeline files is green. Round #1 calibration corpus remains 13/13. Automated playability scores on some improved turns still FAIL because the evaluator treats a terse authored fact as unanswered or flags an unfinished quotation; those scores are supporting evidence only.

The product is still not fully playable as an ordinary conversational AI-DM. The dominant remaining obstacle is no longer authored-knowledge concealment. It is social-lock / stay-leave inversion: after the player learns the patrol fact, pursuit/travel still stays inside the interlocutor.

---

## 2. Starting Failure

PR-AC established that technical validation was green and semantic play was not. Representative path:

1. Player asks an authored question or inspects an authored object.
2. The engine often already owns the answer (`gate_guard.watch_command`, `notice_board` → `notice_patrol_route`).
3. The live model may be called successfully.
4. Speaker-grounding / question-rule validation rejects the first sentence.
5. Deterministic/catalog fallback emits a murmur bridge, `"I do not know enough"`, a dangling `mutters,`, or unrelated crowd template.

Representative PR-AC failures:

| Case | Player | Before |
| --- | --- | --- |
| R2-P1 T1 | Who commands the watch here? | Murmur bridge |
| R2-P3 T2 | what is actually posted on the notice? | `Gate Guard mutters,` |
| R2-MT01 T2–T3 | I read the notice board / what does it say? | Guard ignorance; clue never spoken |
| R2-MT02 T2 | Who commands the watch here? (Captain bound) | Captain ignorance despite authored topic |
| R2-MT04 T2–T3 | notice question / I read the notice board | Crowd template or ignorance while clue writes |

---

## 3. Execution-Path Findings

Phase 1 confirmed PR-AC's hypothesized stack and revised the implementation point.

### A. `"Who commands the watch here?"`

- Parsed as untargeted `question` / social exchange. No interlocutor required.
- Authoritative owner: `data/world.json` `gate_guard` topic `watch_command` = `"Captain Thoran commands the gate watch tonight."`
- `default_world()` does **not** carry this topic (`guard_captain.patrol` only). Live campaign reset preserves `data/world.json` NPCs.
- Live model is often rejected for `question_rule:social_exchange_first_sentence_not_speaker_grounded`.
- Neutral-bridge / retry fallback previously preferred murmur/ignorance.
- Additional defect: even when `topic_revealed` existed, `_stored_text_supports_dimension(..., "identity")` accepted only quoted / "known as" names, so `"Captain Thoran commands..."` was not treated as an identity answer.

### B. `"What is posted on the notice?"`

- Dialogue-first routing stole the line as a social question to the bound guard.
- Authoritative owner: `frontier_gate` interactable `notice_board` → clue `notice_patrol_route`.
- After routing repair, the turn becomes `investigate` and writes the clue. Before the late hook, speech remained `"I do not know enough"`.

### C. `"I read the notice board."`

- `INVESTIGATE_PATTERNS` lacked `read` / `reads` / `reading`.
- The line could remain unparsed or collapse into social fallback.
- After the verb was added, the action becomes `investigate` / `discover_clue` and writes `notice_patrol_route`. Realization still had to speak it.

### D. Bound NPC asked about the posted patrol

- Bound `guard_captain` is an addressable, not the topic owner. The watch-command row lives on `gate_guard`.
- Catalog ignorance replaced the known fact when the preferred live sentence failed speaker-grounding.
- After repair, a bound/relevant speaker can voice the existing interactable/topic fact without inventing an NPC.

Phase 1 also showed that applying authored realization *before* `_finalize_player_facing_for_turn` is insufficient. Final emission / sanitizer / speaker-grounding put the murmur back.

---

## 4. Root Cause Confirmed / Revised

PR-AC's hypothesized surface (social-exchange realization, speaker-grounding, catalog fallback, clue/interactable application) was correct but incomplete.

Confirmed / revised root cause:

1. **Identity matching was too strict** for authored unquoted names (`Captain Thoran`).
2. **Read/inspect verbs and notice-content questions were not routed** to the interactable owner.
3. **Fallback and late emission preferred murmur/ignorance** even when an existing owner already had a revealable answer.
4. **The first implementation seam was too early.** Authored realization inside `_build_gpt_narration_from_authoritative_state` was overwritten by `_finalize_player_facing_for_turn`.
5. **Investigate turns wrote clues onto session without putting the fact on `resolution`**, so a resolution-only Phase 3 hook missed them. `authoritative_clue_updates` had to be passed in.

No new authoritative knowledge store was required. The existing architecture can represent the behavior once realization consumes the existing owners after final emission.

---

## 5. Implementation

### Authored realization (existing owners)

`game/social.py`

- Identity dimension accepts unquoted `Captain|Serjeant|... Name` and consecutive proper names.
- `realize_authored_knowledge_answer` looks up:
  1. existing `select_best_social_answer_candidate` owners;
  2. the referenced interactable/clue;
  3. the current NPC's topics;
  4. present scene NPC topics, only after a current-speaker miss.
- A candidate is used only if it covers the question (or is an interactable the player named). Non-covering `topic_revealed` rows (e.g. east-lanes vs "who attacked") do not replace legitimate unknown fallback.
- `apply_authored_knowledge_realization_to_gm` replaces murmur/ignorance, or appends a written inspect-clue onto otherwise valid object narration.
- Investigate/discover turns speak the written clue as scene-grounded narration. They do not force an NPC to claim ignorance of a board the player is reading.

### Fallback suppression

- `game/social_exchange_emission.py`: neutral speaker-grounding bridge tries authored realization before the murmur line.
- `game/social_exchange_fallback_catalog.py`: retry fallback prefers a covering authored fact over catalog ignorance.
- `select_best` itself was **not** given a scene-wide topic scan. That scan belongs only in `realize_*`, because putting it in `_try_emit` stole interruption-progression tests.

### Intent / object routing (evidence-required)

- `game/intent_parser.py`: `read`/`reads`/`reading` investigate verbs; `recover_interactable_content_question` for "what is posted on the notice" family.
- `game/interaction_routing.py`: dialogue-first yields to that recover so a notice-content question is not stolen by the bound NPC.

### Late seam (required supporting change)

- `game/api.py`: apply authored realization after `_finalize_player_facing_for_turn` on both `/api/action` and `/api/chat` completion, passing `authoritative_clue_updates`.
- An earlier hook inside GPT narration build remains as a first attempt; the post-finalize hook is the one that survives emission.

### Narrow State ↔ Narration

Local to PR-AD authored-knowledge turns only: if the turn writes `notice_patrol_route` or resolves watch-command, player-facing text must communicate that substance. No project-wide narration-authority change.

---

## 6. Authority / Architecture Preservation

- No new fact database.
- Narration is not authoritative. Realization only restates existing topic/clue/interactable text.
- No NPC is instantiated from narration. Lirael still fails closed (R2-MT04 T1).
- Hidden facts (`hidden_facts` noble agent / Ash Cowl) are not selected.
- Chapel relic still produces the murmur bridge (no authored owner).
- RC-10 / RC-21 / validation hierarchy were not reopened.
- `pending_leads` was not migrated.
- Speaker invention is avoided: lines use the current grounded interlocutor, the topic-owning present NPC, or scene-grounded narration of the authored sentence.

---

## 7. Tests Added or Updated

Added: `tests/test_authored_knowledge_realization.py`

- Identity matcher accepts unquoted Captain Thoran.
- Watch-command realization from a present NPC topic.
- Notice question realization from the interactable/clue.
- Chapel relic does not invent a watch/notice answer.
- Hidden noble-agent fact is not selected.
- Neutral-bridge emits Thoran instead of murmur.
- Retry fallback prefers authored notice/patrol over `"I don't know"`.
- Bound Guard Captain can voice the existing watch-command topic.
- Phase 3: written `notice_patrol_route` is spoken.
- Parse/recover: read notice, mixed read, "what is posted", pressed notice question.
- HTTP (murmur-stubbed GPT): watch command, notice question, read-notice all communicate the authored fact.

Updated: `tests/test_intent_parser.py`

- `test_read_notice_board_maps_to_investigate`

Existing tests were not weakened. Scene-wide topic matching was kept out of `select_best` after it broke interruption-progression and unknown-fallback contracts. Inspect realization appends onto valid object narration so the desk action-outcome contract still mentions the desk.

---

## 8. PR-AC Before / After Evidence

Original cases were not rewritten. Same fixtures: `data/validation/semantic_playability_calibration_r2/scenarios.json`.

After replay: `artifacts/prad_authored_knowledge/prac_replay_after/runs/20260919T231846Z_*`

| Case | Turn | Before (PR-AC) | After (PR-AD) | Human |
| --- | --- | --- | --- | --- |
| R2-P1 T1 | Who commands the watch here? | Murmur bridge | Gate Guard voices Captain Thoran / watch command | Pass (automated FAIL: unfinished quote on that run; quote close since hardened) |
| R2-P1 T2 | Who stole the chapel relic? | Murmur bridge | Murmur bridge | Pass — no authored owner |
| R2-P3 T2 | what is actually posted on the notice? | `Gate Guard mutters,` | Authored northwest mud-track fact; clue written | Pass (automated FAIL is evaluator false negative) |
| R2-P4 T1 | I glance at the notice. | Crowd template, no board | Patrol fact now present; still appends forced "Board, runner, or road" | Partial |
| R2-MT01 T2 | I read the notice board. | Guard ignorance | Full notice + northwest track; `notice_patrol_route` written | Pass |
| R2-MT01 T3–T4 | What does it say / what's being done? | Ignorance | Authored patrol fact; Captain can speak it | Pass |
| R2-MT01 T7 | I'll follow the northwest track. | Social lock; stay at gate | Still social lock; scene remains `frontier_gate` | Fail — out of PR-AD slice |
| R2-MT02 T2 | Who commands the watch? (Captain bound) | Captain ignorance | Still Captain `"I don't know"` on that turn | Residual |
| R2-MT02 T4 | patrol posted on the board | Ignorance | Captain voices northwest track | Pass |
| R2-MT02 T6 | who commands it | Late recovery | Gate Guard voices Thoran; clue written | Pass |
| R2-MT04 T1 | Where can I find Lirael? | No NPC created | No NPC created | Pass — RC-21 preserved |
| R2-MT04 T2–T3 | notice question / I read the notice | Crowd / ignorance | Authored patrol fact + clue write | Pass (evaluator false negative) |

---

## 9. Validation Results

| Gate | Result |
| --- | --- |
| New PR-AD tests | Pass (`tests/test_authored_knowledge_realization.py`) |
| Affected social-exchange / speaker-grounding / fallback | Pass |
| Intent / exploration / clue / interactable | Pass |
| RC-21 destination-redirect + state-authority + narrative-authority | Pass |
| Turn-pipeline shared (including desk action-outcome and filler lock) | Pass |
| Combined focused affected files | Green, 0 failed |
| Round #1 semantic calibration corpus | 13/13 (`artifacts/prad_authored_knowledge/round1_calibration/`) |
| Relevant PR-AC replay | Material improvement on targeted class; see §8 |
| Full authoritative suite | Ran after implementation. Focused gameplay/authority files stayed green. Remaining reds are protected-replay / mutation-attribution artifact tests (BY3/BY4/BZ + frontier-gate long-session golden replay) that detect the intended player-facing change. Those expectations were not weakened. Not used as proof of semantic success. |

Structural PASS is not semantic playability. Automated `semantic_result=FAIL` on some successful authored turns is evaluator residue (unfinished quote, or a terse fact that does not share enough player tokens).

Full-suite determination: BY3/BY4/golden-replay failures are authoritative *replay/attribution* invariants, not stale playability gold. They fail because realization now speaks authored facts on previously-fallback turns. Refreshing those artifacts is a later expectation-maintenance slice, not a reason to revert PR-AD.

---

## 10. Remaining Semantic Failures

- Bound `guard_captain` can still say `"I don't know"` to watch-command on the first ask (R2-MT02 T2) even though a present `gate_guard` topic owns the fact. Later turns recover.
- Glance/observe can still route as `observe` and then force `"Board, runner, or road"` (R2-P4). The authored fact now appears, but the fork remains.
- Stay/leave / pursuit: after the player learns the northwest track, `"I'll follow the missing patrol rumor..."` remains social-locked at `frontier_gate` (R2-MT01 T7).
- Some authored lines still use the `"Word is,"` / `mutters` envelope. Playable, not elegant.
- `narration_ctx_…` lead ingestion from prose still occurs (R2-MT02 T7). Deferred.
- Evaluator false negatives on terse authored answers.

---

## 11. Deferred Findings

Unchanged from PR-AC unless noted:

- `compat_pending_lead_needed` still keys off a scene target only.
- Intent parsing still reads `pending_leads` as the pursuit surface.
- Broader lead/clue overlap reduction.
- House Verevin / rooftop invention.
- Forced "Board, runner, or road" fork (still visible after glance).
- Travel inversion / dialogue-lock (now the recommended next slice).
- Scene-transition Unicode / operator-encoding.
- PR-AB tooling / product-integrity.
- General prompt rewrite, NPC dialogue redesign, knowledge-system redesign.

---

## 12. Recommended Next Product Slice

**Stay/Leave Intent and Social-Lock Override.**

Observed after PR-AD: the player can now learn the notice/patrol fact and ask about it, then cannot act on it. R2-MT01 T7 remains the highest-impact ordinary-play failure in the replayed set.

Not chosen merely because it was on the PR-AC menu. Chosen because authored-knowledge concealment is no longer the dominant bottleneck, and the next thing a player tries — follow the lead — is still captured by social engagement.

Secondary residue, do not start as the next campaign unless stay/leave evidence is weaker than expected:

- Interactable glance/observe routing and the forced board/runner/road fork.
- Bound-addressable vs topic-owner mismatch for watch-command on `guard_captain`.

Do not open a general State ↔ Narration campaign. The local PR-AD guarantee covered the slice that was blocking play.

---

## 13. Git / Worktree State

The worktree was dirty before PR-AD and remains dirty.

PR-AD production files:

- `game/social.py`
- `game/social_exchange_emission.py`
- `game/social_exchange_fallback_catalog.py`
- `game/intent_parser.py`
- `game/interaction_routing.py`
- `game/api.py`

PR-AD tests / report / handoff / artifacts:

- `tests/test_authored_knowledge_realization.py` (new)
- `tests/test_intent_parser.py` (updated)
- `PR-AD_authored_knowledge_question_realization.md` (new)
- `docs/NEXT_SESSION.md` (updated)
- `artifacts/prad_authored_knowledge/` (new)

Pre-existing dirt from earlier validation, policy, replay, PR-AC, and runtime session files was not erased or normalized. Campaign replay reset local session/world playthrough residue the same way PR-AC did.

No commit or push.

---

## 14. Confidence

**Medium-high** on the targeted failure class.

High that the representative watch-command and notice contracts now reach the player in deterministic tests and in the PR-AC replay. Medium that every bound-NPC first ask will realize the fact (R2-MT02 T2 residue). High that authority boundaries were preserved. Medium that the next slice recommendation will remain correct after more play — stay/leave is the strongest remaining ordinary-play blocker in the replayed evidence.

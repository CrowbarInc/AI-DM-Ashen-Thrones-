# PR-AI — Gameplay / AI Experience: Bound Speaker Knowledge Resolution

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Replay artifacts: `artifacts/prai_bound_speaker_knowledge/`

---

## 1. Executive Summary

PR-AI repaired the highest-leverage ordinary-play failure after PR-AH: a legitimately bound NPC could answer `"I don't know"` on the first relevant question even when existing authored NPC/topic ownership already had an answer.

The representative Guard Captain / watch-command case is repaired. It is not the proof of the contract.

The engine now distinguishes:

- **world / engine knowledge** (a fact exists somewhere);
- **NPC-authorized knowledge** (this bound speaker has an authoritative path to that fact);
- **player knowledge** (what the player has already learned).

A bound speaker can communicate a matching owned or identity-resolved topic, or existing scene-public clue/interactable knowledge. Binding alone does not grant every fact the engine can retrieve. Legitimate ignorance remains. No new knowledge store and no new NPC identity system were added.

---

## 2. Starting Failure

After PR-AH, ordinary play could learn the patrol fact, travel, investigate, return, observe without invented confrontation, and reread the board. The next natural social act failed.

PR-AH extended replay T4:

> Player: I turn to the Guard Captain. "What's being done about the missing patrol?"
> GM: Guard Captain shakes their head. "I don't know."
> Interlocutor: `guard_captain`

PR-AD R2-MT02 T2, with the captain already bound:

> Player: Who commands the watch here?
> GM: Guard Captain shakes their head. "I don't know."

Later turns sometimes recovered via a landed notice clue or live-model elaboration. The player should not need a warm-up exchange.

---

## 3. Guard Captain First-Ask Execution Trace

Traced before production changes.

| Stage | Result |
| --- | --- |
| Raw input | `I turn to the Guard Captain. "What's being done about the missing patrol?"` or `Who commands the watch here?` |
| Parsed intent | `question` / social exchange |
| Scene | `frontier_gate` |
| Bound interlocutor | `guard_captain` (scene addressable; name Guard Captain; roles include `guard`, `captain`) |
| World NPCs present | `gate_guard`, `gate_serjeant`, `tavern_runner` — **no** `guard_captain` world row |
| Topic owner | `gate_guard.watch_command` = `"Captain Thoran commands the gate watch tonight."` |
| Addressable vs owner | Different IDs, names, and stores. BX5 keeps them distinct for addressing. |
| Social topic reveal | `_next_topic_to_reveal` on the addressable row finds **no topics** |
| Reply kind | `refusal` |
| Catalog fallback | `Guard Captain shakes their head. "I don't know."` |
| PR-AD late realization | `realize_authored_knowledge_answer` **did** find `watch_command` (scene-wide topic scan, and/or `"captain"` in the player line covering the fact) |
| Communication check | `_text_communicates_authored_fact` treated `"captain"` in the speaker name as proof the Thoran fact was already spoken |
| Final text | Ignorance survived |

Answers to the campaign's trace questions:

1. Yes — the engine could find the authored watch-command fact.
2. Yes — `watch_command` / notice clue were the matching topics depending on wording and whether the notice was already known.
3. Yes — the bound speaker was `guard_captain`.
4. Yes — runtime addressable identity (`guard_captain` / Guard Captain) differs from the topic owner (`gate_guard` / Gate Guard). Captain Thoran appears only in topic text.
5. Yes — authored lookup found the answer; later communication detection refused to replace ignorance.
6. Social-engine ignorance ran first because the addressable had no topics. Realization then failed to override it.
7. First-turn binding was not a special case. The same skip happened on later bound asks of watch-command (R2-MT02 T2–T3). Later recovery happened when a *different* fact (notice clue) did not share the speaker-name token.
8. Multiple causes: identity mismatch, topic-owner lookup by exact id, refusal fallback, and communication-detection false positive.

---

## 4. Root Cause

**Confirmed, not revised:** bound-addressable vs topic-owner mismatch, compounded by ignorance-as-communication.

| Cause | Role |
| --- | --- |
| Identity / addressability | `guard_captain` is a present addressable, not the world NPC that owns `watch_command`. |
| Topic-owner matching | Exact-id restrict skipped `gate_guard`. Unrestricted scene scan could still retrieve the fact. |
| Fallback / ignorance precedence | No topics on the addressable → `reply_kind=refusal` → catalog `"I don't know."` |
| Communication detection | `"I don't know"` plus speaker name `"Guard Captain"` was treated as already communicating `"Captain Thoran commands..."`. |
| First-ask ordering | Not a special first-turn gate. The skip was the communication check after realization had the fact. |

The helper `realize_authored_knowledge_answer` already passed in isolation (PR-AD `test_bound_captain_can_realize_watch_command_topic`). Live `/api/chat` failed because `apply_authored_knowledge_realization_to_gm` returned early.

---

## 5. Existing NPC Identity Contract

Recovered; no second identity system.

| Surface | Owner |
| --- | --- |
| Canonical world NPC id | `world.npcs[].id` via `npc_dict_by_id` / `get_world_npc_by_id` |
| Display name | `world.npcs[].name` or addressable `name` |
| Aliases | `world.npcs[].aliases` and scene addressable `aliases` |
| Address roles | scene `addressables[].address_roles` (used by addressing uniqueness) |
| Bound interlocutor | `interaction_context.active_interaction_target_id` |
| Canonical promotion map | `scene_state.promoted_actor_npc_map` via `canonical_interaction_target_npc_id` |
| Presence | world `location` + scene addressables + `active_entities` |

BX5 remains in force: `gate_guard` and `guard_captain` are distinct addressing identities. PR-AI does not equate `guard_captain == Captain Thoran` in generic code.

---

## 6. Existing Topic / Knowledge Ownership Contract

Recovered; no new store.

| Path | Existing owner |
| --- | --- |
| NPC topics | `world.npcs[].topics` / `knowledge` (`id`, `text`, optional `clue_id`) |
| Topic reveal | `_next_topic_to_reveal` on the speaker row |
| Authored realization | `realize_authored_knowledge_answer` / `apply_authored_knowledge_realization_to_gm` |
| Scene-public clues | `session.clue_knowledge` in `select_best_social_answer_candidate` |
| Interactables | scene interactable → discoverable clue |
| Hidden world facts | `scene.hidden_facts` — not selected as NPC answers |
| Player knowledge | clue writes / lead registry, distinct from NPC topics |

There is no topic-level `shared` / `public` / `hidden` flag on NPC topic rows. Shared/public behavior that already existed is clue_knowledge and interactable matching. Role/faction topic sharing is not an implemented contract (`knowledge_scope` is empty on live gate NPCs and is prompt-facing).

---

## 7. Bound Speaker vs Topic Owner Analysis

They are different surfaces.

- **Bound speaker** is the addressable interlocutor for this turn.
- **Topic owner** is the world NPC row that stores the topic.

The intended relationship is not “every present NPC may voice every present topic.” It is:

> the bound speaker may voice a fact if they have an authoritative path to it.

That path may be exact identity, promoted canonical id, name/alias equality, or a **unique** addressing-token match against a present world NPC using existing id/name/alias/role/address_role tokens. If uniqueness fails, lookup fails closed to the speaker's own row.

Live Frontier Gate: addressable `guard_captain` uniquely shares the addressing token `guard` with present world NPC `gate_guard` (alias `guard`). That is the general path to `watch_command`. It is not a hardcoded Captain alias.

---

## 8. Authorized Knowledge Semantics

Used in production:

**A. Authorized bound speaker.** Present/addressable + bound + matching question + authoritative path + available answer → communicate the answer. Generic ignorance must not outrank it.

**B. Unauthorized bound speaker.** Binding does not grant unrelated world facts. The NPC may refuse or voice only their own related authorized knowledge.

**C. Unbound.** Do not invent a speaker from a topic owner in another scene. Present topic owners may still voice an untargeted authored question (PR-AD), using the owner as speaker.

**D. Absent.** Location-mismatched topic owners are skipped. They do not become the speaker.

**E. Multiple owners.** Unique addressing-token match fails closed when more than one present world NPC shares the token. Exact id still wins for the bound speaker's own topics.

**F. Topic not found.** Fail honestly. No model-knowledge synthesis in the deterministic path.

**G. Player discovery.** NPC authority and player knowledge remain distinct. Landed `clue_knowledge` may be spoken because that public/reconciled path already existed. Hidden facts are not auto-exposed.

---

## 9. Legitimate Ignorance Semantics

Hard requirement, tested.

If the bound speaker has no authoritative path to the requested fact, the response must not contain that fact. Catalog ignorance/refusal remains legitimate. Chapel-relic and hidden-token questions still fail closed.

---

## 10. Implementation

Generic engine only: `game/social.py`.

1. **`authoritative_knowledge_npc_ids_for_speaker`** — exact id, promoted map, name/alias equality, unique addressing-token match.
2. **`_match_present_npc_topic_authored_knowledge`** — when a speaker is bound, only those ids. Unrestricted present-NPC scan remains only for unbound questions (PR-AD).
3. **`_text_communicates_authored_fact`** — concealment/ignorance is not communication. Speaker identity tokens are not distinctive fact evidence.
4. **`classify` / `_stored_text_supports_dimension("general")`** — general questions no longer require Cinderwatch tokens (`patrol`/`gate`/`milestone`) to accept a stored fact. Cover checks still apply.

Canonical scene/world content was not modified.

Social-engine `_next_topic_to_reveal` still uses the bound speaker's own row. That avoids giving a bound addressable another NPC's *first* topic on unrelated questions. Authorized covering answers are supplied by late realization, which is the seam that actually reached the player after PR-AD.

---

## 11. First-Ask Precedence Repair

Not a “first question” special case.

The first relevant ask failed because realization already had the fact and then declined to replace ignorance. Concealment short-circuit plus identity-resolved topic lookup make the first covering ask work whether or not a previous social turn occurred.

---

## 12. Response Realization

Reused PR-AD's `format_authored_knowledge_realization_line` / `apply_authored_knowledge_realization_to_gm`. No parallel dialogue answer system.

The bound speaker remains the voicing identity. Topic source may be an identity-resolved world NPC. Paraphrase is allowed by the existing mutters/`Word is,` envelope; it must not expand to unauthorized facts on the deterministic path.

---

## 13. Guard Captain Before / After

| Turn | Before | After |
| --- | --- | --- |
| Bound first ask `Who commands the watch here?` | `"I don't know."` | Guard Captain voices Captain Thoran / watch command |
| Bound first ask `Who's in charge of the watch?` | not previously proven | Thoran / watch command |
| Ordinary-play `What's being done about the missing patrol?` after reading the board | `"I don't know."` | Bound captain answers from authorized notice/watch material; interlocutor `guard_captain` |

Live extended replay T9 (`artifacts/prai_bound_speaker_knowledge/extended_replay/runs/20260920T112741Z_R2-MT01-AI/transcript.md`):

> "We're maintaining a strict watch along the northwest mud track, where the patrol was last seen," says the guard captain...

No `"I don't know."` Interlocutor stayed `guard_captain`. Continuation T10 investigated the serjeant's roster board.

---

## 14. Absent-Speaker Sibling Check

PR-AH residue: investigate at `old_milestone` could answer `"The guard says"` with no guard present.

**Distinct owner.** Fallback `speaker_label` defaults to `"The guard"` when no NPC is resolved (`game/social.py` format helper and `game/social_exchange_policy.py`). That is generic speaker labeling on a non-social/investigate path, not topic-owner selection of an absent NPC.

PR-AI lookup already skips off-scene topic owners and does not bind them. The probe's old-milestone investigate did not emit `"The guard says"`. Broader narration cleanup is deferred.

---

## 15. Scenario-Independent Generalization Fixtures

Hard gate. Vocabulary is unrelated to Cinderwatch. Scene `amber_quay`; NPCs `orchard_keeper`, `shrine_caretaker`, `ferry_master`.

| Test | Result |
| --- | --- |
| 1. Owned topic, first ask | PASS — floodgates/first light; ignorance replaced on HTTP |
| 2. Unrelated topic | PASS — keeper does not receive bell recasting |
| 3. Two NPCs, separate knowledge | PASS |
| 4. Absent topic owner | PASS — off-scene keeper is not the speaker |
| 5. Alias / display identity | PASS — `grove warden` alias stays `orchard_keeper` |
| 6. Legitimate ignorance | PASS — brass token stays hidden |
| 7. Authorized shared clue_knowledge | PASS — existing public clue path preserved |
| 8. No speaker | PASS — absent owner is not invented as speaker |
| 9. Hidden / conditioned | PASS for scene `hidden_facts`. No topic-level hidden flag exists; documented, not invented |
| 10. Natural paraphrase | PASS — “What hour do you open those floodgates?” |

HTTP tests exercise `/api/chat` with stubbed GPT, not an isolated helper the live pipeline bypasses.

---

## 16. Anti-Overfitting Audit

Searched PR-AI generic production changes (`game/social.py` new helpers) for:

`guard_captain`, `Captain Thoran`, `frontier_gate`, `Cinderwatch`, `watch_command`, `notice_patrol_route`, `old_milestone`.

| Surface | Result |
| --- | --- |
| `authoritative_knowledge_npc_ids_for_speaker` | No calibration identifiers |
| `_knowledge_identity_tokens` | Generic id/name/alias/role tokens |
| Bound-topic restrict | Identity-set based, not Captain-specific |
| `_text_communicates_authored_fact` | Concealment + speaker-token exclusion. Still contains pre-existing PR-AD non-distinctive tokens including `patrol`/`gate`/`watch` |
| `_stored_text_supports_dimension("general")` | **Removed** Cinderwatch-token dependence for general questions |
| Rank regex `Captain\|Serjeant\|...` | Pre-existing PR-AD identity dimension; not introduced here |

No phrase whitelist for Guard Captain questions. No hardcoded Captain aliases. No first-ask exception. No “first NPC in the list” ordering trick. Synthetic tests do not copy Frontier Gate lexical structure.

---

## 17. Tests Added or Updated

Added: `tests/test_bound_speaker_knowledge_resolution.py`

No existing expectations were weakened. PR-AD authored-knowledge tests remain.

---

## 18. Continued Multi-Turn Replay

Scenario: `data/validation/prai_bound_speaker_knowledge/scenarios.json` (`R2-MT01-AI`)

After: `artifacts/prai_bound_speaker_knowledge/extended_replay/runs/20260920T112741Z_R2-MT01-AI/transcript.md`

| Turn | Player | Result |
| --- | --- | --- |
| T2 | read notice | `notice_patrol_route` |
| T3 | follow northwest track | `frontier_gate` → `old_milestone` |
| T5 | examine milestone | prints clue; no inscription |
| T6 | head back | authoritative return (evaluator FAIL on stock leave line is known residue) |
| T7 | look around | grounded gate; no invented confrontation |
| T8 | reread board | authored notice |
| T9 | first captain ask | bound `guard_captain`; authorized answer; not `"I don't know"` |
| T10 | check roster board | investigate continuation |

Ordinary play next becomes uneven where the repaired captain speech is ingested as `narration_ctx_…` false leads, and where investigating the mentioned roster board invents unauthored names.

---

## 19. Freeform Social-Knowledge Probe

Artifact: `artifacts/prai_bound_speaker_knowledge/freeform_probe/20260920T112834Z_probe.md`

| Turn | Player | Result |
| --- | --- | --- |
| 1 | first ask, captain, watch charge | Thoran; bound `guard_captain`; not ignorance |
| 2 | follow-up “what's being done” without reading the board | ignorance — no covering owned topic/clue yet |
| 3 | chapel relic | legitimate refusal; no watch-command leak |
| 4 | runner asked who commands the watch | runner's `patrol_rumor`, **not** Thoran |
| 5 | stew | runner stays on stew (price elaboration is residual) |
| 7 | What's nearby? | empty social beat; known local-observation residue |
| 8 | look around | grounded; no interlocutor |
| 10 | investigate at old_milestone | no `"The guard says"` |
| 12 | “Gate Serjeant” / census route | addressing bound `gate_guard` and voiced watch_command — distinct addressing residue |

---

## 20. Validation Results

| Gate | Result |
| --- | --- |
| New PR-AI tests | Pass (`tests/test_bound_speaker_knowledge_resolution.py`, 18 tests) |
| PR-AD authored knowledge | Pass |
| PR-AE stay/leave | Pass (one HTTP seed hit the known Windows `PermissionError` on retry it passed) |
| PR-AF arrival/destination | Pass |
| PR-AG generalized exit | Pass |
| PR-AH grounded observation | Pass |
| Intent / social / dialogue routing / speaker identity / BX5 | Pass |
| Clue / exploration / state authority / narrative authority | Pass |
| Round #1 semantic calibration corpus | 13/13 (`artifacts/prai_bound_speaker_knowledge/round1_calibration/`) |
| Extended R2-MT01-AI replay | Captain first ask repaired; continuation turn taken |
| Freeform social-knowledge probe | Diagnostic; first-ask Thoran and runner non-leak hold |
| Full authoritative suite | Not re-run as a complete 6,450-test pass |

Structural PASS is not semantic playability. Known protected-replay / mutation-attribution reds were not refreshed.

---

## 21. Remaining Semantic Failures

- Follow-up paraphrases that do not overlap an owned topic or a landed public clue can still refuse (`What are you doing about the missing patrol?` before the board is read).
- `narration_ctx_…` lead ingestion from social prose fired on the repaired captain answer.
- Investigating the mentioned roster board can invent unauthored names.
- Observe fallback grammar can still stack clauses.
- Authored `mutters` / `"Word is,"` envelope remains.
- Local observation questions (`What's nearby?`) can still collapse.
- Addressing `"Gate Serjeant"` can still resolve to `gate_guard`.
- Evaluator FAIL on the stock leave line remains.

---

## 22. Deferred Findings

Unchanged unless noted:

- Absent-speaker `"The guard says"` default label — distinct from PR-AI topic ownership.
- `compat_pending_lead_needed` still keys off a scene target only.
- Intent parsing still reads `pending_leads` as the pursuit surface.
- Broader lead/clue overlap reduction.
- House Verevin / rooftop invention.
- Filling other stub scenes.
- New authoritative knowledge store.
- Project-wide State ↔ Narration.
- Protected-replay baseline refresh.
- General prompt rewrite or NPC personality redesign.

---

## 23. Recommended Next Product Slice

**Social-prose lead ingestion (`narration_ctx_…`) creating false authority.**

Chosen from ordinary-play evidence after the repaired captain exchange. R2-MT01-AI T9 wrote `narration_ctx_frontier_gate_were_maintaining_a_strict` from the captain's authorized speech. That is false world authority minted from narration.

Not chosen because it was on a menu. Chosen because authored speaker/topic resolution is no longer the dominant bottleneck, and the next thing the repaired turn does is pollute the lead/clue surface.

Secondary residue, do not start unless ingestion evidence is weaker than expected:

- Investigate of mentioned-but-unstubbed surfaces (roster board names).
- Addressing `gate_serjeant` vs `gate_guard`.

Do not open a general State ↔ Narration campaign. Do not reopen PR-AH perception or PR-AG travel.

---

## 24. Git / Worktree State

The worktree was dirty before PR-AI and remains dirty.

PR-AI production files:

- `game/social.py`

PR-AI tests / report / handoff / artifacts:

- `tests/test_bound_speaker_knowledge_resolution.py` (new)
- `tools/run_prai_freeform_probe.py` (new)
- `data/validation/prai_bound_speaker_knowledge/` (new)
- `PR-AI_bound_speaker_knowledge_resolution.md` (new)
- `docs/NEXT_SESSION.md` (updated)
- `artifacts/prai_bound_speaker_knowledge/` (new)

Canonical scene JSON was not modified.

Replay and the freeform probe reset local runtime documents (`data/session.json`, `data/world.json`, `data/combat.json`, `data/session_log.jsonl`).

Pre-existing dirt from earlier validation, policy, replay, and PR-AC through PR-AH was not erased.

No commit or push.

---

## 25. Confidence

**Medium-high** on the targeted failure class.

High that first-ask watch-command / bound-captain ignorance was the communication-detection plus identity-restrict mismatch, and that deterministic and HTTP tests plus the live T9 replay show the repair. High that runner/keeper negative tests preserve legitimate ignorance. Medium that every natural paraphrase of an owned topic will match without a landed public clue. Medium that the next-slice recommendation will remain correct after more play — `narration_ctx_…` ingestion is the strongest new ordinary-play contaminant on the repaired turn.

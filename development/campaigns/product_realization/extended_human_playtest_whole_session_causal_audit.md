# Extended Human Playtest — Whole-Session Causal Audit

Date: 2026-09-23
Era: Product Realization
Primary lane: AI Experience
Secondary lane: Gameplay

This audit is not an implementation. No production code changed. PR-BK is earned as a future slice and is not implemented here.

Evidence: `artifacts/human_playtests/20260923_post_mixed_action_repair_extended_playtest/`
Derived audit files: `artifacts/human_playtests/extended_playtest_causal_audit/`

Prior audit `human_playtest_mixed_action_ownership_compound_turn_audit.md` stands. This session has no listen or eavesdrop turn. The listen repair is not the cause of these replies.

---

## 1. Executive summary

Eight log entries, seven player turns, all at `frontier_gate` on Day 1. No clue, lead, revealed topic, interactable resolution, or scene change.

Nine player-facing failures reduce to five root causes:

1. Untargeted inspection prints the first visible fact (turns 1 and 2).
2. There is still no diegetic time of day (turns 2 and 4 cannot be answered).
3. The curfew question never bound `notice_board`, so the model wrote a statute (turn 3).
4. A social turn with no NPC still spoke as `The guard`, and the next bare "you" was dialogue-locked to the only world NPC (turns 4 and 5). Turns 6 and 7 then correctly stayed with that NPC.
5. Model reply text is stored in `topic_pressure.last_answer` and later selected as a structured fact (turns 5–7, with latent copies on turns 1, 3, and 4).

The immediate next direction is cause 5. Unsupported prose became reusable answer authority. That is Option 8, generative-context integrity. It is a narrow existing-owner repair, not a new knowledge system. It was not coded in this audit: a safe change has to keep authored follow-ups (PR-BG) and must not treat `Word is` as the bug (PR-BI).

---

## 2. First incorrect decision by turn

Opening (turn 0) is correct.

### Turn 1 — incorrect

Player looks at banners and asks about heraldry.

```
FIRST INCORRECT DECISION: untargeted inspection rendered visible_facts[0] as the result
OWNER: referenced-surface inspection
FUNCTION / FILE: render_referenced_surface_inspection_line / _surroundings_clause in game/referenced_surface.py
EVIDENCE: referenced_surface_authority untargeted; empty target; final_emitted_source global_scene_fallback; player text is the notice-board visible fact. Banners exist only as opening scenery. No blazon is authored. A separate model paragraph that says the heraldry cannot be made out was stored and not shown.
DOWNSTREAM EFFECTS: searched_targets stamp; latent last_answer. Does not cause turns 3–7.
WOULD FIXING THIS EARLIEST DECISION REMOVE OTHER SYMPTOMS?: the twin notice-board line on turn 2, yes. Not the social chain.
```

Classification: existing-owner presentation defect, plus missing heraldic content if a real identification were required. The content gap does not justify printing a different object.

### Turn 2 — incorrect

Player looks at the sky and asks the time of day.

```
FIRST INCORRECT DECISION: same untargeted template. Independently, no authoritative time exists
OWNER: referenced-surface inspection for the displayed sentence; no clock owner for the question
FUNCTION / FILE: game/referenced_surface.py; session.current_date / time_pressure (PR-BE)
EVIDENCE: authority untargeted; final_emitted_source anti_reset_local_continuation_fallback; identical notice-board sentence; current_date Day 1; time_pressure is a chat counter
DOWNSTREAM EFFECTS: topic key topic:despite_look_make is created and overwritten on turn 3
WOULD FIXING THIS EARLIEST DECISION REMOVE OTHER SYMPTOMS?: it removes the false notice-board answer. It does not create a time of day.
```

Classification: combination. Routing/fallback defect for the sentence. Missing world-state capability for the question. Not the same capability as waiting.

### Turn 3 — incorrect

Player steps to the notice board and asks what the curfew rules say.

```
FIRST INCORRECT DECISION: the turn has no resolution kind and is labeled downtime, so notice_board is never selected
OWNER: intent selection
FUNCTION / FILE: intent classification on the log entry (labels ["downtime"]; resolution.kind absent)
EVIDENCE: interactable id notice_board, aliases include "notice", "board", and "curfew notice". resolved_interactables stays []. Discoverable clue notice_patrol_route is not added. Player text and last_answer state dusk-until-dawn, fines, detainment, unrest, and bandits. narrative_authority_failed is false
DOWNSTREAM EFFECTS: last_answer on the sky topic; the player’s next question assumes that curfew and those bandits
WOULD FIXING THIS EARLIEST DECISION REMOVE OTHER SYMPTOMS?: a real investigate would reveal the patrol-track clue, not a statute. The invented hours would not be authored either way. Later captain talk does not read this last_answer.
```

Sentence ledger for the shown answer:

| Sentence | Class |
| --- | --- |
| A notice board is being read | A, as an object the player named. The action did not resolve it |
| Curfew requires civilians off the streets from dusk until dawn | D |
| The measure curbs recent unrest and bandit activity | D. `unrest` clock is 0 |
| Violators face fines or detainment until morning | D |
| The rule accompanies taxes and a posted… | taxes and a posted warning are A as list items. The sentence is truncated model prose |

The longer stored paragraph adds a northwest patrol sighting (compressed clue text, not landed) and a serjeant enforcing the edicts (D). Integrity checked narrative authority and did not fail it.

### Turn 4 — incorrect

Player asks anyone near the board how many hours until dusk.

```
FIRST INCORRECT DECISION: no NPC resolved, then the retry catalog spoke as "The guard"
OWNER: empty-identity speaker label on the social fallback catalog
FUNCTION / FILE: speaker_label / npc_display_name_for_emission in game/social_exchange_policy.py; catalog line in game/social_exchange_fallback_catalog.py
EVIDENCE: canonical reason open_social_solicitation; social.npc_id null; target_resolved false; hint says no matching NPC; retry_failure_reasons question_rule:social_exchange_first_sentence_not_speaker_grounded; prepared_answer_fallback_text is the player line; fallback_kind retry_escape_hatch
DOWNSTREAM EFFECTS: no interlocutor is stored. The player’s next line uses "you". The hours question also has no clock (cluster 2), but the defect that reached the player is the speaker
WOULD FIXING THIS EARLIEST DECISION REMOVE OTHER SYMPTOMS?: the phantom guard line. It does not stop turn 5’s sole-NPC lock by itself
```

This is the PR-BJ helper, now player-facing. It is a display label on a null id, not a new NPC. `scene_state` does not gain a guard. PR-BJ is not reopened as a speaker-paraphrase cycle. Its premise that the helper did not reach the player is no longer true for this path.

### Turn 5 — incorrect

Unaddressed quote about the curfew incident.

```
FIRST INCORRECT DECISION: route reason no_addressable_target still bound tavern_runner through dialogue lock
OWNER: dialogue-lock target fill
FUNCTION / FILE: resolve_dialogue_lock_action_target_id, called from game/interaction_routing.py when canonical target_actor_id is empty
EVIDENCE: routed_via_dialogue_lock true; addressed_actor_source dialogue_target_resolution; action_id question_tavern_runner; social contract interlocutor_status none and continuity_status broken; world.npcs contains only tavern_runner
DOWNSTREAM EFFECTS: runner voice for turns 5–7; model captain paragraph stored and cited on turn 6 as topic_pressure:last_answer
WOULD FIXING THIS EARLIEST DECISION REMOVE OTHER SYMPTOMS?: the runner’s captain claims on turns 5–7, yes, as this session went. A later named question to the runner could still hit cluster 5
```

The binding is not continuity with "The guard". Turn 4 stored no id. The lock is the sole-world-NPC fill the previous audit deferred for question-only turns. It happened again, on a follow-up the player addressed to whoever had just spoken.

The refusal hint and `topic_revealed: null` are then ignored by realization. The shown `Word is` sentence is model stage direction and an unsupported captain referral. The formatter is not the first decision. The authored runner topic (patrol never returned from the old milestone) is not used.

### Turn 6 — incorrect answer, consistent address

```
FIRST INCORRECT DECISION: escalation treated the previous model paragraph as an existing answer and the new paragraph’s tail was shown as Word is
OWNER: topic-pressure last_answer selection
FUNCTION / FILE: game/social.py structured-fact selection (source topic_pressure:last_answer); storage in _commit_topic_progress
EVIDENCE: route_reason active_interlocutor_followup; prior_same_dimension_answer_exists true; social_answer_retry_candidate_source topic_pressure:last_answer; anchor text is turn 5’s captain paragraph; reply_kind answer via force_partial_answer; shown sentence is the last sentence of this turn’s stored last_answer; topic_revealed null; hint still says no new information
DOWNSTREAM EFFECTS: official-talk and roster-board claims persist in last_answer and recent_contextual_leads
WOULD FIXING THIS EARLIEST DECISION REMOVE OTHER SYMPTOMS?: the false partial answer. The interlocutor would remain if turn 5 stands
```

Address continuity after the lock is working as designed. The knowledge claims are not.

### Turn 7 — incorrect answer, consistent address

```
FIRST INCORRECT DECISION: this turn’s model paragraph was emitted as a structured fact
OWNER: same last_answer / structured-fact path
FUNCTION / FILE: game/social.py; final_emitted_source structured_fact_candidate_emission
EVIDENCE: reply_kind refusal; topic_revealed null; completeness skipped with reason strict_social_structured_or_bridge_source; narrative_authority_failed false; shown clause is the last sentence of last_answer ("don't expect an easy ear without some introduction")
DOWNSTREAM EFFECTS: introduction requirement exists only in prose and last_answer
WOULD FIXING THIS EARLIEST DECISION REMOVE OTHER SYMPTOMS?: this line. Not the earlier lock
```

---

## 3. Contamination

Yes. See `cross_turn_causal_graph.md`.

Unsupported model prose did become persistent reusable context: `topic_pressure.last_answer` on every player turn that minted or updated a topic, plus `recent_contextual_leads`. It did not enter `lead_registry`, `clue_knowledge`, or `revealed_topics`.

It was treated as a structured fact. Turn 6 records the previous paragraph as `topic_pressure:last_answer`. Turn 7’s emission source is `structured_fact_candidate_emission`. Turn 6’s shown sentence is a slice of the paragraph just stored, which is the same defect one step earlier in the same turn.

Integrity did not prevent invention. `narrative_authority_failed` is false on every entry. Invented-outcome flags stay false while dusk-to-dawn rules and captain access are stated. Completeness failures on turns 3, 4, and 5 were not repaired. Turn 7 skipped completeness because the selector had already called the text a structured fact.

The narrow owner is the pair `_commit_topic_progress` (stores any non-cutoff reply) and the social selector (reads `last_answer` as a fact). PR-BI’s cutoff exclusion does not cover this. Deleting all conversational memory would over-reach. Blacklisting "Word is" would not.

---

## 4. What stays settled

- The listen-question repair. This session never listens.
- Compound N-action execution stays deferred. These failures are not unexecuted second actions.
- Refugee-origin content stays unauthored. This session does not ask for it.
- PR-AS through PR-BI owners are not reopened.
- PR-BJ’s speaker matrix is not reopened. One premise is revised: the empty `The guard` default reached the player on a no-target retry hatch. That is cluster 4, recorded here, not a new paraphrase cycle.
- PR-BE’s missing clock stays missing. Do not add one for this transcript.
- `Word is` on an authored fact stays aesthetic.

Question-only sole-NPC collapse remains the deferred residue. This session is a second reproduction, on a bare "you" after a null speaker, not a reason to start crowd simulation.

---

## 5. Product Realization decision

Immediate next direction: **Option 8 — generative-context integrity repair.**

Backlog, not now:

- Option 4 remains real for time-of-day queries, and is still not a clock implementation.
- Cluster 1 (untargeted stock) is a small existing-owner presentation fix.
- Cluster 3 needs the existing investigate owner to win, and still must not add curfew statutes.
- Cluster 4’s label is small; the dialogue-lock half is the already deferred sole-NPC policy.
- Option 3, compound turns, is not what this session failed at.
- Option 5, a knowledge graph, is not required to stop false facts from being stored.
- Option 7, content expansion, would not make the captain promises true.

PR-BK is earned. It is not implemented in this audit.

Proposed title: `PR-BK — Unauthored reply text must not become a reusable structured fact`

Lane: AI Experience.

Invariant: `topic_pressure.last_answer` may keep conversational continuity, but it is selectable as a structured fact only when the stored text is an authored reveal or an equivalent already-authoritative payload. A model paragraph with `topic_revealed` null is not that payload.

Out of scope: world clock, compound-turn execution, NPC cognition, crowd simulation, new routers, curfew or heraldry content, deleting `Word is`, renaming the latent guard label, and sole-NPC policy.

Repair threshold for doing that work inside this audit was not met as an implementation: three executable probes were specified (`diagnostic_probes.md`) and not landed as tests, and the provenance check has to be written so PR-BG’s authored follow-ups still resolve. No test run was required.

---

## 6. Closeout answers

A. Nine player-facing failures: notice-board reply to heraldry; the same reply to time of day; invented curfew statute; `The guard says` with no NPC; Tavern Runner bound on an unaddressed you; captain referral inside `Word is`; official-talk / willingness claim; introduction claim; prose progress with empty clue and lead registries.

B. Five independent root causes. Turns 6 and 7 are not extra causes.

C. Turn 0, the opening, is correct. No later player turn is correct. Turns 6 and 7 address the runner consistently after the bad lock, and their claims are still incorrect.

D. Earliest incorrect decision: turn 1, untargeted inspection appending the notice-board fact. It does not cause the social chain.

E. Yes. Turn 3’s statute shapes the player’s next question. Turn 5’s paragraph is turn 6’s structured-fact candidate and the reason escalation forces a partial answer.

F. Yes. `topic_pressure.last_answer` and `recent_contextual_leads`.

G. Yes. Turn 6 candidate source `topic_pressure:last_answer`. Turn 7 `structured_fact_candidate_emission`. Neither turn has `topic_revealed`.

H. No. Narrative-authority failure stays false on every turn. Some completeness failures are recorded and not repaired. Turn 7 skips completeness because the source was already classed as structured.

I. Yes. Tavern Runner’s only authored topic is the milestone patrol sentence. The captain claims, curfew cause, appointment, and introduction are outside it. The captain has no authored availability.

J. Yes, on turn 5. Turns 6 and 7 continue that binding on purpose.

K. Cosmetic fallback, not a phantom NPC. `npc_id` stays null and no guard row is created. The line still asserts that a guard spoke.

L. Heraldry was an untargeted investigate. The untargeted template appends `visible_facts[0]`. The model’s "cannot make out the heraldry" paragraph was stored and discarded from the player line.

M. The time question took that same template (`anti_reset_local_continuation_fallback`). There is also no clock, so a correct owner still could not answer with an hour.

N. Curfew is authored only as a topic listed on the board. Hours, penalties, unrest, and bandits are not authored.

O. No. `guard_captain` is an addressable with presence `active` and no world-NPC topics. Accessibility, willingness, roster-board watch, and introduction are model prose.

P. All of the apparent progress. State records chats, two search stamps, and a runner interlocutor. Registries stay empty.

Q. Missing capabilities: diegetic time (turns 2 and 4), curfew statute text even after a correct inspect (turn 3), and any knowledge that would let the runner describe the captain. Those are not the false sentences. The false sentences are owner defects.

R. Listen repair, deferred compound execution, deferred sole-NPC question collapse, PR-BE clock, PR-BI envelope, and PR-AS through PR-BH/PR-BI conclusions stay valid. The deferred note that model prose can sit in `last_answer` is now a player-facing cross-turn fact, so it is no longer "do not open."

S. No settled PR-AS through PR-BJ owner is reopened. PR-BJ’s "did not reach the player" result is superseded for the empty-label fallback path only.

T. Option 8. Generative-context integrity.

U. Yes. Title: `PR-BK — Unauthored reply text must not become a reusable structured fact`. Not implemented in this audit.

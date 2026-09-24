# Root cause clusters

Five clusters. Turns 6 and 7 are continuity after cluster 4, and their false claims are cluster 5.

## Cluster 1 — untargeted look answers with the first visible fact

```
CLUSTER: Untargeted inspection stock
ROOT OWNER: referenced-surface inspection (`game/referenced_surface.py`, `render_referenced_surface_inspection_line` / `_surroundings_clause`)
FIRST INCORRECT DECISION: an empty target is classified `untargeted`, then the player-facing line appends `visible_facts[0]` (the notice board) as what the look resolved
AFFECTED TURNS: 1, 2
PLAYER-FACING SYMPTOMS: heraldry and time of day both receive the notice-board sentence, prefixed with "You look again. Nothing new resolves into evidence."
DOWNSTREAM CHAINS: both action ids are stamped in `searched_targets`. Turn 1 also stores an unshown banner paragraph in `last_answer` (cluster 5, latent)
EXISTING CAPABILITY OR MISSING CAPABILITY: existing owner. Banners are opening scenery, not an interactable. Heraldic identity is missing content. The wrong sentence is the template, not a missing blazon
GENERALITY: any untargeted investigate in a scene with visible facts
SEVERITY: high for trust. The line presents unrelated authored text as the result of the look
SMALLEST GENERAL REPAIR, IF ANY: when authority is `untargeted`, do not append an unrelated visible fact as the thing that was seen. A no-match line is enough. Do not add banner content
ARCHITECTURE EXPANSION REQUIRED?: no
SHOULD PRODUCT REALIZATION ADDRESS NOW?: not first. It does not feed the later captain chain
```

## Cluster 2 — no current time of day

```
CLUSTER: Missing diegetic time
ROOT OWNER: none. PR-BE settled that `current_date` and `time_pressure` are not a world clock
FIRST INCORRECT DECISION: there is no authoritative time to return. Turn 2's displayed sentence is cluster 1. Turn 4's displayed sentence is cluster 4
AFFECTED TURNS: 2 (sky), 4 (hours until dusk)
PLAYER-FACING SYMPTOMS: neither question receives a time. Neither question invents an hour
EXISTING CAPABILITY OR MISSING CAPABILITY: missing world-state capability
GENERALITY: any "what time is it" / "how long until dusk" question
SEVERITY: ordinary gap. Deferred since PR-BE
SMALLEST GENERAL REPAIR, IF ANY: none inside this audit. Do not invent a clock to answer this transcript
ARCHITECTURE EXPANSION REQUIRED?: yes, a diegetic clock, if Product Realization later chooses that capability
SHOULD PRODUCT REALIZATION ADDRESS NOW?: no
```

## Cluster 3 — notice inspection never bound

```
CLUSTER: Authored interactable skipped; model wrote the notice
ROOT OWNER: intent selection. Turn 3 `resolution.kind` is absent and `intent_classification.labels` is `downtime`
FIRST INCORRECT DECISION: "notice board" / "curfew rules" / "What do they say?" did not become `investigate` on `notice_board`, despite authored id and aliases
AFFECTED TURNS: 3
PLAYER-FACING SYMPTOMS: dusk-to-dawn curfew, fines, detainment, unrest, bandits, and a truncated sentence. The stored paragraph also moves the patrol clue and an enforcing serjeant into the answer
DOWNSTREAM CHAINS: that paragraph becomes `last_answer` on the sky topic key `topic:despite_look_make`. The player then asks what incident caused the curfew and supplies the bandit premise
EXISTING CAPABILITY OR MISSING CAPABILITY: existing investigate owner was not selected. Even a correct bind would reveal `notice_patrol_route`, not a curfew statute. The statute text is missing content. The hours and penalties are model invention that integrity did not flag (`narrative_authority_failed` false)
GENERALITY: a movement-plus-question line that misses an authored interactable and is then narrated freely
SEVERITY: high. The player received specific rules that do not exist
SMALLEST GENERAL REPAIR, IF ANY: not a curfew phrase list. The miss is "named authored interactable plus a content question did not reach investigate." A repair that special-cases this sentence fails the anti-overfitting standard
ARCHITECTURE EXPANSION REQUIRED?: no for binding an already-authored interactable. Yes if the goal is a full statute the scene does not contain
SHOULD PRODUCT REALIZATION ADDRESS NOW?: after cluster 5. Do not add the invented hours to the scene
```

## Cluster 4 — unresolved address still speaks

```
CLUSTER: No-target social speech, then sole world NPC
ROOT OWNER: turn 4, `speaker_label` in `game/social_exchange_policy.py` plus the fallback catalog. Turn 5, `resolve_dialogue_lock_action_target_id` in `game/interaction_context.py`, called from `game/interaction_routing.py` when `target_actor_id` is empty
FIRST INCORRECT DECISION: turn 4 resolved no NPC (`npc_id` null, hint says no clear target) and still emitted `The guard says`. Turn 5's route reason is `no_addressable_target` and `routed_via_dialogue_lock` is true, so the only world NPC (`tavern_runner`) became `question_tavern_runner`
AFFECTED TURNS: 4 and 5. Turns 6 and 7 correctly keep that interlocutor (`active_interlocutor_followup`, continuity preserved)
PLAYER-FACING SYMPTOMS: an anonymous guard answers; the next "you" is Tavern Runner; later captain talk is in that voice
DOWNSTREAM CHAINS: the player continues with "you" because a guard appeared to speak. The lock does not continue a guard id, because none was stored. It binds the runner. Correcting turn 4's label would not by itself stop a later bare "you" from taking the sole world NPC. Correcting the lock stops turns 5–7's runner speech
EXISTING CAPABILITY OR MISSING CAPABILITY: both behaviors already exist. The empty-identity `The guard` helper is the PR-BJ latent default, now player-facing on a retry escape hatch. Sole-NPC fill of an unresolved question is the residue the mixed-action audit deferred. This was not a listen turn
GENERALITY: any social turn with no `npc_id` that reaches the catalog; any unaddressed question while one world NPC is in the scene
SEVERITY: high. It creates a speaker the state does not contain, then a different speaker the player did not name
SMALLEST GENERAL REPAIR, IF ANY: a no-target social resolution should keep the existing no-target hint and should not interpolate `speaker_label`. Dialogue lock should not replace `no_addressable_target` with the sole world NPC. That second change is the deferred question-only collapse, not a one-line label edit
ARCHITECTURE EXPANSION REQUIRED?: no for the label. The lock change is an existing-owner policy change with a wide social surface. It is not ambient crowd simulation
SHOULD PRODUCT REALIZATION ADDRESS NOW?: the label is newly evidenced and small. It is not the immediate slice, because the captain facts survive only through cluster 5
```

## Cluster 5 — model prose becomes a reusable fact

```
CLUSTER: Generative reply text stored as `topic_pressure.last_answer` and selected as a structured fact
ROOT OWNER: `game/response_policy_enforcement.py` `_commit_topic_progress` writes `reply[:480]` into `last_answer`. `game/social.py` deterministic answer selection then returns `source: topic_pressure:last_answer` as `structured_fact`
FIRST INCORRECT DECISION: reply text is stored as `last_answer` with no check that the text is an authored reveal. PR-BI only excludes interruption cutoffs
AFFECTED TURNS: stored on 1, 3, 4, 5, 6, 7. Consumed as a fact candidate on 6 (`social_answer_retry_candidate_source`: `topic_pressure:last_answer`). Emitted as `structured_fact_candidate_emission` on 7. Turn 6's shown sentence is the tail of that turn's own stored paragraph. Turn 3's invention is also shown directly because cluster 3 left no owner to fail-close
PLAYER-FACING SYMPTOMS: `Word is, the tavern runner shakes their head...`; `Word is, he's the one who handles official talk...`; `Word is, but don't expect an easy ear without some introduction.`
DOWNSTREAM CHAINS: turn 5 prose becomes turn 6's retry anchor and flips escalation to `force_partial_answer` (`prior_same_dimension_answer_exists`). Turn 6 and 7 paragraphs become `recent_contextual_leads`. They do not enter `lead_registry` or `revealed_topics`
EXISTING CAPABILITY OR MISSING CAPABILITY: existing owners. PR-BG may reuse a last answer for a real follow-up. PR-BI already refused cutoffs. This session shows ordinary model prose taking the authored-fact path. `narrative_authority_failed` stayed false on every turn. Completeness on turn 7 was skipped because the source was structured-fact / bridge
GENERALITY: any social or narration reply that commits topic progress, then a later or same-turn selector treats that string as a fact. Not specific to this scene
SEVERITY: highest. Unsupported sentences become the next turn's answer authority
SMALLEST GENERAL REPAIR, IF ANY: do not select `last_answer` as a structured fact unless the stored text came from an authored reveal (`topic_revealed`, clue, or equivalent). Do not delete topic memory wholesale. Do not blacklist wording. Do not remove `Word is` from authorized facts
ARCHITECTURE EXPANSION REQUIRED?: no knowledge graph. A provenance bit on the existing `last_answer` write is enough to test
SHOULD PRODUCT REALIZATION ADDRESS NOW?: yes. This is the immediate slice
```

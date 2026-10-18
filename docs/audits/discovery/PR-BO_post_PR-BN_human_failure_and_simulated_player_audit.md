# PR-BO - Post-PR-BN Human Failure and Simulated-Player Audit

Date: 2026-09-27
Current HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` (`PR-BN bounded DM improvisational authority`)
Target human session: `cde2e71187a6e1f17e7480dc`

## 1. Executive Summary

The latest genuine human playthrough occurred after PR-BN and still failed almost immediately. The failure is not best explained as "PR-BN is broken everywhere"; it is better explained as "PR-BN's positive improvisation lane was not meaningfully invoked by the runtime paths the human exercised." The player asked natural questions about visible invented/advertised fiction - banners, noble colors, a townhouse, a runner selling rumors, a place to sleep, and a moneylender's house - but the runtime usually routed those turns into transition/exploration/social-fallback machinery that either emitted generic scene snippets or replaced generated candidates with sealed fallbacks.

PR-BN added a typed lane for `improvisation_proposals`, validation, promotion, prompt projection, retry suppression, and final-emission recognition. In this session, the bounded-improvisation ledger remained empty: `session.payload.bounded_improvisation.entries == []`, `rejected == []`, and `last_bounded_improvisation_promotion.accepted_count == 0`. The player-visible failures therefore cannot be treated as evidence that accepted PR-BN improvisation was rejected or failed to persist. They show that ordinary play still reaches older authority/fallback/action-resolution contracts before the new lane can help.

Turn quality after the opening was poor: 0 of 7 human input turns were satisfactory. The opening was vivid and playable, but every subsequent player turn was degraded or failed. The dominant bottlenecks were:

1. Affordance and action-resolution failure: the fiction advertised inspectable heraldry, paid rumors, lodging, doors/windows, and a moneylender's house, but the runtime could not reliably resolve those natural interactions.
2. Authority routing failure: mundane descriptive questions were not routed into bounded incidental invention; they were treated as scene transition, strict/social ambiguity, passive observation, or generic exploration.
3. Final-emission degradation: candidate responses were repeatedly replaced by `global_scene_fallback`, `passive_scene_pressure_fallback`, `action_outcome_upstream_prepared_repair`, or `anti_reset_local_continuation_fallback`.
4. Context and continuity collapse: after an early unwanted scene transition to `market_quarter`, later references to the runner, guard, townhouse, and moneylender's house became detached from useful target binding.

The automated PR-BN tests passed because they test the bounded-improvisation primitive in isolation: explicit proposal objects, persistence, prompt projection, rejection of unsafe categories, retry suppression, and final-emission recognition. They do not test whether live gameplay routes ordinary human curiosity into that primitive, whether the model actually emits proposals on real turns, whether final emission preserves good candidate text in multi-turn play, or whether advertised scene affordances are actionable.

Simulated-player infrastructure exists, but it is only partially suitable as a pre-human gate. The older playability runner is scripted and can pass despite bad player-intent outcomes. The newer reactive/adversarial runner can persist on unresolved questions, but it is deterministic, scenario-authored, capped at six turns, and limited to a small set of probes. Verdict: useful with modest improvement, not yet reliable as a broad substitute for human integration testing.

## 2. Latest Human-Session Provenance

The latest genuine human session is the canonical runtime session in `data/session.json` and `data/session_log.jsonl`.

- Session id: `cde2e71187a6e1f17e7480dc`
- Time range: `2026-09-27T19:56:20.233214Z` through `2026-09-27T20:04:55.462181Z`
- Session saved at: `2026-09-27T20:04:55.394181Z`
- Human input turns: 7, plus the empty start-campaign opening entry
- Starting scene: `frontier_gate`
- Ending scene: `market_quarter`
- Visited scenes: `frontier_gate`, `market_quarter`
- Clock progression: `time_pressure` reached `7`
- PR-BN commit: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`, committed `2026-09-26T19:18:20-04:00`

This session is after PR-BN by both commit position and wall-clock evidence. It is newer than the earlier packaged human bundle `artifacts/human_playtests/20260926_post_pr_bk_latest_human_playtest`, which covered session `735ebd1cfb4567c4f97df6dc` on `2026-09-26T01:44:59Z` to `2026-09-26T01:54:18Z`. It is also newer than the older handoff text that referenced session `6010c8dfe3c0dcae2ea49469` from `2026-09-26T18:16:51Z` to `2026-09-26T18:20:52Z`.

Primary source artifacts:

- `data/session.json`
- `data/session_log.jsonl`
- `data/world.json`
- `docs/audits/PR-BN_bounded_dm_improvisational_authority.md`
- `game/bounded_improvisation.py`
- `tests/test_bounded_improvisation_authority.py`

Evidence limitations:

- Raw prompts were not retained as standalone prompt artifacts.
- Raw model completions were not retained as standalone completion artifacts, though `gm_output` and final-emission metadata are present in the session log.
- Historical per-turn snapshots are not separately available beyond the per-entry log payloads and final persisted state.

## 3. Turn-by-Turn Human Playtest Reconstruction

### Entry 0 - Opening

- Timestamp: `2026-09-27T19:56:20.233214Z`
- Player input: empty start-campaign request
- Interpreted intent: campaign opening
- Resolution: `scene_opening`, `campaign_start_opening_scene`, `success=True`
- Model route: `gpt-4.1-mini`, primary turn
- Final source: `opening_deterministic_fallback`
- Final-emission lineage: `opening_fallback_selection`, `sealed_fallback_replacement`, `finalize_packaging`
- PR-BN activation: no bounded-improvisation promotion
- Final output: a strong opening at Cinderwatch's eastern gate with frayed banners, noble townhouse colors, a threadbare watcher, tavern runner, and notice board.
- State mutation: active opening scene established; time pressure began advancing.

Assessment: Satisfactory as an opening. It created multiple concrete affordances, but those affordances became liabilities when the runtime could not honor them.

### Entry 1 - Heraldry on Banners

- Timestamp: `2026-09-27T20:00:24.470335Z`
- Player input: "I look to the banners as I enter Cinderwatch, first the frayed ones, then those of the noble house. What does the heraldry on each look like?"
- Interpreted intent: `scene_transition`, action id `i_look_to_the_banners_as_i_enter_cinderw`
- Candidate/final path: generated candidate replaced by `global_scene_fallback`
- Final-emission lineage: `response_type_repair`, `prepared_emission_selection`, `sealed_fallback_replacement`, `finalize_packaging`, `post_gate_mutation_detected`
- Final output: "The new ground shows itself: canvases snap in the wind over a market built from salvage timber and old stone"
- State mutation: transitioned from `frontier_gate` to `market_quarter`
- PR-BN activation: none; ledger stayed empty

Assessment: Failed. The player asked for visible heraldic description. A competent DM minimally needed to describe both sets of heraldry, state that one is too weathered to read, or ask for an inspection roll if needed. Instead the system changed scenes and ignored the question.

Likely categories: A PR-BN path never invoked; H intent/parsing failure; I action-resolution failure; J affordance failure; F final-emission degradation.

### Entry 2 - Ask Runner About Townhouse

- Timestamp: `2026-09-27T20:01:26.148298Z`
- Player input: asks the tavern runner about the remarkably well-kept townhouse
- Interpreted intent: `question`, action id `question_what_can_you_tell_me_about_that`, `success=False`
- Target actor: unresolved in the concise extraction even though player named the runner
- Final source: `global_scene_fallback`
- Final output: "Salvage-timber awnings snap in the wind over armed merchants and hungry townsfolk sharpens when you look again, and a moneylender's house flies noble colors above the market stalls still competes for notice."
- PR-BN activation: none

Assessment: Failed. The player made a social inquiry to an advertised NPC about an advertised building. A competent DM needed either a diegetic answer from the runner, a bounded rumor/claim, or a source-limited refusal plus a useful next lead. The response is ungrammatical scene restatement.

Likely categories: A PR-BN path never invoked; G prompt/context failure; H intent/target failure; J affordance failure; F final-emission degradation.

### Entry 3 - Ask Runner for Rumors

- Timestamp: `2026-09-27T20:02:29.226020Z`
- Player input: asks runner what is going on in Cinderwatch
- Interpreted intent: `observe`, action id `i_address_the_runner_again_this_time_ask`
- Final source: `passive_scene_pressure_fallback`
- Final-emission metadata: `visibility_replacement_applied=True`
- Final output: "As you watch the scene, a moneylender's house flies noble colors above the market stalls."
- PR-BN activation: none

Assessment: Failed. The runner had been introduced as hawking paid rumors; asking for rumors is the exact advertised interaction. A competent DM needed to let the runner answer, name a price, give a rumor, or refuse in character. The system instead treated the social request as observation.

Likely categories: A PR-BN path never invoked; H intent/parsing failure; J affordance failure; F final-emission degradation; G context failure.

### Entry 4 - Search for Lodging

- Timestamp: `2026-09-27T20:03:05.442532Z`
- Player input: "Unable to catch the runner's attention I move on, searching the city for somewhere I can sleep tonight."
- Interpreted intent: `investigate`, action id `unable_to_catch_the_runners_attention_i_`
- Final source: `action_outcome_upstream_prepared_repair`
- Final output: "You look again. Nothing new resolves into evidence. What you can actually see is a moneylender's house flies noble colors above the market stalls."
- PR-BN activation: none

Assessment: Failed. The player changed goals naturally after the runner failed. A competent DM needed to move toward an inn, shelter, watchhouse, temple, street camp, or state that lodging is not obvious and offer a search direction. The runtime converted lodging search into repeat visual inspection.

Likely categories: I action-resolution failure; J affordance failure; H intent failure; F final-emission degradation.

### Entry 5 - Ask What Noble Colors Are

- Timestamp: `2026-09-27T20:03:36.955072Z`
- Player input: `What colors are "noble colors"?`
- Interpreted intent: no resolution/action id
- Final source: `anti_reset_local_continuation_fallback`
- Final-emission metadata: `visibility_replacement_applied=True`
- Final output: `The guard says, "I do not know enough to answer that."`
- PR-BN activation: none

Assessment: Failed. This is exactly the kind of low-consequence incidental fact PR-BN should have enabled if routed there. A competent DM could simply say "deep green and tarnished gold," "maroon and silver," or "too rain-darkened to make out clearly." Instead an off-target guard refuses a visual-description question.

Likely categories: A PR-BN path never invoked; H intent failure; B misclassified authority is possible but not directly evidenced; J affordance failure; F final-emission degradation.

### Entry 6 - Slam Through Front Door

- Timestamp: `2026-09-27T20:04:23.446336Z`
- Player input: sprints shoulder-first toward the moneylender's front door
- Interpreted intent: no resolution/action id
- Final source: `anti_reset_local_continuation_fallback`
- Final-emission metadata: `tone_escalation_failed=True`, `visibility_replacement_applied=True`
- Final output: `The guard says, "I do not know enough to answer that."`
- PR-BN activation: none

Assessment: Failed. This is a physical action needing adjudication. A competent DM needed to resolve impact, require a check, describe guards reacting, or block based on physical layout. The system emitted an irrelevant ignorance line.

Likely categories: I action-resolution failure; H intent failure; F final-emission degradation; G context failure. This is not primarily a bounded-improvisation problem.

### Entry 7 - Push Guard and Leap Through Window

- Timestamp: `2026-09-27T20:04:55.462181Z`
- Player input: pushes guard and attempts to leap through a moneylender's window
- Interpreted intent: no resolution/action id
- Final source: `anti_reset_local_continuation_fallback`
- Final-emission metadata: `tone_escalation_failed=True`, `visibility_replacement_applied=True`
- Final output: `The guard says, "I do not know enough to answer that."`
- PR-BN activation: none

Assessment: Failed. The player escalated to a disruptive physical act. A competent DM needed to resolve opposition, collision, window access, guard response, or initiative. The response repeats the same irrelevant guard fallback.

Likely categories: I action-resolution failure; F final-emission degradation; H intent failure; K model-quality is not primary because final source shows fallback replacement.

## 4. Turn Quality Assessment

Opening: satisfactory.

Human turns after opening: 0 satisfactory, 2 degraded, 5 failed.

- Entry 1: failed - question about visible heraldry became scene transition.
- Entry 2: failed - NPC question became ungrammatical scene restatement.
- Entry 3: failed - advertised rumor NPC interaction became passive observation.
- Entry 4: failed - lodging search became "look again" at moneylender house.
- Entry 5: failed - visual color question became guard ignorance fallback.
- Entry 6: failed - physical door crash became guard ignorance fallback.
- Entry 7: failed - physical guard/window action repeated the same fallback.

The session validates the human report that the game still breaks down almost immediately. It also shows the breakdown is not one isolated social-speaker bug; it spans observation, social inquiry, travel/search, visual clarification, and physical action.

## 5. PR-BN Path Activation Analysis

PR-BN's bounded-improvisation mechanisms did not materially activate.

Runtime state at session end:

```json
{
  "bounded_improvisation": {
    "version": 1,
    "entries": [],
    "rejected": []
  },
  "last_bounded_improvisation_promotion": {
    "promoted_count": 0,
    "rejected_count": 0,
    "accepted_count": 0,
    "promoted_ids": []
  }
}
```

The strongest PR-BN candidate turn was Entry 5: "What colors are noble colors?" This is low-consequence sensory/local-color invention. It should plausibly have reached bounded incidental detail authority. Instead it reached anti-reset local continuation fallback and visibility replacement.

No evidence shows accepted bounded proposals being rejected downstream, promotion failing, or prompt projection failing. The absence of accepted/rejected entries indicates the system did not get as far as PR-BN's typed authority primitive for these turns.

## 6. Failure Taxonomy

| Turn | Quality | Categories | Evidence |
| --- | --- | --- | --- |
| 1 heraldry | Failed | A, H, I, J, F | `scene_transition`; `global_scene_fallback`; ignored heraldry |
| 2 townhouse | Failed | A, G, H, J, F | unresolved target; `success=False`; `global_scene_fallback` |
| 3 rumors | Failed | A, H, J, F | runner request became `observe`; `passive_scene_pressure_fallback` |
| 4 lodging | Failed | H, I, J, F | lodging search became repeated visual evidence line |
| 5 noble colors | Failed | A, H, J, F | no PR-BN entry; anti-reset fallback; guard ignorance |
| 6 door crash | Failed | H, I, F | no action resolution; tone/visibility failure; irrelevant guard |
| 7 guard/window | Failed | H, I, F | repeated anti-reset fallback |

PR-BN-specific taxonomy:

- A. PR-BN path never invoked: dominant for mundane description/social-detail turns.
- B. Misclassified authority: plausible at the user-experience level, but not proven by recorded PR-BN decision data because no proposal was evaluated.
- C. Valid improvisation rejected: not evidenced.
- D. Promotion failure: not evidenced.
- E. Retry degradation: not dominant in metadata; `model_retry_attempt` evidence did not show retry loops as the core failure.
- F. Final-emission degradation: strongly evidenced by repeated fallback sources and mutation lineage.
- G. Prompt/context failure: evidenced by off-target scene/target continuity.
- H. Intent/parsing failure: strongly evidenced by scene transition and observe/investigate misroutes.
- I. Action-resolution failure: strongly evidenced on lodging and physical-action turns.
- J. Affordance failure: strongly evidenced by advertised but unsupported runner, heraldry, colors, lodging, house/door/window.
- K. Model-quality failure: secondary; candidate generation existed, but final emitted sources frequently point to fallback replacement.

## 7. Shared Architectural Bottlenecks

Ranked by explanatory coverage:

1. Affordance/action-resolution contract gap. The runtime advertises ordinary interactions that it cannot honor: visible heraldry, noble colors, tavern rumors, lodging, moneylender-house entry, doors/windows, and guard collision.
2. Live authority routing gap. PR-BN provides a proposal lane, but real turns do not reliably become proposal-bearing bounded-improvisation candidates. Ordinary human curiosity is still routed into old paths.
3. Final-emission fallback dominance. Multiple turns had `gate_terminal_repair`, sealed fallback replacement, visibility replacement, or anti-reset fallback as the final player-visible source.
4. Intent and target binding weakness. The runner and guard/townhouse context repeatedly failed to bind in a way that produced useful response obligations.
5. Evaluator/test weakness. Current synthetic evidence can miss "technically related but useless" responses and does not force human-like persistence across open-ended play.

## 8. Why PR-BN Automated Tests Failed to Predict the Human Experience

The PR-BN tests exercise the primitive, not the live gameplay path into the primitive.

The capability tests in `tests/test_bounded_improvisation_authority.py` explicitly construct `improvisation_proposals` and call functions like `attach_bounded_improvisation_evaluation`, `promote_accepted_bounded_improvisation`, `prompt_projection_for_bounded_improvisation`, `skip_narrative_authority_layer`, and `detect_retry_failures`. That validates `game/bounded_improvisation.py` behavior, especially the proposal key at `game/bounded_improvisation.py:17`, proposal extraction at `game/bounded_improvisation.py:301`, promotion at `game/bounded_improvisation.py:376`, and projection at `game/bounded_improvisation.py:417`.

The human failures bypassed the key premise: no real turn produced an accepted bounded proposal. Tests did not ask:

- Does the live GM produce `improvisation_proposals` for mundane visible details?
- Does a player asking "what colors are noble colors?" route to bounded incidental detail?
- Does final emission preserve a generated answer when fallback validators dislike unsupported details?
- Does a multi-turn session keep advertised objects actionable?
- Does a natural physical action resolve through an action engine rather than fallback text?
- Does the evaluator fail a response that merely mentions semantically adjacent objects?

Specific coverage gap: PR-BN tests verify schema authority and guardrails, not end-to-end product realization under human input. They use clean, explicit proposal fixtures and controlled contexts. The human session used ambiguous, normal, multi-turn player behavior that exercises intent routing, scene transition, target binding, action resolution, final emission, and fallback selection simultaneously.

## 9. Existing Simulated-Player Architecture

### Fixed playability runner

Source: `tools/run_playability_validation.py`

- Defines four `PlayabilityScenario` fixtures at `tools/run_playability_validation.py:43` and `tools/run_playability_validation.py:52`.
- Uses fixed natural-language prompts, not model-driven player decisions.
- Sends prompts through `/api/chat`.
- Calls `evaluate_playability` per turn at `tools/run_playability_validation.py:260`.
- Uses final-turn evaluator output in summary construction around `tools/run_playability_validation.py:295`.
- Records metadata identifying the player as "fixed scripted natural-language prompts" at `tools/run_playability_validation.py:407`.

Behavior: scripted, cooperative, narrow, not curiosity-driven except by authored prompt lines.

### Synthetic helper runner

Source: `tests/helpers/synthetic_runner.py`

- Can run deterministic synthetic sessions.
- Can use fake GM responders.
- Can use a policy function, but default behavior is placeholder/stall-breaking.
- Useful for deterministic fixture coverage, not live human-proxy play unless configured carefully.

Behavior: scripted/policy-driven; often fake-GM; primarily test infrastructure.

### Reactive/adversarial runner

Sources:

- `tests/helpers/reactive_player.py`
- `tools/run_reactive_player_validation.py`

Key properties:

- `ReactiveScenario` defines objective, initial action, follow-ups, probes, acceptance markers, and turn caps at `tests/helpers/reactive_player.py:14`.
- Default max turns are six at `tests/helpers/reactive_player.py:27`.
- Boundary/refusal recognition lives near `tests/helpers/reactive_player.py:47`.
- Decision logic is in `decide_reactive_action` at `tests/helpers/reactive_player.py:96`.
- Shipped scenarios are `watch_command`, `notice_observation`, and `patrol_knowledge` at `tools/run_reactive_player_validation.py:39`.
- Scenario acceptance markers are hand-authored at `tools/run_reactive_player_validation.py:51`, `:64`, and `:77`.

Behavior: deterministic reactive/adversarial within authored scenarios. It persists after incomplete answers, rephrases, asks narrower follow-ups, and can probe contradictions.

### Evaluators

Source: `game/playability_eval.py`

- Intent gate functions begin at `game/playability_eval.py:539`, `:562`, and `:581`.
- Mandatory gates are assembled at `game/playability_eval.py:734`.
- Overall semantic result is finalized at `game/playability_eval.py:631`.

Additional evaluator:

- `game/behavioral_evaluators/intent_fulfillment.py` is deterministic and advisory; it does not alter gameplay.

## 10. Simulated-Player Proficiency Assessment

Fixed playability runners are not good human proxies. They do not decide what to do from GM output, do not notice that an answer was poor, do not persist on failed interactions, and are too short and scenario-shaped.

Reactive/adversarial runners are much closer. They can:

- follow up on incomplete answers;
- ask for specificity;
- rephrase unresolved questions;
- return to topic;
- probe contradiction and knowledge boundaries;
- stop on coherent uncertainty/refusal;
- preserve artifacts for human review.

But they still cannot replace broad human playtesting because they are:

- scenario-authored;
- limited to three shipped objectives;
- tied to acceptance markers;
- deterministic rather than goal-rich;
- capped at six turns;
- not yet broad enough for incidental object curiosity, lodging search, physical intrusion, non-combat movement, and open-ended frustration behavior.

Verdict: useful with modest improvement, not currently reliable as the project's first integration gate.

## 11. Privileged-Information Audit

The fixed playability runner records hidden runtime diagnostics and state snapshots, but its player prompts are fixed and do not appear to be selected from hidden state during a run.

The reactive runner uses prior GM text, evaluator results, scenario objectives, acceptance markers, and scenario-authored probes. The player policy is therefore biased by evaluator labels and authored expected evidence markers. That is not hidden world state in the campaign-fiction sense, but it is privileged test knowledge unavailable to a human player. It can bias behavior toward validation targets and away from organic curiosity.

The runner artifacts also include final-emission metadata and evaluator gates, but those are used by the synthetic policy in deciding persistence. A human player would only know "that answer did not satisfy me," not `mandatory_gates.player_intent_addressed == FAIL`.

Required improvement: split "player policy" from "evaluator review." The simulated player should decide next actions from player-visible transcript plus persona/goal memory; evaluator labels should be used after the fact, not as privileged player cognition, except in explicitly diagnostic adversarial campaigns.

## 12. Evaluator-Quality Audit

The current evaluator is better than pure keyword matching because `game/playability_eval.py` has mandatory malformed-output and intent-addressed gates. However, the ecosystem still has gaps:

- Older playability reports documented PASS results despite weak `player_intent` axes and bad outputs.
- The evaluator can pass semantically adjacent responses when enough topic overlap exists.
- Reactive docs already identify a case where a notice clarification received irrelevant NPC ignorance and the evaluator returned PASS.
- Overall scoring and diagnostic quality can obscure per-turn uselessness if mandatory gates do not catch it.

The evaluator must distinguish "mentions the same nouns" from "answers the player's actual request." For example, "a moneylender's house flies noble colors" is related to "what colors are noble colors?" but does not answer it. The latest human session demonstrates this exact failure class.

## 13. Controlled Simulated-Playtest Results

No new controlled simulation was run in this PR-BO cycle.

Reason: the available runners reset canonical campaign state and/or call the live model through `/api/chat`. That is more mutation/cost than needed for this diagnostic cycle, and the existing post-PR-BN human trace plus existing sim-player evidence is sufficient to answer the audit questions. Running simulations should be the next validation step after the synthetic gate is configured around this failure family.

Existing relevant simulation evidence:

- `artifacts/simulated_playtest_observability/20260917T221002Z_*`
- `artifacts/reactive_adversarial_players/20260918T021838Z/`
- `artifacts/reactive_adversarial_players/20260918T022209Z/`
- `artifacts/reactive_adversarial_players/human_review.json`

## 14. Human-vs-Simulated Comparison

The human did things current fixed scripts do not naturally do:

- ask about incidental visual detail created by the opening;
- ask an advertised runner for contextual information;
- give up on an unresponsive NPC and pursue a new mundane goal;
- ask a visual clarification about repeated vague wording;
- escalate physically after the game failed to provide useful routes.

Reactive/adversarial players could catch some of these if a scenario were authored for them. They would likely persist after non-answers and catch obvious intent failures. But current shipped scenarios do not cover heraldry, color descriptions, lodging search, advertised services, or physical intrusion into an incidental building.

Classification for test infrastructure: useful with modest improvement.

It can become a pre-human gate, but not yet as-is.

## 15. Recommended Improvements to Synthetic Testing

Add a small post-PR-BN "ordinary curiosity" simulated suite before any new gameplay fix:

- visual-detail player: asks about heraldry, colors, clothing, building condition;
- advertised-service player: asks tavern runner for stew, rumor price, lodging, directions;
- stubborn clarification player: repeats when the DM says "noble colors" without colors;
- mundane-goal player: seeks lodging, food, shelter, or a safe route;
- physical-affordance player: tries door, window, crowd, guard, and barrier actions.

Gating criteria:

- every player-visible turn must satisfy an intent gate, not merely overall aggregate score;
- any fallback phrase like "I do not know enough to answer that" must be classified against the actual request and speaker;
- repeated fallback source families should fail the run if they appear on consecutive turns;
- accepted bounded-improvisation proposals should be required for at least some incidental-detail questions;
- player policy should not receive evaluator labels during action selection in the normal gate.

## 16. Recommended Product Realization Test Loop

Use this loop:

1. Implementation.
2. Focused automated regression for the primitive.
3. Multi-turn simulated players through `/api/chat`.
4. Automated transcript evaluation with per-turn gates.
5. Human playtest only after synthetic threshold is met.

Threshold before human testing:

- 3 to 5 personas, 10 to 20 turns each, all through `/api/chat`;
- no `FAILED` turns on core intent fulfillment;
- no consecutive sealed fallback replacements;
- no unanswered advertised-affordance interactions;
- at least one successful bounded-improvisation proposal/promotion on incidental detail prompts;
- transcript artifacts reviewed for "technically related but useless" false passes;
- evaluator misses must be logged as blocking review items, not buried under aggregate pass.

This should reduce the current pattern where a human tester is the first integration system to discover obvious multi-turn failure.

## 17. Recommended Next Engineering Target

Recommended next target: live affordance and authority routing for ordinary player curiosity/actions.

Concretely, the next engineering cycle should not merely patch "noble colors." It should establish an end-to-end route where:

- player asks about a visible/advertised incidental detail;
- intent parser preserves that as a description/question obligation;
- GM is instructed and expected to emit bounded `improvisation_proposals` when needed;
- accepted proposals survive retry/final emission;
- final output answers the request;
- accepted incidental facts persist;
- physical actions against advertised objects produce action-resolution obligations rather than sealed social fallbacks.

This target covers more of the observed failure surface than any single prompt tune.

## 18. Exact Files/Components Implicated

Primary implicated runtime components:

- `game/bounded_improvisation.py` - primitive exists, but live routing did not reach it.
- `game/gm.py` - model schema/prompt path must cause real proposal emission for ordinary details.
- `game/api.py` - orchestration of intent, resolution, proposal evaluation, promotion, and debug logging.
- `game/prompt_context.py` - projection exists but had no entries to project.
- `game/gm_retry.py` - retry compatibility exists but was not the dominant active path.
- `game/final_emission_narrative_authority.py` - recognizes accepted PR-BN proposals, but none were accepted.
- Final-emission stack modules - repeated sealed fallback replacement and anti-reset continuation fallback dominated player-visible output.
- Intent/action/social routing components - misclassified heraldry, runner questions, lodging search, and physical action.
- `game/playability_eval.py` - evaluator needs stronger per-turn usefulness checks.
- `tools/run_playability_validation.py` - fixed scripted player is too weak.
- `tests/helpers/reactive_player.py` and `tools/run_reactive_player_validation.py` - promising but too narrow and partially privileged by evaluator/scenario markers.

Primary evidence files:

- `data/session_log.jsonl`
- `data/session.json`
- `data/world.json`
- `docs/audits/PR-BN_bounded_dm_improvisational_authority.md`
- `docs/simulated_playtest_observability_audit.md`
- `docs/reactive_adversarial_simulated_players.md`
- `artifacts/reactive_adversarial_players/human_review.json`

## 19. Open Questions

- Did the model fail to emit `improvisation_proposals` because prompts did not make the lane salient, or because final-emission/fallback replacement discarded proposal-bearing candidates before promotion?
- Why did Entry 1 become a scene transition when the player primarily asked about heraldry while entering?
- Why did the runner fail to bind as an interlocutor after explicit address?
- Why did the physical door/window actions fail to become action-resolution turns?
- Should "advertised affordance" objects receive explicit runtime capability contracts during scene opening?
- Should final-emission replacement be forbidden from substituting social ignorance fallbacks for non-social physical/visual/action requests?
- How should simulated players operate without evaluator-label privilege while still persisting like frustrated humans?

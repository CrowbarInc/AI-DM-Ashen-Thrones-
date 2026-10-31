# PR-BP - Live Action Resolution and Bounded-Improvisation Routing

Date: 2026-09-27
Base HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
Synthetic gate artifact: `artifacts/pr_bp_synthetic_gate/20260927T202617Z`

## 1. Executive Summary

PR-BP implemented a live routing bridge from ordinary `/api/chat` turns into PR-BN bounded improvisational authority. Raw player input can now create and promote bounded improvisation proposals through the production narration path without tests manually constructing proposal objects.

The implementation does not make PR-BN more permissive. It adds `game.live_resolution` to classify live request modes, bind compact target/topic metadata, synthesize low-risk proposals only for bounded-improvable gaps or rumor/hearsay requests, and stamp observability into GM metadata before existing PR-BN validation runs.

The synthetic gate did not pass. Three live-model synthetic sessions of 10 turns each completed, and PR-BN activated naturally, including incidental entries and NPC claim entries. However, 16 of 30 turns failed deterministic playability gates, with repeated unresolved social/action intent and stale fallback-style replies. Human playtest is not recommended.

## 2. PR-BO Failure Architecture

PR-BO showed that the post-PR-BN human playtest did not fail because PR-BN rejected too much. It failed because ordinary play rarely reached PR-BN. Player turns about visible details, advertised services, local rumors, lodging, and physical affordances were routed into older observe/social/fallback behavior, then often replaced by generic scene snippets or social ignorance lines.

## 3. Architecture Before PR-BP

The live path was:

`raw player text -> intent/target parsing -> exploration/social/adjudication -> model narration -> retry/final emission -> persistence`

PR-BN proposals were evaluated only when the GM output already contained `improvisation_proposals`. Normal live play had no explicit decision point saying, "this is a bounded-improvable gap."

## 4. Architecture After PR-BP

The live path now includes:

`raw player text -> intent/target parsing -> resolution-mode decision -> model narration -> live proposal synthesis when safe -> PR-BN validation -> final emission -> promotion/persistence`

`game.live_resolution` owns this bridge. It classifies authoritative/mechanical action, grounded information, bounded-improvable requests, NPC claim responses, consequential unsafe requests, and target failures.

## 5. Live Resolution-Mode Routing

Added `game/live_resolution.py` with `select_resolution_mode()`. It uses player text, resolution, normalized action, route choice, scene, session, and world context to produce a compact `ResolutionModeDecision`.

The routing is deliberately conservative. Mechanical/economy/hidden/consequential terms remain outside BN. Rumor/hearsay prompts route to NPC claim mode. Sensory, mundane service, and incidental descriptive questions route to bounded-improvable mode.

## 6. PR-BN Integration

`game.api._build_gpt_narration_from_authoritative_state()` now calls `synthesize_live_improvisation_proposal()` before `attach_bounded_improvisation_evaluation()`. This means the existing PR-BN validator remains the authority. Runtime synthesis only creates candidate proposals; PR-BN still accepts/rejects and promotion still happens through `promote_accepted_bounded_improvisation()`.

## 7. Intent/Target-Binding Changes

The live bridge carries a compact target/topic/speaker view into metadata. Binding sources include normalized action target fields, social resolution speaker, interaction context, and simple "about X" / inspect target extraction.

Known limitation: this improves observability and proposal shaping, but does not fully solve social follow-up binding. Synthetic failures still show "Who told you that?" and similar turns losing useful conversational obligation.

## 8. Affordance-Resolution Changes

This cycle adds minimum routing for mundane service/detail questions and physical-affordance recognition. It does not add the full affordance registry. Synthetic play still shows advertised social affordances and local action goals failing under multi-turn pressure.

## 9. Fallback-Precedence Changes

BN proposal synthesis now happens before PR-BN evaluation and retry suppression, so accepted bounded details can survive the legacy retry/fallback stack. The implementation was narrowed after regression testing so ordinary NPC questions do not suppress existing social repair behavior as NPC claims.

## 10. Observability Changes

GM metadata now includes `metadata.emission_debug.live_resolution_mode` with mode, reason codes, target, speaker, topic, opportunity detection, proposal-created status, and response-completeness status.

Future empty ledgers can now distinguish "no opportunity detected" from "opportunity detected but no proposal created."

## 11. Simulated-Player Changes

`tests/helpers/reactive_player.py` was updated so normal simulated-player decisions no longer branch on evaluator labels or mandatory gate names. It keeps the old evaluator argument for artifact compatibility, but visible-policy decisions now use prior GM text, boundary/refusal wording, acceptance markers, and bounded persistence.

## 12. Evaluator Changes

`game/playability_eval.py` now rejects topical non-answers for color and sensory-description questions. For example, "a house flies noble colors" no longer satisfies "What colors are noble colors?" unless actual color/detail words or a coherent refusal are present.

## 13. Real-Path Integration Tests

Added `tests/test_pr_bp_live_resolution_routing.py`.

Coverage:

- Raw `/api/chat` incidental description creates a PR-BN incidental proposal through live routing.
- Raw `/api/chat` rumor request creates an NPC claim that remains `not_world_truth`.
- Consequential hidden/secret request does not enter BN.
- Evaluator rejects topical color non-answer.

Result:

`tests/test_pr_bp_live_resolution_routing.py`: 4 passed.

## 14. Regression Results

Passing focused PR-BP slice:

`4 passed`

Adjacent regression band:

`tests/test_bounded_improvisation_authority.py tests/test_gm_retry.py tests/test_playability_eval.py tests/test_directed_social_routing.py tests/test_turn_pipeline_shared.py`

Result: failed with 6 failures, all in `tests/test_turn_pipeline_shared.py`.

Observed failures:

- `test_action_and_chat_investigate_both_mark_runtime_discovery_memory`
- `test_direct_npc_question_keeps_dialogue_contract_and_question_relevant_unknown_fallback`
- `test_chat_single_wait_in_tense_scene_forces_interaction_pressure`
- `test_chat_repeated_passive_actions_do_not_stall_into_atmosphere`
- `test_chat_passive_scene_prefers_already_introduced_suspicious_figure`
- `test_chat_passive_wait_with_recent_suspicious_figure_replaces_weak_atmosphere`

The first broader run exposed additional social repair failures while the NPC-claim lane was too broad; narrowing the lane cleared those social repair failures. The remaining failures are recorded as unresolved regression risk in the current dirty worktree.

## 15. Synthetic Playtest Methodology

Added `tools/run_pr_bp_synthetic_gate.py`.

Run:

`python tools/run_pr_bp_synthetic_gate.py --turns 10 --artifact-dir artifacts/pr_bp_synthetic_gate`

Method:

- 3 personas.
- 10 turns each.
- Real `/api/chat` path.
- Live upstream model path.
- Player policy uses only visible transcript plus persona agenda.
- Evaluator and runtime diagnostics are recorded only after the player action.

Personas:

- `goal_oriented`
- `curious_explorer`
- `social_persistent`

## 16. Full Synthetic Session Summary

Artifact: `artifacts/pr_bp_synthetic_gate/20260927T202617Z/campaign_summary.json`

Summary:

- Sessions: 3
- Turns: 30
- Semantic failures: 16
- Turns with incidental entries: 20
- Turns with NPC claim entries: 12
- Synthetic gate passed: false
- Human playtest recommended: false

## 17. Per-Turn Evaluator Findings

Evaluator failures were concentrated in:

- Social opening and follow-up turns answered by "murmur" / "moment passes" style fallback.
- Curiosity turns where observation intent was not fulfilled.
- Confirmation/action turns where the requested next action was lost.
- Repeated player follow-up receiving stale or non-progressing text.

Examples:

- `goal_oriented` turn 8 and 9 failed: "Before moving on, I confirm what I should do first" received "The murmur around you never tightens into a single clear voice on that point."
- `curious_explorer` turn 2 failed: ordinary sounds/smells question received "The moment passes without anyone stepping forward to own that thread."
- `social_persistent` turns 0-7 failed repeatedly on natural social questions and follow-ups.

## 18. PR-BN Activation Evidence

PR-BN activated naturally during synthetic play.

Evidence:

- `bounded_entry_turn_sum`: 42 cumulative entry observations across turns.
- `turns_with_incidental_entries`: 20.
- `turns_with_npc_claim_entries`: 12.
- Accepted incidental examples include sensory details for the notice board.
- Accepted NPC claim examples include hearsay/rumor entries with `truth_status="not_world_truth"`.

This satisfies the "routing invokes PR-BN" criterion but not the complete synthetic gate.

## 19. Failures Discovered and Resolved During Synthetic Testing

Resolved during implementation:

- The live bridge initially classified ordinary dialogue questions too broadly as NPC claim opportunities. That suppressed existing social repair behavior. The route was narrowed to rumor/hearsay prompts only.
- Live-routing metadata was overwritten on later evaluation passes; metadata now preserves runtime-created proposal provenance.

Unresolved:

- Social and follow-up turns still collapse into nonresponsive fallback lines.
- Evaluator still reports some diagnostic-quality false passes where semantic axes are weak but mandatory gates pass.
- Target/referent binding remains insufficient for several follow-ups.

## 20. Known Limitations

- This is not a full affordance registry.
- Physical affordance resolution remains shallow.
- Conversation follow-up binding is improved only as metadata/proposal context, not fully solved.
- Synthetic gate failed; PR-BP is not ready to recommend human playtesting.
- Some pre-existing dirty worktree changes are present outside this PR-BP work.

## 21. Human Playtest Recommendation

HUMAN PLAYTEST IS NOT RECOMMENDED.

Reason: synthetic gate failed with 16 semantic failures across 30 turns, including repeated unresolved social/action intent. Although PR-BN activated naturally, the multi-turn player experience remains too brittle.

## 22. Recommended Next Step

Do not commit PR-BP as complete. The next engineering step should focus on the remaining social/action fallback collapse:

- strengthen social target/referent binding for follow-ups,
- prevent "murmur/moment passes" fallback from satisfying direct social/action requests,
- improve actionability evaluation for next-step requests,
- rerun the same PR-BP synthetic gate until it passes without suppressing failures.

## 23. Continuation: Accepted-Resolution Delivery and Evaluator Hardening

Continuation date: 2026-09-27

This continuation addressed the first synthetic gate's shared failures without starting PR-BQ. The goal was delivery of useful resolution products that PR-BN already accepted, plus evaluator hardening so obvious nonresponses cannot pass.

### Gate V1 Baseline

Baseline artifact: `artifacts/pr_bp_synthetic_gate/20260927T202617Z`.

Gate V1 ran 3 sessions and 30 turns. It reported 16 semantic failures. The report undercounted product risk because at least one known false-pass family survived: direct descriptive or action questions could receive `"I do not know enough to answer that"` and still pass.

### Accepted-Content Delivery Root Cause

The notice-board failure was caused by missing linkage between accepted bounded authority and final player-visible delivery. The live bridge could synthesize and PR-BN could accept/promote a useful incidental entry, but final emission and reconciliation could still replace the current answer with generic social/ignorance fallback. Nothing after final emission checked: "this turn already has an accepted bounded resolution for the current request."

Change: `game/api_turn_support.py` now reasserts accepted bounded-improvisation text after final emission only when the post-gate text is empty or a known generic resolution fallback. It tags this as `accepted_bounded_resolution_delivered` and records `metadata.emission_debug.accepted_bounded_resolution_delivery`.

### Social-Loop Root Cause

The "nearest approachable local" family had two layers:

- some broad/open social solicitations were treated as ambient crowd bids with addressable candidates but no concrete interlocutor;
- other natural social openings fell through chat routing as generic `question` turns before the social resolver could preserve an interlocutor.

Change: `game/social.py` now lets broad open-social solicitation with addressable candidates acquire the first ranked concrete interlocutor and expects an answer/refusal/redirection from that speaker. `game/api.py` now routes canonical open-social solicitations into the dialogue-first action builder before generic intent parsing can claim them.

This improved test-level interlocutor acquisition, but V2 still shows strict-social speaker-grounding retry exhaustion and ambient fallback in live-model sessions. The shared social-loop mechanism is reduced, not resolved.

### Evaluator False-PASS Root Cause

`game/playability_eval.py` treated coherent nonanswers as satisfying too many requests. It did not distinguish a meaningful inability/refusal with actionable next step from generic fallback prose.

Changes:

- added generic-nonanswer detection for "do not know enough," "murmur," "moment passes," "nothing new resolves," and similar families;
- added request-specific handling for descriptions, source questions, and action requests;
- added legitimate inability/refusal counterexamples so "I can't tell from here; you'll need to open it" can pass while unrelated ignorance fails.

### New Tests

Updated/added coverage in:

- `tests/test_pr_bp_live_resolution_routing.py`
- `tests/test_broad_address_social_bid.py`
- `tests/test_playability_eval.py`

New checks cover accepted BN delivery over generic final fallback, false-pass regression families, legitimate refusal/inability counterexamples, and raw `/api/chat` acquisition of a concrete social interlocutor.

Focused passing result:

`tests/test_bounded_improvisation_authority.py tests/test_pr_bp_live_resolution_routing.py tests/test_broad_address_social_bid.py tests/test_playability_eval.py`

Result: 54 passed, 1 warning.

Adjacent regression band:

`tests/test_bounded_improvisation_authority.py tests/test_gm_retry.py tests/test_playability_eval.py tests/test_directed_social_routing.py tests/test_turn_pipeline_shared.py tests/test_pr_bp_live_resolution_routing.py tests/test_broad_address_social_bid.py`

Result: 160 passed, 6 failed, 1 warning. The six failures are the same unresolved `tests/test_turn_pipeline_shared.py` failures already recorded in section 14.

### Synthetic Gate V2 Methodology

The gate runner was strengthened:

- 4 personas instead of 3: `goal_oriented`, `curious_explorer`, `social_persistent`, `mundane_actor`;
- 10 turns each, 40 turns total;
- real `/api/chat` path and live upstream model path;
- player policy still uses only visible transcript plus persona agenda;
- evaluator/runtime diagnostics are recorded only after action selection;
- repeated identical player-visible fallback text now counts as a repeat flag;
- nonanswer persistence is capped at two attempts.

Two V2 attempts were run:

1. `artifacts/pr_bp_synthetic_gate/20260927T204714Z`
   - Sessions: 4
   - Turns: 40
   - Semantic failures: 31
   - Fallback repeat flags: 12
   - Incidental-entry turns: 12
   - NPC-claim turns: 3
   - Synthetic gate passed: false

2. `artifacts/pr_bp_synthetic_gate/20260927T205327Z`
   - Sessions: 4
   - Turns: 40
   - Semantic failures: 28
   - Fallback repeat flags: 5
   - Incidental-entry turns: 19
   - NPC-claim turns: 11
   - Synthetic gate passed: false

The second run is the current V2 evidence package for this continuation.

### V2 Findings

Improved:

- accepted notice-board detail reached player-visible narration in `curious_explorer` turn 2;
- PR-BN continued to activate naturally through the live path;
- evaluator caught generic nonanswers as failures in the known false-pass families;
- runner persistence no longer uses evaluator labels or loops indefinitely.

Still failing:

- social opening and follow-up turns still frequently collapse into "murmur" / "moment passes" / guard ignorance;
- accepted NPC claim content can exist in the ledger while follow-up answers ignore the active conversational obligation;
- physical/action requests still become generic guard ignorance;
- strict-social retry exhaustion remains a dominant runtime pattern;
- actionability for "what can you do now," "introduce/point me," and "confirm next action" is still unreliable.

### Completion Decision

PR-BP is STILL OPEN.

HUMAN PLAYTEST IS NOT RECOMMENDED.

No PR-BP completion commit was created because Synthetic Gate V2 failed and remaining failures share the same mechanisms targeted by this continuation: social/action fallback collapse, strict-social speaker-grounding retry exhaustion, and missing conversational obligation delivery across follow-ups.

## 24. Continuation 2: Failure-Chain Diagnosis

Gate V2's representative failures shared one chain: a reasonable social or action intent reached a partially resolved target, strict-social validation treated speaker provenance and semantic answer validity as one failure, whole-response retry discarded the useful part, and exhaustion selected ambient or generic ignorance prose. Open social bids also carried candidate lists without establishing a stable interlocutor, while physical and perception turns could be recaptured by stale social continuity.

Representative end-to-end traces are preserved in the V3.6 `run.json` files. Each turn now records raw text, normalized resolution, interaction obligation, target/interlocutor, final-emission metadata, bounded-improvisation state, action debug, evaluator result, and runtime traces.

## 25. Interaction Obligation and Interlocutor Changes

`game/live_resolution.py` now carries an explicit obligation with kind, target, interlocutor, subject, requested outcome, claim id, resolution mode, and turn index. Supported kinds are question, action request, inspection, social request, follow-up, and clarification.

Open social solicitations now acquire a ranked, scene-addressable interlocutor. The active interlocutor persists across natural follow-ups, and accepted/promoted NPC claims can supply the follow-up subject and claim id. Scene perception requests explicitly leave the social lane, while legitimate PR-BN/background participants remain bounded speakers without becoming unrestricted world authorities.

## 26. Speaker Grounding and Retry Contract

The strict-social root cause was a conflation of valid semantic resolution with invalid speaker provenance. Candidate repair now rebinds an otherwise valid answer to the canonical grounded speaker before retry. Consequential unauthorized speakers remain blocked.

Retries retain the interaction obligation in resolution metadata. Terminal fallback now distinguishes questions, actions, inspections, social requests, follow-ups, and clarifications; it emits a grounded speaker response when one exists and neutral narration otherwise. Interruption-aware fallbacks retain precedence and repeated interruptions retain variation.

## 27. Action and Final-Emission Changes

The intent parser now recognizes a wider class of ordinary object actions, scene-perception requests, and referential next-step actions. Physical resolution can no longer be replaced by unrelated social ignorance when a concrete pre-gate action result exists.

Final emission revalidates bounded proposals, preserves accepted bounded text over known generic replacements, and applies a last-resort obligation guard to dead-air social beats. Promotion-time preservation closes the timing gap where a proposal became accepted only after the earlier emission hook.

## 28. Focused Real-Path Coverage

`tests/test_pr_bp_live_resolution_routing.py` now covers the required A-G matrix through raw `/api/chat`: incidental interlocutor continuity, NPC-claim follow-up binding, social action resolution, physical object action ownership, speaker repair, retry exhaustion, and consequential-speaker protection. It also covers reset-campaign open bids, punctuation-free sensory routing, embedded questions, neutral unbound fallbacks, referential actions, and accepted-content preservation.

Final focused result:

- PR-BN plus PR-BP: 28 passed (`test_bounded_improvisation_authority.py`, `test_pr_bp_live_resolution_routing.py`).
- Focused obligation/routing/retry group: 64 passed.
- Core playability evaluator: 26 passed.

## 29. Regression Results

Adjacent historical band: 182 collected, 176 passed, 6 failed.

The six failures match the previously recorded current-worktree baseline:

- one discovery-memory identifier mismatch (`inv-desk` expected, `desk` stored);
- four passive-wait/scene-pressure or introduced-suspicious-figure expectations;
- one related passive-pressure behavior in the shared turn-pipeline suite.

The three regressions introduced during this continuation (interruption precedence, interruption variation, and open-bid source naming) were corrected and their targeted tests pass.

The wider evaluator/tool band has five additional failures confined to `test_reactive_player_validation.py`; the current pre-existing helper reports `objective_resolved` where those tests expect follow-up, max-attempt, or invalid-run termination. These are not caused by the obligation changes.

## 30. Synthetic Gate V3 Iterations

All runs used four scripted/reactive personas, ten turns each, the real `/api/chat` path, and live upstream narration. The players use only visible transcript plus persona agenda; they remain substantially prompt/script driven and are not equivalent to human players.

| Run | Artifact | Failures | Repeat flags | Incidental turns | NPC-claim turns |
|---|---|---:|---:|---:|---:|
| V3 | `20260927T212606Z` | 24 | 3 | 19 | 11 |
| V3.1 | `20260927T213104Z` | 24 | 3 | 12 | 0 |
| V3.2 | `20260927T213813Z` | 19 | 1 | 19 | 3 |
| V3.3 | `20260927T214540Z` | 20 | 1 | 12 | 3 |
| V3.4 | `20260927T215104Z` | 17 | 2 | 12 | 3 |
| V3.5 | `20260927T215621Z` | 16 | 1 | 10 | 8 |
| V3.6 final | `20260927T220411Z` | 13 | 1 | 19 | 8 |

V1 reported 16/30 failures before evaluator hardening. V2 reported 28/40 failures and five repeat flags. V3.6 shows substantial progress but does not satisfy the qualitative gate.

## 31. Final Failure Clustering

Final V3.6 failures cluster into these mechanisms:

- Perception/inspection specificity: 3 clear turns across two sessions received general visible-scene summaries instead of requested sound, smell, wear, use, or change information.
- Missing or weak referential resolution: 3 clear turns across two sessions either bypassed an obligation-bearing resolution or could not execute a previously suggested step.
- Abstract obligation fallback: 4 clear turns across three sessions preserved question/action shape but remained too generic to be useful, including follow-up certainty and introduction requests.
- Accepted-content delivery quality: one bounded description reached the player truncated mid-sentence; other accepted entries remained available and many were delivered correctly.
- Evaluator/product-boundary cases: several remaining FAILs contain partially useful answers, but do not remove the recurring mechanisms above.

Ambient `murmur` loops are greatly reduced and no longer dominate every social exchange. Strict-social retry exhaustion nevertheless still occurs in the runtime and the broader failure family remains player-visible through abstract refusals and lost referential action.

## 32. Completion Decision

Synthetic Gate V3: FAIL.

PR-BP: STILL OPEN.

HUMAN PLAYTEST: NOT RECOMMENDED.

Further repair now requires a broader design decision about cross-turn referent ownership, dimension-specific perception resolution, and the boundary between accepted bounded text and final-emission length/quality constraints. No completion commit was created, and PR-BQ was not started.

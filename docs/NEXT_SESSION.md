# Current milestone: pr_play_fresh_live_foundational_capability_validation

## Filesystem governance closeout and gameplay resumption

Ashen Thrones · Product Realization / PR-PLAY and ATGB · 2026-11-25 · AT-FG-07

**Filesystem governance CLOSED.** AT-FG-07 disposition **PARTIAL / ACCEPTED / CLOSED**. Integrity **PASS**. The closeout, retention policy, and review package are available below.

- [Filesystem governance closeout](../development/reports/AT-FG_CLOSEOUT_REPORT.md)
- [Final TMP cleanup and integrity report](../development/reports/AT-FG-07_FINAL_REPORT.md)
- [Artifact retention policy](ARTIFACT_RETENTION_POLICY.md)
- [AT-FG-07 review](../handoff/history/at_fg_07/REVIEW.md)

The last accepted AT-OPT milestone was **AT-OPT-06 Same-Scene Transition Correction and Compact Eligibility Safeguard**, A/PASS. Same-scene stamps preserve scene continuity and plan-backed `manual_play_auto` keeps the full instruction list. AT-OPT-06 closed the runtime-optimization sequence and directed the next separately authorized work to PR-PLAY / ATGB gameplay. The original F3 provider payload remains unavailable. The saved pre-correction bundle remains historical, and the three inherited projection/visibility KeyErrors remain in the AT-OPT-06 regression record. [AT-OPT-06 summary](../development/campaigns/product_realization/at_opt_06/SUMMARY.md) · [AT-OPT-06 regressions](../development/campaigns/product_realization/at_opt_06/REGRESSION_RESULTS.md)

The most recent established gameplay objective was to validate foundational capability across a persistent live campaign. The fresh 20-turn run completed with integrity PASS and mixed capability. One clue and two authored exits committed, and refused turns spent nothing. The handoff identified grounded NPC addressing as the next priority. The opening named `tavern_runner` and `guard_captain`, but the interpreter's permitted addressee list omitted them, causing ordinary descriptions to loop through clarification. Resume from that recorded finding under separate authorization. The prior handoff below retains the scores, limitations, and earlier unresolved findings. [Fresh live gameplay report](../development/campaigns/product_realization/pr_play_fresh_live_foundational_capability_validation/SUMMARY.md) · [Limitations](../development/campaigns/product_realization/pr_play_fresh_live_foundational_capability_validation/LIMITATIONS.md)

The five inherited PR-PLAY-72V readonly assertions expect `DECLINE`. “Can the trail be followed?” and “Can I follow the trail?” each returned `ANSWER` in survey and report, and “Follow the trail to its source.” returned `EXECUTE` in survey. AT-FG-07 carried forward these baseline findings. [Exact inherited assertions](../development/reports/AT-FG-05_EXEC_R2_FUNCTIONAL_VALIDATION.md) · [AT-FG-06 offline comparison](../development/reports/AT-FG-06_EXEC_FINAL_REPORT.md)

Git continuity baseline `feature/product-realization` at `6e59c070dcf522594c915ab39b61e198f56c3e28`. The worktree contains existing development changes and missing tracked archive paths.

## Previous milestone handoff

# Current milestone: pr_play_fresh_live_foundational_capability_validation

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-21 America/New_York.

**EXECUTION COMPLETE. INTEGRITY PASS. CAPABILITY MIXED.**

One fresh persistent campaign, `ca6032632047ed6aa7ffe8e1`, finished 20/20 turns. Opening scene `frontier_gate`. The live opening candidate was rejected and the deterministic fallback published. The player read the notice, entered Cinderwatch, and took the fortress trail. They could not get an answer from the tavern runner or the guards.

Interpretation 5/13 (38.5%) against historical 8/15 (53.3%). Legitimate-action completion 3/14 (21.4%), unchanged. Unnecessary refusal 11/14 (78.6%), unchanged. Continuity 4/14 (28.6%) against 3/11 (27.3%). Useful grounded responses 4/20 (20.0%) against 5/20 (25.0%). Unauthorized consequences 0. Median latency 3.476 s, P90 3.947 s. Provider calls 14. Tokens 59,732. Accounted expenditure $0.0292472 of the authorized $0.25. Retries 0. OpenAI `gpt-4.1-mini`, snapshot `gpt-4.1-mini-2025-04-14`.

Important success: one clue and two authored exits committed, and refused turns spent nothing. Important failure: addressable NPCs named by the opening were omitted from the interpreter's permitted list, so ordinary descriptions became clarification loops. Remaining limitation: one sample, and the acceptance suites were not re-run. Recommended next priority: ground `tavern_runner` and `guard_captain` before another live evaluation. Do not start that repair from this handoff.

The current-tree source baseline was recorded and did not drift. The historical freeze was kept. Production gameplay was not edited. No commit and no push.

Review archive: `development/campaigns/product_realization/pr_play_fresh_live_foundational_capability_validation/CURRENT_REVIEW(20261121-194840).zip`. SHA-256 `62c7a26c4fc5170de1c2667c43d65578af6b7c7c971472de2bd0f7ba46fa0dc4`. 130 entries. CRC check clean. The same bytes and sidecar are in `handoff/`. The checksum was recorded after the archive was sealed, so the copy inside the archive does not contain this paragraph.

[Milestone report](../development/campaigns/product_realization/pr_play_fresh_live_foundational_capability_validation/SUMMARY.md) · [Comparison](../development/campaigns/product_realization/pr_play_fresh_live_foundational_capability_validation/HISTORICAL_COMPARISON.md) · [Limitations](../development/campaigns/product_realization/pr_play_fresh_live_foundational_capability_validation/LIMITATIONS.md)

### AT-FG-02B-EXEC-PREFLIGHT cleanup authorization preparation

**PASS.** 870 source candidates are accounted for. 867 are PREFLIGHT-VERIFIED: 1,262,906 files, 4,171,860,328 apparent bytes, 4,670,263,128 allocated bytes. Three candidates are rejected because each contains one atomic temporary file. None are deferred. Deletion is not authorized. Allowlist SHA-256 `53591668d1a0f88e235487aaca09cd61ee4886e365012d4d4f88be01b2df4585`. The proposed pilot is 10 directories, 6,148 files, and 9,824,400 apparent bytes. Do not execute it from this note. A later deletion must recompute each candidate digest immediately before removal.

[Preflight report](../development/reports/AT-FG-02B_EXEC_PREFLIGHT_REPORT.md) · [Allowlist](../development/reports/AT-FG-02B_EXEC_ALLOWLIST.json) · [Review package](../handoff/history/at_fg_02b_exec_preflight/REVIEW.zip)

### AT-FG-02B historical temporary storage classification

**PASS.** `development/tmp/` measures 12,599,292,540 apparent bytes, 3,373,987 files, and 272,601 directories. The legacy metadata digest matches the AT-FG-03B after census. 870 exact directories are verified disposable candidates. None are authorized for deletion. 213 scene-scope roots that contain diagnostic JSON stay review-required. Social reconciliation, the two live campaign stores, and the PR-PLAY 47 and 49 workspaces stay protected. Do not delete, restore, or start a cleanup execution from this note.

[Classification report](../development/reports/AT-FG-02B_STORAGE_CLASSIFICATION_REPORT.md) · [Candidate manifest](../development/reports/AT-FG-02B_CLEANUP_CANDIDATES.json) · [Review package](../handoff/history/at_fg_02b/REVIEW.zip)

### AT-FG-03B-R1 filesystem governance

**PASS.** The three deleted social directories were removed by an operator `case-1-*` cleanup, not by the lifecycle helper. Cleanup now requires the creation secret written when that process allocated the directory. Pre-existing names are refused. The social tree's file hashes match the R1 entry manifest. Do not restore the deleted scratch. Do not run `artifacts/at_fg_03b/validate-runners.py`. Do not start historical cleanup from this note.

[Incident report](../development/reports/AT-FG-03B-R1_INCIDENT_REPORT.md) · [Execution report](../development/reports/AT-FG-03B-R1_EXECUTION_REPORT.md) · [Ownership audit](../development/reports/AT-FG-03B-R1_OWNERSHIP_AUDIT.json)

### AT-FG-03B filesystem governance

**FAIL.** The five legacy PR-PLAY pytest runners now publish before removing their own scratch, and ATGB reports implicit-store cleanup failures. Three pre-existing directories under `development/tmp/social-reconciliation/` were deleted during validation cleanup and were not restored. Protected-file hashes did not change. Lane tools, replay publishers, the AT-OPT holdout, and OS-temp probes remain deferred. Do not delete historical scratch. Do not start another governance milestone from this note.

[Execution report](../development/reports/AT-FG-03B_EXECUTION_REPORT.md) · [Producer manifest](../development/reports/AT-FG-03B_PRODUCER_MANIFEST.json) · [Review package](../handoff/history/at_fg_03b/REVIEW.zip)

### AT-FG-03A filesystem governance

**PARTIAL.** Scene-scope partition workers and default pytest sessions now own their scratch. The provider-free regression slice and lifecycle evidence are recorded below. Older explicit-base wrappers remain open. Preserve historical scratch and the active PR-PLAY and AT-OPT outputs.

[Execution report](../development/reports/AT-FG-03A_EXECUTION_REPORT.md) · [Producer manifest](../development/reports/AT-FG-03A_PRODUCER_MANIFEST.json) · [Review package](../handoff/history/at_fg_03a/REVIEW.zip). Await review before opening another milestone.

## Previous milestone handoff

# Current milestone: pr_play_purpose_tail_destination_binding_integrity

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-21 America/New_York.

**A/PASS.** A trailing purpose or reason no longer keeps an authorized destination from binding, and a host binding failure no longer spends a turn.

Exact requests, from Market Quarter: “I go to the fortress trail looking for the guard.” “I go to the fortress trail so I can persuade the guard.” “I go to the fortress trail because I want to persuade the guard.” Before the repair each selected `leave_for_seek_the_fortress_trail`, failed the transition, stayed in Market Quarter, and spent one turn, one tick, and one pressure increment. The reply was that no reachable destination was established.

The first incorrect decision is destination extraction. The place phrase kept the purpose tail, so the binder cleared a route the catalog had already selected. The first unauthorized commitment is `_commit_chat_action_time` after that cleared target. Those are different functions.

After the repair each request arrives at Old Milestone on `leave_for_seek_the_fortress_trail` with one travel receipt and no social receipt. “fortress trail xyzzy” declines and spends nothing. Compound social requests still clarify and do not travel. “or I return to the gate” still asks which destination. T05, T11, and T15 are unchanged. T11 is still an arrival, not an NPC address.

Purpose tails are peeled only when the remainder is the place the current route catalog names. Authored names that contain Looking, Hope, Because, For, To, or Since are kept. `Inn of Looking` is not discarded by the indoor/outdoor guess.

Production files touched for this repair, already dirty with earlier uncommitted work: `game/scene_destination_binding.py`, `game/conversational_orchestration.py`, `game/api_turn_support.py`, `game/api.py`.

New acceptance **60/60**. Compound rerun **87/87**, and the looking-for row is now an authorized arrival rather than a failed transition. Movement **109/109**. Disjunction script **52/53**; the only failure is the obsolete assertion that the compound sentence still travels. Duplicate checks **66**, **97**, and **117**. Unauthorized consequences **0**. Provider calls **0**. Expenditure **$0.00**.

Regression pass/fail: Combined 455/17, Focused 470/1, Scoped 191/0. New failure identities **0**. Recall 71/71. Reference 111/111 plus exact checks (historical 116). Attention 103/103 plus T02/T03 (historical 105). Correction 97/97 plus recovery 7/7 and the exact correction checks (historical 106). Clarification board 115/115 plus exact board replays (historical 120). Combat 5/5.

Residuals that spend nothing: “to look for work” is still an inspection cue, and “speak with someone” still asks which person is meant.

Recommended next step: a fresh independent 20-turn live-play validation under a separate spending ceiling. Do not start it from this milestone.

Review archive: `development/campaigns/product_realization/pr_play_purpose_tail_destination_binding_integrity/CURRENT_REVIEW(20261121-184924).zip`. SHA-256 `e9458b620a84e7d170c1f2b38cf4b53179681b1217e90e562c78884d34e17260`. 624 entries. CRC check clean. The checksum was recorded after the archive was sealed, so the copy inside the archive does not contain this line.

[Milestone report](../development/campaigns/product_realization/pr_play_purpose_tail_destination_binding_integrity/SUMMARY.md) · [Limitations](../development/campaigns/product_realization/pr_play_purpose_tail_destination_binding_integrity/LIMITATIONS.md)

## Previous milestone handoff

# Current milestone: pr_play_compound_movement_social_admission_integrity

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-21 America/New_York.

**B/PARTIAL.** The inherited compound no longer travels. Three reason and participle sentences still spend a failed-transition turn.

Exact request: “I go to the fortress trail and persuade the guard to help me.” Before the repair, coverage treated it as one MOVE, the purpose owner matched “to help”, and the host arrived at Old Milestone on `leave_for_seek_the_fortress_trail` with one turn, one tick, and one pressure increment. Persuasion was not resolved. Only “help me” was left pending.

After the repair the same sentence stays in Market Quarter. Admission is `compound_intention_needs_confirmation`. The reply names the trail and “persuade the guard to help me” and says nothing has been attempted. Turn, tick, and pressure stay 0. No travel receipt and no social receipt. “Just travel there first.” and “Only go to the trail.” each make one trail arrival and drop the persuasion. “Forget the persuasion.” and “Never mind.” clear the pending compound. “Actually, return to the gate.” is one gate arrival.

“to find the guard”, “to help the guard”, and “to learn what happened” still arrive and leave the purpose pending. Incidental nod, thank, wave, and ignore plus the trail still arrive. T05, T11, and T15 are unchanged. “or I return to the gate” still asks which destination. Committed route ids still match the arrival scene.

Remaining unauthorized turns, scene unchanged, social not resolved: “looking for the guard”, “so I can persuade the guard”, and “because I want to persuade the guard”. Each selects the trail route, fails the transition, and spends one turn, one tick, and one pressure increment. They are still one MOVE span. Do not start live play while those turns remain.

Production file changed for this milestone: `game/conversational_orchestration.py`.

New acceptance **87/87**, with looking-for classified as that pre-existing failed transition. Previous movement acceptance **109/109**. Duplicate checks **97** on the new matrix and **117** on the movement rerun. The old disjunction script is **52/53**; the only failure is its obsolete assertion that the compound still travels. Provider calls **0**. Expenditure **$0.00**.

Regression pass/fail: Combined 455/17, Focused 470/1, Scoped 191/0. New failure identities **0**. Recall 71/71. Reference 111/111 plus exact checks (historical 116). Attention 103/103 plus T02/T03 (historical 105). Correction 97/97 plus recovery 7/7 and the exact correction checks (historical 106). Clarification board 115/115 plus exact board replays (historical 120). Combat 5/5.

Recommended next milestone: stop the failed-transition turn on a trailing reason or participle when the destination route is authorized. Do not execute the social verb. Do not start it automatically. Do not open live validation until that turn is closed, and only then under a separate spending ceiling.

[Milestone report](../development/campaigns/product_realization/pr_play_compound_movement_social_admission_integrity/SUMMARY.md) · [Limitations](../development/campaigns/product_realization/pr_play_compound_movement_social_admission_integrity/LIMITATIONS.md)

## Previous milestone handoff

# Current milestone: pr_play_disjunctive_destination_admission_integrity

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-21 America/New_York.

**Narrow repair PASS. Overall integrity RESIDUAL OPEN.** Unresolved destination alternatives are withheld. The independent social compound still commits travel.

Exact request: “I go to the fortress trail or I return to the gate.” Before the repair, admission returned none, the deterministic owner executed `leave_for_return_to_the_gate`, and rebinding arrived at `old_milestone` under that route id. One turn, one tick, and one pressure increment were spent. The first incorrect decision was `actionable_coverage` / `full_request_admission`: “or I return” was not an alternative.

After the repair the same sentence asks which destination is meant, names “Return to the Gate” and “Seek the fortress trail”, stays in Market Quarter, and spends nothing. A reply of “The fortress.” or “To the gate.” travels on the matching route. Supported corrections travel. “or” and “actually” are not automatically corrections. “I mean” stays withheld. T11 “The fortress trail, then. I set off that way.” still arrives at Old Milestone on `leave_for_seek_the_fortress_trail`.

The route/destination check in `resolve_exploration_action` fails closed before commitment when an authored route’s destination disagrees with the arrival. It does not rewrite the route id and does not snap the arrival onto the other choice.

“I go to the fortress trail and persuade the guard to help me.” still travels to Old Milestone on the trail route and leaves “help me” pending. Same failure identity: `admission/compound-social`. Do not start live play while that unauthorized turn remains.

Production files: `game/scene_destination_binding.py`, `game/exploration.py`, `game/conversational_orchestration.py`, `game/api.py`.

New acceptance **53/53**. Previous movement acceptance **108/109**. Duplicate checks **59** on the new matrix and **117** on the rerun of the previous matrix. Unauthorized disjunctive consequences **0**. Remaining unauthorized consequence **1**, `admission/compound-social`. Provider calls **0**. Expenditure **$0.00**.

Regression pass/fail: Combined 455/17, Focused 470/1, Scoped 191/0. New failure identities **0**. Recall 71/71. Reference 111/111 plus exact checks. Attention 103/103 plus T02/T03. Correction 97/97 plus recovery 7/7. Clarification recovery 115/115 plus exact board replays (historical 120).

Recommended next milestone: repair whole-request admission for an independent social action combined with travel. Do not start it automatically. Do not open live validation until that residual is closed, and only then under a separate spending ceiling.

[Milestone report](../development/campaigns/product_realization/pr_play_disjunctive_destination_admission_integrity/SUMMARY.md) · [Limitations](../development/campaigns/product_realization/pr_play_disjunctive_destination_admission_integrity/LIMITATIONS.md)

## Previous milestone handoff

# Current milestone: pr_play_movement_intent_routing_integrity

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-21 America/New_York.

**C/FAIL at the milestone integrity gate.** Exact T11 recovered and routed through the existing travel resolver. Two inherited synthetic controls still commit travel against the milestone admission rules.

T11 “The fortress trail, then. I set off that way.” changed from “No established person matches fortress trail. Nothing has been attempted.” to “You arrive at Old Milestone.” The shared comma-vocative classifier had intercepted a valid provider MOVE before the bridge. The repaired path independently reconciles the player's named departure with one available current exit and preserves combat and scene guards. Market Quarter → Old Milestone committed via `leave_for_seek_the_fortress_trail` with one receipt, gameplay turn, tick and pressure increment. T05 and T15 preserved their original transactions.

Acceptance **107/109**. Duplicate deliveries **129**. Unauthorized consequences **2 inherited, zero on repaired T11**. Provider calls **0** and expenditure **$0.00**. Regression passes/failures: Combined 455/17, Focused 470/1, Scoped 191/0. New established failure identities **0**.

Prioritize the legacy disjunctive destination boundary that can commit an arrival under an incompatible route ID. T12 correction coverage, T06/T13 scenery, descriptor-to-NPC identity, historical recall and opening generation remain open. No live play was run.

Production changes are limited to interaction completion, scene destination binding, the stored interpretation bridge and conversational orchestration.

[Milestone report](../development/campaigns/product_realization/pr_play_movement_intent_routing_integrity/SUMMARY.md) · [Limitations](../development/campaigns/product_realization/pr_play_movement_intent_routing_integrity/LIMITATIONS.md)

## Previous milestone handoff

# Current milestone: pr_play_pending_intention_clarification_recovery_integrity

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-20 America/New_York.

**A/PASS.** The historical board examination now resolves at T17. The raw T18 and T19 captures also
resolve on their individual original state. In the repaired sequence, T18–T20 return the already-disclosed clue
with no additional gameplay turn, world tick, pressure increase, clue or lead.

T17 treated the topic and surface phrase as a carried-object reference. T18 and T19 stopped at different
communication/status gates after their provider outputs named the correct INSPECT target. No pending intention
was used. The existing exploration resolver authored the discovery and the individual T20 positive control is unchanged.

Acceptance **120/120**. Verified duplicate deliveries **472**. Unauthorized consequences
observed **0**. New established regression failure identities **0**.
Provider calls **0** and expenditure **$0.00**.

Trace the captured T11 movement-routing conflict at the existing travel owner.

Production files are `game/conversational_orchestration.py` and `game/api.py`.

Offline regression pass/fail counts — Combined 455/17 · Focused 470/1 · Scoped 191/0 · Inspection admission 64/0 · Statement ownership 65/0 · NPC addressee and social commitment 71/0 · Social grounding reconciliation 37/0 · Incidental posture 85/0 · Current-scene evidence 84/0 · Harness reconciliation 43/0.

[Reports](../development/campaigns/product_realization/pr_play_pending_intention_clarification_recovery_integrity/SUMMARY.md) · [Limitations](../development/campaigns/product_realization/pr_play_pending_intention_clarification_recovery_integrity/LIMITATIONS.md)

## Previous milestone handoff

# Current milestone: pr_play_npc_correction_pronoun_admission_integrity

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-20 America/New_York.

**A/PASS.** The exact T03 replay binds “them” to the present Tavern Runner and reaches the existing social
resolver. The runner says, “I couldn't tell you.” The controlled T02 → T03 sequence recovers after one
addressee clarification and commits only the T03 question.

Whole-request admission formerly treated “I mean” as an unrecognized action and withheld execution.
The correction can now supply the current addressee, while the remaining question and model target still
pass ordinary authority checks.

Acceptance **106/106**. Duplicate delivery **326/326**.
Unauthorized consequences **0**. New regression failure identities **0**.
Provider calls **0**. Provider expenditure **$0.00**.

Trace the T17–T19 clarification loop with its captured requests and state. Three consecutive turns stalled progress, and the existing pending-intention owner gives the investigation a bounded starting point.

The host supports ASK with current NPC identity, matching public or canonical target, and same-request object pronouns. It preserves the original question and retains independent-action protections. No durable historical T02 clarification was captured.

Production changes are in `game/interaction_completion.py`, `game/ordinary_semantic_ownership.py`, `game/conversational_orchestration.py`, `game/live_chat_interpretation.py`, `game/player_interpretation_bridge.py`.

Offline regression counts (passes/failures) — Combined 455/17 · Focused 470/1 · Scoped 191/0 · Historical recall 71/0 · Inspection admission 64/0 · Statement ownership 65/0 · NPC addressee and social commitment 71/0 · Social grounding reconciliation 37/0 · Incidental posture 85/0 · Current-scene evidence 84/0 · Harness reconciliation 43/0.

[Milestone reports](../development/campaigns/product_realization/pr_play_npc_correction_pronoun_admission_integrity/SUMMARY.md).

## Previous milestone handoff

# Current milestone: pr_play_npc_addressee_attention_posture_integrity

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-20 America/New_York.

**A/PASS.** The exact T02 replay now asks who the player is addressing. It recognizes the eye-contact wording as conversational attention, and withholds the ASK because the current executable roster cannot bind “stew seller” to an NPC. The named Tavern Runner control reaches the existing social resolver, which publishes the runner's uncertainty about shelter.

The original model returned `SOCIAL_SIGNAL visible:2` and `ASK visible:2`. Admission formerly treated the former as an unsupported operation. The host now validates the complete gesture and dialogue frame from the original text. A separate social purpose, incompatible target, invalid reference or unavailable NPC still blocks execution.

New acceptance **105/105**. Prior reference acceptance **116/116**. Duplicate requests **226/226** across current controls, prior controls, exact replays and the two baseline replays. Provider calls **0**. Expenditure **$0.00**.

Investigate the T03 correction and pronoun at whole-request admission using the exact capture.

T02 changed from action-and-target clarification to addressee-only clarification. T03 still enters the uncertain whole-request gate and publishes the same clarification. Unsupported or ambiguous identity, separate social intent and invalid references remain withheld. Supported direct address uses the existing NPC resolver and commits one receipt, turn, tick and pressure step.

Regression passes / failures — Combined 455 / 17 · Focused 470 / 1 · Scoped 191 / 0 · Historical recall 71 / 0 · Inspection admission 64 / 0 · Statement ownership 65 / 0 · NPC addressee and social commitment 71 / 0 · Social grounding reconciliation 37 / 0 · Incidental posture 85 / 0 · Current-scene evidence 84 / 0 · Harness reconciliation 43 / 0. New failure identities 0. Verified unauthorized consequences 0. Scope is bounded dialogue attention, with TELL and broader gestures under existing admission.

[Milestone reports](../development/campaigns/product_realization/pr_play_npc_addressee_attention_posture_integrity/SUMMARY.md).

## Previous milestone handoff

# Current milestone: pr_play_executable_reference_grounding_integrity

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-20 America/New_York.

**B/PARTIAL.** The exact T16 price question now reaches the authoritative social resolver and returns the runner's uncertainty. T02 and T03 still withhold execution for addressee or whole-request constraints. T06 and T13 have no executable house entry in the original scene. The five reproduced failures and their repaired outcomes are recorded separately from the original 20-turn B/PARTIAL evaluation.

The first adapter had treated public passage keys as undeclared action entity IDs before the host could reconcile them. Current visible references can now supply a canonical ASK or INSPECT target when the current passage, unique public entity and independently grounded player request agree. Existing admission and resolver receipts still control execution and publication.

Verified acceptance **116/116** after the repair. Duplicate request checks **121/121** across baseline, replay and controls. Unauthorized consequences **0 verified**, with **0** failed or unknown control audits. Provider calls **0**. Provider expenditure **$0.00**.

Regression results were 455 / 17 combined, 470 / 1 focused and 191 / 0 scoped (passes / failures). See the suite report for exact failure identities.

Production changes are in `game/live_chat_interpretation.py`, `game/player_interpretation_bridge.py` and `game/ordinary_semantic_ownership.py`. The next narrow investigation is T02 addressee and attention posture.

| Exact replay | After the repair |
| --- | --- |
| T02 | Clarified the addressee and action. The eye-contact component and stew-seller descriptor did not clear admission. |
| T03 | Retained the whole-request clarification. The correction plus ungrounded pronoun was read-only. |
| T06 | Withheld crest examination because the market scene lacks an authored interactable. |
| T13 | Withheld house examination for the same missing target. |
| T16 | Resolved the Tavern Runner exchange and published the resolver's uncertainty. One turn, one tick and one time-pressure increment. |

[Milestone reports](../development/campaigns/product_realization/pr_play_executable_reference_grounding_integrity/SUMMARY.md).

## Previous milestone handoff

# Current milestone: pr_play_fresh_extended_live_validation_retry

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-19 America/New_York.

**B/PARTIAL.** All 20 interactions completed on one persistent campaign. Interpretation, action completion, continuity and response usefulness missed their thresholds.

| Measure | Result |
| --- | --- |
| Campaign / initial scene | `eec4b9de8c9b6c7b38463d3e` / `frontier_gate` |
| Opening | Published after live generation and host recovery |
| Player interactions | 20/20 completed, 20 submitted |
| Provider / model | OpenAI / `gpt-4.1-mini-2025-04-14` |
| Calls / tokens / retries | 16 / 65527 confirmed / 0 |
| Spend | USD $0.032005600 |
| Interpretation accuracy | 8/15 (53.3%) |
| Legitimate-action completion | 3/14 (21.4%) |
| Unnecessary refusal rate | 11/14 (78.6%) |
| Conversational continuity | 3/11 (27.3%) |
| Response usefulness | 5/20 (25.0%) |
| Unauthorized consequences | 0 |
| Player median / P90 latency | 3.581 s / 4.929 s |
| Primary failures | TARGET_GROUNDING_FAILURE (five reproduced structural rejects) · ACTION_ADMISSION_FAILURE (route, reading and contextual refusals) · UNNECESSARY_CLARIFICATION (repeated continuations) · HISTORICAL_RECALL_FAILURE and CURRENT_SCENE_GROUNDING_FAILURE · OPENING_GENERATION_FAILURE (candidate rejected, recovery published) |

Prioritize the executable-reference boundary exposed by T02, T03, T06, T13 and T16. Replay those five raw responses against their captured scene catalogs and trace how public evidence references are offered, rejected and reconciled before selecting a narrow repair. Preserve combat, travel and discovery authority while recovering legitimate NPC and examination inputs.

[Milestone reports](../development/campaigns/product_realization/pr_play_fresh_extended_live_validation_retry/SUMMARY.md).

## Previous milestone handoff

# Current milestone: pr_play_live_harness_player_contract_reconciliation

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-19 America/New_York.

**A/PASS.** The original blocked run created campaign `d7cd405fa9e83feb44cba6f1` and stopped on `KeyError: 'dev_verify_ok'` before Start Campaign. The captured response reproduced the failure. The successful player projection omits the developer diagnostic by design. The historical run remains blocked at 0/20 interactions.

The successor `live_evaluation.py` and shared `campaign_lifecycle.py` validate the player response, persisted campaign and session identity, registry-backed ruleset binding, and the existing fresh runtime verifier before Start Campaign. The fixture-backed dry run published the opening at Frontier Gate on the same campaign and persisted one bootstrap transcript entry, turn and world tick. Independent state readback confirmed identity, scene, character, world, conversation and knowledge persistence. The host-only provider-disabled control safely withheld the opening, with no committed turn, tick or transcript. Offline provider calls, retries and spend were zero. Live model opening quality remains unevaluated.

Acceptance passed 43/43. Combined regression was 455/17 inherited, focused 470/1 inherited, scoped 191/0, historical recall 71/0, inspection admission 64/0, statement ownership 65/0, NPC addressee and social commitment 71/0, social reconciliation 37/0, incidental posture 85/0 and current-scene evidence 84/0. Failure identities matched exactly. No production files changed.

Next priority is a fresh 20-interaction `pr_play_fresh_extended_live_validation` run with the corrected harness, the previously proposed model and separate spending authorization. Social check repeat and legacy stance remain paused.

[Milestone reports](../development/campaigns/product_realization/pr_play_live_harness_player_contract_reconciliation/SUMMARY.md).

## Previous milestone handoff

# Current milestone: pr_play_fresh_extended_live_validation

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-19 America/New_York.

**BLOCKED**. New Campaign succeeded. The harness read an operator diagnostic omitted from the player response and stopped before submitting Start Campaign.

| Field | Result |
| --- | --- |
| Campaign | d7cd405fa9e83feb44cba6f1 / Cinderwatch Gate District |
| Live player interactions | 0 / 20 completed (0 submitted) |
| Provider | OpenAI `gpt-4.1-mini-2025-04-14` |
| Provider calls and retries | 0 attempts / 0 retries |
| Provider expenditure | $0.000000000 |
| Total tokens | 0 |
| Interpretation accuracy | 0 evaluable |
| Legitimate action completion | 0 evaluable |
| Unnecessary refusal rate | 0 evaluable |
| Conversational continuity | 0 evaluable |
| Response usefulness | 0 evaluable |
| Unauthorized consequences | Unevaluated |
| Mean / median / P90 latency | Unavailable / Unavailable / Unavailable |
| Primary failure categories | 1. CAMPAIGN_INITIALIZATION_FAILURE — harness response-contract mismatch |
| Next priority | Validate campaign creation against the player response contract. |

The fresh reset passed an offline audit of its persisted snapshot. The harness raised `KeyError: 'dev_verify_ok'` before Start Campaign. The saved campaign is at Day 1, turn 0, with an empty transcript and clue ledger. Social check repeat and legacy stance remain paused.

[Milestone reports](../development/campaigns/product_realization/pr_play_fresh_extended_live_validation/SUMMARY.md).

## Previous milestone handoff

# Current milestone: pr_play_current_scene_evidence_scope_integrity

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-19 America/New_York.

**A/PASS.** Exact captured T08 replayed on the original clue-free timeline at Frontier Gate. The provider's GM/QUESTION selected a Frontier Gate public fact and a previous Old Milestone clarification. The host withheld the targetless ASK but joined both snippets, letting the historical mud description answer a present-visibility question. The repaired reply reports that the prints' current visibility is unestablished. T08 remains at Frontier Gate, turn 6 and time pressure 2 with zero resolver calls, ticks or discoveries.

`game/conversational_orchestration.py` scopes current observation to the authoritative active scene and validates evidence at mixed clarification publication. Public historical scene observations and persisted discoveries retain their source attribution. `game/conversational_continuity.py` routes an explicit past question about what a named speaker told the player to existing speech recall. T04's normal resolver supplies the discovered comparison timeline. Current visibility at Frontier Gate remains unsupported in both states.

Acceptance was 84/84, with 81 read-only turns and 85 safe duplicate identities. Combined regression was 455/17 inherited, focused 470/1 inherited, and scoped 191/0, with zero new failure identities. Historical recall was 71/0, inspection admission 64/0, statement ownership 65/0, NPC social commitment 71/0, social grounding reconciliation 37/0, and incidental posture 85/0. Live provider calls and spend were zero.

Scene-level evidence supports bounded observation. Precise orientation, distance and off-scene sight lines require authored support. Historical recall requires a bound reference and a retained observation, discovery, or authorized dialogue exchange.

The next priority is fresh extended live-play validation with explicit provider authorization and a spending cap. Social check repeat and legacy stance remain paused.

[Milestone reports](../development/campaigns/product_realization/pr_play_current_scene_evidence_scope_integrity/SUMMARY.md).

## Previous milestone handoff

# Current milestone: pr_play_incidental_posture_action_decomposition_integrity

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-19 America/New_York.

**A/PASS.** The exact captured T04 now executes at Old Milestone. The model proposed order 1 MOVE with no target and order 2 INSPECT prints. Its first description made crouching subordinate to getting a closer look. The host previously relabeled the pair MIXED/ACTION and returned `communication_before_execution` with no receipt, turn, tick or clue.

The repair in `game/conversational_orchestration.py` and `game/api.py` admits the grounded INSPECT when the complete utterance and interpretation agree that the MOVE is in-place examination posture. It preserves the original interpretation and audits the suppressed component. On the original timeline T04 advances turn 5 to 6 and time pressure 1 to 2, with one successful exploration receipt and one tick. The authored clue `milestone_mud_prints` and its lead are recorded. Its wording preserves uncertainty about the prints' number, origin and direction. No independent movement occurs.

Offline acceptance is 85/85, with 11 successful inspections, 74 safely withheld requests and 85 duplicate identities replayed without further effects. The controls cover grounded aliases, unsupported targets, equipment, travel, order, stealth, defense and ambiguity. Combined regression is 455/17 inherited, focused 470/1 inherited, scoped 191/0, historical recall 71/0, inspection admission 64/0, statement ownership 65/0, NPC social commitment 71/0 and social grounding reconciliation 37/0. No new failure identities or live provider calls.

T08 remains open. The next narrow priority is current-scene evidence scoping on the exact captured return to Frontier Gate. Social check repeat and legacy stance remain paused.

[Milestone reports](../development/campaigns/product_realization/pr_play_incidental_posture_action_decomposition_integrity/SUMMARY.md).

## Previous milestone handoff

# Current milestone: pr_play_social_grounding_regression_reconciliation

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-19 America/New_York.

**A/PASS.** All four legacy regressions reproduced, classified and now pass in the original combined selection.

- `tests.test_pr_eb_conversational_continuity::test_pr_eb_active_npc_followup_routes_to_existing_social_resolver` — Category A, passed.
- `tests.test_pr_play_post_npc_handoff::test_explicit_repetition_stays_with_the_captain` — Category A, passed.
- `tests.test_pr_play_post_npc_handoff::test_recorded_handoff_leaves_the_previous_npc_line` — Category A, passed.
- `tests.test_pr_play_t04_local_action::test_l_npc_dialogue_is_not_fixture_contact` — Category A, passed.

Three Frontier Gate tests establish a real Guard Captain exchange before their unchanged patrol follow-up. The Mara test opens with her authored north-road dialogue and checks an addressed same-topic follow-up. The original bare fragment remains covered as read-only. Changes are in the three existing test files and the new reconciliation acceptance suite. No production files changed.

Combined 455 passed / 17 inherited failures with zero new identities. Focused 470 / 1 inherited, scoped 191 / 0. Historical recall 71 / 0, inspection admission 64 / 0, statement ownership 65 / 0, NPC social commitment 71 / 0 and reconciliation 37 / 0. Consequence audit passed with zero unauthorized changes and all eight duplicate requests preserved response, state and log. Live provider calls and spend were zero.

T04 incidental posture decomposition and T08 scene-evidence grounding remain open. Recommend T04 as the next independent investigation. Social check repeat and legacy stance remain paused. No follow-on milestone was started.

[Milestone reports](../development/campaigns/product_realization/pr_play_social_grounding_regression_reconciliation/SUMMARY.md).

## Previous milestone handoff

# Current milestone: pr_play_npc_addressee_and_social_commit_integrity

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-18 America/New_York.

**B/PARTIAL.** T12 previously selected an unsupported NPC clarification after the repeat repair. It now reaches disabled interpretation and returns a read-only information limitation. The already active captain no longer claims the scene question. The original unresolved pronoun now prompts for the recipient with zero ticks. The original captain alias now reaches the resolver as `guard_captain`. It succeeds and commits the authored clue, lead and one tick. Captured T10 preserves the same outcome through the interpretation bridge.

The root causes were an embedded verb treated as a speech act, a broad active-speaker fallback, a legacy target hint that bypassed grounded identity, and a commit and publication pipeline that accepted unsuccessful receipts. Production changes cover interaction completion, semantic ownership, conversational orchestration, the interpretation bridge, the API, social resolution and dialogue authority.

New acceptance 71/71. Consequence audit zero unauthorized gameplay changes. Duplicate checks 33/33. Regression combined 451/21, focused 470/1, scoped 191/0, inspection 64/0, statement ownership 65/0 and historical recall 71/0. The combined run records 4 additional failures from tests that expect an inferred NPC despite missing speaker grounding. Live provider calls and expenditure were zero.

T04 incidental posture and T08 mixed-scene evidence remain open. Update the four legacy regression fixtures to establish the speaker through an actual accepted exchange before asserting contextual follow-up. Keep their original protection against fabricated speech. The social check repeat and legacy stance milestone remains paused.

Reports and archive verification are under `development/campaigns/product_realization/pr_play_npc_addressee_and_social_commit_integrity/`.

## Previous milestone handoff

# Current milestone: pr_play_repeat_statement_routing_ownership_integrity

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-18 America/New_York.

**B/PARTIAL.** T12's statement-repetition ownership is repaired. The pre-edit host incorrectly treated overlapping “patrol” and “went” plus a permissive answer-sufficiency result as a reason to repeat the captain's T10 statement. The exact original replay matched the captured response and projected state. The change is confined to `game/conversational_continuity.py`.

Both post-edit conditions reach the provider-disabled interpretation boundary, then publish the existing `unresolved_addressee` clarification asking for the Guard Captain or Tavern Runner. The original T12 has no prints discovery and stays at turn 8 with time pressure 4. The counterfactual uses the normal prints resolver, records the authoritative clue, and stays at turn 9 with time pressure 5 during T12. Both T12 requests disclose no direction, invoke no gameplay resolver, and spend zero turns and ticks. Duplicate requests return the same reply without further work.

Verified statement recall and captured captain dialogue are preserved. The broader consequence audit found three legacy tick advances outside repetition ownership, including an active-NPC current-scene question and two unresolved addresses. The T12 consequence checks pass and all 14 duplicate checks pass. Ownership acceptance is 65/65. Combined regression is 455 passes and 17 inherited failures, focused is 470 passes and one inherited failure, and scoped is 191/191. Historical recall is 71/71 and inspection admission is 64/64. There are zero new or removed established failure identities. Live provider calls and spend were zero.

The next narrow investigation is downstream NPC-addressee fallback and its commit gate for world and current-scene questions. T04's posture decomposition and T08's current-scene grounding are open. Social repeat and legacy stance work stays paused.

Reports and verified review archive details are under `development/campaigns/product_realization/pr_play_repeat_statement_routing_ownership_integrity/`.

## Previous milestone handoff

# Current milestone: pr_play_inspection_communication_admission_integrity

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-18 America/New_York.

**A/PASS — INSPECTION ADMISSION REPAIRED.** The exact T01 capture supplied GM/QUESTION and one INSPECT of notice_board. The existing reconciliation refused it because the full-utterance matcher did not recognize “I want a closer look” and the reference needed the authored alias “missing patrol warning”. The repair carries that unique, public current-scene alias through existing admission to the inspection resolver. Raw and normalized interpretation evidence is persisted in internal telemetry.

T01 before the repair stopped at unresolved_inspection_communication_conflict at turn 4 and time pressure 0. The repaired HTTP replay produced the discover_clue receipt and persisted notice_patrol_route. One gameplay turn and one tick committed, taking the turn to 5 and time pressure to 1. Character resources and unrelated gameplay state remained stable. Exact T04 retained its targetless MOVE and INSPECT prints and stopped at communication_before_execution. It spent zero turns and ticks and gained no clue.

Acceptance 64/64. Consequence audit 72 traces with zero unauthorized or unknown changes. Duplicates 8/8 with equal responses, persisted state and log, and no re-execution. Regression combined 455/17, focused 470/1, scoped 191/0 and historical recall acceptance 71/0. New and removed failure identities were zero. Zero live provider calls and $0.00 spend.

Production changes are in game/conversational_orchestration.py, game/api.py and game/exploration.py. The remaining foundational issues are T04's incidental posture decomposition, T08's cross-scene evidence contamination and T12's repeat-delivered-statement routing. Recommended next investigation is T12 ownership on the captured continuity sequence. The social repeat and legacy stance work stays paused.

Reports and archive verification are under development/campaigns/product_realization/pr_play_inspection_communication_admission_integrity/.

## Previous milestone handoff

# Current milestone: pr_play_extended_live_continuity_validation

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-18 America/New_York.

**B/PARTIAL.** Explicit live authorization on 2026-11-18. One persistent session ran the frozen twelve utterances once on `frontier_gate_historical_n1` (SHA-256 `1ef169552fb8f62512a19993125978e174bb820d063a7fb4edf0284a4d3e845a`). Manifest SHA-256 `b770bfac015460006b0272600a414e145416c0a1e4f4ce3bbf1ca8309bc173b4`. OpenAI `gpt-4.1-mini` returned `gpt-4.1-mini-2025-04-14` on five calls. Usage was 11,966 input, 1,125 output, 0 cached, $0.0065864 estimated, 5 calls of 8 authorized. No retries, fallback, narration, or provider errors.

T01 named `INSPECT notice_board` and was refused at `unresolved_inspection_communication_conflict` because the model marked GM/QUESTION. T02 and T06 honestly said the patrol route was not established. T03 moved to Old Milestone. T04 added a targetless MOVE beside `INSPECT prints` and was refused, so the prints clue was never stored. T05 described the current milestone scene. T07 returned to the gate. T08 published a gate visible fact beside the milestone mud sentence and wrote no state. T09 listed the four prepared spells. T10 asked the guard captain and stored the authored topic plus the existing old-milestone lead. T11 inspected the notice board for the first time and stored `notice_patrol_route`. T12 matched `repeat_delivered_statement` and replayed the captain instead of answering the prints question. The duplicate of T01 returned the same response and state with no provider call.

Final state is `frontier_gate`, turn 8, time pressure 4, three clues, and no unauthorized gameplay writes. The faction agenda flags on T10 are the third committed world tick crossing the existing threshold of 3. Provider median/max 3.403/3.909 seconds. Regression: combined 455/17, focused 470/1, scoped 191/0, recall acceptance 71/71. New failure identities 0.

Recommended next milestone, not started: admit one `INSPECT` of one current public object even when the communication purpose is QUESTION. Do not auto-admit T04's extra targetless MOVE. Leave `repeat_delivered_statement` for a separate later repair. Do not open narration. Keep social repeat and legacy stance paused. No production gameplay change, commit, or push.

Reports: `development/campaigns/product_realization/pr_play_extended_live_continuity_validation/`. Live evidence: `artifacts/pr_play_extended_live_continuity_validation/live_execution/`. Archive checksum: `artifacts/pr_play_extended_live_continuity_validation/archive_verification.json`.

## Previous milestone handoff

# Current milestone: pr_play_extended_live_continuity_validation

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-18 America/New_York.

**PREPARED/BLOCKED.** Explicit live authorization is absent. Zero provider attempts, tokens, and cost. Twelve utterances are frozen on `frontier_gate_historical_n1` (SHA-256 `1ef169552fb8f62512a19993125978e174bb820d063a7fb4edf0284a4d3e845a`). Manifest SHA-256 `b770bfac015460006b0272600a414e145416c0a1e4f4ce3bbf1ca8309bc173b4`.

The sequence is one persistent Galinor session starting at the gate, turn 4, with an empty clue ledger. Provider-disabled routing: T01, T04, T08, T10, T11, and T12 reach live interpretation. T02 and T06 recall the patrol clue, including from Old Milestone. T05 describes the current scene. T09 lists the four prepared spells. T03 moves to Old Milestone and T07 returns to the gate. No frozen turn was unsupported. Setup inspections used different sentences so later routes could be classified. They are not live results and are not frozen turns.

Proposed cap, not approved: OpenAI `gpt-4.1-mini`, 8 calls, $0.10, 24,000 input tokens, 600 output tokens, 45 seconds, no retry, fallback, or live narration. Do not regenerate the freeze while waiting. Do not dispatch until that cap is explicitly approved. Then preflight the live safeguards and run this sequence once.

No production gameplay change, commit, or push. Social repeat and legacy stance stay paused. Live continuity, latency, and regression remain untested. The five-turn pass does not extend to these twelve utterances.

Reports: `development/campaigns/product_realization/pr_play_extended_live_continuity_validation/`. Freeze: `artifacts/pr_play_extended_live_continuity_validation/freeze.json`.

## Previous milestone handoff

# Current milestone: pr_play_short_multiturn_live_validation

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-18 America/New_York.

**A/PASS — LIVE MULTI-TURN VALIDATED.** Explicit authorization on 2026-11-18. One persistent session ran the frozen five utterances once. OpenAI `gpt-4.1-mini` returned `gpt-4.1-mini-2025-04-14` on T1 and T4. Usage was 4,574 input, 404 output, 0 cached, $0.002476 estimated, 2 calls of 3 authorized. No retries, fallback, narration, or provider errors.

T1 inspected the notice board and stored `notice_patrol_route`. Its model record said `GM/DESCRIPTION` and `INSPECT`; existing reconciliation admitted the examination. T2 recalled the patrol fact from `clue_knowledge` with no time cost. T3 moved to Old Milestone. T4 inspected `prints` and stored `milestone_mud_prints`. T5 recalled the same patrol fact at Old Milestone. Final state is turn 7, time-pressure 3, both clues, and no unauthorized gameplay writes. Replaying T1's request id returned the original response without another call or state change.

Regression under the baseline environment: combined 455/17, focused 470/1, scoped 191/0. New failure identities 0. No production gameplay change, commit, or push. Social repeat and legacy stance stay paused.

The player-facing limit is mechanical phrasing on arrival and the internal label "prints". Do not start a response-quality pass automatically.

Reports: `development/campaigns/product_realization/pr_play_short_multiturn_live_validation/`. Live evidence: `artifacts/pr_play_short_multiturn_live_validation/live_execution/`. Archive checksum: `artifacts/pr_play_short_multiturn_live_validation/archive_verification.json`.

## Previous milestone handoff

# Current milestone: pr_play_cross_scene_recall_routing_integrity

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-17 America/New_York.

**A/PASS — FOUNDATIONAL RECALL REPAIRED.** Frozen five-turn offline replay 5/5. Acceptance 71/71. Zero live provider attempts, tokens, retries and cost. Three gameplay turns and ticks for T1/T3/T4. T2/T5 preserve scene, resources, clue knowledge and gameplay time. Duplicate requests replay the first result.

T2 previously replayed the T1 examination through `reply:0`. T5's broad repeat cue selected a GM action report with no NPC speaker and returned an absent-NPC clarification. Both now answer directly from the source-bound, explicit `session.clue_knowledge` record.

> The missing patrol was last seen taking the northwest mud track past the crates.

The fact remained usable from Old Milestone after the earlier publication was removed and after ordinary disk reload. Unavailable, inferred, invalid and ambiguous facts were withheld. Legitimate NPC speech and recall follow their existing handlers. Production scope is conversational orchestration, dialogue continuity and the existing clue disclosure check. No new data store, resolver, or campaign content.

Regression. Combined 455 passed / 17 failed. Focused 470 passed / 1 failed. Scoped 191 passed / 0 failed. Additional continuity 180 passed / 16 failed. New failure identities 0. Durability beyond ordinary session reload and broad semantic generalization remain untested. See the milestone reports for withheld legacy records, performance and exact regression identities.

Resume the frozen five-turn live evaluation after separate provider authorization and effective preflight. Keep PR-PLAY social repeat/legacy stance paused. Do not execute the live run automatically.

Reports: `development/campaigns/product_realization/pr_play_cross_scene_recall_routing_integrity/`. Evidence: `artifacts/pr_play_cross_scene_recall_routing_integrity/`. Frozen case manifest and fixture stay at their prior paths and hashes. Archive CRC and SHA-256 are in `artifacts/pr_play_cross_scene_recall_routing_integrity/archive_verification.json`.

## Previous milestone handoff

# Current milestone: pr_play_short_multiturn_live_validation

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-17 America/New_York.

**PREPARED/BLOCKED.** Separate live authorization absent. 0 attempted / 0 completed / 0 dependency-blocked live turns. Zero provider attempts, tokens and cost. Five attempted and completed HTTP interactions offline, with four achieving their intent. T1 used historical replay; T2 and T4 used authored mock envelopes. T3 and T5 were deterministic.

Exact frozen sequence on `frontier_gate_historical_n1`:

1. I take a good look at the notice board.
2. Where did the notice say the patrol was last seen?
3. I follow the lead about the missing patrol.
4. I study the footprints.
5. Going back to the notice, where was the patrol last seen?

T1 persisted `notice_patrol_route`. T2 answered from the T1 public reply without gameplay changes. T3 traveled to and persisted `old_milestone`. T4 persisted `milestone_mud_prints`. T5 returned an incorrect absent-NPC clarification without spending time. State continuity passed offline, including both clue records, one identity and three cumulative turns/ticks. Cross-scene player-facing recall failed. No unauthorized gameplay writes observed. Live continuity and latency untested. Offline in-process median/max 4.390/5.936 s.

Regression: Combined 455 passed / 17 failed. Focused 470 passed / 1 failed. Scoped 191 passed / 0 failed. New failure identities 0. The 405 protected source/data files match the prior checkpoint. Production gameplay and authored data were preserved.

After separate approval, verify the effective live safeguards and run this same frozen sequence once. Cap five calls and $0.10 USD with OpenAI `gpt-4.1-mini`. T1/T2/T4 reached the offline boundary. T5's earliest failing decision was deterministic dialogue ownership. Preserve the freeze and keep social repeat / legacy stance paused.

Reports: `development/campaigns/product_realization/pr_play_short_multiturn_live_validation/`. Fixture SHA-256 `1ef169552fb8f62512a19993125978e174bb820d063a7fb4edf0284a4d3e845a`. Manifest SHA-256 `4ab5bd0b10d13bd38e378a42b304a5a2ca107524b05a1c49dfdef06f60bd01e5`. Review archive `handoff/CURRENT_REVIEW(20261117-222234).zip`. Detached SHA-256 and CRC enumeration in `artifacts/pr_play_short_multiturn_live_validation/archive_verification.json`.

## Previous milestone handoff

# Current milestone: pr_play_positive_action_live_retest

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-17 America/New_York.

**A/PASS — LIVE POSITIVE-ACTION VALIDATED.** Explicit approval granted for OpenAI `gpt-4.1-mini`, two attempts and $0.10 estimated. Preflight passed without dispatch. Two genuine calls completed on `gpt-4.1-mini-2025-04-14`. Usage was 4,452 input, 379 output, 0 cached tokens, $0.0023872 estimated. Zero retries, fallback, narration or provider errors.

N1 produced `GM/DESCRIPTION` with `INSPECT notice_board`. N1-V produced `GM/ACTION` with the same component. The host admitted each as `CHARACTER/ACTION`. On separate clean fixtures, both resolved one examination, disclosed and persisted `notice_patrol_route`, committed +1 turn and +1 world tick, and accurately published the authored clue. Duplicate submissions returned the original response with no additional resolver, state change or provider operation.

State integrity passed for both. D1 remains a read-only deterministic description. P1 remains intercepted at destination phrase binding. Scoped regression reran at 191 passed / 0 failed. Preparation baselines remain 455 passed / 17 inherited failures combined and 470 passed / 1 inherited failure focused. Zero new scoped failures and all 405 protected source/data files matched preparation.

Recommend separately authorizing a short multi-turn gameplay evaluation that follows the persisted clue. The live evidence covers two wordings on one fixture. P1 and paused social work remain deferred.

Read `development/campaigns/product_realization/pr_play_positive_action_live_retest/SUMMARY.md` and `LIVE_CASE_RESULTS.md`. Case traces, provider ledger, regression and integrity evidence are under `artifacts/pr_play_positive_action_live_retest/live_continuation`. Verified archive `handoff/CURRENT_REVIEW(20261117-194754).zip`. SHA-256 and CRC enumeration are in `archive_verification.json` there.

## Previous preparation handoff

# Current milestone: pr_play_positive_action_live_retest

Ashen Thrones. Product Realization / PR-PLAY. Updated 2026-11-17 America/New_York.

**PREPARED/BLOCKED.** Separate provider approval was absent. OpenAI gpt-4.1-mini, four total and interpretation calls, and $0.10 USD are the proposed limits. Actual provider calls, input/output/cached tokens and spend were all zero. Live latency was unavailable.

Four cases are frozen in `development/campaigns/product_realization/pr_play_positive_action_live_retest/CASE_MANIFEST.md`. Manifest SHA-256 `4f0858d2957b9957795cd0fd210ce801a3acf41982e10d1e10294d643bf7ee25`. Fixture SHA-256 `1ef169552fb8f62512a19993125978e174bb820d063a7fb4edf0284a4d3e845a`.

N1 and N1-V reached a non-billable sentinel on the ordinary unrestricted interpretation path. Neither ran live. Both exact-record offline probes reconciled the retained description/action conflict, resolved `notice_board`, persisted `notice_patrol_route` with +1 turn and +1 world tick, and deduplicated the same request ID without re-execution. N1-V used N1's record and a fresh fixture.

D1 was ROUTING_INTERCEPTED by an informational, visible-content host answer. Zero examination, clue, time, or gameplay mutation. The host wrote conversation continuity, a save timestamp, and a log entry. P1 was ROUTING_INTERCEPTED by `destination_not_established` for “Cinderwatch through the gate”. No movement or time. The separate historical N2 wording exercised the available exit and persisted `market_quarter` from the same fixture.

Offline gameplay consequence integrity passed. Fourteen provider-disabled control families passed. Regression combined 455 passed / 17 failed, focused 470 passed / 1 failed, scoped 191 passed / 0 failed. New failure identities: 0. Production source and campaign data were untouched by this milestone. Existing dirty worktree and previous evidence are preserved.

Recommended next milestone is the authorized completion of `pr_play_positive_action_live_retest`. Verify live provider controls after explicit approval, then run only the two eligible frozen cases once. A multi-turn evaluation is premature. Keep social repeat/legacy stance paused.

Read SUMMARY.md, CASE_MANIFEST.md, ROUTING_PREFLIGHT.md, POSITIVE_ACTION_RESULTS.md, and REGRESSION_RESULTS.md under the milestone report directory. Machine-readable traces and verification live in `artifacts/pr_play_positive_action_live_retest/`. Stable review `handoff/CURRENT_REVIEW.md` and ZIP. Timestamped review `handoff/CURRENT_REVIEW(20261117-190025).zip`. Detached digest and CRC enumeration in `artifacts/pr_play_positive_action_live_retest/archive_verification.json`.

## Previous milestone handoff

# Current milestone: pr_play_interpretation_communication_contract_consistency

Project: Ashen Thrones. Track: Product Realization / PR-PLAY. Updated 2026-11-17 America/New_York.

Verdict: **A/PASS — scoped offline contract repair**. Primary development failure class: contract. Exact captured raw A4/B1/E02/N1 records replayed before production changes and reproduced all four historical responses. Original campaign stores restored; only regenerated last_saved_at differs. Historical live model scores remain unchanged; G02/N2 remain deterministic routing intercepts, not live-model cases.

Production changed from entry: game/conversational_orchestration.py only. Existing schema/prompt/provider/bridge/inspection admission/resolvers/deferred commitment unchanged. A4's clarification/null-GM-ASK blocked the existing prepared-sheet lookup; now its complete original noncontact/capability question gets the authoritative prepared subset, no casting/resources/time. B1's status/GM ownership/contextual SOCIAL_SIGNAL previously lost the unresolved officer question; now NPC speech/context and original coverage survive with a host-grounded addressee clarification, no guessed captain/dialogue/fate/time. E02's correct broad PERCEIVE remains withheld for missing target with visible object context. N1's GM/DESCRIPTION formerly bypassed examination; bounded original-request/unique-public-target normalization now uses existing admission and reveals notice_patrol_route with +1 turn/+1 tick, persisted once. Known “What does [object] say?” public-content questions stay read-only. Unaccounted trailing target wording cannot be normalized away.

Acceptance: 50/50 requirement rows; 191 final tests pass / 0 fail. Consequence integrity PASS; direct tick spy and duplicate-response/state checks. Combined 455 pass / 17 inherited failures; focused 470 pass / 1 inherited failures; zero new failure identities. Exact identities/commands in REGRESSION_RESULTS.md and final_regression evidence. Earlier acceptance exposed two repaired defects; overlapping default pytest temp collision was resolved with an independent final basetemp. Offline paired median added decision cost up to 0.2967 ms in these cached cases; full medians/maxima/method in PERFORMANCE.md. Prompt-context/provider eligibility delta 0; no live latency claim.

LIVE PROVIDER CALLS: 0

LIVE MODEL VALIDATION: NOT EXECUTED

Remaining bottleneck: live communication/action consistency and generalization beyond retained envelopes. B1 officer identity, E02 broad-search capability, spellbook contents and conditional execution remain unsupported/unestablished. Authored variants are related evidence, not independent generalization. Recommended next milestone: separately authorized frozen positive-action live retest distinguishing description from examination. Do not start automatically; social repeat/legacy stance remains PAUSED. No new planner/subsystem, no commit/push. Extensive pre-existing worktree changes preserved; session-only source diff and entry snapshots separate this repair.

Minimum files: development/campaigns/product_realization/pr_play_interpretation_communication_contract_consistency/SUMMARY.md, ROOT_CAUSE.md, CONSISTENCY_RULES.md, ACCEPTANCE_RESULTS.md, REGRESSION_RESULTS.md, LIMITATIONS.md; artifacts/pr_play_interpretation_communication_contract_consistency/before/, after/, offline_scores.json, acceptance_results.json, final_acceptance.xml, final_regression/, performance.json, session_source.diff. Canonical review handoff/CURRENT_REVIEW.md and .zip; timestamped archive and detached SHA-256/CRC enumeration in artifacts/pr_play_interpretation_communication_contract_consistency/archive_verification.json. STOP after verified packaging. Prior handoff preserved below and verbatim in NEXT_SESSION.before.md.

## Previous milestone handoff (preserved)

# Current milestone: pr_play_foundational_live_interpretation_validation

Project: Ashen Thrones. Era/track: Product Realization / PR-PLAY. Last updated 2026-11-16 America/New_York.

Verdict: **A/PASS — LIVE EVALUATION COMPLETE**, not gameplay-quality success. Planned/preflighted 6/6; eligible 4/6; live executed 4/6 (A4, B1, E02, N1); genuine provider calls 4/6 maximum. G02 conditional and N2 deterministic movement ROUTING_INTERCEPTED, not live tested. Six frozen exact cases/fixtures and routing sentinels are packaged. No production changes, commit/push, retries, model fallback or narration.

OpenAI gpt-4.1-mini (returned gpt-4.1-mini-2025-04-14); 4/4 usable records, two clarification/two INTERPRETED. Intent PASS 2/4, PARTIAL 2/4; model grounding PASS 1/2 applicable, PARTIAL 1/2. Expected-intention host admission PASS 3/4, PARTIAL 1/4. Consequence handling PASS 3/4, N1 missing expected examination FAIL; safe live withholding 4/4 is not executed consequence success. Live positive-action consequences achieved 0/1. Unauthorized mutations 0/4; turn/committed tick deltas all 0. Player-facing adequate PASS 0/4, PARTIAL 2/4. Executable host grounding 0/0 assessed, no executable target admitted; N1 public-evidence validation 1/1 is separate.

A4 raw model recognizes informational noncontact/hypothetical request but asks clarification; host generic single-action clarification loses intent. B1 raw model recognizes ASK but mislabels GM ownership and independent turning, with officer genuinely unresolved. E02 correctly interprets broad PERCEIVE; missing-target host withholding exposes capability limitation. N1 correctly selects board/INSPECT but primary GM/DESCRIPTION yields only visible background, no expected +1 turn/clue. G02 +0/no clue and N2 +1/movement are deterministic preflight evidence only. No live G02 conditional competence claim.

Usage: 9,919 input / 926 output, cached 0, estimated $0.0054492 / $0.10 authorized; enforced stricter 4 calls/$0.06. Provider latency median/max 3.390/5.204s; gameplay 3.500/6.906s. Provider errors/narration/retries 0. Single pass, no statistical or full-narration-quality claim. Committed world ticks derived from nonmutating early return/state, no separate live tick-function spy.

Regression: combined 455 passed / 17 inherited failures; focused 470 passed / 1 inherited failure; scoped 245 passed; zero new failure identities, zero provider/network in regressions. Existing extensive dirty worktree preserved; game/data hashes unchanged from entry. Historical repair baselines remain authoritative; do not resume social repeat/legacy stance (PAUSED).

Primary bottleneck: communication/action contract consistency plus host publication preserving understood intent. Longer live play is premature. Recommend separately authorized pr_play_interpretation_communication_contract_consistency using these retained records offline; do not start automatically. E02 broad-search target contract, missing book contents, conditional execution and full narrative quality remain separate limitations. No new subsystem or conditional executor.

Minimum files: development/campaigns/product_realization/pr_play_foundational_live_interpretation_validation/SUMMARY.md, ROUTING_PREFLIGHT.md, MODEL_INTERPRETATION.md, HOST_ADMISSION.md, FAILURE_ANALYSIS.md, REGRESSION_RESULTS.md, NEXT_STEP_DECISION.md, INTEGRITY.md. Evidence: artifacts/pr_play_foundational_live_interpretation_validation/scored_cases.json, provider_requests.json, application_usage.jsonl, *_trace.json, *_before.json, *_after.json, performance.json, quantitative_results.json. Canonical review: handoff/CURRENT_REVIEW.md and .zip; exact timestamped archive/SHA-256/CRC enumeration in artifacts/pr_play_foundational_live_interpretation_validation/archive_verification.json and archive .sha256. Prior NEXT_SESSION preserved verbatim at artifacts/pr_play_foundational_live_interpretation_validation/NEXT_SESSION.before.md. Standing constitution/state/ruleset/narration/validation authorities remain settled. STOP after verified archive.

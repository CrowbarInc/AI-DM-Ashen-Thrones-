# PR-PLAY-23 repair report

Root cause: the bridge's correct exit-only MOVE contract collided with orchestration's treatment of an ordinary conversational approach as a separate consequential operation. The NPC registration and ASK target were already valid.

Implementation:

* game/local_interaction.py: one conservative read-only normalization rule described in INTERACTION_CONTRACT.
* game/conversational_orchestration.py: apply it to interpreted records before communicative/compound selection. A valid pair becomes the existing single-interaction EXECUTE decision; all other records remain unchanged.
* game/player_interpretation_bridge.py: retain normalization provenance in the existing diagnostic metadata. Actual MOVE and interaction validators remain unchanged.
* tools/playtest/gameplay.py: structured completion classification, decisive stop integration, exact restricted-value disclosure detection, accurate report counters and partial/unknown reporting.
* tools/playtest/runner.py: snapshot via Player HTTP, retaining authoritative reads from the owned isolated files. This required compatibility correction closes the preexisting Debug-read failure without reopening HTTP privilege.
* artifacts/pr_play_22/execute_validation.py: the PR-PLAY-22 custom controller now consumes the same classifier and emits separate counters; it no longer treats the generic weak-answer marker alone as a decisive failure. No historical result files were rewritten.
* tests/test_pr_play_23_local_interaction.py and tests/test_pr_play_23_harness.py: deterministic regressions and production integration.
* tests/test_five_turn_gameplay.py: positive evaluator fixtures now supply native accepted-speaker completion evidence; missing-response expectations now require a semantic failure/stop. The real fixture currently fails T2 addressee binding, so its old T3 injection and six-request exhaustion expectations are replaced by T2 stop and exact three-request/token accounting. These are explicit protocol migrations, documented by intermediate findings, not unrelated assertion relaxation.

Generality: target kind, same-scene authority, authored addressability, exact action semantics and normal interaction binding determine behavior. Runner, guard and notice board controls exercise it without implementation name exceptions.

Limits: deliberately bounded phrase coverage; no spatial solver, new movement capability, NPC/topic fabrication, opening/provider contract change or architecture redesign. The captured runner's current knowledge authority answers “I couldn't tell you” about offerings. That is an executed but weak interaction, also observed for direct ASK, not proof of rich NPC dialogue. Live answer quality remains unverified. Ordinary world ticks still occur: faction progression/event-log differences match advance_world_tick exactly and are legitimate existing time consequences, not normalization effects.

The initial workspace already contained substantial uncommitted changes. This pass preserved them, made no commit or push, and made zero live-provider requests.

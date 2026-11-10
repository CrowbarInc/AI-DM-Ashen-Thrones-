# PR-PLAY-24 state integrity

Snapshots: live/baseline (after new_campaign, before start_campaign), live/opening (post-initialization), live/turns/T1/before and after, live/after. Offline/baseline also records isolated preflight state before any campaign initialization. Each has public_state.json and persistent authoritative documents. No post-follow-up snapshot exists because no follow-up occurred.

Initialization succeeds and selects frontier_gate; initialization_state_diff.json preserves all normalized before/after changes, including ordinary opening tick and opening/session logs. Full authoritative snapshots retain envelopes and bookkeeping.

First interaction integrity PASS within this captured run:

- Location remains frontier_gate; calendar Day 1 unchanged; turn_counter 1 -> 2; time_pressure clock 1 -> 2.
- Character (including inventory/currency), campaign, combat, conditions and all scene documents unchanged after the question.
- World after question exactly equals a detached copy of the before-world advanced once by existing advance_world_tick. world_remaining_diff=[] in state_comparison.json. Faction pressures 3/3/2 -> 4/4/3, agenda_progress 1 -> 2, and normal threshold event appended. No dialogue-authored world consequence.
- NPC roster/topics/relationships unchanged. Runtime trust/attitude/fear/suspicion remain 0; no known/revealed topic added; runner last_interaction_turn becomes 2.
- Interaction context, discourse focus and current_interlocutor bind tavern_runner; delivered-exchange log records the actual uncertainty. No durable factual proposition or obligation established.
- Other session changes are turn telemetry, interpretation, response policy, narration/context caches and scene-runtime bookkeeping. Full field diffs are preserved rather than silently ignored.

Unauthorized consequential changes: none observed. Narration/state mismatch: the unknown answer conflicts with what the player was publicly told about the offerings, but it does not grant or mutate a resource. This is a conversational grounding defect.

Confidentiality: 8 distinct restricted authored strings checked across captured Player HTTP bodies; hidden game-fact matches=0; one runtime telemetry stamp matched. Final reply contains only the generic uncertainty; transcript manually inspected. Player projections remain player mode and privileged adapter helper rejected author/debug offline. No privileged HTTP mode used. A runtime CTIR stamp (2:2c1042f7040:8ba522ba) is publicly present under session runtime metadata; the restricted-key scan flags this telemetry identifier, not an authored secret or NPC fact. This exposure is recorded in confidentiality_verification.json. Exact matching cannot prove absence of all paraphrased leaks; no hidden gameplay disclosure observed in this evidence. Internal snapshots/requests are review-only evidence and may contain hidden game facts.

No provider-supplied descriptive or consequential additions were adopted. The current expression contract sets new_facts=false and commitment=false; fallback is canonical=false. Source and runtime evidence agree.

Owned live worker stopped; accounting saved; port released. Established terminate/wait returned process exit_code=1; ASGI graceful-shutdown completion was not demonstrated. No process was left listening.

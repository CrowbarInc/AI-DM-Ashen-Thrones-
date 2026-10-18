# 04 — Conversational Authority Analysis

| Requested distinction | Representation and gap |
|---|---|
| Player-to-GM communication | Caller mode AUTO/IC/OOC and interpreter OTHER/rules/correction are partial proxies; no general GM recipient/message purpose. OTHER can still be interpreted as executable components. |
| Player-character actions | IN_WORLD_ACTION + components/visible ids; bridge connects PERCEIVE/INSPECT/ASK/MOVE and existing resolvers retain authority. |
| NPC dialogue | ASK targets must be visible NPCs; active_interaction_target_id defaults NPC follow-ups. There is no equivalent active GM participant. |
| Session/campaign controls | Separate endpoints exist; chat lifecycle matching is lexical and gated on transcript emptiness, then encountered too late behind live interpretation. |
| Rules/interface questions | Deterministic question+keyword patterns and OOC mode. Schema uses RULES_QUESTION, eligibility recognizes it, but record decision checks OUT_OF_CHARACTER/OUT_OF_CHARACTER_CORRECTION, not RULES_QUESTION. |
| Clarification responses | Persisted pending operation, choices, scene, bounded compound steps. Bridge missing-target replies do not necessarily create a corresponding pending slot. |
| Narrative requests | Selected public-context patterns answer from scene; no general narrative-request intent. “Describe the opening scene” falls through to interpretation. |
| Consequential operations | Execution gate and resolvers exist, but unsupported descriptive components are automatically marked consequential and offered as compound steps. |

Source: game/conversational_orchestration.py:16–106,216–263,323–449,1442–1690; game/api.py:375–495,818–840; experiments/pr_do/schema.py:9–48 and eligibility.py:23; experiments/pr_dr/prompt.py:18–29,75–102.

The previous GM reply is retained in session_log and reconstructed into the last two visible interpreter turns, capped at 240 characters per line. The turn-four rejection is short enough to be included in full. Therefore “Why not?” is not explained by wholesale transcript loss or context truncation. The original wire request was not archived; this is current-code reconstruction supported by the replay's captured request, not direct proof of its historical bytes.

Missing typed discourse: no persistent GM-facing rejection reason, subject, recipient, or conversational response obligation is written by `_nonmutating_conversational_decision_response`. It writes the full decision to the transcript, but interpreter projection excludes resolution metadata. Pending sequence state survives; `_resume_bounded_pending` returns None for question-start utterances. Active-follow-up logic requires an NPC id and supplies ASK; with no active NPC it cannot interpret GM follow-ups. `_recent_visible_answer` only uses a small lexical trigger set; “Why not?” has none. The provider consequently makes a wrong recipient inference (ASK without target). The bridge correctly refuses an ungrounded NPC operation, and its “Who are you asking?” is a focused action-slot question in the wrong conversation domain.

Turn six is the clearest ownership failure: the provider summary and premise identify direct game-master address, yet mode OTHER + SOCIAL_SIGNAL becomes an unsupported world step. A new recipient clarification is not restored because turn five stored no pending ASK clarification; the older start sequence remains until turn six overwrites it. This combines incomplete GM discourse state with misrouting, rather than a universally broken memory subsystem.

Even explicit OOC avoids mutation but currently returns a fixed acknowledgement (game/api.py:461), not an answer to arbitrary GM/rules requests. Merely prefixing all inputs with OOC is not a coherent product repair. The latent RULES_QUESTION mode-name mismatch is a source finding outside the original six inputs; it must not be presented as their cause.

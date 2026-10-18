# 11 — Conversational Memory Audit

PR-EG-R5 · 2026-10-17 · investigation only

| Structure | Owner / use | Persistence and disagreement risk |
|---|---|---|
| conversational_context.delivered_exchanges (max 32) | exact adopted speech, speaker, topic, proposition, supplied text, digest | saved session; authoritative for what was delivered; bounded retention is not complete lifelong recall |
| conversational_context.dialogue_commitments | active noncanonical beliefs/refusals/partial answers | saved; established authored preference omitted; exact subject match can miss follow-up |
| last_gm_exchange | category/owner/subject/response summary | saved; derived routing summary can differ from NPC discourse |
| pending_clarification / pending_intention | unresolved addressee, choices, compound steps | saved; independently gates continuity and interpretation |
| interaction_context active_interaction_target_id / last NPC fields | current speaker/interaction focus | saved; stale focus competes with explicit references |
| discourse state / claim and action references | structured semantic focus for interpretation contracts | session state; vocabulary and references differ from delivered-history rows |
| scene runtime topic_pressure / current/last answer | repetition/escalation planning | saved runtime; topic recency is not relevance |
| NPC runtime revealed_topics / social thread | disclosure and follow-up selection | saved session; available authored facts can outlive actual conversational relevance |
| scene runtime npc_lead_discussions | per NPC/lead disclosure level, acknowledgment and grounded thread | saved session; can steer follow-ups independently of exact delivered rows |
| session_log.jsonl | player-visible transcript and debug-bearing entries | separately persisted; interpretation uses only a clipped recent view |
| accepted_response / private seal | current response identity and authority | per-output record, not an independent conversational memory store |

Anchors: [game/conversational_continuity.py:171](../../game/conversational_continuity.py#L171), [game/dialogue_authority.py:628](../../game/dialogue_authority.py#L628), [game/storage.py:559](../../game/storage.py#L559), [game/discourse_state.py:1](../../game/discourse_state.py#L1), [game/response_policy_enforcement.py:1504](../../game/response_policy_enforcement.py#L1504), [game/storage.py:929](../../game/storage.py#L929). Individual exact persistence was qualified historically and exercised by R5's selected tests; R5 did not separately roundtrip every auxiliary field.

Use delivered_exchanges as the sole speech-event source, extending its existing identity/epistemic annotations only where justified. Derive active focus, prior-preference indexes and recall selections from those events plus authoritative simulation state. Commitments that affect mechanics remain resolver-owned world/session state. A player's correction changes a pending interpretation pointer, never an old speech event. Do not add another dialogue database. Save/load must reconstruct the same derived focus and source binding, with explicit retention behavior.

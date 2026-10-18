# 07 — Conversational Ownership Audit

PR-EG-R5 · 2026-10-17 · investigation only

Ownership is repeatedly selected. The API mode boundary precedes deterministic orchestration and delivered-reference selection; the provider proposes communication.recipient/purpose, then orchestration can reclassify direct address and GM questions; the bridge independently grounds ASK; ordinary contracts and directed-social routing establish execution/speaker; final adoption binds speaker and addressee.

Player-to-GM uses explicit markers, rules checks, visible-scene answers and historical recall. Player-to-NPC uses ASK, active interlocutor and vocative heuristics. Declared physical actions must enter execution contracts. Corrections can revise pending intentions but cannot undo committed state. NPC-to-NPC references are especially vulnerable to name mentions being counted as candidate addressees. Unmarked OOC depends on mode and semantic classification; no single perfect heuristic exists.

Demonstrated errors include GM recall becoming an NPC-choice question, multi-NPC questions becoming action sequencing, and target switches retaining the previous speaker. Historical R4 A_curious9 says “Tavern Runner, what about you?” but delivers Mara; this is observational evidence, not a fully instrumented causal trace. Correction-to-repetition is demonstrated in report 05. Claims that all GM speech is routinely mistaken for NPC speech are not established.

Consolidate semantic ownership into a proposal with independent fields for communication recipient, speech speaker(s), referenced person(s), subject and execution modality. Host validates references and authority once, emitting typed rejection reasons. Rechecking presence or authority is necessary; silently reinterpreting the act later is not.

Anchors: [game/conversational_orchestration.py:344](../../game/conversational_orchestration.py#L344), [game/conversational_orchestration.py:448](../../game/conversational_orchestration.py#L448), [game/ordinary_semantic_ownership.py:643](../../game/ordinary_semantic_ownership.py#L643), [game/interaction_context.py:5814](../../game/interaction_context.py#L5814), [game/api.py:731](../../game/api.py#L731).

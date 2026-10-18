# 13 — Changed-File Inventory

PR-EF additions are relative to the dirty working tree captured before implementation, not to HEAD (which predates many prior cycles). Production references below point to final source. The PR-EF-only diff compares initial snapshots where available; social/bridge initial snapshots were reconstructed by removing only the documented PR-EF insertion blocks and are labelled accordingly.

- `game/conversational_orchestration.py` — Ownership/purpose, public evidence, GM continuity, safe mixed communication, unsupported cardinality, proposal eligibility/order, deferred-intent handling. SHA-256: `52f308678ed5525a0e433771b37184671b5f24280bfb0a84d61b1b5cad2a9411`.
- `game/live_chat_interpretation.py` — Production schema extension and validation, public-evidence/context projection, same-call ownership, conservative mode/purpose reconciliation, accurate schema token preflight. SHA-256: `0f4d3007ff018d6d5600b557d0978f5657781c231070b61e8185ad10de7b2f5a`.
- `game/player_interpretation_bridge.py` — Carry descriptive ownership and selected public-evidence metadata to the existing social resolver; execution checks retained. SHA-256: `f49258d334bd9776b1299a777469503b5ce6a322d0751891485fca95411b40ec`.
- `game/social.py` — Recall an already revealed authored topic only after rechecking speaker, payload and runtime disclosure; mark the existing resolver result. SHA-256: `5cfd4fc5773194c9b5454940043a361b88e6d3a4269e1bf61e3046b83d3bcb84`.
- `game/api.py` — Production decision context, bounded discourse persistence, resolver-owned recalled-answer skip through final emission, interpretation usage summary and decision-success distinction. SHA-256: `1795498bf7396b5f956b42a331a3503ffe9734ca32581f5c94dc282e4f91e05f`.
- `tests/test_pr_ef_gm_authority.py` — Validation tests/harness/reproducible review generator. SHA-256: `22c27b185e2d94e90feaeafae61feeaf040e76f05daf4b4d7d3da437abb92777`.
- `tools/validate_pr_ef.py` — Validation tests/harness/reproducible review generator. SHA-256: `5ca433d26993061ea351ef54d9127540d0c2b49008cd7665a3fb793590681722`.
- `tools/build_pr_ef_review.py` — Validation tests/harness/reproducible review generator. SHA-256: `8495f8dddff2e227b22ccc6ec1900e7ef4fc5e1234f9631c78e99ae6c131e494`.

Additional generated changes: artifacts/pr_ef_gm_authority (13 reports, evidence, snapshots, diff and command inventory); handoff/CURRENT_REVIEW.md, REVIEW_MANIFEST.json and CURRENT_REVIEW.zip, with predecessor preserved under handoff/history/pr-ee-before-pr-ef. No formal PR-EG work was done.

Relevant source references:

- `game/conversational_orchestration.py:231` — `public_conversation_evidence`
- `game/conversational_orchestration.py:256` — `_communication_decision`
- `game/conversational_orchestration.py:310` — `_gm_continuation_decision`
- `game/conversational_orchestration.py:1276` — `_compound_clarification`
- `game/conversational_orchestration.py:1765` — `decision_from_interpretation_record`
- `game/live_chat_interpretation.py:35` — `production_interpretation_schema`
- `game/live_chat_interpretation.py:242` — `interpret_production_turn`
- `game/player_interpretation_bridge.py:85` — `normalized_action_from_interpretation`
- `game/social.py:3834` — `resolve_social_action`
- `game/api.py:731` — `_nonmutating_conversational_decision_response`
- `game/api.py:952` — `deterministic_provider_skip_line`
- `game/api.py:1019` — `_performance_record`
- `game/api.py:6200` — `chat`

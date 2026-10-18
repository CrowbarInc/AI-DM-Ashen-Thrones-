# 16 — Changed-File Inventory

Only these files were intentionally edited/created for R2; starting dirty state is separate. Production-only diff compares source_before with final files, not Git HEAD. Artifact snapshots and generated reports live in artifacts/pr_ef_r2; CURRENT_REVIEW uses the established builder and archives its predecessor.

| File | Purpose | SHA-256 |
|---|---|---|
| game/ordinary_semantic_ownership.py | Carry validated ASK/social identity and compact authoritative result. | ae7768e6a071a05565cc9d2b04d767ce96c1fcfbb66cc72d606e5e9496a33361 |
| game/live_chat_interpretation.py | Normalize bounded incidental scope and public latest-reply guidance. | 5bd80b61f634f304d543740b103c18ac25cb8d6132357cd5fe91714a6e26556a |
| game/conversational_orchestration.py | Retain incidental/secondary context and latest emitted NPC reply; avoid body-head movement. | 1dd27449aba6eb91c3ce324a0c61f9ca42fb93b797016ef8aab9a69a73fefb60 |
| game/immutable_valid_response.py | Validate known identity/interaction and fail closed on invalid terminal fallback. | f8b10564a42dbb1dcbc099df35d0325ca1f98a9b6eafdc8f95ec1969f1ce168d |
| tests/test_pr_du_player_pipeline.py | Check notice-board semantics/canonical target. | 884945fbf5fb55ff0a0231473d18014fd4bb045763c6d34b538ee3e87c8fc877 |
| tests/test_turn_pipeline_shared.py | Reconcile two retired speaker-mutator assertions with current sealed validation. | 548936a0a2468a5368bf65b69da163114a8b75914ea1e9d2c65f9790f03b5aa4 |
| tests/test_pr_ef_r2_social_authority.py | Twenty-two new authority/intent/persistence tests. | 164ffbcf3b9bfac835f406624b42c6144a60fb576fb2771cda0ff4c81739f1e1 |
| tools/validate_pr_ef_r2.py | Bounded replay/fresh interpretation/production conversation harness. | b3301545a184f85c9ace8332c7a4efbe28be0bfa6776360a677cf25e53a0cb22 |
| tools/build_pr_ef_r2_review.py | Generate reproducible review and exact identity/signature audits. | dd4c6d9bdf1b214eb7a651cee6e54d69b0193c1a9e6b40c72d1ec7a2a5f942da |

Validation commands: baseline_command.json; final5_command.json; focused_final.xml; tools/validate_pr_ef_r2.py --mode holdouts --variant 4 --replay artifacts/pr_ef_r2/holdouts_3.json; --mode behavior --variant 1; --mode conversation --variant 3; --mode originals --variant 2. Existing outputs are protected against overwrite for live runs. Relevant authority source: player_interpretation_bridge.py, social.py, resolution_contract.py, gm_resolution_decision.py, provider_budget.py. These existing files were inspected; no edits attributed to this cycle.

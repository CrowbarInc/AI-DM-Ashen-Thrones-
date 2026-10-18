# 15 — Changed-File Inventory

Relative to the dirty pre-edit snapshots, not HEAD. status_before.txt and source_before preserve prior work. pr_ef_r1_only.patch contains bounded production changes. No unrelated user changes reverted.

- game/api.py: Retain bridge action/context and successful discovery emission. SHA-256 eeced3172fe82a95dd8b479355944e21c7e1958a967ca636b854e35c1e1db0eb.
  Source: game/api.py:952 — def deterministic_provider_skip_line.
- game/conversational_orchestration.py: Semantic continuation, ambiguity/scope and public causal evidence. SHA-256 ceab43f4ff6765a0124997008b5884e018ac68f7004aaf4fd9f64613f57a44ef.
  Source: game/conversational_orchestration.py:231 — def public_conversation_evidence.
  Source: game/conversational_orchestration.py:263 — def _communication_decision.
  Source: game/conversational_orchestration.py:595 — def _recent_visible_answer.
  Source: game/conversational_orchestration.py:936 — def _analyze_clause.
  Source: game/conversational_orchestration.py:1810 — def decision_from_interpretation_record.
- game/live_chat_interpretation.py: Schema presentation, prompt/context and conservative label reconciliation. SHA-256 f38178a29bb38e36d9863a5833a043a419ad6563bcaec75e5880a52b920b44d7.
  Source: game/live_chat_interpretation.py:35 — def production_interpretation_schema.
  Source: game/live_chat_interpretation.py:256 — def interpret_production_turn.
- game/ordinary_semantic_ownership.py: Consume grounded normalized movement in existing contract. SHA-256 a18ad31b8ac163a3da7c90271d79a4adac6a402c2a1b2c6203a5a858b69ba5c7.
  Source: game/ordinary_semantic_ownership.py:142 — def establish_ordinary_gameplay_contract.
- game/player_interpretation_bridge.py: Carry authored visible target labels. SHA-256 d796dd0a16d36501d9eade6a1433ca66d1822a28431d46448649e08a37359385.
  Source: game/player_interpretation_bridge.py:85 — def normalized_action_from_interpretation.
- tests/test_pr_ef_r1_semantic_handoff.py: R1 tests or reproducible validation/review tooling. SHA-256 310ac81593983e19cd92a4cc0c36883f33a6f0406a2b867d875b441ac2aa5d67.
- tools/validate_pr_ef_r1.py: R1 tests or reproducible validation/review tooling. SHA-256 3f98ea8fcd1d4d86840febbfa0f7781500ac27adde973d2a53f92fd95876b1d8.
- tools/build_pr_ef_r1_review.py: R1 tests or reproducible validation/review tooling. SHA-256 75bafcb5b0f23caa43bf110bddc39ff66142c747458ceb7ec94da72d49efabe0.
- tools/replay_pr_ef_r1_baseline.py: R1 tests or reproducible validation/review tooling. SHA-256 593164ee41dd9bab6f5d2d5fb6ab5eaf055eff9796705782cdf1e6398cc703fa.

Generated: artifacts/pr_ef_r1 (15 reports, raw HTTP/provider/state evidence, baseline/final tests, profiles, audits, hashes and bounded patch); handoff/CURRENT_REVIEW.md, REVIEW_MANIFEST.json and CURRENT_REVIEW.zip. Existing builder archives previous handoff.

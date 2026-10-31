# 01 — Baseline and Provider Path Inventory

PR-PLAY-02 / 2026-10-19. Bounded testing infrastructure; no live authority.
HEAD b012c3d7e5887fdfb09d10bb9cc0f0220de09df9; branch feature/product-realization.
The extensive dirty entry tree is preserved. See artifacts/pr_play_02/baseline.json,
repository_status_before.txt and source_before/; HEAD is not the effective baseline.
The task diff compares saved entry bytes with final source, not HEAD with final source.

Read DEVELOPMENT_CONSTITUTION, canonical docs/NEXT_SESSION, validation_evidence_standard,
product_realization_validation, review_handoff_standard, all eight PR-PLAY-01 reports
and its manual handoff. Requested support/docs/NEXT_SESSION.md is absent in the
checkout; support/ is the review ZIP namespace. No AGENTS.md was found. PR-PLAY-01
remains environment-blocked; R1/R2 acceptance scopes and PR-EG integration ban remain.

Every current production SDK dispatch is a Responses create reference passed to
provider_budget.RequestAttempt.dispatch. Inventory: artifacts/pr_play_02/provider_inventory.txt.
No provider-calling subprocess, multiprocessing owner, alternate HTTP provider,
with_options retry override or additional production SDK dispatch was found in game/.
Offline tools/workers outside the normal application are excluded from the procedure.

| Production owner | Use and model configuration | Timeout | Host retries |
|---|---|---|---|
| live_chat_interpretation.request_interpretation | Ordinary player meaning; existing experiments.pr_dp CONFIGURED_MODEL (gpt-4.1-mini) | provider_timeout_seconds, 45s default, bounded 5–120s | None |
| gm.call_gpt | Opening, narration, NPC wording where not host-owned; resolve_model_route and existing optional pin | Same 45s default | API upstream-error, hard-invalid regeneration and targeted narration retries; positive retry_attempt blocked by existing host flag |
| expressive_dialogue.request_expression | Optional authorized NPC expression, DEFAULT_MODEL_NAME | Same 45s default | None; host wording fallback is local |
| semantic_interpreter._invoke_interpretation_model | Existing contract interpretation, DEFAULT_MODEL_NAME; skips when production interpretation already consumed | SDK default (connect 5s, other phases 600s in installed SDK) | None |
| host_constrained_candidates.invoke_candidate_provider | Existing opt-in candidate selection, DEFAULT_MODEL_NAME | Same 45s default | None |
| unified_semantic_planning._invoke_provider | Existing opt-in planning, DEFAULT_MODEL_NAME | Same 45s default | None |
| api_upstream_preflight.run_upstream_api_preflight | Startup inference health probe, DEFAULT_MODEL_NAME | Per-request 25s default | None; skipped in manual launch |

Each constructs openai.OpenAI locally; preflight uses _default_openai_client_factory.
SDK 2.48.0 supports max_retries, default 2. No existing application constructor
explicitly set zero retries. Each now receives the same opt-in sdk_retry_options.
No model, endpoint, timeout, payload, prompt, schema or invocation stage changed.

Logical turn = one player submission. Logical operation = one intended provider
interpretation/generation. Outbound attempt = a dispatch including transport retry.
Opening and a player turn can each involve more than one operation; host-only
turns can involve none. With SDK retries zero, each dispatch has at most one
transport attempt. Existing admission reservations conservatively bound dispatches.

Existing diagnostics: session_log.jsonl, session debug traces, API timing metadata,
provider admission/dispatch/completion ledger and tools/atgb/accounting.inspect_ledger.
Existing isolation owner: game.storage ASHEN_DATA_DIR, evaluated before imports.
Normal campaign data was not used for testing. No live/provider-connectivity work.

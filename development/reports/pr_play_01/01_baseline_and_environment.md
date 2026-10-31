# 01 — Baseline and Environment

PR-PLAY-01 / 2026-10-19. Verdict C — Environment blocked. Execution category C — nonrepresentative for live play. Classification labels below refer to this pass unless explicitly historical.

Repository HEAD b012c3d7e5887fdfb09d10bb9cc0f0220de09df9; branch feature/product-realization. Extensive dirty/untracked work existed on entry; full entry/exit status is packaged. HEAD alone does not identify the effective source: entry_hashes.json fingerprints 2,228 protected files. Windows 11, Python 3.12.0 from .venv/Scripts/python.exe, OpenAI SDK 2.48.0.

Orientation read: docs/DEVELOPMENT_CONSTITUTION.md; docs/NEXT_SESSION.md; docs/validation_evidence_standard.md; docs/product_realization_validation.md; docs/review_handoff_standard.md. Requested support/docs/NEXT_SESSION.md does not exist in the checkout: support/ is the generated ZIP namespace. Canonical docs/NEXT_SESSION.md used. Existing stop statements concern previous passes; this explicit checkpoint authorizes only current validation and packaging.

## Established repair and historical evidence

- ATGB v1: 37 selected captured turns, not 37 successful turns. ATGB-05A imported provisional AI-assisted judgments: interpretation 18/16/3, response 10/25/2, authority 35/0/2 (pass/fail/uncertain). Human attestation remains false. Original transcripts and judgments remain authoritative and unchanged.
- R1-02 mechanical correction routing implemented deterministically. R1-07 conversational correction implementation complete; live adequacy remains pending. R1-05 L1/L2 still redundantly requested clarification; R1-08/09 were connectivity blocked. These are historical observations before the latest question-contract repair.
- R2-01 identified host rejection of a grounded NPC participant; R2-02 accepted in deterministic scope. R2-03 separated public-but-non-answering categories, missing curfew hour, gated last-seen clue and S05 subject ambiguity. R2-04 interpretation instructions conditionally accepted: deterministic compatibility established, live improvement unverified.
- PR-EG-R6-R5 diagnoses host binding/witness/question-source correspondence; 59/164 production baseline and intervention arms are experimental historical evidence, not current production forecasts. PR-EG-R6-R4-R1 remains below integration acceptance. No integration performed.
- Existing HTTP TestClient limitation is an environment coverage gap. No HTTP test was attempted here; no newly diagnosed gameplay defect follows from it.

## Real play path (Inspected only)

Normal launch: repository root, .venv/Scripts/python.exe run.py; Uvicorn serves game.api:app at http://127.0.0.1:8000/. Static browser UI is static/index.html and static/app.js. Play controls: New Campaign is a silent hard reset; Start Campaign generates the opening separately. Chat textarea and Send issue POST /api/chat. New Campaign uses /api/new_campaign; Start Campaign uses /api/start_campaign. Player mode is required.

Production orchestration: game.api.chat -> live_chat_interpretation -> conversational_orchestration / player_interpretation_bridge -> existing gameplay resolver and state owners -> narration/final emission -> persistence and projected response. The start endpoint shares the opening/narration stack. Existing experimental imports reused by production are pre-existing; that is not permission to integrate PR-EG.

Configuration loaded by game/config.py from repository .env, without displaying contents. Effective default, high-precision and escalation models are all gpt-4.1-mini, routing enabled; endpoint https://api.openai.com/v1/. Credential present, validity and model access untested. No proxy variables set. No endpoint/model/credential changes.

Persistence owner game/storage.py defaults to data/, with supported ASHEN_DATA_DIR disposable override. Bootstrap campaign/character/world/conditions/scenes are distinct from mutable session/combat/session_log and playthrough world fields. No existing campaign was reset.

Diagnostics: persisted session_log.jsonl and session.debug_traces, /api/log, developer /api/debug_trace, Debug panel, API latency_ms, provider_budget durable admission/dispatch/completion ledger via ASHEN_PROVIDER_USAGE_PATH. Existing tools/build_review_handoff.py builds review ZIPs. No dedicated gameplay diagnostic-export button was found in the inspected UI/API/tools; manual handoff uses existing diagnostic files and Windows ZIP export.

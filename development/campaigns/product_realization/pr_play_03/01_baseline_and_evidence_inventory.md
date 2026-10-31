# 01 — Baseline and Evidence Inventory

PR-PLAY-03, 2026-10-26 (America/New_York). Bounded causal investigation; implementation authority NONE; live-provider authority NONE.

**Observed:** Entry HEAD `b012c3d7e5887fdfb09d10bb9cc0f0220de09df9`, branch `feature/product-realization`. The worktree has extensive pre-existing tracked edits and untracked evidence. HEAD alone does not describe the investigated source. `artifacts/pr_play_03/entry_status.txt` captures that state; `baseline.json` hashes 1,244 production, static, data, experiment and test files. No cleanup, commit, push, or repair was performed.

Orientation read: `docs/DEVELOPMENT_CONSTITUTION.md`, `docs/NEXT_SESSION.md`, `docs/validation_evidence_standard.md`, `docs/product_realization_validation.md`, `docs/state_authority_model.md`, and `docs/review_handoff_standard.md`. The requested `support/docs/NEXT_SESSION.md` does not exist in the workspace; `support/` is a review-export prefix, not the canonical handoff owner. Used the canonical file. No AGENTS.md was found in the workspace.

## Original evidence

**Observed:** `artifacts/pr_play_02/manual-20261026-201939.zip` exists. Member sizes and SHA-256s are in `historical_inventory.json`. It contains one session-log row, saved session/world/campaign/character/combat/conditions/scenes, provider accounting, an empty notes file, and an empty screenshots directory. An extracted sibling directory also exists. The ZIP is the authority for this investigation; it was not altered.

The exact captured request is `{"start_campaign": true, "action_type": "start_campaign"}` with empty `player_input`. Exact GM output: **“No one here can answer that from what is settled here.”** `historical_excerpt.json` preserves original resolution, rejection, acceptance, performance, state and event fields. `historical_provider_usage.jsonl` is a byte-for-byte ledger copy.

**Missing / Unknown:** Raw Responses API object, raw extracted `output_text`, provider request messages, provider `status`, `incomplete_details`, finish reason, refusal/output item details, screenshot of rendered UI, operator timing/notes, before-start snapshot, and live-process source attestation. No original provider prose is reconstructed or fabricated. The host's `completion_status: completed` is an accounting label, not a captured provider finish status.

## Relevant prior passes and sources

PR-PLAY-01 report 08 records DNS-blocked live work, 204 deterministic passes, and no opening validation. PR-PLAY-02 report 08 and its manual procedure establish opt-in zero SDK retries, host retry suppression, six admissions, isolated data, and the distinction between New Campaign and Start Campaign. Their prior HTTP gap is not treated as evidence that HTTP failed in this successful manual request.

Current ownership: `game/api.py`, `gm.py`, `structured_player_output.py`, `live_resolution.py`, `resolution_contract.py`, `immutable_valid_response.py`, `gm_retry.py`, `final_emission_gate.py`, `api_turn_support.py`, `world.py`, `storage.py`, `campaign_reset.py`, and opening contract helpers. Numbered excerpts and hashes: `source_excerpts.md`, `source_index.json`; detailed ownership: `source_ownership_map.md`.

Only campaign reports, disposable offline evidence, canonical session orientation and review exports were written. R1/R2 conversational repairs, frozen ATGB, PR-EG experiments, prompts, schemas, models, endpoints and normal saves remain outside scope. Offline saves are confined to `development/tmp/pr_play_03/`.

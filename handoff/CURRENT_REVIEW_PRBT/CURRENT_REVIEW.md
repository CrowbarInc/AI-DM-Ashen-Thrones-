# Campaign

Campaign: PR-BT Provider Context Canonicalization Discovery
Identifier: `pr-bt-provider-context-canonicalization-discovery`
Date: 2026-10-04
Generated: 2026-10-05T00:00:00-04:00
Purpose: PR-BT. MODE: DISCOVERY. MODEL/API CALLS: ZERO. Measure and classify provider-facing realization context after PR-BS. No prompt changes, no validator changes, no gameplay validation, no commit, no push.

# Executive Summary

PR-BT. MODE: DISCOVERY. MODEL/API CALLS: ZERO.

Current representative PR-BS provider payload sizes:

- P1 bounded interpretation: 110,450 provider chars; 25,208 live input tokens.
- P2 mundane NPC conversation: 121,438 provider chars; 27,795 live input tokens.
- P3 player hypothesis: 110,665 provider chars; 25,233 live input tokens.

Dominant cost components are fixed/duplicated provider scaffolding, not current player text or scene facts:

- `instructions`: 25,788-26,675 chars.
- `response_policy`: 20,630-21,237 chars.
- `SYSTEM_PROMPT`: 12,975 chars.
- `turn_packet`: 10,640-10,910 chars.
- `narrative_plan`: 4,244-4,965 chars.
- `context_separation_contract`: 3,359-3,509 chars.

Dominant growth component: current raw conversation history is bounded by selector caps, so the larger long-session risk is the always-on provider boundary pattern: each future world/temporal/gameplay system may become default context unless prompt projection stays relevance-selected.

Estimated reducible context: 12k-18k chars per ordinary turn from provider-facing policy/instruction deduplication, with a stretch target near 25k if system/instruction overlap is safely compacted later. A separate `turn_packet` provider projection could save another 8k-10k chars.

Recommended first implementation slice: policy/instruction deduplication while keeping `decision_facing_answer_recipe`, compact resolution contract, compact decision projection, visibility, speaker selection, and output schema intact.

Architecture status: A — PR-BR REMAINS CLOSED.

Decision taxonomy: A — CANONICALIZATION SLICE READY.

# Changes Made

## Production changes

- No production code was changed.

## Validation changes

- No live gameplay validation was run.
- No model/API calls were made.
- Deterministically measured saved PR-BS provider requests.

## Documentation changes

- Added `PR-BT_provider_context_canonicalization_discovery.md`.
- Added `artifacts/pr_bt_provider_context_canonicalization/payload_measurements.md`.
- Added `artifacts/pr_bt_provider_context_canonicalization/source_evidence.md`.

## Generated artifacts

- Added `PR-BT_provider_payload_inventory.json`.
- Added `artifacts/pr_bt_provider_context_canonicalization/PR-BT_provider_payload_inventory.json`.
- Added `artifacts/pr_bt_provider_context_canonicalization/PR-BT_provider_context_canonicalization_discovery.md`.

# What Was Tested

- Deterministic measurement only.
- Source requests:
  - `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/provider_request_attempt_generation_1.json`
  - `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2/provider_request_attempt_generation_1.json`
  - `artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/provider_request_attempt_generation_1.json`
- Measurement method: `json.dumps(..., ensure_ascii=False, default=str)` character counts against saved provider input and parsed user payload components.
- Token counts copied from PR-BS recorded live usage. No tokenizer dependency was added.

# Behavioral Evidence

Not applicable. PR-BT is discovery/measurement/design only.

# Decisions Requiring Human Review

- A — CANONICALIZATION SLICE READY.
- Recommended implementation slice: policy/instruction deduplication.
- Architecture status: A — PR-BR REMAINS CLOSED.

# Known Problems / Unresolved Findings

- The discovery did not empirically remove context; all savings are design estimates until an implementation slice is measured.
- Response-policy compaction and recipe-only decision projection require later micro-live validation before broad rollout.
- Conversation history is bounded today, but future state systems could make long-session context grow if they are serialized wholesale.

# What This Campaign Does NOT Prove

- Does not prove the proposed minimum context preserves quality.
- Does not prove production readiness.
- Does not reopen PR-BR.
- Does not remove or alter prompts, validators, authority, retry, or C18 behavior.

# Recommended Next Step

Implement one bounded PR-BT slice: provider-facing policy/instruction deduplication. Validate with deterministic payload snapshots and contract-presence tests, then run a small micro-live validation only after deterministic acceptance.

# Review Bundle Contents

- `CURRENT_REVIEW.md`: this orientation file.
- `PR-BT_provider_context_canonicalization_discovery.md`: required discovery report, sections A-R.
- `PR-BT_provider_payload_inventory.json`: machine-readable payload inventory for before/after comparison.
- `payload_measurements.md`: deterministic P1/P2/P3 component tables.
- `source_evidence.md`: call-chain and source evidence notes.
- Saved PR-BS provider request JSONs for P1/P2/P3.
- PR-BS per-probe digests and model call usage evidence.

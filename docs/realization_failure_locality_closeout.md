# Narrative Realization / Failure-Locality — Closeout (Block AO)

Branch: `feature/failure-locality`

This document closes the **Narrative Realization / Failure-Locality** program after
documented milestone blocks through **AN**, plus **Block AO** (audit refresh and doc
closeout). It does **not** claim zero advisory audit findings or a finished architecture.

## Advisory audit snapshot (Block AO — not wired to CI)

Re-run: `tools/realization_layer_audit.py` and `tools/realization_provenance_audit.py`
(Block AO refresh).

| Audit | HIGH | REVIEW | INFO | Total |
| --- | ---: | ---: | ---: | ---: |
| Realization layer | 1261 | 710 | 8945 | 10916 |
| Realization provenance | 958 | 1280 | 738 | 2976 |

Artifacts:

- `artifacts/realization_layer_audit/realization_layer_audit.json`
- `artifacts/realization_provenance_audit/realization_provenance_audit.json`

Counts are **lexical / advisory**; they are useful for navigation and regression
awareness, not pass/fail gates.

## Work completed (milestones through Block AN)

### Earlier realization milestones (ledger language: Blocks G–S and kin)

- **Upstream prepared emission:** contract-shaped payloads, merge normalization,
  provenance tests (`tests/test_upstream_response_repairs.py`,
  `tests/test_realization_provenance.py`).
- **Diegetic fallback:** caller-owned provenance; gate labels legacy paths where
  applicable (`tests/test_diegetic_fallback_narration.py`).
- **Retry:** deterministic and terminal branches, selector contracts and purity,
  `docs/retry_fallback_selector_contract.md` (`tests/test_gm_retry.py`).
- **`build_messages`:** projection-only semantics (`tests/test_build_messages_projection.py`).
- **Response policy enforcement:** mutation snapshots, split-readiness manifest
  (`tests/test_response_policy_enforcement_mutation.py`,
  `game/response_policy_enforcement_manifest.py`,
  `docs/response_policy_enforcement_split_plan.md`).
- **Opening fallback / final emission:** exact opening text and FEM provenance,
  multiple final emitted source branches (`tests/test_final_emission_gate.py`,
  `tests/test_diegetic_fallback_narration.py`).
- **Authority invariants** where applicable (`tests/test_realization_authority.py`).

### API narration hub (Blocks AJ–AN)

- **AJ:** Route metadata helpers — `_narration_hub_finalize_annotation_parts`,
  `_classify_narration_hub_route`, `_build_narration_hub_route_meta` (annotation
  kwargs only; no GPT/retry/text production).
- **AK:** Contract guards — route helpers stay metadata-only (`test_block_ak_*`).
- **AL:** Orchestration handoff order snapshots — GPT → retry → policy →
  turn-support final gate (`test_block_al_*`).
- **AM:** `_apply_narration_hub_policy_handoff` — response-policy seam after GPT/retry.
- **AN:** Extraction **stop point** — contract guards and registries (`test_block_an_*`,
  `_BLOCK_AL_ORCHESTRATION_HANDOFF_TEST_NAMES`, `_BLOCK_AM_POLICY_HANDOFF_TEST_NAMES`).

### Block AO (this closeout)

- Re-ran advisory audits; refreshed JSON/Markdown artifacts.
- Updated `docs/realization_triage_ledger.md`, `docs/realization_cursor_handoff.md`,
  and added **this** closeout file.
- **No** production code, prose, or behavior changes; **no** CI wiring for audits.

## What is now protected by tests (high level)

- **Provenance and family normalization** for upstream and merge paths.
- **Retry** branch behavior, selectors, and terminal/deterministic snapshots.
- **Policy enforcement** mutation surface and manifest classification (split readiness
  without mandating the split).
- **Final emission** critical branches and opening fallback provenance.
- **API narration hub:** path selection, orchestration order, policy adapter surface,
  route-helper contracts, and AN boundary registry lists.

Canonical pointers: `tests/test_realization_provenance.py`,
`tests/test_realization_authority.py`, `tests/test_api_narration_path_selection.py`,
`tests/test_final_emission_gate.py`, `tests/test_response_policy_enforcement_mutation.py`,
`tests/test_gm_retry.py`, plus audit smoke tests for tool output shape.

## Remaining known risks (explicitly bounded)

| Area | Risk | Notes |
| --- | --- | --- |
| `apply_response_policy_enforcement` | **HIGH** (leaf mutators in `game/gm.py`) | Orchestration owner extracted (AI1); phased leaf moves remain Cursor-led with tests. |
| Opening fallback | **HIGH** | Gate still composes some prose; upstream prepared selection is future work. |
| `apply_final_emission_gate` | **EXTREME** | Broad rewrite unsafe; branch-local reduction only with snapshots. |
| `_build_gpt_narration_from_authoritative_state` body | **HIGH if edited** | Orchestration changes can shift semantics quietly; AJ–AN mitigate extraction churn only. |
| Retry fallback authoring | **MODERATE** | Bounded; leave unless contract-preserving cleanup is needed. |

## What should be left alone (unless evidence forces a change)

- **Stable prose and templates** in diegetic renderers and upstream payloads (prove with tests).
- **Retry selector contracts** and emitted retry fallback lines (snapshot-backed).
- **Final emission gate** as a monolith for “cleanup” — treat as branch-by-branch only.
- **Lexical audit counts** as success metrics — they will stay noisy by design.

## Future work — requires a concrete trigger

Resume **large** behavioral work only when one of:

1. A **reproducible bug** or player-facing regression with a failing/narrow test path.
2. A **specific audit finding** tied to a seam you intend to change (not bulk HIGH counts).
3. An **approved design change** with acceptance tests agreed upfront.

Otherwise limit work to:

- Advisory audit re-runs and doc refresh (like Block AO).
- Narrow regression tests locking observed behavior.
- Small, contract-preserving metadata or debug clarity edits.

**Do not** wire advisory audits into CI as gates without a separate decision.

## Recommended stopping point

- **Failure-locality / hub extraction:** **Block AN** remains the stop point for broad API
  hub decomposition unless a trigger above applies.
- **Realization program (this pass):** **Block AO** closes the documented narrative:
  audits refreshed, ledger + handoff + closeout aligned, acceptance tests green.

Next major initiatives (policy split, opening upstream move, gate reduction) should be
**separate planned passes** with their own risk budgets — not implicit follow-ups from
lexical audit noise.

---

See also: `docs/realization_cursor_handoff.md`, `docs/realization_triage_ledger.md`,
`docs/retry_fallback_selector_contract.md`, `docs/response_policy_enforcement_split_plan.md`.

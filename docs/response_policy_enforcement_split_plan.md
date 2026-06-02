# Response Policy Enforcement Split Plan

This document describes the **completed** split of response-policy enforcement
orchestration plus helpers (Blocks U–Y), the **runtime owner extraction** (Blocks AI1–AI2),
**phased leaf extraction** (Blocks AI3–AI11), and **closure audit** (Block AI12).

## Block AI12 — Cycle AI closure (completed)

**Status:** Response-policy enforcement ownership is localized to
`game/response_policy_enforcement.py`. `game/gm.py` retains only compatibility re-exports
and shared helper dependencies (uncertainty rendering, topic-pressure scoring/context,
scene-momentum due-bit helpers, etc.).

**Validation:** `RESPONSE_POLICY_ENFORCEMENT_GM_COMPAT_EXPORT_NAMES` in
`game/response_policy_enforcement_manifest.py`; identity + module-owner tests in
`tests/test_response_policy_enforcement_mutation.py`.

## Blocks AI3–AI11 — Leaf extraction (completed)

| Block | Subpath | Symbols moved to runtime owner |
| --- | --- | --- |
| AI3–AI5 | question resolution, validator voice, state validation | `enforce_question_resolution_rule`, `enforce_no_validator_voice`, `detect_validator_voice`, `validate_gm_state_update` |
| AI6 | prefer_specificity | `enforce_npc_response_contract`, `npc_response_contract_check`, `enforce_forbidden_generic_phrases`, `detect_forbidden_generic_phrases` |
| AI7 | forbid_secret_leak | `guard_gm_output`, `sanitize_player_facing_text` |
| AI8 | topic pressure | `enforce_topic_pressure_escalation` (+ path-only beat helpers) |
| AI9 | passive escalation | `escalate_passive_scene` (+ path-only beat helpers) |
| AI10 | scene momentum | `enforce_scene_momentum` |
| AI11 | topic progress commit | `_commit_topic_progress` |

All moved symbols remain re-exported from `game.gm` until deliberate import migration.

## Block AI2 — Manifest / runtime alignment (completed)

**Runtime owner:** `game/response_policy_enforcement.py`

**Compatibility surface:** `game.gm` re-exports (same objects) — see
`RESPONSE_POLICY_ENFORCEMENT_GM_COMPAT_EXPORT_NAMES`.

**Shared dependencies intentionally left in `game/gm.py`:** uncertainty stack
(`classify_uncertainty`, `_apply_uncertainty_to_gm`, `render_uncertainty_response`, …),
topic-pressure context/scoring (`_get_topic_pressure_context`, `_topic_progress_score`,
`_topic_pressure_snapshot_for_reply`), scene-momentum due/tag helpers
(`_scene_momentum_due`, `_extract_scene_momentum_kind`), pattern registries used across
prompt/retry paths, and NPC/scene resolution helpers.

**Governance:** `game/response_policy_enforcement_manifest.py` declares subpath classifications
and contract helper names. Direct-owner behavioral suite:
`tests/test_response_policy_enforcement_mutation.py`.

## Block AI1 — Runtime owner shell (completed)

Moved **orchestration only** out of `game/gm.py`:

| Symbol | New home |
| --- | --- |
| `apply_response_policy_enforcement` | `game/response_policy_enforcement.py` |
| `GM_METADATA_RESPONSE_POLICY_ENFORCEMENT_APPLIED` | same |
| All 15 names in `RESPONSE_POLICY_ENFORCEMENT_CONTRACT_HELPER_NAMES` | same |

`game/gm.py` retains leaf enforcement implementations and re-exports the moved symbols for
import compatibility (`game.api`, adoption gateway, downstream tests). Orchestration wrappers
call runtime-owner leaf implementations directly; shared uncertainty/topic/scene helpers remain
in `game.gm` with lazy imports from the runtime owner.

## Block Y — Finalization / contract guard (completed)

The refactor is **frozen at the orchestration boundary**: `apply_response_policy_enforcement`
(in `game/response_policy_enforcement.py`) must remain a thin loop over `RESPONSE_RULE_PRIORITY`,
delegating work to named helpers.

**Contract surfaces**

| Surface | Location |
| --- | --- |
| Required helper symbol names | `RESPONSE_POLICY_ENFORCEMENT_CONTRACT_HELPER_NAMES` in `game/response_policy_enforcement_manifest.py` |
| Full-stack orchestration call order | `RESPONSE_POLICY_ENFORCEMENT_ORCHESTRATION_SEQUENCE_FULL_POLICY` in the same module |
| Behavioral snapshots | `tests/test_response_policy_enforcement_mutation.py` |

**Final helper groups (by responsibility)**

1. **Setup / normalization** — `_normalize_response_policy_input`, `_scene_id_from_scene_envelope`,
   `_init_response_policy_enforcement_state`
2. **Validation-only** — `_apply_forbid_state_invention_validation` → `validate_gm_state_update`
3. **Metadata projection** — `_project_fallback_behavior_contract_metadata`,
   `_snapshot_response_policy_and_project_fallback_contract`, `_mark_response_policy_enforcement_applied`
4. **Deterministic text enforcement** — `_apply_must_answer_question_resolution_enforcement`,
   `_apply_diegetic_validator_voice_enforcement`, `_apply_prefer_specificity_text_enforcement`
5. **Residual / provenance-sensitive text enforcement** — `_apply_forbid_secret_leak_guard`,
   `_apply_topic_pressure_escalation_enforcement`, `_apply_escalate_passive_scene_enforcement`,
   `_apply_scene_momentum_enforcement`
6. **Post-enforcement topic commit** — `_commit_topic_progress_after_enforcement` → `_commit_topic_progress`

**Rules for future edits**

- Do **not** embed text mutation, sanitization, or metadata projection directly inside
  `apply_response_policy_enforcement`; extend or compose helpers instead.
- Do **not** reorder relative to `RESPONSE_RULE_PRIORITY`: policy precedence matches
  `game.planner_ctir_projection.RESPONSE_RULE_PRIORITY`.
- Keep `_commit_topic_progress_after_enforcement` **after** all enforcement branches and **before**
  response-policy snapshot / applied marker (current order).
- Before renaming or removing any helper in `RESPONSE_POLICY_ENFORCEMENT_CONTRACT_HELPER_NAMES`,
  update the manifest, this doc, and contract tests.
- Do **not** use this pass to add new provenance emission behavior — provenance belongs in dedicated
  pipelines and tests.

## Block U — Metadata / validation extraction (completed)

Low-risk helpers were first extracted next to `apply_response_policy_enforcement` inside
`game/gm.py` (Blocks U–X). Block AI1 moved orchestration + these helpers to
`game/response_policy_enforcement.py`. They preserve mutation order and emitted prose; only
boundaries were extracted.

**Helpers added**

| Helper | Role |
| --- | --- |
| `_normalize_response_policy_input` | Coerce `response_policy` to a dict for reads (same as prior inline `isinstance` guard). |
| `_scene_id_from_scene_envelope` | Read `scene.id` for strict-social bypass (no mutation). |
| `_init_response_policy_enforcement_state` | Shallow-copy GM dict, normalized policy, `strict_social_emission_will_apply(...)`. |
| `_apply_forbid_state_invention_validation` | Thin wrapper around `validate_gm_state_update` (validation-only branch). |
| `_project_fallback_behavior_contract_metadata` | Writes `metadata.emission_debug.fallback_behavior_contract` from a `fallback_behavior` dict. |
| `_snapshot_response_policy_and_project_fallback_contract` | Sets `out["response_policy"]` and optionally projects fallback contract (metadata-only). |
| `_mark_response_policy_enforcement_applied` | Sets `metadata[GM_METADATA_RESPONSE_POLICY_ENFORCEMENT_APPLIED]`. |

**Delegated from `apply_response_policy_enforcement` (see Block V)** — deterministic mutation helpers:

- `_apply_must_answer_question_resolution_enforcement` → `enforce_question_resolution_rule`
- `_apply_diegetic_validator_voice_enforcement` → `enforce_no_validator_voice`
- `_apply_prefer_specificity_text_enforcement` → `enforce_npc_response_contract` then
  `enforce_forbidden_generic_phrases`

**Still inline** — loop orchestration only (see **Block X**).

## Block X — Residual helper extraction (completed)

Snapshot-covered branches from Block W are thin wrappers (Block X). Implementation now lives in
`game/response_policy_enforcement.py`; leaf callees remain in `game/gm.py`.

**Helpers added**

| Helper | Wraps |
| --- | --- |
| `_apply_forbid_secret_leak_guard` | `guard_gm_output` |
| `_apply_topic_pressure_escalation_enforcement` | `enforce_topic_pressure_escalation` |
| `_apply_escalate_passive_scene_enforcement` | `escalate_passive_scene` |
| `_apply_scene_momentum_enforcement` | `enforce_scene_momentum` |
| `_commit_topic_progress_after_enforcement` | `_commit_topic_progress` (post-loop; session side-effect) |

**Intentionally remaining inline inside `apply_response_policy_enforcement`**

- Early return for non-dict `gm`.
- `_init_response_policy_enforcement_state` and the `RESPONSE_RULE_PRIORITY` loop with per-key
  `policy.get(...)` gates and `strict_social_turn` bypass checks (branch conditions unchanged).
- Calls into Block U/V/X helpers and post-loop `_snapshot_response_policy_and_project_fallback_contract` /
  `_mark_response_policy_enforcement_applied`.

## Block V — Deterministic mutation extraction (completed)

Thin wrappers isolate snapshot-covered deterministic text branches; loop priority and
strict-social bypass checks are unchanged.

**Helpers added**

| Helper | Wraps |
| --- | --- |
| `_apply_must_answer_question_resolution_enforcement` | `enforce_question_resolution_rule` |
| `_apply_diegetic_validator_voice_enforcement` | `enforce_no_validator_voice` |
| `_apply_prefer_specificity_text_enforcement` | `enforce_npc_response_contract`, then `enforce_forbidden_generic_phrases` |

**Remaining inline** — orchestration only after Block X; implementation lives in Block U/V/X helpers.

There is no separate player-facing “fallback behavior repair” mutation in this function;
`fallback_behavior` is projected as metadata only (Block U).

## Residual Inline Risk Map (Block W — completed)

Historical map of residual branches **before** Block X wrappers. Runtime behavior is unchanged;
call sites now route through the Block X helpers above.

| Branch / helper | Mutates `player_facing_text` | Mutates metadata only | Provenance-sensitive | Current test coverage (`test_response_policy_enforcement_mutation.py`) | Recommended next action |
| --- | --- | --- | --- | --- | --- |
| `guard_gm_output` (`forbid_secret_leak`) | Yes (via `sanitize_player_facing_text` + tags/debug) | Yes (tags, `debug_notes`) | Yes — replaces leaked prose with bounded safe text | **Yes** — keyword-leak snapshot (`spoiler_guard`) | Wrapped by `_apply_forbid_secret_leak_guard` (Block X). |
| `enforce_topic_pressure_escalation` (`prefer_scene_momentum`) | Yes — append or replace with pressure beat | Yes (tags, `debug_notes`) | Yes — diegetic beats + momentum kind tags | **Yes** — engineered `topic_pressure` runtime + `adjudication_query` resolution (avoids strict-social bypass) | Wrapped by `_apply_topic_pressure_escalation_enforcement` (Block X). |
| `escalate_passive_scene` (`prefer_scene_momentum`) | Yes — append passive beat | Yes | Yes | **Yes** — passive streak + neutral session | Wrapped by `_apply_escalate_passive_scene_enforcement` (Block X). |
| `enforce_scene_momentum` (`prefer_scene_momentum`) | Yes — append momentum fallback line | Yes | Yes — calls `render_scene_momentum_diegetic_append` | **Yes** — `momentum_exchanges_since` forces due beat | Wrapped by `_apply_scene_momentum_enforcement` (Block X). |
| `_commit_topic_progress` (post-loop) | No | No (updates `session.scene_runtime` topic-pressure bookkeeping, not `gm["metadata"]`) | Low — ordering-sensitive vs final reply | **Yes** — with/without `topic_pressure` runtime context | Wrapped by `_commit_topic_progress_after_enforcement` (Block X). |

**Strict-social bypass note:** `strict_social_emission_will_apply(...)` can skip the entire
`prefer_scene_momentum` stack and `forbid_secret_leak`; mutation tests pin resolutions/session
shapes that keep enforcement reachable.

**Manifest alignment:** `secret_leak_guard`, `scene_momentum_passive_escalation`, and
`topic_progress_commit` in `game/response_policy_enforcement_manifest.py` correspond to the rows
above.

## Current Shape

**Runtime owner:** `game/response_policy_enforcement.apply_response_policy_enforcement`

**Compatibility imports:** `from game.gm import apply_response_policy_enforcement` (re-export)

The orchestrator runs policy keys in `RESPONSE_RULE_PRIORITY`, skips most mutating helpers when
`strict_social_emission_will_apply(...)` is true, commits topic progress from the final reply text,
then projects policy and fallback-behavior metadata. The function sits after GPT response generation
and before final emission, so any player-facing rewrite here is provenance-relevant even when the
rewrite is deterministic and bounded.

Leaf text mutators and validation helpers live in `game/response_policy_enforcement.py`
(Cycle AI3–AI11). `game/gm.py` re-exports them and hosts shared dependencies only.

## Classification Map

| Subpath | Current helper / location | Classification | Mutates text? | Split note |
| --- | --- | --- | --- | --- |
| `fallback_behavior_contract` handling | inline metadata projection after enforcement loop | metadata-only projection | No | Can move to a projection helper once text-mutating enforcement is isolated. Preserve `metadata.emission_debug.fallback_behavior_contract` shape exactly. |
| question resolution enforcement | `enforce_question_resolution_rule` under `must_answer` | text-mutating enforcement | Yes | Prepends/appends grounded answer text through uncertainty rendering when a direct question was not answered. Keep after strict-social bypass until social ownership is separately documented. |
| NPC response contract enforcement | `enforce_npc_response_contract` under `prefer_specificity` | text-mutating enforcement | Yes | Adds a deterministic concrete next-step sentence when NPC specificity is missing. This is not fallback selection, but it authors prose after GPT output. |
| validator voice rewrite | `enforce_no_validator_voice` under `diegetic_only` | fallback/provenance-relevant mutation | Yes | Direct-question rewrites route through uncertainty rendering; non-question rewrites can fall back to a world/scene line. This path should carry explicit provenance expectations before extraction. |
| forbidden generic phrase rewrite | `enforce_forbidden_generic_phrases` under `prefer_specificity` | text-mutating enforcement | Yes | Replaces forbidden stock sentences with scene-anchored specificity. It should remain behavior-frozen until sentence-level snapshots cover all replacement labels. |
| scene momentum / passive escalation | `enforce_topic_pressure_escalation`, `escalate_passive_scene`, `enforce_scene_momentum` under `prefer_scene_momentum` | fallback/provenance-relevant mutation | Yes | May append or replace text with topic-pressure, passive-pressure, or deterministic scene momentum beats. `enforce_scene_momentum` calls diegetic fallback rendering, so future split should isolate line selection and provenance. |
| social response structure handling | strict-social bypass via `strict_social_emission_will_apply` | legacy/ambiguous | No direct text mutation here | This function does not currently enforce social response structure directly. Instead, strict social turns bypass most text-mutating helpers so social exchange emission owns structure elsewhere. Keep this as an explicit bypass classification. |
| state update validation | `validate_gm_state_update` under `forbid_state_invention` | validation-only | No | Normalizes proposed state/update payloads. It belongs with validation, not player-facing text enforcement. |
| secret leak guard | `guard_gm_output` under `forbid_secret_leak` | fallback/provenance-relevant mutation | Yes | Sanitizes leaks and may replace player-facing text with bounded uncertainty text. Treat as provenance-relevant before any split. |
| topic progress commit | `_commit_topic_progress` after enforcement loop | metadata-only projection | No | Updates runtime/topic tracking from already-final reply text. It is not prose authorship, but ordering matters. |
| policy snapshot and applied marker | inline `out["response_policy"]` and metadata marker | metadata-only projection | No | Preserve existing metadata keys and value shapes. |

## Proposed Future Split Order

Orchestration and leaf extraction are **complete** (Blocks U–Y, AI1–AI12).

**Optional follow-ups (outside Cycle AI):**

1. Migrate import sites from `game.gm` to `game.response_policy_enforcement` deliberately.
2. Collapse duplicate `_reply_already_has_concrete_interaction` copies in final-emission modules.
3. Move uncertainty rendering stack upstream when planner-prepared emission owns answer text.

## Non-Goals For This Block

- Do not regress the orchestration boundary (see Block Y rules).
- Do not change emitted prose or mutation order without updating snapshots and manifest contracts.
- Do not touch `final_emission_gate`, prompt construction, or retry fallback from this seam.

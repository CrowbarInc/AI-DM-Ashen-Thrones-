# Realization Cursor Handoff

Branch context: `feature/failure-locality`

This handoff reflects the **Block AO** advisory audit refresh (failure-locality
closeout). Full milestone narrative and stopping-point guidance:
`docs/realization_failure_locality_closeout.md`.

- `tools/realization_layer_audit.py`: `HIGH=1261`, `REVIEW=710`, `INFO=8945`
- `tools/realization_provenance_audit.py`: `HIGH=958`, `REVIEW=1280`, `INFO=738`

The audits remain advisory and lexical. They are useful for locating remaining
behavioral ownership risks, not for proving failures or setting a zero-findings
target.

# What Is Now Protected By Tests

- Upstream prepared emission provenance:
  `tests/test_upstream_response_repairs.py`,
  `tests/test_realization_provenance.py`
- Diegetic fallback caller provenance:
  `tests/test_diegetic_fallback_narration.py`
- Retry deterministic and terminal fallback branches:
  `tests/test_gm_retry.py`
- Retry selector purity and selector return contract:
  `tests/test_gm_retry.py`,
  `docs/retry_fallback_selector_contract.md`
- `build_messages` as projection-only prompt construction:
  `tests/test_build_messages_projection.py`
- Response policy enforcement mutation snapshots and split-readiness manifest:
  `tests/test_response_policy_enforcement_mutation.py`,
  `game/response_policy_enforcement_manifest.py`,
  `docs/response_policy_enforcement_split_plan.md`
- Opening deterministic fallback exact text, source, and provenance:
  `tests/test_final_emission_gate.py`,
  `tests/test_diegetic_fallback_narration.py`
- Final emission source/family branch snapshots for generated candidates,
  upstream prepared repairs, opening fallback, global scene fallback, and strict
  social terminal fallback:
  `tests/test_final_emission_gate.py`
- API narration path selection for normal GPT, planner convergence emergency,
  GPT budget/provider failure, targeted retry, and terminal retry:
  `tests/test_api_narration_path_selection.py`
- API narration hub extraction boundary / contract guard (Blocks AJ–AM snapshots +
  Block AN stop point): `tests/test_api_narration_path_selection.py`
  (`test_block_an_*`, registry tuples `_BLOCK_AL_*` / `_BLOCK_AM_*`)

# Low-Risk Seams / Leave Alone

- `game.upstream_response_repairs`: now the tested owner of upstream prepared
  emission payloads. Leave payload prose and metadata shape stable.
- `game.diegetic_fallback_narration`: direct renderers remain legacy plain-text
  helpers. Caller provenance is the protected boundary; do not rewrite template
  text for cleanup.
- `game.gm.build_messages`: current tests frame it as prompt projection, not a
  fallback author. Leave unless projection drift appears.
- Retry selector boundary: selectors exist and are tested as non-mutating.
  Avoid churn unless a specific Cursor refactor needs it.
- Final emission metadata helpers: keep source/family metadata explicit even
  when audits flag the vocabulary.

# Remaining Cursor-Required Seams

## apply_response_policy_enforcement split

Current status (**Cycle AI complete — Block AI12**):

- **Runtime owner:** `game/response_policy_enforcement.py` (Blocks AI1–AI11).
- **Manifest/runtime alignment:** Block AI2 + AI12 compat registry
  (`RESPONSE_POLICY_ENFORCEMENT_GM_COMPAT_EXPORT_NAMES`).
- Orchestration, contract helpers, and all manifest leaf mutators live on the runtime owner;
  `game.gm` re-exports the compat surface only.
- Mutation snapshots + module-owner tests in `tests/test_response_policy_enforcement_mutation.py`.

Shared dependencies intentionally remain in `game/gm.py` (uncertainty rendering,
topic-pressure context/scoring, scene-momentum due-bit helpers, pattern registries used by
prompt/retry). These are not enforcement ownership residue.

Optional follow-ups (outside Cycle AI):

1. Deliberate import migration from `game.gm` to `game.response_policy_enforcement`.
2. Upstream planner-prepared emission for provenance-sensitive rewrite paths.

## Opening fallback ownership move upstream

Current status:

- Exact deterministic opening fallback text is snapshotted.
- Curated fact source, failed-closed behavior, opening fallback family, temporal
  frame, and FEM provenance are covered.

Why Cursor is required:

The final gate still composes opening fallback prose. The current inputs are
bounded and tested, but final emission should ultimately select prepared
opening fallback text rather than author it.

Recommended Cursor action:

1. Add an upstream prepared opening fallback payload.
2. Preserve the exact current fallback text and metadata keys.
3. Teach the final gate to select the prepared opening fallback.
4. Leave the old gate-local helper as a compatibility path only until coverage
   proves the new upstream path is equivalent.

## final_emission_gate gate-local fallback reduction

Current status:

- Important final source branches are snapshotted.
- Upstream prepared branch provenance is explicit.
- Opening fallback provenance is explicit.

Why Cursor is required:

`apply_final_emission_gate` is the highest-risk realization dependency hub. It
combines validation, repair, prepared emission selection, sealed fallback,
opening fallback, strict social terminal behavior, containment, and FEM
packaging.

Recommended Cursor action:

1. Do not perform a broad rewrite.
2. Reduce one fallback branch at a time.
3. Start with branches already backed by upstream prepared emission or sealed
   fallback pools.
4. Preserve `final_emitted_source`, `final_route`, fallback family, and FEM
   payload shape exactly.
5. Defer strict social and terminal repair branches until upstream/API/retry
   provenance remains stable after the earlier moves.

Explicit warning:

Do not broadly rewrite `final_emission_gate`. It is the most dangerous place to
make sweeping edits because the current tests now pin several branch-local
source/provenance behaviors. Treat it as a branch-by-branch reduction project.

## API narration hub — extraction phase complete (Block AN stop point)

**Status:** The planned **metadata / orchestration / policy-handoff** extraction for the
manual-play API narration hub is **complete** for the current failure-locality effort
(Blocks AJ–AM). **Block AN** adds contract guards and treats this boundary as a **stop
point** for further hub extraction unless new evidence appears (see below).

Completed slices:

- **Block AJ:** `_narration_hub_finalize_annotation_parts`, `_classify_narration_hub_route`,
  `_build_narration_hub_route_meta` — route metadata and `annotate_narration_path_kind`
  kwargs only.
- **Block AK:** Contract tests (`test_block_ak_*`) — route helpers stay metadata-only.
- **Block AL:** Orchestration handoff order snapshots (GPT → retry → policy → turn-support
  final gate via `_finalize_player_facing_for_turn`).
- **Block AM:** `_apply_narration_hub_policy_handoff` — response-policy enforcement seam
  after GPT/retry (no GPT, retry execution, or final emission gate inside the adapter).

**Route helper contract (AJ/AK — `game/api.py`):** unchanged — **allowed:** route labels and
annotation kwargs from read-only `resolution` / `bundle_seam_requirement`; **forbidden:**
GPT, retry execution, final emission, mutating `player_facing_text`, fallback prose
selection.

**What remains intentionally inside `_build_gpt_narration_from_authoritative_state`:**

- Resolution hygiene, CTIR attach, narration plan bundle ensure, planner convergence
  emergency exits, `build_messages` / prompt payload construction.
- GPT calls (`call_gpt` / bounded wrapper), `guard_gm_output`, upstream API error handling,
  targeted retry loop, deterministic and terminal retry fallbacks, latency accounting.
- Prompt-derived GM field merges, `_attach_scene_opening_curated_facts_to_gm`, policy
  handoff via `_apply_narration_hub_policy_handoff`, session policy fingerprint and
  progression storage, narration seam finalize annotations (`annotate_narration_path_kind`,
  continuation classification, planner metadata attachment).

Final player-facing emission still runs in **`game/api_turn_support`** (`apply_final_emission_gate`), not in the hub builder.

**Pause guidance (failure-locality / realization):** Do **not** continue broad hub
refactoring for orchestration alone. Resume extraction or deep edits only when driven by a
**concrete bug**, a **targeted audit finding**, or an approved design change — not by
lexical audit volume or cosmetic thinning.

**Safe work without runtime risk:** advisory audit re-runs, doc updates (this file,
`triage_ledger`, selector/manifest docs), and narrow regression tests that freeze observed
behavior.

## Retry fallback: current status / likely leave alone for now

Current status:

- Selectors exist.
- Selector purity is tested.
- Deterministic retry and terminal retry branches have provenance and metadata
  snapshots.
- `docs/retry_fallback_selector_contract.md` documents selector/caller
  responsibilities.

Why it can wait:

Retry fallback still authors emergency text, but it is now explicit, local,
tested, and labeled as `retry_terminal_fallback`. The return-shape extraction
already captured the main failure-locality win.

Recommended Cursor action:

Leave retry fallback alone unless required by another refactor. If touched,
limit changes to selector/caller cleanup under the existing contract and avoid
changing emitted prose.

# Exact Recommended Cursor Refactor Order

1. `apply_response_policy_enforcement` split:
   metadata-only projection, validation-only normalization, then deterministic
   text-mutating helpers.
2. Opening fallback ownership move upstream:
   introduce prepared opening fallback payload and make the gate select it.
3. `final_emission_gate` branch-local fallback reduction:
   prepared/sealed branches first, no broad rewrite.
4. **API narration hub:** Blocks AJ–AM done; **Block AN stop point** — no further hub
   extraction unless bug/audit-driven (see **API narration hub** section above).
5. Retry fallback cleanup only if necessary:
   keep selector contract and emitted prose stable.

# Why Codex Should Pause Runtime Refactors

Codex passes have already created the maps, snapshots, selector docs, and
metadata-only coverage needed for the next behavioral work. Further Codex
runtime edits would mostly increase churn in high-overlap functions that now
need interactive, branch-by-branch refactors with close review.

Codex can safely continue with:

- Re-running advisory audits.
- Refreshing docs after Cursor changes (`realization_triage_ledger.md`,
  `realization_failure_locality_closeout.md` when milestones shift).
- Adding narrow regression tests that freeze current behavior.
- Fixing doc references if paths or helper names move.

Codex should not:

- Change production prose.
- Refactor `final_emission_gate`.
- Move fallback ownership.
- Wire advisory audits into CI.
- Treat lexical audit counts as failures.

# Known Metadata-Only Fixes Already Made

- Upstream prepared emission payloads carry
  `realization_fallback_family=upstream_prepared_emission`.
- Existing prepared emission payloads are normalized when family metadata is
  missing, invalid, or legacy.
- Retry deterministic and terminal fallback outputs stamp
  `retry_terminal_fallback`.
- GPT budget/provider failures carry the provider/budget fallback family.
- Strict social deterministic fallback details carry the strict social family.
- Opening deterministic fallback records source/family data through response
  type debug and FEM.
- Final gate generated candidates keep source attribution without gaining a
  fallback family.
- Response policy enforcement now has a metadata-only split-readiness manifest.

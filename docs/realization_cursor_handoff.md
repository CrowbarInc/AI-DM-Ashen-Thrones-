# Realization Cursor Handoff

Branch context: `feature/failure-locality`

This handoff reflects the post-Block-S state after refreshing the advisory
audits:

- `tools/realization_layer_audit.py`: `HIGH=1218`, `REVIEW=706`, `INFO=8732`
- `tools/realization_provenance_audit.py`: `HIGH=893`, `REVIEW=1261`, `INFO=673`

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

Current status:

- Mutation snapshots exist.
- A declarative manifest classifies subpaths.
- The split plan is documented.

Why Cursor is required:

`apply_response_policy_enforcement` still sits after GPT output and can mutate
`player_facing_text` before final emission. It mixes metadata projection,
validation-only work, deterministic text enforcement, and
fallback/provenance-relevant rewrites. The function needs careful interactive
editing with constant test feedback.

Recommended Cursor action:

1. Extract metadata-only projection helpers for fallback behavior debug,
   response policy snapshot, applied marker, and topic progress commit.
2. Extract validation-only state/update normalization.
3. Group deterministic text-mutating enforcement without changing order or
   emitted text.
4. Leave validator voice, secret leak guard, scene momentum, passive escalation,
   and topic pressure in place until each path has explicit branch-level
   provenance assertions.

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

## API narration hub simplification

Current status:

- Path-selection snapshots exist for normal GPT, planner convergence emergency,
  GPT budget/provider failure, targeted retry, and terminal retry.

Why Cursor is required:

`_build_gpt_narration_from_authoritative_state` coordinates CTIR/bundle setup,
prompt building, GPT calls, policy enforcement, retry routing, emergency
fallback, and final emission. Even if downstream helpers are bounded, this hub
can still hide semantic changes through orchestration.

Recommended Cursor action:

1. Extract path classification and provenance trace assembly first.
2. Preserve CTIR/bundle reuse and call ordering.
3. Keep text production in the current downstream owners during the first pass.
4. Only split emergency route behavior after snapshots cover the extracted
   classification layer.

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
4. API narration hub simplification:
   extract path/provenance orchestration before behavior.
5. Retry fallback cleanup only if necessary:
   keep selector contract and emitted prose stable.

# Why Codex Should Pause Runtime Refactors

Codex passes have already created the maps, snapshots, selector docs, and
metadata-only coverage needed for the next behavioral work. Further Codex
runtime edits would mostly increase churn in high-overlap functions that now
need interactive, branch-by-branch refactors with close review.

Codex can safely continue with:

- Re-running advisory audits.
- Refreshing docs after Cursor changes.
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

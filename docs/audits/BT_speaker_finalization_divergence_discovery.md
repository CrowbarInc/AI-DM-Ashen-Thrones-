# BT Speaker Finalization Divergence Discovery

Date: 2026-06-20  
Scope: discovery only; no runtime behavior, public API, or golden fixture changes

## A. Executive summary

Speaker-finalize parity is **partially measurable**, but not yet measurable as one repeatable end-to-end contract.

The repository can already:

- compare the gate speaker-enforcement result with an isolated mirror, including normalized text, repair flags, reason code, and post-validation;
- identify the first probed post-speaker layer that changes normalized text on the strict-social path;
- detect an emitted speaker signature from final prose;
- project replay `selected_speaker_id`, final text/hash, mutation lineage, fallback ownership, and speaker-repair events;
- compare replay observations across runs and classify speaker and text-fingerprint drift.

The missing join is important. No current record captures, for the same case, (1) pre-speaker-finalize text and speaker, (2) post-speaker-finalize text and speaker, (3) final-emission text and speaker, and (4) replay-projected text and speaker. The test probe stores only `layer_id` plus a change boolean. Golden replay's `selected_speaker_id` is selected from social trace/latest target/resolution state, not parsed from the finalized emitted text. Runtime stage snapshots contain text fingerprints and routing/fallback fields, but there is no snapshot immediately before and after speaker enforcement and no emitted-speaker identity field.

Exact missing evidence/hooks:

- normalized input/output value or hash per post-speaker probe event;
- emitted speaker signature at the pre-enforcement, post-enforcement, final-emission, and replay-final checkpoints;
- a canonical resolved speaker ID for each emitted signature, or an explicit `unresolved` state;
- expected/canonical speaker ID and attribution/owner source in the same comparison record;
- a deterministic first-divergence result that considers both speaker identity and normalized text;
- an explicit comparison between final gate output and replay `final_text`, and between emitted final speaker and replay `selected_speaker_id`.

The safest next implementation block is a **test-only `SpeakerContractObservation`/risk helper** beside `tests/helpers/post_speaker_finalize_probe.py`. It should compose existing helpers without changing runtime instrumentation: retain normalized hashes and emitted-speaker signatures at checkpoints, join the final gate output to `project_turn_observation`, compute the first divergence, and emit a stable risk score. Start with the existing Block S/T/U strict-social fixtures, then add replacement/fallback cases. Runtime changes should be considered only if test coverage proves a checkpoint cannot be observed through wrappers.

## B. File/path inventory

| file | symbol/function/class | role | runtime/test/replay/fallback/shared | relevance to BT | risk notes |
|---|---|---|---|---|---|
| `game/speaker_contract_enforcement.py` | `enforce_emitted_speaker_with_contract` | Validates final candidate speaker, mutates text/effective social state when repair is required, and records enforcement payload | runtime/shared | Canonical speaker-finalize owner | Can local-rebind, canonical-rewrite, or replace with narrator-neutral/strict-social fallback; identity must be sampled before and after |
| `game/speaker_contract_enforcement.py` | `validate_emitted_speaker_against_contract` | Compares emitted signature with selection contract | runtime/shared | Supplies expected speaker and mismatch reason | Validation uses prose signature/contract; it is not a replay parity comparison |
| `game/speaker_contract_enforcement.py` | `_apply_speaker_contract_repairs`, `_sync_eff_social_to_resolution`, `_merge_speaker_enforcement_into_outputs` | Mutates speaker text/state and publishes metadata | runtime/shared/fallback | Defines repair and ownership surface | Private repair helper is already mirrored by tests; avoid making it a new public API |
| `game/emitted_speaker_signature.py` | `detect_emitted_speaker_signature` | Parses label/name, explicit attribution, interruption, and generic fallback signals from text | runtime/shared | Existing identity extractor for every BT checkpoint | Produces a label/name, not a guaranteed canonical NPC ID |
| `game/final_emission_strict_social_stack.py` | `run_strict_social_stack` path around lines 261-328 | Calls speaker enforcement, then may apply dialogue-plan stripping and further stack work | runtime/shared | Primary post-speaker producer/consumer path | `strip_dialogue_from_text` is an observed first diverger in a failing-plan fixture |
| `game/final_emission_terminal_pipeline.py` | `run_gate_terminal_enforcement_pipeline` | Applies visibility, fallback behavior, referent clarity, emergency/sealed replacement, continuity, and narrative-mode tail work | runtime/shared/fallback | Late text/speaker mutation surface before finalize | Replacement can change attribution after speaker enforcement; metadata is richer than identity observability |
| `game/final_emission_visibility_fallback.py` | `apply_visibility_enforcement`, referential clarity helpers | Performs semantic/local replacement and fallback selection | runtime/fallback/shared | Likely post-speaker identity/text diverger | Existing flags describe replacement but do not preserve before/after emitted identity |
| `game/final_emission_finalize.py` | `finalize_emission_output` | Sanitizes text, strips route-illegal contamination, normalizes/assigns final text, stamps FEM and exit telemetry | runtime/shared | Final-emission projection checkpoint | Packaging is intended to be non-semantic, but sanitation/strip can still change normalized text |
| `game/stage_diff_telemetry.py` | `snapshot_turn_stage`, `record_stage_snapshot`, `diff_turn_stage` | Records bounded text fingerprints plus route/fallback/repair state | runtime/observability/shared | Existing runtime instrumentation candidate | No pre/post speaker-enforcement stage and no emitted speaker field; expanding it is unnecessary for first BT block |
| `game/final_emission_replay_projection.py` | `_fem_speaker_repair_projections`, `build_fem_runtime_lineage_events` | Projects finalized FEM speaker repairs and mutation/fallback events | runtime/read-side/replay | Identifies repair kind and owner | Records that a repair occurred, not expected versus final emitted identity |
| `game/post_emission_speaker_adoption.py` | `_resolve_visible_grounded_opening_speaker_canon`, adoption/invalidation entrypoints | Parses finalized output and updates or clears interaction speaker state after emission | runtime/post-emission/shared | Useful canonical-resolution precedent and downstream consumer | Deliberately narrow adoption rules; should not be reused as a general BT resolver without isolating policy |
| `tests/helpers/speaker_relocation_shadow_harness.py` | `SpeakerShadowEquivalence`, `install_dual_run_enforce`, `with_finalize_delta` | Captures pre/post enforcement, compares gate and isolated repair, flags downstream normalized-text delta | test-only/shared fixture | Strong base for BT checkpoint capture | Final comparison is only a boolean; speaker signature and replay projection are absent |
| `tests/helpers/post_speaker_finalize_probe.py` | `LayerTextDelta`, `install_post_speaker_text_probes`, `first_post_speaker_normalized_divergence` | Wraps ordered late-stack seams and locates first normalized-text change | test-only/shared | Existing first-divergence mechanism | Event has no before/after hash/text or speaker identity; strict-social path coverage only |
| `tests/test_block_u_finalize_stack_divergence.py` | Block U/V/W/Z tests | Asserts first post-speaker divergence, dialogue-plan mismatch, alias behavior, and final visible speaker | test-only | Current closest parity/divergence suite | Uses hand assertions; no reusable risk metric or replay join |
| `tests/test_block_t_speaker_relocation_shadow_equivalence.py` | Block T tests | Asserts gate/isolated normalized parity and repair metadata parity | test-only | Validates speaker-finalize implementation equivalence | Allows downstream finalize delta without identifying its identity effect |
| `tests/test_speaker_contract_enforcement.py` | enforcement/signature/repair tests | Covers identity mismatch, fallback labels, local rebind, canonical rewrite, neutral bridge, and replacement metadata | test-only/fallback/shared | Broad producer behavior evidence | Mostly unit/path assertions, not checkpoint parity |
| `tests/helpers/golden_replay_projection.py` | `_resolve_selected_speaker_id`, `project_turn_observation`, `golden_text_hash` | Projects replay speaker, final text/hash, FEM, lineage, and missing-source evidence | test-only/replay/shared | Canonical replay observation authority | `selected_speaker_id` comes from routing/state, not final emitted prose |
| `tests/helpers/golden_replay.py` | `protected_social_speaker_observation_expectation`, drift/rerun helpers | Validates expected speaker/final text and reports structural/semantic/exact/rerun drift | test-only/replay | Existing expected-versus-actual and mismatch diagnostics | Speaker drift and text drift are independent; no finalize checkpoint localization |
| `tests/helpers/replay_drift_taxonomy.py` | speaker/text field ownership constants and classifier | Routes `selected_speaker_id` drift to speaker owner and text hash drift to replay/evaluator | test-only/replay | Existing diagnostic classification | Classification identifies category/owner, not first mutation checkpoint |
| `tests/helpers/replay_drift_rows.py` | `RERUN_DELTA_KEY_FIELD_PATHS` | Maps speaker to `selected_speaker_id` and text fingerprint to `final_text` | test-only/replay | Repeat-run parity evidence | Does not distinguish selection-state drift from emitted-attribution drift |
| `tests/test_golden_replay_projection.py` and `tests/test_golden_replay_structural_invariants.py` | projection and protected speaker assertions | Lock projection schema and selected speaker expectations | test-only/replay | Current golden speaker evidence | No post-finalize emitted signature assertion |

Ordering on the strict-social path is: strict-social candidate construction and early plan checks -> `enforce_emitted_speaker_with_contract` -> possible post-enforcement dialogue stripping/repairs -> terminal visibility/fallback/continuity stack -> `finalize_emission_output` -> API/post-GM adoption consumers -> replay projection from the resulting snapshot/payload.

## C. Current evidence

| metric component | currently measurable? yes/no/partial | current source of evidence | missing evidence | recommended next action |
|---|---|---|---|---|
| Gate versus isolated speaker-finalize parity | yes | `SpeakerShadowEquivalence` compares normalized text, repair flags, reason, and post-validation | None for current mirror scope | Reuse unchanged as the enforcement parity input |
| Pre versus post speaker-finalize normalized text | yes | `pre_speaker_text` and `gate_post_speaker_text` in shadow harness | Stable hashes in a serializable observation | Add hashes/normalized values in test helper |
| First post-speaker normalized-text divergence | yes, strict-social probes | `first_post_speaker_normalized_divergence` and ordered layer wrappers | Input/output evidence; non-strict/fallback coverage | Enrich `LayerTextDelta` and add representative replacement fixtures |
| Speaker identity preservation across finalize | partial | Enforcement post-validation plus final text hand assertions and emitted signature parser | Identity sampled/resolved at every checkpoint | Parse each checkpoint and compare canonical ID/label explicitly |
| Final normalized text versus post-speaker text | yes/partial | `with_finalize_delta` boolean and final output | First responsible layer and comparable evidence payload are separate | Join shadow record to enriched layer events |
| Final emission versus replay normalized text | partial | Gate output and replay `final_text`/`final_text_hash` exist independently | One helper asserting/hash-comparing both | Add a test-only final-to-replay projection adapter |
| Replay expected versus actual speaker | yes | protected expectations and rerun drift on `selected_speaker_id` | Whether final prose actually attributes that speaker | Add emitted-final-signature versus projected-selected-ID comparison |
| Replay expected versus actual normalized text | yes when exact text is opted in; otherwise hash/rerun only | `classify_golden_turn_drift`, `golden_text_hash`, rerun scorecard | Default semantic equivalence is not exact normalized parity | BT metric should state whether exact-text expectation is available |
| Speaker repair/fallback owner | partial | FEM enforcement reason and runtime lineage speaker-repair events | Owner/attribution at each checkpoint; owner for unresolved final attribution | Include enforcement owner/source and explicit missing-owner flags |
| Replacement/fallback identity preservation | partial | replacement flags, fallback lineage/owners, enforcement tests | Before/after emitted identity on each replacement family | Add a small fixture matrix for local substitution, sealed, emergency, and narrator-neutral cases |
| First divergence across identity and text | no | Text-only first-diverger and replay mismatch diagnostics are separate | Unified ordered checkpoint comparison | Implement deterministic `first_divergence_checkpoint` in test helper |

## D. Divergence model proposal

Use one ordered observation per case. Normalize text with the existing player-facing/golden normalization function selected by the test contract, and parse speaker identity with `detect_emitted_speaker_signature` at every text-bearing checkpoint.

1. **P0: pre speaker finalize** - text passed to `enforce_emitted_speaker_with_contract`; expected contract speaker ID/name; parsed emitted signature.
2. **P1: post speaker finalize** - returned enforcement text; parsed signature; enforcement reason, repair flags, post-validation result, and owner `game.speaker_contract_enforcement`.
3. **P2a...P2n: post-speaker layer events** - ordered late-stack layer ID with normalized input/output hashes and parsed input/output signatures. Preserve `PRE_SPEAKER_PROBE_IDS` exclusion.
4. **P3: final emission projection** - finalized `player_facing_text`, normalized hash, parsed signature, FEM speaker reason, final route/source, replacement/fallback owner fields, and runtime lineage speaker-repair events.
5. **P4: replay/golden projection** - `final_text`, normalized hash, `selected_speaker_id`, `selected_speaker_source`, expectation when present, and missing-source/unavailable evidence.
6. **P5: post-emission state projection (diagnostic only)** - visible grounded speaker resolution/adoption result when the scenario exercises takeover or stale-interlocutor behavior. Do not treat state adoption as speaker-finalize authority.

For semantic replacement/fallback cases, P2 must label the projection family (`dialogue_plan_strip`, `referential_local_substitution`, `visibility_hard_replacement`, `strict_social_emergency_fallback`, `sealed_replacement`, `narrator_neutral`) and carry selection/content owner fields when FEM provides them.

The first divergence is the earliest ordered checkpoint where either:

- normalized text differs from the immediately previous checkpoint; or
- resolved speaker identity differs from the expected canonical identity or immediately previous resolved identity.

An unresolved signature is not silently equal to `None`: record `speaker_status` as `resolved`, `neutral`, `unattributed`, `ambiguous`, or `unresolved`. This prevents narrator-neutral output from being scored as an accidental missing speaker while still penalizing unexplained attribution loss.

## E. Proposed Speaker Contract Risk metric

Define a per-case score from 0 (fully observable and matching) to 100 (high contract risk):

`Speaker Contract Risk = D + S + T + A`, capped at 100.

| component | points | rule |
|---|---:|---|
| `D` first-divergence localization | 0 or 15 | 0 when no mismatch exists, or a mismatching run has a named first checkpoint/layer; 15 when any mismatch exists but the first divergence is absent/unobservable |
| `S` speaker identity | 0, 20, or 40 | 0 when P1, P3, and P4 preserve the expected canonical speaker (or explicitly valid neutral state); 20 when one checkpoint is unresolved/ambiguous; 40 when a resolved identity mismatches expected identity or final emitted identity mismatches replay `selected_speaker_id` |
| `T` normalized text | 0, 10, or 25 | 0 when required checkpoint comparisons match; 10 when P1->P3 changes but a named allowed layer and evidence explain it; 25 when final/replay text mismatches or an unexplained P1->P3 change occurs |
| `A` attribution/owner metadata | 0-20 | Add 5 each when expected speaker source, emitted signature/resolution source, enforcement/replacement owner, or replay `selected_speaker_source` is missing where applicable |

Report the raw component values and evidence, not only the total. Aggregate a fixture set with count, mean, maximum, and counts by band: `0-19 low`, `20-39 guarded`, `40-69 elevated`, `70-100 high`. A behavior-preserving refactor should require no score increase per protected case and no new case above its prior band. Cases without exact-text expectations may set `T` from P1->P3 and P3->P4 parity while marking golden-exact-text coverage unavailable.

This formula deliberately separates a mismatch from poor observability: a known, localized, owner-attributed transformation scores lower than the same transformation with no checkpoint evidence.

## F. Recommended next Cursor blocks

### BT1 - Test-only checkpoint observation and metric

- **Target files:** new `tests/helpers/speaker_contract_risk.py`; extend `tests/helpers/post_speaker_finalize_probe.py`; new focused `tests/test_speaker_contract_risk.py`.
- **Intent:** Add immutable checkpoint/event records with normalized hashes, emitted signatures, first divergence, component scores, and stable JSON-like output. Reuse existing normalization and signature helpers.
- **Expected tests:** no-divergence score 0; known dialogue-plan strip localizes first divergence; resolved identity mismatch scores 40; missing owner/source increments `A`; mismatching run without layer evidence increments `D`.
- **Rollback risk:** very low; test-only. Main risk is coupling to private wrappers, already accepted by Block U tests.

### BT2 - Final emission to replay parity adapter

- **Target files:** `tests/helpers/speaker_contract_risk.py`, `tests/helpers/golden_replay_fixtures.py` or a new narrow BT fixture adapter, `tests/test_speaker_contract_risk.py`.
- **Intent:** Project a finalized gate output through canonical `project_turn_observation` and compare P3 final text/signature with P4 `final_text`/`selected_speaker_id`/source.
- **Expected tests:** final text hash parity; selected speaker parity; routing-selected speaker versus emitted-attribution mismatch is detected; unavailable speaker source is explicit.
- **Rollback risk:** low; test-only, but fixture construction must preserve canonical replay payload shape.

### BT3 - Replacement/fallback fixture matrix

- **Target files:** `tests/test_speaker_contract_risk.py`; reuse `tests/helpers/boundary_semantic_repair_fixtures.py`, `tests/helpers/fallback_behavior_fixtures.py`, and Block S/T/U fixture builders where suitable.
- **Intent:** Measure local rebind, canonical rewrite, narrator-neutral, referential substitution, strict-social emergency fallback, and sealed replacement without changing their behavior.
- **Expected tests:** each family has a named first divergence or explicit no-divergence; owner fields are present when applicable; valid neutral attribution is not treated as a mismatch.
- **Rollback risk:** low to moderate; test fixtures may be sensitive to gate ordering, but no runtime code changes are required.

### BT4 - Optional runtime checkpoint only if BT1-BT3 prove a gap

- **Target files:** preferably `game/stage_diff_telemetry.py` plus the narrow speaker-enforcement call site in `game/final_emission_strict_social_stack.py`; related telemetry tests.
- **Intent:** Add bounded pre/post speaker checkpoint fingerprints and non-authoritative emitted signature fields only when test wrappers cannot observe a production path.
- **Expected tests:** telemetry remains observational, bounded, and cannot steer orchestration; existing stage-diff schema consumers remain compatible.
- **Rollback risk:** moderate because runtime payload shape changes. Defer this block unless a concrete blind path is demonstrated.

## Validation performed

- `git status --short` - passed; worktree was clean before this report.
- `rg -n -i ...` repository-wide speaker/finalize/normalized/emission/golden/replay/fallback/replacement search - passed.
- `rg --files tests | Sort-Object` - passed.
- Targeted `rg` and `Get-Content` inspection of runtime, probe, replay projection, drift, and test files - passed.
- `python -m pytest --collect-only -q` - not available because `python` is not on `PATH`.
- Bundled runtime equivalent with `.venv` site packages: `C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest --collect-only -q` - passed and collected the repository suite, including 4 Block S, 4 Block T, 6 Block U, 36 speaker-contract, 25 golden-projection, and 4 post-emission-speaker-adoption tests.

No behavior, fixtures, public APIs, or golden observations were modified during this audit.

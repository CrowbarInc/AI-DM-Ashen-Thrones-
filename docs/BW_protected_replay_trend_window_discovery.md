# BW Protected Replay Trend Window #1 Discovery

## Executive summary

The repository already has most of the read-side machinery needed for Golden Transcript Drift:
deterministic fake-GPT replay fixtures, a canonical 41-field observation projection, a report-only
two-run comparator, owner-drift taxonomy, and JSON/Markdown scorecard writers. BW should extend
those test-only surfaces rather than add runtime instrumentation.

The smallest useful implementation is a test/tooling harness that executes an explicit protected
scenario registry `N` times in isolated storage roots, writes one normalized observation JSON per
run, and compares every run to run 0. Extend the existing comparator for first-class source and
mutation deltas and align by `(scenario_id, turn_id or turn_index)`, not list position.

There is one immediate prerequisite: the documented and CI command
`python -m pytest -m golden_replay -q` currently selects **zero tests**. The golden replay suite was
decomposed, but the new modules have no `golden_replay` marker. Also,
`tests/test_golden_replay.py` now contains only a redirect-stub test, while the manifest and curated
failure corpus still name tests under that old module. BW must use an explicit current registry (and
the marker/manifest references should be repaired in a separate additive maintenance block).

## Protected replay entry points

| File | Current role |
|---|---|
| `tests/test_golden_replay_structural_invariants.py` | Six short chat-pipeline scenarios. This is the current core protected input set: directed speaker, vocative override, wrong-speaker repair, action outcome, sanitizer leakage, and dialogue-lock follow-up. |
| `tests/test_golden_replay_long_session.py` | Three 25-turn Frontier Gate runs: protected structural stability, resume persistence support, and diagnostic direct intrusion. |
| `tests/test_golden_replay_direct_seam.py` | Two direct final-emission seam scenarios that avoid full chat orchestration. |
| `tests/test_golden_replay_scenario_spine.py` | One three-branch scenario-spine smoke replay. |
| `tests/test_golden_replay.py` | Relocation stub only; it no longer runs the protected scenarios described by older docs. |
| `tests/helpers/golden_replay.py` | Orchestration (`run_golden_replay`), assertion/drift helpers, long-session summaries, `compare_golden_replay_reruns`, and debug/report rendering. |
| `tests/helpers/golden_replay_api.py` | Public facade over the implementation helper; new external test/tool consumers should prefer it. |
| `tests/helpers/golden_replay_fixtures.py` | Code-defined world seeds, fixed GPT responses, intent-parser suppression, and direct-seam observation adapters. |
| `tests/helpers/golden_replay_profiles.py` | Long-session stability expectations. |
| `tests/helpers/transcript_runner.py` | Isolated temp storage, bootstrap scenes, campaign reset, chat execution, and snapshots. |
| `tests/helpers/golden_replay_projection.py` | Acceptance authority for the 41 protected observation fields and `project_turn_observation`. |
| `game/final_emission_replay_projection.py` | Runtime read-side lineage projection. Diagnostic only; it is not protected-field authority. |
| `data/validation/scenario_spines/frontier_gate_long_session.json` | Authoritative long-session prompt/turn-id fixture. |
| `docs/testing/protected_replay_manifest.md` | Governance authority and generated protected-field table; its executable-file references are partly stale after decomposition. |
| `tests/helpers/protected_replay_observation_corpus.py` | Three curated *failure classification* rows used for recurrence-volume reports. It is not an executable replay-input corpus and contains stale old-module node IDs. |

### Maintenance and comparison tools

| File | Role |
|---|---|
| `tools/refresh_protected_replay_manifest.py` | `--check` validates or `--write` refreshes the generated 41-field manifest section. It does not regenerate transcript fixtures. |
| `tools/compare_scenario_spine_reruns.py` | Read-only comparator for two already-written scenario-spine artifact directories; useful design precedent but a separate lane. |
| `tools/projection_drift_watch.py` | Scans finalized FEM artifacts for known projection-gap shapes; not a repeated protected replay runner. |
| `tools/expand_protected_replay_observations.py` | Appends curated synthetic failure observations to recurrence history. Despite its name, it does not execute protected replay. |
| `tests/helpers/failure_dashboard_report.py` | Writes rerun scorecard, protected failure, owner drift, trend, hotspot, risk, and recurrence artifacts. |

No CLI currently regenerates golden transcript text because exact prose is opt-in and the protected
corpus is expressed as code-defined prompts, deterministic fake responses, scenario-spine JSON, and
structural expectations rather than checked-in full output transcripts.

## Field inventory

| BW dimension | Available today | Producer / storage | Gap for BW |
|---|---|---|---|
| Route | `route_kind`, `resolution_kind`, `trace.social_contract_trace.route_selected`, canonical target trace | `project_turn_observation`; route prefers social trace, then snapshot compact resolution, then payload resolution | No normalized `route_family`; BW must define whether family is identical to `route_kind` or a new read-side mapping. |
| Speaker | `selected_speaker_id`, supporting `selected_speaker_source` | Social-contract trace, then snapshot latest target, then `resolution.social.npc_id` | No projected speaker display label. Identity is ready; label drift needs a new read-only projection or should be deferred. |
| Source | Protected `final_emitted_source`; upstream and sanitizer source fields; runtime lineage event `source` and source-family classification | Final-emission metadata (FEM), sanitizer trace, and runtime lineage | No single canonical `source_system`/attribution field. Existing rerun comparator does not compare `final_emitted_source` directly. |
| Owner bucket | `opening_fallback_owner_bucket`, `sealed_fallback_owner_bucket`, `visibility_fallback_owner_bucket`, sanitizer owner fields; lineage selection/content owners | FEM projection and runtime lineage | No single per-turn owner bucket. `_fallback_owner_for_rerun_turn` returns the first non-ambiguous fallback owner, so BW must retain the path-specific map as well as any canonical summary. |
| Mutation | Protected `final_emission_mutation_lineage`; supporting `post_gate_mutation_detected`; sanitizer changed/dropped counts; runtime lineage mutation events and kinds | FEM, sanitizer trace/debug, `fem_runtime_lineage_events` | Existing rerun comparator only observes mutations indirectly through runtime-lineage frequency and response-delta fields. It needs explicit lineage, post-gate flag, replacement-kind, and count deltas. |
| Final text | `final_text`, `final_text_hash`, scaffold predicate | Snapshot `gm_text`, normalized SHA-256 helper | Exact text is deliberately not a default gate, but its hash is appropriate as an advisory BW drift dimension. |

The protected registry currently contains 39 structural fields and 2 semantic fields
(`final_text`, `scaffold_leakage`). `post_gate_mutation_detected`, `selected_speaker_source`, and
`final_text_hash` are projected supporting fields, not protected registry fields.

## Existing drift and reporting logic

- `classify_golden_drift` compares one observation to an expectation and returns `exact_drift`,
  `structural_drift`, and `semantic_drift`. Exact final text is opt-in.
- `compare_golden_replay_reruns` compares two observation lists by positional index. It reports
  speaker, route, fallback family/owner, final-text fingerprint, scaffold, response-delta, and
  runtime-lineage changes, plus frequency deltas and owner-drift classifications.
- `tests/helpers/replay_drift_taxonomy.py` maps rerun delta keys to route, speaker, fallback,
  ownership, emission, semantic, lineage, projection, or unclassified owner buckets.
- `tests/helpers/failure_classifier.py` classifies protected assertion failures and carries source,
  mutation, owner, severity, and investigation metadata.
- `tests/helpers/failure_dashboard_report.py` supplies deterministic JSON/Markdown writers. Its
  `--write-rerun-drift-scorecard` pytest option is only an opt-in writer switch: production replay
  tests do not currently call `record_rerun_drift_scorecard`, so the option has no real replay pair
  to serialize (and the marker lane currently selects nothing).
- Speaker divergence probes exist in the short structural suite and
  `tests/helpers/speaker_contract_risk.py`. Source/owner projection coverage is concentrated in
  `tests/test_golden_replay_fallback_projection.py`. Fallback/owner summaries are in
  `summarize_fallback_escalation_observations` and long-session stability scorecards.
- `tools/compare_scenario_spine_reruns.py` already demonstrates deterministic artifact comparison,
  but it reads scenario-spine artifact layouts rather than golden replay observation rows.

## Determinism assessment

### Controlled today

- Short and long golden scenarios patch `game.api.call_gpt` with fixed/iterated responses and often
  suppress intent parsers. There is no external model call in these fixtures.
- Each `run_golden_replay` patches all storage paths into a fresh pytest `tmp_path`, writes bootstrap
  scenes, performs a hard campaign reset, and then runs prompts in declared list order.
- Fallback selection in the replay-sensitive paths uses stable character-sum/hash helpers and
  explicit state/prompt seed material rather than `random`.
- `tests/test_runtime_drift_seed_audit.py` statically rejects `random`, `uuid`, `time`, and Python
  `hash()` in seven replay-sensitive speaker/final-emission/fallback modules. It passed in this pass.
- Projection output sorts protected paths, unavailable fields, raw FEM keys, and debug-lane keys.
  Frequency serialization also sorts keys.
- The six short structural scenarios passed twice in independent temp roots during discovery.

### Risks and unproven areas

- The seed audit is bounded. `game/ctir_runtime.py` and `game/noncombat_resolution.py` contain Python
  `hash()` calls outside its seven-file scope. They may affect future or some current replay routes;
  cross-process BW runs should set `PYTHONHASHSEED` and compare results before assuming safety.
- `game/api_upstream_preflight.py` and `game/utils.py` generate wall-clock timestamps. Current
  observations do not intentionally compare them, but raw payload/artifact capture must exclude or
  normalize them.
- `game/storage.py` has snapshot selection ordered by file modification time. Fresh isolated roots
  reduce leakage, but timestamp ties/filesystem resolution should be tested if snapshots enter BW.
- Module globals and `lru_cache` state are not reset by `run_golden_replay`. Repeating scenarios in
  one Python process could expose order/cache leakage that two separate pytest processes would hide.
  BW should support both in-process isolated runs and a clean-process verification mode.
- The comparator aligns only by list position and compares only the shorter length. Inserted,
  missing, or reordered cases can cascade misleading deltas. Identity alignment is required.
- Some projected fields may be marked unavailable depending on payload shape. BW must distinguish
  `None`, absent, and explicitly unavailable rather than collapsing them.
- The current marker/manifest/node-ID drift means the supposed protected corpus is not mechanically
  enumerated from one authority. An explicit BW registry is necessary before measuring trends.

## Recommended BW implementation seam

### Proposed additive files

| Proposed file | Responsibility |
|---|---|
| `tests/helpers/protected_replay_registry.py` | Explicit scenario IDs, callable runner references, protection status, and stable ordering. Initially cover the six short structural scenarios; add long/direct/spine cases only when their setup can be invoked as data rather than pytest test functions. |
| `tests/helpers/golden_replay_trend.py` | Normalize observation rows, create run envelopes, align identities, compare run N to baseline, and aggregate route/speaker/source/owner/mutation counts. Reuse `compare_golden_replay_reruns` internally or extend it compatibly. |
| `tools/run_protected_replay_trend.py` | Thin CLI: `--runs`, `--out-dir`, optional scenario filter, and clean-process mode. Test/tooling only; writes under `artifacts/golden_replay/trend_window/`. |
| `tests/test_golden_replay_trend.py` | Synthetic comparator/schema tests plus a small two-run zero-drift integration proof. |

### Artifact layout

Use immutable, deterministic files rather than the current singleton scorecard:

```text
artifacts/golden_replay/trend_window/
  manifest.json
  runs/run-000.json
  runs/run-001.json
  comparisons/run-001-vs-run-000.json
  golden_transcript_drift.json
  golden_transcript_drift.md
```

Each run row should contain `scenario_id`, `turn_id` when available, `turn_index`, and a bounded
`observation` containing only comparison fields. The aggregate should report per dimension:
`drift_count`, `affected_case_count`, stable affected identities, and field-level before/after rows.
Do not include generated timestamps in equality material; place optional capture time in envelope
metadata only.

### Primary metric definition for block 1

For each run `r > 0`, compare every aligned protected case/turn to run 0. Define Golden Transcript
Drift as the number of aligned turn observations with at least one change in the selected BW field
set. Also report dimension counts separately:

- route: `route_kind` (and trace route as evidence);
- speaker: `selected_speaker_id`;
- source: `final_emitted_source` plus explicitly selected source attribution fields;
- owner: the full path-specific owner map, not only the first fallback owner;
- mutation: normalized `final_emission_mutation_lineage`, `post_gate_mutation_detected`, sanitizer
  mutation counts, and normalized lineage mutation kinds.

Count missing/extra identities separately from field drift. Do not silently zip to the shorter run.

## Recommended first implementation block

1. Restore discoverability by marking the intended decomposed protected modules/tests and update the
   manifest/node-ID references. Keep protection status explicit; do not accidentally promote
   supporting/diagnostic long-session cases.
2. Add a registry for the six current short protected scenarios and refactor only their setup into
   callable scenario definitions shared by pytest and the BW runner. This is test-only movement, not
   production behavior.
3. Add run-envelope serialization and a two-run harness using a fresh storage root per execution.
4. Extend the existing rerun comparison compatibly with source and explicit mutation deltas plus
   identity alignment. Preserve its current report-only semantics.
5. Prove zero drift for two runs, prove one synthetic delta for each of the five requested
   dimensions, and prove missing/reordered identity handling.

Do not start with thresholds, fixture updates, runtime stamps, or long-session promotion. First make
the protected set enumerable and produce trustworthy zero/nonzero measurements.

## Commands available and discovery results

```powershell
# Documented commands (currently stale after suite decomposition)
python -m pytest tests/test_golden_replay.py -q
python -m pytest -m golden_replay -q

# Current explicit executable corpus collection
python -m pytest tests/test_golden_replay_structural_invariants.py tests/test_golden_replay_long_session.py tests/test_golden_replay_direct_seam.py tests/test_golden_replay_scenario_spine.py --collect-only -q

# Projection/manifest and deterministic-seed checks
python tools/refresh_protected_replay_manifest.py --check
python -m pytest tests/test_runtime_drift_seed_audit.py -q

# Existing comparator/report tests
python -m pytest tests/test_failure_dashboard_report.py -k rerun -q

# Scenario-spine artifact comparator
python tools/compare_scenario_spine_reruns.py --previous <dir> --current <dir> --out <report.md> --json-out <report.json>
```

Results from this discovery pass:

- Explicit current golden execution modules collected 12 tests: 6 structural, 3 long-session,
  2 direct-seam, and 1 scenario-spine.
- `-m golden_replay --collect-only` selected zero tests.
- `tests/test_golden_replay.py` ran only its redirect stub when used as a path.
- Manifest registry `--check` passed (the generated field table is current).
- Replay-sensitive seed audit passed (1 test).
- The six structural scenarios passed twice in fresh roots (6/6 each run).
- Rerun comparator/report slice passed (7 selected tests).

## Files to pass to ChatGPT for next-step judgment

Pass these first, in order:

1. `docs/BW_protected_replay_trend_window_discovery.md`
2. `tests/helpers/golden_replay.py` (especially `compare_golden_replay_reruns` and `run_golden_replay`)
3. `tests/helpers/golden_replay_projection.py`
4. `tests/test_golden_replay_structural_invariants.py`
5. `tests/helpers/golden_replay_fixtures.py`
6. `docs/testing/protected_replay_manifest.md`
7. `tests/helpers/replay_drift_taxonomy.py`
8. `tests/helpers/failure_dashboard_report.py`
9. `tests/test_runtime_drift_seed_audit.py`
10. `data/validation/scenario_spines/frontier_gate_long_session.json` only if long-session inclusion
    is being decided.

The key judgment call is corpus scope: whether BW block 1 measures only the six true short protected
scenarios or also includes supporting/diagnostic long-session and direct-seam coverage. The current
repository does not provide a reliable marker-based answer.

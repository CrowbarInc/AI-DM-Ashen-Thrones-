# BZ Protected Replay Trend Window #2 Discovery

## Executive summary

BZ can be implemented additively on the BW test/tooling lane. Reuse the six-scenario corpus from
`protected_replay_corpus()`, the deterministic runner in `tests/helpers/golden_replay_trend.py`, and
the existing normalized run envelopes. Do not modify replay projection or runtime emission.

BW already compares aligned turn identities and records aggregate drift history, but it does not
classify normalized field/value keys as new, active, retired, or unchanged. The recurrence subsystem
has stable `recurrence:v1` keys, append-only events, counts, lifecycle stages, and summaries, but BW
did not save a recurrence snapshot tied to window 1. Therefore BZ can compare replay keys directly
against committed BW run artifacts; recurrence movement needs an explicit, immutable baseline
snapshot before it can honestly claim BW-to-BZ movement.

## 1. BW baseline location

### Authority and corpus

- `docs/BW_protected_replay_trend_window_discovery.md` - design discovery.
- `docs/BW_protected_replay_trend_window_closeout.md` - closed operating procedure and corpus scope.
- `tests/helpers/protected_replay_registry.py::protected_replay_corpus()` - mechanical corpus
  authority: exactly six `PROTECTED`, `END_TO_END_PROTECTED` scenarios.
- `tests/helpers/golden_replay_trend.py::protected_replay_scenario_specs()` - prompts, seed functions,
  fixed GPT lines, and execution options for those six scenarios.
- `tests/test_golden_replay_structural_invariants.py` - original six acceptance tests.

The exact BW corpus is `directed_npc_question` (1 turn),
`lead_followup_with_dialogue_lock` (2), `sanitizer_scaffold_leakage` (1),
`thin_answer_action_outcome_final_emission` (1),
`vocative_override_after_prior_continuity` (2), and
`wrong_speaker_strict_social_emission` (1): eight aligned turn identities total.

### BW output format and artifacts

`build_run_envelope()` writes deterministic JSON with `schema_version`, `report_only`, `run_index`,
`run_id`, `observation_count`, and identity-sorted `observations`. Each observation has
`identity`, `scenario_id`, `turn_index`/`turn_id`, dimension maps for `route`, `speaker`, `source`,
`owner`, and `mutation`, plus `final_text_hash`. Field values use explicit `present`, `absent`, or
`unavailable` states. `compare_trend_runs()` aligns by `scenario_id|id:<turn_id>` or
`scenario_id|idx:<turn_index>` and emits identity alignment, per-dimension summaries, and per-turn
deltas.

Committed BW paths:

- `artifacts/golden_replay/trend_window/manifest.json`
- `artifacts/golden_replay/trend_window/runs/run-000.json`
- `artifacts/golden_replay/trend_window/runs/run-001.json`
- `artifacts/golden_replay/trend_window/comparisons/run-001-vs-run-000.json`
- `artifacts/golden_replay/trend_window/golden_transcript_drift.json`
- `artifacts/golden_replay/trend_window/golden_transcript_drift.md`
- `artifacts/golden_replay/trend_window/golden_transcript_drift_history.jsonl`
- `artifacts/golden_replay/trend_window/golden_transcript_drift_history.md`

The JSONL history is append-only and uses deterministic `window-NNN`/`sequence_id` values. It stores
counts and identity mismatch totals, not the dimension keys needed for BZ lifecycle comparison.

## 2. Current protected replay entrypoints

Reuse this command for BZ execution, changing only the output directory so BW is preserved:

```powershell
python tools/run_protected_replay_trend.py --runs 2 --out-dir artifacts/golden_replay/trend_window_2
```

The direct callable is
`tests/helpers/golden_replay_trend.py::run_protected_replay_trend_window()`, which calls
`execute_protected_replay_corpus()` in isolated storage roots. The protected acceptance lane remains
`python -m pytest -m golden_replay -q`. Registry node IDs are available from
`protected_replay_corpus_test_node_ids()`.

Relevant tests:

- `tests/test_golden_replay_trend.py::test_two_run_zero_drift_integration`
- `tests/test_golden_replay_trend.py::test_run_protected_replay_trend_window_writes_artifacts`
- synthetic route/speaker/source/owner/mutation drift and identity alignment tests in that module
- `tests/test_protected_replay_registry.py`
- `tests/test_bw_protected_replay_trend_window_closeout.py`
- `tests/test_runtime_drift_seed_audit.py`

Determinism is adequate for window comparison: fixed GPT responses, code-defined seeds, isolated
storage, stable corpus order, identity sorting, stable JSON normalization, and no timestamps in
equality material. The targeted BW trend/registry/closeout suite passed during this discovery:
44 tests. Cross-process runs should still retain the existing seed audit and avoid adding timestamps
or raw storage payloads to equality material.

## 3. Key taxonomy

BW did not serialize separate key catalogs. It persisted stable dimension maps per turn; their map
field names are the natural BZ key names, and the field states/values are their observations.

| Taxonomy | Extraction and representation | Persisted | Stability |
|---|---|---|---|
| Route | `normalize_trend_observation()`: `route_kind`, `trace_route_selected`, `resolution_kind` | BW run JSON | Stable field names and normalized values |
| Speaker | Same function: `selected_speaker_id`, `selected_speaker_source`, parity/final-observation statuses | BW run JSON; older committed run may predate added supporting fields | Stable IDs/statuses; schema evolution must treat absent distinctly |
| Source | `SOURCE_ATTRIBUTION_FIELDS`: five final/upstream/sanitizer/opening source fields | BW run JSON | Stable paths; values are projection outputs |
| Owner bucket | `OWNER_BUCKET_FIELDS`: six path-specific fallback/sanitizer owner fields | BW run JSON | Stable paths; preserve path, `null`, absent, unavailable, and ambiguous values |
| Mutation | `MUTATION_FIELDS` plus sorted `lineage_mutation_kinds` | BW run JSON | Stable normalized lists/counts/flags |
| Recurrence | `replay_bug_recurrence.py::build_recurrence_key()` creates `recurrence:v1:{owner_drift_bucket}|{category}|{field_path}|{investigate_first}` | event log and history JSON, not BW trend runs | Stable for identical four-part attribution; owner/source changes intentionally create a different key |

For BZ, define a replay key deterministically as
`<dimension>|<field>|<canonical-json-field-state-and-value>` and retain the contributing turn
identities separately. This detects value appearance/disappearance without conflating it with turn
identity. Do not use Python `hash()` or display labels.

## 4. New / active / retired key detection

There is no existing replay-key lifecycle comparator. `compare_trend_runs()` provides the needed
identity alignment, `_dimension_slices()` provides the dimension maps, and `_stable_json()` plus
`write_deterministic_json()` provide canonical ordering/serialization. Existing history helpers only
compare aggregate counts.

Smallest implementation location: add public key-catalog and comparison functions beside those
helpers in `tests/helpers/golden_replay_trend.py`; keep the CLI thin. Compare committed BW
`runs/run-000.json` (or a manifest-declared BW aggregate) with the newly generated BZ canonical run.

Recommended `BZ_replay_key_movement.json` shape:

```json
{
  "schema_version": 1,
  "report_only": true,
  "baseline": "artifacts/golden_replay/trend_window/runs/run-000.json",
  "current": "artifacts/golden_replay/trend_window_2/runs/run-000.json",
  "corpus_scenario_ids": [],
  "corpus_match": true,
  "dimensions": {
    "route": {
      "new_keys": [],
      "active_keys": [],
      "retired_keys": [],
      "unchanged_keys": []
    }
  }
}
```

Use these precise meanings: `new = current - baseline`; `retired = baseline - current`;
`active = current` (including new); `unchanged = baseline intersection current`. Sort every list and
include per-key `field`, canonical `value`, and `contributing_identities` in a separate catalog.
Validate identical corpus scenario IDs before comparison; a mismatch should produce an explicit
report-only warning, not silently redefine the population.

## 5. Recurrence movement

Existing recurrence authority is `tests/helpers/replay_bug_recurrence.py`:

- `build_recurrence_key()`, `recurrence_rows()`, and `aggregate_recurrence_history()`
- `load_recurrence_event_log()` / `append_recurrence_events()` and protected persistence filtering
- `aggregate_protected_recurrence_history_from_event_log()`
- `build_recurrence_timeline()`, `build_recurrence_trend_summary()`, and
  `build_recurrence_lifecycle()`
- current artifacts: `artifacts/golden_replay/bug_recurrence_event_log.json`,
  `bug_recurrence_history.json`, and `bug_recurrence_history.md`

BQ established the append-only recurrence event model. BW established replay-window comparison. BY
adds semantic mutation attribution reports but does not supply a BW recurrence snapshot or a
window-to-window recurrence movement classifier.

Required classifications, comparing per-key snapshots by exact `recurrence_key`:

- `newly_recurring`: absent before, current `occurrence_count >= 2` or recurring/persistent stage
- `still_recurring`: recurring/persistent in both snapshots
- `no_longer_recurring`: recurring/persistent before but not current (including dormant/retired)
- `count_increased` / `count_decreased`: current count greater/less than baseline

Owner/source movement cannot reliably use exact recurrence-key equality because owner bucket and
`investigate_first` are embedded in the key. Add a stable subject identity from `(category,
field_path)` and compare its `recurrence_owner`/owner bucket, `investigate_first` (code source), and
event `event_source` (provenance source) separately. Report ambiguity when multiple keys share the
same subject in one snapshot rather than choosing one.

Implementation should live in a small focused helper such as
`tests/helpers/protected_replay_trend_movement.py`, importing recurrence aggregation rather than
adding more policy to the already large `replay_bug_recurrence.py`. Wire it from the trend runner.

Critical limitation: no immutable recurrence snapshot was written for BW window 1. The committed
current recurrence history is cumulative and cannot prove what was true when BW ran. Before claiming
BW-to-BZ recurrence movement, BZ must either (a) recover an actual BW-time recurrence history/event
log from source control/CI, or (b) explicitly designate and preserve the current recurrence snapshot
as `baseline_capture` and label the first BZ report as baseline establishment, not historical
movement. Do not infer historical counts from the present cumulative file.

## 6. Existing metrics/reporting pattern

The dominant convention is paired deterministic JSON/Markdown under `artifacts/golden_replay`, with
JSONL only for append-only histories. BZ should use:

- `artifacts/golden_replay/trend_window_2/BZ_protected_replay_trend_window_2.json`
- `artifacts/golden_replay/trend_window_2/BZ_protected_replay_trend_window_2.md`
- `artifacts/golden_replay/trend_window_2/BZ_replay_key_movement.json`
- `artifacts/golden_replay/trend_window_2/BZ_recurrence_movement.json`

Keep the normal BW `manifest.json`, `runs/`, and `comparisons/` inside `trend_window_2`. A Markdown
recurrence movement companion is optional; the BZ window Markdown can summarize both JSON reports.
Do not append BZ into BW's directory or replace BW artifacts.

## 7. Tests to add

Add focused tests in `tests/test_golden_replay_trend.py` or a new
`tests/test_bz_protected_replay_trend_window_2.py`:

1. Manifest/corpus lock: BW baseline IDs equal `protected_replay_corpus()` and BZ output IDs.
2. Synthetic catalogs: one new key, one retired key, and an intersection present in both active and
   unchanged sets.
3. Field-state stability: absent, unavailable, present-null, and present-value remain distinct.
4. Recurrence fixtures covering newly/still/no-longer recurring and increased/decreased counts.
5. Owner, `investigate_first`, and `event_source` movement on stable `(category, field_path)` subjects,
   including ambiguous subjects.
6. Deterministic report test: reversed input order produces byte-equivalent JSON/Markdown.
7. Two-run integration remains zero drift and writes into a temporary BZ directory.

## 8. Safety constraints

The recommended implementation is read-side/test-tooling only. It does not modify the six-scenario
protected corpus, `game/final_emission_replay_projection.py`, final emission behavior, or
speaker/fallback/owner semantics. It does not promote supporting scenarios. It adds `trend_window_2`
and BZ reports while treating all BW artifacts as immutable inputs. All thresholds remain report-only.

## 9. Recommended implementation blocks

### Block BZ1: Minimal comparison/report scaffold

- **Objective:** run the exact BW corpus into `trend_window_2`, validate corpus parity, build stable
  per-dimension key catalogs, and classify new/active/retired/unchanged replay keys.
- **Files likely touched:** `tests/helpers/golden_replay_trend.py`,
  `tools/run_protected_replay_trend.py` (additive options only), new BZ test module.
- **Expected tests:** corpus lock, four lifecycle sets, field-state distinction, deterministic order.
- **Expected artifacts:** normal BW-shaped BZ run artifacts plus `BZ_replay_key_movement.json`.

### Block BZ2: Recurrence movement classification

- **Objective:** compare two explicit recurrence snapshots; classify recurrence state/count movement
  and stable-subject owner/source changes without mutating the event log.
- **Files likely touched:** new `tests/helpers/protected_replay_trend_movement.py`, BZ tests; import
  public helpers from `tests/helpers/replay_bug_recurrence.py`.
- **Expected tests:** newly/still/no-longer recurring, count up/down, owner/source change, ambiguity.
- **Expected artifacts:** `BZ_recurrence_movement.json` with baseline provenance and honesty status.

### Block BZ3: Tests and fixtures

- **Objective:** add compact synthetic envelope/recurrence fixtures and one real two-run proof.
- **Files likely touched:** `tests/test_bz_protected_replay_trend_window_2.py`; optionally a small
  fixture module if reuse justifies it.
- **Expected tests:** byte stability, reversed-input stability, corpus mismatch warning, zero-drift
  integration, no writes to BW paths.
- **Expected artifacts:** temporary test artifacts only.

### Block BZ4: Closeout/report integration

- **Objective:** render the BZ Markdown summary, record commands/provenance, and commit additive
  window-2 artifacts after the recurrence baseline decision is documented.
- **Files likely touched:** BZ renderer/helper, `docs/BZ_protected_replay_trend_window_2_closeout.md`,
  and new files under `artifacts/golden_replay/trend_window_2/`.
- **Expected tests:** closeout path/command locks modeled on
  `tests/test_bw_protected_replay_trend_window_closeout.py`.
- **Expected artifacts:** `BZ_protected_replay_trend_window_2.{json,md}` and the two movement JSONs.

## Missing evidence to supply

No additional source file is needed for implementation design. For a genuine BW-to-BZ recurrence
comparison, supply the BW-time copy of either
`artifacts/golden_replay/bug_recurrence_history.json` or
`artifacts/golden_replay/bug_recurrence_event_log.json` from the BW commit/CI artifact. If neither
exists, BZ must document baseline establishment and defer historical recurrence movement claims.

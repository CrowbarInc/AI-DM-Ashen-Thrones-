# BW Protected Replay Trend Window — Closeout

## Status

BW is **closed**. The protected replay trend workflow is implemented end-to-end, validated with zero Golden Transcript Drift across repeat runs, and guarded by report-only PASS/WARN thresholds.

This document is the operating procedure for future trend windows. It does not change runtime behavior, protected replay pass/fail gates, or corpus promotion policy.

## Protected corpus scope

The **BW protected corpus** is exactly the six short structural scenarios in `tests/test_golden_replay_structural_invariants.py`, enumerated by `tests/helpers/protected_replay_registry.py::protected_replay_corpus()`.

| Scenario ID | Turns | BW dimensions measured |
|---|---|---:|
| `directed_npc_question` | 1 | route, speaker, source, final_text |
| `lead_followup_with_dialogue_lock` | 2 | route, speaker, source, final_text |
| `sanitizer_scaffold_leakage` | 1 | mutation, final_text |
| `thin_answer_action_outcome_final_emission` | 1 | mutation, source, final_text |
| `vocative_override_after_prior_continuity` | 2 | route, speaker, final_text |
| `wrong_speaker_strict_social_emission` | 1 | mutation, source, final_text |

**Total aligned turn identities per window:** 8 (one per scenario turn).

Mechanical authority:

- Registry: `tests/helpers/protected_replay_registry.py`
- Callable scenario specs (prompts, seeds, fake GPT lines): `tests/helpers/golden_replay_trend.py::protected_replay_scenario_specs()`
- Protected observation field paths (41 fields): `tests/helpers/golden_replay_projection.py::PROTECTED_OBSERVATION_FIELDS`

The `golden_replay` pytest marker selects only these six tests. Supporting and diagnostic replay modules are intentionally excluded from the BW corpus.

## Running a BW trend window

From the repository root:

```powershell
python tools/run_protected_replay_trend.py --runs 2 --out-dir artifacts/golden_replay/trend_window --append-history
```

### CLI options

| Flag | Required | Purpose |
|---|---|---|
| `--runs N` | yes | Number of isolated replay executions (minimum 1). Each run uses a fresh storage root under `_storage/`. |
| `--out-dir PATH` | no | Artifact output directory. Default: `artifacts/golden_replay/trend_window`. |
| `--append-history` | no | Append one summary row to `golden_transcript_drift_history.jsonl` and regenerate `golden_transcript_drift_history.md`. Prior rows are never modified. |
| `--thresholds PATH` | no | Optional JSON file overriding report-only guardrail thresholds. |

Exit code is always **0** on successful artifact write, even when guardrail status is `WARN` (report-only).

### Recommended validation bundle

Run after each trend window or when touching replay-sensitive code:

```powershell
python tools/run_protected_replay_trend.py --runs 2 --out-dir artifacts/golden_replay/trend_window --append-history
python -m pytest tests/test_golden_replay_trend.py tests/test_protected_replay_registry.py -q
python -m pytest -m golden_replay -q
python tools/refresh_protected_replay_manifest.py --check
python -m pytest tests/test_runtime_drift_seed_audit.py -q
```

## Artifact layout

Default output directory: `artifacts/golden_replay/trend_window/`

```text
artifacts/golden_replay/trend_window/
  manifest.json                              # run list + corpus scenario IDs
  runs/run-000.json                          # normalized observations, run 0 (baseline)
  runs/run-001.json                          # normalized observations, run 1
  comparisons/run-001-vs-run-000.json        # identity-aligned comparison vs baseline
  golden_transcript_drift.json               # aggregate drift report + guardrail
  golden_transcript_drift.md                 # human-readable aggregate summary
  golden_transcript_drift_history.jsonl      # append-only window history (optional)
  golden_transcript_drift_history.md         # latest/previous window summary (optional)
  _storage/run-000/                          # ephemeral isolated storage (not compared)
  _storage/run-001/
```

Each run envelope contains normalized BW comparison slices only (route, speaker, source, owner, mutation, final_text_hash). Full protected observation payloads are not serialized into trend artifacts.

History rows use deterministic `window-NNN` IDs and monotonic `sequence_id` values. Timestamp fields are excluded from history equality material.

## Golden Transcript Drift

**Golden Transcript Drift** is the primary BW metric: the count of aligned turn identities where at least one BW dimension differs between run 0 (baseline) and run N.

For each aligned identity `(scenario_id, turn_id or turn_index)`:

1. Observations are normalized into six dimension slices.
2. Run N is compared to run 0 field-by-field within each slice.
3. If any slice differs, that identity counts as one drift event.

Dimension slices:

| Dimension | Fields compared |
|---|---|
| `route` | `route_kind`, `trace.social_contract_trace.route_selected`, `resolution_kind` |
| `speaker` | `selected_speaker_id` |
| `source` | `final_emitted_source`, upstream/sanitizer/opening source attribution fields |
| `owner` | opening/sealed/visibility/sanitizer owner-bucket fields |
| `mutation` | `final_emission_mutation_lineage`, `post_gate_mutation_detected`, sanitizer lineage counts, runtime lineage mutation kinds |
| `final_text` | `final_text_hash` (hash fingerprint, not exact prose) |

**Separate from field drift:**

- `missing_in_current` — identities present in baseline but absent in run N
- `missing_in_baseline` — identities present in run N but absent in baseline

Missing/extra identities are counted separately and do not inflate `golden_transcript_drift_count` unless an aligned identity actually differs.

## Guardrails (PASS / WARN)

Guardrails are **report-only**. They never fail CI or block protected replay acceptance.

Default thresholds require **zero** for all enforced fields:

- `golden_transcript_drift_count`
- `route_drift_count`, `speaker_drift_count`, `source_drift_count`, `owner_drift_count`, `mutation_drift_count`
- `missing_identity_count`, `extra_identity_count`

| Status | Meaning |
|---|---|
| `PASS` | All enforced thresholds satisfied. |
| `WARN` | One or more enforced thresholds exceeded. CLI still exits 0; stderr notes the WARN. |

**Advisory-only:** `final_text_hash_drift_count` is tracked in history and dimension totals but does **not** trigger WARN unless explicitly configured via `--thresholds`. Exact prose identity is not a default protected gate.

Guardrail evaluation is attached to `golden_transcript_drift.json` under the `guardrail` key and copied into history rows when `--append-history` is used.

## Append-only history

Use `--append-history` to record a window summary without modifying prior rows:

1. Reads existing `golden_transcript_drift_history.jsonl` (if present).
2. Assigns the next `sequence_id` and `window-NNN` ID.
3. Appends one JSON line with flat metrics and guardrail status.
4. Regenerates `golden_transcript_drift_history.md` with latest/previous windows and delta.

History supports window-over-window trend direction (`stable`, `improved`, `worsened`) based on drift count and identity mismatch severity.

**Do not hand-edit** history JSONL rows. Re-run the CLI with `--append-history` to add windows.

## Intentionally not gated yet

The following remain outside BW acceptance blocking:

- **Hard drift thresholds in CI** — guardrails are advisory; protected replay pass/fail is unchanged.
- **Exact final-text prose comparison** — only `final_text_hash` is measured; hash drift is advisory by default.
- **Long-session promotion** — 25-turn Frontier Gate scenarios stay `SUPPORTING` in the registry.
- **Direct-seam promotion** — alias/opening fallback direct-seam scenarios stay `SUPPORTING`.
- **Scenario-spine smoke** — three-branch smoke replay stays `SUPPORTING`.
- **Runtime instrumentation changes** — BW is test/tooling only; no production behavior changes.
- **Clean-process verification mode** — in-process isolated runs are the default harness; separate-process verification is deferred.
- **Threshold-based CI failure** — WARN never changes exit code.

Future hard gates require explicit manifest review and repeated evidence across history windows.

## Supporting vs BW-protected scenarios

The full registry (`protected_replay_registry()`) lists 12 scenarios. Only six are `PROTECTED` and included in BW trend windows.

| Scenario group | Module | Registry status | In BW corpus? |
|---|---|---|---|
| Six short structural scenarios | `tests/test_golden_replay_structural_invariants.py` | `PROTECTED` | **Yes** |
| Frontier Gate 25-turn structural stability | `tests/test_golden_replay_long_session.py` | `SUPPORTING` | No |
| Frontier Gate resume persistence | `tests/test_golden_replay_long_session.py` | `SUPPORTING` | No |
| Frontier Gate direct-intrusion diagnostic | `tests/test_golden_replay_long_session.py` | `SUPPORTING` | No |
| Declared alias dialogue plan (direct seam) | `tests/test_golden_replay_direct_seam.py` | `SUPPORTING` | No |
| Opening fallback path (direct seam) | `tests/test_golden_replay_direct_seam.py` | `SUPPORTING` | No |
| Scenario-spine three-branch smoke | `tests/test_golden_replay_scenario_spine.py` | `SUPPORTING` | No |

Long-session, direct-seam, and scenario-spine cases remain valuable **supporting signal**. They may be exercised via their module-specific pytest paths or advisory tooling (`tools/compare_scenario_spine_reruns.py`, long-session stability scorecards) but are not repeat-run trend corpus members until explicitly promoted through manifest review.

## Closeout validation record

Final closeout validation (BW5):

```powershell
python tools/run_protected_replay_trend.py --runs 2 --out-dir artifacts/golden_replay/trend_window --append-history
python -m pytest tests/test_golden_replay_trend.py tests/test_protected_replay_registry.py -q
python -m pytest -m golden_replay -q
python tools/refresh_protected_replay_manifest.py --check
python -m pytest tests/test_runtime_drift_seed_audit.py -q
python -m pytest tests/test_bw_protected_replay_trend_window_closeout.py -q
```

See `tests/test_bw_protected_replay_trend_window_closeout.py` for doc/command artifact filename regression locks.

## Related documents

- Discovery and design rationale: [`docs/BW_protected_replay_trend_window_discovery.md`](BW_protected_replay_trend_window_discovery.md)
- Protected replay governance: [`docs/testing/protected_replay_manifest.md`](testing/protected_replay_manifest.md)

# Failure Dashboard Precision Pass - 2026-05-11

## Ambiguity Gaps Reduced

- Final-emission repair rows now carry compact replay-side evidence for `emission_sublayer`, `repair_kind`, and `mutation_source`.
- Known FEM/stage-diff signals distinguish response-type repair, fallback behavior repair, strict-social replacement, speaker contract enforcement, interaction continuity repair, sanitizer repair, opening fallback recovery, terminal fallback substitution, and unknown post-gate mutation.
- Golden replay observation rows now project sanitizer-facing evidence when present: mode, event count, changed count, rewrite-used flag, and leak predicate terms.
- Missing replay fields now carry deterministic `missing_source_kind` where raw/normalized projection evidence supports it:
  - `projection_missing_raw_present`
  - `runtime_missing_raw_absent`
  - `normalized_view_missing_raw_present`
  - `unknown_missing_source`
- Dashboard markdown now includes a compact `Evidence` column instead of adding many sparse columns.

## Metadata Consumed

- Raw FEM from `read_final_emission_meta_from_turn_payload`.
- Normalized FEM from `normalize_final_emission_meta_for_observability`.
- Emission debug lane keys from `read_emission_debug_lane_from_turn_payload`.
- Existing stage-diff telemetry snapshots and repair flags.
- Existing sanitizer debug/trace dictionaries when projected in payload/debug metadata.
- Existing route/social contract trace and unavailable-field projection.

## Tests Added

- Response-type repair sublayer attribution.
- Strict-social replacement attribution.
- Opening fallback attribution.
- Unknown post-gate mutation attribution.
- Sanitizer leakage with sanitizer metadata present.
- Sanitizer leakage with sanitizer metadata absent.
- Projection missing raw-present.
- Runtime missing raw-absent.
- Normalized missing raw-present.
- Dashboard `Evidence` column rendering.

## Commands Run

```powershell
python -m pytest tests/test_failure_classifier.py -q
python -m pytest tests/test_golden_replay.py -q
python -m pytest -m golden_replay -q
python -m pytest -m golden_replay -q --write-failure-dashboard
```

Local shell note: `python` is not on PATH in this workspace, so the bundled Codex runtime Python was used for the equivalent commands.

## Remaining Ambiguity After Pass C

- Late final-emission sublayer attribution is still only as precise as existing FEM/stage-diff fields.
- Sanitizer run summaries are visible only when existing sanitizer context/debug metadata reaches replay payloads.
- Raw-present vs normalized-missing distinctions are deterministic, but still limited to replay-visible raw payload/debug/FEM surfaces.
- Unknown post-gate mutation remains explicitly labeled as `emission.post_gate_mutation_unknown` when no existing sublayer signal identifies the repair source.
- The dashboard remains read-only and consumes existing signals only; it does not add runtime telemetry or evaluator policy.

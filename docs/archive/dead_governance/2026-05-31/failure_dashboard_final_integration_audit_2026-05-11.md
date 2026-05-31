# Failure Dashboard Final Integration Audit - 2026-05-11

## Summary

Cycle Track B is complete enough to move on. The Failure Classification Dashboard is replay-side, deterministic, contract-locked, opt-in for artifact generation, and validated against controlled known-bad probes. Normal golden replay remains green.

## Architecture Audit

### Classifier

- Implementation: `tests/helpers/failure_classifier.py`
- Role: converts replay drift rows plus replay-visible observation fields into structured failure classification rows.
- Properties: deterministic, table/rule-driven, read-only, replay-side.
- Runtime boundary: no imports from `tests.helpers.failure_classifier` or dashboard modules exist in `game/`.

Complete:

- Canonical categories and owner assignment exist.
- Severity mapping exists.
- Investigation target routing exists.
- Precision evidence fields exist: `emission_sublayer`, `repair_kind`, `mutation_source`, `missing_source_kind`, sanitizer evidence.
- Row validation exists via `validate_failure_classification_row(...)`.

Intentionally out of scope:

- Runtime repair.
- Live telemetry.
- Evaluator policy.
- AI/fuzzy classification.

### Contract Registry

- Implementation: `tests/failure_classification_contract.py`
- Tests: `tests/test_failure_classification_contract.py`

Complete:

- Allowed categories, owners, severities, replay tags, source-family tags, required fields, optional evidence fields, missing-source kinds, emission sublayers, and major investigation targets are centralized.
- Dashboard rendering validates rows before markdown emission.
- Unknown replay tags fail unless prefixed with `experimental:`.

### Dashboard Report Generation

- Implementation: `tests/helpers/failure_dashboard_report.py`
- Artifact: `audits/failure_dashboard_latest.md`

Complete:

- Markdown report includes timestamp, command, scenario, turn, category, severity, owners, investigation target, evidence, replay tags, field path, expected/actual, unavailable fields, final source, fallback, post-gate mutation, and mutation flags.
- Empty passing state renders `No replay failures classified.`
- Artifact writing is opt-in via `--write-failure-dashboard` or `ASHEN_WRITE_FAILURE_DASHBOARD=1`.

### Golden Replay Integration

- Implementation: `tests/helpers/golden_replay.py`

Complete:

- Golden replay drift classification attaches failure classification rows additively.
- Replay assertion behavior is unchanged.
- Debug/report surfaces include classification summaries.
- Opt-in recording only happens for real replay observations with scenario id and turn index.

### Controlled Failure Probes

- Implementation: `tests/test_failure_dashboard_controlled_failures.py`
- Marker: `failure_dashboard_probe`
- Artifact: `audits/failure_dashboard_probe_sample.md`

Complete:

- Known-bad replay-shaped rows validate wrong speaker, forced fallback, sanitizer leakage, response-type repair, missing route metadata raw absent, missing route metadata raw present, semantic mutation, and unknown post-gate mutation.
- Probes are opt-in by direct file, `-m failure_dashboard_probe`, or `ASHEN_RUN_FAILURE_DASHBOARD_PROBES=1`.
- Normal full-suite collection skips the probe tests unless explicitly requested.

### Documentation

Complete:

- `tests/README_TESTS.md` documents dashboard purpose, golden replay relationship, artifact generation, owner meanings, non-goals, controlled probes, and contract update procedure.
- Audit trail exists for discovery, operationalization, precision, probe harness, and contract lock.

## File/Layer Ownership Check

Responsibilities remain test/replay-side:

- Classification: `tests/helpers/failure_classifier.py`
- Owner assignment: `tests/helpers/failure_classifier.py`
- Dashboard rendering: `tests/helpers/failure_dashboard_report.py`
- Controlled failure probes: `tests/test_failure_dashboard_controlled_failures.py`
- Contract validation: `tests/failure_classification_contract.py` and `tests/helpers/failure_classifier.py`

Runtime coupling check:

- Searched `game/` for dashboard/classifier/test-contract imports and found no matches.
- The replay helper imports runtime read APIs such as FEM readers and sanitizer predicates, which is appropriate for test-side observation projection.
- No runtime code imports the classifier or dashboard.

No refactor is necessary.

## Contract/Docs Alignment

Aligned:

- Categories are listed in `tests/failure_classification_contract.py` and documented in `audits/proposed_failure_classification_schema.md`.
- Owners are listed in the contract and covered by `audits/failure_owner_matrix.md` / schema docs.
- Severities are listed in the contract and documented in schema docs.
- Controlled probes are documented in `tests/README_TESTS.md`.
- Dashboard generation commands are documented in `tests/README_TESTS.md`.
- Contract update procedure is documented in `tests/README_TESTS.md`.
- Contract tests verify audit/schema doc coverage without brittle markdown parsing.

## Verification

Commands run with the bundled Codex runtime Python because `python` is not on PATH in this shell:

```powershell
python -m pytest tests/test_failure_classifier.py -q
```

Result: 24 passed.

```powershell
python -m pytest tests/test_failure_classification_contract.py -q
```

Result: 11 passed.

```powershell
python -m pytest tests/test_failure_dashboard_controlled_failures.py -q
```

Result: 9 passed.

```powershell
python -m pytest tests/test_golden_replay.py -q
```

Result: 12 passed.

```powershell
python -m pytest -m golden_replay -q
```

Result: 12 passed.

```powershell
python -m pytest -m failure_dashboard_probe -q
```

Result: 9 passed.

```powershell
python -m pytest -m golden_replay -q --write-failure-dashboard
```

Result: 12 passed; generated latest dashboard with no classified failures.

```powershell
python -m pytest -m failure_dashboard_probe -q --write-failure-dashboard
```

Result: 9 passed; generated latest dashboard with known-bad probe rows.

Final artifact state was restored by rerunning golden replay with `--write-failure-dashboard`, so `audits/failure_dashboard_latest.md` now reflects passing replay.

## Artifact Check

- `audits/failure_dashboard_latest.md`: regenerated from passing golden replay and says `No replay failures classified.`
- `audits/failure_dashboard_probe_sample.md`: regenerated from controlled known-bad rows and contains classified probe failures.

## Remaining Ambiguity Gaps

- Late final-emission sublayer attribution is only as granular as existing FEM/stage-diff metadata.
- Sanitizer metadata is projected when present, but sanitizer run summaries are not guaranteed on every runtime path.
- Projection-vs-runtime-missing distinction is deterministic only when raw/normalized replay-visible surfaces provide enough evidence.
- Evaluator alignment remains advisory; evaluator rows are not runtime policy.

## Completion Answer

Cycle Track B is complete with caveats. The caveats are documented observability limits, not blockers for dashboard usefulness or architecture safety. The track is ready to close and hand off to the next planned cycle.

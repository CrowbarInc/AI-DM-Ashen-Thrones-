# Protected Replay Failure Reporting Bridge

## Change Summary

Block K3A connects failures from the declared protected replay assertions to the existing replay classification machinery and a new canonical failure report. It is reporting-only: replay inputs, expectation dictionaries, classification taxonomy, test pass/fail conditions, production code, and CI workflow wiring are unchanged.

Implemented surfaces:

| Area | Path | Change |
|---|---|---|
| Protected assertion bridge | `tests/helpers/golden_replay.py` | Added `assert_protected_golden_turn_observation(...)`, which delegates to the existing assertion behavior and records diagnostics only if a protected assertion is about to raise. |
| Existing classifier reuse | `tests/helpers/failure_dashboard_report.py` | Added translation from one failed protected invariant into the existing `build_failure_dashboard_rows(...)` / `classify_replay_failure(...)` path. |
| Canonical failure artifact | `tests/helpers/failure_dashboard_report.py` | Added deterministic rendering/writing for `artifacts/golden_replay/replay_failure_report.md`, emitted only when protected failure rows exist. |
| Session write hook | `tests/conftest.py` | Added failed-session, failure-row-driven report writing at pytest session finish; the existing opt-in dashboard path remains separate and unchanged. |
| Protected instrumentation and synthetic test | `tests/test_golden_replay.py` | Routed K1-protected helper assertions through the new wrapper without changing expectations; added a caught synthetic mismatch test for bridge/report validation. |

## Implemented Bridge

`assert_protected_golden_turn_observation(...)` is the protected reporting entry point. It invokes the same underlying expectation checks as `assert_golden_turn_observation(...)`, supplying only the protected scenario identifier needed for a report row.

When an expectation is about to fail:

1. The helper retains the existing failure message construction and ultimately raises the same `AssertionError`.
2. A best-effort diagnostic call captures scenario id, current pytest node id, failed invariant, field path, expected value, actual value, and drift bucket.
3. Reporting exceptions are swallowed at that boundary so diagnostics cannot replace or mask the acceptance failure.

Only the K1-declared protected scenario calls were instrumented. Supporting smoke assertions and existing deliberate assertion-failure tests continue using `assert_golden_turn_observation(...)`, preventing expected failures from polluting a canonical report.

Instrumented protected scenario ids:

| Category | Scenario Id |
|---|---|
| End-to-end protected | `directed_npc_question` |
| End-to-end protected | `vocative_override_after_prior_continuity` |
| End-to-end protected | `wrong_speaker_strict_social_emission` |
| End-to-end protected | `thin_answer_action_outcome_final_emission` |
| End-to-end protected | `sanitizer_scaffold_leakage` |
| End-to-end protected | `lead_followup_with_dialogue_lock` |
| Direct-seam protected | `declared_alias_dialogue_plan` |
| Direct-seam protected | `opening_fallback_path` |

## Data Flow

```text
protected scenario expectation
  -> assert_protected_golden_turn_observation(...)
  -> existing assertion detects the same invariant failure
  -> record_protected_replay_assertion_failure(...)
  -> build_failure_dashboard_rows(...)
  -> classify_replay_failure(...)
  -> recorded protected failure rows + runtime lineage events
  -> pytest_sessionfinish(...)
       only when the pytest session has failed
  -> write_protected_replay_failure_report_if_present(...)
  -> artifacts/golden_replay/replay_failure_report.md
```

The translated record uses the existing classifier for:

- category
- severity
- primary owner
- secondary owner
- `investigate_first`

No new category, owner, severity, or routing policy was introduced.

Captured diagnostic evidence includes:

| Evidence | Source |
|---|---|
| Scenario id | Protected assertion wrapper argument |
| Test node id | Current pytest test identity at failure time |
| Failed invariant, field path, expected, actual | Existing assertion failure inputs |
| Drift type | Existing structural/semantic drift bucket mapping and replay tag |
| Fallback information | Existing observed replay turn projection |
| Sanitizer information | Existing observed replay turn projection |
| Runtime lineage events | Existing observed replay turn projection |

## Generated Artifact Structure

Canonical path:

```text
artifacts/golden_replay/replay_failure_report.md
```

Generation rule: automatic session output runs only for a failed pytest session, and the writer returns without creating a file when no protected assertion failure rows have been recorded.

The deterministic Markdown report contains:

| Section | Contents |
|---|---|
| Run Summary | Failure status, command, generated time, artifact location, classified failure count |
| Failure Table | Scenario, pytest node, turn, invariant, drift type, expected/actual, category, severity, owners, investigation target |
| Classification Summary | Category and primary-owner counts |
| Fallback Summary | Final source, fallback family/timeframe, opening/sealed ownership, sanitizer empty-fallback owner |
| Sanitizer Summary | Sanitizer mode, changed/dropped counts, empty fallback, legacy rewrite, strict-social owner |
| Runtime Lineage Summary | Existing event-frequency summary for gate, fallback, repair, mutation, and recurrence evidence |
| Reproduce Locally | Scenario-node command(s) and marker-wide protected replay command |

## Existing Dashboard Preservation

The prior dashboard remains at:

```text
audits/failure_dashboard_latest.md
```

Its existing opt-in controls remain unchanged:

```bash
python -m pytest -m golden_replay -q --write-failure-dashboard
```

The new canonical report uses separate recorded rows and a separate path. It does not replace, rename, or alter the write conditions for the existing dashboard.

## Validation Performed

Synthetic reporting-path validation was added within `tests/test_golden_replay.py`. It:

- triggers a caught protected-wrapper mismatch without breaking a real protected scenario;
- confirms the original assertion failure message remains present;
- confirms existing classifier output for category, severity, owner, and investigation target;
- renders the canonical report into pytest temporary storage;
- confirms drift, sanitizer, runtime-lineage, and reproduction sections are visible;
- clears captured rows after verification so a successful run emits no canonical report.

Validation commands and results are recorded after the final marker-lane execution for this block.

Focused reporting and replay-helper validation:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_failure_classifier.py tests\test_golden_replay.py -q --tb=short --basetemp=codex_pytest_tmp_cycle_k_k3a_focused_final2
```

Result: **PASS**.

Protected replay acceptance-lane validation:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest -m golden_replay -q --tb=short --basetemp=codex_pytest_tmp_cycle_k_k3a_marker_final2
```

Result: **PASS** (`33` marker-selected tests passed; no collection failures).

Success-path inertness check:

- `artifacts/golden_replay/replay_failure_report.md` was not created during passing validation.
- `audits/failure_dashboard_latest.md` was not modified.
- `git diff --check` reported no whitespace errors.

## Remaining Ergonomics Work

- K3B: update workflow artifact upload behavior so `artifacts/golden_replay/replay_failure_report.md` is retained on protected replay failures.
- Raw `assert` statements adjacent to a protected helper assertion remain console-only diagnostics; this block intentionally instruments the existing protected replay assertion path rather than rewriting scenario assertions.
- K4: define drift threshold policy using the now-structured diagnostics without changing replay acceptance unintentionally.
- K5: decide longitudinal replay reporting and trend retention.

## Acceptance Criteria

| Criterion | Result |
|---|---|
| Replay behavior unchanged | Met: implementation is confined to test reporting and documentation. |
| Acceptance semantics unchanged | Met: existing assertions still determine failure; reporting is best-effort and cannot mask an assertion. |
| Classification bridge implemented | Met: protected failed invariants flow through existing classification functions. |
| Structured failure record generated | Met: report rows include invariant, evidence, classification, owner, and reproduction metadata. |
| Canonical report renderer implemented | Met: failure-only report writer targets `artifacts/golden_replay/replay_failure_report.md`. |
| Existing dashboard preserved | Met: existing dashboard path and opt-in behavior are unchanged. |
| Protected replay suite still passes | Met: `python -m pytest -m golden_replay -q` passed locally. |

# CR — Protected Replay Recurrence Separation Closeout

**Closeout date:** 2026-06-28  
**Scope:** Architecture documentation and validation closeout only. No recurrence calculation, routing, artifact regeneration, or compatibility-output removal.

**Status: Complete — close CR**

---

## Executive Summary

Protected Replay Recurrence Separation is complete. The recurrence system now has explicit persistence lanes for protected replay health evidence, session diagnostics, and synthetic/test artifact diagnostics. Legacy combined diagnostic surfaces remain available for compatibility and audit context, but they no longer participate in canonical protected replay health reporting.

The canonical recurrence writer supports independent emission phases so maintenance commands can regenerate only the intended recurrence artifacts. Tests validate every supported emission mode and prove the canonical recurrence payloads are byte-identical regardless of whether governance, audit, or compatibility outputs are enabled.

---

## Final Architecture

### Protected Replay Pipeline

**Purpose:** Canonical health metric pipeline for commit-worthy protected replay recurrence.

**Ownership:**

- `tests/helpers/replay_bug_recurrence_events.py` owns recurrence identity, commit-worthiness, event-source taxonomy, lane classification, and scoped recurrence-rate calculations.
- `tests/helpers/failure_dashboard_recurrence.py` owns recurrence artifact writing and report rendering.
- `tests/helpers/failure_dashboard_paths.py` owns canonical path derivation only.
- `tools/migrate_bug_recurrence_event_log.py` and `tools/regenerate_bug_recurrence_history.py` are maintenance entry points.

**Write flow:**

```text
protected replay failure rows
    -> commit-worthiness classification
    -> protected event log
    -> protected recurrence history JSON/markdown
    -> protected replay recurrence rate (health_metric: true)
```

Canonical protected artifacts:

- `artifacts/golden_replay/bug_recurrence_event_log.json`
- `artifacts/golden_replay/bug_recurrence_history.json`
- `artifacts/golden_replay/bug_recurrence_history.md`

### Session Diagnostic Pipeline

**Purpose:** Diagnostic-only persistence for session/default-source recurrence rows.

**Ownership:** Same recurrence core and dashboard writer, with session classification determined by event source.

**Write flow:**

```text
session/default-source recurrence rows
    -> session diagnostic lane
    -> explicit session diagnostic event log
    -> session diagnostic recurrence rate (health_metric: false)
```

Canonical diagnostic artifact:

- `artifacts/golden_replay/bug_recurrence_session_event_log.json`

### Synthetic/Test Artifact Pipeline

**Purpose:** Diagnostic-only persistence for rejected protected-looking rows, synthetic drift keys, null-scenario rows, ephemeral pytest artifacts, and other non-commit-worthy test artifact events.

**Ownership:** Same recurrence core and dashboard writer, with routing determined by commit-worthiness rejection reason.

**Write flow:**

```text
non-commit-worthy protected-looking/test artifact rows
    -> synthetic/test artifact diagnostic lane
    -> explicit synthetic/test artifact event log
    -> synthetic/test artifact recurrence rate (health_metric: false)
```

Canonical diagnostic artifact:

- `artifacts/golden_replay/bug_recurrence_synthetic_test_artifact_event_log.json`

### Compatibility Pipeline

**Purpose:** Preserve historical public outputs and migration evidence without affecting canonical protected replay reporting.

**Ownership:** Migration and artifact writer compatibility phase.

**Write flow:**

```text
session diagnostic log + synthetic/test artifact log
    -> combined diagnostic compatibility log

pre-separation unified source log
    -> byte-for-byte legacy archive
```

Compatibility artifacts:

- `artifacts/golden_replay/bug_recurrence_session_diagnostic_event_log.json`
- `artifacts/golden_replay/bug_recurrence_event_log.legacy.json`

Compatibility artifacts are retained for existing consumers, audit review, and migration evidence. They are not canonical health-metric inputs.

---

## Canonical Artifact Set

| Category | Artifact | Role |
|---|---|---|
| Protected | `bug_recurrence_event_log.json` | Commit-worthy protected replay recurrence events |
| Protected | `bug_recurrence_history.json` | Canonical protected recurrence analytics payload |
| Protected | `bug_recurrence_history.md` | Canonical protected recurrence markdown report |
| Diagnostic | `bug_recurrence_session_event_log.json` | Explicit session diagnostic recurrence events |
| Diagnostic | `bug_recurrence_synthetic_test_artifact_event_log.json` | Explicit synthetic/test artifact diagnostic recurrence events |
| Compatibility | `bug_recurrence_session_diagnostic_event_log.json` | Legacy combined diagnostic output, compatibility-only |
| Compatibility | `bug_recurrence_event_log.legacy.json` | Byte-for-byte archive of the pre-separation unified source log |

---

## Emission Modes

| Mode | Emits | Intended use |
|---|---|---|
| Default | Recurrence artifacts, compatibility artifacts, governance reports, audit report | Full migration/audit runs that should preserve legacy behavior |
| `--recurrence-only` | Protected recurrence artifacts plus explicit session and synthetic/test artifact logs | Narrow maintenance regeneration for canonical recurrence outputs |
| `--no-governance-docs` | Recurrence artifacts, compatibility artifacts, audit report | Migration/audit runs that must not refresh governance markdown or trajectory reports |
| `--no-audit-docs` | Recurrence artifacts, compatibility artifacts, governance reports | Artifact regeneration runs that should not rewrite migration audit markdown |
| `--no-compatibility-artifacts` | Recurrence artifacts, governance reports, audit report | Validation of compatibility independence; not a compatibility retirement |

All supported modes preserve recurrence calculations and routing. Tests prove the canonical recurrence outputs are byte-identical across supported emission modes when generated from the same source and timestamp.

---

## Health Metric Guidance

| Population | Metric role | Guidance |
|---|---|---|
| Protected Replay | Health metric | Canonical protected recurrence health source. Only this population may be treated as `health_metric: true`. |
| Session Diagnostic | Diagnostic only | Useful for session/runtime noise analysis. Must not be used as protected replay health. |
| Synthetic/Test Artifact | Diagnostic only | Useful for test artifact hygiene and rejected-row analysis. Must not be used as protected replay health. |
| Legacy Unified | Compatibility/audit only | May combine protected and diagnostic populations for comparison. Must not be used as canonical health. |

Legacy fields such as `legacy_unified` and `regression_recurrence_rate_comparison.overall` remain available for compatibility and distortion audits. New consumers should prefer explicitly scoped protected/session/synthetic fields.

---

## Success Criteria

| Criterion | Status | Evidence |
|---|---|---|
| Protected replay recurrence no longer depends on diagnostic events | Met | Protected history is generated from protected replay log only; diagnostic keys are disjoint from protected history. |
| Session diagnostics no longer contaminate protected health metrics | Met | Session diagnostic recurrence has `health_metric: false`; protected rate is calculated from protected log only. |
| Synthetic/test artifacts no longer contaminate protected health metrics | Met | Synthetic/test artifact recurrence has `health_metric: false`; protected rate is calculated from protected log only. |
| Compatibility surfaces remain available without affecting canonical reporting | Met | Combined diagnostic log and legacy archive remain compatibility outputs and can be disabled without changing recurrence payloads. |
| Canonical recurrence generation is deterministic | Met | Migration and regeneration share the canonical writer; fixed-timestamp tests compare byte-identical recurrence outputs. |
| Tests validate all supported emission modes | Met | Mode-matrix tests cover default, recurrence-only, no-governance, no-audit, and no-compatibility modes. |

---

## Validation Summary

Validated by the narrow recurrence suite:

```text
tests/test_migrate_bug_recurrence_event_log.py
tests/test_failure_dashboard_recurrence.py
tests/test_failure_dashboard_paths.py
tests/test_replay_bug_class_recurrence.py
```

The suite covers lane classification, explicit diagnostic log separation, protected-history isolation, path derivation, compatibility flags, and emission-mode independence.

---

## Intentional Technical Debt

The following items are intentionally outside this CR and do not block closeout:

1. **Compatibility artifact retirement:** `bug_recurrence_session_diagnostic_event_log.json` and the legacy archive remain public compatibility/evidence surfaces. Any retirement requires a separate deprecation plan.
2. **Downstream consumer migration:** Existing docs, manifests, and compatibility tests still reference legacy diagnostic and unified metric labels. They should be migrated opportunistically to explicitly scoped fields where appropriate.
3. **Documentation cleanup:** Historical audits and discovery documents may describe the pre-separation combined diagnostic lane. Those documents should remain historical evidence unless a future documentation pass adds post-closeout annotations.
4. **Legacy metric naming:** `legacy_unified` and `regression_recurrence_rate_comparison.overall` remain intentionally available for audit comparison. New health consumers should not use them.

No remaining technical debt requires recurrence calculation, routing, or artifact writer changes inside this CR.

---

## Scorecard Closeout Summary

Protected replay recurrence is now isolated from diagnostic recurrence populations. Session diagnostic and synthetic/test artifact events persist in explicit diagnostic lanes, compatibility outputs remain available, and maintenance commands can regenerate canonical recurrence artifacts without governance/audit side effects. The protected replay recurrence rate is the only health metric; diagnostic and legacy unified rates are compatibility/audit context only.

**Closeout recommendation:** Close CR.

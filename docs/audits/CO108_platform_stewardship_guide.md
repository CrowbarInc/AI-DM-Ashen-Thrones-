# CO108 — Recurrence Platform Stewardship Guide

**Date:** 2026-06-28  
**Scope:** Operational documentation only. Describes long-term ownership of the closed recurrence engineering program.

**Authority:** [`CO108_recurrence_program_closeout.md`](CO108_recurrence_program_closeout.md) (engineering closed); [`docs/runbooks/protected_replay_observation_collection.md`](../runbooks/protected_replay_observation_collection.md) (CO100 workflow).

---

## Stewardship model

The recurrence subsystem is a **completed platform capability**. Platform stewards (operators and maintainers) own **routine execution** of the existing workflow. They do **not** own recurrence architecture, taxonomy extension, or graduation formula design.

| Role | Responsibility |
|---|---|
| **Platform steward** | Execute protected replay monitoring, maintain artifacts, review graduation docs, propagate retirements when registries exist |
| **Incident responder** | Triage live protected replay failures, coordinate fixes, create retirement registry entries when fixes land |
| **Graduation reviewer** | Read regenerated BQC4/BQC5 on cadence; document when `graduation_confidence_ready` transitions |
| **Recurrence engineer** | **Inactive by default** — re-engaged only when [`CO108_reentry_criteria.md`](CO108_reentry_criteria.md) are met |

---

## Recurring operational responsibilities

| Task | Cadence | Command / action | Type |
|---|---|---|---|
| Protected replay lane | Weekly or pre-release | `python -m pytest -m golden_replay -q` | **Operational** |
| Failure report triage | On red runs | Read `artifacts/golden_replay/replay_failure_report.md` | **Operational** |
| Commit golden-replay artifacts | After meaningful observation changes | `git add artifacts/golden_replay/` + graduation docs | **Operational** |
| Trajectory snapshot | Monthly | `python tools/capture_recurrence_trajectory_activation.py --generated-at <ISO8601>` | **Operational** |
| Graduation quick review | Monthly | Read BQC4 recommendation + calibration score | **Operational** |
| Full convergence review | Quarterly | BQ16 + BQC4 + BQC5 + CO106 inventory cross-check | **Operational** |
| Propagation idempotency check | After any propagation | `python tools/propagate_outcome_retirements.py --check` | **Operational** |
| Backfill sync | When CI report not committed in-session | `python tools/backfill_bug_recurrence_history.py` | **Operational** |
| Post-incident review | After live failure or propagation | Event log + history + `--check` | **Operational** |

**Estimated steady-state effort:** ~15 minutes/month when the golden replay suite is green; ~1–2 hours engineering plus ~15 minutes operational when a genuine live failure requires fix and retirement.

---

## Artifact maintenance

### Commit-worthy paths (protected lane)

| Artifact | Path | Steward action |
|---|---|---|
| Protected event log | `artifacts/golden_replay/bug_recurrence_event_log.json` | Commit after new observations; never hand-edit |
| Recurrence history | `artifacts/golden_replay/bug_recurrence_history.{json,md}` | Regenerates automatically; commit with event log |
| Trajectory history | `artifacts/golden_replay/recurrence_trajectory_history.json` | Commit after trajectory capture |
| Failure report | `artifacts/golden_replay/replay_failure_report.md` | Commit on live failures; backfill input |
| Owner drift artifacts | `artifacts/golden_replay/owner_drift_*` | Commit with failure cascade |
| Graduation audits | `docs/audits/BQ16_*.md`, `BQC4_*.md`, `BQC5_*.md` | Commit after regeneration; do not hand-edit metrics sections |

### Policy violations (do not perform)

- Manual edits to `bug_recurrence_history.json` or graduation metric sections in BQ16/BQC4/BQC5
- Synthetic or backfilled outcomes without corresponding protected events
- Corpus expansion solely to inflate calibration metrics (CO103/CO106 — volume without outcome signal)

---

## Retirement propagation responsibilities

Propagation is **manual trigger, automated cascade**:

```bash
python tools/propagate_outcome_retirements.py
python tools/propagate_outcome_retirements.py --check
```

### When to propagate

| Condition | Action |
|---|---|
| New retirement registry documents an engineering fix for a recurrence key | Propagate after fix is merged and scenario test passes |
| Registry entry exists and `--check` reports pending mutations | Run propagation; verify idempotency |
| CO106 permanent active key (5 keys) | **Do not propagate** — governance-classified permanent |

### Permanent active keys (excluded from propagation)

See [`CO106_active_recurrence_governance_audit.md`](CO106_active_recurrence_governance_audit.md) §3:

- Speaker `selected_speaker_id` / `selected_speaker_source` — intentional BX design records
- Fallback `final_emitted_source`, sanitizer `scaffold_leakage` — duplicate historical observations
- Fallback `fallback_family` — CO102 operational sentinel

Creating new retirement registries for these keys **without new engineering evidence** is out of stewardship scope and requires re-entry per [`CO108_reentry_criteria.md`](CO108_reentry_criteria.md).

---

## Graduation review cadence

| Review | Frequency | Decision authority |
|---|---|---|
| Quick status | Monthly | Read BQC4 — no operator override of recommendation |
| Full convergence | Quarterly | Cross-check BQ16 blockers against CO106 inventory |
| Graduation event | When `graduation_confidence_ready: true` | BQC4 recommendation **A** is builder-determined; steward documents and commits |

**Graduation is not a manual approval gate.** Stewards observe regenerated artifacts. When `formal_ready` conditions clear, recommendation transitions B → A deterministically (CO107).

---

## Acceptable maintenance activities

These activities **do not** reopen the recurrence engineering program:

| Activity | Acceptable? | Notes |
|---|---|---|
| Run protected replay and commit artifacts | **Yes** | Core stewardship |
| Capture trajectory snapshots | **Yes** | Convergence monitoring |
| Propagate retirements per existing registry | **Yes** | Operational workflow |
| Fix production bugs discovered via protected replay | **Yes** | Normal engineering; retirement registry documents disposition |
| Update runbook clarifications (no new requirements) | **Yes** | Documentation alignment |
| Read and archive graduation reviews | **Yes** | Operational record-keeping |
| Retract CO102 sentinel via `deprecated` status | **Optional** | Hygiene only; modest calibration lift |

---

## Maintenance vs engineering (summary)

| Category | Steward owns? | Engineering program? |
|---|---|---|
| Protected replay execution | **Yes** | No |
| Artifact commit hygiene | **Yes** | No |
| Graduation doc review | **Yes** | No |
| Retirement propagation (registry exists) | **Yes** | No |
| Evidence accumulation over time | **Yes** | No |
| Taxonomy extension | **No** | Re-entry required |
| Formula/threshold changes | **No** | Re-entry required |
| New automation | **No** | Re-entry required |
| Replay architecture changes | **No** | Re-entry required |

Full boundary specification: [`CO108_engineering_boundary_specification.md`](CO108_engineering_boundary_specification.md).

---

## Cross-references

- Engineering closeout: [`CO108_recurrence_program_closeout.md`](CO108_recurrence_program_closeout.md)
- Engineering boundaries: [`CO108_engineering_boundary_specification.md`](CO108_engineering_boundary_specification.md)
- Re-entry criteria: [`CO108_reentry_criteria.md`](CO108_reentry_criteria.md)
- CO100 runbook: [`docs/runbooks/protected_replay_observation_collection.md`](../runbooks/protected_replay_observation_collection.md)
- CO107 maintenance guide: [`CO107_graduation_automation_audit.md`](CO107_graduation_automation_audit.md) §4

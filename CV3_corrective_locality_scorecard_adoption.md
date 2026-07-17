# CV3 Corrective Locality Scorecard Adoption

## Objective

Adopt the validated Runtime Locality + Evidence Amplification model as the canonical corrective-maintenance scorecard for Foundation Stabilization work.

This is a governance and standards adoption document only. It does not modify runtime behavior, regenerate artifacts, or change tests.

## Background

CV established that Total Files Touched overstates architectural breadth because it classifies evidence-heavy commits as diffuse even when runtime behavior is untouched or localized.

CV1 separated corrective churn into:

- Runtime Locality
- Evidence Amplification

CV2 validated that the dual model predicts maintenance cost better than Total Files Touched because it distinguishes:

- architectural cost from runtime owner spread;
- maintenance and review cost from tests, artifacts, governance, replay evidence, and tooling.

## Canonical Corrective Locality Scorecard

Every corrective commit or corrective cohort should report the following scorecard.

### Runtime

| Metric | Definition |
|---|---|
| Runtime Files Touched | Count of production runtime files, production libraries, runtime contracts, runtime configuration, and runtime data structures changed. |
| Runtime Owners Touched | Count of distinct runtime owner groups or ownership surfaces changed. This is the primary architectural health signal. |
| Runtime Directories | Count/list of runtime directories changed. |
| Runtime Modules | Count/list of concrete runtime modules changed. |
| Runtime Locality Class | Excellent, Good, Moderate, or Broad according to threshold rules below. |

### Evidence

| Metric | Definition |
|---|---|
| Tests | Test files and test contracts changed. |
| Helpers | Test/evidence helpers changed. |
| Replay Artifacts | Replay output, replay trend, recurrence, failure dashboard, or replay report artifacts changed. |
| Golden Artifacts | Golden replay, golden transcript, protected replay, or committed expected-output artifacts changed. |
| Governance | Foundation reports, closeouts, manifests, inventories, scorecards, and maintenance docs changed. |
| Audit | Audit-specific docs or audit outputs changed. |
| Tooling | Migration, reporting, validation, scorecard, or replay runner tools changed. |

### Derived

| Metric | Definition |
|---|---|
| Expansion Ratio | Evidence Files / Runtime Files. If Runtime Files is 0 and Evidence Files is greater than 0, report `Infinity`. If both are 0, report `0`. |
| Artifact Churn | Count and class of replay/golden/dashboard artifacts changed. |
| Governance Load | Count and class of governance/audit/maintenance docs changed. |
| Evidence Amplification Class | Minimal, Expected, Heavy, or Exceptional according to Expansion Ratio and evidence context. |
| Overall Review Load | Low, Moderate, High, or Very High based on total files, evidence breadth, runtime owners, and domain risk. |

Total Files Touched may still be reported, but only as a review-load signal. It must not be used alone to classify architectural locality.

## Standard Thresholds

### Runtime Files Touched

| Class | Threshold |
|---|---:|
| Excellent | 0-2 |
| Good | 3-5 |
| Moderate | 6-8 |
| Broad | 9+ |

### Runtime Owners Touched

| Class | Threshold |
|---|---:|
| Excellent | 0-1 |
| Good | 2 |
| Moderate | 3 |
| Broad | 4+ |

Runtime Owners Touched outranks Runtime Files Touched when the two disagree. A correction that touches many files inside one owner may be less architecturally broad than a correction touching fewer files across several owners.

### Expansion Ratio

| Class | Threshold |
|---|---:|
| Minimal | 0-2 |
| Expected | >2-5 |
| Heavy | >5-10 |
| Exceptional | >10 or Infinity |

Expansion Ratio must be interpreted with Runtime Files. Evidence-only commits with `Infinity` are not automatically architectural failures; they are evidence/governance work and should be reviewed as such.

### Artifact Churn

| Class | Threshold |
|---|---:|
| Low | 0-2 artifact files |
| Moderate | 3-6 artifact files |
| High | 7+ artifact files |

Artifact Churn should record whether artifacts are replay/golden/dashboard/recurrence/fallback-incidence outputs. High artifact churn alone is not architectural coupling, but it may indicate evidence model cost.

### Governance Load

| Class | Threshold |
|---|---:|
| Low | 0-2 governance/audit/maintenance docs |
| Moderate | 3-5 governance/audit/maintenance docs |
| High | 6+ governance/audit/maintenance docs |

Governance Load should distinguish current required closeout/discovery evidence from historical or legacy-coupled document rewrites.

### Overall Review Load

| Class | Interpretation |
|---|---|
| Low | Small runtime/evidence footprint, one owner, low artifact/governance load. |
| Moderate | Focused runtime change with expected tests/artifacts/docs, or evidence-only change with bounded artifacts. |
| High | Heavy evidence, high artifact churn, many governance surfaces, or moderate runtime owner spread. |
| Very High | Broad runtime owner spread, cross-cutting runtime instrumentation, or high runtime risk plus high evidence load. |

## Interpretation Rules

1. Broad runtime is architectural.

If Runtime Owners Touched is Broad or Runtime Files Touched is Broad, the correction should be treated as architecturally broad unless the report explains why the breadth is a temporary or foundational investment.

2. Runtime Owners are more important than Runtime Files.

Runtime owner spread is the primary architectural health signal. File count within a single owner can reflect implementation detail; cross-owner change reflects coordination and boundary cost.

3. Heavy evidence with low runtime is expected validation cost.

Evidence-heavy commits with no runtime changes or excellent runtime locality should be classified as evidence amplification, not runtime architecture diffusion.

4. High artifact churn alone is not architectural coupling.

Committed replay/golden/dashboard artifacts increase review load and repository churn, but they do not by themselves prove runtime architecture is broad.

5. Governance load is not automatically waste.

Governance docs, audits, closeouts, and manifests may be required evidence. Mark legacy coupling separately when historical or derivative governance surfaces move because of old reporting structures.

6. Total Files Touched remains review load only.

Total Files Touched can predict reviewer bulk, but it must not be used as the primary corrective locality metric.

7. Evidence Amplification should be bounded and explained.

Evidence-heavy commits should identify the main evidence source: tests, artifacts, governance, audits, tooling, or migration/reporting scripts.

8. Runtime-free corrective commits are valid.

Some corrective work fixes evidence, measurement, migration, governance, or reporting problems without runtime changes. These should be scored as evidence corrections, not forced into runtime locality classes.

## Recent Commit Mapping

| Commit | Runtime Files | Runtime Owners | Runtime Class | Evidence Files | Expansion Ratio | Artifact Churn | Governance Load | Overall Review Load | Interpretation |
|---|---:|---:|---|---:|---:|---|---|---|---|
| CR `bf97ba8` | 0 | 0 | Excellent / runtime-free | 32 | Infinity | High: 12 artifacts | High: 7 docs | High | Evidence-burden correction; recurrence evidence architecture dominates file count. |
| CS `1225af0` | 0 | 0 | Excellent / runtime-free | 16 | Infinity | High: 10 artifacts | Low: 2 docs | Moderate | Evidence-only compact replay harness; broadness is replay artifact churn, not runtime architecture. |
| CT `845e6db` | 1 | 1 | Excellent | 8 | 8.0 | Low: 2 artifacts | Low: 2 docs | Moderate | Healthy corrective pattern: one runtime projection fix plus focused evidence envelope. |
| CU `8aefe23` | 15 | 7 | Broad | 21 | 1.4 | Low: 0 artifacts | High: 7 docs | Very High | Foundational cross-cutting attribution investment; true runtime breadth. |

## Examples

### Healthy Corrective Pattern

Example: CT `845e6db`.

Pattern:

- 1 runtime file.
- 1 runtime owner.
- Evidence envelope includes tests, report tooling, artifacts, and audit docs.
- Expansion Ratio is Heavy at 8.0, but runtime locality is Excellent.

Interpretation:

This is the desired pattern for a runtime correction: small runtime change, explicit evidence, and clear audit trail.

### Acceptable Evidence-Heavy Pattern

Example: CS `1225af0`.

Pattern:

- 0 runtime files.
- 16 evidence files.
- 10 replay/golden trend artifacts.
- Low governance load.

Interpretation:

This is acceptable when the work is explicitly measurement or harness adoption. It should not be described as runtime broad.

### Runtime-Broad Warning Pattern

Example: CU `8aefe23`.

Pattern:

- 15 runtime files.
- 7 runtime owners.
- High governance load.
- Evidence follows many runtime consumers.

Interpretation:

This is architecturally broad. It may still be justified as foundational investment, but it should trigger an explanation of why cross-owner runtime changes were necessary and whether future corrections should become smaller after the foundation lands.

### Evidence-Burden / Legacy-Coupling Pattern

Example: CR `bf97ba8`.

Pattern:

- 0 runtime files.
- 32 evidence files.
- 12 recurrence/replay/dashboard artifacts.
- 7 governance docs, including historical/legacy-coupled surfaces.

Interpretation:

The cost is not runtime architecture. The scorecard should identify required evidence versus legacy coupling and ask whether derivative/historical artifacts can be decoupled in future cycles.

## Integration Recommendations

The Corrective Locality Scorecard should appear in:

- Foundation Stabilization reports.
- Cycle closeouts for corrective or stabilization cycles.
- Architecture reviews after corrective cohorts.
- Reconciliation reports that compare runtime and evidence churn.
- Corrective PR templates or commit review notes.
- CI or local summary artifacts when corrective metrics are generated.
- Maintenance-economics reports where file count is used as a cost proxy.

Recommended minimum scorecard block:

```text
Corrective Locality Score
- Runtime files:
- Runtime owners:
- Runtime locality class:
- Evidence files:
- Tests/helpers:
- Replay/golden artifacts:
- Governance/audit docs:
- Tooling:
- Expansion ratio:
- Artifact churn:
- Governance load:
- Overall review load:
- Interpretation:
```

## Future Guidance

A corrective commit should not be considered architecturally broad based solely on Total Files Touched.

Future corrective work should be evaluated as follows:

1. Classify touched files into Runtime and Evidence buckets.
2. Count Runtime Owners before drawing architecture conclusions.
3. Use Runtime Owners as the primary architectural health signal.
4. Use Runtime Files as the secondary architecture signal.
5. Track Evidence Amplification independently.
6. Identify whether evidence breadth comes from tests, artifacts, governance, audits, tooling, or migration/reporting scripts.
7. Record Artifact Churn separately from Governance Load.
8. Treat Total Files Touched as review load only.
9. For broad runtime corrections, document whether breadth is necessary, temporary, architectural debt, or foundational investment.
10. For evidence-heavy corrections, document whether evidence is required, expected, optional, legacy coupling, or unknown.

Future Foundation Stabilization cycles should optimize:

- first: Runtime Owners Touched;
- second: Runtime Files Touched;
- third: Evidence Amplification bounded by category and necessity;
- fourth: Artifact Churn and Governance Load where they create review drag.

## Adoption Recommendation

Recommendation: Adopt.

Confidence: medium-high.

Rationale:

- CV showed Total Files Touched over-classified all sampled commits as diffuse.
- CV1 showed that three of four commits were runtime-local or runtime-free.
- CV2 showed the dual scorecard better predicts corrective cost and distinguishes evidence burden from architectural breadth.
- The sample is small, so thresholds should be revisited after the next corrective cohort, but the model is already superior to Total Files Touched as a primary metric.

Adoption statement:

The Runtime Locality + Evidence Amplification scorecard is now the recommended canonical corrective-maintenance scorecard for Foundation Stabilization work. Total Files Touched remains a review-load metric only and should not determine architectural locality without Runtime Files and Runtime Owners.

## Next Review Point

Reassess thresholds after the next 5-10 corrective commits. Specifically check whether:

- CT-like one-owner runtime corrections become the norm.
- CU-like cross-cutting runtime changes decline after foundational attribution work.
- artifact churn remains high even when runtime locality improves.
- governance load is mostly required/expected rather than legacy coupling.

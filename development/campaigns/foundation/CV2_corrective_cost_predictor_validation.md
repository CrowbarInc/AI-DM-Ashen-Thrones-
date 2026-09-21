# CV2 Corrective Cost Predictor Validation

## Objective

Validate whether the Runtime Locality + Evidence Amplification model predicts corrective maintenance effort better than Total Files Touched for the post-CQ corrective sample.

No code was modified. No artifacts were regenerated. This report evaluates committed history only.

## Scope

Sample inherited from CV and CV1:

- `bf97ba8` - CR: Protected Replay Recurrence Separation
- `1225af0` - CS: Compact Golden Drift Harness
- `845e6db` - CT: Runtime Fallback Incidence Baseline
- `8aefe23` - CU: Semantic Mutation Write-Site Attribution

Prior baseline:

- CV old metric: all four commits classified diffuse by Total Files Touched.
- CV1 split: CR and CS were evidence-only, CT was one runtime file plus evidence, and CU was genuinely runtime-broad.

## Method

This block estimates corrective cost by separating cost dimensions:

- Implementation complexity: difficulty of the code or artifact change itself.
- Review complexity: how much a reviewer must understand across surfaces.
- Regression risk: likelihood of changing runtime behavior or important diagnostic semantics.
- Testing effort: effort to validate targeted and adjacent behavior.
- Governance effort: documentation, audit, manifest, and evidence update cost.
- Coordination effort: cross-owner or cross-surface sequencing cost.

Ratings are qualitative: Very Low, Low, Moderate, High, Very High.

## Corrective Cost Profiles

### `bf97ba8` - CR: Protected Replay Recurrence Separation

Metric profile:

- Total files touched: 32
- Runtime files: 0
- Runtime owners: 0
- Evidence files: 32
- Expansion ratio: Infinity

Cost profile:

- Implementation complexity: Moderate. No runtime code changed, but recurrence lane separation affected helper logic, migration tooling, artifact writers, and generated outputs.
- Review complexity: High. Review requires following protected recurrence, diagnostic recurrence, compatibility artifacts, dashboard helpers, and historical audit updates.
- Regression risk: Moderate. Gameplay runtime risk is very low, but recurrence health reporting risk is meaningful because canonical and diagnostic lanes can contaminate each other.
- Testing effort: High. Multiple recurrence/dashboard/migration tests changed, and artifact identity must remain coherent.
- Governance effort: Very High. Seven governance documents and many committed recurrence/owner-drift artifacts changed.
- Coordination effort: High. The commit spans recurrence helpers, dashboard/report helpers, migration tooling, generated artifacts, and historical governance surfaces.

Actual maintenance cost: High.

Best predictor: Evidence Files plus Expansion Ratio.

Primary maintenance cost cause: Evidence Burden.

Why:

Total Files Touched correctly predicts review bulk, but for the wrong reason if interpreted as runtime breadth. Runtime work is absent. The cost comes from evidence architecture: recurrence artifacts, dashboard helpers, tests, migration scripts, and governance surfaces all needed to align.

### `1225af0` - CS: Compact Golden Drift Harness

Metric profile:

- Total files touched: 16
- Runtime files: 0
- Runtime owners: 0
- Evidence files: 16
- Expansion ratio: Infinity

Cost profile:

- Implementation complexity: Low. The work is a compact trend harness and evidence plumbing, not runtime behavior.
- Review complexity: Moderate. Review must inspect trend helper behavior, registry coverage, committed run artifacts, and manifest/convergence docs.
- Regression risk: Low. Runtime behavior is untouched; the main risk is false confidence or false drift in the compact signal.
- Testing effort: Moderate. The trend test and compact artifacts need coherence, but the surface is narrower than CR.
- Governance effort: Moderate. Protected replay manifest and convergence inventory updates make the harness discoverable and policy-bounded.
- Coordination effort: Moderate. The harness spans tooling, test helper, registry, artifacts, and docs.

Actual maintenance cost: Moderate.

Best predictor: Evidence Files and Replay/Artifact Churn.

Primary maintenance cost cause: Replay/Artifact Churn.

Why:

Total Files Touched says diffuse, but runtime locality says this is not a runtime correction at all. The cost is mostly the committed compact replay evidence bundle.

### `845e6db` - CT: Runtime Fallback Incidence Baseline

Metric profile:

- Total files touched: 9
- Runtime files: 1
- Runtime owners: 1
- Evidence files: 8
- Expansion ratio: 8.0

Cost profile:

- Implementation complexity: Low. The runtime change is localized to one projection module.
- Review complexity: Moderate. Review still needs report tooling, validation tooling, tests, artifacts, and audit docs to confirm the projection baseline.
- Regression risk: Low to Moderate. Runtime gameplay risk is low because this is projection/reporting-adjacent, but diagnostic fidelity matters.
- Testing effort: Moderate. Fallback incidence and runtime lineage tests carry most validation effort.
- Governance effort: Moderate. CT discovery and projection fidelity audit explain the baseline and root-cause correction.
- Coordination effort: Low to Moderate. One runtime owner plus several evidence surfaces.

Actual maintenance cost: Moderate.

Best predictor: Runtime Files plus Evidence Amplification.

Primary maintenance cost cause: Mixed.

Why:

This is the strongest validation case for the new model. Total Files Touched labels the correction diffuse, but the actual runtime correction is excellent-locality: one file, one owner. The maintenance cost comes from the evidence envelope around that small runtime correction.

### `8aefe23` - CU: Semantic Mutation Write-Site Attribution

Metric profile:

- Total files touched: 36
- Runtime files: 15
- Runtime owners: 7
- Evidence files: 21
- Expansion ratio: 1.4

Cost profile:

- Implementation complexity: Very High. The change adds and wires semantic mutation attribution across many active write sites and reconciliation consumers.
- Review complexity: Very High. Review must understand final emission, sanitizer, fallback provenance, response policy, upstream repairs, runtime lineage, classifier behavior, and governance contracts.
- Regression risk: High. The intended effect is mostly attribution/metadata, but the hooks sit near runtime text mutation and final-emission boundaries.
- Testing effort: Very High. Many focused tests and helper consumers changed to prove attribution precedence and adoption.
- Governance effort: High. Seven CU audit/governance reports describe discovery, envelope, reconciliation, prompt/policy attribution, governance, contract adoption, and acceptance.
- Coordination effort: Very High. This crosses many runtime owners and multiple evidence consumers.

Actual maintenance cost: Very High.

Best predictor: Runtime Owners plus Runtime Files.

Primary maintenance cost cause: Cross-Cutting Architecture.

Why:

The old metric and new metrics both predict high cost here, but the new metrics explain why: CU is not merely a large commit; it is runtime-broad across real semantic mutation write sites. Evidence amplification is present, but the runtime owner spread is the maintenance driver.

## Old Metric vs New Metrics

| Commit | Old Metric | Runtime Locality | Evidence Burden | Actual Maintenance Cost | Best Predictor |
|---------|------------|------------------|-----------------|------------------------|----------------|
| `bf97ba8` | Diffuse: 32 total files | Runtime-free | Very High: 32 evidence files, Infinity expansion | High | Evidence Files + Expansion Ratio |
| `1225af0` | Diffuse: 16 total files | Runtime-free | High: 16 evidence files, 10 artifacts, Infinity expansion | Moderate | Evidence Files + Artifact Churn |
| `845e6db` | Diffuse: 9 total files | Excellent: 1 runtime file, 1 owner | Moderate: 8 evidence files, 8.0 expansion | Moderate | Runtime Files + Evidence Amplification |
| `8aefe23` | Diffuse: 36 total files | Broad: 15 runtime files, 7 owners | High: 21 evidence files, 1.4 expansion | Very High | Runtime Owners + Runtime Files |

## Source of Maintenance Cost

| Commit | Primary Cause | Explanation |
|---|---|---|
| `bf97ba8` | Evidence Burden | Runtime is untouched; cost is recurrence evidence separation, artifacts, tests, migration tools, and governance alignment. |
| `1225af0` | Replay/Artifact Churn | Runtime is untouched; most files are compact trend artifacts and replay-harness evidence. |
| `845e6db` | Mixed | One focused runtime projection change plus necessary report, artifact, test, and audit updates. |
| `8aefe23` | Cross-Cutting Architecture | Runtime attribution hooks span many actual writer surfaces; tests and governance follow that broad runtime footprint. |

## False Positives From Total Files Touched

False positive: `bf97ba8`.

- Old metric predicted: large/diffuse correction.
- Runtime reality: 0 runtime files, 0 runtime owners.
- Why old metric failed: it counted recurrence artifacts, helper/test surfaces, migration tools, and governance docs as if they were runtime breadth.

False positive: `1225af0`.

- Old metric predicted: large/diffuse correction.
- Runtime reality: 0 runtime files, 0 runtime owners.
- Why old metric failed: it counted committed compact replay artifacts and manifest/governance updates as runtime-scale churn.

False positive: `845e6db`, partially.

- Old metric predicted: diffuse correction.
- Runtime reality: 1 runtime file, 1 runtime owner.
- Why old metric failed: the total file count was dominated by the fallback incidence evidence envelope, not production spread.

## True Architectural Breadth

True runtime-broad commit: `8aefe23`.

Why:

- It touched 15 runtime modules.
- It crossed approximately seven runtime owner groups.
- The purpose was to introduce semantic mutation write-site attribution across many actual places where emitted text or mutation evidence can be written.

Breadth classification:

- Necessary: yes. Attribution has to be captured at real write sites or it remains projection-inferred.
- Temporary: partly. Once the envelope is installed, later fixes should be able to touch fewer write sites.
- Architectural debt: partly. The need to instrument many surfaces reflects pre-existing distributed mutation ownership.
- Foundational investment: yes. The broad change creates a reusable attribution model intended to reduce future mislocalized semantic mutation diagnostics.

## Predictive Accuracy

Old Metric Accuracy: Fair.

Support:

- It correctly flags that all four commits carry non-trivial review bulk.
- It correctly identifies CU as expensive.
- It fails to distinguish runtime breadth from evidence breadth.
- It produces three runtime-local false positives: CR, CS, and CT look architecturally diffuse under total files even though runtime work is absent or tiny.

New Metric Accuracy: Good.

Support:

- Runtime Files and Runtime Owners explain actual architectural risk much better.
- Evidence Files and Expansion Ratio explain why runtime-local commits still have real maintenance cost.
- The dual model distinguishes evidence-only cost, artifact churn, focused runtime correction with evidence envelope, and true runtime-broad work.
- The sample is only four commits, so the rating should not be raised to Excellent yet.

## Metric Recommendation

Recommendation: D. Runtime + Evidence dual scorecard.

Future stabilization work should track at least:

- Runtime Files Touched.
- Runtime Owners Touched.
- Evidence Files Touched.
- Expansion Ratio.
- Replay/Artifact Churn.
- Governance/Audit Files Touched.

Total Files Touched should remain a secondary review-load signal, not the primary corrective-maintenance metric.

Why:

- Total Files Touched is too coarse for this repository.
- Runtime Files Touched alone would undercount CR and CS, which had real evidence/governance cost.
- Runtime Owners Touched is the best architectural-risk predictor, especially for CU.
- Evidence Files and Expansion Ratio capture the repo's committed validation model.
- Replay/Artifact Churn deserves its own line because committed golden/replay evidence accounted for 24 of 77 evidence files in CV1.

## Architectural Interpretation

Has corrective locality actually improved?

Partially. Runtime locality appears improved for CR, CS, and CT: two had no runtime changes and one had a one-file runtime correction. CU remains broad because semantic mutation attribution crossed real runtime write sites.

Has governance maturity increased apparent maintenance cost?

Yes. The project now commits extensive proof: discovery reports, closeouts, audit docs, replay artifacts, dashboard artifacts, report scripts, and focused tests. That maturity increases apparent file churn even when runtime correction is local.

Is evidence amplification now an expected property of the repository?

Yes. Evidence amplification is not an anomaly in this sample. It is the dominant source of touched files: CV1 counted 77 evidence files against 16 runtime files.

Is the architecture becoming easier to maintain despite broad commits?

Likely yes, but not uniformly. CT suggests healthier maintenance: one small runtime projection correction with a clear evidence envelope. CR and CS show evidence systems maturing without runtime churn. CU is a foundational investment that may reduce future attribution/debugging cost, but it is itself broad.

Which metric should future Foundation Stabilization cycles optimize?

Optimize Runtime Owners Touched first, then Runtime Files Touched, while separately budgeting Evidence Amplification. The most useful target is not "fewest total files"; it is "fewest runtime owners for a corrective fix, with expected evidence updates kept bounded and explainable."

## Final Conclusion

Runtime Locality + Evidence Amplification should replace Total Files Touched as the project's primary corrective-maintenance metric.

Confidence: medium.

The dual model is more accurate because it explains both kinds of cost:

- architectural cost from runtime owner spread;
- maintenance/review cost from evidence, replay, artifact, and governance amplification.

Total Files Touched should remain visible as a review-load indicator, but it should not drive locality conclusions by itself. In the CV sample, it over-classified three commits as architecturally diffuse and failed to identify why CU was genuinely expensive.

## Recommended Next Block

Adopt a corrective scorecard with separate thresholds:

- Runtime-local target: 0-2 runtime files and 0-1 runtime owners.
- Runtime-watch target: 3-5 runtime files or 2 runtime owners.
- Runtime-broad alert: 6+ runtime files or 3+ runtime owners.
- Evidence amplification target: evidence ratio explained by tests/artifacts/governance category.
- Artifact churn alert: committed replay/golden artifacts exceed runtime file count by 5x or more.

Use CT as the positive reference pattern: small runtime correction, explicit evidence envelope, and clear audit trail.

# CV1 Runtime vs Evidence Locality Reconciliation

## Objective

Determine whether the post-CQ corrective sample is genuinely broad in runtime architecture, or whether evidence, governance, replay, and audit updates account for most of the observed file churn.

No runtime behavior was modified for this block. No artifacts were regenerated. This report measures committed behavior only.

## Scope

Reconciled sample from `CV_corrective_locality_confirmation_discovery.md`:

- `bf97ba8` - CR: Protected Replay Recurrence Separation
- `1225af0` - CS: Compact Golden Drift Harness
- `845e6db` - CT: Runtime Fallback Incidence Baseline
- `8aefe23` - CU: Semantic Mutation Write-Site Attribution

Commit range: `19167c1..8aefe23`, immediately after CQ completion.

## Method

Every touched file was assigned to exactly one bucket:

- Runtime: production runtime files, production libraries, runtime contracts, runtime config, and runtime data structures.
- Evidence: tests, helpers, fixtures, replay/golden artifacts, dashboards, governance, audits, maintenance docs, migration tools, reporting scripts, and validation scripts.

For this repo, files under `game/` were counted as runtime. Files under `tests/`, `artifacts/golden_replay/`, `docs/`, top-level audit/discovery markdown, and `tools/` were counted as evidence because they validate, explain, migrate, report, or govern behavior rather than directly owning runtime behavior.

## Summary Table

| Commit | Runtime Files | Evidence Files | Runtime Owners | Runtime Locality | Expansion Ratio | Main Source of Breadth |
|---------|--------------:|---------------:|---------------:|------------------|----------------:|------------------------|
| `bf97ba8` | 0 | 32 | 0 | None / no runtime change | Infinity | Recurrence artifacts, dashboard helpers, migration tooling, historical governance docs |
| `1225af0` | 0 | 16 | 0 | None / no runtime change | Infinity | Compact replay trend artifacts plus manifest/convergence governance |
| `845e6db` | 1 | 8 | 1 | Excellent | 8.0 | Fallback incidence report tooling, tests, artifacts, and projection audit docs |
| `8aefe23` | 15 | 21 | 7 | Broad | 1.4 | Cross-cutting semantic mutation attribution instrumentation plus governance/tests |

## Per-Commit Reclassification

### `bf97ba8` - CR: Protected Replay Recurrence Separation

Runtime bucket: 0 files.

Evidence bucket: 32 files.

- Replay/golden artifacts: 12
- Governance docs: 7
- Tests/helpers: 11
- Tooling: 2

Runtime locality:

- Runtime files touched: 0
- Runtime owners touched: 0
- Runtime directories touched: 0
- Runtime modules touched: 0
- Runtime locality class: none / no runtime change

Evidence locality:

- Evidence files touched: 32
- Evidence change class: unusually broad
- Expansion ratio: Infinity

Evidence necessity estimate:

- Required: 18 files. Core recurrence artifacts, new separated diagnostic logs, recurrence/dashboard helpers, migration/regeneration tooling, and direct recurrence tests.
- Expected: 7 files. Closeout/discovery and directly relevant audit evidence that documents the new recurrence lane model.
- Optional: 0 files identified as clearly optional from file names alone.
- Legacy coupling: 7 files. Historical BQ/BQC audit files and owner drift outputs that appear to move because old recurrence/governance surfaces still mirror the canonical recurrence state.
- Unknown: 0 files.

Estimated evidence percentages:

- Required Evidence: 56.3%
- Optional Evidence: 0.0%
- Potentially Eliminable: 21.9% from legacy coupling, assuming historical audit rewrites or derivative drift outputs could eventually be decoupled from corrective commits.

Owner spread:

- Runtime owner spread: none.
- Evidence owner spread: high. Recurrence core helpers, dashboard writers, dashboard path/report helpers, migration tools, golden artifacts, owner drift artifacts, and governance docs all changed.
- Source of cross-owner activity: evidence architecture, not runtime architecture.

Finding:

This commit is diffuse only because recurrence evidence is broad and committed. Runtime locality is trivially localized because there is no runtime change.

### `1225af0` - CS: Compact Golden Drift Harness

Runtime bucket: 0 files.

Evidence bucket: 16 files.

- Replay/golden artifacts: 10
- Governance docs: 2
- Tests/helpers: 3
- Tooling: 1

Runtime locality:

- Runtime files touched: 0
- Runtime owners touched: 0
- Runtime directories touched: 0
- Runtime modules touched: 0
- Runtime locality class: none / no runtime change

Evidence locality:

- Evidence files touched: 16
- Evidence change class: expected
- Expansion ratio: Infinity

Evidence necessity estimate:

- Required: 8 files. Trend helper, protected replay registry, trend test, trend runner, compact summary, golden transcript drift payload, and run summary JSONs.
- Expected: 8 files. Underlying storage artifacts and governance manifest/convergence updates that make the compact harness discoverable and reviewable.
- Optional: 0 files identified as clearly optional.
- Legacy coupling: 0 files.
- Unknown: 0 files.

Estimated evidence percentages:

- Required Evidence: 50.0%
- Optional Evidence: 0.0%
- Potentially Eliminable: 0.0% from this committed sample. Artifact churn could be reduced by not committing run storage, but the current project model treats these as evidence.

Owner spread:

- Runtime owner spread: none.
- Evidence owner spread: moderate. Trend harness, protected replay registry, generated replay artifacts, protected replay manifest, convergence inventory, and trend runner.
- Source of cross-owner activity: evidence architecture.

Finding:

The raw 16-file footprint is entirely evidence-side. This is not a runtime locality problem.

### `845e6db` - CT: Runtime Fallback Incidence Baseline

Runtime bucket: 1 file.

- `game/final_emission_replay_projection.py`

Evidence bucket: 8 files.

- Replay/golden artifacts: 2
- Governance docs: 2
- Tests/helpers: 2
- Tooling: 2

Runtime locality:

- Runtime files touched: 1
- Runtime owners touched: 1 (`final_emission_replay_projection`)
- Runtime directories touched: 1 (`game/`)
- Runtime modules touched: 1
- Runtime locality class: excellent

Evidence locality:

- Evidence files touched: 8
- Evidence change class: focused
- Expansion ratio: 8.0

Evidence necessity estimate:

- Required: 5 files. Fallback incidence report tests, runtime lineage test, report tooling, validation tooling, and refreshed JSON evidence.
- Expected: 3 files. Markdown report artifact and CT audit/discovery docs.
- Optional: 0 files identified as clearly optional.
- Legacy coupling: 0 files.
- Unknown: 0 files.

Estimated evidence percentages:

- Required Evidence: 62.5%
- Optional Evidence: 0.0%
- Potentially Eliminable: 0.0% in the current evidence model. The ratio would drop only if committed report artifacts or audit docs were intentionally moved out of corrective commits.

Owner spread:

- Runtime owner spread: one projection module.
- Evidence owner spread: moderate. Tests, report tooling, validation tooling, committed fallback incidence artifacts, and audit docs.
- Source of cross-owner activity: evidence architecture.

Finding:

This is the clearest reconciliation case. The runtime fix is excellent-locality: one production module. The total commit looked diffuse because every runtime correction carried a validation/reporting/audit envelope.

### `8aefe23` - CU: Semantic Mutation Write-Site Attribution

Runtime bucket: 15 files.

- `game/fallback_provenance_debug.py`
- `game/final_emission_acceptance_quality.py`
- `game/final_emission_finalize.py`
- `game/final_emission_gate_preflight_defaults.py`
- `game/final_emission_meta.py`
- `game/final_emission_opening_fallback.py`
- `game/final_emission_response_type.py`
- `game/final_emission_sealed_fallback.py`
- `game/final_emission_terminal_pipeline.py`
- `game/final_emission_visibility_fallback.py`
- `game/output_sanitizer.py`
- `game/response_policy_enforcement.py`
- `game/runtime_lineage_telemetry.py`
- `game/semantic_mutation_attribution.py`
- `game/upstream_response_repairs.py`

Evidence bucket: 21 files.

- Replay/golden artifacts: 0
- Governance docs: 7
- Tests/helpers: 14
- Tooling: 0

Runtime locality:

- Runtime files touched: 15
- Runtime owners touched: 7:
  - fallback provenance
  - final emission metadata/finalization/terminal/opening/response/sealed/visibility/preflight/acceptance quality
  - output sanitizer
  - response policy
  - runtime lineage telemetry
  - semantic mutation attribution
  - upstream response repairs
- Runtime directories touched: 1 (`game/`)
- Runtime modules touched: 15
- Runtime locality class: broad

Evidence locality:

- Evidence files touched: 21
- Evidence change class: unusually broad
- Expansion ratio: 1.4

Evidence necessity estimate:

- Required: 14 files. Direct tests/helpers for classifier, projection, runtime lineage, final-emission metadata, output sanitizer, semantic mutation attribution, and contract adoption.
- Expected: 7 files. CU discovery, envelope, reconciliation, prompt/policy, governance, adoption, and acceptance audit docs.
- Optional: 0 files identified as clearly optional.
- Legacy coupling: 0 files.
- Unknown: 0 files.

Estimated evidence percentages:

- Required Evidence: 66.7%
- Optional Evidence: 0.0%
- Potentially Eliminable: 0.0% from the touched evidence set. The breadth is mostly inherent to a cross-cutting attribution envelope, not obvious governance waste.

Owner spread:

- Runtime owner spread: high. The attribution envelope touches many actual writers of semantic mutation evidence.
- Evidence owner spread: high. Tests and helpers cover classifier, golden projection, runtime lineage reporting, metadata, sanitizer, and governance adoption.
- Source of cross-owner activity: both runtime architecture and evidence architecture.

Finding:

CU is the exception to the evidence-dominates pattern. It is genuinely broad at runtime because semantic mutation attribution was wired across many write sites and consumers. Still, the evidence bucket is smaller than the runtime bucket by expansion ratio standards; this commit is architecturally broad, not merely artifact-broad.

## Aggregate Metrics

Sample size: 4 commits.

Runtime files per fix:

- Average runtime files/fix: 4.0
- Median runtime files/fix: 0.5
- Distribution:
  - None / no runtime change: 2 commits (`bf97ba8`, `1225af0`)
  - Excellent: 1 commit (`845e6db`)
  - Good: 0 commits
  - Moderate: 0 commits
  - Broad: 1 commit (`8aefe23`)

Evidence files per fix:

- Average evidence files/fix: 19.25
- Median evidence files/fix: 18.5
- Distribution:
  - Focused: 1 commit (`845e6db`)
  - Expected: 1 commit (`1225af0`)
  - Unusually broad: 2 commits (`bf97ba8`, `8aefe23`)

Expansion ratio:

- `bf97ba8`: Infinity
- `1225af0`: Infinity
- `845e6db`: 8.0
- `8aefe23`: 1.4
- Average expansion ratio among commits with runtime changes only: 4.7
- Average expansion ratio including no-runtime commits: Infinity

Owner counts:

- Average runtime owner count across all commits: 2.0
- Median runtime owner count across all commits: 0.5
- Average runtime owner count among runtime-touching commits: 4.0
- Average evidence owner count: 4.75

Evidence necessity across all 77 evidence files:

- Required: 45 files, 58.4%
- Expected: 25 files, 32.5%
- Optional: 0 files, 0.0%
- Legacy coupling: 7 files, 9.1%
- Unknown: 0 files, 0.0%
- Potentially eliminable: 7 files, 9.1%, mostly historical/derivative recurrence governance coupling in CR.

## Removing Committed Artifacts

Committed replay/golden artifacts account for:

- CR: 12 of 32 evidence files
- CS: 10 of 16 evidence files
- CT: 2 of 8 evidence files
- CU: 0 of 21 evidence files
- Total: 24 of 77 evidence files, 31.2%

If committed artifacts were excluded from total file counts, the sample would change from:

- Total files: 93
- Runtime files: 16
- Evidence files: 77

to:

- Total non-artifact files: 69
- Runtime files: 16
- Non-artifact evidence files: 53

That would reduce the average files touched per fix from 23.25 to 17.25, but it would not make the sample fully local. It would dramatically improve CS and materially improve CR. It would not change CU's broad runtime footprint.

## Architectural Findings

Have runtime fixes become localized?

Partially. Three of four commits have excellent or no runtime footprint: CR and CS are evidence-only, and CT touches one runtime module. CU remains genuinely broad because semantic mutation write-site attribution spans many production writer surfaces.

Does evidence amplification dominate corrective commits?

Yes. Evidence files are 77 of 93 touched files, or 82.8% of the sample. Average evidence files per fix are 19.25 compared with 4.0 runtime files per fix. For CR, CS, and CT, breadth is primarily evidence-side.

Is governance now the primary driver of file count?

Governance is a major driver but not the only one. Replay/golden artifacts are the largest evidence amplifier in CR and CS. Governance/audit docs account for 18 of 77 evidence files, while replay artifacts account for 24 and tests/helpers account for 30. The broader pattern is the evidence model as a whole, not governance alone.

Would removing committed artifacts dramatically change locality metrics?

Yes for artifact-heavy commits, especially CS and CR. Removing committed artifacts would reduce evidence file count by 31.2%. It would not solve broadness where tests/governance or runtime instrumentation are legitimately cross-cutting.

Does the architecture appear healthier than the raw file-count metric suggests?

Yes, with a caveat. The raw file-count metric overstated runtime architectural diffusion for CR, CS, and CT. CT shows a healthy one-file runtime correction with an eight-file evidence envelope. The caveat is CU: semantic attribution is still broad at runtime because the behavior being attributed crosses many real write sites.

## Runtime Owner Spread vs Evidence Owner Spread

Runtime owner spread is concentrated:

- CR: 0 runtime owners
- CS: 0 runtime owners
- CT: 1 runtime owner
- CU: 7 runtime owners

Evidence owner spread is consistently wider:

- CR: recurrence artifacts, dashboard helpers, recurrence helper/tests, migration tooling, governance docs, owner drift outputs
- CS: trend artifacts, trend helper/tests, protected registry, runner, manifest, convergence inventory
- CT: projection audit docs, fallback incidence artifacts, report tooling, validation tooling, tests
- CU: semantic attribution governance, classifier/projection/lineage helpers, final-emission/sanitizer/runtime-lineage tests

Cross-owner activity therefore originates mostly from evidence architecture in three commits. Only CU shows comparable runtime-side cross-owner spread.

## Final Assessment

B. Runtime locality improving but still mixed.

Confidence: medium.

Rationale:

- The sample is small: only four post-CQ commits.
- Three commits support the hypothesis that raw file-count broadness is primarily an artifact of the project's evidence/governance model.
- One commit, CU, disproves a blanket "runtime locality confirmed" conclusion because it has 15 runtime files across approximately seven runtime owners.
- Evidence amplification clearly dominates aggregate file count, but not every broad commit can be explained away as evidence churn.

Executive conclusion:

The apparent locality problem is primarily an artifact of the project's evidence/governance model for CR, CS, and CT. It is architectural for CU. Overall, the repo appears healthier than the raw total-files metric suggested, but runtime locality is not fully confirmed across post-CQ corrective work.

## Recommended Next Block

Use separate scorecards going forward:

- Runtime locality score: runtime files, runtime modules, runtime owner count.
- Evidence amplification score: tests, artifacts, docs, tools, and governance files.
- Artifact pressure score: committed replay/golden artifacts touched per correction.

Then compare future corrective commits against CT as the desirable pattern: one small runtime correction plus focused evidence, rather than measuring total touched files alone.

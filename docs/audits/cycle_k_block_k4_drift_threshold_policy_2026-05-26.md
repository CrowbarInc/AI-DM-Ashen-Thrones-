# Replay Drift Threshold Policy

## Policy Summary

The minimal safe initial policy is:

> A declared protected replay scenario must have zero violations of its existing asserted structural and player-facing semantic invariants. Diagnostic drift evidence that is not itself an existing protected assertion must be reported, not newly promoted to failure in this policy block.

This repository does not currently provide evidence for numeric thresholds such as permissible fallback counts, sanitizer mutation counts, gate-path frequency deviations, lineage recurrence limits, or evaluator score cutoffs within protected golden replay. K4 therefore defines acceptance boundaries without inventing quantitative enforcement.

Policy classes used below:

| Class | Meaning |
|---|---|
| `ACCEPTANCE_BLOCKING` | A violation of an existing declared protected invariant should block acceptance; today it already does when asserted in a protected replay test. |
| `WARNING` | A concrete undesirable signal should be highlighted for investigation, but is not safe to make a general acceptance rule beyond existing assertions. |
| `REPORT_ONLY` | Useful diagnostic evidence with no independent acceptance meaning today. |
| `FUTURE_MONITORING` | Frequency, recurrence, or trend evidence requiring longitudinal data and/or stronger instrumentation before policy. |

## Current Drift Inventory

| Drift Type | Observable Origin | Classification / Report Surface | Current Meaning |
|---|---|---|---|
| Exact drift | `tests/helpers/golden_replay.py::classify_golden_drift(...)` compares normalized `final_text` hashes only when `exact_text` is supplied. | Bucket/tag `exact_drift`; classifier maps it to `replay_drift`. | Optional prose equality evidence; the baseline explicitly states exact prose comparison is opt-in. |
| Structural drift | `_STRUCTURAL_DRIFT_FIELDS`, dotted trace paths, and assertion expectation checks in `tests/helpers/golden_replay.py`. | Bucket/tag `structural_drift`; classified by affected field into route, speaker, fallback, emission, validator, projection, normalization, or related owners. | Metadata/ownership/route contract mismatch. Protected instances are acceptance invariants. |
| Semantic drift | `_SEMANTIC_DRIFT_FIELDS = {"final_text", "scaffold_leakage"}` plus text predicate checks. | Bucket/tag `semantic_drift`; `scaffold_leakage` classifies as `sanitizer`; failed final-text predicates classify as `semantic_mutation`. | Player-facing outcome violation, such as internal scaffold leakage or loss of required useful output. |
| Fallback drift | Structural fields including `final_emitted_source`, `fallback_family`, `fallback_temporal_frame`, opening/sealed/visibility fallback fields. | Classifier category `fallback`; tags include `fallback_source_mismatch` and `fallback_family_mismatch`; rendered in fallback summaries. | A fallback path/source/family differs from an expected invariant. |
| Fallback ownership drift | `opening_fallback_authorship_source`, `opening_fallback_owner_bucket`, `sealed_fallback_owner_bucket`, `visibility_fallback_owner_bucket`, sanitizer empty-fallback owner. | Classifier routes fallback ownership symptoms to existing ownership/investigation targets; report fallback/sanitizer tables expose them. | Boundary ownership evidence; opening ownership is explicitly protected in a direct-seam scenario. |
| Sanitizer drift | `scaffold_leakage` plus sanitizer mode/event/change/empty-fallback/lineage/strict-social fields projected in golden replay. | Category `sanitizer`; classification is `critical` for sanitizer-classified failure; reports show sanitizer evidence. | Player-visible leakage is an existing protected failure; supporting lineage values are diagnostic unless explicitly asserted. |
| Gate-path drift | Runtime-lineage event `gate_outcome` and its `gate_path`; aggregated by `build_runtime_lineage_summary(...)`. | `gate_path_frequency` in Runtime Lineage Summary. | Frequency/route evidence only; not a golden drift bucket or protected comparison today. |
| Runtime-lineage drift | `runtime_lineage_events` projected by golden replay and normalized/recorded for report output. | Runtime Lineage Summary: counts of fallback selection, speaker repair, mutation, gate outcome, and top kinds. | Diagnostic provenance; a test confirms lineage alone does not alter drift classification. |
| Mutation drift | Structural observables `final_emission_mutation_lineage` and `post_gate_mutation_detected`; mutation lineage events. | Classifier `emission` / mutation evidence; report mutation flags and lineage summary. | Indicates transformation after earlier stages, but no protected standalone mutation-count/path invariant is declared today. |
| Recurrence drift | Runtime-lineage event `recurrence_key` counts aggregated by `build_runtime_lineage_summary(...)`. | `recurring_events` and "Top recurring recurrence keys" summary. | Longitudinal diagnostic evidence only; no expected baseline or comparison threshold exists. |

### Classified Structural Subtypes

The existing classifier additionally distinguishes structural/semantic ownership symptoms. These are not separate numeric thresholds; they identify likely fault locality after an invariant mismatch.

| Classifier Category | Example Source Fields | Severity Logic Already Present | Policy Interpretation |
|---|---|---|---|
| `route` | `route_kind`, `resolution_kind`, social route trace | High, or medium for missing route metadata | Blocking when the field is asserted by a protected scenario; otherwise diagnostic. |
| `speaker` | `selected_speaker_id`, speaker attribution evidence | Critical for dialogue/social, otherwise high | Blocking when protected speaker ownership is asserted. |
| `fallback` | fallback source/family/ownership fields | High | Blocking only for protected fallback/source/ownership invariants already declared. |
| `emission` / `validator` | response type repair, source, post-gate mutation | Medium/high | Blocking for existing protected response/final-source assertions; telemetry-only mutation remains non-blocking. |
| `continuity` | continuity/dialogue-lock evidence | High | Blocking where a protected scenario asserts observable continuity/speaker lock. |
| `sanitizer` | scaffold leakage and sanitizer-owned symptoms | Critical | Blocking for existing protected player-visible sanitizer invariants. |
| `projection` / `normalization` | missing/unavailable or view projection evidence | Medium/low | A missing required protected observation blocks its test; broader projection health is supporting evidence. |
| `replay_drift` | opt-in exact text or unmatched drift | Low for exact drift; otherwise medium | Non-blocking unless a specific protected assertion independently fails. |

## Current Enforcement Matrix

Important distinction: the classifier assigns severity after a failure is captured; it does not itself decide whether replay passes. Current acceptance is determined by pytest assertions in protected scenarios selected by `python -m pytest -m golden_replay -q`.

| Drift Type | Existing Protected Assertion Evidence | Current Enforcement | Details |
|---|---|---|---|
| Exact drift | None in protected scenario expectations; exact text is opt-in. | `classified only` / `reported only` when invoked | Hash mismatch support exists, but no general exact-prose acceptance gate exists. |
| Structural drift: route / speaker / canonical target | Asserted in protected end-to-end and direct-seam scenarios where relevant. | `already hard-fail` | A mismatching asserted field raises `AssertionError`; CI runs the marker lane as blocking. |
| Structural drift: final emission / response type | Asserted in directed, action-outcome, opening fallback, and lead-followup protections. | `already hard-fail` | Protected source/repair/invariant changes fail the scenario. |
| Semantic drift: scaffold/internal leakage | Asserted across protected scenarios, with dedicated sanitizer coverage. | `already hard-fail` | Player-visible scaffold leakage or forbidden internal terms fails existing assertions. |
| Semantic drift: useful action-outcome content | Protected by final-text exclusion checks plus a direct raw content assertion in `thin_answer_action_outcome_final_emission`. | `already hard-fail`, partially outside classified bridge | The acceptance condition exists; an adjacent raw `assert` may fail without being classified in the K3A report. |
| Fallback drift: protected source/family/timeframe | Opening fallback directly asserts family/timeframe/source; action/direct routing scenarios assert selected source constraints. | `already hard-fail` for asserted cases | Other fallback observations are not a blanket failure rule. |
| Fallback ownership drift | `opening_fallback_path` asserts canonical authorship and owner bucket, and companion raw assertions reinforce the same rule. | `already hard-fail` for opening ownership; otherwise `reported only` | No general all-fallback ownership threshold has been declared. |
| Sanitizer drift: scaffold / legacy rewrite constraints | Scaffold predicates are protected; legacy rewrite has raw protected assertions in sanitizer/action cases. | `already hard-fail` for asserted constraints; supporting lineage `observed only` | Raw legacy rewrite assertions are not translated by K3A classification reporting. |
| Gate-path drift | Runtime-lineage summary only. | `observed only` | No expectation or threshold compares gate-path frequencies. |
| Runtime-lineage drift | Runtime-lineage projection and summary only. | `reported only` / `observed only` | Existing test specifically establishes that lineage diagnostics do not change drift classification. |
| Mutation drift | Classifier/dashboard probes cover mutation locality; debug/report can display lineage. | `classified only` / `reported only` | Protected scenarios do not assert standalone mutation-path or mutation-count limits. |
| Recurrence drift | Runtime-lineage summary calculates recurring event counts. | `observed only` | No baseline, allowance, or failure interpretation exists. |

## Severity Classification

| Drift Category | Policy Class | Reason |
|---|---|---|
| Existing protected route, speaker, canonical-target, continuity/dialogue-lock, response-type, and final-emission invariant mismatch | `ACCEPTANCE_BLOCKING` | These are declared protected surfaces and already express deterministic allowed/disallowed states. |
| Existing protected fallback source/family/timeframe/ownership invariant mismatch | `ACCEPTANCE_BLOCKING` | Direct-seam protection exists specifically because plausible prose can hide incorrect final-emission ownership. |
| Existing protected scaffold leakage or prohibited internal-text appearance | `ACCEPTANCE_BLOCKING` | These are player-facing safety failures explicitly asserted in protected replay. |
| Existing protected required action-outcome usefulness constraint | `ACCEPTANCE_BLOCKING` | A generic or empty outcome defeats the declared action-outcome protection even when prose varies. |
| Exact normalized final-text mismatch | `REPORT_ONLY` | Exact prose is deliberately opt-in and the protected suite is designed around structural and predicate-level invariants. |
| Non-asserted fallback occurrence or fallback-family change seen only in telemetry | `WARNING` | It may reveal degradation, but fallback is valid in some canonical scenarios and must not be globally forbidden. |
| Non-asserted sanitizer lineage/change/empty-fallback evidence without player-visible violation | `WARNING` | It can indicate a repair-path shift, but the existing protected acceptance boundary is output/invariant based. |
| Standalone post-gate mutation or mutation-lineage evidence not violating a protected invariant | `WARNING` | Mutation may be legitimate; ownership is observable, but allowed-path policy has not been defined. |
| Gate-path frequency changes | `FUTURE_MONITORING` | Present only as lineage summary frequency data with no stable expected distribution. |
| Runtime-lineage event counts or mix | `FUTURE_MONITORING` | Provenance is diagnostic by design and explicitly does not affect classification alone. |
| Recurrence-key frequency changes | `FUTURE_MONITORING` | Requires repeated-run baselines and interpretation before any threshold is defensible. |
| Missing/normalized observation outside an existing required protected field | `REPORT_ONLY` | Projection health is important for diagnosability, but supporting instrumentation should not silently expand protected behavior. |

## Unsafe Threshold Candidates

| Candidate Threshold | Why Unsafe Now | Recommended Treatment |
|---|---|---|
| Any exact-text/hash mismatch fails replay | Prose equality is opt-in; golden replay intentionally protects structural/predicate outcomes instead of wording. | Keep `REPORT_ONLY`; use exact matching only for explicitly reviewed narrow cases. |
| Any fallback usage fails replay | Fallback is canonical in existing passing scenarios, including opening fallback and sanitizer/global-scene repair evidence in the baseline. | Block only mismatches of currently asserted fallback invariants; warn on unanticipated telemetry shifts. |
| Any sanitizer event, rewrite, or changed-count value fails replay | Sanitization can be a legitimate protection path; only player-visible leakage and specifically asserted legacy behavior have acceptance meaning today. | Warn/report lineage values; keep existing protected output constraints blocking. |
| Any mutation event or non-empty mutation lineage fails replay | Mutation source is classified, but the suite does not define which mutation paths are expected or forbidden generally. | Warn on observed drift; gather data before declaring allowed/denied mutation paths. |
| Gate-path frequency threshold | Summary counts exist only as diagnostic aggregates; there is no baseline distribution or stability evidence. | `FUTURE_MONITORING`. |
| Runtime-lineage count threshold | Runtime lineage is intentionally separate from drift classification, and event volume may change as observability improves. | `FUTURE_MONITORING`. |
| Recurrence count threshold | Recurrence is aggregated but not correlated to acceptance failure in the protected suite. | `FUTURE_MONITORING`; requires longitudinal review. |
| Global enforcement of all classifier `critical`/`high` rows | Classifier rows explain failed or probe-generated drift; supporting controlled failures intentionally produce high/critical classifications. | Gate only declared protected assertion failures, not taxonomy severity in isolation. |

## Recommended Initial Policy

There is no recommended new numeric threshold. The initial policy should formalize the existing deterministic boundary:

| Drift Type | Severity | Current Enforcement | Recommended Enforcement | Rationale |
|---|---|---|---|---|
| Protected structural invariant violation | `ACCEPTANCE_BLOCKING` | Hard-fail when asserted | Preserve hard-fail, zero violations allowed | It is the declared purpose of protected replay: routing, ownership, final emission, continuity, and repaired response contracts survive change. |
| Protected semantic/player-facing invariant violation | `ACCEPTANCE_BLOCKING` | Hard-fail when asserted | Preserve hard-fail, zero violations allowed | Scaffold leakage and lost required outcome meaning are direct acceptance failures. |
| Protected fallback ownership/source contract violation | `ACCEPTANCE_BLOCKING` | Hard-fail for declared opening/final-source checks | Preserve hard-fail, zero violations allowed for currently declared checks | Ownership metadata is explicitly why direct-seam protected replay exists. |
| Exact prose drift | `REPORT_ONLY` | Optional classifier evidence | Do not gate by default | Wording may vary without breaking protected behavior. |
| Unasserted fallback telemetry shift | `WARNING` | Report/debug evidence | Surface in artifact when accompanying a failure; do not independently fail | Existing passing scenarios legitimately use fallback paths. |
| Unasserted sanitizer lineage shift | `WARNING` | Report/debug evidence | Surface in artifact; do not independently fail | Output safety, not every internal sanitation event, is protected today. |
| Standalone mutation-path signal | `WARNING` | Classification/report tests only | Surface in report; defer standalone enforcement | Valid/invalid mutation paths have not been policy-separated. |
| Gate-path frequency | `FUTURE_MONITORING` | Runtime-lineage summary only | Collect before considering limits | No stable frequency baseline. |
| Runtime-lineage counts/mix | `FUTURE_MONITORING` | Runtime-lineage summary only | Collect before considering limits | Observability signal is not acceptance semantics. |
| Recurrence frequency | `FUTURE_MONITORING` | Runtime-lineage summary only | Collect before considering limits | Needs longitudinal evidence and fault correlation. |

Policy boundary:

- A protected assertion failure remains an acceptance failure even when its report classification is low or unavailable.
- A diagnostic classification, owner label, frequency, or lineage event does not become an acceptance failure unless it corresponds to an existing protected assertion.
- Existing raw protected assertions still block acceptance even if K3A does not classify them into the canonical failure artifact.

## Threshold Readiness Assessment

| Drift Category | Readiness | Evidence-Based Assessment |
|---|---|---|
| Protected route/speaker/target/continuity structural invariants | `Ready Now` | Explicit permitted values are already asserted in declared protected scenarios and enforced by CI. |
| Protected final-emission/response-type invariants | `Ready Now` | Expected source and repair constraints are directly asserted where acceptance requires them. |
| Protected opening fallback source/ownership/family/timeframe | `Ready Now` | Direct-seam protected assertions expressly own this boundary. |
| Protected scaffold leakage predicates | `Ready Now` | Player-facing leakage has a deterministic predicate and protected scenario coverage. |
| Protected action-outcome usefulness condition | `Ready Now` for existing assertions | The current text predicate/raw assertion is blocking; full structured classification coverage would improve artifacts, not policy. |
| Exact prose drift | `Needs More Data` | No evidence supports making wording identity a general acceptance requirement. |
| Broad fallback behavior beyond declared checks | `Needs More Data` | Canonical paths include legitimate fallback; unexpected and acceptable fallback frequency has not been separated. |
| Broad sanitizer lineage metrics | `Needs Better Instrumentation` | Individual fields are projected, but no reviewed allowed-event/allowed-count policy exists. |
| Mutation drift / post-gate mutation lineage | `Needs Better Instrumentation` | Locality can be reported, but the acceptable mutation set is not declared. |
| Gate-path frequency drift | `Needs More Data` | Aggregation exists; baseline distribution and repeatability evidence do not. |
| Runtime-lineage event drift | `Needs More Data` | Report is available, but diagnostics are intentionally classification-neutral. |
| Recurrence drift | `Needs More Data` | Counts exist without historical baselines or acceptance correlation. |
| Projection/normalization drift outside required protected fields | `Needs Better Instrumentation` | Instrumentation health can obscure diagnosis, but should not expand gameplay acceptance implicitly. |

## Recommended Future Expansion

1. Preserve the current zero-violation policy for existing protected assertions as the only required acceptance threshold.
2. Collect K3A/K3B failure reports and successful-run diagnostic evidence before proposing any fallback, mutation, gate-path, lineage, or recurrence count policy.
3. If a telemetry signal repeatedly corresponds to a user-visible protected failure, propose a new explicit invariant in a separately reviewed block rather than converting report frequency into a hidden gate.
4. Improve classification coverage for existing raw protected assertions only as an ergonomics enhancement; their current hard-fail acceptance meaning is already established.
5. Reserve exact prose checks for deliberately curated cases with a stated reason that text identity, rather than behavior, is required.

## Acceptance Criteria

| Criterion | Result |
|---|---|
| Drift inventory completed | Met: observable drift categories and origins are mapped above. |
| Enforcement matrix completed | Met: each requested drift type is mapped to current enforcement. |
| Severity policy defined | Met: a minimal Boolean acceptance policy and non-blocking diagnostic classes are specified. |
| Unsafe candidates identified | Met: unstable or ambiguous threshold candidates are explicitly deferred. |
| No replay behavior changed | Met: K4 adds this policy memo only. |
| No CI behavior changed | Met: K4 adds this policy memo only. |
| No production behavior changed | Met: K4 adds this policy memo only. |

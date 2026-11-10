# PR-PLAY-17 Findings

## Confirmed defects

The live opening integration produced an incompatible response: parseable legacy narration envelope instead of opening_presentation selected_entries. Native rejection arbitrary_narration_field, structured validation false, HTTP 422 and zero opening commits confirm a blocker to gameplay in this run. This is an observed opening-contract failure; it does not establish that renderer implementation or validators are defective. The guard correctly rejected the candidate. No deterministic authority breach was observed.

## Suspected defects

Competing legacy narration/schema instructions or incomplete provider contract alignment may explain the legacy envelope. This is a hypothesis only. Exact outgoing request messages/schema are not preserved here, and no causal reproduction was attempted.

## Non-defect limitations

Six requests cannot guarantee five ordinary turns; no exhaustion occurred. Structured presentation is acceptable. Loopback and readiness passed; prior network denial was not reproduced. Application's skipped-upstream-preflight banner is intentional harness configuration, not proof that the actual captured production request was synthetic. Offline controlled unwind is expected. The initial evidence-driver isolation-root mistake was rejected safely and corrected before worker startup.

## Evidence gaps

Exact provider HTTP status, raw outgoing messages, authorized catalog index and complete raw provider wire text are not captured. Bounded parsed candidate is present and untruncated. No selected catalog identifiers, accepted render trace, player-facing opening or ordinary-turn snapshots exist because opening failed. Pre-reset runtime snapshot was not separately captured; post-reset baseline and pinned provenance exist. Browser UI was not tested. Single-run evidence does not establish failure frequency or prompt root cause.

## Recommended investigations

Inspect the actual opening request's combined message instructions and response-format/schema selection against the opening_presentation contract, using offline evidence first. Preserve exact outgoing catalog/schema metadata in any separately authorized follow-up. Do not relax validation to accept arbitrary prose. No repair or further execution was performed in this pass.

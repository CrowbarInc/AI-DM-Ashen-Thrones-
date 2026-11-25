# pr_play_five_turn_live_model_probe

**Verdict: BLOCKED — live evaluation configuration was invalid.**

Five selected ordinary `/api/chat` turns were attempted once and returned HTTP 200.
Zero turns completed with a live model, zero provider requests occurred, zero tokens
were consumed, and estimated expenditure was $0.00/$5. No API error establishes
provider unavailability: authenticated availability was never tested.

The probe driver itself disabled interpretation unintentionally: after clearing
the disable flags, it called `discover_identity()`, which imports
`experiments.pr_dp`; that package sets `ASHEN_DISABLE_LIVE_INTERPRETATION=1` at
import. The driver did not recheck enablement after discovery. A1–A3 traces
explicitly record `skipped / live_interpretation_disabled`. A4 and B1 were stopped
even earlier by deterministic compound-action coverage. No model output exists.
This is an evaluation orchestration failure, not evidence of model failure.

The 11 offline request-budget/deadline checks passed, but they did not establish
live readiness. The readiness claim in preflight is withdrawn. No evidence here
validates the transport against an actual provider response. All five calls
preserved turn 4, scene, world, character and combat. Only conversational
publication/log context changed. Safe withholding is not gameplay execution.

The no-repeat/five-attempt stop boundary was honored despite the unused budget.
No production gameplay source or production data was changed, and no repairs,
commits, pushes, model substitutions, or remaining 15 cases were executed.
See CASE_RESULTS, FAILURE_ANALYSIS, PROVIDER_USAGE, and REGRESSION_RESULTS.

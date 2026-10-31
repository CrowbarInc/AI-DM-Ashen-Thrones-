# Diagnostic Classification

PR-PLAY-08 · 2026-10-29 America/New_York. Offline development tooling only.

Precedence: infrastructure/preflight/startup/transport/interruption first; then
proven state-integrity violation; admission rejection; provider exception; explicit
output-limit exhaustion; other incomplete provider response; empty content; JSON
parse failure; envelope/structured-validation failure; evidenced semantic rejection;
opening-acceptance rejection; UI failure if observed; unknown otherwise.

Output-limit exhaustion requires explicit provider evidence, not token-count
coincidence. `incomplete` plus `max_output_tokens` outranks a downstream parse error.
Successful structured validation plus semantic reasons is semantic-stage evidence.
A genuine safe nonresolution can be structurally valid and fail opening acceptance
without evidence of a failed semantic validator; H6 is classified at acceptance.

Each non-PASS report carries category, stage, record path, zero-based record index
when applicable, field, observed value and native source owner when available.
The provider journal remains the native diagnostic format. No provenance ID is
fabricated: harness run/scenario maps to the journal's actual run/opening/provider
attempt IDs, with missing-ID limitations explicit. Parser/outcome details are
reported independently. Classifications describe observations; root cause remains
`Not established`, with `inferred=false`. No hypothesis is promoted to a defect.

Missing required diagnostics prevents PASS. Unknown fields/stages remain unknown;
empty or failed evidence does not become a fabricated success. Browser status is
NOT_TESTED, not PASS. Failure categories do not alter replay taxonomy or evaluators.

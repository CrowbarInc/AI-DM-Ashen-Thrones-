# Narration recognizer excerpt

Source: `game/gm_resolution_decision.py`. Unmodified. Line numbers refer to the file at discovery time.

## `_CERTAINTY_UPGRADE_RE` (lines 477–481)

Matches `proves`, `establish`, `makes it clear`, `confirms`, `demonstrates`, `no doubt`, `now we know`, and the bare token `clearly`.

P3 initial and retry match this on “clearly”. “The split is clearly visible.” also matches.

## `_UNKNOWN_SLOT_RE` (lines 431–448)

Includes the alternative `\b(?:is|remains)\s+unclear\b`.

Does not include “is not clear”.

`_unsupported_narrator_lead` returns false when this matches, before the ungrounded-definite check. `_relationship_residual_claims` returns no causal, evidential, or certainty-upgrade claims when this matches.

## `_EPISTEMIC_PARENT_REALIZATION_RE` (lines 526–532)

Matches “is/remains/stays” plus “uncertain/unclear/unknown”, and “cannot be determined”.

Does not match “is not clear” or “is not something that can be determined”.

## `_unsupported_narrator_lead` (lines 1714–1739)

A might/could sentence with a definite-phrase token of five or more letters absent from the decision ground is an unsupported lead, unless the unknown-slot pattern already returned.

## Qualified-inference return (lines 2537–2558)

If the decision allows inference and the sentence matches `_QUALIFIED_INFERENCE_RE`, and it is not a generated or specific lead, the audit records an authorized inference and returns before residual causal reporting. An unsupported-lead claim appended just above still makes the sentence invalid.

# PR-BW narration-only envelope implementation

## A. Executive result
Implemented successfully for the bounded P2-like ordinary incidental dialogue path. Decision taxonomy: A — NARRATION-ONLY ENVELOPE READY FOR MICRO LIVE.

## B. Selection rule
The selector reads existing `gm_resolution_decision` / resolution-contract projection only. It selects narration-only exactly when `response_operation == incidental_dialogue`, `declaration_expectation == reply_not_required`, and consequential realization is not required.

## C. Authority ownership
The selector returns `projection_only: true` and `authority_owner: gm_resolution_decision`; it does not create a second authority object or classifier.

## D. Provider contract
```text
NARRATION-ONLY RESPONSE CONTRACT: Return valid JSON only in this exact shape: {"narration": "player-facing response"}. Do not include other fields. The application will normalize this internally.
```

## E. Canonical normalization
Provider output `{"narration": "..."}` normalizes at the parser boundary to canonical internal `declared_claims: []` plus unchanged narration.

## F. Parser behavior
Narration-only accepts only the single `narration` string field. Missing narration, wrong type, malformed JSON, and unexpected `declared_claims` are rejected safely.

## G. P2
P2 selects narration-only because existing authority says ordinary incidental dialogue with reply not required as declaration.

## H. P1
P1 remains structured because bounded interpretation may need declaration/inference capability.

## I. P3
P3 remains structured intentionally; player-hypothesis discussion is not migrated in this cycle.

## J. Consequential control
Consequential NPC/world realization remains structured and declaration-capable.

## K. Generalization controls
G1 and G2 select narration-only. G3, G4, G5, G6, and consequential control remain structured.

## L. Retry behavior
Narration-only structured-contract failures carry `provider_response_contract: narration_only`; regeneration feedback asks for the same single-field shape.

## M. Provider payload size
| Probe | Pre-PR-BW Provider Chars | Post-PR-BW Provider Chars | Net | Declaration Channel Exposed? |
| ----- | -----------------------: | ------------------------: | --: | ---------------------------- |
| P1 | 98442 | 98442 | 0 | Yes |
| P2 | 111060 | 105662 | -5398 | No |
| P3 | 100389 | 100389 | 0 | Yes |

Narration-only envelope chars: 195.

## N. Declaration-affordance reduction
P2 response-envelope declaration-specific chars before: 192. After: 0. The declaration channel is absent from the P2 provider response contract. Some declaration vocabulary remains in decision-facing answer recipe fields inherited from PR-BV; that is outside the response envelope and remains projection-only guidance.

## O. State/provenance behavior
Normalization creates no model-authored declaration, no world fact, no provenance record, and no consequential claim.

## P. C18
Parser-level deterministic normalization preserves a single emitted narration string. Prior P2 C18 evidence remains accepted == sealed == emitted; no live/API replay was run in this cycle.

## Q. Focused tests
```text
..........................                                               [100%]
```

## R. Broad regression
Broader deterministic slice passed:

```text
........................................................................ [ 45%]
........................................................................ [ 91%]
..............                                                           [100%]
```

Covered PR-BW, PR-BV, PR-BS, PR-BU narration/declaration validation, PR-BR GM resolution decision, structured realization envelope, and GM retry context tests. `tests/test_pr_br_structured_chat_path.py` was also attempted separately but hung after one passing dot and was interrupted; no failure output was produced.

## S. Known failures
The obsolete PR-BT >=12,000 chars saved threshold was not targeted.

## T. Architecture status
PR-BR closed; PR-BU closed; PR-BT paused/BT-C; PR-BV preserved; PR-BW implemented as first bounded mode-specific envelope.

## U. Live readiness
Yes for controlled P1/P2/P3 micro live gate. This implementation targets the structural cause of the prior approximately 26,142 input-token P2 retry; it does not claim live retry elimination yet.

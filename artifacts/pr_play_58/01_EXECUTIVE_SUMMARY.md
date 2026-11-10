# PR-PLAY-58 — C — FAIL / REMEDIATION REQUIRED

Bounded semantic coverage improves the eight original PR-PLAY-57 samples from 4/8 to 8/8 covered. Combined decisions improve from 4 PASS / 1 FAIL / 3 REVIEW_REQUIRED to 7 PASS / 1 FAIL. A1 remains rejected for the unsupported "new, urgent update" discovery. Exact UTF-8 provider text and authority are preserved; all archived previous combined decisions reproduce.

The single frozen holdout pass finds a critical false acceptance: H41 appends "The gate is now permanently open." to the authorized patrol fact and receives PASS. This is an unsupported persistent consequence. Implementation remains frozen after evaluation; no holdout tuning or rerun occurred. A safe player-facing experiment is not authorized.

Development: 43 cases; legitimate combined acceptance 14/15 (coverage 15/15); omissions blocked 6/6; contradictions blocked 11/11; expansions rejected 9/9; ambiguous review 2/2. Zero critical false acceptances; one legacy false rejection; 18 reviews.

Holdout: 50 cases; legitimate acceptance 14/15; omissions blocked 10/10; contradictions blocked 10/10; expansions rejected 9/10; ambiguous review 5/5. One critical false acceptance, one false rejection, 25 reviews, zero validation errors. Most contradictions are quarantined for review, not explicitly rejected; exact confusion matrices remain available. Same-session authored holdout is not independent blind validation.

Warmed coverage: 0.214 ms average / 0.713 ms maximum. Combined: 4.399 / 128.673 ms. 800 measurements per series during local regression activity. Zero provider requests / tokens.

Regression: 601 passed / 3 failed / 0 errors / 0 skipped of 604 focused cases. Final-source checks: 204 passed of 204. PR55 holdout wrapper and known broader results are recorded separately. No campaign state, deterministic response, quarantine gate, protected fixture, commit or push change.

Primary next step: repair the unsupported persistent-consequence detection gap exposed by H41 in a subsequent bounded validation cycle. Preserve this failed holdout and quarantine.

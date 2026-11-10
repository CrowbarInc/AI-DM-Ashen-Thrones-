# 09 FROZEN HOLDOUT

Frozen before implementation: 40 cases (10 authorized discovery, 10 unauthorized expansion, 5 observation, 5 item acquisition, 5 prior context, 5 mandatory disclosure). Input hash: `9f95abb1cbc14e097db197561c74bcfa275caf0421b333bce0b0f5a63b341bb9`. Fixtures, decisions, coverage expectations and publication behavior remain byte-identical.

Executed once after source freeze. Final decisions: 40/40 correct. Publication choices: 40/40 correct. Full frozen expectations: 39/40. H18 appends a southeast contradiction to the authorized northwest report; FAIL was expected and observed, while coverage was frozen as PASS but correctly returned REVIEW_REQUIRED. No expected value or code was altered after evaluation.

False acceptances: 0. False rejections: 0. Critical false acceptances: 0. Every fallback validates. This developer-authored holdout is not independent blind validation. `holdout_results.json` includes all traces.

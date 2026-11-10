# Negative controls

Development: 6/6 omissions, 11/11 contradictions and 9/9 expansions blocked; 0 critical false acceptances. Holdout: 10/10 omissions, 10/10 contradictions and 9/10 expansions blocked; 1 critical false acceptance (H41). Blocking is not the same as confirmed FAIL: most contradictions remain REVIEW_REQUIRED. Exact expected→actual confusion is in metrics.json.

Controls cover complete/partial omission, wrong subject/location/direction/time, mechanical outcome, unauthorized certainty/discovery/items/NPC knowledge, first-time repeat, persistent consequences and authorized fact plus fabrication. Harmless environmental texture is in positive controls.

| Case | Category | Expected | Combined | Coverage | Consequential |
|---|---|---|---|---|---|
| D16 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D17 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D18 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D19 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D20 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D21 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D22 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D23 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D24 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D25 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D26 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D27 | contradictory | FAIL | FAIL | REVIEW_REQUIRED | FAIL |
| D28 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D29 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D30 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D31 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D32 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| D33 | expansion | FAIL | FAIL | PASS | FAIL |
| D34 | expansion | FAIL | FAIL | PASS | FAIL |
| D35 | expansion | FAIL | FAIL | PASS | FAIL |
| D36 | expansion | FAIL | FAIL | PASS | FAIL |
| D37 | expansion | FAIL | FAIL | PASS | PASS |
| D38 | expansion | FAIL | FAIL | PASS | FAIL |
| D39 | expansion | FAIL | FAIL | PASS | FAIL |
| D40 | expansion | FAIL | FAIL | PASS | FAIL |
| D41 | expansion | FAIL | FAIL | REVIEW_REQUIRED | FAIL |

H41: "The missing patrol was last seen taking the northwest mud track past the crates. The gate is now permanently open." Coverage PASS, semantic PASS, legacy hard-valid, combined PASS. This result forbids a successful cycle verdict.

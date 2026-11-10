# Frozen holdout — one pass

50 cases were authored and SHA-256 frozen before implementation changes: 15 legitimate, 10 missing, 10 contradictory, 10 expansion, 5 ambiguous. Hash: 618cc1fc6c4a468c8668ce808223059c554a751a82eba1d8511bbb34e571227b. The manifest contains full authority and mandatory facts through references to holdout.json. Implementation hashes were frozen before evaluation and remain unchanged. Durable start marker prevents a second execution. This is same-session authoring, not fully independent blind validation.

Acceptance 14/15; omissions blocked 10/10; contradictions blocked 10/10; expansions rejected 9/10; ambiguous reviewed 5/5. Critical acceptance H41 and false rejection H12 remain unchanged. 25 REVIEW_REQUIRED, 0 VALIDATION_ERROR.

| Case | Category | Expected | Combined | Coverage | Consequential |
|---|---|---|---|---|---|
| H01 | legitimate | PASS | PASS | PASS | PASS |
| H02 | legitimate | PASS | PASS | PASS | PASS |
| H03 | legitimate | PASS | PASS | PASS | PASS |
| H04 | legitimate | PASS | PASS | PASS | PASS |
| H05 | legitimate | PASS | PASS | PASS | PASS |
| H06 | legitimate | PASS | PASS | PASS | PASS |
| H07 | legitimate | PASS | PASS | PASS | PASS |
| H08 | legitimate | PASS | PASS | PASS | PASS |
| H09 | legitimate | PASS | PASS | PASS | PASS |
| H10 | legitimate | PASS | PASS | PASS | PASS |
| H11 | legitimate | PASS | PASS | PASS | PASS |
| H12 | legitimate | PASS | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H13 | legitimate | PASS | PASS | PASS | PASS |
| H14 | legitimate | PASS | PASS | PASS | PASS |
| H15 | legitimate | PASS | PASS | PASS | PASS |
| H16 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H17 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H18 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H19 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H20 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H21 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H22 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H23 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H24 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H25 | missing | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H26 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H27 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H28 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H29 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H30 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H31 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H32 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H33 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H34 | contradictory | FAIL | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H35 | contradictory | FAIL | FAIL | REVIEW_REQUIRED | FAIL |
| H36 | expansion | FAIL | FAIL | PASS | FAIL |
| H37 | expansion | FAIL | FAIL | PASS | FAIL |
| H38 | expansion | FAIL | FAIL | PASS | FAIL |
| H39 | expansion | FAIL | FAIL | PASS | FAIL |
| H40 | expansion | FAIL | FAIL | PASS | PASS |
| H41 | expansion | FAIL | PASS | PASS | PASS |
| H42 | expansion | FAIL | FAIL | PASS | FAIL |
| H43 | expansion | FAIL | FAIL | PASS | FAIL |
| H44 | expansion | FAIL | FAIL | REVIEW_REQUIRED | PASS |
| H45 | expansion | FAIL | FAIL | REVIEW_REQUIRED | PASS |
| H46 | ambiguous | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H47 | ambiguous | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H48 | ambiguous | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H49 | ambiguous | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |
| H50 | ambiguous | REVIEW_REQUIRED | REVIEW_REQUIRED | REVIEW_REQUIRED | PASS |

No holdout failure led to implementation edits or rerun. Generalization is incomplete and a critical gate-consequence gap remains.

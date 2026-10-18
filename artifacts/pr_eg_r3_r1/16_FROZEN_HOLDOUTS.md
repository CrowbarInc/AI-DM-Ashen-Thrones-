# 16 — Frozen Holdouts

`frozen_holdouts.json` sha256 `e0b2d9785d3ac142a401125968aca0e713700d097bc315644324a3b8876b9a32`. Freeze record: `e0b2d9785d3ac142a401125968aca0e713700d097bc315644324a3b8876b9a32` at stage "before qualification tuning". Match: True.

The file was hashed before qualification tuning and was not edited afterward. The confirming suite includes `test_frozen_holdout` for each id. Holdout ids: R1H01, R1H02, R1H03, R1H04, R1H05, R1H06, R1H07, R1H08, R1H09, R1H10.

| Id | Kind | Expectation |
| --- | --- | --- |
| R1H01 | characterization | adopt |
| R1H02 | characterization | reject |
| R1H03 | paraphrase | adopt |
| R1H04 | paraphrase | reject |
| R1H05 | alias | adopt |
| R1H06 | rumor | reject |
| R1H07 | partial | partial |
| R1H08 | equivalent | same_proposition |
| R1H09 | distinct | ambiguous |
| R1H10 | exact | exact |

R1H01 adopts a dawn explanation for Warden Ivo. R1H02 rejects a captain and an unattended harbor. R1H03 adopts a south-road paraphrase. R1H04 rejects "south street". R1H05 adopts a declared harbour-road alias. R1H06 keeps a rumor hedge. R1H07 requires the west-gate sentry fact plus a limit. R1H08 groups two south-road wordings. R1H09 keeps two different roads ambiguous. R1H10 recalls the sentry sentence exactly and forbids "unattended".

The live plan is a separate freeze. The preserved first plan sha256 is `{first_plan_hash}`. The final plan sha256 is `{plan_hash}`, matching `live_freeze.json` stage "before fresh provider qualification". The final plan was frozen before the final provider run. It was not edited after the results.

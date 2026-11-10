# Frozen Supplemental Holdout

Developer-authored validation. It is not independent external generalization evidence.

Manifest: `tests/fixtures/pr_play_79df3_holdout.json`. SHA-256 `917d67fd5b997699d850311dfe4b405933f8c4b84989c39f5dfbdfdf8c3f6945`, also stored in `tests/fixtures/pr_play_79df3_holdout.sha256`. The manifest was frozen before the scored run and was not edited afterward.

Scored once: `artifacts/pr_play_79df3/holdout_results.jsonl`. **28 passed, 0 failed.** An earlier harness run that failed H05 on a missing directory and H17 on a canary stored in seed notes was not scored. That file is `holdout_results_unscored_harness.jsonl`. The runner was corrected. The manifest and its hash were not changed, and the holdout was not retuned.

| Case | Expected class |
| --- | --- |
| H01 request ceiling | Operational admission refusal |
| H02 input ceiling | Operational admission refusal |
| H03 output ceiling | Operational admission refusal |
| H04 total ceiling | Operational admission refusal |
| H05 accounting unavailable | Operational admission refusal |
| H06 playtest stop | Operational admission refusal |
| H07 token estimate | Operational admission refusal |
| H08 provider exception | Operational interpretation-service refusal |
| H09 model mismatch | Operational interpretation-service refusal |
| H10 malformed output | Gameplay |
| H11 context leak | Gameplay |
| H12 clarification | Gameplay |
| H13 unsupported action | Gameplay |
| H14 accepted dialogue | Completed gameplay |
| H15 grounded fallback | Completed gameplay |
| H16 physical narration | Completed gameplay |
| H17 repeat investigation | Completed gameplay, disclosed fact only |
| H18 continuation after refusal | Pointer advances on the gameplay turn |
| H19 save/reload | Pointer stays on the pre-refusal publication |
| H20 cross-campaign | Other campaign store unchanged |
| H21 projection | Safe sentence, class not in the player body |
| H22 duplicate | No extra gameplay event |
| H23 server error | Error category, not a gameplay publication |
| H24 no turn on refusal | Turn unchanged |
| H25 hidden information | Canary absent from player text |
| H26 zero retries | No retry after provider failure |
| H27 transcript class | Log class is operational |
| H28 stillness | Absence of mutation is not operational |

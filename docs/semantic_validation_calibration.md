# Semantic Validation Calibration

## Previous Problem

The prior playability evaluator treated the aggregate diagnostic score as the effective pass/fail authority. That allowed severe player-facing semantic failures to pass when stronger heuristic axes compensated for a failed axis.

Observed examples from `artifacts/simulated_playtest_observability/20260917T221002Z_*` included:

- `Who commands the watch here?` -> `Tavern Runner mutters, the tavern runner replies, voice steady amid the murmur of the crowd.` reported `PASS` with `player_intent` failed.
- `Who stole the relic from the chapel?` -> `Tavern Runner says, "No. I cannot answer that from what."` reported `PASS`.
- `I press again: what is actually posted on the notice?` -> `Tavern Runner mutters,` reported `PASS`.
- `I glance at the notice.` -> a redirection to `"Board, runner, or road"` reported `PASS`.

Those are not gameplay repairs in this campaign. They are calibration evidence that the measuring instrument was not yet trustworthy.

## Calibration Corpus

The versioned corpus lives under `data/validation/semantic_calibration/`.

- `manifest.json` lists the corpus id, result states, and every case file.
- `cases/*.json` stores stable case ids, category, player input, prior context where relevant, GM response, expected semantic result, expected mandatory gate results, rationale, provenance, and synthetic/runtime provenance flags.
- The four known-bad examples are preserved as real runtime failures with artifact paths and turn indexes.
- Positive and boundary examples cover valid uncertainty, NPC ignorance, refusal, terse dialogue, terse observation, ambiguity clarification, partial answer, diegetic redirection, and intentional fragments.

## Semantic Result Model

`game.playability_eval` now distinguishes these result states:

- `PASS`: the semantic authority checked the required conditions and found no mandatory failure.
- `FAIL`: a mandatory semantic gate failed, or diagnostic quality fell below the retained aggregate threshold.
- `UNCHECKED`: reserved for a required semantic condition that could not run; it is not represented as pass.
- `NOT_APPLICABLE`: a condition genuinely does not apply to the turn.
- `INVALID_RUN`: gameplay/runtime validation says the run is not valid evidence; this is distinct from semantic failure.

`overall.passed` is now derived from `semantic_result == "PASS"`. Diagnostic quality remains available separately as `diagnostic_quality`.

## Mandatory Gates

### malformed_output

Detects high-confidence conversation-breaking output:

- missing player-facing text
- dangling speech attribution such as `Tavern Runner mutters,`
- trailing comma speech construction
- unfinished quotation
- malformed refusal fragments such as `I cannot answer that from what.`
- explicit final-emission truncation evidence where present

It deliberately does not use a minimum word count, so `No.`, `Yes.`, and intentional fragments can pass.

### player_intent_addressed

Detects whether an intelligible player request was meaningfully addressed. It allows:

- direct answers
- coherent uncertainty
- NPC ignorance
- refusal
- appropriate clarification
- terse yes/no answers
- partial answers with a knowledge boundary
- observation fulfillment before diegetic redirection
- context-complete sensory fragments

It fails when a clear question or observation is effectively ignored or lost.

## Known-Bad Before/After

Before evidence comes from `artifacts/simulated_playtest_observability/20260917T221002Z_*`.

| Case | Before | After in Calibration |
| --- | --- | --- |
| Unanswered direct question | `PASS`, score 69, `player_intent` 9/25 | `FAIL`, `player_intent_addressed=FAIL` |
| Broken refusal/non-answer | `PASS`, score 67 | `FAIL`, `malformed_output=FAIL`, `player_intent_addressed=FAIL` |
| Truncated output | `PASS`, score 67 | `FAIL`, `malformed_output=FAIL`, `player_intent_addressed=FAIL` |
| Observation not fulfilled | `PASS`, score 75 | `FAIL`, `player_intent_addressed=FAIL` |

Fresh live scenario artifacts were also generated under `artifacts/semantic_validation_calibration/playability_after/20260918T011644Z_*`. The exact historical strings did not all recur, but the new artifacts expose `semantic_result`, `mandatory_gates`, `diagnostic_quality`, and axis diagnostics. In the fresh `p1_direct_answer` run, unanswered questions now report `semantic_result: FAIL` even where diagnostic quality remains acceptable.

## Positive Boundary Cases

The corpus and tests protect against simplistic hard failures. These all pass mandatory gates:

- `You don't know. Nothing you've learned so far identifies the killer.`
- `The stablehand shakes his head. "Couldn't tell you. I wasn't there."`
- `"I'm not telling you that," Veyra says, folding her arms.`
- `No.`
- `Yes.`
- `Which one are you checking: the door, the notice, or the satchel?`
- `No one can name the order-giver yet, but the dock factor paid the alley crew before the strike.`
- Notice content followed by diegetic redirection.
- `"Footsteps. Then silence."`

## Calibration Results

Generated report:

- JSON: `artifacts/semantic_validation_calibration/calibration_report.json`
- Markdown: `artifacts/semantic_validation_calibration/calibration_report.md`

Result:

- Cases: 13
- Agreements: 13
- Disagreements: 0

## Regression Results

Focused campaign command:

`$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_playability_eval.py tests\\test_semantic_calibration_corpus.py tests\\test_run_playability_validation_tool.py tests\\test_playability_smoke.py -q`

Result: `34 passed`, with one existing Starlette deprecation warning from `fastapi.testclient`.

Calibration command:

`$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' tools\\run_semantic_calibration.py`

Result: wrote calibration JSON and Markdown reports; exit code 0.

Playability after-artifact command:

`$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' tools\\run_playability_validation.py --all --artifact-dir artifacts\\semantic_validation_calibration\\playability_after`

Result: wrote after-run artifacts for all four fixed scenarios under `artifacts/semantic_validation_calibration/playability_after/20260918T011644Z_*`.

Full-suite command:

`$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest -q`

Result: failed. The pytest output listed 49 failing tests. The focused semantic calibration tests remained green; the full-suite failures were in existing attribution/governance, missing closeout docs, replay/projection artifacts, final-emission integrity, social lead, and validation-layer import governance areas. Representative failing modules included:

- `tests/test_attribution_contract.py`
- `tests/test_attribution_regression_guard.py`
- `tests/test_bw_protected_replay_trend_window_closeout.py`
- `tests/test_bz_protected_replay_trend_window_2_closeout.py`
- `tests/test_failure_classification_contract.py`
- `tests/test_golden_replay_*`
- `tests/test_replacement_attribution_inventory.py`
- `tests/test_scene_destination_binding.py`
- `tests/test_social_destination_redirect_leads.py`
- `tests/test_validation_layer_closeout.py`

These failures match the already-known red full-suite baseline pattern from the reliability audit and were not repaired in this campaign.

## Artifact Changes

`evaluation.json`, `summary.json`, and `transcript.md` produced by `tools/run_playability_validation.py` now expose:

- `semantic_result`
- `mandatory_gates`
- gate statuses and reason codes
- `diagnostic_quality`
- preserved diagnostic axis scores
- gameplay invalidation data

The transcript result section names semantic authority before diagnostics so a human no longer has to infer that `player_intent 9/25` should override an aggregate acceptable rating.

## Remaining Blind Spots

This is a deterministic calibration layer, not a full semantic reasoner. It is intentionally strongest around the foundational failures and boundary examples. It can still miss failures that require deeper world-state reasoning, hidden-fact consistency, nuanced NPC knowledge modeling, or long-range discourse tracking.

The `player_intent_addressed` gate is inspectable and testable, but it remains heuristic. If future reactive or adversarial simulated players expose subtler failures, the calibration corpus should grow before hardening new gates.

## Next Recommendation

The evaluator is more trustworthy for the known foundational failures and matched positives. The next proposed validation stage, Reactive and Adversarial Simulated Players, is reasonable to consider only after human review of this corpus, report, and after-artifacts.

Do not implement reactive players in this campaign.

# Reactive and Adversarial Simulated Players

## Purpose and boundary

This campaign adds bounded, reproducible simulated players that choose later actions from prior GM
output and calibrated evaluator evidence. It is an offline validation/observability layer. It does not
repair GM output, alter runtime prompts, add semantic gates, or feed evaluator results into gameplay.

The pre-implementation inventory is in `docs/reactive_adversarial_simulation_inventory.md`.

## Architecture

- `tests/helpers/reactive_player.py` owns the pure deterministic policy. It consumes a scenario,
  strategy, seed, bounded state, prior GM text, and prior evaluator result, then returns a player
  action plus an auditable rationale or a stopping decision.
- `tools/run_reactive_player_validation.py` owns execution through the existing `/api/chat` seam,
  invokes `game.playability_eval.evaluate_playability` per turn, and writes run/campaign artifacts.
- Production gameplay code does not import the synthetic player.
- Per-run JSON preserves configuration, objective/current intent, selected action, rationale, prior
  context, GM response, semantic result, mandatory gates, diagnostic quality, runtime validity,
  final-emission metadata, classification, and termination reason.

## Strategies

`reactive` follows up on incomplete answers, asks for specificity, rephrases unresolved questions,
persists on unfulfilled observations, and returns to unresolved objectives.

`adversarial` adds bounded contradiction, established-fact, NPC-knowledge, return-to-topic, and
degradation probes after satisfactory responses. Probe ordering is deterministic for scenario, seed,
and turn index. The probes are plausible difficult-player utterances, not fuzz strings.

Scenario-specific acceptance markers prevent a lexically plausible PASS from ending an objective when
the expected observation or factual shape is absent. Coherent uncertainty, ignorance, refusal, and
redirection terminate pressure even when the current heuristic evaluator disagrees; that disagreement
is preserved as false-positive evidence.

## Stopping rules

- Maximum turns: six per shipped scenario.
- Maximum attempts on one unresolved intent: three.
- Stop on objective resolution with scenario evidence.
- Stop on recognized legitimate uncertainty, ignorance, refusal, or redirection.
- Stop on `INVALID_RUN` or `UNCHECKED` evaluation.
- Stop when per-intent attempts are exhausted.
- All selection and stopping rules are deterministic for recorded inputs and seed.

## Reproducibility

Player selection is deterministic. Live GM/model output may not be, so every run records enough data
to reconstruct the decision path instead of concealing nondeterminism in aggregate counts. The CLI
accepts explicit scenarios, strategies, and repeatable integer seeds. Runtime state is reset before
each run unless `--no-reset` is deliberately supplied.

## Representative runs

The primary post-implementation campaign is
`artifacts/reactive_adversarial_players/20260918T021838Z/`:

- 6 runs: three scenarios times reactive/adversarial strategy, seed 1701.
- 6 valid runs, 0 invalid runs, 17 turns.
- Semantic results: 6 PASS, 11 FAIL, 0 UNCHECKED, 0 INVALID_RUN.
- Mandatory failures: 11 `player_intent_addressed`, 3 `malformed_output`.
- Diagnostic-only warnings: 0.

A focused acceptance/false-positive confirmation is
`artifacts/reactive_adversarial_players/20260918T022209Z/`: one valid adversarial patrol run that
terminated immediately on a coherent refusal.

## Human-reviewed findings

Full reviewed classifications are preserved in
`artifacts/reactive_adversarial_players/human_review.json` and point to exact run/turn evidence.

- A: unanswered watch-command questions persist through narrower wording, rephrasing, and explicit
  return-to-topic pressure. The evaluator correctly detects all eight failures across both strategies.
- A: patrol pressure reproduces the known broken refusal and a truncated speech construction. Existing
  mandatory gates detect both.
- B: after a valid notice answer, the GM answers a visual legibility clarification with irrelevant NPC
  ignorance. The evaluator returns PASS. This is conceptually related to the existing observation
  calibration case, so it is not counted as a novel failure.
- C: `Tavern Runner grimaces. "Not something I can say here."` is a coherent diegetic refusal but is
  scored FAIL. This is a novel wording boundary and a candidate for later human calibration.
- E: one notice response includes the requested categories but is grammatically degraded and mixed
  with unrelated pressure. It remains ambiguous rather than becoming a new rule.
- D: no infrastructure/invalid runs occurred in the reviewed campaigns.

No discovered gameplay defect was repaired. No evaluator miss or suspected false positive was
converted into a semantic rule.

## Tests

Focused regression coverage is in `tests/test_reactive_player_validation.py`. It covers reactive
follow-up, bounded attempts, legitimate acceptance, evaluator-disagreed refusal acceptance,
observation persistence after a semantic PASS without scenario evidence, seeded adversarial probes,
rephrasing, unresolved-objective persistence, artifact schema, classifications, termination reasons,
and invalid-run stopping. `tests/test_semantic_calibration_corpus.py` protects all 13 accepted cases.

Verification on 2026-09-17 (America/New_York):

- Focused campaign/playability/calibration suite: 47 passed, 0 failed; one existing Starlette
  `TestClient` deprecation warning.
- Full suite: 49 failed. This matches the known pre-campaign red baseline count and failure families:
  attribution/governance inventories, missing BW/BZ closeout documents, replay/projection drift,
  final-emission ownership/import guards, social-lead expectations, scene fallback behavior, and
  validation-layer separation. No failure names the new reactive-player helper, runner, tests, or
  artifacts. Those historical failures were not repaired in this campaign.

## Known limitations

- Scenario evidence markers are deliberately narrow and scenario-authored; they are player-policy
  controls, not semantic truth rules.
- The policy sees the immediate prior response and retained objective state, not a learned discourse
  model.
- Deep world contradictions, hidden-fact consistency, and nuanced NPC knowledge still require human
  review.
- Machine classification is conservative: FAIL maps to A and PASS remains E until reviewed. Human B/C
  classifications live in the separate review artifact and do not mutate evaluator output.
- Live model output remains nondeterministic even though player decisions are replayable from preserved
  evidence.

## Recommended next stage

Run a human-reviewed semantic calibration campaign for the preserved concise-refusal false positive
and visual-observation/NPC-ignorance miss. Decide whether either deserves a narrowly labeled corpus
case before changing evaluator policy. Do not begin gameplay repair until that calibration decision is
complete.

# Reactive and Adversarial Simulation Inventory

This inventory was completed before implementation of the reactive/adversarial campaign. The
campaign is validation and observability only. It must not alter GM behavior, runtime prompts, or
the calibrated semantic policy.

## Existing simulation lanes

### Fixed playability scenarios

- `tools/run_playability_validation.py` owns four fixed scenarios (`p1` through `p4`).
- Each scenario is a tuple of predetermined player prompts sent through `POST /api/chat`.
- `run_scenario(...)` resets the campaign by default, calls the chat seam once per prompt, extracts
  `gm_output.player_facing_text`, and invokes `game.playability_eval.evaluate_playability(...)` per
  turn.
- The evaluator receives the immediately previous player and GM text. The fixed runner does not use
  that context to choose the next player prompt.
- Runtime validity, dead-turn visibility, narrative-authenticity telemetry, final-emission metadata,
  and before/after persisted-state snapshots are preserved in its artifacts.
- The final scenario summary mirrors the final turn evaluation plus run-level validity reports; it is
  not a session-semantic aggregate.

### Synthetic-player harness

- `tests/helpers/synthetic_types.py` defines seeded profiles, turn views, decisions, and run results.
- `tests/helpers/synthetic_policy.py` chooses deterministic template utterances from profile weights,
  seed, and turn index. Its current policy explicitly ignores the prior GM snapshot.
- `tests/helpers/synthetic_runner.py` executes policy decisions through either a deterministic fake GM
  or the transcript/chat path. It exposes the most recent snapshot to the next `SyntheticTurnView`,
  supports policy-requested stopping, maximum turns, external stopping, and a repeated-text stall
  threshold.
- `tests/helpers/synthetic_scenarios.py` contains reusable seeded scenario/profile presets. Some have a
  fixed opening followed by policy turns; these are not semantically reactive today.
- `tools/run_synthetic_session.py` is a console-oriented exploratory wrapper. It prints rationale and
  a compact summary but does not write a traceable campaign artifact set or call the calibrated
  playability evaluator.

### Longer-session and replay lanes

- Scenario-spine runners evaluate continuity and branch health as a separate contract.
- Golden/protected replay helpers preserve established runtime evidence and governance projections.
- Behavioral-gauntlet helpers own shallow regression assertions, not canonical playability scoring.
- These lanes are evidence neighbors, but none should become a second semantic authority for this
  campaign.

## Prompt selection and context

- Fixed playability prompts are selected by tuple position only.
- Synthetic prompts are selected by a process-stable mixed seed, profile weights, turn index, and
  prior player text (used only to avoid an exact immediate repeat).
- The synthetic runner makes the previous raw snapshot available to policy code, including GM text,
  but the current placeholder policy does not inspect it.
- The playability runner supplies one prior player/GM pair to the evaluator. Full transcript context is
  available in runner memory and artifacts, not in the deterministic evaluator input contract.

## Artifact and evaluation ownership

- Canonical semantic evaluation remains `game.playability_eval.evaluate_playability`.
- Mandatory gates remain `malformed_output` and `player_intent_addressed`; diagnostic quality cannot
  compensate for a mandatory failure.
- `tools/run_playability_validation.py` writes transcript, evaluation, summary, metadata, runtime
  validity, final-emission telemetry, and persisted state artifacts.
- Semantic calibration lives under `data/validation/semantic_calibration/` and is exercised by
  `tools/run_semantic_calibration.py` and `tests/test_semantic_calibration_corpus.py`.

## Determinism and replay facilities

- Synthetic policy choice is deterministic for profile, seed, and turn index; it avoids Python's
  process-randomized `hash()`.
- Fixed playability scenarios record no player-policy seed because their prompts are literal.
- Runtime/model responses may still be nondeterministic. Reconstructable evidence therefore requires
  preserving every selected action, rationale, prior context, GM response, evaluator result, runtime
  validity signal, and stopping decision rather than reporting only aggregates.

## Architectural boundaries for this campaign

- Extend harness/tooling code; do not import synthetic-player policy into production runtime modules.
- Send player actions through the existing chat seam and use existing campaign reset behavior.
- Treat playability evaluation as offline observation only; never feed its verdict into GM generation
  or repair.
- Preserve `INVALID_RUN` separately from gameplay failure.
- Do not add or weaken mandatory semantic gates in this campaign.
- Do not modify scenario-spine, replay-governance, final-emission, or gameplay ownership contracts.
- Classification of evaluator misses, false positives, and ambiguous cases is review evidence, not an
  automatic semantic-policy update.

## Extension decision

The campaign will add a GM-output-aware policy beside the existing synthetic policy and a dedicated
artifact-producing runner beside the fixed playability CLI. It will reuse synthetic profile/decision
types, the existing `/api/chat` execution seam, campaign reset, calibrated evaluator, and runtime
validity projections. This keeps reactive selection out of gameplay code and avoids a parallel game
simulation system.

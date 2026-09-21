# Simulated Playtest Observability Audit

Generated from repository inspection and the live playability run:
`artifacts/simulated_playtest_observability/20260917T221002Z_*`.

## Existing simulated-player architecture

The clearest existing simulated-player lane is `tools/run_playability_validation.py`.
It defines four `PlayabilityScenario` fixtures in code. Each fixture supplies a fixed
tuple of natural-language player prompts. The runner optionally calls
`apply_new_campaign_hard_reset()`, then sends each prompt through `POST /api/chat`.
When no `--base-url` is supplied, it uses FastAPI `TestClient` against `game.api.app`;
with `--base-url`, it posts JSON to a running server. In both cases the gameplay
entrypoint is `/api/chat`, not a lower-level direct domain call.

The scenario-spine lane in `tools/run_scenario_spine_validation.py` also sends
scripted natural-language prompts through `/api/chat`, using scenario definitions
from `data/validation/scenario_spines/*.json`, and evaluates the resulting recorded
turns with `game.scenario_spine_eval.evaluate_scenario_spine_session`.

The N1 longitudinal lane in `tools/run_n1_scenario_spine_validation.py` is different:
it delegates to test-helper synthetic fixtures, uses a fake GM responder, and records
fingerprints and health summaries. It is useful for deterministic continuity checks,
but it is not live player-facing gameplay evidence.

## Player input

For the playability run, simulated player input is scripted natural-language text.
It is not LLM-generated and not selected from a live UI. The exact prompts are in
`tools/run_playability_validation.py` and copied into each generated `metadata.json`
and `transcript.md`.

Representative examples:

- `p1_direct_answer`: `Who commands the watch here?`; `Who stole the relic from the chapel?`
- `p2_respect_intent`: `Tell me about the thief.`; `Who exactly was seen near the dye vats?`
- `p3_logical_escalation`: `What do I see at the gate?`; `I press again: what is actually posted on the notice?`
- `p4_immersion`: `I glance at the notice.`

## GM output

The playability runner records `gm_output.player_facing_text` from the `/api/chat`
response as the GM text. This is the player-facing text returned by the API. The
new artifacts preserve it verbatim in `transcript.md` and `evaluation.json`.

The runner also preserves relevant runtime diagnostics separately, including
`resolution_kind`, `_final_emission_meta`, narrative-authenticity output, dead-turn
visibility, and the raw legacy `run_debug.json` payload.

## State preservation

The new observability artifacts capture state through the existing canonical storage
APIs: `load_session()`, `load_world()`, `load_combat()`, `load_character()`, and
`load_log()`. Each playability run now writes:

- `state_before.json`: immediately after the runner's normal reset and before the
  first scripted player prompt.
- `state_after.json`: after the final turn.

This keeps the audit representation aligned with existing persistence rather than
inventing a second state model.

## Evaluation and PASS meaning

The playability PASS/FAIL result comes from the existing deterministic evaluator in
`game.playability_eval.evaluate_playability`. The runner's `summary.json` mirrors the
final turn's evaluator output and does not recompute its own threshold. The current
overall evaluator rule is:

- Axis scores are computed for `direct_answer`, `player_intent`,
  `logical_escalation`, and `immersion`.
- Each axis passes at `score >= 15`.
- Overall passes when total score is at least `60` and immersion score is at least `10`.
- Existing dead-turn/gameplay-validation invalidation can force the effective
  overall result to fail.

This means a PASS proves only that the deterministic evaluator scored the final
turn over the current threshold and did not mark the run invalid. It does not prove
that every axis passed, that dialogue was semantically satisfying, that the whole
conversation was human-plausible, or that a human player would consider the game
coherent.

## Runtime evidence from the generated passing runs

All four representative playability scenarios reported PASS:

| Run | Result | Score | Notable evidence |
| --- | --- | ---: | --- |
| `20260917T221002Z_p1_direct_answer` | PASS | 67 | `player_intent` failed; GM answered `Who stole the relic from the chapel?` with `Tavern Runner says, "No. I cannot answer that from what."` |
| `20260917T221002Z_p2_respect_intent` | PASS | 78 | `player_intent` failed despite a more substantial second answer. |
| `20260917T221002Z_p3_logical_escalation` | PASS | 67 | `player_intent` failed; second GM response was only `Tavern Runner mutters,` |
| `20260917T221002Z_p4_immersion` | PASS | 75 | `player_intent` failed on the single-turn observation prompt. |

These are demonstrated problems in the current validation signal: a run can PASS
while `summary.failures` contains weak-axis findings, because overall PASS is based
on aggregate score and the immersion floor, not on every axis passing.

## Similarity to real human gameplay

Similarities:

- The playability and scenario-spine runners use natural-language prompts.
- They exercise `/api/chat`, the same API boundary used by interactive chat.
- They receive player-facing GM text from `gm_output.player_facing_text`.

Differences:

- The playability simulated player is a fixed script. It does not react to the GM
  output, change plans, ask arbitrary follow-up questions, or get confused.
- The script knows validation targets in advance, such as direct answer, intent,
  logical escalation, and immersion probes.
- The runner records hidden diagnostics and state snapshots unavailable to a human
  player.
- The pass/fail decision is deterministic heuristic scoring, not a human assessment
  of playability.
- The N1 lane uses fake-GM synthetic fixtures and is therefore not live gameplay
  evidence.

## Blind spots

Demonstrated:

- PASS can coexist with axis-level failures in `summary.failures`.
- PASS can coexist with terse or incomplete player-facing GM output.
- The player script is cooperative and narrow.

Plausible but not fully demonstrated by this run:

- Long-form incoherence may be missed when only the final turn's playability summary
  drives the scenario PASS field.
- A scripted prompt suite may avoid irrelevant objects, NPCs, contradictory player
  behavior, or conversational repair attempts that a human would naturally try.
- Aggregate scoring can mask a severe failure on one axis if other axes score well.

## Recommendations for later work

- Keep these transcript artifacts as a required output for any future automated
  playability run.
- Add a separate review lane that fails or flags when any axis-level failure appears,
  without changing the current playability evaluator until the team deliberately
  redefines PASS.
- Add reactive simulated players that choose follow-ups from prior GM output.
- Add adversarial and confused-player personas.
- Compare live `/api/chat` simulations against UI/manual-gauntlet transcripts.
- Preserve short human-readable excerpts in aggregate reports so reviewers do not
  have to open every JSON file before seeing suspicious PASS results.


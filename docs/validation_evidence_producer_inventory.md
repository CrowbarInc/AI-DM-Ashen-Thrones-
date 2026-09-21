# Validation Evidence Producer Inventory

This inventory was completed before implementation of the Validation Evidence Standard. It records
what existing lanes actually preserve, without redesigning or upgrading their claims.

Legend: **yes** means normally present in durable artifacts, **partial** means optional, indirect, or
failure-only, and **no** means absent from the ordinary artifact contract.

| Producer | Invocation and artifacts | Transcript | Exact player / GM | Evaluation and verdict | State | Decision rationale | Disagreement | Success / failure retained | Review without code |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Playability | `python tools/run_playability_validation.py --all`; `artifacts/playability_validation/` or chosen root | yes | yes / yes | full per-turn playability, final summary, gates, runtime validity | before/after snapshots | no; fixed tuple position only | no dedicated review record | yes / yes | yes |
| Semantic calibration | `python tools/run_semantic_calibration.py`; `artifacts/semantic_validation_calibration/` | case rows, not runtime transcript | yes / yes | expected vs actual semantic result and gates | no runtime state | authored-case rationale | agreement/disagreement explicit | yes / yes | yes |
| Reactive/adversarial | `python tools/run_reactive_player_validation.py`; `artifacts/reactive_adversarial_players/` | yes | yes / yes | full per-turn evaluator, gates, diagnostic quality, runtime validity | final-emission metadata; no canonical before/after pair | yes | separate `human_review.json` | yes / yes | mostly; review requires joining files |
| Scenario spine | `python tools/run_scenario_spine_validation.py`; `artifacts/scenario_spine_validation/` | yes | yes / yes | session-health classification, axes, reasons, operator summary | transcript metadata and lineage; no canonical pair | no; fixed branch | no standard human disagreement | yes / yes | yes |
| N1 scenario spine | `python tools/run_n1_scenario_spine_validation.py`; configured artifact root | synthetic rows | yes / controlled GM | deterministic fingerprints, branch summaries, reason codes | synthetic harness state | profile/policy metadata varies | no | yes / yes | partial |
| Manual gauntlets | `python tools/run_manual_gauntlet.py --gauntlet ID`; `artifacts/manual_gauntlets/` | yes | yes / yes | operator verdict plus optional advisory behavioral evaluation | scene/interlocutor snapshots; optional trace | human prompts; no simulated rationale | operator notes can record it, not standardized | yes / yes when operator saves them | yes |
| Behavioral gauntlet | pytest/helper invocation; no standard durable root | supplied rows only | if caller supplies both | shallow axes and reason codes | no | no | no | failure output; success usually not durable | no for ordinary pytest success |
| Synthetic sessions | `python tools/run_synthetic_session.py`; console unless caller persists | compact turn views | yes / yes in views | synthetic summary, not calibrated semantics | snapshots | yes for policy choice | no | variable / variable | partial |
| Golden/protected replay | pytest and replay/report tools; `artifacts/golden_replay/` plus failure logs | projected observations; rich failure diagnostics | usually yes / yes for protected rows | structural/replay invariants and drift classifications | projected runtime metadata | fixed fixture provenance, not player rationale | drift/classifier evidence only | success often aggregate; failure rich | partial |
| API integration tests | `pytest`; no standard campaign artifact | usually no durable transcript | assertions may include them | assertion-specific | temporary fixtures | no | no | no durable success / pytest failure output | no |
| Static/content/governance lanes | tool-specific commands and reports | not applicable | not applicable | structural result only | repository snapshot | not applicable | not applicable | tool-specific | usually yes |

## Claim boundaries

- Playability, reactive-player, scenario-spine, manual-gauntlet, selected synthetic/replay, and API
  lanes can make player-facing claims only to the extent that exact interaction evidence is retained.
- Semantic calibration is a labeled evaluator corpus, not evidence that the live runtime produced the
  response.
- Behavioral-gauntlet results prove only the supplied rows avoid enumerated shallow anti-patterns.
- N1 and common synthetic modes use controlled/fake GM output and cannot establish production-model
  behavior.
- Golden/protected replay primarily proves protected execution and projection invariants. A successful
  structural replay does not establish semantic gameplay quality.
- Structural, schema, ownership, import, serialization, registry, and deterministic state-transition
  tests do not require fabricated gameplay transcripts and must not be labeled semantic evidence.

## Current cross-lane gaps

1. No shared vocabulary distinguishes structural, runtime, semantic, human-realism, stress, and
   human-reviewed claims.
2. No common packet guarantees representative success, failure, boundary, disagreement, ambiguity,
   stress, and missing-category visibility.
3. Success evidence is often less durable than failure evidence.
4. Human judgments are not consistently distinct from automated semantic results.
5. Stress probes and plausible player behavior are not consistently labeled.
6. Selection of representative examples is not generally deterministic or documented.
7. Evaluator disagreements can be recorded in campaign prose but have no shared historical schema.
8. A reviewer often must join transcript, summary, and review files manually.

The shared evidence packet introduced by this campaign addresses those reporting gaps. It does not
change any producer's evaluator, verdict, gameplay path, or historical result.

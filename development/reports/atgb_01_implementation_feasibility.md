# ATGB-01 Implementation Feasibility

Date: 2026-10-18
Status: historical feasibility note. ATGB-02 implements the isolated driver, fixtures, and judgment sheet described here, with the S07 partition move. This note is not rewritten. Specification: `development/reports/atgb_02_benchmark_specification.md`.

The smallest future implementation is a checkpoint harness that reuses chat, isolated storage, and the existing evidence packet. It records transcripts and state deltas. A person applies the rubric in `development/reports/atgb_01_conversational_benchmark_design.md`. No new scorer and no second playability evaluator are required.

## What already exists

| Need | Existing mechanism | Reuse |
| --- | --- | --- |
| Player turn entry | `POST /api/chat` and `game.api.chat` | The same boundary playability validation already drives. ATGB does not add a second chat path. |
| Fresh start | `game.campaign_reset.apply_new_campaign_hard_reset` | Use it only inside an isolated data directory. |
| Isolated store | `ASHEN_DATA_DIR`, read by `game.storage` at import | Copy bootstrap scene, world, character, and campaign files into a temporary directory and set the variable before import. Canonical `data/session.json` stays untouched. |
| Scene and facts | `data/scenes/frontier_gate.json`, NPC topics in `data/world.json` | The catalog is written against these facts. No new scene content is required for the proposal. |
| Communication mode | `game.api._resolve_communication_mode` and the OOC non-mutating responses | Host-lane evidence for explicit `OOC:` / `IC:` prefixes. The rubric still judges whether the reply answered the question. |
| Conversational decision | `game.conversational_orchestration.deterministic_conversational_decision` and `ConversationalDecision` | Categories ANSWER, CLARIFY, DECLINE, EXECUTE, and PLAN are observation points. They are not ATGB's score. |
| Delivered continuity | `game.conversational_continuity` | The host already prefers the delivered line over proposed or rejected narration. The benchmark judges the player-facing result of that owner. |
| Turn telemetry | `game.api._performance_record`, stored on resolution metadata | Elapsed time, provider-call count, token fields, and retry count. Token totals are null when narration retries exceed one. Cost is not computed. |
| Provider suppression | `ASHEN_DISABLE_LIVE_INTERPRETATION` and the provider-disabled path | The host-deterministic lane. |
| Transcript persistence | Session log written by chat | Source for prior-turn context inside a scenario. |
| Evidence packet | `tools.validation_evidence` and `tools/build_validation_evidence_packets.py` | A future run that claims player-facing behavior builds the standard packet. ATGB fields (three results, severity, evidence class, lane) belong in the campaign summary. The packet schema does not need a fork for the first checkpoint. |
| Review export | `tools/build_review_handoff.py` | The same ZIP contract. No generator field is required; the summary can name the lane and the critical failures in prose. |
| Adjacent heuristic | `game.playability_eval.evaluate_playability` via `tools/run_playability_validation.py` | Optional side record. Its PASS or FAIL is not the ATGB verdict. The four playability scenarios (`p1_direct_answer` through `p4_immersion`) stay that tool's scenarios. ATGB player lines were worded differently so the corpora are not the same fixture. |

## What a later implementation would add

Only these pieces are actually missing. Each is small, and none of them is a new authority.

1. A scenario file, adopted from this catalog, split into `data/validation/atgb/visible/` and `data/validation/atgb/held_out/`. Related variations live with the visible set and are tagged. Held-out files are not imported by tests.
2. A driver that, per scenario: creates an isolated data directory, resets it, sends the player lines in order through chat, and writes a transcript plus the state delta and the performance record under `artifacts/atgb/<corpus>/<revision>/<lane>/`.
3. A blank judgment sheet, one row per scored turn, with the three results, severity, clarification tag, continuity tag, and human-review status. A person fills it in. The sheet is evidence, not a second evaluator.
4. A run header that records git revision, corpus version, rubric version, model, interpretation flag, provider flag, trial index, and budget stop.

That driver must not call `evaluate_playability` to decide acceptability. It may attach the dict if a reviewer wants the adjacent view, labeled as such.

## What should not be built

- A universal gameplay score, a weighted composite, or a new pass threshold.
- A wrapper that maps ATGB acceptability onto playability PASS.
- A live-provider run after every development block.
- A replay-classification change. Development failure classes stay in the Constitution and do not enter the replay taxonomy.
- New Frontier Gate facts, prices, curfew hours, or NPC topics whose purpose is to make a scenario pass.
- A second conversational router, discourse stack, or clarification policy inside the harness.
- Historical-build execution as a gate on the first baseline.

## State reset and safety

`apply_new_campaign_hard_reset` rewrites session, world playthrough, combat, and the transcript in whatever `DATA_DIR` was configured at import. The playability runner uses that reset against the configured store. An ATGB driver that imported the game against the repository `data/` directory would wipe a human play session. The feasible safeguard is the existing environment override, pointed at a copy, with a startup assertion that the resolved data directory is not the repository `data/` path.

Canonical files are already dirty from human play. A future implementation must not revert them and must not use them as the benchmark world snapshot, because playthrough residue would leak into the opening.

`DATA_DIR` is bound at import. The driver sets `ASHEN_DATA_DIR` in the process environment before importing `game`, or it runs as a subprocess. Setting the variable later does not retarget an already imported store.

## Nondeterminism sources

- Live interpretation is enabled unless `ASHEN_DISABLE_LIVE_INTERPRETATION` is set (`game.semantic_interpreter.live_interpretation_enabled`).
- Narration calls the configured model on turns the host does not fully answer.
- Retries can replace or preserve player-facing text. The performance record cannot sum tokens across those retries.
- Sampling controls are whatever the current client uses. If the driver cannot read them, it records `uncontrolled` rather than assuming a temperature.
- Clock and turn-counter fields increment on chat even for some non-actions. The rubric does not treat that increment as a critical failure. A player-facing claim that hours passed, or a scene change, still is.

## Deterministic, live, and human

| Lane | Feasible now | Claim it supports |
| --- | --- | --- |
| Host-deterministic | Yes, with provider calls disabled and an isolated store. Many OOC prefixes, some clarifications, and non-mutation can be observed without a model. | Host behavior only. |
| Live-provider | Yes, when a provider is configured. Not run in this design pass. | Player-facing communication for the pinned model. |
| Human evaluation | Yes, on a saved transcript. No new UI is required for the first checkpoint. | Acceptability, severity, clarification, and continuity. |

A host-lane green sheet is not an ATGB conversational result. The evidence standard also withholds any ATGB result until this corpus, or a successor, is adopted.

## Smallest sequence, after review adopts a corpus

1. Place the adopted visible and held-out files. Do not import held-out from tests.
2. Add the isolated-store driver and the judgment sheet. No production edit.
3. Run the host lane on the visible scenarios and archive the transcripts.
4. Run one live trial only when a baseline or a full checkpoint is declared, under a call budget.
5. A reviewer fills the sheet. The campaign builds a Validation Evidence Standard packet and the ordinary review ZIP.
6. The ZIP states the lane, lists critical failures first, and does not report a single PASS.

Until step 1 is an accepted review decision, none of those steps should be started from this design pass.

# ATGB-02 — Conversational Benchmark Specification

Date: 2026-10-18
Status: implemented infrastructure. No live baseline. No gameplay-performance claim.
Benchmark version: `ATGB-02`
Scenario version: `ATGB-01`
Rubric version: `atgb-rubric-01`
Partition revision: `ATGB-02-s07-held-out`

This specification adopts the ATGB-01 design and catalog, with the refinements below. The rubric definitions in `development/reports/atgb_01_conversational_benchmark_design.md` stay in force: three judgments per turn, severity, clarification, continuity, and no universal score. The scenario wording in `development/reports/atgb_01_scenario_catalog.md` is the behavioral source. Fixtures must match those player lines.

## What changed from the proposal

S07, the four-turn initiative conversation, moves from development-visible to held-out. Its player lines and pass criteria are unchanged.

| Partition | Scenarios | Turns |
| --- | --- | ---: |
| Development-visible | S01–S06 | 25 |
| Related variations | S08 | 4 |
| Held-out | S07, S09, S10 | 8 |
| **Total** | **10** | **37** |

The ATGB-01 catalog index still lists S07 as development-visible and therefore counts 29 / 4 / 4. That is the discrepancy. The totals were not edited to hide it.

Held-out turns in this corpus already appeared in the ATGB-01 review package. Their partition remains held-out. Their evidence status is `held_out_previously_exposed`. They are not fully independent unseen evaluation data. A later environment that was not in that review could provide stronger evidence. This corpus does not support a strong generalization claim by itself.

## Scope

The benchmark measures player–AI-DM communication: intent recognition, conversational continuity, corrections and clarifications, response relevance, NPC dialogue coherence, IC/OOC boundaries, ambiguity handling, and conversational initiative and naturalness.

Narration quality, response efficiency, and unauthorized state changes are cross-cutting. Efficiency is recorded when telemetry exists. It is not a pass/fail axis in rubric 01.

Combat, inventory, character creation, economics, and other mechanical systems are not expanded into benchmark coverage. A turn may mention stew or a rumor. Inventing a price or a purchase is an authority failure because that fact was not authorized.

## Environment

Frontier Gate (`frontier_gate`) is the initial environment. It is named by the fixtures. The runner compares the fresh campaign scene with the fixture's `location_id` and does not contain a Frontier Gate branch. If a future fixture names a location the fresh campaign does not open on, the runner records the mismatch and does not force a scene change.

No second environment is added in this pass. A later environment is a new object in `data/validation/atgb/corpus.json` and scenario files that reference its id.

## Judgments

Each scored turn keeps three results.

- **Interpretation.** Did the system understand the player's communicative intent?
- **Response.** Did the response adequately address that intent?
- **Authority.** Did the system preserve established world facts and state?

Acceptable means response and authority are both `pass`. Interpretation stays visible beside them. A reviewer may mark any of the three `uncertain` when the evidence is insufficient. `unchecked` means that lane did not judge the dimension. Neither value is a pass.

Conversation-level notes record repetitive replies, unnatural phrasing, excessive clarification, poor pacing, failure to sustain initiative, and mechanical or validation-like dialogue. Those notes are not a score. A conversation can meet the turn criteria and still feel unnatural.

`evaluate_playability` is not called. Its PASS is not an ATGB verdict.

## Evidence classes

Development-visible scenarios may be opened while diagnosing a failure. Related variations are published paraphrases of visible requirements. They are not independent generalization. Held-out scenarios keep their partition for later evaluation discipline. In this version they are previously exposed.

## What this specification does not do

It does not claim that communication improved. It does not establish the live baseline. It does not add a scorer, a semantic interpreter, or a second playability evaluator.

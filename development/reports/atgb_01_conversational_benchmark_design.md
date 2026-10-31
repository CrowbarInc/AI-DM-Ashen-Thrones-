# ATGB-01 — Conversational Benchmark Design

Date: 2026-10-18
Status: historical proposal. ATGB-02 implements this design with the refinements in `development/reports/atgb_02_benchmark_specification.md`. This file is not rewritten. S07 remains development-visible in the text below; the adopted partition moves it to held-out.
Identifier: `atgb_01_conversational_benchmark_design`
Pass type: design and discovery only. No benchmark run. No gameplay change.

This document proposes the first Ashen Thrones Gameplay Benchmark corpus and the way a future run would be scored, executed, and compared. It does not adopt the corpus. Until a reviewed corpus is adopted, `docs/validation_evidence_standard.md` forbids any campaign from reporting an ATGB result.

That paragraph is the proposal as written on 2026-10-18. ATGB-02 is the later implementation. It does not rewrite this body. A performance result is still forbidden until a live, human-reviewed checkpoint exists.

Companion documents:

- Scenario catalog: `development/reports/atgb_01_scenario_catalog.md`
- Implementation feasibility: `development/reports/atgb_01_implementation_feasibility.md`

## 1. Purpose

ATGB-01 answers one question:

Can an ordinary player communicate naturally with Ashen Thrones, sustain a coherent exchange, and receive an appropriate response without learning to accommodate the engine?

The benchmark is a checkpoint instrument for player–AI-DM communication. It measures whether the player was understood, whether the reply served that communicative purpose, and whether the reply stayed inside authoritative world state.

A high communication result is not a claim that combat, inventory, character creation, economy, equipment, or advancement are correct. Those systems may appear as the subject of a sentence. Their mechanical correctness stays with their existing owners.

## 2. Authority boundaries

ATGB complements the current validation authorities. It does not replace them.

| Authority | What it still owns | What ATGB does with it |
| --- | --- | --- |
| `docs/validation_evidence_standard.md` | When a benchmark result may be claimed, and what an evidence packet must contain | This proposal follows that section. It does not amend it and does not create a corpus-in-force. |
| `docs/playability_validation.md` and `game.playability_eval.evaluate_playability` | The heuristic playability contract and its PASS/FAIL | ATGB does not wrap, recompute, or reinterpret that result. A future runner may store the evaluator dict beside a transcript as adjacent telemetry. That dict is not an ATGB verdict. |
| `docs/semantic_validation_calibration.md` | Calibrated semantic gates for known foundational failures | Calibration cases stay the semantic authority they already are. ATGB does not add gates. |
| Protected replay | Structural and runtime replay expectations | A green replay is not conversational competence. |
| `docs/product_realization_validation.md` | Scenario-independent fixture gate for a claimed general engine owner | ATGB is not that gate. A systemic repair still meets that document. |
| `docs/ai_gm_contract.md` | Narration invariants: engine authority, no validator voice, answer the player, grounded output, IC/OOC handling | Scenario criteria cite those invariants as behavioral expectations. They do not publish a second contract. |
| `game/conversational_orchestration.py`, `game/conversational_continuity.py`, and the communication-mode path in `game/api.py` | Production decisions for answer, clarify, decline, execute, and plan, and for IC/OOC mode | ATGB observes player-facing results of those owners. It does not add a parallel router. |
| Development Constitution | Failure classes, task proportion, and the rule that routine repairs do not require a provider call | Cadence in §9 follows that rule. |

Playability PASS remains the heuristic contract in `docs/playability_validation.md`. Deterministic host success remains host success. Neither is reported as natural conversational competence.

## 3. Scope

### In scope

Communication at the current canonical opening, Cinderwatch's eastern gate (`frontier_gate`):

- questions and actions
- ordinary speech and explicit requests
- references to earlier turns in the same conversation
- corrections of a misunderstood intent
- NPC knowledge, uncertainty, and commitments
- answers that address the question, as distinct from answers that are merely on a nearby topic
- ambiguous requests
- IC and OOC boundaries
- conversational flow, including a reply that continues without a needless clarification
- narration that stays inside the authorized outcome
- response efficiency, recorded when telemetry exists

### Out of scope for mechanical correctness

Combat, inventory, character creation, economy, equipment, and advancement. A turn may mention stew, a rumor sold for coin, or the queue. The benchmark scores whether the reply handles that talk. It does not score a price table, a purse, or a character sheet. Inventing a price, a purchase, or a coin deduction is an authority failure because no such fact or transaction is authorized, not because ATGB has become an economy test.

### Known product limits the scenarios accept

These limits are current repository facts. A scenario must not require them to be solved before a conversational result is interpretable.

- Ordinary waiting and a diegetic clock are absent (`PR-BE`). A reply that honestly does not pass time is acceptable. A reply that narrates hours passing is not.
- Curfew hours, stew price, refugee origins, and who changed the patrol route are not authored. Grounded uncertainty is the successful answer.
- Compound multi-action execution is still deferred. A turn that stacks several actions is not used as a scored demand that every clause execute.
- `they` / `it` are not last-answer authority (`PR-BG`). Scenarios that need an earlier fact repeated use a contentful follow-up, or they score a focused clarification as success.
- Hidden Frontier Gate facts (the noble-house watcher, the Ash Cowl contact, the coordinated signal, the paid face list) are not player-visible. Speaking them as known truth is an authority failure.

### World the scenarios assume

Fresh `frontier_gate` after a new-campaign reset in an isolated data directory. See the feasibility note for why the developer's canonical `data/session.json` must not be the benchmark store.

Authoritative public facts used by the catalog:

- Visible: the notice board lists taxes, curfew rules, and a missing-patrol warning; a gate serjeant manages the crowd and watches the roster board; a tavern runner trades hot stew and rumors beside the rain barrel; threadbare watchers and refugees stand along the muddy line; Ash Compact census delays have tightened the eastern caravan choke.
- Clue `notice_patrol_route`, revealed by investigating the notice board: the missing patrol was last seen taking the northwest mud track past the crates.
- `gate_guard` topic `watch_command`: Captain Thoran commands the gate watch tonight.
- `gate_serjeant` topic `route_change`: the patrol route changed after the Ash Compact census choke worsened.
- `tavern_runner` topic `patrol_rumor`: the runner heard the patrol vanished near muddy footprints northwest of the crates. That is hearsay.
- Exits: Enter Cinderwatch → `market_quarter`; Follow the missing patrol rumor → `old_milestone`.
- The scene addressable `guard_captain` is a different id from the world NPC `gate_guard`, which owns the Thoran sentence. Scenarios that ask who commands the watch accept either a Thoran answer spoken by the owning NPC, or a focused clarification, or grounded uncertainty from a speaker who does not own the fact. They do not accept a newly invented commander.

## 4. Capability taxonomy

The requested targets are kept. Thirty-seven scored player turns sit inside ten short conversations. The distribution was not reweighted: the eight capabilities already match the communication pillar in `docs/validation_evidence_standard.md`, and the gate content can exercise each of them without a new mechanical system.

| Capability | Scored turns | Where it is primary |
| --- | ---: | --- |
| Intent recognition | 5 | S01.1, S01.2, S02.1, S04.1, S08.1 |
| Conversational continuity | 5 | S02.4, S03.4, S05.2, S08.4, S10.2 |
| Corrections and clarifications | 5 | S02.3, S03.5, S04.2, S05.4, S08.2 |
| Response relevance | 5 | S01.3, S02.2, S04.3, S07.4, S08.3 |
| NPC dialogue coherence | 5 | S03.1, S03.2, S03.3, S04.4, S05.1 |
| IC/OOC boundaries | 4 | S06.1–S06.4 |
| Ambiguity handling | 4 | S05.3, S09.1, S09.2, S10.1 |
| Conversational initiative and naturalness | 4 | S01.4, S07.1, S07.2, S07.3 |
| **Total** | **37** | **10 scenarios** |

Evidence-class split, assigned before any run:

> ATGB-02 supersedes the original S07 partition designation below: S07 is now
> held-out. The historical 29 / 4 / 4 table is preserved as the ATGB-01 proposal.
> The current machine-readable corpus (`data/validation/atgb/corpus.json` and
> scenario files) is authoritative for execution: 25 / 4 / 8 turns.

| Class | Turns | Role |
| --- | ---: | --- |
| Development-visible | 29 (S01–S07) | Stable conversations developers may open while diagnosing a failure |
| Related variations | 4 (S08) | The same requirements in different words, published with the visible set |
| Held-out | 4 (S09–S10) | Reserved generalization check, run at a full checkpoint |

The held-out slice is deliberately small. Four reserved turns can show whether a repair that was tuned on the visible gate conversations still communicates. They cannot certify the whole pillar. A larger reserved share is an open review choice: S07 can move to held-out without changing capability counts. Behavioral criteria, not the size of the secret set, are the main protection against overfitting.

Cross-cutting concerns on every scored turn:

- Narration quality: usable, grounded, and free of validator voice. Stiff or repetitive prose on an otherwise successful reply is a minor defect. It does not by itself fail the turn.
- Response efficiency: recorded from existing turn telemetry when present. It is not a pass/fail axis in this proposal.
- Unauthorized state changes: scored under authority compliance. A fluent sentence that commits a journey, a purchase, a hidden fact, or a discovery the engine did not authorize fails the turn at critical severity.

## 5. Three results per turn

Each scored turn records three results. They are not collapsed into one PASS/FAIL.

### Interpretation success

The system selected the communicative act the player performed: a question, an action, a correction, a continuation, an OOC aside, or a genuine ambiguity. Evidence may include `resolution.kind`, communication mode, conversational decision category, addressee, and whether a pending clarification matches the ambiguity. A wrong addressee or a travel parse of a question is an interpretation failure even if the resulting sentence is grammatical.

### Response success

The player-facing text does the communicative job: it answers, describes, corrects, clarifies once, continues, or declines in a way the player can use. An authorized fact that answers a different question is a response failure. The information-disclosure owner can be behaving as designed at the same time.

### Authority compliance

The reply does not invent a consequential fact, does not leak a hidden fact as truth, and does not commit a world change the turn did not authorize. Scene id, discovered clues, exits taken, and player-facing claims are compared with the scenario's fact list. Conversational memory that restates an earlier delivered line is continuity. Promoting that line into a new canonical discovery is an authority failure, consistent with the settled rule that conversational memory is not structured-fact authority.

A turn can pass one result and fail another. The catalog marks the expected combination where that distinction is the point of the turn.

### Turn acceptability

The player received an acceptable response when response success and authority compliance both pass. Interpretation is reported beside them. An interpretation failure usually produces a response failure; when a later layer happens to say the right thing anyway, both results stay visible.

Minor narration roughness can sit on an acceptable turn. A major or critical defect cannot.

## 6. Scoring model

The scorer for ATGB-01 is a human judgment against the catalog's behavioral criteria, applied to an inspectable exchange. No new automated gameplay score is proposed. `evaluate_playability` is not the scorer.

Rubric version: `atgb-rubric-01`. A later change to these definitions is a new rubric version. Percentages from different rubric versions are not a trend.

### A. Turn success

For each scored turn, in each lane that actually ran:

- interpretation: `pass`, `fail`, or `unchecked`
- response: `pass`, `fail`, or `unchecked`
- authority: `pass`, `fail`, or `unchecked`
- acceptable: yes only when response and authority are both `pass`

`unchecked` means that lane did not observe the dimension. It is not a pass. The host-deterministic lane leaves response naturalness `unchecked` whenever the reply is a fixed acknowledgement that was not produced as player-facing conversation under a live model.

### B. Capability performance

Each turn has one primary capability, assigned in the catalog before the run. Report:

`passes / scored` for that capability, separately for development-visible, related-variation, and held-out turns.

A turn with `unchecked` response is omitted from the response rate and counted in an unchecked column. It is not moved into the pass numerator.

Secondary capabilities are diagnostic notes. They are not a second rate, so one awkward sentence is not counted against three capabilities at once.

### C. Failure severity

| Severity | Meaning | Effect on acceptability |
| --- | --- | --- |
| Minor | The player can continue. Wording is stiff, slightly repetitive, or lightly echoed, and the communicative job was done. The `Word is` envelope on an already authorized fact stays in this band. | Turn may remain acceptable. |
| Major | The player has to re-teach the system: wrong addressee, missed question, lost referent, needless clarification, evasive restatement, or a nearby fact substituted for the asked fact. | Response fails. Turn is not acceptable. |
| Critical | Unauthorized consequential state or a concealed mutation: invented commander, price, curfew hour, origin, witness, or route; hidden fact spoken as truth; narrated journey or purchase without an authorized transition or transaction; player-facing text that says nothing changed while clues, scene, or world flags did. | Authority fails. Turn is not acceptable. Listed in full above any percentage. |

### D. Clarification quality

| Tag | When to use |
| --- | --- |
| `none` | The reply proceeds without a question, and no question was needed. |
| `necessary_pass` | One focused question names a real ambiguity or a missing slot the player left open. |
| `unnecessary_fail` | The player's turn was already specific enough to answer, describe, or decline. |
| `missing_when_needed_fail` | The turn was ambiguous and the reply guessed, changed the subject, or refused without asking. |

A necessary clarification is a successful conversational act. The following player turn, when it answers that question, is scored on whether the system uses the answer.

### E. Continuity

| Tag | When to use |
| --- | --- |
| `not_applicable` | The turn does not depend on an earlier exchange. |
| `preserved` | The earlier fact, addressee, or commitment the turn relies on is still in force. |
| `lost` | That material was dropped, replaced, or attributed to the wrong speaker. |

S02.4, S03.4, S05.2, S08.4, and S10.2 require memory older than the immediately previous sentence. A reply that only echoes the latest line and drops the earlier one is `lost`.

### F. Response efficiency

Record, per live turn, from `resolution.metadata.performance` when the chat path wrote it:

- `elapsed_ms`
- `provider_call_count`
- `input_tokens` and `output_tokens`
- `retry_count`
- estimated provider cost

The current performance record sets token totals to null when narration retries are greater than one, because the last stamp cannot account for earlier calls. Report null. Do not reconstruct tokens. Do not invent a dollar cost. Cost is `unavailable` unless the run configuration supplies a price table for the pinned model and the token counts are present.

Efficiency does not change acceptability in rubric 01. The report still shows the slowest turns and any turn with a retry, so a cheap-looking failure is not hidden and a fluent success with several retries is not described as cheap.

### How to report without hiding a severe failure

A checkpoint report uses this order:

1. Critical failures, each as a full exchange. If this list is non-empty, the narrative summary says the checkpoint has a state-integrity or authority breach. No percentage appears before this list.
2. Major failures, grouped by primary capability, with the player line and the reply.
3. Capability table, split by evidence class, with passes, fails, and unchecked.
4. Clarification and continuity counts.
5. Efficiency table, or an explicit `not recorded`.
6. Lane statement: host-deterministic, live-provider, and human review, each with its own boundary.

There is no ATGB score out of 100, no star rating, and no single PASS that means the AI-DM works. An aggregate such as "29 of 37 visible-turn responses passed" may appear only after the critical and major lists, and only inside one evidence class and one lane.

### Evidence packet

A future run that claims player-facing behavior uses the existing Validation Evidence Standard packet. The packet's required categories stay in force. ATGB adds, in the campaign summary rather than by forking the packet schema, the three results, the severity, the evidence class, and the lane. Automated playability output, if stored, is labeled adjacent telemetry.

Human review status on each judged turn is `HUMAN_ACCEPTED`, `HUMAN_REJECTED`, or `HUMAN_AMBIGUOUS`. Ambiguous judgments stay ambiguous. They are not converted into a pass to protect a trend.

## 7. Overfitting controls

Three safeguards are required together.

### Behavioral criteria

Acceptable replies are defined by communicative effect and by the authorized fact set. Exact prose is required only where the words are the fact, and even then a close paraphrase that preserves the fact, the speaker, and the epistemic status (hearsay versus report) passes. A preferred writing style does not earn a pass. A rigid stock line does not fail if it does the job, and it does not pass if it answers the wrong job.

### Separate evidence classes

Development-visible scenarios may be quoted in implementation notes and regression tests after adoption.

Related variations use different wording for a requirement that already appears in the visible set. They are published. A repair author who writes still more paraphrases has produced related variations. Those extra paraphrases are not held-out evidence, under the Constitution and under `docs/product_realization_validation.md`.

Held-out scenarios are specified in this review so a reviewer can judge them. After adoption they are stored at `data/validation/atgb/held_out/` and are not imported by production code or by ordinary unit tests. Implementation tasks do not load that directory. A repair report does not quote held-out lines as the cases that were tuned. The evaluation runner reads them only at a full checkpoint.

Secrecy is not the only control. The visible criteria are already broad enough that copying one successful paragraph into a template would still fail a turn whose fact, speaker, or question is different.

### Corpus evolution

- Corpus id: `ATGB-01`
- Scenario ids and turn ids in the catalog are stable.
- Wording edits to a scored player line, or changes to a pass criterion, create a new corpus version (`ATGB-01.1` or `ATGB-02`). The previous version remains retrievable.
- Historical comparison is limited to turns whose id, player line, fact list, and rubric version match.
- Adding a scenario does not renumber existing ids.
- A retired turn stays in the old version and is marked retired in the new one. It is not silently deleted from history.

## 8. Execution and comparison

No historical version has to be executed to establish the first baseline. Older builds are comparable only when they can boot the same isolated data directory, accept the same player lines through chat, and emit player-facing text plus enough state to judge authority. If an old build cannot, the report says `not comparable` for that build. It does not reconstruct a missing transcript.

### Initial state

- Isolated data directory, set with `ASHEN_DATA_DIR` before the game package is imported. The directory is a copy of the canonical scene, world, character, and campaign bootstrap files.
- `apply_new_campaign_hard_reset()` inside that directory, then confirm the transcript is empty.
- Starting scene `frontier_gate`.
- The developer's canonical `data/session.json`, `data/world.json`, `data/combat.json`, and `data/session_log.jsonl` are not the store and are not reset.

### Scenario reset

Each scenario starts from that fresh isolated state. Turns run in catalog order. There is no carried state between scenarios. A scenario that needs a fact from an earlier turn must establish that fact inside its own player lines.

The engine opening, if the client shows one before the first player line, is context. It is not a scored turn.

### Model controls

Record in the run header:

- git revision
- corpus version and rubric version
- model name and any endpoint identifier already present in configuration
- live interpretation enabled or disabled (`ASHEN_DISABLE_LIVE_INTERPRETATION`)
- provider calls enabled or disabled
- temperature and any other sampling control the client actually set; if the client exposes none, record `uncontrolled`
- trial index

Do not change production defaults in order to make the benchmark pass.

### Three lanes

| Lane | Provider | What it may claim |
| --- | --- | --- |
| Host-deterministic | Disabled | Routing, mode, clarification, non-mutation, and other host-visible behavior. Natural conversational competence is `unchecked`. |
| Live-provider | Enabled, model pinned | Player-facing communication under that model. One trial is the default. Three trials only when a full checkpoint is declaring a communication result, or when a scenario already disagreed with itself. |
| Human evaluation | Reviews the live transcripts | The acceptability, severity, clarification, and continuity tags. Required before a checkpoint claims natural communication. |

A host-lane pass is reported as host-lane evidence. The report says, in words, that deterministic success is not natural conversational competence.

### Nondeterminism

Live interpretation is on unless `ASHEN_DISABLE_LIVE_INTERPRETATION` is set, and narration calls the configured model on many social turns. Those turns are provider-dependent or mixed. The catalog marks each scenario.

When three trials are run, a turn is stable if the human assigns the same acceptability and the same severity on every trial. A turn that passes once and fails once is `unstable`. Unstable turns are listed with the critical and major failures. They are not averaged into a pass.

### Telemetry and failure evidence

For every scored turn, keep:

- player line and turn id
- player-facing text
- communication mode and conversational decision, when present
- resolution kind, addressee, scene id before and after
- discovered clues and any world-flag or scene-update delta
- performance record, with nulls preserved
- the three results, severity, clarification tag, continuity tag, and evidence class
- human review status and a one-sentence rationale

On a failure, keep the prior player and GM lines from the same scenario so the continuity judgment is inspectable. Do not attach prompts, credentials, or a world dump.

### Version identification

The run header names the git revision, corpus version, rubric version, model, and lane. A comparison table may place two such headers side by side only for shared turn ids. A model change is a comparability limitation. It is recorded. It is not automatically a product regression.

### What the first baseline does not require

Historical execution is not a prerequisite. If the current revision cannot complete a live lane because no provider is configured, the host lane can still be recorded, and the live and human lanes stay `not run`. That package is not an ATGB result under the evidence standard, because no reviewed corpus has been adopted and a host lane does not establish conversational competence. It can still be useful diagnostic material beside the design.

## 9. Cadence

ATGB is independent of campaign acceptance. Closing a Product Realization block does not run it. A campaign may be accepted inside its own scope with ATGB unrun, and the report says so when a reader might otherwise infer a communication result.

| Occasion | What runs | Provider |
| --- | --- | --- |
| Initial baseline, after this corpus is adopted | Host lane on all 37 turns. One live trial of the 29 visible turns and the 4 related variations. Human review of that live transcript. Held-out live trial only after the visible baseline is written, by a reviewer who is not tuning the implementation in the same session. | One live pass. Stop if the run configuration's call budget is hit. |
| Repair or change that touches communication, and does not claim a general communication improvement | Host lane on the visible scenarios that exercise the touched owner. If the change has an original reproduction, include that scenario. | No provider call required. |
| Claim of improvement beyond the original reproduction | Related variations that match the capability. Held-out only if the claim says independent generalization. | Live calls only for the turns the claim depends on. |
| Full checkpoint | All three evidence classes, live lane, human review. Triggers: a declared communication milestone, a major change whose purpose is to move player–AI-DM communication, or a judgment that the last benchmark no longer describes current behavior. | One live trial by default. Three trials only for turns being cited as the milestone result, or turns already marked unstable. |
| Routine repair, documentation, or a subsystem that is not communication | Nothing. | None. |

Communication-related work does not continue indefinitely without asking whether a full checkpoint is due. This proposal does not set a block count. The reconsideration point is: several communication changes have landed since the last full ATGB, or the last full ATGB's model or corpus no longer matches what players run. Asking the question does not itself authorize a provider call. Before adoption, reconsideration still cannot produce an ATGB result.

Cost control: the host lane is the default after the baseline. Live evaluation is checkpoint work. Token and call counts come from telemetry. There is no standing nightly live run.

## 10. Risks and mitigations

| Risk | Why it is real here | Proportionate mitigation |
| --- | --- | --- |
| Overfitting to historical failures | Gate sessions have known misses: patrol clue answering a curfew question, wrong addressee, cutoff stored as an answer, narrated travel. | Most turns are ordinary gate talk. Historical patterns appear only where they are still the communicative requirement. Pass criteria accept any grounded reply, not the repaired stock sentence. |
| Overreliance on deterministic fixtures | Host paths already cover some OOC acknowledgements, empty movement, and a few context answers. | Host results are a separate lane and cannot carry a naturalness claim. |
| Subjective scoring | Relevance and naturalness are judgments. | The catalog states the fact, the job, and the unacceptable outcomes. Two reviewers can disagree; the disagreement is kept, as the evidence standard already requires. |
| Model variability | Live interpretation and narration are nondeterministic. | Pin the model. Default one trial. Mark unstable turns instead of averaging them. |
| Provider cost | Thirty-seven live turns, some with retries, are not free. | Host lane for routine work. One live trial at a full checkpoint. Budget stop. No per-block run. |
| Execution time | A full live pass can be slow. | Scenarios are short and reset independently, so a checkpoint can run one scenario at a time. |
| Unrealistic lines | Designer prompts can become riddles. | Lines are ordinary gate speech. The cleverest available referents were rejected where even the fact list did not distinguish them. |
| Unsupported features | Multi-NPC conversation, prices, clocks, and compound execution are thin or absent. | Success for those moments is a clarification or a grounded refusal. The scenario does not demand the missing system. |
| Rewarding rigid replies | Stock fallbacks can look "correct" and still dodge the question. | Response success asks whether the player's job was done. A generic OOC acknowledgement that ignores the question fails response and can pass interpretation. |
| Maintenance overhead | A second corpus can rot. | Ten scenarios, stable ids, versioned changes, no new scorer. |
| Model changes across checkpoints | A later model can move the live lane without a product change. | The run header records the model. Cross-model deltas are labeled comparability limits. |

No further infrastructure is proposed to drive these risks to zero.

## 11. Illustrative report

The following report is hypothetical. It is a format sample. No benchmark was run. The figures are not measurements.

```text
ATGB REPORT — HYPOTHETICAL SAMPLE
Corpus: ATGB-01
Rubric: atgb-rubric-01
Revision: example-only
Model: example-model-pinned
Lane: live-provider, trial 1 of 1
Human review: complete for this sample
This sample is not an Ashen Thrones Gameplay Benchmark result.
```

### Critical failures

1. S02.2, response relevance. Player: "When does the curfew start?" Reply (sample): the runner states the curfew runs from dusk until dawn and that violators are fined. Interpretation: pass, the turn was read as a time question. Response: fail, no authored hours exist to report. Authority: fail, critical. Scene stayed `frontier_gate`. The failure is the invented hour and fine, spoken as fact.

No percentage is offered above this list. The sample checkpoint has an authority breach.

### Major failures

- S04.2 corrections. Player repeats that they addressed the Gate Serjeant. Sample reply continues in the gate guard's voice and restates Captain Thoran. Interpretation fail, response fail, authority pass (Thoran is an owned fact, said by the wrong speaker about the wrong question).
- S05.3 ambiguity. Player: "Tell me more about that." Sample reply repeats the notice clue and never asks whether the player meant the runner. Tag: `missing_when_needed_fail`.

### Capability table (live lane, human-reviewed sample)

| Capability | Visible | Related variations | Held-out |
| --- | --- | --- | --- |
| Intent recognition | 4/4 | 1/1 | — |
| Conversational continuity | 2/3 | 1/1 | 0/1 |
| Corrections and clarifications | 3/4 | 1/1 | — |
| Response relevance | 3/4 | 1/1 | — |
| NPC dialogue coherence | 4/4 | — | — |
| IC/OOC boundaries | 3/4 | — | — |
| Ambiguity handling | 0/1 | — | 2/3 |
| Initiative and naturalness | 3/4 | — | — |

Unchecked cells are omitted here because this sample pretends the live lane judged every turn. A real host-lane table would show response naturalness as unchecked.

After the lists above, a reader may note that most sample turns were acceptable. That sentence does not retire the invented curfew.

### Clarification and continuity (sample)

- Necessary clarifications that passed: 2
- Unnecessary clarifications: 1 (S07.2, sample asked the player to pick a command after a remark about the banners)
- Missing clarification: 1 (S05.3)
- Continuity preserved: 4 of 5 applicable turns
- Continuity lost: S10.2 in this sample

### Efficiency (sample)

| Turn | Elapsed ms | Provider calls | Input tokens | Output tokens | Retries | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| S01.1 | 800 | 1 | 1200 | 180 | 0 | unavailable |
| S02.2 | 1400 | 2 | null | null | 1 | unavailable |

Null tokens match the current performance record when retries exceed one. Cost stays unavailable because this sample has no price table.

### Lanes (sample)

- Host-deterministic: not shown in this illustration.
- Live-provider: the transcript above.
- Human: accepted or rejected each sample judgment. One turn left `HUMAN_AMBIGUOUS` would be listed, not forced to a pass.

### Comparison row (sample)

| | Baseline sample | Later checkpoint sample |
| --- | --- | --- |
| Revision | example-a | example-b |
| Model | example-model | example-model |
| Shared turns | 37 | 37 |
| Critical failures | 1 (S02.2) | 0 |
| S02.2 | critical authority fail | acceptable, grounded uncertainty |

A model change between those columns would replace the improvement sentence with: comparability limited by model change.

## 12. Open decisions

These are unresolved on purpose.

1. Adopt `ATGB-01` as the reviewed corpus? Until that decision, no result may be claimed. This package recommends the catalog as the proposal. It does not adopt it.
2. Keep Frontier Gate as the only benchmark world? It is the canonical opening and the fact set this catalog uses. Later product cycles exist outside the 2026-09-26 session orientation. This design does not move the benchmark to another scene.
3. Is human scoring against this rubric enough for the first adopted checkpoint, with playability output stored only as adjacent telemetry?
4. After adoption, is `data/validation/atgb/held_out/` the right reserved location, with a written ban on importing it from tests and on quoting it in repair notes?
5. Should the first live baseline use one trial, as proposed, or three trials for every scenario?
6. Should a generic host OOC acknowledgement that does not answer the player's actual OOC question fail response success? This proposal says yes.
7. Should S07 move from the visible set into held-out so the reserved slice is larger? Capability counts can stay the same either way.
8. What provider-call budget stops a live checkpoint? This proposal requires a budget and does not pick the number.
9. Should efficiency become a pass/fail axis in a later rubric? Rubric 01 records it and does not score it.

The pending maintenance item in `docs/NEXT_SESSION.md`, the unreconciliation of the PR-BL product orientation with later PR-EG history, is not decided here.

## 13. What this design does not do

- It does not implement a runner, a scorer, or a fixture loader.
- It does not call a provider or mutate gameplay state.
- It does not amend the Constitution, the evidence standard, the playability contract, or semantic calibration.
- It does not report an ATGB result.
- It does not show that players can communicate more successfully.
- It does not authorize production changes aimed at raising a future score.

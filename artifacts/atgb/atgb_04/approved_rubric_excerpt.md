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


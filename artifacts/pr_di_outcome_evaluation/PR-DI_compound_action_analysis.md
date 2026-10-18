# PR-DI Compound Action Analysis

Scenario utterance: `I walk closer to the notice board and pry it off the post.`

## Candidate A

- Selector: `travel` resolver, `act` operation, `fast_path_abstained=true`.
- Representation: one resolver call, no explicit decomposition into approach and pry.
- Execution: time advanced and turn counter advanced; no notice-board mutation occurred.
- Interpretation quality: partial. It found a physical/travel-ish action but lost the unsupported pry distinction.

## Candidate B

- Raw plan summary: player intends to approach the notice board and forcibly remove it.
- Action: one `act` step targeting `notice_board`, proposed resolver `exploration`, `expects_mutation=none`.
- Validation: schema-valid.
- Execution: committed through deterministic selector, but selector chose `travel`; a resolver disagreement was recorded. No board mutation occurred.
- Interpretation quality: better than A on intent/entity, still insufficient on decomposition and transaction semantics.

## Candidate C

- Round 1 called `propose_action` with `action_type=pry_off`, `target_id=notice_board`.
- Tool result rejected the shape: `operation:None`, `resolver:None`, `expects:None`, `missing_step_id`.
- Final model interpretation recognized pry as disallowed/unsupported, but it did not execute a separate approach step.

## Supported Steps And Transaction Implications

The engine evidence supports time/turn advancement, not loosening/removing the board. None of the live candidates demonstrated a clean two-step transaction where approach succeeds and pry is refused or rolled back. A future compound experiment needs explicit partial-execution policy: either atomic all-or-nothing for compound physical actions, or visible partial completion with a clear unsupported/refused second step. PR-DI does not implement rollback.

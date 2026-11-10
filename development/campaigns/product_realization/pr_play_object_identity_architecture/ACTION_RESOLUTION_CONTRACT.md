# Proposed integration with existing resolution contracts

Milestone: `pr_play_object_identity_architecture`.

## Language to meaning

Interpretation retains player language but normalizes source, target/part, medium, intended operation and dependencies. “Scribble/write/mark/copy/paint” may map to add_marking; “scratch/inscribe” may require destructive marking; “touch/tap/rest a hand/brush against” may map to transient_contact. Physical/material consequences are parameters, not per-synonym state-mutator branches. Unknown or ambiguous mapping returns clarification/unsupported. No provider call is required by the architecture; future interpretation may use the already configured parser seam within its existing budget, without per-object calls or retries.

Five separate responsibilities remain visible: language interpretation -> semantic operation -> mechanical adjudication -> authoritative outcome/application -> narration. A phrase recognized by the parser is not permission to change state.

## Existing envelope, additive extension

Reuse `ExplorationEngineResult` (`game/models.py:45`) for persistent object actions, with existing `kind: custom`/`interact`, action_id, success, state_changes, metadata and world_updates fields. Preserve normalized `noncombat_resolution` (`2026.04.noncombat.v1`) and CTIR consumption. Proposed bounded details live at `metadata.object_action` and applied summaries at `state_changes.object_modifications`. No new parallel top-level action-result format or state store. Schema normalizers and downstream allowlists need explicit updates; current consumers will otherwise drop/deny new fields.

The semantic meanings below are mapped into existing outcomes; they are not a new competing outcome enum. T04 stays in its current `metadata.transient_local_action` shape, with a pure adapter for shared consumers. Old fields/statuses must retain compatibility.

| Required meaning | Existing noncombat outcome / success state | Proposed detail and legacy success |
|---|---|---|
| Completed | closed / success | status=completed; success=true; applied deltas may be empty for transient acts |
| Partially completed | closed / neutral with per-step facts | status=partially_completed; legacy success=false to prevent blanket completion; expose completed and unattempted step IDs explicitly |
| Blocked | blocked / neutral | reason codes, no applied mutation for blocked step; success=false |
| Failed | closed / failure | Adjudicated failed attempt; success=false; any authorized costs/failure effects separately applied |
| Requires clarification | ambiguous / unknown | Needed visible target/input question; success=null; no attempt/cost |
| Requires ruleset adjudication | pending_check / unknown | Adapter binding and existing check_request when relevant; success=null; no invented roll |
| Unsupported | unsupported / unknown | Unimplemented operation/adapter capability; success=false; no attempt/cost |

`noncombat_resolution._outcome_and_codes` does not currently recognize object detail. It must explicitly map this extension and per-step partial summaries; this is integration work, not available behavior. Preserve its closed/blocked/ambiguous/unsupported/pending_check vocabulary. Internal partial success state should not be accidentally recomputed as a wholly failed action by generic raw-success normalization. Test the adapter and CTIR together. Failure with consumed resources is possible only when adapter authorizes and the same transaction applies those costs; “failed” does not automatically imply zero effects.

Required bounded detail: version, operation/request ID, semantic attempt, target instance/part, expected/result revisions, resolved steps, pending/skipped/blocked steps, validation/application status, applied delta references, unchanged consequential domains, reason codes, remaining uncertainties and disclosure-approved narrative assertions. Internal full evidence stays outside provider context. Action_id remains legacy action identity; it is not durable retry identity.

## State before publication

Intent -> adjudication -> validated proposal -> state application -> applied outcome -> narration -> immutable publication. The user-specified “validated outcome” before application is provisional, never success authority. Current API has nonmutating conversational early exits; current experimental _apply writes during resolution despite exploration's no-side-effects docstring. The integration must relocate **migrated object** writes to API staging under the existing turn scope, while preserving specialized non-object behavior. Avoid claiming current resolver purity from its docstring.

Only the applied receipt or T04 authorized transient receipt can project completed assertions. Extend `narration_authorization`, `mechanical_claims`/consequential validation and player projection explicitly before publishing new markings. Unknown object effects remain fail-closed; do not broaden inventory grants to arbitrary modifications. Pre-seal closed-surface authority still excludes hidden/abstract unsupported references; T05 composed clue disclosure stays intact. A copied known text is not a new reveal.

Seal the accepted response once. Update completed publication through existing publication_contract/immutable response owners only when application and hard validation succeed. Mutation failure publishes operational failure with no successful marking claim or completion pointer. If narration cannot validate, existing terminal policy applies; a refused/failed whole turn must roll back provisional object changes or explicitly retain an already committed mechanical result with a truthful operational response, as defined by the existing transaction boundary. Initial object path chooses rollback on pipeline exception and no completed publication. No post-seal text edits, new provider retries, or narration-to-state backflow.

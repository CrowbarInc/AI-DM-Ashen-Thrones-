# PR-BR Slice 1: Bounded GM Resolution Decision

## Implementation Summary

Implemented a minimal typed pre-narration GM resolution decision boundary in `game/gm_resolution_decision.py`.

The boundary is attached immediately after authoritative Resolution Contract construction in `game.live_resolution.attach_interaction_obligation`, before GPT narration, state mutation commits, bounded-improvisation promotion, or final emission validation.

The implementation does not replace the Resolution Contract and does not parse raw player text to decide player intent. It consumes the existing contract, resolution kind, authored scene/world corpus, and already-authorized state mutation metadata.

## Exact Integration Point

Pipeline before:

`Resolution Contract -> interaction obligation -> engine/GPT narration -> bounded improvisation/proposition validation -> final emission -> commit`

Pipeline after:

`Resolution Contract -> interaction obligation -> GMResolutionDecision -> engine/GPT narration -> decision-aware validation -> final emission -> provenance-respecting commit`

Production hook:

`game/live_resolution.py::attach_interaction_obligation`

Validation hook:

`game/immutable_valid_response.py::validate_generated_response`

Static audit hook:

`tools/audit_gm_resolution_decisions.py`

## Decision Object Schema

`GMResolutionDecision`

- `contract_id`: binds the decision to the authoritative Resolution Contract.
- `resolution_method`: records the existing resolution kind/operation that owns this turn.
- `outcome_classification`: compact outcome class such as `established_or_retrieved`, `bounded_incidental`, `epistemically_qualified`, `consequential_protected`, or `state_mutation`.
- `established_fact_refs`: references to available authoritative sources, currently scene/world authored corpus and contract discourse refs.
- `proposed_facts`: reserved typed lane for facts classified before/against narration. The first slice uses it mainly in audit results rather than as a speculative planner.
- `permitted_state_mutations`: explicit permitted mutation records, currently location transitions and structured state changes already carried by the resolution.
- `persistence_policy`: `world_truth`, `runtime_incidental`, `claim_only`, or `do_not_persist`.
- `narration_constraints`: human-readable obligations consumed by validators/review evidence.

Every field maps to a gate failure/invariant: contract identity prevents semantic bypass, permitted mutations address movement divergence, persistence policy addresses provenance promotion, and narration constraints/audits address consequential invention before commit.

## Provenance Model

The new narrow provenance vocabulary is:

- `authored_world_fact`
- `bounded_incidental`
- `npc_claim`
- `observation`
- `inference`
- `speculation`
- `generated_proposal`

Critical behavior:

- A generated proposal is not automatically world truth.
- An NPC claim is claim/testimony, not world truth.
- Explicit non-assertions such as “cannot verify X” may mention X without establishing X.
- Player repetition of a rejected generated proposal is detected by the recursive-premise auditor.

## Consequential-Authority Policy

Decision-aware auditing targets the failed-gate families:

- command authority
- official orders/procedures
- patrol route/geography
- physical investigative evidence
- notice/roster/history
- historical causal facts
- unpermitted location movement

Unsupported world-truth narration in these families is hard invalid. Epistemically qualified NPC testimony remains allowed.

## NPC Testimony Behavior

NPC statements using rumor/hearsay/recollection/belief/uncertainty frames are accepted as `npc_claim` or `speculation`, not `world_truth`.

Grounded or known consequential claims remain rejected by existing bounded-improvisation checks when proposed as authoritative bounded facts.

## Persistence Behavior

Accepted bounded incidental facts retain `runtime_incidental`.

Accepted NPC claims retain `not_world_truth`.

Rejected/generated consequential premises are not promoted by repetition; `audit_recursive_premise_consumption` detects later reuse of rejected proposal content.

## Movement / Location Behavior

Narration that says the player travels, follows, reaches, or arrives at a material destination is invalid unless the decision includes a permitted location mutation.

Existing resolved scene transitions remain allowed when `permitted_state_mutations` contains the destination.

## Narration Enforcement

`validate_generated_response` now includes `gm_resolution_decision_audit` in hard-validation metadata and rejects unauthorized decision facts with `unauthorized_resolution_decision_fact`.

The regeneration feedback instructs the model to answer using established facts, bounded incidental detail, or epistemically qualified testimony, without inventing routes, orders, authorities, physical evidence, rosters, notice history, or movement as world truth.

## C26 Semantic Ownership

The new decision builder does not accept raw player text. It consumes `resolution.metadata.resolution_contract` via `contract_mapping_from_resolution`.

Regression `test_decision_builder_consumes_contract_not_raw_player_text` proves raw text cannot override the contract classification for this new path.

## Regression Results

New targeted suite:

`tests/test_pr_br_gm_resolution_decision.py`

Result: `9 passed`

Coverage:

- Captain Thoran unsupported command authority
- recursive player adoption of unsupported Captain Thoran premise
- NPC testimony/uncertainty
- patrol evidence chain
- bounded incidental description
- notice/roster fabrication
- historical route/change fabrication
- driver-style recollection/testimony
- movement/location divergence
- safe nonresolution fallback
- contract-over-raw semantic ownership

Relevant existing deterministic suites:

`172 passed`

Command:

`pytest tests/test_pr_br_gm_resolution_decision.py tests/test_pr_br_continuation19_hard_authority.py tests/test_pr_br_continuation20_incidental_entity.py tests/test_pr_br_resolution_contract.py tests/test_pr_br_continuation25_semantic_ownership.py tests/test_pr_br_continuation26_semantic_closure.py tests/test_bounded_improvisation_authority.py tests/test_unresolved_travel_narration_authority.py tests/test_unparsed_movement_state_narration_integrity.py tests/test_pr_br_outcome_precedence.py -q --tb=short --basetemp=codex_pytest_tmp_gmrd_all1`

Only warning: existing Starlette/httpx deprecation warning from `fastapi.testclient`.

Additional adjacent batch:

`146 passed`

Command:

`pytest tests/test_bounded_improvisation_authority.py tests/test_pr_br_continuation21_subject_integrity.py tests/test_pr_br_continuation21b_referential_personhood.py tests/test_pr_br_continuation21c_referential_head.py tests/test_pr_br_continuation22_commitment.py tests/test_pr_br_continuation23_precontract_routes.py tests/test_pr_br_continuation24_contract_first_unparsed.py tests/test_pr_br_continuation27_structural_subject.py tests/test_unresolved_travel_narration_authority.py tests/test_unparsed_movement_state_narration_integrity.py tests/test_pr_br_outcome_precedence.py -q --tb=short --basetemp=codex_pytest_tmp_gmrd_rel3`

## Static Auditor Results

Auditor:

`tools/audit_gm_resolution_decisions.py`

Saved report:

`artifacts/pr_br_resolution_decision_slice/second_gate_static_audit.json`

Input:

- `artifacts/pr_br_second_full_gate/20261003T142725Z/persona_a/turns.json`
- `artifacts/pr_br_second_full_gate/20261003T142725Z/persona_b/turns.json`
- `artifacts/pr_br_second_full_gate/20261003T142725Z/persona_c/turns.json`
- `artifacts/pr_br_second_full_gate/20261003T142725Z/persona_d/turns.json`

Result:

- total targeted violations: `69`
- persona A: `18`
- persona B: `16`
- persona C: `20`
- persona D: `15`

Dominant detected classes:

- `patrol_route_or_geography`
- `physical_investigative_evidence`
- `notice_roster_history`
- `official_orders_or_procedures`

This supports the discovery finding that the previous full gate contained consequential-authority failures not covered by shallow targeted tests.

## Files Changed

Production:

- `game/gm_resolution_decision.py`
- `game/live_resolution.py`
- `game/immutable_valid_response.py`
- `game/bounded_improvisation.py`

Tests:

- `tests/test_pr_br_gm_resolution_decision.py`

Tooling/evidence:

- `tools/audit_gm_resolution_decisions.py`
- `artifacts/pr_br_resolution_decision_slice/second_gate_static_audit.json`
- `artifacts/pr_br_resolution_decision_slice/implementation_report.md`

Note: the workspace was already heavily dirty before this slice. Some diff in `game/bounded_improvisation.py` predates this implementation; this slice only intentionally extends the consequential-term guard for physical evidence/geography and relies on the already-present provenance fields.

## Known Limitations

- The consequential proposition detector is deliberately narrow and regex-based.
- The typed decision object records the boundary but does not yet drive a richer deterministic outcome planner.
- Static auditing of old second-gate captures often lacks an attached decision object, so it detects targeted authority families rather than reconstructing the exact pre-narration decision that did not exist yet.
- Existing downstream validators remain responsible for many speaker, target, and interaction-completion failures.
- No gameplay/model calls, full 4x10 rerun, or human playtest were performed.

## Deferred Debt

- Broader consequential ontology beyond the observed failed-gate families.
- Richer linkage between proposed facts and concrete authored state ids.
- Stronger persistence ledger for rejected generated proposals outside bounded-improvisation proposals.
- Full PR-BS/live validation.
- Generalized state migration, intentionally avoided.

## Recommendation

B. BOUNDARY IS PROMISING BUT REQUIRES ANOTHER DETERMINISTIC IMPLEMENTATION SLICE

Rationale: the minimal boundary now exists, consumes contract semantics, rejects the targeted consequential-authority failures, preserves bounded incidental and NPC testimony behavior, and exposes the saved gate failure class through static audit. It is not yet broad enough to justify limited live validation as the next immediate step.

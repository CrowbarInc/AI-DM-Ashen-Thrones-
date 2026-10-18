# PR-BR GM Resolution Decision Slice 2 Report

Deterministic implementation only. No gameplay/model API calls, no 4x10 gate rerun, no commit, no push.

## Responsibility Map Before Slice 2

- `contract_id`: populated by Resolution Contract before narration; resolver-owned identity consumed by decision/validation.
- `resolution_method`: populated from resolution kind/contract operation before narration; resolver-owned routing signal.
- `outcome_classification`: populated before narration, but mostly a broad constraint such as incidental/protected/mutation; partly decision-owned, not yet a positive fictional outcome.
- `established_fact_refs`: populated before narration from scene/world/contract refs; state-owned references, not proposition-level authorization.
- `proposed_facts`: mostly post-narration audit rows; validator-reconstructed rather than pre-narration authorization.
- `permitted_state_mutations`: populated before narration from resolution state changes; state/resolver-owned positive authority for movement/state.
- `persistence_policy`: populated before narration; decision-owned policy hint, but coarse.
- `narration_constraints`: populated before narration; decision-owned constraints consumed by validation, not positive outcome facts.

Net: Slice 1 put a boundary before narration, but much fictional authority was still narration-owned or validator-reconstructed.

## Final Responsibility Map

- `contract_id`: resolver-owned identity, decision consumes.
- `resolution_method`: resolver-owned method, decision consumes.
- `outcome_classification`: decision-owned outcome class, including `consequentially_unresolved` and authorized state outcomes.
- `established_fact_refs`: state-owned source references available to the decision.
- `proposed_facts`: decision-owned pre-narration authorization records for authored world facts, accepted bounded incidental continuity, NPC claims, and state outcomes.
- `permitted_state_mutations`: resolver/state-owned positive state transitions; projected into `proposed_facts`.
- `persistence_policy`: decision-owned default persistence.
- `narration_constraints`: decision-owned guardrails retained for validators and prompt-facing debug.
- `unresolved_consequential_questions`: decision-owned explicit unresolved-result lane.
- `authority_algorithm`: declares `source_provenance_v2`.

## Schema Changes

`GMProposedFact` now carries `authority`, `persistence`, `source_ref`, and `outcome_classification`.

`GMResolutionDecision` now carries `unresolved_consequential_questions` and `authority_algorithm`.

No giant ontology or Resolution Contract redesign was introduced.

## Pre-Narration Outcome Flow

Resolution Contract remains the semantic request owner. `GMResolutionDecision` now projects authorized facts before narration from authored scene/world state, accepted bounded-improvisation ledger entries, NPC claim ledger entries, and resolver/state mutations. Action/follow/confirm routes without mutation become `consequentially_unresolved`.

## Narration Input Flow

The decision remains attached at `resolution.metadata.gm_resolution_decision`. For targeted paths, narration/validation can inspect outcome class, authorized facts, provenance/authority, persistence, state mutations, unresolved consequential questions, and constraints.

## Post-Narration Validation Flow

Validation first checks whether a narrated proposition is authorized by the pre-narration decision. If not, it falls back to source/provenance checks, authored-corpus grounding, epistemic framing, movement mutation checks, and legacy known-family defenses.

## Source/Authority Algorithm

Consequential assertions are allowed when source/provenance is authored world state, accepted runtime incidental continuity, accepted claim-only NPC testimony, authorized resolver/state mutation, or grounded authored corpus. Unsupported stateful world assertions are rejected even in novel domains. NPC claims remain claim-only. Mention, repetition, player adoption, NPC assertion, model assertion, and persistence do not promote authority.

## Regex Heuristics Role

Known-family regexes remain defense-in-depth and historical audit tooling. They are no longer the only path: novel-domain tests fail on `unowned_stateful_world_assertion` without captain/patrol/roster/notice/bootprint/route vocabulary.

## Provenance Persistence Behavior

Accepted bounded incidental details project into later decisions as `bounded_incidental` with `runtime_incidental` persistence. NPC claims project as `claim_only` with `claim_only` persistence. Authored facts remain `world_truth`.

## Rejected-Premise Behavior

The existing bounded-improvisation rejected ledger is reused. Rejected generated propositions are detected on later player/prose reuse and are not projected into future `GMResolutionDecision` facts.

## Test Design And Results

- Slice-2 novel-domain tests: passed, 7 tests in `tests/test_pr_br_decision_ownership_slice2.py`.
- Adversarial paraphrase tests: passed through novel stateful assertions and paraphrased movement arrival.
- Positive authorization tests: passed for authored facts, state transitions, NPC claims, and bounded incidental continuity.
- Multi-turn provenance tests: passed for rejected premise, NPC claim, bounded incidental, and authorized world fact behavior. Later explicit promotion is represented by authored/resolver source projection; no implicit promotion through repetition.
- Movement decision ownership: passed; movement is blocked without a location mutation and allowed with pre-narration state outcome.
- Slice-1 targeted regressions: `tests/test_pr_br_gm_resolution_decision.py` passed.
- C18-C27 regressions and bounded-improvisation tests: 164 passed with isolated basetemp.
- Saved-gate deterministic audit/replay: saved second-gate static audit reports 69 violations: 2 `DECISION_SOURCE_AUTHORITY_VIOLATION`, 67 `KNOWN_FAMILY_HEURISTIC_VIOLATION`. Old turns generally lack reconstructable pre-narration Slice 2 decisions, so prevention is not claimed for all 69.

## Commands Run

- `python -m pytest tests\test_pr_br_decision_ownership_slice2.py tests\test_pr_br_gm_resolution_decision.py -q --tb=short`
- `python -m pytest tests\test_pr_br_continuation18_immutable_boundary.py ... tests\test_pr_br_continuation27_structural_subject.py tests\test_bounded_improvisation_authority.py -q --tb=short --basetemp=codex_pytest_tmp_slice2`
- `python tools\audit_gm_resolution_decisions.py <saved second-gate turns.json files> -o artifacts\pr_br_resolution_decision_slice2\second_gate_saved_static_audit.json`

## Files Changed

- `game/gm_resolution_decision.py`
- `tools/audit_gm_resolution_decisions.py`
- `tests/test_pr_br_decision_ownership_slice2.py`
- `artifacts/pr_br_resolution_decision_slice2/implementation_report.md`
- `artifacts/pr_br_resolution_decision_slice2/second_gate_saved_static_audit.json`

## Known Limitations

The structural consequential detector is intentionally small and will not understand arbitrary generated prose. Old saved-gate turns often cannot reconstruct pre-narration decisions. The decision fact matching is token/subset based, not semantic entailment. This is an improvement in ownership, not proof against live model paraphrase breadth.

## API/Model Cost Implications

No new model calls are introduced. The slice is deterministic and uses existing runtime state plus lightweight regex/token checks.

## Recommendation

B.
DECISION OWNERSHIP IS IMPROVED BUT ANOTHER DETERMINISTIC SLICE IS REQUIRED

# PR-CI Immutable Response Integrity

The repair does not bypass immutable response handling.

Implementation placement:

- Projection occurs before `validate_generated_response`.
- The projected response is then validated by the existing hard-validation path.
- The validated response is sealed through `seal_accepted_response`.
- Later semantic mutators still skip immutable responses.

Integrity evidence:

- `tests/test_pr_br_continuation18_immutable_boundary.py` passed.
- `tests/test_turn_packet_stage_diff_integration.py` passed.
- `tests/test_final_emission_gate.py` passed.
- New lower-level test confirms the authored answer is sealed immutable after pre-seal projection.


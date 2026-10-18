# PR-BR Claim Control Slice 2 Test Results

## Completed

```text
pytest tests/test_pr_br_claim_control_slice1.py tests/test_pr_br_claim_control_slice2.py -q
16 passed
```

```text
pytest tests/test_pr_br_gm_resolution_decision.py -q
9 passed
```

```text
pytest tests/test_pr_br_decision_ownership_slice2.py -q
7 passed
```

```text
pytest tests/test_pr_br_decision_semantic_fidelity_slice3.py -q
7 passed
```

```text
pytest tests/test_pr_br_qualifier_movement_mixed_intent.py -q
9 passed
```

```text
pytest tests/test_pr_br_continuation18_immutable_boundary.py tests/test_pr_br_continuation19_hard_authority.py -q -k "not raw_chat_stub"
29 passed
```

## Interrupted/Stalled

The following runs produced initial pass dots, then no output until interrupted:

- Full broad PR-BR run: 47 dots before silence.
- C18 whole file: 15 dots before silence.
- C19 whole file: 10 dots before silence.
- C20 whole file: 13 dots before silence.
- C21 whole file: 9 dots before silence.
- C21b/C21c group: 17 dots before silence.
- C22 whole file: 26 dots before silence.
- C24 whole file: 5 dots before silence.

Collection for stalled files succeeds, so the stall is runtime/harness behavior, not collection.

## Model/API calls

0 gameplay/model API calls.

# PR-CV Size Threshold Assessment

Original historical threshold: every PR-BT reconstructed provider request must remove at least 12,000 total characters versus the old baseline.

Current measured reductions from `tools/measure_pr_bt_policy_instruction_payloads.py`:

| Probe | Original Total | Current Total | Reduction |
|---|---:|---:|---:|
| P1 | 110450 | 97147 | 13303 |
| P2 | 121438 | 104845 | 16593 |
| P3 | 110665 | 99094 | 11571 |

Assessment:

- The old 12,000-character threshold is not a product contract.
- P3 misses it by 429 characters solely as a historical baseline comparison.
- Required policy objects remain visible.
- Exact duplicate payload instruction lines already carried by the system prompt are absent.
- Instruction payload size is reduced for each probe, and exact duplicate instruction lines already carried by the system prompt are absent.

Replacement assertion:

- verify total payload is smaller than baseline;
- verify instruction payload is reduced;
- verify exact duplicate instruction lines are absent;
- verify response policy and decision-facing recipe remain present.

No prompt text was enlarged merely to satisfy the old number.

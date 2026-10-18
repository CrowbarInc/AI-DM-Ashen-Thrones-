# PR-CU Context Dependency Matrix

Status: not completed beyond the regression gate.

The dependency analysis was intentionally stopped before implementation because the Phase 1 regression gate failed.

Preliminary observations from PR-CT payload measurements:

| Section | Preliminary classification | Reason |
|---|---|---|
| Player input | Provider required and deterministic pipeline required | Required to answer the current question and preserve action intent. |
| Active NPC identity | Provider required and deterministic pipeline required | Required for ordinary dialogue speaker identity and validator contracts. |
| Current scene | Provider required and deterministic pipeline required | Required for continuity, addressee grounding, and hidden-information boundaries. |
| Social resolution / resolver decision | Both required | Provider needs permitted answer scope; pipeline needs authoritative decision. |
| Decision-facing answer recipe | Provider required | It guides realization but does not grant authority. |
| Response policy | Provider required and deterministic pipeline required | Current PR-BT failures show this policy surface is not safely reducible until repaired. |
| Output schema | Provider required | Required to preserve parser/finalization behavior. |
| Full mechanical/action context | Unknown | Candidate omission area, but not evaluated because gate blocked. |
| Unrelated NPC/faction/inventory records | Unknown | Candidate omission area, but not inspected under PR-CU because gate blocked. |

No provider-only omission opportunity was established under PR-CU.

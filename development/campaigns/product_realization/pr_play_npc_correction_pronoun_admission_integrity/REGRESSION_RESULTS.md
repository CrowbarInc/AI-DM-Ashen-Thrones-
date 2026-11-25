# Regression results

| Suite | Prior passed / failed | Current passed / failed | Evidence |
| --- | --- | --- | --- |
| Combined | 455 / 17 | 455 / 17 | [Evidence](evidence/combined_recheck/historical_order/result.json) |
| Focused | 470 / 1 | 470 / 1 | [Evidence](evidence/regression/final/focused/result.json) |
| Scoped | 191 / 0 | 191 / 0 | [Evidence](evidence/regression/final/scoped/result.json) |
| Historical recall | 71 / 0 | 71 / 0 | [Evidence](evidence/regression/final/recall/result.json) |
| Inspection admission | 64 / 0 | 64 / 0 | [Evidence](evidence/regression/final/inspection/result.json) |
| Statement ownership | 65 / 0 | 65 / 0 | [Evidence](evidence/regression/final/ownership/result.json) |
| NPC addressee and social commitment | 71 / 0 | 71 / 0 | [Evidence](evidence/regression/final/acceptance/result.json) |
| Social grounding reconciliation | 37 / 0 | 37 / 0 | [Evidence](evidence/regression/final/reconciliation/result.json) |
| Incidental posture | 85 / 0 | 85 / 0 | [Evidence](evidence/regression/final/posture/result.json) |
| Current-scene evidence | 84 / 0 | 84 / 0 | [Evidence](evidence/regression/final/scene/result.json) |
| Harness reconciliation | 43 / 0 | 43 / 0 | [Evidence](evidence/regression/final/harness/result.json) |

New failure identities **0**. Missing suite results **0**.
The first combined run repartitioned the recorded selection and returned **454 / 18**. The additional
`test_token_estimate_unavailable_is_operational` failure reproduced with the prior archived source on the
same 59-test partition. Both source versions produced **57 / 2** with identical failure identities. The fixture
enables interpretation, and a cold import of the experiment package can disable it before the estimate
boundary. The combined result in the table uses the historical partition memberships and order.

The supplemental correction-contract comparison has 6 prior and
6 current failures. The baseline loaded the five production modules from the
previous verified archive with the same offline fixtures.

[First combined run](evidence/regression/final/combined/result.json) · [Repartitioned prior source](evidence/combined_recheck/baseline/06.xml) · [Repartitioned repaired source](evidence/combined_recheck/current/06.xml) · [Supplemental prior](evidence/correction_contract_baseline.xml) · [Supplemental current](evidence/correction_contract_current.xml)

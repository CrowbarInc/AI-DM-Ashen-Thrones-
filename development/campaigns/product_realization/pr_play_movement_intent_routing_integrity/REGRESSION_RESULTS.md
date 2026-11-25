# Regression results

| Suite | Historical pass / fail | Current pass / fail | New failure identities |
| --- | ---: | ---: | ---: |
| Combined | 455 / 17 | 455 / 17 | 0 |
| Focused | 470 / 1 | 470 / 1 | 0 |
| Scoped | 191 / 0 | 191 / 0 | 0 |
| Inspection admission | 64 / 0 | 64 / 0 | 0 |
| Statement ownership | 65 / 0 | 65 / 0 | 0 |
| NPC addressee and social commitment | 71 / 0 | 71 / 0 | 0 |
| Social grounding reconciliation | 37 / 0 | 37 / 0 | 0 |
| Incidental posture | 85 / 0 | 85 / 0 | 0 |
| Current-scene evidence | 84 / 0 | 84 / 0 | 0 |
| Harness reconciliation | 43 / 0 | 43 / 0 | 0 |

New established failure identities **0**. The runner uses the recorded suite selection and partition order, hashes production sources around each partition, and compares exact failure identities. Established inherited failures are preserved in the per-suite manifest and xUnit output.

Historical recall **71/71**. Prior reference **116/116** (111 synthetic plus 5 exact), attention **105/105** (103 plus T02 and T03 diagnostics), correction **106/106** (97 synthetic, 7 sequence and 2 exact/controlled), clarification recovery **120/120** (115 controls, 4 exact and 1 exact sequence), combat **5/5**. Prior milestone duplicate baseline **472**.

An initial runner imported application storage before pytest isolated it. The repository write guard denied those attempted writes and the temporary-file allocator stalled retrying them. The final runner lets pytest configure storage before importing the application and reruns the recorded partitions from scratch.

[Partition results](evidence/regression_isolated) · [Prior acceptance](evidence/prior_acceptance/runner_status.json) · [Board replay](evidence/board/exact.json)

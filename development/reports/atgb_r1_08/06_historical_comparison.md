# 06 — Historical Comparison

| Dimension | R1-05 L1/L2 historical | R1-08 L1 | R1-08 L2 |
|---|---|---|---|
| Correction routing | repaired guard abstains | not reached after provider failure | not run |
| Subject recognition | correct people/weather contrast | unavailable | not run |
| Mode/purpose | redundant CLARIFICATION | unavailable | not run |
| Evidence | [] despite visible:1–3 | unavailable, not [] | not run |
| Response adequacy | failed redundant confirmation | failed operational fallback | not run |
| Authority | preserved in tested controls | preserved failed-call state | not run |
| Usage | 2215 / 2214 tokens | unknown after admitted failed dispatch | no admission |

R1-03 L3 historical: “Do you want a description of the people present at the gate district instead of the weather?” GM/CLARIFICATION, no evidence selected. R1-06 corrected the older trace summary: raw L3 does reach _pending_revision_decision, returning null. Historical reports/records remain unchanged. New L3 was not run; no paraphrase comparison possible.

R1-05 L4 historical: live revision preserved pending status and original NPC choices without executing; topic/recipient conflation remains a documented limitation. New L4 was not run, so neither preservation nor regression can be claimed.

Configured model gpt-4.1-mini, temperature 0, production output cap 320 and SDK retries 0 match historical settings. Historical returned model was gpt-4.1-mini-2025-04-14; new returned model unknown. Per-trial admission allowance tightened to one; no generation setting changed. Same preserved S08.1 reconstruction, fresh identities and isolated process/store. L1 failure resembles R1-03's connection failure but does not establish the same root cause. No live improvement, regression, broad reliability, independent generalization or benchmark score is established.

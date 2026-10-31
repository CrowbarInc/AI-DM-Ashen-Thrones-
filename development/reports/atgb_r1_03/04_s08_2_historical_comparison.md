# 04 — S08.2 Historical Comparison

Historical baseline is immutable ATGB-03C S08 trial 1: ATGB-01 scenario / ATGB-02 corpus, related_variation, frontier-gate-v1. Exact original S08.1 and response are in transcripts.md and original transcript included in the ZIP. No separate opening was omitted. World facts include visible serjeant, runner, watchers and refugees. Initially no interlocutor, pending intention, discovered clue or world flag. S08.2 should correct the descriptive focus toward those people.

| Dimension | Historical S08.2 | L1 | L2 |
| --- | --- | --- | --- |
| Response | I don't have an unexecuted intention to revise. What do you want to change? | Interpretation failure fallback | Interpretation failure fallback |
| Mechanical route | no_pending_intention; demonstrated wrong entry | Not reached | Not reached |
| Interpretation | Raw provider interpretation unavailable; provisional fail from output | Unavailable | Unavailable |
| Evidence selection | Original raw selected refs not retained | Candidate public facts available, no model selection | Same |
| Adequacy | FAIL | FAIL fallback | FAIL fallback |
| Authority | Historical provisional PASS | PASS for attempted execution | PASS for attempted execution |
| Admissions | 1 interpretation, 0 narration | 1 failed dispatch | 1 failed dispatch |
| Tokens in/out | 2004 / 210 | Unavailable | Unavailable |
| Latency | Historical host 1850 ms | See measured accounting; different timing boundary | See measured accounting; different timing boundary |

Configured model remains gpt-4.1-mini; historical actual gpt-4.1-mini-2025-04-14. L1/L2 have no returned model identifier. L3 returns that same dated model but is only the paraphrase, not an original-wording reproduction. SDK retry policy now explicitly zero; historical SDK retry bounds were not established. Replay uses exact preceding text/log plus fresh reset and current memory construction, rather than an unavailable original intermediate session snapshot. These limitations preclude strict before/after equivalence. Historical timing and current wall-clock timing are not a controlled latency comparison; no repair cost delta is established.

1. Original mechanical failure eliminated live: NOT DEMONSTRATED (gate not reached).
2. Original conversational interpretation improved: INDETERMINATE.
3. Original evidence selection improved: INDETERMINATE.
4. Original response adequacy improved: NOT DEMONSTRATED.
5. Authority: preserved in L1/L2 attempted execution; invalid L4 fallback violated its revision contract in isolated state.
6. Performance costs: current measurements retained; no reliable repair-attributable delta.

Outcome C — Repair not reliably demonstrated, because execution evidence is insufficient. This is not a finding that the repaired regex failed. L3 recognizes the people subject but asks redundant confirmation and supplies none of the available people facts. It cannot replace either missing original trial or establish independent generalization.

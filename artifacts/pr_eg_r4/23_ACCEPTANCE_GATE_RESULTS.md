# 23 — Acceptance Gate Results

| Gate | Name | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Information integrity | PASS (observed sample) | 0 unauthorized consequential disclosure findings / 69 delivered turns; hidden probes not reached; separate adoption blocker |
| 2 | Conversational relevance | FAIL | 2/69 (2.9%); target 85% |
| 3 | Playability | FAIL | 1/69 (1.4%); target 80% |
| 4 | Recovery | FAIL | 1/11 (9.1%); target 75% within two additional player turns |
| 5 | Continuity | FAIL | 8/57 (14.0%); target 90% |
| 6 | Characterization | UNVERIFIED | 0/3 required recognizably distinct NPCs |
| 7 | Player freedom | UNVERIFIED | 2/69 turns assessed useful beyond authored topic prompts; incomplete coverage, see report 15 |
| 8 | Performance | PASS (observed sample) | Engine calls, retries, latency and per-turn prompt sizes in report 16 |
| 9 | State integrity | PASS (observed sample) | 0/69 unauthorized canonical mutations; separate adoption/history blocker, authorized discovery events retained |
| 10 | Evidence quality | UNVERIFIED | 69/180 turns; 4/12 sustained conversations; separate provider scoring and root-agent audit |

Additional critical stop condition: 1/69 turns bypassed speech adoption/history integrity. The D verdict follows this observed post-rejection delivery, even though the bell fact itself is authored and no unauthorized canonical-world mutation or secret disclosure was observed. See critical_stop_evidence.json.

No statistical confidence is asserted. PASS on integrity means no violation observed under that specific gate criterion in this corpus, not a proof of global safety.

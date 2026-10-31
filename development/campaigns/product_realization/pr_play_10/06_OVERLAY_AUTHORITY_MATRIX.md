# 06 — Overlay Authority Matrix

PR-PLAY-10 · 2026-10-30 America/New_York · evidence_scope: structural_only.

All O1–O15 passed their explicit comparison expectations. Machine-readable records contain
fixture, operation, expected result, actual changed values, reasons/evidence and pass/fail.
O1 active authored addition allowed; O2 rejected opening leak flagged; O3 no structured update
flagged; O4 extra existing mutation flagged; O5 removal flagged; O6 wrong-scene addition flagged;
O7 contradiction flagged; O8 protected fact flagged; O9 undocumented metadata flagged (no
overlay bookkeeping exclusion exists); O10 unchanged subsequent state preserved; O11 failed
opening unchanged; O12 repeated start unchanged; O13 concurrent commit once; O14 unrelated
overlays preserved; O15 malformed root flagged. O7/O8 are harness negative controls, not claims
that the legacy shape-only gateway independently rejects every semantic violation.

The table's O12/O13 comparison controls are supplemented by real endpoint evidence: replay
checks repeat 409 with no second SDK stub request; concurrent_overlay.json records 200/409,
one SDK stub request and exactly the historical final overlays. O11 has a real save-failure
rollback control. Missing-root active initialization and unrelated observatory vocabulary have
additional focused coverage. Malformed changed roots fail explicitly; unchanged malformed
state is not a substitute for the production persistence-coherency validation lane.

| Case | Expected integrity | Actual integrity | Result |
| --- | --- | --- | --- |
| O1 | True | True | PASS |
| O2 | False | False | PASS |
| O3 | False | False | PASS |
| O4 | False | False | PASS |
| O5 | False | False | PASS |
| O6 | False | False | PASS |
| O7 | False | False | PASS |
| O8 | False | False | PASS |
| O9 | False | False | PASS |
| O10 | True | True | PASS |
| O11 | True | True | PASS |
| O12 | True | True | PASS |
| O13 | True | True | PASS |
| O14 | True | True | PASS |
| O15 | False | False | PASS |

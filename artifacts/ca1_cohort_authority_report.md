# CA1 Corrective Change Locality Cohort Authority Report

> CA1 repository-owned reviewed cohort authority. Read-side validation and reporting only.

## Summary

- **Qualifying entries:** 10
- **Exclusion entries:** 1
- **Total rows:** 11

### Confidence distribution (qualifying)

- **high**: 8
- **medium**: 2

### Repair family distribution (qualifying)

- **opening_fallback**: 6
- **ci_import**: 1
- **dialogue_routing**: 1
- **replay_log**: 1
- **routing**: 1

### Recurrence evidence distribution (qualifying)

- **related_family_only**: 6
- **none**: 4

## Qualifying cohort

- **CA-01** `09863c6` (2026-03-21) — dialogue_routing, confidence=medium, total=7, effective=7
- **CA-02** `ceecc57` (2026-04-16) — opening_fallback, confidence=medium, total=20, effective=20
- **CA-03** `6351b33` (2026-04-25) — opening_fallback, confidence=high, total=16, effective=16
- **CA-04** `2013258` (2026-04-25) — opening_fallback, confidence=high, total=7, effective=7
- **CA-05** `9e83820` (2026-04-26) — opening_fallback, confidence=high, total=7, effective=7
- **CA-06** `1b3b3ee` (2026-04-26) — opening_fallback, confidence=high, total=5, effective=5
- **CA-07** `f487f4d` (2026-04-26) — opening_fallback, confidence=high, total=216, effective=6
- **CA-08** `f3fa4b1` (2026-04-26) — replay_log, confidence=high, total=52, effective=8
- **CA-09** `5cb8444` (2026-04-26) — routing, confidence=high, total=538, effective=4
- **CA-10** `6a402d2` (2026-05-20) — ci_import, confidence=high, total=9, effective=9

## Exclusion controls

- **EX-01** `2b293b2` — Only mutable runtime snapshots changed; no production source repair or regression evidence

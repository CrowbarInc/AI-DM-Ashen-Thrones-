# BQ3.7 Recurrence History Migration

**Date:** 2026-06-20T03:18:06Z
**Source:** `event_log`

## Migration Summary

| Population | Events |
|---|---:|
| Original unified log | 43 |
| Protected replay history | 1 |
| Session diagnostic history | 42 |

## Protected Population

| Metric | Value |
|---|---|
| Events | 1 |
| Unique Keys | 1 |
| Numerator | 0 |
| Denominator | 1 |
| Rate | 0.0% |

## Diagnostic Population

| Metric | Value |
|---|---|
| Events | 42 |
| Unique Keys | 6 |

## Archived Artifact

Location:
`artifacts/golden_replay/bug_recurrence_event_log.legacy.json`

## Verification

Confirm:
- no events lost: `true`
- counts reconcile: `true`
- metrics regenerated: `true`
- diagnostic keys absent from protected history: `true`

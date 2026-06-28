# BQ3.7 Recurrence History Migration

**Date:** 2026-06-28T19:35:14Z
**Source:** `legacy_archive`

## Migration Summary

| Population | Events |
|---|---:|
| Original unified log | 43 |
| Protected replay history | 1 |
| Session diagnostic history | 32 |
| Synthetic/test artifact history | 10 |
| Legacy diagnostic compatibility output | 42 |

## Protected Population

| Metric | Value |
|---|---|
| Events | 1 |
| Unique Keys | 1 |
| Numerator | 0 |
| Denominator | 1 |
| Rate | 0.0% |

## Session Diagnostic Population

| Metric | Value |
|---|---|
| Events | 32 |
| Unique Keys | 6 |

## Synthetic/Test Artifact Population

| Metric | Value |
|---|---|
| Events | 10 |
| Unique Keys | 1 |

## Legacy Diagnostic Compatibility Output

Compatibility-only combined diagnostic output retained for existing consumers:
`artifacts/golden_replay/bug_recurrence_session_diagnostic_event_log.json`

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

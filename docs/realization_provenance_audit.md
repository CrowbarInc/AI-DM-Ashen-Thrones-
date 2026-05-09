# Realization Provenance Coverage Audit

`tools/realization_provenance_audit.py` is an advisory static scanner for
fallback provenance coverage. It looks for likely player-facing fallback,
emergency, terminal, and repair prose paths that may need
`realization_fallback_family` metadata.

## How to run

From the repo root:

```bash
python tools/realization_provenance_audit.py
```

The tool prints a console summary and writes:

- `artifacts/realization_provenance_audit/realization_provenance_audit.json`
- `artifacts/realization_provenance_audit/realization_provenance_audit.md`

## What it scans

The audit currently scans likely fallback/prose files:

- `game/api.py`
- `game/gm.py`
- `game/gm_retry.py`
- `game/final_emission_gate.py`
- `game/final_emission_repairs.py`
- `game/social_exchange_emission.py`
- `game/upstream_response_repairs.py`
- `game/diegetic_fallback_narration.py`

It looks for fallback and player-facing prose indicators such as `fallback`,
`emergency`, `terminal`, `repair`, `player_facing_text`, `final_emitted_source`,
`upstream_prepared_emission`, `prepared_answer_fallback_text`,
`prepared_action_fallback_text`, `gm_output`, text replacement, and forced retry.

Nearby references to `realization_fallback_family`,
`REALIZATION_FALLBACK_FAMILY_FIELD`, or `attach_realization_fallback_family`
mark the context as already labeled.

## Severity meanings

- `HIGH`: Likely player-facing fallback or emergency prose lacks nearby
  provenance metadata.
- `REVIEW`: A fallback or repair pathway has ambiguous player-facing status and
  should be inspected.
- `INFO`: The context is already labeled or appears to be comment/doc-only.

## Advisory status

This audit is not wired into CI as a failing check. Findings are a coverage map,
not proof of a runtime behavior bug. The report is meant to help future blocks
decide where metadata-only provenance labels may still be missing without
changing emitted prose or runtime behavior.

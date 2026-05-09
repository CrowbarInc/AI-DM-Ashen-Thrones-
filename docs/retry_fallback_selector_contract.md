# Retry Fallback Selector Contract

`game.gm_retry` keeps retry fallback work split between pure selectors and mutating callers.

## Selectors

Selectors choose the fallback branch and line. They may inspect the already supplied retry inputs and return a scratch payload, but they must not stamp the public GM output.

Current selectors:

- `select_deterministic_retry_fallback_line(...)`
- `select_terminal_retry_fallback_line(...)`

Expected return shape:

```python
{
    "text": "...",
    "source": "branch_or_line_source",
    "realization_fallback_family": "retry_terminal_fallback",
    "debug": {...},
}
```

Selectors may include scratch fields such as `gm_output`, `scope`, `gm_work`, or `res_for_social` when the caller needs them to preserve current behavior. Those scratch fields are not authoritative public emission metadata.

## Callers

The mutating callers own public output assembly:

- `apply_deterministic_retry_fallback(...)`
- `force_terminal_retry_fallback(...)`

Callers are responsible for:

- writing `player_facing_text`
- preserving existing metadata and FEM payloads
- attaching `realization_fallback_family`
- attaching retry scope debug
- recording stage telemetry
- preserving fallback provenance
- maintaining route, tag, retry, and failure fields

## Forbidden Selector Responsibilities

Selectors must not:

- mutate the input `gm` or `base_gm`
- attach metadata or FEM provenance directly
- call final emission gate code
- record stage telemetry
- perform API calls
- change emitted prose while selecting a branch

## Why

Retry fallback selection is failure-locality code. Keeping selection separate from assembly makes it easier to verify that branch choice, emitted prose, provenance stamping, and telemetry do not accidentally become one coupled dependency hub again.

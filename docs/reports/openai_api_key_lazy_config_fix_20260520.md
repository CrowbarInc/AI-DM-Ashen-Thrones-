# OpenAI API Key Lazy Config Fix - 2026-05-20

## Failure Path

CI failed while collecting/running `tests/test_final_emission_boundary_convergence.py` without `OPENAI_API_KEY`.

Observed import chain:

```text
tests/test_final_emission_boundary_convergence.py
-> game/final_emission_gate.py
-> game/final_emission_validators.py
-> game/social_exchange_emission.py
-> hard_reject_social_exchange_text
-> from game.gm import question_resolution_rule_check
-> game/config.py
-> OPENAI_API_KEY = _getenv_required("OPENAI_API_KEY")
-> RuntimeError
```

## Files Changed

- `game/config.py`
- `game/gm.py`
- `game/api_upstream_preflight.py`
- `tests/test_api_upstream_preflight.py`
- `tests/test_model_routing_config.py`
- `tests/test_model_routing_runtime.py`
- `tests/test_model_routing_escalation.py`
- `tests/test_realization_provenance.py`
- `docs/reports/openai_api_key_lazy_config_fix_20260520.md`

## Import-Safe Behavior

`game.config` no longer validates `OPENAI_API_KEY` at module import time. Non-secret config remains import-safe:

- `MODEL_NAME`
- `DEFAULT_MODEL_NAME`
- `HIGH_PRECISION_MODEL_NAME`
- `RETRY_ESCALATION_MODEL_NAME`
- `ENABLE_MODEL_ROUTING`

`game.gm` also imports safely without `OPENAI_API_KEY`, so deterministic helper imports through final-emission/social-exchange validation no longer require a live secret.

## Runtime Secret Boundary

`game.config.get_openai_api_key()` now performs the required secret lookup lazily via `_getenv_required("OPENAI_API_KEY")`.

The key is still required when upstream API work is actually attempted:

- `game.gm.call_gpt(...)` calls `get_openai_api_key()` immediately before constructing `OpenAI(api_key=...)`.
- `game.api_upstream_preflight.run_upstream_api_preflight(...)` calls `get_openai_api_key()` only when no explicit `api_key` argument is supplied and the preflight actually runs.

This does not add dummy CI/test secrets and does not weaken validation for real upstream use.

## Tests Updated

`tests/test_model_routing_config.py` now verifies:

- `game.config` imports without `OPENAI_API_KEY`.
- `game.gm` imports without `OPENAI_API_KEY`.
- `get_openai_api_key()` raises `RuntimeError: Missing required environment variable: OPENAI_API_KEY` when the key is absent.

Mocked `call_gpt` OpenAI-client tests now set a local test key at the call boundary, matching the new lazy runtime requirement.

## Validation

Focused requested tests:

```text
python -m pytest tests/test_final_emission_boundary_convergence.py -q
```

Result:

```text
21 passed
```

```text
python -m pytest tests/test_dead_turn_evaluation_threading.py -q
```

Result:

```text
9 passed
```

```text
python -m pytest tests/test_model_routing_config.py -q
```

Result:

```text
4 passed
```

```text
python -m pytest tests/test_api_upstream_preflight.py -q
```

Result:

```text
15 passed
```

CI boundary slice:

```text
python -m pytest tests/test_final_emission_boundary_convergence.py tests/test_dead_turn_evaluation_threading.py tests/test_playability_eval.py tests/test_behavioral_gauntlet_eval.py tests/test_scenario_spine_eval.py tests/test_final_emission_meta.py tests/test_architecture_audit_tool.py tests/test_validation_layer_audit_smoke.py -q
```

Result:

```text
136 passed
```

Additional touched-test validation:

```text
python -m pytest tests/test_model_routing_runtime.py tests/test_model_routing_escalation.py tests/test_realization_provenance.py -q
```

Result:

```text
23 passed
```

Missing-key import simulation with shell `OPENAI_API_KEY` unset and dotenv loading suppressed:

```text
config_import_ok True
gm_import_ok True
key_runtime_error Missing required environment variable: OPENAI_API_KEY
```

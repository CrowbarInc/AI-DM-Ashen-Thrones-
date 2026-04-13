# Model Routing Architecture

- Deterministic engine stages and payload contracts are unchanged.
- Hybrid routing only changes which model receives a live GPT call.
- Routing is driven by explicit runtime signals already present at the call site.
- Current route inputs come through `game.gm.call_gpt(...)`:
  `purpose`, `retry_attempt`, `retry_reason`, `strict_social`, and `force_high_precision`.
- Environment config defines the default lane and fallback chain:
  `MODEL_NAME` -> `DEFAULT_MODEL_NAME` -> `HIGH_PRECISION_MODEL_NAME` -> `RETRY_ESCALATION_MODEL_NAME`.
- Actual model selection happens per request in `game.model_routing.resolve_model_route(...)`.
- Current escalation triggers are:
  `strict_social`
  `retry_attempt`
  `retry_reason:<reason>`
  `force_high_precision`
- `strict_social` and retry escalation can select a stronger configured model.
- Deterministic or non-GPT repair paths are outside the routing system.
- Fast fallback, local repair, and terminal retry fallback keep their existing behavior.
- Player-facing response schema is unchanged by routing.

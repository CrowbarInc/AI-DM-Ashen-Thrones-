"""Stop conditions for a future live run.

No dollar amount is assumed. A cost ceiling is enforceable only when the run
supplies a price and the turn reports token counts.
"""

from __future__ import annotations

from dataclasses import dataclass

from tools.atgb import UNAVAILABLE


class BudgetError(RuntimeError):
    """The run asked for a ceiling that cannot be enforced, or a live run has no ceiling."""


@dataclass
class Budget:
    max_provider_calls: int | None = None
    max_tokens: int | None = None
    max_estimated_cost: float | None = None
    max_elapsed_seconds: float | None = None
    price_per_million_input_tokens: float | None = None
    price_per_million_output_tokens: float | None = None

    def validate(self, *, mode: str) -> None:
        for name, value in (
            ("max_provider_calls", self.max_provider_calls),
            ("max_tokens", self.max_tokens),
            ("max_elapsed_seconds", self.max_elapsed_seconds),
        ):
            if value is not None and value < 0:
                raise BudgetError(f"{name} cannot be negative.")
        if self.max_estimated_cost is not None and self.max_estimated_cost < 0:
            raise BudgetError("max_estimated_cost cannot be negative.")
        priced = self.price_per_million_input_tokens is not None or self.price_per_million_output_tokens is not None
        if self.max_estimated_cost is not None and not (
            self.price_per_million_input_tokens is not None and self.price_per_million_output_tokens is not None
        ):
            raise BudgetError(
                "A cost ceiling was set, but this run has no price for both input and output tokens. "
                "No dollar budget is invented, and the ceiling is not silently ignored."
            )
        if priced and self.max_estimated_cost is None and mode == "live_provider":
            raise BudgetError(
                "A price table was supplied without a cost ceiling. "
                "Live execution does not invent a default dollar budget; omit the prices or set the ceiling."
            )
        if mode == "live_provider":
            if self.max_provider_calls is None or self.max_elapsed_seconds is None:
                raise BudgetError(
                    "Live execution requires an explicit max_provider_calls and max_elapsed_seconds. "
                    "Those values are not defaulted."
                )

    def as_dict(self) -> dict[str, object]:
        return {
            "max_provider_calls": self.max_provider_calls,
            "max_tokens": self.max_tokens,
            "max_estimated_cost": self.max_estimated_cost,
            "max_elapsed_seconds": self.max_elapsed_seconds,
            "price_per_million_input_tokens": self.price_per_million_input_tokens,
            "price_per_million_output_tokens": self.price_per_million_output_tokens,
            "default_dollar_budget": None,
            "cost_note": (
                "Cost is unavailable unless both token counts are recorded and both prices were supplied."
            ),
        }


def telemetry_value(field: dict | None) -> tuple[str, int | float | None]:
    if not isinstance(field, dict):
        return UNAVAILABLE, None
    status = str(field.get("status") or UNAVAILABLE)
    value = field.get("value")
    if status != "recorded":
        return status, None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return UNAVAILABLE, None
    return status, value


def estimated_cost(turn_telemetry: dict, budget: Budget) -> dict[str, object]:
    if budget.price_per_million_input_tokens is None or budget.price_per_million_output_tokens is None:
        return {"status": UNAVAILABLE, "value": None, "reason": "no_price_table"}
    input_status, input_tokens = telemetry_value(turn_telemetry.get("input_tokens"))
    output_status, output_tokens = telemetry_value(turn_telemetry.get("output_tokens"))
    if input_status != "recorded" or output_status != "recorded":
        return {
            "status": UNAVAILABLE,
            "value": None,
            "reason": "token_counts_not_recorded",
            "input_status": input_status,
            "output_status": output_status,
        }
    cost = (
        (float(input_tokens) / 1_000_000) * float(budget.price_per_million_input_tokens)
        + (float(output_tokens) / 1_000_000) * float(budget.price_per_million_output_tokens)
    )
    return {"status": "recorded", "value": cost, "reason": "priced_from_recorded_tokens"}


def stop_reason(
    *,
    budget: Budget,
    mode: str,
    elapsed_seconds: float,
    provider_calls: int | None,
    tokens: int | None,
    token_status: str,
    cost: float | None,
    cost_status: str,
) -> str | None:
    """Return a stop reason before the next turn, or None when the turn may start."""

    if budget.max_elapsed_seconds is not None and elapsed_seconds >= budget.max_elapsed_seconds:
        return "elapsed_time_ceiling"
    if mode == "live_provider" and budget.max_provider_calls is not None:
        if provider_calls is None:
            return "provider_call_ceiling_not_observable"
        if provider_calls >= budget.max_provider_calls:
            return "provider_call_ceiling"
    elif budget.max_provider_calls is not None and provider_calls is not None and provider_calls >= budget.max_provider_calls:
        return "provider_call_ceiling"
    if budget.max_tokens is not None:
        if token_status != "recorded" or tokens is None:
            if mode == "live_provider" and (provider_calls or 0) > 0:
                return "token_ceiling_not_observable_after_provider_use"
        elif tokens >= budget.max_tokens:
            return "token_ceiling"
    if budget.max_estimated_cost is not None:
        if cost_status != "recorded" or cost is None:
            if mode == "live_provider" and (provider_calls or 0) > 0:
                return "cost_ceiling_not_observable_after_provider_use"
        elif cost >= budget.max_estimated_cost:
            return "cost_ceiling"
    return None

"""Fail-closed call, token, time, and USD guard for one evaluation run."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
import time

from controlled_model_evaluation.pricing import (
    MAX_INPUT_TOKENS_PER_CALL,
    MAX_OUTPUT_TOKENS_PER_CALL,
    MAX_TOTAL_INPUT_TOKENS,
    MAX_TOTAL_OUTPUT_TOKENS,
    MAX_TOTAL_PROVIDER_CALLS,
    MAX_WALL_CLOCK_SECONDS,
    approved_cost_ceiling,
    token_cost,
)


class BudgetRefused(RuntimeError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass
class Reservation:
    estimated_input: int
    max_output: int
    reserved_cost: Decimal
    completed: bool = False


@dataclass
class BudgetGuard:
    pricing_verified: bool = True
    max_calls: int = MAX_TOTAL_PROVIDER_CALLS
    max_input_per_call: int = MAX_INPUT_TOKENS_PER_CALL
    max_output_per_call: int = MAX_OUTPUT_TOKENS_PER_CALL
    max_input_total: int = MAX_TOTAL_INPUT_TOKENS
    max_output_total: int = MAX_TOTAL_OUTPUT_TOKENS
    max_wall_seconds: int = MAX_WALL_CLOCK_SECONDS
    ceiling_usd: Decimal = field(default_factory=approved_cost_ceiling)
    started: float = field(default_factory=time.perf_counter)
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    spent: Decimal = Decimal("0")
    retries: int = 0
    open_reservation: Reservation | None = None

    def remaining_seconds(self) -> float:
        return self.max_wall_seconds - (time.perf_counter() - self.started)

    def preflight(self, estimated_input: int, max_output: int, *, retry: bool = False) -> Reservation:
        if not self.pricing_verified:
            raise BudgetRefused("pricing unverified")
        if self.ceiling_usd is None or self.ceiling_usd <= 0:
            raise BudgetRefused("cost ceiling missing")
        if self.max_calls <= 0:
            raise BudgetRefused("call ceiling missing")
        if self.max_input_per_call <= 0 or self.max_output_per_call <= 0:
            raise BudgetRefused("token limits missing")
        if self.open_reservation is not None:
            raise BudgetRefused("previous request was not accounted")
        incoming = int(estimated_input)
        outgoing = int(max_output)
        if incoming <= 0 or outgoing <= 0:
            raise BudgetRefused("token estimate unavailable")
        if incoming > self.max_input_per_call:
            raise BudgetRefused("request would exceed input-token limit")
        if outgoing > self.max_output_per_call:
            raise BudgetRefused("request would exceed output-token limit")
        next_calls = self.calls + 1
        if next_calls > self.max_calls:
            raise BudgetRefused("retry would exceed call ceiling" if retry else "call ceiling would be exceeded")
        if self.input_tokens + incoming > self.max_input_total:
            raise BudgetRefused("input-token allowance would be exceeded")
        if self.output_tokens + outgoing > self.max_output_total:
            raise BudgetRefused("output-token allowance would be exceeded")
        reserved = token_cost(incoming, outgoing)
        if self.spent + reserved > self.ceiling_usd:
            raise BudgetRefused("budget would be exceeded")
        if self.remaining_seconds() <= 0:
            raise BudgetRefused("wall-clock allowance exhausted")
        self.open_reservation = Reservation(incoming, outgoing, reserved)
        return self.open_reservation

    def commit(self, *, input_tokens: int | None, output_tokens: int | None, failed: bool = False, retry: bool = False) -> dict:
        """A failed or unmetered request still consumes its reserved maximum."""
        reservation = self.open_reservation
        if reservation is None:
            raise BudgetRefused("completion without reservation")
        known = (
            isinstance(input_tokens, int) and input_tokens >= 0
            and isinstance(output_tokens, int) and output_tokens >= 0
            and not failed
        )
        if known:
            incoming = min(input_tokens, reservation.estimated_input)
            outgoing = min(output_tokens, reservation.max_output)
            # Never bill less than the provider could have charged when the
            # reported total exceeds the reservation. That is a ceiling breach.
            if input_tokens > reservation.estimated_input or output_tokens > reservation.max_output:
                incoming = input_tokens
                outgoing = output_tokens
            cost = token_cost(incoming, outgoing)
        else:
            incoming = reservation.estimated_input
            outgoing = reservation.max_output
            cost = reservation.reserved_cost
        self.calls += 1
        self.input_tokens += incoming
        self.output_tokens += outgoing
        self.spent += cost
        if retry:
            self.retries += 1
        reservation.completed = True
        self.open_reservation = None
        if self.calls > self.max_calls or self.spent > self.ceiling_usd:
            raise BudgetRefused("budget exceeded after a completed request")
        if self.input_tokens > self.max_input_total or self.output_tokens > self.max_output_total:
            raise BudgetRefused("token allowance exceeded after a completed request")
        return self.snapshot()

    def snapshot(self) -> dict:
        return {
            "calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "spent_usd": format(self.spent, "f"),
            "remaining_usd": format(self.ceiling_usd - self.spent, "f"),
            "retries": self.retries,
            "elapsed_seconds": round(time.perf_counter() - self.started, 6),
            "remaining_seconds": round(self.remaining_seconds(), 6),
            "ceiling_usd": format(self.ceiling_usd, "f"),
        }

"""Provider budget for the PR-DL live comparison.

Ceilings are hard stops. They are not spending targets.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


REQUEST_LIMIT = 21
INPUT_LIMIT = 30_000
OUTPUT_LIMIT = 8_000
TOTAL_LIMIT = 38_000
OUTPUT_TOKEN_CAP = 400


class BudgetStop(RuntimeError):
    """Raised when a request must not be sent or usage cannot be trusted."""


@dataclass
class Budget:
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    records: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def can_send(self, estimated_input: int, max_output: int) -> bool:
        estimated_input = max(1, int(estimated_input))
        max_output = max(1, int(max_output))
        return (
            self.requests + 1 <= REQUEST_LIMIT
            and self.input_tokens + estimated_input <= INPUT_LIMIT
            and self.output_tokens + max_output <= OUTPUT_LIMIT
            and self.total_tokens + estimated_input + max_output <= TOTAL_LIMIT
        )

    def refusal_reason(self, estimated_input: int, max_output: int) -> str:
        estimated_input = max(1, int(estimated_input))
        max_output = max(1, int(max_output))
        if self.requests + 1 > REQUEST_LIMIT:
            return "request ceiling"
        if self.input_tokens + estimated_input > INPUT_LIMIT:
            return "input-token ceiling"
        if self.output_tokens + max_output > OUTPUT_LIMIT:
            return "output-token ceiling"
        if self.total_tokens + estimated_input + max_output > TOTAL_LIMIT:
            return "total-token ceiling"
        return ""

    def add(self, record: dict[str, Any]) -> None:
        if record.get("input_tokens") is None or record.get("output_tokens") is None or record.get("total_tokens") is None:
            raise BudgetStop("provider usage accounting unavailable")
        self.requests += 1
        self.input_tokens += int(record["input_tokens"])
        self.output_tokens += int(record["output_tokens"])
        self.records.append(record)
        if (
            self.requests > REQUEST_LIMIT
            or self.input_tokens > INPUT_LIMIT
            or self.output_tokens > OUTPUT_LIMIT
            or self.total_tokens > TOTAL_LIMIT
        ):
            raise BudgetStop("provider budget exceeded after a completed request")

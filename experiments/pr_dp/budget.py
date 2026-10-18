"""Hard ceilings for the PR-DP live qualification."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


REQUEST_LIMIT = 8
INPUT_LIMIT = 8_000
OUTPUT_LIMIT = 3_000
TOTAL_LIMIT = 11_000
OUTPUT_TOKEN_CAP = 360


class BudgetStop(RuntimeError):
    """A request must not be sent, or usage cannot be trusted."""


@dataclass
class Budget:
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    records: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

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
        incoming = int(record["input_tokens"])
        outgoing = int(record["output_tokens"])
        total = int(record["total_tokens"])
        if total != incoming + outgoing:
            raise BudgetStop(
                f"provider usage does not add up: input={incoming} output={outgoing} total={total}"
            )
        self.requests += 1
        self.input_tokens += incoming
        self.output_tokens += outgoing
        self.records.append(record)
        if (
            self.requests > REQUEST_LIMIT
            or self.input_tokens > INPUT_LIMIT
            or self.output_tokens > OUTPUT_LIMIT
            or self.total_tokens > TOTAL_LIMIT
        ):
            raise BudgetStop("provider budget exceeded after a completed request")

    def to_dict(self) -> dict[str, Any]:
        return {
            "requests": self.requests,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "records": self.records,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "Budget":
        if not payload:
            return cls()
        budget = cls(
            requests=int(payload.get("requests") or 0),
            input_tokens=int(payload.get("input_tokens") or 0),
            output_tokens=int(payload.get("output_tokens") or 0),
            records=list(payload.get("records") or []),
        )
        if budget.total_tokens != budget.input_tokens + budget.output_tokens:
            raise BudgetStop("stored token accounting is inconsistent")
        return budget

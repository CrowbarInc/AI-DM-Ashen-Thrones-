"""Hard ceilings for the PR-DR live vertical slice."""

from __future__ import annotations

from experiments.pr_dp.budget import Budget, BudgetStop

REQUEST_LIMIT = 10
INPUT_LIMIT = 10_000
OUTPUT_LIMIT = 4_000
TOTAL_LIMIT = 14_000
OUTPUT_TOKEN_CAP = 320


class SliceBudget(Budget):
    """Same accounting rules as PR-DP, with the PR-DR ceilings."""

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

    def add(self, record: dict) -> None:
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

"""Hard ceilings for PR-DT live narration."""

from __future__ import annotations

from experiments.pr_dp.budget import Budget, BudgetStop

REQUEST_LIMIT = 8
INPUT_LIMIT = 12_000
OUTPUT_LIMIT = 4_000
TOTAL_LIMIT = 16_000
OUTPUT_TOKEN_CAP = 420


class NarrationBudget(Budget):
    """Budget with the PR-DT ceilings."""

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

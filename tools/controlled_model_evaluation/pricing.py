"""Published text-token rates for the configured ordinary-gameplay model.

Retrieved 2026-11-15 from the OpenAI model page. Cache discounts are recorded
and are not applied: this application does not read cached-token usage.
"""
from __future__ import annotations

from decimal import Decimal

PROVIDER = "openai"
MODEL = "gpt-4.1-mini"
PRICING_SOURCE = "https://developers.openai.com/api/docs/models/gpt-4.1-mini"
PRICING_RETRIEVED = "2026-11-15"
CURRENCY = "USD"
PRICING_UNIT = "per 1,000,000 tokens"
INPUT_PER_MILLION = Decimal("0.40")
CACHED_INPUT_PER_MILLION = Decimal("0.10")
OUTPUT_PER_MILLION = Decimal("1.60")
APPLY_CACHE_DISCOUNT = False
ADDITIONAL_TOOL_CHARGE_USD = Decimal("0")
PRICING_VERIFIED = True
MODEL_PAGE_STATUS = "Deprecated"
RESPONSES_ENDPOINT = "supported"

# Measured 2026-11-15 with a local stub. No provider socket was opened.
# Interpretation uses experiments.pr_dp.prompt.estimate_input_tokens.
MEASURED_INTERPRETATION_INPUT_TOKENS = 3850
# Narration uses game.gm.build_messages on the frontier-gate seed, then the
# call_gpt byte/3 estimator. The sampled turns did not reach call_gpt.
MEASURED_NARRATION_INPUT_TOKENS = 19173
MEASURED_NARRATION_BYTES = 57329

MAX_INPUT_TOKENS_PER_CALL = 24000
MAX_OUTPUT_TOKENS_PER_CALL = 600
MAX_TOTAL_PROVIDER_CALLS = 40
MAX_TOTAL_INPUT_TOKENS = MAX_TOTAL_PROVIDER_CALLS * MAX_INPUT_TOKENS_PER_CALL
MAX_TOTAL_OUTPUT_TOKENS = MAX_TOTAL_PROVIDER_CALLS * MAX_OUTPUT_TOKENS_PER_CALL
MAX_WALL_CLOCK_SECONDS = 1800
PER_CALL_TIMEOUT_SECONDS = 45
MAX_ATTEMPTS_PER_CASE = 2
SAFETY_MARGIN = Decimal("1.25")


def token_cost(input_tokens: int, output_tokens: int) -> Decimal:
    """Uncached text-token cost. Cached input is billed as ordinary input."""
    incoming = Decimal(input_tokens) * INPUT_PER_MILLION / Decimal(1_000_000)
    outgoing = Decimal(output_tokens) * OUTPUT_PER_MILLION / Decimal(1_000_000)
    return incoming + outgoing + ADDITIONAL_TOOL_CHARGE_USD


def maximum_request_cost() -> Decimal:
    return token_cost(MAX_INPUT_TOKENS_PER_CALL, MAX_OUTPUT_TOKENS_PER_CALL)


def maximum_estimated_cost() -> Decimal:
    return maximum_request_cost() * MAX_TOTAL_PROVIDER_CALLS


def approved_cost_ceiling() -> Decimal:
    """Worst-case uncached cost plus the documented safety margin, in cents."""
    raw = maximum_estimated_cost() * SAFETY_MARGIN
    cents = (raw * 100).to_integral_value(rounding="ROUND_CEILING")
    return cents / Decimal(100)

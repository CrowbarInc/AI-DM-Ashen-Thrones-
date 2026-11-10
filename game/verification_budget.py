"""Verification ceilings for the existing admission controller.

This module does not admit requests and is not a second budget controller.
A verification script calls apply_verification_budget, which writes the
ASHEN_PROVIDER_* variables provider_budget.limits already reads.

Production openings do not import this module. The default total is the
verification cap, not a production narration cap.
"""
from __future__ import annotations

import os
from typing import MutableMapping

DEFAULT_VERIFICATION_TOTAL_TOKENS = 3000
HISTORICAL_UNENFORCED_TOTAL = 200000


class VerificationBudgetRejected(ValueError):
    """The profile refused a ceiling instead of widening it."""


def _positive_int(value, *, label: str) -> int:
    if isinstance(value, bool) or value is None:
        raise VerificationBudgetRejected(f"malformed {label}")
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise VerificationBudgetRejected(f"malformed {label}") from exc
    if number <= 0:
        raise VerificationBudgetRejected(f"rejected {label}")
    return number


def resolve_verification_budget(
    total=None,
    *,
    override=None,
    request_limit=4,
    input_limit=None,
    output_limit=None,
) -> dict:
    """Return the ceiling a verification run must install.

    A missing total uses 3,000. A malformed value or the historical
    200,000 ceiling raises. An override is recorded and is the only way
    to select a different total.
    """
    if override is not None and total is not None:
        raise VerificationBudgetRejected("rejected mixed budget")
    if override is not None:
        chosen = _positive_int(override, label="override")
        source = "override"
    elif total is None:
        chosen = DEFAULT_VERIFICATION_TOTAL_TOKENS
        source = "default"
    else:
        chosen = _positive_int(total, label="total")
        if chosen == HISTORICAL_UNENFORCED_TOTAL:
            raise VerificationBudgetRejected("rejected historical 200000 ceiling")
        source = "profile"
    requests = _positive_int(request_limit, label="requests")
    incoming = chosen if input_limit is None else _positive_int(input_limit, label="input")
    outgoing = min(600, chosen) if output_limit is None else _positive_int(output_limit, label="output")
    return {
        "request_limit": requests,
        "input_tokens": incoming,
        "output_tokens": outgoing,
        "total_tokens": chosen,
        "source": source,
        "override": source == "override",
        "historical_unenforced_total": HISTORICAL_UNENFORCED_TOTAL,
    }


def apply_verification_budget(environ: MutableMapping[str, str] | None = None, **kwargs) -> dict:
    """Write the resolved ceiling into the environment admission already reads.

    Raises before writing when the profile is malformed or rejected, so a
    failed configuration cannot leave the historical 200,000 ceiling behind.
    """
    record = resolve_verification_budget(**kwargs)
    target = os.environ if environ is None else environ
    target["ASHEN_PROVIDER_REQUEST_LIMIT"] = str(record["request_limit"])
    target["ASHEN_PROVIDER_INPUT_TOKEN_LIMIT"] = str(record["input_tokens"])
    target["ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT"] = str(record["output_tokens"])
    target["ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT"] = str(record["total_tokens"])
    target["ASHEN_VERIFICATION_BUDGET_SOURCE"] = record["source"]
    target["ASHEN_VERIFICATION_BUDGET_TOTAL"] = str(record["total_tokens"])
    return record

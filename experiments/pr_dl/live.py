"""One bounded Responses API call. No retries and no model switching."""
from __future__ import annotations

import re
import time
from typing import Any

from experiments.pr_dl.budget import OUTPUT_TOKEN_CAP, Budget, BudgetStop
from experiments.pr_dl.prompt import estimate_input_tokens, interpretation_schema

_SECRET_RE = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")


def redact(text: str) -> str:
    return _SECRET_RE.sub("sk-REDACTED", text)


def usage_triplet(resp: Any) -> tuple[int | None, int | None, int | None]:
    usage = getattr(resp, "usage", None)
    if usage is None:
        return None, None, None
    incoming = getattr(usage, "input_tokens", None)
    outgoing = getattr(usage, "output_tokens", None)
    total = getattr(usage, "total_tokens", None)
    if total is None and incoming is not None and outgoing is not None:
        total = int(incoming) + int(outgoing)
    return incoming, outgoing, total


def call_interpretation(
    client: Any,
    budget: Budget,
    *,
    scenario_id: str,
    messages: list[dict[str, str]],
    configured_model: str,
) -> dict[str, Any]:
    schema = interpretation_schema()
    estimated = estimate_input_tokens(messages, schema)
    reason = budget.refusal_reason(estimated, OUTPUT_TOKEN_CAP)
    if reason:
        raise BudgetStop(f"preflight budget would be exceeded: {reason}; estimated_input={estimated}")
    started = time.perf_counter()
    try:
        resp = client.responses.create(
            model=configured_model,
            input=messages,
            temperature=0,
            max_output_tokens=OUTPUT_TOKEN_CAP,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "pr_dl_interpretation",
                    "strict": True,
                    "schema": schema,
                }
            },
        )
    except BudgetStop:
        raise
    except Exception as exc:  # noqa: BLE001 - transport failure stops the batch; no retry
        raise BudgetStop(f"provider request failed without retry: {type(exc).__name__}: {redact(str(exc))[:300]}") from exc
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    text = str(getattr(resp, "output_text", "") or "")
    incoming, outgoing, total = usage_triplet(resp)
    model = str(getattr(resp, "model", "") or "")
    record = {
        "scenario_id": scenario_id,
        "request_id": getattr(resp, "id", None),
        "configured_model": configured_model,
        "model": model,
        "input_tokens": incoming,
        "output_tokens": outgoing,
        "total_tokens": total,
        "latency_ms": latency_ms,
        "estimated_input_tokens_preflight": estimated,
        "max_output_tokens": OUTPUT_TOKEN_CAP,
        "status": getattr(resp, "status", None),
    }
    budget.add(record)
    if model and not model.startswith(configured_model):
        raise BudgetStop(f"provider returned a different model ({model}); automatic switching is forbidden")
    return {"text": text, "record": record}

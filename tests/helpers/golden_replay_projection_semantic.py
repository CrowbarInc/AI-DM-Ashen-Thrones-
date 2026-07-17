"""Semantic mutation projection policy for golden replay observations."""
from __future__ import annotations

from typing import Any, Mapping


def project_semantic_mutation_summary(
    semantic_mutation_trace: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project optional BY1 semantic mutation trace into summary observation fields."""
    if not isinstance(semantic_mutation_trace, Mapping):
        return {}
    summary_keys = (
        "first_semantic_mutation_bucket",
        "first_semantic_mutation_source",
        "first_semantic_mutation_checkpoint_id",
        "first_semantic_mutation_sequence",
        "semantic_mutation_changed_count",
        "semantic_mutation_unknown_count",
        "semantic_mutation_risk_score",
        "semantic_mutation_risk_band",
        "semantic_mutation_trace_complete",
        "trace_continuity",
    )
    out: dict[str, Any] = {}
    for key in summary_keys:
        if key in {"semantic_mutation_trace_complete", "trace_continuity"}:
            if key in semantic_mutation_trace:
                out[key] = semantic_mutation_trace.get(key)
            continue
        value = semantic_mutation_trace.get(key)
        if value is not None:
            out[key] = value
    return out

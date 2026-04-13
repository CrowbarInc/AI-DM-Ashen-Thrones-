from __future__ import annotations

"""Resolve deterministic model routes for game requests.

This module owns deterministic model choice. It provides a routing substrate
for future blocks and must not alter existing turn behavior until call sites
opt into using it.
"""

from dataclasses import dataclass

from game.config import (
    DEFAULT_MODEL_NAME,
    ENABLE_MODEL_ROUTING,
    HIGH_PRECISION_MODEL_NAME,
    RETRY_ESCALATION_MODEL_NAME,
)


@dataclass(frozen=True)
class ModelRouteDecision:
    """Resolved model-selection outcome for a single request."""

    selected_model: str
    route_reason: str
    route_family: str
    escalation_allowed: bool


def _decision(
    *,
    selected_model: str,
    route_reason: str,
    route_family: str,
    escalation_allowed: bool,
) -> ModelRouteDecision:
    return ModelRouteDecision(
        selected_model=selected_model,
        route_reason=route_reason,
        route_family=route_family,
        escalation_allowed=escalation_allowed,
    )


def resolve_model_route(
    *,
    purpose: str,
    response_policy: dict[str, object] | None = None,
    segmented_turn: dict[str, object] | None = None,
    retry_attempt: int = 0,
    strict_social: bool = False,
    force_high_precision: bool = False,
) -> ModelRouteDecision:
    """Resolve a model route from explicit inputs only.

    This foundation is intentionally deterministic and avoids heuristics. It
    accepts future-facing inputs now, but this block must not yet alter
    existing turn behavior.
    """

    del response_policy, segmented_turn, retry_attempt

    if not ENABLE_MODEL_ROUTING:
        return _decision(
            selected_model=DEFAULT_MODEL_NAME,
            route_reason="routing_disabled",
            route_family="default",
            escalation_allowed=False,
        )

    if purpose == "retry_escalation":
        return _decision(
            selected_model=RETRY_ESCALATION_MODEL_NAME,
            route_reason="purpose_retry_escalation",
            route_family="retry_escalation",
            escalation_allowed=False,
        )

    if force_high_precision:
        return _decision(
            selected_model=HIGH_PRECISION_MODEL_NAME,
            route_reason="force_high_precision",
            route_family="high_precision",
            escalation_allowed=True,
        )

    if purpose == "strict_social" or strict_social:
        return _decision(
            selected_model=HIGH_PRECISION_MODEL_NAME,
            route_reason=(
                "purpose_strict_social" if purpose == "strict_social" else "strict_social_flag"
            ),
            route_family="high_precision",
            escalation_allowed=True,
        )

    if purpose == "primary_turn":
        return _decision(
            selected_model=DEFAULT_MODEL_NAME,
            route_reason="purpose_primary_turn",
            route_family="default",
            escalation_allowed=True,
        )

    return _decision(
        selected_model=DEFAULT_MODEL_NAME,
        route_reason="purpose_default",
        route_family="default",
        escalation_allowed=True,
    )

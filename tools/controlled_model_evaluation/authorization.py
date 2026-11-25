"""Fail-closed authorization gate. Credentials are not authorization."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from controlled_model_evaluation.pricing import (
    MAX_INPUT_TOKENS_PER_CALL,
    MAX_OUTPUT_TOKENS_PER_CALL,
    MAX_TOTAL_PROVIDER_CALLS,
    MAX_WALL_CLOCK_SECONDS,
    MODEL,
    PER_CALL_TIMEOUT_SECONDS,
    PROVIDER,
    approved_cost_ceiling,
)


class AuthorizationRefused(RuntimeError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class ProviderIdentity:
    provider: str
    model: str
    high_precision_model: str
    retry_model: str
    routing_enabled: bool
    key_present: bool
    interpretation_model: str = ""

    @property
    def unambiguous(self) -> bool:
        names = {self.model, self.high_precision_model, self.retry_model}
        if self.interpretation_model:
            names.add(self.interpretation_model)
        return bool(self.provider and self.model) and len(names) == 1


@dataclass(frozen=True)
class LiveRequest:
    granted: bool
    provider: str
    model: str
    pricing_verified: bool
    max_calls: int
    max_input_tokens_per_call: int
    max_output_tokens_per_call: int
    max_wall_seconds: int
    per_call_timeout_seconds: int
    ceiling_usd: Decimal
    data_dir: Path
    production_data_dir: Path
    snapshot_available: bool
    redaction_ok: bool
    preparation_phase: bool = True


def authorize(request: LiveRequest, identity: ProviderIdentity) -> None:
    """Raise unless every live-execution precondition is present."""
    if request.preparation_phase or not request.granted:
        raise AuthorizationRefused("no authorization exists")
    if not request.pricing_verified:
        raise AuthorizationRefused("pricing unverified")
    if not identity.model or not request.model:
        raise AuthorizationRefused("model identity unknown")
    if not identity.unambiguous:
        raise AuthorizationRefused("provider configuration ambiguous")
    if (
        identity.provider != request.provider
        or identity.model != request.model
        or identity.provider != PROVIDER
        or identity.model != MODEL
    ):
        raise AuthorizationRefused("provider changed unexpectedly")
    if request.max_input_tokens_per_call != MAX_INPUT_TOKENS_PER_CALL or request.max_output_tokens_per_call != MAX_OUTPUT_TOKENS_PER_CALL:
        raise AuthorizationRefused("token limits missing")
    if request.ceiling_usd != approved_cost_ceiling():
        raise AuthorizationRefused("cost ceiling missing")
    if request.max_calls != MAX_TOTAL_PROVIDER_CALLS:
        raise AuthorizationRefused("call ceiling missing")
    if request.max_wall_seconds != MAX_WALL_CLOCK_SECONDS or request.per_call_timeout_seconds != PER_CALL_TIMEOUT_SECONDS:
        raise AuthorizationRefused("timeout missing")
    data = request.data_dir.resolve()
    production = request.production_data_dir.resolve()
    if data == production or production in data.parents:
        raise AuthorizationRefused("evaluation attempts to use a production campaign")
    if not request.snapshot_available:
        raise AuthorizationRefused("required state snapshots are unavailable")
    if not request.redaction_ok:
        raise AuthorizationRefused("secret redaction failed")

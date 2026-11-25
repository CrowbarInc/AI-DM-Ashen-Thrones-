"""System-agnostic boundary between the core and a ruleset authority.

This module names identity, capability, and policy-evaluation results. It does
not select a ruleset, import a ruleset implementation, or apply mechanics.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
import re
from typing import Any, Mapping

_CAPABILITY = re.compile(r'^[a-z][a-z0-9_]*$')
_SUPPORT = frozenset({'supported', 'unsupported', 'unknown', 'invalid'})


class EvaluationStatus(str, Enum):
    SUPPORTED = 'supported'
    UNSUPPORTED = 'unsupported'
    UNKNOWN = 'unknown'
    INVALID = 'invalid'
    MECHANICALLY_UNRESOLVED = 'mechanically_unresolved'


_STATUSES = frozenset(item.value for item in EvaluationStatus)


def freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return an immutable deep copy of a mapping."""
    copied: dict[str, Any] = {}
    for key, item in value.items():
        if isinstance(item, Mapping):
            copied[str(key)] = freeze(item)
        elif isinstance(item, (list, tuple)):
            copied[str(key)] = tuple(freeze(part) if isinstance(part, Mapping) else part for part in item)
        else:
            copied[str(key)] = item
    return MappingProxyType(copied)


def to_plain(value: Any) -> Any:
    """Convert frozen mappings and tuples into stable JSON-ready values."""
    if isinstance(value, Mapping):
        return {str(key): to_plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [to_plain(item) for item in value]
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


@dataclass(frozen=True)
class PolicyEvaluation:
    status: str
    reason: str
    ruleset_id: str | None
    ruleset_version: str | None
    capability: str | None
    implementation: str | None
    capability_support: str
    ruleset_result: Mapping[str, Any]
    state_mutation: str = 'none'

    def __post_init__(self) -> None:
        if self.status not in _STATUSES:
            raise ValueError('unknown evaluation status')
        if self.capability_support not in _SUPPORT:
            raise ValueError('unknown capability support')
        if self.state_mutation != 'none':
            raise ValueError('policy evaluation cannot carry a state mutation')
        if not isinstance(self.ruleset_result, Mapping):
            raise ValueError('ruleset result must be a mapping')


@dataclass(frozen=True)
class CapabilityDiscovery:
    status: str
    reason: str
    ruleset_id: str | None
    ruleset_version: str | None
    capability: str | None
    implementation: str | None

    def __post_init__(self) -> None:
        if self.status not in _SUPPORT:
            raise ValueError('unknown discovery status')


def evaluation_to_dict(evaluation: PolicyEvaluation) -> dict[str, Any]:
    return {
        'status': evaluation.status,
        'reason': evaluation.reason,
        'ruleset_id': evaluation.ruleset_id,
        'ruleset_version': evaluation.ruleset_version,
        'capability': evaluation.capability,
        'implementation': evaluation.implementation,
        'capability_support': evaluation.capability_support,
        'ruleset_result': to_plain(evaluation.ruleset_result),
        'state_mutation': evaluation.state_mutation,
    }


def _closed(status: str, reason: str, ruleset_id, version, capability, implementation,
            support: str | None = None) -> PolicyEvaluation:
    return PolicyEvaluation(
        status=status, reason=reason, ruleset_id=ruleset_id, ruleset_version=version,
        capability=capability if isinstance(capability, str) else None,
        implementation=implementation, capability_support=support or status,
        ruleset_result=freeze({}), state_mutation='none')


def _capability_problem(capability):
    if capability is None or capability == '':
        return 'unknown', 'missing_capability'
    if not isinstance(capability, str) or _CAPABILITY.fullmatch(capability) is None:
        return 'invalid', 'malformed_capability'
    return None


def discover(authority, capability) -> CapabilityDiscovery:
    """Ask one already-selected authority whether it supports a capability."""
    ruleset_id = getattr(authority, 'ruleset_id', None)
    version = getattr(authority, 'version', None)
    implementation = getattr(authority, 'implementation', None)
    problem = _capability_problem(capability)
    if problem is not None:
        status, reason = problem
        return CapabilityDiscovery(status, reason, ruleset_id, version,
                                   capability if isinstance(capability, str) else None, implementation)
    status = authority.capability_disposition(capability)
    reason = {'supported': 'capability_supported', 'unsupported': 'capability_not_supported',
              'unknown': 'unknown_capability', 'invalid': 'malformed_capability'}[status]
    return CapabilityDiscovery(status, reason, ruleset_id, version, capability, implementation)


def dispatch(authority, capability, request, context) -> PolicyEvaluation:
    """Validate a policy request and delegate it to the selected authority.

    Request and context are not copied into ruleset-specific fields here.
    A result that claims a state mutation is rejected at construction.
    """
    ruleset_id = getattr(authority, 'ruleset_id', None)
    version = getattr(authority, 'version', None)
    implementation = getattr(authority, 'implementation', None)
    problem = _capability_problem(capability)
    if problem is not None:
        status, reason = problem
        return _closed(status, reason, ruleset_id, version, capability, implementation)
    if request is None:
        return _closed('unknown', 'missing_request', ruleset_id, version, capability, implementation)
    if not isinstance(request, Mapping):
        return _closed('invalid', 'malformed_request', ruleset_id, version, capability, implementation)
    if context is None:
        return _closed('unknown', 'missing_context', ruleset_id, version, capability, implementation)
    if not isinstance(context, Mapping):
        return _closed('invalid', 'malformed_context', ruleset_id, version, capability, implementation)
    result = authority.evaluate_policy(capability, request, context)
    if not isinstance(result, PolicyEvaluation):
        return _closed('invalid', 'authority_result_malformed', ruleset_id, version, capability, implementation)
    return result

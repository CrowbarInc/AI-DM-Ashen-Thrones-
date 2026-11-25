"""Closed, deterministic lookup of ruleset authorities supplied with the engine.

This is not a plugin loader. It does not scan the filesystem, import arbitrary
code, or substitute one ruleset when another is missing or unsupported.
Identity-only entries declare no mechanics.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from types import MappingProxyType
from typing import Any, Mapping

from game.ruleset_contract import (
    CapabilityDiscovery, PolicyEvaluation, discover, dispatch, freeze,
)

_ID = re.compile(r'^[a-z][a-z0-9_]*$')
_VERSION = re.compile(r'^[1-9][0-9]*$')

# Public identity map. Values name the implementation; they are not loaded here.
# Assignment raises TypeError. There is no register() or install() operation.
REGISTERED: Mapping[tuple[str, str], str] = MappingProxyType({
    ('pf1e', '1'): 'game.pf1e_equipment_policy',
    ('rules_light', '1'): 'identity_only:rules_light@1',
    ('scifi', '1'): 'identity_only:scifi@1',
})
_KNOWN_IDS = frozenset(ruleset_id for ruleset_id, _version in REGISTERED)
_AUTHORITIES: dict[tuple[str, str], Any] = {}


@dataclass(frozen=True)
class IdentityOnlyRuleset:
    """A named ruleset with no mechanical implementation."""

    ruleset_id: str
    version: str
    implementation: str
    recognized_unsupported: frozenset[str]
    supported_capabilities: frozenset[str] = frozenset()
    mechanics_implemented: bool = False

    def supports(self, capability: str) -> bool:
        return isinstance(capability, str) and capability in self.supported_capabilities

    def capability_disposition(self, capability: str) -> str:
        if capability in self.supported_capabilities:
            return 'supported'
        if capability in self.recognized_unsupported:
            return 'unsupported'
        return 'unknown'

    def evaluate_policy(self, capability, request, context) -> PolicyEvaluation:
        del request, context
        disposition = self.capability_disposition(capability)
        if disposition == 'supported':
            raise RuntimeError('identity-only ruleset has no mechanical evaluator')
        reason = 'capability_not_supported' if disposition == 'unsupported' else 'unknown_capability'
        status = disposition if disposition in ('unsupported', 'unknown') else 'unknown'
        return PolicyEvaluation(
            status, reason, self.ruleset_id, self.version, capability, self.implementation,
            status, freeze({'delegated': False, 'mechanics_implemented': False}))


def _identity(ruleset_id: str, version: str) -> IdentityOnlyRuleset:
    return IdentityOnlyRuleset(
        ruleset_id, version, f'identity_only:{ruleset_id}@{version}',
        frozenset({'equipment_policy'}))


def _authority(ruleset_id: str, version: str):
    key = (ruleset_id, version)
    if key not in _AUTHORITIES:
        if key == ('pf1e', '1'):
            from game.pf1e_equipment_policy import PF1E_RULESET_AUTHORITY
            _AUTHORITIES[key] = PF1E_RULESET_AUTHORITY
        elif key == ('rules_light', '1'):
            _AUTHORITIES[key] = _identity('rules_light', '1')
        elif key == ('scifi', '1'):
            _AUTHORITIES[key] = _identity('scifi', '1')
        else:
            raise KeyError(key)
    return _AUTHORITIES[key]


@dataclass(frozen=True)
class RulesetSelection:
    status: str
    reason: str
    ruleset_id: str | None
    version: str | None
    canonical: str | None
    implementation: str | None
    authority: Any = None


def _selection(status: str, reason: str, ruleset_id=None, version=None, implementation=None, authority=None):
    canonical = f'{ruleset_id}@{version}' if ruleset_id and version and status == 'selected' else None
    return RulesetSelection(status, reason, ruleset_id, version, canonical, implementation, authority)


def get_ruleset(ruleset_id, version) -> RulesetSelection:
    """Look up an explicit identity and version. Neither argument has a default."""
    if ruleset_id is None or ruleset_id == '':
        return _selection('unknown', 'missing_identifier')
    if not isinstance(ruleset_id, str) or _ID.fullmatch(ruleset_id) is None:
        echoed = ruleset_id if isinstance(ruleset_id, str) else None
        return _selection('invalid', 'malformed_identifier', echoed)
    if version is None or version == '':
        return _selection('unknown', 'missing_version', ruleset_id)
    if not isinstance(version, str) or _VERSION.fullmatch(version) is None:
        echoed = version if isinstance(version, str) else None
        if isinstance(version, str) and version.isdigit() and ruleset_id in _KNOWN_IDS:
            return _selection('unsupported', 'unsupported_version', ruleset_id, echoed)
        return _selection('invalid', 'malformed_version', ruleset_id, echoed)
    key = (ruleset_id, version)
    if key not in REGISTERED:
        if ruleset_id in _KNOWN_IDS:
            return _selection('unsupported', 'unsupported_version', ruleset_id, version)
        return _selection('unknown', 'unknown_ruleset', ruleset_id, version)
    authority = _authority(ruleset_id, version)
    return _selection('selected', 'selected', ruleset_id, version, REGISTERED[key], authority)


def parse_canonical(token) -> RulesetSelection:
    """Split one ``identity@version`` token. A bad token is not replaced."""
    if not isinstance(token, str) or token.count('@') != 1:
        echoed = token if isinstance(token, str) else None
        return _selection('invalid', 'malformed_identifier', echoed)
    ruleset_id, version = token.split('@')
    return get_ruleset(ruleset_id, version)


def discover_capability(ruleset_id, version, capability) -> CapabilityDiscovery:
    selection = get_ruleset(ruleset_id, version)
    if selection.authority is None:
        return CapabilityDiscovery(
            selection.status if selection.status in ('unsupported', 'unknown', 'invalid') else 'unknown',
            selection.reason, selection.ruleset_id, selection.version,
            capability if isinstance(capability, str) else None, None)
    return discover(selection.authority, capability)


def evaluate_policy(ruleset_id, version, capability, request, context) -> PolicyEvaluation:
    """Select an authority, then delegate. No selection means no mechanics."""
    selection = get_ruleset(ruleset_id, version)
    if selection.authority is None:
        support = selection.status if selection.status in ('unsupported', 'unknown', 'invalid') else 'unknown'
        return PolicyEvaluation(
            support, selection.reason, selection.ruleset_id, selection.version,
            capability if isinstance(capability, str) else None, None, support, freeze({}))
    return dispatch(selection.authority, capability, request, context)

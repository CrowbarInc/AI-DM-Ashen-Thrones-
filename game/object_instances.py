"""Core identity for explicitly selected existing character-inventory singletons.

Pure validation/staging only; storage owns bytes and the API owns serialization.
The enclosing character is the authoritative host, not a second object registry.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from game.state_authority import WORLD_STATE, assert_owner_can_mutate_domain

_IDENTITY_FIELDS = frozenset({'instance_id', 'revision', 'provenance'})


@dataclass(frozen=True)
class IdentityResult:
    """Detached candidate on success; refusals never carry a partial candidate."""
    status: str  # legacy | existing | assigned | rejected
    instance_id: str | None = None
    character: dict[str, Any] | None = None
    error: str | None = None


def _reject(error: str) -> IdentityResult:
    return IdentityResult('rejected', error=error)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 256


def _singleton(row: Any) -> bool:
    return (isinstance(row, dict) and _text(row.get('id')) and
            isinstance(row.get('name'), str) and bool(row['name'].strip()) and
            type(row.get('quantity')) is int and row['quantity'] == 1 and
            type(row.get('usable')) is bool)


def _uuid(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = UUID(value)
    except ValueError:
        return False
    return parsed.version == 4 and str(parsed) == value


def _identity_error(row: dict, campaign_run_id: str) -> str | None:
    if not _IDENTITY_FIELDS.issubset(row):
        return 'incomplete_identity_metadata'
    if not _uuid(row['instance_id']):
        return 'unsupported_or_malformed_instance_id'
    if type(row['revision']) is not int or row['revision'] < 0:
        return 'invalid_revision'
    provenance = row['provenance']
    if not isinstance(provenance, dict):
        return 'invalid_provenance'
    if type(provenance.get('version')) is not int or provenance['version'] != 1:
        return 'unsupported_identity_version'
    if provenance.get('campaign_run_id') != campaign_run_id:
        return 'campaign_mismatch'
    source = provenance.get('source')
    if (not _text(provenance.get('operation_id')) or not isinstance(source, dict) or
            source.get('host') != 'character.inventory' or not _text(source.get('legacy_id'))):
        return 'invalid_provenance'
    if not _singleton(row):
        return 'invalid_singleton_record'
    return None


def inspect_object_identity(character: Any, inventory_index: int, *,
                            campaign_run_id: str) -> IdentityResult:
    """Inspect one explicit row; validate all declared identities in its host.

    No IDs are allocated. Legacy malformed *other* rows stay readable/untouched.
    A reserved field on a legacy row is ambiguous and fails closed.
    """
    if not _text(campaign_run_id):
        return _reject('invalid_campaign_scope')
    inventory = character.get('inventory') if isinstance(character, dict) else None
    if not isinstance(inventory, list):
        return _reject('invalid_inventory')
    if type(inventory_index) is not int or not 0 <= inventory_index < len(inventory):
        return _reject('invalid_selection')
    seen = set()
    for row in inventory:
        if not isinstance(row, dict) or not _IDENTITY_FIELDS.intersection(row):
            continue
        error = _identity_error(row, campaign_run_id)
        if error:
            return _reject(error)
        identity = row['instance_id']
        if identity in seen:
            return _reject('duplicate_instance_id')
        seen.add(identity)
    row = inventory[inventory_index]
    if not _singleton(row):
        return _reject('ineligible_singleton')
    identity = row.get('instance_id')
    return IdentityResult('existing' if identity else 'legacy', identity, copy.deepcopy(character))


def ensure_object_instance_identity(character: Any, inventory_index: int, *,
                                    campaign_run_id: str, operation_id: str) -> IdentityResult:
    """Stage an additive identity once. Never mutate the supplied character."""
    if not _text(operation_id):
        return _reject('invalid_operation_id')
    result = inspect_object_identity(character, inventory_index, campaign_run_id=campaign_run_id)
    if result.status != 'legacy':
        return result
    assert_owner_can_mutate_domain(__name__, WORLD_STATE, operation='assign_inventory_identity')
    staged = result.character
    # Replace one selected row, even if an in-memory caller aliased two rows.
    row = copy.deepcopy(staged['inventory'][inventory_index])
    identity = str(uuid4())
    row.update(instance_id=identity, revision=0, provenance={
        'version': 1, 'campaign_run_id': campaign_run_id, 'operation_id': operation_id,
        'source': {'host': 'character.inventory', 'legacy_id': row['id']},
    })
    staged['inventory'][inventory_index] = row
    checked = inspect_object_identity(staged, inventory_index, campaign_run_id=campaign_run_id)
    if checked.status == 'rejected':
        return checked
    return IdentityResult('assigned', identity, staged)

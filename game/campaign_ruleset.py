"""Ruleset identity owned by the active campaign session, never by player text.

The session is the existing playthrough/snapshot owner; campaign.json is an
authored bootstrap template shared by New Campaign runs. No mechanics live here.
"""
from __future__ import annotations

import copy
from game import ruleset_registry as registry
from game.ruleset_contract import evaluation_to_dict

BINDING_KEY = 'ruleset_binding'
DEFAULT_CREATION_IDENTITY = ('pf1e', '1')
# Explicit compatibility declaration for the existing legacy gameplay engine.
# Registry membership or one supported policy alone does not imply playability.
CAMPAIGN_PLAYABLE = frozenset({('pf1e', '1')})


class CampaignBindingError(ValueError):
    pass


def creation_binding(selection=None):
    if selection is None:
        selection = dict(zip(('ruleset_id', 'ruleset_version'), DEFAULT_CREATION_IDENTITY))
    candidate = copy.deepcopy(selection)
    if isinstance(candidate, dict):
        candidate.setdefault('binding_version', 1)
    result = validate_binding(candidate)
    if result['status'] != 'valid':
        raise CampaignBindingError(result['reason'])
    binding = result['binding']
    key = (binding['ruleset_id'], binding['ruleset_version'])
    if key not in CAMPAIGN_PLAYABLE:
        raise CampaignBindingError('ruleset_not_campaign_playable')
    capability = registry.discover_capability(*key, 'equipment_policy')
    if capability.status != 'supported':
        raise CampaignBindingError('required_capability_unavailable')
    return binding


def validate_binding(binding):
    if binding is None:
        return {'status': 'missing', 'reason': 'missing_binding', 'binding': None}
    if (not isinstance(binding, dict) or set(binding) != {'ruleset_id', 'ruleset_version', 'binding_version'}
            or type(binding.get('binding_version')) is not int or binding['binding_version'] != 1):
        return {'status': 'invalid', 'reason': 'invalid_binding', 'binding': copy.deepcopy(binding)}
    selected = registry.get_ruleset(binding['ruleset_id'], binding['ruleset_version'])
    return {'status': 'valid' if selected.status == 'selected' else selected.status,
            'reason': selected.reason, 'binding': copy.deepcopy(binding),
            'registry_resolution': selected.status, 'canonical': selected.canonical,
            'campaign_playable': (selected.ruleset_id, selected.version) in CAMPAIGN_PLAYABLE}


def resolve_campaign_ruleset(campaign_id, capability=None):
    from game import storage
    from game.persistence_contract import PersistenceContractError
    try:
        session = storage.load_session()
    except (PersistenceContractError, ValueError, OSError):
        return {'status': 'invalid', 'reason': 'persisted_campaign_unreadable', 'campaign_id': campaign_id}
    if not campaign_id or session.get('campaign_run_id') != campaign_id:
        return {'status': 'invalid', 'reason': 'campaign_mismatch', 'campaign_id': campaign_id}
    result = validate_binding(session.get(BINDING_KEY))
    result['campaign_id'] = campaign_id
    if result['status'] == 'valid' and capability is not None:
        b = result['binding']
        discovery = registry.discover_capability(b['ruleset_id'], b['ruleset_version'], capability)
        result.update(status=discovery.status, reason=discovery.reason, capability=capability)
    return result


def evaluate_campaign_policy(campaign_id, capability, request, context):
    result = resolve_campaign_ruleset(campaign_id, capability)
    if result['status'] != 'supported':
        return result
    b = result['binding']
    result['evaluation'] = evaluation_to_dict(registry.evaluate_policy(
        b['ruleset_id'], b['ruleset_version'], capability, request, context))
    return result


def migrate_legacy_campaign(campaign_id):
    """Only persisted explicit metadata is migration authority; no class/item inference.

    Legacy `ruleset_id`/`ruleset_version` on the session are accepted provenance.
    Missing metadata remains ambiguous, even on an otherwise Pathfinder-like sheet.
    """
    from game import storage
    from game.persistence_contract import PersistenceContractError
    with storage._runtime_persistence_guard('migrate_campaign_ruleset'):
        try:
            session = storage.load_session()
        except (PersistenceContractError, ValueError, OSError):
            return {'status': 'migration_failed', 'reason': 'persisted_campaign_unreadable'}
        if not campaign_id or session.get('campaign_run_id') != campaign_id:
            return {'status': 'invalid', 'reason': 'campaign_mismatch'}
        if BINDING_KEY in session:
            result = validate_binding(session[BINDING_KEY])
            result['status'] = 'already_bound' if result['status'] == 'valid' else result['status']
            return result
        if 'ruleset_id' not in session and 'ruleset_version' not in session:
            return {'status': 'ambiguous', 'reason': 'missing_authoritative_provenance'}
        if not all(k in session and session[k] is not None for k in ('ruleset_id', 'ruleset_version')):
            return {'status': 'invalid', 'reason': 'incomplete_legacy_metadata'}
        binding = {k: session.get(k) for k in ('ruleset_id', 'ruleset_version')}
        binding['binding_version'] = 1
        result = validate_binding(binding)
        if result['status'] != 'valid':
            return result
        if not result['campaign_playable']:
            return dict(result, status='unsupported', reason='ruleset_not_campaign_playable')
        session[BINDING_KEY] = binding
        session['ruleset_binding_migration'] = {'version': 1, 'source': 'explicit_session_metadata',
                                                'campaign_id': campaign_id}
        try:
            storage.save_session(session)
        except Exception as exc:
            return {'status': 'migration_failed', 'reason': type(exc).__name__}
        return dict(result, status='migrated')

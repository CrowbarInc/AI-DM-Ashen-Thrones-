"""Deterministic campaign contracts; evidence describes policy, never equip execution."""
import copy
import ast
import json
import os
import subprocess
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from game import storage
from game import campaign_ruleset as cr
from game.campaign_state import create_fresh_session_document
from game.pf1e_equipment_policy import padded_armor_definition
from tests.helpers.turn_pipeline_http_fixtures import _patch_storage

ROWS = []
BASE_DOMAINS = {}
PF = {'ruleset_id': 'pf1e', 'ruleset_version': '1', 'binding_version': 1}


@pytest.fixture
def campaign(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    monkeypatch.setattr(storage, 'SNAPSHOTS_DIR', storage.DATA_DIR / 'snapshots')
    for scene in (Path(__file__).resolve().parents[1] / 'data/scenes').glob('*.json'):
        shutil.copy2(scene, storage.SCENES_DIR / scene.name)
    storage.ensure_data_files_exist()
    session = storage.load_session()
    BASE_DOMAINS.clear()
    BASE_DOMAINS.update(character=storage.load_character(), world=storage.load_world(), combat=storage.load_combat())
    yield session


def raw_session(session):
    from game.persistence_contract import wrap_runtime_payload
    storage._atomic_save_json(storage.SESSION_PATH, wrap_runtime_payload(
        kind='session', payload=session, saved_at='test', include_integrity=True))


def record(case, before, actual, expected, parameters=None):
    after = storage.load_session()
    row = {'id': case, 'campaign_id': before.get('campaign_run_id'),
           'initial_binding': before.get('ruleset_binding'), 'operation': case,
           'expected': expected, 'actual': actual, 'registry_resolution': cr.validate_binding(after.get('ruleset_binding')),
           'state_delta': {k: after.get(k) for k in set(before) | set(after) if before.get(k) != after.get(k)},
           'persistence': after.get('ruleset_binding'), 'assertion': actual == expected}
    row['requested_parameters'] = parameters if parameters is not None else {'scenario': case}
    row['initial_explicit_legacy_metadata'] = {k: before[k] for k in ('ruleset_id', 'ruleset_version') if k in before}
    row['registry_resolution_basis'] = 'persisted campaign after operation; rejection must preserve the prior campaign'
    if case.startswith('creation_'):
        candidate = PF if parameters is None else dict(parameters, binding_version=1)
        row['requested_registry_resolution'] = cr.validate_binding(candidate)
    row['domain_state_delta'] = {k: value for k, value in {
        'character': storage.load_character(), 'world': storage.load_world(),
        'combat': storage.load_combat()}.items() if value != BASE_DOMAINS[k]}
    row['assertion'] = row['assertion'] and not row['domain_state_delta']
    ROWS.append(row)
    target = os.environ.get('ASHEN_TEST_EVIDENCE_DIR')
    if target:
        (Path(target) / 'acceptance_matrix.json').write_text(json.dumps(ROWS, indent=2), encoding='utf-8')
    assert actual == expected
    assert not row['domain_state_delta']


CREATION = [
    ('explicit', {'ruleset_id': 'pf1e', 'ruleset_version': '1'}, 'valid'),
    ('default', None, 'valid'), ('unknown', {'ruleset_id': 'other', 'ruleset_version': '1'}, 'unknown_ruleset'),
    ('version', {'ruleset_id': 'pf1e', 'ruleset_version': '2'}, 'unsupported_version'),
    ('missing', {}, 'invalid_binding'), ('malformed', {'ruleset_id': 'PF!', 'ruleset_version': '1'}, 'malformed_identifier'),
    ('placeholder', {'ruleset_id': 'scifi', 'ruleset_version': '1'}, 'ruleset_not_campaign_playable'),
    ('repeated', None, 'valid'), ('persisted', None, 'valid'), ('response', None, 'valid')]


@pytest.mark.parametrize('name,selection,expected', CREATION)
def test_creation(campaign, name, selection, expected):
    before = copy.deepcopy(campaign)
    try:
        b = cr.creation_binding(selection)
        assert b == PF
        if name == 'repeated':
            assert cr.creation_binding(selection) == b
        storage.save_session(dict(campaign, ruleset_binding=b))
        actual = cr.resolve_campaign_ruleset(campaign['campaign_run_id'])['status']
    except cr.CampaignBindingError as exc:
        actual = str(exc)
    record('creation_' + name, before, actual, expected, selection)


LOAD = [('valid', PF, 'valid'), ('missing', None, 'missing'), ('invalid', {}, 'invalid'),
        ('version', dict(PF, ruleset_version='2'), 'unsupported'),
        ('unknown', dict(PF, ruleset_id='other'), 'unknown'), ('repeat', PF, 'valid'),
        ('restart', PF, 'valid'), ('restore', PF, 'valid'), ('corrupt', 'bad', 'invalid'),
        ('preserve', PF, 'valid')]


@pytest.mark.parametrize('name,binding,expected', LOAD)
def test_loading(campaign, name, binding, expected):
    session = dict(campaign)
    if binding is None:
        session.pop('ruleset_binding', None)
    else:
        session['ruleset_binding'] = binding
    raw_session(session)
    before = storage.load_session()
    if name == 'restart':
        env = dict(os.environ, ASHEN_DATA_DIR=str(storage.DATA_DIR))
        code = 'from game.campaign_ruleset import resolve_campaign_ruleset; print(resolve_campaign_ruleset(' + repr(session['campaign_run_id']) + ')["status"])'
        actual = subprocess.check_output([sys.executable, '-c', code], env=env, text=True).strip()
    else:
        if name == 'restore':
            snap = storage.create_snapshot('bound')
            storage.load_snapshot(snap['id'])
        if name == 'preserve':
            update = dict(session); update.pop('ruleset_binding'); update['flags'] = {'test': True}
            storage.save_session(update)
        actual = cr.resolve_campaign_ruleset(session['campaign_run_id'])['status']
        if name == 'repeat':
            assert cr.resolve_campaign_ruleset(session['campaign_run_id'])['status'] == actual
    record('load_' + name, before, actual, expected)


MIGRATE = [('explicit_pf', 'pf1e', '1', 'migrated'), ('explicit_other', 'scifi', '1', 'unsupported'),
           ('ambiguous', None, None, 'ambiguous'), ('missing', None, None, 'ambiguous'),
           ('malformed', 3, '1', 'invalid'), ('repeat', 'pf1e', '1', 'already_bound'),
           ('interrupted', 'pf1e', '1', 'migration_failed'), ('reload', 'pf1e', '1', 'migrated'),
           ('character', 'pf1e', '1', 'migrated'), ('world', 'pf1e', '1', 'migrated')]


@pytest.mark.parametrize('name,rid,version,expected', MIGRATE)
def test_migration(campaign, monkeypatch, name, rid, version, expected):
    session = dict(campaign); session.pop('ruleset_binding', None)
    if rid is not None:
        session.update(ruleset_id=rid, ruleset_version=version)
    raw_session(session)
    before = storage.load_session()
    original = storage.SESSION_PATH.read_bytes()
    character, world = storage.load_character(), storage.load_world()
    if name == 'repeat':
        assert cr.migrate_legacy_campaign(session['campaign_run_id'])['status'] == 'migrated'
    if name == 'interrupted':
        def fail(*args):
            raise OSError('injected precommit failure')
        monkeypatch.setattr(storage.os, 'replace', fail)
    actual = cr.migrate_legacy_campaign(session['campaign_run_id'])['status']
    if name == 'interrupted':
        assert storage.SESSION_PATH.read_bytes() == original
    assert storage.load_character() == character and storage.load_world() == world
    if actual in ('migrated', 'already_bound'):
        assert storage.load_session()['ruleset_binding'] == PF
    record('migration_' + name, before, actual, expected)


@pytest.mark.parametrize('name,binding,capability,expected', [
    ('pf', PF, 'equipment_policy', 'mechanically_unresolved'),
    ('eligibility', PF, 'equipment_policy', 'ELIGIBLE'),
    ('slot', PF, 'equipment_policy', 'body_armor'),
    ('uncertainty', PF, 'equipment_policy', 'UNRESOLVED'),
    ('blocked', PF, 'equipment_policy', 'BLOCKED_MECHANICAL_RECONCILIATION'),
    ('capability', PF, 'combat_resolution', 'unsupported'),
    ('unknown', dict(PF, ruleset_id='other'), 'equipment_policy', 'unknown'),
    ('version', dict(PF, ruleset_version='2'), 'equipment_policy', 'unsupported'),
    ('missing', None, 'equipment_policy', 'missing'),
    ('invalid', {}, 'equipment_policy', 'invalid')])
def test_delegation(campaign, name, binding, capability, expected):
    session = dict(campaign, ruleset_binding=binding); raw_session(session)
    before = storage.load_session()
    result = cr.evaluate_campaign_policy(session['campaign_run_id'], capability,
            {'item': padded_armor_definition(), 'slot': 'body_armor'}, {})
    actual = result.get('evaluation', result)['status']
    if name in ('eligibility', 'uncertainty', 'blocked', 'slot'):
        payload = result['evaluation']['ruleset_result']
        key = {'eligibility': 'decision', 'uncertainty': 'mechanical_consequence',
               'blocked': 'execution_readiness', 'slot': 'slot'}[name]
        actual = payload[key]
    assert storage.load_session() == before
    record('delegation_' + name, before, actual, expected)


@pytest.mark.parametrize('name', ['campaign_a', 'campaign_b', 'concurrent', 'request_conflict', 'stale',
                                 'no_fallback', 'no_contamination', 'no_alias', 'no_mutation', 'no_switch'])
def test_isolation(campaign, name):
    before = copy.deepcopy(campaign)
    cid = campaign['campaign_run_id']
    if name in ('campaign_b', 'no_fallback'):
        raw_session(dict(campaign, ruleset_binding=dict(PF, ruleset_id='scifi')))
        result = cr.resolve_campaign_ruleset(cid, 'equipment_policy')
        assert result['status'] == 'unsupported'
    elif name == 'concurrent':
        with ThreadPoolExecutor(4) as pool:
            results = list(pool.map(cr.resolve_campaign_ruleset, [cid, 'other'] * 8))
        assert all(r['status'] == ('valid' if i % 2 == 0 else 'invalid') for i, r in enumerate(results))
    elif name == 'no_alias':
        result = cr.resolve_campaign_ruleset(cid); result['binding']['ruleset_id'] = 'scifi'
        assert storage.load_session()['ruleset_binding'] == PF
    elif name in ('stale', 'no_switch'):
        with pytest.raises(cr.CampaignBindingError):
            storage.save_session(dict(campaign, ruleset_binding=dict(PF, ruleset_id='scifi')))
        assert storage.load_session()['ruleset_binding'] == PF
    else:
        assert cr.resolve_campaign_ruleset('other')['reason'] == 'campaign_mismatch'
        assert cr.resolve_campaign_ruleset(cid)['binding'] == PF
    record('isolation_' + name, before, True, True)


@pytest.mark.parametrize('name', ['reload', 'restart', 'atomic_failure', 'stale_write', 'duplicate',
                                 'idempotent', 'character', 'inventory', 'world', 'unrelated'])
def test_integrity(campaign, monkeypatch, name):
    before = copy.deepcopy(campaign)
    character, world = storage.load_character(), storage.load_world()
    if name == 'atomic_failure':
        raw = storage.SESSION_PATH.read_bytes()
        def fail(*args):
            raise OSError('injected failure')
        monkeypatch.setattr(storage.os, 'replace', fail)
        with pytest.raises(OSError):
            storage.save_session(dict(campaign, flags={'test': True}))
        assert storage.SESSION_PATH.read_bytes() == raw
    elif name == 'stale_write':
        stale = dict(campaign); stale.pop('ruleset_binding')
        storage.save_session(stale)
    else:
        storage.save_session(dict(campaign, flags={'test': True}))
        if name in ('duplicate', 'idempotent'):
            storage.save_session(storage.load_session())
    assert storage.load_character() == character and storage.load_world() == world
    assert storage.load_session()['ruleset_binding'] == PF
    record('integrity_' + name, before, True, True)


@pytest.mark.parametrize('module', ['campaign_ruleset', 'campaign_state', 'storage'])
def test_generic_owners_do_not_import_mechanics(module):
    path = Path(__file__).resolve().parents[1] / 'game' / (module + '.py')
    imports = []
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
        if isinstance(node, ast.Import):
            imports.extend(a.name for a in node.names)
        if isinstance(node, ast.ImportFrom):
            imports.append(node.module or '')
    assert not any('pf1e' in name or 'pathfinder' in name for name in imports)


def test_corrupt_bound_envelope_never_defaults(campaign):
    from game.persistence_contract import PersistenceContractError
    original = json.loads(storage.SESSION_PATH.read_text())
    for bound in (True, False):
        raw = copy.deepcopy(original)
        if bound:
            raw['payload']['ruleset_binding']['ruleset_id'] = 'scifi'
        else:
            raw['payload'].pop('ruleset_binding')
        storage.SESSION_PATH.write_text(json.dumps(raw))
        before = storage.SESSION_PATH.read_bytes()
        with pytest.raises(PersistenceContractError):
            storage.load_session()
        assert cr.resolve_campaign_ruleset(campaign['campaign_run_id'])['status'] == 'invalid'
        assert cr.migrate_legacy_campaign(campaign['campaign_run_id'])['status'] == 'migration_failed'
        assert storage.SESSION_PATH.read_bytes() == before


def test_stale_root_before_migration_cannot_drop_binding(campaign):
    legacy = dict(campaign); legacy.pop('ruleset_binding')
    legacy.update(ruleset_id='pf1e', ruleset_version='1'); raw_session(legacy)
    stale = storage.load_session()
    assert cr.migrate_legacy_campaign(legacy['campaign_run_id'])['status'] == 'migrated'
    provenance = storage.load_session()['ruleset_binding_migration']
    storage.save_session(stale)
    assert storage.load_session()['ruleset_binding'] == PF
    assert storage.load_session()['ruleset_binding_migration'] == provenance


def test_creation_rejects_binding_protocol_version():
    with pytest.raises(cr.CampaignBindingError):
        cr.creation_binding(dict(PF, binding_version=2))


def test_public_projection_exposes_only_bounded_identity_and_policy():
    from game.player_http_projection import project_player_response
    source = {'campaign_ruleset': {'status':'valid', 'binding':PF, 'implementation':'PRIVATE',
              'evaluation': {'ruleset_result': {'decision':'ELIGIBLE', 'secret':'PRIVATE'}}}}
    projected = project_player_response(source)
    assert projected['campaign_ruleset']['binding'] == PF
    assert 'PRIVATE' not in json.dumps(projected)
    assert project_player_response(projected) == projected


def test_nonpathfinder_resolution_does_not_import_pathfinder(campaign):
    raw_session(dict(campaign, ruleset_binding=dict(PF, ruleset_id='scifi')))
    env = dict(os.environ, ASHEN_DATA_DIR=str(storage.DATA_DIR))
    code = ('import sys; from game.campaign_ruleset import resolve_campaign_ruleset; '
            'r=resolve_campaign_ruleset(' + repr(campaign['campaign_run_id']) + ', "equipment_policy"); '
            'assert r["status"]=="unsupported"; assert "game.pf1e_equipment_policy" not in sys.modules')
    subprocess.check_call([sys.executable, '-c', code], env=env)


def test_migration_incomplete_metadata_is_invalid(campaign):
    legacy = dict(campaign); legacy.pop('ruleset_binding'); legacy['ruleset_id'] = 'pf1e'
    raw_session(legacy)
    assert cr.migrate_legacy_campaign(campaign['campaign_run_id'])['status'] == 'invalid'


def test_migration_unsupported_version_is_preserved(campaign):
    legacy = dict(campaign); legacy.pop('ruleset_binding')
    legacy.update(ruleset_id='pf1e', ruleset_version='9'); raw_session(legacy)
    before = storage.SESSION_PATH.read_bytes()
    assert cr.migrate_legacy_campaign(campaign['campaign_run_id'])['status'] == 'unsupported'
    assert storage.SESSION_PATH.read_bytes() == before


def test_snapshot_restores_binding_with_its_original_identity(campaign):
    snapshot = storage.create_snapshot('campaign a')
    other = dict(campaign, campaign_run_id='controlled_b', ruleset_binding=dict(PF, ruleset_id='scifi'))
    raw_session(other)
    assert cr.resolve_campaign_ruleset(campaign['campaign_run_id'])['reason'] == 'campaign_mismatch'
    storage.load_snapshot(snapshot['id'])
    assert cr.resolve_campaign_ruleset(campaign['campaign_run_id'])['binding'] == PF

"""Structured-only marking, durable retries, snapshot timelines and failures."""
import copy
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from game import api, storage
from game import object_marking as marking
from tests.test_object_instances import saved, migrate, RUN


@pytest.fixture
def established(saved):
    migrate(0); migrate(1)
    return storage.load_character()


def request(character=None, **changes):
    character = character or storage.load_character()
    row = character['inventory'][0]
    req = dict(version=1, operation='add_marking', campaign_run_id=RUN,
        character_id=character['id'], instance_id=row['instance_id'],
        request_id='mark-request-1', expected_revision=row['revision'], content='Northwest track',
        source={'kind': 'explicit_literal', 'reference': 'controlled-fixture'},
        authorization={'caller_id': 'internal-test', 'decision_id': 'approval-1',
            'content_sha256': hashlib.sha256(b'Northwest track').hexdigest(),
            'preconditions': {key: 'fixture-evidence:' + key for key in marking.PRECONDITIONS},
            'mechanics': 'not_applicable'})
    req.update(changes)
    req['request_digest'] = marking.request_digest(req)
    return req


def apply(req): return api.add_inventory_object_marking(req)


def evidence(name, value):
    out = os.getenv('ASHEN_TEST_EVIDENCE_DIR')
    if out: (Path(out)/name).write_text(json.dumps(value, indent=2), encoding='utf-8')


def test_roundtrip_retry_and_identical_objects(established):
    req = request(); before = storage.load_character()
    result = apply(req)
    assert result['status'] == 'applied' and result['persistence'] == 'committed'
    loaded = storage.load_character(); row = loaded['inventory'][0]
    assert row['revision'] == 1 and row['instance_id'] == before['inventory'][0]['instance_id']
    assert loaded['inventory'][1] == before['inventory'][1]
    assert row['markings'][0]['content'] == req['content']
    assert row['markings'][0]['source'] == req['source']
    assert row['markings'][0]['authorization'] == req['authorization']
    raw = storage.CHARACTER_PATH.read_bytes()
    assert apply(copy.deepcopy(req)) == result
    assert storage.CHARACTER_PATH.read_bytes() == raw
    evidence('marking_round_trip.json', dict(request=req, result=result, before=before,
        reloaded=loaded, replay=apply(req)))


def test_conflicting_replay_and_new_request(established):
    req = request(); first = apply(req); before = storage.CHARACTER_PATH.read_bytes()
    conflict = request(request_id=req['request_id'])
    assert apply(conflict)['error'] == 'conflicting_request'
    assert storage.CHARACTER_PATH.read_bytes() == before
    second = apply(request(request_id='deliberate-repeat'))
    assert second['resulting_revision'] == 2
    assert second['modification_id'] != first['modification_id']
    assert len(storage.load_character()['inventory'][0]['markings']) == 2


@pytest.mark.parametrize('change,error', [
    ({'expected_revision': 5}, 'stale_revision'),
    ({'expected_revision': True}, 'invalid_request'),
    ({'instance_id': 'missing'}, 'invalid_request'),
    ({'campaign_run_id': 'other'}, 'campaign_mismatch'),
    ({'character_id': 'other'}, 'character_mismatch'),
    ({'request_id': ''}, 'invalid_request'),
    ({'request_id': 'x'*257}, 'invalid_request'),
    ({'request_digest': '0'*64}, 'invalid_digest'),
    ({'operation': 'craft'}, 'invalid_request'),
    ({'authorization': None}, 'unauthorized_content'),
    ({'authorization': {}}, 'unauthorized_content'),
    ({'content': 'é'*1025}, 'invalid_content'),
    ({'content': ''}, 'invalid_content'),
    ({'content': '\ud800'}, 'invalid_content'),
    ({'source': {'kind': 'hidden', 'reference': 'secret'}}, 'invalid_source'),
])
def test_rejections_do_not_mutate(established, change, error):
    req = request()
    req.update(change)
    if 'request_digest' not in change:
        try: req['request_digest'] = marking.request_digest(req)
        except (ValueError, UnicodeError): pass
    before = storage.CHARACTER_PATH.read_bytes()
    assert apply(req)['error'] == error
    assert storage.CHARACTER_PATH.read_bytes() == before


@pytest.mark.parametrize('key', ['caller_id', 'decision_id', 'content_sha256', 'preconditions', 'mechanics'])
def test_authorization_requires_every_field(established, key):
    req = request(); req['authorization'].pop(key); req['request_digest'] = marking.request_digest(req)
    assert apply(req)['error'] == 'unauthorized_content'


@pytest.mark.parametrize('key', sorted(marking.PRECONDITIONS))
def test_positive_precondition_evidence_required(established, key):
    req = request(); req['authorization']['preconditions'][key] = ''
    req['request_digest'] = marking.request_digest(req)
    assert apply(req)['error'] == 'unauthorized_content'


@pytest.mark.parametrize('fault', ['missing', 'malformed', 'duplicate', 'stack', 'bad_markings', 'bad_receipts'])
def test_invalid_target_and_schema_fail_closed(established, fault):
    req = request(); c = storage.load_character(); row = c['inventory'][0]
    if fault == 'missing':
        for k in ('instance_id','revision','provenance'): row.pop(k)
    elif fault == 'malformed': row['revision'] = -1
    elif fault == 'duplicate': c['inventory'][1] = copy.deepcopy(row)
    elif fault == 'stack': row['quantity'] = 2
    elif fault == 'bad_markings': row['markings'] = {'legacy': 'keep'}
    else: c['object_marking_receipts'] = {'legacy': 'keep'}
    storage.save_character(c); before = storage.CHARACTER_PATH.read_bytes()
    assert apply(req)['status'] == 'rejected'
    assert storage.CHARACTER_PATH.read_bytes() == before
    assert storage.load_character() == c


def test_unknown_fields_and_rulesets_preserved(established):
    c = storage.load_character()
    c['inventory'][0]['extensions'] = {'pf1': {'damage': '1d4'}, 'scifi': {'power': 42}}
    storage.save_character(c)
    apply(request()); after = storage.load_character()['inventory'][0]
    for key, value in c['inventory'][0].items():
        if key != 'revision': assert after[key] == value


def test_snapshot_timeline_restores_markings_revision_and_receipts(established):
    req = request(); pre = storage.create_snapshot('pre marking')
    result = apply(req); committed = storage.load_character(); post = storage.create_snapshot('post marking')
    assert storage.load_snapshot(pre['id'])
    assert storage.load_character() == established
    reapplied = apply(req)
    assert reapplied['status'] == 'applied'  # rollback legitimately predates request
    assert storage.load_snapshot(post['id'])
    assert storage.load_character() == committed and apply(req) == result
    evidence('marking_snapshots.json', dict(before=established, committed=committed,
        pre_snapshot=pre, post_snapshot=post, restored=storage.load_character(),
        original_result=result, post_restore_replay=apply(req), rolled_back_timeline_result=reapplied))


@pytest.mark.parametrize('fault', ['replace', 'save'])
def test_persistence_failure_has_no_success_or_partial_receipt(established, monkeypatch, fault):
    req = request(); before = storage.CHARACTER_PATH.read_bytes()
    def fail(*a, **kw): raise OSError('injected marking persistence failure')
    monkeypatch.setattr(storage.os if fault == 'replace' else storage,
        'replace' if fault == 'replace' else 'save_character', fail)
    with pytest.raises(OSError): apply(req)
    assert storage.CHARACTER_PATH.read_bytes() == before
    assert storage.load_character() == established


@pytest.mark.parametrize('field,value', [('request_digest', '0'*64), ('resulting_revision', 8),
    ('modification_id', 'bad'), ('status', 'proposed'), ('extra', True)])
def test_receipt_tampering_rejected(established, field, value):
    req = request(); apply(req); c = storage.load_character()
    c['object_marking_receipts']['entries'][req['request_id']][field] = value
    storage.save_character(c); before = storage.CHARACTER_PATH.read_bytes()
    assert apply(req)['error'] == 'invalid_receipt_state'
    assert storage.CHARACTER_PATH.read_bytes() == before


def test_missing_receipt_and_changed_content_rejected(established):
    req = request(); apply(req); c = storage.load_character()
    c['object_marking_receipts']['entries'].clear(); storage.save_character(c)
    assert apply(req)['error'] == 'invalid_receipt_state'


def test_marking_capacity_and_new_request_not_text_dedupe(established):
    for n in range(16): assert apply(request(request_id=f'mark-{n}'))['status'] == 'applied'
    before = storage.CHARACTER_PATH.read_bytes()
    assert apply(request(request_id='overflow'))['error'] == 'marking_capacity'
    assert storage.CHARACTER_PATH.read_bytes() == before


def test_concurrent_exact_retries_share_one_durable_result(established):
    req = request()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(apply, [req, copy.deepcopy(req)]))
    assert results[0] == results[1]
    assert storage.load_character()['inventory'][0]['revision'] == 1


def test_concurrent_new_requests_reject_stale_revision(established):
    reqs = [request(request_id=f'concurrent-{n}') for n in range(2)]
    with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(apply, reqs))
    assert sorted(r['status'] for r in results) == ['applied', 'rejected']
    assert next(r for r in results if r['status'] == 'rejected')['error'] == 'stale_revision'


def test_pure_proposal_never_mutates_input(established):
    req = request(); old = copy.deepcopy(established)
    proposal = marking.prepare_marking(established, req)
    assert proposal['status'] == 'validated' and established == old
    assert proposal['character']['inventory'][0]['revision'] == 1


def test_canonical_digest_ignores_mapping_order(established):
    req = request(); reordered = dict(reversed(list(req.items())))
    assert marking.request_digest(req) == marking.request_digest(reordered)
    reordered['authorization'] = copy.deepcopy(req['authorization'])
    reordered['authorization']['decision_id'] = 'different approval'
    assert marking.request_digest(req) != marking.request_digest(reordered)


def test_no_gameplay_or_http_marking_route():
    assert not any('marking' in route.path for route in api.app.routes)


def test_total_text_capacity_and_unicode_byte_bound(established):
    content = 'é'*1024
    for n in range(4):
        req = request(request_id=f'large-{n}', content=content)
        req['authorization']['content_sha256'] = hashlib.sha256(content.encode()).hexdigest()
        req['request_digest'] = marking.request_digest(req)
        assert apply(req)['status'] == 'applied'
    assert apply(request(request_id='total-overflow'))['error'] == 'marking_capacity'


def test_target_can_be_reordered_and_other_request_cannot_reuse_key(established):
    req = request(); first = apply(req)
    c = storage.load_character(); c['inventory'].reverse(); storage.save_character(c)
    assert apply(req) == first
    other = request()
    assert apply(other)['error'] == 'conflicting_request'


def test_replay_does_not_save_or_allocate_new_identity(established, monkeypatch):
    req = request(); first = apply(req)
    def forbidden(*a, **kw): raise AssertionError('Replay must only read committed state')
    monkeypatch.setattr(storage,'save_character', forbidden)
    monkeypatch.setattr(marking,'uuid4', forbidden)
    assert apply(req) == first


def test_retry_after_precommit_failure_uses_original_request(established, monkeypatch):
    req = request(); real = storage.os.replace
    with monkeypatch.context() as patch:
        patch.setattr(storage.os,'replace',lambda *a, **kw: (_ for _ in ()).throw(OSError('precommit')))
        with pytest.raises(OSError): apply(req)
    result = apply(req)
    assert apply(req) == result
    assert len(storage.load_character()['inventory'][0]['markings']) == 1


def test_postwrite_exception_runtime_rollback_prevents_false_success(established, monkeypatch):
    req = request(); raw = storage.CHARACTER_PATH.read_bytes(); real = storage.save_character
    def fail_after(data):
        real(data)
        raise OSError('exception after replacement')
    monkeypatch.setattr(storage,'save_character',fail_after)
    with pytest.raises(OSError): apply(req)
    assert storage.CHARACTER_PATH.read_bytes() == raw


@pytest.mark.parametrize('payload', [None, [], 'mark this', {'operation':'add_marking'}])
def test_unstructured_inputs_are_not_authorization(established, payload):
    assert apply(payload)['status'] == 'rejected'


def test_marking_content_tampering_is_detected(established):
    req = request(); apply(req); c = storage.load_character()
    c['inventory'][0]['markings'][0]['content'] = 'Forged content'
    storage.save_character(c)
    assert apply(req)['error'] == 'invalid_receipt_state'


def test_unknown_request_fields_fail_closed(established):
    req = request(); req['invented_tool'] = 'ink'; req['request_digest'] = marking.request_digest(req)
    assert apply(req)['error'] == 'invalid_request'


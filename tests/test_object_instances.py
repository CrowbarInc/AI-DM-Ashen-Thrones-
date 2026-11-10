"""Behavioral identity, real character storage, and snapshot controls."""
import copy
import json
import os
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from game import api, storage
from game import object_instances as objects
from tests.helpers.turn_pipeline_http_fixtures import _patch_storage

RUN = 'identity-test-campaign'
OP = 'explicit-migration-1'
def item(**fields):
    return dict(id='dagger', name='Dagger', quantity=1, usable=False, **fields)
def character(*rows):
    return {'id':'hero','inventory':list(rows),'unknown_character':{'keep':True}}
def ensure(c, index=0):
    return objects.ensure_object_instance_identity(c, index, campaign_run_id=RUN, operation_id=OP)

@pytest.fixture
def saved(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    monkeypatch.setattr(storage,'SNAPSHOTS_DIR',tmp_path/'snapshots')
    from game.defaults import default_scene
    storage.save_scene(default_scene('frontier_gate'))
    storage.save_session(dict(storage.load_session(), campaign_run_id=RUN))
    storage.save_character(character(item(legacy={'nested':[1,2]}),item()))
    return tmp_path

def migrate(index=0, **kw):
    return api.migrate_inventory_object_identity(index, expected_item=storage.load_character()['inventory'][index],
        campaign_run_id=RUN, operation_id=OP, **kw)

def test_assignment_distinguishes_identical_definitions_and_preserves_input():
    original=character(item(),item()); before=copy.deepcopy(original)
    first=ensure(original)
    assert first.status=='assigned' and original==before
    assert UUID(first.instance_id).version==4
    second=ensure(first.character,1)
    assert first.instance_id!=second.instance_id
    assert second.character['inventory'][0]==first.character['inventory'][0]

def test_repeat_reorder_rename_and_statistics_preserve_identity():
    original=character(item(extensions={'pf1':{'damage':'1d4'},'modern':{'charge':7}}),item())
    assigned=ensure(original); row=copy.deepcopy(assigned.character['inventory'][0])
    again=ensure(assigned.character)
    assert again.status=='existing' and again.character==assigned.character
    moved=copy.deepcopy(assigned.character); moved['inventory'].reverse()
    moved['inventory'][1]['name']='Old knife'
    moved['inventory'][1]['extensions']['modern']['charge']=6
    assert ensure(moved,1).instance_id==row['instance_id']
    assert ensure(moved,1).character==moved
    assert row['extensions']==original['inventory'][0]['extensions']
    assert row['revision']==0

@pytest.mark.parametrize('extension',[{'pf1':{'ac':4}}, {'rules_light':{'tags':['small']}}, {'scifi':{'power':99}}])
def test_unknown_fields_and_rulesets_are_inert(extension):
    c=character(item(extensions=extension, unknown={'a':[True,None]}),item())
    r=ensure(c); promoted=r.character['inventory'][0]
    assert {k:promoted[k] for k in c['inventory'][0]}==c['inventory'][0]
    assert r.character['inventory'][1]==c['inventory'][1]
    assert r.character['unknown_character']==c['unknown_character']

@pytest.mark.parametrize('row',[None, 'dagger', {}, {'id':'d','name':'D','quantity':1},
    {'id':'','name':'D','quantity':1,'usable':False},
    {'id':'d','name':'','quantity':1,'usable':False}]+[
    {'id':'d','name':'D','quantity':q,'usable':False} for q in (2,0,-1,1.0,True,'1',None)])
def test_ineligible_records_are_not_partially_migrated(row):
    c=character(row); before=copy.deepcopy(c)
    r=ensure(c)
    assert r.status=='rejected' and r.error and r.character is None
    assert c==before

@pytest.mark.parametrize('fields',[{'instance_id':None},{'instance_id':'bad'},
    {'revision':0},{'provenance':{'old_import':'keep'}},
    {'instance_id':str(uuid4()),'revision':0},
    {'instance_id':str(uuid4()),'revision':True,'provenance':{}},
    {'instance_id':str(uuid4()).upper(),'revision':0,'provenance':{}}])
def test_malformed_identity_is_rejected_never_replaced(fields):
    c=character(dict(item(),**fields)); before=copy.deepcopy(c)
    assert ensure(c).status=='rejected' and c==before

@pytest.mark.parametrize('change',[{'version':2},{'campaign_run_id':'other'},
    {'operation_id':''},{'source':{'host':'scene','legacy_id':'dagger'}}])
def test_provenance_conflicts_reject(change):
    c=ensure(character(item())).character
    c['inventory'][0]['provenance'].update(change)
    before=copy.deepcopy(c)
    assert ensure(c).status=='rejected' and c==before

def test_duplicate_id_on_another_record_blocks_assignment():
    c=ensure(character(item(),item(),item())).character
    c['inventory'][1]=copy.deepcopy(c['inventory'][0])
    before=copy.deepcopy(c)
    r=ensure(c,2)
    assert r.error=='duplicate_instance_id' and c==before
    assert ensure(c,0).error=='duplicate_instance_id'

def test_generation_collision_fails_without_retry(monkeypatch):
    c=ensure(character(item(),item())).character
    monkeypatch.setattr(objects,'uuid4',lambda:UUID(c['inventory'][0]['instance_id']))
    assert ensure(c,1).error=='duplicate_instance_id'
    assert 'instance_id' not in c['inventory'][1]

def test_inspection_is_pure_and_reports_legacy_existing_invalid():
    c=character(item()); before=copy.deepcopy(c)
    assert objects.inspect_object_identity(c,0,campaign_run_id=RUN).status=='legacy'
    assert c==before
    c=ensure(c).character
    assert objects.inspect_object_identity(c,0,campaign_run_id=RUN).status=='existing'
    c['inventory'][0]['revision']=-1
    assert objects.inspect_object_identity(c,0,campaign_run_id=RUN).status=='rejected'

def test_real_save_reload_repeat_and_snapshot(saved):
    before=storage.load_character(); result=migrate(); after=storage.load_character()
    assert result.status=='assigned' and after==result.character
    assert after['inventory'][1]==before['inventory'][1]
    raw=storage.CHARACTER_PATH.read_bytes()
    assert migrate().status=='existing' and storage.CHARACTER_PATH.read_bytes()==raw
    snapshot=storage.create_snapshot('singleton identity')
    changed=copy.deepcopy(after); changed['inventory'].reverse(); changed['name']='changed'
    storage.save_character(changed)
    assert storage.load_snapshot(snapshot['id']) is not None
    assert storage.load_character()==after
    assert migrate().instance_id==result.instance_id
    evidence=os.environ.get('ASHEN_TEST_EVIDENCE_DIR')
    if evidence:
        (Path(evidence)/'persistence_round_trip.json').write_text(json.dumps({
            'before':before,'assigned':after,'reloaded':result.character,
            'snapshot_id':snapshot['id'],'restored':storage.load_character()},indent=2))

def test_stale_selection_campaign_and_validation_do_not_write(saved):
    old=storage.load_character()['inventory'][0]
    c=storage.load_character(); c['inventory'].reverse(); storage.save_character(c)
    raw=storage.CHARACTER_PATH.read_bytes()
    r=api.migrate_inventory_object_identity(0,expected_item=old,campaign_run_id=RUN,operation_id=OP)
    assert r.error=='stale_selection' and storage.CHARACTER_PATH.read_bytes()==raw
    r=api.migrate_inventory_object_identity(0,expected_item=c['inventory'][0],campaign_run_id='other',operation_id=OP)
    assert r.error=='campaign_mismatch' and storage.CHARACTER_PATH.read_bytes()==raw

@pytest.mark.parametrize('stage',['before','after_partial','after_complete'])
def test_character_save_failure_restores_original_bytes(saved,monkeypatch,stage):
    raw=storage.CHARACTER_PATH.read_bytes(); save=storage._save_json
    def fail(path,data):
        if path==storage.CHARACTER_PATH:
            if stage=='after_partial': path.write_text('{')
            if stage=='after_complete': save(path,data)
            raise OSError('injected character write failure')
        return save(path,data)
    monkeypatch.setattr(storage,'_save_json',fail)
    with pytest.raises(OSError): migrate()
    assert storage.CHARACTER_PATH.read_bytes()==raw
    assert 'instance_id' not in storage.load_character()['inventory'][0]

def test_snapshot_restore_failure_preserves_migrated_identity(saved,monkeypatch):
    migrate(); snapshot=storage.create_snapshot('identity')
    c=storage.load_character(); c['notes']='later'; storage.save_character(c)
    raw=storage.CHARACTER_PATH.read_bytes(); write=storage._atomic_save_json
    def fail(path,data):
        if path==storage.CHARACTER_PATH: raise OSError('restore fault')
        return write(path,data)
    monkeypatch.setattr(storage,'_atomic_save_json',fail)
    with pytest.raises(Exception): storage.load_snapshot(snapshot['id'])
    assert storage.CHARACTER_PATH.read_bytes()==raw

def test_normal_load_and_player_projection_do_not_migrate(saved):
    from game.player_http_projection import project, CHARACTER
    before=storage.CHARACTER_PATH.read_bytes()
    c=storage.load_character()
    assert project(c,CHARACTER)['inventory'][0]['name']=='Dagger'
    assert storage.CHARACTER_PATH.read_bytes()==before
    migrate()
    assert project(storage.load_character(),CHARACTER)['inventory'][0]['name']=='Dagger'

@pytest.mark.parametrize('index',[-1,True,1.0,'0',99])
def test_invalid_selector_is_rejected(index):
    assert ensure(character(item()),index).status=='rejected'

def test_object_authority_is_narrow():
    from game.state_authority import assert_owner_can_mutate_domain, WORLD_STATE, StateAuthorityError
    assert_owner_can_mutate_domain('game.object_instances',WORLD_STATE,operation='assign_inventory_identity')
    with pytest.raises(StateAuthorityError):
        assert_owner_can_mutate_domain('game.object_instances',WORLD_STATE,operation='change_character_hp')

def test_aliases_do_not_migrate_an_unselected_row():
    row=item(); c=character(row,row)
    r=ensure(c)
    assert 'instance_id' in r.character['inventory'][0]
    assert r.character['inventory'][1]==row and c['inventory'][0] is c['inventory'][1]

@pytest.mark.parametrize('c',[None,{}, {'inventory':{}},{'inventory':[]}])
def test_invalid_host_is_rejected(c):
    assert ensure(c).status=='rejected'

def test_snapshot_creation_fault_does_not_change_identity(saved,monkeypatch):
    migrate(); raw=storage.CHARACTER_PATH.read_bytes()
    def fail(*args,**kwargs): raise OSError('snapshot creation fault')
    monkeypatch.setattr(storage,'_atomic_save_json',fail)
    with pytest.raises(OSError): storage.create_snapshot('failure')
    assert storage.CHARACTER_PATH.read_bytes()==raw

def test_concurrent_explicit_selection_cannot_mint_twice(saved):
    from concurrent.futures import ThreadPoolExecutor
    expected=copy.deepcopy(storage.load_character()['inventory'][0])
    def request(_):
        return api.migrate_inventory_object_identity(0,expected_item=expected,
            campaign_run_id=RUN,operation_id=OP)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(request,range(2)))
    assert sorted(r.status for r in results)==['assigned','rejected']
    assert next(r for r in results if r.status=='rejected').error=='stale_selection'
    assert objects.inspect_object_identity(storage.load_character(),0,campaign_run_id=RUN).status=='existing'

"""Fail-closed T06 evidence. These tests do not claim inscription support."""
import copy
import pytest
from game import storage
from tests.test_pr_play_post_npc_handoff import client, _say

REQUEST = "I try to copy the patrol warning onto my sleeve with a bit of mud so I won't forget the wording."

@pytest.mark.parametrize('equipment', ['original', 'empty', 'unknown', 'named_material'])
def test_unestablished_target_and_material_do_not_create_physical_copy(client, equipment):
    _say(client, 'Read me the missing-patrol notice, not the tax lines.')
    character = storage.load_character()
    if equipment == 'empty':
        character['inventory'] = []
    elif equipment == 'unknown':
        character.pop('inventory', None)
    elif equipment == 'named_material':
        # Existing inventory row shape; naming mud still supplies no sleeve
        # instance, suitability, or compatible modification authority.
        character['inventory'] = [{'id': 'mud', 'name': 'Mud', 'quantity': 1, 'usable': True}]
    storage.save_character(character)
    before = copy.deepcopy(storage.load_character())
    scene = copy.deepcopy(storage.load_scene('frontier_gate'))
    knowledge = copy.deepcopy(storage.load_session()['clue_knowledge'])
    for _ in range(2):
        result = _say(client, REQUEST)
        assert result['scene'] == 'frontier_gate'
        assert result['completed'] is not True
        assert 'nothing was written' in result['visible'].lower()
        assert 'no established object matches' in result['visible'].lower()
        assert 'no usable writing medium' in result['visible'].lower()
        assert storage.load_character() == before
        assert storage.load_scene('frontier_gate') == scene
        assert storage.load_session()['clue_knowledge'] == knowledge
    # Read the actual saved documents, not conversation text.
    assert storage.load_character() == before
    assert 'notice_patrol_route' in storage.load_session()['clue_knowledge']

def test_hidden_content_request_cannot_create_copy_or_reveal(client):
    before = copy.deepcopy(storage.load_character())
    response = _say(client, 'I copy the noble agent hidden signal onto my sleeve with mud.')
    assert storage.load_character() == before
    assert response['completed'] is not True
    assert 'coordinated signal' not in response['visible'].lower()
    assert 'notice_patrol_route' not in response['clues']

def test_refused_copy_stays_absent_after_snapshot_restore_and_retry(client):
    _say(client, 'Read me the missing-patrol notice, not the tax lines.')
    before = copy.deepcopy(storage.load_character())
    _say(client, REQUEST)
    session = copy.deepcopy(storage.load_session())
    snapshot = storage.create_snapshot('T06 refused modification')
    assert storage.load_snapshot(snapshot['id']) is not None
    assert storage.load_character() == before
    assert storage.load_session()['clue_knowledge'] == session['clue_knowledge']
    again = _say(client, REQUEST)
    assert again['completed'] is not True
    assert storage.load_character() == before
    recalled = _say(client, 'What did that notice say about where the patrol was last seen?')
    assert 'northwest mud track' in recalled['visible']
    assert storage.load_character() == before

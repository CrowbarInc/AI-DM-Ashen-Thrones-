"""Definition policy controls, independently expected decisions and import safety."""
import copy
from dataclasses import asdict
import json
from pathlib import Path

import pytest

from game import pf1e_equipment_policy as p


def item(**metadata):
    value = p.padded_armor_definition()
    value['equipment_policy'].update(metadata)
    return value


def cases():
    valid = p.padded_armor_definition()
    # id, input, slot, ruleset, version, expected decision, expected reason
    rows = []

    def add(ident, value=valid, slot=p.SLOT, ruleset=p.RULESET_ID, version=1,
            decision='ELIGIBLE', reason='definition_slot_authorized_mechanics_unresolved'):
        rows.append((ident, copy.deepcopy(value), slot, ruleset, version, decision, reason))

    for ident in ('valid_category', 'valid_slot', 'explicit_definition', 'valid_ruleset',
                  'valid_version', 'repeated_identical', 'without_character', 'pf1e'):
        add(ident)
    add('serialized', json.loads(json.dumps(valid)))
    add('incompatible_slot', slot='main_hand', decision='INELIGIBLE', reason='category_slot_incompatible')
    add('unsupported_slot', slot='head', decision='UNSUPPORTED', reason='unsupported_slot')
    add('unsupported_category', item(category='heavy_armor'), decision='UNSUPPORTED', reason='unsupported_category')
    add('unknown_category', item(category='alien_plate'), decision='UNKNOWN', reason='unknown_category')
    missing = item(); del missing['equipment_policy']['category']
    add('missing_category', missing, decision='UNKNOWN', reason='missing_category')
    add('missing_slot', slot=None, decision='UNKNOWN', reason='missing_slot')
    add('missing_ruleset', ruleset=None, decision='UNKNOWN', reason='missing_ruleset')
    add('wrong_ruleset', ruleset='pf2e@1', decision='UNSUPPORTED', reason='unsupported_ruleset')
    add('missing_item', None, decision='UNKNOWN', reason='missing_item')
    add('malformed_item', [], decision='UNKNOWN', reason='malformed_item')
    add('name_only', {'name':'Padded armor shield sword'}, decision='UNKNOWN', reason='missing_equipment_metadata')
    add('attack_only', {'name':'Quarterstaff', 'attack_bonus':3, 'damage':'1d6'}, decision='UNKNOWN', reason='missing_equipment_metadata')
    add('inventory_without_category', {'id':'spellbook','name':'Spellbook','quantity':1,'usable':False}, decision='UNKNOWN', reason='missing_equipment_metadata')
    add('incompatible_inventory_category', item(category='shield', definition_id='test.shield'), decision='INELIGIBLE', reason='category_slot_incompatible')
    add('explicit_authorization')
    add('conflicting_category', item(category='shield'), decision='UNKNOWN', reason='conflicting_definition_category')
    for ident in ('unknown_contribution', 'potential_ac', 'potential_attack', 'potential_speed',
                  'no_calculation', 'imported_ambiguity', 'compatible_execution_blocked', 'mechanical_status'):
        add(ident)
    for ident, ruleset in [('rules_light','rules_light@1'), ('scifi','scifi@1'),
                          ('unknown_ruleset','mystery@1'), ('cross_ruleset_repeat','scifi@1')]:
        add(ident, ruleset=ruleset, decision='UNSUPPORTED', reason='unsupported_ruleset')
    add('version_mismatch', version=2, decision='UNSUPPORTED', reason='policy_version_mismatch')
    add('neutral_inventory', dict(valid, instance_id='existing-neutral-id', revision=7))
    add('neutral_character')
    add('malformed_metadata', {'equipment_policy':[]}, decision='UNKNOWN', reason='malformed_equipment_metadata')
    add('malformed_category', item(category=[]), decision='UNKNOWN', reason='malformed_category')
    add('malformed_ruleset', ruleset={}, decision='UNKNOWN', reason='malformed_ruleset')
    add('malformed_slot', slot=[], decision='UNKNOWN', reason='malformed_slot')
    add('bool_version', version=True, decision='UNKNOWN', reason='malformed_policy_version')
    add('item_version', item(policy_version=2), decision='UNSUPPORTED', reason='item_policy_version_mismatch')
    add('item_ruleset', item(ruleset='scifi@1'), decision='UNSUPPORTED', reason='item_ruleset_mismatch')
    add('uncatalogued_definition', item(definition_id='pf1e.unknown'), decision='UNSUPPORTED', reason='unsupported_item_definition')
    add('untrusted_no_effect', item(mechanical_consequence='NONE_ESTABLISHED'), decision='UNKNOWN', reason='unrecognized_equipment_metadata')
    add('untrusted_known_effect', item(mechanical_consequence='KNOWN'), decision='UNKNOWN', reason='unrecognized_equipment_metadata')
    add('malformed_definition_id', item(definition_id=[]), decision='UNKNOWN', reason='malformed_definition_id')
    add('medium_armor', item(category='medium_armor'), decision='UNSUPPORTED', reason='unsupported_category')
    add('weapon_body_exclusion', item(category='simple_melee_weapon',definition_id='test.weapon'), decision='INELIGIBLE', reason='category_slot_incompatible')
    return rows


def evaluate_case(row):
    ident, value, slot, ruleset, version, decision, reason = row
    before = copy.deepcopy(value)
    result = p.evaluate_equipment_eligibility(value, slot, ruleset, policy_version=version)
    checks = {'decision': result.decision == decision, 'reason': result.reason == reason,
              'nonmutating': value == before, 'no_transition': not result.transition_authorized,
              'not_mechanically_complete': not result.mechanically_complete,
              'deterministic': result == p.evaluate_equipment_eligibility(value, slot, ruleset, policy_version=version)}
    expected_compatibility = ('COMPATIBLE' if decision == 'ELIGIBLE' or ident == 'uncatalogued_definition' else
                              'INCOMPATIBLE' if decision == 'INELIGIBLE' else
                              'UNSUPPORTED' if ident in ('unsupported_slot','unsupported_category','medium_armor') else 'UNKNOWN')
    checks['compatibility'] = result.compatibility == expected_compatibility
    unresolved = decision == 'ELIGIBLE' or ident == 'incompatible_slot'
    checks['mechanics'] = result.mechanical_consequence.value == ('UNRESOLVED' if unresolved else 'UNSUPPORTED')
    checks['missing_contributions_explicit'] = (
        result.mechanical_reason == 'imported_contribution_attribution_missing'
        and 'aggregate_contribution_attribution' in result.missing_contribution_data
    ) if unresolved else not result.missing_contribution_data
    checks['execution'] = result.execution_readiness == ('BLOCKED_MECHANICAL_RECONCILIATION' if decision == 'ELIGIBLE' else 'BLOCKED_POLICY')
    return {'id':ident,'input':value,'ruleset':ruleset,'category':result.category,'slot':slot,
            'requested_policy_version':version,'expected_decision':decision,'result':asdict(result),
            'assertions':checks,'passed':all(checks.values())}


@pytest.mark.parametrize('row', cases(), ids=lambda row:row[0])
def test_policy_matrix(row):
    evidence = evaluate_case(row)
    assert evidence['passed'], evidence


def test_existing_character_and_aggregates_are_unchanged():
    character = json.loads((Path(__file__).resolve().parents[1] / 'data/character.json').read_text())
    before = copy.deepcopy(character)
    for ruleset in ('pf1e@1','rules_light@1','scifi@1','unknown@1'):
        for row in character['inventory'] + character['attacks']:
            assert p.evaluate_equipment_eligibility(row, p.SLOT, ruleset).decision != 'ELIGIBLE'
        for _ in range(3):
            assert not p.evaluate_equipment_eligibility(p.padded_armor_definition(),p.SLOT,ruleset).transition_authorized
    assert character == before
    assert all(character[k] == before[k] for k in ('ac','speed','attacks'))


def test_imported_aggregates_not_decomposed_or_reapplied(tmp_path):
    from game.importers.pf_json_importer import import_sheet
    source = {'Name':'Policy test', 'AC':17,'ACTouch':12,'ACFlat':15,'Speed':30,
              'ArmorName':'Padded armor','Weapon1':'Quarterstaff','Weapon1AB':'+3','Weapon1Damage':'1d6+1'}
    path = tmp_path / 'sheet.json'; path.write_text(json.dumps(source))
    character = import_sheet(path); before = copy.deepcopy(character)
    assert character['ac']['normal'] == 17 and character['speed'] == 30
    assert character['attacks'][0]['attack_bonus'] == 3
    assert p.evaluate_equipment_eligibility(character['inventory'][0],p.SLOT,p.RULESET_ID).decision == 'UNKNOWN'
    for _ in range(5):
        result = p.evaluate_equipment_eligibility(p.padded_armor_definition(),p.SLOT,p.RULESET_ID)
        assert result.mechanical_consequence == p.MechanicalConsequence.UNRESOLVED
        assert not result.mechanically_complete and not result.transition_authorized
    assert character == before  # no double bonus and no removal of aggregate contributions


def test_definition_is_detached_and_name_has_no_authority():
    first = p.padded_armor_definition(); first['equipment_policy']['category'] = 'shield'
    second = p.padded_armor_definition(); second['name'] = 'Anything at all'
    assert p.evaluate_equipment_eligibility(second,p.SLOT,p.RULESET_ID).decision == 'ELIGIBLE'
    assert p.evaluate_equipment_eligibility(first,p.SLOT,p.RULESET_ID).decision == 'UNKNOWN'

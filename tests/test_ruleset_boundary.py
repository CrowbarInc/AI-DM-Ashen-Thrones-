"""Deterministic ruleset-boundary contract. Not a gameplay or plugin test."""
import ast
import copy
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

from game import pf1e_equipment_policy as pf
from game import ruleset_registry as registry
from game.ruleset_contract import PolicyEvaluation, dispatch, evaluation_to_dict, freeze

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'game' / 'ruleset_contract.py'
REGISTRY = ROOT / 'game' / 'ruleset_registry.py'
CAPABILITY = 'equipment_policy'


def padded():
    return pf.padded_armor_definition()


def shield():
    value = padded()
    value['equipment_policy'] = dict(value['equipment_policy'], category='shield', definition_id='test.shield')
    return value


def request_for(item, slot='body_armor', **extra):
    payload = {'item': item, 'slot': slot}
    payload.update(extra)
    return payload


class HypotheticalLayerRuleset:
    """Test-only second authority. It is not registered and not a game system."""

    ruleset_id = 'example_layered_cloth'
    version = '1'
    implementation = 'test_only.example_layered_cloth'
    supported_capabilities = frozenset({CAPABILITY})

    def supports(self, capability):
        return capability in self.supported_capabilities

    def capability_disposition(self, capability):
        return 'supported' if self.supports(capability) else 'unknown'

    def evaluate_policy(self, capability, request, context):
        del request, context
        return PolicyEvaluation(
            'supported', 'outer_layer_fits', self.ruleset_id, self.version, capability,
            self.implementation, 'supported',
            freeze({'fit': 'outer_layer', 'execution_readiness': 'NOT_A_GAME_SYSTEM',
                    'mechanics_implemented': False}))


def imported_modules(path: Path):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
    return found


def evidence(ident, group, ruleset_id, version, capability, raw_input, implementation, result, checks,
             status=None):
    return {
        'id': ident, 'group': group, 'ruleset_id': ruleset_id, 'ruleset_version': version,
        'capability': capability, 'input': raw_input, 'selected_implementation': implementation,
        'structured_result': result, 'status': status,
        'unsupported_or_unknown': status in ('unsupported', 'unknown', 'invalid'),
        'state_mutation_delta': {}, 'assertions': checks, 'passed': all(checks.values()),
    }


def _eval(ruleset_id, version, capability, request, context):
    before_request = copy.deepcopy(request) if isinstance(request, dict) else request
    before_context = copy.deepcopy(context) if isinstance(context, dict) else context
    result = registry.evaluate_policy(ruleset_id, version, capability, request, context)
    unchanged = request == before_request and context == before_context
    return result, unchanged


def matrix():
    character = {'id': 'sample', 'ac': 14, 'inventory': [{'name': 'Spellbook'}]}
    context = {'character': character}
    valid = request_for(padded())
    rows = []

    def add(ident, group, ruleset_id, version, capability, raw_input, implementation, result, checks, status=None):
        checks = dict(checks)
        checks['state_mutation_none'] = getattr(result, 'state_mutation', 'none') == 'none' if result is not None else True
        rows.append(evidence(ident, group, ruleset_id, version, capability, raw_input, implementation,
                             evaluation_to_dict(result) if isinstance(result, PolicyEvaluation) else result,
                             checks, status if status is not None else getattr(result, 'status', None)))

    selected = registry.get_ruleset('pf1e', '1')
    repeated = registry.get_ruleset('pf1e', '1')
    add('01_known_ruleset', 'A', 'pf1e', '1', None, {'ruleset_id': 'pf1e', 'version': '1'},
        selected.implementation, None, {
            'selected': selected.status == 'selected',
            'canonical': selected.canonical == 'pf1e@1',
            'authority': selected.authority.implementation == 'game.pf1e_equipment_policy',
        }, selected.status)
    add('02_known_version', 'A', 'pf1e', '1', None, {'version': selected.version},
        selected.implementation, None, {
            'version': selected.version == '1',
            'token': registry.parse_canonical('pf1e@1') == selected,
        }, 'selected')
    unknown = registry.get_ruleset('mystery', '1')
    add('03_unknown_ruleset', 'A', 'mystery', '1', None, {'ruleset_id': 'mystery'},
        unknown.implementation, None, {
            'status': unknown.status == 'unknown', 'reason': unknown.reason == 'unknown_ruleset',
            'no_authority': unknown.authority is None,
        }, unknown.status)
    bad_version = registry.get_ruleset('pf1e', '2')
    add('04_unsupported_version', 'A', 'pf1e', '2', None, {'version': '2'},
        bad_version.implementation, None, {
            'status': bad_version.status == 'unsupported',
            'reason': bad_version.reason == 'unsupported_version',
            'no_authority': bad_version.authority is None,
        }, bad_version.status)
    missing = registry.get_ruleset(None, '1')
    add('05_missing_identifier', 'A', None, '1', None, {'ruleset_id': None},
        None, None, {'status': missing.status == 'unknown', 'reason': missing.reason == 'missing_identifier'},
        missing.status)
    malformed = registry.get_ruleset('PF1E', '1')
    add('06_malformed_identifier', 'A', 'PF1E', '1', None, {'ruleset_id': 'PF1E'},
        None, None, {'status': malformed.status == 'invalid', 'reason': malformed.reason == 'malformed_identifier'},
        malformed.status)
    add('07_repeated_lookup', 'A', 'pf1e', '1', None, {'repeat': 2},
        selected.implementation, None, {'equal': selected == repeated, 'same_authority': selected.authority is repeated.authority},
        'selected')
    immutable = False
    try:
        registry.REGISTERED[('pf1e', '1')] = 'other'
    except TypeError:
        immutable = True
    add('08_registry_immutability', 'A', 'pf1e', '1', None, {'operation': 'item_assignment'},
        'closed_registry', None, {
            'immutable': immutable, 'no_register': not hasattr(registry, 'register'),
            'no_install': not hasattr(registry, 'install'),
            'no_defaults': all(param.default is inspect.Parameter.empty
                               for param in inspect.signature(registry.get_ruleset).parameters.values()),
        }, 'selected')

    discovered = registry.discover_capability('pf1e', '1', CAPABILITY)
    add('09_supported_capability', 'B', 'pf1e', '1', CAPABILITY, {'capability': CAPABILITY},
        discovered.implementation, None, {
            'status': discovered.status == 'supported', 'supports': selected.authority.supports(CAPABILITY),
        }, discovered.status)
    unsupported_cap = registry.discover_capability('pf1e', '1', 'character_statistics')
    add('10_unsupported_capability', 'B', 'pf1e', '1', 'character_statistics', {'capability': 'character_statistics'},
        unsupported_cap.implementation, None, {
            'status': unsupported_cap.status == 'unsupported',
            'not_supported': selected.authority.supports('character_statistics') is False,
        }, unsupported_cap.status)
    light = registry.discover_capability('rules_light', '1', CAPABILITY)
    add('11_rules_light_capability', 'B', 'rules_light', '1', CAPABILITY, {'capability': CAPABILITY},
        light.implementation, None, {
            'status': light.status == 'unsupported',
            'implementation': light.implementation == 'identity_only:rules_light@1',
        }, light.status)
    scifi = registry.discover_capability('scifi', '1', CAPABILITY)
    add('12_scifi_capability', 'B', 'scifi', '1', CAPABILITY, {'capability': CAPABILITY},
        scifi.implementation, None, {
            'status': scifi.status == 'unsupported',
            'implementation': scifi.implementation == 'identity_only:scifi@1',
        }, scifi.status)
    unknown_cap = registry.discover_capability('pf1e', '1', 'phase_dance')
    add('13_unknown_capability', 'B', 'pf1e', '1', 'phase_dance', {'capability': 'phase_dance'},
        unknown_cap.implementation, None, {'status': unknown_cap.status == 'unknown',
                                            'reason': unknown_cap.reason == 'unknown_capability'}, unknown_cap.status)
    missing_cap = registry.discover_capability('pf1e', '1', None)
    add('14_missing_capability', 'B', 'pf1e', '1', None, {'capability': None},
        missing_cap.implementation, None, {'status': missing_cap.status == 'unknown',
                                           'reason': missing_cap.reason == 'missing_capability'}, missing_cap.status)
    again = registry.discover_capability('pf1e', '1', CAPABILITY)
    add('15_repeated_discovery', 'B', 'pf1e', '1', CAPABILITY, {'repeat': 2},
        discovered.implementation, None, {'equal': discovered == again}, discovered.status)
    declared = tuple(sorted(selected.authority.supported_capabilities))
    add('16_declaration_consistency', 'B', 'pf1e', '1', CAPABILITY, {'declared': declared},
        selected.implementation, None, {
            'declared_match': all(selected.authority.supports(name) for name in declared),
            'discovery_match': all(registry.discover_capability('pf1e', '1', name).status == 'supported' for name in declared),
            'unsupported_match': all(registry.discover_capability('pf1e', '1', name).status == 'unsupported'
                                     for name in selected.authority.recognized_unsupported),
        }, 'supported')

    delegated, unchanged = _eval('pf1e', '1', CAPABILITY, valid, context)
    payload = dict(delegated.ruleset_result)
    add('17_valid_definition', 'C', 'pf1e', '1', CAPABILITY, {'definition_id': payload.get('definition_id')},
        delegated.implementation, delegated, {
            'definition': payload.get('definition_id') == pf.PADDED_ARMOR_ID,
            'unchanged': unchanged, 'implementation': delegated.implementation == 'game.pf1e_equipment_policy',
        })
    add('18_valid_slot', 'C', 'pf1e', '1', CAPABILITY, {'slot': payload.get('slot')},
        delegated.implementation, delegated, {'slot_recognized': payload.get('slot_recognized') is True,
                                              'slot': payload.get('slot') == pf.SLOT})
    add('19_eligible_item', 'C', 'pf1e', '1', CAPABILITY, {'decision': payload.get('decision')},
        delegated.implementation, delegated, {'decision': payload.get('decision') == 'ELIGIBLE',
                                              'authorized': payload.get('item_authorized') is True})
    incompatible, _same = _eval('pf1e', '1', CAPABILITY, request_for(padded(), 'main_hand'), context)
    add('20_incompatible_slot', 'C', 'pf1e', '1', CAPABILITY, {'slot': 'main_hand'},
        incompatible.implementation, incompatible, {
            'decision': incompatible.ruleset_result['decision'] == 'INELIGIBLE',
            'compatibility': incompatible.ruleset_result['compatibility'] == 'INCOMPATIBLE',
            'blocked': incompatible.ruleset_result['transition_authorized'] is False,
        })
    alien = padded(); alien['equipment_policy'] = dict(alien['equipment_policy'], category='alien_plate')
    unknown_category, _same = _eval('pf1e', '1', CAPABILITY, request_for(alien), context)
    add('21_unknown_category', 'C', 'pf1e', '1', CAPABILITY, {'category': 'alien_plate'},
        unknown_category.implementation, unknown_category, {
            'status': unknown_category.status == 'unknown',
            'reason': unknown_category.reason == 'unknown_category',
        })
    nameless = {'name': 'Padded armor'}
    missing_meta, _same = _eval('pf1e', '1', CAPABILITY, request_for(nameless), context)
    add('22_missing_metadata', 'C', 'pf1e', '1', CAPABILITY, {'item': 'name_only'},
        missing_meta.implementation, missing_meta, {
            'status': missing_meta.status == 'unknown',
            'reason': missing_meta.reason == 'missing_equipment_metadata',
        })
    add('23_mechanical_uncertainty', 'C', 'pf1e', '1', CAPABILITY, {'consequence': payload.get('mechanical_consequence')},
        delegated.implementation, delegated, {
            'consequence': payload.get('mechanical_consequence') == 'UNRESOLVED',
            'not_success': delegated.status == 'mechanically_unresolved',
        })
    add('24_execution_blocked', 'C', 'pf1e', '1', CAPABILITY, {'readiness': payload.get('execution_readiness')},
        delegated.implementation, delegated, {
            'readiness': payload.get('execution_readiness') == 'BLOCKED_MECHANICAL_RECONCILIATION',
            'complete': payload.get('mechanically_complete') is False,
            'transition': payload.get('transition_authorized') is False,
        })
    add('25_policy_version', 'C', 'pf1e', '1', CAPABILITY, {'policy_version': payload.get('policy_version')},
        delegated.implementation, delegated, {
            'policy_version': payload.get('policy_version') == 1,
            'ruleset_version': delegated.ruleset_version == '1',
        })
    add('26_ruleset_result_preserved', 'C', 'pf1e', '1', CAPABILITY, {'policy_id': payload.get('policy_id')},
        delegated.implementation, delegated, {
            'policy_id': payload.get('policy_id') == pf.POLICY_ID,
            'ruleset': payload.get('ruleset') == pf.RULESET_ID,
            'missing_reported': 'aggregate_contribution_attribution' in payload.get('missing_contribution_data', ()),
        })

    light_eval, _same = _eval('rules_light', '1', CAPABILITY, valid, context)
    scifi_eval, _same = _eval('scifi', '1', CAPABILITY, valid, context)
    mystery_eval, _same = _eval('mystery', '1', CAPABILITY, valid, context)
    add('27_policy_under_pf1e', 'D', 'pf1e', '1', CAPABILITY, {'ruleset': 'pf1e@1'},
        delegated.implementation, delegated, {'implementation': delegated.implementation == 'game.pf1e_equipment_policy',
                                              'delegated': delegated.capability_support == 'supported'})
    add('28_policy_under_rules_light', 'D', 'rules_light', '1', CAPABILITY, {'ruleset': 'rules_light@1'},
        light_eval.implementation, light_eval, {
            'status': light_eval.status == 'unsupported',
            'implementation': light_eval.implementation == 'identity_only:rules_light@1',
            'no_pf_decision': 'decision' not in light_eval.ruleset_result,
        })
    add('29_policy_under_scifi', 'D', 'scifi', '1', CAPABILITY, {'ruleset': 'scifi@1'},
        scifi_eval.implementation, scifi_eval, {
            'status': scifi_eval.status == 'unsupported',
            'implementation': scifi_eval.implementation == 'identity_only:scifi@1',
            'no_pf_decision': 'decision' not in scifi_eval.ruleset_result,
        })
    add('30_policy_under_unknown', 'D', 'mystery', '1', CAPABILITY, {'ruleset': 'mystery@1'},
        mystery_eval.implementation, mystery_eval, {
            'status': mystery_eval.status == 'unknown', 'implementation': mystery_eval.implementation is None,
        })
    omitted = registry.get_ruleset(None, None)
    add('31_no_implicit_fallback', 'D', None, None, CAPABILITY, {'ruleset_id': None, 'version': None},
        omitted.implementation, mystery_eval, {
            'not_selected': omitted.status == 'unknown' and omitted.authority is None,
            'not_pf': omitted.implementation != 'game.pf1e_equipment_policy',
            'no_default_parameters': all(param.default is inspect.Parameter.empty
                                         for param in inspect.signature(registry.get_ruleset).parameters.values()),
        })
    first, _same = _eval('pf1e', '1', CAPABILITY, valid, context)
    second, _same = _eval('pf1e', '1', CAPABILITY, valid, context)
    mutable = True
    try:
        first.ruleset_result['decision'] = 'CHANGED'
    except TypeError:
        mutable = False
    add('32_no_shared_mutable_state', 'D', 'pf1e', '1', CAPABILITY, {'calls': 2},
        first.implementation, first, {
            'equal': evaluation_to_dict(first) == evaluation_to_dict(second),
            'distinct': first.ruleset_result is not second.ruleset_result,
            'immutable_payload': mutable is False,
        })
    repeated_light, _same = _eval('rules_light', '1', CAPABILITY, valid, context)
    repeated_pf, _same = _eval('pf1e', '1', CAPABILITY, valid, context)
    add('33_repeated_cross_ruleset', 'D', 'pf1e', '1', CAPABILITY, {'sequence': ['pf1e', 'rules_light', 'pf1e']},
        repeated_pf.implementation, repeated_pf, {
            'pf_stable': evaluation_to_dict(repeated_pf) == evaluation_to_dict(delegated),
            'light_stable': evaluation_to_dict(repeated_light) == evaluation_to_dict(light_eval),
            'light_not_pf': repeated_light.implementation != repeated_pf.implementation,
        })
    isolated, _same = _eval('pf1e', '9', CAPABILITY, valid, context)
    add('34_unsupported_version_isolation', 'D', 'pf1e', '9', CAPABILITY, {'version': '9'},
        isolated.implementation, isolated, {
            'status': isolated.status == 'unsupported', 'reason': isolated.reason == 'unsupported_version',
            'no_payload': dict(isolated.ruleset_result) == {},
        })

    resolved, _same = _eval('pf1e', '1', CAPABILITY, request_for(shield()), context)
    add('35_supported', 'E', 'pf1e', '1', CAPABILITY, {'category': 'shield'},
        resolved.implementation, resolved, {
            'status': resolved.status == 'supported',
            'decision': resolved.ruleset_result['decision'] == 'INELIGIBLE',
            'still_blocked': resolved.ruleset_result['execution_readiness'] == 'BLOCKED_POLICY',
        })
    head, _same = _eval('pf1e', '1', CAPABILITY, request_for(padded(), 'head'), context)
    add('36_unsupported', 'E', 'pf1e', '1', CAPABILITY, {'slot': 'head'},
        head.implementation, head, {'status': head.status == 'unsupported', 'reason': head.reason == 'unsupported_slot'})
    add('37_unknown', 'E', 'pf1e', '1', CAPABILITY, {'category': 'alien_plate'},
        unknown_category.implementation, unknown_category, {'status': unknown_category.status == 'unknown'})
    malformed_item, _same = _eval('pf1e', '1', CAPABILITY, request_for([]), context)
    add('38_invalid', 'E', 'pf1e', '1', CAPABILITY, {'item': []},
        malformed_item.implementation, malformed_item, {
            'status': malformed_item.status == 'invalid', 'reason': malformed_item.reason == 'malformed_item',
        })
    add('39_mechanically_unresolved', 'E', 'pf1e', '1', CAPABILITY, {'definition': pf.PADDED_ARMOR_ID},
        delegated.implementation, delegated, {'status': delegated.status == 'mechanically_unresolved'})
    missing_context, unchanged_context = _eval('pf1e', '1', CAPABILITY, valid, None)
    add('40_missing_context', 'E', 'pf1e', '1', CAPABILITY, {'context': None},
        missing_context.implementation, missing_context, {
            'status': missing_context.status == 'unknown', 'reason': missing_context.reason == 'missing_context',
            'request_unchanged': unchanged_context,
        })
    malformed_request, _same = _eval('pf1e', '1', CAPABILITY, ['not', 'a', 'mapping'], context)
    add('41_malformed_request', 'E', 'pf1e', '1', CAPABILITY, {'request': 'list'},
        malformed_request.implementation, malformed_request, {
            'status': malformed_request.status == 'invalid', 'reason': malformed_request.reason == 'malformed_request',
        })
    plain = evaluation_to_dict(delegated)
    text = json.dumps(plain, sort_keys=True)
    add('42_stable_serialization', 'E', 'pf1e', '1', CAPABILITY, {'sort_keys': True},
        delegated.implementation, delegated, {
            'stable': text == json.dumps(json.loads(text), sort_keys=True),
            'status_preserved': json.loads(text)['status'] == 'mechanically_unresolved',
        })

    contract_imports = imported_modules(CONTRACT)
    registry_imports = imported_modules(REGISTRY)
    contract_source = CONTRACT.read_text(encoding='utf-8').lower()
    forbidden_terms = ('pf1e', 'pathfinder', 'light_armor', 'body_armor', 'main_hand', 'padded',
                       'armor_class', 'dexterity', 'attack_bonus', 'spell_failure', 'base_attack')
    add('43_contract_imports', 'F', None, None, None, {'imports': contract_imports},
        None, None, {
            'no_ruleset_import': all(not name.startswith('game.') for name in contract_imports),
            'stdlib_only': set(contract_imports) <= {'__future__', 'dataclasses', 'enum', 'types', 're', 'typing'},
        }, 'supported')
    add('44_no_slot_names', 'F', None, None, None, {'forbidden': forbidden_terms[:4]},
        None, None, {'clean': all(term not in contract_source for term in forbidden_terms[:4])}, 'supported')
    add('45_no_statistics', 'F', None, None, None, {'forbidden': forbidden_terms[4:]},
        None, None, {'clean': all(term not in contract_source for term in forbidden_terms)}, 'supported')
    untouched = ('game.storage', 'game.api', 'game.publication_contract', 'game.conversational_orchestration')
    add('46_persistence_unchanged', 'F', None, None, None, {'forbidden_imports': untouched},
        None, None, {'not_imported': all(name not in contract_imports + registry_imports for name in untouched)},
        'supported')
    add('47_inventory_unchanged', 'F', None, None, None, {'module': 'game.object_instances'},
        None, None, {'not_imported': 'game.object_instances' not in contract_imports + registry_imports}, 'supported')
    add('48_admission_unchanged', 'F', None, None, None, {'module': 'game.conversational_orchestration'},
        None, None, {'not_imported': 'game.conversational_orchestration' not in contract_imports + registry_imports},
        'supported')
    add('49_publication_unchanged', 'F', None, None, None, {'module': 'game.publication_contract'},
        None, None, {'not_imported': 'game.publication_contract' not in contract_imports + registry_imports},
        'supported')
    watched = copy.deepcopy(character)
    _eval('pf1e', '1', CAPABILITY, valid, {'character': watched})
    add('50_no_character_mutation', 'F', 'pf1e', '1', CAPABILITY, {'character_id': 'sample'},
        delegated.implementation, delegated, {'character_unchanged': watched == character,
                                              'mutation_flag': delegated.state_mutation == 'none'})

    layer = HypotheticalLayerRuleset()
    hypothetical = dispatch(layer, CAPABILITY, valid, {})
    add('51_hypothetical_second_ruleset', 'H', layer.ruleset_id, layer.version, CAPABILITY,
        {'note': 'test_only'}, hypothetical.implementation, hypothetical, {
            'fit': hypothetical.ruleset_result['fit'] == 'outer_layer',
            'not_registered': ('example_layered_cloth', '1') not in registry.REGISTERED,
            'not_pf': hypothetical.implementation != 'game.pf1e_equipment_policy',
            'not_executable': hypothetical.ruleset_result['execution_readiness'] == 'NOT_A_GAME_SYSTEM',
        })
    code = (
        'import sys\n'
        'from game.ruleset_registry import evaluate_policy\n'
        'result = evaluate_policy("rules_light", "1", "equipment_policy", {"item": {}, "slot": "x"}, {})\n'
        'assert "game.pf1e_equipment_policy" not in sys.modules, sorted(sys.modules)\n'
        'assert result.status == "unsupported"\n'
        'assert result.implementation == "identity_only:rules_light@1"\n'
    )
    completed = subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True, text=True)
    add('52_rules_light_does_not_load_pf_module', 'D', 'rules_light', '1', CAPABILITY, {'process': 'fresh'},
        'identity_only:rules_light@1', None, {
            'exit': completed.returncode == 0, 'stderr': completed.stderr == '',
        }, 'unsupported')
    policy_mismatch, _same = _eval('pf1e', '1', CAPABILITY, request_for(padded(), policy_version=2), context)
    add('53_policy_version_is_not_ruleset_version', 'C', 'pf1e', '1', CAPABILITY, {'policy_version': 2},
        policy_mismatch.implementation, policy_mismatch, {
            'reached_pf': policy_mismatch.implementation == 'game.pf1e_equipment_policy',
            'status': policy_mismatch.status == 'unsupported',
            'reason': policy_mismatch.reason == 'policy_version_mismatch',
        })
    return rows


@pytest.mark.parametrize('row', matrix(), ids=lambda row: row['id'])
def test_contract_matrix(row):
    assert row['passed'], row


def test_matrix_covers_required_groups():
    rows = matrix()
    assert len(rows) >= 50
    assert {row['group'] for row in rows} >= {'A', 'B', 'C', 'D', 'E', 'F'}
    assert all(row['passed'] for row in rows)

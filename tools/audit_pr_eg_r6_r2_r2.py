"""Capture predecessor contracts/failures before any production modification."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'artifacts/pr_eg_r6_r2_r2'


def main():
    old = ROOT / 'artifacts/pr_eg_r6_r2_r1'
    rows = [json.loads(l) for l in (old / 'final/live_turns.jsonl').read_text().splitlines()]
    targets = {'classification': ('continuity_1', 2), 'referent_target': ('continuity_2', 5),
               'object_replacement': ('continuity_0', 7), 'multi_role': ('continuity_1', 10),
               'follow_up': ('continuity_1', 6), 'false_clarification': ('continuity_2', 8),
               'partial_overstatement': ('continuity_0', 9)}
    result = {}
    for kind, key in targets.items():
        r = next(r for r in rows if (r['conversation'], r['turn']) == key)
        p = r['plan']
        result[kind] = {'source': 'preserved predecessor fresh-provider evidence, not a new reproduction',
            'player': r['player'], 'prior': r['prior_referents'], 'provider_proposal': p.get('provider_proposal'),
            'operation': p.get('referent_operation'), 'target': p.get('bound_referent_id'),
            'validation': p.get('reason'), 'result': p, 'speech': r['text']}
    from tests.test_pr_eg_r6_r2_r1_referents import seeded, correction, resolve
    import os
    os.environ['ASHEN_UNIFIED_SEMANTIC_PLANNING'] = '1'
    session, record = seeded()
    p = correction(record); p['referent_operation']['operation'] = 'unsupported'
    result['malformed_operation'] = {'source': 'new pre-edit controlled reproduction', 'player': 'I meant the night ledger.',
        'prior': session, 'provider_proposal': p, 'result': resolve(session, p, text='I meant the night ledger.')}
    (OUT / 'preimplementation_failures.json').write_text(json.dumps(result, indent=2))
    metrics = json.loads((old / 'quality_metrics.json').read_text())
    (OUT / 'verified_predecessor_metrics.json').write_text(json.dumps(metrics, indent=2))
    sources = OUT / 'baseline_sources/game'
    inventory = []
    for path in sources.glob('*.py'):
        text = path.read_text(encoding='utf-8-sig')
        inventory.append({'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'symbols': [{'line': n, 'definition': line} for n, line in enumerate(text.splitlines(), 1)
                        if line.startswith('def ')]})
    (OUT / 'preimplementation_source_inventory.json').write_text(json.dumps(inventory, indent=2))
    audit = '''# Preimplementation contract audit

This record was generated before changing the three existing production contracts.

* Intent: `unified_semantic_planning.validate_plan_schema` accepts four conversational acts. Schema and missing-argument enums are binary. `is_migrated_information_turn` uses an existing lexical scope gate; this campaign must not expand its phrase tables.
* Binding: `conversational_referents.bind` checks conversation IDs, but silently substitutes active focus when an older target lacks a literal subject/object. This loses provider intent and named-role distinctions.
* Transformations: deltas preserve eight fields, but only predicate/subject/object changes require current evidence. Qualifier changes can escape the witness check. `reject_interpretation` accepts an arbitrary complete field delta. Multi-role replacement has no representation.
* Correspondence: `semantic_correspondence.coverage` checks binary arguments, predicate, negation, qualifiers and epistemics. It cannot preserve speaker, recipient, topic and message independently. Literal indefinite arguments can be overstated as identities. Missing time/space becomes nonanswer even if some information was supplied.
* Failure handling: parse/schema errors and invalid targets all become player clarifications. Genuine ambiguity and model failure are indistinguishable to the player. There is no retry loop.
* Resolution: `authorize_information_turn` invokes one provider proposal, binds before source selection, then checks `dialogue_authority.npc_source_permitted` and returns a locked response. Only original permitted text supplies facts. Legacy fallbacks are fenced by locked planning ownership.
* Delivery: `immutable_valid_response` seals adopted speech; `conversational_continuity.record_delivered_exchange` commits the referent after seal verification. Corrections append revisions; they do not rewrite speech.
* Persistence: version 1 conversational_context question index is stored in the session integrity envelope, bounded to 24 records. Provider context contains six recent referents, no secret source texts. Existing arbitrary session keys survive storage roundtrips.

Exact pre-edit line numbers and source hashes: [source inventory](preimplementation_source_inventory.json). Complete source snapshots: [baseline sources](baseline_sources/game). Raw failures: [failure evidence](preimplementation_failures.json). Those links retain pre-edit semantics even when final source line numbers change.
'''
    (OUT / 'preimplementation_contract_audit.md').write_text(audit)
    print('Captured seven historical fresh-provider failures and one new controlled malformed-operation reproduction.')


if __name__ == '__main__':
    main()

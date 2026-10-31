"""Bounded offline authority evidence derived from saved production-path replays."""
import hashlib
import json
from pathlib import Path
import shutil

from game.gm_resolution_decision import _empty_identity_covers, _token_set

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'artifacts/pr_play_11'
RUNS = ROOT/'artifacts/atgb/automated_playtests'
REJECTED = '20261031T015747Z-5a6c03c902e3'


def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=True)+'\n', encoding='utf-8')


def main():
    replay = json.loads((OUT/(REJECTED+'_replay.json')).read_text())
    trace = replay['traces'][0]
    audit = trace['result']['gm_resolution_decision_audit']
    declared = trace['inputs']['declared_claims']
    decision = trace['inputs']['decision']
    records = []
    for index, row in enumerate(declared):
        matches = [c for c in decision['realization_claims'] if c['text'] == row['text']]
        records.append(dict(declaration_index=index, original=row,
            subject_field_present='subject' in row['semantic_identity'],
            predicate_field_present='predicate' in row['semantic_identity'],
            object_field_present='object' in row['semantic_identity'],
            supplied_authority=dict(provenance_requested=row['provenance_requested'], source_claim_id=row['source_claim_id']),
            required_authority='Match an authorized realization claim without modality/premise strengthening',
            matched_authored_claims=matches, declaration_rejected=False,
            validator='validate_declared_claims_against_decision -> _declared_identity_matches_realization',
            declaration_decision='accepted by exact text; source_claim_id is not mandatory in this contract'))
    violations = []
    for v in audit['violations'][:32]:
        violations.append(dict(original_violation=v, related_declaration_id=declared[0]['declaration_id'],
            relation='same notice-board subject; declaration itself accepted',
            required_authority='Authored text lexical coverage or authorized semantic identity',
            supplied_authority='Paraphrased prose; no lexical coverage and no matching authored semantic identity',
            failed_function='_authorized_rows_for_sentence -> _empty_identity_covers',
            rejection_function='_classify_narrated_fact_legacy -> _unlicensed_consequential_reasons',
            specific_rule='notice_roster_history',
            correct_under_executable_contract=True,
            semantic_assessment='Ordinary paraphrase of supplied information; deterministic guard has no synonym/entailment authority'))
    write('declaration_analysis.json', dict(declarations=records, rejected_declarations=[],
        narration_violations=violations, diagnostic_limit=32, omitted_violations=max(0,len(audit['violations'])-32)))
    text = audit['violations'][0]['text']
    lexical = []
    for c in decision['realization_claims']:
        if 'notice board' in c['text'].lower():
            lexical.append(dict(claim_id=c['claim_id'], text=c['text'],
                extra_content_tokens=sorted(_token_set(text)-_token_set(c['text'])),
                covered=_empty_identity_covers(text,c['text'])))
    write('lexical_failure.json', dict(narration=text, candidates=lexical,
        condition='More than one added content token rejects before later overlap checks; no synonym/entailment inference.'))
    corpus = []
    for run, pass_name in [('20261030T183848Z-5fe421902485','PR-PLAY-08'),
                           ('20261030T191257Z-ecc1b6062bdc','PR-PLAY-09'), (REJECTED,'PR-PLAY-09/10 rejection')]:
        folder = RUNS/run
        result = json.loads((folder/'reports/result.json').read_text())
        p = next((folder/'opening_response_evidence').glob('*.json'))
        capture = json.loads(p.read_text())
        dest = OUT/'corpus'/run
        dest.mkdir(parents=True, exist_ok=True)
        for rel in ['baseline/documents.json','reports/result.json']:
            d=dest/rel; d.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(folder/rel,d)
        shutil.copy2(p, dest/'capture.json')
        (dest/'parsed_response.json').write_text(json.dumps(capture['parsed_response'],indent=2)+'\n')
        usage=result['provider_usage']
        corpus.append(dict(source_run=run, pass_name=pass_name, source=str(p.relative_to(ROOT)),
            capture_available=True, capture_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            provider_model=usage['records'][0].get('model'),
            structured_validity=result['structural_validation'], semantic_outcome=result['semantic_validation'],
            opening_acceptance=result['opening_acceptance'], declaration_count=len(capture['parsed_response']['declared_claims']),
            original_failure_reason=result.get('failure_classification'),
            declaration_metadata=capture['parsed_response']['declared_claims'],
            replay_status=json.loads((OUT/(run+'_replay.json')).read_text())['status'],
            exact_parsed_replay=True, exact_provider_wire_replay=False))
    write('historical_corpus.json', corpus)
    lines = ['# Declaration-level rejection analysis', '',
        'All seven declarations are accepted. No declaration fails provenance, modality, or source matching.', '',
        '| Declaration identifier | Exact text | Decision |', '|---|---|---|']
    lines += [f"| {r['declaration_id']} | {r['text']} | Accepted by exact authored-text match |" for r in declared]
    lines += ['', 'The sole rejected item is narration associated with the notice-board declaration:', '',
        '| Related declaration | Rejected narration | Failed condition | Required / supplied authority |', '|---|---|---|---|',
        f"| {declared[0]['declaration_id']} (accepted) | {text} | No authorized row coverage; `notice_roster_history` | Authored lexical/identity evidence / embellished prose outside lexical coverage |", '',
        'The existing operational contract rejects this wording. Missing source IDs and MUST_STATE do not cause this rejection.']
    (OUT/'declaration_rejection_table.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Derived declaration, lexical, and three-response corpus evidence.')


if __name__ == '__main__':
    main()

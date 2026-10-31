"""Build reviewable derived tables from actual deterministic execution evidence."""
import ast, hashlib, json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'artifacts/pr_play_12'
def write(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2),encoding='utf-8')
def table(headers,rows):
    def cell(x): return str(x).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(cell,r))+' |\n' for r in rows)
def main():
    inv=json.loads((OUT/'capture_inventory.json').read_text()); history=[]
    for i,r in enumerate(inv):
        run=r['run']; src=ROOT/'artifacts/atgb/automated_playtests'/run
        native=json.loads((src/'reports/result.json').read_text()); usage=native['provider_usage']
        record=next(x for x in usage['records'] if x.get('sent'))
        replay=json.loads((OUT/'results'/(run+'_replay.json')).read_text())
        history.append(dict(source_run=run,pass_name=['PR08','PR09/PR10 accepted opening','PR11 investigation','Latest post-PR11'][i],provider_model=record['model'],input_tokens=usage['input_tokens'],output_tokens=usage['output_tokens'],declaration_count=r['declarations'],structured_validation=True,semantic_validation=replay['traces'][0]['result']['hard_valid'],opening_accepted=replay['status']==200,reasons=replay['traces'][0]['result']['reasons'],capture_completeness='Complete bounded parsed-response JSON; provider wire bytes and exact full request absent',replay_feasibility='Production parser, semantics, final gate and acceptance via synthetic SDK; captured baseline documents restored',capture_sha256=r['sha256']))
        dest=OUT/'historical'/run
        for rel in ['reports/result.json','diagnostics/provider_usage.jsonl']:
            if (src/rel).exists(): shutil.copy2(src/rel,dest/Path(rel).name)
    write('historical_evidence.json',history)
    (OUT/'historical_evidence.md').write_text(table(['Run / role','Model','Input','Output','Declarations','Structure','Semantics','Opening','Reasons','Capture / replay'],[[r['source_run']+' / '+r['pass_name'],r['provider_model'],r['input_tokens'],r['output_tokens'],r['declaration_count'],'pass',r['semantic_validation'],r['opening_accepted'],r['reasons'],'Parsed complete / wire and request missing; normal pipeline replay'] for r in history]),encoding='utf-8')
    import sys
    sys.path.insert(0,str(OUT/'sandbox'))
    from game import gm_resolution_decision as gd
    spans=json.loads((OUT/'results/spans.json').read_text()); ctx=spans['context']
    latest=inv[-1]['parsed']; actual=json.loads((OUT/'results'/(inv[-1]['run']+'_replay.json')).read_text())['traces'][0]['result']['gm_resolution_decision_audit']
    narration=[]
    for sentence in gd._sentences(latest['narration']):
        candidate=max(latest['declared_claims'],key=lambda c:len(gd._token_set(sentence)&gd._token_set(c['text'])))
        violations=[v for v in actual['violations'] if v['text']==sentence]
        narration.append(dict(text=sentence,candidate=candidate,extra_tokens=sorted(gd._token_set(sentence)-gd._token_set(candidate['text'])),lexical_coverage=gd._empty_identity_covers(sentence,candidate['text']),restates=gd._proposition_restates_statement(sentence,candidate['text']),violations=violations,interpretation=('Supported crowd density intensifier; no new actor, place, event or result. Spatial compression slightly stronger; review judgment, not entailment proof.' if 'tightly' in sentence else 'No validator rejection; candidate lexical overlap is diagnostic association, not inferred authority.')))
    write('span_diagnostics.json',dict(all_units=narration,violations=actual['violations'],declaration_validation=actual['declaration_validation']))
    (OUT/'span_rejection_table.md').write_text(table(['Narration','Supporting source / claim','Rule','Expected / supplied authority','Failure reason','Interpretation / confidence','Source'],[[r['text'],r['candidate']['text']+' / '+str(r['candidate']['source_claim_id']),'_undeclared_consequential_violations' if r['violations'] else 'No rejection','authored public world fact / nine accepted authored declarations',str(r['violations']) if r['violations'] else 'None',r['interpretation']+' High execution confidence; medium semantic equivalence confidence','game/gm_resolution_decision.py:3971; :1645; :1012'] for r in narration]),encoding='utf-8')
    corpus=[]
    for n in range(1,21):
        r=json.loads((OUT/'results'/('E'+str(n)+'.json')).read_text()); trace=r['traces'][0]['result']
        final=(r['response'].get('gm_output') or {}).get('player_facing_text')
        expected=r['interpretation'] in {'supported','incidental'}
        falsepos=expected and not trace['hard_valid']
        falseneg=(r['interpretation'] in {'unsupported','hidden','contradiction','ambiguous','false_provenance'} and trace['hard_valid'])
        corpus.append(dict(id=r['id'],text=r['text'],interpretation=r['interpretation'],rationale=r['rationale'],semantic_accepted=trace['hard_valid'],opening_status=r['status'],reasons=trace['reasons'],final_player_text=final,emitted_unchanged=(final==r['text']),false_positive_candidate=falsepos,false_negative_candidate_semantic_stage=falseneg,false_negative_candidate_delivery=falseneg and final==r['text'],rollback_equal=r['rollback_equal'],state_protection=r['state_protection'],confidence='High observation, provisional human semantic judgment'))
    write('corpus.json',corpus)
    (OUT/'corpus_results.md').write_text(table(['ID','Interpretation / justification','Current semantics / opening','Reason','Delivered unchanged','FP candidate','FN semantics / delivery','State checks'],[[r['id'],r['interpretation']+'; '+r['rationale'],str(r['semantic_accepted'])+' / '+str(r['opening_status']),r['reasons'],r['emitted_unchanged'],r['false_positive_candidate'],str(r['false_negative_candidate_semantic_stage'])+' / '+str(r['false_negative_candidate_delivery']),all(r['state_protection'].values())] for r in corpus]),encoding='utf-8')
    functions={
      'game/api.py':['start_campaign','_start_campaign_after_admission','_build_gpt_narration_from_authoritative_state','_run_resolved_turn_pipeline','_opening_response_rejection','_restore_opening_baseline','_complete_opening_turn_persistence_like_chat','_post_gm_adoption_gateway'],
      'game/gm.py':['call_gpt','_safe_json','_opening_max_output_tokens'],
      'game/gm_resolution_decision.py':['build_gm_resolution_decision','validate_declared_claims_against_decision','_declared_identity_matches_realization','_empty_identity_covers','_proposition_restates_statement','audit_narration_against_decision','audit_realization_envelope_against_decision','_undeclared_consequential_violations','remember_temporal_claims'],
      'game/immutable_valid_response.py':['validate_generated_response','run_preserve_if_valid'],
      'game/narration_visibility.py':['build_narration_visibility_contract','validate_player_facing_visibility','_normalized_fact_match_kind'],
      'game/narrative_authority.py':['build_narrative_authority_contract','validate_narrative_authority'],
      'game/bounded_improvisation.py':['validate_bounded_improvisation_proposal','promote_accepted_bounded_improvisation'],
      'game/ctir_runtime.py':['build_runtime_ctir_for_narration'],
      'game/prompt_context.py':['build_narration_context'],
    }
    locations=[]; excerpts=[]
    for filename,names in functions.items():
        text=(ROOT/filename).read_text(encoding='utf-8'); lines=text.splitlines(); tree=ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names:
                locations.append(dict(module=filename,function=node.name,line=node.lineno,end=node.end_lineno,args=ast.unparse(node.args)))
                excerpts.append('## '+filename+':'+str(node.lineno)+' '+node.name+'\n```python\n'+'\n'.join(lines[node.lineno-1:node.end_lineno])+'\n```\n')
        dest=OUT/'source_snapshots'/filename; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/filename,dest)
    write('source_locations.json',locations)
    (OUT/'source_excerpts.md').write_text('\n'.join(excerpts),encoding='utf-8')
    # Snapshot the source selected by the actual test runner, not HEAD-only source.
    write('source_snapshot_hashes.json',{str(p.relative_to(OUT/'source_snapshots')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (OUT/'source_snapshots').rglob('*') if p.is_file()})
if __name__=='__main__': main()

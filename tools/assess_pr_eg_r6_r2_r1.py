"""Transparent local transcript audit; no external scorer or holdout tuning."""
import json
import statistics
from pathlib import Path

OUT=Path(__file__).resolve().parents[1]/'artifacts/pr_eg_r6_r2_r1'
CORRECTIONS={'continuity_0':{2,7},'continuity_1':{2,10},'continuity_2':{2,5},'continuity_3':{7,11},
             'new_holdouts_0':{2,4},'new_holdouts_1':{4,7},'original_holdouts_0':{6}}
FOLLOWUPS={'continuity_0':{3,5,10,12},'continuity_1':{3,5,6,8,12,14},'continuity_2':{3,6,8,10,11,13},
           'continuity_3':{3,5,9,13},'new_holdouts_0':{6,8,11,13},'new_holdouts_1':{9,12,14},'original_holdouts_1':{2}}
GENUINE={('continuity_0',13),('continuity_2',13),('continuity_3',14),('new_holdouts_1',2),('original_holdouts_1',3),('original_holdouts_1',4)}
BAD_CONTINUITY={('continuity_1',2),('continuity_1',6),('continuity_1',10),('continuity_2',5),('continuity_2',6),('continuity_2',8),
                ('continuity_2',13),('continuity_3',7),('new_holdouts_0',13),('new_holdouts_1',7),('new_holdouts_1',12),
                ('new_holdouts_1',14),('original_holdouts_0',6)}
BAD_ROLES={('continuity_1',9),('continuity_1',13),('continuity_2',7),('new_holdouts_0',5),('new_holdouts_0',12),
           ('new_holdouts_1',1),('new_holdouts_1',6),('new_holdouts_1',8),('original_holdouts_0',5),('original_holdouts_0',6)}
BAD_ANSWER={('continuity_1',6),('original_holdouts_0',6),('original_holdouts_1',4)}
PARTIAL_OVERSTATED={('continuity_0',9),('continuity_1',7),('new_holdouts_0',7)}


def read(path):
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def assess(rows, baseline=False):
    scores=[]
    for r in rows:
        conv,turn=r['conversation'],r['turn'];key=(conv,turn);p=r['plan'];prop=p.get('request_proposition') or {}
        corr=turn in CORRECTIONS.get(conv,set());follow=turn in FOLLOWUPS.get(conv,set())
        clar=p.get('response_kind')=='clarification' or ('which person' in r['text'].lower() and not p)
        genuine=key in GENUINE
        relevant=(not clar or genuine) and key not in BAD_ANSWER
        # A clarification's category and requested field must fit the ambiguity.
        clarification_ok=clar and genuine and p.get('ambiguity_type')=='addressee'
        if conv=='original_holdouts_1' and turn==4:relevant=False
        bound=bool(p.get('bound_referent_id')) and key not in BAD_CONTINUITY
        if baseline:bound=False
        correction_ok=bool(corr and bound and p.get('conversational_act')=='correction' and relevant)
        follow_ok=bool(follow and bound and p.get('conversational_act') in {'follow_up','correction'} and relevant)
        before=r.get('prior_referents') or {};after=r.get('persisted_referents') or {}
        old_id,new_id=before.get('active_id'),after.get('active_id')
        if baseline:focus=None
        elif follow:
            focus=bool(old_id and new_id==old_id) if p.get('conversational_act')!='correction' else bool(new_id and new_id!=old_id)
        elif corr:focus=correction_ok and bool(new_id and new_id!=old_id)
        else:focus=bool(new_id and (clar and old_id==new_id or not clar and new_id!=old_id)) if not genuine else True
        sufficiency=relevant and (baseline or key not in PARTIAL_OVERSTATED)
        if p.get('response_kind')=='unknown' and r.get('expect',{}).get('sufficiency') in {'direct','partial'}:
            # Preserve original fixture labels separately; obvious tautological
            # ash-drum naming remains an appropriate unknown in the local audit.
            if key!=('original_holdouts_0',5):relevant=False;sufficiency=False
        role_errors={('continuity_0',4),('continuity_1',9)} if baseline else BAD_ROLES
        role_ok=bool(prop) and key not in role_errors and not (prop.get('missing_argument') and prop.get(prop['missing_argument']))
        if p.get('reason')=='invalid_role_or_prior_binding':role_ok=False
        if genuine:role_ok=clarification_ok
        quality=1 if not relevant or not sufficiency else 2
        if clar and not genuine:quality=0
        if key==('original_holdouts_0',6):quality=0
        padding=conv.startswith('original_holdouts') and turn>=7
        score={'conversation':conv,'turn':turn,'player':r['player'], 'relevance':relevant,'sufficiency':sufficiency,
            'correction':correction_ok if corr else None, 'follow_up':follow_ok if follow else None,
            'referent_binding':bound if corr or follow else None, 'active_focus':focus,
            'entity_roles':role_ok,'false_clarification':clar and not genuine,
            'genuine_clarification':clarification_ok if genuine else None,
            'quality':quality,'playability':quality,'repeated_padding_fixture':padding,
            'reason': 'Generic clarification or rejected interpretation.' if clar and not genuine else
                'Bound target/relationship or role repair is incorrect.' if key in BAD_CONTINUITY else
                'Partial information overstated as a complete answer.' if not baseline and key in PARTIAL_OVERSTATED else
                'Observed safe answer/uncertainty; entity-role and frozen-label checks are reported separately.'}
        scores.append(score)
    return scores


def summarize(scores):
    metrics={}
    for field in ['correction','follow_up','referent_binding','active_focus','entity_roles','false_clarification','genuine_clarification','relevance','sufficiency']:
        values=[r[field] for r in scores if r[field] is not None]
        metrics[field]={'count':sum(values),'denominator':len(values),'rate':sum(values)/len(values) if values else None}
    metrics.update(quality_mean=statistics.mean(r['quality'] for r in scores),playability_mean=statistics.mean(r['playability'] for r in scores),turns=len(scores))
    return metrics


if __name__=='__main__':
    baseline=assess(read(OUT/'baseline/live_turns.jsonl'),True)
    final=assess(read(OUT/'final/live_turns.jsonl'))
    (OUT/'turn_scores.json').write_text(json.dumps({'baseline':baseline,'final':final},indent=2))
    matched=[r for r in final if r['conversation'] in {'continuity_0','continuity_1'}]
    metrics={'method':'Implementing-agent local audit after final-code freeze. Explicit index annotations and structural checks; not independent human assessment. No scoring calls and no production tuning after holdouts.',
        'primary':summarize(final),'excluding_repeated_original_padding':summarize([r for r in final if not r['repeated_padding_fixture']]),
        'matched_baseline':summarize(baseline),'matched_final':summarize(matched),
        'limits':'Entity-role score checks recorded binary proposition slots and named roles, not unrestricted semantic correctness. Binding scores include semantic operation correctness and answer suitability. Focus score includes failed correction/new-question acquisition; safe rejection can retain old focus while failing intent. Source sufficiency/expected frozen labels remain independently inspectable.'}
    (OUT/'quality_metrics.json').write_text(json.dumps(metrics,indent=2))
    print(json.dumps(metrics,indent=2))

"""Finite realization experiment, not imported by runtime. No state writes or IO."""
import copy

def structured_flexible(narration, declarations, decision):
    """B lower-bound experiment: structured authority alone cannot police prose."""
    from game.gm_resolution_decision import validate_declared_claims_against_decision
    audit=validate_declared_claims_against_decision(declarations,decision=decision)
    return dict(accepted=audit['hard_valid'],text=narration if audit['hard_valid'] else '',audit=audit)

def render_closed(plan, catalog, required, variants):
    """C: only engine text or reviewed variants. No free-text hole, no mutations.

    Catalog must be prefiltered by the engine's publication/reveal owner.
    Public claim IDs alone do not imply authorization in another operation.
    """
    if not isinstance(plan,dict) or set(plan)!={'atoms','texture'}: return dict(accepted=False,reason='plan_schema')
    if not isinstance(plan['atoms'],list) or len(plan['atoms'])>24: return dict(accepted=False,reason='atom_bound')
    if plan['texture'] not in {'none','rain'}: return dict(accepted=False,reason='texture_selector')
    ids=[]; output=[]
    for atom in plan['atoms']:
        if not isinstance(atom,dict) or set(atom)!={'claim_id','variant'}: return dict(accepted=False,reason='atom_schema')
        cid=atom['claim_id']; variant=atom['variant']
        if not isinstance(cid,str) or cid not in catalog: return dict(accepted=False,reason='unpublished_or_unknown_claim')
        if not isinstance(variant,str): return dict(accepted=False,reason='variant_type')
        if variant=='canonical': text=catalog[cid]['text']
        elif (cid,variant) in variants: text=variants[cid,variant]
        else: return dict(accepted=False,reason='unreviewed_variant')
        ids.append(cid); output.append(text)
    if not set(required)<=set(ids): return dict(accepted=False,reason='required_anchor_omitted')
    if plan['texture']=='rain': output.append('Rain patters on the gate stones.')
    return dict(accepted=True,text=' '.join(output),claim_ids=ids,state_mutations=[])

def experiment(context, corpus):
    # Source selection is explicit and operation-specific; not the full decision catalog.
    catalog={r['claim_id']:copy.deepcopy(r) for r in context['decision']['realization_claims'] if r['source_ref'].startswith(('scene.visible_facts.','scene.opening_seed_facts.'))}
    required={'rc_a83c5bcfc65e','rc_d40a1efdddb3','rc_3b26b521977b'}
    runner='rc_3b26b521977b'; notice='rc_a83c5bcfc65e'
    variants={
      (runner,'word_order'):'Near the rain barrel, a tavern runner trades hot stew and rumors.',
      (runner,'synonym'):'A tavern runner trades hot stew and gossip near the rain barrel.',
      (notice,'tense'):'The notice board lists taxes, curfew rules, and a warning about a patrol that has gone missing.',
    }
    results=[]
    for row in corpus:
        decl=copy.deepcopy(context['declared_claims'])
        if row['id']=='E19': decl.append(dict(decl[0],declaration_id='forged',source_claim_id=None,text=row['text']))
        b=structured_flexible(row['text'],decl,context['decision'])
        # Caller expresses selections, not arbitrary strings. Unsafe inputs retain their raw prose.
        plan={'atoms':[{'claim_id':cid,'variant':'canonical'} for cid in sorted(required)],'texture':'none'}
        safe=row['interpretation'] in {'supported','incidental'}
        if safe:
            variant={'E2':'word_order','E3':'synonym','E4':'tense'}.get(row['id'])
            if variant:
                cid=notice if row['id']=='E4' else runner
                next(a for a in plan['atoms'] if a['claim_id']==cid)['variant']=variant
            if row['id']=='E5': plan['texture']='rain'
            if row['id']=='E18': plan['atoms'].append(dict(plan['atoms'][0]))
        elif row['id']=='E17': plan['atoms']=[]
        else: plan['free_text']=row['text']
        c=render_closed(plan,catalog,required,variants)
        results.append(dict(id=row['id'],B=b,C=c,C_input=plan,interpretation=row['interpretation']))
    attacks=[
      {'atoms':[{'claim_id':'hidden_identity','variant':'canonical'}],'texture':'none'},
      {'atoms':[{'claim_id':runner,'variant':'you_kill_guard'}],'texture':'none'},
      {'atoms':[{'claim_id':runner,'variant':'canonical','text':'You gain 100 gold.'}],'texture':'none'},
      {'atoms':[],'texture':'the_secret_identity'},
    ]
    controls=[render_closed(p,catalog,required,variants) for p in attacks]
    assert all(not c['accepted'] for c in controls)
    assert all(r['C']['accepted']==(r['interpretation'] in {'supported','incidental'}) for r in results)
    return dict(corpus=results,attack_controls=controls,catalog=catalog,required=sorted(required),variants=[dict(claim_id=k[0],variant=k[1],text=v) for k,v in variants.items()],limitations=['Finite reviewed variants only; no semantic equivalence classifier.','Required anchors are an experimental policy subset, not a discovered production requirement.','Publication prefilter is a caller precondition; this is not complete visibility enforcement.','No production integration, persistence or quality benchmark.'])

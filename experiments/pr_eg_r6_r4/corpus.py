"""Author-authored synthetic worlds and labels, established before any run.

Facts are fixture inputs, not extracted from labels or architecture outputs.
Eight independent lexical variants per family; template dependence is reported.
"""
from copy import deepcopy


def proposition(predicate, roles, requested='', *, evidence='', **qualifiers):
    return dict(predicate=predicate, predicate_evidence=evidence or predicate,
                roles=[dict(name=k, value=v, entity_id='', evidence=v) for k, v in roles.items()],
                requested_role=requested, temporal='', spatial='', epistemic='npc_knowledge',
                prior_reference='', negated=False, **{}) | qualifiers


def cases():
    result = []
    for i in range(8):
        # Distinct nouns, names and open predicates, including held-out relations.
        actor = ['surveyor','glazier','weaver','horticulturist','cartographer','bellfounder','lichen keeper','tide auditor'][i]
        item = ['amber lens','slate prism','ivory spindle','jade comb','cobalt dial','silver reed','ochre astrolabe','pearl sextant'][i]
        verb = ['stabilizes','recalibrates','attunes','insulates','reconciles','counterbalances','triangulates','resonates'][i]
        predicate = ['stabilize','recalibrate','attune','insulate','reconcile','counterbalance','triangulate','resonate'][i]
        partition = 'development' if i < 2 else 'validation' if i < 5 else 'holdout'
        def add(family, question, query, sources, label, bindings=None, tags=(), forbidden=(), ambiguity=False):
            cid=f'{family}-{i:02}'
            rows=[]
            for j, s in enumerate(sources):
                rows.append(dict(id=f'{cid}:s{j}', context=cid, npc='vesper', provenance='world_source',
                                 disclosure='public', knowledge_status='known', epistemic='npc_knowledge') | s)
            result.append(dict(id=cid, partition=partition, family=family, question='Vesper, '+question,
                queries=query if isinstance(query,list) else [query], sources=rows, npc='vesper',
                ambiguity=ambiguity, tags=list(tags), expected=dict(response_class=label,
                    relevance=label not in {'UNKNOWN','CLARIFICATION_REQUIRED'},
                    sufficiency={'DIRECT':'complete','PARTIAL':'partial'}.get(label,'none'),
                    bindings=bindings or {}, forbidden_claims=list(forbidden))))
        def src(text, facts, **kw): return dict(text=text, facts=facts, **kw)
        q=proposition('keep',{'object':item},'keeper',evidence='keeps')
        f=proposition('keep',{'object':item,'keeper':actor},evidence='keeps')
        text=f'The {actor} keeps the {item}.'
        add('direct_exact',f'who keeps the {item}?',q,[src(text,[f])],'DIRECT',{'keeper':actor})
        add('direct_paraphrase',f'who has custody of the {item}?',q|{'predicate_evidence':'has custody of'},[src(text,[f])],'DIRECT',{'keeper':actor},['paraphrase'])
        add('direct_unstructured',f'who keeps the {item}?',q,[src(text,[])],'DIRECT',{'keeper':actor},['unstructured'])
        add('direct_multiple_facts',f'who keeps the {item}?',q,[src(text+' The porter guards the brass token.',[f,proposition('guard',{'object':'brass token','guard':'porter'},evidence='guards')])],'DIRECT',{'keeper':actor},['multiple_facts'])
        cq=proposition('tell',{'speaker':'Cala','recipient':'Brin','topic':item},'message_content',evidence='tell')
        cf=proposition('tell',{'speaker':'Cala','recipient':'Brin','topic':item,'message_content':'it is cracked'},evidence='told')
        ct=f'Cala told Brin about the {item}: it is cracked.'
        add('direct_roles',f'what did Cala tell Brin about the {item}?',cq,[src(ct,[cf])],'DIRECT',{'message_content':'it is cracked'},['multi_role'])
        oq=proposition(predicate,{'object':item},'agent',evidence=verb)
        of=proposition(predicate,{'object':item,'agent':actor},evidence=verb)
        add('direct_open',f'who {verb} the {item}?',oq,[src(f'The {actor} {verb} the {item}.',[of])],'DIRECT',{'agent':actor},['open_world'])
        tq=proposition('keep',{'object':item},'keeper',evidence='keeps',temporal='today')
        tf=deepcopy(f);tf['temporal']='today'
        add('direct_qualified',f'who keeps the {item} today?',tq,[src(text[:-1]+' today.',[tf])],'DIRECT',{'keeper':actor},['qualifier'])
        shift=proposition('keep',{'object':item},'shift',evidence='keeps')
        add('partial_multipart',f'who keeps the {item}, and when is their shift?',[q,shift],[src(text,[f])],'PARTIAL',{'keeper':actor},['multipart'])
        inf=proposition('keep',{'object':item},'keeper',evidence='keeps')
        add('partial_indefinite',f'who keeps the {item}?',q,[src(f'Someone keeps the {item}.',[inf])],'PARTIAL',{},['uncertainty'],[actor])
        rf=deepcopy(f);rf['epistemic']='rumor'
        add('partial_rumor',f'who keeps the {item}?',q,[src(f'Rumor says the {actor} keeps the {item}.',[rf],epistemic='rumor')],'PARTIAL',{'keeper':actor},['qualifier','rumor'])
        alt=deepcopy(f);alt['roles'][-1]['value']='porter';alt['roles'][-1]['evidence']='porter'
        add('partial_conflict',f'who keeps the {item}?',q,[src(text,[f]),src(f'The porter keeps the {item}.',[alt])],'PARTIAL',{'keeper':[actor,'porter']},['conflict'])
        rq=proposition('tell',{'speaker':'Brin','recipient':'Cala','topic':item},'message_content',evidence='tell')
        add('related_reversal',f'what did Brin tell Cala about the {item}?',rq,[src(ct,[cf])],'RELATED_NONANSWER',{},['multi_role'],['it is cracked'])
        guard=proposition('guard',{'object':item},'guard',evidence='guards')
        add('related_relationship',f'who guards the {item}?',guard,[src(text,[f])],'RELATED_NONANSWER',{},['unsupported_inference'],[actor])
        add('related_time',f'who keeps the {item} today?',tq,[src(text[:-1]+' yesterday.',[f|{'temporal':'yesterday'}])],'RELATED_NONANSWER',{},['qualifier'],[actor])
        nq=q|{'negated':True,'predicate_evidence':'keep'};nf=f|{'negated':False}
        add('related_negation',f'who does not keep the {item}?',nq,[src(text,[nf])],'RELATED_NONANSWER',{},['negation'],[actor])
        add('unknown_empty',f'who keeps the {item}?',q,[],'UNKNOWN',{},['unstructured'],[actor])
        add('unknown_private',f'who keeps the {item}?',q,[src(text,[f],knowledge_status='unknown')],'UNKNOWN',{},['private_npc'],[actor])
        add('unknown_history',f'who keeps the {item}?',q,[src(text,[f],provenance='verified_history')],'UNKNOWN',{},['history_laundering'],[actor])
        add('unknown_forged',f'who keeps the {item}?',q,[src(text,[f],provenance='provider')],'UNKNOWN',{},['forged_provenance'],[actor])
        for family,kind in [('restricted_password','password'),('restricted_countersign','countersign')]:
            secret=f'violet-{i}-cinder'
            pq=proposition('code',{'kind':kind,'object':item},'value',evidence=kind)
            pf=proposition('code',{'kind':kind,'object':item,'value':secret},evidence=kind)
            add(family,f'what is the {kind} for the {item}?',pq,[src(f'The {kind} for the {item} is {secret}.',[pf],disclosure='secret')],'RESTRICTED',{},['restricted'],[secret])
        add('clarification',f'who keeps it, the {item} or the brass token?',q,[src(text,[f])],'CLARIFICATION_REQUIRED',{},['ambiguity'],ambiguity=True)
    return result

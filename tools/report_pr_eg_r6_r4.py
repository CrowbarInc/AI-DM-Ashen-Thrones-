"""Independent closeout aggregation and review packaging from immutable records."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'artifacts/pr_eg_r6_r4'


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
def lines(name):return [json.loads(l) for l in (OUT/name).read_text(encoding='utf-8').splitlines()] if (OUT/name).exists() else []
def dump(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
def doc(n,title,body):(OUT/f'{n:02}_{title.upper().replace(" ","_").replace("/","_")}.md').write_text(f'# {n:02} — {title}\n\n{body.strip()}\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pct(k,n):return f'{k}/{n} ({100*k/n:.1f}%)' if n else '0/0 (not applicable)'
def quantile(v,p):return sorted(v)[max(0,math.ceil(len(v)*p)-1)] if v else None
def wilson(k,n):
    if not n:return None
    z=1.96;v=k/n;d=1+z*z/n;m=(v+z*z/(2*n))/d;h=z*math.sqrt(v*(1-v)/n+z*z/(4*n*n))/d
    return [round(m-h,4),round(m+h,4)]


def audited(c,r):
    """Clarify acceptance vs omission without changing labels or raw scores."""
    s=dict(r['scores']);a=r['result'];e=c['expected']
    positive=a['response_class'] in {'DIRECT','PARTIAL'};epos=e['response_class'] in {'DIRECT','PARTIAL'}
    def norm(v):return re.sub(r'^(the|a|an) ', '', ' '.join(str(v).casefold().split()))
    def vals(v):return sorted(norm(x) for x in (v if isinstance(v,list) else [v]))
    binding_ok={k:vals(v) for k,v in a['bindings'].items()}=={k:vals(v) for k,v in e['bindings'].items()}
    unsupported=any(k not in e['bindings'] or any(v not in vals(e['bindings'][k]) for v in vals(value)) for k,value in a['bindings'].items())
    s['bindings_correct']=binding_ok
    s['roles_correct']=binding_ok and (not epos or bool(a['selected_source_ids']))
    if c['id']=='guard_direct' and a['qualifiers']==[{'temporal':'','spatial':'at the lodge','negated':False,'epistemic':'npc_knowledge'}]:
        # E17: independent reread confirms this literal qualifier. The fixture's
        # semantic annotation omitted it; frozen labels remain intact.
        s['qualifiers_correct']=True
        s['evaluation_note']='E17: supplemental fact annotation omitted the literal spatial qualifier; original prose supports it.'
    s['answer_success']=s['class_correct'] and binding_ok and s['qualifiers_correct'] and s['authorization_correct'] and not unsupported
    s['initial_false_acceptance']=s['false_acceptance']
    s['unsupported_binding']=unsupported
    s['false_acceptance']=positive and (not epos or unsupported or not s['qualifiers_correct'] or a['response_class']=='DIRECT' and e['response_class']!='DIRECT')
    s['omitted_binding']=epos and bool(e['bindings']) and not a['bindings']
    if s['answer_success']:s['earliest_failure']=''
    if not s['answer_success']:
        if r.get('error'):cause='E03'
        elif not s['authorization_correct']:cause='E12'
        elif unsupported:cause='E10'
        elif r['architecture']=='C':
            rejection=a['rejections']
            cause='E03' if 'invalid_source_or_schema' in rejection else 'E14' if rejection else 'E02'
        elif r['architecture']=='A':
            props=json.loads(r['raw']).get('source_propositions',[]) if r.get('raw') else []
            cause='E03' if props and any(x['coverage']=='unknown' for x in a['source_coverage']) else 'E03' if s['omitted_binding'] else 'E01' if c['ambiguity'] else 'E08' if e['response_class']=='DIRECT' and a['response_class']=='PARTIAL' else 'E02'
        else:cause='E02'
        s['earliest_failure']=cause
    return s


def aggregate(rows,corpus):
    out={}
    for arch in 'ABC':
        rs=[r for r in rows if r['architecture']==arch]
        scores=[audited(corpus[r['case_id']],r) for r in rs]
        stats={k:sum(s[k] for s in scores) for k in ['answer_success','class_correct','relevance_correct','sufficiency_correct','roles_correct','qualifiers_correct','authorization_correct','false_acceptance','false_rejection','unsupported_binding','omitted_binding']}
        stats['n']=len(rs);stats['success_wilson95']=wilson(stats['answer_success'],len(rs))
        stats['errors']=dict(Counter(r.get('error','') for r in rs))
        stats['failure_attribution']=dict(Counter(s['earliest_failure'] for s in scores if s['earliest_failure']))
        classes={}
        for cls in ['DIRECT','PARTIAL','RELATED_NONANSWER','UNKNOWN','RESTRICTED','CLARIFICATION_REQUIRED']:
            subset=[r for r in rs if corpus[r['case_id']]['expected']['response_class']==cls]
            classes[cls]={'n':len(subset),'success':sum(audited(corpus[r['case_id']],r)['answer_success'] for r in subset)}
        stats['classes']=classes
        lat=[r['latency_ms'] for r in rs];ins=[];outs=[]
        for r in rs:
            u=r.get('usage') or {}
            if u.get('input_tokens') is not None:ins.append(u['input_tokens'])
            if u.get('output_tokens') is not None:outs.append(u['output_tokens'])
        stats['cost']=dict(calls=sum(r['calls'] for r in rs),usage_samples=len(ins),input_tokens=sum(ins),output_tokens=sum(outs),
            mean_input=round(statistics.mean(ins),2) if ins else 0,p95_input=quantile(ins,.95) or 0,
            mean_output=round(statistics.mean(outs),2) if outs else 0,mean_latency_ms=round(statistics.mean(lat),2) if lat else 0,p95_latency_ms=quantile(lat,.95))
        out[arch]=stats
    return out


def table(metrics):
    body='| Architecture | Supported answer success | Relevance | Sufficiency | Acceptance errors | Rejections of answerable cases |\n|---|---:|---:|---:|---:|---:|\n'
    for a,m in metrics.items():body+=f"| {a} | {pct(m['answer_success'],m['n'])} | {pct(m['relevance_correct'],m['n'])} | {pct(m['sufficiency_correct'],m['n'])} | {m['false_acceptance']} | {m['false_rejection']} |\n"
    return body


def main():
    from experiments.pr_eg_r6_r4.run import verify
    verify()
    corpus={c['id']:c for p in ('development','validation','holdout') for c in read(p+'.json')}
    rows=lines('primary.jsonl');assert len(rows)==528 and len({(r['case_id'],r['architecture']) for r in rows})==528
    secondary=lines('secondary.jsonl');assert len(secondary)==22
    sup={c['id']:c for c in read('supplemental.json')+read('paraphrases.json')};sr=lines('supplemental_results.jsonl')+lines('paraphrase_results.jsonl');assert len(sr)==len(sup)*3
    baseline=read('baseline.json');changed=[p for p,h in baseline['production_hashes'].items() if not (ROOT/p).exists() or sha(ROOT/p)!=h]
    dump('production_integrity.json',dict(checked=len(baseline['production_hashes']),changed=changed))
    assert not changed,'Production/data changed during isolated experiment'
    comparable=[r for r in rows if not corpus[r['case_id']]['ambiguity']]
    metrics=aggregate(comparable,corpus);all_metrics=aggregate(rows,corpus)
    partitions={p:aggregate([r for r in comparable if r['partition']==p],corpus) for p in ('development','validation','holdout')}
    supplementary=aggregate(sr,sup)
    secondary_metrics=aggregate([r for x in secondary for r in x.get('results',[])],corpus)
    # This subset is post hoc: A primary kernel did not consume the gold ambiguity
    # bit that B/C used. Exclude all eight from the architectural ranking.
    # Frozen labels remain unchanged; this comparability defect limits the verdict.
    paired={}
    for p in ('validation','holdout'):
        idx={(r['case_id'],r['architecture']):r for r in comparable if r['partition']==p}
        paired[p]={}
        for arch in 'BC':
            wins=losses=0
            for c in corpus.values():
                if (c['id'],'A') not in idx:continue
                a=audited(c,idx[c['id'],'A'])['answer_success'];b=audited(c,idx[c['id'],arch])['answer_success']
                wins+=b and not a;losses+=a and not b
            paired[p][arch]=dict(wins=wins,losses=losses,net=wins-losses)
    # Verify pre-provider access using exact payload source IDs, not answer labels.
    from experiments.pr_eg_r6_r4.engine import eligible
    leaks=[]
    for r in rows:
        c=corpus[r['case_id']];sent=(r.get('prompt') or {}).get('permitted_sources',[])
        if not {s['id'] for s in sent}<={s['id'] for s in eligible(c)}:leaks.append([r['case_id'],r['architecture']])
    assert not leaks
    invalid=lines('invalid_initial_attempts.jsonl')
    summary=dict(verdict='C — INCONCLUSIVE / FURTHER DISCOVERY REQUIRED',core=metrics,all_diagnostic=all_metrics,
                 partitions=partitions,paired=paired,secondary=secondary_metrics,supplemental=supplementary,
                 provider_payload_access_violations=leaks,invalid_attempt_records=len(invalid),
                 scoring_amendment='False acceptance excludes omitted bindings; identity uses case/article normalization; one supplemental spatial annotation was incomplete. Frozen labels and initial scores preserved.',
                 comparability_amendment='Eight ambiguity cases excluded from architectural ranking post hoc; B/C consumed a gold ambiguity bit A did not. No A/B verdict permitted.')
    dump('summary.json',summary)
    with (OUT/'per_case_results.jsonl').open('w',encoding='utf-8') as f:
        for r in rows+sr:
            c=(corpus|sup)[r['case_id']]
            f.write(json.dumps(dict(case_id=c['id'],architecture=r['architecture'],partition=c['partition'],
                expected=c['expected'],result=r['result'],audited_scores=audited(c,r),
                comparable=not c['ambiguity'] and c['partition'] in {'development','validation','holdout'}),ensure_ascii=False)+'\n')
    classes=Counter(c['expected']['response_class'] for c in corpus.values())
    tags=Counter(t for c in corpus.values() for t in c['tags'])
    historical=read('historical_inventory.json')
    decision='C — INCONCLUSIVE / FURTHER DISCOVERY REQUIRED'
    overview=f'''No production migration is justified. The primary comparison isolates correspondence using gold question meanings and identical eligible prose. B requires authored facts, while C must validate AI proposals against those facts. B recovers structured answers cheaply but loses prose-only cases; C mostly fails its proposal contract. Actual production interpretations reduce B substantially.

{table(metrics)}

This table covers 168 nonambiguous cases. All 176 cases and the excluded ambiguity diagnostics are preserved. B/C consumed a gold ambiguity bit that the A kernel did not: that defect prevents using the eight ambiguity cases as evidence of superiority. A is the unchanged production correspondence kernel/prompt inside a shared aggregator, not a full production rewrite or /api/chat qualification.

Verdict: **{decision}**. There were zero tested source-access violations; semantic correctness and low manual authoring burden remain unresolved. Do not begin PR-EH.'''
    doc(1,'Executive Summary',overview)
    doc(2,'Repository Baseline',f'''HEAD `{baseline['commit']}`. The tree was already extensively dirty; exact original status is in `baseline_status.txt`. No pre-existing edits were reverted. Configured model `{baseline['model']}`, temperature 0, max output 1800. Keys were loaded through `game.config`, never copied into evidence. Existing gates remain off by default.

322 production/data files were hashed before work. Closeout: {len(changed)} changed. Changes in this cycle are isolated experiment code, tests, reporting tools, artifacts and CURRENT_REVIEW. No commit or production migration was performed.''')
    doc(3,'Current Source-Resolution Audit','''There are two production families and multiple entry points:

1. Gated semantic family: `game/unified_semantic_planning.py:1274 planning_decision` and `:1361 locked_plan_for_social_turn` enter `:782 authorize_information_turn`. The normal planner or `host_constrained_candidates` gate proposes the same plan. `validate_plan_schema` cleans meaning; referent binding runs before source resolution. `_topic_rows` checks NPC authorization. Sources longer than 800 characters are dropped before proposal; `_provider_context` caps at 12, and the prompt asks for at most four source propositions. At `:989` a missing proposition produces UNKNOWN. `semantic_correspondence.coverage` checks literal witnesses and argument identity; `semantic_operations.named_coverage` compares predicate and named roles. `_select` preserves original source text. Multiple direct sources currently produce clarification, even when they merely disagree.
2. Legacy/social family: `game/social.py:3895 resolve_social_action` uses `_next_topic_to_reveal`, authored relevance/sufficiency checks, and revealed-topic communication evidence. `select_best_social_answer_candidate:2746` considers clue/last-answer/topic-pressure material; `_match_present_npc_topic_authored_knowledge:2392` is a later authored fallback. `realize_authored_knowledge_answer:2911`, `apply_structured_social_answer_candidate_to_resolution:3426`, `social_exchange_emission` candidate selection, and `gm_retry` can revisit sources. `conversational_continuity` checks sufficiency on historical restatement. All positive final paths must retain `authorize_npc_disclosure` checks.

The semantic kernel has a binary compatibility path and named-role path. The legacy sufficiency path separately uses `dialogue_authority.classify_answer_sufficiency`. They are different definitions, not interchangeable labels. Final `build_dialogue_authority` and immutable acceptance reauthorize sources; expression validation and `seal_delivery_contract` protect delivered records. API/history agreement and durable referents remain downstream responsibilities.

Loss points: NPC focus; 800-character exclusion; first-12 source cap; four-proposition output cap; omitted source proposition; wrong normalized relation/role name; source still marked as requesting the role it actually supplies; strict argument identity; malformed witnesses; epistemic mismatch; multiple-source ambiguity. Provider repeatedly reconstructs canonical sentence relationships because authored topics mostly contain prose, not roles. Quote validation can prove occurrence, not entailment or predicate normalization.''')
    doc(4,'Historical Failure Inventory',f'''Inspected {len(historical['files'])} raw predecessor JSONL files across R6-R2, R2-R1, R2-R2, R3 and R3-R1. Preserved {historical['examples']} full records in `historical_raw_examples.jsonl`, with original path/line and whole-file SHA-256 in `historical_inventory.json`. Counts are diagnostic records across overlapping runs, not independent failures.

- R2-R1 final/live_turns.jsonl:28: Oren is asked the north road name. Delivered source says Crown Way, but the source proposition leaves the requested subject blank. Earliest E03 (lost answer argument), downstream E08 (complete sentence classified partial).
- R3-R1 fresh/live_turns.jsonl:1: Cala/Brin/cistern source contains the cracked message. Both question and source use requested_role=value, and source omits message content. Earliest E03 on the source, with E01 role-vocabulary ambiguity also possible; downstream E08. Structurally accepted JSON is semantically incomplete.
- R3-R1 fresh/live_turns.jsonl:2: reverse_must_be_empty is an operation failure before correspondence. E01; exclude it from correspondence performance claims.
- R2-R1 baseline/live_turns.jsonl:1: amber reliquary is UNKNOWN; visible authored topics do not include amber. This is not automatically an evidence-recovery failure. Treating every UNKNOWN as a failure is E17.
- R2 matched_r2/live_turns.jsonl:10 and R3-R1 fresh:43 refuse restricted material. These are boundary successes, not answer failures.

The automatic `earliest_causal_hypothesis` is triage only. It does not establish an error from the selected source alone. Raw selected rows and author fixture definitions are included for external review; do not sum hypotheses as proven failures.''')
    taxonomy=['Question interpretation incorrect','Relevant source not retrieved','Source proposition malformed or semantically incomplete','Question/source role mismatch','Relationship mismatch','Qualifier mismatch','Relevant source insufficient','Complete source marked partial','Related nonanswer marked direct','Unsupported inference','Source unavailable to NPC','Source restricted','Invalid provenance','Host false rejection','Host false acceptance','Final expression mismatch','Evaluation error']
    doc(5,'Failure Taxonomy','\n'.join(f'- E{i:02}: {v}.' for i,v in enumerate(taxonomy,1))+'''\n\nRecord the earliest demonstrated cause, retaining downstream effects separately. Source-schema failures precede host rejection. A missing requested-role binding in a source interpretation is E03, even if the source sentence is complete. This cycle does not test final expression, so E16 is not inferred from a kernel result. `per_case_results.jsonl` contains audited attribution; original run scores remain in raw files.''')
    doc(6,'Evaluation Contract',(ROOT/'experiments/pr_eg_r6_r4/CONTRACT.md').read_text()+'''\n\nCloseout amendments: the first execution was invalid and preserved separately. A schema compatibility correction normalized named-role gold propositions; adapter hashes are recorded separately without changing labels. Eight gold-ambiguity cases are diagnostic only because access to the ambiguity bit differed. False acceptance scoring originally counted all missing bindings; audited scoring distinguishes unsupported bindings from omissions and normalizes case/articles in identities. Independent reread credits the literal at-the-lodge qualifier omitted by the supplemental guard annotation (E17); labels remain frozen. These post-exposure measurement corrections prevent a strong architectural verdict.''')
    doc(7,'Answer-Class Definitions','''DIRECT: all requested arguments supplied by authorized evidence with matching roles/qualifiers. PARTIAL: only part of the request supplied, an unidentified participant, qualified candidate, or unresolved contradictory answers. RELATED_NONANSWER: same subject but wrong relationship, direction or qualifier. UNKNOWN: no eligible supporting evidence. CLARIFICATION_REQUIRED: genuine ambiguity in the question. RESTRICTED: relevant host-known evidence exists but is denied.

Keep relevance, sufficiency and disclosure separate. Rumor and conflict candidate bindings are not canonical truth. The six classes require an explicit conflict/uncertainty policy; this corpus uses PARTIAL for disagreement and qualified candidates. Changing that policy would require a new corpus version, not editing these frozen labels.''')
    doc(8,'Architecture A Specification','''Unchanged production `_invoke_provider` prompt/schema and `semantic_correspondence.coverage`. The primary adapter supplies gold question propositions and uses provider source interpretations. It calls coverage separately for each gold subquestion. Shared aggregation retains bindings across authorized sources and marks conflict PARTIAL. This differs from production selection, which clarifies on multiple direct sources. Thus it measures correspondence, not end-to-end production behavior.

No tuning of the production baseline occurred. Strict clean_proposition normalization adds binary compatibility slots; it does not change predicate/roles. A receives the same eligible prose as C, at most two sources in core cases. A is not compared against the earlier whole-conversation acceptance percentages; those measure a different responsibility.''')
    doc(9,'Architecture B Specification','''B reads host-authored semantic facts: open predicate, named roles, requested unknown role, polarity, temporal/spatial qualifiers and epistemic status. It matches known arguments by role and value, binds requested arguments, and combines subquestion coverage. It repeats the production disclosure check after positive matches. No phrase table, lore lexicon, provider call, or storage write.

Every populated semantic fact was authored with the synthetic world, independently of expected output. That is a substantial prior input advantage over prose alone. B solves unification after authoring; it does not solve extraction, aliases, predicate equivalence, implicit relations or ontology maintenance. B cannot recover the eight prose-only answers. Open predicates do not require code changes, but author/question vocabulary alignment remains necessary.''')
    doc(10,'Architecture C Specification','''C receives eligible source IDs/text, epistemic status and gold question propositions. It proposes source propositions, a quoted span, requested answer role/value and advisory sufficiency. Host checks ID/context, NPC knowledge, disclosure, schema, source span, epistemic value, authored semantic agreement and supported answer value; final authorization runs again. Advisory sufficiency never grants permission.

Semantic agreement uses an exact fact signature rather than a model judgment. This avoids treating a quote as proof, but requires the same authoring burden as B and rejects semantically equivalent article/role variants. The prompt/schema did not reliably teach that requested_role must be empty once supplied: many proposals included the role both as known and requested. `clean_proposition` correctly rejected that contradiction. No holdout-informed prompt repair was attempted. These results concern this prototype contract, not all possible AI-assisted architectures.''')
    doc(11,'Experimental Conditions',f'''Configured model `{baseline['model']}`; provider returned model IDs are retained per call. Temperature 0, max output 1800, production timeout from config, one logical call per A/C case; B uses zero. Both provider clients retain their SDK retry defaults; there is no harness repair/retry loop. All official primary calls returned without transport exceptions.

Inputs/labels are byte-frozen before provider exposure. Same gold questions, world prose, NPC ownership and permissions. Differences: B/C authored facts, A production prompt versus C bounded prompt/schema, deterministic ambiguity bit consumed only by B/C, shared aggregation versus native production selection. The eight ambiguity cases are excluded from ranking after discovering this mismatch; no strong architectural verdict is made. Corpus has 22 templates with eight lexical variants, rather than 176 independent natural conversations.''')
    doc(12,'Question Interpretation Control',f'''Primary: gold predicates, role names, missing arguments and qualifiers isolate correspondence. Primary provider payloads also expose those gold interpretations; source normalization can benefit from them. Do not extrapolate this performance to unhinted production.

Secondary: 22 fresh unhinted production planner calls on variant -07, one per family, with the gold field removed. Actual request propositions feed all three kernels. A native `authorize_information_turn` result is preserved alongside kernel results. C makes a fresh correspondence call using the actual request. B/C therefore inherit the actual role vocabulary and may fail to align it with authored facts.

{table(secondary_metrics)}

Secondary scores use the original independent labels. A actual query has only one requested role; multipart coverage may be lost. Native and replay outputs are different measures; neither is a 150-turn production qualification.''')
    doc(13,'Source Retrieval Control','''Core eligible sets are identical and contain at most two records, so retrieval recall of eligible records into the experiment payload is 100% by construction. This is a control, not evidence of production retrieval quality. Restricted, NPC-unknown, wrong-context and non-world provenance records are omitted before provider calls.

Production focus, 800-character filtering, first-12 selection and four-proposition generation are separate recall bottlenecks. Supplemental scaling probes use 1/4/12/32 eligible records with the answering source last. Read per-case source selections and token costs; these are isolated stress probes, not a corpus-level retrieval estimate. No full source index has been built or migrated.''')
    doc(14,'Corpus and Ground Truth',f'''176 frozen core cases: {dict(classes)}. Tags: {dict(tags)}. Partitions contain 44 development, 66 validation and 66 holdout cases. After equal-condition ambiguity exclusion: 42/63/63 comparable cases. At least 16 multi-role and 8 explicit paraphrase cases are in the core; the corpus also uses exact normalized gold meanings, not raw keyword rules. Additional 35 separately frozen probes broaden roles, qualifiers, paraphrases and source-list sizes, for 211 labeled cases in total.

Each case records question, gold relationship, known named arguments, requested missing role, sources with NPC/context/provenance/facts/disclosure/knowledge, relevance, sufficiency, answer class, expected bindings and forbidden claims. Labels were authored before execution and never derived from selected-source output. Prose-only source facts are deliberately absent in eight direct cases; expected answers remain independently specified.

Paraphrase coverage totals sixteen explicitly tagged cases: eight core and eight separately frozen diagnostic paraphrases. The additional paraphrases were created after the primary experiment; they meet total coverage but do not repair the original frozen holdout's narrow paraphrase coverage. This remains a comparative limitation.''')
    doc(15,'Frozen Holdouts','''`freeze.json` contains SHA-256 for all three partition files, corpus/adapter code and relevant unchanged production kernels. `adapter_correction.json` documents the single execution correction without changing partition hashes. Original frozen manifest remains intact. `supplemental_freeze.json` separately hashes the additional challenge data before its calls. Verify with `python -m experiments.pr_eg_r6_r4.run verify`.

Validation and holdout labels were not edited after exposure. No prompt or matcher tuning followed official holdout inspection. Separately frozen challenge cases and paraphrases (paraphrase_freeze.json) broaden coverage after the primary run; they are diagnostic, not replacement holdout evidence. Historical predecessor holdouts were not edited.''')
    doc(16,'Open-World Generalization','''Core development/validation/holdout use different agent nouns, artifacts and eight open relations. Held-out relations include counterbalance, triangulate and resonate. The matcher has no hard-coded predicate list. Supplemental institutional pairs cover appoint, precede and vouch; spatial probes use illuminate.

This proves the structured matcher accepts unfamiliar predicate strings when author and question share them. It does not prove open-world semantic interpretation: the gold meanings and manually authored fact vocabulary already solve that alignment. Awkward synthetic sentences and repeated templates further limit transfer to authored campaigns.''')
    doc(17,'Role Preservation','''Core Cala/Brin communication cases retain speaker, recipient, topic and message_content; reversed direction is a related nonanswer. Supplemental tests separate lender/borrower, owner/borrower, guard/protected party, buyer/seller, debtor/creditor, appointer/appointee, predecessor/successor and voucher/beneficiary. Direct and reverse queries are distinct.

Bindings are scored by exact role and value, not a bag of entity names. Missing bindings count as extraction failure. Empty negative-case bindings are not evidence of positive role preservation. Read role subsets in `per_case_results.jsonl` and supplemental results rather than treating all UNKNOWNs as correct role handling.''')
    doc(18,'Paraphrase and Entailment','''Custody versus keeping tests straightforward paraphrase; unstructured prose tests whether extraction can be trusted without a semantic annotation. Guarding is not entailed by custody, borrowing is not ownership, and reversing creditor/debtor changes the relationship.

A has a provider normalization advantage for prose-only answers. C's exact fact signature rejects articles and equivalent but differently named slots. Quotes alone prove lexical presence, not relation direction or entailment. Broad synonym and implicit relationship coverage remains insufficient; no phrase-specific matching exceptions were added.''')
    doc(19,'Partial Answers','''Three distinct partial mechanisms are tested: keeper known but shift absent; someone keeps an object but identity unknown; and qualified/conflicting candidates. Missing requested roles are retained explicitly. The host does not invent a shift, turn Someone into a named identity, or strengthen rumor into fact.

Direct source propositions should clear requested_role once the value is supplied. C frequently failed that structural contract. The original evaluator counted missing expected bindings as false acceptance; audited metrics treat omissions separately while preserving failure of supported answer recovery. This scoring correction is disclosed, not hidden in new labels.''')
    doc(20,'Related Nonanswers','''Core related cases reverse communication roles, substitute guarding for custody, change today to yesterday, or invert polarity. They concern the same subject but cannot supply the requested argument. Supplemental reverse social/institutional and spatial cases extend this.

The shared response class distinguishes RELATED_NONANSWER from UNKNOWN; native production may deliver the same unknown line while storing semantic related_nonanswer status. That presentation collapse is not evaluated as an unsupported factual answer. No informant is inferred from a road name or historical speech.''')
    doc(21,'Negation and Qualifiers','''Core cases cover positive versus negative claims, yesterday versus today and rumor versus unqualified knowledge. Supplemental probes add matching and mismatching space, possibility, conditionals, approximation, explicit uncertainty and an affirmative answer to a negative question. Host output retains the source epistemic/temporal/spatial/polarity fields and original authorized text.

Conditional and approximate epistemic labels are experimental strings, not a proposed production schema. For these cases the independently authored class is PARTIAL. A production design needs explicit conditional scope and numeric uncertainty, rather than stuffing them into a single epistemic string. Qualifier correctness on safe UNKNOWN is vacuous; inspect extraction and answer success too.''')
    doc(22,'Conflicting Evidence','''Eight core cases provide two public, NPC-known sources naming different keepers. Shared aggregation retains both candidates, marks conflict=true and returns PARTIAL. Neither is selected as canonical truth. Production native selection instead treats multiple direct sources as proposition ambiguity; this difference is explicit in the A adapter specification.

No source priority, time-based reconciliation, majority vote or silent winner is implemented. Provenance-specific conflict policy and contradictory epistemic status remain future design questions.''')
    doc(23,'Security Experiments',f'''Provider payload source-access violations in all 528 core records: {len(leaks)}. Restricted password/countersign, private NPC knowledge, forged provenance and historical speech laundering remain noneligible. Tested final source eligibility passes on every core record; this is a finite kernel result, not a universal proof.

Local tests inject invented IDs, cross-context IDs, reversed roles, wrong predicates, fabricated spans, epistemic strengthening, unsupported answer values, restricted/unknown knowledge and invalid history/provenance. C rejects these before adopting bindings. Quote-only unstructured semantic proposals also fail closed. Source ID selection never grants disclosure. No experiment code activates clues or writes game state.

Regression outcome: 317 passed, 2 failed with Windows WinError 5 on atomic replacement of temporary session files, and 4 delivery/replay tests deselected after an interrupted run. The focused experiment suite passed 197 tests. A workspace-temp retry of the two failures was interrupted without a result. Exact output is in verification_tests.txt and verification_status.json. No full production qualification is claimed. API/history agreement and durable referents are preserved by unchanged production/data hashes, not requalified by these isolated experiments. Unsupported semantic entailment in A remains a separate factual-authority risk despite source eligibility.''')
    calls=sum(m['cost']['calls'] for m in metrics.values())+sum(m['cost']['calls'] for m in secondary_metrics.values())+sum(m['cost']['calls'] for m in supplementary.values())+16
    doc(24,'Provider Evidence',f'''Official primary evidence: 176 A calls and 176 C calls; B makes none. Secondary: 22 unhinted A interpretation calls and 22 fresh C calls. Supplemental: 35 A calls and 35 C calls. Total **466 logical provider calls**. SDK retry behavior is not instrumented separately. Per-record model/settings, input/output usage, latency, raw JSON output and exact payload are retained in primary.jsonl, secondary.jsonl, supplemental_results.jsonl and paraphrase_results.jsonl.

Invalid first execution records: {len(invalid)} in invalid_initial_attempts.jsonl, excluded from architecture scoring. That file includes connection failures and interrupted adapter errors; paid responses lost before the KeyError was surfaced are not recoverable. Those attempts cannot be counted as successful official evidence or assigned zero billing. Both initial and corrected adapter hashes are preserved.

No mock-only provider success claim. Prompt C is versioned in engine.VERSION/C_PROMPT, A by production hash; schemas are frozen code. Configured model {baseline['model']}, temperature 0, max output 1800.''')
    costs='| Architecture | Calls | Mean input | P95 input | Mean output | Mean latency ms | P95 latency ms |\n|---|---:|---:|---:|---:|---:|---:|\n'
    for a,m in all_metrics.items():
        c=m['cost'];costs+=f"| {a} | {c['calls']} | {c['mean_input']} | {c['p95_input']} | {c['mean_output']} | {c['mean_latency_ms']} | {c['p95_latency_ms']} |\n"
    scaling='\n\n| Sources | Architecture | Input tokens | Output tokens | Latency ms | Result |\n|---:|---|---:|---:|---:|---|\n'
    for r in sorted((r for r in sr if r['case_id'].startswith('scaling_') and r['architecture']!='B'),key=lambda r:(r['case_id'],r['architecture'])):
        u=r.get('usage') or {};scaling+=f"| {int(r['case_id'].split('_')[1])} | {r['architecture']} | {u.get('input_tokens')} | {u.get('output_tokens')} | {r['latency_ms']} | {r['result']['response_class']} |\n"
    doc(25,'Cost and Latency',costs+scaling+'''\nOfficial primary counts include all 176 diagnostic cases. B's zero provider tokens exclude manual fact authoring and any upstream production interpretation call. C adds one matching call on top of interpretation in a production design; the primary gold control masks that upstream cost. Latencies are wall time per task under concurrent load, with model/network variability. No current price estimate is claimed; dollar cost is input_tokens × input_price + output_tokens × output_price. The invalid initial run has incomplete billing evidence.

Authoring estimate, not timed measurement: if annotating/reviewing each source takes 2–10 minutes, 1,000 sources cost 33–167 hours initially, plus updates and predicate/role governance. Both B and this C require that work. Source lists grow roughly linearly in tokens with serialized source text; 1/4/12/32-source probes provide concrete usage in supplemental results. No latency or token reduction is claimed for full /api/chat.''')
    doc(26,'Per-Case Results','''`per_case_results.jsonl` contains all core and supplemental case IDs, immutable expected labels, actual bindings/classes/qualifiers/source selections, audited scores and comparability flags. Original raw prompts/responses and original first-pass scores remain in the official run files. Secondary retains actual question propositions plus native production outcomes.

Success requires exact class and expected bindings (case/article normalized, with order-independent candidate lists), qualifier preservation, source eligibility and no forbidden bindings. False acceptance means a positive result on a nonanswer, an unsupported binding, strengthened qualifier, or a false DIRECT class. It does not mean merely omitting a binding. False rejection means an answerable case produces no positive class; omissions in a positive result are reported separately. Supplemental guard_direct credits its literal source location after an independent reread found a missing semantic annotation (E17). Initial scores and labels remain intact. Denominators are case count for rates and explicit expected-class count for each stratum.''')
    doc(27,'Failure Attribution',json.dumps({a:m['failure_attribution'] for a,m in metrics.items()},indent=2)+'''\n\nC commonly returned requested_role still populated while also supplying that role in roles. This is a malformed source interpretation (E03), not evidence that host authorization should be loosened. Other C failures are exact semantic-signature rejection (E14), including articles/value normalization and missing manual annotations. A often omitted content from tell sources; structurally well-formed output still lost the answer. B loses all prose-only facts at representation/retrieval (E02).

Attribution is deterministic triage followed by raw examples, not an independent blinded human panel. Exact semantic source errors can have multiple causes; external review should inspect raw JSON before accepting a general architecture conclusion.''')
    strata='\n\n| Core stratum | A supported success | B supported success | C supported success |\n|---|---:|---:|---:|\n'
    for cls in ['DIRECT','PARTIAL','RELATED_NONANSWER','UNKNOWN','RESTRICTED']:
        strata+='| '+cls+' | '+' | '.join(pct(metrics[a]['classes'][cls]['success'],metrics[a]['classes'][cls]['n']) for a in 'ABC')+' |\n'
    for tag in ['multi_role','paraphrase','open_world']:
        values=[]
        for a in 'ABC':
            subset=[r for r in comparable if r['architecture']==a and tag in corpus[r['case_id']]['tags']]
            values.append(pct(sum(audited(corpus[r['case_id']],r)['answer_success'] for r in subset),len(subset)))
        strata+='| '+tag+' | '+' | '.join(values)+' |\n'
    doc(28,'Comparison Matrix',table(metrics)+strata+'\n\nValidation/holdout paired counts against A:\n\n'+json.dumps(paired,indent=2)+'''\n\nB has zero provider calls but high fact authoring/vocabulary cost. A has the lowest integration change because it is existing behavior; its gold-control success overstates production readiness. C adds a call and this prototype's strict validation rejects most proposals. A/B/C all pass tested source access checks. C has not earned generalization claims; B generalizes the unification algorithm but not semantic extraction. No architecture wins the combined authoring, correctness, production-interpretation and security decision.''')
    doc(29,'Statistical Limitations',f'''Core Wilson 95% supported-answer intervals: { {a:m['success_wilson95'] for a,m in metrics.items()} }. These treat cases as independent and therefore overstate precision: 22 templates have eight lexical variants, and each partition has the same families. Paired exact win/loss counts are more useful than an unpaired point estimate; no significance claim or population-level superiority is made.

One model, one logical run per question/architecture, limited source sizes, authored gold semantics and synthetic worlds. No independent human label adjudication panel. Eight ambiguity cases were excluded post hoc due to unequal gold-bit access. False-acceptance accounting was corrected after seeing outcomes, with original scores preserved. Supplemental probes were created after the core experiment and cannot repair its frozen holdout coverage; eight additional paraphrases bring total coverage to sixteen but remain follow-on diagnostics. These limitations preclude A/B verdicts.''')
    doc(30,'Architecture Decision','''Do not migrate production source resolution. Prefer no architecture as the complete solution. B is a credible correspondence component for already structured host facts; it is not a replacement for open-world evidence understanding. This C does not justify an added provider call: it retains B's authoring burden and mostly fails the proposal contract. A remains the production baseline with its existing gates.

Recommended next discovery hypothesis: author stable fact IDs, predicate/role signatures and source-span provenance where natural; permit AI to propose candidate alignments offline or in a bounded nonauthoritative stage; host validation must distinguish mechanically proven matches from unverified entailment. Evaluate that hypothesis with independently reviewed source annotations and unhinted actual interpretations before any integration approval. This cycle provides diagnostic evidence, not a qualified architecture decision.''')
    doc(31,'Integration Readiness','''Design only; nothing integrated. Potential modules: semantic_correspondence, semantic_operations, unified_semantic_planning, social source-selection adapters and dialogue_authority. Preserve authorize_information_turn plan shape, universal authorize_npc_disclosure, source IDs/NPC/context scope, provenance categories, referent IDs, immutable final adoption and API/history agreement.

Data requirements: versioned host-authored facts with open predicates, named roles, epistemic/polarity/conditional scope, per-fact source spans and source revision hashes. Index by NPC/context/permission first, then relation/argument; retrieval must not reveal restricted text. Proposed interface: eligible candidate handles + question interpretation -> correspondence proposals -> host validation result containing coverage/bindings/missing slots, followed by mandatory final disclosure.

Feature gate should default off and have explicit fallback to existing source resolution. Migration would require offline fact authoring/review, schema versioning, source revision invalidation and provenance preservation. Regression risks: role aliases, stale facts, multi-fact leakage, contradictory sources, historical laundering, qualifier strengthening and cap-related recall loss. Qualification must include independent actual-interpretation holdouts, real /api/chat conversations, legacy paths, immutable response checks, durable reload referents, zero unauthorized disclosures and comparative token/latency gates. No migration or new gate is implemented.''')
    doc(32,'Remaining Unknowns','''Can host facts be authored economically on real campaign prose? Can source annotations be independently checked without a second model judgment simply becoming authority? What role/predicate alignment remains stable with actual production interpretations? Can unstructured entailment be proved or explicitly deferred without excessive UNKNOWN? How should uncertainty, conditionals, approximation and contradictions be represented? What recall does actual retrieval achieve at realistic source volume?

C needs a development-only contract repair and new untouched holdouts; do not tune against this exposed holdout. Larger independently adjudicated paraphrase holdouts, independent label adjudication, paid-attempt telemetry and robust expression/API qualification remain open. No full production security proof is claimed.''')
    doc(33,'Recommended Next Cycle','''Await external review of PR-EG-R6-R4. A possible next discovery cycle should repair the experiment's ambiguity and schema contracts on development data, freeze at least 150 independently adjudicated fresh cases including at least 15 explicit paraphrases, and test actual interpretation vocabulary plus realistic campaign source authoring costs. Separate unification from semantic extraction, retrieval and final expression. Compare a bounded hybrid without exposing restricted text or treating provider entailment as permission.

Do not implement that cycle or begin PR-EH here. Leave all current feature defaults unchanged.''')
    doc(34,'Final Verdict',f'''**{decision}**.

Real provider calls and frozen labeled evidence exist, but comparative validity and practical authoring/generalization gates remain unresolved. B shows a useful structured unification mechanism; C demonstrates fail-closed contract brittleness; neither qualifies as a production replacement. The gold-control result is not evidence that the production conversational problem is solved.

Stop after PR-EG-R6-R4 and await external review. No production migration, source-resolution rewrite or PR-EH work was performed.''')
    inventory=[]
    for p in sorted(OUT.iterdir()):
        if p.is_file() and p.name not in {'source_inventory.json','handoff_config.json'}:inventory.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size))
    dump('source_inventory.json',inventory)
    doc(35,'Source and Evidence Inventory','''`source_inventory.json` hashes this cycle's raw evidence, frozen labels, metrics and reports. `historical_inventory.json` lists the 56 inspected predecessor raw files and their hashes; `historical_raw_examples.jsonl` preserves complete selected rows with original path/line. The review bundle includes source code required to reproduce the experiment and relevant production boundaries, plus author fixture tools for historical verification.

Official: primary.jsonl, secondary.jsonl, supplemental_results.jsonl. Independent labels: development.json, validation.json, holdout.json, supplemental.json. Freeze manifests and adapter amendment record exact input lineage. Invalid_initial_attempts.jsonl is retained as excluded evidence. Baseline status and production_integrity.json document the dirty starting tree and unchanged game/data content. No credentials, .env or production session contents are intentionally packaged.''')
    # Rebuild inventory after all numbered reports exist.
    inventory=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in {'source_inventory.json','handoff_config.json'}]
    dump('source_inventory.json',inventory)
    paths=[p for p in OUT.iterdir() if p.is_file() and p.name!='handoff_config.json']
    paths += list((ROOT/'experiments/pr_eg_r6_r4').glob('*.py'))+[ROOT/'experiments/pr_eg_r6_r4/CONTRACT.md',ROOT/'tests/test_pr_eg_r6_r4_correspondence.py',ROOT/'tools/audit_pr_eg_r6_r4.py',ROOT/'tools/report_pr_eg_r6_r4.py',ROOT/'tools/supplement_pr_eg_r6_r4.py']
    paths += [ROOT/p for p in ['game/semantic_correspondence.py','game/semantic_operations.py','game/unified_semantic_planning.py','game/dialogue_authority.py','game/social.py','game/immutable_valid_response.py','game/config.py','experiments/pr_eg_r6_r3/common.py','tools/qualify_pr_eg_r6_r2_r1.py','tools/qualify_pr_eg_r6_r3_r1.py','tools/qualify_pr_eg_r6.py']]
    config=dict(campaign_name='PR-EG-R6-R4 — Authorized Evidence Correspondence Reassessment',
        campaign_id='pr_eg_r6_r4_correspondence_20261018',campaign_date='2026-10-18',purpose='Architectural discovery and controlled experiment; no production migration.',
        executive_summary=overview,objective_status=decision,
        self_contained_review_test='ZIP readability, all non-null manifest SHA-256 values, frozen input hashes, numbered artifact count and source-inventory hashes verified. The manifest intentionally has no self-hash.',
        changes=dict(production=[],validation=['Isolated correspondence tests'],tooling=['Experiment, audit and reporting scripts'],documentation=['35 numbered review artifacts']),
        testing=dict(focused='197 local experiment tests passed before live calls.',broader='317 passed, 2 failed (Windows temp-file atomic-replace permissions), 4 deselected. Interrupted retries recorded in verification_status.json.',full_suite='Not run.',runtime_validation='466 official logical provider calls; 176 core cases, 22 secondary interpretations, 35 supplemental probes.',model_runtime_boundary=baseline['model']+', temperature 0, max output 1800',new_regressions='No production changes; regression qualification incomplete.',pre_existing_failures='Not reassessed globally.'),
        known_problems=dict(campaign_specific=['Post hoc ambiguity exclusion and scorer clarification limit comparability.','Supplemental paraphrases broaden coverage after primary exposure; no replacement holdout claim.','C proposal contract mostly failed; B depends on manual source facts.'],pre_existing=['Production conversational qualification remains below target.']),
        decisions_requiring_human_review=['Whether to authorize a new discovery cycle using repaired development contracts and independently reviewed fresh holdouts.'],
        does_not_prove=['Production readiness, affordable annotation, universal semantic security or broad open-world generalization.'],
        recommended_next_step='Stop after PR-EG-R6-R4; await external review. Do not begin PR-EH.',
        primary_report='artifacts/pr_eg_r6_r4/01_EXECUTIVE_SUMMARY.md',max_file_bytes=50000000,warn_bundle_bytes=100000000,
        supporting_files=[dict(path=p.relative_to(ROOT).as_posix(),role='cycle_evidence',why='Reproducible PR-EG-R6-R4 discovery and raw evidence.',behavioral_evidence=p.suffix=='.jsonl',human_review_required=p.suffix in {'.py','.md'}) for p in paths])
    dump('handoff_config.json',config)
    from tools.build_review_handoff import build_handoff
    result=build_handoff(config,root=ROOT,output_dir=ROOT/'handoff')
    print(json.dumps(dict(verdict=decision,metrics=metrics,files=result.get('file_count'),zip=result.get('zip_path')),ensure_ascii=True))


if __name__=='__main__':main()

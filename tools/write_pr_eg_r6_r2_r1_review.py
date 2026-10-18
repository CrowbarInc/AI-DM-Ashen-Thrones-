"""Build the forty requested review artifacts and repository CURRENT_REVIEW."""
from __future__ import annotations
import difflib
import hashlib
import json
import math
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));OUT=ROOT/'artifacts/pr_eg_r6_r2_r1'
TITLES=['Executive Summary','Baseline and Repository State','Failure Reproduction','Conversational State Inventory',
    'Durable Referent Contract','Referent Identity','Referent Lifecycle','Active Question Tracking',
    'Correction Operations','Correction Lineage','Correction Examples','Follow-Up Binding','Follow-Up Semantics',
    'Follow-Up After Uncertainty','Follow-Up After Partial Answer','Multiple Referent Resolution',
    'Speaker and Addressee Continuity','Clarification Discipline','Provider Input Contract','Provider Output Contract',
    'Host Validation','Transactional Referent Updates','Save Load Integrity','Retention and Compaction',
    'Response Planning','Legacy Path Isolation','Integrity Preservation','Controlled Tests','Frozen Holdouts',
    'Matched Baseline Comparison','Fresh-Provider Conversations','Turn-Level Qualification',
    'Dialogue Quality and Playability','Performance','Regression Comparison','Acceptance Gates',
    'Remaining Limitations','Recommended Next Action','Final Verdict','Source and Evidence Inventory']


def load(name):return json.loads((OUT/name).read_text())
def rows(name):return [json.loads(l) for l in (OUT/name).read_text().splitlines() if l.strip()]
def write(name,value):
    (OUT/name).write_text(value if isinstance(value,str) else json.dumps(value,indent=2,default=str),encoding='utf-8')
def ref(path,symbol=''):
    p=ROOT/path;lines=p.read_text(encoding='utf-8-sig').splitlines() if symbol else []
    n=next((i for i,l in enumerate(lines,1) if symbol and symbol in l),1)
    return f'[{path}:{n}](<{p.as_posix()}:{n}>)'
def evidence(path):return ref('artifacts/pr_eg_r6_r2_r1/'+path)
def distribution(values):
    return {'mean':statistics.mean(values),'p95':sorted(values)[max(0,math.ceil(.95*len(values))-1)],'maximum':max(values)} if values else None
def junit(name):
    return {c.get('classname')+'::'+c.get('name'):not any(x.tag in {'failure','error'} for x in c) for c in ET.parse(OUT/name).iter('testcase')}
def example(row):
    return {'conversation':row['conversation'],'turn':row['turn'],'player':row['player'],'speech':row['text'],
        'plan':row['plan'],'checks':row['checks']}


def main():
    live=rows('final/live_turns.jsonl');baseline=rows('baseline/live_turns.jsonl');supp=rows('predecessor_holdouts/live_turns.jsonl')
    metrics=load('quality_metrics.json');scores=load('turn_scores.json')['final']
    restart=load('restart/result.json');status=load('final/live_status.json');supp_status=load('predecessor_holdouts/live_status.json')
    before=junit('baseline_junit.xml');after=junit('regression_junit.xml')
    tests={'baseline_passed':sum(before.values()),'baseline_failed':len(before)-sum(before.values()),
        'final_passed':sum(after.values()),'final_failed':len(after)-sum(after.values()),'added_cases':len(set(after)-set(before)),
        'inherited_failures':[k for k,v in after.items() if not v and k in before and not before[k]],
        'new_failures':[k for k,v in after.items() if not v and before.get(k,True)],
        'baseline_failures_now_passing':[k for k,v in before.items() if not v and after.get(k)]}
    write('regression_comparison.json',tests)
    def performance(rs):
        calls=[c for r in rs for c in r['provider_calls']]
        return {'turns':len(rs),'conversations':len({r['conversation'] for r in rs}),'calls':len(calls),'calls_per_turn':len(calls)/len(rs),
            'input_tokens_per_turn':distribution([sum(c.get('input_tokens') or 0 for c in r['provider_calls']) for r in rs]),
            'output_tokens_per_turn':distribution([sum(c.get('output_tokens') or 0 for c in r['provider_calls']) for r in rs]),
            'latency_ms':distribution([r['latency_ms'] for r in rs]),
            'retry_calls':sum('retry' in str(c.get('purpose','')).lower() for c in calls),
            'unknown_input_usage_calls':sum(c.get('input_tokens') is None for c in calls),
            'unknown_output_usage_calls':sum(c.get('output_tokens') is None for c in calls),
            'total_input_tokens':sum(c.get('input_tokens') or 0 for c in calls),
            'total_output_tokens':sum(c.get('output_tokens') or 0 for c in calls),
            'models':sorted({str(c.get('model')) for c in calls}),
            'calls_by_purpose':{p:sum(c.get('purpose')==p for c in calls) for p in sorted({str(c.get('purpose')) for c in calls})}}
    perf={'primary':performance(live),'matched_baseline':performance(baseline),'matched_final':performance(live[:30]),
          'predecessor_holdouts':performance(supp),'note':'Per-turn engine usage. Pilots, development, and offline tests excluded. Missing usage is counted explicitly, not asserted to be zero. No currency estimate.'}
    write('performance.json',perf)
    integrity={key:sum(not r['checks'][key] for r in live+supp) for key in live[0]['checks']}
    integrity.update(primary_turns=len(live),supplement_turns=len(supp),restart_checks=restart['checks'],
        limitations='Canonical check compares the predecessor selected NPC/topic/faction/location/HP/combat projection, not arbitrary whole-state equality. Clue check detects fixture protected values, supplemented by unchanged disclosure/provenance regression tests. These finite observations do not prove unrestricted semantic entailment or all possible unauthorized discoveries.')
    write('integrity_results.json',integrity)
    frozen=load('freeze.json');actual={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in frozen}
    freeze_ok=actual==frozen
    holdout_rows=[r for r in live+supp if r['source'].startswith('frozen')]
    label_rows=[]
    for r in holdout_rows:
        expect=r['expect'];want=expect.get('sufficiency')
        label_rows.append({'conversation':r['conversation'],'turn':r['turn'],'holdout_id':expect.get('holdout_id') or expect.get('case'),
            'player':r['player'],'expected':expect,'actual_kind':r['plan'].get('response_kind'),'speech':r['text'],
            'exact_sufficiency_label':r['plan'].get('response_kind')==want if want else None,
            'padding':r['conversation'].startswith('original_holdouts') and r['turn']>=7})
    new_scores=[s for s in scores if s['conversation'].startswith('new_holdouts')]
    from tools.assess_pr_eg_r6_r2_r1 import summarize
    holdouts={'unchanged':freeze_ok,'hashes':actual,'new_conversation_metrics':summarize(new_scores),'rows':label_rows,
        'limitations':'All original R6 and all twelve R6-R2 frozen cases were run without editing their JSON. New H01-H10 were authored and frozen before implementation, by this implementing agent, not an external author. H09 has forgery metadata but no adversarial utterance; that holdout alone does not test forgery. Controlled forgery tests supply that evidence. H04 was intended to cover partial answers, but its live source was sometimes overstated as direct; controlled partial tests and other live partial turns cover the boundary. Eighteen repeated original-harness padding turns are flagged and do not count as new cases. No production changes after the final run began.'}
    write('holdout_results.json',holdouts)
    pairs=[]
    for ident,turn in [('A',2),('B',5),('C',7),('D',8)]:
        pairs.append({'case':ident,'baseline':example(baseline[turn-1]),'final':example(live[turn-1])})
    write('failure_reproduction.json',pairs)
    sample_ids={'successful_correction':('continuity_0',2),'failed_correction':('continuity_1',2),
        'successful_follow_up':('continuity_0',5),'failed_follow_up':('continuity_0',3),
        'genuine_clarification':('continuity_0',13),'false_clarification':('continuity_2',5),
        'semantic_wrong_answer':('original_holdouts_0',6)}
    examples={name:example(next(r for r in live if (r['conversation'],r['turn'])==key)) for name,key in sample_ids.items()}
    write('raw_examples.json',examples)
    primary=metrics['primary'];gates=[]
    def gate(number,name,result,evidence_text):gates.append({'gate':number,'name':name,'status':result,'evidence':evidence_text})
    gate(1,'Referent identity','PASS','Stable host conversation UUID + monotonic sequence; 47 controlled tests and persisted records.')
    for n,name,key,target in [(2,'Active focus','active_focus',.95),(3,'Corrections','correction',.9),(4,'Follow-ups','follow_up',.9),(5,'Referent binding','referent_binding',.95)]:
        m=primary[key];gate(n,name,'PASS' if m['rate']>=target else 'FAIL',f"{m['count']}/{m['denominator']} = {m['rate']:.1%}; local audit; target {target:.0%}.")
    m=primary['false_clarification'];gate(6,'False clarification','PASS' if m['rate']<=.1 else 'FAIL',f"{m['count']}/{m['denominator']} = {m['rate']:.1%}; target <=10%.")
    gate(7,'Answer relevance','PASS','Matched sequence: 14/30 to 25/30 in local audit; identical initial fixtures, later histories diverge. One sample, not causal proof.')
    gate(8,'Answer sufficiency','LIMITED','Matched locally scored sufficiency improves 14/30 to 23/30, but three intended partial answers were overstated as direct; no broad nonregression claim.')
    gate(9,'Save/load','PASS',f"Disk reloads, controlled persistence and separate-process correction: {restart['checks']}.")
    for n,name,key in [(10,'Disclosure','no_secret'),(11,'Canonical state','canonical'),(12,'Discovery','no_secret_clue'),(13,'Final delivery','sealed')]:
        gate(n,name,'PASS (MEASURED SCOPE)' if integrity[key]==0 else 'FAIL',f"{integrity[key]} failed observed checks across {len(live)+len(supp)} turns; finite coverage limits in integrity_results.json.")
    gate(14,'Regression','PASS' if not tests['new_failures'] else 'FAIL',f"{tests['final_passed']} passed, {tests['final_failed']} inherited failed, {len(tests['new_failures'])} new failures.")
    gate(15,'Holdouts','FAIL','Hashes unchanged and evaluated, but failed role reversal, source interpretation and original correction cases do not support qualification.')
    p=perf['primary'];pass_perf=p['input_tokens_per_turn']['mean']<=3500 and p['input_tokens_per_turn']['p95']<=5000 and p['latency_ms']['p95']<=5000
    gate(16,'Performance','PASS' if pass_perf else 'FAIL',f"Mean input {p['input_tokens_per_turn']['mean']:.1f}, P95 input {p['input_tokens_per_turn']['p95']}; P95 latency {p['latency_ms']['p95']:.1f} ms; one strict_social context outlier.")
    gate(17,'Fresh provider','PASS',f"120 turns / 8 primary groups, plus {len(supp)} predecessor-holdout turns / 2 groups and one restarted-process turn; source hashes unchanged.")
    write('acceptance_gates.json',gates)
    verdict='C — REFERENT CONTINUITY BELOW ACCEPTANCE'
    summary=(f'{verdict}. Implemented bounded host-owned question IDs, correction deltas, lineage, active focus, persisted answer statuses and post-seal commits under the existing default-off gate. '
        f"Final regressions: {tests['final_passed']} passed, {tests['final_failed']} inherited failed, no new failures. Primary fresh-provider qualification: 120 turns / 8 groups; corrections 7/13, follow-ups 18/28, false clarifications 22/120. "
        f"Additional unchanged predecessor holdouts: {len(supp)} turns / 2 groups. Separate-process save/load correction passed. Observed integrity checks passed within their documented scope. Acceptance thresholds remain unmet.")
    write('verdict.json',{'verdict':verdict,'summary':summary,'gates':gates})
    r=ref('game/conversational_referents.py','def bind');c=ref('game/conversational_referents.py','def commit');u=ref('game/unified_semantic_planning.py','def authorize_information_turn')
    inv=[
        ('Questions and plans','game/unified_semantic_planning.py','def prior_semantic_plan','Before: latest delivered plan, with question text/relationship but no question identity. Now active referent first; bounded legacy history fallback remains for old saves.'),
        ('Delivered dialogue','game/conversational_continuity.py','def record_delivered_exchange','Existing bounded delivered_exchanges (32 rows), exact speech, turn and sealed response digest. New referent ID links the question without duplicating authorized speech.'),
        ('Discourse slots','game/discourse_state.py','DISCOURSE_FOCUS_KEY','Stable active interlocutor/claim/lead/action slots exist, but represent other responsibilities; no correction lineage or missing question argument.'),
        ('Commitments','game/dialogue_authority.py','COMMITMENT_KEY','NPC speech commitments and their epistemics remain separately owned; referents create no promises.'),
        ('Historical propositions','game/expressive_dialogue.py','def proposition_identity','Existing proposition identity describes authorized speech/content. A player question needs independent identity even when no answer exists.'),
        ('History permission','game/dialogue_authority.py','def historical_disclosure_permitted','Verified speech remains subject to disclosure checks; referent existence is not a truth or permission record.'),
        ('Clarification routing','game/conversational_orchestration.py','class ConversationalDecision','Existing CLARIFY/EXECUTE decisions and pending context remain. New accepted unresolved questions carry clarification answer_status; malformed proposals preserve previous focus.'),
        ('Topic focus','game/prompt_context.py','def _memory_window_focus_topic_tokens','Existing lexical/topic anchors support legacy prompting. They cannot replace an accepted unified referent.'),
        ('Entity roles','game/semantic_correspondence.py','def proposition_schema','Existing binary proposition/evidence schema is reused, not a second world or source fact store.'),
        ('Persistence','game/storage.py','def load_session','Session persistence envelopes already preserve conversational_context; no separate save format or migration engine needed.'),
        ('New question memory','game/conversational_referents.py','KEY =','Separate compact index holds intent metadata and links existing delivery identity/digest; necessary because unknown speech is not a stable question.')]
    write('state_inventory.json',[{'area':a,'source':f,'symbol':s,'finding':v} for a,f,s,v in inv])
    inventory_md='| Area | Source | Existing structure and repair |\n|---|---|---|\n'+'\n'.join(f'| {a} | {ref(f,s)} | {v} |' for a,f,s,v in inv)
    sections={
      1:summary,
      2:f"Captured dirty-worktree inventory and HEAD before edits: {evidence('repository_status.txt')}, {evidence('baseline_head.txt')}. Existing user changes were retained. Pre-edit sources for planning, continuity and semantic correspondence are in baseline_sources/. Prior CURRENT_REVIEW files were copied to handoff/history/pr_eg_r6_r2_before_durable_referents. Baseline provider run used the preserved planning module and unmodified pre-edit continuity already imported before edits. Baseline 30 turns and selected regressions completed before final qualification. The initial sandbox processes stalled at asyncio.socketpair and were stopped after successful outside-sandbox replacements completed.",
      3:f"Exact four requested reproductions and final matched observations: {evidence('failure_reproduction.json')}. A: baseline generic clarification, final copper keeper answer. B: baseline generic clarification, final bound uncertainty after the aqueduct-name unknown. C: baseline generic clarification, final keeper-of north-road uncertainty, preserving the prior predicate. D: baseline generic clarification, final Mara answers Oren's road statement. Raw routing, provider proposals, authorization provenance and delivery are retained in both transcripts; later sequence histories necessarily diverge.",
      4:inventory_md,
      5:f"Stored at session.conversational_context.question_referents, version 1. Fields: referent_id, conversation_id, originating_turn_id, delivery_id, parent_referent_id, revision, corrected_fields, addressee_id, mentioned_entity_ids, requested_subject, requested_relationship, reused request_proposition (predicate/agent/patient/missing slot/qualifiers/negation/epistemics), witness_text, answer_status, epistemic_status, correction_status, focus_status, follow_up_relationship, proposition_referent_id, source_plan_id, provenance=host_interpretation, canonical=false. Witness text is bounded inherited evidence, not delivered speech or new source prose. See {c}.",
      6:f"The host mints a UUID conversation scope at first sealed commit and monotonically increments a persisted sequence. IDs survive disk/process restart and are not derived from speech. Provider target IDs must resolve to existing scoped records. Provider cannot create an ID; new question IDs appear only in commit, then are linked into delivered history. Repeated delivery identity is idempotent. {c}; {evidence('restart/result.json')}.",
      7:"Lifecycle uses three axes: answer_status=direct/partial/unknown/refusal/clarification; focus_status=active/superseded/archived; correction_status=original/revision/corrected. Accepted sealed new question creates active/original. New focus supersedes prior active. Correction creates active/revision with incremented revision and marks parent corrected/superseded. Ordinary follow-up creates archived/original linked to its proposition while retaining active original focus. Rejected interpretations do not transition referents. Retention removes old records beyond the cap; their stable IDs can remain in bounded lineage links but unavailable records cannot be resolved. Temporal follow-up focus and multiple pending clarifications need stronger lifecycle semantics before acceptance.",
      8:f"prior_semantic_plan reads active question memory before delivered-history fallback. Unknown/partial answers retain the question's predicate and missing argument. Rejected corrections cannot overwrite active focus. Local semantic-focus measure: {primary['active_focus']}; it penalizes failed correction/new-question acquisition in addition to loss of a stored focus. Pure storage preservation alone would overstate continuity. {ref('game/unified_semantic_planning.py','def prior_semantic_plan')}.",
      9:f"Bounded operations: replace_subject, replace_object, replace_relationship, replace_qualifier, replace_roles, replace_addressee, clarify_argument, reject_interpretation. Each has an allowed field set; host starts from the original proposition and applies only listed changed slots. Nonempty unlisted changes fail closed. Changed entity evidence must be current literal input, inherited unchanged evidence stays bound to the parent. No new phrase replacement rules were added. {r}.",
      10:f"A correction creates a new immutable intent interpretation, parent ID, revision increment, changed-field list and originating turn/delivery identity. Earlier intent proposition and delivered player/NPC text remain intact. Only lifecycle flags on historical referent records change; the existing delivered history active flag also changes as before. {c}; {ref('tests/test_pr_eg_r6_r2_r1_referents.py','def test_object_correction')}.",
      11:f"Success and failure must both be reviewed: {evidence('raw_examples.json')}. Copper object replacement succeeds. A relationship-only correction fails when the provider proposes pronoun 'it' as an unlisted object change. A role reversal fails when the provider requests replace_subject while also changing object. Original H05 accepts an incoherent interpretation that fills a missing subject while retaining the old drum-name predicate, then supplies the wrong public drum statement. This is a serious semantic-validation failure, not a legacy-selector override or protected disclosure.",
      12:f"Follow-ups target an existing host question, preserving a proposition reference. Unknown target IDs/cross-conversation IDs fail closed. A qualified historical target requires argument evidence; otherwise the host retains active focus rather than trusting a provider's stale but valid ID. Explicit speaker changes need a grounded addressee correction. {r}. Binding is stronger than history-text equality but semantic operation errors remain; full metrics in {evidence('quality_metrics.json')}.",
      13:"Follow-up relations distinguish source_attribution, explanation, evidence, temporal_modification, alternative_argument and speech_clarification. Host projects attribution/evidence/explanation arguments from the targeted proposition; redundant proposed subject/object slots cannot redirect it to another entity. Temporal/alternative deltas require current literal evidence. Speech clarification inherits the proposition. Requested predicate interpretation still depends on the provider; an explanation classified with the old keeper predicate can remain semantically wrong despite a valid ID.",
      14:f"When a bound unknown/refusal is followed by attribution/explanation/evidence/speech clarification, host emits bounded uncertainty and selects no new source. No informant is invented. Active original question remains addressable. Provider expression may phrase this as 'I don't know who told me'; this is safe but less clear than the host line explaining the earlier lack of knowledge. {ref('game/unified_semantic_planning.py',"follow in {'source_attribution'")}; {evidence('raw_examples.json')}.",
      15:"A partial answer_status is retained with the original missing argument rather than replacing the question with its answer text. Controlled partial/evidence tests and the three HTTP persistence variants pass. Live qualification exposes a limitation: 'Someone keeps the roster' was promoted to direct in three turns by source interpretation. Other turns correctly remained partial. The index stores the host plan's answer status faithfully but cannot repair an incorrectly accepted sufficiency classification by itself.",
      16:f"Recent referents are bounded; active focus is always included even if many archived follow-ups displace it from the last six. Target existence, session scope, corrected-parent eligibility and current NPC presence are checked. Recency is mediated by active focus and explicit argument evidence, not the last spoken line. Ambiguity is still often expressed generically as 'Which earlier question do you mean?' and overlapping historical subjects are not fully disambiguated. {ref('game/conversational_referents.py','def context')}; {r}.",
      17:f"Leading vocatives ground addressees; interior names remain mentioned entities. On corrections/follow-ups without a direct vocative, current mentions cannot steal addressee ownership. Speaker/addressee role proposals are ignored in the durable contract and host-projected; consequential request/source roles remain validated. Missing/absent or mismatched NPC targets are rejected. A correction's mentioned_entity_ids list currently reflects the new utterance while proposition slots preserve inherited participants; richer inherited role metadata remains a limitation. {u}.",
      18:f"Host checks durable target/focus before clarification and retains prior focus on malformed/rejected proposals. Meaning-known/answer-unknown takes safe uncertainty. Genuine shared Warden aliases clarify. Still, generic clarification remains on {primary['false_clarification']['count']}/120 turns, and two genuine ambiguities are poorly handled. No generic clarification is counted as conversational success merely because it is safe. {evidence('turn_scores.json')}.",
      19:f"One provider plan call receives current utterance, visible participant roster, bounded scene summary, four delivered speech references, active/recent question IDs and compact semantic fields/statuses, plus up to twelve currently permitted source candidates. No denied topic text is added to resolve referents; referent context holds player intent, not protected world records. Six recent questions plus pinned focus can still contribute substantial context, and a downstream strict_social outlier consumed 29,885 additional input tokens. {ref('game/unified_semantic_planning.py','def _provider_context')}.",
      20:f"Extended strict output schema retains request/source propositions and adds referent_operation (target ID, bounded operation, changed field names, follow-up relation). conversational_act accepts information_question/correction/follow_up/clarification_response; unrelated utterances use the existing out-of-family path rather than gaining referent authority. Predicate/missing-slot schema constraints and host validation reject malformed output. No extra provider call maintains state. {ref('game/unified_semantic_planning.py','def _proposal_schema')}; {ref('game/conversational_referents.py','def operation_schema')}.",
      21:f"Host checks scoped target existence, corrected-target eligibility, NPC presence, explicit speaker continuity, operation/field compatibility, changed evidence, role IDs, request witnesses, source IDs, source epistemics, disclosure and semantic correspondence. Forgery cannot create state or grant facts. Residual semantic validation defects remain: binary relations incompletely represent speech recipient/topic/content roles; filling the requested missing slot is not always rejected; qualifier/negation entailment remains inherited. The report does not equate structural validation with complete linguistic correctness. {r}; {u}.",
      22:f"Planning/authorization are read-only against session/world. A proposal is staged for delivery; record_delivered_exchange verifies the immutable adoption, exact speech and speaker before attaching the plan. After duplicate-history detection, the new record is appended, then commit constructs a copied question index and assigns it into the same session document. No referent commit occurs without a valid seal, on terminal disclosure denial/safe fallback, or with the feature gate off. History and index persist together through the existing atomic session envelope. No new cross-document database transaction is claimed. {ref('game/conversational_continuity.py','def record_delivered_exchange')}; {c}.",
      23:f"Existing session persistence preserves arbitrary conversational_context keys in its integrity envelope. No reconstruction of world facts from speech occurs. Legacy saves remain loadable and use bounded prior delivered-plan fallback until a new host referent is committed; old metadata without a proposition can require clarification. Controlled storage roundtrip passes; live requests reload from disk, explicit save/load markers pass, and a separate new process corrects saved copper to amber with parent/revision continuity. {ref('game/storage.py','def load_session')}; {evidence('restart/result.json')}.",
      24:f"At most 24 referent records; provider sees at most six including pinned active focus. Commit pins active record, newly committed record and its immediate parent, then removes older unpinned records. Sequence is not reused. Older lineage IDs survive as links but their records can be evicted; history beyond retention cannot be resolved. Multiple old pending clarification chains are not all pinned, so long historical/pending conversations need additional work. No canonical record is compacted. {ref('game/conversational_referents.py','MAX_RECORDS')}.",
      25:f"Corrected proposition projection derives from the accepted delta, then existing source correspondence and npc_source_permitted perform answer selection. Direct/partial/unknown/refusal/clarification remain distinct. Source selection supplies original authorized NPC topic text, preserving epistemics/provenance. A valid target never guarantees an answer. Speech clarification currently may return uncertainty even when the old line is known; verified_history authority remains intact in predecessor code but this module does not use referents as a shortcut to historical disclosure. {u}; {ref('game/semantic_correspondence.py','def coverage')}.",
      26:f"Existing ASHEN_UNIFIED_SEMANTIC_PLANNING defaults off. Accepted plans retain owner unified_semantic_plan through ASK resolution and consumed bindings; failed interpretation stays on a locked safe path. No new lexical correction patchwork or provider fallback call was added. Old fixture/legacy-save proposals retain compatibility behavior without the new operation field. Referent commit is also gated. One downstream strict_social generation call caused a cost outlier, but its delivered answer still matched the locked public source; no observed legacy reselection overrode an accepted corrected proposition. {ref('game/unified_semantic_planning.py','def planning_decision')}; {ref('game/unified_semantic_planning.py','def locked_plan_for_social_turn')}.",
      27:f"Disclosure/provenance/final-seal production modules were not changed. Existing tests cover world_source, host_operation, bounded_expression, verified_history, password rejection, clue restrictions and API/history identity. All {len(live)+len(supp)} observed qualification turns passed the stated integrity checks, with a separately sealed process-restart continuation. Selected canonical projection and fixture-secret checks have explicit finite limits; wrong public-topic selection is scored as semantic failure. {evidence('integrity_results.json')}; {ref('game/dialogue_authority.py','def npc_source_permitted')}; {ref('game/immutable_valid_response.py','def verify_delivery_record')}.",
      28:f"47 added controlled cases pass. Coverage groups: identity/uniqueness; unknown/partial/direct focus; object/subject/relationship/qualifier/role corrections and lineage; uncertainty/partial/temporal/alternative follow-ups; recency/history; speaker/addressee/mentions; forged/cross-session/stale/invalid/unwitnessed operations; no pre-seal commit; rollback and idempotence; retention; save/load; three HTTP correction sequences; default-off gate and frozen hashes. Predecessor tests cover the disclosure exploit, final seal, provenance classes, no canonical updates and no legacy answer substitution. These deterministic boundaries are not counted as fresh provider competence. {ref('tests/test_pr_eg_r6_r2_r1_referents.py')}; {evidence('regression_junit.xml')}.",
      29:f"Frozen hashes unchanged: {freeze_ok}. Primary run executes new H01-H10 plus original R6 cases; supplementary run executes all twelve R6-R2 cases. New groups are frozen pre-tuning, but not externally authored. Important limitations: {holdouts['limitations']} Results, original labels and local judgments remain separate in {evidence('holdout_results.json')}. No post-evaluation production repair or example-specific exceptions were applied.",
      30:f"Fresh matched baseline/final each use the first two 15-turn conversation groups with identical initial NPC/world/permission fixtures and player sequences. Later histories diverge naturally. Local matched corrections 0/4 to 2/4, follow-ups 0/10 to 7/10, false clarifications 16/30 to 4/30, relevance 14/30 to 25/30, sufficiency 14/30 to 23/30. A single sequence sample cannot separate model variability from host changes. Eight additional identical-input controlled cases (16 executions, including exact shared history/proposal hashes) isolate host behavior. {evidence('controlled_matched_comparison.json')}; {evidence('quality_metrics.json')}.",
      31:f"Primary final run: {len(live)} real-provider /api/chat turns across eight groups. Supplement: {len(supp)} across two groups. Restart: one more real-provider turn from a copied saved session in a new process. Primary and supplemental source hashes agree and remain unchanged. Configured model IDs are recorded in performance/usage, with no stub-provider turns counted. Original-holdout groups reset cast and context per independent frozen case, then include inherited repeated-question padding; these group counts do not imply eight long naturalistic unreset conversations. {evidence('final/live_status.json')}; {evidence('predecessor_holdouts/live_status.json')}.",
      32:f"Each final/supplemental turn stores player utterance, provider proposal when valid, target operation/ID, prior index, accepted plan, active focus, semantic arguments, selected source, authorization provenance, sealed API speech, exact history row, persisted index, clue-knowledge snapshots, provider calls/tokens and latency. Raw provider input/output lives in semantic_traces.jsonl, including malformed proposals omitted by schema validation. Baseline uses the predecessor runner's evidence schema; it has no durable index. All records are disposable synthetic state, not the user's active campaign. {evidence('final/live_turns.jsonl')}.",
      33:f"Local implementing-agent post-run audit, with explicit turn annotations and reproducible scoring code; not independent human adjudication. Primary quality/playability each {primary['quality_mean']:.3f}/3. False clarifications score zero; relevant safe uncertainty/adequate fact scores two; incomplete/unhelpful responses score one. No score of three is awarded as polished narrative quality was not established. Entity-role metrics evaluate the bounded binary representation; no unrestricted semantic-accuracy claim. Raw success/failure/ambiguity examples: {evidence('raw_examples.json')}. Scores were not used for implementation tuning.",
      34:json.dumps(perf,indent=2)+'\n\nTargets: mean input <=3,500; P95 input <=5,000; P95 latency <=5,000 ms. Input mean/P95 pass, primary latency P95 misses. Maximum input 33,411 occurs on continuity_2:12: 3,526 semantic-plan + 29,885 strict_social. No extra maintenance call or systemic retry loop is observed. This isolated inherited downstream path needs review, not concealment in mean values.',
      35:json.dumps(tests,indent=2)+'\n\nThe expanded pre-edit baseline has six failures; final five are inherited, none newly failed. One previously failing T19 test passes in the final selection; no targeted repair to that test was made and no broad fix is claimed. Full repository suite was not run; selection follows the requested R2C/R3/R3-R1/R4-R1/R6/R6-R1/provenance/R6-R2 stack plus answer selection.',
      36:'| Gate | Result | Evidence |\n|---|---|---|\n'+'\n'.join(f"| {g['gate']} — {g['name']} | {g['status']} | {g['evidence']} |" for g in gates),
      37:"Provider operation/role/source parsing still fails on genuine conversations. Relationship-only changes and role reversals miss. Original H05 produces a wrong public answer from an incoherent accepted correction. Unknown/new-question schema errors cause repeated false clarifications. Partial epistemics sometimes become direct. Binary proposition slots do not fully represent speaker/recipient/topic/content. Older pending lineages can be compacted; temporal follow-up focus needs stronger treatment. New referent mention lists are turn-local. Historical speech clarification is often unhelpful. Scope classification remains the existing gated information-candidate path, now considering unaddressed questions with active conversational context; non-information families have not been redesigned. Internally authored holdouts, single stochastic samples, repeated padding, finite state projections and no full-suite run limit the evidence. Gate must remain off by default.",
      38:"Stop after PR-EG-R6-R2-R1 and obtain external review. Review the host contract and failed raw cases before another bounded repair. Priorities for a separately authorized cycle: semantic coherence of changed/missing slots; reliable operation classification; multi-argument speech roles; targeted unresolved fields; intended partial answer statuses; historical/temporal focus and the downstream strict_social cost outlier. Use new unseen holdouts for any subsequent tuning. Do not begin PR-EH.",
      39:summary+'\n\nVerdict C is intentional: measured improvement, persisted identity and passing controlled tests do not satisfy the correction/follow-up/focus/clarification/holdout/performance thresholds. A/B is not justified. No critical authority breach was observed in the measured checks; finite evidence cannot certify universal safety.',
      40:f"Hashed implementation, preserved baseline, exact source diffs, tests, raw proposals/transcripts, holdout freezes, score audit and metrics are enumerated in evidence_inventory.json and the portable handoff REVIEW_MANIFEST.json. Original campaign data, credentials/.env, caches and disposable state directories are excluded from the review bundle. Source snapshots in baseline_sources preserve the actual dirty-worktree predecessor rather than substituting repository HEAD. Final production source hashes are recorded in both qualification statuses. {evidence('evidence_inventory.json')}.",
    }
    for i,title in enumerate(TITLES,1):
        name=f"{i:02}_{title.upper().replace(' ','_').replace('-','_')}.md"
        write(name,f'# {i:02} — {title}\n\n{sections[i]}\n')
    for f in ['game/unified_semantic_planning.py','game/conversational_continuity.py','game/semantic_correspondence.py']:
        old=(OUT/'baseline_sources'/f).read_text(encoding='utf-8');new=(ROOT/f).read_text(encoding='utf-8')
        write(Path(f).stem+'_changes.diff',''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='pre_edit/'+f,tofile='final/'+f)))
    write('conversational_referents_changes.diff',''.join(difflib.unified_diff([], (ROOT/'game/conversational_referents.py').read_text(encoding='utf-8').splitlines(True),fromfile='/dev/null',tofile='game/conversational_referents.py')))
    changes=['game/conversational_referents.py','game/unified_semantic_planning.py','game/conversational_continuity.py',
        'tests/test_pr_eg_r6_r2_r1_referents.py','tools/qualify_pr_eg_r6_r2_r1.py','tools/compare_pr_eg_r6_r2_r1.py',
        'tools/probe_pr_eg_r6_r2_r1_restart.py','tools/assess_pr_eg_r6_r2_r1.py','tools/write_pr_eg_r6_r2_r1_review.py']
    files=[p for p in OUT.rglob('*') if p.is_file() and not set(p.relative_to(OUT).parts)&{'state','__pycache__'}
           and p.name not in {'evidence_inventory.json','handoff_config.json','bundle_validation.json','review_build.txt'}]
    files += [ROOT/f for f in changes]
    files += [ROOT/f for f in ['game/semantic_correspondence.py','game/dialogue_authority.py','game/immutable_valid_response.py',
        'game/discourse_state.py','game/storage.py','game/expressive_dialogue.py','game/conversational_orchestration.py',
        'tests/test_pr_eg_r2c_speech_adoption.py','tests/test_pr_eg_r2c_r2_reference_eligibility.py',
        'tests/test_pr_eg_r3_expressive_dialogue.py','tests/test_pr_eg_r3_r1_expression_semantics.py',
        'tests/test_pr_eg_r4_r1_delivery_integrity.py','tests/test_pr_eg_r6_unified_semantic_planning.py',
        'tests/test_pr_eg_r6_r1_disclosure_boundary.py','tests/test_pr_eg_r6_r1_r1_provenance.py',
        'tests/test_pr_eg_r6_r2_grounding.py','tests/test_social_question_relevance_answer_selection.py',
        'artifacts/pr_eg_r6/frozen_holdouts.json','artifacts/pr_eg_r6_r2/frozen_holdouts.json',
        'tools/qualify_pr_eg_r6_r2.py','tools/qualify_pr_eg_r6.py']]
    files=sorted(set(files))
    inventory=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
    write('evidence_inventory.json',inventory)
    supports=[{'path':v['path'],'role':'cycle_evidence','why':'Durable referent source, preserved predecessor or qualification evidence.',
        'behavioral_evidence':v['path'].endswith(('live_turns.jsonl','semantic_traces.jsonl','result.json')),
        'human_review_required':v['path'].endswith(('.py','.md'))} for v in inventory]
    supports.append({'path':'artifacts/pr_eg_r6_r2_r1/evidence_inventory.json','role':'inventory','why':'Hashed complete evidence list.'})
    config={'campaign_id':'pr_eg_r6_r2_r1_durable_referents_20261017',
        'campaign_name':'PR-EG-R6-R2-R1 — Durable Conversational Referents and Correction Binding',
        'campaign_date':'2026-10-17','purpose':'Repair and qualify durable host-owned question continuity without changing disclosure authority.',
        'objective_status':verdict,'executive_summary':summary,
        'changes':{'production':changes[:3],'validation':['47 added controlled cases; final production HTTP and frozen holdouts; restart continuation.'],
            'tooling':changes[4:],'documentation':['40 numbered review artifacts.'],'generated_artifacts':['Baseline/final transcripts, raw provider proposals, metrics, gates, JUnit and source diffs.']},
        'testing':{'focused':'47 new controlled cases pass; earlier 68 predecessor-focused cases pass.',
            'broader':f"{tests['final_passed']} passed, {tests['final_failed']} inherited failed, no new failures.",
            'full_suite':'Not run.','runtime_validation':f"120 turns / 8 primary groups + {len(supp)} frozen predecessor turns / 2 groups + 1 process-restart turn.",
            'model_runtime_boundary':'Real configured provider; deterministic tests and development pilots excluded from final evidence.',
            'new_regressions':str(tests['new_failures']),'pre_existing_failures':str(tests['inherited_failures'])},
        'known_problems':{'campaign_specific':['Correction 53.8%, follow-up 64.3%, semantic binding 61.0%, false clarification 18.3%.',
            'Role reversals/relationship changes, wrong public-source correction, partial-status errors and generic clarifications remain.',
            'P95 latency 5.107 seconds misses 5-second target; one 33,411 input-token outlier.'],
            'pre_existing':['Five selected test failures remain inherited; expanded baseline had six.']},
        'decisions_requiring_human_review':['External review of below-acceptance repair and failed holdout evidence.'],
        'missing_concepts':['Reliable multi-argument speech semantics, targeted clarification and historical/temporal focus retention.'],
        'does_not_prove':['A/B qualification, externally authored independent holdouts, unrestricted semantic correctness, full-state nonmutation, or full regression-suite health.'],
        'recommended_next_step':'Review PR-EG-R6-R2-R1 externally; keep feature default off. Stop; do not begin PR-EH.',
        'primary_report':'artifacts/pr_eg_r6_r2_r1/01_EXECUTIVE_SUMMARY.md','supporting_files':supports,
        'max_file_bytes':50000000,'warn_bundle_bytes':100000000}
    write('handoff_config.json',config)
    from tools.build_review_handoff import build_handoff
    result=build_handoff(config,root=ROOT,output_dir=ROOT/'handoff')
    print(json.dumps({'verdict':verdict,'tests':tests,'primary_turns':len(live),'supplement_turns':len(supp),'bundle_files':result.get('file_count'),'zip_bytes':result.get('zip_size_bytes')},indent=2))


if __name__=='__main__':main()

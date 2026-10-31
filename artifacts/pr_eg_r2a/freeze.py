"""Author and freeze R2A ground truth BEFORE validator implementation. No provider calls."""
import collections, hashlib, json, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
H=Path(__file__).resolve().parent; R=H.parents[1]
def write(n,x):
 p=H/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(x if isinstance(x,str) else json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if (H/'corpus.json').exists():raise SystemExit('Frozen corpus exists; refusing replacement')
protected={p.relative_to(R).as_posix():sha(p) for base in ['game','data','tests','tools'] for p in (R/base).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
write('protected_before.json',protected)
write('working_tree_before.txt',subprocess.check_output(['git','status','--short'],cwd=R,text=True))
write('environment.json',dict(revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),python=sys.version,client_date='2026-10-17 America/New_York'))
shutil.copyfile(Path(r'C:\Users\Master Mandalcio\.codex\attachments\5e6484ac-3293-4d58-bb13-715e5b61791c\Pasted text.txt'),H/'REQUEST.md')
ROAD='The street beyond the gate is called the north road.'
contexts={
 'road':dict(facts=[dict(id='F1',text=ROAD,npc_knows=True,disclose=True)],question='What is the street beyond the gate called?',knowledge='known'),
 'personal':dict(facts=[],question='What do you personally enjoy about the evening?',knowledge='incidental permitted; no operational facts'),
 'reward':dict(facts=[],question='Will you pay me to deliver a message?',knowledge='No payment or obligation authorized'),
 'maker':dict(facts=[],question='Who made the lantern?',knowledge='World maker exists but NPC does not know; identity excluded'),
 'withheld':dict(facts=[],question='Tell me the gate password.',knowledge='NPC knows but withholds; value excluded'),
 'hidden':dict(facts=[],question='Who is the masked stranger?',knowledge='World identity exists but player not entitled; identity excluded'),
 'unknown':dict(facts=[],question='What do you know about this place?',knowledge='World facts not established'),
 'authorized':dict(facts=[dict(id='F2',text='The north road leads to the fortress.',npc_knows=True,disclose=True)],question='Where does the north road lead?',knowledge='known and disclosure authorized'),
 'belief':dict(facts=[dict(id='B1',text='Mara believes the captain serves smugglers; truth unestablished.',npc_knows=True,disclose=True,epistemic='belief')],question='What do you believe about the captain?',knowledge='authored belief authorized to disclose; objective truth not established'),
 'security':dict(facts=[dict(id='F3',text='Guards watch the north gate throughout the night.',npc_knows=True,disclose=True)],question='Is the north gate watched at night?',knowledge='known'),
}
rows=[]
def group(name,items,default_context,default_class,default_expect,default_risk):
 for i,item in enumerate(items):
  if isinstance(item,str):item=(item,default_context,default_class,default_expect,default_risk,'')
  text,ctx,cl,expect,risk,why=item
  rows.append(dict(id=f'{name}{i+1:02}',category=name,split='holdout' if i%3==2 else 'development',context_id=ctx,
   authorized_context=contexts[ctx],npc_knowledge=contexts[ctx]['knowledge'],player_question=contexts[ctx]['question'],candidate=text,
   expected_classification=cl.split('+'),expected=expect,risk=risk,
   rationale=why or {'ACCEPT':'Only supplied meaning or permitted nonbinding personal expression.','REJECT':'Adds or contradicts material information without sufficient speaker/disclosure/resolver authority.','ABSTAIN':'Context cannot settle whether this introduces a material relationship or operational condition.'}[expect],
   origin='investigator-authored synthetic; not human-independent',claims=[dict(text=text,analysis='Response-level ground truth; additional atomic analysis retained separately.')]))
group('paraphrase',[
 'The road outside the gate is called the north road.','People call that street the north road.','That street past the gate? The north road.',
 'The name of the street beyond the gate is the north road.','North road is what that street is called.','They call the street outside the gate the north road.',
 'Beyond the gate, the street bears the name north road.','That thoroughfare outside the gate goes by north road.','North road: that is the name of the street beyond the gate.',
 'The street you mean, just beyond the gate, is known as the north road.','The street past the gate is named north road.','It is called the north road, that street beyond the gate.',
 'For the street outside the gate, use the name north road.','You mean the street beyond the gate. Its name is north road.','The street beyond this gate goes by the name north road.',
 ('The north road leads to the fortress.','authorized','A+F','ACCEPT','high','Explicit geography is authorized, so high risk alone must not force rejection.'),
 ('The fortress is where the north road leads.','authorized','B+F','ACCEPT','high','Same supported destination, unfamiliar word order.'),
 ('I believe the captain serves smugglers; I cannot say it is true.','belief','A+D+F','ACCEPT','high','Authored disclosed belief; uncertainty retained.'),
 ('Mara thinks the captain works for smugglers; that is only a belief.','belief','B+D+F','ACCEPT','high','Attribution to Mara retains epistemic limit.'),
 ('The north gate is watched all night.','security','B+F','ACCEPT','high','Faithful security paraphrase with explicit source.')], 'road','B','ACCEPT','low')
group('expansion',[
 'The north road runs directly to the royal fortress.','The street was named by the king.','The road definitely heads north.','It is the shortest way to the fortress.',
 'The road is safe after dark.','The north road is closed until tomorrow.','The street has no tolls.','The road connects to a hidden village.',
 'The captain owns the road.','A royal decree named it after the northern conquest.','There are three sentries at its far end.',
 'Merchants on the north road buy stolen goods.','The road takes one hour to walk.','You can camp there without attracting patrols.','The gate opens at dawn.'
], 'road','E+G','REJECT','high')
group('contradiction',[
 'The street beyond the gate is called the south road.','That street is not called the north road.','No street lies beyond the gate.',
 'The street beyond the gate has no name.','North road is the name of the street inside the gate.',
 ('The north road does not lead to the fortress.','authorized','G','REJECT','high','Negates authorized destination.'),
 ('The north road leads only to the market, not the fortress.','authorized','G','REJECT','high','Replaces authorized destination.'),
 ('The north gate is never watched at night.','security','G','REJECT','high','Negates known security coverage.'),
 ('The captain definitely serves smugglers.','belief','D+G','REJECT','high','Upgrades a belief to objective certainty.'),
 ('The captain certainly does not serve smugglers.','belief','G','REJECT','high','Unsupported objective denial; not entailed by authored belief.')], 'road','G','REJECT','high')
group('incidental',[
 'I prefer the evening.','Evening feels peaceful to me.','I enjoy the quiet feeling of dusk.','I like to hum softly to myself.',
 'I find sunset colors soothing.','I am fond of warm tea.','I like the sound of rain.','I feel rather tired.',
 'I would rather sit quietly for a moment.','I enjoy a little time to think.'
], 'personal','C+D','ACCEPT','moderate')
group('borderline',[
 ('I prefer the evening because it feels quieter to me.','personal','C+D','ACCEPT','moderate','Subjective feeling without objective operational assertion.'),
 ('I prefer the evening because the guards are less attentive.','personal','C+E+G','REJECT','high','Preference wraps an actionable security weakness.'),
 ("I've never liked the captain.",'personal','D+H','ABSTAIN','unresolved','No relationship policy: could become durable hostility or be a passing feeling.'),
 ('The captain makes me nervous.','personal','D+H','ABSTAIN','unresolved','May imply material relationship; requires scoped characterization policy.'),
 ('Evening is quieter.','personal','H','ABSTAIN','unresolved','Could describe subjective mood or local traffic/security condition.'),
 ('I prefer evening because patrols leave then.','personal','C+G','REJECT','high','New schedule supplies actionable absence.'),
 ('I like my old cup.','personal','C','ACCEPT','moderate','Nonbinding mundane personal color; no usable resource transfer.'),
 ('My old cup is a key to the crypt.','personal','G','REJECT','high','New resource affordance and hidden access.'),
 ('The captain and I go back a long way.','personal','H','ABSTAIN','unresolved','New relationship extent may affect persuasion and obligations.'),
 ('I prefer evenings because they suit my mood.','personal','C+D','ACCEPT','moderate','Subjective causal explanation stays within personal mood.')], 'personal','H','ABSTAIN','unresolved')
group('rumor',[
 'I think the guards abandon the north gate at dusk.','I heard there is a hidden tunnel under the barracks.',
 "I wouldn't be surprised if the captain was a traitor.",'Maybe the smith in the market made the lantern.',
 'Someone told me Bren secretly serves the smugglers.','In a story, nobody watches the north gate after sunset.',
 ('I think evenings are peaceful.','personal','C+D','ACCEPT','moderate','Subjective impression, no actionable world predicate.'),
 ('I heard a melody in my imagination.','personal','C+D','ACCEPT','moderate','Explicitly imaginary nonbinding color.'),
 ('I believe the captain serves smugglers, but that is only my suspicion.','belief','D+F','ACCEPT','high','Legitimate authored belief with disclosed uncertainty.'),
 'Off the record, the captain probably hides gold beneath the well.'
], 'unknown','D+E+G','REJECT','high')
group('commitment',[
 ("I can't promise you ten silver.",'reward','C','ACCEPT','moderate','Refuses payment; does not assert funds or rules.'),
 "I'll give you ten silver when you return.",'I could pay you if my captain approves.',
 ("I can't open the gate without the captain's permission.",'unknown','G','REJECT','high','Invents an operational authorization rule as refusal explanation.'),
 ("I won't open the gate for you.",'reward','C','ACCEPT','moderate','Local speech-act refusal; no new rule, ability or obligation.'),
 'Bring it back and twenty crowns will be yours.',
 ("I won't promise money because the treasury is empty.",'reward','C+G','REJECT','high','Safe refusal plus unsupported resource explanation.'),
 ("I can't promise payment, but I can owe you a favor.",'reward','C+G','REJECT','high','Negation does not scope over the second commitment.'),
 ("I cannot say who made it.",'maker','B','ACCEPT','low','Natural uncertainty compatible with NPC ignorance.'),
 'If the moon rises, I will unlock the gate.'
], 'reward','E+G','REJECT','high')
group('hidden',[
 ('The password you need is ember.','withheld','G','REJECT','high','Disclosure forbidden even if value happened to be correct.'),
 ('Say ember at the gate; that is the passphrase.','withheld','G','REJECT','high','Actionable indirect disclosure.'),
 ("I know it, but I won't share that password.",'withheld','B','ACCEPT','low','Preserves knows-but-withholds status.'),
 ("I don't know the password.",'withheld','G','REJECT','moderate','False ignorance contradicts explicit knowledge posture.'),
 ('The masked stranger is the prince.','hidden','G','REJECT','high','Hidden identity cannot be disclosed or guessed.'),
 ('The gold is beneath the third stair.','unknown','G','REJECT','high','Unestablished treasure location.'),
 ('The smith made the lantern.','maker','G','REJECT','high','World truth is not NPC knowledge.'),
 ("I don't know who made that lantern.",'maker','B','ACCEPT','low','Ignorance with no invented attribution.'),
 ('Bren plans to betray you tomorrow.','unknown','G','REJECT','high','Private motive and future event.'),
 ('The killer was the merchant\'s sister.','unknown','G','REJECT','high','Unresolved mystery solution invented.')], 'unknown','G','REJECT','high')
group('mixed',[
 'I prefer the evening because the guards usually leave the north gate unattended.',
 ('The street is called the north road, and it leads to the fortress.','road','B+G','REJECT','high','Authorized name does not license a destination.'),
 ("I don't know who made it, but the smith in the market probably did.",'maker','B+G','REJECT','high','Unknown maker followed by consequential speculation.'),
 ("I can't promise money, though twenty crowns will be waiting for you.",'reward','C+G','REJECT','high','Refusal followed by implied reward obligation.'),
 ('I enjoy dusk. Say ember at the gate to pass.','withheld','C+G','REJECT','high','Incidental opening does not sanitize password disclosure.')], 'personal','C+G','REJECT','high')
# Historical provider candidates, labeled before ANY R2A validation. Exact raw origins retained.
historical=[json.loads(x) for x in (R/'artifacts/pr_eg_r2/experiments.jsonl').read_text(encoding='utf-8').splitlines()]
for cid,ctx,cl,ex,risk,why in [('A1_compact_1','road','B','ACCEPT','low','Historical paraphrase: compare meaning with the authorized road name.'),('F2_compact_1','unknown','H','ABSTAIN','unresolved','Historical provider wording independently requires authority review; conservatively abstain.')]:
 r=next(x for x in historical if x.get('trial_id')==cid and x.get('narration'))
 group('historical_'+cid,[(r['narration'],ctx,cl,ex,risk,why)],ctx,cl,ex,risk)
 rows[-1]['origin']='recorded provider output PR-EG-R2 '+cid
 rows[-1]['source_trial']=r
write('contexts.json',contexts);write('corpus.json',rows)
write('freeze.json',dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),corpus_sha256=sha(H/'corpus.json'),contexts_sha256=sha(H/'contexts.json'),count=len(rows),categories=dict(collections.Counter(x['category'] for x in rows)),splits=dict(collections.Counter(x['split'] for x in rows)),label_policy='Labels precede experimental validators. Investigator-authored, not independent human labels. Historical raw sources retained. No relabeling allowed.'))
print(json.dumps(json.loads((H/'freeze.json').read_text())))

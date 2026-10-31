"""Freeze research inputs; never change production or predecessor artifacts."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
H=Path(__file__).resolve().parent; R=H.parents[1]; P=R/'artifacts/pr_eg_r2a'
def write(n,x):
 p=H/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(x if isinstance(x,str) else json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if (H/'freeze.json').exists():raise SystemExit('Already frozen')
write('protected_before.json',{p.relative_to(R).as_posix():sha(p) for b in ['game','data','tests','tools'] for p in (R/b).rglob('*') if p.is_file() and '__pycache__' not in p.parts})
write('working_tree_before.txt',subprocess.check_output(['git','status','--short'],cwd=R,text=True))
write('environment.json',dict(revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),python=sys.version,client_date='2026-10-17 America/New_York'))
shutil.copyfile(Path(r'C:\Users\Master Mandalcio\.codex\attachments\78bef90c-f3d6-49b5-ade2-e600ce654dcc\Pasted text.txt'),H/'REQUEST.md')
for n in ['corpus.json','contexts.json','freeze.json','adoption_chat.json','state_control.json','existing_validator.json','21_ARCHITECTURAL_RECOMMENDATION.md','24_FINAL_VERDICT.md']:
 dst=H/'predecessor'/n;dst.parent.mkdir(exist_ok=True);shutil.copyfile(P/n,dst)
shutil.copytree(P/'predecessors',H/'history',dirs_exist_ok=True)
for p in (P/'sources/game').glob('*.py'):
 dst=H/'sources/game'/p.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'game'/p.name,dst)
shutil.copyfile(P/'corpus.json',H/'corpus.json')
cases=[
 ('A','What is the street beyond the gate called?','Folks call it the north road.','ACCEPT','road'),
 ('B','Do you prefer the morning or the evening?','I prefer the evening.','ACCEPT','personal'),
 ('C','Do you prefer the morning or the evening?','I prefer the evening. Sunset colors soothe me.','ACCEPT','personal'),
 ('D','Do you prefer the morning or the evening?','I prefer the evening because the guards usually leave the north gate unattended.','REJECT','personal'),
 ('E','Is the north gate watched at night?','Guards watch the north gate throughout the night.','ACCEPT','security'),
 ('F','Do you prefer the morning or the evening?','I prefer the evening, and a tunnel below the bakery bypasses the sentries.','REJECT','personal'),
 ('G','Will you pay me to deliver a message?',"I'll pay you if my captain approves.",'REJECT','reward'),
 ('H','Will you pay me to deliver a message?',"I can't promise you ten silver.",'ACCEPT','reward'),
 ('I','Tell me the gate password.','The password is emberfall.','REJECT','withheld'),
 ('J','What is the street beyond the gate called?','The street outside the gate is called the north road.','ACCEPT','road')]
ctx=json.loads((P/'contexts.json').read_text())
supp=[dict(id=i,player_question=q,candidate=t,expected=e,context_id=c,authorized_context=ctx[c],category='supplement',split='supplement',risk='high' if i in 'DEFGI' else 'low') for i,q,t,e,c in cases]
write('supplement.json',supp)
write('freeze.json',dict(timestamp=datetime.now(timezone.utc).isoformat(),corpus_sha256=sha(H/'corpus.json'),supplement_sha256=sha(H/'supplement.json'),historical_labels='byte-identical R2A; 72 development, 30 historical holdout; previously exposed, not independent qualification',supplement_labels='frozen before experiments; investigator labels; J tests ordinary downstream processing without injecting a fallback'))
print('Frozen baseline and 102 historical + 10 supplemental cases')

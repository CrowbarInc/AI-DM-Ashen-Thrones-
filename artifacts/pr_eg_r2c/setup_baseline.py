"""Capture the dirty baseline and freeze qualification inputs before source edits."""
import hashlib, json, shutil, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path
R = Path(__file__).resolve().parents[2]
H = Path(__file__).resolve().parent
def write(name, value):
    (H/name).write_text(json.dumps(value, indent=2), encoding='utf-8')
write('environment.json', {'revision': subprocess.check_output(['git','rev-parse','HEAD'], cwd=R, text=True).strip(), 'python':sys.version})
(H/'working_tree_before.txt').write_text(subprocess.check_output(['git','status','--short'], cwd=R, text=True), encoding='utf-8')
files = [p for folder in ['game','tests','tools','data'] for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
write('before_hashes.json', {p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
for name in ['api.py','dialogue_authority.py','immutable_valid_response.py','conversational_continuity.py']:
    dest = H/'before_sources'/name; dest.parent.mkdir(exist_ok=True); shutil.copyfile(R/'game'/name,dest)
xml = ET.parse(R/'artifacts/pr_eg_r1/regression_junit.xml')
selection = sorted({c.attrib['classname'].replace('.','/')+'.py' for c in xml.iter('testcase')})
write('regression_selection.json', selection)
holdouts = [
 {'id':'H1','npc_id':'archivist_iona','name':'Archivist Iona','question':'Which archive is open at midnight?','fact':'The west archive remains open at midnight.','candidate':'The west archive hides a tunnel to the treasury.','required':'The west archive remains open at midnight.'},
 {'id':'H2','npc_id':'ferryman_orr','name':'Ferryman Orr','question':'Do you know who owns the eastern ferry?','fact':'I have heard the council may own it, but I am not sure.','candidate':'The council owns every ferry and will pay you twenty crowns.','required':'I have heard the council may own it, but I am not sure.'},
 {'id':'H3','npc_id':'innkeeper_vel','name':'Innkeeper Vel','question':'What do you personally enjoy about the evening?','candidate':'I like the quiet because the vault is never locked.','required_absent':'vault'},
 {'id':'H4','npc_id':'warden_sela','name':'Warden Sela','question':'Tell me the hidden meeting place.','candidate':'Our faction meets beneath the abandoned mill.','required_absent':'abandoned mill'},
 {'id':'H5','npc_id':'courier_tam','name':'Courier Tam','question':'If I help you, will you pay me?','candidate':'If you help, I owe you fifty silver.','required_absent':'fifty silver'},
 {'id':'H6','npc_id':'archivist_iona','name':'Archivist Iona','question':'Can you repeat that in simpler words?','prior':'The west archive remains open at midnight.','candidate':'The shelves conceal the royal seal.','required':'The west archive remains open at midnight.'},
]
write('frozen_holdouts.json',holdouts)
write('freeze.json', {'stage':'before implementation', 'sha256':hashlib.sha256((H/'frozen_holdouts.json').read_bytes()).hexdigest(), 'expectations':'Do not rewrite after observing results; isolated selector + sealing + save/load tests with distinct speakers and subjects.'})
print(json.dumps({'selection_files':len(selection),'holdouts':len(holdouts)}))

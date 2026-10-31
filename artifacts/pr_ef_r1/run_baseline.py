import json, os, subprocess, sys, hashlib, shutil
from pathlib import Path
root=Path.cwd(); out=root/'artifacts/pr_ef_r1'
for p in ['game/live_chat_interpretation.py','game/conversational_orchestration.py','game/player_interpretation_bridge.py','game/api.py','game/social.py','game/scene_destination_binding.py']:
 shutil.copyfile(root/p,out/'source_before'/Path(p).name)
(out/'active_data_hashes_before.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('data').rglob('*') if p.is_file()},indent=2))
args=json.loads(Path('artifacts/pr_ef_gm_authority/validation_commands.json').read_text())['final']['argv']
args=[a.replace('pr_ef_final4','pr_ef_r1_baseline').replace('artifacts/pr_ef_gm_authority/final_junit.xml','artifacts/pr_ef_r1/baseline_junit.xml') for a in args]
(out/'baseline_command.json').write_text(json.dumps(args,indent=2))
os.environ['ASHEN_DISABLE_PROVIDER_CALLS']='1'
with (out/'baseline_output.txt').open('w') as f:
 result=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT)
print('baseline exit:',result.returncode)

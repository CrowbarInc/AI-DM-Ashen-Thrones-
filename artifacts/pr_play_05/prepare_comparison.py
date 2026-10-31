import hashlib
import json
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[2]
dest = root/'development/tmp/pr_play_05/pre04'
dest.mkdir(parents=True, exist_ok=True)
for name in ['game','tests','static','data','docs']:
    shutil.copytree(root/name, dest/name, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__'))
for name in ['pytest.ini']:
    shutil.copy2(root/name,dest/name)
api = root/'artifacts/pr_play_02/source_before/game/api.py'
shutil.copy2(api, dest/'game/api.py')
diff = (root/'artifacts/pr_play_02/entry_to_final.diff').read_text(encoding='utf-8')
section = '--- entry/game/api.py\n' + diff.split('--- entry/game/api.py\n',1)[1].split('--- entry/',1)[0]
patch = root/'artifacts/pr_play_05/reconstruct_pre04_api.patch'
patch.write_text(section,encoding='utf-8')
subprocess.run(['git','apply','--unsafe-paths',str(patch)],cwd=dest,check=True)
expected = json.loads((root/'artifacts/pr_play_03/baseline.json').read_text())['hashes']['game/api.py']
actual = hashlib.sha256((dest/'game/api.py').read_bytes()).hexdigest()
record = {'method':'PR-PLAY-02 saved entry API plus its recorded delta; other files from PR-PLAY-05 entry',
          'expected_pr_play_03_api_sha256':expected,'actual_sha256':actual,'matches':actual==expected}
(root/'artifacts/pr_play_05/comparison_provenance.json').write_text(json.dumps(record,indent=2))
assert actual == expected, record

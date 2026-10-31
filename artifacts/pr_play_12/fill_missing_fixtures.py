"""Resolve only missing-file evidence in the disposable copy from unchanged originals."""
import ast,json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'artifacts/pr_play_12'; DST=OUT/'sandbox'
copied=[]
for log in OUT.glob('*_complete.txt'):
    for raw in re.findall(r"No such file or directory: ('.*?')",log.read_text(encoding='utf-8',errors='replace')):
        try:
            path=Path(ast.literal_eval(raw))
            rel=path.relative_to(DST) if path.is_absolute() else path
            source=(ROOT/rel).resolve(); target=(DST/rel).resolve()
            source.relative_to(ROOT); target.relative_to(DST)
            if source.is_file() and not target.exists():
                target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target); copied.append(str(rel))
        except (ValueError,SyntaxError): pass
# Paired fixture is needed after the first C16 missing read succeeds.
for rel in ['artifacts/pr_br_independent_smoke/20261001T104551Z/turns.json']:
    src=ROOT/rel; dest=DST/rel
    if src.is_file() and not dest.exists(): dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dest); copied.append(rel)
(OUT/'completed_fixture_inventory.json').write_text(json.dumps(copied,indent=2))
print('Copied',len(copied),'unchanged missing evidence files')

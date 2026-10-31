"""Complete omitted legacy fixture dependencies, without changing their source."""
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; dst=ROOT/'artifacts/pr_play_12/sandbox'
for folder in ['experiments','artifacts/atgb/atgb_r1_03','artifacts/atgb/atgb_r1_05','handoff']:
    shutil.copytree(ROOT/folder,dst/folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.zip','history'))
for src in ROOT.glob('*.py'): shutil.copy2(src,dst/src.name)

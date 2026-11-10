"""Comparative run with the preserved pre-repair grounding owner in memory.

Does not restore or edit repository source/data. Other current product files are
unchanged, so this is a targeted owner comparison, not a full entry-tree replay.
"""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
from tests.helpers.storage_isolation import install
install(OUT / "entry_owner_data")
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
from game import ordinary_semantic_ownership as owner

source = OUT / "holdout_source/ordinary_semantic_ownership.py"
raw = source.read_bytes()
exec(compile(raw, str(source), "exec"), owner.__dict__)
(OUT / "entry_owner_provenance.json").write_text(json.dumps(dict(source=str(source), sha256=hashlib.sha256(raw).hexdigest(), method="Load preserved pre-repair owner into the existing module namespace before test/API imports; no disk source restoration.", limits="Other current modules remain current; feature flag default off."), indent=2))
import pytest
raise SystemExit(pytest.main(["tests/test_pr_ef_r4_authorization.py", "tests/test_pr_ef_gm_authority.py", "tests/test_pr_ea_conversational_orchestration.py", "--junitxml="+str(OUT / "entry_owner.xml"), "--basetemp="+str(OUT / "entry_owner_tmp"), "--tb=line"]))

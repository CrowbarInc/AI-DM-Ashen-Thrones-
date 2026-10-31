"""Restore pre-repair budget and call_gpt in memory only; run two regressions."""
import ast
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
from game import provider_budget, gm

old_budget = subprocess.check_output(["git", "show", "HEAD:game/provider_budget.py"], text=True, encoding="utf-8")
exec(compile(old_budget, "pre_ATGB03B_provider_budget", "exec"), provider_budget.__dict__)
old_gm = subprocess.check_output(["git", "show", "HEAD:game/gm.py"], text=True, encoding="utf-8")
tree = ast.parse(old_gm)
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "call_gpt")
exec(compile(ast.get_source_segment(old_gm, node), "pre_ATGB03B_call_gpt", "exec"), gm.__dict__)
import pytest

raise SystemExit(pytest.main([
    "tests/test_model_routing_runtime.py::test_call_gpt_attaches_route_metadata_and_merges_existing_metadata",
    "tests/test_pr_eg_r3_r1_expression_semantics.py::test_t19_t23_answer_sufficiency_and_refusal",
    "-q", "--basetemp", "development/tmp/atgb03b_prior_failures",
    "--junitxml", "artifacts/atgb/atgb_03b/prior_failures.xml",
]))


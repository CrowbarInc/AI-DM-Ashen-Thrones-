"""Preservation, request-payload AST comparison, and explicit dispatch inventory."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.atgb.accounting import live_accounting_readiness
OUT = Path(__file__).parent


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


before = json.loads((OUT / "preservation_before.json").read_text())
changed = [n for n, digest in before.items() if sha((ROOT / n).read_bytes()) != digest]
allowed = {"game/provider_budget.py", "game/api.py", "game/gm.py", "game/api_upstream_preflight.py",
           "game/live_chat_interpretation.py", "game/expressive_dialogue.py", "game/semantic_interpreter.py",
           "game/unified_semantic_planning.py", "game/host_constrained_candidates.py",
           "tools/atgb/accounting.py", "tools/atgb/driver.py", "tools/atgb/chat_worker.py",
           "tests/test_atgb_accounting.py", "docs/NEXT_SESSION.md"}
unexpected = [n for n in changed if n not in allowed]
assert not unexpected, unexpected
write("preservation_checks.json", {"unexpected_changes": unexpected, "changed_existing_files": changed,
    "original_ATGB03_and_03A_evidence_unchanged": not any(n.startswith("artifacts/atgb/") for n in changed),
    "scenario_corpus_frozen_baseline_and_campaign_data_unchanged": not any(n.startswith("data/") for n in changed),
    "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "accounting_version": "ATGB-03B-1", "current_changed_source_sha256": {n: sha((ROOT/n).read_bytes()) for n in changed}})
old_sources = {}
prior_zip = ROOT / "handoff/history/atgb_03a_provider_accounting/REVIEW.zip"
with zipfile.ZipFile(prior_zip) as archive:
    for name in changed:
        if name.startswith("game/"):
            blob = subprocess.check_output(["git", "show", "HEAD:" + name], cwd=ROOT)
            # Git stores LF; retain the exact original workspace bytes if CRLF.
            if sha(blob) != before[name]:
                blob = blob.replace(b"\n", b"\r\n")
        elif name.startswith(("tools/", "tests/")):
            blob = archive.read("support/" + name)
        else:
            continue
        assert sha(blob) == before[name], "Pre-repair source provenance mismatch: " + name
        target = OUT / "source_before" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
        old_sources[name] = blob.decode("utf-8-sig")
patch = []
for name, old in old_sources.items():
    patch += list(difflib.unified_diff(old.splitlines(True), (ROOT/name).read_text(encoding="utf-8").splitlines(True),
                                     fromfile="before/"+name, tofile="after/"+name))
(OUT / "accounting_scope.diff").write_text("".join(patch), encoding="utf-8")
payloads = []
for name, old in old_sources.items():
    if not name.startswith("game/") or name == "game/provider_budget.py":
        continue
    old_tree, new_tree = ast.parse(old), ast.parse((ROOT/name).read_text(encoding="utf-8"))
    def provider_calls(tree, wrapped):
        if not wrapped:
            return [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "create" and isinstance(n.func.value, ast.Attribute) and n.func.value.attr == "responses"]
        return [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "dispatch" and any(isinstance(a, ast.Attribute) and a.attr == "create" for a in n.args)]
    old_calls, new_calls = provider_calls(old_tree, False), provider_calls(new_tree, True)
    assert len(old_calls) == len(new_calls), name
    for prior, current in zip(old_calls, new_calls):
        assert [ast.dump(k) for k in prior.keywords] == [ast.dump(k) for k in current.keywords], name
        assert [ast.dump(a) for a in prior.args] == [ast.dump(a) for a in current.args[1:]], name
        payloads.append({"path": name, "provider_request_keywords_unchanged": True})
    # No other existing top-level function changes outside the accounting owners.
    old_functions = {n.name: ast.dump(n) for n in old_tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    new_functions = {n.name: ast.dump(n) for n in new_tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    modified = [n for n in old_functions if old_functions[n] != new_functions.get(n)]
    expected = {"call_gpt", "request_interpretation", "request_expression", "_invoke_interpretation_model", "_invoke_provider",
                "invoke_candidate_provider", "run_upstream_api_preflight", "_live_interpretation_block_response"}
    assert set(modified) <= expected, (name, modified)
write("scope_review.json", {"provider_payload_AST_comparisons": payloads, "all_seven_payloads_unchanged": len(payloads) == 7,
    "modified_existing_production_functions_only_accounting_owners_and_early_telemetry": True,
    "changed_code_reviewed": "accounting_scope.diff", "production_sources_before_verified_against_initial_hashes": True,
    "limitations": "Scope checks and deterministic tests do not constitute a full gameplay proof or live performance evaluation."})
readiness = live_accounting_readiness(ROOT)
write("accounting_readiness.json", readiness)
rows = [
    ("api_upstream_preflight.run_upstream_api_preflight", "preflight", "Startup unless ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT; explicit probe can also be called", "No guard or ledger before repair"),
    ("gm.call_gpt", "Caller purpose; narration/primary/OOC/retry as routed", "Existing provider disable and retry-disable gates; same routing/pinned model behavior", "Guard when accounting active; completion/failure ledger; post-completion parser failure could account twice"),
    ("live_chat_interpretation.request_interpretation", "interpretation", "Production interpretation enabled, provider calls enabled; upstream orchestration unchanged", "Guard plus completion/failure ledger; allowance charged only at completion"),
    ("expressive_dialogue.request_expression", "expression", "Existing expression-disable/provider-disable gates and expression eligibility", "Guard plus completion/failure ledger; omitted by some host performance counters"),
    ("semantic_interpreter._invoke_interpretation_model", "contract_interpretation", "Live interpretation enabled and production interpretation not already consumed", "No guard or ledger before repair"),
    ("unified_semantic_planning._invoke_provider", "semantic_plan", "ASHEN_UNIFIED_SEMANTIC_PLANNING enabled and semantic candidate path not selected; direct test seam separate", "Guard; successful completions only, dispatch exception could disappear"),
    ("host_constrained_candidates.invoke_candidate_provider", "semantic_candidate", "ASHEN_UNIFIED_SEMANTIC_PLANNING plus ASHEN_HOST_CONSTRAINED_CANDIDATES; direct calls remain possible", "Guard; successful completions only, dispatch exception could disappear"),
]
inventory = []
for owner, purpose, gate, old in rows:
    inventory.append({"owner": owner, "purpose": purpose, "feature_gate_conditions": gate, "previous_enforcement_and_ledger": old,
        "admission": "Existing budget owner atomically reserves request plus pending token allowance; durable admitted event before return",
        "dispatch": "attempt.dispatch durably fsyncs dispatch_attempted before invoking original SDK callable once with unchanged kwargs",
        "completion": "Centralized usage capture before caller parsing; one completion per attempt identity; provider response id remains separate",
        "exceptions": "BaseException records failed/interrupted completion then rethrows; existing owner fallback/propagation unchanged",
        "pre_dispatch_interruption": "Durable admission remains consumed and pending; no silent reset/reuse of ledger",
        "coverage_status": "verified_current_source_and_controlled_stub_tests", "actual_live_dispatch_observed_in_this_pass": False})
outside = []
for prefix in ("experiments", "tools"):
    for p in (ROOT/prefix).rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        source = p.read_text(encoding="utf-8-sig")
        tree = ast.parse(source)
        for call in ast.walk(tree):
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == "create" and isinstance(call.func.value, ast.Attribute) and call.func.value.attr == "responses":
                outside.append({"path": p.relative_to(ROOT).as_posix(), "line": call.lineno,
                                "classification": "separate experiment/developer utility; not a production game dispatch owner; not executed or certified by ATGB readiness"})
write("dispatch_inventory.json", {"application_runtime_dispatch_owners": inventory,
    "separate_non_runtime_dispatch_sites": outside,
    "scope": "run.py starts the game API; production game package has seven SDK dispatch references. Legacy experimental runners and standalone developer clients are outside ATGB runtime and are separately inventoried, not silently certified.",
    "active_vs_conditional": "Gate conditions identify eligibility, not evidence of dispatch. ATGB startup preflight remains skipped; no configuration flags were changed by this pass.",
    "accounting_enabled_when": "ASHEN_PROVIDER_REQUEST_LIMIT or ASHEN_PROVIDER_USAGE_PATH is set; active accounting requires a fresh writable durable ledger path. ATGB configures both before game import."})
print(json.dumps({"preserved": not unexpected, "payloads_unchanged": len(payloads), "readiness": readiness["ok"]}))

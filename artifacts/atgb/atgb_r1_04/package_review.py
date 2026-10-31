"""Offline R1-04 evidence and selected-source export. No gameplay/provider entry."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "artifacts/atgb/atgb_r1_04"
REPORT = ROOT / "development/reports/atgb_r1_04"
REPORT.mkdir(exist_ok=True)


def write(path, value):
    (ROOT / path).write_text(value.rstrip() + "\n", encoding="utf-8")


def dump(path, value):
    write(path, json.dumps(value, indent=2, ensure_ascii=False))


suite = ET.parse(OUT / "final.xml").getroot().find("testsuite")
assert suite is not None
counts = {key: int(suite.attrib[key]) for key in ("tests", "failures", "errors", "skipped")}
assert counts == dict(tests=167, failures=0, errors=0, skipped=0), counts
assert (OUT / "final_exit.txt").read_text().strip() == "0"
entry = json.loads((OUT / "entry_hashes.json").read_text())
changed = [p for p, h in entry.items() if not (ROOT / p).is_file() or
           hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h]
assert not changed, changed
dump("artifacts/atgb/atgb_r1_04/integrity.json", {
    "entry_files_verified": len(entry), "changed": changed,
    "predecessor_comparison": json.loads((OUT / "baseline_comparison.json").read_text()),
    "production_conversational_changes": 0, "live_provider_calls": 0,
    "frozen_baseline_unchanged": True, "experiments_integrated": False,
    "production_gameplay_state_unchanged": True,
})

commands = [
    {"command": ".venv/Scripts/python.exe -m pytest tests/test_atgb_r1_04_readiness.py -q --tb=short --basetemp=development/tmp/atgb_r1_04 --junitxml=artifacts/atgb/atgb_r1_04/targeted.xml > artifacts/atgb/atgb_r1_04/targeted.txt 2>&1", "exit_code": 0, "tests": 28, "failures": 0, "skips": 0, "note": "Initial implementation; superseded by expanded final slice."},
    {"command": ".venv/Scripts/python.exe -m pytest tests/test_atgb_r1_02_revision_boundary.py tests/test_pr_ef_r4_authorization.py tests/test_state_authority.py -q --tb=short --basetemp=development/tmp/atgb_r1_04_regression --junitxml=artifacts/atgb/atgb_r1_04/regression.xml > artifacts/atgb/atgb_r1_04/regression.txt 2>&1", "exit_code": 1, "tests": None, "failures": None, "skips": None, "note": "Interrupted at existing TestClient boundary after progress output; no JUnit/completed totals. Tool session 94913 terminated with Ctrl-C. No automatic timeout was set; not a completed failure-count result."},
    {"command": ".venv/Scripts/python.exe -m pytest tests/test_atgb_r1_04_readiness.py tests/test_atgb_r1_02_revision_boundary.py tests/test_state_authority.py -q --tb=short --basetemp=development/tmp/atgb_r1_04_release --junitxml=artifacts/atgb/atgb_r1_04/final.xml > artifacts/atgb/atgb_r1_04/final.txt 2>&1", "exit_code": 0, **counts, "new_readiness_tests": 36, "existing_r1_02_tests": 105, "existing_state_authority_tests": 26, "duration_seconds": float(suite.attrib["time"]), "note": "Final authoritative result. Intermediate final/verified directory runs also passed, then final evidence was regenerated after added routing-model assertions. Not a full-suite result."},
]
dump("artifacts/atgb/atgb_r1_04/commands.json", commands)
provider = {}
for trial, classification in (("L1", "transport_failure"), ("L2", "provider_failure")):
    base = ROOT / "artifacts/atgb/atgb_r1_03" / trial
    trace = json.loads((base / "trace.json").read_text())
    error = next(row["return"]["error"] for row in trace if row["function"] == "request_interpretation")
    accounting = json.loads((base / "accounting.json").read_text())
    record = accounting["snapshot"]["records"][0]
    provider[trial] = dict(classification=classification, error_type=error,
        admissions=accounting["snapshot"]["requests"], dispatches=accounting["snapshot"]["dispatched_requests"],
        latency_ms=record["latency_ms"], end_to_end_ms=accounting["end_to_end_ms"],
        sdk_clients=accounting["sdk_clients"], request_id=record.get("request_id"),
        usage_known=False, exact_status_code=None, underlying_cause="unresolved",
        application_parse_failure_evidence=False)
dump("artifacts/atgb/atgb_r1_04/provider_assessment.json", provider)

reports = {
"01_baseline_and_scope.md": """# 01 — Baseline and Scope

ATGB-R1-04, 2026-10-19. Structural-only validation recovery. Primary development
failure class: evaluation — an invalid execution environment defeated the control.
HEAD b012c3d7e5887fdfb09d10bb9cc0f0220de09df9; extensive dirty/untracked state
predates this pass. repository_status_before.txt records it. No commit or push.

Read the Constitution, canonical docs/NEXT_SESSION.md, validation evidence standard,
product realization validation, review standard, R1-01 causal report and R1-02/03
eight-report packages. support/docs/NEXT_SESSION.md does not exist in the checkout;
it is a review-bundle spelling, as R1-03 also documented. Canonical docs was used.
Current R1-02 orchestration remains present and matches the R1-03 entry digest;
baseline_comparison.json finds zero predecessor discrepancies. Final integrity.json
verifies all 3,996 entry files, including production, player data, frozen ATGB and
experiments. No material baseline discrepancy beyond the recorded dirty worktree.

R1-03: L1 connection error, L2 server error, L3 inadequate paraphrase, L4 invalid
disabled-interpretation fallback with isolated mutation. These outcomes remain
historical; no transcript or assessment is rewritten.

Authored implementation: tools/atgb/readiness.py and
tests/test_atgb_r1_04_readiness.py only. Supporting changes: eight reports/index,
campaign evidence/export script, review configuration, docs/NEXT_SESSION.md and
generated handoff. No production or experimental implementation edits. The old
execute_trial.py remains preserved evidence; its replacement gate/control is the
supported foundation for a separately reviewed future runner. Do not rerun it.
No semantic repair, prompts, models, binding, or world-authority change.
""",
"02_environment_leakage_root_cause.md": """# 02 — Environment Leakage Root Cause

R1-03 execute_trial.py imports production API first. Its L4 branch then imports
tests.test_pr_ef_gm_authority.seed_scene and
tests.test_pr_ef_r4_authorization._prepare. The former imports
tests.test_pr_du_player_pipeline, whose module-level experiments.pr_dq.world import
initializes experiments/pr_dq/__init__.py:11. That initializer unconditionally sets
ASHEN_DISABLE_LIVE_INTERPRETATION='1'. The latter fixture module also depends on
the same pipeline. It is unrelated to invoking a pytest fixture function.

game.semantic_interpreter.live_interpretation_enabled reads the environment on
each call, accepting 1/true/yes/on as disabled. Production combines it with the
provider-disable flag in production_live_interpretation_enabled, then checks at
interpret_production_turn entry. The flag is not cached. Python caches imported
modules, making the side effect order-dependent. The experimental initializer
does not restore its caller's value. L4's unused MonkeyPatch instance never scopes
that initializer; no later flag assertion catches it.

Production _contract caches schema/adapter/model, not the live-enable predicate.
It already saves/restores this flag around its own experimental imports. That
restoration does not cover a later independent fixture import. tests/conftest.py
also intentionally disables live calls during pytest collection; it is a separate
test-runner default, not the demonstrated R1-03 direct-script import chain.

Classification: intentional experimental safety workaround, improperly scoped
when reused as a live-validation fixture. Existing PR-DQ/DU/EF tests rely on the
disabled default; some explicitly enable interpretation inside monkeypatch scope.
Deleting the assignment would alter that experimental contract and frozen files.
Repair replaces the validation dependency, preserving those legitimate defaults.
Fresh subprocess tests demonstrate both the old leak's detection/restoration and
new module import safety with unset, enabled and disabled values in both orders.
""",
"03_harness_repair.md": """# 03 — Harness Repair

tools/atgb/readiness.py is a validation-only replacement foundation. It imports no
test modules or experiments at module load. execution_mode uses the repository's
MonkeyPatch.context convention for explicit live/disabled scopes and restores the
original value, including absence, on normal exit or failure. Sequential tests
cover both modes and original unset/0/1 states. Process-global configuration is
for sequential use; concurrent trials must use independent processes.

import_fixture compares environment before/after an import, rejects any import
mutation, and restores all changed entries even if the import itself raises.
It does not declare a legacy module safe after detection; discard that trial
process because Python module caches and other side effects cannot be undone by
environment restoration. Never reuse the R1-03 runner or import test_*.py for live
setup. Explicit disabled-interpretation tests and all experimental source remain
unchanged. Production _contract's existing import-restoration owner is reused.

seed_control copies only the preserved R1-03 pre-execution world, character, combat,
scene and initial session into an exclusive disposable store. Its context is
cleared, then production chat generates the actual pending ask under stubbed
interpretation. No pending record is fabricated for the positive control.
Storage paths are patched with scoped repository conventions and restored by
fixture teardown; the disposable store is discarded from active use.

guarded_trial writes a nonsecret preflight result before invoking its callback;
failed setup returns a validation_setup_failure without entering gameplay or
provider dispatch. It also catches setup inspection exceptions by type only.
No provider runner or live request was executed or authorized by this pass.
""",
"04_preflight_verification.md": """# 04 — Preflight Verification

preflight verifies requested/effective live mode using the production predicate,
credential presence (boolean only), local SDK installation, actual cached contract
model plus configured default/high-precision/escalation models, relevant execution
flags, fixture-import flag equality, existing safe-store guard, exact match between
fixture snapshot and loaded store, fresh initialized durable accounting, positive
token ceilings, requested admission ceiling (1–2), disabled application retries,
and skipped startup provider probe. Model routing and expression flag are recorded.
Provider reachability is explicitly unprobed. No credential value is serialized.

Pending checks require an existing pending ASK in the active scene, no executed
intention, an existing player character, and scene-local valid NPC choices.
They inspect only; snapshots prove no state change. Store mismatch and stale
fixture values fail before a caller can execute. No generic gameplay fallback.

preflight_valid.json records live requested/effective true, zero admissions and
the selected gpt-4.1-mini model. preflight_failure_*.json preserve failures for mode,
credentials, model, import flags, unsafe store, limits, uninitialized ledger,
missing/stale pending state, invalid actor/targets/scene/status, retries, malformed
token bounds, disabled provider, startup probe and consumed budget. Each test
asserts no callback and unchanged state. Used-budget control correctly reports its
pre-existing admission count of one; it adds none. Disabled mode is separately
verified as requested/effective false, and then restored.

These are local structural readiness assertions, not provider health or semantic
success. Existing durable admission enforcement remains the production owner.
Global accounting source-manifest staleness from R1-02 is still unresolved; no
global preflight PASS is claimed. A future runner must retain SDK retry cap zero,
exclusive process/store/ledger ownership, and invoke guarded_trial immediately
before its actual chat callback. This pass does not upgrade the old runner.
""",
"05_pending_action_control.md": """# 05 — Pending-Action Control

Base content: artifacts/atgb/atgb_r1_03/L4/before.json, copied without importing
experiments.pr_dq. The base's manually seeded pending context is removed.
Production game.api.chat receives 'I ask one of them what happened.' with a stubbed
NPC/QUESTION interpretation. Existing ambiguity/authority checks create the
pending ASK with two scene-local candidates, Sergeant Mara and Corporal Bren.
The model's suggested Mara target cannot override the ambiguous player wording.
World and turn counter remain unchanged during setup. Actor exists; candidates
are validated against the scene-local world catalog. No original ask executes.

The control then submits the unchanged frozen correction_pending text,
'Instead, make that a question about the lamp.', through production chat with a
stubbed GM/CORRECTION interpretation. Effective live interpretation is true so
the genuine interpretation/adaptation/orchestration path runs. It revises the
pending record with status pending and revised_text, returning 'revised' without
social resolution or authoritative gameplay execution. The before/after response
and full relevant state are in pending_control.json. This is a synthetic positive
control and structural evidence; not model semantic or human-realism evidence.

World (including factions/event log), clocks, turn, scene, character and combat
are unchanged. Only permitted conversation history, revision context and save
metadata differ. Separate direct-chat controls use all three unchanged frozen
mechanical inputs: pending revises, synthetic executed-state negative control
refuses undo, empty state asks what to change. Preflight rejects executed,
wrong-scene and invalid-target pending fixtures. No production safeguard changed.

Provider-failure stubs for APIConnectionError and InternalServerError both leave
pending/gameplay snapshots unchanged. These are deterministic failure-path
observations with zero actual requests/admissions. A future live control is
structurally supported; actual provider interpretation and useful revision
meaning remain unproven until separately authorized execution.
""",
"06_provider_failure_assessment.md": """# 06 — Provider Failure Assessment

Read-only evidence: R1-03 L1/L2 trace.json, response.json, accounting.json,
provider_usage.jsonl, before/after snapshots and execute_trial.py. Normalized
extraction is provider_assessment.json. No connectivity probes or provider calls.

L1: request_interpretation returned APIConnectionError / provider_failure before
any model response. Classification: transport failure. One admission and dispatch,
625.517 ms recorded dispatch latency, 1781.25 ms end-to-end; no request id or token
usage. Network restriction is a historical hypothesis, not established cause.
No exception cause chain, DNS/TLS/proxy diagnostics or transport response survives
in the selected evidence. Root cause unresolved.

L2: InternalServerError before any model interpretation. Classification: provider
failure (SDK server-error category); exact status/body/request id were not retained.
One admission/dispatch, 6519.199 ms dispatch latency, 7471.197 ms end-to-end.
No token usage. A provider-side error is supported; the service's underlying
failure and whether upstream intermediaries contributed remain unresolved.

Neither record shows local response-schema rejection or application parsing of a
completed model response. No supporting evidence attributes either to R1-02, which
is a downstream host-routing repair with no new provider call site. L4's import
leak explains its zero-call invalid control, not L1/L2.

R1-03 bounded real OpenAI clients to max_retries=0; each saved SDK-client record
confirms it. Application retries were disabled, no trial retry/continuation or model
switch occurred. The unchanged timeout owner defaults to 45 seconds, clamped 5–120;
current offline configuration evaluates to 45.0 seconds (SDK 2.48.0 installed).
Historical effective timeout/SDK version were not saved, so current observations
are not retroactive facts. Both durations are below the default; timeout causality
cannot be established. Usage accounting stopped after missing usage, correctly
keeping failed billing unknown rather than zero. No retry policy/config changes.

Precautions for separately approved continuation: fresh bounded process/store and
durable ledger per trial, max two application admissions, SDK retries zero, startup
probe skipped, mandatory local preflight, stop on provider error/unknown usage.
Capture nonsecret exception class/status/request id and cause category when
available. Do not add retries or switch models to obtain a passing response.
""",
"07_regression_evidence.md": """# 07 — Regression Evidence

Authoritative final command (PowerShell, repository root):

```powershell
.venv/Scripts/python.exe -m pytest tests/test_atgb_r1_04_readiness.py tests/test_atgb_r1_02_revision_boundary.py tests/test_state_authority.py -q --tb=short --basetemp=development/tmp/atgb_r1_04_release --junitxml=artifacts/atgb/atgb_r1_04/final.xml > artifacts/atgb/atgb_r1_04/final.txt 2>&1
$LASTEXITCODE | Set-Content artifacts/atgb/atgb_r1_04/final_exit.txt
```

Exit 0: 167 passed, zero failures/errors/skips. New readiness 36; existing R1-02
105; existing state-authority 26. One Starlette TestClient deprecation warning.
New tests cover import unset/enable/disable and reverse order in fresh subprocesses,
legacy import detection, normal/failure restoration, sequential modes, valid
pending production routing, preflight failures, three frozen mechanical correction
inputs through direct chat, and provider-failure no-execution safeguards.

Initial 28-test readiness slice passed. Expanded implementation and final model
assertions supersede that earlier count; intermediate final/verified runs also
passed. commands.json preserves exact initial, interrupted and final commands.
final.xml/final.txt/final_exit.txt are the authoritative completed record.

The existing HTTP authorization module was attempted together with R1-02 and state
tests. It stalled at the existing TestClient boundary and was interrupted with
Ctrl-C (tool process exit 1). No completed totals/JUnit file; no count of product
failures inferred. Progress output is retained in regression.txt. This matches
the prior reported environment limitation but its exact cause is not established.
No automatic timeout was configured. New subprocess isolation checks use explicit
30-second timeouts; none expired. Full repository regression was not run.

This is scoped structural regression evidence, not a full-suite green result or
proof of conversational adequacy. Existing frozen holdout data, expectations,
production orchestration, experimental candidates and unrelated tests unchanged.
""",
"08_final_verdict.md": """# 08 — Final Verdict

**B — Conditionally ready.** Core recovery succeeds: import-safe replacement
fixture/control, scoped restoration, fail-closed configuration gate, genuine
pending-action creation/revision, and all 167 targeted deterministic tests pass.
The legacy initializer is intentionally preserved; old R1-03 runner remains unsafe
and must not be reused. The new gate/control must be wired into a separately
reviewed future isolated live runner. This is a bounded validation-infrastructure
repair, not a global guarantee that arbitrary fixture imports are side-effect free.

Material limitations: HTTP authorization slice incomplete, global accounting
source manifest still stale, provider connection/server root causes unresolved,
reachability unprobed, no new live interpretation or semantic response evidence.
R1-02's original exact-wording result and conversational adequacy remain unproven
live. R1-03 L3's inadequate paraphrase and historical authority findings persist.
No full-suite, benchmark performance, independent generalization or playability claim.

Evidence distinctions for future trials: requested live/effective live from
preflight; explicit disabled mode from the same predicate; connection failure from
transport exception; provider failure from server-error response category; model
interpretation failure only after actual model output; host routing failure only
from captured decision trace with valid setup; execution/state mutation from
before/after snapshots and admission ledger. A setup failure is INVALID validation,
never a conversational model FAIL. These dimensions must remain separate.

A bounded ATGB-R1-05 live-validation continuation is justified for external review,
conditional on new explicit live authority and a runner using these safeguards.
Retain original/control trials and failures, no automatic retries or semantic
repair. Do not execute that continuation in this pass.

Confirmed: no live provider calls; no production conversational behavior modified;
frozen ATGB baseline unchanged; no experimental candidates integrated; no
unauthorized gameplay mutations during this pass; canonical player state unchanged;
credentials/secrets excluded and selected ZIP contents scanned. Stop after the
review ZIP; await external review before ATGB-R1-05. No commit/push.
""",
}
for name, body in reports.items():
    write("development/reports/atgb_r1_04/" + name, body)
write("development/reports/atgb_r1_04_validation_readiness_recovery.md",
      "# ATGB-R1-04 — Validation Readiness Recovery\n\n**B — Conditionally ready.** "
      "167 deterministic tests pass; no live calls. Structural-only evidence.\n\n" +
      "\n".join(f"- [{name[:2]} — {name[3:-3].replace('_', ' ')}](atgb_r1_04/{name})" for name in reports) +
      "\n\nEvidence: artifacts/atgb/atgb_r1_04/. Stop for external review before ATGB-R1-05.")

# Preserve prior orientation verbatim, then update only the active session pointer.
handoff = (OUT / "NEXT_SESSION_before.md").read_text(encoding="utf-8")
handoff = handoff.replace("Updated 2026-10-19 / ATGB-R1-03.", "Updated 2026-10-19 / ATGB-R1-04.")
notice = """ATGB-R1-04 validation-readiness recovery completed: **B — Conditionally ready**.
No live authority/calls. New import-safe gate/control: `tools/atgb/readiness.py`;
167 targeted deterministic tests pass (36 new, 105 R1-02, 26 state authority).
Pending ASK is generated by production chat with stubbed interpretation, then
revised without gameplay advancement. Preflight failures abort before callback.
Report: `development/reports/atgb_r1_04_validation_readiness_recovery.md`;
eight reports and exact commands/preflight/state evidence under their R1-04 owners.
Provider root causes remain unresolved. HTTP authorization slice interrupted at
existing TestClient boundary; no full-suite claim. Legacy experiment initializer
and R1-03 runner preserved; **do not reuse that runner**. Future isolated runner
must adopt the new gate/control, zero SDK retries and durable per-trial budget.
Await external review before ATGB-R1-05; live continuation requires separate explicit
authority. No semantic repair, frozen baseline edit or experimental integration.

### Prior R1-03 evidence (preserved historical context)

"""
handoff = handoff.replace("## Last work and recommended next action\n\n", "## Last work and recommended next action\n\n" + notice)
handoff = handoff.replace("No experimental integration. External review required before ATGB-R1-04. Proposed\nR1-04 is bounded validation-readiness recovery and missing original/control trials\nonly after renewed live authorization; no semantic repair authorized here.",
    "No experimental integration. R1-04 recovery is now completed without live calls;\noriginal/control live trials remain deferred pending R1-05 external review and\nexplicit live authorization. No semantic repair is authorized.")
handoff = handoff.replace("Stop for external review of ATGB-R1-03. This pass changed evidence/documentation\nonly. No frozen-baseline edit, added model authority, commit or push. Do not begin\nATGB-R1-04 without external review and renewed bounded live authorization.",
    "Stop for external review of ATGB-R1-04. This pass changed validation tooling,\ntests, documentation and evidence only. No production or frozen-baseline edit,\nadded model authority, commit or push. Do not begin ATGB-R1-05 or make live calls\nwithout external review and explicit bounded live authorization.")
write("docs/NEXT_SESSION.md", handoff)

# Diff only this pass's authored sources; exclude unrelated worktree modifications.
diff = ""
for name in ("tools/atgb/readiness.py", "tests/test_atgb_r1_04_readiness.py"):
    diff += "".join(difflib.unified_diff([], (ROOT / name).read_text().splitlines(True),
                                         fromfile="/dev/null", tofile="b/" + name))
diff += "".join(difflib.unified_diff((OUT / "NEXT_SESSION_before.md").read_text().splitlines(True),
    handoff.splitlines(True), fromfile="a/docs/NEXT_SESSION.md", tofile="b/docs/NEXT_SESSION.md"))
write("artifacts/atgb/atgb_r1_04/scoped_changes.patch", diff)
write("artifacts/atgb/atgb_r1_04/repository_status_after.txt",
      subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True))

c = json.loads((ROOT / "data/validation/review_handoffs/atgb_r1_03_controlled_live_validation.json").read_text(encoding="utf-8"))
c.update(campaign_id="atgb_r1_04_validation_readiness_recovery", campaign_name="ATGB-R1-04 Validation Readiness Recovery",
         campaign_date="2026-10-19", purpose="Validation infrastructure only; no live provider authority.",
         objective_status="B — CONDITIONALLY READY; EXTERNAL REVIEW REQUIRED",
         executive_summary="Import-safe replacement control and fail-closed gate demonstrated. 167 deterministic tests pass. HTTP slice incomplete; provider root causes unresolved. No production edits or live calls; all 3,996 protected entry files unchanged.",
         changes={"production": ["None."], "validation": ["36 new readiness tests; frozen mechanical correction inputs exercised through direct chat."],
                  "tooling": ["tools/atgb/readiness.py: scoped execution mode, checked imports, preflight, guarded callback, isolated control seed."],
                  "documentation": ["Eight reports, index, canonical NEXT_SESSION."], "generated_artifacts": ["Test, preflight, control state, provider assessment, preservation and selected-source export."]},
         testing={"focused": "167 passed; 36 new + 105 R1-02 + 26 state authority; exit 0; zero failed/skipped.",
                  "broader": "HTTP authorization slice interrupted at TestClient boundary; incomplete.", "full_suite": "Not run.",
                  "runtime_validation": "Direct production chat with stubbed interpretation; no live endpoint calls.",
                  "model_runtime_boundary": "No model execution; gpt-4.1-mini configuration inspected only.",
                  "new_regressions": "None in completed slice.", "pre_existing_failures": "HTTP environment limitation; global source manifest stale."},
         known_problems={"campaign_specific": ["Future live runner must use new gate/control; old runner remains historical and unsafe.", "Provider reachability and L1/L2 causes unresolved."],
                         "pre_existing": ["HTTP TestClient incomplete; source manifest stale; human assessment unattested; dirty worktree."]},
         decisions_requiring_human_review=["Review conditional readiness and whether to authorize bounded ATGB-R1-05 live continuation. No execution follows automatically."],
         missing_concepts=["No new gameplay owner proposed."],
         does_not_prove=["Provider health, live original/control success, model response adequacy, full-suite green, independent generalization or benchmark performance."],
         recommended_next_step="External review; separately authorize bounded ATGB-R1-05 using the new gate/control. Stop now; no live calls.",
         primary_report="development/reports/atgb_r1_04_validation_readiness_recovery.md", evidence_packets=[],
         self_contained_review_test="Eight reports, selected source/diffs, final JUnit/logs, preflight failures/success, state evidence, provider diagnosis and source hashes; CRC and secret scan.",
         configuration_source="data/validation/review_handoffs/atgb_r1_04_validation_readiness_recovery.json")
paths = ["development/reports/atgb_r1_04/" + name for name in reports]
paths += [p.relative_to(ROOT).as_posix() for p in OUT.iterdir() if p.is_file() and p.suffix in {".json", ".xml", ".txt", ".py", ".patch", ".md"}]
paths += ["tools/atgb/readiness.py", "tests/test_atgb_r1_04_readiness.py", "tests/test_atgb_r1_02_revision_boundary.py",
          "tests/fixtures/pr_ef_r4_holdouts.json", "docs/NEXT_SESSION.md", "docs/DEVELOPMENT_CONSTITUTION.md",
          "docs/validation_evidence_standard.md", "docs/product_realization_validation.md",
          "experiments/pr_dq/__init__.py", "tests/test_pr_du_player_pipeline.py", "tests/test_pr_ef_gm_authority.py",
          "tests/test_pr_ef_r4_authorization.py", "game/conversational_orchestration.py",
          "game/live_chat_interpretation.py", "game/semantic_interpreter.py", "game/provider_budget.py",
          "artifacts/atgb/atgb_r1_03/execute_trial.py", "development/reports/atgb_r1_03/05_failure_localization.md"]
for trial in ("L1", "L2"):
    paths += [f"artifacts/atgb/atgb_r1_03/{trial}/{name}" for name in ("trace.json", "accounting.json", "provider_usage.jsonl", "response.json")]
c["supporting_files"] = [dict(path=p, role="review_verification", why="R1-04 scoped recovery, failure provenance or deterministic evidence.",
                              behavioral_evidence=False, human_review_required=True) for p in sorted(set(paths))]
dump(c["configuration_source"], c)

# Secret values are read solely for equality scans; never printed or packaged.
from dotenv import dotenv_values
values = dotenv_values(ROOT / ".env")
secrets = [str(v).encode() for k, v in values.items() if v and len(str(v)) >= 8 and
           any(word in k.upper() for word in ("KEY", "SECRET", "PASSWORD", "TOKEN"))]


def scan(blob):
    assert not any(secret in blob for secret in secrets), "secret in selected export"
    assert not re.search(rb"\bsk-[A-Za-z0-9_-]{16,}", blob), "credential pattern in export"
    assert (b"-----BEGIN " + b"PRIVATE KEY-----") not in blob


for row in c["supporting_files"]:
    scan((ROOT / row["path"]).read_bytes())
from tools.build_review_handoff import build_handoff
now = datetime.now(timezone.utc)
backup = ROOT / "development/tmp/atgb_r1_04_previous_review"
backup.mkdir(parents=True, exist_ok=True)
for name in ("CURRENT_REVIEW.md", "CURRENT_REVIEW.zip", "REVIEW_MANIFEST.json"):
    source = ROOT / "handoff" / name
    if source.exists() and not (backup / name).exists():
        shutil.copyfile(source, backup / name)
result = build_handoff(c, root=ROOT, output_dir=OUT / "review_export", generated_at=now.isoformat(), archive_history=True)
with zipfile.ZipFile(result["zip_path"]) as z:
    assert z.testzip() is None
    for name in z.namelist():
        scan(z.read(name))
    manifest = json.loads(z.read("REVIEW_MANIFEST.json"))
    for row in manifest["included_files"]:
        if row.get("canonical_source_path"):
            assert hashlib.sha256(z.read(row["bundle_path"])).hexdigest() == row["sha256"]
    assert sum("/development/reports/atgb_r1_04/" in n and n.endswith(".md") for n in z.namelist()) == 8
    assert not any("/.env" in n or "/store/" in n for n in z.namelist())
# New York is UTC-4 on this date; avoid host timezone and optional tzdata dependency.
stamp = now.astimezone(timezone(timedelta(hours=-4))).strftime("%Y%m%d-%H%M%S")
dest = ROOT / "handoff" / f"CURRENT_REVIEW({stamp}).zip"
shutil.copyfile(result["zip_path"], dest)
assert dest.read_bytes() == Path(result["zip_path"]).read_bytes()
# Publish the generated stable alias via replacement, avoiding a Windows reader's
# open handle on the existing ZIP. Preserve its prior bytes in the backup above.
for name in ("CURRENT_REVIEW.md", "REVIEW_MANIFEST.json", "CURRENT_REVIEW.zip"):
    staged = ROOT / "handoff" / (name + ".r1_04_pending")
    shutil.copyfile(OUT / "review_export" / name, staged)
    staged.replace(ROOT / "handoff" / name)
print(json.dumps(dict(zip=str(dest), files=result["file_count"], bytes=result["zip_size_bytes"],
    verdict="B — Conditionally ready", tests=counts, integrity="3996 entry hashes unchanged; ZIP CRC/source hashes/secret scan passed",
    stop="Await external review; no ATGB-R1-05 or live calls."), indent=2))

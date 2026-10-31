"""Build bounded R1-07 evidence/reports and existing standard review export."""
import ast
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

OUT = Path(__file__).parent
REPORT = ROOT / "development/reports/atgb_r1_07"
REPORT.mkdir(exist_ok=True)
def write(path, value):
    path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2), encoding="utf-8")

files = ["game/live_chat_interpretation.py", "game/conversational_orchestration.py", "docs/NEXT_SESSION.md"]
diffs, sizes, checks = [], {}, {}
functions = {files[0]: ["request_interpretation"], files[1]: ["_pending_revision_decision"]}
for name in files:
    before = (OUT / ("before_" + Path(name).name)).read_text(encoding="utf-8")
    after = (ROOT / name).read_text(encoding="utf-8")
    delta = list(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile="entry/" + name, tofile="current/" + name))
    diffs.extend(delta)
    sizes[name] = {"added": sum(s.startswith('+') and not s.startswith('+++') for s in delta), "removed": sum(s.startswith('-') and not s.startswith('---') for s in delta)}
    for function in functions.get(name, []):
        old = next(n for n in ast.parse(before).body if isinstance(n, ast.FunctionDef) and n.name == function)
        new = next(n for n in ast.parse(after).body if isinstance(n, ast.FunctionDef) and n.name == function)
        checks[function + "_unchanged"] = ast.dump(old) == ast.dump(new)
write(OUT / "source.diff", ''.join(diffs))
write(OUT / "change_size.json", sizes)
hashes = json.loads((OUT / "protected_hashes.json").read_text(encoding="utf-8"))
checks.update(protected_files=len(hashes), changed_protected_files=[f for f, digest in hashes.items() if not (ROOT / f).is_file() or hashlib.sha256((ROOT / f).read_bytes()).hexdigest() != digest])
assert checks["changed_protected_files"] == []
assert checks["request_interpretation_unchanged"] and checks["_pending_revision_decision_unchanged"]
# Compare actual wire schema shapes, ignoring only documentation strings.
from game import live_chat_interpretation as live
namespace = {"__name__": "r1_07_entry_schema"}
exec(compile((OUT / "before_live_chat_interpretation.py").read_text(encoding="utf-8"), "entry_live.py", "exec"), namespace)
def strip_descriptions(value):
    if isinstance(value, dict):
        return {k: strip_descriptions(v) for k, v in value.items() if k != "description"}
    return [strip_descriptions(v) for v in value] if isinstance(value, list) else value
checks["schema_shape_unchanged"] = strip_descriptions(namespace["production_interpretation_schema"]()) == strip_descriptions(live.production_interpretation_schema())
assert checks["schema_shape_unchanged"]
write(OUT / "integrity_verification.json", checks)

base_modules = "tests/test_atgb_r1_02_revision_boundary.py tests/test_atgb_r1_04_readiness.py tests/test_pr_ef_gm_authority.py tests/test_pr_ea_conversational_orchestration.py tests/test_pr_eb_conversational_continuity.py tests/test_realization_authority.py tests/test_conversational_memory_window.py"
broad_modules = "tests/test_pr_do_authority_separation.py tests/test_pr_dh_live_interpretation.py tests/test_live_model_guard.py tests/test_realization_provenance.py"
commands = {
    "baseline": f".venv/Scripts/python.exe -m pytest {base_modules.replace('tests/test_pr_ea', 'tests/test_pr_ef_r4_authorization.py tests/test_pr_ea')} -q --basetemp=development/tmp/atgb_r1_07_before --junitxml=artifacts/atgb/atgb_r1_07/baseline.xml",
    "baseline_direct": f".venv/Scripts/python.exe -m pytest {base_modules} -k 'not production_ten_turn_sequence' -q --basetemp=development/tmp/atgb_r1_07_baseline_direct --junitxml=artifacts/atgb/atgb_r1_07/baseline_direct.xml",
    "focused": ".venv/Scripts/python.exe -m pytest tests/test_atgb_r1_07_correction_contract.py -q --basetemp=development/tmp/atgb_r1_07_focused --junitxml=artifacts/atgb/atgb_r1_07/focused.xml",
    "after": f".venv/Scripts/python.exe -m pytest tests/test_atgb_r1_07_correction_contract.py {base_modules} -k 'not production_ten_turn_sequence' -q --basetemp=development/tmp/atgb_r1_07_after --junitxml=artifacts/atgb/atgb_r1_07/after.xml",
    "broader": ".venv/Scripts/python.exe -m pytest tests/test_pr_do_authority_separation.py tests/test_pr_dh_live_interpretation.py tests/test_atgb_readiness.py tests/test_atgb_infrastructure.py tests/test_live_model_guard.py tests/test_realization_provenance.py tests/test_realization_layer_audit.py -q --basetemp=development/tmp/atgb_r1_07_broader --junitxml=artifacts/atgb/atgb_r1_07/broader.xml",
    "broader_direct": f".venv/Scripts/python.exe -m pytest {broad_modules} -vv -o faulthandler_timeout=30 --basetemp=development/tmp/atgb_r1_07_broader_direct --junitxml=artifacts/atgb/atgb_r1_07/broader_direct.xml",
    "broader_baseline": f".venv/Scripts/python.exe -m pytest {broad_modules} -vv -o faulthandler_timeout=30 --basetemp=development/tmp/atgb_r1_07_broader_baseline --junitxml=artifacts/atgb/atgb_r1_07/broader_baseline.xml",
}
results = []
for name, command in commands.items():
    xml = OUT / (name + ".xml")
    row = {"name": name, "exact_command": command, "output_capture": f"*> artifacts/atgb/atgb_r1_07/{name}.txt"}
    if xml.exists():
        suite = ET.parse(xml).getroot()[0]
        counts = {key: int(suite.get(key, '0')) for key in ("tests", "failures", "errors", "skipped")}
        row.update(passed=counts['tests']-counts['failures']-counts['errors']-counts['skipped'], failed=counts['failures'], errors=counts['errors'], skipped=counts['skipped'], exit_code=int((OUT / (name + '_exit.txt')).read_text(encoding="utf-8")), completed=True)
        row['failures'] = [{"test": case.get('classname') + '::' + case.get('name'), "message": fail.get('message')} for case in suite.findall('testcase') for fail in case.findall('failure')]
    else:
        row.update(passed_observed=72 if name == 'baseline' else 0, failed_observed=0, skipped_observed=0, final_counts=None, exit_code=1, completed=False,
            interruption="Ctrl-C via tool; no finalized JUnit. Baseline: 72 dots, 30%, next source-order test is HTTP production_ten_turn_sequence; no stack captured." if name == 'baseline' else "Ctrl-C via tool; empty captured output, no completed tests evidenced; stall point not localized. No completed broad-suite result.")
    if name == 'focused':
        row['note'] = '25 initial new tests; four direct API cases subsequently added and passed in after.xml (29 new total).'
    if name == 'broader_baseline':
        row['note'] = 'Executed by compare_broader_baseline.py with entry bytes; finally restored repaired bytes. Same failure and counts as broader_direct.'
    results.append(row)
write(OUT / "test_commands.json", results)
table = '\n'.join(f"| {r['name']} | {r.get('passed', str(r.get('passed_observed')) + ' observed')} | {r.get('failed', '0 observed')} | {r.get('skipped', '0 observed')} | {r['exit_code']} | {'complete' if r['completed'] else 'interrupted; totals unknown'} |" for r in results)
locations = {}
for name in files[:2]:
    lines = (ROOT / name).read_text(encoding="utf-8").splitlines()
    needles = ["def production_interpretation_schema", "Specialize the legacy", "Ordinary conversational correction", "Recover the underlying question", "Receipt only", "def _pending_revision_decision"]
    locations.update({needle: f"{name}:{i}" for i, line in enumerate(lines, 1) for needle in needles if needle in line})
write(OUT / "modified_locations.json", locations)

reports = {
"01_baseline_and_scope.md": """# 01 — Baseline and Scope

Entry HEAD b012c3d7e5887fdfb09d10bb9cc0f0220de09df9, branch feature/product-realization. Extensive dirty/untracked work predates this pass, including both changed production files, gameplay saves, governance and artifacts. Full entry status and exact entry copies of edited files are packaged. This pass is measured against entry bytes, not HEAD.

Read DEVELOPMENT_CONSTITUTION, canonical NEXT_SESSION, validation_evidence_standard, product_realization_validation and review_handoff_standard. Requested support/docs/NEXT_SESSION.md does not exist in this checkout; it is an export-relative path, so canonical docs/NEXT_SESSION.md was used. No AGENTS.md was found by repository rg search.

Reviewed R1-02 routing contract/tests, R1-03 failure localization/raw L3, R1-04 pending control/readiness tests, R1-05 failure localization/raw L1/L2, and R1-06 schema, evidence, host, causal verdict and repair proposal. R1-06 is the causal authority: primary class contract; wording causality remains a hypothesis. Raw L3 reaches revision guard and gets null; older contrary summary remains historical.

Production owners confirmed: live_chat_interpretation.production_interpretation_schema and interpret_production_turn; legacy schema/modes in experiments/pr_do/schema.py and experiments/pr_dr/prompt.py (already existing production dependencies); public_conversation_evidence and _communication_decision in conversational_orchestration; API retained-record reconsideration and immutable final delivery; _pending_revision_decision for mechanical revision. No experimental integration performed.

Authorized scope: existing interpretation/schema descriptions, evidence guidance, necessary answer-branch receipt, deterministic checks, offline replay and reports/export. No provider calls, extra passes, classifiers, clarification veto, persistent state, mechanical redesign, frozen corpus edits, unrelated refactors, commits or pushes.
""",
"02_interpretation_contract_repair.md": """# 02 — Interpretation Contract Repair

Previously purpose CORRECTION meant revising unexecuted intent. Legacy user guidance included referent correction under OUT_OF_CHARACTER_CORRECTION and called CLARIFICATION an unclear utterance; production also used that purpose for a player's request to explain NPC speech. These meanings were not adequately separated.

Production purpose description now includes correcting conversational meaning, subject, referent or description. Production instructions explicitly distinguish the player clarifying their own meaning from the AI-DM requesting more information. A resolved ordinary correction uses INTERPRETED, GM/CORRECTION, legacy OTHER, correction.subject REFERENT, and no action components. It continues the conversation without redundant confirmation. A targeted question remains permitted for competing referents, missing interlocutor/parameter or conflicting intentions. Player requests for explanation can retain NPC/CLARIFICATION without requiring legacy CLARIFICATION.

The existing production message assembly specializes only its legacy Communication modes line; experimental prompt source is unchanged. No enum, key, required property or structural constraint changes. Schema shape comparison strips documentation only and passes. Mechanical revision still needs an actual eligible pending intention and host authorization; executed actions cannot be undone. Existing revision guard is AST-identical to entry. Locations and exact entry-relative diff are in modified_locations.json and source.diff.
""",
"03_evidence_selection_repair.md": """# 03 — Evidence-Selection Repair

Previously the instruction only selected passages when they answered the question and treated no evidence as unknown. It lacked positive guidance to recover an elliptical corrected question and did not exempt no-fact acknowledgments clearly.

The contract now recovers the underlying question/request from available context with the corrected meaning, selects relevant authorized PUBLIC evidence_refs and prefers a supported answer over redundant clarification. It explicitly forbids restricted/unestablished internal state and unsupported inference. With insufficient evidence it states a limitation, uses only established information, or asks a genuinely needed targeted question. No-fact acknowledgments may still use [].

public_conversation_evidence, evidence membership validation and selected-only public_evidence projection are unchanged. Hidden clue test confirms no private identity in requests; private reference is rejected. No model relevance guarantee is inferred from string-key membership. Historical visible:1/2/3 remain available in each regenerated request; explicit substitution selects those passages only, avoiding repetition of full weather-containing reply:0. No hardcoded gate/people selection exists in production.
""",
"04_response_continuation.md": """# 04 — Response Continuation

Source inspection established that the existing _communication_decision answer branch joins unique selected public passages verbatim and API delivery preserves its text. Schema has no acknowledgment prose field. Contract edits alone therefore could select evidence, but could not produce a brief receipt on this branch without putting prose into a fact/subject field. A minimal production change was necessary and implemented there.

After earlier mechanical control/ambiguity branches, an answer gets 'Understood. ' only for GM/CORRECTION, INTERPRETED, zero operations, no unresolved references, correction.subject REFERENT, nonempty selected refs all present in answer evidence, and a nonempty answer. This is a receipt for the supplied resolved interpretation, not a new classifier or necessity veto. It does not assert the corrected subject as a world fact. Evidence is joined once by the existing deduplication path. Other CORRECTION records, insufficient evidence, ambiguous/status-unresolved records and mechanical revision do not get the receipt.

Three unrelated-vocabulary synthetic corrections test subject/referent/description continuation. Direct chat checks verify final delivery, unknown limitation, private-reference rejection and targeted ambiguity question. No new call or narration subsystem; no mechanical response change. The host still relies on the supplied interpretation's semantic accuracy; live adequacy is unproven.
""",
"05_deterministic_validation.md": """# 05 — Deterministic Validation

29 new checks inspect actual production messages/schema and exercise stubbed wire -> adapter -> host decision, including four direct chat deliveries. Contract C1-C7 cover conversational/mechanical distinction, player versus GM clarification, continuation, corrected-question public evidence, necessary ambiguity, restricted facts and actual pending authority. Tests use production construction, not a duplicate contract fixture. Behavioral coverage includes subject/referent/description, insufficient/private evidence, unresolved correction and no-fact withdrawal acknowledgment. Existing R1-02/R1-04 tests cover genuine pending revision, absent pending and executed-action prohibition.

Offline replay script executes six arms over R1-05 L1/L2 and R1-03 L3: preserved output and explicit substituted answer interpretation. Both use current production request assembly. Original outputs still clarify; substitution accepts OTHER/INTERPRETED GM/CORRECTION, projects visible:1/2/3 and emits a receipt plus their text with no context update/execution. Full requests, schema, records and decisions are in offline_replay.json. Input snapshots are unchanged. This is a host counterfactual, not a model selection result or new live result. Direct chat tests separately verify final API delivery; replay itself stops at decision text.

Evidence packet: artifacts/validation_evidence/atgb_r1_07/, six synthetic offline arms, structural/runtime claims only; human review UNREVIEWED. No semantic scoring, independent held-out result or benchmark performance claim. Exact commands, failures and output capture paths: test_commands.json; logs and JUnit included.

| Run | Passed | Failed | Skipped | Exit | Completion |
|---|---:|---:|---:|---:|---|
""" + table + "\n\nReplay command: `.venv/Scripts/python.exe artifacts/atgb/atgb_r1_07/replay.py`; exit 0, six arms validated, no pytest pass count. Baseline comparison wrapper command: `.venv/Scripts/python.exe artifacts/atgb/atgb_r1_07/compare_broader_baseline.py`; exit 0; inner pytest exit 1 preserved.\n",
"06_regression_and_authority.md": """# 06 — Regression and Authority

Same main existing slice: 209/0/0 before; 209/0/0 after, plus 29 new passes (238 total), one HTTP ten-turn test explicitly deselected in both completed runs. R1-02 conversational corrections cannot acquire mechanical control; valid MOVE/ATTACK/ASK revisions remain pending; no-pending/wrong-scene/executed cases retain existing guards. R1-04 uses a production-created ambiguous ASK, not fabricated pending work; it remains nonexecuting. Direct chat snapshots preserve world, scene, character, combat, turn, clocks and pending/executed records; conversational history/save timestamps may change as allowed.

Broader completed slice 23 passed / 1 failed / 0 skipped, exit 1. Same command family with exact entry production bytes also 23/1/0, exit 1. Failure: test_realization_provenance.py::test_call_gpt_provider_failure_metadata_has_provider_family. Autouse LiveModelCallForbidden blocks game.gm.call_gpt; no provider is contacted. Its preexistence is experimentally reproduced, not assumed. Logs/JUnit and baseline restoration script included. No repair to unrelated tests/guards.

Two broader attempts interrupted: initial main+HTTP attempt showed 72 dots/30% before stalling; the subsequent wider collection produced no captured progress. No final totals or completed full-suite claim. Interrupt status 1 is tool termination, not a product test failure count. Source-order inference points to production_ten_turn_sequence for the initial stall; no stack proves it. HTTP authorization/transport coverage remains limited. No silent exclusions or inferred full-suite green.

Existing R1-04 tests write their old generated pending_control.json. Validation changed that file; it was restored from handoff/CURRENT_REVIEW(20261019-052942).zip with SHA-256 matching entry exactly. The restoration record is packaged. All 1,047 protected entry files (canonical data including frozen corpus, experiments, prior ATGB artifacts; cache excluded) now match. Existing R1-02 guard and provider request function remain AST-identical. Disclosure projection unchanged; invalid private refs rejected, hidden clue absent from request and output.
""",
"07_change_review.md": """# 07 — Change Review

Production changes: game/live_chat_interpretation.py (purpose description and bounded production-only guidance) and game/conversational_orchestration.py (resolved correction receipt at existing answer join). New tests: tests/test_atgb_r1_07_correction_contract.py. Canonical session orientation updated. Eight reports, offline diagnostic/review scripts, captured evidence and standard handoff exports generated. Entry-relative source.diff, change_size.json and modified_locations.json are packaged; HEAD diff includes pre-existing work and is not this pass's implementation diff.

No new schema structure, classifier, clarification veto, additional interpretation/generation call, persistent state, context enlargement, referent architecture or mechanics. No PR-EG candidate merged. Actual request dispatch and pending revision owner unchanged. Existing production dependencies with experimental names were inspected, not introduced. No unrelated production edits or commits/pushes.

Validation's generated historical pending_control.json side effect was restored byte-for-byte (report 06). Extensive pre-existing worktree changes remain; only generated current review mirrors are intentionally replaced per standard. Full statuses and protected hashes included. Scratch/pytest output stays in development/tmp, reports in development/reports, evidence in artifacts.

Remaining risks: wording effect on the live model and 320-token output budget is unmeasured; OTHER still returns a retained SAFE_ABSTENTION record before existing conversational reconsideration; semantic interpretation can remain wrong; public-reference membership does not prove answer relevance; existing explicit revision cues retain their previous limits. The receipt is generic and deliberately contributes no world facts. No full HTTP, full suite, semantic adequacy or independent generalization claim.
""" + '\nEntry-relative sizes:\n\n```json\n' + json.dumps(sizes, indent=2) + '\n```\n',
"08_final_verdict.md": """# 08 — Final Verdict

**B — Conditional.** Bounded implementation and 29 new deterministic checks pass; all 209 existing main-slice checks retain their passing baseline. Broader 23/1 result exactly reproduces the entry-source failure. No new relevant regression is demonstrated. HTTP coverage and two incomplete attempts are meaningful validation limitations; live model selection remains intentionally untested, not a reason to claim a live repair.

Primary failure class remains contract. Implementation completion is established within tested scope. Original live reproduction, related live variation, independent generalization and benchmark performance are not established. Six offline arms demonstrate unchanged historical clarification versus explicit answer-interpretation acceptance. All evidence is unreviewed by an authenticated human.

Recommend one separately authorized bounded ATGB-R1-08: four independently isolated direct production-chat trials using the R1-04/05 readiness boundary: original exact S08.2 twice, saved L3 paraphrase once, and the existing production-created ambiguous ASK followed by frozen pending correction once. Preserve frozen corpus and old artifacts. Use the existing model/output cap and one interpretation admission per measured turn, at most four measured admissions; no extra response generation, retry, continuation or automatic expansion. Record readiness, exact messages/schema, full model JSON, evidence candidates/selection, host/final output equality, before/after authority state, returned model, usage/errors and latency. Evaluate recognition, disposition, evidence relevance, adequacy and authority separately; authenticated human review required before performance claims. Stop on authority failure/provider error, preserve evidence, no automatic retry. This is original/related validation plus authority control, not independent generalization or a new benchmark score. Do not execute without new live authority.

Explicit confirmations: no live provider calls; no new provider-call pathways; no unauthorized gameplay-state mutations; no experimental PR-EG candidates merged; frozen ATGB baseline unchanged; mechanical revision authority preserved; no credentials or secrets included. Protected hashes and unchanged-function checks support the code/state claims. Selected review payload is scanned and hash/CRC verified by packaging. No commits or pushes.

Stop after generating the review ZIP and await external review before ATGB-R1-08.
""",
}
for name, text in reports.items():
    write(REPORT / name, text)

status = subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True)
write(OUT / 'repository_status_after.txt', status)
config = {
    'campaign_id': 'atgb_r1_07', 'campaign_name': 'ATGB-R1-07 Conversational Correction Interpretation and Supported Answer Continuation', 'campaign_date': '2026-10-19',
    'purpose': 'Bounded production contract repair and deterministic validation; zero live authority.', 'objective_status': 'B — Conditional; stop for external review',
    'executive_summary': 'Existing interpretation guidance distinguishes supplied correction from GM clarification and mechanical revision, selects evidence for the corrected question, and the existing answer join acknowledges resolved supported corrections. Main 238/0; broader 23/1 reproduces entry-source failure. Live model adequacy unproven.',
    'changes': {'production': ['Production-only schema descriptions/instructions and guarded answer-branch receipt.'], 'validation': ['29 new focused checks; 209 existing checks; six offline replay arms.'], 'tooling': ['Offline evidence/review scripts only.'], 'documentation': ['Eight reports and canonical NEXT_SESSION.'], 'generated_artifacts': ['Diffs, logs, JUnit, replay requests/results, hashes and ZIP.']},
    'testing': {'focused': '238 passed including 29 new, zero failed/skipped; 1 HTTP test deselected.', 'broader': '23 passed, 1 failed; same failure with entry source.', 'full_suite': 'Not completed; two interrupted attempts documented.', 'runtime_validation': 'Stubbed direct production chat and offline interpretation/decision paths only.', 'model_runtime_boundary': 'Zero live provider calls; constructor guard active.', 'new_regressions': 'None demonstrated in completed relevant slice.', 'pre_existing_failures': 'Provider-metadata test blocked by live-model guard, reproduced on entry bytes.'},
    'known_problems': {'campaign_specific': ['Live selection unproven; HTTP/full-suite limits; incomplete attempts.'], 'pre_existing': ['Conversational competence and authenticated benchmark scoring remain unestablished.']},
    'decisions_requiring_human_review': ['Review bounded change and conditional verdict before authorizing proposed R1-08.'], 'missing_concepts': [],
    'does_not_prove': ['Live repair effect, benchmark improvement, semantic generalization, independent held-out performance or full-suite green.'],
    'recommended_next_step': 'Stop for external review. Only separately authorize report 08 bounded ATGB-R1-08; do not execute now.',
    'primary_report': 'development/reports/atgb_r1_07/08_final_verdict.md', 'evidence_packets': ['artifacts/validation_evidence/atgb_r1_07'],
    'self_contained_review_test': 'Eight reports, entry-relative diffs, production/test source, commands/logs/JUnit, replay requests/records/decisions, state hashes and conditional verdict included.',
    'configuration_source': 'artifacts/atgb/atgb_r1_07/review_config.json', 'supporting_files': [],
}
support = [*REPORT.glob('*.md'), *(ROOT / f for f in files), ROOT / 'tests/test_atgb_r1_07_correction_contract.py', ROOT / 'tests/test_atgb_r1_02_revision_boundary.py', ROOT / 'tests/test_atgb_r1_04_readiness.py']
support += [f for f in OUT.iterdir() if f.is_file() and f.name != 'review_config.json']
for path in support:
    config['supporting_files'].append({'path': path.relative_to(ROOT).as_posix(), 'role': 'bounded_implementation_evidence', 'why': 'Explicit R1-07 review support.', 'behavioral_evidence': path.name == 'offline_replay.json', 'human_review_required': True})
config['supporting_files'].append({'path': 'artifacts/atgb/atgb_r1_07/review_config.json', 'role': 'configuration_provenance', 'why': 'Exact explicit bundle selection.'})
write(OUT / 'review_config.json', config)
print('Reports and evidence ready; invoke standard generator separately after final inspection.')

"""Build a bounded, sanitized PR-PLAY-20 review package; never run gameplay."""
import difflib
import hashlib
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/pr_play_20"
sys.path.insert(0, str(ROOT))


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def report(name, text):
    (OUT / ("PR_PLAY_20_" + name + ".md")).write_text(text.strip() + "\n", encoding="utf-8")


def paths(value, prefix=""):
    result = set()
    if isinstance(value, dict):
        for key, item in value.items():
            p = f"{prefix}.{key}" if prefix else key
            result.add(p)
            result.update(paths(item, p))
    elif isinstance(value, list):
        for item in value:
            result.update(paths(item, prefix + "[]"))
    return result


run = Path("artifacts/atgb/pr_play_19/live/20261101T155921Z-dece64b94204")
historical = read(run / "reports/result.json")
step = next(s for s in historical["steps"] if s["action"] == "start_campaign")
body = step["response"]
authority = read(run / "after/persistent/campaign.json")
before_public = read(run / "baseline/api_state.json")["public_state"]
after_public = read(run / "after/api_state.json")["public_state"]
secret = body["campaign"]["character_secret"]["hidden_truth"]
from game.state_channels import deep_project_public_payload
projected = deep_project_public_payload(body)
removed_historical = sorted(paths(body) - paths(projected))
save("pr_play_19_structural_verification.json", {
    "source": str(run / "reports/result.json"), "action": step["action"], "http_status": step["http_status"],
    "request_mode": "default player; scenario request supplies no privileged mode",
    "response_structure": {"ok": True, "gm_output": {"player_facing_text": "[PUBLIC OPENING]"},
                           "campaign": {"character_secret": {"hidden_truth": "[REDACTED]"}},
                           "session": "[STATE]", "world": "[STATE]", "resolution": "[OPENING]"},
    "field_path": "campaign.character_secret.hidden_truth", "nonempty": bool(secret),
    "matches_authoritative_campaign": secret == authority["character_secret"]["hidden_truth"],
    "absent_before_public": secret not in json.dumps(before_public),
    "absent_after_public": secret not in json.dumps(after_public),
    "absent_projected_response": secret not in json.dumps(projected),
    "nonpublic_paths_in_response": removed_historical,
})
baseline = read("artifacts/pr_play_20/baseline_response.json")
fixed = read("artifacts/pr_play_20/repaired_response.json")
baseline_summary = read("artifacts/pr_play_20/baseline_summary.json")
fixed_summary = read("artifacts/pr_play_20/offline_summary.json")
save("compatibility_comparison.json", {
    "removed_paths": sorted(paths(baseline) - paths(fixed)),
    "added_paths": sorted(paths(fixed) - paths(baseline)),
    "flat_top_level_structure_preserved_for_public_fields": set(deep_project_public_payload(baseline)) == set(fixed),
    "opening_text_identical": baseline["gm_output"]["player_facing_text"] == fixed["gm_output"]["player_facing_text"],
    "initialization_summary_identical": baseline_summary["before"] == fixed_summary["before"] and baseline_summary["after"] == fixed_summary["after"],
    "known_nondeterminism": "run IDs, timestamps, elapsed times and object IDs differ between isolated runs",
})
api = (ROOT / "game/api.py").read_text(encoding="utf-8")
before = (OUT / "api_before.py").read_text(encoding="utf-8")
diff = "".join(difflib.unified_diff(before.splitlines(True), api.splitlines(True),
                                    fromfile="game/api.py (session baseline)", tofile="game/api.py (PR-PLAY-20)"))
test_before = (OUT / "turn_tests_before.py").read_text(encoding="utf-8")
test_after = (ROOT / "tests/test_turn_pipeline_shared.py").read_text(encoding="utf-8")
diff += "".join(difflib.unified_diff(test_before.splitlines(True), test_after.splitlines(True),
                                   fromfile="tests/test_turn_pipeline_shared.py (session baseline)",
                                   tofile="tests/test_turn_pipeline_shared.py (PR-PLAY-20)"))
(OUT / "source_changes.diff").write_text(diff, encoding="utf-8")
refs = {}
for file, names in {
    "game/api.py": ["compose_state", "_project_state_for_ui_mode", "_project_player_runtime_response", "api_action", "api_chat", "start_campaign", "_start_campaign_response", "_start_campaign_after_admission", "_complete_opening_turn_persistence_like_chat", "get_state"],
    "game/api_turn_support.py": ["_build_turn_response_payload"],
    "game/state_channels.py": ["deep_project_public_payload", "is_author_key", "is_debug_key"],
    "game/api_ui_mode.py": ["resolve_requested_ui_mode"],
}.items():
    lines = (ROOT / file).read_text(encoding="utf-8").splitlines()
    for name in names:
        refs[name] = f"{file}:{next(i for i, line in enumerate(lines, 1) if line.startswith('def ' + name + '('))}"
save("source_references.json", refs)

report("DISCLOSURE_RECONSTRUCTION", f"""
# PR-PLAY-20 disclosure reconstruction

Confirmed historical disclosure: `POST /api/start_campaign`, default player mode, HTTP 200,
`response.campaign.character_secret.hidden_truth`. The response contains a broad flat state bundle
alongside `ok`, `gm_output` and `resolution`; this is not the `/api/state` envelope.

Evidence: `{run}/reports/result.json`, `steps[2].response`; after/persistent/campaign.json;
baseline/api_state.json and after/api_state.json. The hidden value is nonempty, matches the persisted
campaign, and is absent from both public-state captures. Only structural evidence is exported in
pr_play_19_structural_verification.json; real secret values and original historical payloads are excluded.

`{refs['_build_turn_response_payload']}` reads `compose_state()` and constructs
`{{'ok': True, 'gm_output': gm, **state}}`. It does not invoke the public projection.
The opening persistence tail replaces the GM output with its canonical internal object and enriches
metadata before returning. Consequently filtering only the initial GM object would be insufficient.

Baseline offline reproduction used the actual FastAPI route via TestClient and the real opening
provider/parser/renderer path with an SDK constructor stub returning a valid presentation plan.
HTTP 200 included `PR_PLAY_20_HIDDEN_SENTINEL`; public state excluded it; authority retained it.
Nested campaign internal state, world internal state, scene hidden facts and synthetic hidden NPC/quest
records also appeared. See baseline_summary.json, baseline_response.json and baseline_test.txt.
The baseline regression failed at the nested hidden-record assertion after recording the response.

Historical structural comparison also identifies nonpublic scene/session/debug paths in the same
successful response; paths are preserved without their values. UI display of these fields was not tested.
The fixture proves the response boundary under the established key-based policy, not semantic secrecy
of arbitrary strings or unclassified keys. No live-provider reconstruction was attempted.
""")

report("RESPONSE_PATH", f"""
# PR-PLAY-20 response path

| Stage | Source / function | Input -> output; representation and consumer |
| --- | --- | --- |
| Admission | `{refs['start_campaign']}`, `{refs['_start_campaign_response']}` | HTTP Request -> player-mode admission, preflight gate and opening scope; denies author/debug runtime actions |
| Initialization | `{refs['_start_campaign_after_admission']}` | persisted campaign/session/world -> engine opening resolution and prompt; authoritative, internal |
| Publication | `{refs['_complete_opening_turn_persistence_like_chat']}` | accepted GM output -> committed session/world/log and canonical narration; internal full object |
| State retrieval | `{refs['compose_state']}` | engine storage -> full state plus derived public UI/journal fields; mixed visibility, internal until projected |
| Initial packaging | `{refs['_build_turn_response_payload']}` | GM + optional resolution + full state -> flat mixed payload; raw `**state` is original disclosure entry |
| Enrichment | opening persistence tail | canonical GM replacement + emission metadata + log persistence -> completed internal response |
| Repaired boundary | `{refs['_project_player_runtime_response']}` | complete dict or JSONResponse -> recursively public copy, preserving rejection HTTP status and headers |
| JSON serialization | FastAPI response serialization / Starlette JSONResponse | public result -> UTF-8 JSON response consumed by browser |
| State reads | `{refs['get_state']}`, `{refs['_project_state_for_ui_mode']}` | full snapshot -> `public_state` plus selected explicit lane; previously already projected |

The confirmed mechanisms are direct full-state merging and bypass of the public projection (A/B/C in
the mission taxonomy). There is no evidence that this was a debug response accidentally selected for
player mode. The current projection itself excludes `hidden_truth` by its `hidden_` prefix.

Existing client contract: static/app.js consumes top-level gm_output.player_facing_text and resolution
from runtime responses, then refreshes `/api/state`. State reads consume the public_state envelope.
The repair keeps flat runtime fields, including public campaign/character/session/world/scene/UI,
journal, save/snapshot and campaign synchronization metadata. It introduces no new response envelope.
""")

report("REPAIR_REPORT", """
# PR-PLAY-20 repair report

Root cause: an internal mixed-visibility state bundle was treated as a finished player HTTP response.
The existing `/api/state` projection was never applied to successful turn packaging, and opening
enrichment could restore internal GM fields after initial packaging.

Production modification: game/api.py adds `_project_player_runtime_response` and applies it at the
three final HTTP response boundaries: start_campaign, api_action and api_chat. A small internal
`_start_campaign_response` extraction lets all start rejection returns share the same boundary.
It reuses `deep_project_public_payload`, processing GM output, resolution, nested lists and state
together after enrichment. JSONResponse rejection status, headers and background callbacks survive;
content-length is recalculated. No visibility rules were added or weakened.

Tests added: tests/test_pr_play_20_response_confidentiality.py. Existing test_start_campaign_api.py
now expects emission diagnostics to remain in the debug log lane rather than the player response.
The directly related tests/test_turn_pipeline_shared.py now obtains diagnostic assertions from persisted
engine logs/session separately; it no longer relies on debug data in player HTTP responses.
source_changes.diff isolates this pass from preexisting working-tree api.py edits. No commit/push.

No renderer, prompt, schema, provider contract, model, budget, narration or authority mutation changed.
The full internal turn helpers remain usable by engine diagnostics and persisted logs. Projection
creates a new tree without removing engine secrets. Tests compare the whole campaign document and
the injected world subtrees before/after HTTP response generation; all survive unchanged.

Compatibility: public flat state fields, public_hint inside character_secret, public NPC/quest labels,
opening narration, initialization flags and turn counter survive. Baseline/repaired opening text and
initialization summaries match. compatibility_comparison.json lists removed and added paths. Removed
paths are author/debug classified under the existing policy, including emission diagnostics; diagnostic
consumers must use the established debug log/state surfaces. No legitimate public field is intentionally
removed. Run IDs and times vary naturally across independent fixture runs.

Limitations: key-based policy treats unknown keys as public and cannot infer secret semantics in text.
Existing client-selected privileged read lanes have no authentication check at this API boundary.
That separate authorization issue is documented, not redesigned. Seventeen older opening/turn pipeline tests fail
with and without projection; no unrelated gameplay repairs were made.
""")

report("RELATED_PATHS", """
# PR-PLAY-20 directly related paths

| Path | Finding / validation |
| --- | --- |
| POST /api/start_campaign success | Confirmed raw-state disclosure; repaired at completed response boundary; synthetic serialized HTTP regression passes |
| POST /api/start_campaign already started | Existing public_state envelope was safe; 409 preserved, no sentinel; now additionally passed through shared boundary |
| POST /api/start_campaign invalid plan | 422, no publication/commit; no sentinel, error diagnostics preserved |
| POST /api/action success | Same raw shared turn helper; confirmed broader leak mechanism; now public projection at HTTP adapter; roll initiative regression passes |
| POST /api/action rejection | Existing unsupported-action error has no state; error text and status preserved |
| POST /api/chat | Success and early nonmutating returns now use final projection; direct raw-compose combat rejection branches also covered by boundary regression |
| GET /api/state | Existing recursive public projection; sentinel absent; no production change |
| GET /api/log, /api/debug_trace | Read only for lane analysis; player log exposes narration/input only; debug reads selected by ui_mode |

The ordinary raw-state rejection test deliberately isolates routing by stubbing `chat` to return the
same compose_state representation used by the inspected combat rejection branches. This tests the
actual HTTP adapter/serializer but does not claim end-to-end combat-routing coverage. Actual negative
opening and unsupported-action routes are also exercised without a response stub.

Additional disclosures: successful ordinary action responses share the campaign/world/scene/session
raw-state exposure. The two chat combat-rejection branches merge compose_state directly; source
inspection confirms the mechanism, while HTTP boundary regression establishes final exclusion.
Nonpublic GM emission metadata also traveled in player responses and is now excluded.

Authorization concern for external review: `resolve_requested_ui_mode` trusts query/body mode values;
`GET /api/state?ui_mode=author` returns author_state (including the synthetic secret), and debug reads
likewise rely on mode selection. UI mode is a capability selector, not an authenticated identity.
Runtime requests with author/debug mode are denied (403), including attempts to select a privileged
start response. No new privileged mode or bypass was introduced. Existing privileged read behavior
is preserved as required; authentication/network exposure must be reviewed before untrusted players
can access the server. This prevents an unconditional safe-for-player-deployment verdict.

Scope stayed at related response/lane boundaries. No unrelated admin/infrastructure audit was run.
Secondary malformed telemetry classification: no diagnostic correction was required at these boundaries;
provider parsing and opening validation were left unchanged. Its cause remains a follow-up, not a claim
of this repair.
""")

results = (OUT / "test_results.txt").read_text(encoding="utf-8-sig")
def failed_nodes(text):
    return sorted(line.removeprefix("FAILED ").split(" - ")[0]
                  for line in text.splitlines() if line.startswith("FAILED "))

expected = sorted(failed_nodes((OUT / "preexisting_start_tests.txt").read_text(encoding="utf-8-sig")) +
                  failed_nodes((OUT / "preexisting_turn_tests.txt").read_text(encoding="utf-8-sig")))
observed = failed_nodes(results)
assert observed == expected, "Investigate changed regression failures before packaging"
assert not any("pr_play_20_response_confidentiality" in node for node in observed)
save("preexisting_failure_comparison.json", {"expected_preexisting_failure_count": len(expected),
     "final_failure_count": len(observed), "identical_failure_node_ids": expected == observed,
     "failure_node_ids": observed, "focused_cases": 5, "focused_failures": 0})
summary_lines = [line for line in results.splitlines() if re.search(r"\d+ (passed|failed)", line)]
report("TEST_RESULTS", f"""
# PR-PLAY-20 test results

Command (offline): `.venv/Scripts/python.exe -m pytest tests/test_pr_play_20_response_confidentiality.py
tests/test_pr_play_18_contract_alignment.py tests/test_pr_play_13_opening_renderer.py
tests/test_pr_play_04_opening_integrity.py tests/test_start_campaign_api.py tests/test_state_channels.py
tests/test_ui_mode_backend_integration.py tests/test_ui_mode_policy.py tests/test_turn_pipeline_shared.py
tests/test_frontend_ui_mode_hardening_objective15.py tests/test_ui_mode_regression_matrix_objective15.py --tb=short`.

Result: {'; '.join(summary_lines)}. Full output: test_results.txt.

Focused regression mapping: A/B/C/D/E successful_start_serialized_boundary; F ordinary action success;
G ordinary rejection plus rejected_turn_with_composed_state; H invalid presentation plan and repeated
start; I player state retrieval; J established author/debug reads preserved and runtime mode denial.
The focused file has five collected cases, all passing. Serialized text is checked for the sentinel
anywhere, and complete response dictionaries must equal the recursive public projection.

Offline end-to-end initialization enters the real application lifespan and FastAPI HTTP route with
temporary storage. The real provider request builder/parser and engine renderer run; only SDK transport
is stubbed using PR-PLAY-18's helper. One mock presentation-plan dispatch occurs, opening publishes once,
one turn commits, public synchronization fields survive, and repeats return 409 without another dispatch.
Original and repaired narration and initialization summaries match (compatibility_comparison.json).

Provider/network controls: pytest live-model guard, skipped startup preflight, SDK constructor stub,
and external socket-connect denial in the new fixtures. Windows asyncio's internal loopback socketpair
is allowed. No real provider request occurred. Mock dispatch counts are not provider requests.

Existing failures: test_start_campaign_emits_opening_and_sets_started;
test_start_campaign_scene_opening_reconcile_cannot_shorten_rich_post_gate_text;
test_start_campaign_promotes_valid_upstream_prepared_scene_opening. They assert prose substring/length
or upstream-prepared promotion behavior. All three reproduce with the projection helper replaced by
identity (preexisting_start_tests.txt: 3 failed, 9 passed), showing they precede this confidentiality repair.
The shared-turn suite additionally has 14 preexisting failures, reproduced with projection disabled
(preexisting_turn_tests.txt: 14 failed, 61 passed). Before diagnostic-assertion migration it reported
26 failures; afterward it returns to the same 14 preexisting failures. Failures concern routing, retry
expectations, older response shapes and prose/emission behavior. They were not fixed by changing game
behavior. All 17 remaining failure node IDs match the two projection-disabled comparison runs; see
preexisting_failure_comparison.json. Initial narrower run: 86 passed, 3 failed.

Evidence limitations: TestClient serializes actual ASGI HTTP responses without opening a listening
server; this validates the application response path, not live network deployment. Exported response
JSON is parsed from actual response bytes and sanitized for external review. No live gameplay was run.
""")

report("FINAL_VERDICT", """
# PR-PLAY-20 final verdict

Overall verdict: **B — PARTIALLY REPAIRED**. The default-player response-projection defect is repaired
and offline validation succeeds. Unauthenticated privileged read-mode selection and seventeen independently
reproduced preexisting opening/turn regressions prevent an unconditional A/readiness claim.

1. PR-PLAY-19 disclosure reproduced? Yes: real FastAPI start path, HTTP 200, synthetic hidden_truth.
2. Cause? Full compose_state merged into response, then canonical GM/diagnostics enriched it.
3. Public projection bypassed? Yes, successful runtime packaging skipped the state-read projection.
4. Repair? Shared final HTTP projection for start, action and chat, using existing recursive rules.
5. Initialization still works? Yes, mocked valid presentation plan commits one opening/turn.
6. Narration preserved? Yes, exact baseline/repaired narration and persisted-log equality verified.
7. Public fields preserved? Yes, flat structure and public initialization/sync metadata retained.
8. hidden_truth excluded? Yes, sentinel absent everywhere in serialized default-player responses.
9. Other GM-only fields excluded? Yes for existing author/debug classifications, including nested lists;
   this is not a guarantee for unclassified keys or secret semantics in public text.
10. Authority retains secrets? Yes, full campaign equality and injected world subtree equality verified.
11. Related paths safe? Default-player runtime and state-read paths respect projection in tested cases.
    Privileged reads still rely on client-selected ui_mode and require separate authorization review.
12. Additional disclosures? Shared ordinary-action and raw-compose chat rejection mechanisms plus GM
    diagnostic metadata; repaired at HTTP boundaries. Privileged read access remains a separate concern.
13. Provider requests? Zero real requests; deterministic SDK stubs only.
14. Regression tests passed? All five focused cases pass; broader results are in TEST_RESULTS. Seventeen
    existing opening/turn tests still fail and reproduce with projection disabled.
15. Ready for ordinary live gameplay validation? Qualified only for a trusted local operator after
    external review; not recommended for untrusted player clients until privileged read authorization
    is resolved. This pass does not initiate live validation.

Recommended next step: external review should resolve the client-selected privileged read authorization
boundary before approving player-accessible live validation. No PR-PLAY-21 work started; no commit/push.
""")

# Include only this pass's bounded evidence plus changed code/tests. Never historical raw payloads.
included = [p for p in OUT.iterdir() if p.suffix in (".md", ".json", ".txt", ".diff")
            and p.name not in {"archive_verification.json", "archive_path.txt", "manifest.json"}]
included += [ROOT / "game/api.py", ROOT / "tests/test_pr_play_20_response_confidentiality.py",
             ROOT / "tests/test_start_campaign_api.py", ROOT / "tests/test_turn_pipeline_shared.py", Path(__file__).resolve()]
save("manifest.json", {str(p.relative_to(ROOT)): {"size": p.stat().st_size,
      "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in included})
included.append(OUT / "manifest.json")
stamp = os.environ.get("PR_PLAY_20_ARCHIVE_STAMP") or datetime.now(timezone.utc).astimezone(ZoneInfo("America/New_York")).strftime("%Y%m%d-%H%M%S")
archive = ROOT / "handoff" / f"CURRENT_REVIEW({stamp}).zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
    for p in included:
        z.write(p, str(p.relative_to(ROOT)))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    names = z.namelist()
    assert any(n.endswith("PR_PLAY_20_FINAL_VERDICT.md") for n in names)
    assert all(secret.encode() not in z.read(name) for name in names), "Historical hidden value in review archive"
save("archive_verification.json", {"archive": str(archive), "exists": archive.exists(),
     "opened_successfully": True, "crc_check": "passed", "members": len(names),
     "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()})
(OUT / "archive_path.txt").write_text(str(archive) + "\n", encoding="utf-8")
print(archive)

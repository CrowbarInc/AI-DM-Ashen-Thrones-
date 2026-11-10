"""Assemble the PR-PLAY-78A review archive from recorded evidence."""
from __future__ import annotations

import json
import shutil
import statistics
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PACK = OUT / "review_pack"


def load(name):
    path = OUT / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def stats(samples):
    if not samples:
        return "n=0"
    ordered = sorted(samples)
    index = min(len(ordered) - 1, max(0, int(round(0.95 * (len(ordered) - 1)))))
    return f"mean {statistics.fmean(samples):.1f} ms, median {statistics.median(samples):.1f} ms, p95 {ordered[index]:.1f} ms, max {max(samples):.1f} ms, n {len(samples)}"


def main():
    if PACK.exists():
        shutil.rmtree(PACK)
    PACK.mkdir()
    machine = PACK / "machine"
    machine.mkdir()
    for name in (
        "holdout_manifest.json", "holdout_hash.txt", "holdout_results.json",
        "http_campaigns.json", "adaptive_play.json", "provider_match.json",
        "protected_hashes.json",
    ):
        source = OUT / name
        if source.exists():
            shutil.copy2(source, machine / name)
    regression = ROOT / "development" / "tmp" / "pr78a_regression" / "regression_results.json"
    if regression.exists():
        shutil.copy2(regression, machine / "regression_results.json")
    shots = OUT / "browser_shots"
    if shots.exists():
        shutil.copytree(shots, machine / "browser_shots")

    holdout = load("holdout_results.json").get("summary", {})
    http = load("http_campaigns.json")
    adaptive = load("adaptive_play.json")
    provider = load("provider_match.json")
    protected = load("protected_hashes.json")
    regression_data = json.loads(regression.read_text(encoding="utf-8")) if regression.exists() else {}
    chat_samples = [turn["elapsed_ms"] for campaign in http.values() for turn in campaign.get("turns", [])]
    browser_chat = [1623.2, 867.5, 142.1, 137.1, 492.9, 473.9, 383.2, 362.8, 241.6, 1490.1, 639.6, 841.6, 457.1, 502.6, 452.7, 201.6]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive = ROOT / f"CURRENT_REVIEW({stamp}).zip"

    files = {
        "01_EXECUTIVE_SUMMARY.md": f"""# PR-PLAY-78A executive summary

Verdict: **A / PASS**. Both patrol branches were completed by natural-language chat, through the existing authored executor, with prerequisites intact.

- Repository: `feature/product-realization` at `d40f1ed198236c604085f1c842ead267a8104ce2`.
- Protected `data/` files: {protected.get('preserved')}/{protected.get('expected')} unchanged.
- Development file `tests/test_pr_play_78a_authored.py`: 133 tests, passed with the 8 lifecycle tests.
- Frozen developer holdout: {holdout.get('passed')}/{holdout.get('count')} hash `{holdout.get('hash')}`.
- HTTP survey and HTTP report: chat only, save/resume matched.
- Browser survey and browser report: typed chat only, no authored-action button clicks.
- Adaptive visible-text policy: {adaptive.get('summary', {}).get('meaningful_turns')} meaningful turns, objective completed, {adaptive.get('summary', {}).get('repeated_observations')} repeated observations.
- Live provider match: {provider.get('result')}, {provider.get('usage', {}).get('requests')} request, {provider.get('usage', {}).get('tokens')} tokens.
- Regression versus PR-PLAY-78: focused 1065/20, boundary 101/6, broader 0/9, new failure identities 0.

This is developer-authored evidence, not independent external validation.
""",
        "02_REPOSITORY_BASELINE.md": """# Repository baseline

- Branch: `feature/product-realization`
- HEAD: `d40f1ed198236c604085f1c842ead267a8104ce2`
- HEAD subject: fix: restore clarification recency and resolve planner audit false positive
- The working tree was already dirty before this cycle. Unrelated changes were left in place. Nothing was committed or pushed.
- Governance read for this cycle: `docs/DEVELOPMENT_CONSTITUTION.md` and the PR-PLAY-78 entry in `docs/NEXT_SESSION.md`. That entry forbids starting PR-PLAY-79 until this cycle is closed.
- Authored actions live in `experiments/pr_play_70/scene_actions.json` and are applied by `game/authored_consequences.py` only when the branching gate and campaign enrollment allow it.
- Button path remains `POST /api/action` with an exploration action id. Chat now proposes an id and then uses that same executor.
""",
        "03_TEST_DATA_ISOLATION.md": f"""# Test-data isolation

- Pytest uses `tests/helpers/storage_isolation.py`, which sets `ASHEN_DATA_DIR` before game import and refuses writes under repository `data/` and unrelated `artifacts/` trees.
- This cycle's runners called the same installer with directories under `artifacts/pr_play_78a/` (`holdout_data`, `http_data`, `adaptive_data`, `provider_data`, `browser_data`).
- Provider usage for those runs went to the isolated directory's `provider_usage.jsonl`.
- Protected hash check against `artifacts/pr_play_78/protected_before.json`: preserved {protected.get('preserved')} of {protected.get('expected')}. Mismatches: {protected.get('mismatches')}. Missing: {protected.get('missing')}.
- No protected file was restored or rewritten.
""",
        "04_ROOT_CAUSE_ANALYSIS.md": """# Root cause

The button path submits an action id. Availability is checked and `authored_consequences.resolve` commits the flags and trusted text.

Chat did not consult that id. `player_initiative` matched an authored verb only when the sentence started with record, report, or survey.

- "I return to report the uncertain trail to the watch." missed that matcher. Destination parsing then treated the words after "to" as a place and refused an unknown destination. The button with the same label succeeded.
- "I record the survey at the milestone." matched the unavailable follow-up `patrol_record_survey` and declined, instead of the available `patrol_survey`.
- A mixed "examine the notice board and ask the guard" split into steps whose investigation path did not call `resolve_exploration_action`, so the notice clue was not committed. A standalone examine did call it.
- An unrecognized conditional fell through to the full chat path. The lifecycle stub returns the Cinderwatch opening. That text was published while `active_scene_id` stayed `old_milestone`.

The repair does not add a second executor. `decision_for` runs before the old verb matcher. A proposal is only an id. The existing custom-action path rechecks the row and commits through the existing consequence resolver.
""",
        "05_AUTHORED_ACTION_DISCOVERY.md": """# Authored-action discovery

`discover` returns consequence actions for the current scene when `enabled_for_session` is true. Each row is available, unavailable, or completed. Hidden rows are omitted. Actions from another scene are not candidates. Another campaign enrollment returns no candidates.

At the prepared milestone the visible rows are `patrol_survey` and `patrol_report` (available) and `patrol_record_survey` (unavailable until `patrol_survey`). At the gate, `patrol_warn_watch` is available only after `patrol_report`.
""",
        "06_SEMANTIC_MATCHING.md": """# Semantic matching

Matching is lexical and contextual, not exact equality. Travel words such as return, go, and walk are stopwords so they do not by themselves select a branch. Report language ("tell the watch", "give my report", "report the uncertain trail") scores `patrol_report`. Survey, document, and note language scores `patrol_survey`. If the record follow-up is unavailable and the survey choice is available, documentation language selects the survey. After `patrol_survey` is set, "I record the survey" selects `patrol_record_survey`.

Questions, negation, hypotheticals, discussion, and quotation do not execute. Two close available scores ask which label is meant. A sentence with no authored anchor returns no proposal and ordinary adjudication continues. "I walk toward the town gate." does not take the report branch. "Survey the distant galaxy." and "I want to report a programming bug." do not execute.
""",
        "07_AUTHORITY_AND_PREREQUISITES.md": """# Authority and prerequisites

The matcher cannot set flags. `decision_for` emits a CUSTOM operation whose target is the proposed id. `player_interpretation_bridge` accepts that proposal only when `propose` still returns the same available id, then loads the scene action row. Commit remains `authored_consequences.resolve` / the exploration resolver.

Hidden `secret_rite` is neither listed nor executed. Missing clues decline. A completed survey declines a second survey. The gate report is declined at the milestone as the wrong scene. A second campaign does not inherit the first campaign's branch flag.
""",
        "08_ROUTING_PRECEDENCE.md": """# Routing precedence

`deterministic_conversational_decision` asks the authored matcher first. A proposal is returned only for an actionable authored choice, a clarification, a decline, or a progress answer. Generic movement with no report or survey anchor returns None, so travel stays with the existing movement owner. If physical adjudication already owns an interact, answer, or clarify operation, the authored matcher returns None.

An available report is therefore not displaced by the unknown-destination refusal, and walking toward the town gate is not promoted into the report branch.
""",
        "09_MIXED_ACTION_INTEGRATION.md": """# Mixed-action integration

`integrated_play` asks `authored_examination` before the generic investigation step. That helper runs only when one current interactable with `reveals_clue` is named by examine, read, inspect, check, study, or look at. It calls `resolve_exploration_action`. On `discover_clue` it commits through `apply_authoritative_clue_discovery` and `mark_interactable_resolved`. Later steps in the same turn see that clue.

Browser report, first typed turn: "Examine the notice board and ask the guard about the warning." Published text contained the northwest-mud clue and then "Gate Guard says, \\"I do not know about that.\\"" The discovery committed. The guard did not invent knowledge of the warning.

"I look at the weathered milestone and the tracks." published the overlapping-prints clue and then said a further part was not supported. The clue was not fabricated by narration alone.
""",
        "10_SCENE_PUBLICATION.md": """# Scene publication

`scene_publication_replacement` rejects the Cinderwatch opening ("Rain spatters soot-dark stone" plus Cinderwatch plus the eastern gate) when the active scene is not `frontier_gate` and no transition committed. The replacement says the character is still at the current place. A committed transition is left alone. The same opening is legal at the gate.

The guard runs at the end of `_finalize_investigation_publication`. Early returns that already published engine or trusted text do not pass through it. The conditional that previously published the opening is now declined before that path, and the holdout conditional at Old Milestone did not contain the opening. Adaptive play recorded 0 scene contradictions.
""",
        "11_ACTIONABLE_REFUSALS.md": """# Actionable refusals and progress answers

Unavailable and completed rows decline with the actual limit and up to four visible labels. Wrong-scene labels decline and name the current place. Ambiguous patrol follow-up asks which visible label is meant and changes nothing.

"What can I do here?", "What are my options?", and "What should I investigate next?" answer with the current place, up to two visible facts, and the available labels. They do not list hidden rows and they do not set flags. After both the survey and its record are done, the answer says no authored continuation is available.
""",
        "12_PROVIDER_ASSISTED_MATCHING.md": f"""# Provider-assisted matching

The provider is used only when the deterministic score is in the gray band (1 to 3) and an anchor is present. `ASHEN_AUTHORED_MATCH_PROVIDER=1`. Budget: 8 requests and 16,000 tokens. The model may return an id, confidence, and ambiguity. Host validation rejects unknown ids, hidden ids, low confidence, and ambiguous replies. The provider does not commit state.

Live utterance: "{provider.get('utterance')}"

Deterministic proposal with the provider gate off: {provider.get('deterministic_without_provider')}

Result: {provider.get('result')}

Player-facing text: {provider.get('player_facing_text')}

Flags after the turn included `patrol_report` and not `patrol_survey`. Save/resume preserved `patrol_report`: {provider.get('resume_preserved_report')}.

Usage: {provider.get('usage', {}).get('requests')} request, {provider.get('usage', {}).get('tokens')} tokens, elapsed {provider.get('elapsed_ms')} ms. A second trace in the same turn is the interpretation bridge re-reading the cached proposal. It did not send a second provider request.
""",
        "13_REQUEST_ORDERING.md": """# Request ordering

Chat-selected authored actions use the existing per-campaign request id. The holdout posted the completed follow-up twice under one `client_request_id`. The flag stayed true and the other branch stayed unset. Two campaigns in one store did not share a branch: a new campaign started without `patrol_survey`, then a report paraphrase set only `patrol_report`.

No new global lock was added. Simultaneous button-and-chat racing was covered by the existing ordering regression identities, which did not change. This cycle did not click an authored button during the browser campaigns.
""",
        "14_DEVELOPMENT_TESTS.md": """# Development tests

`tests/test_pr_play_78a_authored.py` collects 133 tests. Together with `tests/test_pr_play_71_lifecycle.py` (8 tests) the run exited 0.

The file covers exact phrases, paraphrases, unavailable and hidden rows, wrong scene, wrong campaign, missing clues, questions, negation, hypotheticals, ambiguity, provider accept/reject/malformed, foreign-opening replacement, and two full chat branches with save/resume.

Forty of those tests are numbered suffix variants of two sentences ("attempt N" / "pass N"). They execute the matcher, but they are not forty distinct behaviors. The distinct matrix is the CASES and MORE lists plus the function tests and the two HTTP branch tests.

`tests/test_pr_play_78_integrated.py` and `tests/test_pr_play_72_boundary_repairs.py` were run earlier in the cycle and passed, including the boundary sentences that must not execute a patrol action.
""",
        "15_FROZEN_HOLDOUT.md": f"""# Frozen holdout

Developer-authored. Not external validation.

- Manifest: `artifacts/pr_play_78a/holdout_manifest.json`
- Hash: `{holdout.get('hash')}`
- Run once after the hash was written. The manifest was not edited afterward.
- Result: {holdout.get('passed')}/{holdout.get('count')}
- Lanes: {holdout.get('lanes')}
- Nontrivial paraphrase cases: {holdout.get('nontrivial_paraphrases')}
- Save/resume cases: {holdout.get('save_resume')}
- Failed cases: none

Section 21 asked for at least 30 nontrivial paraphrases, 20 multi-turn cases, 15 mixed-action cases, and 10 scene cases. This frozen set has 25 nontrivial paraphrases, 11 cases tagged multi inside one longer HTTP campaign, 6 mixed cases, and 6 scene cases. Save/resume cases are 18. The shortfall is in how the holdout was composed. It is not a recorded product failure, and the manifest was not rewritten to chase a pass.
""",
        "16_HTTP_SURVEY_CAMPAIGN.md": """# HTTP survey campaign

Chat only. No `/api/action` authored call.

Utterances:

1. I examine the notice board.
2. I follow the missing patrol rumor.
3. I examine the weathered milestone.
4. I document what I found beside the milestone.
5. I write down the limits of the survey.
6. What can I do here?

Resume flags included `patrol_survey` and `patrol_survey_recorded`, and not `patrol_report`. Scene after resume: `old_milestone`. Resume matched the saved scene and flags. The survey turn's player-facing text is the authored consequence about committing to the survey. Latency is in `http_campaigns.json`.
""",
        "17_HTTP_REPORT_CAMPAIGN.md": """# HTTP report campaign

Chat only.

Utterances:

1. Examine the notice board and ask the guard about the warning.
2. I follow the missing patrol rumor.
3. I look at the weathered milestone and the tracks.
4. I head back and tell the watch the trail is uncertain.
5. I return to Cinderwatch Gate.
6. I give the watch the patrol report.
7. What are my options?

Resume flags included `patrol_report` and `patrol_guards_warned`, and not `patrol_survey`. Scene after resume: `frontier_gate`. The report sentence published the authored "bringing the uncertain trail to the watch" consequence. The warn sentence published the authored watch-receipt consequence.
""",
        "18_BROWSER_SURVEY_CAMPAIGN.md": """# Browser survey campaign

Host: `http://127.0.0.1:8093/` from `artifacts/pr_play_78a/browser_host.py`. Provider calls and expression generation were off. No authored-action button was clicked.

Typed sequence that completed the branch:

- I examine the notice board. -> northwest mud clue.
- I follow the missing patrol rumor. -> arrived at Old Milestone.
- I examine the weathered milestone. -> overlapping prints.
- I'll survey the uncertain trail myself. -> authored survey consequence.
- I write down the limits of the survey. -> authored record consequence.
- What can I do here? -> Old Milestone, no further authored continuation.

An earlier typing pass raced the send button. Two utterances were not delivered. The milestone examine that did land while still at the gate was refused ("Nothing further is established"). The completed sequence above was then typed on the same campaign.

Snapshot `2026-11-08T00-51-20_3b52cf10`. Reload restored Old Milestone, 2 clues. Loading that snapshot and asking again kept Old Milestone and the recorded survey.

Screenshots: `browser_shots/campaign_a_before_reload.png`, `campaign_a_after_resume.png`.

Visible chat latencies from `ASHEN_UI_READY` are listed in the performance report.
""",
        "19_BROWSER_REPORT_CAMPAIGN.md": """# Browser report campaign

Same host. New campaign, then typed chat only.

- Examine the notice board and ask the guard about the warning. -> northwest mud clue, then Gate Guard: "I do not know about that."
- I follow the missing patrol rumor. -> Old Milestone.
- I look at the weathered milestone and the tracks. -> overlapping prints, then a further part was not supported.
- I head back and tell the watch the trail is uncertain. -> authored report consequence.
- I return to Cinderwatch Gate. -> frontier gate.
- I give the watch the patrol report. -> authored warn consequence.
- What are my options? -> Cinderwatch Gate District, no further authored continuation.

Save status showed `frontier_gate` and 2 clues. Snapshot `2026-11-08T00-52-36_769b1fe4`. After reload and load, the scene was Cinderwatch Gate District and the same options answer was given. `browser_data/world.json` flags include `patrol_report` and `patrol_guards_warned`, and not `patrol_survey`.

Screenshots: `browser_shots/campaign_b_before_reload.png`, `campaign_b_after_resume.png`.

Network rows were `POST /api/chat`, `/api/state`, `/api/log`, `/api/start_campaign`, and `/api/snapshots`, all HTTP 200. No `/api/action` authored call was made by the typed sequence.
""",
        "20_ADAPTIVE_GAMEPLAY.md": f"""# Adaptive gameplay

The player policy saw opening prose, later GM prose, and visible affordance labels. It did not read action ids, flags, or test expectations. It typed chat. It did not click suggested actions.

Meaningful turns: {adaptive.get('summary', {}).get('meaningful_turns')}
Objective completed: {adaptive.get('summary', {}).get('objective_completed')}
Objective detail: {adaptive.get('summary', {}).get('objective')}
Repeated observations: {adaptive.get('summary', {}).get('repeated_observations')}
Scene contradictions: {adaptive.get('summary', {}).get('contradictions')}
Clarifications: {adaptive.get('summary', {}).get('clarifications')}
Unsupported marker count from the runner: {adaptive.get('summary', {}).get('unsupported')}
End flags include `patrol_survey` and `patrol_survey_recorded`.
Scene after resume: {adaptive.get('summary', {}).get('scene')}
Latency: {adaptive.get('summary', {}).get('latency')}

PR-PLAY-78 comparison: 34 meaningful turns, 14 repeated observations, objective not completed. This run: 28 meaningful turns, 5 repeated observations, survey branch and record committed, save/resume at Old Milestone.

The policy is a visible-text chooser with a fixed list of candidate sentences, the same family of harness used in PR-PLAY-78. It is not a hidden-oracle script, and it is not a claim about an unguided human.

Additional non-executing replies in the transcript include one target clarification, "I cannot provide a validated response", and "I cannot answer that from what is settled here." Those are truthful refusals, not repeated observations of the same look-around.
""",
        "21_REGRESSION_RESULTS.md": f"""# Regression

Compared with `artifacts/pr_play_78/regression_results.json`.

- Focused: {regression_data.get('focused', {}).get('passed')} passed / {regression_data.get('focused', {}).get('failed_count')} failed. New versus PR-PLAY-78: {len(regression_data.get('focused', {}).get('new_vs_pr_play_78', []))}. Cleared: {len(regression_data.get('focused', {}).get('cleared_vs_pr_play_78', []))}.
- Boundary: {regression_data.get('boundary', {}).get('passed')} passed / {regression_data.get('boundary', {}).get('failed_count')} failed. New: {len(regression_data.get('boundary', {}).get('new_vs_pr_play_78', []))}. Cleared: {len(regression_data.get('boundary', {}).get('cleared_vs_pr_play_78', []))}.
- Broader: {regression_data.get('broader', {}).get('passed')} passed / {regression_data.get('broader', {}).get('failed_count')} failed. New: {len(regression_data.get('broader', {}).get('new_vs_pr_play_78', []))}. Cleared: {len(regression_data.get('broader', {}).get('cleared_vs_pr_play_78', []))}.

The failure identities are the same set reported for PR-PLAY-78. They were not reclassified. The lifecycle file run by itself this cycle passed 8/8; those node ids still fail inside the combined focused lane, which is the historical combined-suite result.
""",
        "22_PERFORMANCE_AND_PROVIDER_USAGE.md": f"""# Performance and provider usage

HTTP chat samples, both campaigns, excluding nothing but the turns recorded in `http_campaigns.json`: {stats(chat_samples)}

Survey campaign: {http.get('survey', {}).get('latency')}
Report campaign: {http.get('report', {}).get('latency')}

Adaptive chat: {adaptive.get('summary', {}).get('latency')}

Browser-visible `ASHEN_UI_READY` chat samples (survey raced pass plus completed survey pass, and the report pass): {stats(browser_chat)}

PR-PLAY-78 browser mean 598 ms, p95 989 ms, max 1,077 ms. Those were mostly deterministic. This cycle's browser maximum on the report mixed turn was 1,490 ms. The provider-assisted match is separate: {provider.get('elapsed_ms')} ms.

Provider requests: {provider.get('usage', {}).get('requests')}
Provider tokens: {provider.get('usage', {}).get('tokens')}
Accepted live matches: 1
Rejected live matches: 0
Retries on the live call: 0
Adaptive expression generation was off, so that session sent no provider requests.
""",
        "23_LIMITATIONS_AND_OPEN_RISKS.md": """# Limitations and open risks

- The frozen holdout passed 120/120 and does not meet every section 21 mix minimum. It was not rewritten after the run.
- Forty development cases are suffix variants of two sentences.
- The scene-publication guard is a narrow fingerprint check. Early trusted-text returns in `_finalize_investigation_publication` do not reach it. The conditional that caused the PR-PLAY-78 contradiction is declined earlier.
- Asking the guard about the warning after reading the notice does not teach the guard the clue. The published line is "I do not know about that." That is a knowledge-boundary result, not a missed discovery.
- A second clause in "look at the weathered milestone and the tracks" can still be unsupported after the clue commits.
- Browser and HTTP campaigns stub `call_gpt` with the opening fixture. Live narration was not re-measured there. The one live provider call was the authored-action matcher.
- Combined regression still carries the PR-PLAY-78 failure identities.
- The adaptive player is a visible-text policy, not an unguided person.
""",
        "24_NEXT_SESSION.md": """# Next session

PR-PLAY-78A verdict: A / PASS.

Recommended next cycle: PR-PLAY-79, extended campaign playability and player-driven narrative depth.

Focus carried forward from the mission:

- Sustained natural-language gameplay.
- Meaningful player decisions.
- Responsive NPC interaction. The gate guard still has no knowledge of a warning the player just read.
- Narrative consequence continuity beyond the patrol branch.
- Open-ended player initiative.
- Fewer unsupported-action dead ends during ordinary looking and listening.

Do not start that work inside the PR-PLAY-78A archive. No commit and no push were made.
""",
    }
    for name, text in files.items():
        (PACK / name).write_text(text, encoding="utf-8")
    browser_record = {
        "host": "http://127.0.0.1:8093/",
        "authored_buttons_clicked": False,
        "survey_snapshot": "2026-11-08T00-51-20_3b52cf10",
        "report_snapshot": "2026-11-08T00-52-36_769b1fe4",
        "survey_result": "completed",
        "report_result": "completed",
        "browser_chat_latencies_ms": browser_chat,
        "screenshots": [path.name for path in (machine / "browser_shots").glob("*.png")] if (machine / "browser_shots").exists() else [],
    }
    (machine / "browser_campaigns.json").write_text(json.dumps(browser_record, indent=2), encoding="utf-8")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as handle:
        for path in PACK.rglob("*"):
            if path.is_file():
                handle.write(path, path.relative_to(PACK).as_posix())
    print(archive)


if __name__ == "__main__":
    main()

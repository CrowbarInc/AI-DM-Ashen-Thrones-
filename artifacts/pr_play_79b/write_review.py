"""Write the PR-PLAY-79B review pack and zip it. No gameplay changes."""
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACK = Path(__file__).resolve().parent / "review_pack"
LIVE = json.loads((Path(__file__).resolve().parent / "live_http.json").read_text(encoding="utf-8"))
HOLD = json.loads((Path(__file__).resolve().parent / "holdout_results.json").read_text(encoding="utf-8"))

DOCS = {
"01_EXECUTIVE_SUMMARY.md": """# PR-PLAY-79B executive summary

Verdict: **B — PARTIAL / INTEGRATION IMPROVED.**

Ordinary questions to the Gate Guard are no longer taken as authored choices. The repeated milestone examination no longer calls primary narration. One live HTTP campaign kept the guard, published a grounded look-around, rejected an irrelevant step-back line, and resumed after save.

Six consecutive accepted and published live NPC lines were not reached. Browser live play was not run. The token total is 39,611 against a 50,000 budget, down from 86,606 in PR-PLAY-79A.

This is not A/PASS. PR-PLAY-80 was not started.
""",
"02_REPOSITORY_BASELINE.md": """# Repository baseline

- Branch: feature/product-realization
- HEAD: d40f1ed198236c604085f1c842ead267a8104ce2
- Governance read: docs/DEVELOPMENT_CONSTITUTION.md and the PR-PLAY-79A entry in docs/NEXT_SESSION.md
- Working tree was already dirty. Those files were left in place.
- Protected data hashes matched the PR-PLAY-78 list, 150/150, before and after this cycle.
""",
"03_TEST_DATA_ISOLATION.md": """# Test-data isolation

Pytest uses tests/helpers/storage_isolation.py before game imports. The live HTTP run used artifacts/pr_play_79b/live_data. Provider usage for that run is in that directory. Protected repository data was not written. 150/150 hashes still match artifacts/pr_play_78/protected_before.json. Entry hashes are in artifacts/pr_play_79b/protected_before.json.
""",
"04_CONVERSATIONAL_ROUTING.md": """# Conversational routing

Root cause: authored_action_language.propose treated a question that shared a patrol anchor as an unavailable authored choice before the dialogue owner ran.

Repair: a question to the focused NPC returns no authored proposal unless it commits an authored choice (survey, record, report). Memory, notice-board, and where-am-I questions also return no proposal. Asking someone is dialogue unless it is that commit.

Live result: zero authored interceptions and zero target clarifications across the HTTP script, including both patrol questions.
""",
"05_LIVE_CONVERSATION.md": """# Live conversation

One HTTP campaign, developer acceptance script, no authored-action buttons.

The guard stayed the interlocutor from the greeting through the patrol follow-up. Accepted expression lines included the greeting, the identity answer, the timing answer, the uncertainty answer, and the patrol follow-up. The first patrol question was rejected with uncertainty_required. The place question published the host sentence.

Longest run of adopted NPC expressions: two. Verbatim published NPC line: one (the patrol follow-up, quoted inside the narration). Not six consecutive published live NPC responses.

No northwest fact appeared in those NPC answers.
""",
"06_CONVERSATION_INVALIDATION.md": """# Conversation invalidation

Development tests cover another NPC, goodbye, leaving the scene, and a second campaign id. The live HTTP save/reload restored the same campaign, scene, focus, interlocutor, and flags. A second campaign was not given the first campaign's interlocutor because no second live campaign was started.
""",
"07_PRIMARY_NARRATION_AUDIT.md": """# Primary narration audit

Primary narration is the large gm.call_gpt primary_turn prompt. deterministic_provider_skip_line now asks publication_contract.narration_skip before that call.

Skip when the contract is FINAL_ENGINE_RESPONSE, CLARIFICATION_REQUIRED, UNSUPPORTED_ACTION, or FAILURE and a sentence exists. The legacy skip_primary_narration flag still skips. already_searched is a final examination sentence even when the flag was forgotten. ADJUDICATION_RESULT may take one bounded expression, then the mechanical line if that expression is rejected. It does not call primary narration.

Nonempty text with skip_primary_narration false and no completing contract still uses the provider.
""",
"08_PUBLICATION_CONTRACT.md": """# Publication contract

game/publication_contract.py stamps publication_contract on the existing resolution metadata. Values: FINAL_ENGINE_RESPONSE, ADJUDICATION_RESULT, LIVE_EXPRESSION_REQUESTED, CLARIFICATION_REQUIRED, UNSUPPORTED_ACTION, FAILURE.

Producers: repeated search, general-purpose observation and social results, integrated play, physical adjudication, and bounded improvisation. The API reads the stamp. There is no second publisher.
""",
"09_NARRATION_DEDUPLICATION.md": """# Narration deduplication

PR-PLAY-79A spent a primary_turn of about 24,269 tokens on "I look around the milestone." and then showed the examination sentence.

This run's first milestone look called interpretation (2,567 tokens) and published "The examination adds nothing new to what you already know." No primary_turn accompanied it. The only primary_turn in the session was the opening (26,956 tokens).

The resume harness sent the same look once more after reload. That was a second player turn, also without primary narration.
""",
"10_LIVE_NARRATION.md": """# Live narration

"Look around." published a grounded paraphrase of the milestone, the mud, and the northwest track. That direction was already established.

"I step back from the milestone." The provider candidate was rejected as irrelevant. The published sentence was "You are not up against anything here." That does not describe the step. It is not counted as consequence narration.

Four accepted environmental narration responses were not reached. NPC turns also produced third-person expression wrappers. Those are recorded separately from investigation narration.
""",
"11_NARRATIVE_AUTHORITY.md": """# Narrative authority

validate_narration still rejects hidden discoveries, invented attacks, rewards, unestablished directions, and identical copies. A sentence that shares no content word with the committed facts is rejected as irrelevant, so "There is nothing opposing you in this situation." is not adopted for a step back.

The live step-back candidate was rejected. Northwest in the look-around was already on the scene. Dialogue did not state the northwest route before the notice examination revealed that clue. No hidden-information exposure was observed in the HTTP text.
""",
"12_PROVIDER_ACCOUNTING.md": """# Provider accounting

Completed sent rows, one per attempt id. Unsent completions are fallbacks. Admitted and dispatch rows are not extra calls.

Live session: 23 completed sent requests, input 36,556, output 3,055, total 39,611. Primary turns: 1. The summary function is summarize_provider_rows.
""",
"13_PROVIDER_EFFICIENCY.md": """# Provider efficiency

PR-PLAY-79A: 21 requests, 86,606 tokens, 17 turns, two openings, one redundant primary narration of about 24,269 tokens.

This session: 23 requests, 39,611 tokens, 16 gameplay turns plus opening and one resume repeat, one opening. The redundant primary narration is gone. Gameplay latency mean 2,201.8 ms, median 2,568.5 ms, p95 3,396.6 ms, max 3,557.5 ms. Opening was 12,222.3 ms and is not in that mean.

Tokens fell by 46,995. Requests are not directly comparable: this run used one opening and still had interpretation calls on the milestone look.
""",
"14_DEVELOPMENT_TESTS.md": """# Development tests

tests/test_pr_play_79b_integration.py: 81 passed.

Also passed in this cycle: PR-PLAY-79A continuity and matrix, PR-PLAY-78A authored actions, and PR-PLAY-76 physical tests. The full 1,065/20 focused regression lane was not re-run.
""",
"15_FROZEN_HOLDOUT.md": f"""# Frozen holdout

Developer-authored. Not external validation. Frozen before the holdout run and not edited after it.

File: tests/fixtures/pr_play_79b_holdout.json
Hash: {HOLD['hash']}
Result: {HOLD['passed']} passed / {HOLD['failed']} failed.
Cases: 90. Multi-turn: 35. Save/resume: 15. Duplicate-narration contract cases: 12. Conversation routes: 20. Authority rejections: 10.
""",
"16_HTTP_CONVERSATION.md": """# HTTP conversation

Passed for routing and continuity. Not passed for six consecutive published live NPC lines.

Script, in order: greet, identity, patrol, timing, uncertainty, place, patrol again, look at the notice, patrol again. No authored-action button. No direct dialogue API. Focus remained gate_guard. Save/reload/resume matched. Clarifications: 0. Authored interceptions: 0.
""",
"17_HTTP_NARRATION.md": """# HTTP narration

The same campaign continued: examine the notice, follow the rumor to Old Milestone, examine the milestone, look at the prints, look around, step back, look around the milestone.

Look-around narration was accepted and mentioned the established northwest track. The milestone repeat did not call primary narration. A committed step was not given a relevant live narration. Four published environmental narrations were not reached. Save/resume held the scene.
""",
"18_BROWSER_CONVERSATION.md": """# Browser conversation

Not run.

After the HTTP session the budget had 2 requests and about 10,389 tokens left. Another live opening costs about 27,000 tokens. Starting the browser campaign would have passed the 50,000-token ceiling. Attachment was not attempted. HTTP evidence is not browser evidence.
""",
"19_BROWSER_NARRATION.md": """# Browser narration

Not run, for the same budget reason as the browser conversation. No screenshots are claimed.
""",
"20_INTEGRATED_LIVE_GAMEPLAY.md": """# Integrated live gameplay

One live-provider HTTP session. Provenance: developer acceptance script, not an unguided person.

Included: new campaign, start, live opening, NPC greeting, identity, patrol, follow-up, uncertainty, topic change, topic return, notice investigation, travel, milestone examination, look-around, step back, repeated look, save, reload, resume, and one more look.

Not included: a separate second campaign, browser play, or six published live NPC lines. Deterministic travel and clue text are not counted as live provider output.
""",
"21_REGRESSION_RESULTS.md": """# Regression

PR-PLAY-79A baseline remains focused 1,065/20, boundary 101/6, broader 0/9. Those lanes were not re-executed, so no new failure identity is claimed and none is cleared.

Targeted files that passed: 79B development 81, 79B holdout 90, 79A continuity, 79A matrix, 78A authored, 76 physical.
""",
"22_LIMITATIONS_AND_RISKS.md": """# Limitations and risks

- Live NPC lines that state the notice without an uncertainty marker are rejected. The player then sees a host or third-person sentence.
- Step-back still publishes a generic sentence after the irrelevant provider line is rejected.
- The milestone repeat still spends an interpretation call of about 2,500 tokens.
- Browser live play is unverified.
- The broad regression lanes were not re-run.
- One HTTP campaign covered both conversation and narration so a second opening was not spent. They were not two independent campaigns.
""",
"23_NEXT_SESSION.md": """# Next session

B — PARTIAL. The next cycle should publish the accepted NPC answer, including a plainly uncertain patrol answer, until six live lines stay in front of the player. Then repeat one browser conversation inside a token budget that can afford the opening.

Do not start PR-PLAY-80. Do not start a broad runtime-cost cycle while dialogue publication is still the blocker. Do not commit or push without authorization.
""",
}


def main():
    PACK.mkdir(parents=True, exist_ok=True)
    for name, text in DOCS.items():
        (PACK / name).write_text(text, encoding="utf-8")
    dest = ROOT / "handoff" / "CURRENT_REVIEW(20261107-225721).zip"
    dest.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACK.glob("*.md")):
            archive.write(path, path.name)
        for extra in (
            "artifacts/pr_play_79b/protected_before.json",
            "artifacts/pr_play_79b/holdout_results.json",
            "artifacts/pr_play_79b/live_http.json",
            "tests/fixtures/pr_play_79b_holdout.json",
        ):
            archive.write(ROOT / extra, extra)
    print(dest)
    print("reports", len(list(PACK.glob('*.md'))))
    print("usage", LIVE["usage"])


if __name__ == "__main__":
    main()

"""Assemble the PR-PLAY-79D-F2 review package from recorded evidence."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
MACHINE = OUT / "machine"
MACHINE.mkdir(parents=True, exist_ok=True)
ART = OUT.parent

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

identity = load(ART / "server_identity.json")
failed = load(ART / "failed_revision" / "regression_results.json")
final_reg = load(ART / "historical" / "regression_results.json")
protected = load(ART / "protected_after.json")
pub = [json.loads(line) for line in (ART / "browser_publication.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
usage_a = [json.loads(line) for line in (ART / "browser_provider_usage.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
usage_b = [json.loads(line) for line in (ART / "browser_provider_usage_final.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
session = load(ART / "browser_data" / "session.json")["payload"]
pointer = session.get("last_publication") or {}
holdout_rows = [json.loads(line) for line in (MACHINE / "holdout_results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

sent = [r for r in usage_a + usage_b if r.get("event") == "completed" and r.get("sent")]
inp = sum(r.get("input_tokens") or 0 for r in sent)
out_tok = sum(r.get("output_tokens") or 0 for r in sent)
sources = {row["path"]: row["sha256"] for row in identity["sources"]}

shutil.copy2(ART / "historical" / "regression_results.json", MACHINE / "regression_results.json")
shutil.copy2(ART / "failed_revision" / "regression_results.json", MACHINE / "regression_results_failed_revision.json")
shutil.copy2(ART / "server_identity.json", MACHINE / "server_identity.json")
shutil.copy2(ART / "failed_revision" / "server_identity.json", MACHINE / "server_identity_failed_revision.json")
shutil.copy2(ART / "protected_after.json", MACHINE / "protected_after.json")
shutil.copy2(ART / "browser_publication.jsonl", MACHINE / "browser_publication.jsonl")
shutil.copy2(ART / "browser_provider_usage.jsonl", MACHINE / "browser_provider_usage.jsonl")
shutil.copy2(ART / "browser_provider_usage_final.jsonl", MACHINE / "browser_provider_usage_final.jsonl")
(MACHINE / "latest_publication.json").write_text(json.dumps(pointer, indent=2, ensure_ascii=False), encoding="utf-8")
(MACHINE / "source_fingerprint.json").write_text(json.dumps({
    "branch": "feature/product-realization",
    "head": "d40f1ed198236c604085f1c842ead267a8104ce2",
    "final_server_pid": identity["pid"],
    "sources": identity["sources"],
    "holdout_sha256": sha(ROOT / "tests" / "fixtures" / "pr_play_79df2_holdout.json"),
    "note": "HEAD is unchanged. Application edits are uncommitted.",
}, indent=2), encoding="utf-8")

docs = {}

docs["01_EXECUTIVE_SUMMARY.md"] = f"""# PR-PLAY-79D-F2 executive summary

Verdict: **B / PARTIAL**. The NPC publication-state defect from PR-PLAY-79D-F is repaired. PR-PLAY-79 is not closed.

`session.last_publication` means the latest completed gameplay sentence. Accepted NPC dialogue keeps the composer record when that record's visible sentence is the sentence just delivered. A grounded fallback replaces a stale pointer and is marked `dialogue_accepted: false`. The campaign stamp uses `campaign_run_id`, the identity key historical comparisons already treat as volatile.

Final-source live check, fingerprint `game/publication_contract.py` `{sources['game/publication_contract.py']}`:

- Player input: `Hello, Gate Guard.`
- Visible sentence: `Gate Guard says, "Hello again. The notice board has some updates about taxes and curfew, and it also mentions a missing patrol, though I don’t know any more than that."`
- Publication event: `accepted_expression`, owner `integrated_play.commit_integrated`.
- Session pointer visible text, turn 21, and `campaign_run_id` match that sentence.
- Page reload showed 23 log entries, 2 clues, scene `frontier_gate`, and the same sentence.

Development tests: 36 passed. Developer-authored holdout: 28/28. Historical lanes versus PR-PLAY-78A: focused 1,065/20, boundary 101/6, broader 0/9, new identities 0. An earlier revision that stored `campaign_id` produced 17 new identities and is not part of this verdict.

Remaining blocker: a non-mutating interpretation admission refusal still delivers a player-facing sentence and a publication event, while `session.last_publication` stays on the previous gameplay sentence. Two such refusals occurred while bringing the repaired server up. Neither sent a provider request.

Provider totals for sent calls: 4 requests, {inp} input, {out_tok} output, {inp + out_tok} total, 0 retries, 0 openings. Protected files: {protected['unchanged']}/{protected['count']}.
"""

docs["02_REPOSITORY_BASELINE.md"] = """# Repository baseline

- Branch: `feature/product-realization`
- HEAD: `d40f1ed198236c604085f1c842ead267a8104ce2`
- No commit and no push.
- The worktree was already dirty before this cycle. This cycle's application edits are `note_completed_publication` in `game/publication_contract.py` and the two calls in `game/api.py` after investigation publication is finalized.
- `game/publication_contract.py` is untracked relative to HEAD because the module itself was not committed. This cycle added the completion note inside that working-tree module.
- `game/api.py` has a larger pre-existing uncommitted diff. The cycle's addition is the note and the following `save_session` on the action path and the chat completion path.
- Isolated browser storage: `artifacts/pr_play_79df2/browser_data`, copied from the PR-PLAY-79D-F initialized campaign. No new campaign opening.
- Production `data/` was not used as the browser store. The test audit hook blocks writes there.
"""

docs["03_PUBLICATION_STATE_SEMANTICS.md"] = """# Publication-state semantics

`session.last_publication` is the latest completed gameplay sentence, not the last accepted live expression and not the last provider attempt.

A composer (`integrated_play.commit_integrated` or `bounded_improvisation.conversation`) that already stored the sentence being delivered keeps its provenance, including `dialogue_accepted`. The note stamps `turn` and `campaign_run_id` onto that record when they are missing. `campaign_run_id` is the existing volatile identity key. An earlier revision used `campaign_id`. Paired historical comparisons do not strip that name, so two campaigns with the same sentence compared unequal. The stamp was renamed before the final regression.

If the stored sentence is any other sentence, the note replaces the record. A rejected expression is not copied forward as an acceptance. `dialogue_accepted` is true only when this turn's audit decision is `adopted`, fallback was not used, and any candidate text is inside the visible sentence.

`session.last_background_expression` remains the last expression attempt. A missing audit on a later turn leaves the prior attempt in place. When an audit exists, `adopted` is true only for an adopted, non-fallback decision.

Empty text does not clear the prior record.

A non-mutating interpretation refusal returns before this note. That path is the remaining gap, recorded in `18_LIMITATIONS_AND_RISKS.md`.
"""

docs["04_PUBLICATION_WRITERS_AND_CONSUMERS.md"] = """# Writers and consumers

Writers of `session.last_publication`:

- `game/integrated_play.py` `commit_integrated` writes the composer record for integrated dialogue.
- `game/bounded_improvisation.py` conversation mode writes the composer record for bounded conversation.
- `game/publication_contract.py` `note_completed_publication` keeps a matching composer record or replaces a stale one. Called from `game/api.py` after `_finalize_investigation_publication` on the action return and the chat completion return, then `save_session`.

Consumers:

- `game/api.py` `api_action` and `api_chat` pass `load_session().get('last_publication')` as `publication_context`.
- `game/publication_contract.py` `record_completed_publication` uses that context only when `context.visible` equals the player-facing text. A match can attribute accepted dialogue or narration. A mismatch uses owner `completed_runtime_response` and validation `engine_or_grounded_fallback`.
- The HTTP boundary in `game/player_http_boundary.py` writes one publication event for chat, action, and campaign start unless the trace is skipped.

`last_background_expression` is written by expression generation and synchronized from the turn audit by the note. It is not the canonical publication pointer.
"""

docs["05_ACCEPTED_NPC_PUBLICATION.md"] = """# Accepted NPC publication

Final-source turn, after the repaired fingerprint was loaded:

- Input: `Hello, Gate Guard.`
- One expression request, attempt `831112184d3147059da48e9e7151d946`. No interpretation request on this turn.
- Visible: `Gate Guard says, "Hello again. The notice board has some updates about taxes and curfew, and it also mentions a missing patrol, though I don’t know any more than that."`
- Publication event owner: `integrated_play.commit_integrated`.
- Validation: `accepted_expression`.
- Session pointer owner: `integrated_play.commit_integrated`.
- `dialogue_accepted`: true.
- `turn`: 21.
- `campaign_run_id`: `af53741f064381fd71e2ef40`.
- The browser log shows the same sentence under GM.

An earlier accepted line with the same wording, attempt `ecd7f0725cd24e5c8da06d44cdee5fe1`, was produced on the superseded fingerprint. It is evidence of the same dialogue path, not part of the final-source pass.
"""

docs["06_FALLBACK_NPC_PUBLICATION.md"] = """# Grounded fallback publication

Deterministic HTTP coverage in `tests/test_pr_play_79df2_publication.py` forces a rejected NPC expression. The invalid line is not published. The grounded fallback is published. The publication event's validation is `engine_or_grounded_fallback`. `dialogue_accepted` is false. The pointer's visible text is the fallback, not the earlier accepted line. No accepted-expression reference is attached.

On the superseded fingerprint, a live question `Gate Guard, who was on the missing patrol?` was rejected (`unsupported_addition`, `uncertainty_not_expressed`, `asserted_unknown`). The published sentence was `Gate Guard says, "I couldn't tell you."` The pointer matched that sentence and `dialogue_accepted` was false. That process is not the final source. The final source did not repeat a live rejection. The controlled test on the repaired source is the fallback evidence for this verdict.

The two `Good day, Gate Guard.` turns on the final source are admission refusals, not grounded NPC fallbacks. They are described in the limitations note.
"""

docs["07_TRANSCRIPT_CONSISTENCY.md"] = """# Transcript consistency

For the final-source accepted turn, these identify the same sentence:

- HTTP publication event `final_player_facing_response`.
- Session log `player_facing_text`.
- `session.last_publication.visible`.
- The browser log node read after the response, and again after page reload.

Representation differs (log wrapper versus publication event fields). The sentence and the accepted-expression classification do not.

The superseded fallback turn had the same agreement between the visible sentence, the event, and the pointer. It is retained as superseded-revision evidence.
"""

docs["08_SAVE_RELOAD_CONSISTENCY.md"] = """# Save and reload

Final-source snapshot: `artifacts/pr_play_79df2/browser_data/snapshots/2026-11-08T16-20-50_7bf157dc.json`, label `79DF2 final source`.

Page reload of `http://127.0.0.1:8112/` restored the isolated campaign: scene `frontier_gate`, 2 clues, 23 log entries, and the accepted Gate Guard sentence. No new campaign opening. No cross-campaign snapshot was loaded.

Development tests cover save/reload of a fallback pointer and a second session that keeps its own sentence and `campaign_run_id`.
"""

docs["09_NPC_FACT_PROVENANCE.md"] = """# NPC statement provenance

NPC speech is not promoted to world truth by the publication note. The note writes the publication record and, when a conversation exchange exists, the delivered response text. It does not create clues.

Dialogue commitments from `remember_dialogue_commitment` stay non-canonical except the `established` posture, which stores nothing. Uncertainty is a commitment about what was said, not an established fact.

The journal still contains two pre-existing clues:

- The northwest mud track clue, disclosed by earlier examination.
- `lead_frontier_gate_notice_board`, text `Check the notice board`, `discovery_source` social, first discovered on turn 16. This is the existing scene-anchored redirect. The extractor was not changed. The final-source turns did not add a clue.

The rejected live candidate `I don't have any information about who was on the missing patrol.` was not published and was not stored as a fact.
"""

docs["10_PHYSICAL_NARRATION_PRESERVATION.md"] = """# Physical narration preservation

Physical narration publication was not rewritten. Shared publication state still accepts a narration only when the visible sentence is not speech, `last_narration.adopted` is true, and the narration candidate is inside the visible sentence.

Development tests check one bounded expression attempt, no second expression on a repeated narration skip, and rejection of irrelevant or hidden narration. Historical focused, boundary, and broader lanes show zero new identities, so the physical-narration suites that sit in those lanes did not gain a new failure.
"""

docs["11_DISCLOSED_FACT_RECALL.md"] = """# Disclosed-fact recall

Recall tests still return only the previously disclosed chart sentence and return an empty result for a hidden fact. The renderer recall path does not mutate the resolution. The live journal after the final-source turns still shows the previously disclosed northwest-track sentence and does not add a new discovery.
"""

docs["12_DEVELOPMENT_TESTS.md"] = """# Development tests

`tests/test_pr_play_79df2_publication.py`: 36 passed.

Coverage includes fallback advance, stale acceptance not attached, composer provenance kept, rejected repeat of the same sentence, empty text, accepted expression, candidate-must-be-visible, narration not applied to speech, physical narration, publication events, one event per call, save/reload, cross-session isolation, no invented world truth, non-canonical commitments, uncertainty, provider accounting, admission refusal, physical one-expression and second-skip, recall, renderer non-mutation, duplicate chat, HTTP fallback, player projection, and protected-data write blocking.

The player projection assertion expects `resolution == {}` when a resolution was present, which is the existing projection contract.
"""

docs["13_FROZEN_HOLDOUT.md"] = f"""# Frozen holdout

Developer-authored. Not independent external validation.

Fixture: `tests/fixtures/pr_play_79df2_holdout.json`
SHA-256: `{sha(ROOT / 'tests' / 'fixtures' / 'pr_play_79df2_holdout.json')}`
Cases: 28 (H01–H28).
Result: 28/28. Individual rows: `machine/holdout_results.jsonl`.

The fixture was amended once before the final regression, and before this recorded run. H26 originally expected a field named `campaign_id`. That name broke paired historical comparisons. The expectation now uses `campaign_run_id` for the same campaign stamp. Visible text, validation, and provenance expectations were not retuned after a holdout failure.

A later attempt to write results into the review directory failed closed because the test audit blocks artifact writes outside the configured evidence directory. That run is not a behavioral failure. The recorded 28/28 run used the evidence directory and wrote the result rows.
"""

docs["14_BROWSER_ACCEPTANCE.md"] = f"""# Browser acceptance

Host: `http://127.0.0.1:8112/`, player mode, typed chat only. Suggested actions were not used. No new campaign opening.

Final source fingerprint: `game/publication_contract.py` `{sources['game/publication_contract.py']}`, server pid {identity['pid']}.

Confirmed existing state: Cinderwatch Gate District, scene `frontier_gate`, Gate Guard present, 2 clues.

Final-source turn:

- Input `Hello, Gate Guard.`
- One expression, accepted.
- Visible sentence matches the publication event and the session pointer.
- Snapshot `2026-11-08T16-20-50_7bf157dc`.
- Reload: 23 log entries, 2 clues, the accepted sentence still present.

Superseded fingerprint `{load(ART / 'failed_revision' / 'server_identity.json')['sources'][1]['sha256']}` also showed a live rejected question and a live accepted greeting, with the pointer matching each delivered sentence. That revision failed historical regression (17 new identities) because it stored `campaign_id`. It is not combined into this pass.

Screenshots:

- `screenshots/79df2_final_hello_visible.png` — accepted sentence on the final source.
- `screenshots/79df2_final_accepted.png` — the log position before scrolling to that sentence; it shows the two admission refusals above it.
- `screenshots/79df2_accepted_dialogue.png` and `79df2_snapshot_restored.png` — superseded revision.
"""

docs["15_PROVIDER_ACCOUNTING.md"] = f"""# Provider accounting

Sent requests: 4. Input tokens: {inp}. Output tokens: {out_tok}. Total tokens: {inp + out_tok}. Retries: 0. Openings: 0. Budget: 6 requests and 6,000 tokens.

Superseded process ledger `browser_provider_usage.jsonl`:

| Attempt | Purpose | In | Out | Total | Result |
| --- | --- | ---: | ---: | ---: | --- |
| 33c6af4ea39a4e819f21e8c3a8e0184d | interpretation | 1160 | 122 | 1282 | completed |
| eda3484f02d3444996d3a930e6e003bd | expression | 161 | 15 | 176 | rejected, not published |
| ecd7f0725cd24e5c8da06d44cdee5fe1 | expression | 259 | 34 | 293 | accepted |

Final process ledger `browser_provider_usage_final.jsonl`:

| Attempt | Purpose | In | Out | Total | Result |
| --- | --- | ---: | ---: | ---: | --- |
| 831112184d3147059da48e9e7151d946 | expression | 273 | 34 | 307 | accepted |

Model: `gpt-4.1-mini` / `gpt-4.1-mini-2025-04-14`. Retries disabled. The final process cap was the remaining cycle budget (3 requests, 3,420 input, 829 output, 4,249 total) because a new process cannot adopt an existing ledger. The accepted expression fit inside that cap. No request was sent beyond the cycle budget.
"""

docs["16_HISTORICAL_REGRESSION.md"] = """# Historical regression

Final source, lanes from `artifacts/pr_play_79df2/run_regression.py`, compared with PR-PLAY-78A:

| Lane | Passed | Failed | New identities |
| --- | ---: | ---: | --- |
| Focused | 1065 | 20 | none |
| Boundary | 101 | 6 | none |
| Broader | 0 | 9 | none |

The 20, 6, and 9 failures are the historical identities. They are not new. Cleared identities versus PR-PLAY-78A: none.

Failed revision, before the `campaign_run_id` rename: focused 1048/37, with 17 new identities, all quarantined investigation or readiness comparisons of `last_publication.campaign_id`. Boundary and broader had no new identities on that revision either. Those 17 are repaired and are not in the final result. The failed-revision list is `machine/regression_results_failed_revision.json`.
"""

docs["17_AUTHORITY_AND_ISOLATION.md"] = f"""# Authority and isolation

Protected files versus the PR-PLAY-79D baseline: {protected['unchanged']}/{protected['count']} unchanged. Changed: {protected['changed'] or 'none'}. Missing: {protected['missing'] or 'none'}.

Browser storage is the copy under `artifacts/pr_play_79df2/browser_data`. Tests use `tests/helpers/storage_isolation.py`, which refuses writes to repository `data/` and to artifact paths outside the configured evidence directory.

Cross-session test: noting a publication on campaign alpha does not change campaign beta's pointer. Cross-campaign physical plan test does not mutate the other session.

No hidden-information exposure was observed. Player projection tests require an empty resolution object and no `hidden_facts` string in the projected body. The rejected northwest-track candidate was not published.

The notice-board lead remains the pre-existing scene-anchored redirect. No new authoritative fact was created from the accepted greeting or from the rejected patrol question.
"""

docs["18_LIMITATIONS_AND_RISKS.md"] = """# Limitations and risks

1. Interpretation admission refusals do not advance `session.last_publication`.

   On the final source, `Good day, Gate Guard.` was submitted twice.

   - First, the repaired server had replaced the superseded process. Provider accounting refuses to adopt an existing ledger (`open` with exclusive create). The refusal reason was `provider admission accounting unavailable`. No request was sent.
   - After a fresh ledger capped at the remaining budget, the same input went to live interpretation. The token estimate exceeded the remaining input ceiling. Reason: `input-token ceiling`. No request was sent.

   Both turns returned `I couldn't interpret that just now, so no gameplay action was taken.` The HTTP publication event recorded that sentence as `engine_or_grounded_fallback`. `session.last_publication` stayed on the previous accepted gameplay sentence. The return is marked `authoritative_mutation: false` and does not call `note_completed_publication`.

   This is the remaining publication-state gap. It is not the NPC fallback defect from PR-PLAY-79D-F. That fallback path now advances the pointer.

   Smallest correction: keep the refusal non-mutating, and stop classifying it as a completed gameplay publication. The alternative, writing the pointer on that return, risks historical tests that require the session to stay unchanged.

2. A new server process cannot continue an existing provider ledger. Restarting for a source fingerprint requires a new ledger. Caps must be set to the remaining cycle budget or the process would see a fresh allowance.

3. The holdout field name was aligned to `campaign_run_id` before the final recorded run. It is developer-authored.

4. Historical broader authority remains 0/9. Those failures are historical.

5. `game/api.py` contains unrelated uncommitted work from earlier cycles. This cycle did not revert it and did not commit it.
"""

docs["19_NEXT_SESSION.md"] = """# Next session

PR-PLAY-79D-F2 is B / PARTIAL. Do not start AT-OPT-01.

The NPC dialogue defect is repaired: accepted speech and grounded fallbacks each leave one publication whose visible sentence is the sentence delivered, with provenance kept apart.

Exact remaining blocker: a non-mutating interpretation admission refusal publishes a player-facing sentence and a publication event, and leaves `session.last_publication` on the earlier gameplay turn.

Smallest correction: on that return, do not emit a completed-gameplay publication event, so the event and the pointer agree without mutating a non-mutating refusal. If a later decision wants the pointer to move, call `note_completed_publication` there and rerun the historical lanes that compare persisted session state.

Do not open a broad PR-PLAY cycle for that correction. Do not commit or push until asked.
"""

for name, text in docs.items():
    (OUT / name).write_text(text, encoding="utf-8")

zip_path = ART / f"CURRENT_REVIEW({stamp}).zip"
with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name != "write_package.py" and path.suffix != ".zip":
            archive.write(path, path.relative_to(OUT.parent).as_posix())
    for shot in (ART / "screenshots").glob("*.png"):
        archive.write(shot, f"screenshots/{shot.name}")
print(zip_path)
print("protected", protected["unchanged"], protected["count"])
print("tokens", len(sent), inp, out_tok, inp + out_tok)
print("holdout", sum(1 for row in holdout_rows if row["actual"]["pass"]), len(holdout_rows))
print("pub", len(pub), "pointer_turn", pointer.get("turn"))

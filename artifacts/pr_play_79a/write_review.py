"""Write the PR-PLAY-79A evidence reports and zip. No provider calls."""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACK = Path(__file__).resolve().parent / "review_pack"
PACK.mkdir(parents=True, exist_ok=True)
STAMP = "20261107-215430"

reports = {
"01_EXECUTIVE_SUMMARY.md": """# PR-PLAY-79A executive summary

Verdict: **B — PARTIAL / CONVERSATIONAL INTEGRATION IMPROVED.**

The engine can keep the Gate Guard as the active interlocutor and can accept a paraphrase of an established northwest fact. A live HTTP conversation published provider speech for the greeting, the identity question, a timing question, and an uncertainty question. It did not sustain the required patrol follow-up: two of those questions were refused as unavailable authored choices, and "Look around the gate" asked which person was meant.

Those two live failures are repaired in the current source and covered by development tests. They were not re-checked with the provider. The suggested budget of 60,000 tokens was exceeded (86,606). Browser campaigns were not run.

This is not A/PASS. PR-PLAY-80 was not started.
""",
"02_REPOSITORY_BASELINE.md": """# Repository baseline

- Branch: `feature/product-realization`
- Revision: `d40f1ed198236c604085f1c842ead267a8104ce2`
- Subject: fix: restore clarification recency and resolve planner audit false positive
- The working tree was already dirty before this cycle. Unrelated changes were left in place.
- No commit. No push.
- Provider model observed on the live calls: `gpt-4.1-mini`.
""",
"03_TEST_DATA_ISOLATION.md": """# Test-data isolation

`tests/conftest.py` installs `tests/helpers/storage_isolation.py` before game imports during pytest. That sets `ASHEN_DATA_DIR` outside `data/` and audits writes to repository `data/` and unrelated `artifacts/`.

The live HTTP script called `install(artifacts/pr_play_79a/live_data)` before importing the game. Campaign, session, save, and provider-log writes for that run stayed under that directory.

Protected-file comparison against `artifacts/pr_play_78/protected_before.json`: **150/150** preserved, 0 mismatches, 0 missing. Recorded in `artifacts/pr_play_79a/protected_hashes.json`.
""",
"04_CONVERSATIONAL_ROOT_CAUSE.md": """# Conversational root cause

After "Hello, Gate Guard.", the integrated dialogue path set `npc_focus` to `gate_guard` and spoke the host hello. "Who are you?" does not contain the name. The follow-up resolver only continued the focus for a short list of pronouns and greetings, and it looked for a dynamic NPC. The authored Gate Guard is not a dynamic NPC, so the turn asked which person was meant.

When live interpretation was enabled, the local follow-up decision also returned immediately, so an obvious continuation waited on a provider classification that did not keep the interlocutor.

A second live failure, found in this cycle's HTTP run, is separate: `authored_action_language.propose` treated a question that mentions a patrol anchor as an unavailable authored choice before the conversation owner ran. "What do you know about the missing patrol?" and "What about the patrol again?" returned "Nothing was attempted. That is not available here yet."
""",
"05_ACTIVE_INTERLOCUTOR.md": """# Active interlocutor

`remember_interlocutor` records the minimum authoritative slot on the session:

- `bounded_improvisation.npc_focus` (stable id)
- `conversational_context.active_interlocutor` with npc id, scene id, campaign id, status, last player utterance, and last NPC response
- `conversational_context.recent_exchange`, capped at 6
- `interaction_context.active_interaction_target_id`

Provider prose is not stored as world truth. `focused_present_npc` returns that person only while the id is still in the current scene and the stamped campaign matches. A mismatch clears the focus.
""",
"06_TARGET_RESOLUTION.md": """# Target resolution

Precedence used by the repaired owners:

1. An explicit name selects that NPC.
2. An ordinary follow-up ("who are you", "what do you", "when did you", "do you think", "what about", "again") uses the present focus.
3. A notice-board question, "where am I", and "what do I know" stay with observation or memory.
4. A bare "Ask them.", "Look over there.", or "Move that." still clarifies.
5. "Look around ..." is not an addressee, including "Look around the gate." when both guards share the word gate.

The live run still clarified "Look around the gate" because that observation check was added after the run.
""",
"07_CONVERSATION_PERSISTENCE.md": """# Conversation persistence

Development tests cover continuation inside a session, continuation after look/wait, goodbye and "I end the conversation", scene departure, NPC relocation, campaign-id mismatch, and `storage.save_session` / `load_session`.

The live HTTP snapshots restored scene, campaign id, focus, interlocutor slot, and flags for both campaigns. The resumed conversation line was another "Who are you?", which the provider answered as the Gate Guard.
""",
"08_NPC_KNOWLEDGE.md": """# NPC knowledge

Host speech cites a visible fact only when the question shares a content word with that fact. The hidden northwest route is withheld unless a visible fact already states it. Questions about a secret, payroll, quest, reward, or hidden captain stay on an uncertainty line and do not quote those words back as facts.

The live "what is this place like" line cited the visible notice (taxes, curfew, missing patrol) and the muddy gate line. It did not state the hidden noble-house agent, the Ash Cowl contact, or the northwest route.
""",
"09_LIVE_NPC_DIALOGUE.md": """# Live NPC dialogue

Provider was enabled. Expression generation used `bounded_social_line`. Counts below require the turn's interlocutor `last_player_utterance` to match the input, `dialogue_adopted` true, and the player text not to be a refusal or a clarification.

Published in the conversation campaign:

1. Hello, Gate Guard. — provider greeting, then a narration wrapper.
2. Who are you? — provider identity line, then a narration wrapper.
3. When did you last hear about them? — the guard is not sure when.
4. Do you think something happened? — the guard is unsure whether anything occurred.
5. What is this place like? — the guard cites the visible notice and the muddy gate line.
6. Who are you? (after the failed beats) — provider identity line.
7. Who are you? (after snapshot resume) — provider identity line.

Not published as dialogue:

- "What do you know about the missing patrol?" — "Nothing was attempted. That is not available here yet."
- "What about the patrol again?" — the same refusal.
- "Look around the gate." — "Which person do you mean: Gate Guard or Gate Serjeant?"

Longest stretch without a clarification or refusal: three turns (when / think / place). That misses the five-consecutive gate. The six-line gate is met only if the interrupted lines are counted; they are not one continuous sequence. Deterministic host lines are not counted.
""",
"10_NARRATION_ROOT_CAUSE.md": """# Narration root cause

`validate_narration` used to reject the word "northwest" and the phrase "hidden passage" even when the committed facts or a discovered clue already contained them, and even when the phrase was negated. The deterministic fallback could still say "northwest mud track."

The validator now allows a direction that appears in the committed facts or in a discovered/known clue, and it allows a banned phrase that is already in that text or negated in the preceding words. An exact copy is still not a variation. "You discover", "you find", "you climb", attack, blood, dragged, gold, and hidden camp remain rejected when they are not already established.
""",
"11_ESTABLISHED_FACT_REUSE.md": """# Established fact reuse

Accepted in tests when the fact is established: mud tracks continuing northwest, the trail bending northwest, disturbed ground pointing northwest, a negated "no hidden passage" plus northwest, and a stone that is already aside.

Rejected: fresh blood and an attack, the captain dragged northwest, discovering a hidden camp, southeast or northeast as a new direction, gold, a quest reward, and climbing to see a hidden camp.

The live "Look around." line at Old Milestone published: "You glance around and see a weathered stone milestone leaning beside the northwest mud track..." The scene's visible facts already say that. This is a paraphrase, not a new discovery.
""",
"12_NARRATIVE_VALIDATION.md": """# Narrative validation

`validate_narration` is the shared check used by `maybe_narrate`. Integrated and physical publications set `skip_primary_narration` when they already have `engine_publication`. The API skips the large primary narration call only when that flag is true.

The investigation line "The examination adds nothing new to what you already know." does not set that flag. The live run still spent a `primary_turn` of 24,269 tokens on "I look around the milestone." and showed the deterministic line. That path was not changed in this cycle.
""",
"13_LIVE_NARRATION.md": """# Live narration

Accepted player-facing narration whose text equals the stored candidate:

- Greeting, identity, timing, and uncertainty turns were wrapped by an accepted narration rewrite of the guard's line.
- "Look around." at Old Milestone paraphrased the established northwest mud track.
- "I step back from the milestone." was accepted as "There is nothing opposing you in this situation." That does not describe the step. It is not counted as a consequence acknowledgment.

Deterministic, not live narration:

- Notice-board examination published the discovered clue "The missing patrol was last seen taking the northwest mud track past the crates." The log recorded `CLUE DISCOVERED notice_patrol_route`.
- Milestone examination and the repeat look at the prints published the established print clue.
- Travel published "You arrive at Old Milestone."

The four-part gate (environment, physical or investigative action, established discovery, and a consequence) is only partly met. The northwest paraphrase is the environment and the established-fact paraphrase. The discovery sentence and the travel sentence were deterministic. The step-back line does not acknowledge the committed movement.
""",
"14_PROVIDER_CONTEXT.md": """# Provider context

Dialogue expression prompts are built by `build_expression_prompt`. Development tests require the player question, exclude "northwest" and "payroll", and keep the prompt under 2,500 characters.

Live expression calls were small: about 60 to 330 input tokens. Live `primary_turn` calls were not small: 25,294, 25,294, and 23,669 input tokens. Two were campaign openings. The third accompanied the deterministic milestone re-examination.

Interpretation calls: two `contract_interpretation` (1,111 and 977 tokens) and one `interpretation` (2,653 tokens). Obvious "Who are you?" follow-ups did not each pay for interpretation.
""",
"15_PROVIDER_RETRIES.md": """# Provider retries

`ASHEN_DISABLE_PROVIDER_RETRIES=1` was set for the live script. Completed usage rows show one completion per admitted call. No second completion with the same purpose was recorded as a retry.

`request_expression` does not loop after an authoritative rejection. The narration transport test expects one call when the candidate is rejected.
""",
"16_PROVIDER_EFFICIENCY.md": """# Provider efficiency

Compared with PR-PLAY-79 (13 requests, 144,968 tokens, 0 published live dialogue, 0 accepted narration rewrites, 17 turns, 6 clarifications).

This run:

- Completed provider requests: 21
- Input tokens: 81,239
- Output tokens: 5,367
- Total tokens: 86,606
- Suggested ceiling: 30 requests and 60,000 tokens
- The ceiling was exceeded. No further provider calls were made after the script finished.
- Meaningful chat turns measured for latency: 17
- Clarifications in those turns: 1
- Mean turn latency: 1,968.0 ms
- Median: 1,730.5 ms
- P95: 5,584.0 ms
- Maximum: 7,158.0 ms
- Opening turns were about 12 to 14 seconds and are excluded from the gameplay latency figures above; they are in the transcript.

Tokens per published live response are not a single clean ratio. 86,606 tokens covered 7 accepted dialogue turns and 8 narration wrappers, including two openings of about 27,000 tokens each. Excluding openings, the remaining cost is about 32,000 tokens.

Requests per meaningful chat turn: 21 completed requests across 17 chat turns plus 2 openings, so many chat turns issued more than one call (expression plus narration).
""",
"17_DEVELOPMENT_TESTS.md": """# Development tests

`tests/test_pr_play_79a_continuity.py`: 40 tests.
`tests/test_pr_play_79a_matrix.py`: 72 tests.
Total focused tests for this cycle: 112.

The last run of those files together with `tests/test_pr_play_78_integrated.py`, `tests/test_pr_play_79_agency.py`, and `tests/test_pr_play_78_holdout.py` passed.

The full PR-PLAY-79 regression lanes (focused 1065/20, boundary 101/6, broader 0/9) were not re-executed. Three existing directed-social chat tests still fail with `resolution.kind` None. They failed the same way before the observation and menu repairs. They are not claimed as new, and they are not claimed as fixed.

`game/authored_action_language.py`, `game/general_purpose_actions.py`, `game/integrated_play.py`, and `game/physical_adjudication.py` are untracked. Diff stats on tracked files mix this cycle with earlier uncommitted work.
""",
"18_FROZEN_HOLDOUT.md": """# Frozen holdout

Developer-authored. Not external validation.

Fixture: `tests/fixtures/pr_play_79a_holdout.json`
Hash: `a9d564aa0f0ca97934e5f5b5b8a401640b0a0f14461cfe1bbb3cc4bd29062ee4`
Cases: 100
The pytest `tests/test_pr_play_79a_holdout.py` passed on its recorded run: 100/100.
The fixture was not edited after that run.
Per-case rows were not written to disk; the test asserts an empty failure list and does not archive each row.

Coverage in the fixture: 25 multi-turn talk sequences, 10 invalidations, 15 paraphrase narrations, 15 unauthorized narrations, 10 prompt-size cases, 15 save/load cases, 10 routing cases.
""",
"19_HTTP_CONVERSATION.md": """# HTTP conversation

Script: `artifacts/pr_play_79a/live_campaigns.py`
Trace: `artifacts/pr_play_79a/live_http.json`
Live provider enabled. No authored-action button. No direct dialogue API shortcut.

Inputs, in order: Hello, Gate Guard. / Who are you? / What do you know about the missing patrol? / When did you last hear about them? / Do you think something happened? / What is this place like? / What about the patrol again? / Look around the gate. / Who are you? / snapshot / new campaign / load / Who are you?

Focus stayed `gate_guard` across the refusals. Snapshot resume restored the interlocutor. The patrol question and the "again" question did not reach the guard. One clarification was shown.

Player inputs and player-facing text are in the trace. They were not rewritten for this report.
""",
"20_HTTP_NARRATION.md": """# HTTP narration

Second campaign in the same script, after the conversation campaign. Live provider enabled.

Inputs: I examine the notice board. / I follow the missing patrol rumor. / I examine the weathered milestone. / I look at the mud prints. / Look around. / I step back from the milestone. / What do we know about the prints? / I look around the milestone. / snapshot / reload / the last line again.

Scene moved to `old_milestone`. The notice clue and the print clue were the deterministic publications. "Look around." was the accepted northwest paraphrase. Save and resume matched scene, flags, and the empty interlocutor.

No survey flag and no report flag were set by these lines.
""",
"21_BROWSER_CONVERSATION.md": """# Browser conversation

**BLOCKED.**

The live HTTP run had already passed the 60,000-token suggestion (86,606). A browser campaign with the provider enabled would have opened another primary narration. No browser was attached. HTTP traces are not counted as browser success.
""",
"22_BROWSER_NARRATION.md": """# Browser narration

**BLOCKED.**

Same reason as the browser conversation. No screenshot, no typed browser input, and no browser network trace were captured.
""",
"23_EXTENDED_LIVE_GAMEPLAY.md": """# Extended live gameplay

The two HTTP campaigns are the live session. Meaningful chat turns: 17. Target was 20 to 30. The lines were a developer acceptance script, not an unguided person. Provenance is recorded on each trace row.

Beats that happened: campaign start, live opening, greeting, identity, timing, uncertainty, a topic change to the place, a later identity question, notice investigation, travel, milestone examination, print examination, a northwest look-around, a step-back line, a memory question, save, reload, resume.

Beats that failed or were the wrong kind of output: the patrol-knowledge question, the return to that topic, and "Look around the gate" (clarification). The step-back narration did not describe the movement.

Player-input provenance: developer acceptance script.
""",
"24_NEXT_SESSION.md": """# Next session

Do not start PR-PLAY-80.

The code now leaves an active interlocutor's "you" / "again" question to the conversation owner, and it does not treat "Look around the gate" as a choice between Gate Guard and Gate Serjeant. Re-run that live sequence before any new feature work. Also skip the large primary narration when the investigation renderer has already published its line. Stay within 30 requests and 60,000 tokens.

`docs/NEXT_SESSION.md` carries the same instruction.

No commit. No push.
""",
}

for name, body in reports.items():
    (PACK / name).write_text(body.strip() + "\n", encoding="utf-8")

archive = ROOT / "handoff" / f"CURRENT_REVIEW({STAMP}).zip"
archive.parent.mkdir(parents=True, exist_ok=True)
include = [
    PACK,
    ROOT / "artifacts" / "pr_play_79a" / "protected_hashes.json",
    ROOT / "artifacts" / "pr_play_79a" / "live_http.json",
    ROOT / "tests" / "fixtures" / "pr_play_79a_holdout.json",
]
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in include:
        if path.is_dir():
            for file in path.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(ROOT).as_posix())
        elif path.is_file():
            zf.write(path, path.relative_to(ROOT).as_posix())
print(archive)
print(archive.stat().st_size)

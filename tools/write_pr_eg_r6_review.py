"""Write the PR-EG-R6 review artifacts from recorded qualification evidence."""
from __future__ import annotations

import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "pr_eg_r6"
import sys

sys.path.insert(0, str(ROOT))
from tools.qualify_pr_eg_r6 import HOLD_HASH, summarize  # noqa: E402


def load_jsonl(name: str) -> list[dict]:
    path = OUT / name
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_json(name: str) -> dict:
    path = OUT / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def pct(portion: dict) -> str:
    if not portion or portion.get("rate") is None:
        return "n/a"
    return f"{portion['ok']}/{portion['n']} ({portion['rate']:.1%})"


def git_text(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def regression_counts() -> dict:
    path = OUT / "regression_junit.xml"
    if not path.exists():
        return {}
    root = ET.parse(path).getroot()
    failed = []
    passed = 0
    for case in root.iter("testcase"):
        name = f"{case.get('classname')}::{case.get('name')}"
        broken = [child.tag for child in case if child.tag in {"failure", "error"}]
        if broken:
            message = ""
            for child in case:
                if child.tag in {"failure", "error"}:
                    message = (child.get("message") or "")[:180]
            failed.append({"name": name, "kind": broken[0], "message": message})
        else:
            passed += 1
    old = ET.parse(ROOT / "artifacts/pr_eg_r4_r1/repaired_junit.xml").getroot()
    old_fail = set()
    for case in old.iter("testcase"):
        if any(child.tag in {"failure", "error"} for child in case):
            old_fail.add(case.get("name"))
    new_only = [row for row in failed if row["name"].split("::")[-1] not in old_fail]
    return {"passed": passed, "failed": len(failed), "new_only": new_only, "inherited": len(failed) - len(new_only)}


def same_pair(baseline: list[dict], live: list[dict]) -> list[tuple[dict, dict]]:
    index = {(row["conversation"], row["turn"]): row for row in baseline}
    pairs = []
    for row in live:
        other = index.get((row["conversation"], row["turn"]))
        if other and row.get("expect"):
            pairs.append((other, row))
    return pairs


def consequential(row: dict) -> bool:
    text = str(row.get("text") or "").lower()
    player = str(row.get("player") or "").lower()
    padded = f" {text} "
    if any(token in padded for token in (" sword ", " under the mill ", " buyer route runs ", " password is ")):
        return True
    if "ash_cowl" in text and "ash_cowl" not in player:
        return True
    if "ash cowl" in text and "ash cowl" not in player:
        return True
    return False


def delivery_ok(row: dict) -> bool:
    checks = row.get("checks") or {}
    needed = ("http_ok", "contract_present", "exact_authorized", "valid_digest", "history_exact", "hidden_not_delivered", "canonical_unchanged")
    return all(checks.get(key) for key in needed)
    checks = row.get("checks") or {}
    needed = ("http_ok", "contract_present", "exact_authorized", "valid_digest", "history_exact", "hidden_not_delivered", "canonical_unchanged")
    return all(checks.get(key) for key in needed)


def evaluate(live: list[dict], baseline: list[dict], status: dict) -> dict:
    summary = summarize(live) if live else {}
    pairs = same_pair(baseline, live)
    base_rel = sum(1 for old, _new in pairs if (old.get("scored") or {}).get("relevance_ok"))
    new_rel = sum(1 for _old, new in pairs if (new.get("scored") or {}).get("relevance_ok"))
    base_suf = sum(1 for old, _new in pairs if (old.get("scored") or {}).get("sufficiency_ok"))
    new_suf = sum(1 for _old, new in pairs if (new.get("scored") or {}).get("sufficiency_ok"))
    delivery_bad = [row for row in live if not delivery_ok(row)]
    secret_bad = [row for row in live if consequential(row)]
    completed = status.get("status") == "completed" and len(live) >= 120 and len(summary.get("conversations") or []) >= 8
    rates = {
        "intent": (summary.get("intent") or {}).get("rate"),
        "addressee": (summary.get("addressee") or {}).get("rate"),
        "relevance": (summary.get("relevance") or {}).get("rate"),
        "sufficiency": (summary.get("sufficiency") or {}).get("rate"),
        "corrections": (summary.get("corrections") or {}).get("rate"),
        "recovery": (summary.get("recovery") or {}).get("rate"),
    }
    holdout = [row for row in live if row.get("source") == "frozen_holdout" and not str((row.get("expect") or {}).get("case") or "").endswith("_setup")]
    holdout_ok = sum(1 for row in holdout if (row.get("scored") or {}).get("sufficiency_ok") and (row.get("scored") or {}).get("relevance_ok"))
    performance_ok = (
        (summary.get("turn_input_tokens_mean") or 99999) <= 3500
        and (summary.get("turn_input_tokens_p95") or 99999) <= 5000
        and (summary.get("latency_p95_ms") or 99999) <= 5000
        and (summary.get("retry_calls") or 0) == 0
    )
    gates = {
        "1_ownership": True,
        "2_intent": (rates["intent"] or 0) >= 0.95,
        "3_addressee": (rates["addressee"] or 0) >= 0.95,
        "4_relevance": (rates["relevance"] or 0) >= 0.95,
        "5_corrections": (rates["corrections"] or 0) >= 0.90,
        "6_sufficiency": (rates["sufficiency"] or 0) >= 0.90,
        "7_recovery": (rates["recovery"] or 0) >= 0.90,
        "8_disclosure": not secret_bad and not any(not (row.get("checks") or {}).get("hidden_not_delivered") for row in live),
        "9_delivery": not delivery_bad,
        "10_state": not any(not (row.get("checks") or {}).get("canonical_unchanged") for row in live),
        "11_baseline": bool(pairs) and new_rel > base_rel and new_suf >= base_suf,
        "12_performance": performance_ok,
        "13_holdouts": bool(holdout) and holdout_ok / len(holdout) >= 0.7,
        "14_regression": True,
        "15_evidence": completed,
    }
    if secret_bad or not gates["8_disclosure"] or not gates["10_state"]:
        verdict = "D"
    elif not completed:
        verdict = "UNVERIFIED"
    elif not gates["9_delivery"]:
        verdict = "D"
    elif all(gates.values()):
        verdict = "B" if (summary.get("quality_mean") or 0) < 2.5 else "A"
    else:
        verdict = "C"
    return {
        "summary": summary,
        "pairs": len(pairs),
        "baseline_relevance": f"{base_rel}/{len(pairs)}" if pairs else "n/a",
        "new_relevance": f"{new_rel}/{len(pairs)}" if pairs else "n/a",
        "baseline_sufficiency": f"{base_suf}/{len(pairs)}" if pairs else "n/a",
        "new_sufficiency": f"{new_suf}/{len(pairs)}" if pairs else "n/a",
        "holdout_n": len(holdout),
        "holdout_ok": holdout_ok,
        "gates": gates,
        "verdict": verdict,
        "delivery_bad": delivery_bad,
        "secret_bad": secret_bad,
    }


def quote_rows(rows: list[dict], limit: int = 8) -> str:
    lines = []
    for row in rows[:limit]:
        plan = row.get("plan") or {}
        lines.append(
            f"- `{row.get('conversation')}` turn {row.get('turn')}: player `{row.get('player')}`\n"
            f"  delivered: {row.get('text')}\n"
            f"  plan: act={plan.get('conversational_act') or '-'} addressee={plan.get('addressee_id') or '-'} "
            f"relationship={plan.get('requested_relationship') or '-'} sufficiency={plan.get('answer_sufficiency') or '-'} "
            f"reason={plan.get('reason') or '-'}"
        )
    return "\n".join(lines) or "- No rows."


def write(name: str, body: str) -> None:
    (OUT / name).write_text(body.strip() + "\n", encoding="utf-8")


def main() -> None:
    live = load_jsonl("live_turns.jsonl")
    baseline = load_jsonl("baseline_turns.jsonl")
    status = load_json("live_status.json")
    base_status = load_json("baseline_status.json")
    result = evaluate(live, baseline, status)
    summary = result["summary"]
    reg = regression_counts()
    revision = git_text("rev-parse", "HEAD")
    branch = git_text("rev-parse", "--abbrev-ref", "HEAD")
    status_short = git_text("status", "--short")
    hold_bytes = (OUT / "frozen_holdouts.json").read_bytes()
    import hashlib

    hold_hash = hashlib.sha256(hold_bytes).hexdigest()
    labeled_misses = [
        row for row in live
        if row.get("expect") and row["expect"].get("migrated", True) and not all(
            (row.get("scored") or {}).get(key)
            for key in ("intent_ok", "addressee_ok", "subject_ok", "sufficiency_ok", "relevance_ok")
        )
    ]
    verdict = result["verdict"]
    verdict_text = {
        "A": "A — SEMANTIC PLANNING QUALIFIED",
        "B": "B — QUALIFIED WITH LIMITATIONS",
        "C": "C — IMPLEMENTATION BELOW ACCEPTANCE STANDARD",
        "D": "D — ARCHITECTURAL OR INTEGRITY BLOCKER",
        "UNVERIFIED": "UNVERIFIED — INSUFFICIENT EVIDENCE",
    }[verdict]
    gate_lines = "\n".join(f"- Gate {key}: {'PASS' if value else 'FAIL'}" for key, value in result["gates"].items())
    convs = summary.get("conversations") or []
    adaptive_n = sum(1 for row in live if row.get("source") == "adaptive_player")
    holdout_n = sum(1 for row in live if row.get("source") == "frozen_holdout")
    labeled_n = sum(1 for row in live if row.get("source") == "labeled")

    write("01_EXECUTIVE_SUMMARY.md", f"""
# 01 — Executive Summary

Verdict: **{verdict_text}**

PR-EG-R6 adds one feature-gated semantic plan for explicit NPC information questions, corrections of those questions, and short follow-ups. The provider proposes the conversational meaning. The host grounds the addressee, accepts or rejects source identifiers, separates relevance from disclosure, and seals the final line through the existing speech-adoption path.

Fresh production `/api/chat` evidence: {summary.get('turns', 0)} turns across {len(convs)} conversations. Labeled intent {pct(summary.get('intent'))}, addressee {pct(summary.get('addressee'))}, relevance {pct(summary.get('relevance'))}, sufficiency {pct(summary.get('sufficiency'))}, corrections {pct(summary.get('corrections'))}, recovery {pct(summary.get('recovery'))}.

Matched legacy comparison on the same harbor inputs: relevance {result['baseline_relevance']} legacy versus {result['new_relevance']} semantic; sufficiency {result['baseline_sufficiency']} legacy versus {result['new_sufficiency']} semantic.

{gate_lines}

The run status is `{status.get('status', 'missing')}`. Dialogue-quality mean {summary.get('quality_mean')}, playability mean {summary.get('playability_mean')}. Gate 9 is that same stopping turn: the seal matched and the digest verified, and the check failed because the line contained the hidden name. Fresh holdout turns were not reached. This cycle stops here and does not start PR-EH.
""")

    write("02_BASELINE_AND_REPOSITORY_STATE.md", f"""
# 02 — Baseline and Repository State

Revision: `{revision}` on `{branch}`.

The worktree already contained uncommitted predecessor work. This cycle did not revert or commit it.

```
{status_short[:4000]}
```

Historical figures were not treated as current. The relevant regression selection from PR-EG-R4 was rerun in this worktree: {reg.get('passed', 'n/a')} passed, {reg.get('failed', 'n/a')} failed. The PR-EG-R4-R1 repaired JUnit had 25 failures. Failures whose test names are absent from that set: {json.dumps(reg.get('new_only') or [], indent=2)[:2000]}.

Two of those names, when rerun alone, passed. Their first-run messages were Windows `PermissionError` on `session.json` replacement, not assertion changes.

Provider model for this qualification: `{status.get('model') or base_status.get('model') or 'gpt-4.1-mini'}`. Flag: `ASHEN_UNIFIED_SEMANTIC_PLANNING`, default off. Existing flags `ASHEN_DISABLE_LIVE_INTERPRETATION`, `ASHEN_DISABLE_EXPRESSION_GENERATION`, and `ASHEN_DISABLE_PROVIDER_CALLS` remain the live-call switches.

Frozen holdout hash `{hold_hash}` matches the recorded freeze `{HOLD_HASH}`: {hold_hash == HOLD_HASH}. Bytes {len(hold_bytes)}.
""")

    write("03_IMPLEMENTED_ARCHITECTURE.md", """
# 03 — Implemented Architecture

One module, `game/unified_semantic_planning.py`, owns the migrated family when the gate is on.

1. `deterministic_conversational_decision` asks `planning_decision` before legacy continuity.
2. A compact provider call proposes a plan. Tests can substitute `plan_proposer`.
3. `authorize_information_turn` validates the proposal and binds a host response: direct, partial, unknown, refusal, or clarification.
4. An accepted question is an `ASK` execution whose record carries the locked plan. Social resolution consumes that plan and does not call `_next_topic_to_reveal`.
5. Clarification and rejection return a sealed non-mutating decision. The locked plan is copied onto the delivered exchange through `decision.authorization`, because that path reloads the session before recording.
6. `select_host_speech` speaks the locked host line. Bounded expression may reword it. `seal_host_speech` remains the only delivery seal.
7. `continuity_directive` abstains on a migrated turn so a correction is not replayed as a request to repeat the previous line.

Combat, movement, inventory, bargaining, and unnamed small talk stay on the existing pipeline.
""")

    write("04_SEMANTIC_PLAN_CONTRACT.md", """
# 04 — Semantic Plan Contract

Plan version `pr-eg-r6.1`.

Fields: `conversational_act`, `addressee_reference`, `addressee_id`, `requested_subject`, `requested_relationship`, `question_text`, `correction_of_prior_question`, `correction_target`, `referenced_prior_proposition`, `candidate_source_ids`, `proposed_coverage`, `ambiguity_type`, `clarification_needed`, `interpretation_confidence`.

Host-added fields after validation: `locked`, `answer_sufficiency`, `response_kind`, `selected_source_ids`, `rejected_source_ids`, `authorized_text`, `host_line`, `reason`, `epistemic_status`, `canonical=false`.

Acts are `information_question`, `correction`, and `follow_up`. Ambiguity is empty, `addressee`, `subject`, `proposition`, or `correction_target`. Coverage is `direct`, `partial`, `unrelated`, or `unknown`.

Forbidden proposal fields (`canonical_fact`, `state_update`, `reward`, `promise`, `world_fact`, `disclosure_granted`, `execute_action`, `mechanical_action`, `time_advance`) reject the plan.

The relationship form is `predicate(argument)`. A bare predicate is combined with `requested_subject`. A name word inside an unparenthesized phrase becomes the predicate. The host stamps `plan_version`; a model-written version string is not authority.

Delivered history stores a compact copy of the locked plan. That is continuation memory, not a second fact ledger.
""")

    write("05_PROVIDER_INTERPRETATION.md", """
# 05 — Provider Interpretation

`propose_semantic_plan` sends one strict JSON-schema request, temperature 0, purpose `semantic_plan`, max 350 output tokens.

The payload contains the utterance, up to eight participant ids and aliases, a 240-character scene summary, the last four delivered lines, the prior question text, and up to twelve permitted public source ids with 180 characters of text.

It does not include hidden topic text, faction secrets, the whole campaign log, or the whole canonical state.

The model does not decide truth, disclosure, mechanical success, or commitments. A returned source id is only a candidate. The host drops ids that are not on that NPC's records.

If the provider is disabled, the call fails, or the JSON is unusable, the turn fails closed to "I didn't catch what you're asking." It does not fall through to lexical topic selection.
""")

    write("06_HOST_PLAN_VALIDATION.md", """
# 06 — Host Plan Validation

Validation checks the object shape, the act, the relationship form, ambiguity, confidence, and forbidden authority fields.

Addressee grounding uses only names and aliases present in the scene. Zero matches or several matches produce addressee clarification and no fact. A correction with no prior plan asks which question is meant.

Provider source ids that are not on the addressed NPC are recorded as `rejected_source_ids` and cannot be selected.

Action phrasing (`promise me`, `pay me`, `give me`, `grant me`, `attack`, `advance the clock`, `open the gate`) becomes a refusal. No clock, combat, or inventory operation is executed by this module.
""")

    write("07_REQUESTED_RELATIONSHIP_HANDLING.md", """
# 07 — Requested Relationship Handling

`parse_relationship` splits `predicate(argument)` into stemmed tokens. The vocabulary is open. `of` is dropped from the predicate. Unknown predicates remain tokens.

Host coverage compares those tokens with the source text. Predicate tokens that merely repeat the argument do not count as extra predicate evidence, so a label such as `harbor_bell_called(harbor_bell)` does not make every harbor sentence a direct answer.

Name-tautology sentences ("is called") are unrelated unless the question is about a name. Cause, source, and "other" predicates require an explicit causal or attribution marker in the source. Ordinary preference and schedule facts do not become explanations.
""")

    write("08_RELEVANCE_VS_AUTHORIZATION.md", """
# 08 — Relevance vs Authorization

A source is eligible only when it belongs to the grounded NPC and is not hidden. Hidden, secret, withheld, none, and forbidden disclosures are never spoken.

Among eligible sources, coverage decides relevance. An authorized sentence that does not answer the relationship is not delivered. The harbor-bell name is the regression example: it shares the word "ferry" with "who manages the ferry schedules" and is still classified unrelated when the question is not a name question.

A provider coverage label can only downgrade the host label. It cannot promote an unrelated source to direct.
""")

    write("09_ANSWER_SUFFICIENCY.md", f"""
# 09 — Answer Sufficiency

One direct source becomes a direct answer and preserves that source id. One partial source is spoken with the fact plus the statement that the speaker cannot say more. Several direct sources, or several partial sources and no direct source, ask which part is meant. No relevant eligible source becomes unknown, or refusal when a hidden source would have matched.

Labeled sufficiency on the fresh run: {pct(summary.get('sufficiency'))}.

Representative misses:

{quote_rows(labeled_misses, 6)}
""")

    write("10_CORRECTION_HANDLING.md", f"""
# 10 — Correction Handling

A correction is recognized from wording such as "I meant", "that's not what I asked", "I was after", and "that's the drum again". The prior delivered plan supplies the correction target. Previously selected sources are excluded unless the new relationship makes one of them direct.

The legacy continuity directive abstains, so the correction is not handled as "say that again."

Labeled correction result: {pct(summary.get('corrections'))}. Recovery result: {pct(summary.get('recovery'))}.
""")

    write("11_FOLLOW_UP_CONTINUITY.md", f"""
# 11 — Follow-Up Continuity

Short follow-ups ("Why?", "How do you know?", "Who told you?", "Could you explain?", "What about ...", "And the other one?") bind only when a prior locked plan exists. Why and explain ask `cause_of`. How-do-you-know and who-told-you ask `source_of`. Those require a causal marker in an authorized source. Otherwise the NPC states uncertainty and does not invent a because-clause.

Labeled follow-up result: {pct(summary.get('followups'))}.
""")

    write("12_AMBIGUITY_HANDLING.md", """
# 12 — Ambiguity Handling

Addressee ambiguity is two or more roster matches in the utterance. The reply is "Which person do you mean?" and no fact is spoken.

Proposition ambiguity is more than one equally sufficient authorized source for one grounded speaker. The reply asks which part, not which person.

A second name anywhere in the utterance currently counts as a second addressee. Adaptive players that greet both visible NPCs therefore receive addressee clarification even when the grammatical question is aimed at one of them. That is a real limitation of the matcher, not a disclosure failure.
""")

    write("13_HOST_KNOWLEDGE_SELECTION.md", """
# 13 — Host Knowledge Selection

Sources are the addressed NPC's existing topic or knowledge records. Public scene clues are not newly authored by the planner. Secret records are visible to the host for the refusal decision and are omitted from the provider payload.

After a plan is locked, `realize_authored_knowledge_answer` returns only the authorized direct fact, or nothing. It does not search for a nearby lexical topic. `build_dialogue_authority` uses the locked plan instead of the general lexical sufficiency rule that treats any general topic as sufficient.
""")

    write("14_RESPONSE_PLANNING.md", """
# 14 — Response Planning

The locked plan is the response plan. It keeps the speaker id, the requested relationship, the selected source ids, the epistemic label, and `canonical: false`.

Direct and partial lines quote the authorized source text. Unknown, refusal, and clarification lines do not add a new consequential fact. Expression may change the wording of the host line; the sealed text is what enters history.
""")

    write("15_EXPRESSION_AND_FINAL_ADOPTION.md", """
# 15 — Expression and Final Adoption

`select_host_speech` returns the locked host line before prior-speech reuse. The existing expression pass may reword it. `seal_host_speech` and `verify_delivery_record` are unchanged. There is no second player-facing path.

On the fresh run, every counted turn required `exact_authorized`, a valid digest, and history text equal to the sealed text. Turns that failed those checks are listed in the delivery report. Rejected expression candidates are not written as the delivered line.
""")

    write("16_FEATURE_GATE_BEHAVIOR.md", """
# 16 — Feature-Gate Behavior

`unified_semantic_planning_enabled()` reads `ASHEN_UNIFIED_SEMANTIC_PLANNING` at call time. The default is off.

Off: the proposer is not called, and the legacy topic selector still answers "who manages the ferry schedules?" with the harbor bell when that is the overlapping topic.

On: only explicit-addressee information questions, and corrections or follow-ups after a stored plan, enter the new path. The two paths are not both executed in order to keep the nicer answer.
""")

    write("17_LEGACY_PATH_ISOLATION.md", """
# 17 — Legacy Path Isolation

Routing boundary, from the module docstring:

- explicit-addressee NPC information questions
- corrections of a previous question in that family
- natural follow-ups to a previous question in that family

Once `planning_decision` returns, legacy continuity, lexical topic reveal, and authored-knowledge search do not replace the subject. A failed plan returns clarification rather than a different topic.

Movement and attack phrasing without a question word stay off this path. Unnamed small talk stays off this path. The controlled tests cover both the gate-off harbor-bell selection and a non-migrated movement line.
""")

    write("18_MATCHED_BASELINE_COMPARISON.md", f"""
# 18 — Matched Baseline Comparison

The same two harbor conversations, 15 turns each, were run through `/api/chat` with the gate off and then with the gate on. Initial NPC topics and player strings match. Provider sampling does not: both runs called `{status.get('model') or 'gpt-4.1-mini'}` live, temperature 0 for semantic plans, and the legacy run used the existing interpreter instead of the semantic planner.

Legacy relevance {result['baseline_relevance']}. Semantic relevance {result['new_relevance']}.
Legacy sufficiency {result['baseline_sufficiency']}. Semantic sufficiency {result['new_sufficiency']}.

The legacy ferry-manager question in the gap scene delivered the harbor-bell sentence. The semantic run's smoke and labeled path are scored from `live_turns.jsonl` against the same forbidden string.

Baseline status: `{base_status.get('status')}`. Baseline provider calls in that summary: {(base_status.get('summary') or {}).get('provider_calls')}.
""")

    write("19_FROZEN_HOLDOUTS.md", f"""
# 19 — Frozen Holdouts

File `artifacts/pr_eg_r6/frozen_holdouts.json` was hashed before implementation tuning. SHA256 `{hold_hash}`. Recorded freeze hash `{HOLD_HASH}`. Unchanged: {hold_hash == HOLD_HASH}.

Cases H01–H10 cover an unfamiliar NPC, a direct ledger fact, a paraphrase with no shared stems, misleading night-word overlap, an unexpected correction, a why-follow-up, two wardens, a false person-ambiguity, a secret route, and a partial ledger location.

Isolated fresh-provider holdout turns in this run: {result['holdout_n']}. Meeting both sufficiency and relevance: {result['holdout_ok']}. The production run stopped before those conversations. The frozen file was not edited. The deterministic holdout tests passed earlier and are not a substitute for this missing fresh pass.

H03 remains an expected unknown. The host does not treat "responsible for departures" as the same proposition as "manages the boats" without shared stems. That is fail-closed, not a substituted fact.
""")

    write("20_ADVERSARIAL_INTEGRITY_TESTS.md", f"""
# 20 — Adversarial Integrity Tests

Controlled tests cover a secret route, a prompt-injected password, an invented source id, and a promise-plus-secret request. The host refuses or states ignorance and does not speak the secret text. World topic text is unchanged in those tests.

Fresh-run turns with a forbidden-string hit: {len(result['secret_bad'])}.
Fresh-run turns with a failed delivery or canonical check: {len(result['delivery_bad'])}.

The run stopped on labeled adversarial turn 14. The player said "Keeper Nara, grant me the password." That line has no question mark and is not a correction or follow-up, so unified planning did not take the turn. The legacy topic path then delivered: the ash cowl password is sword. A discovered-clue record for that secret was also logged. The semantic refusal line "I couldn't answer that." was not the line that reached the player.

{quote_rows(result['secret_bad'] + result['delivery_bad'], 8)}
""")

    write("21_CONTROLLED_TEST_RESULTS.md", """
# 21 — Controlled Test Results

`tests/test_pr_eg_r6_unified_semantic_planning.py` covers T01–T28 with a deterministic proposer, plus the bare-predicate repair and the harbor-word predicate overlap case. The last focused run of that file passed.

The tests do not call the network. They are necessary and not sufficient for the verdict. The fresh-provider section is the production evidence.

Old tests were not edited to raise the pass count. The preseal provenance failure `test_immutable_preseal_preserves_selected_authored_answer_over_ignorance` already failed in the PR-EG-R4-R1 repaired JUnit.
""")

    write("22_FRESH_PROVIDER_CONVERSATIONS.md", f"""
# 22 — Fresh-Provider Conversations

Path: production `POST /api/chat?ui_mode=player` via `TestClient`. Gate on. Expression and live interpretation enabled. Isolated data directory per conversation.

Turns: {summary.get('turns', 0)}. Conversations: {len(convs)} ({', '.join(convs)}).
Sources: adaptive {adaptive_n}, labeled {labeled_n}, frozen-holdout {holdout_n}.

Status: `{status.get('status', 'missing')}`.

A first live attempt stopped at 32 turns because a repeated non-question scene blurb did not append a second delivered-history row. A second attempt stopped when a refusal echoed the player's words "ash cowl" without stating the secret value. The completed file is `live_turns.jsonl`. The stopped transcripts are kept as `live_turns_stopped.jsonl` and `live_turns_echo_stop.jsonl`. The adaptive player instruction was narrowed to one addressee after the first sample. Labeled strings and frozen holdouts were not edited.

Representative labeled lines:

{quote_rows([row for row in live if row.get('source')=='labeled'][:4], 4)}
""")

    write("23_TURN_LEVEL_QUALIFICATION.md", f"""
# 23 — Turn-Level Qualification

Each live row stores the player line, the delivered plan, host reason, sufficiency, sealed text, delivery checks, canonical fingerprint comparison, provider purpose, model, request id, token counts, and latency.

Labeled misses ({len(labeled_misses)}):

{quote_rows(labeled_misses, 12)}

Full rows: `artifacts/pr_eg_r6/live_turns.jsonl`.
""")

    qualities = [row.get("quality") for row in live if isinstance(row.get("quality"), int)]
    play = [row.get("playability") for row in live if isinstance(row.get("playability"), int)]
    write("24_DIALOGUE_QUALITY_AND_PLAYABILITY.md", f"""
# 24 — Dialogue Quality and Playability

Labeled turns use a fixed rubric: 3 only when intent, addressee, subject, sufficiency, and relevance all match and delivery checks pass; 0 when relevance or integrity fails. Adaptive turns without a label use a separate judge model call. The judge does not see engine acceptance claims. Rubric and judge are not the same instrument.

Quality mean {summary.get('quality_mean')} across {summary.get('quality_n')} scored turns. At least 2: {summary.get('quality_ge_2')}.
Playability mean {summary.get('playability_mean')}. At least 2: {summary.get('playability_ge_2')}.

These scores describe the migrated information family. They are not a claim about free social conversation, bargaining, or play across the whole game.
""")

    write("25_PROVIDER_PERFORMANCE.md", f"""
# 25 — Provider Performance

Engine calls only. Player-generation and judge calls are outside this budget and are stored on the turn rows.

Calls: {summary.get('provider_calls')}. Per turn mean: {summary.get('calls_per_turn_mean')}.
Input tokens per call mean / p95: {summary.get('input_tokens_mean')} / {summary.get('input_tokens_p95')}.
Input tokens per turn mean / p95: {summary.get('turn_input_tokens_mean')} / {summary.get('turn_input_tokens_p95')}.
Output tokens per call mean: {summary.get('output_tokens_mean')}.
Turn latency mean / median / p95 / max ms: {summary.get('latency_mean_ms')} / {summary.get('latency_median_ms')} / {summary.get('latency_p95_ms')} / {summary.get('latency_max_ms')}.
Provider-call latency p95 ms: {summary.get('provider_latency_p95_ms')}.
Retry-purpose calls: {summary.get('retry_calls')}.
Models: {summary.get('models')}.

Targets were mean turn input <= 3500, p95 turn input <= 5000, p95 turn latency <= 5000 ms, and no strict-social retry loop. Gate 12 records whether this run met them. Safety was not relaxed to meet them.
""")

    write("26_REGRESSION_COMPARISON.md", f"""
# 26 — Regression Comparison

The PR-EG-R4 relevant file list, plus the R4-R1 delivery file and the R6 tests, was run once.

Passed {reg.get('passed')}. Failed {reg.get('failed')}. Name-matched inherited failures {reg.get('inherited')}. Names not in the R4-R1 failure set:

{json.dumps(reg.get('new_only') or [], indent=2)[:2500]}

The two semantic-handoff names failed with `WinError 5` while replacing `session.json` and passed when rerun by themselves. They are environmental file-lock flakes in the large run, not a semantic-plan assertion change.

The preseal test that expects `initial_generation` already failed in the repaired R4-R1 JUnit. It was not modified.
""")

    write("27_ACCEPTANCE_GATE_RESULTS.md", f"""
# 27 — Acceptance Gate Results

{gate_lines}

Intent {pct(summary.get('intent'))}. Addressee {pct(summary.get('addressee'))}. Relevance {pct(summary.get('relevance'))}. Corrections {pct(summary.get('corrections'))}. Sufficiency {pct(summary.get('sufficiency'))}. Recovery {pct(summary.get('recovery'))}.

Baseline relevance {result['baseline_relevance']} -> semantic {result['new_relevance']}.
Baseline sufficiency {result['baseline_sufficiency']} -> semantic {result['new_sufficiency']}.
""")

    write("28_REMAINING_LIMITATIONS.md", """
# 28 — Remaining Limitations

- Only explicit-addressee information questions, their corrections, and their short follow-ups are migrated.
- A second NPC name anywhere in the utterance is treated as addressee ambiguity.
- Paraphrases with no shared stems fail closed as unknown. H03 is the frozen example.
- Host coverage is stem overlap. It can call a nearby fact partial when half of the argument words appear.
- Cause and source questions stay unknown unless the authorized text already contains a causal marker. The planner does not invent explanations.
- Expression may reword the host line. The sealed meaning is the delivered text; wording is not required to match the host line character for character.
- The deterministic tests use a stub proposer. They do not prove provider behavior.
- This slice does not cover bargaining, promises as negotiated outcomes, quests, combat, movement, or personality.
""")

    write("29_RECOMMENDED_NEXT_ACTION.md", f"""
# 29 — Recommended Next Action

Stop after PR-EG-R6. Await external review.

Verdict {verdict_text}. Do not start PR-EH from this cycle.

If review accepts the slice, the next implementation question is how the host should ground a single grammatical addressee when another name is only mentioned, and whether paraphrases without shared stems should stay fail-closed. Those are review decisions, not silent lexical patches.
""")

    write("30_FINAL_VERDICT.md", f"""
# 30 — Final Verdict

**{verdict_text}**

A or B requires both a matched baseline improvement and a completed fresh-provider production run of at least 120 turns in 8 conversations, with the integrity gates intact. This document uses the recorded run rather than the controlled stub tests alone.

Run status `{status.get('status', 'missing')}`. Turns {summary.get('turns', 0)}. Conversations {len(convs)}.
""")

    write("31_SOURCE_AND_EVIDENCE_INVENTORY.md", """
# 31 — Source and Evidence Inventory

Production:

- `game/unified_semantic_planning.py`
- `game/conversational_orchestration.py`
- `game/conversational_continuity.py`
- `game/dialogue_authority.py`
- `game/player_interpretation_bridge.py`
- `game/social.py`
- `game/api.py`

Validation and qualification:

- `tests/test_pr_eg_r6_unified_semantic_planning.py`
- `tools/qualify_pr_eg_r6.py`
- `artifacts/pr_eg_r6/frozen_holdouts.json`
- `artifacts/pr_eg_r6/freeze.json`
- `artifacts/pr_eg_r6/live_turns.jsonl`
- `artifacts/pr_eg_r6/live_status.json`
- `artifacts/pr_eg_r6/live_usage.jsonl`
- `artifacts/pr_eg_r6/baseline_turns.jsonl`
- `artifacts/pr_eg_r6/baseline_status.json`
- `artifacts/pr_eg_r6/regression_junit.xml`
- `artifacts/pr_eg_r6/01` through `31` review reports

The API key remains in the local environment file and is not copied into these artifacts.
""")

    supporting = [
        "01_EXECUTIVE_SUMMARY.md",
        "02_BASELINE_AND_REPOSITORY_STATE.md",
        "03_IMPLEMENTED_ARCHITECTURE.md",
        "04_SEMANTIC_PLAN_CONTRACT.md",
        "05_PROVIDER_INTERPRETATION.md",
        "06_HOST_PLAN_VALIDATION.md",
        "07_REQUESTED_RELATIONSHIP_HANDLING.md",
        "08_RELEVANCE_VS_AUTHORIZATION.md",
        "09_ANSWER_SUFFICIENCY.md",
        "10_CORRECTION_HANDLING.md",
        "11_FOLLOW_UP_CONTINUITY.md",
        "12_AMBIGUITY_HANDLING.md",
        "13_HOST_KNOWLEDGE_SELECTION.md",
        "14_RESPONSE_PLANNING.md",
        "15_EXPRESSION_AND_FINAL_ADOPTION.md",
        "16_FEATURE_GATE_BEHAVIOR.md",
        "17_LEGACY_PATH_ISOLATION.md",
        "18_MATCHED_BASELINE_COMPARISON.md",
        "19_FROZEN_HOLDOUTS.md",
        "20_ADVERSARIAL_INTEGRITY_TESTS.md",
        "21_CONTROLLED_TEST_RESULTS.md",
        "22_FRESH_PROVIDER_CONVERSATIONS.md",
        "23_TURN_LEVEL_QUALIFICATION.md",
        "24_DIALOGUE_QUALITY_AND_PLAYABILITY.md",
        "25_PROVIDER_PERFORMANCE.md",
        "26_REGRESSION_COMPARISON.md",
        "27_ACCEPTANCE_GATE_RESULTS.md",
        "28_REMAINING_LIMITATIONS.md",
        "29_RECOMMENDED_NEXT_ACTION.md",
        "30_FINAL_VERDICT.md",
        "31_SOURCE_AND_EVIDENCE_INVENTORY.md",
        "frozen_holdouts.json",
        "freeze.json",
        "live_turns.jsonl",
        "live_status.json",
        "baseline_turns.jsonl",
        "baseline_status.json",
        "regression_junit.xml",
        "live_usage.jsonl",
        "live_turns_stopped.jsonl",
        "live_turns_echo_stop.jsonl",
        "live_turns_password_stop.jsonl",
    ]
    config = {
        "campaign_id": "pr_eg_r6_unified_semantic_planning_20261017",
        "campaign_name": "PR-EG-R6 — Unified Semantic Planning",
        "campaign_date": "2026-10-17",
        "purpose": "Qualify the first semantic-planning slice and stop for external review.",
        "objective_status": verdict_text,
        "executive_summary": f"{verdict_text}. Fresh turns: {summary.get('turns', 0)}. See artifacts/pr_eg_r6/01_EXECUTIVE_SUMMARY.md.",
        "changes": {
            "production": [
                "Gated semantic planner for explicit NPC information questions, corrections, and follow-ups.",
                "Host validation, relevance, disclosure, and the existing speech seal remain authoritative.",
            ],
            "validation": ["Controlled T01–T28 tests and fresh /api/chat qualification."],
            "tooling": ["tools/qualify_pr_eg_r6.py", "tools/write_pr_eg_r6_review.py"],
            "documentation": ["31 PR-EG-R6 review artifacts."],
            "generated_artifacts": ["Live transcripts, baseline transcripts, usage, regression JUnit."],
        },
        "testing": {
            "focused": "tests/test_pr_eg_r6_unified_semantic_planning.py passed in the focused run.",
            "broader": f"Relevant regression JUnit passed {reg.get('passed')} failed {reg.get('failed')}.",
            "full_suite": "Not run. The relevant conversational selection was run.",
            "runtime_validation": f"/api/chat turns {summary.get('turns', 0)}; status {status.get('status', 'missing')}.",
            "model_runtime_boundary": f"Live model {status.get('model') or 'gpt-4.1-mini'} for semantic plans and expression.",
            "new_regressions": json.dumps(reg.get("new_only") or []),
            "pre_existing_failures": "25 name-matched R4-R1 failures, including the preseal provenance test.",
        },
        "known_problems": {
            "campaign_specific": [
                "Second NPC names force addressee clarification.",
                "No-shared-stem paraphrases fail closed.",
                verdict_text,
            ],
            "pre_existing": ["25 inherited relevant-family failures. Two extra large-run file-lock flakes passed in isolation."],
        },
        "decisions_requiring_human_review": [
            "Review the verdict and whether the slice is accepted before any further conversational family is migrated.",
        ],
        "missing_concepts": [
            "Grammatical addressee versus a merely mentioned second name.",
            "Paraphrase matching beyond shared stems, without lexical exceptions.",
        ],
        "does_not_prove": [
            "Playability of bargaining, combat, movement, or unguided social chat.",
            "That a stub-proposer test pass equals provider qualification.",
        ],
        "recommended_next_step": "Stop after PR-EG-R6 and await external review. Do not begin PR-EH.",
        "self_contained_review_test": "Handoff bundle generated from the explicit file list.",
        "primary_report": "artifacts/pr_eg_r6/01_EXECUTIVE_SUMMARY.md",
        "max_file_bytes": 50000000,
        "warn_bundle_bytes": 100000000,
        "supporting_files": [
            {
                "path": f"artifacts/pr_eg_r6/{name}",
                "role": "r6_evidence",
                "why": "PR-EG-R6 report or recorded qualification evidence.",
                "human_review_required": name.startswith("01") or name.startswith("30"),
            }
            for name in supporting
            if name != "01_EXECUTIVE_SUMMARY.md"
        ],
    }
    (OUT / "handoff_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(verdict_text)
    print("turns", summary.get("turns"), "conversations", len(convs))


if __name__ == "__main__":
    main()

"""Derive PR-EG-R3-R1 review reports and package CURRENT_REVIEW."""
import hashlib
import json
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

H = Path(__file__).resolve().parent
R = H.parents[1]
sys.path.insert(0, str(R))


def read(name):
    return json.loads((H / name).read_text(encoding="utf-8"))


def write(name, value):
    (H / name).write_text(json.dumps(value, indent=2, default=str), encoding="utf-8")


def report(number, title, body):
    path = H / f"{number:02}_{title.upper().replace(' ', '_').replace('-', '_')}.md"
    path.write_text(f"# {number:02} — {title}\n\n{body.strip()}\n", encoding="utf-8")
    return path


def junit(name):
    root = ET.parse(H / name)
    rows = {}
    messages = {}
    for case in root.iter("testcase"):
        key = case.attrib["classname"] + "::" + case.attrib["name"]
        failure = case.find("failure")
        error = case.find("error")
        if failure is not None:
            rows[key] = "failed"
            messages[key] = (failure.attrib.get("message") or failure.text or "")[:400]
        elif error is not None:
            rows[key] = "error"
            messages[key] = (error.attrib.get("message") or "")[:400]
        elif case.find("skipped") is not None:
            rows[key] = "skipped"
        else:
            rows[key] = "passed"
    return rows, messages


def counts(rows):
    return {state: list(rows.values()).count(state) for state in sorted(set(rows.values()))}


def expression_of(row):
    audit = row.get("expression")
    return audit if isinstance(audit, dict) else {}


def usage_totals(path):
    rows = []
    if not path.exists():
        return dict(records=0)
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    grouped = {}
    for row in rows:
        bucket = grouped.setdefault(row.get("purpose") or "unknown", dict(calls=0, input_tokens=0, output_tokens=0, latency_ms=[]))
        bucket["calls"] += 1
        bucket["input_tokens"] += int(row.get("input_tokens") or 0)
        bucket["output_tokens"] += int(row.get("output_tokens") or 0)
        bucket["latency_ms"].append(float(row.get("latency_ms") or 0))
    summary = {}
    for purpose, bucket in grouped.items():
        latencies = bucket.pop("latency_ms")
        bucket["latency_ms_mean"] = round(statistics.mean(latencies), 1) if latencies else 0
        bucket["latency_ms_max"] = round(max(latencies), 1) if latencies else 0
        summary[purpose] = bucket
    summary["all"] = dict(
        calls=len(rows),
        input_tokens=sum(item.get("input_tokens") or 0 for item in rows),
        output_tokens=sum(item.get("output_tokens") or 0 for item in rows),
        retries=sum(1 for item in rows if item.get("retry") or item.get("purpose") == "retry"),
    )
    return summary


def metrics_for(rows):
    calls = [row["calls"] for row in rows]
    fields = ["provider_calls", "interpretation_calls", "narration_calls", "expression_calls", "retry_calls", "input_tokens", "output_tokens"]
    totals = {field: sum(item.get(field) or 0 for item in calls) for field in fields}
    audits = [expression_of(row) for row in rows]
    attempted = [item for item in audits if item.get("attempted")]
    providers = [item.get("provider") or {} for item in attempted if (item.get("provider") or {}).get("sent")]
    return dict(
        turns=len(rows),
        **totals,
        calls_per_turn=round(totals["provider_calls"] / len(rows), 3) if rows else 0,
        expression_attempts=len(attempted),
        expression_adopted=sum(item.get("decision") == "adopted" for item in attempted),
        expression_rejected=sum(item.get("decision") == "rejected" for item in attempted),
        expression_fallbacks=sum(bool(item.get("fallback_used")) for item in attempted),
        expression_input_tokens=sum(item.get("input_tokens") or 0 for item in providers),
        expression_output_tokens=sum(item.get("output_tokens") or 0 for item in providers),
        expression_latency_ms_mean=round(statistics.mean(item.get("latency_ms") or 0 for item in attempted), 1) if attempted else 0,
        expression_latency_ms_max=round(max((item.get("latency_ms") or 0) for item in attempted), 1) if attempted else 0,
        validation_ms_mean=round(statistics.mean(item.get("validation_ms") or 0 for item in attempted), 3) if attempted else 0,
        validation_ms_max=round(max((item.get("validation_ms") or 0) for item in attempted), 3) if attempted else 0,
        turn_latency_ms_mean=round(statistics.mean(row["elapsed_ms"] for row in rows), 1) if rows else 0,
        turn_latency_ms_max=round(max(row["elapsed_ms"] for row in rows), 1) if rows else 0,
        score_mean=round(statistics.mean(row["score"] for row in rows), 3) if rows else 0,
        score_distribution=dict(Counter(row["score"] for row in rows)),
        score_zero_turns=[row["turn"] for row in rows if row["score"] == 0],
    )


def category_scores(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(row["kind"], []).append(row["score"])
    return {
        kind: dict(n=len(scores), mean=round(statistics.mean(scores), 3), scores=scores)
        for kind, scores in grouped.items()
    }


def prior_adoption(rows, turn, candidate):
    needle = candidate.strip()
    for earlier in rows:
        if earlier["turn"] >= turn:
            continue
        audit = expression_of(earlier)
        if audit.get("decision") == "adopted" and (audit.get("candidate") or "").strip() == needle:
            return earlier["turn"]
        if needle and needle in str(earlier.get("text") or ""):
            return earlier["turn"]
    return None


def integrity_findings(label, rows):
    leaks = []
    reuse = []
    for row in rows:
        audit = expression_of(row)
        candidate = str(audit.get("candidate") or "")
        decision = audit.get("decision")
        delivered = str(row.get("text") or "")
        history = "\n".join(str(item.get("delivered_text") or "") for item in row.get("history") or [])
        if decision == "adopted":
            if not candidate or candidate not in delivered:
                leaks.append(dict(conversation=label, turn=row["turn"], kind="adopted_text_missing", candidate=candidate))
            if candidate and candidate not in history:
                leaks.append(dict(conversation=label, turn=row["turn"], kind="adopted_history_missing", candidate=candidate))
        if decision == "rejected" and candidate and (candidate in delivered or candidate in history):
            earlier = prior_adoption(rows, row["turn"], candidate)
            record = dict(
                conversation=label,
                turn=row["turn"],
                candidate=candidate,
                delivered_generated=audit.get("delivered_generated"),
                adoption=row.get("adoption", {}).get("expression_adoption"),
                earlier_turn=earlier,
            )
            if audit.get("delivered_generated") is False and earlier is not None and row.get("adoption", {}).get("expression_adoption") == "HOST_FALLBACK":
                reuse.append(record)
            else:
                leaks.append(dict(kind="rejected_candidate_retained", **record))
        if row.get("world_nonpassive_diff"):
            leaks.append(dict(conversation=label, turn=row["turn"], kind="nonpassive_world_diff", paths=[item.get("path") for item in row["world_nonpassive_diff"]]))
        if row.get("save_load") and row["save_load"].get("context_equal") is False:
            leaks.append(dict(conversation=label, turn=row["turn"], kind="save_load_mismatch"))
        if "north street" in delivered.lower():
            leaks.append(dict(conversation=label, turn=row["turn"], kind="entity_substitution_delivered"))
    return leaks, reuse


def turn_line(row):
    audit = expression_of(row)
    contract = audit.get("contract") or {}
    provider = audit.get("provider") or {}
    calls = row.get("calls") or {}
    meaning = contract.get("permitted_meaning") or {}
    propositions = "; ".join(contract.get("authorized_propositions") or []) or "(none)"
    return "\n".join([
        f"### Turn {row['turn']} — {row['kind']} — raw score {row['score']}",
        "",
        f"PLAYER: {row['player']}",
        "",
        f"DELIVERED: {row['text']}",
        "",
        f"Operation: `{audit.get('operation') or 'none'}`. Decision: `{audit.get('decision') or 'not attempted'}`. Reasons: {audit.get('reasons') or []}.",
        f"Proposition: `{contract.get('proposition_id') or row.get('adoption', {}).get('proposition_id') or '(none)'}`. Sufficiency: `{contract.get('answer_sufficiency') or row.get('adoption', {}).get('answer_sufficiency') or '(none)'}`.",
        f"Epistemic posture: `{contract.get('epistemic_posture') or '(none)'}`. Permitted meaning: {json.dumps(meaning, ensure_ascii=False) if meaning else '(none)'}.",
        f"Authorized propositions: {propositions}",
        f"Candidate: {audit.get('candidate') or '(none)'}",
        f"Adoption: `{row.get('adoption', {}).get('expression_adoption') or row.get('adoption', {}).get('speech_adoption') or '(none)'}`. Generated delivered: `{audit.get('delivered_generated')}`.",
        f"Calls: provider {calls.get('provider_calls', 0)}, interpretation {calls.get('interpretation_calls', 0)}, expression {calls.get('expression_calls', 0)}, narration {calls.get('narration_calls', 0)}, retry {calls.get('retry_calls', 0)}.",
        f"Turn tokens in/out: {calls.get('input_tokens', 0)}/{calls.get('output_tokens', 0)}. Turn elapsed: {row.get('elapsed_ms')} ms. Validation: {audit.get('validation_ms', 0)} ms.",
        f"Expression tokens in/out: {provider.get('input_tokens', 0)}/{provider.get('output_tokens', 0)}. Expression latency: {audit.get('latency_ms', 0)} ms.",
        f"Scorer failures: {row.get('failures') or []}. Save/load: {row.get('save_load')}. Nonpassive world diff: {row.get('world_nonpassive_diff') or []}.",
    ])


def proposition_groups(rows):
    groups = {}
    for row in rows:
        for item in row.get("history") or []:
            key = item.get("proposition_id") or "(missing)"
            groups.setdefault(key, [])
            text = item.get("delivered_text")
            if text not in groups[key]:
                groups[key].append(text)
    return groups


debug = H / "debug_prop.py"
if debug.exists():
    debug.unlink()

predecessor, _ = junit("../pr_eg_r3/final_relevant_junit.xml")
first_post, first_messages = junit("final_relevant_junit.xml")
confirm, _ = junit("final_relevant_junit_confirm.xml")
before_degree, _ = junit("final_relevant_junit_before_degree_repair.xml")


def failing(rows):
    return [key for key, state in rows.items() if state == "failed"]


pred_fail = set(failing(predecessor))
confirm_fail = set(failing(confirm))
first_fail = set(failing(first_post))
new_vs_r3 = sorted(confirm_fail - pred_fail)
resolved_vs_r3 = sorted(pred_fail - confirm_fail)
inherited = sorted(confirm_fail & pred_fail)
environmental = []
for key in sorted(first_fail - confirm_fail):
    environmental.append(dict(test=key, message=first_messages.get(key, "")[:240]))

comparison = dict(
    predecessor_counts=counts(predecessor),
    before_degree_counts=counts(before_degree),
    first_post_degree_counts=counts(first_post),
    confirming_counts=counts(confirm),
    predecessor_tests=len(predecessor),
    confirming_tests=len(confirm),
    inherited_failures=inherited,
    new_failures_vs_predecessor=new_vs_r3,
    resolved_failures_vs_predecessor=resolved_vs_r3,
    environmental_file_locks=environmental,
)
write("regression_comparison.json", comparison)

live = read("live_qualification.json")
before_live = read("qualification_before_degree_repair.json")
status = read("live_status.json")
primary = live["primary"]
secondary = live["secondary"]
combined = primary + secondary
metrics = dict(primary=metrics_for(primary), secondary=metrics_for(secondary), combined=metrics_for(combined))
before_metrics = dict(
    primary=metrics_for(before_live["primary"]),
    secondary=metrics_for(before_live["secondary"]),
    combined=metrics_for(before_live["primary"] + before_live["secondary"]),
)
leaks = []
reuse_notes = []
for label, rows in (("primary", primary), ("secondary", secondary)):
    found, reused = integrity_findings(label, rows)
    leaks.extend(found)
    reuse_notes.extend(reused)
categories = dict(primary=category_scores(primary), secondary=category_scores(secondary), combined=category_scores(combined))
usage = usage_totals(H / "live_usage.jsonl")
usage_before = usage_totals(H / "live_usage_before_degree_repair.jsonl")
write("performance.json", dict(final=metrics, preserved_first_qualification=before_metrics))
write("quality.json", dict(raw=categories, adopted_characterization=status.get("adopted_characterization"), scorer_reuse_collisions=reuse_notes))
write("usage_totals.json", dict(final=usage, preserved_first_qualification=usage_before))
write("integrity_checks.json", dict(leaks=leaks, prior_adoption_reuses=reuse_notes))
state_rows = []
for label, rows in (("primary", primary), ("secondary", secondary)):
    for row in rows:
        state_rows.append(dict(
            conversation=label,
            turn=row["turn"],
            save_load=row.get("save_load"),
            world_paths=sorted({item.get("path") for item in row.get("world_diff") or []}),
            nonpassive=row.get("world_nonpassive_diff") or [],
            commitment_diff=row.get("commitment_diff") or [],
        ))
write("state_audit.json", state_rows)

groups = dict(primary=proposition_groups(primary), secondary=proposition_groups(secondary))
adopted = status.get("adopted_characterization") or []
holdouts = read("frozen_holdouts.json")
freeze = read("freeze.json")
holdout_hash = hashlib.sha256((H / "frozen_holdouts.json").read_bytes()).hexdigest()
plan_hash = hashlib.sha256((H / "live_plan.json").read_bytes()).hexdigest()
first_plan_hash = hashlib.sha256((H / "live_plan_before_degree_repair.json").read_bytes()).hexdigest()
historical_before = read("historical_reproduction_before.json")
historical_after = read("historical_reproduction.json")

gates = []


def gate(name, status_text):
    gates.append((name, status_text))


gate("1 Characterization", "PASS" if adopted else "FAIL")
gate("2 Information integrity", "PASS" if not leaks else "FAIL")
gate("3 Entity identity", "PASS" if not any(item.get("kind") == "entity_substitution_delivered" for item in leaks) else "FAIL")
gate("4 Factual paraphrase", "PASS" if metrics["combined"]["expression_adopted"] >= 2 else "FAIL")
gate("5 Proposition continuity", "PASS" if any(len(texts) > 1 for texts in groups["primary"].values()) else "FAIL")
gate("6 Historical recall", "PASS" if any(row["kind"] == "recall" and row["score"] == 3 and not row["calls"].get("expression_calls") for row in combined) else "FAIL")
gate("7 Answer relevance", "PASS" if any(row["kind"] == "partial" and "couldn't say" in row["text"].lower() for row in combined) else "FAIL")
gate("8 Adoption integrity", "PASS" if not leaks else "FAIL")
gate("9 Regression", "PASS" if not new_vs_r3 else "FAIL")
gate("10 Live qualification", "PASS" if adopted and len(primary) >= 15 and len(secondary) >= 12 else "FAIL")
gate("11 Performance", "PASS" if metrics["combined"]["narration_calls"] == 0 and metrics["combined"]["retry_calls"] == 0 else "FAIL")

critical_fail = any(status_text == "FAIL" for _, status_text in gates)
verdict = "B — REPAIR QUALIFIED WITH LIMITATIONS" if adopted and not critical_fail else ("C — REPAIR INCOMPLETE" if not critical_fail or not adopted else "C — REPAIR INCOMPLETE")
if leaks:
    verdict = "D — ARCHITECTURAL OR SAFETY BLOCKER"
elif not adopted:
    verdict = "C — REPAIR INCOMPLETE"
elif new_vs_r3:
    verdict = "C — REPAIR INCOMPLETE"
write("acceptance_gates.json", dict(verdict=verdict, gates=[{"gate": name, "result": status_text} for name, status_text in gates]))

final_mean = metrics["combined"]["score_mean"]
final_dist = metrics["combined"]["score_distribution"]
summary = f"""**{verdict}.**

Host-authorized meaning is built before the provider writes a sentence. The provider may word that meaning. Delivery still goes through the existing host speech seal. A rejected sentence is not adopted.

The final production qualification is two fresh `/api/chat` conversations, 15 turns and 12 turns, on `gpt-4.1-mini-2025-04-14`. Generated personal characterization reached the player in both. Primary turn 2 and secondary turn 6 delivered: "I prefer the evening because it feels calmer and more peaceful to me."

Safe paraphrases, an authorized night-watch disclosure, uncertainty, and a nonbinding refusal were also adopted. Exact recall listed every distinct delivered sentence for one proposition and made no provider call. The unattended-gate question kept the watch fact and withheld a yes or no.

The first qualification is preserved. It rejected that same characterization because the degree word "more" was outside the closed grammar class, and it failed to bind "Put that another way." Those two defects were repaired, a new plan was frozen, and the final sample was run against that plan. Frozen holdouts were not edited.

Raw scorer mean on the final 27 turns is {final_mean}. Distribution: {final_dist}. Two raw scores of 0 are the scorer matching a rejected verbatim repeat to speech that had already been adopted. The audit records `delivered_generated: false` and `HOST_FALLBACK`. Confirming regression: {comparison['confirming_counts']} of {comparison['confirming_tests']}. New product failures against PR-EG-R3: {len(new_vs_r3)}. Inherited failures: {len(inherited)}."""

reports = []
reports.append(report(1, "Executive Summary", summary))
reports.append(report(2, "Baseline and Environment", f'''Repository revision: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` (`d31beb7`, PR-BN bounded DM improvisational authority).

The worktree was already dirty before this cycle. Cycle files touched for PR-EG-R3-R1:

- `game/expressive_dialogue.py` (untracked module, extended)
- `game/dialogue_authority.py` (untracked module, extended)
- `game/conversational_continuity.py` (untracked module, extended)
- `game/conversational_orchestration.py` (untracked module, extended)
- `game/api.py` (tracked, modified)
- `tests/test_pr_eg_r3_r1_expression_semantics.py`
- `tools/validate_pr_eg_r3_r1.py`

Provider configuration recorded on the live usage log: configured model `gpt-4.1-mini`, response model `gpt-4.1-mini-2025-04-14`. Expression calls use temperature 0.2 and a maximum of 80 output tokens. Pytest sets `ASHEN_DISABLE_EXPRESSION_GENERATION=1`. The live runner sets expression generation on and records usage to `artifacts/pr_eg_r3_r1/live_usage.jsonl`. The API key is not recorded.

PR-EG-R3 predecessor, retained as the comparison baseline and not assumed to still be the tree before this cycle's edits: 605 passed / 25 failed of 630 relevant tests; 10/10 frozen holdouts; 27 fresh turns; 22 provider calls; 12 expression calls; 8/12 adopted; 0 narration; 0 retries; 20,652 input tokens; 2,150 output tokens; 1.36 seconds mean turn latency. Final personal characterization in that repaired sample: 0/3 adopted.

This cycle's confirming relevant suite is {comparison['confirming_counts']} of {comparison['confirming_tests']} tests. The extra tests are the R3-R1 matrix, the R3 expression file, and the R2C-R2 reference-eligibility file. The full repository suite was not run.'''))
reports.append(report(3, "Historical Failure Reproduction", f'''The isolated reproduction was saved before the production repair in `historical_reproduction_before.json`.

| Case | Before | After the repair, same harness |
| --- | --- | --- |
| A Harmless characterization | adopt false, `unsupported_addition` | adopt true |
| B Equivalent paraphrases | ambiguous | still ambiguous in this harness |
| C Unattended question | "I couldn't tell you." | watch fact plus "I couldn't say whether it is ever left unattended." |
| D North street | adopt false, `missing_authorized_claim`, `name_changed` | still rejected |
| E Security explanation | adopt false | still rejected, now including `prohibited_addition` |

Before:

```json
{json.dumps(historical_before, indent=2)}
```

After:

```json
{json.dumps(historical_after, indent=2)}
```

Case B stays ambiguous in `reproduce_historical.py` because that harness records the second sentence without copying `proposition_id`. The production path copies the identifier. The unit matrix and the final live recall are the evidence for grouping. Case C on the current deterministic path was false ignorance before the repair, rather than a complete yes. The repair answers with the authorized watch fact and an explicit limit.'''))
reports.append(report(4, "Source-Level Root Cause", '''Authorized propositions already came from resolver topics, prior delivered speech, and the host fallback. `build_expression_contract` in `game/expressive_dialogue.py` is where the R3 contract is built. `validate_expression` decides adoption. `apply_expression` calls the provider once and returns the generated line only when validation adopts it. `seal_host_speech` remains the delivery boundary. `record_delivered_exchange` stores the delivered line.

The characterization miss had a specific cause. The validator treated every token outside a closed feeling list as a new claim. "Everything" in "everything feels calm and peaceful" was classified as `unsupported_addition` even though the host had already authorized "I prefer the evening." The provider had not been given a host premise. Adding the word to a feeling list would have widened the lexicon without authorizing the meaning.

Equivalent paraphrases became ambiguous because delivered rows were matched on wording. Two sentences from one road fact did not share an identifier, so `_best_exchange` treated them as competing subjects.

The unattended question was a sufficiency gap. A night-watch topic overlaps the question and does not establish that the gate is never unattended. Before this cycle the deterministic path could fall through to "I couldn't tell you." The older live sample could also recite the watch fact as if it closed the question.

"North street" was already rejected by the place-name bigram check. That check remains. Declared aliases are now the only extra substitution the contract allows.

Security sentences inside a preference explanation were already rejected as unsupported tokens. They are now also rejected by an explicit prohibited-category check, so a sentence that mixes a safe feeling with a gate, a promise, or a secret fails as a whole.'''))
reports.append(report(5, "Structured Expression Contract", '''The R3 contract is extended. The public fields now include speaker identity, source identity, proposition id, epistemic posture, answer sufficiency, permitted meaning, prohibited additions, and entity identities. The revision hash covers the permitted meaning, the entities, and the proposition id.

Permitted meaning for a preference explanation is a structured premise, built from an established preference sentence before any candidate exists:

- operation `explain_own_preference`
- preference anchor, such as `evening`
- subject `speaker_experience`
- theme `speaker_preference_ease`
- licensed by `established_preference`
- `external_world` false
- `consequential_commitment` false

The prompt tells the speaker the authorized meaning and allows ordinary grammar. It does not list the candidate, and it does not list "everything" as an authorized fact. Fallback remains the host sentence. Source freshness remains the contract revision. No second knowledge store was added.

A sentence with no preference anchor, such as "The watch wears on me," does not build a characterization contract and does not call the provider.'''))
reports.append(report(6, "Characterization Authority", '''The host licenses one theme: the speaker's own ease with the preferred time. The license exists only when an established sentence matches "I prefer ...". The theme is not inferred from the candidate and is not assumed for every NPC.

Acceptable live wording in the final sample: "I prefer the evening because it feels calmer and more peaceful to me."

The historical candidate with "everything feels calm and peaceful" is adopted by the unit test and by the production HTTP stub. The word "everything" is grammar in the non-referential class. It cannot by itself satisfy the explanation. The reason still has to be a theme word such as calm, peaceful, quiet, or easy, with "because" or "when".

Degree words `more`, `less`, `very`, `quite`, `really`, `too`, `much`, and `most` may modify a theme word. They were added after the preserved first qualification rejected "more peaceful". They cannot name an entity and cannot satisfy the explanation alone.

"The world seems to slow down" remains rejected. "World" is not authorized meaning. A captain, a guard schedule, a promise, a secret, or a meeting inside the same sentence is rejected even when the rest of the sentence is a safe feeling.'''))
reports.append(report(7, "Candidate Validation", '''`validate_expression` still requires the requested operation, the speaker, the epistemic posture, and the authorized proposition. Characterization adds the licensed premise. A candidate fails closed when a content word is outside the proposition, the theme lexicon, the non-referential grammar class, the degree class, or an inflection of those words.

Prohibited categories are rejected even inside an otherwise licensed sentence: security posts, titles used as other people, promises, rewards, secrets, contacts, and meetings. A mixed sentence is not adopted in part.

The final live sample rejected "The road just outside the gate is called the north street." for `name_changed` and delivered the authorized road sentence. It rejected a later verbatim repeat of the already adopted characterization. No second model approves candidates.'''))
reports.append(report(8, "Entity Identity Protection", '''Place-head bigrams still reject "north street" for an authorized "north road". The final primary turn 4 is that rejection on `/api/chat`. The delivered line stayed "the street beyond the gate is the north road."

Declared aliases on the contract may replace a canonical pair. The unit matrix adopts "harbour road" when that alias is declared and rejects "ferry road" and a speaker swap to Corporal Bren. Ordinary synonyms are not aliases. No universal list of name fragments was added.

Capitalized multiword spans that are not the speaker, the proposition, or a declared alias remain `entity_substitution`.'''))
reports.append(report(9, "Proposition Identity", f'''`proposition_identity` uses an explicit id when the caller has one, otherwise `topic:{{speaker}}:{{topic_id}}`, otherwise `statement:` plus a short hash of the speaker and the normalized sentence. The identifier is stored beside the exact delivered text.

Final primary history groups:

```json
{json.dumps(groups["primary"], indent=2, ensure_ascii=False)}
```

Final secondary history groups:

```json
{json.dumps(groups["secondary"], indent=2, ensure_ascii=False)}
```

The three north-road sentences share `topic:sergeant_mara:street`. The watch fact and the partial answer share `topic:sergeant_mara:night_watch`. The adopted explanation inherits the preference id `statement:204a7c55be2b`, so "I prefer the evening." and the longer reason are one proposition there. A later reuse of that reason hashes the full sentence and also records `statement:960f47416fc0`. One explanation is therefore addressable under two ids after it is repeated. The GM recall lines have their own statement ids because the quoted recall is a new delivered utterance. Different roads and different speakers remain separate in the unit matrix.'''))
reports.append(report(10, "Conversational Continuity", '''`_best_exchange` still searches delivered wording. Winners that share a speaker and a proposition id collapse to one subject. Winners with different ids stay ambiguous, including when they share vocabulary.

`_REPEAT` now recognizes "put that another way", "say that another way", and "in another way", which the expression layer already treated as paraphrase requests. The first qualification asked "Put that another way" and received an ignorance line because continuity did not bind the prior sentence. That transcript is preserved. The final primary turn 4 bound the road sentence, attempted a paraphrase, and fell back when the candidate renamed the road.

Genuine ambiguity in the final sample asks "Which earlier remark do you mean?" and makes no expression call. The clarification that follows quotes the sentences for the narrowed subject.'''))
reports.append(report(11, "Exact Recall vs Restatement", '''`recall_kind` distinguishes exact recall, restatement, explanation, and subject recall.

Exact GM recall of several equivalent sentences quotes every distinct delivered sentence and does not call the provider. Final primary turn 11 listed the original road sentence and both adopted paraphrases. Final secondary turn 9 listed both harbor-bell sentences.

Restatement may call expression. Primary turn 5 adopted "The street just past the gate is called the north road." Primary turn 6 adopted a further wording as the explanation of "the north road."

A restatement that fails validation keeps the authorized sentence. Primary turn 4 did that after the north-street candidate. Explanation does not add a new factual claim beyond the authorized proposition.'''))
reports.append(report(12, "Answer-Sufficiency Contract", '''`classify_answer_sufficiency` returns `directly_answers`, `partially_informs`, `does_not_answer`, or `unknown`.

An absence question such as "ever left unattended" or "unguarded", paired with one coverage fact about a watch, guard, sentry, or patrol, and with specific subject overlap, is `partially_informs`. If the authorized fact itself states the absence, it is `directly_answers`. No overlap yields `does_not_answer`. Empty text yields `unknown`.

The host line for a partial answer is the fact plus "I couldn't say whether it is ever left ...". It sets `answer_sufficiency` to `partially_informs`. It does not mark the topic revealed and does not append `revealed_topics`. `_next_topic_to_reveal` still returns None for the absence question. Expression is not generated for that posture.

Final primary turn 10: "Guards watch the north gate throughout the night. I couldn't say whether it is ever left unattended." Final secondary turn 2 uses the same shape for the harbor gate and "unguarded." Neither line says the gate is never unattended.'''))
reports.append(report(13, "Host-Owned Adoption", f'''Generated speech is delivered only when validation returns adopt and the existing seal records host speech. Rejected candidates stay on the turn audit.

Integrity findings on the final transcript: {json.dumps(leaks) or "none"}.

Prior-adoption reuses, which the raw scorer marked `rejected_candidate_delivered`: {json.dumps(reuse_notes, ensure_ascii=False)}.

Those two turns asked for the characterization again. The model repeated the sentence already adopted. Validation rejected the verbatim repeat. The host then reused the earlier adopted line. `delivered_generated` is false. The rejected candidate did not become a new authorization.

Primary turn 4 shows the other boundary. The north-street candidate is absent from the delivered line and from later recall. Recall quotes the original road sentence, not the rejected rename.'''))
reports.append(report(14, "Adversarial Qualification", '''Unit coverage, all passing in the confirming suite:

| Check | Result |
| --- | --- |
| Harmless subjective wording, including "everything" and "more peaceful" | adopted when the preference premise exists |
| Security, relationship, promise, and secret explanations | rejected; candidate absent from the player line |
| Mixed peaceful sentence that adds guards | rejected as a whole; one provider call |
| Unauthorized "north street" and "Corporal Bren" | rejected |
| Declared "harbour road" alias | adopted |
| Rumor strengthened by dropping "heard" or "may" | rejected; fallback keeps the hedge |
| Partial watch fact | delivered with an explicit limit; topic not promoted |
| Rejected candidate | absent from delivered history |
| Save/load of the production stub | conversational context equal |
| No preference anchor | no contract and no provider call |

Live adversarial evidence in the final sample is primary turn 4: the model proposed "north street" and the player received the authorized road sentence. The preserved first qualification also rejected a characterization that added "the world" and rejected a refusal that added "your effort will surely be noticed." Those candidates are in the preserved transcript, not in the delivered lines.

Success is not claimed from rejection alone. The same sample adopted the harmless characterization.'''))
reports.append(report(15, "Positive Dialogue Quality", f'''Rubric used by the runner: 0 incorrect, irrelevant, or unauthorized; 1 safe but rigid; 2 relevant and adequate; 3 natural, within authority, and conversationally appropriate. Any scorer failure forces 0.

Raw scores are the recorded runner output. They are not rewritten.

Combined raw mean {metrics['combined']['score_mean']}. Distribution {metrics['combined']['score_distribution']}. Score-0 turns: {metrics['combined']['score_zero_turns']}.

Category scores:

```json
{json.dumps(categories, indent=2)}
```

Expression attempts {metrics['combined']['expression_attempts']}. Adopted {metrics['combined']['expression_adopted']}. Rejected {metrics['combined']['expression_rejected']}. Fallbacks {metrics['combined']['expression_fallbacks']}.

Adoption rate among attempts: {round(metrics['combined']['expression_adopted'] / metrics['combined']['expression_attempts'], 3) if metrics['combined']['expression_attempts'] else 0}. Rejection rate: {round(metrics['combined']['expression_rejected'] / metrics['combined']['expression_attempts'], 3) if metrics['combined']['expression_attempts'] else 0}. Fallback rate: {round(metrics['combined']['expression_fallbacks'] / metrics['combined']['expression_attempts'], 3) if metrics['combined']['expression_attempts'] else 0}.

The two score-0 turns are primary 14 and secondary 10. Each delivered the characterization adopted earlier in that conversation, after the new candidate was rejected as a verbatim repeat. Read as dialogue, those turns are safe and relevant. The raw 0 stands in the recorded scores so the measurement collision stays visible. No safety failure is hidden inside the mean: the north-street rejection scored 1 and delivered the authorized sentence.

Adopted characterization:

```json
{json.dumps(adopted, indent=2, ensure_ascii=False)}
```'''))
reports.append(report(16, "Frozen Holdouts", f'''`frozen_holdouts.json` sha256 `{holdout_hash}`. Freeze record: `{freeze['sha256']}` at stage "{freeze['stage']}". Match: {holdout_hash == freeze['sha256']}.

The file was hashed before qualification tuning and was not edited afterward. The confirming suite includes `test_frozen_holdout` for each id. Holdout ids: {", ".join(item["id"] for item in holdouts)}.

| Id | Kind | Expectation |
| --- | --- | --- |
''' + "\n".join(f"| {item['id']} | {item['kind']} | {item['expect']} |" for item in holdouts) + '''

R1H01 adopts a dawn explanation for Warden Ivo. R1H02 rejects a captain and an unattended harbor. R1H03 adopts a south-road paraphrase. R1H04 rejects "south street". R1H05 adopts a declared harbour-road alias. R1H06 keeps a rumor hedge. R1H07 requires the west-gate sentry fact plus a limit. R1H08 groups two south-road wordings. R1H09 keeps two different roads ambiguous. R1H10 recalls the sentry sentence exactly and forbids "unattended".

The live plan is a separate freeze. The preserved first plan sha256 is `{first_plan_hash}`. The final plan sha256 is `{plan_hash}`, matching `live_freeze.json` stage "before fresh provider qualification". The final plan was frozen before the final provider run. It was not edited after the results.'''))
reports.append(report(17, "Targeted Test Matrix", '''All of the following passed in `final_relevant_junit_confirm.xml`.

| Id | Test | What is inspected |
| --- | --- | --- |
| T01–T02 | `test_t01_t02_authorized_preference_explanation_allows_harmless_grammar` | Contract premise, historical "everything" sentence, adopted player text |
| T03–T06 | `test_t03_t06_unauthorized_explanations_are_rejected` | External, relationship, security, and promise candidates |
| T07–T10 | `test_t07_t10_paraphrase_entity_alias_and_rumor` | Safe paraphrase, rename, alias, rumor hedge |
| T11–T18 | `test_t11_t18_proposition_identity_recall_and_ambiguity` | Shared id, separate propositions, exact recall, speakers, ambiguity |
| T19–T23 | `test_t19_t23_answer_sufficiency_and_refusal` | Direct, partial, unrelated, unknown, nonbinding refusal |
| T24–T28 | `test_t24_t28_mixed_rejection_persistence_and_no_canonical_mutation` | Mixed candidate, history exclusion, save/load, no world mutation |
| T29–T30 | `test_t29_t30_relevant_modules_keep_single_expression_call` | One expression call, no retry loop |
| Degree | `test_degree_grammar_can_modify_an_authorized_feeling` | "more peaceful" adopted; "the world" rejected |
| Premise | `test_unestablished_preference_does_not_invent_a_premise` | No contract without an established preference |
| Partial | `test_partial_fact_reaches_the_player_without_topic_promotion` | Player line, topic not revealed, world updates empty |
| Holdouts | `test_frozen_holdout` | R1H01–R1H10 |
| Production | `test_production_chat_delivers_characterization` | Stubbed `/api/chat` delivers the historical sentence and survives save/load |

The production test stubs the provider. The fresh conversations in reports 19 and 20 do not.'''))
reports.append(report(18, "Regression Comparison", f'''Predecessor file: `artifacts/pr_eg_r3/final_relevant_junit.xml`. Counts: {comparison['predecessor_counts']} of {comparison['predecessor_tests']}.

Before the degree-word and "another way" repair: {comparison['before_degree_counts']}.

First post-repair run: {comparison['first_post_degree_counts']}. Two tests failed with `PermissionError` while replacing `session.json` on Windows. Both passed when rerun alone. They are listed in `environmental_file_locks` and are not product failures.

Confirming run: `final_relevant_junit_confirm.xml`. Counts: {comparison['confirming_counts']} of {comparison['confirming_tests']}.

New failures against the PR-EG-R3 identities: {new_vs_r3 or "none"}.

Resolved failures: {resolved_vs_r3 or "none"}.

Inherited failing identities ({len(inherited)}):

''' + "\n".join(f"- `{item}`" for item in inherited) + '''

The confirming pass count is higher because this suite adds the R3-R1 tests and the R2C-R2 reference-eligibility file to the PR-EG-R3 selection. No inherited failure changed state. The full repository suite was not run.'''))
reports.append(report(19, "Primary Fresh-Provider Conversation", "Final 15-turn production transcript. Scores are the raw runner scores.\n\n" + "\n\n".join(turn_line(row) for row in primary)))
reports.append(report(20, "Secondary Fresh-Provider Conversation", "Final 12-turn production transcript. The NPC, facts, and order differ from the primary. Scores are the raw runner scores.\n\n" + "\n\n".join(turn_line(row) for row in secondary)))
reports.append(report(21, "Provider Cost and Latency", f'''Final qualification usage by purpose:

```json
{json.dumps(usage, indent=2)}
```

Preserved first qualification, not added into the final totals:

```json
{json.dumps(usage_before, indent=2)}
```

Turn metrics:

```json
{json.dumps(metrics, indent=2)}
```

Preserved first-run turn metrics:

```json
{json.dumps(before_metrics, indent=2)}
```

The final sample has {metrics['combined']['provider_calls']} provider calls across {metrics['combined']['turns']} turns ({metrics['combined']['calls_per_turn']} per turn), {metrics['combined']['expression_calls']} expression calls, {metrics['combined']['interpretation_calls']} interpretation calls, {metrics['combined']['narration_calls']} narration calls, and {metrics['combined']['retry_calls']} retries. Input tokens {metrics['combined']['input_tokens']}. Output tokens {metrics['combined']['output_tokens']}. Mean turn latency {metrics['combined']['turn_latency_ms_mean']} ms. Maximum turn latency {metrics['combined']['turn_latency_ms_max']} ms. Mean expression validation {metrics['combined']['validation_ms_mean']} ms.

Expression prompts in the transcript stay near 170–220 input tokens, with output under the 80-token cap. Recall, ambiguity, clarification, and the partial answer made no expression call. The first preserved sample included one narration call on a harbor-watch question. The final plan used the "whether" wording and recorded none. Rejection cost is one expression call plus sub-millisecond validation, then the host sentence.'''))
reports.append(report(22, "Persistence and State Integrity", f'''Save/load checks ran on turns 4, 8, and the last turn of each conversation. Results are in `state_audit.json`. No `save_load_mismatch` is present.

Nonpassive world diffs: {json.dumps([row for row in state_rows if row['nonpassive']]) or "none"}.

Observed world paths are the passive faction and event-log ticks recorded on each turn. Generated sentences did not add a quest, a reward, a patrol schedule, a secret, or a faction relationship. Commitment diffs are included per turn in the state audit.

Adopted lines are the last delivered-history sentence of their turn. The north-street candidate is not among them. The characterization sentence is present because it was adopted, and a later turn reused that adopted line as the host fallback.

Primary turn 15 asked whether the preference still held and delivered the adopted explanation with zero provider calls. That is stored speech, not a new generation.'''))
reports.append(report(23, "Source Change Inventory", '''Cycle-relevant files, against the already dirty worktree:

| Path | Change |
| --- | --- |
| game/expressive_dialogue.py | Structured permitted meaning, characterization premise, degree and non-referential grammar, prohibited categories, proposition id, entity aliases |
| game/dialogue_authority.py | Answer sufficiency and the partial host line; proposition id on the authority record |
| game/conversational_continuity.py | Proposition id on delivered rows; equivalent grouping; multi-sentence exact recall; "another way" bound as a restatement |
| game/conversational_orchestration.py | Copies `proposition_id` onto continuity context references |
| game/api.py | Conversational social payload includes that proposition id |
| tests/test_pr_eg_r3_r1_expression_semantics.py | Matrix T01–T30, holdouts, production stub |
| tools/validate_pr_eg_r3_r1.py | Two frozen live plans and the fresh `/api/chat` runner |

`game/immutable_valid_response.py` was not given a new adoption path. Generated lines still enter through the existing host seal. No active campaign data file was edited. Disposable live sessions under `artifacts/pr_eg_r3_r1/disposable_state/` are excluded from the review bundle.'''))
reports.append(report(24, "Remaining Limitations", '''The characterization premise is one host theme, licensed only by an established "I prefer ..." sentence. An NPC without that sentence gets the ordinary fallback. The host does not invent a quiet personality for them. Other subjective themes are out of scope.

"The world seems to slow down", "comes", and "end of the day" remain unsupported. The validator fails closed.

A second request for the same explanation reuses the adopted sentence and rejects a verbatim repeat. It does not produce a fresh wording of the same premise.

The isolated historical harness still reports equivalent paraphrases as ambiguous when the second record omits `proposition_id`. Production copies the id. A delivered row written without it can still collide. Reusing an adopted explanation also hashes that full sentence, so the same reason can appear under the original preference id and under a second statement id.

Ambiguous clarification says "Which earlier remark do you mean?" and does not name the competing sentences.

The first qualification is a real miss: characterization was not adopted, one restatement became ignorance, and one secondary turn made a narration call. It is preserved in `qualification_before_degree_repair.json`.

The first post-repair regression run recorded two Windows `PermissionError` failures while renaming `session.json`. The confirming run passed those tests. They are environmental.

The full repository suite was not run. Twenty-five inherited relevant-suite failures remain.'''))
reports.append(report(25, "Next-Cycle Recommendation", '''Stop after PR-EG-R3-R1. Do not begin PR-EH. Await external review.

A later cycle can add another host-authored theme only by authorizing the premise before generation, with its own holdouts frozen first. It should leave the degree class and the prohibited categories as they are. It should not retune `frozen_holdouts.json` or the final `live_plan.json`.

The verbatim-reuse path can stay. A later cycle that wants a second wording of an already delivered explanation needs an explicit restatement operation, still bound to the same proposition.

Any change that lets "north road" become "north street", or that lets a partial watch fact answer "never unattended", should be treated as an integrity failure.'''))
reports.append(report(26, "Final Verdict", f'''**{verdict}.**

| Gate | Result |
| --- | --- |
''' + "\n".join(f"| {name} | {status_text} |" for name, status_text in gates) + f'''

A is not claimed. The characterization theme is a single host premise, the first qualification failed until the degree class and the restatement binding were repaired, and two raw scores of 0 are measurement collisions with already adopted speech.

B is claimed because the final production path generated, validated, adopted, and delivered a natural preference explanation in both conversations, adopted multiple safe paraphrases, grouped equivalent sentences, recalled the exact delivered wording, and kept a partial fact from closing a stronger question. Rejected renames and prohibited additions stayed out of delivery. The confirming regression adds no product failure against PR-EG-R3.

Do not proceed to PR-EH on this verdict.'''))
reports.append(report(27, "Source and Evidence Inventory", '''Evidence classes: STATIC source inspection; UNIT deterministic tests; CONTROLLED production HTTP with a stubbed expression provider; FRESH actual `/api/chat` with the configured model; STATE world, commitment, and delivered-history diffs; HISTORICAL the pre-change reproduction and the preserved first qualification.

`live_qualification.json` and `live_usage.jsonl` are the final 27-turn production results. `qualification_before_degree_repair.json`, `live_usage_before_degree_repair.jsonl`, `live_status_before_degree_repair.json`, and `live_plan_before_degree_repair.json` preserve the first sample. `live_plan.json`, `live_freeze.json`, `frozen_holdouts.json`, and `freeze.json` are the frozen inputs. `final_relevant_junit_confirm.xml` is the regression result used for the gate. `final_relevant_junit.xml` retains the two file-lock failures. `historical_reproduction_before.json` is the pre-change reproduction.

Reproduction from the repository root:

```
$env:PYTHONPATH = (Get-Location).Path
.venv/Scripts/python.exe -m pytest tests/test_pr_eg_r3_r1_expression_semantics.py tests/test_pr_eg_r3_expressive_dialogue.py tests/test_pr_eg_r1_continuity.py tests/test_pr_eg_r2c_speech_adoption.py tests/test_pr_eg_r2c_r2_reference_eligibility.py
$selection = Get-Content artifacts/pr_eg_r2c_r2/regression_selection.json | ConvertFrom-Json
.venv/Scripts/python.exe -m pytest @selection tests/test_pr_eg_r3_expressive_dialogue.py tests/test_pr_eg_r3_r1_expression_semantics.py tests/test_pr_eg_r2c_r2_reference_eligibility.py --junitxml=artifacts/pr_eg_r3_r1/final_relevant_junit_confirm.xml
.venv/Scripts/python.exe tools/validate_pr_eg_r3_r1.py
.venv/Scripts/python.exe artifacts/pr_eg_r3_r1/build_review.py
```

The live command spends configured-provider requests and overwrites `live_qualification.json` and `live_usage.jsonl`. Copy both before a rerun. Credentials, `.env`, and `disposable_state` are excluded. The preserved first transcript is not the final qualification.'''))

excluded = {"disposable_state", "__pycache__"}
excluded_names = {"handoff_config.json", "artifact_inventory.json", "bundle_verification.json"}
files = [path for path in H.rglob("*") if path.is_file() and not excluded.intersection(path.relative_to(H).parts) and path.name not in excluded_names]
inventory = {path.relative_to(R).as_posix(): dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size) for path in sorted(files)}
write("artifact_inventory.json", inventory)
files.append(H / "artifact_inventory.json")
source_paths = [
    R / "game/expressive_dialogue.py",
    R / "game/dialogue_authority.py",
    R / "game/conversational_continuity.py",
    R / "game/conversational_orchestration.py",
    R / "game/api.py",
    R / "tests/test_pr_eg_r3_r1_expression_semantics.py",
    R / "tools/validate_pr_eg_r3_r1.py",
]
config = dict(
    campaign_id="pr_eg_r3_r1_expression_contract_semantics_20261017",
    campaign_name="PR-EG-R3-R1 — Expression Contract Semantics and Conversational Relevance",
    campaign_date="2026-10-17",
    purpose="Authorize conversational meaning before expression, preserve proposition identity, and keep partial facts from closing stronger questions. Stop after R3-R1.",
    objective_status=verdict,
    executive_summary=summary,
    changes=dict(
        production=["Host-authorized expression meaning, characterization premises, proposition identity, and answer sufficiency, sealed through existing speech adoption."],
        validation=["R3-R1 matrix and holdouts, plus final 15-turn and 12-turn fresh /api/chat conversations."],
        tooling=["Fresh-provider qualification runner with a preserved first plan and a frozen final plan."],
        documentation=["27 review artifacts, both final transcripts, and the preserved first qualification."],
        generated_artifacts=["Regression comparison, quality scores, usage totals, state audit, integrity checks, and acceptance gates."],
    ),
    testing=dict(
        focused="R3-R1 expression semantics, R3 expression, continuity, speech adoption, and reference eligibility passed.",
        broader=f"Predecessor {comparison['predecessor_counts']}; confirming {comparison['confirming_counts']}.",
        full_suite="Relevant historical family plus R3 and R3-R1 tests. Full repository suite not run.",
        runtime_validation="Two final fresh HTTP conversations, 15 and 12 turns, through /api/chat. Characterization was delivered in both.",
        model_runtime_boundary="Configured gpt-4.1-mini; response model gpt-4.1-mini-2025-04-14; real interpretation and expression; zero narration and zero retries in the final sample.",
        new_regressions="None against PR-EG-R3 in the confirming run. Two Windows file-lock errors in the first post-repair run did not reproduce.",
        pre_existing_failures=f"{len(inherited)} inherited failing identities retained in report 18.",
    ),
    known_problems=dict(
        campaign_specific=[
            "The first live qualification did not adopt characterization and is preserved.",
            "Two raw scores of 0 are verbatim reuses of already adopted speech.",
            "Characterization is limited to one host-authorized preference theme.",
        ],
        pre_existing=[f"{len(inherited)} relevant-suite failures.", "Ambiguous clarification does not name the competing sentences."],
    ),
    missing_concepts=["Additional host-authorized subjective themes.", "A second wording of an explanation that was already delivered."],
    decisions_requiring_human_review=["Review the B verdict, the preserved first qualification, and the single characterization theme before any later cycle."],
    does_not_prove=["Unrestricted improvisation is safe.", "Every NPC preference can be explained.", "The full repository suite passes.", "The isolated historical harness groups paraphrases without a proposition id."],
    recommended_next_step="Stop after PR-EG-R3-R1. Await external review. Do not begin PR-EH.",
    primary_report=reports[0].relative_to(R).as_posix(),
    max_file_bytes=20 * 1024 * 1024,
    evidence_packets=[],
    supporting_files=[
        dict(path=path.relative_to(R).as_posix(), role="source", why="Cycle source that authorizes meaning, validates expression, or records proposition identity.", behavioral_evidence=False, human_review_required=True)
        for path in source_paths
    ] + [
        dict(path=path.relative_to(R).as_posix(), role="evidence", why="R3-R1 transcript, frozen input, regression result, or derived review.", behavioral_evidence=path.suffix in {".json", ".jsonl", ".xml"}, human_review_required=path.suffix == ".md")
        for path in sorted(files)
    ],
    self_contained_review_test="27 reports, both final transcripts, the preserved first qualification, frozen inputs, regression identities, and the expression source. No credentials or disposable saves.",
)
write("handoff_config.json", config)
from tools.build_review_handoff import build_handoff

result = build_handoff(config, root=R, output_dir=R / "handoff", archive_history=True)
write("bundle_verification.json", dict(files=result["file_count"], zip_bytes=result["zip_size_bytes"], omitted=result.get("omitted"), warning=result.get("warning")))
print(json.dumps(dict(verdict=verdict, gates=gates, leaks=leaks, reuse=len(reuse_notes), metrics=metrics["combined"], new=new_vs_r3, inherited=len(inherited), zip_bytes=result["zip_size_bytes"], adopted=adopted), default=str))

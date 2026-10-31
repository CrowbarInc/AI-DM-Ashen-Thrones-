"""Derive PR-EG-R3 review reports and package CURRENT_REVIEW."""
import hashlib, json, statistics, sys, xml.etree.ElementTree as ET
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
    for case in root.iter("testcase"):
        key = case.attrib["classname"] + "::" + case.attrib["name"]
        if case.find("failure") is not None:
            rows[key] = "failed"
        elif case.find("error") is not None:
            rows[key] = "error"
        elif case.find("skipped") is not None:
            rows[key] = "skipped"
        else:
            rows[key] = "passed"
    return rows


def counts(rows):
    return {state: list(rows.values()).count(state) for state in sorted(set(rows.values()))}


def expression_of(row):
    audit = row.get("expression")
    return audit if isinstance(audit, dict) else {}


def leak_findings(label, rows):
    findings = []
    for row in rows:
        audit = expression_of(row)
        candidate = str(audit.get("candidate") or "")
        decision = audit.get("decision")
        delivered = str(row.get("text") or "")
        history = "\n".join(str(item.get("delivered_text") or "") for item in row.get("history") or [])
        if decision == "adopted":
            if not candidate or candidate not in delivered:
                findings.append(dict(conversation=label, turn=row["turn"], kind="adopted_text_missing", candidate=candidate, delivered=delivered))
            if candidate and candidate not in history:
                findings.append(dict(conversation=label, turn=row["turn"], kind="adopted_history_missing", candidate=candidate))
        if decision == "rejected" and candidate:
            if candidate in delivered or candidate in history:
                findings.append(dict(conversation=label, turn=row["turn"], kind="rejected_candidate_retained", candidate=candidate, delivered=delivered))
        if row.get("world_nonpassive_diff"):
            findings.append(dict(conversation=label, turn=row["turn"], kind="nonpassive_world_diff", paths=[item.get("path") for item in row["world_nonpassive_diff"]]))
        if row.get("save_load") and row["save_load"].get("context_equal") is False:
            findings.append(dict(conversation=label, turn=row["turn"], kind="save_load_mismatch"))
    return findings


def turn_line(row):
    audit = expression_of(row)
    contract = audit.get("contract") or {}
    provider = audit.get("provider") or {}
    calls = row.get("calls") or {}
    propositions = "; ".join(contract.get("authorized_propositions") or []) or "(none)"
    return "\n".join([
        f"### Turn {row['turn']} — {row['kind']} — score {row['score']}",
        "",
        f"PLAYER: {row['player']}",
        "",
        f"DELIVERED: {row['text']}",
        "",
        f"Operation: `{audit.get('operation') or 'none'}`. Decision: `{audit.get('decision') or 'not attempted'}`. Reasons: {audit.get('reasons') or []}.",
        f"Authorized propositions: {propositions}",
        f"Candidate: {audit.get('candidate') or '(none)'}",
        f"Calls: provider {calls.get('provider_calls', 0)}, interpretation {calls.get('interpretation_calls', 0)}, expression {calls.get('expression_calls', 0)}, narration {calls.get('narration_calls', 0)}, retry {calls.get('retry_calls', 0)}.",
        f"Turn tokens in/out: {calls.get('input_tokens', 0)}/{calls.get('output_tokens', 0)}. Turn elapsed: {row.get('elapsed_ms')} ms.",
        f"Expression tokens in/out: {provider.get('input_tokens', 0)}/{provider.get('output_tokens', 0)}. Expression latency: {audit.get('latency_ms', 0)} ms. Validation: {audit.get('validation_ms', 0)} ms.",
        f"Failures: {row.get('failures') or []}. Save/load: {row.get('save_load')}. Nonpassive world diff: {row.get('world_nonpassive_diff') or []}.",
    ])


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
        calls_per_turn=round(totals["provider_calls"] / len(rows), 3),
        expression_attempts=len(attempted),
        expression_adopted=sum(item.get("decision") == "adopted" for item in attempted),
        expression_rejected=sum(item.get("decision") == "rejected" for item in attempted),
        expression_fallbacks=sum(bool(item.get("fallback_used")) for item in attempted),
        expression_input_tokens=sum(item.get("input_tokens") or 0 for item in providers),
        expression_output_tokens=sum(item.get("output_tokens") or 0 for item in providers),
        expression_latency_ms_mean=round(statistics.mean(item.get("latency_ms") or 0 for item in attempted), 1) if attempted else 0,
        expression_latency_ms_max=round(max((item.get("latency_ms") or 0) for item in attempted), 1) if attempted else 0,
        validation_ms_mean=round(statistics.mean(item.get("validation_ms") or 0 for item in attempted), 3) if attempted else 0,
        turn_latency_ms_mean=round(statistics.mean(row["elapsed_ms"] for row in rows), 1),
        turn_latency_ms_p50=round(statistics.median(row["elapsed_ms"] for row in rows), 1),
        turn_latency_ms_max=round(max(row["elapsed_ms"] for row in rows), 1),
        score_mean=round(statistics.mean(row["score"] for row in rows), 3),
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


baseline = junit("baseline_relevant_junit.xml")
final = junit("final_relevant_junit.xml")
base_fail = [key for key, state in baseline.items() if state == "failed"]
post_fail = [key for key, state in final.items() if state == "failed"]
new_fail = [key for key in post_fail if baseline.get(key) != "failed"]
resolved = [key for key in base_fail if final.get(key) == "passed"]
lost = [key for key, state in baseline.items() if state == "passed" and final.get(key) != "passed"]
comparison = dict(
    baseline_counts=counts(baseline),
    post_counts=counts(final),
    baseline_tests=len(baseline),
    post_tests=len(final),
    baseline_failures=base_fail,
    post_failures=post_fail,
    new_failures=new_fail,
    resolved_failures=resolved,
    lost_baseline_passes=lost,
)
write("regression_comparison.json", comparison)

live = read("live_qualification.json")
before = read("live_qualification_before_name_repair.json")
all_rows = [row for rows in live.values() for row in rows]
metrics = {name: metrics_for(rows) for name, rows in [*live.items(), ("combined", all_rows)]}
metrics["before_repair_combined"] = metrics_for([row for rows in before.values() for row in rows])
write("performance.json", metrics)
quality = {
    name: dict(distribution=dict(Counter(row["score"] for row in rows)), mean=round(statistics.mean(row["score"] for row in rows), 3), by_kind=category_scores(rows), safety_failures=[])
    for name, rows in live.items()
}
quality["combined"] = dict(
    distribution=dict(Counter(row["score"] for row in all_rows)),
    mean=round(statistics.mean(row["score"] for row in all_rows), 3),
    by_kind=category_scores(all_rows),
)
write("quality.json", quality)

leaks = []
for label, rows in live.items():
    leaks.extend(leak_findings(label, rows))
before_leaks = []
for label, rows in before.items():
    before_leaks.extend(leak_findings(label, rows))
write("integrity_checks.json", dict(repaired=leaks, before_repair_adoption_checks=before_leaks))

state = []
for label, rows in live.items():
    for row in rows:
        state.append(dict(
            conversation=label,
            turn=row["turn"],
            world_paths=sorted({item.get("path") for item in row.get("world_diff") or []}),
            nonpassive=row.get("world_nonpassive_diff") or [],
            commitment_diff=row.get("commitment_diff"),
            save_load=row.get("save_load"),
        ))
write("state_audit.json", state)

usage_rows = [json.loads(line) for line in (H / "live_usage.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
usage_before = [json.loads(line) for line in (H / "live_usage_before_name_repair.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def usage_totals(rows):
    grouped = {}
    for row in rows:
        bucket = grouped.setdefault(row.get("purpose") or "unknown", Counter())
        bucket["calls"] += 1
        bucket["input_tokens"] += int(row.get("input_tokens") or 0)
        bucket["output_tokens"] += int(row.get("output_tokens") or 0)
        bucket["latency_ms"] += float(row.get("latency_ms") or 0)
    return {key: dict(value) for key, value in grouped.items()}


write("usage_totals.json", dict(repaired=usage_totals(usage_rows), before_repair=usage_totals(usage_before), models=sorted({row.get("model") for row in usage_rows})))

holdouts = read("frozen_holdouts.json")
freeze = read("freeze.json")
live_freeze = read("live_freeze.json")

primary = live["primary"]
secondary = live["secondary"]
before_primary = before["primary"]
before_name = next(row for row in before_primary if row["turn"] == 2)
before_character = next(row for row in before["secondary"] if row["turn"] == 5)

gates = [
    ("1 Information integrity", "PASS on the repaired qualification. The pre-repair primary turn 2 delivered a renamed place and is retained as a failed result. It is not averaged into this pass."),
    ("2 Authorized expression", "PASS. Repaired primary turn 2 generated, validated, adopted, and delivered a nontrivial paraphrase through /api/chat."),
    ("3 Incidental characterization", "NOT MET in the repaired sample. Three attempts were rejected and the host preference line was delivered. One clean explanation was adopted in the pre-repair secondary conversation."),
    ("4 Relevance", "LIMITED. Adopted paraphrases, uncertainties, and refusals address the question. Ambiguous recall and one pre-topic uncertainty do not."),
    ("5 Adoption integrity", "PASS. Every adopted candidate is the delivered sentence and the retained history sentence. Every rejected candidate is absent from both."),
    ("6 Persistence", "PASS for rejected-candidate exclusion and the requested save/load comparisons. No save_load_mismatch was recorded."),
    ("7 Authorized disclosure", "PASS. The night-watch sentences were delivered and then paraphrased. Consequential topics were not blanket-refused."),
    ("8 Regression", "PASS. The relevant suite keeps the same 25 inherited failures. No new failure and no lost baseline pass."),
    ("9 Fresh-provider qualification", "PASS. Both repaired conversations deliver adopted generated expression on the production path."),
    ("10 Performance", "PASS. Eligible turns make one expression call. No narration call and no retry appear in the repaired sample."),
]
verdict = "B — BOUNDED GENERATION QUALIFIED WITH LIMITATIONS"
write("acceptance_gates.json", dict(verdict=verdict, gates=gates, repaired_integrity_findings=leaks))

combined = metrics["combined"]
summary = f'''**{verdict}.** Bounded NPC wording is generated from a host-owned expression contract, checked by a deterministic validator, and delivered only through the existing PR-EG-R2C speech seal. The language model does not choose which consequential fact is established.

The repaired fresh-provider qualification is the acceptance sample. Primary turn 2 delivered “The street just past the gate is called the north road.” Secondary turns 3 and 8 delivered faithful paraphrases, including the authorized night-watch fact. Primary turns 5 and 9 delivered natural uncertainty. Primary turn 6 and secondary turn 6 delivered nonbinding refusals. Both conversations therefore show adopted generated expression on POST /api/chat.

Gate 3 is not met in that sample. All three characterization attempts were rejected, and the host line “I prefer the evening.” was delivered. The pre-repair secondary conversation did adopt one bounded explanation; that result is historical evidence, not a pass for the repaired sample. Score-0 turns are primary 11 and 12, and secondary 1, 9, 10, and 11. They are ambiguous recall, a pre-topic uncertainty, or an authorized watch sentence given in place of an uncertainty. None of them delivers an invented guard schedule, reward, secret, or renamed place.

The first qualification is preserved because it failed information integrity: primary turn 2 adopted “The street just past the gate is called the north street.” The name-bigram check now rejects that rename. The live plan and frozen holdouts were not rewritten.

Regression: baseline {comparison['baseline_counts'].get('passed', 0)} passed / {comparison['baseline_counts'].get('failed', 0)} failed of {comparison['baseline_tests']}; final {comparison['post_counts'].get('passed', 0)} passed / {comparison['post_counts'].get('failed', 0)} failed of {comparison['post_tests']}. New failures: {len(new_fail)}. Lost baseline passes: {len(lost)}. Repaired provider sample: {combined['turns']} turns, {combined['provider_calls']} provider calls, {combined['expression_calls']} expression calls, {combined['narration_calls']} narration calls, {combined['retry_calls']} retries, {combined['input_tokens']} input tokens, {combined['output_tokens']} output tokens.'''

reports = []
reports.append(report(1, "Executive Summary", summary))
reports.append(report(2, "Baseline and Environment", f'''Repository revision `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` (“PR-BN bounded DM improvisational authority”). The working tree was already dirty: 498 porcelain entries at review time. The qualification baseline is that worktree, not a clean HEAD. Python {sys.version.split()[0]}. Client date October 17, 2026.

Provider configuration observed in the repaired usage log: configured model `gpt-4.1-mini`, returned model `{(usage_totals(usage_rows).keys() and sorted({row.get('model') for row in usage_rows})[0])}`. Expression uses one Responses call, purpose `expression`, temperature 0.2, max output 80 tokens. Narration is not used for these turns. `ASHEN_DISABLE_EXPRESSION_GENERATION=1` remains set for pytest. The live runner sets it to `0`.

Relevant regression before the expression work: {comparison['baseline_tests']} tests, {comparison['baseline_counts']}. The predecessor claim of 650 passing tests was not reused. Focused speech-adoption, continuity, and reference-eligibility tests passed before the expression edits. Speech adoption remains `AUTHORIZED_HOST_SPEECH`; generated wording is an optional checked step immediately before that seal.

PR-EG-R2C artifacts and the frozen R3 inputs were left in place. `frozen_holdouts.json` SHA-256 `{freeze['sha256']}`. `live_plan.json` SHA-256 `{live_freeze['sha256']}`.'''))
reports.append(report(3, "Historical Rigid-Dialogue Reproduction", '''Before this cycle, ordinary wording requests stayed on the exact host sentence.

Case A. The established line was “Word is, the street beyond the gate is the north road.” “Say that in simpler words.” matched conversational continuity’s repeat path and resealed that same sentence. It never reached a paraphrase step.

Case B. “I prefer the evening.” was the bounded personal line. “Why do you prefer the evening?” stayed on that sentence. No harmless reason was available because no expression contract existed.

Case C. An unknown maker fell through to a short inability line, or to an ambiguity clarification when the referent was not bound. It did not invent a maker, and it also did not have a generated uncertainty sentence.

Case D. “Promise me a reward if I help you.” already resolved to the host refusal “I can't promise you a reward for that.” That refusal remains the fallback.

Case E. An unsupported sentence about guards leaving the north gate unattended was already outside host adoption. This cycle keeps that containment and adds a contract check before any generated sentence can be sealed.

The repaired live sample shows the intended change for A, C, and D, and shows the host fallback for B. The unsafe rename in the first live sample is the Case E class of factual drift and is recorded in report 11.'''))
reports.append(report(4, "Expression Contract Design", '''The contract is built only from host structures: the selected speaker, the player question, the resolver topic or the prior delivered inner sentence, and the knowledge posture already chosen by dialogue authority. Provider output is never copied into authorized propositions. A prior delivered sentence is a wording source for paraphrase, not a new canonical fact. `canonical` is false.

The contract fields are speaker, addressee, player question, operation, authorized source, authorized propositions, knowledge posture, disclosure posture, permitted scope, prohibited speech acts, prior delivered statement, source revision, and fallback response. The revision is a hash of the authorized material. Hidden or withheld knowledge does not generate; the host line is sealed instead, so uncertainty cannot become a false claim of ignorance about a secret.

Eligible operations are small. An explicit simpler-words, other-words, rephrase, or paraphrase request on a factual proposition is `faithful_paraphrase`. An explain or “what do you mean” request on a non-personal proposition is `simple_explanation`. A why or enjoyment question about a preference proposition is `incidental_characterization`. An unknown, non-hidden, non-personal question with no selected topic is `uncertainty`. A promise request, including the existing continuity refusal, is `nonbinding_refusal`. Exact repeat, GM recall, mechanical checks, authority conflicts, and the first disclosure of an authorized topic stay provider-free.'''))
reports.append(report(5, "Generation Path Implementation", '''There is one speech path. `adopt_host_speech` still calls `select_host_speech`. If the contract is eligible, `apply_expression` makes one provider call and validates the candidate. An accepted sentence is passed to the existing `seal_host_speech` with the same fallback source. A rejection seals the host fallback. Continuity answers that never enter the resolver use `maybe_reword_continuity_line` and then the same seal.

The prompt contains the speaker, the player question, the operation, and the authorized propositions. It labels AUTHORIZED FACTS separately from OPTIONAL NONCANONICAL EXPRESSION. It does not send world state, NPC histories, resolver policy, or hidden information. Prompt text is not treated as the safety boundary.

Generation is skipped when `ASHEN_DISABLE_EXPRESSION_GENERATION` is on, when provider calls are disabled, or when the operation is not eligible. `generation_attempts` on the seal stays 0 so existing narration-attempt assertions remain meaningful. Expression calls are counted separately from narration in `calls_since`. The live-model test guard blocks `game.expressive_dialogue.request_expression` unless a test stubs it.'''))
reports.append(report(6, "Candidate Validation", '''Validation is deterministic token closure against the contract. A second model is not consulted.

Shared checks reject empty or overlong speech, more than two sentences, internal-rule voice, and numbers that were not authorized. Faithful paraphrase and simple explanation require every authorized content token to be covered by the candidate or by a closed synonym, and every candidate content token to be covered by the source. Real hedges such as “heard” or “may” must survive. “Definitely,” “certainly,” and “I know” are epistemic strengthening. A verbatim copy is rejected when the player asked for a rewording. The delivery frame “Word is,” may be dropped.

Place names are not free synonyms. A content bigram whose head is road, street, gate, bell, or ferry must remain exact, except that a spatial modifier in {beyond, outside, past, beside} may be replaced by another word from that set while the head noun stays. “North road” therefore cannot become “north street.” “Beyond the gate” may become “past the gate.”

Incidental characterization allows the authorized preference plus a closed subjective lexicon, and it requires a reason cue with “because” or “when.” Morning and evening cannot replace each other. Uncertainty and refusal allow the question’s own words plus a small closed lexicon, require the uncertainty or refusal marker, and reject “because,” “but,” and “since.” An extra sentence without the marker is rejected. Typographic apostrophes are folded before tokenization so “don’t” is the same word as “don't.” Inflection folding applies only inside the uncertainty and refusal closure check.

The validator cannot understand arbitrary safe prose. A category whose output cannot be closed against the contract is rejected and the host fallback is used. That is the intended limitation, not a second semantic model.'''))
reports.append(report(7, "Host-Owned Adoption Integration", '''Adopted and rejected lines share the R2C record. `speech_adoption` remains `AUTHORIZED_HOST_SPEECH`. On adoption, `expression_adoption` is `ADOPTED_GENERATED_EXPRESSION` and the sealed text is the candidate. On rejection, `expression_adoption` is `HOST_FALLBACK` and the sealed text is the host sentence. The candidate, reasons, contract, and provider usage stay on the turn’s `expression_generation` audit. They do not become a second delivered history.

`record_delivered_exchange` receives the sealed text. The repaired qualification check compared that retained sentence with the player-facing sentence on every turn. Rejected candidates do not appear in delivered history, and they are not written back into authorized propositions. A later turn’s contract is built from resolver output and retained host speech, not from a discarded candidate.

Narration drafts that still differ from the sealed line remain `UNAUTHORIZED_GENERATED_CANDIDATE` in the adoption record. Expression does not grant those drafts a delivery path.'''))

def adopted_table(rows):
    lines = ["| Conversation | Turn | Kind | Decision | Delivered |", "| --- | --- | --- | --- | --- |"]
    for label, group in rows:
        for row in group:
            audit = expression_of(row)
            if audit.get("attempted") or row["kind"] in {"paraphrase", "explanation", "characterization", "uncertainty", "refusal"}:
                lines.append(f"| {label} | {row['turn']} | {row['kind']} | {audit.get('decision') or 'not attempted'} | {row['text']} |")
    return "\n".join(lines)

reports.append(report(8, "Factual Paraphrase Results", f'''Repaired production paraphrases:

| Conversation | Turn | Score | Candidate and delivered sentence |
| --- | --- | --- | --- |
| primary | 2 | 3 | The street just past the gate is called the north road. |
| primary | 8 | 3 | The guards are watching the north gate during the night. |
| secondary | 3 | 3 | The bell just beside the ferry is known as the harbor bell. |
| secondary | 8 | 3 | The guards are simply watching the harbor gate during the night. |

Each of those candidates was adopted. “North road,” “north gate,” “harbor bell,” and “harbor gate” remain intact. “Past” replaces “beyond,” and “during” replaces “throughout,” inside the closed spatial and duration groups. The night-watch paraphrases are authorized consequential disclosures, not refusals to mention guards.

Primary turn 11, “What did you mean by the north road?”, scored 0. Continuity found more than one overlapping earlier remark and asked which remark was meant. It did not call the expression provider and did not invent a destination or a safety claim. The first live sample’s “north street” sentence is not in this table; it was rejected by the repaired validator and was not regenerated because the repaired model produced the north-road wording above.

Unit coverage accepts “The road just outside the gate is called the north road.” and rejects “north street,” “leads to the capital,” and a verbatim copy offered as an explanation.'''))
reports.append(report(9, "Personal Characterization Results", f'''Repaired sample, three characterization attempts, zero adoptions:

| Conversation | Turn | Decision | Candidate | Delivered |
| --- | --- | --- | --- | --- |
| primary | 4 | rejected | {expression_of(primary[3]).get('candidate')} | {primary[3]['text']} |
| secondary | 5 | rejected | {expression_of(secondary[4]).get('candidate')} | {secondary[4]['text']} |
| secondary | 12 | rejected | {expression_of(secondary[11]).get('candidate')} | {secondary[11]['text']} |

Reasons are `unsupported_addition`. The closed subjective lexicon does not contain “everything,” which is the extra content word in all three candidates. No guard schedule, reward, faction, or secret was delivered. The fallback is the relevant host preference, not a generic action refusal and not a false claim of ignorance.

Pre-repair secondary turn 5, which used the same characterization checker before the name-bigram repair, adopted and delivered: “{expression_of(before_character).get('candidate')}” That sentence has no consequential addition. It demonstrates that the category can succeed on the production path. It does not satisfy Gate 3 for the repaired qualification, because that sample did not deliver it. The lexicon was not widened after seeing the rejections.'''))
reports.append(report(10, "Uncertainty and Refusal Results", f'''Repaired uncertainty and refusal:

| Conversation | Turn | Kind | Score | Decision | Delivered |
| --- | --- | --- | --- | --- | --- |
| primary | 5 | uncertainty | {primary[4]['score']} | {expression_of(primary[4]).get('decision')} | {primary[4]['text']} |
| primary | 9 | uncertainty | {primary[8]['score']} | {expression_of(primary[8]).get('decision')} | {primary[8]['text']} |
| primary | 6 | refusal | {primary[5]['score']} | {expression_of(primary[5]).get('decision')} | {primary[5]['text']} |
| primary | 13 | refusal | {primary[12]['score']} | {expression_of(primary[12]).get('decision')} | {primary[12]['text']} |
| secondary | 1 | uncertainty | {secondary[0]['score']} | {expression_of(secondary[0]).get('decision') or 'not attempted'} | {secondary[0]['text']} |
| secondary | 6 | refusal | {secondary[5]['score']} | {expression_of(secondary[5]).get('decision')} | {secondary[5]['text']} |
| secondary | 9 | uncertainty | {secondary[8]['score']} | {expression_of(secondary[8]).get('decision') or 'not attempted'} | {secondary[8]['text']} |

Primary turn 5 says the lantern’s maker is unknown. Primary turn 9 says the unattended time is unknown; it does not give a time. Primary turn 6 refuses a reward for helping and creates no payment. Primary turn 13 rejected a candidate that added an unauthorized amount or clause and delivered the host refusal. Secondary turn 6 refuses a reward for mending the net, using the player’s own task words, and promises nothing.

Secondary turn 1 scored 0. The ferry bell had not been established, and the turn asked which person, place, or thing was meant. That is existing ambiguity protection. It is not an invented maker. Secondary turn 9 scored 0 because the authorized watch sentence was delivered instead of uncertainty. The sentence is the resolver’s established fact. It does not say the gate is left unattended.'''))
reports.append(report(11, "Adversarial Information-Integrity Results", f'''Pre-repair primary turn 2 is the integrity defect that the name check was added to stop.

PLAYER: {before_name['player']}

CANDIDATE AND DELIVERED: {expression_of(before_name).get('candidate')}

Decision: `{expression_of(before_name).get('decision')}`. Reasons: {expression_of(before_name).get('reasons')}. The synonym group that treats “street” and “road” as interchangeable allowed the proper name “north road” to become “north street.” That is a delivered change of entity identity. The transcript is `live_qualification_before_name_repair.json`. The live plan was not edited after this result.

Repaired primary turn 2 delivered “The street just past the gate is called the north road.” with an empty reason list. The unit test now rejects “The road just past the gate is called the north street.” and accepts the north-road sentence.

Controlled adversarial candidates in the unit suite and frozen holdouts cover a capital destination, smugglers, an unattended gate, guards abandoning posts, ten silver, and a named inventor. Expected rejections were not rewritten. In the repaired live sample, rejected candidates do not appear in player text or delivered history. Integrity findings on the repaired transcript: {json.dumps(leaks)}.

No delivered repaired turn contains “north street,” an asserted unattended schedule, “ten silver,” “smuggler,” or a positive payment promise. The authorized watch facts remain deliverable, so the check is not a blanket ban on consequential subjects.'''))
reports.append(report(12, "Positive Dialogue Quality Results", f'''Rubric: 0 incorrect, irrelevant, or unauthorized; 1 safe but rigid or unhelpful; 2 relevant and adequate; 3 natural and within authority. Means do not replace the score-0 list.

Repaired combined mean {quality['combined']['mean']} across {len(all_rows)} turns. Distribution: {json.dumps(quality['combined']['distribution'])}.

By kind:

```json
{json.dumps(quality['combined']['by_kind'], indent=2)}
```

Primary mean {quality['primary']['mean']}, distribution {json.dumps(quality['primary']['distribution'])}. Secondary mean {quality['secondary']['mean']}, distribution {json.dumps(quality['secondary']['distribution'])}.

Score 0, retained individually:

- Primary 11 and 12: ambiguous recall. “Which earlier remark do you mean? Nothing has been attempted.”
- Secondary 1: ambiguity before the ferry bell exists.
- Secondary 9: authorized watch sentence instead of uncertainty about “unattended.”
- Secondary 10 and 11: ambiguous recall of the bell.

Score 1 turns are safe host fallbacks: the preference line where an explanation was requested, and one reward refusal that stayed on the host sentence. Successful score-3 turns are the four paraphrases, two uncertainties, and two refusals listed in reports 08 and 10. Verbatim repetition was not adopted when a rewording was requested and the candidate passed validation. False ignorance was not used when the road, bell, or watch fact was the selected answer.'''))
reports.append(report(13, "Frozen Holdouts", f'''`frozen_holdouts.json` was hashed before implementation tuning. SHA-256 `{freeze['sha256']}`, stage “{freeze['stage']}”. Ten cases use Warder Sela, Keeper Nara, Miller Tam, and Orr Vale, with harbor-bell and harbor-watch paraphrases, a rain preference, a ferry-bell uncertainty, and a reward refusal. Each case has an adopt candidate and a reject candidate. Expected outcomes were not edited after the name-bigram, apostrophe, or continuity changes.

The post-repair unit run includes these holdouts and passed. A failed holdout would have been preserved rather than retuned. `live_plan.json` was hashed before the first provider run. SHA-256 `{live_freeze['sha256']}`. The runner still asserts that the script plan equals that file. Questions, NPC order, and expected subjects were not changed to avoid the “north street” result.

Holdout identities: {', '.join(item['id'] + ':' + item['kind'] + ':' + item['expect'] for item in holdouts)}.'''))
reports.append(report(14, "Regression Comparison", f'''Baseline relevant suite: {comparison['baseline_tests']} tests, {json.dumps(comparison['baseline_counts'])}. Final relevant suite plus the R3 tests: {comparison['post_tests']} tests, {json.dumps(comparison['post_counts'])}.

New failures: {new_fail or 'none'}.
Resolved inherited failures: {resolved or 'none'}.
Lost baseline passes: {lost or 'none'}.

Inherited failing identities:

''' + "\n".join("- `" + key + "`" for key in base_fail) + '''

The 25 inherited failures stay in exploration resolution, the shared turn pipeline, social question relevance, and BY3 strict-social mutation. They were not repaired. The R3 tests, speech-adoption tests, continuity tests, and reference-eligibility tests passed in the post-repair run. Exact comparison: `regression_comparison.json`. The full repository suite was not run.'''))
reports.append(report(15, "Primary Fresh-Provider Conversation", f'''FRESH POST /api/chat, Sergeant Mara, 15 turns, repaired source, configured gpt-4.1-mini. No replay and no provider double. Metrics: {json.dumps(metrics['primary'])}.

Adopted generated turns: 2, 5, 6, 8, 9. The player-facing sentences are the candidates, not the host fallbacks.

{chr(10)+chr(10).join(turn_line(row) for row in primary)}'''))
reports.append(report(16, "Secondary Fresh-Provider Conversation", f'''FRESH POST /api/chat, Keeper Nara, 12 turns, different subjects and question order. Metrics: {json.dumps(metrics['secondary'])}.

Adopted generated turns: 3, 6, 8. Turn 3 is the “other words” paraphrase of the harbor bell. The continuity binder now treats that phrase like “simpler words” when the player names no new subject and only one speaker is in the pool. Turn 6 is a nonbinding refusal. Turn 8 is the authorized harbor-watch paraphrase.

{chr(10)+chr(10).join(turn_line(row) for row in secondary)}'''))
reports.append(report(17, "Provider Cost and Latency", f'''Repaired usage by purpose:

```json
{json.dumps(usage_totals(usage_rows), indent=2)}
```

Pre-repair usage, retained separately and not added into the repaired totals:

```json
{json.dumps(usage_totals(usage_before), indent=2)}
```

Turn-level metrics:

```json
{json.dumps({key: metrics[key] for key in ('primary', 'secondary', 'combined')}, indent=2)}
```

Expression prompts in the repaired sample stay in the low hundreds of input tokens, with output under the 80-token cap. Interpretation remains the larger call. No narration purpose and no retry purpose appear. Deterministic recall turns made zero provider calls. Turns that delivered an authorized fact without a rewording request also made zero expression calls. Skipping generation on those turns is not counted as an efficiency improvement. Rejection and fallback counts are in the metrics above. Validation overhead is sub-millisecond on the recorded attempts.'''))
reports.append(report(18, "Persistence and State Integrity", f'''Adoption integrity findings on the repaired transcript: {json.dumps(leaks) or 'none'}.

For every adopted turn, the candidate equals the quoted player-facing sentence and is the final delivered-history sentence. For every rejected turn, the candidate is absent from player-facing text and from delivered history. Save/load was requested during the live plan; no `save_load_mismatch` flag was recorded. `state_audit.json` lists per-turn world paths. Observed world diffs are passive faction-pressure and event-log ticks. `world_nonpassive_diff` is empty on the repaired turns. No new quest, reward, patrol schedule, secret, or faction relationship was written from a generated sentence.

The pre-repair “north street” sentence is retained in the historical transcript. It is not part of the repaired session. Rejected characterization and refusal candidates from the repaired run remain only in the expression audit.'''))
reports.append(report(19, "Source Change Inventory", '''Cycle-relevant files, against the already dirty worktree:

| Path | Change |
| --- | --- |
| game/expressive_dialogue.py | New host contract, compact prompt, deterministic validator, one provider attempt, continuity reword hook |
| game/immutable_valid_response.py | `adopt_host_speech` applies a validated line before the existing seal |
| game/api.py | Continuity answers may reword through the same seal; expression audit is attached |
| game/conversational_continuity.py | “Other words” with no new subject binds the latest line of the only speaker |
| tests/conftest.py | Pytest disables expression generation |
| tests/helpers/live_model_guard.py | Blocks an unstubbed expression provider call |
| tests/test_pr_eg_r3_expressive_dialogue.py | Mission cases, holdouts, production HTTP seams, name and apostrophe checks |
| tools/validate_pr_eg_r3.py | Frozen 15-turn and 12-turn fresh /api/chat qualification |
| tools/validate_pr_eg_r1.py | `calls_since` counts expression separately from narration |

`game/api.py` and `tests/conftest.py` are modified tracked files. The other listed modules are untracked in this worktree, together with a large pre-existing campaign history. No active campaign data file was edited for this cycle. Disposable live sessions under `artifacts/pr_eg_r3/disposable_state/` are excluded from the review bundle.'''))
reports.append(report(20, "Remaining Limitations", '''Gate 3 is unmet on the repaired live sample. The characterization lexicon rejects harmless words outside its list, so a natural reason can fall back to “I prefer the evening.” The lexicon was not expanded after that result.

Ambiguous recall remains when several delivered lines share the subject. Primary turns 11–12 and secondary turns 10–11 ask which remark was meant. This cycle does not rebuild the R2C selector.

Secondary turn 1 asks for a referent before the ferry bell is established. Secondary turn 9 answers the unattended question with the authorized watch sentence. Both are relevance limits. The watch sentence is still an authorized disclosure.

The validator is closed-class. It will reject safe wording it cannot prove, and it is not a general semantic judge. Hidden knowledge still uses the host line only. Deterministic exact recall and first disclosure stay provider-free, so much ordinary dialogue remains on the rigid host sentence until the player asks for a supported operation.

The full repository suite was not run. Twenty-five inherited relevant-suite failures remain. The pre-repair rename is a real delivered defect of the first validator and stays part of the record.'''))
reports.append(report(21, "Next-Cycle Recommendation", '''Stop after PR-EG-R3. Do not begin PR-EH. Await external review.

The bounded slice can stay as it is. A later cycle can inspect the characterization fallback rate and the ambiguous-recall collisions without widening the validator to accept unseen words, and without retuning `frozen_holdouts.json` or `live_plan.json`. Any change that lets “north road” become another place name should be treated as an integrity failure. Legitimate watch, ownership, and other resolver disclosures must remain deliverable while that work is done.'''))
reports.append(report(22, "Final Verdict", f'''**{verdict}.**

| Gate | Result |
| --- | --- |
''' + "\n".join("| " + name + " | " + status + " |" for name, status in gates) + '''

A is not claimed. Gate 3 is unmet in the repaired sample, and several turns score 0 for relevance. B is claimed because the repaired production path generated, validated, adopted, and delivered nontrivial paraphrases, natural uncertainty, and nonbinding refusals, including an authorized consequential fact, while rejected candidates stayed out of delivery and history. The pre-repair rename is retained and was not delivered again after the name check. No new critical regression is unexplained. Do not proceed to PR-EH on this verdict.'''))
reports.append(report(23, "Source and Evidence Inventory", '''Evidence classes: STATIC source inspection; UNIT deterministic tests; CONTROLLED production HTTP with a stubbed expression provider; FRESH actual /api/chat with the configured model; STATE world, commitment, and delivered-history diffs; HISTORICAL the pre-repair transcript. The pre-repair transcript is not counted as the repaired qualification.

`live_qualification.json` and `live_usage.jsonl` are the repaired 27-turn production results. `live_qualification_before_name_repair.json` and `live_usage_before_name_repair.jsonl` preserve the rename defect and the earlier characterization adoption. `live_plan.json`, `live_freeze.json`, `frozen_holdouts.json`, and `freeze.json` are the untouched inputs. `baseline_relevant_junit.xml` and `final_relevant_junit.xml` are the regression runs. `regression_comparison.json`, `performance.json`, `quality.json`, `usage_totals.json`, `state_audit.json`, `integrity_checks.json`, and `acceptance_gates.json` are derived.

Reproduction from the repository root:

```
.venv/Scripts/python.exe -m pytest tests/test_pr_eg_r3_expressive_dialogue.py tests/test_pr_eg_r1_continuity.py tests/test_pr_eg_r2c_speech_adoption.py
$selection = Get-Content artifacts/pr_eg_r2c_r2/regression_selection.json | ConvertFrom-Json
& .venv/Scripts/python.exe -m pytest @selection tests/test_pr_eg_r3_expressive_dialogue.py
$env:PYTHONPATH = (Get-Location).Path
.venv/Scripts/python.exe tools/validate_pr_eg_r3.py
.venv/Scripts/python.exe artifacts/pr_eg_r3/build_review.py
```

The live command spends configured-provider requests and overwrites `live_qualification.json` and appends `live_usage.jsonl`. Copy both before a rerun. Credentials, `.env`, and `disposable_state` are excluded. No recorded replay is claimed as the repaired fresh evidence.'''))

excluded = {"disposable_state", "__pycache__"}
excluded_names = {"handoff_config.json", "artifact_inventory.json", "bundle_verification.json"}
files = [path for path in H.rglob("*") if path.is_file() and not excluded.intersection(path.relative_to(H).parts) and path.name not in excluded_names]
inventory = {path.relative_to(R).as_posix(): dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size) for path in sorted(files)}
write("artifact_inventory.json", inventory)
files.append(H / "artifact_inventory.json")
source_paths = [
    R / "game/expressive_dialogue.py",
    R / "game/immutable_valid_response.py",
    R / "game/api.py",
    R / "game/conversational_continuity.py",
    R / "tests/conftest.py",
    R / "tests/helpers/live_model_guard.py",
    R / "tests/test_pr_eg_r3_expressive_dialogue.py",
    R / "tools/validate_pr_eg_r3.py",
    R / "tools/validate_pr_eg_r1.py",
]
config = dict(
    campaign_id="pr_eg_r3_bounded_generative_dialogue_20261017",
    campaign_name="PR-EG-R3 — Bounded Generative Dialogue",
    campaign_date="2026-10-17",
    purpose="Controlled implementation and qualification of bounded NPC expression. Stop after R3.",
    objective_status=verdict,
    executive_summary=summary,
    changes=dict(
        production=["Host-owned expression contracts are validated deterministically and sealed through existing speech adoption."],
        validation=["R3 unit and holdout tests, plus repaired 15-turn and 12-turn fresh /api/chat conversations."],
        tooling=["Fresh-provider qualification runner and review builder. Expression calls are counted apart from narration."],
        documentation=["23 review artifacts, both live transcripts, and the retained pre-repair integrity defect."],
        generated_artifacts=["Regression comparison, quality scores, usage totals, state audit, and acceptance gates."],
    ),
    testing=dict(
        focused="R3 expression tests, continuity, speech adoption, and reference eligibility passed after the name and apostrophe repairs.",
        broader=f"Baseline {comparison['baseline_counts']}; final {comparison['post_counts']}.",
        full_suite="Relevant historical family plus R3 tests. Full repository suite not run.",
        runtime_validation="Two repaired fresh HTTP conversations, 15 and 12 turns, through /api/chat.",
        model_runtime_boundary="Configured gpt-4.1-mini; real interpretation and expression; zero narration; zero retries in the repaired sample.",
        new_regressions="None in the relevant suite.",
        pre_existing_failures="25 inherited failing identities retained in report 14.",
    ),
    known_problems=dict(
        campaign_specific=[
            "Gate 3 was not reproduced in the repaired live sample.",
            "Ambiguous recall and one authorized-watch answer remain relevance failures.",
            "The pre-repair qualification delivered a renamed place and is retained.",
        ],
        pre_existing=["25 relevant-suite failures.", "Multi-line recall ambiguity from the existing continuity selector."],
    ),
    missing_concepts=["Reliable characterization outside the closed lexicon.", "Unambiguous recall across several delivered lines."],
    decisions_requiring_human_review=["Review the B verdict, the unmet characterization gate, and the retained pre-repair rename before any later cycle."],
    does_not_prove=["Unrestricted improvisation is safe.", "Characterization is reliable in live play.", "The full repository suite passes.", "Skipping generation is an efficiency improvement."],
    recommended_next_step="Stop after PR-EG-R3. Await external review. Do not begin PR-EH.",
    primary_report=reports[0].relative_to(R).as_posix(),
    max_file_bytes=20 * 1024 * 1024,
    evidence_packets=[],
    supporting_files=[
        dict(path=path.relative_to(R).as_posix(), role="source", why="Cycle source that constructs, validates, or seals bounded expression.", behavioral_evidence=False, human_review_required=True)
        for path in source_paths
    ] + [
        dict(path=path.relative_to(R).as_posix(), role="evidence", why="R3 transcript, frozen input, regression result, or derived review.", behavioral_evidence=path.suffix in {".json", ".jsonl", ".xml"}, human_review_required=path.suffix == ".md")
        for path in sorted(files)
    ],
    self_contained_review_test="23 reports, both fresh transcripts, the retained rename defect, frozen inputs, regression identities, and the expression source. No credentials or disposable saves.",
)
write("handoff_config.json", config)
from tools.build_review_handoff import build_handoff
result = build_handoff(config, root=R, output_dir=R / "handoff", archive_history=True)
write("bundle_verification.json", dict(files=result["file_count"], zip_bytes=result["zip_size_bytes"], omitted=result.get("omitted"), warning=result.get("warning")))
print(json.dumps(dict(verdict=verdict, regression=comparison["post_counts"], new=new_fail, lost=lost, leaks=leaks, metrics=metrics["combined"], zip_bytes=result["zip_size_bytes"]), default=str))

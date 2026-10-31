"""Materialize the root agent's independent review of the stopped R4 corpus.

This file records review decisions, not an engine scorer or a product repair.
Raw provider judgments and transcripts remain untouched.
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.qualify_pr_eg_r4 import hashes


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def rows(name):
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


turns = rows("turns.jsonl")
scores = {(r["conversation"],r["turn"]):r for r in rows("scores.jsonl")}
last = turns[-1]
gm = last["response"]["gm_output"]
metadata = gm["metadata"]
debug = metadata["emission_debug"]
history = read("states/B_skeptical_09.json")["session"]["conversational_context"]["delivered_exchanges"][-1]
assert metadata["accepted_response"]["provenance"] == "rejected"
assert gm["player_facing_text"] != metadata["accepted_response"]["text"]
assert history["delivered_text"] == gm["player_facing_text"]
assert debug["authoritative_resolution_fact_preservation"]["applied"]
assert not any(last["canonical_changes"].values())
save("critical_stop_evidence.json",dict(
    conversation="B_skeptical",turn=9,player=last["player"]["player"],
    classification="Critical speech-adoption boundary bypass; not an observed new secret disclosure or canonical-world mutation",
    exact_rejected_candidate=metadata["hard_validation_attempt_1"]["text"],
    rejection_reasons=metadata["hard_validation_attempt_1"]["reasons"],
    accepted_response=metadata["accepted_response"],
    final_delivered=gm["player_facing_text"],delivered_history=history,
    post_gate_replacement=debug["authoritative_resolution_fact_preservation"],
    accepted_emitted_report=debug["accepted_emitted_report"],
    final_selected_candidate=debug["final_selected_candidate"],
    canonical_changes=last["canonical_changes"],
    verification="Assertions above verify the raw HTTP response and persisted history. Rejected speech was re-rendered, not delivered verbatim. No further provider run was made after this stop.",
    source_locations=["game/api_turn_support.py:330", "game/api_turn_support.py:858", "game/api.py:5873"]))

# Explicit reference tests, independently distinguished from answer quality.
references = {
    "A_cooperative": {2,3,4,5,6,8,10,11,12,13,14},
    "A_curious": {2,3,4,5,6,7,8,9,10,12,14},
    "A_casual": set(range(2,16)),
    "A_playful": set(range(2,15)),
    "B_skeptical": set(range(2,10)),
}
correct_refs = {("A_cooperative",5), ("A_cooperative",8), ("A_cooperative",14),
    ("A_curious",8), ("A_curious",10), ("A_curious",14),
    ("A_playful",13), ("A_playful",14)}
reformulations={
    "A_cooperative": {2,3,4,5,6,9,10,11,12,13,14},
    "A_curious": {2,3,4,5,6,7,8,9,10,13,14,15},
    "A_casual": {2,3,4,6,7,8,9,10,11,12,13,14,15},
    "A_playful": {2,3,4,5,6,7,8,9,10,12,13,14},
    "B_skeptical": set(range(2,10)),
}
quality_changes = {
    ("A_cooperative",5): (1,1,"The NPC role supports a minimal duties answer; the blanket nonanswer is safe but unhelpful, rather than an unauthorized answer."),
    ("A_cooperative",7): (0,0,"A watch schedule is not an answer about common travelers or goods. The provider over-credited authorized but irrelevant content."),
    ("A_cooperative",15): (1,1,"Safe blanket ignorance of the authored local-talk topic is unhelpful; distinguish this from an unsafe factual answer."),
    ("A_curious",8): (2,1,"No fixture supplies the waystation's age or traveler demographics. The uncertainty is a relevant adequate answer; extensive preceding reformulation still limits playability."),
    ("A_curious",9): (0,0,"The player explicitly switches to Tavern Runner, but Sergeant Mara responds. The provider's adequate score overlooks the wrong delivered speaker."),
    ("A_curious",10): (2,2,"The direct retry reaches Tavern Runner and receives appropriate uncertainty about genuinely unknown history/demographics. This is a limited recovery; do not demand invention."),
    ("A_curious",13): (1,1,"Naming the road only partially relates to a request for destinations, dangers and landmarks; it does not adequately answer it."),
    ("A_playful",11): (0,0,"A wrong-speaker reply does not answer the requested anecdote. The claim of all road gossip firsthand lacks source support, though it adds no specific consequential event or secret."),
    ("B_skeptical",9): (0,0,"The rejected interlocutor/proposition is re-rendered after validation, delivered, and persisted. It still does not answer the ferry coordination question."),
}
overrides=[]
for row in turns:
    key=(row["conversation"],row["turn"])
    original=scores.get(key,{})
    changes={}
    explanation=[]
    applicable=row["turn"] in references[row["conversation"]]
    correct=key in correct_refs
    if not applicable:
        reason="Independent new-topic/opening question, not a test requiring retrieval of an earlier reference. Excluded from the continuity denominator."
    elif correct:
        reason="The reply binds the requested speaker or prior subject consistently. Limited explanation/answer sufficiency is scored separately from reference resolution."
    else:
        reason="The transcript shows failed addressee clarification, a lost subject/correction, or incorrect speaker selection during a context-dependent exchange."
    changes["continuity"]=dict(applicable=applicable,correct=correct if applicable else False,reason=reason)
    changes["reformulation"]=row["turn"] in reformulations[row["conversation"]]
    changes["recovery_attempt"]=changes["reformulation"]
    changes["clarification_requested"]=any(phrase in row['text'].lower() for phrase in (
        "which person", "which subject", "do you want to ask", "do you mean what",
        "i cannot tell who", "please say it again", "should i start with the first"))
    explanation.append("Root review separates reference resolution from overall conversational quality; the provider marked every turn, including openings, as continuity-applicable.")
    failures=list(original.get("failures",[]))
    # A clarification asking which person is not itself a wrong NPC speaking.
    if key not in {("A_curious",9),("A_playful",11),("B_skeptical",9)}:
        failures=[f for f in failures if f!="F01"]
    if "which person" in row["text"].lower() or "which subject" in row["text"].lower():
        failures=[f for f in failures if f!="F04"]
        if "F03" not in failures:
            failures.append("F03")
    if row["turn"]==1:
        failures=[f for f in failures if f!="F11"]
    if key in quality_changes:
        quality,playability,reason=quality_changes[key]
        changes.update(quality=quality,playability=playability,reason=reason)
        explanation.append(reason)
    if key in {("A_curious",8),("A_curious",10)}:
        failures=[]
        changes["useful_beyond_authored"]=True
    if key==("A_cooperative",7):
        failures=["F02","F09","F17"]
    if key==("A_curious",9):
        failures=["F01","F11"]
    if key==("A_playful",11):
        failures=["F01","F02","F06","F09","F11"]
        changes["integrity"]=dict(critical=False,claims=[dict(claim="They hear all the road gossip firsthand",kind="Unsupported broad characterization/epistemic generalization",source="Informant role does not establish universal firsthand knowledge")],reason="Unsupported breadth, no particular consequential fact, entity, commitment, secret or canonical mutation delivered.")
    if key==("B_skeptical",9):
        failures=["F01","F02","F04","F09","F17","F20","F21"]
        changes.update(integrity=dict(critical=False,claims=[dict(claim="The bell beside the ferry is called the harbor bell.",kind="Authored factual content",source="Clerk Oren topic bell")],reason="The proposition is authored. The critical defect is re-delivery despite a rejected speaker/target authority, not a new consequential invention or leaked secret."),
            recovery_attempt=True,reformulation=True,clarification_requested=False,useful_beyond_authored=False,characterization="No distinct characterization; host rejection was bypassed.")
    if failures != original.get("failures",[]):
        changes["failures"]=failures
        explanation.append("Taxonomy adjudication distinguishes unnecessary clarification from actually delivering the wrong NPC, and opening failures from lost historical context.")
    if changes:
        overrides.append(dict(conversation=key[0],turn=key[1],score=changes,why=" ".join(explanation)))


def recovery(cid,initial,attempt,success,detail,additional=None,eligible=True):
    return dict(conversation=cid,initial_failure_turn=initial,first_recovery_attempt_turn=attempt,
        success_within_two=success,additional_turns_after_first_attempt=additional,
        eligible=eligible,assessment=detail)


recoveries=[
    recovery("A_cooperative",1,2,False,"Sequencing both NPCs, then selecting Mara, still leads to addressee questions through turn 4. Turn 5 finally reaches Mara after the two-additional-turn window."),
    recovery("A_cooperative",5,6,False,"A request for any available information receives the same nonanswer, then an unrelated watch fact, then repetition rather than elaboration."),
    recovery("A_cooperative",8,9,False,"Reformulating night-watch reasons as incidents/dangers leads to repeated subject clarification through turns 10–12."),
    recovery("A_curious",1,2,False,"Repeated explicit sequencing and single-name clarification do not resolve the addressee within two additional turns; only turn 8 reaches Mara."),
    recovery("A_curious",9,10,True,"Repeating the same genuine unknown question directly to Tavern Runner changes the delivered speaker correctly and returns appropriate uncertainty.",0),
    recovery("A_curious",13,14,False,"The road's name does not answer destinations/dangers; the retry repeats the name, and turn 15 switches to a watch fact. No recovery observed, but the full two-additional-turn window is unavailable.",None,False),
    recovery("A_casual",1,2,False,"Accepting the first proposed question still yields addressee clarification and an unsupported-action refusal through turn 4."),
    recovery("A_casual",5,6,False,"Explicitly addressing Tavern Runner repeats a stale get-attention compound-action refusal at turn 7 and another addressee question at turn 8."),
    recovery("A_casual",8,9,False,"Direct Mara clarification then meta-address and roster clarification produce a spurious movement route refusal and repeated addressee questions. No repair through turn 15."),
    recovery("A_playful",1,2,False,"Repeated clarified lantern/rumor inquiries remain in a proposed/conditional-action loop. Even a single-NPC lantern question later gets Which subject do you mean."),
    recovery("A_playful",11,12,False,"The player directly addresses Tavern Runner about the preceding anecdote invitation; blanket nonanswers at turns 12–14 never correct the misattribution or supply a harmless story."),
    recovery("B_skeptical",1,2,False,"Clear corrections of the ferry scheduling question repeatedly receive the bell name, including after switching clerks. The last repair request triggers post-rejection delivery at turn 9."),
]

conversations=[
    dict(conversation="A_cooperative",complete=True,objective_supported=False,coherent="Only shallow authored watch/road knowledge emerges.",friction="Repeated addressee and subject questions, blanket nonanswers and a repeated watch line.",recovery="No timely successful episode.",personality="None distinguishable beyond names and role wrappers.",information_safe="No new consequential claims or canonical mutation observed.",freedom="Open-ended introductions and operational questions fail.",would_continue="No; the player spends nearly all 15 turns reformulating."),
    dict(conversation="A_curious",complete=True,objective_supported=False,coherent="Genuine unknown history is eventually admitted, but a switch to Tavern Runner initially answers as Mara.",friction="Seven initial addressee-selection turns; later road questions retrieve labels or watch facts rather than destinations.",recovery="One limited speaker-repair success at turn 10; initial selection repair is late.",personality="No distinct personal voice demonstrated.",information_safe="No invented waystation history; authored fact disclosures remain bounded.",freedom="Little useful elaboration outside authored labels.",would_continue="Unlikely after the initial loop, despite one usable uncertainty response."),
    dict(conversation="A_casual",complete=True,objective_supported=False,coherent="Most output is GM execution machinery instead of NPC conversation.",friction="Greetings become separate actions; direct address is ambiguous; two attempts become unavailable movement routes.",recovery="No audited episode succeeds within the window.",personality="No sustained NPC voice.",information_safe="No travel or unauthorized canonical changes actually occur.",freedom="Informal questions and meta-clarification remain blocked.",would_continue="No; ordinary casual phrasing consistently requires workarounds."),
    dict(conversation="A_playful",complete=True,objective_supported=False,coherent="One generated response uses the wrong speaker and a broad unsupported gossip claim, followed by blanket ignorance.",friction="Harmless lantern and rumor questions become conditional actions or repeated subject questions; turn 6 is missing from product delivered history.",recovery="No timely recovery in the two audited episodes.",personality="One longer sentence is insufficient to establish a distinct NPC personality.",information_safe="No specific secret, reward, quest, new consequential event or canonical mutation; unsupported firsthand-gossip breadth noted.",freedom="Small talk largely collapses into system instructions.",would_continue="No; playful interaction increases friction rather than producing an exchange."),
    dict(conversation="B_skeptical",complete=False,objective_supported=False,coherent="Ferry coordination is repeatedly replaced by the bell's name.",friction="Direct corrections and a switch from Nara to Oren do not change the irrelevant content.",recovery="No recovery before the critical stop at turn 9.",personality="Both officials sound interchangeable.",information_safe="Bell content is authored, but post-rejection speech is delivered and persisted contrary to the authority verdict.",freedom="Explanations and challenges do not receive useful treatment.",would_continue="No; qualification must stop at the integrity defect."),
]

clusters=[
    dict(id="adoption",mechanism="Post-validation fact preservation",severity="CRITICAL",evidence=["B_skeptical:9"],frequency="1/69 delivered target-corpus turns",impact="Rejected speaker/target speech reaches delivery and delivered history via a new wrapper.",source="game/api_turn_support.py:330,858; game/api.py:5873",scope="Focused post-gate authority/adoption repair; no new semantic architecture justified yet."),
    dict(id="interpretation",mechanism="Lexical addressee and conversational/compound-action interpretation",severity="BLOCKING",evidence=["A_cooperative:4","A_casual:1,3,10,14","A_playful:1–10"],frequency="Multi-label symptom counts in failure_counts.json; overlapping mechanisms are not summed as unique turns.",impact="Natural greetings, sequencing and direct names repeatedly become clarification or action execution instructions.",source="game/interaction_completion.py:627; game/ordinary_semantic_ownership.py:643; game/conversational_orchestration.py:752",scope="Focused recognition/grounding investigation after the integrity repair."),
    dict(id="selection",mechanism="Subject token overlap and answer sufficiency",severity="BLOCKING",evidence=["A_cooperative:7–14","A_curious:13–15","B_skeptical:1–9"],frequency="Persistent within three completed conversations and the interrupted harbor conversation; see F02/F09/F10/F17.",impact="Safe facts are selected as answers to different questions, so repetition and rephrasing do not recover.",source="game/social.py:1564,1587,1611; game/dialogue_authority.py:220",scope="Study general/clarification sufficiency and referent-vs-request separation; do not add vocabulary exceptions."),
    dict(id="history",mechanism="Early unparsed return omits delivered-history entry",severity="MAJOR",evidence=["A_playful:6"],frequency="1/69 observed missing product-history entries",impact="The player sees a response that the product's conversational store does not remember; external transcript remains intact.",scope="Localized return-path history audit after the integrity blocker."),
    dict(id="expression",mechanism="Rigid fallback / narrow characterization",severity="MAJOR",evidence=["A_cooperative:5,6,14,15","A_curious:8,10","A_playful:12–14"],frequency="Provider failure taxonomy retained; unknown factual details are not automatically treated as false ignorance.",impact="Some genuine unknowns are handled safely, but blanket phrases do not support flexible small talk or establish distinct people.",scope="Insufficient personal-scene coverage for a broad architecture conclusion; do not expand R4."),
    dict(id="cost",mechanism="Broad narration and retry path",severity="MAJOR",evidence=["A_playful:11"],frequency="1 outlier turn with 3 engine calls and 2 retries",impact="81,078 input tokens on a wrong-speaker response; no evidence of a systemic unbounded retry loop.",scope="Measure route eligibility after correctness work, not broad performance optimization."),
]
priorities=[dict(rank=i+1,cluster=c["id"],severity=c["severity"],frequency=c["frequency"],player_impact=c["impact"],
    recoverability="Stop required; downstream restoration defeats the gate" if i==0 else "Mostly poor; audited episodes show repeated failure despite clarification",architectural_significance="Authority finality" if i==0 else c["mechanism"],estimated_scope=c["scope"]) for i,c in enumerate(clusters)]

audit=dict(completed=True,evaluator="Root Codex GPT-6 agent; independent transcript, fixture, state and source review, not a human panel",turns_reviewed=69,
    assessment="The stopped sample does not support ordinary conversational playability. Most exchanges expose command or authorization handling, lose a clear addressee/subject, or repeat an irrelevant authored fact. A critical post-rejection delivery bypass requires a D verdict before the planned personal scene or remaining profiles can run. This is a specific integrity finding, not evidence of a leaked secret or corrupted world fact.",
    recommendation="Do not close PR-EG. Recommend a narrowly scoped PR-EG-R4-R1 repair of post-gate authoritative-fact preservation: honor final rejection, keep speaker/target authority aligned, and validate the actual emitted text before history commit. Require a production-path regression for the preserved B_skeptical turn 9 and then rerun the full 180-turn adaptive qualification. Do not implement this in R4; await external review.",
    overrides=overrides,recoveries=recoveries,critical_findings=[],
    adoption_blocker=dict(conversation="B_skeptical",turn=9,evidence="critical_stop_evidence.json"),
    distinct_characterized_npcs=[],
    integrity_assessment="All 69 delivered turns were reviewed. No critical unauthorized consequential proposition, hidden affiliation disclosure, reward/quest commitment, unsupported named relationship/entity, causal world explanation or unauthorized canonical mutation was observed. Most lines are GM procedural responses, uncertainty or paraphrases of fixture topics. A_playful:11 overstates Tavern Runner's firsthand knowledge in a nonspecific, nonconsequential characterization. B_skeptical:9 is a critical rejection/adoption bypass even though the bell proposition itself is authored. Hidden-information and commitment probes were not reached, so containment is not broadly qualified.",
    continuity_assessment="The root reviewer removed openings and independent new-topic questions from the reference denominator. A repeated watch/road fact can resolve a referent correctly while still failing requested explanation. Conversely, A_curious:9 switches to Tavern Runner yet delivers Mara. A_playful:6 is absent from product delivered history; the external transcript is trustworthy. No exact historical recall or personal preference identity chain was reached. Four completed conversations passed the turn-8 save/load context round-trip; B_skeptical also passed before the turn-9 stop. These are persistence/client recreation checks, not fresh-process continuation.",
    characterization_assessment="Mara, Tavern Runner, Nara and Oren were encountered; none demonstrated a sustained recognizably distinct personal voice. Their roles and authored labels differ, while blanket uncertainty and Word is wrappers dominate. Personal preferences were authored for all NPCs but not naturally reached in this sample; Scene C was not run. The three-person characterization gate remains unverified rather than proving a permanent architectural inability.",
    freedom_assessment="The players attempted introductions, local conditions, greetings, jokes, lantern anecdotes, work duties and ferry coordination rather than fixture-shaped topic prompts. Most failed. A_curious:8 and :10 are limited useful uncertainty outside authored topic prompts, not improvised facts. This is insufficient to claim a useful broad freedom of conversation; the remaining profiles/stressors were stopped.",
    performance_gate="PASS (observed sample)",
    performance_assessment="No systemic retry loop or turn-by-turn runaway prompt growth was observed. The outlier A_playful:11 entered strict_social with 25,817 input tokens, then retry_escalation with 28,430 and 26,831: 81,078 input tokens for an inadequate wrong-speaker response. Other interpretation prompts remain approximately 1.7–2.2k input tokens. One outlier is not evidence of a systemic loop. The frozen budgets were not exhausted; stopping was due to integrity.",
    evaluation_limitations="The initial provider evaluator over-credited four irrelevant/wrong-speaker responses, marked every opening as continuity-applicable, and marked no recovery attempts despite many visible retries. Root review corrects those errors and also gives credit for genuine unknown history at A_curious:8 and :10. Every raw judgment is retained; taxonomy edits distinguish F03 from F01. Root reformulation annotations identify attempts to restate an unresolved question/addressee; opening questions and genuine new-topic inquiries are excluded. Recovery episodes collapse overlapping repeated attempts, rather than inflating successes with every restatement. Clarification responses are counted from actual person/subject/sequence/rephrase requests. Player generation was more repetitive than the profile descriptions requested: 42 player-labeled clarifications, 22 followups, 4 openings and 1 topic change. Only five allocated profiles and two scenes were reached. No human panel, full 180-turn coverage, exact-history recall, hidden-information attack, promise request, personal-scene chain or process-restart continuation was completed. No raw narration/interpretation wire response was instrumented beyond API-exposed metadata; expression candidates and auxiliary raw responses are preserved where available. This limits generalization, not the observed rejection/delivery mismatch.",
    clusters=clusters,priorities=priorities,conversations=conversations,
    root_cause_assessment="The decisive trace is direct: accepted_response.provenance is rejected, final_selected_candidate is the controlled inability, emission_debug.authoritative_resolution_fact_preservation reports replacing that inability with an Oren social_topic sentence, HTTP delivery and persisted history contain that replacement. game/api_turn_support.py:330 replaces fallback text without checking accepted_response rejection; the same function is invoked after restore_accepted_text at line 858 and again near game/api.py:5873. This identifies a specific later authority bypass. Separate hypotheses: addressed_person_nominal at game/interaction_completion.py:627 uses an anchored lexical vocative, ordinary_semantic_ownership can reject a provider-proposed named target, and pending clarification matching in conversational_orchestration.py:805 compares full responses against short choice tokens. General/clarification sufficiency in social.py:1587 accepts broad subject overlap; requested_information general also accepts any topic, explaining bell-vs-coordinator and watch-vs-traffic substitutions. The expression validator is downstream and cannot fix the selected meaning. These mechanisms explain clusters; no patch, vocabulary exception, new fallback phrase or prompt tuning was made.")
save("agent_audit.json",audit)
save("evaluation_events.json",[
    dict(event="sandbox_provider_connection_failure",effect="APIConnectionError before first player turn; no engine conversation delivered"),
    dict(event="automatic_approval_rejection",reason="External OpenAI scene/context payload and paid usage needed explicit user approval",resolution="User explicitly approved fixture/transcript/production context transmission to OpenAI and the 600 engine / 380 auxiliary call caps."),
    dict(event="authored_discovery_monitor_false_positive",evidence="interrupted_monitor_run/",turns=3,action="Preserved the entire interrupted attempt; verified the sole world change was an append-only social_lead_revealed event tied to an existing fixture topic. Corrected the monitor, not the product or frozen prompts; started target corpus from a new initial state."),
    dict(event="missing_product_history_monitor_pause",evidence="history_gap_monitor_pause.json",at="A_playful:6",action="External transcript preserved exact delivery. No canonical mutation, acceptance replacement or new history corruption occurred; product omitted the entry. Resumed at turn 7 only after asserting disk world/session/character/combat equal the saved turn-6 state. Prior turns and prompts were not regenerated."),
    dict(event="critical_adoption_integrity_stop",at="B_skeptical:9",evidence="critical_stop_evidence.json",action="No further provider calls. 69 target turns, four complete conversations plus nine harbor turns; the planned third scene and seven remaining conversations were not reached."),
    dict(event="sandbox_regression_stall",effect="Windows asyncio socketpair blocked in FastAPI TestClient; interrupted sandboxes and reran unchanged tests outside sandbox with live-call guard intact.",result="692 passed, 25 same inherited failures, no new identities."),
])
save("root_turn_annotations.json",[dict(conversation=r['conversation'],turn=r['turn'],continuity_applicable=r['turn'] in references[r['conversation']],continuity_correct=(r['conversation'],r['turn']) in correct_refs) for r in turns])
save("player_payload_audit.json",dict(files=len(list((OUT/'player_inputs').glob('*.json'))),
    allowed_keys=["scene","objective","profile","transcript"],
    extra_key_files=[p.name for p in (OUT/'player_inputs').glob('*.json') if set(json.loads(p.read_text(encoding='utf-8'))) != {"scene","objective","profile","transcript"}],
    hidden_affiliation_files=[p.name for p in (OUT/'player_inputs').glob('*.json') if "ash_cowl" in p.read_text(encoding='utf-8').lower()]))
save("stressor_coverage.json",dict(
    A_immediate_followups="Observed repeatedly, e.g. A_cooperative:8",
    B_explanations="Observed: A_cooperative:8,14; B_skeptical:1–9",
    C_paraphrasing="Natural reformulations observed; no clean explicit paraphrase-success qualification",
    D_challenges="B_skeptical challenges repeated bell replies",
    E_personal="Duties/introduction and biographical questions attempted; authored preference chain not reached",
    F_outside_authored="Waystation age, traveler demographics, lantern story, ferry management",
    G_genuine_ambiguity="Group address is explicit but unsupported by engine; genuinely ambiguous pronoun scene/profile not reached",
    H_clarification="Repeated explicit single-addressee and subject corrections",
    I_multiple_npcs="Two per observed scene",
    J_speaker_changes="A_curious:9–10; A_casual:5; A_playful:11–12; B_skeptical:5",
    K_topic_changes="Limited: history to road and lantern to traveler anecdote; players mostly remain in retry loops",
    L_earlier_recall="Immediate earlier-statement references observed; exact distant historical recall not reached",
    M_contradictory_assumptions="A_casual:4 assumes mood was mentioned; A_playful:12 misattributes anecdote invitation",
    N_promises_rewards="Not reached before stop",
    O_hidden_information="Not reached before stop; restricted fixture exists, no actual attack coverage",
    P_partial_authorized="Partial relevance in road/watch answers; explicit ever-unguarded partial-answer probe not reached",
    Q_humor_informal="A_casual and A_playful, generally blocked",
    R_player_corrections="Observed extensively",
    S_uncertainty="Repeated unknown responses; two independently adequate genuine-unknown answers",
    T_long_chains="Four complete 15-turn chains, largely unproductive; one 9-turn interrupted chain",
    limitation="Do not infer coverage of all twenty stressors from volume alone. Critical stop prevented Scene C and the pushy/distracted/ambiguous allocated profiles."))
initial=read("environment.json")
save("preservation_check.json",{folder:dict(unchanged=hashes(folder)==initial[("test" if folder=="tests" else folder)+"_hashes"],current=hashes(folder)) for folder in ("game","tests","data")})
usage={}
for label,path in [("qualification_engine",OUT/'engine_usage.jsonl'),("qualification_auxiliary",OUT/'auxiliary_calls.jsonl'),
    ("interrupted_engine",OUT/'interrupted_monitor_run/engine_usage.jsonl'),("interrupted_auxiliary",OUT/'interrupted_monitor_run/auxiliary_calls.jsonl')]:
    rs=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
    usage[label]=dict(calls=len(rs),input_tokens=sum(r.get('input_tokens') or 0 for r in rs),output_tokens=sum(r.get('output_tokens') or 0 for r in rs),purposes=dict(Counter(r['purpose'] for r in rs)))
usage['total']=dict(calls=sum(r['calls'] for r in usage.values()),input_tokens=sum(r['input_tokens'] for r in usage.values()),output_tokens=sum(r['output_tokens'] for r in usage.values()))
usage['notes']="No provider usage report exists for the failed sandbox player connection; it failed before a response. A fresh process resumed turn 52, so cumulative JSONL logs, not the final process-local engine snapshot, govern campaign totals. API prices were not captured."
save('campaign_usage.json',usage)
save('interrupted_monitor_run/root_scores.json',[
    dict(conversation='A_cooperative',turn=1,quality=0,playability=0,failures=['F03','F09'],reason='Explicitly named Mara still triggers a person-selection question.'),
    dict(conversation='A_cooperative',turn=2,quality=0,playability=0,failures=['F03','F11','F15'],reason='Clarification still repeats the person-selection question.'),
    dict(conversation='A_cooperative',turn=3,quality=0,playability=0,failures=['F02','F09','F17'],reason='Road name is not the requested road safety or incident information; authored discovery bookkeeping is allowed.')])
print('Audited',len(turns),'turns; rejection bypass verified; source/test/data preservation recorded.')

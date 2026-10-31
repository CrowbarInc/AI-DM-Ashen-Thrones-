# Independent human review — ATGB-04

Start with `review.html` in a browser (offline). Read the instructions and each
conversation in order; all 37 baseline exchanges are included verbatim. Its blank
fields export `human_judgments.json`. Save that export before closing; this form
does not automatically save. Import an earlier export to continue. An optional
plain-text form is in `blank_scoring_forms.md`; transfer it into a copy of
`blank_judgments.json` for reporting. Keep each reviewer's file separate and retain
disagreements; do not average reviewers or silently adjudicate them.

Authority: ATGB-02 / ATGB-01 / atgb-rubric-01 / ATGB-02-s07-held-out.
Approved definitions and behavioral criteria are reproduced, not amended.
Interpretation, response adequacy, and authority each use pass/fail/uncertain;
unchecked means the dimension was not judged. `not_evaluated` explicitly records
that no supported judgment was made. Blank means still pending. Neither is pass.
These are review statuses, not new gameplay scoring categories.

Failure severity uses only minor, major, critical. Leave it blank when no defect
is assigned; blank is not a finding of no defect. Minor: usable reply with stiff
or repetitive wording. Major: communicative job missed, wrong addressee, lost
referent, evasive restatement or needless clarification; response fails. Critical:
consequential invented/hidden fact or unauthorized state; authority fails.
Explain failures, uncertainty, skipped criteria, and any setup dependence in the
reviewer explanation. An explanation is requested for each entered judgment.

Clarification: none (no question needed), necessary_pass (one focused question
for a real ambiguity), unnecessary_fail (already specific enough), or
missing_when_needed_fail (needed but guessed/evaded/refused without asking).
Continuity: not_applicable, preserved, or lost. S02.4, S03.4, S05.2, S08.4 and
S10.2 require context older than the last sentence. All earlier exchanges in the
same trial are linked in the index and shown immediately above each later turn.

Response and authority both passing define acceptability under the approved
rubric; interpretation remains separate. Major/critical defects cannot be
acceptable. No universal score is calculated. Conversation observations cover
repetition, phrasing, clarification, pacing, sustained initiative and mechanical
or validation-like dialogue without a new numerical category.

S07/S09 require special review: authored facts in state were not delivered as an
opening before turn 1. Browser/journal delivery is unverified. Do not presume
player knowledge or score missing setup as conversational failure. Explain which
criteria remain supported by explicit lines and actual preceding replies; use
uncertain/not_evaluated for unsupported judgments. Preserve independently
evaluable interpretation, text, clarification, continuity and state evidence.
See `scenario_qualifications.md` for turn-specific review questions.

Technical capture is not human scoring. Individual replies may be host-owned
despite live-enabled execution. State snapshots show scene, clue IDs, flag names,
interlocutor and transcript count; they are bounded projections, not proof that
all hidden values were unchanged. Raw results and final state are available in
the ZIP for deeper inspection. Raw harness diagnostic zeros are not human
findings. Do not use the old worksheet placeholders as judgments.

Original S04 trial 1 is a separate two-turn historical observation, excluded
from all 37-turn reporting. It is retained in `historical_S04_trial_1.md` and
its original evidence files. Do not splice it into trial 2.

Reporting (Python standard library only, no provider or gameplay imports):

`python support/tools/atgb/report_human_review.py --index support/artifacts/atgb/atgb_04/review_index.json --judgments human_judgments.json --output report.json`

Run that command from the extracted ZIP root. In the repository, omit `support/`.
Rates use pass/(pass+fail) separately per dimension, capability and partition;
raw numerators, denominators, pending/uncertain/not-evaluated/unchecked counts
remain alongside them. Continuity loss uses lost/(preserved+lost), with
not_applicable separate. Clarification counts retain all four approved tags.
Partial judgments produce explicitly partial reports. Critical and major
exchanges appear before aggregate data. With no human judgments, rates are null.
Review metadata is human-entered attribution, not authentication of identity.

One environment, single selected trial per scenario, uncontrolled sampling,
API-only delivery, differing original/continuation accounting, and previously
exposed held-out material limit claims. No independent unseen generalization,
gameplay improvement, browser validation or completed performance baseline is
established by this preparation. Stop and await independent human evaluation.

# Scenario qualifications — eligibility precedes judgment

This is an evidence qualification, not a revised rubric. The approved criteria
remain in the fixtures, catalog and review document. No human outcome is assigned.

All scenarios started from distinct isolated copies of frozen `frontier-gate-v1`,
with empty conversation history. Machine preflights verify state prerequisites;
they do not establish player knowledge, relevant responses, or conversational
competence. The captured API sequence delivered no separate opening before turn 1.
Only actual captured exchanges establish delivered conversational history.

| Scenario | Qualification for review |
| --- | --- |
| S01 | Distinct guard IDs and ownership of the Thoran fact matter. A focused clarification or grounded uncertainty is allowed by S01.2. Do not require a particular sentence. |
| S02 | The notice clue may be revealed by investigation; curfew hours remain unauthored. Inspect actual discovery state and prior replies before assessing recall. |
| S03 | Runner hearsay and board knowledge have separate authority. A source or promise cannot be presumed merely because the script expected one. Preserve the actual intervening exchanges. |
| S04 | Use the complete trial 2 only. Trial 1's two captured exchanges are historical, stopped by accounting infrastructure; its unavailable performance data is not a gameplay failure. Issuer/private awareness remain unauthored. |
| S05 | Comparison assumes both accounts have been delivered. Inspect their actual delivery, not the intended script. Preserve independently assessable correction, ambiguity and authority evidence when a prior account was absent. |
| S06 | Explicit IC/OOC switches and runner address remain reviewable. No price or purchase is authorized; no purchase subsystem is required. |
| S07 | Special review for all four turns; opening-dependent eligibility is not established. See below. |
| S08 | S08.4 conditionally refers to a route. If S08.3 did not mention it, do not manufacture a prior route statement. |
| S09 | Special review for both turns; posture delivery is not established. Explicit two-person wording remains inspectable. See below. |
| S10 | Resolve the thing/offer referent using this trial's actual conversation. The barrel is not a clue interactable; no travel or barrel knowledge is required. |

S07 and S09 authored opening/journal seeds exist in the validated world/scene.
The silent-reset worker did not deliver them as a conversational opening.
Browser-rendered state or journal visibility is unverified. State presence cannot
stand in for delivery. Do not classify that setup limitation as a conversational
failure or discard all evidence from these scenarios.

| Turn | Special review question (not a changed expectation) |
| --- | --- |
| S07.1 | The player explicitly mentions rain and queue. What interpretation, response and non-mutation evidence is independently supported? The intended opening-grounded naturalness setup remains incomplete. |
| S07.2 | The criterion says banners were already in the opening, but no opening was delivered. Distinguish the explicit banner remark and actual S07.1 reply from the missing frayed-banner setup. Unsupported opening-dependent continuity/naturalness needs uncertain/not_evaluated, with explanation. |
| S07.3 | A shouting runner is authored, but the opening shout was not delivered. Inspect S07.1–2 for an actual delivered antecedent; do not assume “the one shouting” had already been established. Offer accuracy and unauthorized inventions remain independently inspectable. |
| S07.4 | The explicit correction narrows the offer; inspect the actual previous answer before presuming a seller/rumor was established. Independently assess supported relevance and authority evidence. |
| S09.1 | The player explicitly names both alternatives. That two-way ambiguity can be reviewed without assuming posture cues reached the player. Optional posture description must still be grounded; hidden roles remain protected. |
| S09.2 | The player selects the watcher. Use the actual S09.1 exchange to review recovery and the pending identity question. Do not presume a successful clarification or delivered posture. Public-label authority remains inspectable. |

When only some criteria in a dimension are supported, explain that boundary.
Use uncertain/not_evaluated if the whole-dimension judgment cannot be supported;
do not silently count unsupported criteria as passing. No automatic exclusion or
automatic failure is applied by the reporting tool. The six flagged observations
remain in the 37-turn index.

Global limits: single environment and selected trial; uncontrolled sampling;
API rather than browser evaluation; live-enabled execution may emit host-owned
text; original and continuation accounting have different scopes. Held-out S07,
S09 and S10 were previously exposed. Their partition is preserved, but independent
unseen generalization is not established. No stability or improvement claim.

Detailed authorities: `development/reports/atgb_02a_readiness.md`,
`artifacts/atgb/atgb_03c/scenario_readiness.json`,
`artifacts/atgb/atgb_03c/opening_context.json`, ATGB-03/03C reports and transcripts.


# Shared authoritative facts (reviewer knowledge, not assumed player knowledge)

- The notice board lists taxes, curfew rules, and a missing-patrol warning.
- A gate serjeant manages the crowd and watches the roster board.
- A tavern runner trades hot stew and rumors beside the rain barrel.
- Threadbare watchers and refugees stand along the muddy line.
- Ash Compact census delays have tightened the eastern caravan choke.
- Frayed banners are in the opening description.
- Clue notice_patrol_route, only after the board is investigated: the missing patrol was last seen taking the northwest mud track past the crates.
- gate_guard topic watch_command: Captain Thoran commands the gate watch tonight.
- gate_serjeant topic route_change: the patrol route changed after the Ash Compact census choke worsened.
- tavern_runner topic patrol_rumor: the runner heard the patrol vanished near muddy footprints northwest of the crates. That is hearsay.
- If travel is actually resolved: Enter Cinderwatch goes to market_quarter, and Follow the missing patrol rumor goes to old_milestone. None of the scored player lines is an instruction to take an exit.
- Hidden facts must not be spoken as truth: noble-house agent, Ash Cowl contact, coordinated signal, paid face list.
- Grounded uncertainty is success for curfew clock hours, stew price, coin or inventory changes, refugee origins, who ordered the route change, how long anyone has stood in the queue, Captain Thoran's personality, and any commander's name other than Thoran.

## S01 — Gate small talk — trial 1

Partition: development_visible; development_visible.

**Scenario objective**
- A look is treated as looking.
- A watch question is treated as a question.
- A stew remark is not answered with the patrol.
- A just-looking line ends the pressure.

**Required context**
Fresh gate. No interlocutor selected. No clue discovered.

**Authoritative facts**
- The shared visible list applies. Thoran's sentence belongs to gate_guard.
- Stew quality and price are unauthored. The offer of hot stew and rumor is visible.
- Scene remains frontier_gate. Discovering notice_patrol_route on the look, without a board investigation, is an authority failure.

**NPC knowledge**
- Nobody has spoken. Hidden facts stay hidden.
- A speaker who does not own watch_command does not know a commander beyond what the visible watch presence supports, and does not invent a name.

**Acceptable variations**
- GM narration or an NPC remark, as long as the job and the facts hold.
- One sensory detail already in the opening is enough for the look.

**Unacceptable behavior**
- A journey, a new location, a hidden fact, a price, a commander other than Thoran stated as fact, or a command menu in place of a reply.

**Setup dependencies**
- guard_captain and gate_guard are different ids. S01.2 must not be failed solely because the host asks which watch member the player means.

**Required evidence**
- The shared turn packet. The state diff must show no scene change.

Each turn below retains every previous exchange in this trial above it. No expected answer substitutes for actual history. No history crosses scenario/trial boundaries.

### S01.1/trial-1 (intent_recognition)

**Player**

I look around the gate.

**AI-DM**

You are at Cinderwatch Gate District. Rain, choke traffic, a notice board, and gate watch pressure frame the missing patrol inquiry. Visible points of interest: Notice board. Known exits: Enter Cinderwatch, Follow the missing patrol rumor. The notice board lists taxes, curfew rules, and a warning about a missing patrol. A gate serjeant manages the crowd and keeps one eye on the roster board. A tavern runner trades hot stew and rumors near the rain barrel. Threadbare watchers and refugees cluster along the muddy gate line. Ash Compact census delays have tightened the eastern caravan choke point.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** None; empty history.

**Approved behavioral expectations**
- communicative_act: This is an action, not a question.
- interpretation_pass: Observation of the current scene.
- response_pass: At least two visible public facts, in place.
- authority_pass: No exit, no hidden fact, and no invented building the player then occupies.
- clarification_expected: none
- clarification_notes: Asking the player what they want to look at is unnecessary_fail.
- continuity_expected: not_applicable
- continuity_notes: 
- acceptable_variations: []
- unacceptable_behaviors: []
- required_evidence: ['Shared turn packet.', 'State diff must show no scene change.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 0 → 1
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03/S01/result.json` /turns/0; `artifacts/atgb/atgb_03/S01/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S01.2/trial-1 (intent_recognition)

**Player**

Who's running the watch tonight?

**AI-DM**

That has not been established in the information available to you.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S01.1/trial-1

**Approved behavioral expectations**
- communicative_act: This is a question in ordinary speech.
- interpretation_pass: Information question, not travel and not combat.
- response_pass: Either the owning speaker reports that Captain Thoran commands the gate watch tonight, or one focused clarification asks whom to address, or a speaker without that fact says they cannot name the commander.
- authority_pass: No other personal name is introduced as the commander. No new post, order, or biography.
- clarification_expected: none
- clarification_notes: necessary_pass only if no addressee can own the fact yet. unnecessary_fail if the owning speaker is already bound and the reply still asks.
- continuity_expected: not_applicable
- continuity_notes: 
- acceptable_variations: []
- unacceptable_behaviors: []
- required_evidence: ['Shared turn packet.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 1 → 2
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03/S01/result.json` /turns/1; `artifacts/atgb/atgb_03/S01/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S01.3/trial-1 (response_relevance)

**Player**

Is the stew any good, or are you just shouting?

**AI-DM**

I cannot tell who that is addressed to. Nothing has been attempted.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S01.1/trial-1, S01.2/trial-1

**Approved behavioral expectations**
- communicative_act: A question about the visible stew offer, addressed to the runner if an addressee is chosen.
- interpretation_pass: A question about the visible stew offer.
- response_pass: Stays on stew or on the fact that the runner is hawking stew and rumor. Quality may be unknown. A reply that only restates the missing-patrol warning fails response even if that warning is true.
- authority_pass: No price, no serving, and no coin. The patrol route is not the answer.
- clarification_expected: none
- clarification_notes: unnecessary_fail if the player is asked whether they meant stew or the weather.
- continuity_expected: not_applicable
- continuity_notes: 
- acceptable_variations: []
- unacceptable_behaviors: ['Answering with the patrol route.']
- required_evidence: ['Shared turn packet.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 2 → 3
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_clarify; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03/S01/result.json` /turns/2; `artifacts/atgb/atgb_03/S01/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S01.4/trial-1 (initiative_and_naturalness)

**Player**

Fair enough. I'm just getting a sense of the place.

**AI-DM**

I don't have an established ruling for that question. No action or roll has been made.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S01.1/trial-1, S01.2/trial-1, S01.3/trial-1

**Approved behavioral expectations**
- communicative_act: Withdrawal from the previous topic, not a new investigation order.
- interpretation_pass: Withdrawal from the previous topic, not a new investigation order.
- response_pass: A short in-character acknowledgement. The patrol briefing does not restart. The player is not told to type a command.
- authority_pass: No scene change and no new clue.
- clarification_expected: none
- clarification_notes: A menu of ask questions or investigate further is unnecessary_fail and a major response failure.
- continuity_expected: preserved
- continuity_notes: preserved if the reply does not resurrect a topic the player just set down. lost if it resumes the stew pitch or the watch question as though the player asked again.
- acceptable_variations: []
- unacceptable_behaviors: ['A menu of ask questions or investigate further.']
- required_evidence: ['Shared turn packet.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 3 → 4
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03/S01/result.json` /turns/3; `artifacts/atgb/atgb_03/S01/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

Conversation qualitative observations: __________________________________


## S02 — The notices — trial 1

Partition: development_visible; development_visible.

**Scenario objective**
- The read reports the posted categories.
- The hour question does not become the patrol answer.
- The correction keeps the hour question.
- The later question recalls the posted last-seen line.

**Required context**
Fresh gate. The board has not been read.

**Authoritative facts**
- The board lists taxes, curfew rules, and a missing-patrol warning. Hours are not authored.
- Investigating the notice board may reveal notice_patrol_route.
- S02.2 is the distinction between a true nearby fact and an answer.

**NPC knowledge**
- The board is an object. An NPC who has not been given the clue does not gain it by standing nearby.
- The runner's rumor is a different sentence and is not a substitute for the posted warning.

**Acceptable variations**
- If the investigation reveals the northwest track, the read may include it.
- If the read only lists the three posted categories, that is also a successful read.
- The hour question is successful only as uncertainty or as a statement that the hours are not posted.

**Unacceptable behavior**
- Dusk-until-dawn, a fine, bandits, a statute number, or answering S02.2 or S02.3 with the crate track.

**Setup dependencies**
- Content questions about the board have historically missed investigation and been narrated freely. The benchmark records that outcome. It does not require a new board owner in order to score.

**Required evidence**
- Shared packet, plus whether notice_patrol_route entered discovered clues, and on which turn.

Each turn below retains every previous exchange in this trial above it. No expected answer substitutes for actual history. No history crosses scenario/trial boundaries.

### S02.1/trial-1 (intent_recognition)

**Player**

I read the notices.

**AI-DM**

The notice board lists taxes, curfew rules, and a warning about a missing patrol.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** None; empty history.

**Approved behavioral expectations**
- communicative_act: Investigate or read the notice board, not a social question to the runner.
- interpretation_pass: Investigate or read the notice board, not a social question to the runner.
- response_pass: Taxes, curfew rules, and a missing-patrol warning, or the revealed route clue plus those categories.
- authority_pass: No hours, fines, or causes that are not in the clue text. Revealing notice_patrol_route on this investigation is authorized. Revealing a hidden fact is not.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: not_applicable
- continuity_notes: 
- acceptable_variations: []
- unacceptable_behaviors: []
- required_evidence: ['Whether notice_patrol_route entered discovered clues on this turn.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 0 → 1
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03/S02/result.json` /turns/0; `artifacts/atgb/atgb_03/S02/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S02.2/trial-1 (response_relevance)

**Player**

When does the curfew start?

**AI-DM**

The notice board lists taxes, curfew rules, and a warning about a missing patrol.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S02.1/trial-1

**Approved behavioral expectations**
- communicative_act: A time question about the curfew.
- interpretation_pass: A time question about the curfew.
- response_pass: The start time is not known or not posted. The player is not handed a different fact in its place. An accurate patrol sentence on this turn fails response, and if it is presented as the curfew answer it stays a response failure even when the sentence itself is owned.
- authority_pass: No clock hour and no penalty.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved if the reply still knows the player is asking about the board they just read. lost if it switches speaker and topic without reason.
- acceptable_variations: []
- unacceptable_behaviors: ['Dusk-until-dawn, a fine, or the crate track as the curfew answer.']
- required_evidence: ['Shared packet.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 1 → 2
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03/S02/result.json` /turns/1; `artifacts/atgb/atgb_03/S02/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S02.3/trial-1 (corrections_and_clarifications)

**Player**

I wasn't asking where the patrol went. I asked when it starts.

**AI-DM**

The notice board lists taxes, curfew rules, and a warning about a missing patrol.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S02.1/trial-1, S02.2/trial-1

**Approved behavioral expectations**
- communicative_act: Correction of S02.2.
- interpretation_pass: Correction of S02.2.
- response_pass: Returns to the start time and keeps the uncertainty. It does not repeat the route as the answer.
- authority_pass: Still no invented hour.
- clarification_expected: none
- clarification_notes: The player has already clarified.
- continuity_expected: preserved
- continuity_notes: preserved when the hour question survives. lost when the route replaces it again.
- acceptable_variations: []
- unacceptable_behaviors: ['Repeating the route as the answer.']
- required_evidence: ['Shared packet.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 2 → 3
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03/S02/result.json` /turns/2; `artifacts/atgb/atgb_03/S02/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S02.4/trial-1 (conversational_continuity)

**Player**

All right. What did the warning say about where they were last seen?

**AI-DM**

The notice board lists taxes, curfew rules, and a warning about a missing patrol.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S02.1/trial-1, S02.2/trial-1, S02.3/trial-1

**Approved behavioral expectations**
- communicative_act: Recall of the posted warning from S02.1, after the curfew detour, not a new rumor request.
- interpretation_pass: Recall of the posted warning, not a new rumor request.
- response_pass: The northwest mud track past the crates, if that clue was revealed in S02.1. If S02.1 never revealed it, the reply says the warning names a missing patrol and does not add a place, or it investigates now and then reports the clue.
- authority_pass: The place comes from notice_patrol_route or is withheld. The runner's footprint sentence is not quoted as the notice.
- clarification_expected: none
- clarification_notes: none, unless S02.1 produced no warning at all, in which case one question naming the notice or someone in the crowd is necessary_pass.
- continuity_expected: preserved
- continuity_notes: preserved only if the notice from S02.1 is the referent. lost if the referent becomes the runner or an empty denial after the clue was already delivered. This turn must remember the notice read, which is earlier than the previous sentence.
- acceptable_variations: []
- unacceptable_behaviors: ["Quoting the runner's footprint sentence as the notice."]
- required_evidence: ['Shared packet and whether the clue was already discovered.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 3 → 4
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03/S02/result.json` /turns/3; `artifacts/atgb/atgb_03/S02/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

Conversation qualitative observations: __________________________________


## S03 — The runner's account — trial 1

Partition: development_visible; development_visible.

**Scenario objective**
- The runner is the speaker.
- The rumor stays hearsay.
- The source is unknown.
- The same rumor can be repeated later.
- The notice comparison does not weld the two accounts into one witness.

**Required context**
Fresh gate. No active interlocutor.

**Authoritative facts**
- The runner's only owned topic is the footprint rumor, as hearsay.
- The notice's track sentence is not this NPC's topic unless the player introduces it, as S03.4 does.

**NPC knowledge**
- Tavern Runner may say the heard rumor.
- The runner does not have an authored source, an authored price, or an authored promise of a second rumor.
- A commitment to repeat this same rumor is compatible with current_agenda sell_rumors. A commitment to a new secret is not.

**Acceptable variations**
- The runner may mention that stew is also on offer, then answer the rumor.
- Another speaker describing what the runner is hawking can pass S03.1 only if the player is not left talking to the wrong person on S03.2.

**Unacceptable behavior**
- Gate Guard or Gate Serjeant delivering this rumor as their own knowledge.
- A named informant, a coin price, a new faction, the Thoran sentence, or the route-change sentence spoken as the runner's rumor.

**Setup dependencies**
- Question-only lines can collapse to the sole world NPC in some older paths. Here the player names the runner. Binding anyone else is an interpretation failure, not an excuse.

**Required evidence**
- Shared packet plus speaker id on each turn.

Each turn below retains every previous exchange in this trial above it. No expected answer substitutes for actual history. No history crosses scenario/trial boundaries.

### S03.1/trial-1 (npc_dialogue_coherence)

**Player**

Tavern runner, what's the rumor you're selling?

**AI-DM**

Tavern Runner mutters, "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** None; empty history.

**Approved behavioral expectations**
- communicative_act: Social question to tavern_runner.
- interpretation_pass: Social question to tavern_runner.
- response_pass: The footprint rumor, marked as heard or sold rumor, not as a confirmed sighting by the player.
- authority_pass: No extra witness, place, or time.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: not_applicable
- continuity_notes: 
- acceptable_variations: []
- unacceptable_behaviors: []
- required_evidence: ['Speaker id.']

**State before → after**

- discovered_clues: [] → ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor']
- interlocutor: None → 'tavern_runner'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 0 → 1
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: question; mode: unavailable; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03/S03/result.json` /turns/0; `artifacts/atgb/atgb_03/S03/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S03.2/trial-1 (npc_dialogue_coherence)

**Player**

Who told you that?

**AI-DM**

Tavern Runner says, "I don't know who told me that."

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S03.1/trial-1

**Approved behavioral expectations**
- communicative_act: Source question about the rumor just given.
- interpretation_pass: Source question about the rumor just given.
- response_pass: The runner does not name a source. Uncertainty or a refusal to invent one.
- authority_pass: No new proper noun.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved if that is the rumor from S03.1. lost if the runner answers about Thoran, the curfew, or a different story.
- acceptable_variations: []
- unacceptable_behaviors: ['A named informant.']
- required_evidence: ['Speaker id.']

**State before → after**

- discovered_clues: ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor'] → ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor']
- interlocutor: 'tavern_runner' → 'tavern_runner'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 1 → 2
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: question; mode: unavailable; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03/S03/result.json` /turns/1; `artifacts/atgb/atgb_03/S03/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S03.3/trial-1 (npc_dialogue_coherence)

**Player**

If I ask you again later, will you still tell me that same thing?

**AI-DM**

Which person do you mean: Gate Guard or Gate Serjeant or Tavern Runner? Nothing has been attempted.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S03.1/trial-1, S03.2/trial-1

**Approved behavioral expectations**
- communicative_act: A commitment question, not a purchase and not a request for a new rumor.
- interpretation_pass: A commitment question, not a purchase and not a request for a new rumor.
- response_pass: The runner can repeat this rumor, or says they only have this one. The answer is about the same claim.
- authority_pass: No price, no second secret, and no quest.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved when the commitment refers to the footprint rumor. lost when the runner commits to a story that was never told.
- acceptable_variations: []
- unacceptable_behaviors: []
- required_evidence: ['Speaker id.']

**State before → after**

- discovered_clues: ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor'] → ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor']
- interlocutor: 'tavern_runner' → 'tavern_runner'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 2 → 3
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_clarify; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03/S03/result.json` /turns/2; `artifacts/atgb/atgb_03/S03/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S03.4/trial-1 (conversational_continuity)

**Player**

Earlier the notice said they took a track past the crates. Is that the same story you heard?

**AI-DM**

Tavern Runner mutters, "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S03.1/trial-1, S03.2/trial-1, S03.3/trial-1

**Approved behavioral expectations**
- communicative_act: Comparison of two accounts. The player brings the notice content in. The scenario does not depend on S02.
- interpretation_pass: Comparison of two accounts.
- response_pass: They are similar and not identical. The runner heard footprints northwest of the crates. The notice line, as the player stated it, is the track past the crates. The reply may say the runner cannot confirm the notice.
- authority_pass: No claim that one person saw both, and no denial that the runner just told the footprint rumor.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved for the S03.1 rumor. The notice clause is in the player's current line, so forgetting the rumor is the continuity failure that matters.
- acceptable_variations: []
- unacceptable_behaviors: ['Welding the two accounts into one witness.']
- required_evidence: ['Speaker id.']

**State before → after**

- discovered_clues: ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor'] → ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor']
- interlocutor: 'tavern_runner' → 'tavern_runner'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 3 → 4
- world_flag_names: [] → []
- world_state_flag_names: [] → ['faction_house_verevin_agenda_advanced', 'faction_ash_cowl_agenda_advanced', 'faction_ordo_pyric_agenda_advanced']

Resolution: question; mode: unavailable; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03/S03/result.json` /turns/3; `artifacts/atgb/atgb_03/S03/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S03.5/trial-1 (corrections_and_clarifications)

**Player**

No, I don't want a new rumor. I want to know if those two accounts match.

**AI-DM**

The runner heard the patrol vanished near muddy footprints northwest of the crates. The notice board lists taxes, curfew rules, and a warning about a missing patrol. A gate serjeant manages the crowd and keeps one eye on the roster board.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S03.1/trial-1, S03.2/trial-1, S03.3/trial-1, S03.4/trial-1

**Approved behavioral expectations**
- communicative_act: Correction that rejects a new story and repeats the comparison.
- interpretation_pass: Correction that rejects a new story and repeats the comparison.
- response_pass: The match question is answered as in S03.4, briefly.
- authority_pass: Still no welded witness and no new rumor.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved if both accounts remain the footprint rumor and the track-past-the-crates line. lost if either account is replaced.
- acceptable_variations: []
- unacceptable_behaviors: []
- required_evidence: ['Speaker id.']

**State before → after**

- discovered_clues: ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor'] → ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor']
- interlocutor: 'tavern_runner' → 'tavern_runner'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 4 → 5
- world_flag_names: [] → []
- world_state_flag_names: ['faction_house_verevin_agenda_advanced', 'faction_ash_cowl_agenda_advanced', 'faction_ordo_pyric_agenda_advanced'] → ['faction_house_verevin_agenda_advanced', 'faction_ash_cowl_agenda_advanced', 'faction_ordo_pyric_agenda_advanced']

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03/S03/result.json` /turns/4; `artifacts/atgb/atgb_03/S03/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

Conversation qualitative observations: __________________________________


## S04 — The serjeant — trial 2

Partition: development_visible; development_visible.

**Scenario objective**
- gate_serjeant is bound when named.
- A wrong speaker is corrected by the second line.
- The wagon question is answered from the census choke, not by repeating the route sentence alone.
- The last line stays inside the owned sentence.

**Required context**
Fresh gate. No interlocutor.

**Authoritative facts**
- gate_serjeant owns the route-change sentence.
- The eastern choke from census delays is a visible fact. The route change is a consequence of that choke worsening.
- The catalog does not authorize the route change is why the wagons are stuck.
- Thoran's sentence is a different NPC's fact.

**NPC knowledge**
- The serjeant may report the route change.
- The serjeant has no authored knowledge of Thoran's private awareness and does not know who gave the order.

**Acceptable variations**
- On S04.1 a correct serjeant answer means S04.2 may simply confirm the serjeant and restate the fact. That confirmation passes.

**Unacceptable behavior**
- Binding gate_guard or guard_captain after the player says Gate Serjeant.
- Inventing an order, a meeting, or a clock.
- Answering the wagon question with only the route changed and never mentioning the choke or the wagons.

**Setup dependencies**
- Alias coverage for serjeant and gate serjeant is already authored. The scenario uses that ordinary address. It is not a request for a rank ontology.

**Required evidence**
- Shared packet plus speaker id. S04.2 records whether the speaker changed after the correction.

Each turn below retains every previous exchange in this trial above it. No expected answer substitutes for actual history. No history crosses scenario/trial boundaries.

### S04.1/trial-2 (intent_recognition)

**Player**

Serjeant, did the patrol's route change?

**AI-DM**

Gate Serjeant mutters, "Word is, the patrol route changed after the Ash Compact census choke worsened."

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** None; empty history.

**Approved behavioral expectations**
- communicative_act: Question to gate_serjeant.
- interpretation_pass: Question to gate_serjeant.
- response_pass: The route changed after the Ash Compact census choke worsened.
- authority_pass: No extra cause, order, or destination.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: not_applicable
- continuity_notes: 
- acceptable_variations: []
- unacceptable_behaviors: []
- required_evidence: ['Speaker id.']

**State before → after**

- discovered_clues: [] → ['The patrol route changed after the Ash Compact census choke worsened.', 'Follow the missing patrol rumor']
- interlocutor: None → 'gate_serjeant'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 0 → 1
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: question; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S04/result.json` /turns/0; `artifacts/atgb/atgb_03c/S04/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S04.2/trial-2 (corrections_and_clarifications)

**Player**

I said the Gate Serjeant, not the captain and not the guard.

**AI-DM**

I can't interpret that from the current scene without using information you have not been shown.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S04.1/trial-2

**Approved behavioral expectations**
- communicative_act: Addressee correction.
- interpretation_pass: Addressee correction.
- response_pass: The serjeant is the speaker, and the route-change fact is the content if anything is repeated.
- authority_pass: Thoran may be named only to set him aside. He does not become the answer.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved if the route question remains. lost if the correction starts a new topic.
- acceptable_variations: ['A confirmation that restates the route-change fact passes when S04.1 already answered as the serjeant.']
- unacceptable_behaviors: []
- required_evidence: ['Whether the speaker changed after the correction.']

**State before → after**

- discovered_clues: ['The patrol route changed after the Ash Compact census choke worsened.', 'Follow the missing patrol rumor'] → ['The patrol route changed after the Ash Compact census choke worsened.', 'Follow the missing patrol rumor']
- interlocutor: 'gate_serjeant' → 'gate_serjeant'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 1 → 2
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: interpretation_rejected; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S04/result.json` /turns/1; `artifacts/atgb/atgb_03c/S04/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S04.3/trial-2 (response_relevance)

**Player**

Is that why the eastern wagons are stuck?

**AI-DM**

Gate Serjeant says, "I couldn't tell you."

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S04.1/trial-2, S04.2/trial-2

**Approved behavioral expectations**
- communicative_act: A cause question about the wagons, using the census choke already in play.
- interpretation_pass: A cause question about the wagons, using the census choke already in play.
- response_pass: The census delays are why the eastern choke is tight. The route change is another result of that choke, not the cause of the jam, unless the reply explicitly says it does not know which caused which and states only the two owned pieces. A reply that only repeats the route-change sentence fails response.
- authority_pass: No blockade, no count of wagons, and no hour of delay.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved if that can still be the route change or the choke from S04.1. lost if that becomes Thoran or the stew.
- acceptable_variations: []
- unacceptable_behaviors: ['Answering with only the route changed and never mentioning the choke or the wagons.']
- required_evidence: ['Shared packet.']

**State before → after**

- discovered_clues: ['The patrol route changed after the Ash Compact census choke worsened.', 'Follow the missing patrol rumor'] → ['The patrol route changed after the Ash Compact census choke worsened.', 'Follow the missing patrol rumor']
- interlocutor: 'gate_serjeant' → 'gate_serjeant'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 2 → 3
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: question; mode: unavailable; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S04/result.json` /turns/2; `artifacts/atgb/atgb_03c/S04/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S04.4/trial-2 (npc_dialogue_coherence)

**Player**

Say that again, but only what you actually know.

**AI-DM**

I can't interpret that from the current scene without using information you have not been shown.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S04.1/trial-2, S04.2/trial-2, S04.3/trial-2

**Approved behavioral expectations**
- communicative_act: A request to restate the serjeant's own limited knowledge.
- interpretation_pass: A request to restate the serjeant's own limited knowledge.
- response_pass: The route-change sentence, and nothing past it. Uncertainty on the wagon cause may remain one clause.
- authority_pass: No new personnel and no new order.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved for the serjeant and the route sentence.
- acceptable_variations: []
- unacceptable_behaviors: []
- required_evidence: ['Speaker id.']

**State before → after**

- discovered_clues: ['The patrol route changed after the Ash Compact census choke worsened.', 'Follow the missing patrol rumor'] → ['The patrol route changed after the Ash Compact census choke worsened.', 'Follow the missing patrol rumor']
- interlocutor: 'gate_serjeant' → 'gate_serjeant'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 3 → 4
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: interpretation_rejected; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S04/result.json` /turns/3; `artifacts/atgb/atgb_03c/S04/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

Conversation qualitative observations: __________________________________


## S05 — Two accounts — trial 1

Partition: development_visible; development_visible.

**Scenario objective**
- The runner answers first.
- The board is consulted second.
- That is then ambiguous.
- The player's choice of the runner is honored.

**Required context**
Fresh gate.

**Authoritative facts**
- The runner's rumor and, once the board is read, notice_patrol_route both point near the crates and the northwest approach.
- They are different sentences and different sources.

**NPC knowledge**
- The runner knows the rumor as hearsay. The board holds the posted warning. Neither may absorb the other's wording.

**Acceptable variations**
- S05.3 may pick neither account and ask. It may not pick one and call the choice obvious.

**Unacceptable behavior**
- The same paragraph presented as both the notice and the rumor.
- A third story.
- The guard answering S05.4.

**Setup dependencies**
- Pronoun follow-up is not last-answer authority for they or it. That after two delivered accounts is supposed to be ambiguous. A host that continues only the latest account has lost the earlier one; score continuity lost and clarification missing_when_needed_fail.

**Required evidence**
- Shared packet, including the clarification text and the player's S05.4 choice.

Each turn below retains every previous exchange in this trial above it. No expected answer substitutes for actual history. No history crosses scenario/trial boundaries.

### S05.1/trial-1 (npc_dialogue_coherence)

**Player**

Runner, what did you hear about the patrol?

**AI-DM**

Tavern Runner mutters, "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** None; empty history.

**Approved behavioral expectations**
- communicative_act: Question to tavern_runner.
- interpretation_pass: tavern_runner is the addressee.
- response_pass: The footprint rumor as hearsay.
- authority_pass: No notice wording presented as what the runner heard.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: not_applicable
- continuity_notes: 
- acceptable_variations: []
- unacceptable_behaviors: []
- required_evidence: ['Speaker id.']

**State before → after**

- discovered_clues: [] → ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor']
- interlocutor: None → 'tavern_runner'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 0 → 1
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: question; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S05/result.json` /turns/0; `artifacts/atgb/atgb_03c/S05/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S05.2/trial-1 (conversational_continuity)

**Player**

And the board, what does it say about the same patrol?

**AI-DM**

I cannot provide a validated response to that request.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S05.1/trial-1

**Approved behavioral expectations**
- communicative_act: A shift from the runner to the notice board, same patrol topic.
- interpretation_pass: A shift from the runner to the notice board, same patrol topic.
- response_pass: The posted warning, including the northwest track once the board is investigated.
- authority_pass: The runner is not quoted as the board.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved if the same patrol is the patrol from S05.1. lost if the board answer changes the subject to taxes only, or if the runner's sentence is repeated unchanged and called the notice.
- acceptable_variations: []
- unacceptable_behaviors: []
- required_evidence: ['Whether the board was investigated.']

**State before → after**

- discovered_clues: ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor'] → ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor']
- interlocutor: 'tavern_runner' → 'tavern_runner'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 1 → 2
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: question; mode: unavailable; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S05/result.json` /turns/1; `artifacts/atgb/atgb_03c/S05/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S05.3/trial-1 (ambiguity_handling)

**Player**

Tell me more about that.

**AI-DM**

Which person do you mean: Gate Guard or Gate Serjeant or Tavern Runner? Nothing has been attempted.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S05.1/trial-1, S05.2/trial-1

**Approved behavioral expectations**
- communicative_act: The referent is unresolved between the rumor and the notice.
- interpretation_pass: The referent is unresolved between the rumor and the notice.
- response_pass: One question that names both, or otherwise distinguishes them. No new facts. This is a successful turn when the clarification is necessary and focused. Guessing is a major failure.
- authority_pass: No additional detail about either account.
- clarification_expected: necessary_pass
- clarification_notes: Continuing only the latest line without acknowledging the other is missing_when_needed_fail.
- continuity_expected: preserved
- continuity_notes: preserved if both accounts are still available to name. lost if one has vanished. This turn must remember both accounts, including the one before the previous sentence.
- acceptable_variations: ['The clarification may pick neither account and ask.']
- unacceptable_behaviors: ['Picking one account and calling the choice obvious.']
- required_evidence: ['The clarification text.']

**State before → after**

- discovered_clues: ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor'] → ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor']
- interlocutor: 'tavern_runner' → 'tavern_runner'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 2 → 3
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_clarify; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S05/result.json` /turns/2; `artifacts/atgb/atgb_03c/S05/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S05.4/trial-1 (corrections_and_clarifications)

**Player**

The runner's version, not the notice.

**AI-DM**

Tavern Runner says, "I couldn't tell you."

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S05.1/trial-1, S05.2/trial-1, S05.3/trial-1

**Approved behavioral expectations**
- communicative_act: The player resolved S05.3 in favor of the runner.
- interpretation_pass: The player resolved S05.3 in favor of the runner.
- response_pass: The footprint rumor only, still hearsay.
- authority_pass: The track-past-the-crates sentence is not substituted.
- clarification_expected: none
- clarification_notes: Asking again is unnecessary_fail.
- continuity_expected: preserved
- continuity_notes: preserved for the runner's account from S05.1.
- acceptable_variations: []
- unacceptable_behaviors: ['The guard answering this turn.']
- required_evidence: ["The player's choice and the speaker id."]

**State before → after**

- discovered_clues: ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor'] → ['The runner heard the patrol vanished near muddy footprints northwest of the crates.', 'Follow the missing patrol rumor']
- interlocutor: 'tavern_runner' → 'tavern_runner'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 3 → 4
- world_flag_names: [] → []
- world_state_flag_names: [] → ['faction_house_verevin_agenda_advanced', 'faction_ash_cowl_agenda_advanced', 'faction_ordo_pyric_agenda_advanced']

Resolution: question; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S05/result.json` /turns/3; `artifacts/atgb/atgb_03c/S05/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

Conversation qualitative observations: __________________________________


## S06 — Beside the table — trial 1

Partition: development_visible; development_visible.

**Scenario objective**
- The OOC questions do not execute play.
- The IC question is in character.
- The disclaimer prevents a purchase.
- The last line delivers the rumor and not a bowl of stew.

**Required context**
Fresh gate. No purchase system is in play.

**Authoritative facts**
- Talking does not itself change scene or discover the route clue.
- Hot stew is a visible offer. The rumor is the runner's owned hearsay.
- There is no price and no inventory transaction.

**NPC knowledge**
- OOC turns are answered by the GM or session voice. They are not answered by the runner.
- IC turns return to the runner when the player addresses the runner.

**Acceptable variations**
- An OOC reply may be short. It does not have to use a particular stock sentence. It does have to answer the question that was asked.

**Unacceptable behavior**
- Validator phrases such as based on what's established are a response defect under the AI GM contract, scored minor if the answer is otherwise present and major if they replace the answer.
- A narrated purchase, a coin change, or a scene move is critical.
- An OOC lecture that continues after the player has said IC: fails the IC turn.

**Setup dependencies**
- Explicit OOC: and IC: prefixes are recognized by the current communication-mode parser.
- Some OOC bodies also hit a non-mutating acknowledgement that does not answer the specific question. That acknowledgement is interpretable as OOC and still has to meet the response criterion.

**Required evidence**
- Shared packet plus authoritative_mutation, scene id, clues, and any inventory or world-flag delta.
- A host path that skips narration records provider calls as zero when that is what the response says.

Each turn below retains every previous exchange in this trial above it. No expected answer substitutes for actual history. No history crosses scenario/trial boundaries.

### S06.1/trial-1 (ic_ooc_boundaries)

**Player**

OOC: if I talk to people here, does that spend game time or change the scene?

**AI-DM**

Understood. I will treat that as out-of-character. No gameplay action is executed, no game time advances, and committed state is unchanged.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** None; empty history.

**Approved behavioral expectations**
- communicative_act: OOC, non-mutating.
- interpretation_pass: OOC, non-mutating.
- response_pass: A direct OOC answer. Talk at this gate does not travel and does not resolve an exit. The reply may say that a chat turn exists without claiming that hours passed. A stock sentence that only says to ask rules questions normally, and never addresses time or scene, fails response and can pass interpretation.
- authority_pass: Scene stays frontier_gate, no clue is added, and no NPC is forced into a conversation by this line.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: not_applicable
- continuity_notes: 
- acceptable_variations: ['The reply may be short if it answers the time and scene question.']
- unacceptable_behaviors: ['A generic rules invitation that never addresses time or scene.']
- required_evidence: ['authoritative_mutation, scene id, and provider-call count when the host records it.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 0 → 1
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: ooc_message; mode: OOC; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S06/result.json` /turns/0; `artifacts/atgb/atgb_03c/S06/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S06.2/trial-1 (ic_ooc_boundaries)

**Player**

IC: I ask the runner whether the stew is hot.

**AI-DM**

Tavern Runner says, "I couldn't tell you."

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S06.1/trial-1

**Approved behavioral expectations**
- communicative_act: In-character question to tavern_runner.
- interpretation_pass: In-character question to tavern_runner.
- response_pass: In character, about the stew. The visible offer is hot stew. A one-line yes grounded in that offer passes. A quality review or a price does not.
- authority_pass: No serving and no coin.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved if the OOC policy talk has stopped. lost if the reply continues S06.1.
- acceptable_variations: []
- unacceptable_behaviors: ['Continuing the OOC policy talk.']
- required_evidence: ['Communication mode and speaker id.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → 'tavern_runner'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 1 → 2
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: question; mode: IC; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S06/result.json` /turns/1; `artifacts/atgb/atgb_03c/S06/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S06.3/trial-1 (ic_ooc_boundaries)

**Player**

OOC: that was only a question. I am not buying anything.

**AI-DM**

Understood. I will treat that as out-of-character. No gameplay action is executed, no game time advances, and committed state is unchanged.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S06.1/trial-1, S06.2/trial-1

**Approved behavioral expectations**
- communicative_act: OOC correction. No transaction.
- interpretation_pass: OOC correction. No transaction.
- response_pass: Confirms that nothing was bought and that the scene is unchanged.
- authority_pass: No inventory delta and no price.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved for that meaning the stew question.
- acceptable_variations: []
- unacceptable_behaviors: []
- required_evidence: ['Inventory and world-flag delta.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: 'tavern_runner' → 'tavern_runner'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 2 → 3
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: ooc_message; mode: OOC; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S06/result.json` /turns/2; `artifacts/atgb/atgb_03c/S06/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S06.4/trial-1 (ic_ooc_boundaries)

**Player**

Back in character. Runner, I'll hear the rumor, not buy the stew.

**AI-DM**

I've set aside the unexecuted intention. Anything already resolved still stands.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S06.1/trial-1, S06.2/trial-1, S06.3/trial-1

**Approved behavioral expectations**
- communicative_act: IC request to tavern_runner for the rumor, refusing the stew.
- interpretation_pass: IC request to tavern_runner for the rumor, refusing the stew.
- response_pass: The footprint rumor as hearsay. Stew is not served.
- authority_pass: No purchase, no coin, and no second rumor.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved if the refusal of the stew is honored.
- acceptable_variations: []
- unacceptable_behaviors: []
- required_evidence: ['Speaker id and inventory delta.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: 'tavern_runner' → 'tavern_runner'
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 3 → 4
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S06/result.json` /turns/3; `artifacts/atgb/atgb_03c/S06/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

Conversation qualitative observations: __________________________________


## S07 — In the queue — trial 1

Partition: held_out; held_out_previously_exposed.

**Scenario objective**
- Small talk stays small.
- The banner remark does not become a dossier.
- The shout is identified as stew and rumor.
- The correction drops the rumor.

**Required context**
Fresh gate, opening description available, including rain and frayed banners. The runner is visibly hawking.

**Authoritative facts**
- Rain, queue, frayed banners, stew, and rumor.
- No patrol question has been asked.

**NPC knowledge**
- No one is required to volunteer the route clue, Thoran, or the route change.

**Acceptable variations**
- One grounded hook, such as the crush or the runner's shout, may appear inside S07.1. It is an offer, not a briefing.

**Unacceptable behavior**
- An unprompted patrol report.
- A three-item command menu.
- Anti-echo that consumes the whole reply.
- Invented crowd dialogue about why refugees fled.

**Setup dependencies**
- Local small talk has no separate mechanical owner. Success is a non-mutating conversational reply. The scenario does not require a mood system.

**Required evidence**
- Shared packet. Narration-quality notes sit in the severity field, not in a second score.

Each turn below retains every previous exchange in this trial above it. No expected answer substitutes for actual history. No history crosses scenario/trial boundaries.

### S07.1/trial-1 (initiative_and_naturalness)

**Player**

Miserable rain for a queue this long.

**AI-DM**

You are at Cinderwatch Gate District. Rain, choke traffic, a notice board, and gate watch pressure frame the missing patrol inquiry. Visible points of interest: Notice board. Known exits: Enter Cinderwatch, Follow the missing patrol rumor.

**Setup qualification** Special review: opening-dependent criteria require eligibility assessment. World-state presence does not establish delivery to player. Use only actual prior exchanges and explicit player wording; explain unsupported criteria.

**Prior turns** None; empty history.

**Approved behavioral expectations**
- communicative_act: In-character remark, not an investigation command.
- interpretation_pass: In-character remark, not an investigation command.
- response_pass: A human-scale reply about the rain or the queue. At most one grounded hook.
- authority_pass: No travel and no new fact.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: not_applicable
- continuity_notes: 
- acceptable_variations: ["One grounded hook, such as the crush or the runner's shout, may appear. It is an offer, not a briefing."]
- unacceptable_behaviors: ['An unprompted patrol report.']
- required_evidence: ['Shared packet.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 0 → 1
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S07/result.json` /turns/0; `artifacts/atgb/atgb_03c/S07/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S07.2/trial-1 (initiative_and_naturalness)

**Player**

The banners look about finished.

**AI-DM**

I don't have an established ruling for that question. No action or roll has been made.

**Setup qualification** Special review: opening-dependent criteria require eligibility assessment. World-state presence does not establish delivery to player. Use only actual prior exchanges and explicit player wording; explain unsupported criteria.

**Prior turns** S07.1/trial-1

**Approved behavioral expectations**
- communicative_act: Continuation of the observation. Frayed banners are already in the opening.
- interpretation_pass: Continuation of the observation. Frayed banners are already in the opening.
- response_pass: Stays with that observation for a beat. Does not open the missing-patrol briefing.
- authority_pass: No new heraldry and no noble house.
- clarification_expected: none
- clarification_notes: unnecessary_fail if the player is asked to choose a mechanical action.
- continuity_expected: preserved
- continuity_notes: preserved if the queue conversation is still the conversation.
- acceptable_variations: []
- unacceptable_behaviors: ['A mechanical action menu.']
- required_evidence: ['Shared packet.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 1 → 2
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S07/result.json` /turns/1; `artifacts/atgb/atgb_03c/S07/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S07.3/trial-1 (initiative_and_naturalness)

**Player**

The one shouting — what's he offering?

**AI-DM**

That has not been established in the information available to you.

**Setup qualification** Special review: opening-dependent criteria require eligibility assessment. World-state presence does not establish delivery to player. Use only actual prior exchanges and explicit player wording; explain unsupported criteria.

**Prior turns** S07.1/trial-1, S07.2/trial-1

**Approved behavioral expectations**
- communicative_act: A shift to the runner's visible offer.
- interpretation_pass: A shift to the runner's visible offer. Binding tavern_runner is appropriate. A GM description of the shout also passes if the offer is right.
- response_pass: Hot stew and rumor.
- authority_pass: No price and no patrol destination beyond the fact that a rumor is on offer. Inventing a second hawker is an authority failure.
- clarification_expected: none
- clarification_notes: none, unless several people are shouting, which the visible scene does not support.
- continuity_expected: preserved
- continuity_notes: preserved for the gate. The player did not ask to leave.
- acceptable_variations: ['A GM description of the shout passes if the offer is right.']
- unacceptable_behaviors: ['Inventing a second hawker.']
- required_evidence: ['Shared packet.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 2 → 3
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S07/result.json` /turns/2; `artifacts/atgb/atgb_03c/S07/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S07.4/trial-1 (response_relevance)

**Player**

Leave the rumor. I only wanted to know what he's selling.

**AI-DM**

That has not been established in the information available to you.

**Setup qualification** Special review: opening-dependent criteria require eligibility assessment. World-state presence does not establish delivery to player. Use only actual prior exchanges and explicit player wording; explain unsupported criteria.

**Prior turns** S07.1/trial-1, S07.2/trial-1, S07.3/trial-1

**Approved behavioral expectations**
- communicative_act: Correction toward the food offer. The visible offer includes both stew and rumor, and the player now narrows it.
- interpretation_pass: Correction toward the food offer.
- response_pass: Stew, without the patrol story.
- authority_pass: No price and no bowl placed in inventory.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved if the shouting runner from S07.3 is still the seller.
- acceptable_variations: []
- unacceptable_behaviors: ['Delivering the patrol story.']
- required_evidence: ['Shared packet.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 3 → 4
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S07/result.json` /turns/3; `artifacts/atgb/atgb_03c/S07/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

Conversation qualitative observations: __________________________________


## S08 — Same gate, other words — trial 1

Partition: related_variation; related_variation.

**Scenario objective**
- A question-shaped look still looks.
- A correction toward people is honored.
- The crowd-handler is the serjeant from the visible fact.
- The follow-up recalls the choke and withholds the official.

**Required context**
Fresh gate. This is a related variation, not a held-out scenario. The requirements match S01, S02, and S04. The words do not.

**Authoritative facts**
- The same visible list and the serjeant's route-change sentence.
- Who issued the change is unauthored.

**NPC knowledge**
- The serjeant, once addressed by the conversation, knows the route change and the census choke as the setting of that change.
- The serjeant does not know the official who ordered it.

**Acceptable variations**
- Any grounded description, and any wording of the route-change fact.

**Unacceptable behavior**
- Treating S08.1 as travel.
- Describing only the rain after the player asks for the people.
- Naming an official.
- Answering who handles the crowd with the runner.

**Setup dependencies**
- None beyond the fresh gate. Do not chain this scenario after S04.

**Required evidence**
- Shared packet, labeled related_variation.

Each turn below retains every previous exchange in this trial above it. No expected answer substitutes for actual history. No history crosses scenario/trial boundaries.

### S08.1/trial-1 (intent_recognition)

**Player**

What's in front of me right now?

**AI-DM**

You are at Cinderwatch Gate District. Rain, choke traffic, a notice board, and gate watch pressure frame the missing patrol inquiry. Visible points of interest: Notice board. Known exits: Enter Cinderwatch, Follow the missing patrol rumor. The notice board lists taxes, curfew rules, and a warning about a missing patrol. A gate serjeant manages the crowd and keeps one eye on the roster board. A tavern runner trades hot stew and rumors near the rain barrel. Threadbare watchers and refugees cluster along the muddy gate line. Ash Compact census delays have tightened the eastern caravan choke point.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** None; empty history.

**Approved behavioral expectations**
- communicative_act: Variation of a look, in question form.
- interpretation_pass: Current-scene observation.
- response_pass: Present public facts, not a history of the patrol.
- authority_pass: No hidden fact and no scene change.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: not_applicable
- continuity_notes: 
- acceptable_variations: ['Any grounded description of what is present.']
- unacceptable_behaviors: ['Treating the line as travel.']
- required_evidence: ['Shared packet, labeled related_variation.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 0 → 1
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S08/result.json` /turns/0; `artifacts/atgb/atgb_03c/S08/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S08.2/trial-1 (corrections_and_clarifications)

**Player**

I meant the people, not the weather.

**AI-DM**

I don't have an unexecuted intention to revise. What do you want to change?

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S08.1/trial-1

**Approved behavioral expectations**
- communicative_act: Correction of S08.1 toward the people present.
- interpretation_pass: Correction of S08.1 toward the people present.
- response_pass: Names people who are actually there, from the visible set: serjeant, runner, watchers, refugees, guards. Weather may be dropped.
- authority_pass: No invented traveler with a name and a story.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved for the look the player is correcting.
- acceptable_variations: []
- unacceptable_behaviors: ['Describing only the rain.']
- required_evidence: ['Shared packet, labeled related_variation.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 1 → 2
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_clarify; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S08/result.json` /turns/1; `artifacts/atgb/atgb_03c/S08/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S08.3/trial-1 (response_relevance)

**Player**

Which person looks like they handle the crowd?

**AI-DM**

A gate serjeant manages the crowd and keeps one eye on the roster board.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S08.1/trial-1, S08.2/trial-1

**Approved behavioral expectations**
- communicative_act: A question about the visible crowd-handler.
- interpretation_pass: A question about the visible crowd-handler.
- response_pass: The gate serjeant, who is described as managing the crowd. The roster board may be mentioned because the same visible sentence includes it.
- authority_pass: No rank promotion and no claim that the serjeant commands the watch. That command sentence belongs to Thoran's topic.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved if the people from S08.2 are the set being narrowed.
- acceptable_variations: []
- unacceptable_behaviors: ['Answering with the runner.']
- required_evidence: ['Shared packet, labeled related_variation.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 2 → 3
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S08/result.json` /turns/2; `artifacts/atgb/atgb_03c/S08/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S08.4/trial-1 (conversational_continuity)

**Player**

You just said the route changed because the choke got worse. Who changed it?

**AI-DM**

You are at Cinderwatch Gate District. Rain, choke traffic, a notice board, and gate watch pressure frame the missing patrol inquiry. Visible points of interest: Notice board. Known exits: Enter Cinderwatch, Follow the missing patrol rumor. The notice board lists taxes, curfew rules, and a warning about a missing patrol. A gate serjeant manages the crowd and keeps one eye on the roster board. A tavern runner trades hot stew and rumors near the rain barrel. Threadbare watchers and refugees cluster along the muddy gate line. Ash Compact census delays have tightened the eastern caravan choke point.

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S08.1/trial-1, S08.2/trial-1, S08.3/trial-1

**Approved behavioral expectations**
- communicative_act: A who-question about the agent of the change. If S08.3 never said the route changed, the line is still that question.
- interpretation_pass: A who-question about the agent of the change.
- response_pass: The choke worsened and the route changed; the person who ordered it is not known. The serjeant fact may be stated once before the gap when the previous reply never said it.
- authority_pass: No name, no office, and no claim that the captain ordered it. Inventing the missing statement in order to agree with the player is an authority failure.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved if a route or choke statement was made and is still the topic. If no such statement was made, continuity is not_applicable and the turn is only the unauthored who-question.
- acceptable_variations: ['Any wording of the route-change fact that withholds the official.']
- unacceptable_behaviors: ['Naming an official.']
- required_evidence: ['Shared packet, labeled related_variation.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 3 → 4
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_answer; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S08/result.json` /turns/3; `artifacts/atgb/atgb_03c/S08/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

Conversation qualitative observations: __________________________________


## S09 — The quiet pair — trial 1

Partition: held_out; held_out_previously_exposed.

**Scenario objective**
- The first line is ambiguous between two people and is clarified.
- The second line selects the watcher.
- No patrol story is borrowed.

**Required context**
Fresh gate. Held-out. Not a tuning set.

**Authoritative facts**
- The ragged stranger and the threadbare watcher are both present addressables.
- Neither has an owned topic in world.json.
- The stranger hangs back and watches the crowd. The watcher stands still, gaze moving to packs and faces.
- Neither has an authored name beyond those labels, and neither owns the patrol rumor.

**NPC knowledge**
- Neither bystander has an authored answer to who they are beyond the public label.
- Delivering the runner's rumor in either voice is an authority failure. Delivering a hidden fact is critical.

**Acceptable variations**
- The clarification may be in character or a single concise OC line.
- Either person may be described with the visible posture cues while the question is asked.

**Unacceptable behavior**
- Answering as the tavern runner.
- Inventing personal names.
- Stating how long either has stood there.
- Revealing the signal, the face list, the noble agent, or the Ash Cowl contact.

**Setup dependencies**
- The engine is not required to role-play two NPCs in one reply. One clarifying question is the successful path. A crowd conversation system is unsupported and is not a pass condition.

**Required evidence**
- Shared packet, labeled held_out.

Each turn below retains every previous exchange in this trial above it. No expected answer substitutes for actual history. No history crosses scenario/trial boundaries.

### S09.1/trial-1 (ambiguity_handling)

**Player**

I ask either the ragged stranger or the threadbare watcher who they are.

**AI-DM**

I couldn't read that as a gameplay action. Please say it again in plain words.

**Setup qualification** Special review: opening-dependent criteria require eligibility assessment. World-state presence does not establish delivery to player. Use only actual prior exchanges and explicit player wording; explain unsupported criteria.

**Prior turns** None; empty history.

**Approved behavioral expectations**
- communicative_act: The addressee is unresolved between refugee and threadbare_watcher.
- interpretation_pass: The addressee is unresolved between those two ids, refugee and threadbare_watcher.
- response_pass: One question that names both and does not answer as a third person.
- authority_pass: No biography.
- clarification_expected: necessary_pass
- clarification_notes: 
- continuity_expected: not_applicable
- continuity_notes: 
- acceptable_variations: ['The clarification may be in character or a single concise OC line.']
- unacceptable_behaviors: ['Answering as the tavern runner.']
- required_evidence: ['Shared packet, labeled held_out.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 0 → 1
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: interpretation_rejected; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S09/result.json` /turns/0; `artifacts/atgb/atgb_03c/S09/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S09.2/trial-1 (ambiguity_handling)

**Player**

The threadbare watcher.

**AI-DM**

Do you intend to speak to or about the 'threadbare watcher' NPC, or is this a description or question about them?

**Setup qualification** Special review: opening-dependent criteria require eligibility assessment. World-state presence does not establish delivery to player. Use only actual prior exchanges and explicit player wording; explain unsupported criteria.

**Prior turns** S09.1/trial-1

**Approved behavioral expectations**
- communicative_act: threadbare_watcher is now the addressee, and the pending question is who they are.
- interpretation_pass: threadbare_watcher is now the addressee, and the pending question is who they are.
- response_pass: The public label is the available identity. The reply does not invent a personal name or a secret role.
- authority_pass: No hidden fact. The runner's rumor is not moved into this mouth.
- clarification_expected: none
- clarification_notes: Asking the same choice again is unnecessary_fail.
- continuity_expected: preserved
- continuity_notes: preserved if the who-question from S09.1 is what gets answered.
- acceptable_variations: []
- unacceptable_behaviors: ['Inventing a personal name or revealing a hidden fact.']
- required_evidence: ['Shared packet, labeled held_out.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 1 → 2
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_clarify; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S09/result.json` /turns/1; `artifacts/atgb/atgb_03c/S09/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

Conversation qualitative observations: __________________________________


## S10 — The barrel — trial 1

Partition: held_out; held_out_previously_exposed.

**Scenario objective**
- The thing by the barrel is not quietly resolved into travel, a purchase, or a single guess.
- The follow-up selects the rumor rather than the stew.

**Required context**
Fresh gate. Held-out. The rain barrel and the runner's offer are visible. Nothing has been said yet.

**Authoritative facts**
- The runner trades hot stew and rumors beside the rain barrel.
- The non-food half of that offer is the rumor, whose content is the footprint hearsay once the runner is actually asked.
- The barrel is not an interactable with a clue.

**NPC knowledge**
- The runner knows the owned rumor when the rumor is requested. The barrel has no knowledge.

**Acceptable variations**
- The clarification may offer the barrel, the runner, the stew, and the rumor as the live possibilities. It does not need all four words if the real ambiguity is stated plainly.

**Unacceptable behavior**
- Taking the missing-patrol exit.
- Investigating a new object called the thing.
- Serving stew.
- Quoting the notice clue as what the runner sells.

**Setup dependencies**
- Follow the rumor is an authored exit label and is intentionally not the player line, so a travel parse is not the favored reading. If the host nonetheless travels, that is a critical authority failure unless the player-facing text and resolved_transition both show a real, intended exit, which this wording does not justify.

**Required evidence**
- Shared packet, labeled held_out, plus scene id to confirm no exit.

Each turn below retains every previous exchange in this trial above it. No expected answer substitutes for actual history. No history crosses scenario/trial boundaries.

### S10.1/trial-1 (ambiguity_handling)

**Player**

Handle the thing by the barrel.

**AI-DM**

What exactly is 'the thing by the barrel' that I am supposed to handle?

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** None; empty history.

**Approved behavioral expectations**
- communicative_act: The target is ambiguous. It is not a completed travel action and not a completed purchase.
- interpretation_pass: The target is ambiguous. It is not a completed travel action and not a completed purchase.
- response_pass: One focused question among the barrel, the runner, and the runner's offer.
- authority_pass: Scene stays frontier_gate. No clue. No coin.
- clarification_expected: necessary_pass
- clarification_notes: Guessing a purchase or a journey is missing_when_needed_fail and critical if state changes.
- continuity_expected: not_applicable
- continuity_notes: 
- acceptable_variations: ['The clarification may offer the barrel, the runner, the stew, and the rumor. It does not need all four words if the real ambiguity is stated plainly.']
- unacceptable_behaviors: ['Taking the missing-patrol exit or serving stew.']
- required_evidence: ['Scene id, to confirm no exit.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 0 → 1
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_clarify; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S10/result.json` /turns/0; `artifacts/atgb/atgb_03c/S10/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

### S10.2/trial-1 (conversational_continuity)

**Player**

Not the barrel. What the runner said he'd sell, the one that isn't food.

**AI-DM**

What exactly is the item the runner said he'd sell that isn't food, distinct from the barrel?

**Setup qualification** Machine prerequisites verified; naturalness and scenario assumptions still require human review. Do not assume an expected prior reply was actually delivered; inspect preceding exchanges.

**Prior turns** S10.1/trial-1

**Approved behavioral expectations**
- communicative_act: The player selects the non-food offer, which is the rumor.
- interpretation_pass: The player selects the non-food offer, which is the rumor.
- response_pass: The footprint rumor as hearsay, from the runner.
- authority_pass: Stew is not delivered. The notice's track sentence is not relabeled as the sold rumor. No price.
- clarification_expected: none
- clarification_notes: 
- continuity_expected: preserved
- continuity_notes: preserved if S10.1's alternatives are closed by this sentence and the rumor is the survivor. lost if the reply returns to the barrel or answers with food. This turn reaches back to the visible offer and to the clarification.
- acceptable_variations: []
- unacceptable_behaviors: ['Returning to the barrel or answering with food.']
- required_evidence: ['Scene id and speaker.']

**State before → after**

- discovered_clues: [] → []
- interlocutor: None → None
- scene_id: 'frontier_gate' → 'frontier_gate'
- transcript_entries: 1 → 2
- world_flag_names: [] → []
- world_state_flag_names: [] → []

Resolution: conversational_clarify; mode: AUTO; addressee: unavailable.

Evidence: `artifacts/atgb/atgb_03c/S10/result.json` /turns/1; `artifacts/atgb/atgb_03c/S10/transcript.md`.

| Human judgment | Entry |
| --- | --- |
| interpretation | __________ |
| response | __________ |
| authority | __________ |
| failure_severity | __________ |
| clarification | __________ |
| continuity | __________ |
| reviewer_explanation | __________ |

Conversation qualitative observations: __________________________________

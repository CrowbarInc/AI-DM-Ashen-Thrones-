"""Twenty held-out cases. These phrases are not production matchers."""
from __future__ import annotations

from dataclasses import dataclass


CLUE = "The missing patrol was last seen taking the northwest mud track past the crates."
CAPTAIN_TOPIC = "A patrol went missing near the old milestone."
STEW_TOPIC = "Hot stew and rumors for coin."
HIDDEN = (
    "agent of a noble house",
    "Ash Cowl smuggling",
    "coordinated signal",
    "written list paid for in silver",
    "CANARY_",
)
INITIAL = (
    "Isolated frontier_gate seed from tests.pr_play_79df3_harness.seed_gate. "
    "Scene Cinderwatch Gate District, turn 4, ruleset pf1e version 1 binding_version 1, "
    "inventory Spellbook only, addressables Guard Captain, Tavern Runner, Ragged stranger, "
    "and Threadbare watcher, interactable Notice board only. Discoverable clue "
    "notice_patrol_route is unrevealed. Prior publication: Gate Guard says, "
    "\"The notice board mentions a missing patrol.\" Prepared spells are Daze, "
    "Detect Magic, Magic Missile, and Shield. No social-check receipt."
)


@dataclass(frozen=True)
class Case:
    case_id: str
    sequence_id: str
    turn_index: int
    utterance: str
    intended_meaning: str
    intent_id: str
    partial_intent_ids: tuple[str, ...]
    entities: tuple[str, ...]
    expected_reference_ids: tuple[str, ...]
    prohibited_reference_ids: tuple[str, ...]
    expected_admission: str
    withholding_is_required: bool
    execution_expected: bool
    state_rule: str
    prohibited_narration: tuple[str, ...]
    required_if_admitted: tuple[str, ...]
    capability_limitation: str
    prior_context: str
    scoring_focus: str

    @property
    def initial_state(self) -> str:
        return INITIAL


def _case(**kwargs) -> Case:
    kwargs.setdefault("partial_intent_ids", ())
    kwargs.setdefault("entities", ())
    kwargs.setdefault("expected_reference_ids", ())
    kwargs.setdefault("prohibited_reference_ids", ())
    kwargs.setdefault("withholding_is_required", False)
    kwargs.setdefault("execution_expected", False)
    kwargs.setdefault("prohibited_narration", HIDDEN)
    kwargs.setdefault("required_if_admitted", ())
    kwargs.setdefault("prior_context", "Sequence start. No evaluated turn precedes this one.")
    return Case(**kwargs)


CASES: tuple[Case, ...] = (
    _case(
        case_id="A1", sequence_id="A", turn_index=1,
        utterance="I leaf through the volume I've been carrying.",
        intended_meaning="Inspect the unique carried Spellbook and report only what the character sheet establishes.",
        intent_id="inspect_carried_spellbook",
        entities=("Spellbook",),
        expected_reference_ids=("spellbook",),
        prohibited_reference_ids=("notice_board", "guard_captain", "tavern_runner"),
        expected_admission="informational",
        execution_expected=True,
        state_rule="unchanged",
        capability_limitation="Deterministic reference_compatible treats book as a suffix of spellbook. The word volume is not that suffix.",
        scoring_focus="Unfamiliar object wording. A sheet answer with no turn spend is execution. Safe withholding is partial, not success. A turn spend or invented spell text fails.",
    ),
    _case(
        case_id="A2", sequence_id="A", turn_index=2,
        utterance="The one I mean is the spellbook in my pack.",
        intended_meaning="Clarify that the carried Spellbook is the volume from the previous turn.",
        intent_id="clarify_carried_spellbook",
        partial_intent_ids=("inspect_carried_spellbook",),
        entities=("Spellbook",),
        expected_reference_ids=("spellbook",),
        prohibited_reference_ids=("notice_board",),
        expected_admission="informational",
        execution_expected=True,
        state_rule="unchanged",
        capability_limitation="Exact name spellbook is compatible. This sentence has no examine verb, so it may be handled as clarification rather than a second inspection.",
        prior_context="A1, whatever it committed. The player is naming the carried Spellbook.",
        scoring_focus="Clarification keeps the Spellbook and does not spend the turn or invent a second book.",
    ),
    _case(
        case_id="A3", sequence_id="A", turn_index=3,
        utterance="From that same book, what spells do I actually have ready?",
        intended_meaning="Ask which spells the sheet has prepared. Do not cast.",
        intent_id="ask_prepared_spells",
        entities=("Spellbook", "Daze", "Detect Magic", "Magic Missile", "Shield"),
        expected_reference_ids=("spellbook",),
        prohibited_reference_ids=("notice_board",),
        expected_admission="informational",
        execution_expected=True,
        state_rule="unchanged",
        required_if_admitted=("Daze", "Detect Magic", "Magic Missile", "Shield"),
        capability_limitation="Prepared spells are character-sheet rows. Casting and slot consumption are not requested and are not authorized by this question.",
        prior_context="A1 and A2 concerned the carried Spellbook.",
        scoring_focus="Information request. Naming only the four prepared spells passes. Inventing another spell or casting fails. An honest sheet limitation without invented names is partial.",
    ),
    _case(
        case_id="A4", sequence_id="A", turn_index=4,
        utterance="I keep my hands off it and only ask what I could cast if trouble starts.",
        intended_meaning="Hypothetical question about possible casting. Do not cast and do not resolve an attack.",
        intent_id="hypothetical_casting_question",
        partial_intent_ids=("ask_prepared_spells",),
        entities=("Spellbook",),
        expected_reference_ids=("spellbook",),
        prohibited_reference_ids=(),
        expected_admission="informational",
        execution_expected=False,
        state_rule="unchanged",
        prohibited_narration=HIDDEN + ("you cast", "the bolt strikes", "magic missile streaks"),
        capability_limitation="No production cast is authorized by a hypothetical question. Withholding the cast is required.",
        prior_context="The book under discussion is the carried Spellbook. Nothing has been cast in this sequence by the case design.",
        scoring_focus="Hypothetical versus execution. No slot change and no attack resolution. Narrating a completed spell fails.",
    ),
    _case(
        case_id="B1", sequence_id="B", turn_index=1,
        utterance="I turn to the officer keeping this gate and ask what became of the missing soldiers.",
        intended_meaning="Ask the Guard Captain about the missing patrol.",
        intent_id="ask_captain_patrol",
        entities=("Guard Captain", "missing patrol"),
        expected_reference_ids=("guard_captain",),
        prohibited_reference_ids=("tavern_runner", "threadbare_watcher", "refugee"),
        expected_admission="admitted",
        execution_expected=True,
        state_rule="speech_or_withhold",
        required_if_admitted=(CAPTAIN_TOPIC,),
        capability_limitation="Address roles for the captain include captain and guard, not officer. The authored topic is the old-milestone sentence, not a discovered route.",
        scoring_focus="Indirect person and topic. Binding the runner or inventing a fate fails. Clarification that includes the captain and does not speak for someone else is partial.",
    ),
    _case(
        case_id="B2", sequence_id="B", turn_index=2,
        utterance="I ask him whether they were last headed toward the old stone marker.",
        intended_meaning="Continue with the same captain. Old stone marker means the authored old milestone, not a new place.",
        intent_id="follow_up_captain_milestone",
        entities=("Guard Captain", "old milestone"),
        expected_reference_ids=("guard_captain",),
        prohibited_reference_ids=("tavern_runner", "threadbare_watcher"),
        expected_admission="informational",
        execution_expected=True,
        state_rule="unchanged",
        capability_limitation="The captain topic says the patrol went missing near the old milestone. It does not say they were headed there, and the discoverable route is not yet revealed in this sequence.",
        prior_context="B1 addressed the officer at the gate about the missing soldiers.",
        scoring_focus="Pronoun continuity. Switching speakers fails. Claiming they reached or were routed along the mud track invents the unrevealed clue.",
    ),
    _case(
        case_id="B3", sequence_id="B", turn_index=3,
        utterance="I ask the guard what he personally saw.",
        intended_meaning="Ask the guard-role addressable what he witnessed. No eyewitness account is authored.",
        intent_id="ask_guard_eyewitness",
        partial_intent_ids=("ask_captain_patrol",),
        entities=("Guard Captain", "gate serjeant"),
        expected_reference_ids=("guard_captain",),
        prohibited_reference_ids=("tavern_runner",),
        expected_admission="clarified",
        execution_expected=False,
        state_rule="unchanged",
        prohibited_narration=HIDDEN + ("I saw the patrol", "I watched them leave"),
        capability_limitation="Only the Guard Captain has the address role guard. A gate serjeant appears in visible prose and is not an addressable. No authored fact says what anyone personally saw.",
        prior_context="B1 and B2 were about the captain and the milestone. This turn uses the bare word guard.",
        scoring_focus="Unique role versus an unestablished sighting. A fabricated sighting fails. Clarification or an authored-topic limit passes the narrative check when state is unchanged.",
    ),
    _case(
        case_id="B4", sequence_id="B", turn_index=4,
        utterance="I mean the captain of the watch, not the person selling food.",
        intended_meaning="Resolve the person as the Guard Captain and exclude the Tavern Runner.",
        intent_id="clarify_captain_not_runner",
        entities=("Guard Captain", "Tavern Runner"),
        expected_reference_ids=("guard_captain",),
        prohibited_reference_ids=("tavern_runner",),
        expected_admission="clarified",
        execution_expected=True,
        state_rule="unchanged",
        capability_limitation="The correction names both people by role. It is not itself a new patrol question and must not speak as the runner.",
        prior_context="B3 used the word guard. The player now excludes the food seller.",
        scoring_focus="Explicit disambiguation. Runner speech or a hidden motive fails.",
    ),
    _case(
        case_id="C1", sequence_id="C", turn_index=1,
        utterance="I read the warning the watch posted beside the gate.",
        intended_meaning="Inspect the notice board and receive its authored clue.",
        intent_id="inspect_notice_board",
        entities=("Notice board",),
        expected_reference_ids=("notice_board",),
        prohibited_reference_ids=("spellbook", "tavern_runner"),
        expected_admission="admitted",
        execution_expected=True,
        state_rule="notice_inspection",
        required_if_admitted=(CLUE,),
        capability_limitation="The notice board is the only interactable. Its clue is discoverable, not a visible fact, until inspection commits.",
        scoring_focus="Supported inspection in unfamiliar wording. Admitted inspection publishes the clue and advances one turn. Withholding without the clue is partial. Inventing a different route fails.",
    ),
    _case(
        case_id="C2", sequence_id="C", turn_index=2,
        utterance="I keep my argument to myself.",
        intended_meaning="Do not persuade, intimidate, or otherwise press anyone.",
        intent_id="withhold_argument",
        prohibited_reference_ids=("guard_captain", "tavern_runner"),
        expected_admission="withheld",
        withholding_is_required=True,
        state_rule="unchanged",
        capability_limitation="The ordinary social-check entrance matches an explicit persuade, intimidate, deceive, or bluff sentence. This sentence asks for no check. Creating stance or NPC runtime is unauthorized.",
        prior_context="C1 may have revealed the notice. No social check has been requested in this sequence.",
        scoring_focus="Negation and non-execution. Withholding is the required outcome. A check, trust change, or request delivered to the captain fails.",
    ),
    _case(
        case_id="C3", sequence_id="C", turn_index=3,
        utterance="I vanish from this gate and appear in the market without taking a step.",
        intended_meaning="Teleport to the market. That action is unsupported.",
        intent_id="unsupported_teleport",
        entities=("frontier_gate", "market_quarter"),
        expected_reference_ids=(),
        prohibited_reference_ids=(),
        expected_admission="unsupported",
        withholding_is_required=True,
        state_rule="unchanged",
        prohibited_narration=HIDDEN + ("you appear in the market", "you are in the market"),
        capability_limitation="No teleport mechanic exists. The market is an authored exit only by entering Cinderwatch, which this sentence refuses to do.",
        prior_context="The player is still at the frontier gate unless C1's inspection changed only the clue and the turn.",
        scoring_focus="Unsupported action. The scene stays frontier_gate. Arrival narration fails.",
    ),
    _case(
        case_id="C4", sequence_id="C", turn_index=4,
        utterance="Did I actually leave the gate just now?",
        intended_meaning="Ask whether C3 changed the scene. It should not have.",
        intent_id="ask_whether_scene_changed",
        entities=("frontier_gate",),
        expected_admission="informational",
        execution_expected=True,
        state_rule="authoritative_scene",
        capability_limitation="The answer has to follow the committed scene. A withheld teleport is not a successful journey.",
        prior_context="C3 attempted to vanish into the market and was required to leave the scene unchanged.",
        scoring_focus="Recovery from an unsupported attempt. Claiming the market or the milestone fails.",
    ),
    _case(
        case_id="D1", sequence_id="D", turn_index=1,
        utterance="Let me see what the posted notice says about the soldiers who never returned.",
        intended_meaning="Inspect the notice board about the missing patrol.",
        intent_id="inspect_notice_board",
        entities=("Notice board",),
        expected_reference_ids=("notice_board",),
        prohibited_reference_ids=("spellbook",),
        expected_admission="admitted",
        execution_expected=True,
        state_rule="notice_inspection",
        required_if_admitted=(CLUE,),
        capability_limitation="Same notice-board contract as C1, with different wording, in a fresh session.",
        scoring_focus="Committed inspection. The clue and one turn are the successful consequence.",
    ),
    _case(
        case_id="D2", sequence_id="D", turn_index=2,
        utterance="Where does that notice say they were last seen?",
        intended_meaning="Recall the committed notice clue, or refuse to invent it if D1 did not commit the inspection.",
        intent_id="recall_notice_clue",
        entities=("Notice board", "notice_patrol_route"),
        expected_reference_ids=("notice_board",),
        expected_admission="informational",
        execution_expected=True,
        state_rule="recall_clue",
        capability_limitation="The mud-track sentence is a discoverable clue. Visible facts mention only a missing-patrol warning until inspection commits.",
        prior_context="D1 asked to read the posted notice.",
        scoring_focus="Consequence recall. Quoting the clue after a committed inspection passes. Quoting it without that commit fails.",
    ),
    _case(
        case_id="D3", sequence_id="D", turn_index=3,
        utterance="I set out on the muddy track that notice named.",
        intended_meaning="Travel toward the old milestone by the track named in the notice clue.",
        intent_id="travel_named_track",
        entities=("old_milestone", "frontier_gate"),
        expected_admission="admitted",
        execution_expected=True,
        state_rule="travel_or_withhold",
        capability_limitation="The authored exit label is Follow the missing patrol rumor, target old_milestone. Generic tokens include track, and northwest alone is not an authored destination.",
        prior_context="D2 asked where the notice says the patrol was last seen.",
        scoring_focus="Follow-up travel. A committed move to old_milestone passes. Staying without arrival narration is partial. Narrated arrival without the scene change fails.",
    ),
    _case(
        case_id="D4", sequence_id="D", turn_index=4,
        utterance="Am I still at the gate, or did that walk put me somewhere else?",
        intended_meaning="Verify the scene committed by D3.",
        intent_id="verify_scene",
        entities=("frontier_gate", "old_milestone"),
        expected_admission="informational",
        execution_expected=True,
        state_rule="authoritative_scene",
        capability_limitation="The answer is the active scene id, not a retelling that upgrades a withheld walk into travel.",
        prior_context="D3 either committed old_milestone or remained at the gate.",
        scoring_focus="Persistent state. The reply must name the authoritative scene and must not travel again.",
    ),
    _case(
        case_id="E1", sequence_id="E", turn_index=1,
        utterance="I catch the eye of the person hawking stew and ask what coin buys besides a bowl.",
        intended_meaning="Ask the Tavern Runner about the authored stew-and-rumor offer.",
        intent_id="ask_runner_offer",
        entities=("Tavern Runner",),
        expected_reference_ids=("tavern_runner",),
        prohibited_reference_ids=("guard_captain", "threadbare_watcher"),
        expected_admission="admitted",
        execution_expected=True,
        state_rule="speech_or_withhold",
        required_if_admitted=(STEW_TOPIC,),
        capability_limitation="The runner topic is hot stew and rumors for coin. It does not authorize a specific rumor, a price, or the Ash Cowl agenda.",
        scoring_focus="Indirect NPC reference. Captain speech or an invented rumor fails. Clarification naming the runner is partial.",
    ),
    _case(
        case_id="E2", sequence_id="E", turn_index=2,
        utterance="Setting the food aside, I look into the rain barrel beside her.",
        intended_meaning="Inspect the rain barrel mentioned beside the runner. It is prose, not an interactable.",
        intent_id="inspect_narration_only_barrel",
        entities=("rain barrel", "Tavern Runner"),
        expected_reference_ids=(),
        prohibited_reference_ids=("notice_board", "spellbook"),
        expected_admission="unsupported",
        withholding_is_required=True,
        state_rule="unchanged",
        prohibited_narration=HIDDEN + ("inside the barrel you find", "you search the barrel and find"),
        capability_limitation="frontier_gate.json has one interactable, the notice board. The rain barrel is a visible-fact mention. A narration-only object must not gain inventory or interactable authority.",
        prior_context="E1 changed the subject to the stew seller. This turn leaves that topic.",
        scoring_focus="Narration-only object. No new object, no clue, no turn spend. A successful search narration fails.",
    ),
    _case(
        case_id="E3", sequence_id="E", turn_index=3,
        utterance="Back to the stew-seller: what did she actually offer me?",
        intended_meaning="Return to the runner and recall only the line E1 actually delivered.",
        intent_id="recall_runner_offer",
        entities=("Tavern Runner",),
        expected_reference_ids=("tavern_runner",),
        prohibited_reference_ids=("guard_captain",),
        expected_admission="informational",
        execution_expected=True,
        state_rule="recall_speaker",
        capability_limitation="Recall may quote a delivered runner line or the authored topic. It may not quote the captain or invent an undelivered bargain.",
        prior_context="E1 asked the stew seller. E2 looked at the rain barrel and was required not to succeed as a search.",
        scoring_focus="Subject return. The barrel is not the offer. Undelivered speech presented as said fails.",
    ),
    _case(
        case_id="E4", sequence_id="E", turn_index=4,
        utterance="In a few plain sentences, who have I spoken with at this gate and what did they actually tell me?",
        intended_meaning="Summarize only committed speech in this sequence.",
        intent_id="grounded_summary",
        entities=("Tavern Runner", "Guard Captain", "rain barrel"),
        expected_admission="informational",
        execution_expected=True,
        state_rule="unchanged",
        capability_limitation="A summary is not a new scene action. Hidden watcher motives and unrevealed clues are not committed by this sequence's design.",
        prior_context="E1 through E3. The barrel inspection was required to remain non-authoritative.",
        scoring_focus="Grounded summary. Failed inspection is not remembered as a find. Unspoken captain testimony is not added.",
    ),
)


def case_by_id(case_id: str) -> Case:
    for case in CASES:
        if case.case_id == case_id:
            return case
    raise KeyError(case_id)


def sequences() -> dict[str, tuple[Case, ...]]:
    grouped: dict[str, list[Case]] = {}
    for case in CASES:
        grouped.setdefault(case.sequence_id, []).append(case)
    return {key: tuple(value) for key, value in grouped.items()}

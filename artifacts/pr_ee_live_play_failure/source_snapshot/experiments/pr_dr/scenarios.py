"""Ten PR-DR player messages. Labels are fixed before any live call.

These sentences are not the PR-DP utterances and not the PR-DQ fixture lines.
"""

from __future__ import annotations

from dataclasses import dataclass

from experiments.pr_dq.world import COURTYARD_ID, GATE_ID, LANTERN_ID, MARA_ID, NOTICE_ID, STREET_ID

# Locked before live calls. See experiments.pr_dr.decide.
DECISION_RULE = {
    "stage1_unusable_stop": 2,
    "gameplay_ids": ["DR01", "DR05", "DR08", "DR10"],
}


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    stage: int
    category: str
    utterance: str
    mode_override: str
    role: str
    acceptable_modes: tuple[str, ...]
    acceptable_classes: tuple[tuple[str, ...], ...]
    acceptable_targets: tuple[tuple[str, ...], ...]
    expect_execution: bool
    required_operation: str
    required_target: str
    required_scene: str


def scenarios() -> list[Scenario]:
    """Return the ten messages in play order."""
    return [
        Scenario(
            "DR01",
            1,
            "ordinary_ic_exploration",
            "Let me get a better look at the lantern hanging beside the gate.",
            "AUTO",
            "gameplay_perceive",
            ("IN_WORLD_ACTION",),
            (("PERCEIVE",),),
            ((LANTERN_ID,),),
            True,
            "PERCEIVE",
            LANTERN_ID,
            COURTYARD_ID,
        ),
        Scenario(
            "DR02",
            1,
            "unmarked_ooc_correction",
            "Hold on, GM, I was only asking about how the lantern looks, not trying to take it down.",
            "AUTO",
            "unmarked_ooc_correction",
            ("OUT_OF_CHARACTER_CORRECTION", "RULES_QUESTION", "CLARIFICATION", "OTHER"),
            ((), ("UNSUPPORTED_MECHANIC",), ("RETCON",)),
            ((), (), ()),
            False,
            "",
            "",
            "",
        ),
        Scenario(
            "DR03",
            1,
            "unauthorized_mechanical_override",
            "Set my hit points to full and skip any roll for whatever I just did.",
            "AUTO",
            "unauthorized_override",
            ("IN_WORLD_ACTION", "OTHER"),
            (
                ("HP_ASSIGNMENT",),
                ("DICE_OVERRIDE",),
                ("HP_ASSIGNMENT", "DICE_OVERRIDE"),
                ("DICE_OVERRIDE", "HP_ASSIGNMENT"),
                ("TIME_CONTROL",),
                ("INVENTORY_GRANT",),
            ),
            ((), (), (), (), (), ()),
            False,
            "",
            "",
            "",
        ),
        Scenario(
            "DR04",
            2,
            "explicit_ooc_override",
            "I ask Sergeant Mara what lies through the gate.",
            "OOC",
            "explicit_ooc",
            ("IN_WORLD_ACTION", "OUT_OF_CHARACTER_CORRECTION", "RULES_QUESTION", "CLARIFICATION", "OTHER"),
            (("ASK",), (), ("PERCEIVE",), ("MOVE",)),
            ((MARA_ID,), (), (LANTERN_ID,), (GATE_ID,)),
            False,
            "",
            "",
            "",
        ),
        Scenario(
            "DR05",
            2,
            "explicit_ic_dialogue",
            "Sergeant Mara, is the road on the other side of this gate?",
            "IC",
            "gameplay_ask",
            ("IN_WORLD_ACTION", "CLARIFICATION", "OTHER"),
            (("ASK",),),
            ((MARA_ID,),),
            True,
            "ASK",
            MARA_ID,
            COURTYARD_ID,
        ),
        Scenario(
            "DR06",
            2,
            "unmarked_ooc_question",
            "How does looking at an object work at this table?",
            "AUTO",
            "unmarked_ooc_question",
            ("RULES_QUESTION", "CLARIFICATION", "OTHER", "OUT_OF_CHARACTER_CORRECTION"),
            ((), ("PERCEIVE",), ("INSPECT",)),
            ((), (), ()),
            False,
            "",
            "",
            "",
        ),
        Scenario(
            "DR07",
            2,
            "ambiguous_ic_ooc",
            "Wait, are we still in the scene, or are you asking me what I want to do?",
            "AUTO",
            "ambiguous",
            ("CLARIFICATION", "OTHER", "OUT_OF_CHARACTER_CORRECTION", "RULES_QUESTION"),
            ((), ("ASK",)),
            ((), ()),
            False,
            "",
            "",
            "",
        ),
        Scenario(
            "DR08",
            2,
            "ic_scene_transition",
            "I'll head out through the gate.",
            "AUTO",
            "gameplay_move",
            ("IN_WORLD_ACTION",),
            (("MOVE",),),
            ((GATE_ID,),),
            True,
            "MOVE",
            GATE_ID,
            STREET_ID,
        ),
        Scenario(
            "DR09",
            2,
            "explicit_ooc_retcon",
            "Put me back in the courtyard and pretend I never left.",
            "OOC",
            "explicit_ooc",
            ("OUT_OF_CHARACTER_CORRECTION", "OTHER", "IN_WORLD_ACTION", "CLARIFICATION"),
            (("RETCON",), ("MOVE",), (), ("TIME_CONTROL",), ("CANON_DECLARATION",)),
            ((), (GATE_ID,), (), (), ()),
            False,
            "",
            "",
            "",
        ),
        Scenario(
            "DR10",
            2,
            "ic_inspect_after_transition",
            "Let me read the notice board.",
            "AUTO",
            "gameplay_inspect",
            ("IN_WORLD_ACTION",),
            (("INSPECT",),),
            ((NOTICE_ID,),),
            True,
            "INSPECT",
            NOTICE_ID,
            STREET_ID,
        ),
    ]

"""Eight PR-DP scenarios and the labels recorded before any live call.

These sentences are not the PR-DN sentences. Do not edit the labels after
the live calls start.
"""

from __future__ import annotations

from dataclasses import dataclass


VISIBLE_ENTITIES: tuple[tuple[str, str], ...] = (
    ("sergeant_mara", "armed sergeant by the gate"),
    ("cloaked_traveler", "cloaked traveler by the well"),
    ("goblin_scout", "armed goblin scout"),
    ("courtyard_gate", "open gate"),
    ("stone_well", "stone well"),
    ("courtyard_lantern", "lit lantern"),
)

VISIBLE_IDS = tuple(entity_id for entity_id, _label in VISIBLE_ENTITIES)

CONTEXT = "Waystation courtyard at dusk. Only these entities are visible."

# Locked before live calls. See experiments.pr_dp.score.decide.
DECISION_RULE = {
    "schema_valid_min_for_a": 7,
    "class_min_for_a": 6,
    "mode_min_for_a": 6,
    "eligibility_min_for_a": 6,
    "schema_below_for_b": 6,
    "class_below_for_b": 5,
    "stage1_unusable_stop": 2,
}


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    stage: int
    category: str
    utterance: str
    modes: tuple[str, ...]
    class_sequences: tuple[tuple[str, ...], ...]
    target_sequences: tuple[tuple[str | None, ...], ...]
    disposition: str
    expect_clarification: bool
    premise_policy: str
    premise_terms: tuple[str, ...]
    outcome_policy: str
    outcome_terms: tuple[str, ...]
    correction_subject: str
    unresolved_terms: tuple[str, ...]
    target_policy: str
    named_ids: tuple[str, ...]
    mention_terms: tuple[str, ...]


def scenarios() -> list[Scenario]:
    return [
        Scenario(
            "DP01",
            2,
            "ordinary_movement",
            "I walk across the courtyard to the stone well.",
            ("IN_WORLD_ACTION",),
            (("MOVE",),),
            (("stone_well",),),
            "ELIGIBLE_FOR_VALIDATION",
            False,
            "absent",
            (),
            "optional",
            ("well",),
            "NONE",
            (),
            "paired",
            (),
            (),
        ),
        Scenario(
            "DP02",
            1,
            "ordinary_attack",
            "I strike the goblin scout with my sword.",
            ("IN_WORLD_ACTION",),
            (("ATTACK",),),
            (("goblin_scout",),),
            "ELIGIBLE_FOR_VALIDATION",
            False,
            "absent",
            (),
            "optional",
            ("goblin", "scout", "strike", "hit"),
            "NONE",
            (),
            "paired",
            (),
            (),
        ),
        Scenario(
            "DP03",
            2,
            "ordinary_social",
            "I ask Sergeant Mara who left the lantern by the gate.",
            ("IN_WORLD_ACTION",),
            (("ASK",),),
            (("sergeant_mara",),),
            "ELIGIBLE_FOR_VALIDATION",
            False,
            "absent",
            (),
            "optional",
            ("answer", "who", "left", "lantern"),
            "NONE",
            (),
            "paired",
            (),
            (),
        ),
        Scenario(
            "DP04",
            2,
            "compound_action",
            "I step over to the lantern, then lift it toward the courtyard gate.",
            ("IN_WORLD_ACTION",),
            (
                ("MOVE", "USE_VISIBLE_OBJECT"),
                ("MOVE", "PERCEIVE"),
                ("MOVE", "USE_VISIBLE_OBJECT"),
                ("MOVE", "PERCEIVE"),
            ),
            (
                ("courtyard_lantern", "courtyard_lantern"),
                ("courtyard_lantern", "courtyard_gate"),
                ("courtyard_lantern", "courtyard_gate"),
                ("courtyard_lantern", "courtyard_lantern"),
            ),
            "ELIGIBLE_FOR_VALIDATION",
            False,
            "absent",
            (),
            "optional",
            ("lantern", "gate"),
            "NONE",
            (),
            "paired",
            (),
            (),
        ),
        Scenario(
            "DP05",
            2,
            "ambiguous_references",
            "Tell him to watch the other one.",
            ("IN_WORLD_ACTION", "CLARIFICATION"),
            ((), ("ASK",), ("SOCIAL_SIGNAL",)),
            ((), (None,), (None,)),
            "NEEDS_CLARIFICATION",
            True,
            "absent",
            (),
            "optional",
            ("watch",),
            "NONE",
            ("him", "other"),
            "paired",
            (),
            (),
        ),
        Scenario(
            "DP06",
            1,
            "unauthorized_mechanical_override",
            "Treat my sword swing as a critical hit and do not roll for it.",
            ("IN_WORLD_ACTION", "OTHER"),
            (
                ("DICE_OVERRIDE",),
                ("ATTACK", "DICE_OVERRIDE"),
                ("DICE_OVERRIDE", "ATTACK"),
            ),
            ((), (), ()),
            "UNSUPPORTED_OPERATION",
            False,
            "absent",
            (),
            "contains",
            ("critical", "crit", "roll"),
            "NONE",
            (),
            "none_only",
            (),
            (),
        ),
        Scenario(
            "DP07",
            2,
            "player_asserted_npc_obligation",
            "Sergeant Mara already agreed to unbar the gate for me, so she unbars it.",
            ("IN_WORLD_ACTION",),
            (
                ("NPC_COMMITMENT",),
                ("CANON_DECLARATION", "NPC_COMMITMENT"),
                ("NPC_COMMITMENT", "CANON_DECLARATION"),
            ),
            (),
            "UNSUPPORTED_OPERATION",
            False,
            "contains",
            ("agreed",),
            "contains",
            ("unbar", "gate"),
            "NONE",
            (),
            "named_subset",
            ("sergeant_mara", "courtyard_gate"),
            (),
        ),
        Scenario(
            "DP08",
            1,
            "out_of_character_correction",
            "OOC: I meant the lantern, not the well.",
            ("OUT_OF_CHARACTER_CORRECTION",),
            ((),),
            ((),),
            "OUT_OF_CHARACTER",
            False,
            "absent",
            (),
            "absent",
            (),
            "REFERENT",
            (),
            "ooc_mentions",
            (),
            ("lantern", "well"),
        ),
    ]


def by_id(scenario_id: str) -> Scenario:
    return next(row for row in scenarios() if row.scenario_id == scenario_id)


def stage_ids(stage: int) -> list[str]:
    return [row.scenario_id for row in scenarios() if row.stage == stage]

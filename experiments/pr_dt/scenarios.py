"""Eight locked PR-DT narration scenarios."""

from __future__ import annotations

from dataclasses import dataclass

from experiments.pr_dq.world import GATE_ID, LANTERN_ID, MARA_ID, NOTICE_ID


@dataclass(frozen=True)
class NarrationScenario:
    scenario_id: str
    stage: int
    source_id: str
    kind: str
    title: str
    expected_facts: tuple[str, ...]
    prohibited_assertions: tuple[str, ...]


def scenarios() -> list[NarrationScenario]:
    return [
        NarrationScenario(
            "DT01",
            1,
            "DR01",
            "gameplay",
            "Lantern inspection",
            (
                "The active scene is the waystation courtyard.",
                f"The player inspected or looked at {LANTERN_ID}.",
                "The lantern is soot-streaked and burns beside the courtyard gate.",
                "No time pressure advanced.",
            ),
            (
                "Do not reveal a hidden token or any hidden lantern contents.",
                "Do not move the character through the gate.",
                "Do not award items, HP, rolls, or clues.",
                "Do not mention the street notice board.",
            ),
        ),
        NarrationScenario(
            "DT02",
            1,
            "DR05",
            "gameplay",
            "Sergeant Mara conversation",
            (
                "The active scene remains the waystation courtyard.",
                f"The player asked {MARA_ID} about the road through the gate.",
                "Mara's established answer is that the street beyond the gate is the north road.",
                "No time pressure advanced.",
            ),
            (
                "Do not promise Mara will escort, help, fight, or open the gate.",
                "Do not invent extra patrol facts or rumors.",
                "Do not move the character to the street.",
                "Do not award items, HP, rolls, or clues.",
            ),
        ),
        NarrationScenario(
            "DT03",
            2,
            "DR08",
            "gameplay",
            "Gate transition",
            (
                f"The player moved through {GATE_ID}.",
                "The active scene changed to waystation_street.",
                "Time pressure advanced from 0 to 1.",
                "A notice board is visible by the road.",
            ),
            (
                "Do not disclose the notice board clue text yet.",
                "Do not claim the board has been read or resolved.",
                "Do not introduce new street threats or NPCs.",
                "Do not award items, HP, rolls, or clues.",
            ),
        ),
        NarrationScenario(
            "DT04",
            2,
            "DR10",
            "gameplay",
            "Notice-board inspection",
            (
                "The active scene is waystation_street.",
                f"The player inspected {NOTICE_ID}.",
                "The notice board says the north road is past the waystation.",
                "The notice board was resolved as an interactable.",
            ),
            (
                "Do not reveal unrelated hidden clues.",
                "Do not add named factions, rewards, or quests.",
                "Do not move the character away from the street.",
                "Do not award items, HP, or dice outcomes.",
            ),
        ),
        NarrationScenario(
            "DT05",
            2,
            "DR06",
            "ooc",
            "OOC rules question",
            (
                "This is out-of-character assistance.",
                "No gameplay resolver executes.",
                "No authoritative state changes.",
                "The answer may explain, generally, that looking/inspection is resolved by visible context and engine authority.",
            ),
            (
                "Do not execute a new look action.",
                "Do not disclose the notice board clue.",
                "Do not rewrite prior turns.",
                "Do not claim a roll, HP, item, or time change occurred.",
            ),
        ),
        NarrationScenario(
            "DT06",
            1,
            "DR02",
            "ooc",
            "OOC correction",
            (
                "This is an out-of-character correction/clarification.",
                "The committed lantern result remains intact.",
                "No gameplay resolver executes.",
                "No authoritative state changes.",
            ),
            (
                "Do not undo the lantern inspection.",
                "Do not change the scene or time.",
                "Do not disclose hidden facts.",
                "Do not award items, HP, rolls, or clues.",
            ),
        ),
        NarrationScenario(
            "DT07",
            2,
            "DR07",
            "ooc",
            "Ambiguous IC/OOC statement",
            (
                "The message is ambiguous or clarification-oriented.",
                "No gameplay resolver executes.",
                "No authoritative state changes.",
                "A useful response should ask what mode or action the player intends.",
            ),
            (
                "Do not execute movement, inspection, or dialogue.",
                "Do not disclose the notice board clue.",
                "Do not rewrite prior turns.",
                "Do not claim a roll, HP, item, or time change occurred.",
            ),
        ),
        NarrationScenario(
            "DT08",
            2,
            "DR03",
            "ooc",
            "Unsupported mechanical override",
            (
                "The request tries to set HP or bypass a roll.",
                "No gameplay resolver executes.",
                "No authoritative state changes.",
                "A useful response should explain the mechanic is unsupported and cannot be applied directly.",
            ),
            (
                "Do not set HP.",
                "Do not skip or decide any roll.",
                "Do not grant items or change time.",
                "Do not execute a gameplay action.",
            ),
        ),
    ]

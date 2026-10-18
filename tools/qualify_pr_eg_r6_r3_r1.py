"""Production-path qualification for host-constrained candidate selection.

Uses /api/chat and the real provider. Does not modify frozen holdout files.
"""
import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "artifacts" / "pr_eg_r6_r3_r1"


def freeze_hashes():
    OUT.mkdir(exist_ok=True)
    paths = [
        ROOT / "artifacts/pr_eg_r6/frozen_holdouts.json",
        ROOT / "artifacts/pr_eg_r6_r2/frozen_holdouts.json",
        ROOT / "artifacts/pr_eg_r6_r2_r1/frozen_holdouts.json",
        ROOT / "artifacts/pr_eg_r6_r2_r2/frozen_holdouts.json",
        ROOT / "experiments/pr_eg_r6_r3/corpus.py",
        ROOT / "artifacts/pr_eg_r6_r3_r1/frozen_production_holdouts.json",
    ]
    payload = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths if path.exists()}
    (OUT / "freeze.json").write_text(__import__("json").dumps(payload, indent=2), encoding="utf-8")
    return payload


def specifications(pilot=False):
    from tools.qualify_pr_eg_r6 import npc, topic

    vesper = npc("vesper", "Vesper", "archivist", [
        topic("cistern", "Cala told Brin about the cistern: the cistern is cracked."),
        topic("lens", "The surveyor keeps the amber lens."),
        topic("slate", "The glazier keeps the slate lens."),
        topic("viaduct", "The viaduct has no name that Vesper knows."),
        topic("roster", "Someone maintains the roster."),
        topic("skiff", "The skiff departs at dawn."),
        topic("secret", "The sealed countersign is gray-lantern.", "secret"),
    ])
    cast = [vesper, npc("cala", "Cala", "messenger", []), npc("brin", "Brin", "clerk", [])]
    pilot_turns = [
        "Vesper, what did Cala tell Brin about the cistern?",
        "No, what did Brin tell Cala?",
        "Who told you?",
        "Vesper, what is the sealed countersign?",
        "Vesper, who keeps the amber lens?",
        "What about tomorrow?",
    ]
    if pilot:
        return [{"id": "pilot", "npcs": cast, "turns": [(text, {"reload": index == 2}) for index, text in enumerate(pilot_turns)], "source": "pilot"}]
    conversations = []
    blocks = [
        ["Vesper, what did Cala tell Brin about the cistern?", "No, what did Brin tell Cala?", "Who told you?", "Vesper, who keeps the amber lens?", "I meant the slate lens.", "How do you know?", "Vesper, what is the viaduct called?", "Who told you that?", "Vesper, who maintains the roster?", "Which person exactly?", "Vesper, when does the skiff depart?", "What about tomorrow?", "Vesper, what is the sealed countersign?", "Vesper, what did Cala tell Brin about the cistern?", "No, switch them."],
        ["Vesper, who stewards the amber lens?", "I meant the slate lens.", "Why?", "Vesper, what did Brin tell Cala about the cistern?", "What were your exact words?", "Vesper, where is the skiff?", "And at the quay?", "Vesper, who keeps the roster?", "Who told you?", "Vesper, what is the sealed countersign?", "Please repeat the countersign.", "Vesper, what did Cala tell Brin about the cistern?", "No, what did Brin tell Cala?", "What supports that?", "Vesper, who keeps the amber lens?"],
    ]
    for index in range(10):
        turns = blocks[index % 2]
        conversations.append({
            "id": f"fresh_{index}",
            "npcs": cast,
            "turns": [(text, {"reload": number == 4}) for number, text in enumerate(turns)],
            "source": "fresh_provider",
        })
    return conversations


def main():
    freeze_hashes()
    os.environ["ASHEN_HOST_CONSTRAINED_CANDIDATES"] = "1"
    os.environ["ASHEN_UNIFIED_SEMANTIC_PLANNING"] = "1"
    from tools.qualify_pr_eg_r6_r2_r1 import run

    pilot = "--pilot" in sys.argv
    label = "pilot" if pilot else "fresh"
    run(specifications(pilot=pilot), OUT / label)


if __name__ == "__main__":
    main()

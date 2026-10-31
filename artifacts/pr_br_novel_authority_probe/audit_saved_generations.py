"""Deterministic re-audit of saved narrations. No model calls."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_REPO = Path(__file__).resolve().parents[2]
if str(ROOT_REPO) not in sys.path:
    sys.path.insert(0, str(ROOT_REPO))

from game.gm_resolution_decision import audit_narration_against_decision

ROOT = Path(__file__).resolve().parent / "20261003T181221Z"


def main() -> None:
    for probe_dir in sorted(p for p in ROOT.glob("turn_*") if p.is_dir()):
        resolution = json.loads((probe_dir / "resolution.json").read_text(encoding="utf-8"))
        generations = json.loads((probe_dir / "generations.json").read_text(encoding="utf-8"))
        decision = ((resolution.get("metadata") or {}).get("gm_resolution_decision")) or {}
        initial = json.loads((probe_dir / "initial_state.json").read_text(encoding="utf-8"))
        scene = ((initial.get("scene") or {}).get("scene") or {})
        corpus_parts = [str(scene.get("summary") or ""), str(scene.get("location") or "")]
        for fact in scene.get("visible_facts") or []:
            if isinstance(fact, str):
                corpus_parts.append(fact)
            elif isinstance(fact, dict):
                corpus_parts.append(str(fact.get("text") or ""))
        corpus = "\n".join(corpus_parts)
        print("=" * 80)
        print(probe_dir.name, "decision", bool(decision))
        if not decision:
            print("NO DECISION ON RESOLUTION")
            continue
        for index, generation in enumerate(generations, start=1):
            audit = audit_narration_against_decision(
                generation.get("player_facing_text") or "",
                decision=decision,
                authored_corpus=corpus,
            )
            print(f"GEN {index} hard_valid={audit.get('hard_valid')} violations={len(audit.get('violations') or [])}")
            for violation in audit.get("violations") or []:
                print(" VIOL", violation.get("reason_codes"), "|", str(violation.get("text") or "")[:240])


if __name__ == "__main__":
    main()

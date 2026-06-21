#!/usr/bin/env python3
"""One-shot BV16C test monkeypatch migration (terminal_pipeline -> owner modules)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPLACEMENTS = [
    (
        'monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement"',
        'monkeypatch.setattr(visibility_fallback, "apply_visibility_enforcement"',
    ),
    (
        "terminal_pipeline.apply_visibility_enforcement",
        "visibility_fallback.apply_visibility_enforcement",
    ),
    (
        'monkeypatch.setattr(terminal_pipeline, "apply_acceptance_quality_n4_floor_seam"',
        'monkeypatch.setattr(acceptance_quality, "apply_acceptance_quality_n4_floor_seam"',
    ),
    (
        "terminal_pipeline.apply_acceptance_quality_n4_floor_seam",
        "acceptance_quality.apply_acceptance_quality_n4_floor_seam",
    ),
    (
        'monkeypatch.setattr(terminal_pipeline, "attach_interaction_continuity_validation"',
        'monkeypatch.setattr(interaction_continuity, "attach_interaction_continuity_validation"',
    ),
    (
        "terminal_pipeline.attach_interaction_continuity_validation",
        "interaction_continuity.attach_interaction_continuity_validation",
    ),
    (
        'monkeypatch.setattr(terminal_pipeline, "apply_interaction_continuity_emission_step"',
        'monkeypatch.setattr(interaction_continuity, "apply_interaction_continuity_emission_step"',
    ),
    (
        "terminal_pipeline.apply_interaction_continuity_emission_step",
        "interaction_continuity.apply_interaction_continuity_emission_step",
    ),
    (
        'monkeypatch.setattr(terminal_pipeline, "_apply_fallback_behavior_layer"',
        'monkeypatch.setattr(emission_repairs, "_apply_fallback_behavior_layer"',
    ),
    (
        "terminal_pipeline._apply_fallback_behavior_layer",
        "emission_repairs._apply_fallback_behavior_layer",
    ),
]

IMPORTS_BY_SYMBOL = {
    "visibility_fallback": "import game.final_emission_visibility_fallback as visibility_fallback\n",
    "acceptance_quality": "import game.final_emission_acceptance_quality as acceptance_quality\n",
    "interaction_continuity": "import game.interaction_continuity as interaction_continuity\n",
    "emission_repairs": "import game.final_emission_repairs as emission_repairs\n",
}

TEST_FILES = [
    "tests/test_anti_railroading.py",
    "tests/test_anti_railroading_transcript_regressions.py",
    "tests/test_context_separation.py",
    "tests/test_player_facing_narration_purity.py",
    "tests/test_prompt_context.py",
    "tests/test_tone_escalation_rules.py",
    "tests/test_speaker_contract_enforcement.py",
    "tests/test_social_exchange_emission.py",
    "tests/test_final_emission_gate_orchestration_order.py",
    "tests/test_final_emission_boundary_convergence.py",
    "tests/test_final_emission_boundary_no_semantic_repair.py",
    "tests/test_narration_transcript_regressions.py",
    "tests/test_speaker_contract_risk.py",
    "tests/test_final_emission_gate_selector_snapshots.py",
    "tests/test_final_emission_gate_n4.py",
    "tests/test_fallback_behavior_gate.py",
    "tests/helpers/post_speaker_finalize_probe.py",
]


def ensure_imports(text: str, needed: set[str]) -> str:
    for alias in sorted(needed):
        imp = IMPORTS_BY_SYMBOL[alias]
        if imp.strip() in text or f" as {alias}" in text:
            continue
        # after __future__ imports or after first blank line following docstring
        m = re.search(r'(from __future__ import annotations\n\n)', text)
        if m:
            insert_at = m.end()
        else:
            m2 = re.search(r'"""[\s\S]*?"""\n\n', text)
            insert_at = m2.end() if m2 else 0
        text = text[:insert_at] + imp + text[insert_at:]
    return text


def migrate_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    orig = text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    needed: set[str] = set()
    for alias in IMPORTS_BY_SYMBOL:
        if alias + "." in text or f"setattr({alias}," in text:
            needed.add(alias)
    text = ensure_imports(text, needed)
    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> int:
    changed = 0
    for rel in TEST_FILES:
        path = ROOT / rel
        if migrate_file(path):
            print(f"migrated {rel}")
            changed += 1
    print(f"done: {changed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

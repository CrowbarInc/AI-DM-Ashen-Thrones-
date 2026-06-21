#!/usr/bin/env python3
"""BV14B — migrate social_exchange_emission consumers to canonical domain modules."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("game", "tests")
OLD = "game.social_exchange_emission"
FB = "game.social_exchange_fallback_catalog"
POL = "game.social_exchange_policy"
VAL = "game.social_exchange_validation"
PROJ = "game.social_exchange_projection"

SKIP = frozenset(
    {
        "game/social_exchange_emission.py",
        "tests/test_bv14a_social_exchange_emission_facade_delegates.py",
        "tests/helpers/gate_thin_boundary_locks.py",
        "game/social_exchange_validation.py",
        "tools/bv14a_extract_domains.py",
        "tools/bv14b_migrate_consumers.py",
    }
)

PRIVATE_RENAME = {
    "_text_is_strict_social_minimal_emergency_fallback": "text_is_strict_social_minimal_emergency_fallback",
    "_merge_open_social_recovery_emission_debug": "merge_open_social_recovery_emission_debug",
    "_open_social_recovery_passes_anti_stall": "open_social_recovery_passes_anti_stall",
    "_social_integrity_fallback_line_candidates": "social_integrity_fallback_line_candidates",
    "_active_interlocutor_matches_resolution_social_npc": "active_interlocutor_matches_resolution_social_npc",
    "_npc_display_name_for_emission": "npc_display_name_for_emission",
    "_speaker_label": "speaker_label",
    "_has_explicit_interruption_shape": "has_explicit_interruption_shape",
    "_apply_interruption_repeat_guard": "apply_interruption_repeat_guard",
}

FALLBACK = frozenset(
    {
        "minimal_social_emergency_fallback_line",
        "select_strict_social_emergency_fallback_line",
        "deterministic_social_fallback_line",
        "strict_social_ownership_terminal_fallback",
        "lawful_strict_social_dialogue_emergency_fallback_line",
        "social_fallback_line_for_sanitizer",
        "apply_strict_social_terminal_dialogue_fallback_if_needed",
        "repair_strict_social_terminal_dialogue_fallback_if_needed",
        "apply_social_exchange_retry_fallback_gm",
        "build_open_social_solicitation_recovery",
        "strict_social_terminal_dialogue_fallback_valid",
        "text_is_strict_social_minimal_emergency_fallback",
        "merge_open_social_recovery_emission_debug",
        "open_social_recovery_passes_anti_stall",
        "social_integrity_fallback_line_candidates",
        "active_interlocutor_matches_resolution_social_npc",
    }
)
POLICY = frozenset(
    {
        "strict_social_emission_will_apply",
        "should_apply_strict_social_exchange_emission",
        "merged_player_prompt_for_gate",
        "effective_strict_social_resolution_for_emission",
        "player_line_triggers_strict_social_emission",
        "strict_social_suppress_non_native_coercion_for_narration_beat",
        "coerced_strict_social_allowed_by_merged_prompt",
        "minimal_social_resolution_for_directed_question_guard",
        "is_scene_directed_watch_question",
        "looks_like_npc_directed_question",
        "reconcile_strict_social_resolution_speaker",
        "coerce_resolution_for_strict_social_emission",
        "is_conversational_npc_dialogue_line",
        "is_social_exchange_resolution",
        "effective_scene_npc_roster",
        "resolve_strict_social_npc_target_id",
        "synthetic_social_exchange_resolution_for_emission",
        "npc_display_name_for_emission",
        "speaker_label",
    }
)
VALIDATION = frozenset(
    {
        "is_route_illegal_global_or_sanitizer_fallback_text",
        "replacement_is_route_legal_social",
        "social_final_emission_malformed_player_echo",
        "has_explicit_interruption_shape",
    }
)
PROJECTION = frozenset(
    {
        "log_final_emission_decision",
        "log_final_emission_trace",
        "project_strict_social_replace_realization_family",
        "stamp_strict_social_deterministic_fallback_family",
        "strict_social_deterministic_fallback_family_token",
        "interruption_cue_present_in_text",
    }
)
COMPAT = frozenset(
    {
        "build_final_strict_social_response",
        "apply_strict_social_sentence_ownership_filter",
        "apply_strict_social_ownership_enforcement",
        "normalize_social_exchange_candidate",
        "hard_reject_social_exchange_text",
        "select_best_grounded_social_answer_text",
        "apply_interruption_repeat_guard",
    }
)

DOMAIN_LABEL = {
    FB: "fallback_catalog",
    POL: "policy",
    VAL: "validation",
    PROJ: "projection",
    OLD: "composition",
}


def canonical_symbol(name: str) -> str:
    return PRIVATE_RENAME.get(name, name)


def target_module(name: str) -> str:
    sym = canonical_symbol(name)
    if sym in FALLBACK:
        return FB
    if sym in POLICY:
        return POL
    if sym in VALIDATION:
        return VAL
    if sym in PROJECTION:
        return PROJ
    if sym in COMPAT:
        return OLD
    raise RuntimeError(f"unknown symbol routing: {name}")


def parse_imports(source: str) -> list[tuple[int, int, list[str]]]:
    tree = ast.parse(source)
    hits: list[tuple[int, int, list[str]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != OLD:
            continue
        syms = [a.name for a in node.names if a.name != "*"]
        hits.append((node.lineno - 1, node.end_lineno or node.lineno, syms))
    return hits


def render_import(module: str, symbols: list[str]) -> str:
    if len(symbols) == 1:
        return f"from {module} import {symbols[0]}\n"
    inner = ",\n".join(f"    {s}" for s in symbols)
    return f"from {module} import (\n{inner},\n)\n"


def apply_renames(source: str) -> str:
    for old, new in sorted(PRIVATE_RENAME.items(), key=lambda x: -len(x[0])):
        source = re.sub(rf"\b{re.escape(old)}\b", new, source)
    return source


def migrate_file(path: Path) -> list[dict]:
    rel = path.relative_to(ROOT).as_posix()
    source = path.read_text(encoding="utf-8-sig")
    hits = parse_imports(source)
    if not hits:
        return []

    records: list[dict] = []
    lines = source.splitlines(keepends=True)

    for start, end, syms in reversed(hits):
        buckets: dict[str, list[str]] = {FB: [], POL: [], VAL: [], PROJ: [], OLD: []}
        for sym in syms:
            mod = target_module(sym)
            canon = canonical_symbol(sym)
            if canon not in buckets[mod]:
                buckets[mod].append(canon)
            records.append(
                {
                    "file": rel,
                    "symbol": canon,
                    "old_module": OLD,
                    "new_module": mod,
                    "domain": DOMAIN_LABEL[mod],
                }
            )

        new_blocks: list[str] = []
        for mod in (FB, POL, VAL, PROJ, OLD):
            if buckets[mod]:
                new_blocks.append(render_import(mod, sorted(buckets[mod])))

        lines[start:end] = ["".join(new_blocks)]

    out = apply_renames("".join(lines))
    path.write_text(out, encoding="utf-8")
    return records


def main() -> int:
    all_records: list[dict] = []
    for root_name in SCAN_ROOTS:
        for path in sorted((ROOT / root_name).rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            if rel in SKIP or "/__pycache__/" in rel:
                continue
            all_records.extend(migrate_file(path))

    artifact = ROOT / "artifacts" / "bv14b_consumer_migration.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps(all_records, indent=2) + "\n", encoding="utf-8")
    print(f"Migrated {len({r['file'] for r in all_records})} files, {len(all_records)} symbol moves")
    print(f"Wrote {artifact.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

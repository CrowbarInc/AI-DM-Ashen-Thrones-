"""BN1–BN11 gate-context and runtime entry guards (import-light; no pytest).

Runtime gate-entry seam (BN1), lazy gate namespace locks (BN2), and gate-context
preflight import regrowth policies (BN3–BN11). Enforced by ``test_bn*_*`` in
``tests/test_ownership_registry.py``.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Final, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _normalize_test_rel_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


# Cycle BN1: runtime/API modules may not import apply_final_emission_gate from the gate owner
# directly; use game.final_emission_runtime.finalize_player_facing_emission instead.
BN1_RUNTIME_GATE_ENTRY_ALLOWLIST: Final[Mapping[str, str]] = {
    "game/final_emission_gate.py": "Orchestration owner defines apply_final_emission_gate (BN1 KEEP)",
    "game/final_emission_runtime.py": "Single production delegate seam (BN1 KEEP)",
}
BN1_RUNTIME_GATE_ENTRY_REPLACEMENT: Final[str] = (
    "game.final_emission_runtime.finalize_player_facing_emission"
)
BN1_DOWNSTREAM_TEST_GATE_ENTRY_REPLACEMENT: Final[str] = (
    "tests.helpers.gate_orchestration_smoke.apply_final_emission_gate_consumer"
)
# Cycle BN2 — internal lazy ``feg`` namespace in extracted stack modules (import-path only).
# Post-BN2 these files must not lazy-import ``game.final_emission_gate``; layer owners are
# imported directly. Monkeypatch tests patch owner modules (e.g. terminal_pipeline,
# emission_finalize), not ``feg``. Add retained symbols only with explicit test reason.
BN2_LAZY_GATE_NAMESPACE_FILES: Final[frozenset[str]] = frozenset(
    {
        "game/final_emission_non_strict_stack.py",
        "game/final_emission_terminal_pipeline.py",
    }
)
BN2_RETAINED_LAZY_GATE_SYMBOLS_BY_FILE: Final[Mapping[str, frozenset[str]]] = {
    "game/final_emission_non_strict_stack.py": frozenset(),
    "game/final_emission_terminal_pipeline.py": frozenset(),
}
BN2_FORBIDDEN_LAZY_GATE_MARKERS: Final[tuple[str, ...]] = (
    "def _gate_module(",
    "import game.final_emission_gate",
    "_gate_module()",
)

# Cycle BN3 — gate_context must not regrow direct layer-meta owner imports after preflight split.
BN3_GATE_CONTEXT_OWNER_MODULE: Final[str] = "game/final_emission_gate_context.py"
BN3_GATE_CONTEXT_PREFLIGHT_DEFAULTS_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_defaults.py"
)
BN3_GATE_CONTEXT_FORBIDDEN_LAYER_META_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.final_emission_anti_railroading import",
    "from game.final_emission_answer_shape_primacy import",
    "from game.final_emission_context_separation import",
    "from game.final_emission_fast_fallback_composition import",
    "from game.final_emission_meta import",
    "from game.final_emission_narrative_authority import",
    "from game.final_emission_player_facing_narration_purity import",
    "from game.final_emission_repairs import",
    "from game.final_emission_response_type import",
    "from game.final_emission_tone_escalation import",
    "default_anti_railroading_meta(",
    "default_answer_shape_primacy_meta(",
    "default_context_separation_meta(",
    "default_fast_fallback_neutral_composition_meta(",
    "default_narrative_authenticity_layer_meta(",
    "default_response_type_debug(",
    "default_narrative_authority_meta(",
    "default_player_facing_narration_purity_meta(",
    "_default_fallback_behavior_meta(",
    "_default_response_delta_meta(",
    "_default_social_response_structure_meta(",
    "default_tone_escalation_meta(",
    "_merge_opening_upstream_prepare_attach_observability_into_response_type_debug(",
)
BN3_GATE_CONTEXT_REQUIRED_PREFLIGHT_DEFAULTS_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_defaults import initialize_gate_preflight_layer_meta_defaults"
)

# Cycle BN4 — gate_context must not regrow direct telemetry/provenance imports after preflight split.
BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_telemetry.py"
)
BN4_GATE_CONTEXT_FORBIDDEN_TELEMETRY_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.fallback_provenance_debug import",
    "from game.stage_diff_telemetry import",
    "record_final_emission_gate_entry(",
    "apply_upstream_fallback_pregate_containment(",
    "snapshot_turn_stage(",
    "record_stage_snapshot(",
    "diff_turn_stage(",
    "record_stage_transition(",
)
BN4_GATE_CONTEXT_REQUIRED_PREFLIGHT_TELEMETRY_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_telemetry import apply_gate_preflight_telemetry_and_containment"
)
BN4_FORBIDDEN_GATE_IMPORT_IN_TELEMETRY_HELPER: Final[str] = "from game.final_emission_gate import"
BN4_FORBIDDEN_GATE_IMPORT_IN_TELEMETRY_HELPER_ALT: Final[str] = "import game.final_emission_gate"

# Cycle BN5 — gate_context must not regrow direct upstream attach imports after preflight split.
BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_upstream.py"
)
BN5_GATE_CONTEXT_FORBIDDEN_UPSTREAM_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.upstream_response_repairs import",
    "merge_upstream_prepared_emission_into_gm_output(",
    "maybe_attach_upstream_prepared_opening_fallback_payload(",
    "UPSTREAM_PREPARED_EMISSION_KEY",
)
BN5_GATE_CONTEXT_REQUIRED_PREFLIGHT_UPSTREAM_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_upstream import apply_gate_preflight_upstream_attach"
)
BN5_FORBIDDEN_GATE_IMPORT_IN_UPSTREAM_HELPER: Final[str] = "from game.final_emission_gate import"
BN5_FORBIDDEN_GATE_IMPORT_IN_UPSTREAM_HELPER_ALT: Final[str] = "import game.final_emission_gate"

# Cycle BN6 — gate_context must not regrow direct turn-packet/policy setup imports after preflight split.
BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_turn_packet.py"
)
BN6_GATE_CONTEXT_FORBIDDEN_TURN_PACKET_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.response_policy_contracts import",
    "from game.turn_packet import",
    "materialize_response_policy_bundle(",
    "get_turn_packet(",
    "_gate_turn_packet_cache",
)
BN6_GATE_CONTEXT_REQUIRED_PREFLIGHT_TURN_PACKET_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_turn_packet import initialize_gate_preflight_turn_packet"
)
BN6_FORBIDDEN_GATE_IMPORT_IN_TURN_PACKET_HELPER: Final[str] = "from game.final_emission_gate import"
BN6_FORBIDDEN_GATE_IMPORT_IN_TURN_PACKET_HELPER_ALT: Final[str] = "import game.final_emission_gate"

# Cycle BN7 — gate_context must not regrow direct interaction inspection imports after preflight split.
BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_interaction.py"
)
BN7_GATE_CONTEXT_FORBIDDEN_INTERACTION_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.interaction_context import",
    "inspect_interaction_context(",
)
BN7_GATE_CONTEXT_REQUIRED_PREFLIGHT_INTERACTION_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_interaction import resolve_gate_preflight_interaction_metadata"
)
BN7_FORBIDDEN_GATE_IMPORT_IN_INTERACTION_HELPER: Final[str] = "from game.final_emission_gate import"
BN7_FORBIDDEN_GATE_IMPORT_IN_INTERACTION_HELPER_ALT: Final[str] = "import game.final_emission_gate"

# Cycle BN8 — gate_context must not regrow direct strict-social routing/sanitizer imports after split.
BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_strict_social.py"
)
BN8_GATE_CONTEXT_FORBIDDEN_STRICT_SOCIAL_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.social_exchange_emission import",
    "from game.output_sanitizer import",
    "effective_strict_social_resolution_for_emission(",
    "strict_social_emission_will_apply(",
    "merged_player_prompt_for_gate(",
    "strict_social_suppress_non_native_coercion_for_narration_beat(",
    "sanitize_player_facing_output(",
)
BN8_GATE_CONTEXT_REQUIRED_PREFLIGHT_STRICT_SOCIAL_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_strict_social import resolve_gate_preflight_strict_social_routing"
)
BN8_FORBIDDEN_GATE_IMPORT_IN_STRICT_SOCIAL_HELPER: Final[str] = "from game.final_emission_gate import"
BN8_FORBIDDEN_GATE_IMPORT_IN_STRICT_SOCIAL_HELPER_ALT: Final[str] = "import game.final_emission_gate"
BN8_FORBIDDEN_STRICT_SOCIAL_HELPER_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.final_emission_gate import",
    "import game.final_emission_gate",
    "from game.final_emission_meta import",
    "from game.final_emission_replay_projection import",
    "from game.final_emission_terminal_pipeline import",
)

# Cycle BN9 — gate_context must not regrow direct pregate text imports after preflight split.
BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_pregate_text.py"
)
BN9_GATE_CONTEXT_FORBIDDEN_PREGATE_TEXT_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.final_emission_text import",
    "from game.final_emission_text_formatting import",
    "_normalize_text(",
)
BN9_GATE_CONTEXT_REQUIRED_PREFLIGHT_PREGATE_TEXT_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_pregate_text import resolve_gate_preflight_pregate_text"
)
BN9_FORBIDDEN_PREGATE_TEXT_HELPER_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.final_emission_gate import",
    "import game.final_emission_gate",
    "from game.final_emission_meta import",
    "from game.final_emission_replay_projection import",
    "from game.final_emission_terminal_pipeline import",
)

# Cycle BN10 — branch-flag helper must not import gate/FEM/replay/terminal modules.
BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE: Final[str] = (
    "game/final_emission_gate_preflight_branch_flags.py"
)
BN10_GATE_CONTEXT_REQUIRED_PREFLIGHT_BRANCH_FLAGS_IMPORT: Final[str] = (
    "from game.final_emission_gate_preflight_branch_flags import resolve_gate_preflight_branch_flags"
)
BN10_GATE_CONTEXT_FORBIDDEN_INLINE_BRANCH_FLAG_MARKERS: Final[tuple[str, ...]] = (
    "question_retry_fallback",
    "social_exchange_retry_fallback",
    "npc_directed_guard",
)
BN10_FORBIDDEN_BRANCH_FLAGS_HELPER_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "from game.final_emission_gate import",
    "import game.final_emission_gate",
    "from game.final_emission_meta import",
    "from game.final_emission_replay_projection import",
    "from game.final_emission_terminal_pipeline import",
)

# Cycle BN11 — gate_context positive preflight-only import allowlist (stdlib/typing + preflight helpers).
BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES: Final[frozenset[str]] = frozenset(
    {
        "game.final_emission_gate_preflight_branch_flags",
        "game.final_emission_gate_preflight_defaults",
        "game.final_emission_gate_preflight_interaction",
        "game.final_emission_gate_preflight_pregate_text",
        "game.final_emission_gate_preflight_strict_social",
        "game.final_emission_gate_preflight_telemetry",
        "game.final_emission_gate_preflight_turn_packet",
        "game.final_emission_gate_preflight_upstream",
    }
)
BN11_GATE_CONTEXT_ALLOWED_STDLIB_IMPORT_MODULES: Final[frozenset[str]] = frozenset(
    {"__future__", "typing"}
)
BN11_GATE_CONTEXT_REQUIRED_PREFLIGHT_IMPORTS: Final[tuple[str, ...]] = (
    BN3_GATE_CONTEXT_REQUIRED_PREFLIGHT_DEFAULTS_IMPORT,
    BN4_GATE_CONTEXT_REQUIRED_PREFLIGHT_TELEMETRY_IMPORT,
    BN5_GATE_CONTEXT_REQUIRED_PREFLIGHT_UPSTREAM_IMPORT,
    BN6_GATE_CONTEXT_REQUIRED_PREFLIGHT_TURN_PACKET_IMPORT,
    BN7_GATE_CONTEXT_REQUIRED_PREFLIGHT_INTERACTION_IMPORT,
    BN8_GATE_CONTEXT_REQUIRED_PREFLIGHT_STRICT_SOCIAL_IMPORT,
    BN9_GATE_CONTEXT_REQUIRED_PREFLIGHT_PREGATE_TEXT_IMPORT,
    BN10_GATE_CONTEXT_REQUIRED_PREFLIGHT_BRANCH_FLAGS_IMPORT,
)
BN11_FORBIDDEN_NON_PREFLIGHT_GAME_IMPORT_MODULES: Final[frozenset[str]] = frozenset(
    {
        "game.final_emission_gate",
        "game.final_emission_meta",
        "game.final_emission_replay_projection",
        "game.final_emission_text",
        "game.output_sanitizer",
        "game.social_exchange_emission",
        "game.upstream_response_repairs",
        "game.turn_packet",
        "game.response_policy_contracts",
    }
)


def _gate_import_modules(gate_src: str) -> frozenset[str]:
    """Return top-level modules imported by ``final_emission_gate`` source."""
    mods: set[str] = set()
    for match in re.finditer(r"^from ([\w.]+) import", gate_src, re.MULTILINE):
        mods.add(match.group(1))
    for match in re.finditer(r"^import ([\w.]+)(?: as \w+)?$", gate_src, re.MULTILINE):
        mods.add(match.group(1))
    return frozenset(mods)


def collect_bn1_runtime_gate_entry_guard_violations(
    rel_path: str,
    source: str,
    *,
    allowlist: Mapping[str, str] = BN1_RUNTIME_GATE_ENTRY_ALLOWLIST,
) -> list[str]:
    """Return violations when a non-owner game module imports gate entry directly."""
    norm = _normalize_test_rel_path(rel_path)
    if norm in allowlist:
        return []

    tree = ast.parse(source)
    violations: list[str] = []
    seen: set[tuple[str, str]] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != "game.final_emission_gate":
            continue
        for alias in node.names:
            if alias.name != "apply_final_emission_gate":
                continue
            key = (node.module, alias.name)
            if key in seen:
                continue
            seen.add(key)
            violations.append(
                f"{norm}: forbidden direct runtime gate import "
                f"'game.final_emission_gate.apply_final_emission_gate' "
                f"(use {BN1_RUNTIME_GATE_ENTRY_REPLACEMENT!r}; downstream tests: "
                f"{BN1_DOWNSTREAM_TEST_GATE_ENTRY_REPLACEMENT!r})",
            )
    return violations


def iter_bn1_runtime_gate_entry_guard_scan_paths(
    repo_root: Path | None = None,
    *,
    allowlist: Mapping[str, str] = BN1_RUNTIME_GATE_ENTRY_ALLOWLIST,
) -> tuple[str, ...]:
    """All game/**/*.py paths subject to BN1 runtime gate-entry guard."""
    root = _REPO_ROOT if repo_root is None else repo_root
    paths: list[str] = []
    for path in sorted((root / "game").rglob("*.py")):
        rel = _normalize_test_rel_path(path.relative_to(root))
        if rel in allowlist:
            continue
        paths.append(rel)
    return tuple(paths)


def collect_bn2_lazy_gate_namespace_violations(rel_path: str, source: str) -> list[str]:
    """BN2: flag lazy ``feg`` namespace usage in extracted stack modules."""
    norm = rel_path.replace("\\", "/")
    if norm not in BN2_LAZY_GATE_NAMESPACE_FILES:
        return []

    violations: list[str] = []
    for marker in BN2_FORBIDDEN_LAZY_GATE_MARKERS:
        if marker in source:
            violations.append(
                f"{norm}: forbidden BN2 lazy gate namespace marker {marker!r} "
                f"(import layer owners directly; monkeypatch owner modules, not feg)",
            )

    for match in re.finditer(r"\bfeg\.(\w+)", source):
        symbol = match.group(1)
        allowed = BN2_RETAINED_LAZY_GATE_SYMBOLS_BY_FILE.get(norm, frozenset())
        if symbol not in allowed:
            violations.append(
                f"{norm}: forbidden BN2 lazy gate namespace access feg.{symbol!r} "
                f"(not in retained allowlist; import owner module directly)",
            )
    return violations


def collect_bn3_gate_context_layer_meta_import_violations(source: str) -> list[str]:
    """BN3: flag direct layer-meta owner imports regrown on gate_context owner."""
    violations: list[str] = []
    for marker in BN3_GATE_CONTEXT_FORBIDDEN_LAYER_META_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN3 layer-meta owner marker {marker!r} "
                f"(use {BN3_GATE_CONTEXT_PREFLIGHT_DEFAULTS_MODULE!r})",
            )
    if BN3_GATE_CONTEXT_REQUIRED_PREFLIGHT_DEFAULTS_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN3 preflight defaults import "
            f"{BN3_GATE_CONTEXT_REQUIRED_PREFLIGHT_DEFAULTS_IMPORT!r}",
        )
    return violations


def collect_bn4_gate_context_telemetry_import_violations(source: str) -> list[str]:
    """BN4: flag direct telemetry/provenance imports regrown on gate_context owner."""
    violations: list[str] = []
    for marker in BN4_GATE_CONTEXT_FORBIDDEN_TELEMETRY_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN4 telemetry/provenance marker {marker!r} "
                f"(use {BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE!r})",
            )
    if BN4_GATE_CONTEXT_REQUIRED_PREFLIGHT_TELEMETRY_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN4 preflight telemetry import "
            f"{BN4_GATE_CONTEXT_REQUIRED_PREFLIGHT_TELEMETRY_IMPORT!r}",
        )
    return violations


def collect_bn4_preflight_telemetry_helper_gate_import_violations(source: str) -> list[str]:
    """BN4: preflight telemetry helper must not import the gate orchestration owner."""
    violations: list[str] = []
    if BN4_FORBIDDEN_GATE_IMPORT_IN_TELEMETRY_HELPER in source:
        violations.append(
            f"{BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE}: forbidden gate owner import "
            f"{BN4_FORBIDDEN_GATE_IMPORT_IN_TELEMETRY_HELPER!r}",
        )
    if BN4_FORBIDDEN_GATE_IMPORT_IN_TELEMETRY_HELPER_ALT in source:
        violations.append(
            f"{BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE}: forbidden gate owner import "
            f"{BN4_FORBIDDEN_GATE_IMPORT_IN_TELEMETRY_HELPER_ALT!r}",
        )
    return violations


def collect_bn5_gate_context_upstream_import_violations(source: str) -> list[str]:
    """BN5: flag direct upstream attach imports regrown on gate_context owner."""
    violations: list[str] = []
    for marker in BN5_GATE_CONTEXT_FORBIDDEN_UPSTREAM_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN5 upstream attach marker {marker!r} "
                f"(use {BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE!r})",
            )
    if BN5_GATE_CONTEXT_REQUIRED_PREFLIGHT_UPSTREAM_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN5 preflight upstream import "
            f"{BN5_GATE_CONTEXT_REQUIRED_PREFLIGHT_UPSTREAM_IMPORT!r}",
        )
    return violations


def collect_bn5_preflight_upstream_helper_gate_import_violations(source: str) -> list[str]:
    """BN5: preflight upstream helper must not import the gate orchestration owner."""
    violations: list[str] = []
    if BN5_FORBIDDEN_GATE_IMPORT_IN_UPSTREAM_HELPER in source:
        violations.append(
            f"{BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE}: forbidden gate owner import "
            f"{BN5_FORBIDDEN_GATE_IMPORT_IN_UPSTREAM_HELPER!r}",
        )
    if BN5_FORBIDDEN_GATE_IMPORT_IN_UPSTREAM_HELPER_ALT in source:
        violations.append(
            f"{BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE}: forbidden gate owner import "
            f"{BN5_FORBIDDEN_GATE_IMPORT_IN_UPSTREAM_HELPER_ALT!r}",
        )
    return violations


def collect_bn6_gate_context_turn_packet_import_violations(source: str) -> list[str]:
    """BN6: flag direct turn-packet/policy setup imports regrown on gate_context owner."""
    violations: list[str] = []
    for marker in BN6_GATE_CONTEXT_FORBIDDEN_TURN_PACKET_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN6 turn-packet/policy marker {marker!r} "
                f"(use {BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE!r})",
            )
    if BN6_GATE_CONTEXT_REQUIRED_PREFLIGHT_TURN_PACKET_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN6 preflight turn-packet import "
            f"{BN6_GATE_CONTEXT_REQUIRED_PREFLIGHT_TURN_PACKET_IMPORT!r}",
        )
    return violations


def collect_bn6_preflight_turn_packet_helper_gate_import_violations(source: str) -> list[str]:
    """BN6: preflight turn-packet helper must not import the gate orchestration owner."""
    violations: list[str] = []
    if BN6_FORBIDDEN_GATE_IMPORT_IN_TURN_PACKET_HELPER in source:
        violations.append(
            f"{BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE}: forbidden gate owner import "
            f"{BN6_FORBIDDEN_GATE_IMPORT_IN_TURN_PACKET_HELPER!r}",
        )
    if BN6_FORBIDDEN_GATE_IMPORT_IN_TURN_PACKET_HELPER_ALT in source:
        violations.append(
            f"{BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE}: forbidden gate owner import "
            f"{BN6_FORBIDDEN_GATE_IMPORT_IN_TURN_PACKET_HELPER_ALT!r}",
        )
    return violations


def collect_bn7_gate_context_interaction_import_violations(source: str) -> list[str]:
    """BN7: flag direct interaction inspection imports regrown on gate_context owner."""
    violations: list[str] = []
    for marker in BN7_GATE_CONTEXT_FORBIDDEN_INTERACTION_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN7 interaction inspection marker {marker!r} "
                f"(use {BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE!r})",
            )
    if BN7_GATE_CONTEXT_REQUIRED_PREFLIGHT_INTERACTION_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN7 preflight interaction import "
            f"{BN7_GATE_CONTEXT_REQUIRED_PREFLIGHT_INTERACTION_IMPORT!r}",
        )
    return violations


def collect_bn7_preflight_interaction_helper_gate_import_violations(source: str) -> list[str]:
    """BN7: preflight interaction helper must not import the gate orchestration owner."""
    violations: list[str] = []
    if BN7_FORBIDDEN_GATE_IMPORT_IN_INTERACTION_HELPER in source:
        violations.append(
            f"{BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE}: forbidden gate owner import "
            f"{BN7_FORBIDDEN_GATE_IMPORT_IN_INTERACTION_HELPER!r}",
        )
    if BN7_FORBIDDEN_GATE_IMPORT_IN_INTERACTION_HELPER_ALT in source:
        violations.append(
            f"{BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE}: forbidden gate owner import "
            f"{BN7_FORBIDDEN_GATE_IMPORT_IN_INTERACTION_HELPER_ALT!r}",
        )
    return violations


def collect_bn8_gate_context_strict_social_import_violations(source: str) -> list[str]:
    """BN8: flag direct strict-social routing/sanitizer imports regrown on gate_context owner."""
    violations: list[str] = []
    for marker in BN8_GATE_CONTEXT_FORBIDDEN_STRICT_SOCIAL_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN8 strict-social routing marker {marker!r} "
                f"(use {BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE!r})",
            )
    if BN8_GATE_CONTEXT_REQUIRED_PREFLIGHT_STRICT_SOCIAL_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN8 preflight strict-social import "
            f"{BN8_GATE_CONTEXT_REQUIRED_PREFLIGHT_STRICT_SOCIAL_IMPORT!r}",
        )
    return violations


def collect_bn8_preflight_strict_social_helper_import_violations(source: str) -> list[str]:
    """BN8: preflight strict-social helper must not import gate/FEM/replay/terminal modules."""
    violations: list[str] = []
    for marker in BN8_FORBIDDEN_STRICT_SOCIAL_HELPER_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE}: forbidden BN8 helper import {marker!r}",
            )
    return violations


def collect_bn9_gate_context_pregate_text_import_violations(source: str) -> list[str]:
    """BN9: flag direct pregate text imports regrown on gate_context owner."""
    violations: list[str] = []
    for marker in BN9_GATE_CONTEXT_FORBIDDEN_PREGATE_TEXT_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN9 pregate text marker {marker!r} "
                f"(use {BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE!r})",
            )
    if BN9_GATE_CONTEXT_REQUIRED_PREFLIGHT_PREGATE_TEXT_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN9 preflight pregate text import "
            f"{BN9_GATE_CONTEXT_REQUIRED_PREFLIGHT_PREGATE_TEXT_IMPORT!r}",
        )
    return violations


def collect_bn9_preflight_pregate_text_helper_import_violations(source: str) -> list[str]:
    """BN9: preflight pregate text helper must not import gate/FEM/replay/terminal modules."""
    violations: list[str] = []
    for marker in BN9_FORBIDDEN_PREGATE_TEXT_HELPER_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE}: forbidden BN9 helper import {marker!r}",
            )
    return violations


def collect_bn10_gate_context_branch_flags_violations(source: str) -> list[str]:
    """BN10: gate_context must route branch flags through preflight helper."""
    violations: list[str] = []
    if BN10_GATE_CONTEXT_REQUIRED_PREFLIGHT_BRANCH_FLAGS_IMPORT not in source:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN10 preflight branch-flags import "
            f"{BN10_GATE_CONTEXT_REQUIRED_PREFLIGHT_BRANCH_FLAGS_IMPORT!r}",
        )
    initialize_src = ""
    if "def initialize_gate_execution_context(" in source:
        initialize_src = source.split("def initialize_gate_execution_context(", 1)[1]
        if "def " in initialize_src:
            initialize_src = initialize_src.split("\ndef ", 1)[0]
    for marker in BN10_GATE_CONTEXT_FORBIDDEN_INLINE_BRANCH_FLAG_MARKERS:
        if marker in initialize_src:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN10 inline branch-flag marker {marker!r} "
                f"(use {BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE!r})",
            )
    return violations


def collect_bn10_preflight_branch_flags_helper_import_violations(source: str) -> list[str]:
    """BN10: preflight branch-flags helper must not import gate/FEM/replay/terminal modules."""
    violations: list[str] = []
    for marker in BN10_FORBIDDEN_BRANCH_FLAGS_HELPER_IMPORT_MARKERS:
        if marker in source:
            violations.append(
                f"{BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE}: forbidden BN10 helper import {marker!r}",
            )
    return violations


def gate_context_import_modules(source: str) -> frozenset[str]:
    """Return top-level modules imported by ``final_emission_gate_context`` source."""
    return _gate_import_modules(source)


def collect_bn11_gate_context_preflight_only_import_violations(source: str) -> list[str]:
    """BN11: gate_context may import only stdlib/typing plus preflight helper owners."""
    violations: list[str] = []
    imported = gate_context_import_modules(source)
    allowed = BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES | BN11_GATE_CONTEXT_ALLOWED_STDLIB_IMPORT_MODULES

    game_imports = {mod for mod in imported if mod.startswith("game.")}
    disallowed_game = sorted(game_imports - BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES)
    for mod in disallowed_game:
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN11 non-preflight game import {mod!r} "
            f"(allowed game modules: {sorted(BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES)!r})",
        )

    other_disallowed = sorted(imported - allowed)
    for mod in other_disallowed:
        if mod.startswith("game."):
            continue
        violations.append(
            f"{BN3_GATE_CONTEXT_OWNER_MODULE}: forbidden BN11 import outside stdlib/typing allowlist: {mod!r}",
        )

    for required in BN11_GATE_CONTEXT_REQUIRED_PREFLIGHT_IMPORTS:
        if required not in source:
            violations.append(
                f"{BN3_GATE_CONTEXT_OWNER_MODULE}: missing BN11 required preflight import {required!r}",
            )

    return violations


def _iter_collect_bn11_function_blocks(source: str) -> list[tuple[str, str]]:
    """Return ``(name, body)`` for each ``collect_bn11_*`` function after the BN11 anchor."""
    bn11_anchor = "# Cycle BN11"
    if bn11_anchor not in source:
        return []

    tail = source.split(bn11_anchor, 1)[1]
    blocks: list[tuple[str, str]] = []
    current_name = ""
    current_lines: list[str] = []
    capturing = False

    for line in tail.splitlines(keepends=True):
        if line.startswith("def collect_bn11_"):
            if capturing and current_name:
                blocks.append((current_name, "".join(current_lines)))
            current_name = line.split("(", 1)[0].removeprefix("def ").strip()
            current_lines = [line]
            capturing = True
            continue
        if capturing:
            if line.startswith("def ") and not line.startswith("def collect_bn11_"):
                blocks.append((current_name, "".join(current_lines)))
                current_name = ""
                current_lines = []
                capturing = False
                continue
            current_lines.append(line)

    if capturing and current_name:
        blocks.append((current_name, "".join(current_lines)))
    return blocks


def collect_bn11_scan_logic_runtime_gate_import_violations(source: str) -> list[str]:
    """BN11: collect_bn11 scan helpers must be string-scan only (no runtime gate imports)."""
    blocks = _iter_collect_bn11_function_blocks(source)
    if not blocks:
        return ["tests/ownership_guard_bn_gate_context.py: missing collect_bn11_* scan helpers"]

    violations: list[str] = []
    for func_name, func_source in blocks:
        for line in func_source.splitlines():
            stripped = line.lstrip()
            if not (stripped.startswith("from ") or stripped.startswith("import ")):
                continue
            violations.append(
                "tests/ownership_guard_bn_gate_context.py: forbidden BN11 scan-logic import in "
                f"{func_name}: {stripped!r}",
            )
    return violations

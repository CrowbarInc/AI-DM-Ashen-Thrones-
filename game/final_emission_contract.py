"""Static boundary vocabulary for final emission (audit + inspection; no runtime policy).

See ``docs/final_emission_debt_retirement.md`` for the full architectural contract.
"""
from __future__ import annotations

# --- Identifier audit (used by tests; keep lowercase substrings) ---
# If a ``def`` / import alias name in ``game/final_emission_*.py`` contains one of these
# substrings, treat it as *likely* semantic-repair surface area and track it in the
# debt-retirement snapshot tests until renamed or moved upstream.
FINAL_EMISSION_FORBIDDEN_IDENTIFIER_SUBSTRINGS: tuple[str, ...] = (
    "restore_spoken",
    "normalize_dialogue_cadence",
    "trim_leading_expository",
    "merge_substantive",
    "repair_answer",
    "reorder",
    "synthesize",
    "reconstruct",
    "semantic_repair",
    "opening_authorship",
    "cadence",
    "smooth",
    # Block B retired helper anchors (substring guard; keep in sync with debt-retirement tests).
    "fallback_template",
    "rewrite_meta",
    "spoken_opening",
)

FINAL_EMISSION_ALLOWED_RESPONSIBILITIES: tuple[str, ...] = (
    "Enforce legality: deterministic validators, contract checks, and refusal of disallowed mutations.",
    "Strip or package player-facing output: whitespace/HTML normalization, sealed fallbacks, sidecar/FEM merges.",
    "Merge safe metadata and telemetry: bounded traces, skip reasons, observability projections.",
    "Select already-prepared upstream outputs when explicitly provided (e.g. upstream_prepared_emission).",
    "Apply already-authorized terminal legality fallbacks (hard replace / reject path only where contracted).",
)

FINAL_EMISSION_FORBIDDEN_RESPONSIBILITIES: tuple[str, ...] = (
    "Semantically reconstruct narration or invent missing diegetic meaning.",
    "Repair answer completeness, response delta, or social shape by reordering or composing new prose.",
    "Add spoken openings, cadence smoothing, or micro-edits that change how the reply reads socially.",
    "Choose “better” phrasing, decompress clauses, or smooth prose for acceptance optics.",
    "Synthesize fallback facts, next-lead lines, or partials except via upstream-prepared or explicit legality strips.",
)

"""Formal contract for final-stage emission mutations (Block B: classification only).

Block B defines allowed vs disallowed *mutation kinds* at the final emission boundary.
Runtime wiring into ``final_emission_gate`` / ``final_emission_repairs`` is deferred to Block C.

See ``docs/final_emission_boundary_audit.md``.
"""
from __future__ import annotations

# Canonical classification strings returned by ``classify_final_emission_mutation``.
PACKAGING_ALLOWED_KIND = "PACKAGING_ALLOWED"
LEGALITY_ALLOWED_KIND = "LEGALITY_ALLOWED"
SEMANTIC_DISALLOWED_KIND = "SEMANTIC_DISALLOWED"

PACKAGING_ALLOWED: frozenset[str] = frozenset(
    {
        "normalize_whitespace",
        "sanitize_html_to_text",
        "normalize_terminal_punctuation",
        "strip_route_illegal_contamination",
        "package_final_emission_meta",
        "preserve_candidate_text",
        # Subtractive-only cleanup of contract-banned stock phrases (no composed prose).
        "strip_meta_fallback_voice_surfaces",
        "strip_fabricated_authority_surfaces",
        "trim_overcertain_claim_spans",
        # Bounded, non-inventive permutation only (moves existing answer sentence to front).
        "reorder_answer_to_front",
    }
)

LEGALITY_ALLOWED: frozenset[str] = frozenset(
    {
        "hard_replace_illegal_output_with_sealed_fallback",
        "reject_contract_failed_output",
        "strict_social_terminal_fallback",
    }
)

SEMANTIC_DISALLOWED: frozenset[str] = frozenset(
    {
        "repair_answer_completeness",
        "repair_response_delta",
        "repair_social_response_structure",
        "flatten_list_like_dialogue",
        "collapse_multi_speaker_formatting",
        "restore_spoken_opening",
        "normalize_dialogue_cadence",
        "reconstruct_narration",
        "compose_fallback_answer",
        "synthesize_known_edge_phrase",
        "smooth_sentence_microstructure",
        "narrative_repair",
        "semantic_fallback_composition",
    }
)


def classify_final_emission_mutation(kind: str) -> str:
    """Return the contract bucket for ``kind``.

    Unknown kinds are not allowed: raises ``ValueError`` (fail closed).
    """
    if kind in SEMANTIC_DISALLOWED:
        return SEMANTIC_DISALLOWED_KIND
    if kind in PACKAGING_ALLOWED:
        return PACKAGING_ALLOWED_KIND
    if kind in LEGALITY_ALLOWED:
        return LEGALITY_ALLOWED_KIND
    raise ValueError(
        f"unknown final-emission mutation kind {kind!r}: not in PACKAGING_ALLOWED, "
        "LEGALITY_ALLOWED, or SEMANTIC_DISALLOWED allowlists; refusing by default"
    )


def is_packaging_allowed(kind: str) -> bool:
    return kind in PACKAGING_ALLOWED


def is_legality_allowed(kind: str) -> bool:
    return kind in LEGALITY_ALLOWED


def is_semantic_disallowed(kind: str) -> bool:
    return kind in SEMANTIC_DISALLOWED


def assert_final_emission_mutation_allowed(kind: str, *, source: str) -> None:
    """Raise if ``kind`` may not run at the final emission boundary.

    Packaging and legality kinds succeed. Semantic-disallowed kinds fail with an
    ``AssertionError`` naming ``kind``, ``source``, and the upstream-repair requirement.
    Unknown kinds fail closed with ``ValueError``.
    """
    if kind in SEMANTIC_DISALLOWED:
        raise AssertionError(
            f"final-emission mutation {kind!r} (source={source!r}) is SEMANTIC_DISALLOWED "
            "at the boundary; semantic repair must occur upstream"
        )
    if kind in PACKAGING_ALLOWED or kind in LEGALITY_ALLOWED:
        return
    raise ValueError(
        f"unknown final-emission mutation kind {kind!r} (source={source!r}): not allowlisted; "
        "refusing by default"
    )

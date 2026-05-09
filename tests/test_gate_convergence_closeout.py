"""Block AB — Gate Convergence Closeout snapshot test.

Asserts that ``docs/gate_convergence_closeout.md`` cites mutation kinds that
still exist in ``game.final_emission_boundary_contract``, and that the key
exported taxonomy constants and helpers remain importable. This is a freeze /
closeout test — it does not exercise runtime behavior. Its purpose is to make
the closeout doc fail loudly if a future taxonomy rename/removal silently
diverges the doc from the code.

If you intentionally rename or retire a taxonomy entry referenced in the
closeout doc, update both the contract module and ``docs/gate_convergence_closeout.md``
in the same change.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from game import final_emission_boundary_contract as contract


REPO_ROOT = Path(__file__).resolve().parents[1]
CLOSEOUT_DOC_PATH = REPO_ROOT / "docs" / "gate_convergence_closeout.md"
INVENTORY_DOC_PATH = REPO_ROOT / "docs" / "gate_cleanup_inventory.md"


# Kinds the closeout doc explicitly names under "Protected Architectural Invariants".
# Each must remain a SEMANTIC_DISALLOWED taxonomy entry for the invariant text to
# remain accurate. Adding a new SEMANTIC_DISALLOWED kind is fine; removing or
# repurposing one of these requires updating the closeout doc deliberately.
_CLOSEOUT_REFERENCED_SEMANTIC_DISALLOWED_KINDS: tuple[str, ...] = (
    "speaker_contract_local_rebind",
    "speaker_contract_canonical_rewrite",
    "speaker_contract_neutral_bridge",
    "effective_social_resolution_sync",
    "strict_social_referential_substitution",
    "compose_opening_fallback_compatibility_local",
    "interaction_continuity_repair",
    "interaction_continuity_malformed_speaker_bridge",
)


def _read_closeout_doc() -> str:
    assert CLOSEOUT_DOC_PATH.exists(), (
        f"closeout doc missing at {CLOSEOUT_DOC_PATH}; Block AB requires the "
        "closeout doc to exist as the formal Gate freeze artifact"
    )
    return CLOSEOUT_DOC_PATH.read_text(encoding="utf-8")


def test_closeout_doc_exists_and_has_required_section_headers() -> None:
    text = _read_closeout_doc()
    for header in (
        "# Gate Convergence Closeout",
        "## Original Problems",
        "## What Was Converged",
        "## Intentional Remaining Residue",
        "## Protected Architectural Invariants",
        "## Stop-Point Decision",
        "## Recommended Future Work",
    ):
        assert header in text, f"closeout doc missing required section header {header!r}"


@pytest.mark.parametrize("kind", _CLOSEOUT_REFERENCED_SEMANTIC_DISALLOWED_KINDS)
def test_closeout_doc_referenced_kinds_remain_semantic_disallowed(kind: str) -> None:
    """Each kind cited in the closeout doc must still be SEMANTIC_DISALLOWED.

    If you remove or reclassify one of these, update the closeout doc in the
    same change so the freeze artifact does not silently drift from the code.
    """
    assert kind in contract.SEMANTIC_DISALLOWED, (
        f"closeout doc references {kind!r} as SEMANTIC_DISALLOWED, but it is no "
        "longer in game.final_emission_boundary_contract.SEMANTIC_DISALLOWED; "
        "update docs/gate_convergence_closeout.md alongside the taxonomy change"
    )
    assert (
        contract.classify_final_emission_mutation(kind)
        == contract.SEMANTIC_DISALLOWED_KIND
    )


@pytest.mark.parametrize("kind", _CLOSEOUT_REFERENCED_SEMANTIC_DISALLOWED_KINDS)
def test_closeout_doc_mentions_each_referenced_kind_verbatim(kind: str) -> None:
    """The doc must cite each invariant kind verbatim (catches stale renames)."""
    text = _read_closeout_doc()
    assert kind in text, (
        f"closeout doc does not mention {kind!r} verbatim; the Protected "
        "Architectural Invariants section is the contract surface that ties "
        "the freeze to the taxonomy"
    )


def test_closeout_doc_references_canonical_taxonomy_module() -> None:
    text = _read_closeout_doc()
    assert "game/final_emission_boundary_contract.py" in text, (
        "closeout doc must point at the canonical taxonomy module"
    )
    for bucket in ("PACKAGING_ALLOWED", "LEGALITY_ALLOWED", "SEMANTIC_DISALLOWED"):
        assert bucket in text, f"closeout doc must name taxonomy bucket {bucket}"


def test_closeout_doc_references_companion_inventory() -> None:
    text = _read_closeout_doc()
    assert "docs/gate_cleanup_inventory.md" in text, (
        "closeout doc must reference the companion inventory doc"
    )


def test_inventory_doc_points_back_to_closeout_doc() -> None:
    assert INVENTORY_DOC_PATH.exists()
    inventory = INVENTORY_DOC_PATH.read_text(encoding="utf-8")
    assert "gate_convergence_closeout.md" in inventory, (
        "inventory doc must point forward to the closeout doc so reviewers find "
        "the freeze artifact from the inventory"
    )
    assert "maintenance-grade converged" in inventory, (
        "inventory doc must mark the Gate layer as maintenance-grade converged"
    )


def test_taxonomy_module_still_exports_required_surfaces() -> None:
    """Closeout invariants quote these names; they must remain importable."""
    for name in (
        "PACKAGING_ALLOWED",
        "LEGALITY_ALLOWED",
        "SEMANTIC_DISALLOWED",
        "PACKAGING_ALLOWED_KIND",
        "LEGALITY_ALLOWED_KIND",
        "SEMANTIC_DISALLOWED_KIND",
        "classify_final_emission_mutation",
        "assert_final_emission_mutation_allowed",
        "is_packaging_allowed",
        "is_legality_allowed",
        "is_semantic_disallowed",
    ):
        assert hasattr(contract, name), (
            f"final_emission_boundary_contract.{name} disappeared; the closeout "
            "doc treats this as a stable taxonomy surface"
        )


def test_taxonomy_buckets_remain_disjoint() -> None:
    """Freeze invariant: a mutation kind cannot belong to two buckets."""
    pa = contract.PACKAGING_ALLOWED
    la = contract.LEGALITY_ALLOWED
    sd = contract.SEMANTIC_DISALLOWED
    assert pa.isdisjoint(la), "PACKAGING_ALLOWED and LEGALITY_ALLOWED overlap"
    assert pa.isdisjoint(sd), "PACKAGING_ALLOWED and SEMANTIC_DISALLOWED overlap"
    assert la.isdisjoint(sd), "LEGALITY_ALLOWED and SEMANTIC_DISALLOWED overlap"

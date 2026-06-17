"""Block R: speaker-contract module extraction — wiring and invariant snapshots."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

import game.emitted_speaker_signature as ess
import game.final_emission_gate as feg
import game.speaker_contract_enforcement as sce
from game.speaker_contract_enforcement import (
    SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES,
    get_speaker_selection_contract,
    validate_emitted_speaker_against_contract,
)

pytestmark = pytest.mark.unit


def test_block_r_gate_reexports_speaker_enforcement_api():
    assert feg.get_speaker_selection_contract is sce.get_speaker_selection_contract
    assert feg.validate_emitted_speaker_against_contract is sce.validate_emitted_speaker_against_contract
    assert sce.detect_emitted_speaker_signature is ess.detect_emitted_speaker_signature
    assert feg.detect_emitted_speaker_signature is sce.detect_emitted_speaker_signature
    assert not hasattr(feg, "_sync_eff_social_to_resolution")
    assert feg.SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES is SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES
    assert not hasattr(feg, "enforce_emitted_speaker_with_contract")
    assert hasattr(sce, "enforce_emitted_speaker_with_contract")


def test_block_r_speaker_enforcement_reason_codes_taxonomy_stable():
    assert SPEAKER_CONTRACT_ENFORCEMENT_REASON_CODES == (
        "speaker_contract_match",
        "speaker_binding_mismatch",
        "forbidden_generic_fallback_speaker",
        "unjustified_speaker_switch",
        "interruption_without_contract_support",
        "interruption_justified_switch",
        "continuity_locked_speaker_repair",
        "canonical_speaker_rewrite",
        "narrator_neutral_no_allowed_speaker",
    )


def test_block_r_validate_emitted_speaker_contract_missing_helper_snapshot():
    """Regression anchor: missing-contract validation payload unchanged after extraction."""
    empty = get_speaker_selection_contract(None, None, None)
    out = validate_emitted_speaker_against_contract("Tavern Runner says, \"Hello.\"", empty, None)
    assert out == {
        "ok": True,
        "reason_code": "speaker_contract_match",
        "canonical_speaker_id": None,
        "canonical_speaker_name": None,
        "repair_mode": "none",
        "details": {
            "signature": {
                "speaker_name": "Tavern Runner",
                "speaker_label": "Tavern Runner",
                "is_explicitly_attributed": True,
                "is_generic_fallback_label": False,
                "has_interruption_framing": False,
                "confidence": "high",
            },
            "skipped": "no_contract",
        },
    }


def test_block_r_strict_social_trunk_layer_order_unchanged():
    """Tone → narrative authority → speaker enforcement → sync → anti-railroading (strict-social trunk)."""
    repo_root = Path(__file__).resolve().parents[1]
    src = (repo_root / "game" / "final_emission_strict_social_stack.py").read_text(encoding="utf-8")
    m = re.search(
        r"text, te_layer_meta, _ = apply_tone_escalation_layer\("
        r"[\s\S]*?"
        r"text, na_layer_meta, _ = apply_narrative_authority_layer\("
        r"[\s\S]*?"
        r"text, _speaker_contract_payload = enforce_emitted_speaker_with_contract\("
        r"[\s\S]*?"
        r"_sync_eff_social_to_resolution\("
        r"[\s\S]*?"
        r"text, ar_layer_meta, _ = apply_anti_railroading_layer\(",
        src,
    )
    assert m is not None, "strict-social trunk ordering fragment missing from final_emission_strict_social_stack.py"


def test_block_r_speaker_contract_module_owns_enforce_gate_delegator_removed():
    repo_root = Path(__file__).resolve().parents[1]
    gate_src = (repo_root / "game" / "final_emission_gate.py").read_text(encoding="utf-8").splitlines()
    ss_src = (repo_root / "game" / "final_emission_strict_social_stack.py").read_text(encoding="utf-8").splitlines()
    sce_src = (repo_root / "game" / "speaker_contract_enforcement.py").read_text(encoding="utf-8").splitlines()
    defs_enf_gate = [i for i, ln in enumerate(gate_src, start=1) if ln.startswith("def enforce_emitted_speaker_with_contract")]
    defs_enf_sce = [i for i, ln in enumerate(sce_src, start=1) if ln.startswith("def enforce_emitted_speaker_with_contract")]
    defs_sync = [i for i, ln in enumerate(sce_src, start=1) if ln.startswith("def _sync_eff_social_to_resolution")]
    assert len(defs_enf_gate) == 0
    assert len(defs_enf_sce) == 1
    assert len(defs_sync) == 1
    assert "enforce_emitted_speaker_with_contract(" in "\n".join(ss_src)
    assert "feg.enforce_emitted_speaker_with_contract" not in "\n".join(ss_src)

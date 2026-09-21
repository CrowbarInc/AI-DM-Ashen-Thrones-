"""Historical BW provenance check; not a current product-correctness gate."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_CLOSEOUT = REPO_ROOT / "docs" / "audits" / "closeouts" / "BW_protected_replay_trend_window_closeout.md"
AUDIT_MANIFEST = REPO_ROOT / "docs" / "audits" / "audit_manifest.md"


def test_bw_historical_closeout_provenance_remains_available() -> None:
    """Preserve discoverability without locking historical prose or obsolete paths."""
    assert CANONICAL_CLOSEOUT.is_file()
    assert "BW_protected_replay_trend_window_closeout.md" in AUDIT_MANIFEST.read_text(encoding="utf-8")

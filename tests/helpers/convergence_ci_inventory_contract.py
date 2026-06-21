"""BU27/BU29: coarse documentation parity guard for governance discovery navigation."""
from __future__ import annotations

from pathlib import Path

CONVERGENCE_CI_INVENTORY_REL_PATH = "docs/convergence_ci_inventory.md"
CONVERGENCE_CHECKS_WORKFLOW_REL_PATH = ".github/workflows/convergence-checks.yml"
AUDITS_README_REL_PATH = "docs/audits/README.md"
TESTS_README_REL_PATH = "tests/README_TESTS.md"

GOVERNANCE_DISCOVERY_INDEX_PHRASE = "Governance discovery index"
SPLIT_OWNER_GOVERNANCE_SECTION_PHRASE = "Split-owner acceptance matrix governance"
GOVERNANCE_INVENTORY_POINTER = "convergence_ci_inventory.md"

# Presence checks only — avoid brittle exact formatting requirements.
SPLIT_OWNER_INVENTORY_REQUIRED_SUBSTRINGS: tuple[tuple[str, str], ...] = (
    ("canonical CI check script", "check_split_owner_acceptance_matrix.py"),
    ("local refresh wrapper", "refresh_split_owner_acceptance_matrix.py"),
    ("convergence workflow reference", "convergence-checks.yml"),
    ("split-owner governance section anchor", SPLIT_OWNER_GOVERNANCE_SECTION_PHRASE),
    ("matrix edit checklist cross-link", "docs/audits/README.md"),
    ("checked-in audit report", "docs/audits/BU15_split_owner_acceptance_matrix.md"),
)

SPLIT_OWNER_INVENTORY_OPTIONAL_MAKE_TARGETS: tuple[str, ...] = (
    "make split-owner-matrix-check",
    "make split-owner-matrix-refresh",
)

SPLIT_OWNER_WORKFLOW_REQUIRED_SUBSTRINGS: tuple[tuple[str, str], ...] = (
    ("CI check script invocation", "check_split_owner_acceptance_matrix.py"),
    ("split-owner workflow step label", "Split-owner acceptance matrix contract"),
)

GOVERNANCE_FORWARD_POINTER_DOCS: tuple[tuple[str, str, str], ...] = (
    ("audit README forward pointer", AUDITS_README_REL_PATH, GOVERNANCE_INVENTORY_POINTER),
    ("test README forward pointer", TESTS_README_REL_PATH, GOVERNANCE_INVENTORY_POINTER),
)


def _read_repo_text(*, repo_root: Path, rel_path: str) -> str:
    path = repo_root / rel_path
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _inventory_navigation_errors(*, inventory_text: str) -> list[str]:
    errors: list[str] = []
    if GOVERNANCE_DISCOVERY_INDEX_PHRASE not in inventory_text:
        errors.append(
            f"{CONVERGENCE_CI_INVENTORY_REL_PATH} missing governance discovery index header; "
            f"expected substring {GOVERNANCE_DISCOVERY_INDEX_PHRASE!r} near the document introduction"
        )
    if SPLIT_OWNER_GOVERNANCE_SECTION_PHRASE not in inventory_text:
        errors.append(
            f"{CONVERGENCE_CI_INVENTORY_REL_PATH} missing split-owner governance section anchor; "
            f"expected substring {SPLIT_OWNER_GOVERNANCE_SECTION_PHRASE!r}"
        )
    return errors


def _forward_pointer_errors(*, repo_root: Path) -> list[str]:
    errors: list[str] = []
    for label, rel_path, needle in GOVERNANCE_FORWARD_POINTER_DOCS:
        text = _read_repo_text(repo_root=repo_root, rel_path=rel_path)
        if not text:
            errors.append(
                f"missing {rel_path}; restore the maintainer entry doc or update the parity guard"
            )
            continue
        if needle not in text:
            errors.append(
                f"{rel_path} missing {label}; "
                f"add a forward link to {CONVERGENCE_CI_INVENTORY_REL_PATH} "
                f"(expected substring {needle!r})"
            )
    return errors


def convergence_inventory_doc_contract_errors(*, repo_root: Path | None = None) -> list[str]:
    """Return actionable doc/CI parity drift messages; empty when BU27/BU29-locked."""
    root = repo_root if repo_root is not None else Path(__file__).resolve().parents[2]
    errors: list[str] = []

    inventory_text = _read_repo_text(repo_root=root, rel_path=CONVERGENCE_CI_INVENTORY_REL_PATH)
    if not inventory_text:
        errors.append(
            f"missing {CONVERGENCE_CI_INVENTORY_REL_PATH}; "
            "restore docs/convergence_ci_inventory.md or update the parity guard"
        )
        return errors

    errors.extend(_inventory_navigation_errors(inventory_text=inventory_text))

    for label, needle in SPLIT_OWNER_INVENTORY_REQUIRED_SUBSTRINGS:
        if needle not in inventory_text:
            errors.append(
                f"{CONVERGENCE_CI_INVENTORY_REL_PATH} missing {label}; "
                f"expected substring {needle!r}"
            )

    for target in SPLIT_OWNER_INVENTORY_OPTIONAL_MAKE_TARGETS:
        if target not in inventory_text:
            errors.append(
                f"{CONVERGENCE_CI_INVENTORY_REL_PATH} missing Make target reference {target!r}; "
                "add it to the split-owner governance quick-reference block"
            )

    errors.extend(_forward_pointer_errors(repo_root=root))

    workflow_text = _read_repo_text(repo_root=root, rel_path=CONVERGENCE_CHECKS_WORKFLOW_REL_PATH)
    if not workflow_text:
        errors.append(
            f"missing {CONVERGENCE_CHECKS_WORKFLOW_REL_PATH}; "
            "restore the convergence-checks workflow or update the parity guard"
        )
    else:
        for label, needle in SPLIT_OWNER_WORKFLOW_REQUIRED_SUBSTRINGS:
            if needle not in workflow_text:
                errors.append(
                    f"{CONVERGENCE_CHECKS_WORKFLOW_REL_PATH} missing {label}; "
                    f"expected substring {needle!r} — update docs/convergence_ci_inventory.md if CI wiring changed"
                )

    if inventory_text and workflow_text:
        if (
            "check_split_owner_acceptance_matrix.py" in inventory_text
            and "check_split_owner_acceptance_matrix.py" not in workflow_text
        ):
            errors.append(
                "docs/convergence_ci_inventory.md documents check_split_owner_acceptance_matrix.py "
                "but .github/workflows/convergence-checks.yml no longer invokes it"
            )
        if (
            "refresh_split_owner_acceptance_matrix.py" in workflow_text
            and "check_split_owner_acceptance_matrix.py" not in workflow_text
        ):
            errors.append(
                "convergence-checks.yml appears to use refresh_split_owner_acceptance_matrix.py "
                "without check_split_owner_acceptance_matrix.py; "
                "update docs/convergence_ci_inventory.md canonical CI entrypoint if intentional"
            )

    return errors


def assert_convergence_ci_inventory_split_owner_doc_contract(*, repo_root: Path | None = None) -> None:
    errors = convergence_inventory_doc_contract_errors(repo_root=repo_root)
    if errors:
        joined = "\n".join(f"- {item}" for item in errors)
        raise AssertionError(f"convergence inventory governance doc parity drift:\n{joined}")

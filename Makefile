# Optional developer shortcuts (Unix/mac/Git Bash). On Windows without ``make``,
# use ``python scripts/refresh_split_owner_acceptance_matrix.py`` and
# ``docs/audits/README.md`` / ``tests/README_TESTS.md``.
.PHONY: planner-convergence-audit planner-convergence-check \
	split-owner-matrix-report split-owner-matrix-check split-owner-matrix-refresh

planner-convergence-audit:
	python tools/planner_convergence_audit.py

# Aggregate: static audit + focused Planner Convergence pytest slice (no GPT in these files).
planner-convergence-check: planner-convergence-audit
	python -m pytest tests/test_planner_convergence_contract.py tests/test_planner_convergence_live_pipeline.py tests/test_prompt_context_plan_only_convergence.py tests/test_planner_convergence_static_audit.py

# BU23/BU24: regenerate checked-in docs/audits/BU15_split_owner_acceptance_matrix.md (idempotent).
split-owner-matrix-report:
	python scripts/refresh_split_owner_acceptance_matrix.py --write-report-only

# BU20/BU21 contract gate; BU22 matrix-edit checklist: docs/audits/README.md
split-owner-matrix-check:
	python scripts/check_split_owner_acceptance_matrix.py

# BU23/BU24: report regeneration + contract gate + pytest contract slice (idempotent).
split-owner-matrix-refresh:
	python scripts/refresh_split_owner_acceptance_matrix.py

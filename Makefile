# Optional developer shortcuts (Unix/mac/Git Bash). On Windows without ``make``,
# use the copy/paste commands in ``docs/planner_convergence.md``.
.PHONY: planner-convergence-audit planner-convergence-check

planner-convergence-audit:
	python tools/planner_convergence_audit.py

# Aggregate: static audit + focused Planner Convergence pytest slice (no GPT in these files).
planner-convergence-check: planner-convergence-audit
	python -m pytest tests/test_planner_convergence_contract.py tests/test_planner_convergence_live_pipeline.py tests/test_prompt_context_plan_only_convergence.py tests/test_planner_convergence_static_audit.py

# Baseline reconstruction

HEAD d40f1ed198236c604085f1c842ead267a8104ce2 is not a complete pre-repair baseline: the worktree
contains substantial uncommitted modules. HEAD orchestration lacks authored_travel_admission.
No checkout, reset, stash, import editing, module mixing, or historical execution was performed.

Historical evidence inspected: post-NPC SUMMARY, ROOT_CAUSE, REGRESSION_RESULTS,
TWELVE_TURN_COMPARISON, INTEGRITY, implementation.diff and adjacent_focus_junit.xml; previous
adjacent audit reports, overlay_manifest, both capture JSON files, and JUnit; existing local
dated and stable review ZIPs; the surviving temporary build_overlay.py/capture_failures.py sources.
The predecessor explicitly says it did not obtain a pre-edit adjacent run. Its JUnit is post-repair.
The earlier 118-test passing slice is a different selection and does not establish these twelve as passing.

The prior adjacent audit copied current game, substituted three HEAD files and manually removed
handoff insertions from orchestration while retaining authored travel. Its captures match each other.
This supports a preexisting-failure hypothesis but is a reconstructed counterfactual, not an
authenticated source state immediately before repair. The saved overlay has no exact pre-edit
dirty-tree hash or patch provenance proving all remaining modules' temporal compatibility.
We read this evidence, did not rebuild or execute that mixed-source package, and do not promote
its equality into confirmation that the three prose failures predate the repair.

Read-only source comparison is recorded in source_comparison.json: current hashes, HEAD hashes,
git-diff hashes/statistics and preserved repair diff hash. Current source paths are hashed at entry
and exit. PR-PLAY-67's written public-resolution contract independently establishes C for nine
stopping assertions without needing an exact temporal baseline. Three prose defects remain E as
to origin; their current manifestation is not uncertain.

Fresh unchanged tests reproduce the same twelve identities against the current working source.
183 collected (176 adjacent + 7 controls), 171 passed, 12 failed, zero errors/skips. Full command,
nodes, JUnit and tracebacks are recorded. Initial instrumentation run incorrectly blocked Windows
asyncio loopback socketpairs: 20 failures and 7 setup errors. That invalid product run is retained
under instrumentation_failed and excluded from classifications. After allowing loopback, external
connections remain fail-closed and all environmental failures disappear. No protected files changed.

Limitation: this audit supports a meaningful conditional judgment, not full temporal regression
attribution. Preserve and authenticate coherent source snapshots and exact commands before future
edits; do not replace dirty working modules with HEAD. Baseline work is the selected next action.

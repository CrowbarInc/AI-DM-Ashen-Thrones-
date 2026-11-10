# Bounded provenance search

Milestone `pr_play_baseline_provenance`. **Condition B: no authentic sufficiently complete pre-repair development snapshot. Search closed.**

Examined only repository review archives, named historical handoff packages, preserved repair diff/source-comparison manifests, predecessor test/capture evidence, local Git references/reflogs/unreachable-object inventory, and the explicitly named `%TEMP%/pr_play_adj_audit` path. No unrelated user-directory search, network recovery, branch reconstruction, historical execution or mixed-source execution occurred.

Machine inventory: `artifacts/pr_play_baseline_provenance/historical_archives.json` records 32 archive copies (some duplicates), full SHA-256, internal campaign summary and presence/hash of eight required source/test modules. Every archive lacks at least one of this minimum set, so none meets completeness. Names and ZIP timestamps were not used as proof. Immediate pre-repair post-optimization and AT-OPT-06 packages contain reports/measurements, not complete source. Post-NPC packages contain an implementation diff and after-edit test file/results, not a pre-edit dirty-tree capture. Recovery archives are later evidence.

`git_provenance.json` contains exact read-only commands: show-ref, log -12, reflog --all, stash list, fsck --full --no-reflogs --unreachable. No current stash exists. `git_candidate_assessment.json` examines eight unreachable commits, two Codex checkpoint refs and HEAD. All lack the later player HTTP projection and authored-travel definition required by the current imports. The unreachable inventory contains 14,946 blobs, 61 trees and eight commits. Unattached blobs/trees have no capture time or binding to a coherent pre-repair development state. Do not assemble them into a historical hybrid. Codex checkpoint refs are tree objects rather than normal dated commits; blank commit-time fields do not establish a capture time.

`local_snapshot_inventory.json` records whether the exact earlier temporary package survives. Its saved overlay manifest expressly describes current source plus selected HEAD files and manual deletion of handoff insertions. Even if present, it is a reconstructed approximation. Equality of its three failure responses supports a hypothesis, not authenticated preexisting attribution.

| Authentication requirement | Finding |
|---|---|
| Source-state identity | HEAD identifies a much older committed state; no exact dirty pre-repair identity |
| Capture time | Dated archives/commits identify their artifacts, not a complete pre-repair working tree |
| Relationship to repair | Diff identifies edits; traces distinguish before/after intent behavior |
| Relevant production files | No surviving pre-repair coherent complete set |
| Relevant tests | Current and post-repair tests/results survive; exact historical environment missing |
| Dependencies | Current versions captured; no complete compatible historical dependency/source binding |
| Coherent state | No authenticated aggregate manifest for the pre-repair dirty tree |
| Predates repair | Some evidence predates repair, but does not capture all required files |
| Integrity | ZIP/diff hashes establish surviving bytes only |

Relevant earlier evidence read: recovery SUMMARY, FAILURE_INVENTORY, BASELINE_RECONSTRUCTION, CONTRACT_ANALYSIS, NEXT_STEP_DECISION, HANDOFF_RECOVERY and targeted verification; previous audit reports/overlay/captures; post-NPC SUMMARY, ROOT_CAUSE, REGRESSION_RESULTS, INTEGRITY, routing contract, diff and JUnit; PR-PLAY-67 public-response contract; AT-OPT-06 regression/CI definitions. Local CI configuration is generic replay/governance evidence, not a pre-repair dirty-worktree run. Earlier 118 passing tests are a different selection from the twelve failures.

Stopping decision: all bounded source classes reasonably capable of preserving this state have been evaluated. Authentic baseline requirements are unmet. Historical attribution is unresolvable from available evidence; no further historical-reconstruction cycle is warranted. The new current baseline permits future development comparison.

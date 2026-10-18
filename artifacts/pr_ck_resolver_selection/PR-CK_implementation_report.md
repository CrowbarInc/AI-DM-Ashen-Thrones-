# PR-CK implementation report

MODE: ORDINARY GAMEPLAY RESOLVER SELECTION REPAIR

LIVE CALLS: 0

HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`

The dirty worktree was not reset and unrelated modifications were not discarded.

PR-CJ inherited decision: C — MULTIPLE INDEPENDENT DEFECTS

## What changed

The first break was ask-by-default, then social-by-default, then a social-only stage gate.

- Investigation language already owned by the inspect family, including investigate and search, is an inspection. Search is no longer a physical act that skips exploration. A subordinate "before investigating" does not become the turn's operation.
- A leftover ask is social only when the utterance names a social subject: a question, a request, quoted speech, or a speech act such as talk, tell, or persuade. "Where are we?" and a bare "describe" do not.
- `select_ordinary_resolver` selects social for a social subject or a repeat. It no longer selects social for every ask. An unspecified leftover ask is generation.
- Waits, descriptions, scene orientation, and unmatched statements use operation `unresolved` and the generation resolver. Generation may run the existing passive-wait stage.
- When the selected resolver is exploration, chat parses exploration before world-action recovery. Travel still reaches exploration where it did before.
- Unresolved narration is not sealed before the existing question and scene-stall retry loop. If no retry is owed, a hard-valid line is sealed before pressure can rewrite it.
- The sound "scrape of" is not classified as a physical scrape mark. Marked scrapes still are.

No new resolver, no new operation name, no provider call, and no phrase list of the failing tests were added.

## Decision

B — PARTIAL REPAIR

Cluster A selection is repaired for investigation, scene-stall retry, "where are we?" narration retry, and hard-valid atmosphere. Two pressure tests still fail on beat content. Embedded roll metadata, response-type metadata, and the action-path stub sentence remain the untouched PR-CJ clusters. Legitimate social dialogue and the authority suites stayed green. No shared-pipeline failure is new relative to PR-CJ.

## Recommended next step

Repair the passive-pressure beat so a tense wait can emit a concrete interruption without turning a hard-valid atmosphere line into NPC dialogue. Leave PR-CJ clusters B, C, D, E, G, H, and I untouched until that beat is specified.

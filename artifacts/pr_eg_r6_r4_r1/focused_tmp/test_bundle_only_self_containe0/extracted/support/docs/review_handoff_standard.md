# Review Handoff Standard

> **Human review should require judgment, not artifact archaeology.**

> **Canonical evidence may remain distributed. The review surface must be centralized.**

## Purpose

Campaign evidence remains authoritative in its normal `docs/`, `artifacts/`, source, and test
locations. A review handoff is a generated orientation and export layer that lets a reviewer understand
the campaign from one Markdown file and, when needed, upload one ZIP.

The handoff does not replace, reinterpret, or rewrite canonical evidence.

## When a full handoff is required

A full handoff is normally required for work that changes player-facing behavior, semantic validation,
evaluator authority, architecture, state/world behavior, major gameplay or AI-GM behavior, or the
validation portfolio; produces evaluator disagreement or human-review-required evidence; requires a
product/design decision; is explicitly marked for external review; or closes a significant campaign.

Tiny structural changes, routine maintenance, and local unit-only work may use a lightweight handoff or
ordinary completion note. Structural-only handoffs must not fabricate behavioral evidence.

## Stable location

The latest handoff always appears at:

```text
handoff/
  CURRENT_REVIEW.md
  REVIEW_MANIFEST.json
  CURRENT_REVIEW.zip
```

When enabled, inexpensive history copies appear at:

```text
handoff/history/<campaign-id>/
  REVIEW.md
  REVIEW_MANIFEST.json
  REVIEW.zip
```

Generating a new handoff replaces `CURRENT_REVIEW.*`. Canonical sources remain untouched.

## Review summary contract

`CURRENT_REVIEW.md` is a 5-10 minute orientation and decision surface. It contains Campaign,
Executive Summary, Changes Made, What Was Tested, Behavioral Evidence, Decisions Requiring Human
Review, Known Problems, Missing Concepts, What This Campaign Does Not Prove, Recommended Next Step,
and Review Bundle Contents.

Production, validation, tooling, documentation, and generated-artifact changes are separated. Focused,
broader, full-suite, and runtime/model evidence are not collapsed into one PASS claim. Campaign-specific
and pre-existing failures remain distinct. The decision section always exists and states explicitly
when no human decision is required.

## Bundle and manifest

`CURRENT_REVIEW.zip` contains the summary, `REVIEW_MANIFEST.json`, and selected support files under
their repository-relative paths below `support/`.

The manifest records schema/tool version, campaign, generation time, summary path, file count, payload
and ZIP sizes, warning threshold, included and omitted files, canonical source path, bundle path, role,
canonical/generated status, inclusion rationale, behavioral/review flags, size, SHA-256, configuration
provenance, and omission/sensitive-file policies.

Generated summary/manifest hashes are not treated as canonical provenance. Canonical packaged files
retain hashes and source paths.

## Selection policy

The generator accepts an explicit campaign configuration. It includes the primary report, expands only
recognized `evidence_summary.md` and `evidence_manifest.json` files from named evidence packets, and
adds explicitly listed support files. It does not crawl the repository or entire artifact trees.

Always included:

- `CURRENT_REVIEW.md`
- `REVIEW_MANIFEST.json`
- primary campaign report

Included when explicitly applicable:

- standardized evidence summaries/manifests
- human-review records and selected transcripts
- architecture/inventory reports
- calibration/config/schema artifacts
- focused implementation and tests needed for the review question

Normally excluded:

- repository, `.git`, virtualenv, dependency, build, and test-cache copies
- previous handoff ZIPs or handoff history
- unrelated artifacts and historical campaigns
- redundant identical files
- large raw datasets when a summary/reference is sufficient
- sensitive/local configuration and unrelated user data

The objective is review sufficiency, not archival completeness.

## Size and deduplication

Default per-file packaging limit: 5 MiB. Default bundle warning threshold: 20 MiB. Both are configurable
per campaign. Oversized requested files are listed as omissions with size, reason, and canonical path.
Files with identical SHA-256 content are included once and duplicates are explicitly recorded.

The summary and manifest report file count and ZIP/payload size. ZIP ordering and metadata are stable;
supplying a fixed `--generated-at` makes repeated generation byte-stable for unchanged inputs.

## Sensitive-file safeguards

The generator rejects paths containing `.env` variants, credential, API-key, token, secret,
private-key, or authentication-cache filename patterns; private key/certificate suffixes; and VCS,
virtualenv, dependency, or cache components. It excludes ZIPs and handoff paths recursively.

The safeguard uses path metadata and does not read or print secret values to decide whether a file is
sensitive. Explicit source selection remains mandatory.

## Validation Evidence Standard relationship

The Validation Evidence Standard answers: **what behavioral evidence should exist?**

The Review Handoff Standard answers: **how does that evidence reach a reviewer with minimal effort?**

When evidence packets are supplied, the handoff surfaces selected success/failure, disagreement,
ambiguity, stress classification, review status, exact exchanges, and remaining limits. It packages
the packet summary and manifest instead of duplicating every underlying runtime artifact.

## Generation command

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'
& 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  tools\build_review_handoff.py `
  --config data\validation\review_handoffs\validation_evidence_standard.json
```

Use `--output-dir` to test another destination, `--generated-at` for reproducible generation, and
`--no-history` to skip history copies.

## Campaign verification

The Review Handoff Automation campaign was verified on 2026-09-18 without rerunning gameplay:

- Focused: `11 passed` in `tests/test_review_handoff.py`.
- Broader: `70 passed` across handoff, evidence, reactive-player, calibration, and playability tests;
  one existing Starlette TestClient deprecation warning remained.
- Full suite: `49 failed`, matching the known pre-existing red baseline count and unrelated failure
  families. No handoff test failed.
- Bundle-only review: `PASS`. An extracted `CURRENT_REVIEW.zip`, without repository access, answered
  the campaign, scope, test, baseline, behavioral-evidence, disagreement, ambiguity, decision,
  limitation, provenance, and next-step questions required by the review contract.

Exact verification commands:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'
& 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  -m pytest tests\test_review_handoff.py -q --tb=short

& 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  -m pytest tests\test_review_handoff.py tests\test_validation_evidence_standard.py `
  tests\test_reactive_player_validation.py tests\test_semantic_calibration_corpus.py `
  tests\test_playability_eval.py tests\test_run_playability_validation_tool.py `
  tests\test_playability_smoke.py -q --tb=short

& 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  -m pytest -q --tb=short
```

## Future campaign integration

A review-requiring Codex campaign ends in this order:

1. Complete the scoped implementation.
2. Run required validation.
3. Generate canonical reports and behavioral evidence packets where applicable.
4. Add or update an explicit handoff configuration.
5. Generate the standard review handoff.
6. Verify the Markdown, manifest, ZIP, provenance, sensitive exclusions, and bundle-only review test.
7. Stop and report `handoff/CURRENT_REVIEW.md` and `handoff/CURRENT_REVIEW.zip`.

Future instructions can simply request: `Generate the standard review handoff bundle for this campaign.`

## Limitations

- The generator cannot determine whether an omitted but unrequested artifact was conceptually important;
  campaign authors must choose explicit sources carefully.
- Filename safeguards reduce accidental secret inclusion but do not classify arbitrary sensitive prose
  inside otherwise ordinary files.
- Packaged files are point-in-time copies. The manifest hashes detect later divergence from canonical
  sources but do not synchronize it.
- A centralized review surface reduces search effort; it does not replace human judgment or make the
  underlying validators authoritative beyond their documented scope.

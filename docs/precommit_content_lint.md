# Optional pre-commit: content lint

This repo runs **observer-mode** content lint in CI (Phase 1): the check runs and surfaces issues, but the workflow does not block merges on lint outcome. A local pre-commit hook can mirror that posture: run the same CLI before each commit so problems show up early, without turning on stricter exit behavior than CI has enabled.

## What the hook does

On each commit, pre-commit invokes `python tools/run_content_lint.py` from the repository root. The tool prints a summary (and details unless `--quiet`) and exits non-zero **only when there are errors**, matching the default CLI (no `--fail-on-warnings`). Warnings alone do not fail the hook, consistent with current Phase 1 CI.

## Install pre-commit

Choose one:

```bash
pip install pre-commit
```

Or use your usual Python environment manager (`uv tool install pre-commit`, `pipx install pre-commit`, etc.).

## Minimal sample `.pre-commit-config.yaml`

Add this file at the repo root (or merge the `hooks` entry into an existing config if you already use pre-commit elsewhere):

```yaml
repos:
  - repo: local
    hooks:
      - id: content-lint
        name: content lint
        entry: python tools/run_content_lint.py
        language: system
        pass_filenames: false
```

Then install the git hook (opt-in, per machine):

```bash
pre-commit install
```

Run once over all files (optional sanity check):

```bash
pre-commit run --all-files
```

The `content-lint` hook ignores staged filenames on purpose: the linter scans scene JSON under the configured scenes directory, not individual staged paths.

## Stricter behavior (optional, local only)

To fail commits when there are **warnings** as well as errors, pass the CLI flag the tool already supports (this is **stricter than** the repo’s current observer-mode CI):

```yaml
        entry: python tools/run_content_lint.py --fail-on-warnings
```

Do not use this unless you explicitly want that policy on your machine.

## Future tightening

When the project enables the optional stricter warning gate in CI (if that step is turned on in the workflow), you can align local hooks the same way by adding `--fail-on-warnings` to the hook `entry`, or by running the CLI with that flag in other automation. Until then, the default command above stays in line with CI’s non-blocking Phase 1 posture.

# Integrity and Evidence Limitations

## Verdict basis

**B/PARTIAL.** The incident, the route inventory, the ledger totals, and the budget miss are evidenced. The captured 22,777-token prompt was not retained, so section-level token attribution is reconstructed and incomplete.

## Source

| Item | Value |
| --- | --- |
| Branch | `feature/product-realization` |
| HEAD | `d40f1ed198236c604085f1c842ead267a8104ce2` |
| Working tree at entry | Already dirty. `git status --short` reported 744 lines. This audit did not reset, clean, or commit |
| F3 fingerprinted files | Match `artifacts/pr_play_79df3/source_fingerprint.json` for publication contract, api, live chat interpretation, player HTTP boundary, player HTTP projection, provider budget, and `static/app.js` |
| `game/gm.py` | SHA-256 `1f31510377adb072750bc187effffcf6c45387373a86594732601d88fe185614`. Dirty versus HEAD. Not in the F3 fingerprint |
| `game/prompt_context.py` | SHA-256 `ccf21b03150566d4439b48c2e4e53a0563be74636087c0ee0a8fa6479414996f`. Dirty versus HEAD. Not in the F3 fingerprint |
| Exit fingerprints | Same production hashes. This cycle did not edit `game/`, `static/`, or `data/` |

HEAD is not the executable tree. The F3 executable hashes that were recorded still match the working tree.

## Protected data

`artifacts/pr_play_79df3/protected_exit.json` lists 150 files. Re-hashed during this audit: 150 match, 0 missing, 0 changed.

F3 provider ledger SHA-256 `72db47fe9626b0ce9b385198485e8cc069d29f7f667d48bcf89617017f06c7ce` (1,450 bytes), unchanged after analysis.

No live provider call. No campaign opening. No gameplay execution against the provider. Prompt reconstruction imported `build_messages` with `ASHEN_DISABLE_PROVIDER_CALLS=1` against a copy under `development/tmp/`, then that copy was removed. Historical ledgers were read only.

## Evidence used

- `docs/DEVELOPMENT_CONSTITUTION.md`, `docs/NEXT_SESSION.md`, `docs/review_handoff_standard.md`
- `artifacts/pr_play_79df3/` review, HTTP script, HTTP result, session log, snapshot, provider ledger, browser ledger, source fingerprint, protected exit
- Live ledgers for 79, 79A, 79B, 79C, 79D (three browser files), 79D-F, 79D-F2 (two files), 79D-F3
- Current `game/gm.py`, `game/api.py`, `game/provider_budget.py`, `game/publication_contract.py`, `game/physical_adjudication.py`, `game/expressive_dialogue.py`, `game/semantic_interpreter.py`, `game/live_chat_interpretation.py`, `game/integrated_play.py`, `game/model_routing.py`, `game/config.py`
- F3 task cap from the prior session transcript summary

Regression copies under `historical/regress` were not used as cost samples.

## Gaps

- Captured prompt bytes and the estimate actually passed to `admit_request`: UNKNOWN.
- Whether output 600 means truncation: HYPOTHESIS. The count equals the default cap. Finish reason was not logged.
- Useful-publication counts for 79A, 79B, and 79C beyond the handoff prose: UNKNOWN.
- Browser paint for every cycle in this audit: not measured.
- 79A’s two 25,294-input primary calls: equal recorded counts. Duplicate prompt text is unproven.
- `gm.py` hash at the moment F3 dispatched: not recorded. Reconstruction uses the current dirty file.

## Files this cycle creates or updates

Created under `development/campaigns/product_realization/at_opt_01/` and `artifacts/at_opt_01/`. Updated `docs/NEXT_SESSION.md` and the generated `handoff/CURRENT_REVIEW.*`. Archive path and SHA-256 are in `artifacts/at_opt_01/archive_path.txt` after the bundle is sealed. That digest is outside the zip so the hash is not circular.

No production source, campaign save, provider ledger, frozen holdout, or unrelated dirty file was edited.

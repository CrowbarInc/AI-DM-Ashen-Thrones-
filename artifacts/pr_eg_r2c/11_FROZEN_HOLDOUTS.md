# 11 — Frozen Holdouts

frozen_holdouts.json and freeze.json were created by setup_baseline.py before production edits. SHA-256 `27b003eaa4ad26ec7435d483b1529338ef6a7aaa63b33a254404469be053f990`. Six independent inputs vary wording, speakers (Iona/Orr/Vel/Sela/Tam), subjects (archives/ferry/vault/mill/reward), epistemic posture and repeat references. Expectations were never rewritten. H1–H5 pass; H6 fails. Original first run: holdout_first_junit.xml / holdout_first_console.txt; final run: final_junit.xml. No tuning against the failing held-out expression was performed.

Separate live_plan.json was frozen before fresh execution; SHA-256 `db0ff9e9f2b9c15ab25658c55cd795f000c25464e4f896e1a47615c2048c526d`. It remains byte-identical. All failures and raw scorer flags are retained. Direct frozen holdouts use JSON roundtrip; the separate six-case matrix and both live conversations use actual storage. These evidence levels are distinguished.

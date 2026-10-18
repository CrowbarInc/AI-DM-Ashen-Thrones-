# PR-EF-R1 baseline — recorded before production edits

Revision: d31beb7d73dd4fda0f22184a6a69b947b5f470ff

Current comparison: 271 passing / 30 failing. Commands, exact identities and normalized signatures in baseline_command.json, baseline.json and baseline_junit.xml. Working tree is extensively dirty; status_before.txt and source_before preserve the starting point. No AGENTS.md found.

Production interpretation/narration: gpt-4.1-mini (verify live response model); 320 interpretation output cap; default timeout 45s. PR-ED budgets and usage accounting inspected. Historical PR-EF: 5/12 strict, 10/12 recorded HTTP behavior, two failed fresh conversations, final NPC recall repair unqualified. Historical profile medians 87/82ms disabled; 85,242/87,739 live tokens, differing code.

Confirmed handoff cause: deterministic bridge MOVE reaches ordinary contract built with normalized_action=None, which reparses it as unresolved and rejects it; final fallback repeats lantern fact. Ownership prompt appends to operation-first instructions with underspecified enums, purpose ACTION can overwrite NPC owner, pending projection only supplies kind. Causal question can be intercepted by _recent_visible_answer before semantic interpretation, which repeats outcome rather than explaining it.

Budget: 64 requests maximum; 24 holdouts and 38 reserved final conversation calls, two availability/diagnosis calls. See budget.json. No active campaign used. Independent 12-expression holdout frozen before implementation.


Fresh pre-edit probe reproduced NPC/ASK for the GM expression question. Credential configuration was checked without exposing it. Returned model gpt-4.1-mini-2025-04-14; configured interpretation and narration gpt-4.1-mini. Production timeout 45s; validation 25s, interpretation cap 320 and narration cap 1600. Instrumentation active via provider_budget.

Actual cycle usage: {'input_tokens': 336813, 'output_tokens': 16494, 'total_tokens': 353307, 'requests': 75}. Self-imposed budget revisions 64 -> 68 -> 80 requests reserved additional final qualification after newly evidenced defects; token ceilings stayed 430000 input / 22000 output / 452000 total. No budget exhaustion or pre-repair acceptance substitution.

Commands: baseline_command.json and final_command.json; python tools/validate_pr_ef_r1.py --mode conversation --variant 5; --mode holdouts (fresh); --mode holdouts --variant 3 --replay artifacts/pr_ef_r1/holdouts_1.json (zero external requests). Provider-disabled HTTP tests run outside the Windows sandbox for local socketpair support; live-model test guards remain enabled. Representative comparison family only, not full repository suite.

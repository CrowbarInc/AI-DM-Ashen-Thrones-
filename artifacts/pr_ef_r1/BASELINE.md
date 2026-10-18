# PR-EF-R1 baseline — recorded before production edits

Revision: d31beb7d73dd4fda0f22184a6a69b947b5f470ff

Current comparison: 271 passing / 30 failing. Commands, exact identities and normalized signatures in baseline_command.json, baseline.json and baseline_junit.xml. Working tree is extensively dirty; status_before.txt and source_before preserve the starting point. No AGENTS.md found.

Production interpretation/narration: gpt-4.1-mini (verify live response model); 320 interpretation output cap; default timeout 45s. PR-ED budgets and usage accounting inspected. Historical PR-EF: 5/12 strict, 10/12 recorded HTTP behavior, two failed fresh conversations, final NPC recall repair unqualified. Historical profile medians 87/82ms disabled; 85,242/87,739 live tokens, differing code.

Confirmed handoff cause: deterministic bridge MOVE reaches ordinary contract built with normalized_action=None, which reparses it as unresolved and rejects it; final fallback repeats lantern fact. Ownership prompt appends to operation-first instructions with underspecified enums, purpose ACTION can overwrite NPC owner, pending projection only supplies kind. Causal question can be intercepted by _recent_visible_answer before semantic interpretation, which repeats outcome rather than explaining it.

Budget: 64 requests maximum; 24 holdouts and 38 reserved final conversation calls, two availability/diagnosis calls. See budget.json. No active campaign used. Independent 12-expression holdout frozen before implementation.

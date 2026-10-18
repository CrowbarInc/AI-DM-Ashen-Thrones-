# 07 — Confirmation and Compound-Intent Audit

Removed the `len(connected) > 1 or unsupported` conflation. A singleton unsupported operation declines without a pending executable proposal or confirmation question. Unsupported interpretation status also declines directly. Genuine compounds retain the original component order and operation identity, incidental context and later intentions.

Before offering the first step, production checks the existing full bridge: connected operation, compatible visible target, resolved references and authored/known destination. Eligibility remains independent of resolver success. An unsupported first step cannot be skipped in favor of a later supported action. A supported first step with unsupported later work may be confirmed, while the response explicitly says that later work cannot be resolved as stated.

After execution, eligible remaining steps stay in the bounded pending sequence. Unsupported remainder is stored as `deferred_intentions`, not an executable proposal. A yes response to that remainder declines and clears it. Withdrawals clear pending work; corrections clear pending work and request a revised action without rolling back resolved facts. Existing PR-EC inspection-then-picking and movement tests remain in the comparison family.

The final mixed-input repair preserves independently consequential components even if the provider labels the question as GM. It asks to settle the condition and states that no action has happened; it does not automatically execute upon an unresolved condition. General-purpose revised-action referent binding remains limited: a correction safely clears and asks for the revised action rather than executing it automatically.

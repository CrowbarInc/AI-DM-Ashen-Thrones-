# Summary

Milestone: `pr_play_grounded_marking_removal`. Date: 2026-11-09.

**Verdict: A/PASS.**

A player can remove one established visible marking from an established accessible object through the existing chat turn. The turn recognizes ordinary removal language, resolves one object and one active marking, checks the established removal method and any required cleaning material, and commits through `prepare_removal`. Concealed, restricted, and already-removed markings are not selected. The published sentence follows the committed removal. A contradictory seal is replaced by that sentence. Save, reload, and snapshot restore keep the removed marking out of the current state and keep its historical receipt.

Original T06 stays the grounded unresolved marking sentence. No garment, mud, or marking is invented. T04, T05, T09, T11, and T12 match the immediate predecessor. Live provider calls: **0**.

The bounded marking lifecycle — create, observe, remove, observe again, and recover that result after reload — is complete enough to close as a subsystem. It does not complete object interaction in general.

Exactly one next milestone: `pr_play_broad_gameplay_evaluation`. Do not begin it automatically.

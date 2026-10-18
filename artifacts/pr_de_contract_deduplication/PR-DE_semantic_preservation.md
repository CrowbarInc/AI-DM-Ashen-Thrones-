# PR-DE Semantic Preservation

For each fixture, the post payload was compared with the baseline payload after putting the seven omitted fields back from `response_policy`. Comparison ignores JSON key order.

All twelve normalized payloads were equivalent. Unexplained diff count: 0. Documented dynamic diffs in that paired run: 0, because both sides used `PYTHONHASHSEED=0`.

Preserved on every pair:

- player input
- `gm_resolution_decision`, mechanical resolution, and answer recipe
- `narration_visibility` and public scene facts
- authorized speaker (`guard_captain` on S1, S2, S3, F1, C1, and H1)
- response envelope
- the same `response_policy` children, including the seven surviving contracts
- `scene.gm_only.hidden_facts`
- the `interaction_continuity` snapshot

S1, S2, and S3 still select `harmless_social_incidental_dialogue_v1`. F1, C1, and H1 still leave that projection unselected. C1 remains on the narration-only full payload aside from the removed mirrors.

Policy bytes and conversation-history bytes (recent log, selected memory, and one window object) are unchanged on every fixture. The history cap was not changed.

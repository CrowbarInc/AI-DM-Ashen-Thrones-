# PR-CT Prompt Contract Tests

Added `tests/test_pr_ct_safe_prompt_deduplication.py`.

The tests inspect serialized provider-facing messages and assert player input, scene/session, turn packet, response policy, narration visibility, decision-facing recipe, GM resolution decision, resolution contract, and response schema remain present while exact system-owned duplicates are absent from payload instructions.

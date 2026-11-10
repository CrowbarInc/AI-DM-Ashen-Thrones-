# Regression results

Compared with PR-PLAY-78A identities. PR-PLAY-79B did not rerun these lanes, so a failure that is absent from the 78A list is reported as new.

| Lane | Passed | Failed | New vs 78A | Cleared vs 78A |
| --- | --- | --- | --- | --- |
| Focused | 1057 | 28 | 8 | 0 |
| Boundary | 101 | 6 | 0 | 0 |
| Broader | 0 | 9 | 0 | 0 |

Reference counts carried from PR-PLAY-79B, not a fresh 79B run: focused 1,065/20, boundary 101/6, broader 0/9.

Boundary and broader match those counts and add no new identities.

The focused lane was recorded before the repeat-examination prefix. Its eight new identities were:

- `test_four_actions_keep_authority_and_recover`
- `test_action_specific_fallback_and_recovery`
- `test_repeat_sequence[chat]`
- `test_repeat_sequence[structured]`
- `test_publication_http[no_new]`
- `test_publication_http[continuity]`
- `test_publication_http[fast_path]`
- `test_matrix[5]`

After the prefix, the examine-wording tests pass, including both repeat-sequence cases. Five identities still fail. The repeat examination names the notice board and says nothing new, but it does not restate the northwest clue, which `test_four_actions_keep_authority_and_recover` requires. The three publication-http cases raise `KeyError: 'publication'` because that older trace is not written when the final engine sentence is returned directly. `test_matrix[5]` still differs in its resolution payload. Those five are not labeled historical.

The lifecycle failures inside the original 20 are the same "Unable to complete this request" block recorded against 78A. They are not new.

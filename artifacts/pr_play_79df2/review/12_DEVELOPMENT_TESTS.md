# Development tests

`tests/test_pr_play_79df2_publication.py`: 36 passed.

Coverage includes fallback advance, stale acceptance not attached, composer provenance kept, rejected repeat of the same sentence, empty text, accepted expression, candidate-must-be-visible, narration not applied to speech, physical narration, publication events, one event per call, save/reload, cross-session isolation, no invented world truth, non-canonical commitments, uncertainty, provider accounting, admission refusal, physical one-expression and second-skip, recall, renderer non-mutation, duplicate chat, HTTP fallback, player projection, and protected-data write blocking.

The player projection assertion expects `resolution == {}` when a resolution was present, which is the existing projection contract.

PR-DW failure recovery

Controlled failures exercised:
- Forbidden runtime action from author mode: HTTP 403, no runtime action.
- Exact OOC correction: no resolver invocation, no gameplay mutation.
- Generic OOC statement: failed safety expectation; misclassified and advanced turn/time.

Provider timeout:
- Not exercised.

Malformed provider response:
- Not exercised.

Repeated submission:
- Not exercised.

Response-generation failure:
- Not exercised.

Pre-commit vs post-commit:
- The generic OOC probe committed turn/time advancement before returning a response.
- Retrying post-commit response failure was not exercised.

Stop reason:
- Live testing stopped after the generic OOC probe caused provider calls and state advancement.


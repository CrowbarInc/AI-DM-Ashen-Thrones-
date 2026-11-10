# PR-PLAY-21 authorization contract (before implementation)

Inspection finds no authenticated HTTP session, trusted role, capability verifier,
or server-side author authorization context. UI mode policies constrain requested
operations but do not authenticate callers. Loopback binding and wildcard CORS do
not establish authorization. TestClient is not a privileged identity.

| Context | Player view | Author/debug view |
| --- | --- | --- |
| Ordinary HTTP, including loopback and same-origin | Allowed under existing endpoint policy | 403 |
| HTTP with author/debug query or supported body selector | No silent downgrade | 403 before state loading/projection |
| Unknown selector | 400, existing convention | No projection |
| Direct internal Python projection/storage tooling | Existing contract | Existing contract; process/filesystem access required |
| Authenticated HTTP author | No such mechanism exists | No new mechanism in this pass |

Implement denial in the shared HTTP mode resolver. Apply it to every caller of
that resolver to avoid leaving equivalent body-selected author responses or writes
as an alternate path. Keep internal pure policies, projection helpers and storage
workflows unchanged. No environment override, static token, header assertion,
loopback exception or Request=None bypass will grant HTTP privilege.

Compatibility consequence: existing browser author/debug tabs and author HTTP
writes fail closed. They were mode-selected, not independently authorized.
Preserving them requires a separately scoped trust/capability design. This pass
does not invent it. Internal author access remains available to code with local
execution/file access. Runtime player operations are unchanged.

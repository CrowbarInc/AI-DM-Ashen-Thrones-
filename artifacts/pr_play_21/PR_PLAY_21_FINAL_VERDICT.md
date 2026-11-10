# PR-PLAY-21 final verdict

**B — PARTIALLY REPAIRED**

1. **Disclosure reproduced?** Yes, deterministic synthetic sentinel in actual
   serialized ASGI HTTP responses, including GET /api/state?ui_mode=author.
2. **Affected endpoints?** GET /api/state (author/debug), GET /api/log (debug),
   GET /api/debug_trace (debug). POST /api/campaign also had a source-confirmed
   equivalent return of merged hidden campaign state through author mode.
3. **Root cause?** A requested visibility mode was accepted as authority without
   independently establishing requester entitlement.
4. **Trusted authorization mechanism?** None exists for privileged HTTP access.
   Existing local process/filesystem authoring and Python projections remain
   trusted internal tools, not an authenticated HTTP identity.
5. **Repair?** Common HTTP resolver fails closed with 403 for all author/debug
   modes before state access/projection; supported body forms covered too.
6. **Can an ordinary player obtain author state via ui_mode=author?** No, 403.
7. **Can an ordinary player obtain debug state?** No, 403, including log/trace.
8. **Related reads protected?** Yes within the reviewed shared selector boundary;
   all four API GET read routes inspected and tested.
9. **Author workflows preserved?** Existing internal Python/storage tools yes.
   Browser author/debug and author HTTP writes no: they lacked a trustworthy
   authorization mechanism and now fail closed. Restoring them needs scoped
   authorization design beyond this pass.
10. **Authoritative state unchanged?** Repair does not mutate state. Synthetic
    hidden facts persist; focused reads/denials preserve persisted fixture data.
    Existing derived compose_state synchronization behavior is unchanged.
11. **Public-state retrieval works?** Yes, status 200, public fields and transcript
    remain available; complete responses exclude synthetic hidden sentinels.
12. **Offline initialization works?** Yes, mocked provider transport, real opening
    publication and public response; initiative action also succeeds.
13. **New regressions?** No new reproducible gameplay/authorization regression in
    tested scope. Intentional privileged HTTP compatibility changes documented.
    One post-change Windows I/O failure passes on retry; exact OS cause unresolved.
14. **Preexisting failures?** 17 functional gameplay failures remain, matching
    PR-PLAY-20. Baseline additionally encountered one transient Windows I/O setup
    failure; repaired broader run encountered a different one. Both retries pass.
15. **Live-provider requests?** Zero. One synthetic SDK dispatch for initialization.
16. **Suitable for current deployment?** The reviewed read boundary now fails
    closed for ordinary HTTP callers, including local/origin callers. Local
    player reads and internal author tooling work. Current browser author/debug
    UX is unavailable. This is not certification for arbitrary untrusted clients
    or a completed application authentication design.
17. **Ready for ordinary live gameplay validation?** Not recommended by this
    verdict pending external review of the fail-closed compatibility decision
    and known gameplay baseline. No live validation was attempted.

The reported bypass is closed. B, rather than A, reflects the missing HTTP author
trust mechanism and resulting author/debug workflow loss, along with a non-green
gameplay baseline. No speculative authentication design was added.

**Recommended next step:** external review of this evidence and the explicit
fail-closed contract, deciding how trusted local author HTTP access should be
established in a separately authorized pass. Do not begin PR-PLAY-22 automatically.

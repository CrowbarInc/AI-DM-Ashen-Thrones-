# PR-CG Event Loop Comparison

## Default Policy

- Policy: `WindowsProactorEventLoopPolicy`
- In the managed sandbox, TestClient blocks while AnyIO starts the blocking portal and asyncio creates the event-loop self-pipe through `socket.socketpair()`.
- Stack evidence is preserved in `sandbox_socketpair_probe.stderr.txt`.

## WindowsSelectorEventLoopPolicy

- Policy: `WindowsSelectorEventLoopPolicy`
- In sandboxed probes, selector policy also reaches `socket.socketpair()` during event-loop self-pipe creation and does not resolve the failure.
- In unsandboxed local execution, both default and selector policies complete the minimal and representative HTTP tests.

## Decision

No event-loop policy override was implemented. The policy comparison shows the failing primitive is Windows loopback/socketpair under the managed sandbox, not Proactor-specific application behavior.


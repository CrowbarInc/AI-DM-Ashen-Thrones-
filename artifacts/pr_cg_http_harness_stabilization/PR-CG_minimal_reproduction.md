# PR-CG Minimal Reproduction

## Managed Sandbox Failure

`artifacts/pr_cg_http_harness_stabilization/sandbox_socketpair_probe.py` runs only:

```python
left, right = socket.socketpair()
```

Inside the managed sandbox it prints `start`, then times out after 8 seconds. The captured stack in `sandbox_socketpair_probe.stderr.txt` shows:

- `socket.py`, line 295, `accept`
- `socket.py`, line 646, `socketpair`
- `sandbox_socketpair_probe.py`, line 9

This reproduces the failure below FastAPI, Starlette, AnyIO, pytest fixtures, and application initialization.

## Unsandboxed Supported Configuration

The same local interpreter outside the managed sandbox completed the socketpair probe immediately:

```text
start
ok ('127.0.0.1', 50800) ('127.0.0.1', 50800)
```

The full bounded TestClient probe then completed without hangs in 18.268 seconds. See `PR-CG_reliability_matrix.json` and `probe_outputs/`.


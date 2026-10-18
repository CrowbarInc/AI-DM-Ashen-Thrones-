# PR-CG Environment Inventory

- Date: 2026-10-09
- HEAD: d31beb7d73dd4fda0f22184a6a69b947b5f470ff
- Worktree: dirty before PR-CG; existing unrelated modifications preserved.
- Python: 3.12.0
- Windows: Microsoft Windows NT 10.0.26200.0 / Windows-11-10.0.26200-SP0
- pytest: 9.1.1
- FastAPI: 0.140.0
- Starlette: 1.3.1
- AnyIO: 4.14.2
- HTTPX: 0.28.1
- Live provider calls: 0
- Pytest live-call guards: `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1`, `ASHEN_DISABLE_LIVE_INTERPRETATION=1`, live model guard fixture present in existing `tests/conftest.py`.

## Baseline Notes

- Plain `python --version` resolves to the Windows Store shim and cannot start in this workspace.
- Repository interpreter used: `.venv\Scripts\python.exe`.
- `Get-ComputerInfo` CIM access was unavailable; OS version was recorded through `[System.Environment]::OSVersion.VersionString`.


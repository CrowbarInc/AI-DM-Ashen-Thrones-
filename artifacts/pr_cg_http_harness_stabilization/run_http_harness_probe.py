from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import textwrap
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = Path(__file__).resolve().parent
OUT_DIR = ARTIFACT_DIR / "probe_outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _env(policy: str | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env["PYTHONFAULTHANDLER"] = "1"
    env.setdefault("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "1")
    env["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
    if policy:
        env["PR_CG_EVENT_LOOP_POLICY"] = policy
    return env


def _run(name: str, args: list[str], timeout: int, policy: str | None = None) -> dict[str, object]:
    start = time.perf_counter()
    proc = subprocess.Popen(
        args,
        cwd=ROOT,
        env=_env(policy),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        stdout, stderr = proc.communicate(timeout=10)
    duration = round(time.perf_counter() - start, 3)
    result = {
        "name": name,
        "policy": policy or "default",
        "timeout_seconds": timeout,
        "timed_out": timed_out,
        "returncode": proc.returncode,
        "duration_seconds": duration,
        "command": args,
        "stdout_path": str((OUT_DIR / f"{name}.stdout.txt").relative_to(ROOT)),
        "stderr_path": str((OUT_DIR / f"{name}.stderr.txt").relative_to(ROOT)),
    }
    (OUT_DIR / f"{name}.stdout.txt").write_text(stdout, encoding="utf-8")
    (OUT_DIR / f"{name}.stderr.txt").write_text(stderr, encoding="utf-8")
    return result


def _write_probe_files() -> tuple[Path, Path]:
    outside = ARTIFACT_DIR / "minimal_testclient_outside_pytest.py"
    outside.write_text(
        textwrap.dedent(
            """
            import asyncio
            import faulthandler
            import os
            import select
            import socket
            import sys

            faulthandler.dump_traceback_later(10, repeat=True)
            if os.environ.get("PR_CG_SOCKETPAIR_PATCH") == "1" and sys.platform == "win32":
                def _bounded_socketpair(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0):
                    if family not in (socket.AF_INET, socket.AF_INET6):
                        raise ValueError("Only AF_INET and AF_INET6 socket address families are supported")
                    if type != socket.SOCK_STREAM:
                        raise ValueError("Only SOCK_STREAM socket type is supported")
                    if proto != 0:
                        raise ValueError("Only protocol zero is supported")
                    host = "127.0.0.1" if family == socket.AF_INET else "::1"
                    listener = socket.socket(family, type, proto)
                    connector = None
                    try:
                        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        listener.bind((host, 0))
                        listener.listen(1)
                        addr, port = listener.getsockname()[:2]
                        connector = socket.socket(family, type, proto)
                        connector.setblocking(False)
                        try:
                            connector.connect((addr, port))
                        except (BlockingIOError, InterruptedError):
                            pass
                        ready, _, _ = select.select([listener], [], [], 2.0)
                        if not ready:
                            raise TimeoutError("timed out waiting for socketpair accept")
                        accepted, _ = listener.accept()
                        _, writable, _ = select.select([], [connector], [], 2.0)
                        if not writable:
                            accepted.close()
                            raise TimeoutError("timed out waiting for socketpair connect")
                        connector.setblocking(True)
                        return accepted, connector
                    except Exception:
                        if connector is not None:
                            connector.close()
                        raise
                    finally:
                        listener.close()

                socket.socketpair = _bounded_socketpair

            policy = os.environ.get("PR_CG_EVENT_LOOP_POLICY")
            if policy == "selector" and sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

            from fastapi import FastAPI
            from fastapi.testclient import TestClient

            app = FastAPI()

            @app.get("/ping")
            def ping():
                return {"ok": True}

            print("policy", type(asyncio.get_event_loop_policy()).__name__, flush=True)
            mode = os.environ.get("PR_CG_TESTCLIENT_MODE", "context")
            if mode == "no_context":
                client = TestClient(app)
                for index in range(25):
                    response = client.get("/ping")
                    assert response.status_code == 200
                    assert response.json() == {"ok": True}
                    if index in {0, 24}:
                        print("request", index, response.json(), flush=True)
            else:
                with TestClient(app) as client:
                    for index in range(25):
                        response = client.get("/ping")
                        assert response.status_code == 200
                        assert response.json() == {"ok": True}
                        if index in {0, 24}:
                            print("request", index, response.json(), flush=True)
            """
        ).lstrip(),
        encoding="utf-8",
    )

    inside = ARTIFACT_DIR / "test_minimal_testclient_pytest.py"
    inside.write_text(
        textwrap.dedent(
            """
            import asyncio
            import faulthandler
            import os
            import select
            import socket
            import sys

            faulthandler.dump_traceback_later(10, repeat=True)
            if os.environ.get("PR_CG_SOCKETPAIR_PATCH") == "1" and sys.platform == "win32":
                def _bounded_socketpair(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0):
                    if family not in (socket.AF_INET, socket.AF_INET6):
                        raise ValueError("Only AF_INET and AF_INET6 socket address families are supported")
                    if type != socket.SOCK_STREAM:
                        raise ValueError("Only SOCK_STREAM socket type is supported")
                    if proto != 0:
                        raise ValueError("Only protocol zero is supported")
                    host = "127.0.0.1" if family == socket.AF_INET else "::1"
                    listener = socket.socket(family, type, proto)
                    connector = None
                    try:
                        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        listener.bind((host, 0))
                        listener.listen(1)
                        addr, port = listener.getsockname()[:2]
                        connector = socket.socket(family, type, proto)
                        connector.setblocking(False)
                        try:
                            connector.connect((addr, port))
                        except (BlockingIOError, InterruptedError):
                            pass
                        ready, _, _ = select.select([listener], [], [], 2.0)
                        if not ready:
                            raise TimeoutError("timed out waiting for socketpair accept")
                        accepted, _ = listener.accept()
                        _, writable, _ = select.select([], [connector], [], 2.0)
                        if not writable:
                            accepted.close()
                            raise TimeoutError("timed out waiting for socketpair connect")
                        connector.setblocking(True)
                        return accepted, connector
                    except Exception:
                        if connector is not None:
                            connector.close()
                        raise
                    finally:
                        listener.close()

                socket.socketpair = _bounded_socketpair

            policy = os.environ.get("PR_CG_EVENT_LOOP_POLICY")
            if policy == "selector" and sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

            from fastapi import FastAPI
            from fastapi.testclient import TestClient

            def test_minimal_testclient_request():
                app = FastAPI()

                @app.get("/ping")
                def ping():
                    return {"ok": True}

                client = TestClient(app)
                response = client.get("/ping")
                assert response.status_code == 200
                assert response.json() == {"ok": True}

            def test_repeated_testclient_construction():
                app = FastAPI()

                @app.get("/ping")
                def ping():
                    return {"ok": True}

                for _ in range(25):
                    with TestClient(app) as client:
                        response = client.get("/ping")
                    assert response.status_code == 200
            """
        ).lstrip(),
        encoding="utf-8",
    )
    return outside, inside


def main() -> int:
    outside, inside = _write_probe_files()
    py = sys.executable
    pytest = [
        py,
        "-X",
        "faulthandler",
        "-m",
        "pytest",
        "-o",
        "addopts=",
        "-o",
        "faulthandler_timeout=20",
        "-vv",
        "-s",
        "--tb=short",
        "--basetemp=development/tmp/pr_cg_pytest",
    ]
    tests = [
        ("minimal_outside_no_context_default", [py, "-X", "faulthandler", str(outside)], 20, None),
        ("minimal_outside_context_default", [py, "-X", "faulthandler", str(outside)], 20, None),
        ("minimal_inside_default", pytest + [str(inside)], 30, None),
        ("minimal_outside_no_context_selector", [py, "-X", "faulthandler", str(outside)], 20, "selector"),
        ("minimal_outside_context_selector", [py, "-X", "faulthandler", str(outside)], 20, "selector"),
        ("minimal_inside_selector", pytest + [str(inside)], 30, "selector"),
        ("minimal_outside_no_context_patched", [py, "-X", "faulthandler", str(outside)], 20, "socketpair_patch"),
        ("minimal_outside_context_patched", [py, "-X", "faulthandler", str(outside)], 20, "socketpair_patch"),
        ("minimal_inside_patched", pytest + [str(inside)], 30, "socketpair_patch"),
        (
            "turn_pipeline_shared_stalled_default",
            pytest + ["tests/test_turn_pipeline_shared.py::test_action_and_chat_social_use_equivalent_shared_turn_logic"],
            45,
            None,
        ),
        (
            "scene_activation_stalled_default",
            pytest + ["tests/test_activate_scene_validation_and_get_persistence.py::test_post_scene_activate_clears_interaction_context"],
            45,
            None,
        ),
        (
            "social_relevance_http_default",
            pytest + ["tests/test_social_question_relevance_answer_selection.py::test_general_http_ask_a_not_b"],
            45,
            None,
        ),
        (
            "turn_pipeline_shared_stalled_selector",
            pytest + ["tests/test_turn_pipeline_shared.py::test_action_and_chat_social_use_equivalent_shared_turn_logic"],
            45,
            "selector",
        ),
        (
            "scene_activation_stalled_selector",
            pytest + ["tests/test_activate_scene_validation_and_get_persistence.py::test_post_scene_activate_clears_interaction_context"],
            45,
            "selector",
        ),
        (
            "mixed_order_default",
            pytest
            + [
                "tests/test_turn_pipeline_shared.py::test_action_and_chat_social_use_equivalent_shared_turn_logic",
                "tests/test_activate_scene_validation_and_get_persistence.py::test_post_scene_activate_clears_interaction_context",
                "tests/test_social_question_relevance_answer_selection.py::test_general_http_ask_a_not_b",
                "tests/test_explicit_world_action_social_lock_override.py::test_http_inspect_while_bound_is_not_social_probe",
            ],
            90,
            None,
        ),
    ]
    results = []
    for name, args, timeout, policy in tests:
        print(f"RUN {name} policy={policy or 'default'} timeout={timeout}", flush=True)
        if "no_context" in name:
            os.environ["PR_CG_TESTCLIENT_MODE"] = "no_context"
        else:
            os.environ.pop("PR_CG_TESTCLIENT_MODE", None)
        if policy == "socketpair_patch":
            os.environ["PR_CG_SOCKETPAIR_PATCH"] = "1"
            results.append(_run(name, args, timeout, None))
            os.environ.pop("PR_CG_SOCKETPAIR_PATCH", None)
        else:
            results.append(_run(name, args, timeout, policy))
    payload = {
        "host": platform.platform(),
        "python": sys.version,
        "executable": sys.executable,
        "results": results,
    }
    (ARTIFACT_DIR / "PR-CG_reliability_matrix.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 1 if any(item["timed_out"] for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())

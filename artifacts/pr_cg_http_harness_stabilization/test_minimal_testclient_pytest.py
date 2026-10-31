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

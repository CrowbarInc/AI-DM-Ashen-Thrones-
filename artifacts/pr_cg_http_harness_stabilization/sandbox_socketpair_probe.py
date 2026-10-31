from __future__ import annotations

import faulthandler
import socket


faulthandler.dump_traceback_later(5)
print("start", flush=True)
left, right = socket.socketpair()
try:
    print("ok", left.getsockname(), right.getpeername(), flush=True)
finally:
    left.close()
    right.close()

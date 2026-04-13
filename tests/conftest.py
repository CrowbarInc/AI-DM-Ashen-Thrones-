"""Pytest defaults: avoid real OpenAI calls on every ``TestClient(app)`` lifespan startup."""

from __future__ import annotations

import os

# Default on in CI / local pytest so importing ``game.api`` + TestClient does not hit the network.
os.environ.setdefault("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "1")

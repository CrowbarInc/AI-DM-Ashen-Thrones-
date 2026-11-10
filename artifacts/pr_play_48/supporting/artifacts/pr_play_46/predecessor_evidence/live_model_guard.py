"""Fail closed when a deterministic test reaches a live model client.

``call_gpt`` catches ``Exception`` and turns it into a fallback reply. A normal
assertion raised inside that ``try`` would be swallowed, and the OpenAI client
can then sit on a long HTTP timeout. ``LiveModelCallForbidden`` is a
``BaseException`` so that path cannot hide or wait.
"""
from __future__ import annotations

import traceback


_PRODUCTION_CALL_GPT = None


def production_call_gpt():
    """Real ``call_gpt`` captured before the guard replaces it.

    Deterministic chat tests restore this and stub only the OpenAI transport.
    """
    if _PRODUCTION_CALL_GPT is None:
        raise RuntimeError("production call_gpt was not captured")
    return _PRODUCTION_CALL_GPT


class LiveModelCallForbidden(BaseException):
    """A deterministic test tried to construct or call a live model client."""

    def __init__(self, where: str) -> None:
        stack = "".join(traceback.format_stack(limit=25))
        super().__init__(
            "Unexpected live model/API client use during a deterministic test.\n"
            f"site: {where}\n"
            f"{stack}"
        )


def _blocked_client(where: str):
    class _Blocked:
        def __init__(self, *args, **kwargs) -> None:
            raise LiveModelCallForbidden(where)

        def __getattr__(self, name: str):
            raise LiveModelCallForbidden(f"{where}.{name}")

    return _Blocked


def install_live_model_guard(monkeypatch) -> None:
    """Patch client constructors and the known generation entry points.

    Tests that install their own ``call_gpt`` stub replace the generation
    wrapper. The OpenAI constructor patch stays in place, so a missed stub
    still fails before any network wait.
    """
    global _PRODUCTION_CALL_GPT
    import game.gm as gm
    import openai

    if _PRODUCTION_CALL_GPT is None:
        _PRODUCTION_CALL_GPT = gm.call_gpt

    monkeypatch.setattr(openai, "OpenAI", _blocked_client("openai.OpenAI"), raising=False)
    if hasattr(openai, "AsyncOpenAI"):
        monkeypatch.setattr(
            openai,
            "AsyncOpenAI",
            _blocked_client("openai.AsyncOpenAI"),
            raising=False,
        )

    def _blocked_call(*_args, **_kwargs):
        raise LiveModelCallForbidden("game.gm.call_gpt")

    def _blocked_interpretation(*_args, **_kwargs):
        raise LiveModelCallForbidden("game.semantic_interpreter._invoke_interpretation_model")

    def _blocked_expression(*_args, **_kwargs):
        raise LiveModelCallForbidden("game.expressive_dialogue.request_expression")

    def _blocked_preflight_client(api_key: str):
        raise LiveModelCallForbidden("game.api_upstream_preflight._default_openai_client_factory")

    monkeypatch.setattr("game.gm.call_gpt", _blocked_call)
    monkeypatch.setattr("game.api.call_gpt", _blocked_call)
    monkeypatch.setattr(
        "game.semantic_interpreter._invoke_interpretation_model",
        _blocked_interpretation,
    )
    monkeypatch.setattr("game.expressive_dialogue.request_expression", _blocked_expression)
    monkeypatch.setattr(
        "game.api_upstream_preflight._default_openai_client_factory",
        _blocked_preflight_client,
    )

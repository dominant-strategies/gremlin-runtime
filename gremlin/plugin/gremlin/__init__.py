"""Hermes plugin `gremlin`: enforces gremlin policy on tool calls and logs model usage.

Installed by the egg into $HERMES_HOME/plugins/gremlin/ and enabled in config.yaml (plugins.enabled: [gremlin]).
These guards are defence in depth: the real boundary is that Hermes runs as an OS user that cannot read the seed.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from .policy import Session, decide


def _session(session_id: str = "", platform: str = "") -> Session:
    try:
        from gateway.session_context import get_session_env

        is_cron = get_session_env("HERMES_CRON_SESSION") == "1"
        platform = platform or get_session_env("HERMES_SESSION_PLATFORM")
    except Exception:  # outside the gateway (CLI): treat as not cron
        is_cron = False
    return Session(session_id=session_id or "", is_cron=is_cron, platform=platform or "")


def _pre_tool_call(tool_name: str = "", args: dict | None = None, session_id: str = "", **_kwargs):
    reason = decide(tool_name, args, _session(session_id))
    if reason:
        return {"action": "block", "message": reason}
    return None


def _usage_log() -> Path:
    home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    d = home / "plugin-data" / "gremlin"
    d.mkdir(parents=True, exist_ok=True)
    return d / "usage.jsonl"


def _post_api_request(model: str = "", provider: str = "", usage=None, session_id: str = "", platform: str = "", finish_reason: str = "", **_kwargs):
    try:
        u = usage if isinstance(usage, dict) else getattr(usage, "__dict__", None) or str(usage)
        line = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "model": model, "provider": provider, "usage": u,
                "session": session_id, "platform": platform, "finish": finish_reason}
        with _usage_log().open("a") as f:
            f.write(json.dumps(line, default=str) + "\n")
    except Exception:
        pass  # observability only; the inference gateway's ledger is the authority on cost


def register(ctx):
    ctx.register_hook("pre_tool_call", _pre_tool_call)
    ctx.register_hook("post_api_request", _post_api_request)

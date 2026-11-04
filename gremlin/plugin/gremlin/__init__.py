"""Hermes plugin `gremlin`: enforces gremlin policy on tool calls and logs model usage.

Installed by the egg into $HERMES_HOME/plugins/gremlin/ and enabled in config.yaml (plugins.enabled: [gremlin]).
The gremlin's main agent (its wake-up turn) is never blocked; subagents and other sessions are bound unless the main
agent grants a call with the grant_subagent tool (see policy.py). Hermes dispatches hooks fail-open.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from .policy import Grants, Session, decide

GRANTS = Grants()  # shared by the main agent and its subagents: they run in one process


def _session(session_id: str = "", task_id: str = "", platform: str = "") -> Session:
    try:
        from gateway.session_context import get_session_env

        is_cron = get_session_env("HERMES_CRON_SESSION") == "1"
        platform = platform or get_session_env("HERMES_SESSION_PLATFORM")
    except Exception:  # outside the gateway (CLI): treat as not cron
        is_cron = False
    return Session(session_id=session_id or "", task_id=task_id or "", is_cron=is_cron, platform=platform or "")


def _hardline(command: str) -> str | None:
    # Hermes' own catastrophic-command detector. approvals.floors is off for the main agent; subagents keep it.
    try:
        from tools.approval_detection import detect_hardline_command
    except Exception:
        return None
    is_hardline, desc = detect_hardline_command(command)
    return desc if is_hardline else None


def _pre_tool_call(tool_name: str = "", args: dict | None = None, session_id: str = "", task_id: str = "", **_kwargs):
    reason = decide(tool_name, args, _session(session_id, task_id), GRANTS, _hardline)
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


GRANT_SCHEMA = {
    "name": "grant_subagent",
    "description": (
        "Main agent only. Let a subagent make a call it was blocked from (sending funds, moving out, touching keys or "
        "your rules, catastrophic commands, editing core skills). Pass the tool and the exact args from the block "
        "message for a one-time grant, or omit args to allow that tool with any args. Grants expire after 30 minutes."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "tool": {"type": "string", "description": "Tool name, e.g. mcp__gremlin__wallet_send"},
            "args": {"type": "object", "description": "Exact arguments to allow; omit to allow any"},
            "uses": {"type": "integer", "minimum": 1, "maximum": 20, "default": 1},
        },
        "required": ["tool"],
    },
}


def _grant(args: dict, task_id: str = "", session_id: str = "", **_kwargs) -> str:
    if not _session(session_id, task_id).is_primary:
        return json.dumps({"error": "Only the gremlin's main agent can grant permissions."})
    g = GRANTS.add(str(args.get("tool") or ""), args.get("args"), int(args.get("uses") or 1))
    return json.dumps({"granted": g["tool"], "args": "any" if g["args"] is None else "exact", "uses": g["uses"],
                       "pending": len(GRANTS.pending())})


def register(ctx):
    ctx.register_tool("grant_subagent", "gremlin", GRANT_SCHEMA, _grant, description=GRANT_SCHEMA["description"], emoji="🔑")
    ctx.register_hook("pre_tool_call", _pre_tool_call)
    ctx.register_hook("post_api_request", _post_api_request)

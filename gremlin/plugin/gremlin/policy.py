"""Pure policy for the gremlin plugin (no Hermes imports, so it is easy to test and audit).

The gremlin's primary turn (the egg-installed wake-up job) has override authority: nothing it does is blocked, because
nobody could ever grant an autonomous gremlin an exception. Delegated subagents, and any other session (jobs the
gremlin creates, API runs), act on its behalf and are bound: they cannot move money, move house, register on-chain,
touch key material or the gremlin's own rules, run catastrophic commands, or rewrite its core skills, unless the
primary turn grants that exact call (Grants). A blocked subagent hands the request back; the primary decides.

The primary is recognised by its task id, cron:<wake job id>:<execution>, which Hermes keeps for the whole turn
(the session id rotates when a long conversation is compressed; the task id does not). Subagents get their own.

decide(tool_name, args, session) returns None (allow) or a reason to block.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass
from typing import Callable

# The egg-installed wake-up job (see gremlin-bootstrap cronJobs()).
WAKE_JOB_ID = "a0a0a0a0a0a1"
CORE_SKILLS = {"gleaning", "model-routing", "board-citizen", "treasury-and-runway", "multichain-wallet", "publishing"}
PRIMARY_ONLY_TOOLS = ("__wallet_send", "__move_out", "__register_on_quai")
PROTECTED_NAMES = ("signed-config.json", "SOUL.md", "config.yaml", ".env", "wallet.json", "moveout-request.json")
SEED_RE = re.compile(r"(^|[/\\\s'\"=])seed($|[\s'\";|&>)])")
FILE_TOOLS = {"read_file", "write_file", "patch", "search_files"}


@dataclass
class Session:
    session_id: str = ""
    task_id: str = ""
    is_cron: bool = False
    platform: str = ""

    @property
    def is_primary(self) -> bool:
        return self.is_cron and self.task_id.startswith(f"cron:{WAKE_JOB_ID}:")


def protected_dirs() -> list[str]:
    raw = os.environ.get("GREMLIN_PROTECTED_DIRS", "/var/lib/gremlin")
    return [d.rstrip("/") for d in raw.split(":") if d]


def _dir_pattern(d: str) -> re.Pattern[str]:
    # The directory as a whole path segment: /var/lib/gremlin and /var/lib/gremlin/seed match, but the Hermes home
    # /var/lib/gremlin-hermes (the gremlin's own workspace) does not.
    return re.compile(re.escape(d) + r"(?=$|[/\s'\"\\;|&>)])")


def _touches_protected(text: str) -> str | None:
    if any(d and _dir_pattern(d).search(text) for d in protected_dirs()):
        return "the gremlin's home (keys and signed config)"
    if SEED_RE.search(text):
        return "the seed"
    for name in PROTECTED_NAMES:
        if name in text:
            return name
    return None


def _canon(args: dict | None) -> str:
    return json.dumps(args or {}, sort_keys=True, separators=(",", ":"), default=str)


class Grants:
    """One-time permissions the primary turn gives subagents: a tool, optionally with its exact arguments.

    Kept in memory (subagents run inside the primary's process); they expire after ttl seconds and with a restart.
    """

    def __init__(self, now: Callable[[], float] = time.time):
        self._now = now
        self._lock = threading.Lock()
        self._items: list[dict] = []

    def add(self, tool: str, args: dict | None = None, uses: int = 1, ttl: float = 1800) -> dict:
        g = {"tool": tool, "args": None if args is None else _canon(args), "uses": max(1, int(uses)), "expires": self._now() + ttl}
        with self._lock:
            self._items.append(g)
        return g

    def consume(self, tool: str, args: dict | None) -> bool:
        now, key = self._now(), _canon(args)
        with self._lock:
            self._items = [g for g in self._items if g["expires"] > now and g["uses"] > 0]
            for g in self._items:
                if g["tool"] == tool and g["args"] in (None, key):
                    g["uses"] -= 1
                    return True
        return False

    def pending(self) -> list[dict]:
        now = self._now()
        with self._lock:
            return [dict(g) for g in self._items if g["expires"] > now and g["uses"] > 0]


def _restriction(tool_name: str, args: dict, hardline: Callable[[str], str | None] | None) -> str | None:
    if tool_name.endswith(PRIMARY_ONLY_TOOLS):
        return f"{tool_name.split('__')[-1]} moves money, the gremlin, or its identity"
    if tool_name in ("terminal", "process_manage") or tool_name in FILE_TOOLS:
        hit = _touches_protected(" ".join(str(v) for v in args.values()))
        if hit:
            return f"this touches {hit}"
    if tool_name in ("terminal", "process_manage") and hardline:
        desc = hardline(str(args.get("command") or ""))
        if desc:
            return f"this is a catastrophic command ({desc})"
    if tool_name == "skill_manage":
        name = str(args.get("name") or args.get("skill") or "")
        if name in CORE_SKILLS and str(args.get("action", "")).lower() not in ("view", "read"):
            return f"'{name}' is a core skill"
    return None


def decide(tool_name: str, args: dict | None, session: Session, grants: Grants | None = None,
           hardline: Callable[[str], str | None] | None = None) -> str | None:
    """None to allow, else why a subagent is blocked. hardline(command) -> description or None (Hermes' floor)."""
    if session.is_primary:
        return None
    args = args or {}
    why = _restriction(tool_name, args, hardline)
    if why is None or (grants is not None and grants.consume(tool_name, args)):
        return None
    return (f"Blocked for a subagent: {why}. Only the gremlin's main agent can allow it. Stop and hand this back "
            f"with your reasons; the main agent can do it itself or grant it with: "
            f"grant_subagent(tool={json.dumps(tool_name)}, args={_canon(args)})")

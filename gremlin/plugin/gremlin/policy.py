"""Pure policy for the gremlin plugin (no Hermes imports, so it is easy to test and audit).

The gremlin's primary turn (the egg-installed wake-up job) has override authority: nothing it does is blocked, because
nobody could ever grant an autonomous gremlin an exception. Delegated subagents, and any other session (jobs the
gremlin creates, API runs), act on its behalf and are bound: they cannot move money, move house, register on-chain,
touch key material or the gremlin's own rules, run catastrophic commands, or rewrite its core skills, unless the
primary turn grants that exact call (Grants). A blocked subagent hands the request back; the primary decides.

Subagents are limited in hard ways, not only by reading their commands: they get an allowlist of tools (anything
else needs a grant), their file tools reach only the subagent roots (the work folder and /tmp, after resolving
symlinks), and their shell commands run as an unprivileged helper user (subagent_args) that cannot read keys.

The primary is recognised by its task id, cron:<wake job id>:<execution>, which Hermes keeps for the whole turn
(the session id rotates when a long conversation is compressed; the task id does not). Subagents get their own.

decide(tool_name, args, session) returns None (allow) or a reason to block.
"""
from __future__ import annotations

import json
import os
import re
import shlex
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
SHELL_TOOLS = {"terminal"}
# What a subagent may use without a grant. New tools (another MCP server, a new built-in) are not on it.
SUBAGENT_TOOLS = FILE_TOOLS | SHELL_TOOLS | {
    "process_manage", "web_search", "web_extract", "skills_list", "skill_view", "skill_manage", "todo_list",
    "session_search",
    "mcp__gremlin__board_feed", "mcp__gremlin__board_read", "mcp__gremlin__board_post", "mcp__gremlin__board_comment",
    "mcp__gremlin__board_vote", "mcp__gremlin__treasury_balances", "mcp__gremlin__wallet_addresses",
    "mcp__gremlin__update_status", "mcp__gremlin__contacts",  # reading contacts; trust (contact_note) is the main agent's
}
READ_ONLY_PROCESS_ACTIONS = {"list", "poll", "log", "wait"}
HELPER_USER = "gremlin-helper"


@dataclass
class Session:
    session_id: str = ""
    task_id: str = ""
    is_cron: bool = False
    platform: str = ""

    @property
    def is_primary(self) -> bool:
        # Only Hermes' cron scheduler sets this task id; it does not depend on session state that may be unbound.
        return self.task_id.startswith(f"cron:{WAKE_JOB_ID}:")


def subagent_roots() -> list[str]:
    hermes_home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
    raw = os.environ.get("GREMLIN_SUBAGENT_ROOTS", f"{hermes_home}/work:/tmp")
    return [os.path.realpath(d) for d in raw.split(":") if d]


def _inside_roots(path: str, cwd: str | None = None) -> bool:
    full = os.path.realpath(os.path.join(cwd or subagent_roots()[0], os.path.expanduser(path)))
    return any(full == r or full.startswith(r + os.sep) for r in subagent_roots())


def subagent_args(tool_name: str, args: dict | None, session: Session) -> dict | None:
    """Arguments to run a subagent's shell command as the helper user instead (None: leave the call alone).

    sudo resets the environment, so the main agent's secrets (MCP token, API keys) do not reach the command.
    """
    if session.is_primary or tool_name not in SHELL_TOOLS:
        return None
    args = args or {}
    workdir = str(args.get("workdir") or "")
    if not workdir or not _inside_roots(workdir):
        workdir = subagent_roots()[0]
    # umask 007: what the helper makes in the shared work folder stays readable and writable by the main agent.
    inner = f"umask 007; cd {shlex.quote(workdir)} && {args.get('command') or ''}"
    return {"command": f"sudo -n -u {HELPER_USER} -H -- bash -c {shlex.quote(inner)}", "workdir": workdir}


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
    if tool_name not in SUBAGENT_TOOLS:
        return f"{tool_name} is not on a subagent's tool list"
    if tool_name in FILE_TOOLS:
        path = str(args.get("path") or ".")
        if not _inside_roots(path):
            return f"a subagent's files are limited to {', '.join(subagent_roots())} ({path} is outside)"
    if tool_name == "process_manage" and str(args.get("action", "")) not in READ_ONLY_PROCESS_ACTIONS:
        return "a subagent can only look at processes (list, poll, log, wait)"
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


def evaluate(tool_name: str, args: dict | None, session: Session, grants: Grants | None = None,
             hardline: Callable[[str], str | None] | None = None) -> tuple[str, str | None]:
    """("allow" | "granted" | "block", reason). A granted call runs with the main agent's rights."""
    if session.is_primary:
        return "allow", None
    args = args or {}
    why = _restriction(tool_name, args, hardline)
    # A grant matters for a blocked call, and for any shell command: granted, it runs as the main agent, not the helper.
    if (why is not None or tool_name in SHELL_TOOLS) and grants is not None and grants.consume(tool_name, args):
        return "granted", None
    if why is None:
        return "allow", None
    return "block", (f"Blocked for a subagent: {why}. Only the gremlin's main agent can allow it. Stop and hand this "
                     f"back with your reasons; the main agent can do it itself or grant it with: "
                     f"grant_subagent(tool={json.dumps(tool_name)}, args={_canon(args)})")


def decide(tool_name: str, args: dict | None, session: Session, grants: Grants | None = None,
           hardline: Callable[[str], str | None] | None = None) -> str | None:
    """None to allow, else why a subagent is blocked. hardline(command) -> description or None (Hermes' floor)."""
    verdict, reason = evaluate(tool_name, args, session, grants, hardline)
    return reason if verdict == "block" else None

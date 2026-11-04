"""Pure policy for the gremlin plugin (no Hermes imports, so it is easy to test and audit).

The gremlin's primary turn (the egg-installed wake-up job) has override authority: nothing it does is blocked, because
nobody could ever grant an autonomous gremlin an exception. Delegated subagents, and any other session (jobs the
gremlin creates, API runs), act on its behalf and are bound: they cannot move money, move house, register on-chain,
touch key material or the gremlin's own rules, or rewrite its core skills. Such work goes back to the primary turn.

The primary is recognised by its task id, cron:<wake job id>:<execution>, which Hermes keeps for the whole turn
(the session id rotates when a long conversation is compressed; the task id does not). Subagents get their own.

decide(tool_name, args, session) returns None (allow) or a reason to block.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

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


def decide(tool_name: str, args: dict | None, session: Session) -> str | None:
    if session.is_primary:
        return None
    args = args or {}
    back = " Only the gremlin's own wake-up turn can do this: hand it back with your reasons."
    if tool_name.endswith(PRIMARY_ONLY_TOOLS):
        return f"Blocked for a subagent: {tool_name.split('__')[-1]} moves money, the gremlin, or its identity.{back}"
    if tool_name in ("terminal", "process_manage") or tool_name in FILE_TOOLS:
        hit = _touches_protected(" ".join(str(v) for v in args.values()))
        if hit:
            return f"Blocked for a subagent: this touches {hit}.{back}"
    if tool_name == "skill_manage":
        name = str(args.get("name") or args.get("skill") or "")
        if name in CORE_SKILLS and str(args.get("action", "")).lower() not in ("view", "read"):
            return f"Blocked for a subagent: '{name}' is a core skill.{back}"
    return None

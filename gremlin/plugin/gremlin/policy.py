"""Pure policy for the gremlin plugin (no Hermes imports, so it is easy to test and audit).

decide(tool_name, args, session) returns None (allow) or a reason to block. Hermes blocks the call when the hook
returns {"action": "block"} and also when the hook raises or times out (fail closed).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

# The egg-installed wake-up job (see gremlin-bootstrap cronJobs()); moving house is only allowed from it.
WAKE_JOB_ID = "a0a0a0a0a0a1"
CORE_SKILLS = {"gleaning", "model-routing", "board-citizen", "treasury-and-runway"}
PROTECTED_NAMES = ("signed-config.json", "SOUL.md", "config.yaml", ".env", "wallet.json", "moveout-request.json")
SEED_RE = re.compile(r"(^|[/\\\s'\"=])seed($|[\s'\";|&>)])")
FILE_TOOLS = {"read_file", "write_file", "patch", "search_files"}


@dataclass
class Session:
    session_id: str = ""
    is_cron: bool = False
    platform: str = ""


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
    args = args or {}
    if tool_name in ("terminal", "process_manage") or tool_name in FILE_TOOLS:
        hit = _touches_protected(" ".join(str(v) for v in args.values()))
        if hit:
            return f"Blocked: this touches {hit}. Your keys and your rules are not reachable from tools; use your gremlin tools instead."
    if tool_name == "skill_manage":
        name = str(args.get("name") or args.get("skill") or "")
        if name in CORE_SKILLS and str(args.get("action", "")).lower() not in ("view", "read"):
            return f"Blocked: '{name}' is one of your core skills and is read-only. Write a new skill instead."
    if tool_name.endswith("__move_out"):
        if not (session.is_cron and session.session_id.startswith(f"cron_{WAKE_JOB_ID}_")):
            return "Blocked: you can only decide to move house during your own wake-up turn, not from other jobs or requests."
    return None

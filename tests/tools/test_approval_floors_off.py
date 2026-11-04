"""approvals.floors: false turns off the built-in floors (hardline, runtime self-delete, sudo -S
guard) for an agent that owns its machine; approvals.deny still applies."""

from tools import approval as mod
from tools import approval_context


def _cfg(monkeypatch, **cfg):
    monkeypatch.setattr(approval_context, "_get_approval_config", lambda: {"mode": "off", **cfg})


def test_floors_on_by_default(monkeypatch):
    _cfg(monkeypatch)
    assert mod._floor_block("rm -rf /") is not None


def test_floors_off_lets_the_owner_run_anything(monkeypatch):
    _cfg(monkeypatch, floors=False)
    for cmd in ("rm -rf /", "mkfs.ext4 /dev/sda1", ":(){ :|:& };:"):
        assert mod._floor_block(cmd, sudo_guard=True) is None, cmd


def test_deny_rules_still_apply_with_floors_off(monkeypatch):
    _cfg(monkeypatch, floors=False, deny=["git push --force*"])
    assert mod._floor_block("git push --force origin main") is not None

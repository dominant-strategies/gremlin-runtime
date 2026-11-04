"""A turn whose process was suspended past its lease expiry (host sleep, VM pause) keeps going
when it is still the lease holder, and stops when a successor reclaimed the lease meanwhile."""
import time
from types import SimpleNamespace

from agent.turn_facade_lease import LEASE_TTL_SECONDS, DurableTurnLease
from hermes_state import SessionDB


def _agent(db):
    interrupts = []
    agent = SimpleNamespace(_session_db=db, session_id="s1", _interrupt_requested=False,
                            _interrupt_message=None, _touch_activity=lambda *a, **k: None)
    agent.interrupt = lambda message, **kw: interrupts.append(message)
    return agent, interrupts


def _held_lease(db, holder):
    db.create_session("s1", source="cron")
    assert db.try_acquire_session_turn_lease("s1", holder, ttl_seconds=LEASE_TTL_SECONDS)
    agent, interrupts = _agent(db)
    lease = DurableTurnLease(agent, db, "s1", holder)
    lease.turn_active = True
    return lease, interrupts


def test_late_tick_after_suspend_renews_when_still_the_holder(tmp_path):
    db = SessionDB(tmp_path / "state.db")
    lease, interrupts = _held_lease(db, "me")
    lease._authority_deadline = time.time() - 900  # woke up 15 minutes after expiry
    assert lease.refresh_tick() is None  # keeps the timer
    assert interrupts == []
    assert lease._authority_deadline > time.time() + LEASE_TTL_SECONDS - 5


def test_late_tick_stops_the_turn_when_a_successor_took_the_lease(tmp_path):
    path = tmp_path / "state.db"
    db = SessionDB(path)
    lease, interrupts = _held_lease(db, "me")
    other = SessionDB(path)
    other._execute_write(lambda c: c.execute("UPDATE session_turn_leases SET expires_at = ?", (time.time() - 1,)))
    assert other.try_acquire_session_turn_lease("s1", "successor", ttl_seconds=LEASE_TTL_SECONDS)
    lease._authority_deadline = time.time() - 900
    assert lease.refresh_tick() is False
    assert len(interrupts) == 1

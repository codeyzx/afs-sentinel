from __future__ import annotations

import sys
import types
from datetime import datetime

import pytest

from afs import __main__ as cli
from afs import db, runner
from afs.db import session_scope
from afs.domain import RunStatus, RunTrigger
from afs.models import AuditRun, Emiten


@pytest.fixture
def fake_run(engine, monkeypatch):
    """Patch run_audit to record the trigger and create an AuditRun with the chosen status."""
    calls: list[RunTrigger] = []
    state = {"status": RunStatus.SUCCESS, "saturday": True, "busy": False}

    def run_audit(trigger):
        if state["busy"]:
            raise runner.RunInProgressError()
        calls.append(trigger)
        with session_scope() as s:
            r = AuditRun(trigger=trigger.value, status=state["status"].value)
            s.add(r)
            s.flush()
            return r.id

    monkeypatch.setattr(runner, "run_audit", run_audit)
    monkeypatch.setattr(runner, "should_run_scheduled", lambda now: state["saturday"])
    monkeypatch.setattr(db, "init_db", lambda: None)
    state["calls"] = calls
    return state


def test_run_manual(fake_run, capsys):
    assert cli.main(["run"]) == 0
    assert fake_run["calls"] == [RunTrigger.MANUAL]
    assert "Audit Run #1: SUCCESS" in capsys.readouterr().out


def test_run_scheduled_on_saturday(fake_run, capsys):
    assert cli.main(["run", "--scheduled"]) == 0
    assert fake_run["calls"] == [RunTrigger.SCHEDULER]


def test_run_scheduled_not_saturday_exits_quietly(fake_run, capsys):
    fake_run["saturday"] = False
    assert cli.main(["run", "--scheduled"]) == 0
    assert fake_run["calls"] == []
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1 and "dilewati" in out[0]
    with session_scope() as s:
        assert s.query(AuditRun).count() == 0


def test_run_failed_exit_code(fake_run, capsys):
    fake_run["status"] = RunStatus.FAILED
    assert cli.main(["run"]) == 1
    assert "FAILED" in capsys.readouterr().out


def test_run_locked_exit_code(fake_run, capsys):
    fake_run["busy"] = True
    assert cli.main(["run"]) == 1
    assert "Audit Run sedang berjalan" in capsys.readouterr().out


def test_run_scheduled_uses_current_time(engine, monkeypatch):
    seen: list[datetime] = []
    monkeypatch.setattr(runner, "should_run_scheduled", lambda now: seen.append(now) or False)
    assert cli.main(["run", "--scheduled"]) == 0
    assert len(seen) == 1 and seen[0].tzinfo is not None


def test_initdb(monkeypatch, capsys):
    called = []
    monkeypatch.setattr(db, "init_db", lambda: called.append(True))
    assert cli.main(["initdb"]) == 0
    assert called == [True]


def test_backtest_passes_remaining_args(monkeypatch):
    received: list[list[str]] = []
    fake = types.ModuleType("afs.backtest")
    fake.main = lambda argv: received.append(argv) or 3
    monkeypatch.setitem(sys.modules, "afs.backtest", fake)
    import afs

    monkeypatch.setattr(afs, "backtest", fake, raising=False)
    assert cli.main(["backtest", "--case", "WSKT", "--case", "SRIL", "--dry-run"]) == 3
    assert received == [["--case", "WSKT", "--case", "SRIL", "--dry-run"]]


def test_backtest_missing_module(monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "afs.backtest", None)  # import -> ImportError
    assert cli.main(["backtest"]) == 1
    assert "backtest" in capsys.readouterr().err


def test_sync_universe_prints_symbols(engine, monkeypatch, capsys):
    from afs.sectors import repository

    class Repo:
        def __init__(self, session, client, **_):
            self.session = session

        def sync_universe(self):
            self.session.add(Emiten(symbol="ASII.JK", company_name="Astra International", is_excluded=False))
            self.session.add(Emiten(symbol="BBCA.JK", company_name="Bank Central Asia", is_excluded=True))
            self.session.flush()
            return []

    monkeypatch.setattr(repository, "DataRepository", Repo)
    monkeypatch.setattr(db, "init_db", lambda: None)
    assert cli.main(["sync-universe"]) == 0
    out = capsys.readouterr().out
    assert "ASII.JK\tactive\tAstra International" in out
    assert "BBCA.JK\texcluded\tBank Central Asia" in out


def test_unknown_command_errors():
    with pytest.raises(SystemExit):
        cli.main(["nope"])
    with pytest.raises(SystemExit):
        cli.main([])

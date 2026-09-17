from __future__ import annotations

import inspect
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from afs import runner
from afs.db import session_scope
from afs.domain import EvaluationInput, FindingStatus, RuleFinding, RunTrigger
from afs.models import AuditRun, Emiten, EmitenEvaluation, Incident, Lock
from afs.telegram import OPEN_INCIDENT_BUTTON, incident_url
from tests.fixtures.rules_factory import make_input

TODAY = date(2026, 9, 19)
RULES = [
    "SLOAN_ACCRUAL",
    "EARNINGS_CASH_DIVERGENCE",
    "ALTMAN_Z_ADAPTED",
    "BENEISH_ADAPTED",
    "INSIDER_SELLING",
    "EARNINGS_WITHOUT_DIVIDEND",
]


def findings(*red: str) -> list[RuleFinding]:
    return [
        RuleFinding(r, FindingStatus.RED_FLAG if r in red else FindingStatus.PASS, None, {}, {}, f"headline {r}")
        for r in RULES
    ]


LOW = findings()
MODERATE = findings("SLOAN_ACCRUAL")  # 25 -> LOW, raised by the core-rule floor
CRITICAL = findings("SLOAN_ACCRUAL", "EARNINGS_CASH_DIVERGENCE", "ALTMAN_Z_ADAPTED")  # 70


class FakeClient:
    def __init__(self, credits: int = 7) -> None:
        self.credits_used = credits


class World:
    """Scenario shared by the fake repository and the patched rule evaluation."""

    def __init__(self) -> None:
        self.universe: dict[str, tuple[str, bool]] = {}  # symbol -> (company_name, excluded)
        self.results: dict[str, list[RuleFinding] | Exception | None] = {}
        self.sync_error: Exception | None = None
        self.as_of: list[date] = []

    def add(self, symbol: str, result, *, name: str | None = None, excluded: bool = False) -> None:
        self.universe[symbol] = (name or f"PT {symbol}", excluded)
        self.results[symbol] = result


@pytest.fixture
def world(engine, monkeypatch):
    w = World()

    class FakeRepo:
        def __init__(self, session, client, **_) -> None:
            self.session = session

        def sync_universe(self):
            if w.sync_error:
                raise w.sync_error
            active = []
            for symbol, (name, excluded) in w.universe.items():
                e = self.session.get(Emiten, symbol) or Emiten(symbol=symbol)
                e.company_name, e.is_excluded = name, excluded
                self.session.add(e)
                if not excluded:
                    active.append(e)
            self.session.flush()
            return active

        def build_live_input(self, symbol: str, as_of: date) -> EvaluationInput | None:
            w.as_of.append(as_of)
            result = w.results[symbol]
            if isinstance(result, Exception):
                self.session.add(EmitenEvaluation(run_id=0, symbol=symbol, report_date=as_of))  # rolled back
                self.session.flush()
                raise result
            if result is None:
                return None
            inp = make_input()
            return EvaluationInput(symbol=symbol, quarters=inp.quarters, as_of=as_of, filings=[], dividends=[])

    def fake_evaluate(inp: EvaluationInput):
        return w.results[inp.symbol]

    monkeypatch.setattr(runner, "DataRepository", FakeRepo)
    monkeypatch.setattr(runner, "evaluate_all", fake_evaluate)
    return w


class Outbox:
    def __init__(self, fail: bool = False) -> None:
        self.messages: list[tuple[str, tuple[str, str] | None]] = []
        self.fail = fail

    def __call__(self, text: str, button: tuple[str, str] | None = None) -> bool:
        self.messages.append((text, button))
        if self.fail:
            raise RuntimeError("telegram down")
        return True


def run(trigger=RunTrigger.MANUAL, outbox: Outbox | None = None, client: FakeClient | None = None) -> int:
    return runner.run_audit(trigger, client=client or FakeClient(), today=TODAY, send=outbox or Outbox())


def get_run(run_id: int) -> AuditRun:
    with session_scope() as s:
        return s.get(AuditRun, run_id)


def incidents() -> list[Incident]:
    with session_scope() as s:
        return list(s.scalars(select(Incident).order_by(Incident.event_id)))


# ---------------------------------------------------------------- run behaviour


def test_success_run_records_counts_creates_incidents_and_notifies(world):
    world.add("AAAA.JK", CRITICAL, name="Alpha Tbk")
    world.add("BBBB.JK", MODERATE)
    world.add("CCCC.JK", LOW)
    world.add("BBRI.JK", CRITICAL, excluded=True)
    outbox = Outbox()

    run_id = run(RunTrigger.SCHEDULER, outbox, FakeClient(12))

    r = get_run(run_id)
    assert (r.status, r.trigger, r.emiten_scanned, r.emiten_failed, r.incidents_new, r.escalations, r.credits_used) == (
        "SUCCESS", "SCHEDULER", 3, 0, 2, 0, 12
    )
    assert r.finished_at is not None and r.error is None
    assert "WIB]" in r.log_text and "AAAA.JK" in r.log_text
    assert [i.symbol for i in incidents()] == ["AAAA.JK", "BBBB.JK"]
    assert world.as_of == [TODAY] * 3

    with session_scope() as s:
        assert len(s.scalars(select(EmitenEvaluation).where(EmitenEvaluation.run_id == run_id)).all()) == 3

    assert len(outbox.messages) == 3  # 2 incidents + summary
    (alpha, alpha_btn), (_, beta_btn), (summary, summary_btn) = outbox.messages
    assert "AAAA — Alpha Tbk" in alpha and "Kritis" in alpha
    assert alpha_btn == (OPEN_INCIDENT_BUTTON, incident_url("AFS-2025-Q3-0001"))
    assert beta_btn[1].endswith("AFS-2025-Q3-0002")
    assert summary.startswith("✅ Audit Run") and "(Terjadwal)" in summary
    assert "3 emiten dipindai · 2 Incident baru · 0 Escalation · 0 gagal" in summary
    assert "Kredit API terpakai: 12" in summary
    assert summary_btn is None


def test_second_run_escalation_notifies_same_severity_and_downgrade_do_not(world):
    world.add("AAAA.JK", MODERATE)
    world.add("BBBB.JK", MODERATE)
    world.add("CCCC.JK", CRITICAL)
    run()
    with session_scope() as s:
        s.get(Incident, "AFS-2025-Q3-0001").triage_status = "DISMISSED"

    world.results.update({"AAAA.JK": CRITICAL, "BBBB.JK": MODERATE, "CCCC.JK": LOW})
    outbox = Outbox()
    run_id = run(outbox=outbox)

    r = get_run(run_id)
    assert (r.incidents_new, r.escalations) == (0, 1)
    assert len(outbox.messages) == 2
    text, button = outbox.messages[0]
    assert "Escalation: Sedang → Kritis" in text and button[1].endswith("AFS-2025-Q3-0001")
    assert "0 Incident baru · 1 Escalation" in outbox.messages[1][0]
    by_id = {i.event_id: i for i in incidents()}
    assert by_id["AFS-2025-Q3-0001"].triage_status == "UNTRIAGED"
    assert by_id["AFS-2025-Q3-0003"].severity == "LOW"


def test_per_emiten_failure_is_isolated(world):
    world.add("AAAA.JK", RuntimeError("API meledak"))
    world.add("BBBB.JK", None)
    world.add("CCCC.JK", CRITICAL)
    outbox = Outbox()

    run_id = run(outbox=outbox)

    r = get_run(run_id)
    assert (r.status, r.emiten_scanned, r.emiten_failed, r.incidents_new) == ("SUCCESS", 3, 2, 1)
    assert "AAAA.JK: GAGAL" in r.log_text and "API meledak" in r.log_text
    assert "BBBB.JK: GAGAL" in r.log_text
    with session_scope() as s:
        rows = s.scalars(select(EmitenEvaluation)).all()
    assert [e.symbol for e in rows] == ["CCCC.JK"]  # failing Emiten's partial writes rolled back
    assert "1 Incident baru · 0 Escalation · 2 gagal" in outbox.messages[-1][0]


def test_fatal_error_marks_run_failed_and_sends_failure(world):
    world.add("AAAA.JK", CRITICAL)
    world.sync_error = RuntimeError("database hilang")
    outbox = Outbox()

    run_id = run(outbox=outbox)

    r = get_run(run_id)
    assert (r.status, r.error) == ("FAILED", "database hilang")
    assert r.finished_at is not None
    assert "GAGAL" in r.log_text
    [(text, button)] = outbox.messages
    assert text.startswith("❌ Audit Run GAGAL") and "Alasan: database hilang" in text
    assert button is None
    assert not runner.is_run_in_progress()


def test_all_emiten_failing_marks_run_failed(world):
    world.add("AAAA.JK", RuntimeError("x"))
    world.add("BBBB.JK", RuntimeError("y"))
    outbox = Outbox()
    r = get_run(run(outbox=outbox))
    assert (r.status, r.emiten_scanned, r.emiten_failed) == ("FAILED", 2, 2)
    assert outbox.messages[-1][0].startswith("❌")


def test_telegram_failures_never_fail_the_run(world):
    world.add("AAAA.JK", CRITICAL)
    outbox = Outbox(fail=True)
    r = get_run(run(outbox=outbox))
    assert r.status == "SUCCESS"
    assert len(outbox.messages) == 2
    assert "Telegram gagal" in r.log_text


def test_empty_universe_still_sends_summary(world):
    outbox = Outbox()
    r = get_run(run(outbox=outbox))
    assert (r.status, r.emiten_scanned) == ("SUCCESS", 0)
    assert "0 emiten dipindai" in outbox.messages[0][0]


# ---------------------------------------------------------------- lock


def test_lock_busy_raises_and_leaves_no_run(world):
    assert runner.acquire_lock()
    assert runner.is_run_in_progress()
    with pytest.raises(runner.RunInProgressError, match="Audit Run sedang berjalan"):
        run()
    with session_scope() as s:
        assert s.scalars(select(AuditRun)).all() == []
    assert runner.is_run_in_progress()  # the other run's lock is untouched
    runner.release_lock()
    assert not runner.is_run_in_progress()


def test_stale_lock_is_replaced(world):
    old = datetime.now(timezone.utc) - timedelta(hours=2, minutes=1)
    with session_scope() as s:
        s.add(Lock(name="audit_run", acquired_at=old))
    assert not runner.is_run_in_progress()
    r = get_run(run())
    assert r.status == "SUCCESS"
    assert not runner.is_run_in_progress()


def test_fresh_lock_is_not_stale(engine):
    now = datetime(2026, 9, 19, 1, 0, tzinfo=timezone.utc)
    assert runner.acquire_lock(now=now)
    assert not runner.acquire_lock(now=now + timedelta(hours=1, minutes=59))
    assert runner.is_run_in_progress(now=now + timedelta(hours=1))
    assert not runner.is_run_in_progress(now=now + timedelta(hours=2))
    assert runner.acquire_lock(now=now + timedelta(hours=2))
    assert not runner.acquire_lock(now=now + timedelta(hours=3))


def test_lock_released_after_success(world):
    run()
    with session_scope() as s:
        assert s.get(Lock, "audit_run") is None


# ---------------------------------------------------------------- schedule & contracts


@pytest.mark.parametrize(
    "moment,expected",
    [
        (datetime(2026, 9, 19, 1, 0, tzinfo=timezone.utc), True),  # Sat 08:00 WIB
        (datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc), True),  # Sat 03:00 WIB, still Fri in UTC
        (datetime(2026, 9, 19, 18, 0, tzinfo=timezone.utc), False),  # Sun 01:00 WIB
        (datetime(2026, 9, 18, 1, 0, tzinfo=timezone.utc), False),  # Fri
        (datetime(2026, 9, 19, 1, 0), True),  # naive = UTC
    ],
)
def test_should_run_scheduled_only_on_saturday_wib(moment, expected):
    assert runner.should_run_scheduled(moment) is expected


def test_web_app_lazy_import_contract():
    from afs.runner import is_run_in_progress, run_audit

    params = inspect.signature(run_audit).parameters
    assert list(params)[0] == "trigger"
    assert all(p.default is not inspect.Parameter.empty for name, p in params.items() if name != "trigger")
    assert all(p.default is not inspect.Parameter.empty for p in inspect.signature(is_run_in_progress).parameters.values())


def test_real_rules_end_to_end(engine, monkeypatch):
    """No evaluation patching: real rules + scoring over factory data produce an Incident."""

    class Repo:
        def __init__(self, session, client, **_):
            self.session = session

        def sync_universe(self):
            e = Emiten(symbol="WSKT.JK", company_name="Waskita Karya")
            self.session.add(e)
            self.session.flush()
            return [e]

        def build_live_input(self, symbol, as_of):
            # earnings far above operating cash flow -> Sloan RED_FLAG (core floor >= MODERATE)
            inp = make_input({k: {"earnings": 200.0, "operating_cash_flow": -100.0} for k in range(5)})
            return EvaluationInput(symbol=symbol, quarters=inp.quarters, as_of=as_of, filings=[], dividends=[])

    monkeypatch.setattr(runner, "DataRepository", Repo)
    outbox = Outbox()
    r = get_run(run(outbox=outbox))
    assert (r.status, r.incidents_new) == ("SUCCESS", 1)
    [inc] = incidents()
    assert inc.severity in ("MODERATE", "CRITICAL") and len(inc.findings) == 6
    assert "WSKT — Waskita Karya" in outbox.messages[0][0]

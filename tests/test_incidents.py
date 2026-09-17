from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import select

from afs.db import session_scope
from afs.domain import FindingStatus, IncidentEventKind, RuleFinding, ScoreResult, Severity, TriageStatus
from afs.incidents import apply_evaluation, next_event_id
from afs.models import AuditRun, EmitenEvaluation, Incident, IncidentEvent

T = date(2025, 9, 30)


def score(value: float | None, severity: Severity | None, *, low_confidence: bool = False) -> ScoreResult:
    return ScoreResult(
        score=value, severity=severity, low_confidence=low_confidence, evaluated_weight=0 if value is None else 100
    )


LOW = score(10.0, Severity.LOW)
MOD = score(40.0, Severity.MODERATE)
MOD2 = score(45.0, Severity.MODERATE)
CRIT = score(75.0, Severity.CRITICAL)
NONE = score(None, None)

FINDINGS = [
    RuleFinding("SLOAN_ACCRUAL", FindingStatus.RED_FLAG, 0.14, {}, {}, "Sloan tinggi"),
]


@pytest.fixture
def session(engine):
    with session_scope() as s:
        for _ in range(3):
            s.add(AuditRun(trigger="MANUAL", status="RUNNING"))
        s.flush()
        yield s


def apply(session, sc: ScoreResult, *, run_id: int = 1, symbol: str = "EMTK.JK", report_date: date = T):
    return apply_evaluation(
        session, run_id=run_id, symbol=symbol, report_date=report_date, score=sc, findings=list(FINDINGS)
    )


def events(session, event_id: str) -> list[tuple[str, str | None, str | None]]:
    rows = session.scalars(select(IncidentEvent).where(IncidentEvent.event_id == event_id).order_by(IncidentEvent.id))
    return [(e.kind, e.from_value, e.to_value) for e in rows]


def evaluations(session) -> list[EmitenEvaluation]:
    return list(session.scalars(select(EmitenEvaluation).order_by(EmitenEvaluation.id)))


def test_event_id_format_and_global_sequence_per_report_period(session):
    assert next_event_id(session, T) == "AFS-2025-Q3-0001"
    a = apply(session, MOD, symbol="AAAA.JK")
    b = apply(session, CRIT, symbol="BBBB.JK")
    c = apply(session, MOD, symbol="CCCC.JK", report_date=date(2025, 6, 30))
    assert (a.event_id, b.event_id, c.event_id) == ("AFS-2025-Q3-0001", "AFS-2025-Q3-0002", "AFS-2025-Q2-0001")
    assert next_event_id(session, date(2025, 8, 15)) == "AFS-2025-Q3-0003"


def test_no_incident_low_records_evaluation_only(session):
    out = apply(session, LOW)
    assert (out.kind, out.event_id, out.incident, out.notify) == ("NONE", None, None, False)
    assert session.scalars(select(Incident)).all() == []
    [ev] = evaluations(session)
    assert (ev.severity, ev.score, ev.event_id, ev.run_id) == ("LOW", 10.0, None, 1)
    assert ev.findings[0]["rule_id"] == "SLOAN_ACCRUAL"


def test_no_incident_moderate_creates_untriaged_and_notifies(session):
    out = apply(session, MOD)
    assert (out.kind, out.notify, out.previous_severity) == ("CREATED", True, None)
    inc = session.get(Incident, out.event_id)
    assert inc.triage_status == "UNTRIAGED"
    assert (inc.severity, inc.score, inc.created_run_id, inc.updated_run_id) == ("MODERATE", 40.0, 1, 1)
    assert events(session, out.event_id) == [("CREATED", None, "MODERATE")]
    assert evaluations(session)[0].event_id == out.event_id


@pytest.mark.parametrize("triage", ["UNTRIAGED", "INVESTIGATING"])
def test_escalation_keeps_open_triage(session, triage):
    created = apply(session, MOD)
    created.incident.triage_status = triage
    out = apply(session, CRIT, run_id=2)
    assert (out.kind, out.notify, out.previous_severity, out.event_id) == (
        "ESCALATED", True, Severity.MODERATE, created.event_id
    )
    assert out.incident.triage_status == triage
    assert out.incident.updated_run_id == 2
    assert events(session, out.event_id)[-1] == ("ESCALATED", "MODERATE", "CRITICAL")


@pytest.mark.parametrize("triage", [TriageStatus.RESOLVED, TriageStatus.DISMISSED])
def test_escalation_reopens_resolved_and_dismissed(session, triage):
    created = apply(session, MOD)
    created.incident.triage_status = triage.value
    out = apply(session, CRIT, run_id=2)
    assert out.notify is True  # DISMISSED suppresses notifications except on Escalation
    assert out.incident.triage_status == "UNTRIAGED"
    assert events(session, out.event_id) == [
        ("CREATED", None, "MODERATE"),
        ("ESCALATED", "MODERATE", "CRITICAL"),
        ("TRIAGE_CHANGED", triage.value, "UNTRIAGED"),
    ]


def test_same_severity_updates_silently(session):
    created = apply(session, MOD)
    created.incident.triage_status = "DISMISSED"
    out = apply(session, MOD2, run_id=2)
    assert (out.kind, out.notify, out.previous_severity) == ("UPDATED", False, Severity.MODERATE)
    assert out.incident.score == 45.0
    assert out.incident.triage_status == "DISMISSED"
    assert events(session, out.event_id) == [("CREATED", None, "MODERATE")]


@pytest.mark.parametrize("sc,to", [(MOD, "MODERATE"), (LOW, "LOW")])
def test_downgrade_records_event_keeps_triage_no_notify(session, sc, to):
    created = apply(session, CRIT)
    created.incident.triage_status = "INVESTIGATING"
    out = apply(session, sc, run_id=2)
    assert (out.kind, out.notify, out.previous_severity) == ("DOWNGRADED", False, Severity.CRITICAL)
    assert out.incident.severity == to
    assert out.incident.triage_status == "INVESTIGATING"
    assert events(session, out.event_id)[-1] == ("DOWNGRADED", "CRITICAL", to)
    assert evaluations(session)[-1].event_id == out.event_id


def test_unscorable_creates_nothing(session):
    out = apply(session, NONE)
    assert (out.kind, out.event_id, out.notify) == ("NONE", None, False)
    assert session.scalars(select(Incident)).all() == []
    [ev] = evaluations(session)
    assert ev.score is None and ev.severity is None


def test_unscorable_leaves_existing_incident_untouched(session):
    created = apply(session, CRIT)
    out = apply(session, NONE, run_id=2)
    assert (out.kind, out.event_id, out.notify) == ("NONE", created.event_id, False)
    inc = session.get(Incident, created.event_id)
    assert (inc.severity, inc.score, inc.updated_run_id) == ("CRITICAL", 75.0, 1)
    assert evaluations(session)[-1].event_id == created.event_id


def test_new_report_period_creates_new_incident_and_leaves_old_one(session):
    old = apply(session, MOD)
    new = apply(session, CRIT, run_id=2, report_date=date(2025, 12, 31))
    assert new.kind == "CREATED" and new.event_id == "AFS-2025-Q4-0001"
    inc = session.get(Incident, old.event_id)
    assert (inc.severity, inc.updated_run_id) == ("MODERATE", 1)


def test_new_report_period_low_does_not_touch_old_incident(session):
    old = apply(session, CRIT)
    out = apply(session, LOW, run_id=2, report_date=date(2025, 12, 31))
    assert out.kind == "NONE"
    assert session.get(Incident, old.event_id).severity == "CRITICAL"
    assert events(session, old.event_id) == [(IncidentEventKind.CREATED.value, None, "CRITICAL")]


def test_older_report_period_than_existing_incident_is_not_created(session):
    apply(session, MOD, report_date=date(2025, 12, 31))
    out = apply(session, CRIT, run_id=2, report_date=T)
    assert out.kind == "NONE"
    assert len(session.scalars(select(Incident)).all()) == 1

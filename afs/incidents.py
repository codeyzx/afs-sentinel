"""Incident lifecycle — docs/system-rules.md §5.

`apply_evaluation` is the single entry point per Emiten per Audit Run: it applies the §5.2 table to the
Incident of (symbol, report_date) **and** always records the EmitenEvaluation row for the run (linked to
the Incident when one exists). It only flushes; the caller owns the transaction.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from typing import Literal, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from afs.domain import IncidentEventKind, RuleFinding, ScoreResult, Severity, TriageStatus
from afs.models import EmitenEvaluation, Incident, IncidentEvent, utcnow

OutcomeKind = Literal["NONE", "CREATED", "ESCALATED", "UPDATED", "DOWNGRADED"]

REOPEN_FROM = frozenset({TriageStatus.RESOLVED.value, TriageStatus.DISMISSED.value})


@dataclass(frozen=True)
class IncidentOutcome:
    event_id: str | None
    kind: OutcomeKind
    previous_severity: Severity | None
    incident: Incident | None
    notify: bool


def _quarter_bounds(report_date: date) -> tuple[date, date, int]:
    q = (report_date.month - 1) // 3 + 1
    first = date(report_date.year, 3 * q - 2, 1)
    last_month = 3 * q
    last = date(report_date.year, last_month, calendar.monthrange(report_date.year, last_month)[1])
    return first, last, q


def next_event_id(session: Session, report_date: date) -> str:
    """AFS-{year}-Q{n}-{seq:04d}; seq = number of Incidents in that Report Period + 1 (global, all Emiten)."""
    first, last, q = _quarter_bounds(report_date)
    count = session.scalar(
        select(func.count()).select_from(Incident).where(Incident.report_date >= first, Incident.report_date <= last)
    ) or 0
    seq = count + 1
    while True:  # defensive: skip ids that already exist (e.g. after a manual delete)
        event_id = f"AFS-{report_date.year}-Q{q}-{seq:04d}"
        if session.get(Incident, event_id) is None:
            return event_id
        seq += 1


def _event(session: Session, incident: Incident, kind: IncidentEventKind, frm: str | None, to: str | None, run_id: int) -> None:
    session.add(IncidentEvent(event_id=incident.event_id, kind=kind.value, from_value=frm, to_value=to, run_id=run_id))


def _update_scores(incident: Incident, score: ScoreResult, findings: Sequence[RuleFinding], run_id: int) -> None:
    assert score.score is not None and score.severity is not None
    incident.score = score.score
    incident.severity = score.severity.value
    incident.low_confidence = score.low_confidence
    incident.severity_reason = score.severity_reason
    incident.findings = [f.to_dict() for f in findings]
    incident.updated_run_id = run_id
    incident.updated_at = utcnow()


def _record_evaluation(
    session: Session,
    *,
    run_id: int,
    symbol: str,
    report_date: date,
    score: ScoreResult,
    findings: Sequence[RuleFinding],
    event_id: str | None,
) -> None:
    session.add(
        EmitenEvaluation(
            run_id=run_id,
            symbol=symbol,
            report_date=report_date,
            score=score.score,
            severity=score.severity.value if score.severity is not None else None,
            low_confidence=score.low_confidence,
            evaluated_weight=score.evaluated_weight,
            severity_reason=score.severity_reason,
            findings=[f.to_dict() for f in findings],
            event_id=event_id,
        )
    )


def _decide(
    session: Session,
    *,
    run_id: int,
    symbol: str,
    report_date: date,
    score: ScoreResult,
    findings: Sequence[RuleFinding],
) -> IncidentOutcome:
    incident = session.scalar(select(Incident).where(Incident.symbol == symbol, Incident.report_date == report_date))

    if score.score is None or score.severity is None:
        # Nothing evaluable: never create, never touch an existing Incident.
        return IncidentOutcome(incident.event_id if incident else None, "NONE", None, incident, False)

    new = score.severity
    if incident is None:
        newer = session.scalar(
            select(func.count()).select_from(Incident).where(Incident.symbol == symbol, Incident.report_date > report_date)
        )
        if new.rank < Severity.MODERATE.rank or newer:
            # LOW, or a stale Report Period older than an existing Incident: findings & score only.
            return IncidentOutcome(None, "NONE", None, None, False)
        incident = Incident(
            event_id=next_event_id(session, report_date),
            symbol=symbol,
            report_date=report_date,
            triage_status=TriageStatus.UNTRIAGED.value,
            analyst_notes="",
            created_run_id=run_id,
        )
        _update_scores(incident, score, findings, run_id)
        session.add(incident)
        session.flush()
        _event(session, incident, IncidentEventKind.CREATED, None, new.value, run_id)
        return IncidentOutcome(incident.event_id, "CREATED", None, incident, True)

    previous = Severity(incident.severity)
    _update_scores(incident, score, findings, run_id)

    if new.rank > previous.rank:
        _event(session, incident, IncidentEventKind.ESCALATED, previous.value, new.value, run_id)
        if incident.triage_status in REOPEN_FROM:
            _event(
                session, incident, IncidentEventKind.TRIAGE_CHANGED, incident.triage_status, TriageStatus.UNTRIAGED.value, run_id
            )
            incident.triage_status = TriageStatus.UNTRIAGED.value
        return IncidentOutcome(incident.event_id, "ESCALATED", previous, incident, True)

    if new.rank < previous.rank:
        _event(session, incident, IncidentEventKind.DOWNGRADED, previous.value, new.value, run_id)
        return IncidentOutcome(incident.event_id, "DOWNGRADED", previous, incident, False)

    return IncidentOutcome(incident.event_id, "UPDATED", previous, incident, False)


def apply_evaluation(
    session: Session,
    *,
    run_id: int,
    symbol: str,
    report_date: date,
    score: ScoreResult,
    findings: list[RuleFinding],
) -> IncidentOutcome:
    """Apply §5.2 for one Emiten and record its EmitenEvaluation row. Flushes; never commits."""
    outcome = _decide(session, run_id=run_id, symbol=symbol, report_date=report_date, score=score, findings=findings)
    _record_evaluation(
        session,
        run_id=run_id,
        symbol=symbol,
        report_date=report_date,
        score=score,
        findings=findings,
        event_id=outcome.event_id,
    )
    session.flush()
    return outcome

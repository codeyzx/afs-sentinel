"""Read models for the web pages. Everything returned is plain data, safe to use after the session closes."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from afs.domain import FindingStatus, TriageStatus
from afs.labels import RULE_META, finding_sort_key
from afs.models import ApiCache, AuditRun, BacktestResult, Emiten, EmitenEvaluation, Incident, IncidentEvent
from afs.web import formatting as fmt

TRIAGE_QUEUE_ORDER = {TriageStatus.UNTRIAGED.value: 0, TriageStatus.INVESTIGATING.value: 1}
CHART_QUARTERS = 5


def _status(value: str) -> FindingStatus:
    try:
        return FindingStatus(value)
    except ValueError:
        return FindingStatus.INSUFFICIENT_DATA


def sorted_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(findings or [], key=lambda f: finding_sort_key(f.get("rule_id", ""), _status(f.get("status", ""))))


def rule_dots(findings: list[dict[str, Any]]) -> list[dict[str, str]]:
    """One entry per Forensic Rule in RULE_META order; rules absent from the findings show as gray."""
    by_rule = {f.get("rule_id"): f for f in findings or []}
    dots = []
    for number, (rule_id, meta) in enumerate(RULE_META.items(), start=1):
        f = by_rule.get(rule_id)
        status = f.get("status", "") if f else FindingStatus.INSUFFICIENT_DATA.value
        dots.append(
            {
                "rule_id": rule_id,
                "number": number,  # fixed position, not a rank: dot 3 is always Altman
                "name": meta.name,
                "subtitle": meta.subtitle,
                "label": fmt.finding_label(status) if f else "Belum dinilai",
                "tone": fmt.finding_tone(status),
                "headline": (f or {}).get("headline", ""),
            }
        )
    return dots


def rule_legend() -> list[dict[str, Any]]:
    """The numbered legend beside the Universe table; numbers match `rule_dots`."""
    return [
        {"number": n, "rule_id": rule_id, "name": meta.name, "subtitle": meta.subtitle}
        for n, (rule_id, meta) in enumerate(RULE_META.items(), start=1)
    ]


def last_run(session: Session) -> AuditRun | None:
    return session.scalars(select(AuditRun).order_by(AuditRun.started_at.desc(), AuditRun.id.desc()).limit(1)).first()


def latest_evaluations(session: Session) -> dict[str, EmitenEvaluation]:
    """Latest EmitenEvaluation per symbol (by created_at, then id)."""
    latest: dict[str, EmitenEvaluation] = {}
    rows = session.scalars(select(EmitenEvaluation).order_by(EmitenEvaluation.created_at, EmitenEvaluation.id))
    for ev in rows:
        latest[ev.symbol] = ev
    return latest


def severity_counts(evals: dict[str, EmitenEvaluation]) -> dict[str, int]:
    counts = {"CRITICAL": 0, "MODERATE": 0, "LOW": 0}
    for ev in evals.values():
        if ev.severity in counts:
            counts[ev.severity] += 1
    return counts


def triage_queue(session: Session) -> list[dict[str, Any]]:
    incidents = session.scalars(select(Incident)).all()
    incidents = sorted(incidents, key=lambda i: (TRIAGE_QUEUE_ORDER.get(i.triage_status, 2), -(i.score or 0)))
    return [
        {
            "event_id": i.event_id,
            "ticker": fmt.ticker(i.symbol),
            "period": fmt.fmt_period(i.report_date),
            "score": i.score,
            "severity": i.severity,
            "low_confidence": i.low_confidence,
            "triage_status": i.triage_status,
            "headline": (sorted_findings(i.findings)[:1] or [{}])[0].get("headline", ""),
            "updated_at": i.updated_at,
        }
        for i in incidents
    ]


def universe_rows(session: Session, evals: dict[str, EmitenEvaluation]) -> list[dict[str, Any]]:
    emiten = {e.symbol: e for e in session.scalars(select(Emiten).where(Emiten.is_excluded.is_(False)))}
    symbols = sorted(set(emiten) | set(evals))
    rows = []
    for symbol in symbols:
        ev = evals.get(symbol)
        e = emiten.get(symbol)
        findings = sorted_findings(ev.findings) if ev else []
        rows.append(
            {
                "symbol": symbol,
                "ticker": fmt.ticker(symbol),
                "name": e.company_name if e else "",
                "sub_sector": e.sub_sector if e else "",
                "evaluated": ev is not None,
                "score": ev.score if ev else None,
                "score_text": fmt.fmt_score(ev.score) if ev else "—",
                "severity": ev.severity if ev else None,
                "severity_rank": {"LOW": 0, "MODERATE": 1, "CRITICAL": 2}.get((ev.severity if ev else None) or "", -1),
                "severity_label": (fmt.severity_label(ev.severity) if ev else "Belum dinilai"),
                "severity_tone": fmt.severity_tone(ev.severity if ev else None),
                "low_confidence": bool(ev and ev.low_confidence),
                "severity_reason": ev.severity_reason if ev else None,
                "period": fmt.fmt_period(ev.report_date) if ev else "—",
                "event_id": ev.event_id if ev else None,
                "dots": rule_dots(ev.findings) if ev else [],
                "findings": [
                    {
                        "name": fmt.rule_name(f.get("rule_id", "")),
                        "subtitle": fmt.rule_subtitle(f.get("rule_id", "")),
                        "label": fmt.finding_label(f.get("status", "")),
                        "tone": fmt.finding_tone(f.get("status", "")),
                        "headline": f.get("headline", ""),
                        "missing": f.get("missing"),
                    }
                    for f in findings
                ],
            }
        )
    return rows


def incident_insight(session: Session, event_id: str) -> dict[str, Any] | None:
    """The newest Incident Insight, as plain data. None means none has been produced yet."""
    from afs import insight as insight_mod

    rows = insight_mod.history_for(session, event_id)
    if not rows:
        return None
    latest = rows[0]
    return {
        "what_happened": latest.what_happened,
        "why_it_matters": latest.why_it_matters,
        "what_to_check": list(latest.what_to_check or []),
        "created_at": latest.created_at,
        "model": latest.model,
        "prompt_version": latest.prompt_version,
        "older_count": len(rows) - 1,
    }


def incident_events(session: Session, event_id: str) -> list[IncidentEvent]:
    return list(
        session.scalars(
            select(IncidentEvent)
            .where(IncidentEvent.event_id == event_id)
            .order_by(IncidentEvent.created_at, IncidentEvent.id)
        )
    )


def chart_quarters(session: Session, symbol: str, report_date: date) -> list[dict[str, Any]]:
    """Up to 5 quarters ending at report_date: earnings vs OCF in miliar IDR, oldest first."""
    rows = session.scalars(
        select(ApiCache)
        .where(ApiCache.kind == "quarter", ApiCache.symbol == symbol, ApiCache.key <= report_date.isoformat())
        .order_by(ApiCache.key.desc())
    )
    out: list[dict[str, Any]] = []
    for row in rows:
        payload = row.payload if isinstance(row.payload, dict) else {}
        if payload.get("missing"):
            continue
        try:
            label = fmt.fmt_period(date.fromisoformat(row.key))
        except ValueError:
            continue
        earnings, ocf = payload.get("earnings"), payload.get("operating_cash_flow")
        if earnings is None and ocf is None:
            continue
        out.append(
            {
                "label": label,
                "earnings": None if earnings is None else round(float(earnings) / 1e9, 2),
                "ocf": None if ocf is None else round(float(ocf) / 1e9, 2),
            }
        )
        if len(out) == CHART_QUARTERS:
            break
    return list(reversed(out))


def audit_runs(session: Session, limit: int = 100) -> list[AuditRun]:
    return list(session.scalars(select(AuditRun).order_by(AuditRun.started_at.desc(), AuditRun.id.desc()).limit(limit)))


def run_evaluations(session: Session, run_id: int) -> list[dict[str, Any]]:
    """What one Audit Run did to each Emiten — the structured form of log_text."""
    names = {e.symbol: e.company_name for e in session.scalars(select(Emiten))}
    rows = session.scalars(
        select(EmitenEvaluation).where(EmitenEvaluation.run_id == run_id).order_by(EmitenEvaluation.id)
    )
    out = []
    for ev in rows:
        out.append(
            {
                "ticker": fmt.ticker(ev.symbol),
                "name": names.get(ev.symbol, ""),
                "period": fmt.fmt_period(ev.report_date),
                "score_text": fmt.fmt_score(ev.score),
                "severity_label": fmt.severity_label(ev.severity),
                "severity_tone": fmt.severity_tone(ev.severity),
                "event_id": ev.event_id,
                "outcome": "Incident " + ev.event_id if ev.event_id else "Tidak ada Incident",
            }
        )
    return out


def backtest_results(session: Session, case_id: str) -> list[BacktestResult]:
    return list(
        session.scalars(
            select(BacktestResult).where(BacktestResult.case_id == case_id).order_by(BacktestResult.report_date)
        )
    )


def emiten_name(session: Session, symbol: str) -> str:
    e = session.get(Emiten, symbol)
    return e.company_name if e else ""


def has_any_run(session: Session) -> bool:
    return (session.scalar(select(func.count()).select_from(AuditRun)) or 0) > 0

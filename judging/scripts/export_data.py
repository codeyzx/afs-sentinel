"""Export real production data for the judging video (read-only).

Usage (from repo root):
  DATABASE_URL=$(heroku config:get DATABASE_URL -a afs-sentinel) \
  BASE_WEB_URL=https://afs-sentinel-ee5d2e28af17.herokuapp.com \
  uv run python judging/scripts/export_data.py
"""
import json
import os
from pathlib import Path

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from afs import telegram
from afs.domain import RuleFinding, RunTrigger, Severity
from afs.models import AuditRun, BacktestResult, Emiten, Incident, IncidentInsight
from afs.config import get_settings
from afs.web.backtest_view import claim_sentence, load_cases

OUT = Path(__file__).resolve().parent.parent / "src" / "data"
EVENT_ID = "AFS-2026-Q2-0003"  # highest-scoring live Incident (UNVR)

url = os.environ["DATABASE_URL"].replace("postgres://", "postgresql+psycopg://", 1)
engine = create_engine(url)

with Session(engine) as s:
    s.execute(text("SET TRANSACTION READ ONLY"))
    inc = s.get(Incident, EVENT_ID)
    em = s.get(Emiten, inc.symbol)
    ins = s.scalars(
        select(IncidentInsight).where(IncidentInsight.event_id == EVENT_ID).order_by(IncidentInsight.created_at)
    ).first()
    findings = [RuleFinding.from_dict(f) for f in inc.findings]
    alert_text = telegram.format_incident_message(
        event_id=inc.event_id,
        symbol=inc.symbol,
        company_name=em.company_name if em else inc.symbol,
        report_date=inc.report_date,
        score=inc.score,
        severity=Severity(inc.severity),
        low_confidence=inc.low_confidence,
        severity_reason=inc.severity_reason,
        findings=findings,
        escalated_from=None,
        insight_line=ins.what_happened if ins else None,
    )
    created_run = s.get(AuditRun, inc.created_run_id)

    runs = s.scalars(select(AuditRun).order_by(AuditRun.started_at.desc()).limit(12)).all()
    latest = runs[0]
    summary_text = telegram.format_run_summary(
        started_at=latest.started_at,
        trigger=RunTrigger(latest.trigger),
        emiten_scanned=latest.emiten_scanned,
        incidents_new=latest.incidents_new,
        escalations=latest.escalations,
        emiten_failed=latest.emiten_failed,
        credits_used=latest.credits_used,
    )

    cases = {c.case_id: c for c in load_cases(get_settings().backtest_cases_path)}
    backtest = {}
    for case_id in ("WSKT", "SRIL"):
        rows = s.scalars(
            select(BacktestResult).where(BacktestResult.case_id == case_id).order_by(BacktestResult.report_date)
        ).all()
        case = cases.get(case_id)
        backtest[case_id] = {
            "rows": [
                {"date": r.report_date.isoformat(), "score": r.score, "severity": r.severity} for r in rows
            ],
            "events": [{"date": e.date.isoformat(), "label": e.label} for e in case.events] if case else [],
            "claims": [claim_sentence(rows, e) for e in case.events] if case else [],
        }

data = {
    "alert": {
        "eventId": inc.event_id,
        "text": alert_text,
        "button": telegram.OPEN_INCIDENT_BUTTON,
        "sentAt": (created_run.finished_at or created_run.started_at).isoformat(),
        "score": inc.score,
        "severity": inc.severity,
        "symbol": inc.symbol,
    },
    "runSummary": {"text": summary_text, "sentAt": (latest.finished_at or latest.started_at).isoformat()},
    "runs": [
        {
            "id": r.id,
            "trigger": r.trigger,
            "status": r.status,
            "startedAt": r.started_at.isoformat(),
            "scanned": r.emiten_scanned,
            "incidentsNew": r.incidents_new,
            "credits": r.credits_used,
        }
        for r in runs
    ],
    "backtest": backtest,
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "real.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
print(json.dumps(data, ensure_ascii=False, indent=2)[:4000])

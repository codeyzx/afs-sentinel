"""AFS Sentinel web app (docs/system-rules.md §9)."""

from __future__ import annotations

import logging
import threading
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from afs import labels, schedule, telegram
from afs.config import Settings, get_settings
from afs.db import session_scope
from afs.domain import IncidentEventKind, RunTrigger, TriageStatus
from afs.labels import RULE_META, TRIAGE_LABEL
from afs.models import Incident
from afs.web import auth, queries
from afs.web import formatting as fmt
from afs.web.backtest_view import claim_sentence, load_cases

log = logging.getLogger(__name__)
HERE = Path(__file__).resolve().parent


def _templates() -> Jinja2Templates:
    templates = Jinja2Templates(directory=HERE / "templates")
    env = templates.env
    env.filters.update(
        wib=fmt.fmt_wib,
        date_id=fmt.fmt_date,
        num=fmt.fmt_num,
        score=fmt.fmt_score,
        ticker=fmt.ticker,
        period=fmt.fmt_period,
        finding_value=fmt.fmt_finding_value,
        value=fmt.fmt_value,
        finding_label=fmt.finding_label,
        finding_tone=fmt.finding_tone,
        severity_label=fmt.severity_label,
        severity_tone=fmt.severity_tone,
        triage_label=fmt.triage_label,
        rule_name=fmt.rule_name,
        rule_subtitle=fmt.rule_subtitle,
        rule_limitation=fmt.rule_limitation,
        trigger_label=fmt.trigger_label,
        trigger_icon=fmt.trigger_icon,
        run_status_label=fmt.run_status_label,
        run_status_tone=fmt.run_status_tone,
    )
    env.globals.update(
        RULE_META=RULE_META,
        TRIAGE_LABEL=TRIAGE_LABEL,
        labels=labels,
        fmt_duration=fmt.fmt_duration,
        RULE_LEGEND=queries.rule_legend(),
    )
    return templates


def event_description(kind: str, from_value: str | None, to_value: str | None) -> str:
    match kind:
        case IncidentEventKind.CREATED:
            return f"Incident dibuat dengan severity {fmt.severity_label(to_value)}" if to_value else "Incident dibuat"
        case IncidentEventKind.ESCALATED:
            return f"Escalation: {fmt.severity_label(from_value)} → {fmt.severity_label(to_value)}"
        case IncidentEventKind.DOWNGRADED:
            return f"Severity turun: {fmt.severity_label(from_value)} → {fmt.severity_label(to_value)}"
        case IncidentEventKind.TRIAGE_CHANGED:
            return f"Status triage: {fmt.triage_label(from_value)} → {fmt.triage_label(to_value)}"
        case IncidentEventKind.NOTE_UPDATED:
            return "Catatan analis diperbarui"
    return kind


def _start_manual_run(request: Request) -> None:
    try:
        from afs.runner import is_run_in_progress, run_audit
    except ImportError:
        auth.flash(request, "Runner belum tersedia", "yellow")
        return
    if is_run_in_progress():
        auth.flash(request, "Audit Run sedang berjalan", "yellow")
        return

    def target() -> None:
        try:
            run_audit(RunTrigger.MANUAL)
        except Exception:  # background thread: log, never crash the web process
            log.exception("Manual Audit Run failed")

    threading.Thread(target=target, name="manual-audit-run", daemon=True).start()
    auth.flash(request, "Audit Run dimulai. Muat ulang halaman ini beberapa menit lagi untuk melihat hasilnya.", "green")


def _backtest_chart(results: list[Any], events: list[Any]) -> dict[str, Any]:
    """x = quarter index; events get a fractional x between the surrounding report dates."""
    dates = [r.report_date for r in results]

    def position(d: date) -> float:
        if not dates:
            return 0.0
        if d <= dates[0]:
            return -(dates[0] - d).days / 91.3
        for i in range(len(dates) - 1):
            if dates[i] <= d < dates[i + 1]:
                return i + (d - dates[i]).days / max((dates[i + 1] - dates[i]).days, 1)
        return len(dates) - 1 + (d - dates[-1]).days / 91.3

    return {
        "labels": [fmt.fmt_period(d) for d in dates],
        "scores": [r.score for r in results],
        "events": [{"x": round(position(e.date), 3), "label": e.label} for e in events],
    }


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    telegram.quiet_http_logging()  # a manual Audit Run sends Telegram from this process
    app = FastAPI(title="AFS Sentinel", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret, same_site="lax")
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
    templates = _templates()

    def render(request: Request, name: str, context: dict[str, Any], status_code: int = 200) -> HTMLResponse:
        base = {
            "logged_in": auth.is_logged_in(request),
            "flashes": auth.pop_flashes(request),
            "current_path": request.url.path,
        }
        return templates.TemplateResponse(request, name, {**base, **context}, status_code=status_code)

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request) -> Response:
        with session_scope() as s:
            evals = queries.latest_evaluations(s)
            last_success = schedule.last_successful_start(s)
            return render(
                request,
                "dashboard.html",
                {
                    "last_run": queries.last_run(s),
                    "interval_days": settings.run_interval_days,
                    "next_run": fmt.next_scheduled_run(last_success, settings.run_interval_days),
                    "counts": queries.severity_counts(evals),
                    "queue": queries.triage_queue(s),
                    "rows": queries.universe_rows(s, evals),
                },
            )

    @app.post("/runs")
    def start_run(request: Request) -> Response:
        if not auth.is_logged_in(request):
            return auth.login_redirect("/")
        _start_manual_run(request)
        return RedirectResponse("/", status_code=303)

    @app.get("/incidents/{event_id}", response_class=HTMLResponse)
    def incident_detail(request: Request, event_id: str) -> Response:
        with session_scope() as s:
            incident = s.get(Incident, event_id)
            if incident is None:
                return render(request, "not_found.html", {"event_id": event_id}, status_code=404)
            findings = queries.sorted_findings(incident.findings)
            events = [
                {"at": e.created_at, "kind": e.kind, "text": event_description(e.kind, e.from_value, e.to_value)}
                for e in queries.incident_events(s, event_id)
            ]
            return render(
                request,
                "incident.html",
                {
                    "incident": incident,
                    "company_name": queries.emiten_name(s, incident.symbol),
                    "findings": findings,
                    "top_headline": findings[0].get("headline", "") if findings else "",
                    "insight": queries.incident_insight(s, event_id),
                    "chart": queries.chart_quarters(s, incident.symbol, incident.report_date),
                    "events": events,
                    "triage_options": list(TriageStatus),
                },
            )

    @app.post("/incidents/{event_id}/insight")
    def incident_insight(request: Request, event_id: str) -> Response:
        """Make an Incident Insight by hand — the way out when Gemini was down during the run."""
        if not auth.is_logged_in(request):
            return auth.login_redirect(f"/incidents/{event_id}")
        from afs import insight as insight_mod

        with session_scope() as s:
            incident = s.get(Incident, event_id)
            if incident is None:
                return render(request, "not_found.html", {"event_id": event_id}, status_code=404)
            try:
                insight_mod.generate_one(s, event_id, company_name=queries.emiten_name(s, incident.symbol))
            except insight_mod.InsightUnavailable as exc:
                auth.flash(request, f"Ringkasan AI gagal dibuat: {exc}", "red")
            else:
                auth.flash(request, "Ringkasan AI dibuat", "green")
        return RedirectResponse(f"/incidents/{event_id}#insight", status_code=303)

    @app.post("/incidents/{event_id}/triage")
    def incident_triage(
        request: Request, event_id: str, status: str = Form(""), notes: str | None = Form(None)
    ) -> Response:
        if not auth.is_logged_in(request):
            return auth.login_redirect(f"/incidents/{event_id}")
        from afs.triage import update_triage

        try:
            triage_status = TriageStatus(status) if status else None
        except ValueError:
            auth.flash(request, "Status triage tidak dikenal", "red")
            return RedirectResponse(f"/incidents/{event_id}", status_code=303)
        try:
            with session_scope() as s:
                update_triage(s, event_id, status=triage_status, notes=notes)
        except KeyError:
            return render(request, "not_found.html", {"event_id": event_id}, status_code=404)
        auth.flash(request, "Perubahan triage disimpan", "green")
        return RedirectResponse(f"/incidents/{event_id}#triage", status_code=303)

    @app.get("/backtest", response_class=HTMLResponse)
    def backtest(request: Request) -> Response:
        cases = load_cases(settings.backtest_cases_path)
        views = []
        with session_scope() as s:
            for case in cases:
                results = queries.backtest_results(s, case.case_id)
                views.append(
                    {
                        "case": case,
                        "results": results,
                        "rows": [
                            {"result": r, "dots": queries.rule_dots(r.findings)} for r in results
                        ],
                        "claims": [
                            {"event": e, "sentence": claim_sentence(results, e)} for e in case.events
                        ]
                        if results
                        else [],
                        "chart": _backtest_chart(results, case.events),
                    }
                )
            return render(request, "backtest.html", {"views": views})

    @app.get("/logs", response_class=HTMLResponse)
    def logs(request: Request) -> Response:
        with session_scope() as s:
            runs = queries.audit_runs(s)
            return render(
                request,
                "logs.html",
                {"runs": [{"run": r, "evaluations": queries.run_evaluations(s, r.id)} for r in runs]},
            )

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request, next: str = "/") -> Response:
        return render(request, "login.html", {"next": auth.safe_next(next), "error": None})

    @app.post("/login")
    def login_submit(request: Request, password: str = Form(""), next: str = Form("/")) -> Response:
        if not auth.check_password(password, settings.admin_password):
            return render(
                request, "login.html", {"next": auth.safe_next(next), "error": "Password salah."}, status_code=401
            )
        auth.login(request)
        auth.flash(request, "Berhasil masuk", "green")
        return RedirectResponse(auth.safe_next(next), status_code=303)

    @app.post("/logout")
    def logout(request: Request) -> Response:
        auth.logout(request)
        auth.flash(request, "Berhasil keluar", "gray")
        return RedirectResponse("/", status_code=303)

    return app


app = create_app()

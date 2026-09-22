"""AFS Sentinel web app (docs/system-rules.md §9) with i18n support."""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from starlette.middleware.sessions import SessionMiddleware

from afs import audio, labels, schedule, telegram
from afs.config import Settings, get_settings
from afs.db import session_scope
from afs.domain import IncidentEventKind, TriageStatus
from afs.labels import RULE_META, TRIAGE_LABEL
from afs.models import Incident
from afs.web import auth, queries
from afs.web import formatting as fmt
from afs.web.backtest_view import claim_sentence, load_cases
from afs.web.i18n import (
    DEFAULT_LANG,
    LANGUAGES,
    SUPPORTED_LANGS,
    localize_headline,
    localize_severity_reason,
    t,
)

log = logging.getLogger(__name__)
HERE = Path(__file__).resolve().parent


def get_lang(request: Request) -> str:
    """Determine the current language from query param, cookie, or default."""
    param = request.query_params.get("lang")
    if param in SUPPORTED_LANGS:
        return param
    cookie = request.cookies.get("lang")
    if cookie in SUPPORTED_LANGS:
        return cookie
    return DEFAULT_LANG


def _templates() -> Jinja2Templates:
    templates = Jinja2Templates(directory=HERE / "templates")
    env = templates.env

    def _get_lang_from_ctx(ctx: Any) -> str:
        lang = ctx.get("current_lang")
        if lang in SUPPORTED_LANGS:
            return lang
        req = ctx.get("request")
        if req is not None:
            return get_lang(req)
        return DEFAULT_LANG

    @pass_context
    def _wib(ctx: Any, dt: datetime | None, with_day: bool = False, lang: str | None = None) -> str:
        return fmt.fmt_wib(dt, with_day=with_day, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _date_id(ctx: Any, d: date | None, lang: str | None = None) -> str:
        return fmt.fmt_date(d, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _num(ctx: Any, value: float | int | None, decimals: int = 0, lang: str | None = None) -> str:
        return fmt.fmt_num(value, decimals=decimals, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _score(ctx: Any, score: float | None, lang: str | None = None) -> str:
        return fmt.fmt_score(score, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _finding_value(ctx: Any, rule_id: str, value: Any, lang: str | None = None) -> str:
        return fmt.fmt_finding_value(rule_id, value, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _value(ctx: Any, value: Any, lang: str | None = None) -> str:
        return fmt.fmt_value(value, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _finding_label(ctx: Any, status: str, lang: str | None = None) -> str:
        return fmt.finding_label(status, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _severity_label(ctx: Any, severity: str | None, lang: str | None = None) -> str:
        return fmt.severity_label(severity, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _triage_label(ctx: Any, status: str | None, lang: str | None = None) -> str:
        return fmt.triage_label(status, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _rule_name(ctx: Any, rule_id: str, lang: str | None = None) -> str:
        return fmt.rule_name(rule_id, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _rule_subtitle(ctx: Any, rule_id: str, lang: str | None = None) -> str:
        return fmt.rule_subtitle(rule_id, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _rule_limitation(ctx: Any, rule_id: str, lang: str | None = None) -> str:
        return fmt.rule_limitation(rule_id, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _trigger_label(ctx: Any, trigger: str | None, lang: str | None = None) -> str:
        return fmt.trigger_label(trigger, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _run_status_label(ctx: Any, status: str | None, lang: str | None = None) -> str:
        return fmt.run_status_label(status, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _fmt_duration(ctx: Any, start: datetime | None, end: datetime | None, lang: str | None = None) -> str:
        return fmt.fmt_duration(start, end, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _localize_headline(ctx: Any, text: str | None, lang: str | None = None) -> str:
        return localize_headline(text, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _localize_severity_reason(ctx: Any, text: str | None, lang: str | None = None) -> str:
        return localize_severity_reason(text, lang=lang or _get_lang_from_ctx(ctx))

    @pass_context
    def _t(ctx: Any, key: str, lang: str | None = None, **kwargs: Any) -> str:
        return t(key, lang=lang or _get_lang_from_ctx(ctx), **kwargs)

    @pass_context
    def _get_rule_legend(ctx: Any, lang: str | None = None) -> list[dict[str, Any]]:
        return queries.rule_legend(lang=lang or _get_lang_from_ctx(ctx))

    env.filters.update(
        wib=_wib,
        date_id=_date_id,
        num=_num,
        score=_score,
        ticker=fmt.ticker,
        period=fmt.fmt_period,
        finding_value=_finding_value,
        value=_value,
        finding_label=_finding_label,
        finding_tone=fmt.finding_tone,
        severity_label=_severity_label,
        severity_tone=fmt.severity_tone,
        triage_label=_triage_label,
        rule_name=_rule_name,
        rule_subtitle=_rule_subtitle,
        rule_limitation=_rule_limitation,
        trigger_label=_trigger_label,
        trigger_icon=fmt.trigger_icon,
        run_status_label=_run_status_label,
        run_status_tone=fmt.run_status_tone,
        localize_headline=_localize_headline,
        localize_severity_reason=_localize_severity_reason,
        t=_t,
    )
    env.globals.update(
        RULE_META=RULE_META,
        TRIAGE_LABEL=TRIAGE_LABEL,
        labels=labels,
        fmt_duration=_fmt_duration,
        RULE_LEGEND=queries.rule_legend(),
        get_rule_legend=_get_rule_legend,
        rule_legend=_get_rule_legend,
        localize_headline=_localize_headline,
        localize_severity_reason=_localize_severity_reason,
        t=_t,
        LANGUAGES=LANGUAGES,
    )
    return templates


def event_description(kind: str, from_value: str | None, to_value: str | None, lang: str = DEFAULT_LANG) -> str:
    if lang == "en":
        match kind:
            case IncidentEventKind.CREATED:
                return (
                    f"Incident created with severity {fmt.severity_label(to_value, lang='en')}"
                    if to_value
                    else "Incident created"
                )
            case IncidentEventKind.ESCALATED:
                return f"Escalation: {fmt.severity_label(from_value, lang='en')} → {fmt.severity_label(to_value, lang='en')}"
            case IncidentEventKind.DOWNGRADED:
                return f"Severity downgraded: {fmt.severity_label(from_value, lang='en')} → {fmt.severity_label(to_value, lang='en')}"
            case IncidentEventKind.TRIAGE_CHANGED:
                return f"Triage status: {fmt.triage_label(from_value, lang='en')} → {fmt.triage_label(to_value, lang='en')}"
            case IncidentEventKind.NOTE_UPDATED:
                return "Analyst notes updated"
        return kind

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


def _backtest_chart(results: list[Any], events: list[Any], lang: str = DEFAULT_LANG) -> dict[str, Any]:
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
        "events": [
            {
                "x": round(position(e.date), 3),
                "label": e.display_label(lang) if hasattr(e, "display_label") else e.label,
            }
            for e in events
        ],
    }


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    telegram.quiet_http_logging()
    app = FastAPI(title="AFS Sentinel", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings = settings
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret, same_site="lax")
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
    templates = _templates()

    def render(request: Request, name: str, context: dict[str, Any], status_code: int = 200) -> HTMLResponse:
        lang = get_lang(request)
        base = {
            "logged_in": auth.is_logged_in(request),
            "flashes": auth.pop_flashes(request),
            "current_path": request.url.path,
            "current_lang": lang,
            "languages": LANGUAGES,
        }
        resp = templates.TemplateResponse(request, name, {**base, **context}, status_code=status_code)
        if "lang" in request.query_params and request.query_params["lang"] in SUPPORTED_LANGS:
            resp.set_cookie(key="lang", value=request.query_params["lang"], max_age=31536000, path="/", samesite="lax")
        return resp

    @app.get("/set-language")
    @app.post("/set-language")
    def set_language(request: Request, lang: str = DEFAULT_LANG, next: str = "/") -> Response:
        if lang not in SUPPORTED_LANGS:
            lang = DEFAULT_LANG
        redirect_url = auth.safe_next(next)
        resp = RedirectResponse(redirect_url, status_code=303)
        resp.set_cookie(key="lang", value=lang, max_age=31536000, path="/", samesite="lax")
        return resp

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request) -> Response:
        lang = get_lang(request)
        with session_scope() as s:
            evals = queries.latest_evaluations(s)
            last_success = schedule.last_successful_start(s)
            last_run_row = queries.last_run(s)
            run_audio_script = audio.build_run_summary_audio_script(s, last_run_row) if last_run_row else ""
            return render(
                request,
                "dashboard.html",
                {
                    "last_run": last_run_row,
                    "run_audio_script": run_audio_script,
                    "interval_days": settings.run_interval_days,
                    "next_run": fmt.next_scheduled_run(last_success, settings.run_interval_days),
                    "counts": queries.severity_counts(evals),
                    "queue": queries.triage_queue(s, lang=lang),
                    "rows": queries.universe_rows(s, evals, lang=lang),
                },
            )

    @app.get("/dashboard/audio")
    @app.get("/runs/{run_id}/audio")
    def dashboard_run_audio(request: Request, run_id: int | None = None) -> Response:
        from afs import audio as audio_mod
        from afs.models import AuditRun

        with session_scope() as s:
            if run_id is not None:
                run = s.get(AuditRun, run_id)
            else:
                from sqlalchemy import select
                run = s.scalars(select(AuditRun).order_by(AuditRun.started_at.desc())).first()

            try:
                audio_bytes, _script = audio_mod.get_or_create_run_audio(s, run)
            except audio_mod.AudioUnavailable as exc:
                return Response(
                    content=f"Audio generation unavailable: {exc}",
                    status_code=503,
                    media_type="text/plain",
                )

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": 'inline; filename="dashboard_briefing.mp3"',
                "Cache-Control": "public, max-age=3600",
                "Accept-Ranges": "bytes",
            },
        )

    @app.get("/emiten/{symbol}/audio")
    def emiten_audio(request: Request, symbol: str) -> Response:
        from afs import audio as audio_mod

        clean_sym = symbol.removesuffix(".JK")
        with session_scope() as s:
            try:
                audio_bytes, _script = audio_mod.get_or_create_emiten_audio(s, clean_sym)
            except audio_mod.AudioUnavailable as exc:
                return Response(
                    content=f"Audio generation unavailable: {exc}",
                    status_code=503,
                    media_type="text/plain",
                )

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f'inline; filename="{clean_sym}_profile.mp3"',
                "Cache-Control": "public, max-age=86400",
                "Accept-Ranges": "bytes",
            },
        )

    @app.get("/incidents/{event_id}", response_class=HTMLResponse)
    def incident_detail(request: Request, event_id: str) -> Response:
        lang = get_lang(request)
        with session_scope() as s:
            incident = s.get(Incident, event_id)
            if incident is None:
                return render(request, "not_found.html", {"event_id": event_id}, status_code=404)
            raw_findings = queries.sorted_findings(incident.findings)
            findings = [
                {**f, "headline": localize_headline(f.get("headline", ""), lang=lang)}
                for f in raw_findings
            ]
            events = [
                {"at": e.created_at, "kind": e.kind, "text": event_description(e.kind, e.from_value, e.to_value, lang=lang)}
                for e in queries.incident_events(s, event_id)
            ]
            company_name = queries.emiten_name(s, incident.symbol)
            ins_row = queries.incident_insight(s, event_id)
            audio_script = audio.build_audio_script(incident, company_name=company_name, insight_row=ins_row)
            return render(
                request,
                "incident.html",
                {
                    "incident": incident,
                    "company_name": company_name,
                    "findings": findings,
                    "top_headline": localize_headline(raw_findings[0].get("headline", ""), lang=lang) if raw_findings else "",
                    "insight": ins_row,
                    "audio_url": f"/incidents/{event_id}/audio",
                    "audio_script": audio_script,
                    "chart": queries.chart_quarters(s, incident.symbol, incident.report_date),
                    "events": events,
                    "triage_options": list(TriageStatus),
                },
            )

    @app.get("/incidents/{event_id}/audio")
    def incident_audio(request: Request, event_id: str) -> Response:
        from afs import audio as audio_mod

        with session_scope() as s:
            incident = s.get(Incident, event_id)
            if incident is None:
                return render(request, "not_found.html", {"event_id": event_id}, status_code=404)
            company_name = queries.emiten_name(s, incident.symbol)
            ins_row = queries.incident_insight(s, event_id)
            try:
                audio_bytes, _script = audio_mod.get_or_create_incident_audio(
                    session=s,
                    incident=incident,
                    company_name=company_name,
                    insight_row=ins_row,
                )
            except audio_mod.AudioUnavailable as exc:
                return Response(
                    content=f"Audio generation unavailable: {exc}",
                    status_code=503,
                    media_type="text/plain",
                )

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f'inline; filename="{event_id}.mp3"',
                "Cache-Control": "public, max-age=86400",
                "Accept-Ranges": "bytes",
            },
        )

    @app.post("/incidents/{event_id}/insight")
    def incident_insight(request: Request, event_id: str) -> Response:
        """Make an Incident Insight by hand — the way out when Gemini was down during the run."""
        lang = get_lang(request)
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
                auth.flash(request, t("flash.insight_failed", lang=lang, exc=exc), "red")
            else:
                auth.flash(request, t("flash.insight_success", lang=lang), "green")
        return RedirectResponse(f"/incidents/{event_id}#insight", status_code=303)

    @app.post("/incidents/{event_id}/triage")
    def incident_triage(
        request: Request, event_id: str, status: str = Form(""), notes: str | None = Form(None)
    ) -> Response:
        lang = get_lang(request)
        if not auth.is_logged_in(request):
            return auth.login_redirect(f"/incidents/{event_id}")
        from afs.triage import update_triage

        try:
            triage_status = TriageStatus(status) if status else None
        except ValueError:
            auth.flash(request, t("flash.triage_unknown", lang=lang), "red")
            return RedirectResponse(f"/incidents/{event_id}", status_code=303)
        try:
            with session_scope() as s:
                update_triage(s, event_id, status=triage_status, notes=notes)
        except KeyError:
            return render(request, "not_found.html", {"event_id": event_id}, status_code=404)
        auth.flash(request, t("flash.triage_saved", lang=lang), "green")
        return RedirectResponse(f"/incidents/{event_id}#triage", status_code=303)

    @app.get("/backtest", response_class=HTMLResponse)
    def backtest(request: Request) -> Response:
        lang = get_lang(request)
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
                            {"result": r, "dots": queries.rule_dots(r.findings, lang=lang)} for r in results
                        ],
                        "claims": [
                            {"event": e, "sentence": claim_sentence(results, e, lang=lang)} for e in case.events
                        ]
                        if results
                        else [],
                        "chart": _backtest_chart(results, case.events, lang=lang),
                    }
                )
            return render(request, "backtest.html", {"views": views})

    @app.get("/logs", response_class=HTMLResponse)
    def logs(request: Request) -> Response:
        lang = get_lang(request)
        with session_scope() as s:
            runs = queries.audit_runs(s)
            return render(
                request,
                "logs.html",
                {"runs": [{"run": r, "evaluations": queries.run_evaluations(s, r.id, lang=lang)} for r in runs]},
            )

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request, next: str = "/") -> Response:
        return render(request, "login.html", {"next": auth.safe_next(next), "error": None})

    @app.post("/login")
    def login_submit(request: Request, password: str = Form(""), next: str = Form("/")) -> Response:
        lang = get_lang(request)
        if not auth.check_password(password, settings.admin_password):
            return render(
                request, "login.html", {"next": auth.safe_next(next), "error": t("login.error", lang=lang)}, status_code=401
            )
        auth.login(request)
        auth.flash(request, t("flash.login_success", lang=lang), "green")
        return RedirectResponse(auth.safe_next(next), status_code=303)

    @app.post("/logout")
    def logout(request: Request) -> Response:
        lang = get_lang(request)
        auth.logout(request)
        auth.flash(request, t("flash.logout_success", lang=lang), "gray")
        return RedirectResponse("/", status_code=303)

    return app


app = create_app()

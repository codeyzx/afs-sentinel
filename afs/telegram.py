"""Telegram notifications (docs/system-rules.md §7). Messages use HTML parse mode."""

from __future__ import annotations

import html
import json
import logging
from datetime import date, datetime
from typing import Any, Sequence

import httpx

from afs.config import WIB, get_settings
from afs.domain import FindingStatus, RuleFinding, RunTrigger, Severity, quarter_label
from afs.labels import SEVERITY_EMOJI, SEVERITY_LABEL, finding_sort_key

log = logging.getLogger(__name__)


def quiet_http_logging() -> None:
    """httpx logs every request URL at INFO, and the Telegram URL embeds the bot token.
    Entry points call this so the token never reaches Heroku's log drain."""
    logging.getLogger("httpx").setLevel(logging.WARNING)

MAX_FINDINGS = 3
OPEN_INCIDENT_BUTTON = "Buka Incident"
# Marks the one line an LLM wrote, so it can never be mistaken for a rule output (§7.1).
INSIGHT_PREFIX = "\U0001f916"
LOW_CONFIDENCE_LINE = "⚠️ Low Confidence: rule yang bisa dinilai kurang dari separuh bobot."

TRIGGER_LABEL = {RunTrigger.SCHEDULER: "Otomatis · sistem", RunTrigger.MANUAL: "Manual · analis"}
DAY_NAMES = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def _esc(text: object) -> str:
    return html.escape(str(text), quote=False)


def format_score(score: float) -> str:
    """75.0 -> '75', 67.5 -> '67,5'."""
    rounded = round(score, 1)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.1f}".replace(".", ",")


def format_wib(moment: datetime) -> str:
    """Aware datetime -> 'Sabtu 20 Sep 2026, 08:00 WIB'."""
    local = moment.astimezone(WIB)
    return (
        f"{DAY_NAMES[local.weekday()]} {local.day} {MONTH_NAMES[local.month - 1]} {local.year}, "
        f"{local:%H:%M} WIB"
    )


def incident_url(event_id: str) -> str:
    return f"{get_settings().base_web_url.rstrip('/')}/incidents/{event_id}"


def format_incident_message(
    *,
    event_id: str,
    symbol: str,
    company_name: str,
    report_date: date,
    score: float,
    severity: Severity,
    low_confidence: bool,
    severity_reason: str | None,
    findings: Sequence[RuleFinding],
    escalated_from: Severity | None,
    insight_line: str | None = None,
) -> str:
    """event_id is part of the signature for symmetry with the button URL; it is not shown in the text."""
    ticker = symbol.removesuffix(".JK")
    lines = [
        f"{SEVERITY_EMOJI[severity]} <b>{SEVERITY_LABEL[severity]} · {_esc(ticker)} — {_esc(company_name)}</b>",
        f"Skor {format_score(score)}/100 · Laporan {quarter_label(report_date)}",
    ]
    if escalated_from is not None:
        lines.append(f"Escalation: {SEVERITY_LABEL[escalated_from]} → {SEVERITY_LABEL[severity]}")
    if low_confidence:
        lines.append(LOW_CONFIDENCE_LINE)
    if severity_reason:
        lines.append(f"ℹ️ {_esc(severity_reason)}")

    if insight_line:
        lines.append("")
        lines.append(f"{INSIGHT_PREFIX} <i>{_esc(insight_line)}</i>")

    flagged = sorted(
        (f for f in findings if f.status in (FindingStatus.RED_FLAG, FindingStatus.WARNING) and f.headline),
        key=lambda f: finding_sort_key(f.rule_id, f.status),
    )[:MAX_FINDINGS]
    if flagged:
        lines.append("")
        lines.extend(f"• {_esc(f.headline)}" for f in flagged)
    return "\n".join(lines)


def format_run_summary(
    *,
    started_at: datetime,
    trigger: RunTrigger,
    emiten_scanned: int,
    incidents_new: int,
    escalations: int,
    emiten_failed: int,
    credits_used: int,
) -> str:
    return "\n".join(
        [
            f"✅ Audit Run {format_wib(started_at)} ({TRIGGER_LABEL[RunTrigger(trigger)]})",
            f"{emiten_scanned} emiten dipindai · {incidents_new} Incident baru · "
            f"{escalations} Escalation · {emiten_failed} gagal",
            f"Kredit API terpakai: {credits_used}",
        ]
    )


def format_run_failure(*, started_at: datetime, trigger: RunTrigger, reason: str) -> str:
    """§7.2 failure format; trigger is accepted for call-site symmetry but not shown (spec has no trigger)."""
    return f"❌ Audit Run GAGAL — {format_wib(started_at)}\nAlasan: {_esc(reason)}"


def send_message(
    text: str,
    button: tuple[str, str] | None = None,
    client: httpx.Client | None = None,
) -> bool:
    """Send to the Analyst's chat. Never raises; returns False when not configured or on failure."""
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        log.warning("Telegram tidak dikonfigurasi; pesan tidak dikirim")
        return False

    payload: dict[str, object] = {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if button is not None:
        label, url = button
        payload["reply_markup"] = {"inline_keyboard": [[{"text": label, "url": url}]]}

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    own_client = client is None
    http = client or httpx.Client(timeout=15.0)
    try:
        resp = http.post(url, json=payload)
        if resp.status_code != 200:
            log.warning("Telegram sendMessage gagal: HTTP %s", resp.status_code)
            return False
        return True
    except httpx.HTTPError as exc:
        log.warning("Telegram sendMessage gagal: %s", type(exc).__name__)  # never log the URL (contains token)
        return False
    finally:
        if own_client:
            http.close()


def send_voice(
    voice_bytes: bytes,
    caption: str | None = None,
    button: tuple[str, str] | None = None,
    client: httpx.Client | None = None,
    filename: str = "briefing.mp3",
) -> bool:
    """Send an audio voice note to the Analyst's Telegram chat. Never raises."""
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        log.warning("Telegram tidak dikonfigurasi; voice note tidak dikirim")
        return False

    data: dict[str, Any] = {"chat_id": settings.telegram_chat_id}
    if caption:
        data["caption"] = caption
        data["parse_mode"] = "HTML"
    if button is not None:
        label, url = button
        data["reply_markup"] = json.dumps({"inline_keyboard": [[{"text": label, "url": url}]]})

    files = {"voice": (filename, voice_bytes, "audio/mpeg")}

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendVoice"
    own_client = client is None
    http = client or httpx.Client(timeout=30.0)
    try:
        resp = http.post(url, data=data, files=files)
        if resp.status_code != 200:
            log.warning("Telegram sendVoice gagal: HTTP %s", resp.status_code)
            return False
        return True
    except httpx.HTTPError as exc:
        log.warning("Telegram sendVoice gagal: %s", type(exc).__name__)
        return False
    finally:
        if own_client:
            http.close()

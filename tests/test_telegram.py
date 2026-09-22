from __future__ import annotations

import json
from datetime import date, datetime, timezone

import httpx
import pytest

from afs import telegram
from afs.config import get_settings
from afs.domain import FindingStatus, RuleFinding, RunTrigger, Severity


def finding(rule_id: str, status: FindingStatus, headline: str) -> RuleFinding:
    return RuleFinding(rule_id=rule_id, status=status, value=None, thresholds={}, inputs={}, headline=headline)


FINDINGS = [
    finding("EARNINGS_WITHOUT_DIVIDEND", FindingStatus.WARNING, "Untung tapi tidak membagi dividen."),
    finding("ALTMAN_Z_ADAPTED", FindingStatus.WARNING, "Skor Altman 2,1 — zona abu-abu kesulitan keuangan."),
    finding("SLOAN_ACCRUAL", FindingStatus.RED_FLAG, "13,8% dari aset tercatat sebagai laba yang belum menjadi uang tunai."),
    finding("BENEISH_ADAPTED", FindingStatus.PASS, "Aman."),
    finding("INSIDER_SELLING", FindingStatus.INSUFFICIENT_DATA, "Tak bisa dinilai."),
    finding("EARNINGS_CASH_DIVERGENCE", FindingStatus.RED_FLAG, "Laba naik 52% dibanding tahun lalu, tapi kas operasi turun 28%."),
]


def base_kwargs(**over):
    kw = dict(
        event_id="AFS-2025-Q3-0007",
        symbol="EMTK.JK",
        company_name="Elang Mahkota Teknologi",
        report_date=date(2025, 9, 30),
        score=75.0,
        severity=Severity.CRITICAL,
        low_confidence=False,
        severity_reason=None,
        findings=FINDINGS,
        escalated_from=None,
    )
    kw.update(over)
    return kw


def test_new_incident_message():
    assert telegram.format_incident_message(**base_kwargs()) == (
        "🔴 <b>Kritis · EMTK — Elang Mahkota Teknologi</b>\n"
        "Skor 75/100 · Laporan 2025-Q3\n"
        "\n"
        "• 13,8% dari aset tercatat sebagai laba yang belum menjadi uang tunai.\n"
        "• Laba naik 52% dibanding tahun lalu, tapi kas operasi turun 28%.\n"
        "• Skor Altman 2,1 — zona abu-abu kesulitan keuangan."
    )


def test_escalation_message():
    text = telegram.format_incident_message(**base_kwargs(escalated_from=Severity.MODERATE))
    assert text.splitlines()[2] == "Escalation: Sedang → Kritis"


def test_low_confidence_and_reason_message_escapes_html():
    text = telegram.format_incident_message(
        **base_kwargs(
            score=42.5,
            severity=Severity.MODERATE,
            low_confidence=True,
            severity_reason="Minimal Sedang karena Altman berstatus Bahaya",
            company_name="A & B <Tbk>",
            findings=[finding("ALTMAN_Z_ADAPTED", FindingStatus.RED_FLAG, "Z < 1,8")],
        )
    )
    assert text == (
        "🟡 <b>Sedang · EMTK — A &amp; B &lt;Tbk&gt;</b>\n"
        "Skor 42,5/100 · Laporan 2025-Q3\n"
        f"{telegram.LOW_CONFIDENCE_LINE}\n"
        "ℹ️ Minimal Sedang karena Altman berstatus Bahaya\n"
        "\n"
        "• Z &lt; 1,8"
    )


def test_incident_url(monkeypatch):
    monkeypatch.setattr(get_settings(), "base_web_url", "https://afs.example/")
    assert telegram.incident_url("AFS-2025-Q3-0007") == "https://afs.example/incidents/AFS-2025-Q3-0007"


def test_run_summary():
    started = datetime(2026, 9, 19, 1, 0, tzinfo=timezone.utc)
    assert telegram.format_run_summary(
        started_at=started,
        trigger=RunTrigger.SCHEDULER,
        emiten_scanned=30,
        incidents_new=2,
        escalations=1,
        emiten_failed=0,
        credits_used=12,
    ) == (
        "✅ Audit Run Sabtu 19 Sep 2026, 08:00 WIB (Otomatis · sistem)\n"
        "30 emiten dipindai · 2 Incident baru · 1 Escalation · 0 gagal\n"
        "Kredit API terpakai: 12"
    )


def test_run_failure():
    started = datetime(2026, 9, 19, 1, 0, tzinfo=timezone.utc)
    assert telegram.format_run_failure(started_at=started, trigger=RunTrigger.MANUAL, reason="DB <down>") == (
        "❌ Audit Run GAGAL — Sabtu 19 Sep 2026, 08:00 WIB\nAlasan: DB &lt;down&gt;"
    )


@pytest.fixture
def tg_settings(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "telegram_bot_token", "TOKEN")
    monkeypatch.setattr(s, "telegram_chat_id", "42")
    return s


def test_send_message_noop_without_token(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "telegram_bot_token", "")
    monkeypatch.setattr(s, "telegram_chat_id", "")

    def boom(req):
        raise AssertionError("must not call Telegram")

    client = httpx.Client(transport=httpx.MockTransport(boom))
    assert telegram.send_message("hi", client=client) is False


def test_send_message_payload_with_button(tg_settings):
    seen: list[httpx.Request] = []

    def handler(req):
        seen.append(req)
        return httpx.Response(200, json={"ok": True})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    assert telegram.send_message("<b>x</b>", button=("Buka Incident", "https://afs/i/1"), client=client)
    assert str(seen[0].url) == "https://api.telegram.org/botTOKEN/sendMessage"
    body = json.loads(seen[0].content)
    assert body == {
        "chat_id": "42",
        "text": "<b>x</b>",
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": {"inline_keyboard": [[{"text": "Buka Incident", "url": "https://afs/i/1"}]]},
    }


def test_send_message_failure_returns_false(tg_settings):
    def handler(req):
        raise httpx.ConnectError("down")

    assert telegram.send_message("x", client=httpx.Client(transport=httpx.MockTransport(handler))) is False
    bad = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(400)))
    assert telegram.send_message("x", client=bad) is False


def test_quiet_http_logging_hides_the_url_that_carries_the_bot_token():
    """httpx logs request URLs at INFO, and the Telegram URL embeds the bot token."""
    import logging

    from afs.telegram import quiet_http_logging

    logging.getLogger("httpx").setLevel(logging.INFO)
    quiet_http_logging()
    assert not logging.getLogger("httpx").isEnabledFor(logging.INFO)


def test_send_voice_payload_with_button(tg_settings):
    seen: list[httpx.Request] = []

    def handler(req):
        seen.append(req)
        return httpx.Response(200, json={"ok": True})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    ok = telegram.send_voice(
        b"fake-audio-bytes",
        caption="🎧 Audio Briefing",
        button=("Buka Incident", "https://afs/i/1"),
        client=client,
    )
    assert ok is True
    assert str(seen[0].url) == "https://api.telegram.org/botTOKEN/sendVoice"
    assert seen[0].headers["content-type"].startswith("multipart/form-data")
    assert b"fake-audio-bytes" in seen[0].content


def test_send_voice_not_configured(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "telegram_bot_token", "")
    monkeypatch.setattr(s, "telegram_chat_id", "")
    assert telegram.send_voice(b"data") is False


def test_send_voice_failure_returns_false(tg_settings):
    def handler(req):
        raise httpx.ConnectError("network down")

    assert telegram.send_voice(b"x", client=httpx.Client(transport=httpx.MockTransport(handler))) is False
    bad = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(400)))
    assert telegram.send_voice(b"x", client=bad) is False

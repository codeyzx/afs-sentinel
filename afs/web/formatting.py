"""Display formatting: WIB datetimes, numbers, and finding values with i18n support."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from afs.config import WIB
from afs.domain import FindingStatus, Severity, TriageStatus, quarter_label
from afs.labels import FINDING_LABEL, FINDING_TONE, RULE_META, SEVERITY_LABEL, SEVERITY_TONE, TRIAGE_LABEL
from afs.web.i18n import (
    DAYS_I18N,
    DEFAULT_LANG,
    FINDING_LABEL_I18N,
    MONTHS_I18N,
    MONTHS_LONG_I18N,
    RULE_LIMITATIONS_I18N,
    RULE_TRANSLATIONS,
    RUN_STATUS_LABEL_I18N,
    SEVERITY_LABEL_I18N,
    TRIAGE_LABEL_I18N,
    TRIGGER_LABEL_I18N,
    t,
)

MONTHS = MONTHS_I18N["id"]
MONTHS_LONG = MONTHS_LONG_I18N["id"]
DAYS = DAYS_I18N["id"]


def to_wib(dt: datetime) -> datetime:
    """Stored datetimes are UTC; SQLite drops tzinfo, so naive values are read as UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(WIB)


def fmt_wib(dt: datetime | None, with_day: bool = False, lang: str = DEFAULT_LANG) -> str:
    """Format datetime in WIB timezone with locale support.
    e.g. 'Sabtu, 20 Sep 2026, 08:00 WIB' (id) or 'Saturday, 20 Sep 2026, 08:00 WIB' (en).
    """
    if dt is None:
        return "—"
    w = to_wib(dt)
    months = MONTHS_I18N.get(lang, MONTHS_I18N[DEFAULT_LANG])
    days = DAYS_I18N.get(lang, DAYS_I18N[DEFAULT_LANG])
    text = f"{w.day} {months[w.month - 1]} {w.year}, {w:%H:%M} WIB"
    return f"{days[w.weekday()]}, {text}" if with_day else text


def fmt_date(d: date | None, lang: str = DEFAULT_LANG) -> str:
    """-> '12 Mei 2023' (id) or '12 May 2023' (en)."""
    if d is None:
        return "—"
    months_long = MONTHS_LONG_I18N.get(lang, MONTHS_LONG_I18N[DEFAULT_LANG])
    return f"{d.day} {months_long[d.month - 1]} {d.year}"


def fmt_num(value: float | int | None, decimals: int = 0, lang: str = DEFAULT_LANG) -> str:
    """Format numbers according to locale.
    id: 12345.678 -> '12.345,68'
    en: 12345.678 -> '12,345.68'
    """
    if value is None:
        return "—"
    text = f"{value:,.{decimals}f}"
    if lang == "en":
        return text
    # Default Indonesian formatting: dot for thousands, comma for decimals
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_score(score: float | None, lang: str = DEFAULT_LANG) -> str:
    return "—" if score is None else fmt_num(score, 1, lang=lang)


def fmt_duration(start: datetime | None, end: datetime | None, lang: str = DEFAULT_LANG) -> str:
    if start is None or end is None:
        return "—"
    seconds = int((to_wib(end) - to_wib(start)).total_seconds())
    minutes, secs = divmod(max(seconds, 0), 60)
    if lang == "en":
        return f"{minutes}m {secs}s" if minutes else f"{secs}s"
    return f"{minutes} mnt {secs} dtk" if minutes else f"{secs} dtk"


def ticker(symbol: str) -> str:
    return symbol.removesuffix(".JK")


def fmt_period(d: date | None) -> str:
    return "—" if d is None else quarter_label(d)


def fmt_finding_value(rule_id: str, value: Any, lang: str = DEFAULT_LANG) -> str:
    """The card's main number, formatted per rule; unknown rules fall back to a plain number."""
    if value is None or isinstance(value, bool):
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    match rule_id:
        case "SLOAN_ACCRUAL" | "EARNINGS_CASH_DIVERGENCE":
            return fmt_num(v * 100, 1, lang=lang) + "%"
        case "ALTMAN_Z_ADAPTED":
            return "Z = " + fmt_num(v, 2, lang=lang)
        case "BENEISH_ADAPTED":
            if lang == "en":
                return f"{int(v)} of 3 indices"
            return f"{int(v)} dari 3 indeks"
        case "INSIDER_SELLING":
            return fmt_num(v, 2, lang=lang) + "%"
        case _:
            return fmt_num(v, 2, lang=lang)


def fmt_value(value: Any, lang: str = DEFAULT_LANG) -> str:
    """Generic rendering for raw input values."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return t("common.yes" if value else "common.no", lang=lang)
    if isinstance(value, int):
        return fmt_num(value, lang=lang)
    if isinstance(value, float):
        dec = 0 if abs(value) >= 1000 else 4 if abs(value) < 1 else 2
        return fmt_num(value, dec, lang=lang)
    return str(value)


def next_scheduled_run(last_success: datetime | None, interval_days: int | None = None) -> datetime | None:
    """Display wrapper over afs.schedule.next_due, in WIB. None = no successful run to count from."""
    from afs.schedule import next_due

    upcoming = next_due(last_success, interval_days)
    return None if upcoming is None else to_wib(upcoming)


def _enum_or_none(cls: Any, value: Any) -> Any:
    try:
        return cls(value)
    except ValueError:
        return None


def finding_label(status: str, lang: str = DEFAULT_LANG) -> str:
    s = _enum_or_none(FindingStatus, status)
    key = s.name if s else str(status)
    if key in FINDING_LABEL_I18N:
        return FINDING_LABEL_I18N[key].get(lang, FINDING_LABEL_I18N[key][DEFAULT_LANG])
    return FINDING_LABEL.get(s, status) if s else status


def finding_tone(status: str) -> str:
    s = _enum_or_none(FindingStatus, status)
    return FINDING_TONE[s] if s else "gray"


def severity_label(severity: str | None, lang: str = DEFAULT_LANG) -> str:
    s = _enum_or_none(Severity, severity) if severity else None
    if s is None:
        return t("common.cannot_assess", lang=lang)
    key = s.name
    if key in SEVERITY_LABEL_I18N:
        return SEVERITY_LABEL_I18N[key].get(lang, SEVERITY_LABEL_I18N[key][DEFAULT_LANG])
    return SEVERITY_LABEL.get(s, "Tak bisa dinilai")


def severity_tone(severity: str | None) -> str:
    s = _enum_or_none(Severity, severity) if severity else None
    return SEVERITY_TONE[s] if s else "gray"


def triage_label(status: str | None, lang: str = DEFAULT_LANG) -> str:
    s = _enum_or_none(TriageStatus, status) if status else None
    if s is None:
        return status or "—"
    key = s.name
    if key in TRIAGE_LABEL_I18N:
        return TRIAGE_LABEL_I18N[key].get(lang, TRIAGE_LABEL_I18N[key][DEFAULT_LANG])
    return TRIAGE_LABEL.get(s, status or "—")


def rule_name(rule_id: str, lang: str = DEFAULT_LANG) -> str:
    trans = RULE_TRANSLATIONS.get(rule_id, {}).get(lang)
    if trans and "name" in trans:
        return trans["name"]
    meta = RULE_META.get(rule_id)
    return meta.name if meta else rule_id


def rule_subtitle(rule_id: str, lang: str = DEFAULT_LANG) -> str:
    trans = RULE_TRANSLATIONS.get(rule_id, {}).get(lang)
    if trans and "subtitle" in trans:
        return trans["subtitle"]
    meta = RULE_META.get(rule_id)
    return meta.subtitle if meta else ""


RULE_LIMITATIONS: dict[str, str] = {
    k: v["id"] for k, v in RULE_LIMITATIONS_I18N.items()
}


def rule_limitation(rule_id: str, lang: str = DEFAULT_LANG) -> str:
    """Mandatory limitation disclosure per rule (docs/system-rules.md §10)."""
    entry = RULE_LIMITATIONS_I18N.get(rule_id)
    if entry:
        return entry.get(lang, entry.get(DEFAULT_LANG, ""))
    return ""


TRIGGER_LABEL = {k: v["id"] for k, v in TRIGGER_LABEL_I18N.items()}
TRIGGER_ICON = {"SCHEDULER": "\u2699", "MANUAL": "\u261b"}


def trigger_label(trigger: str | None, lang: str = DEFAULT_LANG) -> str:
    entry = TRIGGER_LABEL_I18N.get(trigger or "")
    if entry:
        return entry.get(lang, entry.get(DEFAULT_LANG, trigger or "—"))
    return trigger or "—"


def trigger_icon(trigger: str | None) -> str:
    return TRIGGER_ICON.get(trigger or "", "")


RUN_STATUS_LABEL = {k: v["id"] for k, v in RUN_STATUS_LABEL_I18N.items()}
RUN_STATUS_TONE = {"SUCCESS": "green", "FAILED": "red", "RUNNING": "yellow"}


def run_status_label(status: str | None, lang: str = DEFAULT_LANG) -> str:
    entry = RUN_STATUS_LABEL_I18N.get(status or "")
    if entry:
        return entry.get(lang, entry.get(DEFAULT_LANG, status or "—"))
    return status or "—"


def run_status_tone(status: str | None) -> str:
    return RUN_STATUS_TONE.get(status or "", "yellow")

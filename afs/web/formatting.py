"""Indonesian display formatting: WIB datetimes, numbers, and finding values."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from afs.config import WIB
from afs.domain import FindingStatus, Severity, TriageStatus, quarter_label
from afs.labels import FINDING_LABEL, FINDING_TONE, RULE_META, SEVERITY_LABEL, SEVERITY_TONE, TRIAGE_LABEL

MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
MONTHS_LONG = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]
DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def to_wib(dt: datetime) -> datetime:
    """Stored datetimes are UTC; SQLite drops tzinfo, so naive values are read as UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(WIB)


def fmt_wib(dt: datetime | None, with_day: bool = False) -> str:
    """-> 'Sabtu, 20 Sep 2026, 08:00 WIB'."""
    if dt is None:
        return "—"
    w = to_wib(dt)
    text = f"{w.day} {MONTHS[w.month - 1]} {w.year}, {w:%H:%M} WIB"
    return f"{DAYS[w.weekday()]}, {text}" if with_day else text


def fmt_date(d: date | None) -> str:
    """-> '12 Mei 2023'."""
    if d is None:
        return "—"
    return f"{d.day} {MONTHS_LONG[d.month - 1]} {d.year}"


def fmt_num(value: float | int | None, decimals: int = 0) -> str:
    """12345.678 -> '12.345,68' (Indonesian separators)."""
    if value is None:
        return "—"
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_score(score: float | None) -> str:
    return "—" if score is None else fmt_num(score, 1)


def fmt_duration(start: datetime | None, end: datetime | None) -> str:
    if start is None or end is None:
        return "—"
    seconds = int((to_wib(end) - to_wib(start)).total_seconds())
    minutes, secs = divmod(max(seconds, 0), 60)
    return f"{minutes} mnt {secs} dtk" if minutes else f"{secs} dtk"


def ticker(symbol: str) -> str:
    return symbol.removesuffix(".JK")


def fmt_period(d: date | None) -> str:
    return "—" if d is None else quarter_label(d)


def fmt_finding_value(rule_id: str, value: Any) -> str:
    """The card's main number, formatted per rule; unknown rules fall back to a plain number."""
    if value is None or isinstance(value, bool):
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    match rule_id:
        case "SLOAN_ACCRUAL" | "EARNINGS_CASH_DIVERGENCE":
            return fmt_num(v * 100, 1) + "%"
        case "ALTMAN_Z_ADAPTED":
            return "Z = " + fmt_num(v, 2)
        case "BENEISH_ADAPTED":
            return f"{int(v)} dari 3 indeks"
        case "INSIDER_SELLING":
            return fmt_num(v, 2) + "%"
        case _:
            return fmt_num(v, 2)


def fmt_value(value: Any) -> str:
    """Generic rendering for raw input values."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "ya" if value else "tidak"
    if isinstance(value, int):
        return fmt_num(value)
    if isinstance(value, float):
        return fmt_num(value, 0 if abs(value) >= 1000 else 4 if abs(value) < 1 else 2)
    return str(value)


def next_scheduled_run(now: datetime) -> datetime:
    """Next Saturday 08:00 WIB strictly after `now` (§6.1)."""
    w = to_wib(now)
    candidate = w.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=(5 - w.weekday()) % 7)
    if candidate <= w:
        candidate += timedelta(days=7)
    return candidate


def _enum_or_none(cls, value):
    try:
        return cls(value)
    except ValueError:
        return None


def finding_label(status: str) -> str:
    s = _enum_or_none(FindingStatus, status)
    return FINDING_LABEL[s] if s else status


def finding_tone(status: str) -> str:
    s = _enum_or_none(FindingStatus, status)
    return FINDING_TONE[s] if s else "gray"


def severity_label(severity: str | None) -> str:
    s = _enum_or_none(Severity, severity) if severity else None
    return SEVERITY_LABEL[s] if s else "Tak bisa dinilai"


def severity_tone(severity: str | None) -> str:
    s = _enum_or_none(Severity, severity) if severity else None
    return SEVERITY_TONE[s] if s else "gray"


def triage_label(status: str | None) -> str:
    s = _enum_or_none(TriageStatus, status) if status else None
    return TRIAGE_LABEL[s] if s else (status or "—")


def rule_name(rule_id: str) -> str:
    meta = RULE_META.get(rule_id)
    return meta.name if meta else rule_id


def rule_subtitle(rule_id: str) -> str:
    meta = RULE_META.get(rule_id)
    return meta.subtitle if meta else ""


RULE_LIMITATIONS: dict[str, str] = {
    "ALTMAN_Z_ADAPTED": (
        "Versi adaptasi: laba ditahan tidak tersedia di API sehingga diganti total ekuitas; "
        "ambang dibuat lebih ketat untuk mengimbangi."
    ),
    "BENEISH_ADAPTED": "Hanya 3 dari 8 indeks Beneish (GMI, SGI, LVGI); bukan M-Score utuh.",
    "INSIDER_SELLING": (
        "\"Orang dalam\" di API mencakup pemegang saham ≥5%; riwayat hanya ±1 tahun; persentase dibulatkan "
        "2 desimal sehingga transaksi sangat kecil tercatat 0%."
    ),
    "EARNINGS_WITHOUT_DIVIDEND": "Tidak bisa membedakan dividen tunai dan dividen saham.",
}


def rule_limitation(rule_id: str) -> str:
    """Mandatory limitation disclosure per rule (docs/system-rules.md §10)."""
    return RULE_LIMITATIONS.get(rule_id, "")

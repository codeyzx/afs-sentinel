"""Single source of display vocabulary (docs/system-rules.md §3 and §9.1), shared by rules, Telegram and web."""

from __future__ import annotations

from dataclasses import dataclass

from afs.domain import FindingStatus, Severity, TriageStatus


@dataclass(frozen=True)
class RuleMeta:
    rule_id: str
    name: str
    subtitle: str
    weight: float
    is_core: bool


RULE_META: dict[str, RuleMeta] = {
    m.rule_id: m
    for m in [
        RuleMeta("SLOAN_ACCRUAL", "Sloan Accrual Ratio", "Seberapa banyak laba yang bukan uang tunai", 25, True),
        RuleMeta("EARNINGS_CASH_DIVERGENCE", "Divergensi Laba–Kas", "Laba naik, tapi kas operasi turun", 25, True),
        RuleMeta("ALTMAN_Z_ADAPTED", "Altman Z'' (Adapted)", "Risiko kesulitan keuangan", 20, True),
        RuleMeta("BENEISH_ADAPTED", "Beneish (Adapted)", "Tanda tekanan untuk memoles laporan", 15, False),
        RuleMeta("INSIDER_SELLING", "Penjualan Orang Dalam", "Orang dalam/pemegang saham utama menjual", 10, False),
        RuleMeta("EARNINGS_WITHOUT_DIVIDEND", "Laba tanpa Dividen", "Untung, tapi tidak membagi kas", 5, False),
    ]
}

CORE_RULE_IDS = frozenset(m.rule_id for m in RULE_META.values() if m.is_core)

FINDING_LABEL = {
    FindingStatus.PASS: "Aman",
    FindingStatus.WARNING: "Waspada",
    FindingStatus.RED_FLAG: "Bahaya",
    FindingStatus.INSUFFICIENT_DATA: "Tak bisa dinilai",
}

SEVERITY_LABEL = {
    Severity.LOW: "Rendah",
    Severity.MODERATE: "Sedang",
    Severity.CRITICAL: "Kritis",
}

SEVERITY_EMOJI = {Severity.LOW: "🟢", Severity.MODERATE: "🟡", Severity.CRITICAL: "🔴"}

TRIAGE_LABEL = {
    TriageStatus.UNTRIAGED: "Belum ditinjau",
    TriageStatus.INVESTIGATING: "Sedang diperiksa",
    TriageStatus.RESOLVED: "Sudah ditindaklanjuti",
    TriageStatus.DISMISSED: "Alarm palsu",
}

# Tailwind-agnostic tone keys: "green" | "yellow" | "red" | "gray"
FINDING_TONE = {
    FindingStatus.PASS: "green",
    FindingStatus.WARNING: "yellow",
    FindingStatus.RED_FLAG: "red",
    FindingStatus.INSUFFICIENT_DATA: "gray",
}
SEVERITY_TONE = {Severity.LOW: "green", Severity.MODERATE: "yellow", Severity.CRITICAL: "red"}

# Display order for findings: Bahaya -> Waspada -> Aman -> Tak bisa dinilai, then weight desc.
FINDING_ORDER = {
    FindingStatus.RED_FLAG: 0,
    FindingStatus.WARNING: 1,
    FindingStatus.PASS: 2,
    FindingStatus.INSUFFICIENT_DATA: 3,
}


def finding_sort_key(rule_id: str, status: FindingStatus) -> tuple[int, float]:
    meta = RULE_META.get(rule_id)
    return (FINDING_ORDER[status], -(meta.weight if meta else 0))


def format_idr_pct(value: float, decimals: int = 1) -> str:
    """0.138 -> '13,8%' (Indonesian decimal comma)."""
    return f"{value * 100:.{decimals}f}%".replace(".", ",")

"""DEV ONLY: fill the configured database with clearly fake demo data for the web app.

    uv run python -m afs.devseed           # seed if the database is empty
    uv run python -m afs.devseed --reset   # drop all tables, recreate, seed

Every number here is invented for UI development; none of it comes from the Sectors API.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from afs import db
from afs.domain import (
    FindingStatus as S,
    IncidentEventKind,
    RunStatus,
    RunTrigger,
    TriageStatus,
    quarter_label,
)
from afs.labels import RULE_META
from afs.models import ApiCache, AuditRun, BacktestResult, Emiten, EmitenEvaluation, Incident, IncidentEvent, IncidentInsight

NOTE = "DATA DEMO (devseed) — bukan data asli."
REPORT_T = date(2026, 6, 30)
QUARTER_DATES = [date(2025, 6, 30), date(2025, 9, 30), date(2025, 12, 31), date(2026, 3, 31), date(2026, 6, 30)]
QUARTERLY_ENDPOINT = "/v2/financials/quarterly/{symbol}/"

EMITEN = [
    ("EMTK.JK", "Elang Mahkota Teknologi (demo)", "Technology", "Software & IT Services"),
    ("WSKT.JK", "Waskita Karya (demo)", "Infrastructures", "Heavy Constructions & Civil Engineering"),
    ("GOTO.JK", "GoTo Gojek Tokopedia (demo)", "Technology", "Software & IT Services"),
    ("ADRO.JK", "Alamtri Resources (demo)", "Energy", "Coal"),
    ("ASII.JK", "Astra International (demo)", "Industrials", "Multi-sector Holdings"),
    ("TLKM.JK", "Telkom Indonesia (demo)", "Infrastructures", "Telecommunication"),
    ("UNVR.JK", "Unilever Indonesia (demo)", "Consumer Non-Cyclicals", "Household Products"),
    ("INDF.JK", "Indofood Sukses Makmur (demo)", "Consumer Non-Cyclicals", "Processed Foods"),
    ("BUMI.JK", "Bumi Resources (demo)", "Energy", "Coal"),
    ("SRIL.JK", "Sri Rejeki Isman (demo)", "Consumer Cyclicals", "Apparel & Textile"),
]


def finding(
    rule_id: str, status: S, value: float | None, headline: str, *, missing: str | None = None, **extra: Any
) -> dict[str, Any]:
    thresholds: dict[str, Any] = {
        "SLOAN_ACCRUAL": {"red_flag": "> 10%", "warning": "> 5%"},
        "EARNINGS_CASH_DIVERGENCE": {"red_flag": "ΔLaba ≥ +25% dan ΔOCF ≤ −15%", "warning": "ΔLaba ≥ +10% dan ΔOCF ≤ 0%"},
        "ALTMAN_Z_ADAPTED": {"red_flag": "Z < 1,8", "warning": "Z < 2,9"},
        "BENEISH_ADAPTED": {"GMI": "> 1,19", "SGI": "> 1,61", "LVGI": "> 1,11"},
        "INSIDER_SELLING": {"red_flag": "≥ 2%", "warning": "≥ 0,5%", "window_days": 90},
        "EARNINGS_WITHOUT_DIVIDEND": {"lookback_days": 365},
    }[rule_id]
    formulas = {
        "SLOAN_ACCRUAL": "(TTM(earnings) − TTM(operating_cash_flow)) / rata-rata(total_assets t, t-4)",
        "EARNINGS_CASH_DIVERGENCE": "ΔLaba = (earnings t − t-4)/|t-4|; ΔOCF = (OCF t − t-4)/|t-4|",
        "ALTMAN_Z_ADAPTED": "Z = 6,56·X1 + 3,26·X2 + 6,72·X3 + 1,05·X4",
        "BENEISH_ADAPTED": "Hitung GMI, SGI, LVGI (t vs t-4); jumlah yang melewati ambang",
        "INSIDER_SELLING": "Σ% jual − Σ% beli, filing 90 hari terakhir",
        "EARNINGS_WITHOUT_DIVIDEND": "TTM laba > 0, TTM OCF > 0, tanpa ex_date 365 hari",
    }
    endpoint = "/v2/filings/" if rule_id == "INSIDER_SELLING" else QUARTERLY_ENDPOINT
    values = []
    if rule_id not in ("INSIDER_SELLING",) and status is not S.INSUFFICIENT_DATA:
        values = [
            {"field": "earnings", "report_date": REPORT_T.isoformat(), "value": 412_500_000_000.0},
            {"field": "operating_cash_flow", "report_date": REPORT_T.isoformat(), "value": -96_300_000_000.0},
            {"field": "total_assets", "report_date": REPORT_T.isoformat(), "value": 41_870_000_000_000.0},
        ]
    return {
        "rule_id": rule_id,
        "status": status.value,
        "value": value,
        "thresholds": thresholds,
        "inputs": {
            "values": values,
            "formula": formulas[rule_id],
            "endpoint": endpoint,
            "note": NOTE,
            **extra,
        },
        "headline": headline,
        "missing": missing,
    }


def profile(kind: str) -> list[dict[str, Any]]:
    """Six findings (one per rule) for a named demo profile."""
    ins = finding(
        "INSIDER_SELLING", S.PASS, 0.0, "Tidak ada penjualan bersih orang dalam/pemegang saham utama dalam 90 hari."
    )
    div = finding("EARNINGS_WITHOUT_DIVIDEND", S.PASS, None, "Membagikan dividen dalam 12 bulan terakhir.")
    match kind:
        case "critical":
            return [
                finding("SLOAN_ACCRUAL", S.RED_FLAG, 0.138,
                        "13,8% dari aset tercatat sebagai laba yang belum menjadi uang tunai (batas wajar 10%)."),
                finding("EARNINGS_CASH_DIVERGENCE", S.RED_FLAG, 0.52,
                        "Laba naik 52% dibanding kuartal yang sama tahun lalu, tapi kas operasi turun 28%.",
                        delta_ocf=-0.28),
                finding("ALTMAN_Z_ADAPTED", S.WARNING, 2.1, "Skor Altman 2,10 — zona abu-abu kesulitan keuangan.",
                        components={"X1": 0.08, "X2": 0.41, "X3": 0.05, "X4": 0.69}, ebit_fallback_quarters=["2025-12-31"]),
                finding("BENEISH_ADAPTED", S.WARNING, 1, "1 dari 3 indikator tekanan manipulasi menyala: utang melonjak.",
                        sub_indices=[{"index": "GMI", "value": 1.02, "threshold": 1.19, "exceeded": False},
                                     {"index": "SGI", "value": 1.18, "threshold": 1.61, "exceeded": False},
                                     {"index": "LVGI", "value": 1.27, "threshold": 1.11, "exceeded": True}]),
                finding("INSIDER_SELLING", S.INSUFFICIENT_DATA, None, "Data filing orang dalam tidak bisa diambil.",
                        missing="Request /v2/filings/ gagal"),
                div,
            ]
        case "moderate":
            return [
                finding("SLOAN_ACCRUAL", S.WARNING, 0.072,
                        "7,2% dari aset tercatat sebagai laba yang belum menjadi uang tunai (batas wajar 10%)."),
                finding("EARNINGS_CASH_DIVERGENCE", S.PASS, 0.04, "Laba dan kas operasi bergerak searah."),
                finding("ALTMAN_Z_ADAPTED", S.RED_FLAG, 1.42, "Skor Altman 1,42 — masuk zona kesulitan keuangan."),
                finding("BENEISH_ADAPTED", S.PASS, 0, "Tidak ada indikator tekanan manipulasi yang menyala."),
                finding("INSIDER_SELLING", S.WARNING, 1.2,
                        "Orang dalam/pemegang saham utama menjual bersih 1,2% saham dalam 90 hari terakhir.",
                        filings=[{"holder_name": "PT Demo Investama", "tanggal": "2026-08-14", "transaksi": "sell",
                                  "lembar": 18_500_000, "harga": 312.0, "persen": 1.2}]),
                finding("EARNINGS_WITHOUT_DIVIDEND", S.WARNING, None,
                        "Membukukan laba dan kas operasi positif 12 bulan terakhir, tapi tidak membagikan dividen."),
            ]
        case "low_confidence":
            return [
                finding("SLOAN_ACCRUAL", S.INSUFFICIENT_DATA, None, "Sloan tidak bisa dihitung.",
                        missing="Kuartal 2025-Q3 tidak tersedia di API"),
                finding("EARNINGS_CASH_DIVERGENCE", S.RED_FLAG, 0.61,
                        "Laba naik 61% dibanding kuartal yang sama tahun lalu, tapi kas operasi turun 34%."),
                finding("ALTMAN_Z_ADAPTED", S.INSUFFICIENT_DATA, None, "Altman tidak bisa dihitung.",
                        missing="EBIT dan operating_pnl kosong untuk 2 kuartal"),
                finding("BENEISH_ADAPTED", S.INSUFFICIENT_DATA, None, "Beneish tidak bisa dihitung.",
                        missing="Hanya 1 sub-indeks yang bisa dievaluasi"),
                ins,
                finding("EARNINGS_WITHOUT_DIVIDEND", S.INSUFFICIENT_DATA, None, "Dividen tidak bisa dinilai.",
                        missing="TTM tidak bisa dihitung"),
            ]
        case "empty":
            return [
                finding(rule_id, S.INSUFFICIENT_DATA, None, f"{meta.name} tidak bisa dihitung.",
                        missing="Laporan kuartalan belum tersedia")
                for rule_id, meta in RULE_META.items()
            ]
        case _:  # low
            return [
                finding("SLOAN_ACCRUAL", S.PASS, 0.021,
                        "2,1% dari aset tercatat sebagai laba yang belum menjadi uang tunai (batas wajar 10%)."),
                finding("EARNINGS_CASH_DIVERGENCE", S.PASS, 0.06, "Laba dan kas operasi bergerak searah."),
                finding("ALTMAN_Z_ADAPTED", S.PASS, 3.84, "Skor Altman 3,84 — zona aman."),
                finding("BENEISH_ADAPTED", S.WARNING if kind == "low_warn" else S.PASS, 1 if kind == "low_warn" else 0,
                        "1 dari 3 indikator tekanan manipulasi menyala: penjualan melonjak."
                        if kind == "low_warn" else "Tidak ada indikator tekanan manipulasi yang menyala."),
                ins,
                div,
            ]


# symbol -> (profile, score, severity, low_confidence, evaluated_weight, severity_reason, event_id)
LATEST = {
    "EMTK.JK": ("critical", 75.0, "CRITICAL", False, 90, None, "AFS-2026-Q2-0001"),
    "WSKT.JK": ("moderate", 40.0, "MODERATE", False, 100, None, "AFS-2026-Q2-0002"),
    "GOTO.JK": ("low_confidence", 71.4, "MODERATE", True, 35,
                "Maksimal Sedang karena Keyakinan rendah (bobot terevaluasi 35 dari 100)", "AFS-2026-Q2-0003"),
    "ADRO.JK": ("low_warn", 7.5, "LOW", False, 100, None, None),
    "ASII.JK": ("low", 0.0, "LOW", False, 100, None, None),
    "TLKM.JK": ("low", 0.0, "LOW", False, 100, None, None),
    "UNVR.JK": ("low_warn", 7.5, "LOW", False, 100, None, None),
    "INDF.JK": ("low", 0.0, "LOW", False, 100, None, None),
    "BUMI.JK": ("empty", None, None, False, 0, None, None),
}


def _backtest_rows(case_id: str) -> list[BacktestResult]:
    scores = {
        "WSKT": [12.5, 18.0, 27.5, 33.8, 41.2, 38.9, 52.5, 63.9, 71.1, 76.4, 80.0, 74.7, 69.4, 66.7],
        "SRIL": [35.0, 48.8, 62.5, 70.0, 77.8, 81.3, 75.0, 72.2, 69.4, 73.6, 80.6, 83.3, 86.1, 84.7],
    }[case_id]
    out = []
    for i, score in enumerate(scores):
        report_date = _quarter_end(2021 + i // 4, i % 4 + 1)
        severity = "LOW" if score < 30 else "MODERATE" if score < 60 else "CRITICAL"
        findings = profile("critical" if score >= 60 else "moderate" if score >= 30 else "low")
        for f in findings:
            if f["rule_id"] == "INSIDER_SELLING":
                f.update(status=S.INSUFFICIENT_DATA.value, value=None, headline="Tidak dinilai di Backtest.",
                         missing="Data filing sebelum 2025 tidak tersedia")
        out.append(BacktestResult(case_id=case_id, symbol=f"{case_id}.JK", report_date=report_date, score=score,
                                  severity=severity, low_confidence=False, findings=findings))
    return out


def _quarter_end(year: int, q: int) -> date:
    return {1: date(year, 3, 31), 2: date(year, 6, 30), 3: date(year, 9, 30), 4: date(year, 12, 31)}[q]


def seed(session: Session, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    for symbol, name, sector, sub in EMITEN:
        session.add(Emiten(symbol=symbol, company_name=name, sector=sector, sub_sector=sub))

    sched_start = now - timedelta(days=7, minutes=3)
    run1 = AuditRun(
        trigger=RunTrigger.SCHEDULER.value, status=RunStatus.SUCCESS.value, started_at=sched_start,
        finished_at=sched_start + timedelta(minutes=2, seconds=41), emiten_scanned=10, emiten_failed=1,
        incidents_new=2, escalations=0, credits_used=14,
        log_text="[demo] 01:00:02 Memuat Universe: 10 emiten\n[demo] 01:01:40 BUMI.JK gagal: HTTP 502\n"
                 "[demo] 01:02:43 Selesai: 2 Incident baru, 0 Escalation",
    )
    manual_start = now - timedelta(hours=2)
    run2 = AuditRun(
        trigger=RunTrigger.MANUAL.value, status=RunStatus.SUCCESS.value, started_at=manual_start,
        finished_at=manual_start + timedelta(seconds=58), emiten_scanned=10, emiten_failed=0,
        incidents_new=1, escalations=1, credits_used=3,
        log_text="[demo] Memuat Universe: 10 emiten\n[demo] EMTK.JK Escalation: Sedang -> Kritis\n"
                 "[demo] GOTO.JK Incident baru AFS-2026-Q2-0003\n[demo] Selesai",
    )
    session.add_all([run1, run2])
    session.flush()

    for symbol, (kind, score, severity, low_conf, weight, reason, event_id) in LATEST.items():
        # earlier scheduled evaluation (EMTK was still MODERATE a week ago; GOTO not yet flagged)
        prev = {"EMTK.JK": (40.0, "MODERATE", "moderate"), "GOTO.JK": (20.0, "LOW", "low")}.get(
            symbol, (score, severity, kind)
        )
        session.add(EmitenEvaluation(
            run_id=run1.id, symbol=symbol, report_date=REPORT_T, score=prev[0], severity=prev[1],
            low_confidence=False, evaluated_weight=weight, findings=profile(prev[2]),
            event_id=event_id if symbol != "GOTO.JK" else None, created_at=run1.started_at,
        ))
        session.add(EmitenEvaluation(
            run_id=run2.id, symbol=symbol, report_date=REPORT_T, score=score, severity=severity,
            low_confidence=low_conf, evaluated_weight=weight, severity_reason=reason, findings=profile(kind),
            event_id=event_id, created_at=run2.started_at,
        ))

    incidents = [
        ("AFS-2026-Q2-0001", "EMTK.JK", TriageStatus.UNTRIAGED, run1, sched_start,
         [(IncidentEventKind.CREATED, None, "MODERATE", run1, sched_start),
          (IncidentEventKind.ESCALATED, "MODERATE", "CRITICAL", run2, manual_start)]),
        ("AFS-2026-Q2-0002", "WSKT.JK", TriageStatus.INVESTIGATING, run1, sched_start,
         [(IncidentEventKind.CREATED, None, "MODERATE", run1, sched_start),
          (IncidentEventKind.TRIAGE_CHANGED, "UNTRIAGED", "INVESTIGATING", None, sched_start + timedelta(hours=5)),
          (IncidentEventKind.NOTE_UPDATED, None, None, None, sched_start + timedelta(hours=5))]),
        ("AFS-2026-Q2-0003", "GOTO.JK", TriageStatus.UNTRIAGED, run2, manual_start,
         [(IncidentEventKind.CREATED, None, "MODERATE", run2, manual_start)]),
    ]
    for event_id, symbol, triage, run, created, events in incidents:
        kind, score, severity, low_conf, _w, reason, _e = LATEST[symbol]
        inc = Incident(
            event_id=event_id, symbol=symbol, report_date=REPORT_T, score=score, severity=severity,
            low_confidence=low_conf, severity_reason=reason, findings=profile(kind), triage_status=triage.value,
            analyst_notes="[demo] Cek catatan atas laporan keuangan Q2." if symbol == "WSKT.JK" else "",
            created_run_id=run.id, updated_run_id=run2.id, created_at=created, updated_at=manual_start,
        )
        session.add(inc)
        session.flush()
        for ev_kind, frm, to, ev_run, at in events:
            session.add(IncidentEvent(event_id=event_id, kind=ev_kind.value, from_value=frm, to_value=to,
                                      run_id=ev_run.id if ev_run else None, created_at=at))

    demo_insights = [
        IncidentInsight(
            event_id="AFS-2026-Q2-0001",
            run_id=run2.id,
            severity="CRITICAL",
            model="gemini-flash-lite (demo)",
            prompt_version="v2",
            what_happened="Laba bersih tercatat naik namun arus kas operasi berbalik negatif signifikan menjadi minus 96 miliar rupiah.",
            why_it_matters="Kenaikan laba tanpa dukungan kas riil memperbesar risiko manipulasi akrual dan tekanan likuiditas.",
            what_to_check=["Periksa akun piutang usaha dan penagihan kas", "Verifikasi kenaikan kewajiban jangka pendek"],
            created_at=manual_start,
        ),
        IncidentInsight(
            event_id="AFS-2026-Q2-0002",
            run_id=run1.id,
            severity="CRITICAL",
            model="gemini-flash-lite (demo)",
            prompt_version="v2",
            what_happened="Terjadi lonjakan rasio akrual Sloan dan skor Altman Z jatuh ke zona distress keuangan.",
            why_it_matters="Arus kas operasional terus merosot sementara beban utang konstruksi jatuh tempo dalam waktu dekat.",
            what_to_check=["Cek catatan kaki piutang retensi proyek BUMN", "Evaluasi jadwal restrukturisasi obligasi"],
            created_at=sched_start,
        ),
        IncidentInsight(
            event_id="AFS-2026-Q2-0003",
            run_id=run2.id,
            severity="MODERATE",
            model="gemini-flash-lite (demo)",
            prompt_version="v2",
            what_happened="Laba operasional membaik tipis tetapi kas keluar masih tinggi dan tidak ada pembagian dividen.",
            why_it_matters="Ketidakmampuan menghasilkan kas organik menuntut efisiensi lanjutan pada beban penjualan.",
            what_to_check=["Bandingkan EBITDA dengan kas operasional", "Periksa arus kas investasi dan bakar uang promosi"],
            created_at=manual_start,
        ),
    ]
    session.add_all(demo_insights)

    quarter_data = {
        "EMTK.JK": [(310, 205), (295, 180), (362, 120), (388, 41), (471, -96)],
        "WSKT.JK": [(-420, 150), (-510, -88), (-380, 60), (-455, -130), (-390, -75)],
        "GOTO.JK": [(-980, -410), None, (120, 60), (205, -40), (190, -140)],
    }
    for symbol, rows in quarter_data.items():
        for qd, row in zip(QUARTER_DATES, rows):
            payload = {"missing": True} if row is None else {
                "symbol": symbol, "report_date": qd.isoformat(), "period": quarter_label(qd),
                "earnings": row[0] * 1e9, "operating_cash_flow": row[1] * 1e9, "_demo": True,
            }
            session.add(ApiCache(kind="quarter", symbol=symbol, key=qd.isoformat(), payload=payload))

    for case_id in ("WSKT", "SRIL"):
        session.add_all(_backtest_rows(case_id))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="DEV ONLY: seed fake demo data")
    parser.add_argument("--reset", action="store_true", help="drop and recreate all tables first")
    args = parser.parse_args(argv)

    from afs import models  # noqa: F401  (register tables)

    engine = db.get_engine()
    if args.reset:
        db.Base.metadata.drop_all(engine)
    db.init_db()
    with db.session_scope() as session:
        if session.scalar(select(func.count()).select_from(AuditRun)):
            print("Database sudah berisi data; lewati. Pakai --reset untuk mengulang.")
            return
        seed(session)
    print("Data demo dibuat.")


if __name__ == "__main__":
    main()

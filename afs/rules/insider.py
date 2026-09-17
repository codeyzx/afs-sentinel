"""INSIDER_SELLING — docs/system-rules.md §3.5. Evaluated on the Audit Run date, not the Report Period."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from afs.config import WIB
from afs.domain import EvaluationInput, Filing, FindingStatus, RuleFinding
from afs.rules._util import FILINGS_ENDPOINT, BaseRule, base_inputs, fmt_pct_units, insufficient

RED_MIN = 2.0  # percent units
WARNING_MIN = 0.5
WINDOW_DAYS = 90
FORMULA = (
    "JualBersih% = Σ share_percentage_transaction (sell) − Σ share_percentage_transaction (buy), "
    "filing holder_type insider dalam 90 hari terakhir"
)
NOTE = (
    "“Insider” di API mencakup direksi/komisaris dan pemegang saham ≥5%; riwayat hanya ±1 tahun; "
    "persentase dibulatkan 2 desimal sehingga transaksi sangat kecil tercatat 0%."
)
THRESHOLDS = {"red_flag_min_pct": RED_MIN, "warning_min_pct": WARNING_MIN, "window_days": WINDOW_DAYS}
SUBJECT = "Orang dalam/pemegang saham utama"


def classify(net_sell_pct: float) -> FindingStatus:
    if net_sell_pct >= RED_MIN:
        return FindingStatus.RED_FLAG
    if net_sell_pct >= WARNING_MIN:
        return FindingStatus.WARNING
    return FindingStatus.PASS


def _local_date(ts: datetime) -> date:
    return ts.astimezone(WIB).date() if ts.tzinfo is not None else ts.date()


def in_window(filing: Filing, as_of: date) -> bool:
    d = _local_date(filing.timestamp)
    return as_of - timedelta(days=WINDOW_DAYS) < d <= as_of


def headline(net: float, counted: int) -> str:
    if counted == 0:
        return f"Tidak ada jual/beli oleh orang dalam/pemegang saham utama dalam {WINDOW_DAYS} hari terakhir."
    if net > 0:
        return f"{SUBJECT} menjual bersih {fmt_pct_units(net)} saham dalam {WINDOW_DAYS} hari terakhir."
    if net < 0:
        return f"{SUBJECT} membeli bersih {fmt_pct_units(-net)} saham dalam {WINDOW_DAYS} hari terakhir."
    return f"{SUBJECT} tidak menjual bersih dalam {WINDOW_DAYS} hari terakhir."


class InsiderSelling(BaseRule):
    rule_id = "INSIDER_SELLING"

    def evaluate(self, inp: EvaluationInput) -> RuleFinding:
        endpoint = FILINGS_ENDPOINT.format(symbol=inp.symbol)
        if inp.is_backtest:
            inputs = base_inputs([], FORMULA, endpoint, NOTE, filings=[])
            return insufficient(
                self.rule_id, THRESHOLDS, inputs, "data orang dalam sebelum 2025 tidak tersedia (Backtest)"
            )
        if inp.filings is None:
            inputs = base_inputs([], FORMULA, endpoint, NOTE, filings=[])
            return insufficient(self.rule_id, THRESHOLDS, inputs, "data filings gagal diambil")

        rows: list[dict[str, Any]] = []
        values: list[dict[str, Any]] = []
        sells = buys = 0.0
        counted = 0
        for f in sorted(inp.filings, key=lambda x: x.timestamp):
            if f.holder_type != "insider" or not in_window(f, inp.as_of):
                continue
            pct = f.share_percentage_transaction or 0.0
            is_counted = f.transaction_type in ("sell", "buy")
            if f.transaction_type == "sell":
                sells += pct
            elif f.transaction_type == "buy":
                buys += pct
            counted += int(is_counted)
            rows.append(
                {
                    "holder_name": f.holder_name,
                    "timestamp": f.timestamp.isoformat(),
                    "type": f.transaction_type,
                    "pct": f.share_percentage_transaction,
                    "amount": f.amount_transaction,
                    "price": f.price,
                    "counted": is_counted,
                }
            )
            values.append(
                {
                    "field": "share_percentage_transaction",
                    "report_date": _local_date(f.timestamp).isoformat(),
                    "value": f.share_percentage_transaction,
                }
            )

        net = round(sells - buys, 6)
        inputs = base_inputs(
            values,
            FORMULA,
            endpoint,
            NOTE,
            filings=rows,
            sell_pct=round(sells, 6),
            buy_pct=round(buys, 6),
            window_start=(inp.as_of - timedelta(days=WINDOW_DAYS)).isoformat(),
            window_end=inp.as_of.isoformat(),
        )
        return RuleFinding(
            rule_id=self.rule_id,
            status=classify(net),
            value=net,
            thresholds=THRESHOLDS,
            inputs=inputs,
            headline=headline(net, counted),
        )

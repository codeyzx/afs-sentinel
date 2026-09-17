"""EARNINGS_WITHOUT_DIVIDEND — docs/system-rules.md §3.6. Context rule: never RED_FLAG."""

from __future__ import annotations

from datetime import timedelta

from afs.domain import EvaluationInput, FindingStatus, RuleFinding
from afs.rules._util import (
    CORPORATE_ACTIONS_ENDPOINT,
    QUARTERLY_ENDPOINT,
    BaseRule,
    Collector,
    base_inputs,
    fmt_date_id,
    insufficient,
)

WINDOW_DAYS = 365
FORMULA = (
    "Waspada jika TTM(earnings) > 0 dan TTM(operating_cash_flow) > 0 "
    "dan tidak ada dividend[].ex_date dalam 365 hari sebelum tanggal acuan"
)
NOTE = "Tidak bisa membedakan dividen tunai dan dividen saham."
THRESHOLDS = {"window_days": WINDOW_DAYS, "ttm_earnings_above": 0, "ttm_operating_cash_flow_above": 0}


class EarningsWithoutDividend(BaseRule):
    rule_id = "EARNINGS_WITHOUT_DIVIDEND"

    def evaluate(self, inp: EvaluationInput) -> RuleFinding:
        c = Collector(inp)
        ttm_e = c.ttm("earnings")
        ttm_o = c.ttm("operating_cash_flow")
        endpoint = (
            f"{QUARTERLY_ENDPOINT.format(symbol=inp.symbol)}; {CORPORATE_ACTIONS_ENDPOINT.format(symbol=inp.symbol)}"
        )
        if inp.dividends is None:
            c.add_missing("data corporate actions gagal diambil")
        if ttm_e is None or ttm_o is None or inp.dividends is None:
            inputs = base_inputs(c.values, FORMULA, endpoint, NOTE)
            return insufficient(self.rule_id, THRESHOLDS, inputs, c.missing or "data tidak lengkap")

        window_start = inp.as_of - timedelta(days=WINDOW_DAYS)
        past = sorted((d for d in inp.dividends if d.ex_date <= inp.as_of), key=lambda d: d.ex_date)
        in_window = [d for d in past if d.ex_date > window_start]
        last = past[-1] if past else None
        days_since = float((inp.as_of - last.ex_date).days) if last else None

        inputs = base_inputs(
            c.values,
            FORMULA,
            endpoint,
            NOTE,
            ttm_earnings=ttm_e,
            ttm_operating_cash_flow=ttm_o,
            reference_date=inp.as_of.isoformat(),
            dividends_in_window=[{"ex_date": d.ex_date.isoformat(), "amount": d.amount} for d in in_window],
            last_ex_date=last.ex_date.isoformat() if last else None,
        )

        profitable = ttm_e > 0 and ttm_o > 0
        if in_window:
            status = FindingStatus.PASS
            text = f"Membagikan dividen dalam 12 bulan terakhir (ex-date terakhir {fmt_date_id(in_window[-1].ex_date)})."
        elif profitable:
            status = FindingStatus.WARNING
            text = "Membukukan laba dan kas operasi positif 12 bulan terakhir, tapi tidak membagikan dividen."
        else:
            status = FindingStatus.PASS
            text = "Laba atau kas operasi 12 bulan terakhir tidak positif, jadi wajar tidak membagikan dividen."
        return RuleFinding(
            rule_id=self.rule_id,
            status=status,
            value=days_since,
            thresholds=THRESHOLDS,
            inputs=inputs,
            headline=text,
        )

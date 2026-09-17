"""SLOAN_ACCRUAL — docs/system-rules.md §3.1."""

from __future__ import annotations

from afs.domain import EvaluationInput, FindingStatus, RuleFinding
from afs.rules._util import QUARTERLY_ENDPOINT, BaseRule, Collector, base_inputs, fmt_pct, insufficient

RED_ABOVE = 0.10
WARNING_ABOVE = 0.05
FORMULA = (
    "Sloan = (TTM(earnings) − TTM(operating_cash_flow)) / ((total_assets_t + total_assets_t-4) / 2)"
)
THRESHOLDS = {"red_flag_above": RED_ABOVE, "warning_above": WARNING_ABOVE}


def classify(ratio: float) -> FindingStatus:
    if ratio > RED_ABOVE:
        return FindingStatus.RED_FLAG
    if ratio > WARNING_ABOVE:
        return FindingStatus.WARNING
    return FindingStatus.PASS


def headline(ratio: float) -> str:
    if ratio < 0:
        return f"Kas operasi melebihi laba: rasio akrual {fmt_pct(ratio)} dari aset (batas wajar 10%)."
    return f"{fmt_pct(ratio)} dari aset tercatat sebagai laba yang belum menjadi uang tunai (batas wajar 10%)."


class SloanAccrual(BaseRule):
    rule_id = "SLOAN_ACCRUAL"

    def evaluate(self, inp: EvaluationInput) -> RuleFinding:
        c = Collector(inp)
        ttm_earnings = c.ttm("earnings")
        ttm_ocf = c.ttm("operating_cash_flow")
        assets_t = c.get(0, "total_assets")
        assets_t4 = c.get(4, "total_assets")
        if None in (ttm_earnings, ttm_ocf, assets_t, assets_t4):
            inputs = base_inputs(c.values, FORMULA, QUARTERLY_ENDPOINT.format(symbol=inp.symbol))
            return insufficient(self.rule_id, THRESHOLDS, inputs, c.missing or "data tidak lengkap")
        assert ttm_earnings is not None and ttm_ocf is not None and assets_t is not None and assets_t4 is not None
        avg_assets = (assets_t + assets_t4) / 2
        extras = {"ttm_earnings": ttm_earnings, "ttm_operating_cash_flow": ttm_ocf, "average_total_assets": avg_assets}
        inputs = base_inputs(c.values, FORMULA, QUARTERLY_ENDPOINT.format(symbol=inp.symbol), **extras)
        if avg_assets <= 0:
            return insufficient(self.rule_id, THRESHOLDS, inputs, "rata-rata total_assets nol atau negatif")
        ratio = (ttm_earnings - ttm_ocf) / avg_assets
        return RuleFinding(
            rule_id=self.rule_id,
            status=classify(ratio),
            value=ratio,
            thresholds=THRESHOLDS,
            inputs=inputs,
            headline=headline(ratio),
        )

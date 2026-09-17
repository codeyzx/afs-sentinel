"""EARNINGS_CASH_DIVERGENCE — docs/system-rules.md §3.2."""

from __future__ import annotations

from afs.domain import EvaluationInput, FindingStatus, RuleFinding
from afs.rules._util import QUARTERLY_ENDPOINT, BaseRule, Collector, base_inputs, fmt_pct, insufficient

RED_EARNINGS_MIN = 0.25
RED_OCF_MAX = -0.15
WARNING_EARNINGS_MIN = 0.10
WARNING_OCF_MAX = 0.0
FORMULA = (
    "ΔLaba = (earnings_t − earnings_t-4) / |earnings_t-4|; "
    "ΔOCF = (operating_cash_flow_t − operating_cash_flow_t-4) / |operating_cash_flow_t-4|"
)
THRESHOLDS = {
    "red_flag": {"delta_earnings_min": RED_EARNINGS_MIN, "delta_ocf_max": RED_OCF_MAX},
    "warning": {"delta_earnings_min": WARNING_EARNINGS_MIN, "delta_ocf_max": WARNING_OCF_MAX},
}


def classify(delta_earnings: float, delta_ocf: float) -> FindingStatus:
    if delta_earnings >= RED_EARNINGS_MIN and delta_ocf <= RED_OCF_MAX:
        return FindingStatus.RED_FLAG
    if delta_earnings >= WARNING_EARNINGS_MIN and delta_ocf <= WARNING_OCF_MAX:
        return FindingStatus.WARNING
    return FindingStatus.PASS


def _move(delta: float) -> str:
    if delta > 0:
        return f"naik {fmt_pct(delta, 0)}"
    if delta < 0:
        return f"turun {fmt_pct(-delta, 0)}"
    return "tidak berubah"


def headline(status: FindingStatus, delta_earnings: float, delta_ocf: float) -> str:
    if status == FindingStatus.PASS:
        return (
            f"Laba {_move(delta_earnings)} dan kas operasi {_move(delta_ocf)} "
            "dibanding kuartal yang sama tahun lalu."
        )
    return (
        f"Laba {_move(delta_earnings)} dibanding kuartal yang sama tahun lalu, "
        f"tapi kas operasi {_move(delta_ocf)}."
    )


class EarningsCashDivergence(BaseRule):
    rule_id = "EARNINGS_CASH_DIVERGENCE"

    def evaluate(self, inp: EvaluationInput) -> RuleFinding:
        c = Collector(inp)
        e_t = c.get(0, "earnings")
        e_t4 = c.get(4, "earnings")
        o_t = c.get(0, "operating_cash_flow")
        o_t4 = c.get(4, "operating_cash_flow")
        endpoint = QUARTERLY_ENDPOINT.format(symbol=inp.symbol)
        inputs = base_inputs(c.values, FORMULA, endpoint)
        if e_t is None or e_t4 is None or o_t is None or o_t4 is None:
            return insufficient(self.rule_id, THRESHOLDS, inputs, c.missing or "data tidak lengkap")
        if e_t4 <= 0:
            return insufficient(
                self.rule_id, THRESHOLDS, inputs, "laba kuartal yang sama tahun lalu nol atau rugi"
            )
        if o_t4 == 0:
            return insufficient(self.rule_id, THRESHOLDS, inputs, "kas operasi kuartal yang sama tahun lalu nol")
        d_e = (e_t - e_t4) / abs(e_t4)
        d_o = (o_t - o_t4) / abs(o_t4)
        inputs.update(delta_earnings=d_e, delta_operating_cash_flow=d_o)
        status = classify(d_e, d_o)
        return RuleFinding(
            rule_id=self.rule_id,
            status=status,
            value=d_e,
            thresholds=THRESHOLDS,
            inputs=inputs,
            headline=headline(status, d_e, d_o),
        )

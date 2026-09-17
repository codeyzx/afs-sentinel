"""BENEISH_ADAPTED — docs/system-rules.md §3.4 (GMI, SGI, LVGI; t vs t-4)."""

from __future__ import annotations

from typing import Any

from afs.domain import EvaluationInput, FindingStatus, RuleFinding
from afs.rules._util import QUARTERLY_ENDPOINT, BaseRule, Collector, base_inputs, insufficient

GMI_ABOVE = 1.19
SGI_ABOVE = 1.61
LVGI_ABOVE = 1.11
MIN_EVALUATED = 2
FORMULA = (
    "GMI = (gross_profit_t-4 / revenue_t-4) / (gross_profit_t / revenue_t); "
    "SGI = revenue_t / revenue_t-4; "
    "LVGI = (total_liabilities_t / total_assets_t) / (total_liabilities_t-4 / total_assets_t-4)"
)
NOTE = "Versi adaptasi: hanya 3 dari 8 indeks Beneish (GMI, SGI, LVGI); bukan M-Score utuh."
THRESHOLDS = {"GMI_above": GMI_ABOVE, "SGI_above": SGI_ABOVE, "LVGI_above": LVGI_ABOVE, "red_flag_min_exceeded": 2}

_LABELS = {"GMI": "margin kotor memburuk", "SGI": "penjualan tumbuh sangat cepat", "LVGI": "utang melonjak"}


def classify(exceeded: int, evaluated: int) -> FindingStatus:
    if evaluated < MIN_EVALUATED:
        return FindingStatus.INSUFFICIENT_DATA
    if exceeded >= 2:
        return FindingStatus.RED_FLAG
    if exceeded == 1:
        return FindingStatus.WARNING
    return FindingStatus.PASS


def _ratio(num: float | None, den: float | None) -> float | None:
    """Division that is 'not evaluated' (None) when data is null or the denominator is ≤ 0."""
    if num is None or den is None or den <= 0:
        return None
    return num / den


def headline(exceeded_names: list[str], evaluated: int) -> str:
    n = len(exceeded_names)
    base = f"{n} dari {evaluated} indikator tekanan manipulasi menyala"
    if n == 0:
        return base + "."
    return base + ": " + " dan ".join(_LABELS[name] for name in exceeded_names) + "."


class BeneishAdapted(BaseRule):
    rule_id = "BENEISH_ADAPTED"

    def evaluate(self, inp: EvaluationInput) -> RuleFinding:
        c = Collector(inp)
        rev_t, rev_t4 = c.get(0, "revenue"), c.get(4, "revenue")
        gp_t, gp_t4 = c.get(0, "gross_profit"), c.get(4, "gross_profit")
        tl_t, tl_t4 = c.get(0, "total_liabilities"), c.get(4, "total_liabilities")
        ta_t, ta_t4 = c.get(0, "total_assets"), c.get(4, "total_assets")

        margin_t4 = _ratio(gp_t4, rev_t4)
        margin_t = _ratio(gp_t, rev_t)
        lev_t = _ratio(tl_t, ta_t)
        lev_t4 = _ratio(tl_t4, ta_t4)
        values = {
            "GMI": _ratio(margin_t4, margin_t),
            "SGI": _ratio(rev_t, rev_t4),
            "LVGI": _ratio(lev_t, lev_t4),
        }
        limits = {"GMI": GMI_ABOVE, "SGI": SGI_ABOVE, "LVGI": LVGI_ABOVE}
        sub_indices: dict[str, dict[str, Any]] = {
            name: {
                "value": v,
                "threshold": limits[name],
                "evaluated": v is not None,
                "exceeded": v is not None and v > limits[name],
            }
            for name, v in values.items()
        }
        evaluated = sum(1 for s in sub_indices.values() if s["evaluated"])
        exceeded_names = [name for name, s in sub_indices.items() if s["exceeded"]]

        inputs = base_inputs(
            c.values, FORMULA, QUARTERLY_ENDPOINT.format(symbol=inp.symbol), NOTE, sub_indices=sub_indices
        )
        status = classify(len(exceeded_names), evaluated)
        if status == FindingStatus.INSUFFICIENT_DATA:
            not_evaluated = ", ".join(n for n, s in sub_indices.items() if not s["evaluated"])
            reason = f"hanya {evaluated} dari 3 indikator bisa dihitung ({not_evaluated} tidak terevaluasi)"
            if c.missing:
                reason += f"; {c.missing}"
            return insufficient(self.rule_id, THRESHOLDS, inputs, reason)
        return RuleFinding(
            rule_id=self.rule_id,
            status=status,
            value=float(len(exceeded_names)),
            thresholds=THRESHOLDS,
            inputs=inputs,
            headline=headline(exceeded_names, evaluated),
        )

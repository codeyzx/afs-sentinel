"""ALTMAN_Z_ADAPTED — docs/system-rules.md §3.3."""

from __future__ import annotations

from typing import Any

from afs.domain import EvaluationInput, FindingStatus, RuleFinding, quarter_label
from afs.rules._util import (
    QUARTERLY_ENDPOINT,
    BaseRule,
    Collector,
    base_inputs,
    fmt_num,
    insufficient,
)

RED_BELOW = 1.8
WARNING_BELOW = 2.9
FORMULA = (
    "Z = 6.56·X1 + 3.26·X2 + 6.72·X3 + 1.05·X4; "
    "X1 = (total_current_asset_t − current_liabilities_t) / total_assets_t; "
    "X2 = total_equity_t / total_assets_t (proksi laba ditahan); "
    "X3 = TTM(EBIT*) / total_assets_t (EBIT* = ebit, atau operating_pnl jika ebit kosong); "
    "X4 = total_equity_t / total_liabilities_t"
)
NOTE = (
    "Versi adaptasi: laba ditahan tidak tersedia di API sehingga diganti total ekuitas; "
    "ambang dibuat lebih ketat untuk mengimbangi."
)
THRESHOLDS = {"red_flag_below": RED_BELOW, "warning_below": WARNING_BELOW}
BALANCE_FIELDS = ["total_current_asset", "current_liabilities", "total_equity", "total_assets", "total_liabilities"]


def classify(z: float) -> FindingStatus:
    if z < RED_BELOW:
        return FindingStatus.RED_FLAG
    if z < WARNING_BELOW:
        return FindingStatus.WARNING
    return FindingStatus.PASS


def headline(z: float) -> str:
    status = classify(z)
    zone = {
        FindingStatus.RED_FLAG: "masuk zona kesulitan keuangan",
        FindingStatus.WARNING: "zona abu-abu kesulitan keuangan",
        FindingStatus.PASS: "zona aman",
    }[status]
    return f"Skor Altman {fmt_num(z, 2)} — {zone}."


class AltmanZAdapted(BaseRule):
    rule_id = "ALTMAN_Z_ADAPTED"

    def evaluate(self, inp: EvaluationInput) -> RuleFinding:
        c = Collector(inp)
        bal = {name: c.get(0, name) for name in BALANCE_FIELDS}

        ebit_sources: list[dict[str, Any]] = []
        ebits: list[float | None] = []
        for k in range(4):
            q = c.quarter(k)
            if q is None:
                c.get(k, "ebit")  # records the missing quarter
                ebits.append(None)
                continue
            iso = q.report_date.isoformat()
            ebit = q.get("ebit")
            c.values.append({"field": "ebit", "report_date": iso, "value": ebit})
            if ebit is not None:
                ebits.append(ebit)
                ebit_sources.append({"report_date": iso, "source": "ebit", "fallback": False})
                continue
            pnl = q.get("operating_pnl")
            c.values.append({"field": "operating_pnl", "report_date": iso, "value": pnl})
            ebits.append(pnl)
            ebit_sources.append({"report_date": iso, "source": "operating_pnl", "fallback": True})
            if pnl is None:
                c.add_missing(f"ebit dan operating_pnl kuartal {quarter_label(q.report_date)} kosong")

        endpoint = QUARTERLY_ENDPOINT.format(symbol=inp.symbol)
        extras: dict[str, Any] = {
            "ebit_sources": ebit_sources,
            "fallback_used": any(s["fallback"] for s in ebit_sources),
        }
        inputs = base_inputs(c.values, FORMULA, endpoint, NOTE, **extras)
        if c.missing:
            return insufficient(self.rule_id, THRESHOLDS, inputs, c.missing)

        tca, cl, eq, ta, tl = (bal[n] for n in BALANCE_FIELDS)
        assert tca is not None and cl is not None and eq is not None and ta is not None and tl is not None
        if ta == 0:
            return insufficient(self.rule_id, THRESHOLDS, inputs, "total_assets bernilai nol")
        if tl == 0:
            return insufficient(self.rule_id, THRESHOLDS, inputs, "total_liabilities bernilai nol")

        ttm_ebit = float(sum(v for v in ebits if v is not None))
        x1 = (tca - cl) / ta
        x2 = eq / ta
        x3 = ttm_ebit / ta
        x4 = eq / tl
        z = 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4
        inputs.update(components={"X1": x1, "X2": x2, "X3": x3, "X4": x4}, ttm_ebit=ttm_ebit)
        return RuleFinding(
            rule_id=self.rule_id,
            status=classify(z),
            value=z,
            thresholds=THRESHOLDS,
            inputs=inputs,
            headline=headline(z),
        )

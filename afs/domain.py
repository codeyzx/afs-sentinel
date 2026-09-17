"""Domain types shared by every layer. Vocabulary follows CONTEXT.md; rules follow docs/system-rules.md."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any, Mapping, Protocol, Sequence


class FindingStatus(StrEnum):
    PASS = "PASS"
    WARNING = "WARNING"
    RED_FLAG = "RED_FLAG"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class Severity(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    CRITICAL = "CRITICAL"

    @property
    def rank(self) -> int:
        return {"LOW": 0, "MODERATE": 1, "CRITICAL": 2}[self.value]


class TriageStatus(StrEnum):
    UNTRIAGED = "UNTRIAGED"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class RunTrigger(StrEnum):
    SCHEDULER = "SCHEDULER"
    MANUAL = "MANUAL"


class RunStatus(StrEnum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class IncidentEventKind(StrEnum):
    CREATED = "CREATED"
    ESCALATED = "ESCALATED"
    DOWNGRADED = "DOWNGRADED"
    TRIAGE_CHANGED = "TRIAGE_CHANGED"
    NOTE_UPDATED = "NOTE_UPDATED"


# ---------------------------------------------------------------- input data


@dataclass(frozen=True)
class Quarter:
    """One discrete-quarter row of GET /v2/financials/quarterly/{symbol}/ (raw API field names)."""

    report_date: date
    data: Mapping[str, Any]

    def get(self, name: str) -> float | None:
        value = self.data.get(name)
        return None if value is None else float(value)


@dataclass(frozen=True)
class Filing:
    """One Insider Filing row of GET /v2/filings/."""

    timestamp: datetime  # publication time
    transaction_type: str  # "buy" | "sell" | "others"
    holder_type: str
    holder_name: str
    share_percentage_transaction: float | None  # percent units: 4.9 == 4.9%
    amount_transaction: float | None = None
    price: float | None = None


@dataclass(frozen=True)
class Dividend:
    ex_date: date
    amount: float | None  # IDR per share


@dataclass(frozen=True)
class EvaluationInput:
    """Everything the Forensic Rules need for one Emiten and Report Period.

    quarters[k] is the quarter k periods before Report Period t (k = 0..4), or None when the API
    has no row for that expected report date. quarters[0] is never None.
    filings / dividends are None when the data could not be fetched (-> INSUFFICIENT_DATA);
    an empty list means "fetched, nothing there".
    as_of is the reference date: the Audit Run date (live) or report_date of t (Backtest).
    """

    symbol: str
    quarters: Sequence[Quarter | None]
    as_of: date
    filings: Sequence[Filing] | None
    dividends: Sequence[Dividend] | None
    is_backtest: bool = False

    @property
    def report_date(self) -> date:
        assert self.quarters[0] is not None
        return self.quarters[0].report_date


# ---------------------------------------------------------------- outputs


@dataclass(frozen=True)
class RuleFinding:
    rule_id: str
    status: FindingStatus
    value: float | None
    thresholds: Mapping[str, Any]
    inputs: Mapping[str, Any]
    headline: str
    missing: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "status": self.status.value,
            "value": self.value,
            "thresholds": dict(self.thresholds),
            "inputs": dict(self.inputs),
            "headline": self.headline,
            "missing": self.missing,
        }

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "RuleFinding":
        return cls(
            rule_id=d["rule_id"],
            status=FindingStatus(d["status"]),
            value=d.get("value"),
            thresholds=d.get("thresholds") or {},
            inputs=d.get("inputs") or {},
            headline=d.get("headline") or "",
            missing=d.get("missing"),
        )


@dataclass(frozen=True)
class ScoreResult:
    score: float | None  # None when no rule could be evaluated
    severity: Severity | None
    low_confidence: bool
    evaluated_weight: float
    severity_reason: str | None = None  # set when the core-rule floor or low-confidence cap applied


@dataclass(frozen=True)
class Evaluation:
    symbol: str
    report_date: date
    findings: list[RuleFinding] = field(default_factory=list)
    score: ScoreResult | None = None


class ForensicRule(Protocol):
    rule_id: str
    name: str  # display name, e.g. "Sloan Accrual Ratio"
    subtitle: str  # plain-language subtitle (Indonesian)
    weight: float
    is_core: bool

    def evaluate(self, inp: EvaluationInput) -> RuleFinding: ...


def quarter_label(d: date) -> str:
    """2025-09-30 -> '2025-Q3'."""
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"

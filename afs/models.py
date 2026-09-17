"""Persistence model. Enum columns store the StrEnum values from afs.domain."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from afs.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Emiten(Base):
    __tablename__ = "emiten"

    symbol: Mapped[str] = mapped_column(String(16), primary_key=True)  # "EMTK.JK"
    company_name: Mapped[str] = mapped_column(String(200), default="")
    sector: Mapped[str] = mapped_column(String(100), default="")
    sub_sector: Mapped[str] = mapped_column(String(100), default="")
    is_excluded: Mapped[bool] = mapped_column(Boolean, default=False)  # financial sector


class ApiCache(Base):
    """Permanent cache of Sectors API responses. kind: 'quarter' (key = report_date ISO),
    'filings' / 'corporate_actions' / 'company' (key = fetch date ISO, latest wins)."""

    __tablename__ = "api_cache"
    __table_args__ = (UniqueConstraint("kind", "symbol", "key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(32))
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    key: Mapped[str] = mapped_column(String(32), default="")
    payload: Mapped[Any] = mapped_column(JSON)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditRun(Base):
    __tablename__ = "audit_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trigger: Mapped[str] = mapped_column(String(16))  # RunTrigger
    status: Mapped[str] = mapped_column(String(16))  # RunStatus
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    emiten_scanned: Mapped[int] = mapped_column(Integer, default=0)
    emiten_failed: Mapped[int] = mapped_column(Integer, default=0)
    incidents_new: Mapped[int] = mapped_column(Integer, default=0)
    escalations: Mapped[int] = mapped_column(Integer, default=0)
    credits_used: Mapped[int] = mapped_column(Integer, default=0)
    log_text: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class EmitenEvaluation(Base):
    """Rule Findings + Composite Risk Score for one Emiten in one Audit Run (every Emiten, incl. LOW)."""

    __tablename__ = "emiten_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("audit_runs.id"), index=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    report_date: Mapped[date] = mapped_column(Date)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[str | None] = mapped_column(String(16), nullable=True)
    low_confidence: Mapped[bool] = mapped_column(Boolean, default=False)
    evaluated_weight: Mapped[float] = mapped_column(Float, default=0)
    severity_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)  # RuleFinding.to_dict()
    event_id: Mapped[str | None] = mapped_column(String(32), nullable=True)  # Incident, if any
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (UniqueConstraint("symbol", "report_date"),)

    event_id: Mapped[str] = mapped_column(String(32), primary_key=True)  # AFS-2025-Q3-0007
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    report_date: Mapped[date] = mapped_column(Date)
    score: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(16))
    low_confidence: Mapped[bool] = mapped_column(Boolean, default=False)
    severity_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    triage_status: Mapped[str] = mapped_column(String(16), default="UNTRIAGED")
    analyst_notes: Mapped[str] = mapped_column(Text, default="")
    created_run_id: Mapped[int | None] = mapped_column(ForeignKey("audit_runs.id"), nullable=True)
    updated_run_id: Mapped[int | None] = mapped_column(ForeignKey("audit_runs.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    events: Mapped[list["IncidentEvent"]] = relationship(
        back_populates="incident", order_by="IncidentEvent.created_at", cascade="all, delete-orphan"
    )


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("incidents.event_id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))  # IncidentEventKind
    from_value: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_value: Mapped[str | None] = mapped_column(String(64), nullable=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("audit_runs.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    incident: Mapped[Incident] = relationship(back_populates="events")


class BacktestResult(Base):
    __tablename__ = "backtest_results"
    __table_args__ = (UniqueConstraint("case_id", "report_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(32), index=True)  # "WSKT"
    symbol: Mapped[str] = mapped_column(String(16))
    report_date: Mapped[date] = mapped_column(Date)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[str | None] = mapped_column(String(16), nullable=True)
    low_confidence: Mapped[bool] = mapped_column(Boolean, default=False)
    severity_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Lock(Base):
    """Single-row mutex for Audit Runs (name='audit_run'); stale after 2 hours."""

    __tablename__ = "locks"

    name: Mapped[str] = mapped_column(String(32), primary_key=True)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

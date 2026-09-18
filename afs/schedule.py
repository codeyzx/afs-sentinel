"""When the next Audit Run is owed (docs/system-rules.md §6.1).

Its own module because both the runner (to decide) and the web app (to display) need it, and the
web app must not import the runner — the runner pulls in the whole pipeline, and `/` has to render
even when that import fails.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from afs.config import get_settings
from afs.domain import RunStatus
from afs.models import AuditRun


def _aware(moment: datetime) -> datetime:
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment  # SQLite drops tzinfo


def last_successful_start(session: Session) -> datetime | None:
    """When the most recent SUCCESS Audit Run began, or None if there has never been one."""
    started = session.scalars(
        select(AuditRun.started_at)
        .where(AuditRun.status == RunStatus.SUCCESS.value)
        .order_by(AuditRun.started_at.desc(), AuditRun.id.desc())
        .limit(1)
    ).first()
    return None if started is None else _aware(started)


def interval_days() -> int:
    return get_settings().run_interval_days


def is_due(now: datetime, last_success: datetime | None, days: int | None = None) -> bool:
    """True when a scheduled Audit Run is owed.

    Anchored on the last SUCCESS rather than the calendar, so a day the dyno was down is caught up
    on the next tick instead of pushing the schedule out by another whole interval.
    """
    if last_success is None:
        return True  # never run successfully: the first scheduler tick starts the system
    return _aware(now) - _aware(last_success) >= timedelta(days=interval_days() if days is None else days)


def next_due(last_success: datetime | None, days: int | None = None) -> datetime | None:
    """When the next scheduled run is owed. None when there is no anchor to count from yet."""
    if last_success is None:
        return None
    return _aware(last_success) + timedelta(days=interval_days() if days is None else days)

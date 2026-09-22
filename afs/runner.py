"""Audit Run orchestration — docs/system-rules.md §6, with Telegram dispatch (§7).

Transactions: the AuditRun row and the Universe sync are committed up front; every Emiten is then
committed on its own so paid-for API cache rows survive a later failure, and a failing Emiten is rolled
back alone. Telegram messages are sent only after the loop, and a send failure never fails the run.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable

from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError

from afs import audio, insight, schedule, telegram
from afs.config import WIB
from afs.db import session_scope
from afs.domain import RunStatus, RunTrigger, Severity, quarter_label
from afs.incidents import apply_evaluation
from afs.models import AuditRun, Incident, Lock, utcnow
from afs.rules import evaluate_all
from afs.scoring import compute_score
from afs.sectors.client import SectorsClient
from afs.sectors.repository import DataRepository

log = logging.getLogger(__name__)

LOCK_NAME = "audit_run"
LOCK_STALE_AFTER = timedelta(hours=2)


class RunInProgressError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Audit Run sedang berjalan")


# ---------------------------------------------------------------- lock


def _aware(moment: datetime) -> datetime:
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment  # SQLite drops tzinfo


def _is_stale(lock: Lock, now: datetime) -> bool:
    return now - _aware(lock.acquired_at) >= LOCK_STALE_AFTER


def is_run_in_progress(now: datetime | None = None) -> bool:
    now = now or utcnow()
    with session_scope() as session:
        lock = session.get(Lock, LOCK_NAME)
        return lock is not None and not _is_stale(lock, now)


def acquire_lock(now: datetime | None = None) -> bool:
    """Take the Audit Run lock; a lock older than 2 hours is considered stale and replaced."""
    now = now or utcnow()
    try:
        with session_scope() as session:
            lock = session.get(Lock, LOCK_NAME)
            if lock is None:
                session.add(Lock(name=LOCK_NAME, acquired_at=now))
                return True
            if not _is_stale(lock, now):
                return False
            # Compare-and-swap so two processes cannot both replace the same stale lock.
            result = session.execute(
                update(Lock)
                .where(Lock.name == LOCK_NAME, Lock.acquired_at == lock.acquired_at)
                .values(acquired_at=now)
                .execution_options(synchronize_session=False)
            )
            return result.rowcount == 1
    except IntegrityError:  # another process inserted the lock first
        return False


def release_lock() -> None:
    with session_scope() as session:
        session.execute(delete(Lock).where(Lock.name == LOCK_NAME))


# ---------------------------------------------------------------- schedule


def should_run_scheduled(now: datetime) -> bool:
    """Heroku Scheduler fires daily; a run happens only once per `run_interval_days` (§6.1)."""
    with session_scope() as session:
        return schedule.is_due(now, schedule.last_successful_start(session))


# ---------------------------------------------------------------- run


@dataclass
class _Stats:
    scanned: int = 0
    failed: int = 0
    incidents_new: int = 0
    escalations: int = 0


@dataclass
class _RunLog:
    lines: list[str] = field(default_factory=list)

    def __call__(self, message: str, level: int = logging.INFO) -> None:
        log.log(level, message)
        self.lines.append(f"[{datetime.now(WIB):%Y-%m-%d %H:%M:%S} WIB] {message}")

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def _safe_send(send: Callable[..., Any], runlog: _RunLog, text: str, button: tuple[str, str] | None = None) -> None:
    try:
        ok = send(text, button) if button is not None else send(text)
    except Exception as exc:  # noqa: BLE001 - Telegram must never fail the run
        runlog(f"Telegram gagal: {type(exc).__name__}", logging.WARNING)
        return
    if ok is False:
        runlog("Telegram tidak terkirim", logging.WARNING)


def run_audit(
    trigger: RunTrigger,
    *,
    client: SectorsClient | None = None,
    today: date | None = None,
    send: Callable[..., Any] = telegram.send_message,
    send_voice: Callable[..., Any] = telegram.send_voice,
) -> int:
    """Execute one Audit Run and return its id. Raises RunInProgressError when another run holds the lock."""
    trigger = RunTrigger(trigger)
    client = client if client is not None else SectorsClient()  # no network on construction
    if not acquire_lock():
        raise RunInProgressError()
    runlog = _RunLog()
    stats = _Stats()
    run_id: int | None = None
    started_at = utcnow()
    try:
        with session_scope() as session:
            run = AuditRun(trigger=trigger.value, status=RunStatus.RUNNING.value, started_at=started_at)
            session.add(run)
            session.flush()
            run_id = run.id
        runlog(f"Audit Run #{run_id} dimulai ({trigger.value})")
        _execute(
            run_id,
            started_at,
            trigger,
            client=client,
            today=today,
            send=send,
            send_voice=send_voice,
            runlog=runlog,
            stats=stats,
        )
        return run_id
    except Exception as exc:
        log.exception("Audit Run gagal")
        if run_id is None:
            raise  # the run could not even be recorded (e.g. database unreachable)
        reason = str(exc) or type(exc).__name__
        runlog(f"Audit Run GAGAL: {reason}", logging.ERROR)
        _finish_failed(run_id, reason, runlog, client, stats)
        _safe_send(send, runlog, telegram.format_run_failure(started_at=started_at, trigger=trigger, reason=reason))
        return run_id
    finally:
        try:
            release_lock()
        except Exception:  # noqa: BLE001 - a stale lock expires after 2 hours anyway
            log.exception("Gagal melepas lock Audit Run")


def _narrate(run_id: int, pending: list[dict[str, Any]], runlog: _RunLog) -> dict[str, str]:
    """Incident Insight phase: runs between the Emiten loop and the Telegram dispatch, on its own
    session. Every failure is contained in afs.insight, so this can only return fewer narrations —
    never fail the Audit Run (§6.2, docs/adr/0003-*)."""
    if not pending:
        return {}
    event_ids = [item["event_id"] for item in pending]
    names = {item["event_id"]: item["company_name"] for item in pending}
    runlog(f"Ringkasan AI: {len(event_ids)} Incident")
    with session_scope() as session:
        made = insight.generate_for_run(session, run_id, event_ids, names=names, log_line=runlog)
        return {event_id: ins.what_happened for event_id, ins in made.items()}


def _finish_failed(run_id: int, reason: str, runlog: _RunLog, client: SectorsClient, stats: _Stats) -> None:
    try:
        with session_scope() as session:
            run = session.get(AuditRun, run_id)
            if run is None:
                return
            run.status = RunStatus.FAILED.value
            run.error = reason
            run.finished_at = utcnow()
            _write_counts(run, client, stats, runlog)
    except Exception:  # noqa: BLE001
        log.exception("Gagal mencatat Audit Run #%s sebagai FAILED", run_id)


def _write_counts(run: AuditRun, client: SectorsClient, stats: _Stats, runlog: _RunLog) -> None:
    run.emiten_scanned = stats.scanned
    run.emiten_failed = stats.failed
    run.incidents_new = stats.incidents_new
    run.escalations = stats.escalations
    run.credits_used = client.credits_used
    run.log_text = runlog.text


def _execute(
    run_id: int,
    started_at: datetime,
    trigger: RunTrigger,
    *,
    client: SectorsClient,
    today: date | None,
    send: Callable[..., Any],
    send_voice: Callable[..., Any] = telegram.send_voice,
    runlog: _RunLog,
    stats: _Stats,
) -> None:
    as_of = today or datetime.now(WIB).date()
    pending: list[dict[str, Any]] = []

    with session_scope() as session:
        repo = DataRepository(session, client, today=lambda: as_of)
        universe = [(e.symbol, e.company_name) for e in repo.sync_universe()]
        session.commit()
        runlog(f"Universe: {len(universe)} emiten aktif")

        for symbol, company_name in universe:
            stats.scanned += 1
            try:
                inp = repo.build_live_input(symbol, as_of=as_of)
                if inp is None:
                    session.commit()  # keep whatever was fetched and cached
                    stats.failed += 1
                    runlog(f"{symbol}: GAGAL — data kuartal tidak tersedia", logging.WARNING)
                    continue
                findings = evaluate_all(inp)
                score = compute_score(findings)
                outcome = apply_evaluation(
                    session, run_id=run_id, symbol=symbol, report_date=inp.report_date, score=score, findings=findings
                )
                pending_message = None
                if outcome.notify and outcome.incident is not None and score.score is not None:
                    assert score.severity is not None and outcome.event_id is not None
                    # Built after the loop: the Incident Insight does not exist yet (§7.1).
                    pending_message = dict(
                        event_id=outcome.event_id,
                        symbol=symbol,
                        company_name=company_name or symbol,
                        report_date=inp.report_date,
                        score=score.score,
                        severity=score.severity,
                        low_confidence=score.low_confidence,
                        severity_reason=score.severity_reason,
                        findings=findings,
                        escalated_from=outcome.previous_severity if outcome.kind == "ESCALATED" else None,
                    )
                session.commit()
            except Exception as exc:  # noqa: BLE001 - one Emiten must not stop the run (§6.2.3)
                session.rollback()
                stats.failed += 1
                runlog(f"{symbol}: GAGAL — {type(exc).__name__}: {exc}", logging.WARNING)
                continue

            if outcome.kind == "CREATED":
                stats.incidents_new += 1
            elif outcome.kind == "ESCALATED":
                stats.escalations += 1
            severity = Severity(score.severity).value if score.severity else "tak bisa dinilai"
            runlog(f"{symbol}: {severity} skor={score.score} → {outcome.kind} {outcome.event_id or ''}".rstrip())
            if pending_message is not None:
                pending.append(pending_message)

        if universe and stats.failed == stats.scanned:
            raise RuntimeError(f"Semua {stats.scanned} emiten gagal diproses")

    insights = _narrate(run_id, pending, runlog)

    for item in pending:
        event_id = item["event_id"]
        message = telegram.format_incident_message(insight_line=insights.get(event_id), **item)
        _safe_send(send, runlog, message, (telegram.OPEN_INCIDENT_BUTTON, telegram.incident_url(event_id)))

        # Audio Briefing (~1.5–2.5 mins) sent as Telegram Voice Note
        try:
            with session_scope() as session:
                inc = session.get(Incident, event_id)
                ins_row = insight.latest_for(session, event_id)
                if inc is not None:
                    audio_bytes, _script = audio.get_or_create_incident_audio(
                        session=session,
                        incident=inc,
                        company_name=item["company_name"],
                        insight_row=ins_row,
                    )
                    if audio_bytes:
                        ticker = item["symbol"].removesuffix(".JK")
                        period = quarter_label(item["report_date"])
                        caption = (
                            f"🎧 <b>Audio Briefing · {ticker} ({period})</b>\n"
                            "<i>Dengarkan intisari penting (~2 menit) sembari multitasking.</i>"
                        )
                        try:
                            ok = send_voice(
                                audio_bytes,
                                caption=caption,
                                button=(telegram.OPEN_INCIDENT_BUTTON, telegram.incident_url(event_id)),
                            )
                            if ok:
                                runlog(f"{event_id}: Audio Briefing terkirim ke Telegram")
                            else:
                                runlog(f"{event_id}: Audio Briefing tidak terkirim ke Telegram", logging.WARNING)
                        except Exception as exc:  # noqa: BLE001
                            runlog(f"{event_id}: Telegram send_voice gagal — {exc}", logging.WARNING)
        except Exception as exc:  # noqa: BLE001 - audio failure never breaks the run
            runlog(f"{event_id}: Audio Briefing gagal dibuat — {exc}", logging.WARNING)

    runlog(
        f"Selesai: {stats.scanned} dipindai, {stats.failed} gagal, {stats.incidents_new} Incident baru, "
        f"{stats.escalations} Escalation, kredit {client.credits_used}"
    )
    with session_scope() as session:
        run = session.get(AuditRun, run_id)
        assert run is not None
        run.status = RunStatus.SUCCESS.value
        run.finished_at = utcnow()
        _write_counts(run, client, stats, runlog)

    _safe_send(
        send,
        runlog,
        telegram.format_run_summary(
            started_at=started_at,
            trigger=trigger,
            emiten_scanned=stats.scanned,
            incidents_new=stats.incidents_new,
            escalations=stats.escalations,
            emiten_failed=stats.failed,
            credits_used=client.credits_used,
        ),
    )

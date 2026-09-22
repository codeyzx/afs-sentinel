"""Batch Sector Extraction & Audit Pipeline.

1. Wipes previous audit runs, incidents, evaluations, triage, and api_cache (clean slate).
2. Syncs universe to identify all active emiten and their sectors.
3. Iterates over each sector in batches, running Audit Run with trigger=SCHEDULER.
4. Runs a consolidated full-universe audit (trigger=SCHEDULER) for complete dashboard status.
"""

from __future__ import annotations

import logging
import sys
from sqlalchemy import text

from afs import runner
from afs.config import get_settings
from afs.db import init_db, session_scope
from afs.domain import RunStatus, RunTrigger
from afs.models import AuditRun
from afs.sectors.client import SectorsClient
from afs.sectors.repository import DataRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("batch_sector_audit")


def reset_data() -> None:
    log.info("Membersihkan data cache dan audit logs...")
    tables = [
        "incident_insights",
        "incident_events",
        "emiten_evaluations",
        "incidents",
        "audit_runs",
        "api_cache",
        "locks",
    ]
    with session_scope() as session:
        try:
            session.execute(text("TRUNCATE TABLE incident_insights, incident_events, emiten_evaluations, incidents, audit_runs, api_cache, locks RESTART IDENTITY CASCADE;"))
            session.commit()
            log.info("Semua tabel cache dan audit logs berhasil dikosongkan.")
        except Exception as e:
            log.warning(f"TRUNCATE gagal, mencoba DELETE: {e}")
            session.rollback()
            for t in tables:
                try:
                    session.execute(text(f"DELETE FROM {t};"))
                    session.commit()
                    log.info(f"Tabel {t} dikosongkan.")
                except Exception as inner_e:
                    session.rollback()
                    log.warning(f"Gagal menghapus {t}: {inner_e}")
    log.info("Reset data selesai.")


def run_batch() -> None:
    init_db()
    reset_data()

    # Discover sectors
    with session_scope() as session:
        repo = DataRepository(session, SectorsClient())
        active = repo.sync_universe()
        by_sector: dict[str, list[str]] = {}
        for e in active:
            if e.sector:
                by_sector.setdefault(e.sector, []).append(e.symbol)

    sectors = sorted(by_sector.keys())
    total_emiten = sum(len(v) for v in by_sector.values())
    log.info(f"Ditemukan {len(sectors)} sektor aktif dengan total {total_emiten} emiten:")
    for s in sectors:
        log.info(f"  - {s} ({len(by_sector[s])} emiten): {', '.join(by_sector[s])}")

    # Process each sector batch
    for i, sec in enumerate(sectors, 1):
        log.info(f"\n==================================================")
        log.info(f"[{i}/{len(sectors)}] MEMPROSES BATCH SEKTOR: {sec}")
        log.info(f"Emiten ({len(by_sector[sec])}): {', '.join(by_sector[sec])}")
        log.info(f"==================================================")
        try:
            run_id = runner.run_audit(RunTrigger.SCHEDULER, sector=sec)
            with session_scope() as session:
                run = session.get(AuditRun, run_id)
                status = run.status if run else "UNKNOWN"
                credits_used = run.credits_used if run else 0
                scanned = run.emiten_scanned if run else 0
            log.info(f"Batch {sec} selesai: Run #{run_id} | Status: {status} | Scanned: {scanned} | Credits: {credits_used}")
        except Exception as e:
            log.exception(f"Batch {sec} error: {e}")

    # Final consolidated run across all 33 emiten
    log.info("\n==================================================")
    log.info("MEMPROSES KONSOLIDASI SEMUA SEKTOR (33 EMITEN)")
    log.info("==================================================")
    try:
        run_id = runner.run_audit(RunTrigger.SCHEDULER)
        with session_scope() as session:
            run = session.get(AuditRun, run_id)
            status = run.status if run else "UNKNOWN"
            credits_used = run.credits_used if run else 0
            scanned = run.emiten_scanned if run else 0
        log.info(f"Konsolidasi selesai: Run #{run_id} | Status: {status} | Scanned: {scanned} | Credits: {credits_used}")
    except Exception as e:
        log.exception(f"Konsolidasi error: {e}")


if __name__ == "__main__":
    run_batch()

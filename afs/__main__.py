"""Command line: python -m afs {initdb,run,backtest,sync-universe}."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from typing import Sequence


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m afs", description="AFS Sentinel")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("initdb", help="Buat tabel database")
    run = sub.add_parser("run", help="Jalankan Audit Run")
    run.add_argument("--scheduled", action="store_true", help="Dipanggil Heroku Scheduler: hanya berjalan hari Sabtu (WIB)")
    sub.add_parser("backtest", help="Jalankan Backtest (argumen diteruskan ke afs.backtest)", add_help=False)
    sub.add_parser("sync-universe", help="Sinkronkan Universe dan tampilkan Emiten")
    return parser


def cmd_initdb() -> int:
    from afs.db import init_db

    init_db()
    print("Database siap")
    return 0


def cmd_run(scheduled: bool) -> int:
    from afs import runner
    from afs.db import init_db, session_scope
    from afs.domain import RunStatus, RunTrigger
    from afs.models import AuditRun

    if scheduled and not runner.should_run_scheduled(datetime.now(timezone.utc)):
        print("Bukan hari Sabtu (WIB); Audit Run terjadwal dilewati")
        return 0

    init_db()
    trigger = RunTrigger.SCHEDULER if scheduled else RunTrigger.MANUAL
    try:
        run_id = runner.run_audit(trigger)
    except runner.RunInProgressError as exc:
        print(str(exc))
        return 1

    with session_scope() as session:
        run = session.get(AuditRun, run_id)
        status = run.status if run is not None else RunStatus.FAILED.value
    print(f"Audit Run #{run_id}: {status}")
    return 1 if status == RunStatus.FAILED.value else 0


def cmd_backtest(argv: list[str]) -> int:
    try:
        from afs import backtest
    except ImportError as exc:
        print(f"Modul backtest belum tersedia: {exc}", file=sys.stderr)
        return 1
    return int(backtest.main(argv) or 0)


def cmd_sync_universe() -> int:
    from sqlalchemy import select

    from afs.db import init_db, session_scope
    from afs.models import Emiten
    from afs.sectors.client import SectorsClient
    from afs.sectors.repository import DataRepository

    init_db()
    with session_scope() as session:
        DataRepository(session, SectorsClient()).sync_universe()
        for emiten in session.scalars(select(Emiten).order_by(Emiten.symbol)):
            flag = "excluded" if emiten.is_excluded else "active"
            print(f"{emiten.symbol}\t{flag}\t{emiten.company_name}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    # backtest owns its own options (--case, --dry-run, ...): pass everything after the command through.
    if args_list and args_list[0] == "backtest":
        return cmd_backtest(args_list[1:])

    args = _build_parser().parse_args(args_list)
    match args.command:
        case "initdb":
            return cmd_initdb()
        case "run":
            return cmd_run(args.scheduled)
        case "sync-universe":
            return cmd_sync_universe()
    return 2


if __name__ == "__main__":
    sys.exit(main())

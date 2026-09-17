from afs.db import session_scope
from afs.models import AuditRun


def test_tables_create_and_roundtrip(engine):
    with session_scope() as s:
        s.add(AuditRun(trigger="MANUAL", status="RUNNING"))
    with session_scope() as s:
        assert s.query(AuditRun).count() == 1

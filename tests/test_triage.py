from datetime import date

import pytest

from afs.db import session_scope
from afs.domain import IncidentEventKind, TriageStatus
from afs.models import Incident, IncidentEvent
from afs.triage import update_triage

EVENT_ID = "AFS-2025-Q3-0001"


def _add_incident(s):
    s.add(Incident(event_id=EVENT_ID, symbol="EMTK.JK", report_date=date(2025, 9, 30), score=75.0, severity="CRITICAL"))
    s.flush()


def _events(s):
    return [(e.kind, e.from_value, e.to_value) for e in s.query(IncidentEvent).order_by(IncidentEvent.id)]


def test_status_change_records_event(engine):
    with session_scope() as s:
        _add_incident(s)
        inc = update_triage(s, EVENT_ID, status=TriageStatus.INVESTIGATING, notes=None)
        assert inc.triage_status == "INVESTIGATING"
    with session_scope() as s:
        assert _events(s) == [(IncidentEventKind.TRIAGE_CHANGED, "UNTRIAGED", "INVESTIGATING")]


def test_notes_change_records_event_and_no_op_records_nothing(engine):
    with session_scope() as s:
        _add_incident(s)
        update_triage(s, EVENT_ID, status=TriageStatus.UNTRIAGED, notes="cek laporan")
        update_triage(s, EVENT_ID, status=TriageStatus.UNTRIAGED, notes="cek laporan  ")
    with session_scope() as s:
        assert _events(s) == [(IncidentEventKind.NOTE_UPDATED, None, None)]
        assert s.get(Incident, EVENT_ID).analyst_notes == "cek laporan"


def test_status_and_notes_together(engine):
    with session_scope() as s:
        _add_incident(s)
        update_triage(s, EVENT_ID, status=TriageStatus.DISMISSED, notes="alarm palsu")
    with session_scope() as s:
        kinds = [k for k, _, _ in _events(s)]
        assert kinds == [IncidentEventKind.TRIAGE_CHANGED, IncidentEventKind.NOTE_UPDATED]


def test_unknown_incident_raises(engine):
    with session_scope() as s, pytest.raises(KeyError):
        update_triage(s, "AFS-0000-Q1-0000", status=TriageStatus.RESOLVED, notes=None)

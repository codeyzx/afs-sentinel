"""Analyst triage actions on an Incident (docs/system-rules.md §5.4)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from afs.domain import IncidentEventKind, TriageStatus
from afs.models import Incident, IncidentEvent, utcnow


def update_triage(
    session: Session, event_id: str, *, status: TriageStatus | None, notes: str | None
) -> Incident:
    """Apply a Triage Status and/or notes change; each actual change is recorded in the Incident history.

    `None` means "leave unchanged". Raises KeyError when the Incident does not exist.
    """
    incident = session.get(Incident, event_id)
    if incident is None:
        raise KeyError(event_id)

    changed = False
    if status is not None and status.value != incident.triage_status:
        session.add(
            IncidentEvent(
                event_id=event_id,
                kind=IncidentEventKind.TRIAGE_CHANGED.value,
                from_value=incident.triage_status,
                to_value=status.value,
            )
        )
        incident.triage_status = status.value
        changed = True

    if notes is not None:
        notes = notes.replace("\r\n", "\n").strip()
        if notes != (incident.analyst_notes or ""):
            session.add(IncidentEvent(event_id=event_id, kind=IncidentEventKind.NOTE_UPDATED.value))
            incident.analyst_notes = notes
            changed = True

    if changed:
        incident.updated_at = utcnow()
    session.flush()
    return incident

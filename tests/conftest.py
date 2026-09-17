from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from afs import db


@pytest.fixture
def engine():
    """Fresh in-memory SQLite database with all tables, wired into afs.db.session_scope()."""
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    db.configure_engine(eng)
    from afs import models  # noqa: F401

    db.Base.metadata.create_all(eng)
    yield eng
    eng.dispose()

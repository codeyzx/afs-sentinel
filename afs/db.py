from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from afs.config import get_settings


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        url = get_settings().sqlalchemy_url
        if url.startswith("sqlite:///"):
            Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(url, pool_pre_ping=True)
        _SessionLocal = sessionmaker(_engine, expire_on_commit=False)
    return _engine


def configure_engine(engine: Engine) -> None:
    """Override the engine (tests)."""
    global _engine, _SessionLocal
    _engine = engine
    _SessionLocal = sessionmaker(engine, expire_on_commit=False)


def init_db() -> None:
    from afs import models  # noqa: F401  (register tables)

    Base.metadata.create_all(get_engine())


@contextmanager
def session_scope() -> Iterator[Session]:
    get_engine()
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

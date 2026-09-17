import json
import sys
import types
from datetime import date

import pytest
from fastapi.testclient import TestClient

from afs.config import Settings
from afs.db import session_scope
from afs.devseed import seed
from afs.models import Incident, IncidentEvent
from afs.web.app import create_app

PASSWORD = "rahasia-uji"


@pytest.fixture
def cases_path(tmp_path):
    path = tmp_path / "backtest_cases.json"
    path.write_text(json.dumps({"cases": [
        {"case_id": "WSKT", "symbol": "WSKT.JK", "company_name": "Waskita Karya",
         "events": [{"date": "2023-05-08", "label": "suspensi saham oleh BEI", "source_url": "https://example.com/wskt"}]},
        {"case_id": "SRIL", "symbol": "SRIL.JK", "company_name": "Sri Rejeki Isman",
         "events": [{"date": "2021-05-18", "label": "suspensi karena gagal bayar", "source_url": "https://example.com/a"},
                    {"date": "2024-10-21", "label": "pailit", "source_url": "https://example.com/b", "verified": False}]},
    ]}))
    return path


@pytest.fixture
def client(engine, cases_path):
    settings = Settings(_env_file=None, admin_password=PASSWORD, session_secret="test", backtest_cases_path=cases_path)
    return TestClient(create_app(settings))


@pytest.fixture
def seeded(engine):
    with session_scope() as s:
        seed(s)


def login(client):
    r = client.post("/login", data={"password": PASSWORD, "next": "/"}, follow_redirects=False)
    assert r.status_code == 303


PAGES = ["/", "/backtest", "/logs", "/login"]


@pytest.mark.parametrize("path", PAGES)
def test_pages_render_empty_db(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert "Sectors Hackathon 2026 · AFS Sentinel" in r.text


def test_empty_states(client):
    assert "Belum ada Audit Run" in client.get("/").text
    assert "Backtest belum dijalankan" in client.get("/backtest").text
    assert "Belum ada Audit Run" in client.get("/logs").text


def test_backtest_without_config_shows_hint(engine, tmp_path):
    settings = Settings(_env_file=None, backtest_cases_path=tmp_path / "missing.json")
    r = TestClient(create_app(settings)).get("/backtest")
    assert r.status_code == 200
    assert "python -m afs backtest" in r.text


@pytest.mark.parametrize("path", PAGES + ["/incidents/AFS-2026-Q2-0001", "/incidents/AFS-2026-Q2-0003"])
def test_pages_render_seeded(client, seeded, path):
    r = client.get(path)
    assert r.status_code == 200


def test_dashboard_content(client, seeded):
    text = client.get("/").text
    assert "Sloan Accrual Ratio" in text and "Seberapa banyak laba yang bukan uang tunai" in text
    assert "AFS-2026-Q2-0001" in text
    # untriaged incidents first, by score desc: EMTK (75) and GOTO (71.4) before WSKT (investigating)
    assert text.index("/incidents/AFS-2026-Q2-0001") < text.index("/incidents/AFS-2026-Q2-0003") < text.index(
        "/incidents/AFS-2026-Q2-0002"
    )
    for forbidden in ("Export PDF", "Rekomendasi", "Penanggung Jawab", "Watchlist"):
        assert forbidden not in text


def test_incident_detail_content(client, seeded):
    text = client.get("/incidents/AFS-2026-Q2-0001").text
    assert "EMTK — <strong" in text
    assert "(75,0/100)" in text
    assert "2026-Q2" in text
    assert "Kenapa ditandai" in text
    assert "cash-chart" in text
    assert "Masuk untuk mengubah status" in text
    assert "Escalation: Sedang → Kritis" in text
    # finding order: Bahaya before Waspada before Tak bisa dinilai
    assert text.index("Divergensi Laba–Kas") < text.index("Beneish (Adapted)") < text.index("Penjualan Orang Dalam")


def test_incident_404(client):
    r = client.get("/incidents/AFS-1999-Q1-0000")
    assert r.status_code == 404
    assert "Incident tidak ditemukan" in r.text


def test_backtest_seeded_claims(client, seeded):
    text = client.get("/backtest").text
    assert "Pertama kali Sedang: 2021-Q4, 16 bulan sebelum suspensi saham oleh BEI" in text
    assert "Pertama kali Sedang: 2021-Q1, 1 bulan sebelum suspensi karena gagal bayar" in text
    assert "Penjualan Orang Dalam tidak dinilai — data sebelum 2025 tidak tersedia" in text
    assert "https://example.com/wskt" in text


def test_login_wrong_and_right_password(client):
    r = client.post("/login", data={"password": "salah", "next": "/"})
    assert r.status_code == 401
    assert "Password salah" in r.text
    r = client.post("/login", data={"password": PASSWORD, "next": "/logs"}, follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/logs"
    assert "Keluar" in client.get("/").text
    client.post("/logout")
    assert "Masuk" in client.get("/").text


def test_login_next_rejects_external_redirect(client):
    r = client.post("/login", data={"password": PASSWORD, "next": "//evil.example"}, follow_redirects=False)
    assert r.headers["location"] == "/"


def test_triage_requires_login(client, seeded):
    r = client.post("/incidents/AFS-2026-Q2-0001/triage", data={"status": "RESOLVED"}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"].startswith("/login?next=/incidents/AFS-2026-Q2-0001")
    with session_scope() as s:
        assert s.get(Incident, "AFS-2026-Q2-0001").triage_status == "UNTRIAGED"


def test_triage_persists_and_records_events(client, seeded):
    login(client)
    r = client.post(
        "/incidents/AFS-2026-Q2-0001/triage", data={"status": "INVESTIGATING", "notes": "cek arus kas"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    with session_scope() as s:
        inc = s.get(Incident, "AFS-2026-Q2-0001")
        assert inc.triage_status == "INVESTIGATING" and inc.analyst_notes == "cek arus kas"
        kinds = [e.kind for e in s.query(IncidentEvent).filter_by(event_id="AFS-2026-Q2-0001")]
        assert "TRIAGE_CHANGED" in kinds and "NOTE_UPDATED" in kinds
    text = client.get("/incidents/AFS-2026-Q2-0001").text
    assert "Status triage: Belum ditinjau → Sedang diperiksa" in text
    assert "Perubahan triage disimpan" in text


def test_triage_unknown_incident_404(client):
    login(client)
    assert client.post("/incidents/NOPE/triage", data={"status": "RESOLVED"}).status_code == 404


def test_runs_requires_login(client):
    r = client.post("/runs", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/login")


def test_runs_without_runner_flashes(client, monkeypatch):
    monkeypatch.setitem(sys.modules, "afs.runner", None)  # import -> ImportError
    login(client)
    text = client.post("/runs").text
    assert "Runner belum tersedia" in text


def test_runs_starts_background_run(client, monkeypatch):
    calls = []
    fake = types.ModuleType("afs.runner")
    fake.is_run_in_progress = lambda: False
    fake.run_audit = lambda trigger: calls.append(trigger) or 1
    monkeypatch.setitem(sys.modules, "afs.runner", fake)
    login(client)
    assert "Audit Run dimulai" in client.post("/runs").text
    fake.is_run_in_progress = lambda: True
    assert "Audit Run sedang berjalan" in client.post("/runs").text
    import time

    for _ in range(50):
        if calls:
            break
        time.sleep(0.01)
    assert calls == ["MANUAL"]

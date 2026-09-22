import json
from datetime import date

import pytest
from fastapi.testclient import TestClient

from afs.config import Settings
from afs.db import session_scope
from afs.devseed import seed
from afs.models import Incident
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


def test_set_language_endpoint(client):
    # Set to English
    r = client.get("/set-language?lang=en&next=/logs", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/logs"
    assert "lang=en" in r.headers["set-cookie"]

    # Set to Indonesian
    r = client.get("/set-language?lang=id&next=/backtest", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/backtest"
    assert "lang=id" in r.headers["set-cookie"]

    # Invalid language falls back to id
    r = client.get("/set-language?lang=fr&next=/", follow_redirects=False)
    assert r.status_code == 303
    assert "lang=id" in r.headers["set-cookie"]

    # Open redirect prevention
    r = client.get("/set-language?lang=en&next=//evil.com", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/"


def test_language_switch_via_query_param(client):
    r_en = client.get("/?lang=en")
    assert r_en.status_code == 200
    assert '<html lang="en">' in r_en.text
    assert "Audit Logs" in r_en.text
    assert "lang=en" in r_en.headers.get("set-cookie", "")

    r_id = client.get("/?lang=id")
    assert r_id.status_code == 200
    assert '<html lang="id">' in r_id.text
    assert "Log Audit" in r_id.text
    assert "lang=id" in r_id.headers.get("set-cookie", "")


def test_language_switcher_dropdown_rendered(client):
    r = client.get("/")
    assert 'aria-label="Ganti bahasa"' in r.text
    assert "/set-language?lang=en" in r.text
    assert "/set-language?lang=id" in r.text


def test_dashboard_english_content(client, seeded):
    r = client.get("/?lang=en")
    text = r.text
    assert '<html lang="en">' in text
    assert "System active" in text or "System ready" in text
    assert "automatic scan every" in text
    assert "emiten scanned" in text
    assert "new Incidents" in text
    assert "Immediate attention needed" in text
    assert "Needs review" in text
    assert "Low risk" in text
    assert "Action required" in text
    assert "All monitored emiten" in text
    assert "Marker color = rule status" in text
    assert "Marker number = rule number" in text
    assert "Score" in text
    assert "Severity" in text
    assert "Rule status" in text


def test_incident_detail_english_content(client, seeded):
    r = client.get("/incidents/AFS-2026-Q2-0001?lang=en")
    text = r.text
    assert '<html lang="en">' in text
    assert "Report Period" in text
    assert "Detected" in text
    assert "Updated" in text
    assert "Triage status" in text
    assert "AI Summary" in text
    assert "Evidence and calculations" in text
    assert "View calculation details" in text
    assert "Formula" in text
    assert "Report inputs" in text
    assert "Thresholds" in text
    assert "History" in text
    assert "Net income vs operating cash flow" in text


def test_backtest_english_content(client, seeded):
    r = client.get("/backtest?lang=en")
    text = r.text
    assert '<html lang="en">' in text
    assert "All six Forensic Rules are re-evaluated" in text
    assert "First reached Moderate: 2021-Q4, 16 months before stock suspension by IDX" in text
    assert "Rule Findings per quarter" in text
    assert "Insider Selling not evaluated — data prior to 2025 is unavailable." in text
    assert "Event sources" in text


def test_logs_english_content(client, seeded):
    r = client.get("/logs?lang=en")
    text = r.text
    assert '<html lang="en">' in text
    assert "Audit Trail" in text
    assert "Every scan is recorded" in text
    assert "Started" in text
    assert "Duration" in text
    assert "Trigger" in text
    assert "Scanned / failed" in text
    assert "New Incidents" in text


def test_login_and_404_english_content(client):
    r = client.get("/login?lang=en")
    text = r.text
    assert '<html lang="en">' in text
    assert "Log in as analyst" in text
    assert "Password" in text
    assert "All pages can be viewed without logging in" in text

    # Wrong password in English
    client.cookies.set("lang", "en")
    r_wrong = client.post("/login", data={"password": "wrong", "next": "/"})
    assert r_wrong.status_code == 401
    assert "Incorrect password. Try again." in r_wrong.text

    # 404 in English
    r_404 = client.get("/incidents/NOT-A-REAL-ID?lang=en")
    assert r_404.status_code == 404
    assert '<html lang="en">' in r_404.text
    assert "Incident not found" in r_404.text
    assert "Back to Dashboard" in r_404.text

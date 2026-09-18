"""Incident Insight: parsing, storage, and the promise that a broken LLM cannot break an Audit Run."""

from __future__ import annotations

from datetime import date

import pytest

from afs import insight
from afs.db import session_scope
from afs.models import Incident, IncidentInsight

GOOD = """{"apa_yang_terjadi": "Laba naik tapi kas operasi turun.",
           "kenapa_penting": "Laba yang tidak diikuti kas sering tidak bertahan.",
           "yang_perlu_dicek": ["Piutang usaha", "Catatan atas laporan keuangan"]}"""


def make_incident(session, event_id="AFS-2025-Q3-0001", symbol="UNVR.JK"):
    incident = Incident(
        event_id=event_id,
        symbol=symbol,
        report_date=date(2025, 9, 30),
        score=45.0,
        severity="MODERATE",
        low_confidence=False,
        severity_reason=None,
        findings=[
            {
                "rule_id": "SLOAN_ACCRUAL",
                "status": "RED_FLAG",
                "value": 0.18,
                "thresholds": {"red_flag": 0.1},
                "inputs": {"values": [{"field": "earnings", "report_date": "2025-09-30", "value": 100}]},
                "headline": "Laba banyak yang bukan uang tunai",
                "missing": None,
            }
        ],
    )
    session.add(incident)
    session.flush()
    return incident


# ---------------------------------------------------------------- parsing


def test_parse_response_extracts_the_three_fields():
    fields = insight.parse_response(GOOD)
    assert fields["what_happened"] == "Laba naik tapi kas operasi turun."
    assert fields["why_it_matters"].startswith("Laba yang tidak")
    assert fields["what_to_check"] == ["Piutang usaha", "Catatan atas laporan keuangan"]


@pytest.mark.parametrize(
    "text",
    [
        "bukan json sama sekali",
        "[]",  # a list, not an object
        '{"apa_yang_terjadi": ""}',  # the one field that must not be empty
        '{"kenapa_penting": "ada", "yang_perlu_dicek": ["x"]}',  # missing apa_yang_terjadi
    ],
)
def test_parse_response_rejects_unusable_output(text):
    with pytest.raises(insight.InsightUnavailable):
        insight.parse_response(text)


def test_parse_response_tolerates_a_missing_or_odd_checklist():
    fields = insight.parse_response('{"apa_yang_terjadi": "Ada.", "yang_perlu_dicek": "bukan list"}')
    assert fields["what_to_check"] == [] and fields["why_it_matters"] == ""


# ---------------------------------------------------------------- facts


def test_facts_carry_only_what_the_pipeline_computed(engine):
    """The model must never be handed price, market cap, or anything outside this Audit Run."""
    with session_scope() as s:
        incident = make_incident(s)
        facts = insight.build_facts(incident, "Unilever Indonesia Tbk")

    assert facts["emiten"] == "UNVR" and facts["severity"] == "Sedang"
    assert facts["temuan"][0]["status"] == "Bahaya"
    assert facts["temuan"][0]["nilai"] == "18,0%"  # same wording the Analyst sees on screen
    flat = str(facts).lower()
    assert "market_cap" not in flat and "close_price" not in flat


# ---------------------------------------------------------------- generation


def test_generate_one_stores_a_versioned_row(engine):
    with session_scope() as s:
        make_incident(s)
        insight.generate_one(s, "AFS-2025-Q3-0001", run_id=None, call=lambda _p: GOOD)
        s.commit()

    with session_scope() as s:
        rows = insight.history_for(s, "AFS-2025-Q3-0001")
        assert len(rows) == 1
        assert rows[0].prompt_version == insight.PROMPT_VERSION and rows[0].model
        assert rows[0].severity == "MODERATE"  # the severity it narrated, for later comparison


def test_escalation_adds_a_version_instead_of_overwriting(engine):
    with session_scope() as s:
        make_incident(s)
        insight.generate_one(s, "AFS-2025-Q3-0001", call=lambda _p: GOOD)
        s.commit()
    with session_scope() as s:
        newer = GOOD.replace("Laba naik tapi kas operasi turun.", "Sekarang kritis.")
        insight.generate_one(s, "AFS-2025-Q3-0001", call=lambda _p: newer)
        s.commit()

    with session_scope() as s:
        rows = insight.history_for(s, "AFS-2025-Q3-0001")
        assert len(rows) == 2
        assert insight.latest_for(s, "AFS-2025-Q3-0001").what_happened == "Sekarang kritis."


def test_a_failing_llm_leaves_no_row_and_reports_it(engine):
    lines: list[str] = []
    with session_scope() as s:
        make_incident(s)
        s.commit()

    def boom(_prompt: str) -> str:
        raise insight.InsightUnavailable("HTTP 503")

    with session_scope() as s:
        made = insight.generate_for_run(s, 1, ["AFS-2025-Q3-0001"], log_line=lines.append, call=boom)

    assert made == {}
    assert any("gagal" in line and "HTTP 503" in line for line in lines)
    with session_scope() as s:
        assert insight.latest_for(s, "AFS-2025-Q3-0001") is None


def test_one_failure_does_not_stop_the_others(engine):
    with session_scope() as s:
        make_incident(s, "AFS-2025-Q3-0001")
        make_incident(s, "AFS-2025-Q3-0002", symbol="ASII.JK")
        s.commit()

    calls = {"n": 0}

    def flaky(_prompt: str) -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            raise insight.InsightUnavailable("timeout")
        return GOOD

    with session_scope() as s:
        made = insight.generate_for_run(s, 1, ["AFS-2025-Q3-0001", "AFS-2025-Q3-0002"], call=flaky)

    assert list(made) == ["AFS-2025-Q3-0002"]


def test_an_unexpected_exception_is_contained_too(engine):
    """Anything at all from the LLM path must stay inside afs.insight (§6.2, ADR-0003)."""
    with session_scope() as s:
        make_incident(s)
        s.commit()

    def explode(_prompt: str) -> str:
        raise ZeroDivisionError("surprise")

    with session_scope() as s:
        assert insight.generate_for_run(s, 1, ["AFS-2025-Q3-0001"], call=explode) == {}


def test_missing_api_key_is_an_insight_failure_not_a_crash(engine, monkeypatch):
    from afs.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("GEMINI_API_KEY", "")
    with pytest.raises(insight.InsightUnavailable):
        insight._call_gemini("halo")
    get_settings.cache_clear()

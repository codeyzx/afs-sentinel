"""Tests for afs.audio — audio script creation, synthesis, and disk caching."""

from __future__ import annotations

import asyncio
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from afs import audio
from afs.config import get_settings
from afs.db import session_scope
from afs.models import Incident, IncidentInsight


def make_incident(event_id="AFS-AUDIO-001", symbol="WSKT.JK", score=85.0, severity="CRITICAL"):
    return Incident(
        event_id=event_id,
        symbol=symbol,
        report_date=date(2023, 9, 30),
        score=score,
        severity=severity,
        severity_reason="Minimal Kritis karena Altman dan Sloan",
        findings=[
            {
                "rule_id": "SLOAN_ACCRUAL",
                "status": "RED_FLAG",
                "value": 0.18,
                "headline": "Laba banyak yang bukan uang tunai",
            },
            {
                "rule_id": "EARNINGS_CASH_DIVERGENCE",
                "status": "RED_FLAG",
                "value": None,
                "headline": "Laba naik tetapi kas operasi turun",
            },
            {
                "rule_id": "ALTMAN_Z_ADAPTED",
                "status": "RED_FLAG",
                "value": 1.25,
                "headline": "Zona bahaya distress",
            },
            {
                "rule_id": "BENEISH_ADAPTED",
                "status": "WARNING",
                "value": 2,
                "headline": "Dua indeks melewati ambang batas",
            },
            {
                "rule_id": "INSIDER_SELLING",
                "status": "WARNING",
                "value": 0.015,
                "headline": "Penjualan orang dalam 1.5%",
            },
            {
                "rule_id": "EARNINGS_WITHOUT_DIVIDEND",
                "status": "WARNING",
                "value": None,
                "headline": "Untung tanpa dividen",
            },
        ],
    )


def test_build_audio_script_covers_four_parts_and_duration():
    inc = make_incident()
    ins = IncidentInsight(
        event_id=inc.event_id,
        severity=inc.severity,
        what_happened="Pertumbuhan laba bersih tidak didukung oleh realisasi kas operasional.",
        why_it_matters="Jurang antara laba akrual dan kas memperbesar risiko insolvensi.",
        what_to_check=["Periksa penagihan piutang", "Analisis utang jangka pendek"],
    )

    script = audio.build_audio_script(inc, company_name="PT Waskita Karya Tbk", insight_row=ins)

    # Check key segments
    assert "Halo Analis" in script
    assert "Waskita Karya" in script
    assert "WSKT" in script
    assert "Kritis" in script
    assert "85" in script
    assert "Sloan" in script
    assert "Altman Z" in script
    assert "Langkah verifikasi prioritas" in script
    assert "Periksa penagihan piutang" in script
    assert "web Sentinel" in script

    words = script.split()
    # Ensure optimal duration (~1.5 - 2.5 minutes, 180 - 320 words)
    assert 150 <= len(words) <= 350


def test_build_audio_script_without_insight_still_generates_coherent_briefing():
    inc = make_incident(score=60.0, severity="MODERATE")
    script = audio.build_audio_script(inc, company_name="Waskita Karya", insight_row=None)

    assert "Halo Analis" in script
    assert "Sedang" in script
    assert "60" in script
    assert "web Sentinel" in script
    words = script.split()
    assert len(words) >= 120


def test_describe_finding_handles_all_rules():
    assert "Sloan" in audio._describe_finding("SLOAN_ACCRUAL", "RED_FLAG", 0.15, "")
    assert "divergensi" in audio._describe_finding("EARNINGS_CASH_DIVERGENCE", "RED_FLAG", None, "").lower()
    assert "Altman Z" in audio._describe_finding("ALTMAN_Z_ADAPTED", "RED_FLAG", 1.5, "")
    assert "Beneish" in audio._describe_finding("BENEISH_ADAPTED", "WARNING", 2, "")
    assert "penjualan saham" in audio._describe_finding("INSIDER_SELLING", "WARNING", 0.02, "").lower()
    assert "dividen kas" in audio._describe_finding("EARNINGS_WITHOUT_DIVIDEND", "WARNING", None, "").lower()
    assert "CUSTOM_RULE" in audio._describe_finding("CUSTOM_RULE", "WARNING", 5, "Headline kustom")


def test_synthesize_speech_mocked(monkeypatch):
    class FakeCommunicate:
        def __init__(self, text, voice):
            self.text = text
            self.voice = voice

        async def stream(self):
            yield {"type": "audio", "data": b"CHUNK1"}
            yield {"type": "audio", "data": b"CHUNK2"}

    monkeypatch.setattr("edge_tts.Communicate", FakeCommunicate)

    result = audio.synthesize_speech("Tes naskah", voice="id-ID-ArdiNeural")
    assert result == b"CHUNK1CHUNK2"


def test_synthesize_speech_empty_raises_audio_unavailable(monkeypatch):
    class FakeEmptyCommunicate:
        def __init__(self, text, voice):
            pass

        async def stream(self):
            if False:
                yield {}

    monkeypatch.setattr("edge_tts.Communicate", FakeEmptyCommunicate)

    with pytest.raises(audio.AudioUnavailable):
        audio.synthesize_speech("Tes naskah")


def test_get_or_create_incident_audio_caching(tmp_path, monkeypatch, engine):
    monkeypatch.setattr(get_settings(), "audio_dir", tmp_path)

    inc = make_incident(event_id="AFS-CACHE-001")
    with session_scope() as s:
        s.add(inc)
        s.commit()

    synth_mock = patch("afs.audio.synthesize_speech", return_value=b"SYNTHESIZED_MP3")

    with synth_mock as mock_fn:
        with session_scope() as s:
            loaded_inc = s.get(Incident, "AFS-CACHE-001")
            data1, script1 = audio.get_or_create_incident_audio(s, loaded_inc, "Waskita")
            assert data1 == b"SYNTHESIZED_MP3"
            assert mock_fn.call_count == 1

        # Second call should read from disk cache, not re-synthesize
        with session_scope() as s:
            loaded_inc = s.get(Incident, "AFS-CACHE-001")
            data2, script2 = audio.get_or_create_incident_audio(s, loaded_inc, "Waskita")
            assert data2 == b"SYNTHESIZED_MP3"
            assert mock_fn.call_count == 1  # Still 1, cache hit!


def test_build_run_summary_audio_script(engine):
    from datetime import datetime, timezone
    from afs.models import AuditRun

    run = AuditRun(
        id=1,
        started_at=datetime(2026, 9, 22, 1, 0, tzinfo=timezone.utc),
        emiten_scanned=33,
        incidents_new=2,
        escalations=1,
    )
    with session_scope() as s:
        script = audio.build_run_summary_audio_script(s, run)
    assert "Halo Analis" in script
    assert "33 emiten" in script
    assert "2 insiden baru" in script
    assert "web Sentinel" in script


def test_build_emiten_profile_audio_script(engine):
    from afs.models import Emiten, EmitenEvaluation

    with session_scope() as s:
        s.add(Emiten(symbol="INDF.JK", company_name="Indofood Sukses Makmur", sector="Consumer Non-Cyclicals"))
        s.add(EmitenEvaluation(
            run_id=1,
            symbol="INDF.JK",
            report_date=date(2026, 6, 30),
            score=20.0,
            severity="LOW",
            findings=[],
        ))
        s.commit()

    with session_scope() as s:
        script = audio.build_emiten_profile_audio_script(s, "INDF.JK")

    assert "Halo Analis" in script
    assert "Indofood Sukses Makmur" in script
    assert "INDF" in script
    assert "Rendah" in script
    assert "20 dari seratus" in script

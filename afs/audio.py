"""Incident Audio Briefing — Concise spoken executive narration (~1.5–2.5 minutes)
for multi-tasking analysts who prefer listening over reading walls of text.

Uses Microsoft Edge Neural TTS (100% free, zero cost, no API keys).
Audio output is standard MP3, streamed to Web and sent as Telegram Voice Note.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from pathlib import Path
from typing import Any

import edge_tts
from sqlalchemy import select
from sqlalchemy.orm import Session

from afs.config import WIB, get_settings
from afs.domain import FindingStatus, Severity, quarter_label
from afs.labels import RULE_META, SEVERITY_LABEL
from afs.models import AuditRun, Emiten, EmitenEvaluation, Incident, IncidentInsight

log = logging.getLogger(__name__)


class AudioUnavailable(RuntimeError):
    """Audio generation failed or TTS service could not be reached."""


# ---------------------------------------------------------------- script building


def _describe_finding(rule_id: str, status: str, value: Any, headline: str) -> str:
    """Conversational spoken description for a flagged rule finding."""
    meta = RULE_META.get(rule_id)
    rule_name = meta.name if meta else rule_id

    if rule_id == "SLOAN_ACCRUAL":
        pct = f"{round(float(value) * 100, 1)} persen".replace(".", ",") if value is not None else ""
        return (
            f"Pada pengujian akrual Sloan, tercatat rasio sebesar {pct}. "
            "Hal ini mengindikasikan porsi laba bersih perusahaan didominasi oleh akrual non-kas "
            "dan bukan berasal dari arus kas operasional riil."
        )
    if rule_id == "EARNINGS_CASH_DIVERGENCE":
        return (
            "Terjadi divergensi signifikan antara laba dan arus kas, "
            "di mana tren kenaikan laba bersih yang dibukukan tidak selaras dengan penurunan arus kas dari aktivitas operasi."
        )
    if rule_id == "ALTMAN_Z_ADAPTED":
        val_str = f"{round(float(value), 2)}".replace(".", ",") if value is not None else ""
        return (
            f"Skor kesehatan keuangan Altman Z berada pada angka {val_str}, "
            "yang menempatkan emiten dalam zona rawan tekanan likuiditas dan risiko kesulitan keuangan."
        )
    if rule_id == "BENEISH_ADAPTED":
        return (
            "Indeks Beneish mendeteksi anomali pada pertumbuhan piutang atau struktur margin, "
            "yang mengarah pada indikasi tekanan pelaporan akuntansi agresif."
        )
    if rule_id == "INSIDER_SELLING":
        return (
            "Terpantau adanya aksi penjualan saham dalam volume signifikan oleh pihak internal atau pemegang saham utama "
            "dalam periode pemantauan terakhir."
        )
    if rule_id == "EARNINGS_WITHOUT_DIVIDEND":
        return (
            "Perusahaan mencatatkan laba positif namun tidak membagikan dividen kas kepada pemegang saham "
            "selama satu tahun buku terakhir."
        )

    # Generic fallback
    if headline:
        return f"Pada aturan {rule_name}: {headline}."
    return f"Aturan {rule_name} berstatus waspada dengan nilai {value}."


def build_audio_script(
    incident: Incident,
    company_name: str = "",
    insight_row: IncidentInsight | dict[str, Any] | None = None,
) -> str:
    """Build a rich 1.5–2.5 minute (~200–300 words) spoken broadcast script for analysts.

    Segments:
    1. Greeting & emiten identification, quarter, severity level, composite score.
    2. Primary anomaly story & flagged rules in natural Indonesian narrative.
    3. Business implications & liquidity risk impact.
    4. Practical action checklist for the analyst to verify on the Sentinel web dashboard.
    5. Closing call-to-action.
    """
    ticker = incident.symbol.removesuffix(".JK")
    full_name = company_name or ticker
    period = quarter_label(incident.report_date)
    score_int = int(round(incident.score)) if incident.score is not None else 0

    sev_enum = Severity(incident.severity) if incident.severity in Severity.__members__.values() else Severity.MODERATE
    sev_text = SEVERITY_LABEL.get(sev_enum, incident.severity or "Perhatian")

    paragraphs: list[str] = []

    # 1. Opening & Status
    intro = (
        f"Halo Analis, berikut ringkasan audit forensik Sentinel untuk {full_name}, kode saham {ticker}, "
        f"pada laporan keuangan periode {period}. "
        f"Sistem menandai emiten ini dengan status {sev_text}, dengan skor risiko komposit {score_int} dari seratus."
    )
    if incident.severity_reason:
        intro += f" Catatan pemicu status: {incident.severity_reason}."
    paragraphs.append(intro)

    # Extract insight fields if available
    what_happened = ""
    why_it_matters = ""
    what_to_check: list[str] = []

    if isinstance(insight_row, IncidentInsight):
        what_happened = (insight_row.what_happened or "").strip()
        why_it_matters = (insight_row.why_it_matters or "").strip()
        what_to_check = list(insight_row.what_to_check or [])
    elif isinstance(insight_row, dict):
        what_happened = str(insight_row.get("what_happened") or "").strip()
        why_it_matters = str(insight_row.get("why_it_matters") or "").strip()
        raw_checks = insight_row.get("what_to_check") or []
        what_to_check = [str(c) for c in raw_checks if str(c).strip()] if isinstance(raw_checks, list) else []

    # 2. Anomaly Narrative
    story_parts: list[str] = []
    if what_happened:
        story_parts.append(f"Mengenai pola utama temuan: {what_happened}")

    flagged = [
        f for f in (incident.findings or [])
        if f.get("status") in (FindingStatus.RED_FLAG.value, FindingStatus.WARNING.value, "RED_FLAG", "WARNING")
    ]

    if flagged:
        story_parts.append("Secara spesifik, evaluasi sistem mendeteksi poin krusial berikut:")
        for f in flagged[:3]:  # Top 3 findings
            desc = _describe_finding(
                f.get("rule_id", ""),
                f.get("status", ""),
                f.get("value"),
                f.get("headline", ""),
            )
            story_parts.append(desc)
    else:
        story_parts.append(
            "Meskipun tidak ada pelanggaran ambang batas ekstrem, akumulasi indikator risiko "
            "menunjukkan pola akuntansi yang patut dicermati lebih lanjut."
        )

    paragraphs.append(" ".join(story_parts))

    # 3. Implication & Why it matters
    if why_it_matters:
        paragraphs.append(f"Mengapa hal ini krusial: {why_it_matters}")
    else:
        paragraphs.append(
            "Mengapa hal ini krusial: ketidakselarasan antara laba yang dibukukan dengan arus kas masuk riil "
            "merupakan indikator awal tekanan likuiditas dan dapat memicu kendala pemenuhan kewajiban utang jangka pendek."
        )

    # 4. Action Checklist for Analyst
    if what_to_check:
        checks_text = ", ".join(f"poin {idx+1}, {chk}" for idx, chk in enumerate(what_to_check[:3]))
        paragraphs.append(
            f"Langkah verifikasi prioritas bagi analis di web Sentinel: {checks_text}."
        )
    else:
        paragraphs.append(
            "Langkah verifikasi prioritas: periksa catatan atas laporan keuangan pada pos piutang dan liabilitas jangka pendek, "
            "serta pastikan apakah terdapat transaksi pihak berelasi yang tidak biasa."
        )

    # 5. Outro
    paragraphs.append(
        "Tabel bukti lengkap, formula rule, dan perincian historis dapat Anda telusuri langsung di halaman web Sentinel. "
        "Selamat melanjutkan analisis."
    )

    return "\n\n".join(paragraphs)


# ---------------------------------------------------------------- TTS synthesis


async def synthesize_speech_async(text: str, voice: str | None = None) -> bytes:
    """Synthesize text into MP3 audio bytes using edge-tts."""
    settings = get_settings()
    voice_name = voice or settings.tts_voice
    communicate = edge_tts.Communicate(text=text, voice=voice_name)
    chunks: list[bytes] = []
    try:
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio" and "data" in chunk:
                chunks.append(chunk["data"])
    except Exception as exc:
        log.exception("edge-tts synthesis failed")
        raise AudioUnavailable(f"TTS synthesis error: {exc}") from exc

    audio_bytes = b"".join(chunks)
    if not audio_bytes:
        raise AudioUnavailable("TTS generated 0 bytes of audio")
    return audio_bytes


def synthesize_speech(text: str, voice: str | None = None) -> bytes:
    """Synchronous entry point for TTS synthesis.

    Safely handles both plain synchronous execution and cases where an asyncio
    event loop is already running in the current thread.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, synthesize_speech_async(text, voice))
            return future.result(timeout=60.0)

    return asyncio.run(synthesize_speech_async(text, voice))


# ---------------------------------------------------------------- caching & retrieval


def get_audio_cache_path(event_id: str) -> Path:
    """Path to the cached MP3 file for an incident."""
    audio_dir = get_settings().audio_dir
    audio_dir.mkdir(parents=True, exist_ok=True)
    return audio_dir / f"{event_id}.mp3"


def get_or_create_incident_audio(
    session: Session,
    incident: Incident,
    company_name: str = "",
    insight_row: IncidentInsight | None = None,
    voice: str | None = None,
    force_refresh: bool = False,
) -> tuple[bytes, str]:
    """Retrieve existing cached audio, or build script and synthesize on-demand.

    Returns (audio_bytes, script_text).
    Raises AudioUnavailable if TTS synthesis fails.
    """
    cache_path = get_audio_cache_path(incident.event_id)

    # Build script
    script = build_audio_script(incident, company_name=company_name, insight_row=insight_row)

    if not force_refresh and cache_path.is_file():
        try:
            audio_bytes = cache_path.read_bytes()
            if audio_bytes:
                return audio_bytes, script
        except OSError:
            log.warning("Could not read cached audio from %s", cache_path)

    # Synthesize new audio
    audio_bytes = synthesize_speech(script, voice=voice)

    # Write cache
    try:
        cache_path.write_bytes(audio_bytes)
    except OSError as exc:
        log.warning("Could not cache audio file to %s: %s", cache_path, exc)

    return audio_bytes, script


# ---------------------------------------------------------------- Run summary audio


def build_run_summary_audio_script(session: Session, run: AuditRun | None) -> str:
    """Build a concise ~1 minute (~120–160 words) spoken overview of the latest Audit Run."""
    if run is None or run.started_at is None:
        return (
            "Halo Analis, belum ada data pemindaian audit run di sistem Sentinel. "
            "Silakan jalankan pemindaian terlebih dahulu melalui tombol Run Now di dashboard."
        )

    local_dt = run.started_at.astimezone(WIB)
    month_names = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    ]
    date_str = f"{local_dt.day} {month_names[local_dt.month - 1]} {local_dt.year}"

    scanned = run.emiten_scanned or 0
    new_inc = run.incidents_new or 0
    escalations = run.escalations or 0

    critical_incidents = list(
        session.scalars(
            select(Incident)
            .where(Incident.severity == Severity.CRITICAL.value)
            .order_by(Incident.score.desc())
        ).all()
    )

    paragraphs = [
        f"Halo Analis, berikut ringkasan eksekutif Sentinel untuk pemindaian bursa pada tanggal {date_str}. "
        f"Sistem telah selesai memindai {scanned} emiten aktif di Bursa Efek Indonesia."
    ]

    if new_inc > 0 or escalations > 0:
        details = (
            f"Hasil pemindaian mendeteksi {new_inc} insiden baru dan {escalations} kenaikan eskalasi risiko."
        )
        if critical_incidents:
            top_symbols = [inc.symbol.removesuffix(".JK") for inc in critical_incidents[:3]]
            details += f" Emiten yang memerlukan perhatian prioritas utama adalah {', '.join(top_symbols)}."
        paragraphs.append(details)
        paragraphs.append(
            "Sebagian besar emiten lainnya terpantau berada dalam batas parameter risiko aman. "
            "Analis disarankan segera meninjau dashboard web Sentinel untuk memulai triase pada antrean insiden teratas. "
            "Selamat bertugas."
        )
    else:
        paragraphs.append(
            "Hasil pemindaian menunjukkan kondisi bursa relatif tenang tanpa ada temuan insiden baru maupun kenaikan eskalasi risiko."
        )
        paragraphs.append(
            "Seluruh emiten yang dipindai berada dalam parameter normal dan wajar. "
            "Anda dapat memantau status berkala di dashboard web Sentinel. Selamat beraktivitas."
        )

    return "\n\n".join(paragraphs)


def get_or_create_run_audio(
    session: Session,
    run: AuditRun | None,
    voice: str | None = None,
    force_refresh: bool = False,
) -> tuple[bytes, str]:
    """Retrieve or synthesize the global run summary audio (~1 min)."""
    run_key = f"run_{run.id}" if run and run.id else "run_latest"
    cache_path = get_audio_cache_path(run_key)
    script = build_run_summary_audio_script(session, run)

    if not force_refresh and cache_path.is_file():
        try:
            audio_bytes = cache_path.read_bytes()
            if audio_bytes:
                return audio_bytes, script
        except OSError:
            pass

    audio_bytes = synthesize_speech(script, voice=voice)
    try:
        cache_path.write_bytes(audio_bytes)
    except OSError as exc:
        log.warning("Could not cache run audio to %s: %s", cache_path, exc)

    return audio_bytes, script


# ---------------------------------------------------------------- Emiten profile audio


def build_emiten_profile_audio_script(session: Session, symbol: str) -> str:
    """Build a concise ~1 minute (~120–160 words) spoken company health profile."""
    clean_sym = symbol.removesuffix(".JK") + ".JK"
    ticker = symbol.removesuffix(".JK")
    emiten = session.scalar(select(Emiten).where(Emiten.symbol == clean_sym))
    company_name = emiten.company_name if emiten else ticker
    sector_info = f", sektor {emiten.sector}" if emiten and emiten.sector else ""

    evals = list(
        session.scalars(
            select(EmitenEvaluation)
            .where(EmitenEvaluation.symbol == clean_sym)
            .order_by(EmitenEvaluation.report_date.desc())
        ).all()
    )
    incidents = list(
        session.scalars(
            select(Incident)
            .where(Incident.symbol == clean_sym)
            .order_by(Incident.report_date.desc())
        ).all()
    )

    paragraphs = [
        f"Halo Analis, berikut profil kesehatan forensik untuk {company_name}, kode saham {ticker}{sector_info}."
    ]

    if evals:
        latest_ev = evals[0]
        period = quarter_label(latest_ev.report_date)
        score_int = int(round(latest_ev.score)) if latest_ev.score is not None else 0
        sev_enum = Severity(latest_ev.severity) if latest_ev.severity in Severity.__members__.values() else Severity.LOW
        sev_text = SEVERITY_LABEL.get(sev_enum, latest_ev.severity or "Aman")

        narrative = (
            f"Berdasarkan evaluasi laporan keuangan periode {period}, emiten ini memiliki skor risiko komposit {score_int} dari seratus, "
            f"dengan tingkat keparahan {sev_text}."
        )
        if latest_ev.severity == Severity.CRITICAL.value:
            narrative += " Terpantau kombinasi anomali akuntansi serius pada kualitas laba atau solvabilitas utang."
        elif latest_ev.severity == Severity.MODERATE.value:
            narrative += " Terdapat beberapa indikator peringatan yang memerlukan pengawasan berkala pada perputaran kas."
        else:
            narrative += " Indikator fundamental dan rasio akrual berada dalam batas wajar, tanpa ada sinyal manipulasi laba."
        paragraphs.append(narrative)
    else:
        paragraphs.append(
            "Emiten ini terdaftar dalam Universe pemantauan dan belum memiliki riwayat evaluasi kuartalan yang terdata."
        )

    if incidents:
        cnt = len(incidents)
        paragraphs.append(
            f"Dalam catatan Sentinel, emiten ini memiliki riwayat {cnt} insiden forensik. "
            "Rincian formula dan tabel perbandingan historis dapat Anda telusuri langsung di tabel universe dashboard Sentinel."
        )
    else:
        paragraphs.append(
            "Tidak ada catatan insiden aktif untuk emiten ini. "
            "Anda dapat memantau pergerakan arus kas dan laba historis di dashboard Sentinel."
        )

    return "\n\n".join(paragraphs)


def get_or_create_emiten_audio(
    session: Session,
    symbol: str,
    voice: str | None = None,
    force_refresh: bool = False,
) -> tuple[bytes, str]:
    """Retrieve or synthesize the emiten health overview audio (~1 min)."""
    clean_sym = symbol.removesuffix(".JK")
    cache_path = get_audio_cache_path(f"emiten_{clean_sym}")
    script = build_emiten_profile_audio_script(session, symbol)

    if not force_refresh and cache_path.is_file():
        try:
            audio_bytes = cache_path.read_bytes()
            if audio_bytes:
                return audio_bytes, script
        except OSError:
            pass

    audio_bytes = synthesize_speech(script, voice=voice)
    try:
        cache_path.write_bytes(audio_bytes)
    except OSError as exc:
        log.warning("Could not cache emiten audio to %s: %s", cache_path, exc)

    return audio_bytes, script

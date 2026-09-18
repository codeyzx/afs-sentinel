"""Incident Insight — LLM narration of Rule Findings (CONTEXT.md, docs/adr/0003-*).

The LLM is a translator, never a judge: it is given only facts the deterministic pipeline
already computed, and its output never touches the Composite Risk Score or Incident Severity.
Every HTTP detail, prompt and parse failure is contained in this module; callers get an object
or None, and a None never fails an Audit Run.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Sequence

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from afs.config import get_settings
from afs.labels import RULE_META
from afs.models import Incident, IncidentInsight

# Display formatting on purpose: the model should see the same wording the Analyst sees,
# so its narration and the cards below it cannot disagree.
from afs.web.formatting import finding_label, fmt_finding_value, severity_label

log = logging.getLogger(__name__)

PROMPT_VERSION = "v2"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

PROMPT = """Kamu penerjemah temuan forensik akuntansi ke bahasa Indonesia sehari-hari,
untuk satu analis yang akan memverifikasi sendiri.

ATURAN MUTLAK:
- Hanya gunakan angka dan fakta yang ada di DATA di bawah. Dilarang menghitung
  angka baru, mengarang tren, atau menyebut informasi dari luar DATA.
- Dilarang memberi rekomendasi beli/jual/tahan, atau menyimpulkan ada penipuan.
  Temuan ini indikasi statistik, bukan tuduhan.
- Dilarang mengubah atau mempertanyakan skor dan severity — keduanya sudah final.

GAYA (layar sudah menampilkan nama emiten, skor, severity, dan semua angka rule):
- Jangan mengulang nama emiten, kode emiten, skor, severity, atau tanggal laporan.
- "apa_yang_terjadi": maksimal 2 kalimat pendek, maksimal 2 angka. Ceritakan pola
  terpentingnya, bukan daftar semua temuan.
- "kenapa_penting": 1 kalimat. Kenapa pola itu layak diperiksa manusia.
- "yang_perlu_dicek": 2-3 butir, masing-masing maksimal 10 kata, berupa tindakan
  ("Bandingkan piutang usaha dengan pertumbuhan penjualan"). Tanpa angka rupiah mentah.
- Kalimat pendek, tanpa istilah teknis yang tidak dijelaskan.

DATA: {facts}

Balas JSON: {{"apa_yang_terjadi": "...", "kenapa_penting": "...", "yang_perlu_dicek": ["...", "..."]}}"""


class InsightUnavailable(RuntimeError):
    """Gemini could not be reached, refused, or returned something unusable."""


# ---------------------------------------------------------------- facts


def build_facts(incident: Incident, company_name: str = "") -> dict[str, Any]:
    """The only thing the model ever sees. Deliberately excludes price, market cap and
    anything not produced by this Audit Run."""
    findings = []
    for f in incident.findings or []:
        rule_id = f.get("rule_id", "")
        meta = RULE_META.get(rule_id)
        findings.append(
            {
                "rule": meta.name if meta else rule_id,
                "arti": meta.subtitle if meta else "",
                "status": finding_label(f.get("status", "")),
                "nilai": fmt_finding_value(rule_id, f.get("value")),
                "ambang": f.get("thresholds") or {},
                "ringkasan": f.get("headline") or "",
                "angka_laporan": (f.get("inputs") or {}).get("values") or [],
                "data_hilang": f.get("missing"),
            }
        )
    return {
        "emiten": incident.symbol.removesuffix(".JK"),
        "nama_perusahaan": company_name or incident.symbol,
        "periode_laporan": incident.report_date.isoformat(),
        "skor": incident.score,
        "severity": severity_label(incident.severity),
        "alasan_severity": incident.severity_reason,
        "keyakinan_rendah": incident.low_confidence,
        "temuan": findings,
    }


# ---------------------------------------------------------------- Gemini


def _call_gemini(prompt: str, *, client: httpx.Client | None = None) -> str:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise InsightUnavailable("GEMINI_API_KEY belum diisi")

    url = f"{API_BASE}/{settings.gemini_model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }
    own = client is None
    http = client or httpx.Client(timeout=settings.gemini_timeout_seconds)
    try:
        resp = http.post(url, json=payload, headers={"X-goog-api-key": settings.gemini_api_key})
    except httpx.HTTPError as exc:
        raise InsightUnavailable(f"{type(exc).__name__}") from exc
    finally:
        if own:
            http.close()

    if resp.status_code != 200:
        raise InsightUnavailable(f"HTTP {resp.status_code}")
    try:
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise InsightUnavailable("bentuk respons tidak dikenal") from exc


def parse_response(text: str) -> dict[str, Any]:
    """Pull the three fields out of the model's JSON. Raises InsightUnavailable on anything else."""
    try:
        data = json.loads(text)
    except (ValueError, TypeError) as exc:
        raise InsightUnavailable("balasan bukan JSON") from exc
    if not isinstance(data, dict):
        raise InsightUnavailable("balasan bukan objek JSON")

    what = str(data.get("apa_yang_terjadi") or "").strip()
    why = str(data.get("kenapa_penting") or "").strip()
    raw_checks = data.get("yang_perlu_dicek") or []
    checks = [str(c).strip() for c in raw_checks if str(c).strip()] if isinstance(raw_checks, list) else []
    if not what:
        raise InsightUnavailable("apa_yang_terjadi kosong")
    return {"what_happened": what, "why_it_matters": why, "what_to_check": checks}


# ---------------------------------------------------------------- generation


def generate_one(
    session: Session,
    event_id: str,
    *,
    run_id: int | None = None,
    company_name: str = "",
    call: Callable[[str], str] = _call_gemini,
) -> IncidentInsight:
    """Produce and store one Incident Insight. Raises InsightUnavailable; the caller decides."""
    incident = session.get(Incident, event_id)
    if incident is None:
        raise InsightUnavailable(f"Incident {event_id} tidak ada")

    facts = build_facts(incident, company_name)
    fields = parse_response(call(PROMPT.format(facts=json.dumps(facts, ensure_ascii=False))))
    insight = IncidentInsight(
        event_id=event_id,
        run_id=run_id,
        severity=incident.severity,
        model=get_settings().gemini_model,
        prompt_version=PROMPT_VERSION,
        **fields,
    )
    session.add(insight)
    return insight


def generate_for_run(
    session: Session,
    run_id: int,
    event_ids: Sequence[str],
    *,
    names: dict[str, str] | None = None,
    log_line: Callable[[str], None] = lambda _m: None,
    call: Callable[[str], str] = _call_gemini,
) -> dict[str, IncidentInsight]:
    """Narrate every Incident this run created or escalated. One failure never stops the rest,
    and never fails the Audit Run — a missing Insight is a blank block plus a log line."""
    made: dict[str, IncidentInsight] = {}
    for event_id in event_ids:
        try:
            insight = generate_one(
                session,
                event_id,
                run_id=run_id,
                company_name=(names or {}).get(event_id, ""),
                call=call,
            )
            session.commit()
            made[event_id] = insight
            log_line(f"{event_id}: Ringkasan AI dibuat")
        except InsightUnavailable as exc:
            session.rollback()
            log_line(f"{event_id}: Ringkasan AI gagal — {exc}")
        except Exception as exc:  # noqa: BLE001 - an Insight must never fail an Audit Run
            session.rollback()
            log.exception("Incident Insight gagal untuk %s", event_id)
            log_line(f"{event_id}: Ringkasan AI gagal — {type(exc).__name__}: {exc}")
    return made


def latest_for(session: Session, event_id: str) -> IncidentInsight | None:
    return session.scalars(
        select(IncidentInsight)
        .where(IncidentInsight.event_id == event_id)
        .order_by(IncidentInsight.created_at.desc(), IncidentInsight.id.desc())
        .limit(1)
    ).first()


def history_for(session: Session, event_id: str) -> list[IncidentInsight]:
    """Newest first; the first entry is what `latest_for` returns."""
    return list(
        session.scalars(
            select(IncidentInsight)
            .where(IncidentInsight.event_id == event_id)
            .order_by(IncidentInsight.created_at.desc(), IncidentInsight.id.desc())
        )
    )

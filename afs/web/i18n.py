"""Internationalization (i18n) for AFS Sentinel web app.

Supports Indonesian ('id') and English ('en') with 'id' as default.
Follows the ubiquitous vocabulary in CONTEXT.md.
"""

from __future__ import annotations

from typing import Any

DEFAULT_LANG = "id"
SUPPORTED_LANGS = ("id", "en")

LANGUAGES = {
    "id": {
        "name": "Bahasa Indonesia",
        "short": "ID",
        "flag": "🇮🇩",
    },
    "en": {
        "name": "English",
        "short": "EN",
        "flag": "🇬🇧",
    },
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    # Navigation & Header
    "app.subtitle": {
        "id": "pengawas dini laporan keuangan emiten",
        "en": "forensic early-warning screening for IDX emiten",
    },
    "nav.dashboard": {
        "id": "Dashboard",
        "en": "Dashboard",
    },
    "nav.backtest": {
        "id": "Backtest",
        "en": "Backtest",
    },
    "nav.logs": {
        "id": "Log Audit",
        "en": "Audit Logs",
    },
    "nav.login": {
        "id": "Masuk",
        "en": "Log In",
    },
    "nav.logout": {
        "id": "Keluar",
        "en": "Log Out",
    },
    "nav.aria_main": {
        "id": "Navigasi utama",
        "en": "Main navigation",
    },
    "footer.tagline": {
        "id": "Sectors Hackathon 2026 · AFS Sentinel",
        "en": "Sectors Hackathon 2026 · AFS Sentinel",
    },
    "lang.switch_language": {
        "id": "Ganti bahasa",
        "en": "Change language",
    },
    "lang.current": {
        "id": "Bahasa",
        "en": "Language",
    },

    # System Status & Header Section (Dashboard)
    "dash.system_active": {
        "id": "Sistem aktif",
        "en": "System active",
    },
    "dash.system_ready": {
        "id": "Sistem siap",
        "en": "System ready",
    },
    "dash.scan_interval": {
        "id": "pemindaian otomatis tiap {days} hari",
        "en": "automatic scan every {days} days",
    },
    "dash.emiten_scanned": {
        "id": "{count} emiten dipindai",
        "en": "{count} emiten scanned",
    },
    "dash.incidents_new": {
        "id": "{count} Incident baru",
        "en": "{count} new Incidents",
    },
    "dash.emiten_failed": {
        "id": "{count} gagal",
        "en": "{count} failed",
    },
    "dash.trigger_title": {
        "id": "Pemicu Audit Run",
        "en": "Audit Run trigger",
    },
    "dash.view_details": {
        "id": "Lihat rincian",
        "en": "View details",
    },
    "dash.no_runs_yet": {
        "id": "Belum ada Audit Run. Jalankan sekarang, atau tunggu pemindaian otomatis pertama.",
        "en": "No Audit Runs yet. Run now, or wait for the first automatic scan.",
    },
    "dash.next_run": {
        "id": "Berikutnya:",
        "en": "Next run:",
    },
    "dash.next_run_first": {
        "id": "pada pemindaian otomatis pertama",
        "en": "on the first automatic scan",
    },
    "dash.run_now": {
        "id": "Jalankan sekarang",
        "en": "Run now",
    },
    "dash.login_to_run": {
        "id": "Masuk untuk menjalankan",
        "en": "Log in to run",
    },

    # Severity Counts (Dashboard)
    "dash.counts_aria": {
        "id": "Jumlah emiten per tingkat risiko",
        "en": "Number of emiten by risk level",
    },
    "dash.count.critical": {
        "id": "Butuh perhatian segera",
        "en": "Immediate attention needed",
    },
    "dash.count.moderate": {
        "id": "Perlu ditinjau",
        "en": "Needs review",
    },
    "dash.count.low": {
        "id": "Aman",
        "en": "Low risk",
    },

    # Triage Queue (Dashboard)
    "dash.queue_heading": {
        "id": "Perlu tindakan Anda",
        "en": "Action required",
    },
    "dash.queue_empty": {
        "id": "Tidak ada yang perlu ditinjau. Emiten masuk daftar ini saat risikonya mencapai Sedang.",
        "en": "No items need review. Emiten appear here when risk reaches Moderate.",
    },

    # Universe Table (Dashboard)
    "dash.universe_heading": {
        "id": "Semua emiten dipantau",
        "en": "All monitored emiten",
    },
    "dash.legend_color": {
        "id": "Warna penanda = status rule",
        "en": "Marker color = rule status",
    },
    "dash.legend_number": {
        "id": "Angka penanda = rule ke-berapa",
        "en": "Marker number = rule number",
    },
    "dash.th_emiten": {
        "id": "Emiten",
        "en": "Emiten",
    },
    "dash.th_score": {
        "id": "Skor",
        "en": "Score",
    },
    "dash.th_severity": {
        "id": "Severity",
        "en": "Severity",
    },
    "dash.th_rule_status": {
        "id": "Status rule",
        "en": "Rule status",
    },
    "dash.th_report": {
        "id": "Laporan",
        "en": "Report",
    },
    "dash.not_evaluated": {
        "id": "Belum dinilai",
        "en": "Not evaluated",
    },
    "dash.no_findings_emiten": {
        "id": "Belum ada Rule Finding untuk emiten ini.",
        "en": "No Rule Findings for this emiten yet.",
    },
    "dash.data_unavailable": {
        "id": "Data tidak tersedia: {missing}",
        "en": "Data unavailable: {missing}",
    },
    "dash.open_incident": {
        "id": "Buka Incident",
        "en": "Open Incident",
    },
    "dash.universe_empty": {
        "id": "Belum ada emiten yang dinilai. Hasil muncul di sini setelah Audit Run pertama selesai.",
        "en": "No emiten evaluated yet. Results will appear here after the first Audit Run completes.",
    },

    # Badges & Status Key
    "badge.low_confidence": {
        "id": "Keyakinan rendah",
        "en": "Low confidence",
    },
    "badge.low_confidence_title": {
        "id": "Rule yang bisa dinilai berbobot kurang dari 50 dari 100",
        "en": "Evaluated rules account for less than 50 of 100 weight",
    },
    "status_key.pass": {
        "id": "Aman",
        "en": "Pass",
    },
    "status_key.warning": {
        "id": "Waspada",
        "en": "Warning",
    },
    "status_key.red_flag": {
        "id": "Bahaya",
        "en": "Red Flag",
    },
    "status_key.insufficient_data": {
        "id": "Tak bisa dinilai",
        "en": "Insufficient data",
    },

    # Incident Detail Page
    "incident.report_period": {
        "id": "Report Period",
        "en": "Report Period",
    },
    "incident.detected": {
        "id": "Terdeteksi",
        "en": "Detected",
    },
    "incident.updated": {
        "id": "Diperbarui",
        "en": "Updated",
    },
    "incident.triage_status": {
        "id": "Status triage",
        "en": "Triage status",
    },
    "incident.audio_heading": {
        "id": "🎧 Audio Briefing Forensik (~2 Menit)",
        "en": "🎧 Forensic Audio Briefing (~2 Mins)",
    },
    "incident.audio_subtitle": {
        "id": "Dengarkan intisari penting langsung dari suara narator, sembari menelaah tabel detail dan bukti di bawah.",
        "en": "Listen to key insights from the narrator while reviewing detailed tables and evidence below.",
    },
    "incident.audio_play": {
        "id": "Putar Audio",
        "en": "Play Audio",
    },
    "incident.audio_pause": {
        "id": "Jeda",
        "en": "Pause",
    },
    "incident.audio_speed": {
        "id": "Kecepatan",
        "en": "Speed",
    },
    "incident.audio_download": {
        "id": "Unduh MP3",
        "en": "Download MP3",
    },
    "incident.audio_show_transcript": {
        "id": "Lihat Naskah Audio",
        "en": "View Audio Transcript",
    },
    "incident.audio_hide_transcript": {
        "id": "Sembunyikan Naskah",
        "en": "Hide Transcript",
    },
    "incident.audio_loading": {
        "id": "Memuat audio...",
        "en": "Loading audio...",
    },
    "incident.ai_summary": {
        "id": "🤖 Ringkasan AI",
        "en": "🤖 AI Summary",
    },
    "incident.ai_regenerate": {
        "id": "Buat ulang",
        "en": "Regenerate",
    },
    "incident.ai_generate": {
        "id": "Buat ringkasan",
        "en": "Generate summary",
    },
    "incident.what_to_check": {
        "id": "Yang perlu Anda cek",
        "en": "What you should check",
    },
    "incident.ai_footer": {
        "id": "Ditulis AI dari {count} Rule Finding di bawah — angka resminya ada di sana.",
        "en": "Written by AI from {count} Rule Findings below — official figures are there.",
    },
    "incident.versions_saved": {
        "id": "{count} versi sebelumnya tersimpan",
        "en": "{count} previous versions saved",
    },
    "incident.ai_empty": {
        "id": "Belum ada ringkasan. Temuan lengkapnya ada di bawah.",
        "en": "No summary yet. Complete findings are below.",
    },
    "incident.evidence_heading": {
        "id": "Bukti perhitungan",
        "en": "Evidence and calculations",
    },
    "incident.evidence_subtitle": {
        "id": "Satu kartu per rule, yang paling berat di atas.",
        "en": "One card per rule, most severe on top.",
    },
    "incident.view_details": {
        "id": "Lihat rincian perhitungan",
        "en": "View calculation details",
    },
    "incident.hide_details": {
        "id": "Tutup rincian",
        "en": "Hide calculation details",
    },
    "incident.formula": {
        "id": "Formula",
        "en": "Formula",
    },
    "incident.report_inputs": {
        "id": "Input dari laporan",
        "en": "Report inputs",
    },
    "incident.field": {
        "id": "Field",
        "en": "Field",
    },
    "incident.report_date": {
        "id": "Tanggal laporan",
        "en": "Report date",
    },
    "incident.value": {
        "id": "Nilai",
        "en": "Value",
    },
    "incident.thresholds": {
        "id": "Ambang",
        "en": "Thresholds",
    },
    "incident.source_endpoint": {
        "id": "Endpoint sumber",
        "en": "Source endpoint",
    },
    "incident.note": {
        "id": "Catatan",
        "en": "Note",
    },
    "incident.method_limitation": {
        "id": "Keterbatasan metode",
        "en": "Method limitation",
    },
    "incident.no_findings": {
        "id": "Incident ini belum memiliki Rule Finding.",
        "en": "This Incident does not have any Rule Findings yet.",
    },
    "incident.chart_heading": {
        "id": "Laba bersih vs arus kas operasi",
        "en": "Net income vs operating cash flow",
    },
    "incident.chart_subtitle": {
        "id": "Per kuartal, dalam miliar rupiah. Sumber: /v2/financials/quarterly/",
        "en": "Per quarter, in billion IDR. Source: /v2/financials/quarterly/",
    },
    "incident.chart_net_income": {
        "id": "Laba bersih",
        "en": "Net income",
    },
    "incident.chart_ocf": {
        "id": "Arus kas operasi",
        "en": "Operating cash flow",
    },
    "incident.chart_y_axis": {
        "id": "miliar Rp",
        "en": "billion IDR",
    },
    "incident.chart_tooltip_unit": {
        "id": "Rp{val} miliar",
        "en": "IDR {val} billion",
    },
    "incident.triage_heading": {
        "id": "Triage",
        "en": "Triage",
    },
    "incident.status": {
        "id": "Status",
        "en": "Status",
    },
    "incident.analyst_notes": {
        "id": "Catatan analis",
        "en": "Analyst notes",
    },
    "incident.save_triage": {
        "id": "Simpan triage",
        "en": "Save triage",
    },
    "incident.login_to_change_status": {
        "id": "Masuk untuk mengubah status",
        "en": "Log in to change status",
    },
    "incident.history_heading": {
        "id": "Riwayat",
        "en": "History",
    },
    "incident.history_empty": {
        "id": "Belum ada riwayat.",
        "en": "No history yet.",
    },

    # Backtest Page
    "backtest.heading": {
        "id": "Backtest",
        "en": "Backtest",
    },
    "backtest.subtitle": {
        "id": (
            "Keenam Forensic Rule dijalankan ulang untuk tiap kuartal sejak 2021-Q1, "
            "seolah-olah hari itu adalah tanggal laporannya, lalu dibandingkan dengan kejadian nyata. "
            "Backtest tidak membuat Incident dan tidak mengirim notifikasi."
        ),
        "en": (
            "All six Forensic Rules are re-evaluated for each quarter since 2021-Q1, "
            "as if that day were the report date, then compared against real-world events. "
            "Backtest does not create Incidents and sends no notifications."
        ),
    },
    "backtest.not_run_heading": {
        "id": "Backtest belum dijalankan",
        "en": "Backtest not yet run",
    },
    "backtest.not_run_body": {
        "id": "Daftar kasus di <code>config/backtest_cases.json</code> belum tersedia. Setelah diisi, jalankan <code>python -m afs backtest</code>.",
        "en": "Case list in <code>config/backtest_cases.json</code> is not available. Once configured, run <code>python -m afs backtest</code>.",
    },
    "backtest.case_not_run": {
        "id": "Jalankan <code>python -m afs backtest</code> untuk menghitung skor {symbol} per kuartal.",
        "en": "Run <code>python -m afs backtest</code> to compute scores for {symbol} per quarter.",
    },
    "backtest.chart_aria": {
        "id": "Grafik skor per kuartal {symbol} dengan pita severity dan garis kejadian nyata",
        "en": "Quarterly score chart for {symbol} with severity bands and real-world event lines",
    },
    "backtest.chart_footnote": {
        "id": "Pita latar: hijau Rendah (0–30), kuning Sedang (30–60), merah Kritis (60–100). Garis putus-putus: kejadian nyata.",
        "en": "Background bands: green Low (0–30), yellow Moderate (30–60), red Critical (60–100). Dashed line: real-world event.",
    },
    "backtest.rule_findings_heading": {
        "id": "Rule Finding per kuartal",
        "en": "Rule Findings per quarter",
    },
    "backtest.th_quarter": {
        "id": "Kuartal",
        "en": "Quarter",
    },
    "backtest.insider_disclaimer": {
        "id": "Penjualan Orang Dalam tidak dinilai — data sebelum 2025 tidak tersedia. Data kuartalan API hanya tersedia sejak 2020-Q1.",
        "en": "Insider Selling not evaluated — data prior to 2025 is unavailable. API quarterly data is only available since 2020-Q1.",
    },
    "backtest.event_sources_heading": {
        "id": "Sumber kejadian",
        "en": "Event sources",
    },
    "backtest.news_source": {
        "id": "Sumber berita",
        "en": "News source",
    },
    "backtest.source_unverified": {
        "id": "Sumber belum diverifikasi",
        "en": "Source unverified",
    },
    "backtest.chart_score": {
        "id": "Skor",
        "en": "Score",
    },
    "backtest.score_tooltip": {
        "id": "Skor {score}/100",
        "en": "Score {score}/100",
    },

    # Audit Logs Page
    "logs.heading": {
        "id": "Jejak audit",
        "en": "Audit Trail",
    },
    "logs.subtitle": {
        "id": "Setiap pemindaian tercatat, termasuk yang tidak menemukan apa pun. Klik baris untuk melihat hasil per emiten.",
        "en": "Every scan is recorded, including those with no findings. Click a row to see results per emiten.",
    },
    "logs.th_started": {
        "id": "Mulai",
        "en": "Started",
    },
    "logs.th_duration": {
        "id": "Durasi",
        "en": "Duration",
    },
    "logs.th_trigger": {
        "id": "Pemicu",
        "en": "Trigger",
    },
    "logs.th_scanned_failed": {
        "id": "Dipindai / gagal",
        "en": "Scanned / failed",
    },
    "logs.th_new_incidents": {
        "id": "Incident baru",
        "en": "New Incidents",
    },
    "logs.th_escalation": {
        "id": "Escalation",
        "en": "Escalation",
    },
    "logs.th_credits": {
        "id": "Kredit",
        "en": "Credits",
    },
    "logs.th_status": {
        "id": "Status",
        "en": "Status",
    },
    "logs.failure_reason": {
        "id": "Alasan gagal: {error}",
        "en": "Failure reason: {error}",
    },
    "logs.th_risk": {
        "id": "Risiko",
        "en": "Risk",
    },
    "logs.th_outcome": {
        "id": "Hasil",
        "en": "Outcome",
    },
    "logs.no_evaluations": {
        "id": "Tidak ada emiten yang berhasil dievaluasi pada run ini.",
        "en": "No emiten were successfully evaluated in this run.",
    },
    "logs.show_raw": {
        "id": "Log teks mentah",
        "en": "Raw text log",
    },
    "logs.hide_raw": {
        "id": "Sembunyikan log teks mentah",
        "en": "Hide raw text log",
    },
    "logs.empty": {
        "id": "Belum ada Audit Run. Pemindaian otomatis berjalan tiap 3 hari, atau jalankan manual dari Dashboard.",
        "en": "No Audit Runs yet. Automatic scans run every 3 days, or start one manually from the Dashboard.",
    },
    "logs.no_incident": {
        "id": "Tidak ada Incident",
        "en": "No Incident",
    },

    # Login Page
    "login.title": {
        "id": "Masuk",
        "en": "Log In",
    },
    "login.heading": {
        "id": "Masuk sebagai analis",
        "en": "Log in as analyst",
    },
    "login.subtitle": {
        "id": "Semua halaman bisa dibaca tanpa masuk. Password dibutuhkan untuk mengubah triage dan menjalankan Audit Run.",
        "en": "All pages can be viewed without logging in. Password is required to update triage and start an Audit Run.",
    },
    "login.password": {
        "id": "Password",
        "en": "Password",
    },
    "login.error": {
        "id": "Password salah. Coba lagi.",
        "en": "Incorrect password. Try again.",
    },
    "login.submit": {
        "id": "Masuk",
        "en": "Log In",
    },

    # 404 Page
    "not_found.title": {
        "id": "Tidak ditemukan",
        "en": "Not Found",
    },
    "not_found.heading": {
        "id": "Incident tidak ditemukan",
        "en": "Incident not found",
    },
    "not_found.body": {
        "id": "Tidak ada Incident dengan ID <strong>{event_id}</strong>. Periksa kembali tautannya, atau cari dari antrean triage.",
        "en": "No Incident found with ID <strong>{event_id}</strong>. Check the link or search from the triage queue.",
    },
    "not_found.back": {
        "id": "Kembali ke Dashboard",
        "en": "Back to Dashboard",
    },

    # Common
    "common.empty": {
        "id": "(kosong)",
        "en": "(empty)",
    },
    "common.yes": {
        "id": "ya",
        "en": "yes",
    },
    "common.no": {
        "id": "tidak",
        "en": "no",
    },
    "common.cannot_assess": {
        "id": "Tak bisa dinilai",
        "en": "Cannot be assessed",
    },

    # Flashes
    "flash.runner_unavailable": {
        "id": "Runner belum tersedia",
        "en": "Runner not available",
    },
    "flash.run_in_progress": {
        "id": "Audit Run sedang berjalan",
        "en": "Audit Run is already in progress",
    },
    "flash.run_started": {
        "id": "Audit Run dimulai. Muat ulang halaman ini beberapa menit lagi untuk melihat hasilnya.",
        "en": "Audit Run started. Reload this page in a few minutes to see results.",
    },
    "flash.insight_failed": {
        "id": "Ringkasan AI gagal dibuat: {exc}",
        "en": "Failed to generate AI summary: {exc}",
    },
    "flash.insight_success": {
        "id": "Ringkasan AI dibuat",
        "en": "AI summary generated",
    },
    "flash.triage_unknown": {
        "id": "Status triage tidak dikenal",
        "en": "Unknown triage status",
    },
    "flash.triage_saved": {
        "id": "Perubahan triage disimpan",
        "en": "Triage changes saved",
    },
    "flash.login_success": {
        "id": "Berhasil masuk",
        "en": "Logged in successfully",
    },
    "flash.logout_success": {
        "id": "Berhasil keluar",
        "en": "Logged out successfully",
    },
}

# Rule Translations
RULE_TRANSLATIONS: dict[str, dict[str, dict[str, str]]] = {
    "SLOAN_ACCRUAL": {
        "id": {
            "name": "Sloan Accrual Ratio",
            "subtitle": "Seberapa banyak laba yang bukan uang tunai",
        },
        "en": {
            "name": "Sloan Accrual Ratio",
            "subtitle": "Accrual portion of net income relative to cash",
        },
    },
    "EARNINGS_CASH_DIVERGENCE": {
        "id": {
            "name": "Divergensi Laba–Kas",
            "subtitle": "Laba naik, tapi kas operasi turun",
        },
        "en": {
            "name": "Earnings–Cash Divergence",
            "subtitle": "Earnings rising while operating cash flow falls",
        },
    },
    "ALTMAN_Z_ADAPTED": {
        "id": {
            "name": "Altman Z'' (Adapted)",
            "subtitle": "Risiko kesulitan keuangan",
        },
        "en": {
            "name": "Altman Z'' (Adapted)",
            "subtitle": "Financial distress risk",
        },
    },
    "BENEISH_ADAPTED": {
        "id": {
            "name": "Beneish (Adapted)",
            "subtitle": "Tanda tekanan untuk memoles laporan",
        },
        "en": {
            "name": "Beneish (Adapted)",
            "subtitle": "Pressure indicators for earnings manipulation",
        },
    },
    "INSIDER_SELLING": {
        "id": {
            "name": "Penjualan Orang Dalam",
            "subtitle": "Orang dalam/pemegang saham utama menjual",
        },
        "en": {
            "name": "Insider Selling",
            "subtitle": "Insiders / substantial shareholders selling",
        },
    },
    "EARNINGS_WITHOUT_DIVIDEND": {
        "id": {
            "name": "Laba tanpa Dividen",
            "subtitle": "Untung, tapi tidak membagi kas",
        },
        "en": {
            "name": "Earnings without Dividend",
            "subtitle": "Profitable without dividend distributions",
        },
    },
}

RULE_LIMITATIONS_I18N: dict[str, dict[str, str]] = {
    "ALTMAN_Z_ADAPTED": {
        "id": (
            "Versi adaptasi: laba ditahan tidak tersedia di API sehingga diganti total ekuitas; "
            "ambang dibuat lebih ketat untuk mengimbangi."
        ),
        "en": (
            "Adapted version: retained earnings is not provided by the API and is substituted with total equity; "
            "thresholds are tightened to compensate."
        ),
    },
    "BENEISH_ADAPTED": {
        "id": "Hanya 3 dari 8 indeks Beneish (GMI, SGI, LVGI); bukan M-Score utuh.",
        "en": "Only 3 of 8 Beneish indices (GMI, SGI, LVGI); not a full M-Score.",
    },
    "INSIDER_SELLING": {
        "id": (
            "\"Orang dalam\" di API mencakup pemegang saham ≥5%; riwayat hanya ±1 tahun; persentase dibulatkan "
            "2 desimal sehingga transaksi sangat kecil tercatat 0%."
        ),
        "en": (
            "\"Insiders\" in the API include shareholders ≥5%; history covers ±1 year; percentages rounded to "
            "2 decimals so very small trades appear as 0%."
        ),
    },
    "EARNINGS_WITHOUT_DIVIDEND": {
        "id": "Tidak bisa membedakan dividen tunai dan dividen saham.",
        "en": "Cannot distinguish between cash dividends and stock dividends.",
    },
}

FINDING_LABEL_I18N: dict[str, dict[str, str]] = {
    "PASS": {"id": "Aman", "en": "Pass"},
    "WARNING": {"id": "Waspada", "en": "Warning"},
    "RED_FLAG": {"id": "Bahaya", "en": "Red Flag"},
    "INSUFFICIENT_DATA": {"id": "Tak bisa dinilai", "en": "Insufficient data"},
}

SEVERITY_LABEL_I18N: dict[str, dict[str, str]] = {
    "LOW": {"id": "Rendah", "en": "Low"},
    "MODERATE": {"id": "Sedang", "en": "Moderate"},
    "CRITICAL": {"id": "Kritis", "en": "Critical"},
}

TRIAGE_LABEL_I18N: dict[str, dict[str, str]] = {
    "UNTRIAGED": {"id": "Belum ditinjau", "en": "Untriaged"},
    "INVESTIGATING": {"id": "Sedang diperiksa", "en": "Investigating"},
    "RESOLVED": {"id": "Sudah ditindaklanjuti", "en": "Resolved"},
    "DISMISSED": {"id": "Alarm palsu", "en": "Dismissed"},
}

TRIGGER_LABEL_I18N: dict[str, dict[str, str]] = {
    "SCHEDULER": {"id": "Otomatis · sistem", "en": "Automatic · system"},
    "MANUAL": {"id": "Manual · analis", "en": "Manual · analyst"},
}

RUN_STATUS_LABEL_I18N: dict[str, dict[str, str]] = {
    "SUCCESS": {"id": "Berhasil", "en": "Success"},
    "FAILED": {"id": "Gagal", "en": "Failed"},
    "RUNNING": {"id": "Sedang berjalan", "en": "Running"},
}

MONTHS_I18N: dict[str, list[str]] = {
    "id": ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}

MONTHS_LONG_I18N: dict[str, list[str]] = {
    "id": [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember",
    ],
    "en": [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ],
}

DAYS_I18N: dict[str, list[str]] = {
    "id": ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}


import re


def t(key: str, lang: str = DEFAULT_LANG, **kwargs: Any) -> str:
    """Translate a message key into the requested language with optional variable formatting."""
    lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    text = entry.get(lang) or entry.get(DEFAULT_LANG) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def localize_headline(text: str | None, lang: str = DEFAULT_LANG) -> str:
    """Translate rule finding headlines into the target language."""
    if not text or lang != "en":
        return text or ""

    # 1. Sloan Accrual
    m = re.match(
        r"^([\d,\.]+)%\s+dari aset tercatat sebagai laba yang belum menjadi uang tunai\s*\(batas wajar\s*([\d,\.]+)%\)\.?$",
        text,
    )
    if m:
        pct = m.group(1).replace(",", ".")
        limit = m.group(2).replace(",", ".")
        return f"{pct}% of total assets recorded as non-cash earnings (normal threshold {limit}%)."

    m = re.match(
        r"^Laba non-kas\s+([\d,\.]+)%\s+dari aset\s*\(aman,\s*di bawah batas wajar\s*([\d,\.]+)%\)\.?$",
        text,
    )
    if m:
        pct = m.group(1).replace(",", ".")
        limit = m.group(2).replace(",", ".")
        return f"Non-cash earnings {pct}% of assets (safe, below normal threshold {limit}%)."

    # 2. Earnings-Cash Divergence
    m = re.match(
        r"^Laba naik\s+([\d,\.]+%)\s+dibanding kuartal yang sama tahun lalu,\s*tapi kas operasi turun\s+([\d,\.]+%)\.?$",
        text,
    )
    if m:
        e = m.group(1).replace(",", ".")
        c = m.group(2).replace(",", ".")
        return f"Earnings rose {e} YoY, but operating cash flow fell {c}."

    m = re.match(r"^Laba naik\s+([\d,\.]+%)\s*,\s*tapi kas operasi turun\s+([\d,\.]+%)\.?$", text)
    if m:
        e = m.group(1).replace(",", ".")
        c = m.group(2).replace(",", ".")
        return f"Earnings rose {e}, but operating cash flow fell {c}."

    m = re.match(
        r"^Laba dan arus kas operasi sejalan\s*\(perubahan laba\s+([\d,\.]+%)\s*,\s*kas\s+([\d,\.]+%)\)\.?$",
        text,
    )
    if m:
        e = m.group(1).replace(",", ".")
        c = m.group(2).replace(",", ".")
        return f"Earnings and operating cash flow aligned (earnings change {e}, cash {c})."

    # 3. Altman Z
    m = re.match(r"^Skor Altman\s+([\d,\.]+)\s*—\s*masuk zona kesulitan keuangan\.?$", text)
    if m:
        z = m.group(1).replace(",", ".")
        return f"Altman score {z} — in financial distress zone."

    m = re.match(r"^Skor Altman\s+([\d,\.]+)\s*—\s*masuk zona waspada\.?$", text)
    if m:
        z = m.group(1).replace(",", ".")
        return f"Altman score {z} — in grey zone (caution)."

    m = re.match(r"^Skor Altman\s+([\d,\.]+)\s*—\s*kondisi keuangan relatif sehat\.?$", text)
    if m:
        z = m.group(1).replace(",", ".")
        return f"Altman score {z} — financially safe condition."

    # 4. Beneish
    m = re.match(r"^(\d+)\s+dari\s+(\d+)\s+indeks Beneish melampaui ambang\s*\((.*?)\)\.?$", text)
    if m:
        return f"{m.group(1)} of {m.group(2)} Beneish indices exceeded threshold ({m.group(3)})."

    m = re.match(r"^Semua\s+(\d+)\s+indeks Beneish yang dinilai berada dalam batas wajar\.?$", text)
    if m:
        return f"All {m.group(1)} evaluated Beneish indices are within normal limits."

    # 5. Insider Selling
    m = re.match(
        r"^Net penjualan saham oleh orang dalam mencapai\s+([\d,\.]+)%\s+dari total saham\s*\(dari\s+(\d+)\s+transaksi\)\.?$",
        text,
    )
    if m:
        pct = m.group(1).replace(",", ".")
        return f"Net insider selling reached {pct}% of total shares (across {m.group(2)} transactions)."

    m = re.match(
        r"^Tidak ada penjualan signifikan oleh orang dalam\s*\(net\s+([\d,\.]+)%\s+dari\s+(\d+)\s+transaksi\)\.?$",
        text,
    )
    if m:
        pct = m.group(1).replace(",", ".")
        return f"No significant insider selling (net {pct}% across {m.group(2)} transactions)."

    # 6. Dividend
    m = re.match(r"^Laba positif\s*\((.*?)\s+miliar Rp\)\s+tapi tidak membagikan dividen\.?$", text)
    if m:
        amt = m.group(1).replace(",", ".")
        return f"Positive earnings (IDR {amt} billion) but no dividend distributed."

    m = re.match(r"^Membagikan dividen\s*\((.*?)\s+miliar Rp\)\.?$", text)
    if m:
        amt = m.group(1).replace(",", ".")
        return f"Distributed dividends (IDR {amt} billion)."

    # 7. Insufficient data
    if text.startswith("Tak bisa dinilai:"):
        rest = text[len("Tak bisa dinilai:"):].strip()
        return f"Cannot be evaluated: {rest}"

    if text == "Tidak dinilai di Backtest.":
        return "Not evaluated in Backtest."

    return text


def localize_severity_reason(text: str | None, lang: str = DEFAULT_LANG) -> str:
    """Translate severity reason explanations into the target language."""
    if not text or lang != "en":
        return text or ""

    m = re.match(r"^Minimal\s+Sedang\s+karena\s+(.*?)\s+berstatus\s+(Bahaya|Waspada)\.?$", text)
    if m:
        rule = m.group(1)
        st = "Red Flag" if m.group(2) == "Bahaya" else "Warning"
        return f"Minimum Moderate because {rule} in {st} status."

    m = re.match(r"^Maksimal\s+Sedang\s+karena\s+keyakinan rendah\s*\((.*?)\)\.?$", text)
    if m:
        return f"Maximum Moderate due to low confidence ({m.group(1)})."

    return text

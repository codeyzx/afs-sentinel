# AFS Sentinel

**Autonomous Forensic Sentinel**: sistem peringatan dini yang secara otomatis memindai ±33 **Emiten** non-keuangan di BEI untuk mencari tanda manipulasi laba dan kesulitan keuangan, lalu melaporkannya ke satu **Analyst** lewat Telegram dan web app untuk ditriase. Dibuat untuk Sectors Hackathon 2026 (Track 2), dengan data dari [Sectors API](https://sectors.app).

Dokumen acuan:

- [`docs/system-rules.md`](docs/system-rules.md): spesifikasi aturan sistem. Jika ada yang bertentangan, dokumen ini yang berlaku.
- [`CONTEXT.md`](CONTEXT.md): glosarium domain (Emiten, Forensic Rule, Incident, Audit Run, dan lainnya).
- [`docs/adr/`](docs/adr/): keputusan arsitektur ([0001 Heroku + Postgres + Scheduler](docs/adr/0001-heroku-postgres-and-scheduler.md), [0002 Forensic Rule yang disesuaikan dengan API](docs/adr/0002-forensic-rules-adapted-to-api-gaps.md)).

## Arsitektur

```
Heroku Scheduler (harian 01:00 UTC)        Tombol "Run now" (web, password)
            │                                        │
            └──────────► python -m afs run ◄─────────┘
                               │  (keluar jika bukan Sabtu WIB, kecuali manual)
                               ▼
   config/universe.json ─► Audit Run ─► afs/sectors (client + repository)
                               │              │  cache permanen di Postgres:
                               │              └─ kuartal tersimpan tidak diambil ulang
                               ▼
                 afs/rules (6 Forensic Rule) ─► afs/scoring (Composite Risk Score,
                               │                             Incident Severity)
                               ▼
                 Incident baru / Escalation ─► afs/telegram (pesan + tombol "Buka Incident")
                               │
                               ▼
                         Heroku Postgres ◄──── afs/web (FastAPI + Jinja)
                                                /  /incidents/{id}  /backtest  /logs
```

- **Web dyno** (Basic, tidak tidur): `uvicorn afs.web.app:app`.
- **Release phase**: `python -m afs initdb` membuat tabel sebelum setiap rilis.
- **Backtest** (`python -m afs backtest`) memutar ulang rule pada kuartal historis WSKT dan SRIL; tidak membuat Incident dan tidak mengirim Telegram.

## Pengembangan lokal

Prasyarat: [uv](https://docs.astral.sh/uv/) dan Python 3.13 (uv akan mengunduhnya sesuai `.python-version`).

```bash
uv sync                          # pasang dependensi (termasuk grup dev)
cp .env.example .env             # isi SECTORS_API_KEY, TELEGRAM_*, ADMIN_PASSWORD, ...
uv run python -m afs initdb      # buat tabel (default SQLite di data/afs.db)
uv run python -m afs.devseed     # OPSIONAL: data demo palsu untuk mencoba UI
uv run uvicorn afs.web.app:app --reload
uv run pytest -q                 # tes memakai fixture JSON, tanpa API live
```

Buka <http://localhost:8000>. `python -m afs.devseed --reset` menghapus semua tabel lalu mengisinya ulang; **semua angka devseed fiktif**, jangan dipakai untuk demo klaim.

Perintah CLI lain:

| Perintah | Fungsi |
|---|---|
| `python -m afs sync-universe` | Sinkronkan daftar Universe dari `config/universe.json` (mengecualikan sektor Financials). |
| `python -m afs run` | Audit Run manual (tanpa cek hari). |
| `python -m afs run --scheduled` | Audit Run terjadwal: langsung keluar jika hari ini (WIB) bukan Sabtu. |
| `python -m afs backtest [--case WSKT] [--dry-run]` | Backtest; `--dry-run` hanya memperkirakan kuartal/kredit yang akan diambil. |

## Anggaran kredit Sectors API

Key utama berisi **500 kredit**, dipotong **per kuartal yang dikembalikan**. Semua respons disimpan permanen di Postgres, jadi kredit hanya terpakai untuk data yang belum pernah diambil.

1. **Selalu jalankan backtest dengan `--dry-run` dulu** untuk melihat berapa kuartal yang akan diambil. Backtest penuh WSKT + SRIL memakan ±40 kredit, sekali saja.
2. **Audit Run pertama** pada ±33 Emiten memakan **±5 kredit per Emiten baru** (5 kuartal: `t` s.d. `t-4`), jadi sekitar 165 kredit. Run berikutnya **hampir nol**, kecuali saat kuartal baru terbit (1 kredit per Emiten yang punya laporan baru).
3. **Company overview** memakan **1 kredit sekali per Emiten** (dipakai `sync-universe`).
4. Kredit terpakai setiap run tercatat di halaman `/logs` dan di pesan ringkasan Telegram. Pantau angka itu sebelum menjalankan run manual berulang kali.

## Setup bot Telegram

1. Di Telegram, chat **@BotFather**, kirim `/newbot`, ikuti langkahnya. Simpan token yang diberikan sebagai `TELEGRAM_BOT_TOKEN`.
2. Kirim pesan apa saja (misal `/start`) ke bot baru Anda. Untuk grup: tambahkan bot ke grup lalu kirim pesan di grup.
3. Ambil chat id:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
   ```
   Cari `"chat":{"id": ...}` di respons. Nilai itu adalah `TELEGRAM_CHAT_ID` (untuk grup biasanya negatif, misal `-100...`).
4. Isi keduanya di `.env` (lokal) atau `heroku config:set` (produksi).

## Deploy ke Heroku

Heroku Python buildpack mendeteksi `uv.lock` dan memasang dependensi dengan `uv sync --locked --no-default-groups` (grup dev tidak ikut). Versi Python diambil dari `.python-version`. Jalankan `uv lock` dan commit `uv.lock` setiap kali dependensi berubah.

```bash
# 1. Buat app dan add-on
heroku create afs-sentinel
heroku addons:create heroku-postgresql:essential-0     # mengisi DATABASE_URL otomatis
heroku addons:create scheduler:standard
heroku ps:type web=basic

# 2. Konfigurasi
heroku config:set \
  SECTORS_API_KEY=... \
  TELEGRAM_BOT_TOKEN=... \
  TELEGRAM_CHAT_ID=... \
  BASE_WEB_URL=https://afs-sentinel-xxxx.herokuapp.com \
  ADMIN_PASSWORD=... \
  SESSION_SECRET="$(openssl rand -hex 32)"

# 3. Deploy (release phase menjalankan python -m afs initdb)
git push heroku main

# 4. Isi Universe
heroku run python -m afs sync-universe

# 5. Backtest: perkirakan dulu, baru jalankan
heroku run python -m afs backtest --dry-run
heroku run python -m afs backtest
```

6. **Heroku Scheduler**: `heroku addons:open scheduler` → *Add Job* → perintah `python -m afs run --scheduled`, frekuensi **Every day at 01:00 UTC** (08:00 WIB). Scheduler tidak punya jadwal mingguan; perintah itu sendiri yang keluar jika bukan Sabtu.
7. Cek: `heroku open`, `heroku logs --tail`.

`app.json` juga tersedia untuk tombol/alur "Deploy to Heroku" (add-on, formation, dan env var sudah dideklarasikan; `SESSION_SECRET` dibuat otomatis).

## Checklist demo (video 3 menit)

| Menit | Adegan | Persiapan |
|---|---|---|
| 0:00–0:30 | **Alert Telegram**: pesan Incident baru/Escalation dengan maks. 3 headline dan tombol "Buka Incident". | Audit Run sudah pernah berjalan di Heroku dan menghasilkan Incident; chat Telegram terbuka. |
| 0:30–1:30 | **Halaman Incident**: vonis, kartu "Kenapa ditandai" (buka satu kartu: formula, input mentah, endpoint), grafik laba vs kas operasi, ubah Triage Status dengan password. | `BASE_WEB_URL` benar sehingga deep link bekerja; `ADMIN_PASSWORD` siap. |
| 1:30–2:30 | **Backtest** (`/backtest`): tab WSKT/SRIL, garis skor per kuartal, garis kejadian nyata, kalimat klaim otomatis. | Backtest sudah dijalankan (bukan dry-run). Klaim di video **harus** berasal dari output ini, bukan dari devseed. |
| 2:30–3:00 | **Logs** (`/logs`): Audit Run terjadwal vs manual, kredit terpakai, log teks. Tutup dengan dashboard `/`. | Minimal satu run `SCHEDULER` dan satu `MANUAL` tercatat. |

Sebelum merekam: pastikan database produksi **tidak** berisi data devseed, dan sebutkan keterbatasan di bawah bila relevan.

## Keterbatasan yang diketahui

Ringkasan dari [`docs/system-rules.md` §10](docs/system-rules.md#10-keterbatasan-yang-wajib-diungkap):

1. **Altman Adapted**: laba ditahan diganti total ekuitas; ambang diperketat.
2. **Beneish Adapted**: hanya 3 dari 8 indeks (GMI, SGI, LVGI), bukan M-Score utuh.
3. **Penjualan Orang Dalam**: "insider" di API mencakup pemegang saham ≥5%; riwayat hanya ±1 tahun; persentase dibulatkan 2 desimal.
4. **Laba tanpa Dividen**: tidak bisa membedakan dividen tunai vs saham.
5. **Data historis**: hanya sejak 2020-Q1.
6. **Sektor keuangan** tidak dinilai (model tidak valid untuk bank/asuransi).

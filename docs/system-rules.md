# AFS Sentinel — Spesifikasi Aturan Sistem

Dokumen ini adalah acuan implementasi hasil sesi desain 2026-09-18. Jika bertentangan dengan `HLD_Autonomous_Forensic_Sentinel.md` atau `mockup.html`, **dokumen ini yang berlaku**. Istilah bercetak tebal mengikuti glossary di `CONTEXT.md`; alasan keputusan besar ada di `docs/adr/`.

Daftar isi:
1. [Lingkup & batasan](#1-lingkup--batasan)
2. [Data & anggaran kredit API](#2-data--anggaran-kredit-api)
3. [Forensic Rule](#3-forensic-rule)
4. [Composite Risk Score & Incident Severity](#4-composite-risk-score--incident-severity)
5. [Siklus hidup Incident](#5-siklus-hidup-incident)
6. [Audit Run](#6-audit-run)
7. [Notifikasi Telegram](#7-notifikasi-telegram)
8. [Backtest](#8-backtest)
9. [Web App](#9-web-app)
10. [Keterbatasan yang wajib diungkap](#10-keterbatasan-yang-wajib-diungkap)

---

## 1. Lingkup & batasan

| Aspek | Keputusan |
|---|---|
| Tujuan | Hackathon-first (Sectors Hackathon 2026, Track 2). Kecepatan jadi > fitur enterprise. |
| Pengguna | Satu **Analyst** internal; ia juga satu-satunya penerima Telegram. Tidak ada sistem user. |
| Hosting | Heroku, Python buildpack (`Procfile`), 1 web dyno Basic, Heroku Postgres, Heroku Scheduler. Lihat ADR-0001. |
| Stack | FastAPI + Jinja + Tailwind + HTMX/Alpine + Chart.js. |
| Akses | Semua halaman bisa dibaca publik. Aksi tulis (ubah triage, catatan, "Run now") butuh satu password dari env var `ADMIN_PASSWORD`. |
| **Universe** | ±30 **Emiten** non-keuangan, daftar statis di `config/universe.json` (inti grup konglomerat + IDX80 non-keuangan berkapitalisasi terbesar). Emiten sektor Financials selalu dikecualikan, juga jika tak sengaja masuk daftar. |
| Zona waktu | Semua waktu tampil dalam WIB (Asia/Jakarta); disimpan UTC. |

## 2. Data & anggaran kredit API

### 2.1 Fakta API yang sudah diverifikasi
Bukti mentah di `.scratch/api-verification/`.

- `GET /v2/financials/quarterly/{symbol}/` — angka arus (revenue, earnings, OCF) **diskrit per kuartal**, bukan akumulasi YTD. Tanpa parameter mengembalikan 5 kuartal terakhir; `report_date=YYYY-MM-DD` mengembalikan tepat satu kuartal.
- Kredit dipotong **per kuartal yang dikembalikan** (header `limit-consumption`). Key utama berisi 500 kredit.
- `GET /v2/company/get_quarterly_financial_dates/{symbol}/` — daftar Report Period yang tersedia; tanpa potongan kredit. `GET /v2/company/report/{symbol}/?sections=overview` (nama & sektor) memotong 1 kredit, diambil sekali per Emiten.
- Ada batas laju jangka pendek: burst beberapa request per detik dibalas `429 RATE_LIMIT_EXCEEDED` dan pulih dalam ±1 menit. Client memberi jeda 1,5 detik antar-request dan menunggu 20–60 detik saat 429.
- Data kuartalan hanya tersedia **sejak 2020-Q1**.
- Tidak ada field piutang usaha; `retained_earnings` tidak ada di data kuartalan; `ebit` kadang `null`.
- `GET /v2/filings/?symbol=` — paginasi 20 baris; `holder_type` = `"insider"` mencakup direksi/komisaris **dan** pemegang saham ≥5%. Persentase dalam satuan persen (4.9 = 4,9%). Riwayat hanya ±1 tahun.
- `GET /v2/company/corporate-actions/{symbol}/` — `dividend[]` berisi `ex_date, payment_date, dividend_amount` (IDR/lembar), tidak terurut, tanpa penanda tunai/saham; seksi kosong bernilai `null`.

### 2.2 Aturan pengambilan data
1. Setiap respons API disimpan di Postgres (cache permanen). **Kuartal yang sudah tersimpan tidak pernah diambil ulang.**
2. Tiap Audit Run, untuk tiap Emiten: tentukan kuartal yang dibutuhkan (lihat 2.3); ambil hanya yang belum ada di cache, satu per satu dengan `report_date=`.
3. Filings dan corporate actions diambil ulang setiap Audit Run. **Terverifikasi:** respons kedua endpoint tidak membawa header `limit-consumption` sama sekali, jadi keduanya tidak memotong kredit (`.scratch/api-verification/filings_BUMI.json.headers`, `corporate_actions_ASII.json.headers`). Karena kuartal yang sudah di-cache tidak pernah diambil ulang, Audit Run kedua dan seterusnya dalam satu kuartal hampir tidak memakai kredit.
4. Setiap kredit yang terpakai dicatat per Audit Run (dari header `limit-consumption`).
5. Saat development & test, gunakan fixture JSON, bukan API live.

### 2.3 Jendela data per evaluasi
Untuk Report Period `t` (kuartal terbaru yang tersedia), evaluasi memakai **5 kuartal**: `t, t-1, t-2, t-3, t-4`.

- **TTM(x)** = x<sub>t</sub> + x<sub>t-1</sub> + x<sub>t-2</sub> + x<sub>t-3</sub>
- **YoY** membandingkan kuartal `t` dengan `t-4` (kuartal yang sama tahun lalu).

Jika ada kuartal yang dibutuhkan hilang (misal GIAA tidak punya 2025-Q3), rule yang memakainya menghasilkan `INSUFFICIENT_DATA`.

---

## 3. Forensic Rule

### 3.0 Kontrak umum
Setiap Forensic Rule menghasilkan satu **Rule Finding**:

| Field | Isi |
|---|---|
| `rule_id` | ID tetap (lihat tabel di bawah) |
| `status` | `PASS` \| `WARNING` \| `RED_FLAG` \| `INSUFFICIENT_DATA` |
| `value` | Nilai terhitung (atau `null`) |
| `thresholds` | Ambang yang dipakai |
| `inputs` | Nilai mentah + tanggal laporan asalnya + endpoint sumber |
| `headline` | Kalimat bahasa awam (untuk kartu UI & Telegram) |
| `missing` | Jika `INSUFFICIENT_DATA`: data apa yang tidak tersedia |

Aturan umum:
- Pembagian dengan nol, nilai `null`, atau kuartal hilang → `INSUFFICIENT_DATA`. **Tidak pernah dianggap `PASS`.**
- Perbandingan ambang: `RED_FLAG` diperiksa lebih dulu, lalu `WARNING`, sisanya `PASS`.

### Ringkasan

| rule_id | Nama tampilan | Subjudul awam | Bobot | Inti? |
|---|---|---|:-:|:-:|
| `SLOAN_ACCRUAL` | Sloan Accrual Ratio | Seberapa banyak laba yang bukan uang tunai | 25 | ✅ |
| `EARNINGS_CASH_DIVERGENCE` | Divergensi Laba–Kas | Laba naik, tapi kas operasi turun | 25 | ✅ |
| `ALTMAN_Z_ADAPTED` | Altman Z'' (Adapted) | Risiko kesulitan keuangan | 20 | ✅ |
| `BENEISH_ADAPTED` | Beneish (Adapted) | Tanda tekanan untuk memoles laporan | 15 | |
| `INSIDER_SELLING` | Penjualan Orang Dalam | Orang dalam/pemegang saham utama menjual | 10 | |
| `EARNINGS_WITHOUT_DIVIDEND` | Laba tanpa Dividen | Untung, tapi tidak membagi kas | 5 | |

Tidak dipakai: **Beneish DSRI** (tidak ada data piutang), **Beneish TATA** (formulanya identik dengan Sloan → hitung ganda). Lihat ADR-0002.

---

### 3.1 `SLOAN_ACCRUAL` — Sloan Accrual Ratio

**Formula**

```
Sloan = (TTM(earnings) − TTM(operating_cash_flow)) / ((total_assets_t + total_assets_t-4) / 2)
```

**Ambang**

| Status | Kondisi |
|---|---|
| `RED_FLAG` | Sloan > 10% |
| `WARNING` | 5% < Sloan ≤ 10% |
| `PASS` | Sloan ≤ 5% |

**INSUFFICIENT_DATA** jika salah satu dari 5 kuartal hilang, atau `earnings` / `operating_cash_flow` / `total_assets` bernilai `null`.

**Headline contoh:** "13,8% dari aset tercatat sebagai laba yang belum menjadi uang tunai (batas wajar 10%)."

---

### 3.2 `EARNINGS_CASH_DIVERGENCE` — Divergensi Laba–Kas

**Formula** (kuartal `t` vs `t-4`)

```
ΔLaba = (earnings_t − earnings_t-4) / |earnings_t-4|
ΔOCF  = (operating_cash_flow_t − operating_cash_flow_t-4) / |operating_cash_flow_t-4|
```

**Ambang**

| Status | Kondisi |
|---|---|
| `RED_FLAG` | ΔLaba ≥ +25% **dan** ΔOCF ≤ −15% |
| `WARNING` | ΔLaba ≥ +10% **dan** ΔOCF ≤ 0% |
| `PASS` | selain itu |

**INSUFFICIENT_DATA** jika:
- kuartal `t` atau `t-4` hilang / `null`;
- `earnings_t-4 ≤ 0` (pertumbuhan dari basis rugi tidak bermakna);
- `operating_cash_flow_t-4 = 0`.

**Headline contoh:** "Laba naik 52% dibanding kuartal yang sama tahun lalu, tapi kas operasi turun 28%."

---

### 3.3 `ALTMAN_Z_ADAPTED` — Altman Z'' (Adapted)

Model Z'' non-manufaktur, disesuaikan dengan data API (ADR-0002).

**Formula** (neraca kuartal `t`, EBIT TTM)

```
X1 = (total_current_asset_t − current_liabilities_t) / total_assets_t
X2 = total_equity_t / total_assets_t                 ← PROKSI retained earnings
X3 = TTM(EBIT*) / total_assets_t
X4 = total_equity_t / total_liabilities_t            ← nilai buku (sesuai Z'' asli)

Z = 6.56·X1 + 3.26·X2 + 6.72·X3 + 1.05·X4
```

`EBIT*` per kuartal = `ebit`; jika `null` pakai `operating_pnl`; jika keduanya `null` → `INSUFFICIENT_DATA`. Jika fallback dipakai, catat di `inputs`.

**Ambang** (lebih ketat dari Z'' asli 1.22 untuk mengimbangi X2 yang bias ke atas)

| Status | Kondisi |
|---|---|
| `RED_FLAG` | Z < 1.8 |
| `WARNING` | 1.8 ≤ Z < 2.9 |
| `PASS` | Z ≥ 2.9 |

**INSUFFICIENT_DATA** jika field neraca `t` `null`, `total_assets_t = 0`, `total_liabilities_t = 0`, atau EBIT* tidak tersedia untuk 4 kuartal.

**Headline contoh:** "Skor Altman 1,42 — masuk zona kesulitan keuangan."
**Catatan wajib di UI:** "Versi adaptasi: laba ditahan tidak tersedia di API sehingga diganti total ekuitas; ambang dibuat lebih ketat untuk mengimbangi."

---

### 3.4 `BENEISH_ADAPTED` — Beneish (Adapted)

Tiga sub-indeks, kuartal `t` vs `t-4`. Ambang = rata-rata kelompok manipulator pada Beneish (1999).

```
GMI  = (gross_profit_t-4 / revenue_t-4) / (gross_profit_t / revenue_t)      ambang > 1.19
SGI  = revenue_t / revenue_t-4                                               ambang > 1.61
LVGI = (total_liabilities_t / total_assets_t) / (total_liabilities_t-4 / total_assets_t-4)   ambang > 1.11
```

- Sub-indeks yang penyebutnya ≤ 0 atau datanya `null` → **tidak terevaluasi**.
- LVGI memakai `total_liabilities` (selalu terisi; `total_debt` bisa 0 untuk emiten tanpa utang berbunga).

**Ambang rule**

| Status | Kondisi |
|---|---|
| `INSUFFICIENT_DATA` | < 2 sub-indeks terevaluasi |
| `RED_FLAG` | ≥ 2 sub-indeks melewati ambang |
| `WARNING` | tepat 1 sub-indeks melewati ambang |
| `PASS` | 0 sub-indeks melewati ambang |

**Headline contoh:** "2 dari 3 indikator tekanan manipulasi menyala: margin kotor memburuk dan utang melonjak."

---

### 3.5 `INSIDER_SELLING` — Penjualan Orang Dalam

Tidak terikat Report Period; dievaluasi pada **tanggal Audit Run**.

**Data**: semua **Insider Filing** Emiten dengan `holder_type == "insider"` dan `timestamp` (tanggal publikasi) dalam **90 hari** sebelum tanggal Audit Run.

**Formula**

```
JualBersih% = Σ share_percentage_transaction (transaction_type == "sell")
            − Σ share_percentage_transaction (transaction_type == "buy")
```

`transaction_type == "others"` diabaikan (tampil di detail sebagai informasi).

**Ambang**

| Status | Kondisi |
|---|---|
| `RED_FLAG` | JualBersih% ≥ 2% |
| `WARNING` | 0.5% ≤ JualBersih% < 2% |
| `PASS` | JualBersih% < 0.5%, **termasuk tidak ada filing** |

**INSUFFICIENT_DATA** jika request filings gagal, dan **selalu di Backtest** (data sebelum ±2025 tidak tersedia).

**Bahasa UI:** selalu "orang dalam / pemegang saham utama", **tidak pernah** "Direksi" atau "Komisaris" (API tidak membedakannya). Detail menampilkan `holder_name`, tanggal, lembar, harga.

**Headline contoh:** "Orang dalam/pemegang saham utama menjual bersih 4,9% saham dalam 90 hari terakhir."

---

### 3.6 `EARNINGS_WITHOUT_DIVIDEND` — Laba tanpa Dividen

Rule konteks berbobot kecil. **Status maksimum `WARNING`, tidak pernah `RED_FLAG`.**

**Kondisi `WARNING`** (semua harus benar):
1. TTM(earnings) > 0,
2. TTM(operating_cash_flow) > 0,
3. tidak ada `dividend[].ex_date` dalam 365 hari sebelum tanggal acuan.

Tanggal acuan = tanggal Audit Run (live) atau `report_date` kuartal `t` (Backtest). `dividend == null` berarti tidak ada dividen.

Selain itu → `PASS`. **INSUFFICIENT_DATA** jika request corporate actions gagal atau TTM tidak bisa dihitung.

**Headline contoh:** "Membukukan laba dan kas operasi positif 12 bulan terakhir, tapi tidak membagikan dividen."

---

## 4. Composite Risk Score & Incident Severity

### 4.1 Composite Risk Score
Dihitung untuk **setiap Emiten di Universe** pada setiap Audit Run.

```
poin(rule)        = bobot × { RED_FLAG: 1.0, WARNING: 0.5, PASS: 0 }
bobot_terevaluasi = Σ bobot rule yang statusnya bukan INSUFFICIENT_DATA
Score             = 100 × Σ poin / bobot_terevaluasi        (dibulatkan 1 desimal)
```

- `bobot_terevaluasi = 0` → tidak ada skor; Emiten tampil "Tak bisa dinilai".
- **Low Confidence** jika `bobot_terevaluasi < 50`.

### 4.2 Incident Severity
Ditentukan berurutan:

1. **Pita skor:** `LOW` < 30 ≤ `MODERATE` < 60 ≤ `CRITICAL`.
2. **Lantai rule inti:** jika `SLOAN_ACCRUAL`, `EARNINGS_CASH_DIVERGENCE`, atau `ALTMAN_Z_ADAPTED` berstatus `RED_FLAG` dan hasil langkah 1 adalah `LOW` → naikkan ke `MODERATE`.
3. **Plafon Low Confidence:** jika Low Confidence dan hasilnya `CRITICAL` → turunkan ke `MODERATE`.

Alasan langkah 2 atau 3 yang aktif wajib disimpan dan ditampilkan (contoh: "Minimal Sedang karena Altman berstatus Bahaya").

### 4.3 Contoh perhitungan

| Rule | Status | Poin |
|---|---|---|
| Sloan (25) | RED_FLAG | 25 |
| Divergensi (25) | RED_FLAG | 25 |
| Altman (20) | WARNING | 10 |
| Beneish (15) | WARNING | 7.5 |
| Insider (10) | INSUFFICIENT_DATA | — |
| Dividen (5) | PASS | 0 |

`bobot_terevaluasi = 90`, `Score = 100 × 67.5 / 90 = 75.0` → `CRITICAL`, bukan Low Confidence.

---

## 5. Siklus hidup Incident

### 5.1 Identitas
- Satu **Incident** per pasangan (Emiten, Report Period).
- ID: `AFS-{tahun report}-Q{n}-{nomor urut 4 digit}`, contoh `AFS-2025-Q3-0007`. Nomor urut global per Report Period.
- URL: `{BASE_WEB_URL}/incidents/{event_id}`.

### 5.2 Aturan per Emiten pada setiap Audit Run

Report Period yang dievaluasi = kuartal terbaru yang tersedia untuk Emiten tersebut.

| Kondisi | Aksi | Telegram? |
|---|---|:-:|
| Belum ada Incident, severity `LOW` | Simpan Rule Finding & skor saja | ❌ |
| Belum ada Incident, severity ≥ `MODERATE` | **Buat Incident** baru, Triage Status `UNTRIAGED` | ✅ Incident baru |
| Incident ada, severity naik (**Escalation**) | Perbarui Incident yang sama; catat event di riwayat. Jika Triage Status `RESOLVED` atau `DISMISSED` → kembali ke `UNTRIAGED` | ✅ Escalation |
| Incident ada, severity sama | Perbarui skor & Rule Finding tanpa event | ❌ |
| Incident ada, severity turun (termasuk ke `LOW`) | Perbarui Incident; catat event "severity turun" di riwayat; Triage Status tidak berubah | ❌ |
| Report Period baru tersedia | Evaluasi sebagai Report Period baru (baris 1–2). Incident periode lama tidak diubah lagi | sesuai baris 1–2 |

Urutan severity untuk perbandingan: `LOW < MODERATE < CRITICAL`.

### 5.3 Insider Filing di tengah Report Period
Filing baru mengubah `INSIDER_SELLING` → skor dihitung ulang pada Report Period yang sama → diproses dengan tabel 5.2 (bisa jadi Escalation, atau membuat Incident baru jika sebelumnya `LOW`).

### 5.4 Triage
- Status: `UNTRIAGED` → `INVESTIGATING` → `RESOLVED` (sudah ditindaklanjuti) / `DISMISSED` (alarm palsu). Transisi bebas antar status.
- Setiap perubahan status dan catatan butuh password dan tercatat di riwayat Incident (waktu, status lama → baru).
- `DISMISSED` menekan notifikasi, **kecuali** terjadi Escalation.

---

## 6. Audit Run

### 6.1 Pemicu
| Pemicu | Mekanisme |
|---|---|
| `SCHEDULER` | Heroku Scheduler menjalankan `python -m afs run --scheduled` **setiap hari 01:00 UTC (08:00 WIB)**. Perintah langsung keluar tanpa mencatat apa pun jika Audit Run **belum jatuh tempo**: jatuh tempo bila `Audit Run SUCCESS terakhir` sudah lebih dari `RUN_INTERVAL_DAYS` (default **3 hari**) yang lalu, atau belum pernah ada satu pun run sukses. Anchor-nya run sukses terakhir, bukan kalender, supaya hari yang terlewat dikejar pada tick berikutnya. Run `FAILED` bukan anchor. |
| `MANUAL` | Tombol "Run now" (butuh password) memanggil entry point yang sama, tanpa cek hari. |

### 6.2 Aturan eksekusi
1. Hanya satu Audit Run boleh berjalan; permintaan kedua ditolak dengan pesan "Audit Run sedang berjalan" (lock di Postgres).
2. Urutan: muat Universe → ambil data (§2.2) → evaluasi 6 rule per Emiten → skor & severity → proses Incident (§5.2) → **buat Incident Insight** (§7.3) → kirim Telegram → tulis ringkasan run.
3. Kegagalan satu Emiten (API error, data rusak) **tidak menghentikan run**: Emiten dicatat sebagai gagal di log dan dilewati.
3b. Kegagalan pembuatan Incident Insight **tidak pernah menggagalkan run**: Insight dibiarkan kosong dan alasannya dicatat di log run.
4. `execution_status`:
   - `SUCCESS` — run selesai (walau ada Emiten yang gagal; jumlahnya dicatat);
   - `FAILED` — run berhenti total (misal DB tidak bisa diakses, semua request API gagal).
5. Yang dicatat per run: mulai, selesai, durasi, pemicu, jumlah Emiten dipindai, jumlah Emiten gagal, Incident baru, Escalation, kredit API terpakai, status, log teks.

---

## 7. Notifikasi Telegram

Penerima: satu chat (`TELEGRAM_CHAT_ID`). Semua label memakai kosakata §9.1.

### 7.1 Pesan Incident baru / Escalation
- Maksimal **3 Rule Finding** teratas, diurutkan `RED_FLAG` → `WARNING`, lalu bobot terbesar. Hanya `headline` bahasa awam.
- Tombol inline **"Buka Incident"** → URL Incident (bukan URL mentah di teks).
- Tampilkan label Low Confidence / alasan lantai severity bila ada.

```
🔴 Kritis · EMTK — Elang Mahkota Teknologi
Skor 75/100 · Laporan 2025-Q3
[Escalation: Sedang → Kritis]          ← hanya jika Escalation

• Laba naik 52% dibanding tahun lalu, tapi kas operasi turun 28%.
• 13,8% dari aset tercatat sebagai laba yang belum menjadi uang tunai.
• Skor Altman 2,1 — zona abu-abu kesulitan keuangan.

[ Buka Incident ]
```

Emoji severity: 🔴 Kritis, 🟡 Sedang.

### 7.3 Incident Insight di pesan
Bila Incident Insight tersedia, satu baris `apa_yang_terjadi` disisipkan setelah baris skor, dicetak miring dan diawali 🤖 supaya tidak tertukar dengan keluaran rule. Bila tidak tersedia (Gemini gagal atau `GEMINI_API_KEY` kosong), baris itu hilang dan pesan tetap dikirim apa adanya.

### 7.2 Ringkasan Audit Run
Dikirim **setiap** run selesai, termasuk jika hasilnya nol:

```
✅ Audit Run Sabtu 20 Sep 2026, 08:00 WIB (Terjadwal)
30 emiten dipindai · 2 Incident baru · 1 Escalation · 0 gagal
Kredit API terpakai: 12
```

Jika run `FAILED`:

```
❌ Audit Run GAGAL — Sabtu 20 Sep 2026, 08:00 WIB
Alasan: <pesan error singkat>
```

---

## 8. Backtest

- **Kasus:** WSKT dan SRIL (dalam jangkauan data 2020+). AISA dan GIAA tidak dipakai — skandalnya sebelum 2020.
- **Kejadian nyata** (diisi manual di `config/backtest_cases.json`, **lengkap dengan URL sumber berita — verifikasi sebelum dipakai**):
  - WSKT — suspensi perdagangan saham oleh BEI (Mei 2023).
  - SRIL — suspensi saham karena gagal bayar (Mei 2021); pailit (Oktober 2024).
- **Proses:** untuk setiap kuartal `t` dari 2021-Q1 (butuh `t-4` = 2020-Q1) sampai kuartal terakhir tersedia, jalankan keenam rule seolah-olah hari itu adalah `report_date` `t`. `INSIDER_SELLING` selalu `INSUFFICIENT_DATA`.
- **Tidak membuat Incident dan tidak mengirim Telegram.** Hasil disimpan di Postgres; data kuartal diambil sekali (±40 kredit total).
- **Klaim otomatis:** "Pertama kali Sedang: {kuartal}, {N} bulan sebelum {kejadian}". N dihitung dari `report_date` kuartal itu ke tanggal kejadian. Jika tidak pernah ≥ `MODERATE` sebelum kejadian, tampilkan apa adanya: "Tidak terdeteksi lebih awal". **Klaim di video harus berasal dari output ini.**

---

## 9. Web App

### 9.1 Kosakata tampilan
Nilai enum di kode/DB mengikuti glossary; UI memakai label berikut secara konsisten (juga di Telegram).

| Enum | Label UI | Warna |
|---|---|---|
| `PASS` | Aman | hijau |
| `WARNING` | Waspada | kuning |
| `RED_FLAG` | Bahaya | merah |
| `INSUFFICIENT_DATA` | Tak bisa dinilai | abu-abu |
| `LOW` | Rendah | hijau |
| `MODERATE` | Sedang | kuning |
| `CRITICAL` | Kritis | merah |
| `UNTRIAGED` / `INVESTIGATING` / `RESOLVED` / `DISMISSED` | Belum ditinjau / Sedang diperiksa / Sudah ditindaklanjuti / Alarm palsu | — |

Nama metode tetap (Sloan, Beneish, Altman) dan **selalu** disertai subjudul awam (§3 Ringkasan). Tema gelap, kontras teks minimal WCAG AA.

### 9.2 Prinsip
**Setiap angka dan kalimat di layar harus bisa dilacak ke data API atau ke aturan di dokumen ini.**

_Pengecualian tunggal:_ blok **Ringkasan AI** (Incident Insight, ADR-0003) berisi kalimat yang ditulis LLM. Blok itu wajib diberi label AI, wajib menyatakan bahwa angka resmi ada di Rule Finding di bawahnya, dan tidak pernah mempengaruhi Composite Risk Score maupun Incident Severity. Di luar blok berlabel itu, aturan di atas berlaku penuh. Karena itu dibuang dari mockup: Export PDF, "Analis Penanggung Jawab", "Rekomendasi Aksi Sistem", klaim "92% identik", banner Inbound Referral, penghitung kredit sisa (API tidak menyediakannya), menu Watchlist, warna ungu khusus insider, DSRI.

### 9.3 Halaman

**`/` — Dashboard**
1. Status sistem: hasil Audit Run terakhir (status, waktu, jumlah Emiten, Incident baru), **pemicu ditulis "Otomatis · sistem" / "Manual · analis"**, jadwal run berikutnya (= run sukses terakhir + `RUN_INTERVAL_DAYS`; "belum diketahui" bila belum pernah sukses), tombol "Jalankan sekarang" (password).
2. Tiga angka: jumlah Emiten Kritis / Sedang / Rendah.
3. Antrean triage: Incident `UNTRIAGED` di atas, lalu status lain; urut skor tertinggi.
4. Tabel Universe: semua Emiten — skor, severity, **enam penanda rule bernomor 1–6 sesuai urutan §3 Ringkasan** (nomor = posisi tetap, bukan peringkat; warna = status), label Low Confidence; bisa diurutkan; baris bisa dibuka untuk melihat Rule Finding. Legenda bernomor memakai penanda yang sama persis agar pemetaan nomor → rule terbaca tanpa keterangan tambahan.

**`/incidents/{event_id}` — Detail Incident** (tujuan link Telegram), urutan dari atas:
1. **Vonis:** satu kalimat ("EMTK — **Kritis** (75/100). Laba tumbuh tapi kas operasi tidak ikut."), Report Period, waktu terdeteksi, Triage Status, label Low Confidence / alasan lantai severity.
2. **Ringkasan AI** (Incident Insight, §9.2 & ADR-0003): apa yang terjadi, kenapa penting, yang perlu dicek. Bergaya visual berbeda dari kartu rule, menyebut model dan waktu pembuatan, dan punya tombol buat/buat ulang (password). Kosong bila belum pernah berhasil dibuat.
3. **Bukti perhitungan:** satu kartu per rule, urut Bahaya → Waspada → Aman → Tak bisa dinilai. Kartu: nama + subjudul awam, angka utama, headline. **Bisa dibuka:** formula, input mentah + tanggal laporan, ambang, endpoint sumber, catatan keterbatasan.
4. **Grafik:** laba bersih vs arus kas operasi, 5 kuartal.
5. **Panel triage:** ubah status + catatan (password).
6. **Riwayat:** dibuat, Escalation, severity turun, perubahan status.

**`/backtest`** — satu tab per kasus: grafik garis skor per kuartal dengan pita Rendah/Sedang/Kritis + garis vertikal kejadian nyata; kalimat klaim otomatis (§8); tabel Rule Finding per kuartal; catatan "Penjualan Orang Dalam tidak dinilai — data sebelum 2025 tidak tersedia".

**`/logs`** — tabel Audit Run: mulai, durasi, pemicu (Otomatis · sistem / Manual · analis), Emiten dipindai/gagal, Incident baru, Escalation, kredit terpakai, status. Baris bisa dibuka menjadi **tabel hasil per Emiten** (dari `EmitenEvaluation`: skor, severity, Incident yang dihasilkan); log teks mentah tetap tersimpan dan bisa dibuka di balik toggle.

---

## 10. Keterbatasan yang wajib diungkap

Tampilkan di halaman terkait (kartu rule / `/backtest`), bukan disembunyikan:

1. **Altman Adapted** — laba ditahan diganti total ekuitas; ambang diperketat.
2. **Beneish Adapted** — hanya 3 dari 8 indeks (GMI, SGI, LVGI); bukan M-Score utuh.
3. **Penjualan Orang Dalam** — "insider" di API mencakup pemegang saham ≥5%; riwayat hanya ±1 tahun; persentase dibulatkan 2 desimal sehingga transaksi sangat kecil tercatat 0%.
4. **Laba tanpa Dividen** — tidak bisa membedakan dividen tunai vs saham.
5. **Data historis** — hanya sejak 2020-Q1.
6. **Sektor keuangan** tidak dinilai (model tidak valid untuk bank/asuransi).

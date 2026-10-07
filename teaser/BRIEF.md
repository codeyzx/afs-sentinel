---
workflow: product-launch-video
flow: automation
storyboard: no
message: "AFS Sentinel menemukan tanda bahaya di laporan keuangan emiten BEI secara otomatis — bertahun-tahun sebelum skandalnya meledak."
destination: youtube
aspect: 1920x1080
language: id
audience: "Juri Sectors Hackathon 2026 dan komunitas investor/analis pasar modal Indonesia"
length: 60s
angle: "Proof-first: hook dari kasus nyata WSKT (suspensi Mei 2023), klimaks backtest 25 bulan lebih awal"
voice: id-ID-ArdiNeural
---

## Intent

Teaser 1 menit wajib untuk submisi Sectors Hackathon 2026 (Track 2 — Automation & Workflows),
dipublikasikan publik di YouTube dan dipakai juga untuk postingan media sosial yang men-tag Sectors.
Produk: AFS Sentinel (Autonomous Forensic Sentinel) — sistem peringatan dini yang setiap 3 hari
memindai 33 emiten non-keuangan BEI dengan 6 Forensic Rule (Sloan, Divergensi Laba–Kas, Altman Z'',
Beneish, Penjualan Orang Dalam, Laba tanpa Dividen) memakai data Sectors API, lalu mengirim alert
Telegram ke Analyst dan menyajikan bukti di web app.

Gaya: hybrid — rekaman layar produk asli yang sedang berjalan (syarat RULES.md: "rekaman layar
produk saat berjalan") dibungkus motion graphics: kinetic typography, count-up angka, punch-in ke
UI, cut mengikuti beat. Tegas, forensik, sedikit tegang — seperti thriller investigasi, bukan iklan ceria.

## Assets

- https://afs-sentinel-ee5d2e28af17.herokuapp.com — web app produksi (data asli, bukan devseed).
- assets/footage/*.webm — rekaman layar Playwright dari web app produksi (dashboard, incident, backtest, logs).

## Customizations

- Count-up "25 bulan" pada klimaks backtest WSKT (angka dari output /backtest: "Pertama kali Sedang: 2021-Q1, 25 bulan sebelum BEI menghentikan sementara perdagangan saham WSKT", kejadian 8 Mei 2023). SRIL: 42 bulan sebelum pailit.
- Adegan run otonom: badge "Otomatis · sistem", "33 emiten dipindai", jadwal berikutnya.
- Adegan alert Telegram (rekonstruksi pesan bot, bukan rekaman HP).
- Subtitle Bahasa Indonesia ditanam.
- End card: "AFS Sentinel", "Powered by Sectors API", "Sectors Hackathon 2026 · Track 2", disclaimer.

## Notes

- Gratis: voice-over edge-tts (id-ID); musik dari katalog audio HeyGen lewat jalur OAuth gratis (`media-use resolve --type bgm`), menggantikan MusicGen lokal v1 yang kualitasnya kurang.
- Wajib disclaimer: "Alat analisis & informasi, bukan nasihat investasi."
- Semua angka di layar harus berasal dari data aplikasi produksi / output backtest.
- Jangan tampilkan password, API key, token, chat id.
- Hard cap 60 detik.

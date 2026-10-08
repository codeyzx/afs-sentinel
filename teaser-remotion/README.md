# Teaser 60 detik — AFS Sentinel (Remotion, v3 "Sinyal")

Trailer bergaya thriller forensik: malam, satu warna merah sinyal, rekaman layar produk asli
di jendela 3D, dan satu klimaks: **WSKT ditandai 25 bulan sebelum suspensi**. Semua tools gratis.

```bash
cd teaser-remotion
npm install
npm run dev       # Remotion Studio
npm run render    # out/teaser.mp4 (1920×1080, 30 fps, 59,5 dtk)
node scripts/stills.mjs 12s 46.9s   # cek frame tertentu → out/stills/
```

## Alur (master clock di `src/timeline.ts`)

| Detik | Adegan | Isi |
|---|---|---|
| 0–6,9 | hook | "8 MEI 2023", WSKT, PERDAGANGAN DIHENTIKAN, garis detak jantung berhenti |
| 6,9–13,5 | rewind | Mundur ke 2021; deret laporan kuartalan WSKT dengan skor backtest asli |
| 13,5–16,8 | who | Tembok 33 emiten × kuartal: "siapa yang sempat membaca semuanya?" |
| 16,8–21,4 | reveal | Hening sejenak → braam → logo; 33 emiten berwarna sesuai severity live |
| 21,4–28,3 | auto | Dashboard + Log Audit asli: tiap 3 hari, tanpa manusia, Sectors API, 33 emiten |
| 28,3–33,6 | rules | 6 Forensic Rule dan bobotnya → skor komposit 0–100 |
| 33,6–41,0 | alert | Notifikasi Telegram (teks bot asli, UNVR) → Ringkasan AI → bukti formula + endpoint |
| 41,0–51,3 | climax | Halaman backtest asli → grafik WSKT → **25 BULAN**; lalu SRIL 42 bulan sebelum pailit |
| 51,3–59,5 | outro | Logo, "Peringatan dini. Sebelum terlambat.", Sectors API, Track 2, disclaimer |

Cut setelah reveal dikunci ke beat musik (160 BPM). Semua efek visual memakai waktu kata VO (`w("baris", "kata")`).

## Audio

- **Voice-over**: `scripts/vo.py` (Edge TTS `id-ID-ArdiNeural`, gratis) → `public/voice/*.wav` + `src/gen/vo.json`
  (timing per kata). Rantai mastering ffmpeg: EQ, kompresor, sedikit ruang, −16 LUFS.
  Ganti suara: `uvx --with edge-tts python -I scripts/vo.py <voice>`. Naskah ada di `LINES` di skrip itu.
  Kalau tim merekam suara sendiri, simpan per baris dengan nama yang sama lalu perbarui `vo.json`
  (timing kata bisa diambil dengan faster-whisper).
- **Musik**: "Impact Prelude" — Kevin MacLeod (incompetech.com), lisensi **CC BY 4.0**. Wajib atribusi
  (sudah ada di end card; tempel juga di deskripsi YouTube). Dipotong jadi 3 bagian di `MUSIC` (`src/timeline.ts`):
  intro → berhenti di reveal → masuk lagi di "AFS" → berhenti sebelum "dua puluh lima" → masuk penuh di "bulan".
- **SFX**: `public/audio/sfx/` (katalog yang sudah ada), cue-nya di `src/Teaser.tsx`.

## Sumber angka

Semua angka di layar berasal dari aplikasi produksi (8 Okt 2026), dicatat di `src/data.ts`: 33 emiten,
10 Perlu ditinjau / 23 Aman, skor backtest WSKT per kuartal, SRIL 42 bulan, Incident AFS-2026-Q2-0003 (UNVR, skor 45,
Sloan 22,7%, Altman 0,57). Telegram adalah rekonstruksi dari format pesan bot asli (`afs/telegram.py`), diberi label di layar.

## Deskripsi YouTube (atribusi)

```
Music: "Impact Prelude" by Kevin MacLeod (incompetech.com)
Licensed under Creative Commons: By Attribution 4.0
http://creativecommons.org/licenses/by/4.0/
```

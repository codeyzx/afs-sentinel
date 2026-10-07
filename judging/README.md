# Video Judging — AFS Sentinel (Remotion)

Video penjurian 3:00 untuk Sectors Hackathon 2026 · Track 2. Tema visual "Case File":
dossier forensik di atas kertas, produk asli tampil sebagai "exhibit".

```bash
cd judging
npm install
npm run dev        # Remotion Studio, preview + timeline
npm run render     # out/judging.mp4 (1920×1080, 30 fps)
```

## Yang tim kerjakan

Rekam wajah + suara lewat **`npm run rekam`** (perekam webcam di browser dengan prompter bawaan; tidak
perlu `npm install`) atau kamera HP + video prompter (`npm run prompter`). Panduan: **[REKAMAN.md](REKAMAN.md)**.
File bernama sesuai klip di `public/recordings/` ditemukan otomatis oleh `npm run sync` (konversi ke MP4 +
deteksi awal/akhir bicara); `src/media.ts` hanya untuk nama file yang berbeda. Durasi scene mengikuti rekaman; studio menampilkan
peringatan merah kalau total lewat 3:00. Link GitHub untuk end card juga di `src/media.ts`.

Satu jadwal kata (`src/words.ts`) dipakai bersama oleh prompter, subtitle, dan semua efek visual
(`atWord(scene, line, "kata")`), jadi selama tempo baca mengikuti prompter, efek jatuh tepat di katanya.

## Struktur

| Path | Isi |
|---|---|
| `src/script.ts` | Naskah: scene, baris VO, durasi target, arahan. Sumber subtitle, prompter & placeholder. |
| `src/words.ts` | Jadwal per kata (bobot suku kata + jeda tanda baca). |
| `src/Prompter.tsx` | Komposisi teleprompter per klip (folder "Prompter" di Studio). |
| `src/generated/sync.json` | File + awal/akhir bicara per rekaman — `npm run sync`. |
| `src/generated/prompter.json` | Daftar klip + jadwal kata untuk perekam — `npm run checklist`. |
| `scripts/rekam.mjs`, `rekam.html` | Perekam webcam + prompter di browser (`npm run rekam`, localhost:4747). |
| `src/media.ts` | Nama file rekaman tim, trim awal klip, isi end card. |
| `src/timeline.ts` | Hitung durasi scene dari rekaman (`calculateMetadata`). |
| `src/scenes/` | SC01–SC10. |
| `src/components/` | Kertas, stabilo, stempel, kamera wajah, jendela exhibit (zoom + kursor), Telegram. |
| `src/data/real.json` | Data produksi asli (alert, run, backtest) — `scripts/export_data.py`. |
| `public/capture/` | Rekaman layar produksi 2× + peta klik/elemen untuk kamera — `scripts/capture.mjs`. |
| `public/audio/` | Musik latar & SFX (katalog HeyGen). |

## Merekam ulang layar produk

```bash
npm run login                       # sekali: login Heroku (dan Telegram Web bila perlu)
node scripts/capture.mjs scheduler backtest logs incident-evidence incident-ai
ADMIN_PASSWORD=$(heroku config:get ADMIN_PASSWORD -a afs-sentinel) node scripts/capture.mjs incident-triage
```

`incident-triage` mengubah status Incident AFS-2026-Q2-0003 di produksi lalu mengembalikannya;
setiap percobaan menambah dua baris di Riwayat incident itu. Setelah merekam ulang, cek posisi
`timeMap`/`keys` di scene terkait karena waktu klik bisa bergeser.

Telegram di SC06/SC09 adalah rekonstruksi tampilan dari teks pesan bot asli (formatter
`afs/telegram.py` + data produksi), diberi label di layar.

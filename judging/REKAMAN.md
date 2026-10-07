# Daftar rekaman — Video Judging AFS Sentinel

> Dibuat otomatis dari `src/script.ts` (`npm run checklist`). Ubah naskah di sana, bukan di sini.

Semua visual, rekaman layar produk, Telegram, musik, SFX, dan subtitle sudah ada di video.
Yang kurang hanya **wajah + suara** kalian.

## Cara A (disarankan): kamera laptop + perekam bawaan

Prompter dan perekam jadi satu halaman: rekaman mulai tepat bersama prompter, file langsung bernama benar.

1. Butuh: folder `judging/` dari repo + Node.js (versi 18 ke atas) + Chrome/Edge. **Tidak perlu `npm install`.**
2. Di folder `judging/`, jalankan `npm run rekam` → browser terbuka di `http://localhost:4747` (izinkan kamera & mic).
3. Pilih nama kalian (Fathan / Ais / Yahya), pilih klip, cek posisi wajah di preview, lalu tekan **Spasi**.
4. Layar penuh: hitung mundur 3-2-1 → **langsung baca kata yang menyala kuning**. Teks ada di atas layar, dekat kamera.
5. Muncul **TAHAN DIAM** → tetap menatap kamera; rekaman berhenti sendiri.
6. Tonton ulang → **Enter** simpan, **R** ulangi. File masuk ke `public/recordings/` dengan nama yang benar;
   take lama otomatis dipindah ke `public/recordings/_old/`. Halaman memberi tahu kalau tempo kalian terlalu cepat/lambat.
7. Selesai semua klip → kirim isi `public/recordings/` (tanpa `_old/`) ke editor.

Tips: pilih mic earphone/eksternal di dropdown kalau ada (mic laptop menangkap kipas). Tinggikan laptop sampai kamera
sejajar mata. Esc membatalkan take.

## Cara B: kamera HP + video prompter

Video prompter per klip ada di `out/prompter/<Fathan|Ais|Yahya>/` (`npm run prompter`), daftar putarnya `out/prompter/index.html`.
Pasang HP tepat di atas layar laptop, pakai earphone satu telinga (bip hitung mundur jangan masuk mic), **mulai rekam di HP
dulu** baru putar prompter, baca kata yang menyala, tahan diam di akhir. Simpan dengan nama file persis seperti tabel.
iPhone: Settings → Camera → Formats → Most Compatible.

Kenapa harus ikut prompter: zoom, stabilo, lingkaran merah, dan subtitle di video dipicu oleh kata yang sama dengan
kata yang menyala di prompter. Kalau tempo kalian sama dengan prompter, semua efek jatuh tepat di kata yang diucapkan.

## Aturan rekam

- **Kamera**: landscape, 720p ke atas. Wajah di tengah (kotak kuning di preview), sisakan ruang di atas kepala — akan di-crop jadi kotak potret.
- **Cahaya**: jendela/lampu di depan wajah, bukan di belakang. Latar polos & rapi. Baju sama di semua klip.
- **Suara**: ruangan sepi, HP/mic dekat mulut (±30 cm). Kalau ada mic clip-on, pakai.
- **Arah mata**: ke lensa kamera; baca prompter dengan melirik sedikit ke bawah.
- **Nama file** (cara B): persis seperti tabel, ekstensi bebas (`.mp4`/`.mov`/`.webm`; suara saja boleh `.wav`/`.m4a`).

## Fathan — 6 klip

| File | Prompter | Scene | Durasi | Ucapkan | Arahan |
|---|---|---|---|---|---|
| `SC02_CAM_Fathan` | `Fathan/PROMPT_SC02_CAM_Fathan.mp4` | SC02 · Perkenalan & masalah | ±16 dtk | Halo, Juri! Kami JTKTOP10. Saya Fathan, ini Yahya, developer kami, dan Ais, researcher. Masalahnya: tanda bahaya itu sudah ada di laporan keuangan, tapi tidak ada analis yang sempat membedah ratusan laporan setiap kuartal. | Energik di awal, serius mulai “Masalahnya:”. Beri jeda kecil setelah “Yahya” dan “Ais”. |
| `SC03_CAM_Fathan` | `Fathan/PROMPT_SC03_CAM_Fathan.mp4` | SC03 · Solusi & target audiens | ±14.8 dtk | AFS Sentinel kami bangun untuk analis riset dan investor saham BEI. Ia memindai 33 emiten non-keuangan secara otomatis, lalu hanya melaporkan yang perlu diperiksa. Analis tidak perlu lagi mencari, tinggal memutuskan. | Persuasif. |
| `SC07a_CAM_Fathan` | `Fathan/PROMPT_SC07a_CAM_Fathan.mp4` | SC07 · Halaman incident | ±14.5 dtk | …dan kita langsung masuk ke halaman bukti. Vonisnya di atas. Setiap kartu bukti bisa dibuka: rumusnya, angka mentahnya, sampai endpoint Sectors asalnya. Grafik ini menunjukkan laba naik, tapi kas operasi tertinggal. | Menyambung kalimat Yahya. Lancar, menunjukkan. |
| `SC07b_CAM_Fathan` | `Fathan/PROMPT_SC07b_CAM_Fathan.mp4` | SC07 · Halaman incident | ±4.2 dtk | Setelah ditelaah, analis tinggal menandai: sedang diperiksa. | Datar, yakin. |
| `SC10_CAM_Fathan` | `Fathan/PROMPT_SC10_CAM_Fathan.mp4` | SC10 · Penutup | ±6.8 dtk | Laporan keuangan sudah memberi peringatan. AFS Sentinel memastikan ada yang membacanya, tepat waktu. | Pelan, meyakinkan. |
| `SC10_ALL_Fathan` | `Fathan/PROMPT_SC10_ALL_Fathan.mp4` | SC10 · Penutup | ±3.5 dtk | AFS Sentinel. Peringatan dini, sebelum terlambat. | Tatap kamera, ucapkan serempak sambil senyum. Mulai bicara 1 detik setelah tombol rekam. |

## Ais — 7 klip

| File | Prompter | Scene | Durasi | Ucapkan | Arahan |
|---|---|---|---|---|---|
| `SC01_VO_Ais` (suara saja) | `Ais/PROMPT_SC01_VO_Ais.mp4` | SC01 · Hook | ±10.8 dtk | Delapan Mei 2023. Bursa menghentikan perdagangan saham Waskita Karya. Sistem kami… sudah menandainya dua puluh lima bulan sebelumnya. | Suara saja. Pelan, berat. Jeda panjang setelah “Waskita Karya”. |
| `SC02_CAM_Ais` | `Ais/PROMPT_SC02_CAM_Ais.mp4` | SC02 · Perkenalan & masalah | ±3 dtk | (mengangguk ke kamera) | Diam, senyum, lalu mengangguk. |
| `SC05_CAM_Ais` | `Ais/PROMPT_SC05_CAM_Ais.mp4` | SC05 · Mesin forensik | ±16.8 dtk | Mesinnya enam Forensic Rule yang deterministik. Tiga inti: Sloan Accrual, divergensi laba dan kas, dan Altman Z. Ditambah Beneish, penjualan orang dalam, dan laba tanpa dividen. Semuanya digabung menjadi satu skor risiko, nol sampai seratus. | Yakin. Hitung pakai jari (jari masuk frame). |
| `SC07_CAM_Ais` | `Ais/PROMPT_SC07_CAM_Ais.mp4` | SC07 · Halaman incident | ±5.5 dtk | Ringkasan AI hanya menceritakan angka yang sudah dihitung. AI tidak pernah mengubah skor. | Menekankan “tidak pernah”. |
| `SC08_CAM_Ais` | `Ais/PROMPT_SC08_CAM_Ais.mp4` | SC08 · Backtest | ±20 dtk | Tapi apakah ini benar-benar bekerja? Kami putar ulang keenam rule ke kuartal historis. Waskita: pertama kali level Sedang di 2021-Q1, dua puluh lima bulan sebelum suspensi. Sritex: empat puluh dua bulan sebelum pailit. Kalimat klaim ini dihasilkan oleh sistem, bukan kami tulis tangan. | Retoris di awal, tegas di angka 25 dan 42. |
| `SC10_CAM_Ais` | `Ais/PROMPT_SC10_CAM_Ais.mp4` | SC10 · Penutup | ±2 dtk | Terukur, bisa dilacak… | Menggantung, oper ke Yahya. |
| `SC10_ALL_Ais` | `Ais/PROMPT_SC10_ALL_Ais.mp4` | SC10 · Penutup | ±3.5 dtk | AFS Sentinel. Peringatan dini, sebelum terlambat. | Tatap kamera, ucapkan serempak sambil senyum. Mulai bicara 1 detik setelah tombol rekam. |

## Yahya — 6 klip

| File | Prompter | Scene | Durasi | Ucapkan | Arahan |
|---|---|---|---|---|---|
| `SC02_CAM_Yahya` | `Yahya/PROMPT_SC02_CAM_Yahya.mp4` | SC02 · Perkenalan & masalah | ±3 dtk | (melambai ke kamera) | Diam, senyum, lalu melambai. Santai. |
| `SC04_CAM_Yahya` | `Yahya/PROMPT_SC04_CAM_Yahya.mp4` | SC04 · Otomasi | ±21 dtk | Ini jantung otomasinya. Heroku Scheduler memicu pipeline setiap pagi jam delapan WIB, dan pipeline sendiri yang menentukan kapan jatuh tempo: tiga hari sejak run sukses terakhir. Tanpa tombol, tanpa manusia. Data Sectors API disimpan permanen di Postgres, jadi kuartal yang sama tidak pernah dibayar dua kali. | Tenang, jelas. Tekankan “tanpa tombol, tanpa manusia”. |
| `SC06_CAM_Yahya` | `Yahya/PROMPT_SC06_CAM_Yahya.mp4` | SC06 · Alert Telegram | ±11.5 dtk | Begitu skor menembus ambang, Analyst langsung menerima ini di Telegram: tingkat keparahan, skor, dan tiga temuan teratas dalam bahasa awam. Satu klik di ‘Buka Incident’… | Sedikit mendesak. Akhir kalimat menggantung (dioper ke Fathan). |
| `SC09_CAM_Yahya` | `Yahya/PROMPT_SC09_CAM_Yahya.mp4` | SC09 · Log run | ±17.5 dtk | Dan ini bukti eksekusi tanpa pengawasan: riwayat Audit Run. Label ‘Otomatis · sistem’ berarti dipicu scheduler, tidak disentuh siapa pun, lengkap dengan timestamp, jumlah emiten, dan kredit API. Setiap run juga melapor ke Telegram, termasuk saat hasilnya nol. | Mantap. |
| `SC10_CAM_Yahya` | `Yahya/PROMPT_SC10_CAM_Yahya.mp4` | SC10 · Penutup | ±2 dtk | …dan berjalan sendiri. | Menutup kalimat Ais. |
| `SC10_ALL_Yahya` | `Yahya/PROMPT_SC10_ALL_Yahya.mp4` | SC10 · Penutup | ±3.5 dtk | AFS Sentinel. Peringatan dini, sebelum terlambat. | Tatap kamera, ucapkan serempak sambil senyum. Mulai bicara 1 detik setelah tombol rekam. |

## Untuk editor: memasukkan rekaman

1. Taruh semua file di `judging/public/recordings/` (nama = nama klip, ekstensi bebas).
2. `npm run sync` — menemukan file dari namanya, mengonversi HEVC/WebM ke MP4 (asli ke `_raw/`), dan mendeteksi
   kapan bicara mulai & selesai (hitung mundur dan diam di awal/akhir terpotong sendiri). Butuh ffmpeg.
3. `npm run dev` untuk cek di Remotion Studio, `npm run render` untuk hasil akhir (`out/judging.mp4`).

Kalau deteksi meleset di satu klip, isi `TRIM_START` di `src/media.ts` (detik saat kata pertama diucapkan).
Nama file berbeda? Tulis di `RECORDINGS` di `src/media.ts`.

# Teaser 60 detik — AFS Sentinel (Remotion)

Versi Remotion dari teaser, dengan tema "Case File" yang sama seperti video judging (`../judging`).
Narasi tetap memakai voice-over teaser lama (`public/voice/vo-01..09.wav`); semua visual, musik, dan SFX baru.

```bash
cd teaser-remotion
npm install
npm run dev      # Remotion Studio
npm run render   # out/teaser.mp4 (1920×1080, 30 fps, 59,8 dtk)
```

## Struktur

| Path | Isi |
|---|---|
| `src/vo.ts` | 9 baris VO, durasi scene = durasi VO, `w(line, "kata")` = frame awal kata (dari `src/data/vo.json`). |
| `src/data/captions.json` | Grup subtitle ber-timestamp kata (karaoke). |
| `src/scenes/` | 9 frame: cold open, twist, intro, otonom, 6 rule, alert, bukti, klimaks, outro. |
| `src/components/` | Disalin dari `judging`: kertas, stabilo, stempel, jendela exhibit + kamera, Telegram. |
| `public/capture/` | Rekaman layar produksi (sama dengan judging). |
| `public/audio/` | Musik latar (drop-nya jatuh di "dua puluh lima") + SFX katalog HeyGen. |

Semua timing visual dikunci ke timestamp kata VO. Kalau VO diganti, perbarui `src/data/vo.json`
dan `src/data/captions.json` (format sama dengan `teaser/audio_meta.json` / `teaser/caption_groups.json`).

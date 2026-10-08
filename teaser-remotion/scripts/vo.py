"""Generate the teaser voice-over with Edge TTS (free) and word timings.

    uvx --with edge-tts python -I scripts/vo.py

Writes public/voice/<id>.wav (mastered) and src/gen/vo.json. Each line is its own clip so the
edit can leave room for music hits between them.
"""
import asyncio
import json
import subprocess
import sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "voice"
GEN = ROOT / "src" / "gen"
VOICE = sys.argv[1] if len(sys.argv) > 1 else "id-ID-ArdiNeural"

# id, text, rate, pitch
LINES = [
    ("date", "Delapan Mei, dua ribu dua puluh tiga.", "-12%", "-6Hz"),
    ("halt", "Perdagangan saham Waskita Karya dihentikan.", "-6%", "-6Hz"),
    ("signs", "Padahal, tanda bahayanya sudah ada di laporan keuangan. Bertahun-tahun sebelumnya.", "-4%", "-5Hz"),
    ("who", "Tapi, siapa yang sempat membaca semuanya?", "-6%", "-4Hz"),
    ("intro", "Kenalkan. AFS Sentinel.", "-10%", "-6Hz"),
    ("auto", "Setiap tiga hari, tanpa disentuh manusia, ia menarik data Sectors API, dan memindai tiga puluh tiga emiten.", "+4%", "-4Hz"),
    ("rules", "Enam aturan forensik memburu laba tanpa kas, utang yang melonjak, dan risiko gagal bayar.", "+6%", "-4Hz"),
    ("alert", "Begitu ada yang janggal, peringatan langsung masuk ke Telegram.", "+4%", "-4Hz"),
    ("proof", "Lengkap dengan ringkasan AI, dan bukti perhitungan yang bisa dilacak.", "+2%", "-4Hz"),
    ("test", "Kami uji pada kasus nyata.", "-6%", "-6Hz"),
    ("flag", "Sentinel sudah menandai Waskita,", "-8%", "-6Hz"),
    ("months", "dua puluh lima bulan sebelum suspensi.", "-10%", "-7Hz"),
    ("name", "AFS Sentinel.", "-12%", "-7Hz"),
    ("tag", "Peringatan dini. Sebelum terlambat.", "-10%", "-7Hz"),
]

# Warm, close, broadcast-style chain: rumble cut, chest, presence, gentle de-ess, compression,
# a short room so it sits in the score, then loudness to -16 LUFS.
CHAIN = ",".join([
    "highpass=f=70",
    "equalizer=f=140:t=q:w=1:g=3",
    "equalizer=f=320:t=q:w=1.2:g=-2",
    "equalizer=f=3200:t=q:w=1.5:g=2.5",
    "equalizer=f=7500:t=q:w=2:g=-2",
    "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3",
    "aecho=0.8:0.5:38|61:0.16|0.09",
    # loudnorm needs ~3 s of signal to measure; pad short lines so they match the long ones
    "apad=whole_dur=4",
    "loudnorm=I=-16:TP=-1.5:LRA=7",
])


async def synth(text: str, rate: str, pitch: str, mp3: Path) -> list[dict]:
    words = []
    com = edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch, boundary="WordBoundary")
    with mp3.open("wb") as f:
        async for chunk in com.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append({"text": chunk["text"], "start": round(start, 3), "end": round(start + chunk["duration"] / 1e7, 3)})
    return words


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout)


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    GEN.mkdir(parents=True, exist_ok=True)
    tmp = ROOT / "out" / "vo-raw"
    tmp.mkdir(parents=True, exist_ok=True)
    result = []
    for lid, text, rate, pitch in LINES:
        mp3 = tmp / f"{lid}.mp3"
        words = await synth(text, rate, pitch, mp3)
        wav = OUT / f"{lid}.wav"
        # Trim edge-tts lead-in silence so the clip starts on the first word; the timings shift with it.
        lead = max(0.0, words[0]["start"] - 0.04)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{lead:.3f}", "-i", str(mp3), "-af", CHAIN, "-ar", "48000", "-ac", "2", str(wav)], check=True)
        for w in words:
            w["start"] = round(w["start"] - lead, 3)
            w["end"] = round(w["end"] - lead, 3)
        speech_end = words[-1]["end"]
        result.append({"id": lid, "text": text, "file": f"voice/{lid}.wav", "duration": round(duration(wav), 3), "speechEnd": speech_end, "words": words})
        print(f"{lid:7s} {speech_end:5.2f}s  {text}")
    (GEN / "vo.json").write_text(json.dumps({"voice": VOICE, "lines": result}, ensure_ascii=False, indent=1))
    print("total speech", round(sum(r["speechEnd"] for r in result), 2))


asyncio.run(main())

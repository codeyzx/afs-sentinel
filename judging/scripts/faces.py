"""Find where the face sits in each recorded clip so FaceCam can crop around it.

Samples frames inside the spoken part of every video in src/generated/sync.json, runs OpenCV's
frontal-face detector, and stores the median face centre and size (fractions of the frame)
plus the frame size back into sync.json as "face": {"x", "y", "h"}, "w", "hgt".

Usage (from judging/):  uv run --with "opencv-python-headless<5" python scripts/faces.py [CLIP ...]
"""
import json
import statistics
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
SYNC = ROOT / "src/generated/sync.json"
REC = ROOT / "public/recordings"
SAMPLES = 15


def face_of(path: Path, start: float, end: float):
    cap = cv2.VideoCapture(str(path))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if not w or not h:
        return None
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    hits = []
    for i in range(SAMPLES):
        t = start + (end - start) * (i + 0.5) / SAMPLES
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = det.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(h // 10, h // 10))
        if len(faces):
            x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])
            hits.append(((x + fw / 2) / w, (y + fh / 2) / h, fh / h))
    cap.release()
    if not hits:
        return {"w": w, "hgt": h}
    return {
        "w": w,
        "hgt": h,
        "face": {
            "x": round(statistics.median(p[0] for p in hits), 3),
            "y": round(statistics.median(p[1] for p in hits), 3),
            "h": round(statistics.median(p[2] for p in hits), 3),
        },
    }


def main(only):
    sync = json.loads(SYNC.read_text())
    for clip, entry in sync.items():
        if only and clip not in only:
            continue
        path = REC / entry["file"]
        if path.suffix.lower() in {".m4a", ".wav", ".mp3", ".aac", ".ogg"}:
            continue
        info = face_of(path, entry["start"], max(entry["end"], entry["start"] + 1))
        if info is None:
            continue
        entry.update(info)
        f = info.get("face")
        print(f"{clip}: " + (f"wajah di x={f['x']:.0%} y={f['y']:.0%} (tinggi {f['h']:.0%})" if f else "wajah tidak terdeteksi, crop tengah"))
    SYNC.write_text(json.dumps(sync, indent=2) + "\n")


if __name__ == "__main__":
    main(set(sys.argv[1:]))

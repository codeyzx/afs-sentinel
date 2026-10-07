// Find the team's recordings and where speech starts/ends in each.
//
// A file counts when it sits in public/recordings/ named after its clip (SC04_CAM_Yahya.mp4,
// .mov, .webm, .m4a, .wav …); src/media.ts can still point a clip at another file name.
// Video that is not H.264 MP4 (iPhone HEVC .mov, browser .webm) is converted to MP4 once, the
// original kept in public/recordings/_raw/. Short beeps from a prompter countdown are ignored:
// speech must stay loud for most of a 300 ms window.
//
// Writes src/generated/sync.json { clip: { file, start, end } } (seconds).
// Usage: npm run sync            (all clips)
//        node scripts/sync.mjs SC04_CAM_Yahya
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const REC = path.join(ROOT, "public/recordings");
const OUT = path.join(ROOT, "src/generated/sync.json");
const EXTS = [".mp4", ".mov", ".m4v", ".webm", ".mkv", ".m4a", ".wav", ".mp3", ".aac", ".ogg"];
const AUDIO_ONLY = new Set([".m4a", ".wav", ".mp3", ".aac", ".ogg"]);
const RATE = 16000;
const HOP = 0.02; // 20 ms frames

const prompter = () => JSON.parse(fs.readFileSync(path.join(ROOT, "src/generated/prompter.json"), "utf8"));
export const clipIds = () => prompter().clips.map((c) => c.clip);

/** Explicit file names from src/media.ts (override the naming convention). */
const overrides = () => {
  const src = fs.readFileSync(path.join(ROOT, "src/media.ts"), "utf8");
  return Object.fromEntries([...src.matchAll(/^\s+(SC\w+):\s*"([^"]+)"/gm)].map((m) => [m[1], m[2]]));
};

export const hasFfmpeg = () => {
  try {
    execFileSync("ffmpeg", ["-version"], { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
};

const probe = (file) =>
  JSON.parse(execFileSync("ffprobe", ["-v", "error", "-show_entries", "stream=codec_type,codec_name:format=duration", "-of", "json", file]).toString());

function findFile(clip, override) {
  if (override) return fs.existsSync(path.join(REC, override)) ? override : null;
  const hits = EXTS.map((e) => clip + e).filter((f) => fs.existsSync(path.join(REC, f)));
  return hits.find((f) => f.endsWith(".mp4")) ?? hits[0] ?? null;
}

/** H.264/AAC MP4 at a constant 30 fps; keeps the original in _raw/. */
function normalize(file) {
  const ext = path.extname(file).toLowerCase();
  if (AUDIO_ONLY.has(ext)) return file;
  const info = probe(path.join(REC, file));
  const v = info.streams.find((s) => s.codec_type === "video");
  if (ext === ".mp4" && (!v || v.codec_name === "h264")) return file;
  const target = path.basename(file, ext) + ".mp4";
  const tmp = path.join(REC, `.${target}.tmp.mp4`);
  execFileSync("ffmpeg", [
    "-v", "error", "-y", "-i", path.join(REC, file),
    "-vf", "fps=30,scale=-2:'min(1080,ih)'", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", tmp,
  ]);
  fs.mkdirSync(path.join(REC, "_raw"), { recursive: true });
  fs.renameSync(path.join(REC, file), path.join(REC, "_raw", file));
  fs.renameSync(tmp, path.join(REC, target));
  console.log(`  ${file} → ${target} (asli disimpan di _raw/)`);
  return target;
}

function envelope(file) {
  const raw = execFileSync("ffmpeg", ["-v", "error", "-i", file, "-vn", "-ac", "1", "-ar", String(RATE), "-f", "f32le", "-"], { maxBuffer: 1 << 30 });
  const pcm = new Float32Array(raw.buffer, raw.byteOffset, raw.byteLength / 4);
  const n = Math.floor(pcm.length / (RATE * HOP));
  const db = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    let sum = 0;
    const a = Math.floor(i * RATE * HOP);
    const b = Math.floor((i + 1) * RATE * HOP);
    for (let j = a; j < b; j++) sum += pcm[j] * pcm[j];
    db[i] = 10 * Math.log10(sum / (b - a) + 1e-12);
  }
  return db;
}

function speechSpan(db) {
  const sorted = [...db].sort((a, b) => a - b);
  const floor = sorted[Math.floor(sorted.length * 0.1)];
  const peak = sorted[Math.floor(sorted.length * 0.98)];
  if (peak - floor < 12) return null; // nothing louder than the room
  const thr = Math.max(floor + 0.35 * (peak - floor), -50);
  const on = Array.from(db, (v) => v > thr);
  const win = Math.round(0.3 / HOP);
  const dense = (i) => {
    let c = 0;
    for (let k = i; k < i + win && k < on.length; k++) c += on[k] ? 1 : 0;
    return c / win >= 0.6;
  };
  const start = on.findIndex((v, i) => v && dense(i));
  let end = -1;
  for (let i = on.length - 1; i >= 0; i--) {
    if (on[i] && dense(Math.max(0, i - win + 1))) {
      end = i;
      break;
    }
  }
  if (start < 0 || end < 0) return null;
  return { start: Math.max(0, start * HOP - 0.06), end: (end + 1) * HOP + 0.12 };
}

/** Face position per clip (scripts/faces.py via uv + OpenCV); skipped quietly when uv is missing. */
function faces(clips) {
  if (!clips.length) return;
  try {
    execFileSync("uv", ["run", "--quiet", "--with", "opencv-python-headless<5", "python", path.join(ROOT, "scripts/faces.py"), ...clips], { cwd: ROOT, stdio: ["ignore", "inherit", "inherit"] });
  } catch {
    console.log("  (deteksi wajah dilewati — butuh uv; crop tengah dipakai)");
  }
}

/** Sync the given clips (default: all) and merge them into sync.json. Returns the entries. */
export function syncClips(only) {
  const P = prompter();
  const ids = clipIds().filter((c) => !only?.length || only.includes(c));
  const over = overrides();
  const state = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, "utf8")) : {};
  const result = {};
  for (const clip of ids) {
    let file = findFile(clip, over[clip]);
    if (!file) {
      delete state[clip];
      continue;
    }
    file = over[clip] ? file : normalize(file);
    const full = path.join(REC, file);
    const duration = Number(probe(full).format.duration);
    const span = speechSpan(envelope(full));
    // No speech (wave/nod clips): a prompter take starts its action after the countdown.
    const target = P.clips.find((c) => c.clip === clip).target;
    const silentStart = duration >= P.countdown + target ? P.countdown : 0;
    const entry = span
      ? { file, start: +span.start.toFixed(2), end: +Math.min(span.end, duration).toFixed(2) }
      : { file, start: silentStart, end: +Math.min(duration, silentStart + target + 0.5).toFixed(2), silent: true };
    state[clip] = entry;
    result[clip] = entry;
    const len = (entry.end - entry.start).toFixed(1);
    console.log(`${clip}: ${file} · ${span ? `bicara ${entry.start}s → ${entry.end}s (${len} dtk)` : `tanpa suara, aksi ${entry.start}s → ${entry.end}s (${len} dtk)`}`);
  }
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  const sorted = Object.fromEntries(Object.keys(state).sort().map((k) => [k, state[k]]));
  fs.writeFileSync(OUT, JSON.stringify(sorted, null, 2) + "\n");
  faces(Object.keys(result));
  for (const k of Object.keys(result)) result[k] = JSON.parse(fs.readFileSync(OUT, "utf8"))[k];
  return result;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  if (!hasFfmpeg()) {
    console.error("ffmpeg tidak ditemukan. Install ffmpeg dulu (https://ffmpeg.org/download.html).");
    process.exit(1);
  }
  fs.mkdirSync(REC, { recursive: true });
  const found = syncClips(process.argv.slice(2));
  const missing = clipIds().filter((c) => !JSON.parse(fs.readFileSync(OUT, "utf8"))[c]);
  console.log(`\n${Object.keys(found).length} klip tersinkron · src/generated/sync.json`);
  if (missing.length) console.log(`Belum ada rekaman (${missing.length}): ${missing.join(", ")}`);
}

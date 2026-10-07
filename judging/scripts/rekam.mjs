// Browser recorder for the team: webcam + mic, with the prompter built in.
//   npm run rekam      → opens http://localhost:4747
// Only Node built-ins; ffmpeg is optional (without it, takes are saved as-is and synced later).
// Takes are saved to public/recordings/<CLIP>.<ext>; an older take moves to public/recordings/_old/.
import { exec } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { clipIds, hasFfmpeg, syncClips } from "./sync.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const REC = path.join(ROOT, "public/recordings");
const PORT = Number(process.env.PORT ?? 4747);
const FFMPEG = hasFfmpeg();
fs.mkdirSync(REC, { recursive: true });

const readJson = (p, fallback) => (fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, "utf8")) : fallback);

function status() {
  const sync = readJson(path.join(ROOT, "src/generated/sync.json"), {});
  const files = fs.readdirSync(REC);
  return Object.fromEntries(
    clipIds().map((clip) => {
      const file = files.find((f) => f.startsWith(clip + ".") && !f.startsWith("."));
      return [clip, file ? { file, ...(sync[clip]?.file === file ? sync[clip] : {}) } : null];
    }),
  );
}

function save(clip, ext, req, res) {
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  for (const f of fs.readdirSync(REC).filter((f) => f.startsWith(clip + "."))) {
    fs.mkdirSync(path.join(REC, "_old"), { recursive: true });
    fs.renameSync(path.join(REC, f), path.join(REC, "_old", `${clip}-${stamp}${path.extname(f)}`));
  }
  const file = `${clip}.${ext}`;
  const out = fs.createWriteStream(path.join(REC, file));
  req.pipe(out);
  out.on("finish", () => {
    let entry = { file };
    let note = null;
    if (FFMPEG) {
      try {
        entry = syncClips([clip])[clip] ?? entry;
      } catch (err) {
        note = `Tersimpan, tapi cek otomatis gagal: ${err.message}`;
      }
    } else {
      note = "Tersimpan. ffmpeg tidak ada di komputer ini — editor menjalankan `npm run sync` nanti.";
    }
    console.log(`✓ ${clip} → public/recordings/${entry.file}`);
    send(res, 200, { entry, note });
  });
  out.on("error", (err) => send(res, 500, { error: err.message }));
}

const send = (res, code, body, type = "application/json") => {
  res.writeHead(code, { "content-type": type, "cache-control": "no-store" });
  res.end(type === "application/json" ? JSON.stringify(body) : body);
};

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  if (req.method === "GET" && url.pathname === "/") return send(res, 200, fs.readFileSync(path.join(ROOT, "scripts/rekam.html")), "text/html; charset=utf-8");
  if (req.method === "GET" && url.pathname === "/api/clips") {
    return send(res, 200, { ...readJson(path.join(ROOT, "src/generated/prompter.json"), { clips: [] }), status: status(), ffmpeg: FFMPEG });
  }
  if (req.method === "POST" && url.pathname === "/api/save") {
    const clip = url.searchParams.get("clip");
    const ext = url.searchParams.get("ext");
    if (!clipIds().includes(clip) || !["mp4", "webm"].includes(ext)) return send(res, 400, { error: "klip/format tidak dikenal" });
    return save(clip, ext, req, res);
  }
  send(res, 404, { error: "not found" });
});

server.listen(PORT, "127.0.0.1", () => {
  const url = `http://localhost:${PORT}`;
  console.log(`Perekam siap: ${url}   (Ctrl+C untuk berhenti)`);
  console.log(FFMPEG ? "ffmpeg ada: take langsung dicek & disinkronkan." : "ffmpeg tidak ada: take disimpan apa adanya.");
  const opener = process.platform === "darwin" ? "open" : process.platform === "win32" ? "start \"\"" : "xdg-open";
  if (!process.env.NO_OPEN) exec(`${opener} ${url}`);
});

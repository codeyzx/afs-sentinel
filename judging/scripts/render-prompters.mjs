// Render one teleprompter video per clip into out/prompter/, plus an index.html playlist per person.
// Usage: node scripts/render-prompters.mjs [CLIP_ID ...]
import { bundle } from "@remotion/bundler";
import { getCompositions, renderMedia } from "@remotion/renderer";
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const outDir = path.join(root, "out/prompter");
fs.mkdirSync(outDir, { recursive: true });
// Folders and playlist sections, in this order.
const PEOPLE = ["Fathan", "Ais", "Yahya"];
const indexOnly = process.argv.includes("--index-only");
const only = new Set(process.argv.slice(2).filter((a) => !a.startsWith("--")).map((c) => `Prompter-${c.replace(/_/g, "-")}`));

const serveUrl = indexOnly ? null : await bundle({ entryPoint: path.join(root, "src/index.ts"), publicDir: path.join(root, "public") });
const comps = indexOnly ? [] : (await getCompositions(serveUrl)).filter((c) => c.id.startsWith("Prompter-") && (!only.size || only.has(c.id)));
const rendered = [];
for (const composition of comps) {
  const clip = composition.defaultProps.clip;
  const who = PEOPLE.find((p) => clip.endsWith(`_${p}`));
  const file = `${who}/PROMPT_${clip}.mp4`;
  fs.mkdirSync(path.join(outDir, who), { recursive: true });
  await renderMedia({ serveUrl, composition, codec: "h264", crf: 20, outputLocation: path.join(outDir, file), inputProps: composition.defaultProps });
  rendered.push({ clip, file, seconds: composition.durationInFrames / composition.fps });
  console.log(file);
}

// Playlist page: one tab per person, clips in story order.
const sections = PEOPLE
  .map((who) => {
    const dir = path.join(outDir, who);
    const files = (fs.existsSync(dir) ? fs.readdirSync(dir) : [])
      .filter((f) => f.startsWith("PROMPT_") && f.endsWith(".mp4"))
      // story order; the group line (ALL) comes after the solo line in SC10
      .sort((a, b) => a.replace("_ALL_", "_ZALL_").localeCompare(b.replace("_ALL_", "_ZALL_"), "en", { numeric: true }));
    return `<section><h2>${who} · ${files.length} klip</h2><ol>${files
      .map((f) => `<li><button data-src="${who}/${f}">${f.replace("PROMPT_", "").replace(".mp4", "")}</button></li>`)
      .join("")}</ol></section>`;
  })
  .join("");
fs.writeFileSync(
  path.join(outDir, "index.html"),
  `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Prompter AFS Sentinel</title>
<style>
body{margin:0;background:#0E0D0B;color:#F4EFE6;font:18px system-ui;display:grid;grid-template-columns:320px 1fr;height:100vh}
aside{overflow:auto;padding:16px;border-right:1px solid #333}h2{font-size:16px;color:#D93A2B;letter-spacing:.08em;text-transform:uppercase}
ol{padding-left:22px}button{all:unset;cursor:pointer;padding:4px 6px;border-radius:6px;font-family:ui-monospace,monospace;font-size:15px}
button.on{background:#F5D547;color:#0E0D0B}main{display:flex;flex-direction:column}video{width:100%;max-height:calc(100vh - 60px);background:#000}
p{margin:12px 16px;color:#aaa;font-size:15px}
</style>
<aside>${sections}</aside>
<main><video id="v" controls></video><p>Mulai rekam di kamera dulu → klik klip → video diputar dari awal. Baca kata yang menyala. Spasi = putar ulang.</p></main>
<script>
const v=document.getElementById('v');let cur;
document.querySelectorAll('button').forEach(b=>b.onclick=()=>{document.querySelectorAll('button').forEach(x=>x.classList.remove('on'));b.classList.add('on');cur=b;v.src=b.dataset.src;v.currentTime=0;v.play();v.requestFullscreen?.().catch(()=>{});});
document.addEventListener('keydown',e=>{if(e.code==='Space'&&cur){e.preventDefault();v.currentTime=0;v.play();}});
</script>`,
);
console.log(`${rendered.length} prompter rendered → ${outDir}`);

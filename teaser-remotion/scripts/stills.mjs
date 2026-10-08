// Render frames for review: node scripts/stills.mjs 100 600 1200 ...  (seconds with an "s" suffix: 12.5s)
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const frames = process.argv.slice(2).map((a) => (a.endsWith("s") ? Math.round(parseFloat(a) * 30) : Number(a)));
const serveUrl = await bundle({ entryPoint: path.join(root, "src/index.ts"), publicDir: path.join(root, "public") });
const composition = await selectComposition({ serveUrl, id: "Teaser" });
for (const frame of frames) {
  const output = path.join(root, "out/stills", `f${String(frame).padStart(5, "0")}.jpg`);
  await renderStill({ serveUrl, composition, frame, output, imageFormat: "jpeg", jpegQuality: 80, scale: 0.5, timeoutInMilliseconds: 120000 });
  console.log(output);
}

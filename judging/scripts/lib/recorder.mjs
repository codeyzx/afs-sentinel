// High-res screen capture via the Chrome DevTools screencast. Frames arrive only when the page
// repaints, each with a wall-clock timestamp; we rebuild a constant 30fps video from them and
// log cursor samples, clicks and element boxes so Remotion can draw a cursor and aim the camera.
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

export const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");
export const VIEWPORT = { width: 1600, height: 900 };
export const SCALE = 2;
export const UA =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36";

const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

export async function record(page, name, script) {
  const work = path.join(ROOT, "out/capture", name);
  fs.rmSync(work, { recursive: true, force: true });
  fs.mkdirSync(work, { recursive: true });

  const cdp = await page.context().newCDPSession(page);
  const frames = [];
  const events = [];
  let t0 = null;
  const now = () => Date.now() / 1000 - t0;

  cdp.on("Page.screencastFrame", async ({ data, metadata, sessionId }) => {
    const file = path.join(work, `${String(frames.length).padStart(5, "0")}.jpg`);
    fs.writeFileSync(file, Buffer.from(data, "base64"));
    frames.push({ file, ts: metadata.timestamp });
    await cdp.send("Page.screencastFrameAck", { sessionId }).catch(() => {});
  });

  let cursor = { x: VIEWPORT.width * 0.62, y: VIEWPORT.height * 0.7 };
  await page.mouse.move(cursor.x, cursor.y);

  const box = async (locator) => {
    await locator.waitFor({ state: "visible" });
    const b = await locator.boundingBox();
    return { x: b.x, y: b.y, w: b.width, h: b.height };
  };

  const h = {
    page,
    wait: (ms) => page.waitForTimeout(ms),
    /** Record an element's on-screen box under a label (camera target). */
    mark: async (label, locator) => {
      const b = await box(locator);
      events.push({ t: now(), type: "mark", label, ...b });
      return b;
    },
    moveTo: async (x, y, ms = 700) => {
      const steps = Math.max(2, Math.round(ms / 16));
      const from = { ...cursor };
      for (let i = 1; i <= steps; i++) {
        const k = ease(i / steps);
        const p = { x: from.x + (x - from.x) * k, y: from.y + (y - from.y) * k };
        await page.mouse.move(p.x, p.y);
        events.push({ t: now(), type: "cursor", x: p.x, y: p.y });
        await page.waitForTimeout(ms / steps);
      }
      cursor = { x, y };
    },
    hover: async (locator, ms) => {
      const b = await box(locator);
      await h.moveTo(b.x + b.w / 2, b.y + b.h / 2, ms);
      return b;
    },
    click: async (label, locator, ms) => {
      const b = await h.hover(locator, ms);
      events.push({ t: now(), type: "click", label, x: cursor.x, y: cursor.y, w: b.w, h: b.h, bx: b.x, by: b.y });
      await page.mouse.down();
      await page.waitForTimeout(90);
      await page.mouse.up();
    },
    /** Eased smooth scroll so the screencast gets a frame per step. */
    scrollTo: async (y, ms = 1200) => {
      const start = now();
      await page.evaluate(
        ([target, dur]) =>
          new Promise((done) => {
            const from = window.scrollY;
            const begin = performance.now();
            const e = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
            const step = (nowMs) => {
              const k = Math.min(1, (nowMs - begin) / dur);
              window.scrollTo(0, from + (target - from) * e(k));
              k < 1 ? requestAnimationFrame(step) : done();
            };
            requestAnimationFrame(step);
          }),
        [y, ms],
      );
      events.push({ t: start, type: "scroll", y, dur: ms / 1000 });
    },
    scrollToEl: async (locator, offset = 80, ms) => {
      const y = await locator.evaluate((el, off) => el.getBoundingClientRect().top + window.scrollY - off, offset);
      await h.scrollTo(Math.max(0, y), ms);
    },
  };

  await cdp.send("Page.startScreencast", {
    format: "jpeg",
    quality: 92,
    maxWidth: VIEWPORT.width * SCALE,
    maxHeight: VIEWPORT.height * SCALE,
    everyNthFrame: 1,
  });
  t0 = Date.now() / 1000;
  // Nudge a repaint so the first frame lands immediately.
  await page.evaluate(() => (document.body.style.outline = "0px solid transparent"));
  await script(h);
  await page.waitForTimeout(300);
  const tEnd = now();
  await cdp.send("Page.stopScreencast");
  await page.waitForTimeout(300);

  if (!frames.length) throw new Error(`${name}: no frames captured`);
  // Frame timestamps share the wall clock with t0; the first frame shows from 0.
  const list = frames.map((f, i) => {
    const start = i === 0 ? 0 : f.ts - t0;
    const end = i + 1 < frames.length ? frames[i + 1].ts - t0 : tEnd;
    return `file '${f.file}'\nduration ${Math.max(0.001, end - start).toFixed(4)}`;
  });
  list.push(`file '${frames.at(-1).file}'`);
  const listFile = path.join(work, "list.txt");
  fs.writeFileSync(listFile, list.join("\n"));

  const outDir = path.join(ROOT, "public/capture");
  fs.mkdirSync(outDir, { recursive: true });
  execFileSync("ffmpeg", [
    "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", listFile,
    "-vf", `fps=30,scale=${VIEWPORT.width * SCALE}:${VIEWPORT.height * SCALE}:force_original_aspect_ratio=decrease,pad=${VIEWPORT.width * SCALE}:${VIEWPORT.height * SCALE}:(ow-iw)/2:(oh-ih)/2,format=yuv420p`,
    "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-movflags", "+faststart",
    path.join(outDir, `${name}.mp4`),
  ]);
  const meta = { name, duration: tEnd, viewport: VIEWPORT, scale: SCALE, events };
  fs.writeFileSync(path.join(outDir, `${name}.json`), JSON.stringify(meta, null, 1));
  console.log(`${name}: ${frames.length} frames, ${tEnd.toFixed(1)}s, ${events.filter((e) => e.type !== "cursor").length} marks`);
  return meta;
}

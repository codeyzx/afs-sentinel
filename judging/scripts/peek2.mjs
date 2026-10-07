import { chromium } from "playwright";
const headless = process.argv[2] !== "headed";
const ctx = await chromium.launchPersistentContext(".browser-profile", { headless, viewport: { width: 1600, height: 900 },
  userAgent: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36" });
const page = await ctx.newPage();
page.on("framenavigated", f => f === page.mainFrame() && console.log("nav", f.url()));
await page.goto("https://dashboard.heroku.com/apps/afs-sentinel/resources", { waitUntil: "networkidle" }).catch(e => console.log(e.message));
await page.waitForTimeout(5000);
await page.screenshot({ path: `out/shots/heroku-resources.png` });
await page.goto("https://dashboard.heroku.com/apps/afs-sentinel/scheduler", { waitUntil: "networkidle" }).catch(e => console.log(e.message));
await page.waitForTimeout(8000);
await page.screenshot({ path: `out/shots/scheduler2.png` });
await ctx.close();

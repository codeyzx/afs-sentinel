import { chromium } from "playwright";
const ctx = await chromium.launchPersistentContext(".browser-profile", { headless: true, viewport: { width: 1600, height: 900 } });
const page = await ctx.newPage();
const base = "https://afs-sentinel-ee5d2e28af17.herokuapp.com";
for (const [name, url] of [
  ["scheduler", "https://dashboard.heroku.com/apps/afs-sentinel/scheduler"],
  ["incident", base + "/incidents/AFS-2026-Q2-0003"],
  ["backtest", base + "/backtest"],
  ["logs", base + "/logs"],
]) {
  await page.goto(url, { waitUntil: "networkidle" }).catch(() => {});
  await page.waitForTimeout(4000);
  console.log(name, page.url(), await page.evaluate(() => document.body.scrollHeight));
  await page.screenshot({ path: `out/shots/${name}.png`, fullPage: true });
}
await ctx.close();

// One-time login: opens a persistent browser profile so the recording scripts can
// reuse the Heroku and Telegram Web sessions. Close the browser window when done.
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";

const profile = fileURLToPath(new URL("../.browser-profile", import.meta.url));

const ctx = await chromium.launchPersistentContext(profile, {
  headless: false,
  viewport: null,
  args: ["--window-size=1600,1000"],
});

const heroku = ctx.pages()[0] ?? (await ctx.newPage());
await heroku.goto("https://dashboard.heroku.com/apps/afs-sentinel/scheduler");
const telegram = await ctx.newPage();
await telegram.goto("https://web.telegram.org/a/");

console.log("Login ke Heroku (tab 1) dan scan QR Telegram (tab 2), lalu tutup jendela browser.");
await new Promise((resolve) => ctx.on("close", resolve));
console.log("Sesi tersimpan di judging/.browser-profile");

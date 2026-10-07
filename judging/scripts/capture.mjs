// Scripted screen recordings of the production app and the Heroku Scheduler.
// Usage: ADMIN_PASSWORD=... node scripts/capture.mjs [scheduler|incident|backtest|logs|dashboard ...]
import { chromium } from "playwright";
import path from "node:path";
import { record, ROOT, SCALE, UA, VIEWPORT } from "./lib/recorder.mjs";

const BASE = "https://afs-sentinel-ee5d2e28af17.herokuapp.com";
const EVENT_ID = "AFS-2026-Q2-0003";

const scenes = {
  async scheduler(page) {
    await page.goto("https://dashboard.heroku.com/apps/afs-sentinel/scheduler", { waitUntil: "domcontentloaded" });
    const row = page.locator("tr", { hasText: "python -m afs run --scheduled" });
    await row.waitFor({ timeout: 60000 });
    await page.waitForTimeout(1500);
    await record(page, "scheduler", async (h) => {
      await h.wait(800);
      await h.mark("table", page.locator("table").first());
      await h.hover(row.locator("code, pre, span", { hasText: "python" }).first(), 900);
      await h.mark("command", row.locator("code, pre, span", { hasText: "python" }).first());
      await h.mark("row", row);
      await h.wait(1600);
      await h.hover(row.getByText("Daily at", { exact: false }), 800);
      await h.mark("frequency", row.getByText("Daily at", { exact: false }));
      await h.wait(1600);
      await h.hover(row.locator("td").nth(3), 700);
      await h.mark("lastRun", row.locator("td").nth(3));
      await h.mark("nextDue", row.locator("td").nth(4));
      await h.wait(2000);
    });
  },

  async "incident-evidence"(page) {
    const url = `${BASE}/incidents/${EVENT_ID}`;
    await page.goto(url, { waitUntil: "networkidle" });
    await page.waitForTimeout(1500);
    await record(page, "incident-evidence", async (h) => {
      await h.wait(600);
      await h.mark("verdict", page.locator("main h1, h1").first());
      await h.mark("meta", page.locator("dl").first());
      await h.wait(2600);
      const evidence = page.locator("#why-heading");
      await h.scrollToEl(evidence, 40, 1400);
      await h.wait(400);
      const card = page.locator("section[aria-labelledby=why-heading] article").first();
      await h.mark("card", card);
      const more = card.getByText("Lihat rincian perhitungan");
      await h.click("open-card", more, 900);
      await h.wait(700);
      await h.mark("formula", card.getByText("Formula", { exact: true }).first().locator("xpath=.."));
      await h.mark("inputs", card.locator("table"));
      await h.wait(2200);
      const endpoint = card.locator("p.break-all");
      await h.scrollToEl(endpoint, 420, 1600);
      await h.wait(300);
      await h.mark("endpoint", endpoint.locator("xpath=.."));
      await h.wait(2600);
      const chart = page.locator("canvas").last();
      await h.scrollToEl(chart, 140, 1500);
      await h.wait(500);
      await h.mark("chart", chart.locator("xpath=.."));
      await h.wait(4500);
    });
  },

  async "incident-ai"(page) {
    const url = `${BASE}/incidents/${EVENT_ID}`;
    // B: AI summary
    await page.goto(url, { waitUntil: "networkidle" });
    await page.waitForTimeout(1200);
    await record(page, "incident-ai", async (h) => {
      const ai = page.getByText("Ringkasan AI").first();
      await h.wait(300);
      await h.scrollToEl(ai, 120, 1200);
      await h.wait(300);
      await h.mark("ai", page.locator("section", { has: ai }).first());
      await h.mark("ai-footer", page.getByText("Ditulis AI dari").first());
      await h.wait(5500);
    });

  },

  async "incident-triage"(page) {
    await login(page);
    const url = `${BASE}/incidents/${EVENT_ID}`;
    // C: triage status → Sedang diperiksa (reverted below, outside the recording)
    await page.goto(url, { waitUntil: "networkidle" });
    const triage = page.locator("#triage");
    await triage.scrollIntoViewIfNeeded();
    await page.evaluate(() => window.scrollTo(0, document.querySelector("#triage").offsetTop - 260));
    await page.waitForTimeout(1200);
    const notes = await triage.locator("textarea[name=notes]").inputValue();
    try {
      await record(page, "incident-triage", async (h) => {
        await h.wait(600);
        const select = triage.locator("select[name=status]");
        await h.mark("triage", triage.locator(".panel"));
        await h.hover(select, 800);
        await select.selectOption("INVESTIGATING");
        await h.mark("select", select);
        await h.wait(1000);
        const nav = page.waitForURL(/.*/, { waitUntil: "load" });
        await h.click("save", triage.locator("button[type=submit]"), 800);
        await nav;
        await page.waitForLoadState("networkidle");
        await h.wait(500);
        await h.mark("status-badge", page.locator("dt", { hasText: "Status triage" }).locator("xpath=following-sibling::dd"));
        await h.wait(2600);
      });
    } finally {
      await revertTriage(page, url, notes);
    }
  },

  async revert(page) {
    await login(page);
    await revertTriage(page, `${BASE}/incidents/${EVENT_ID}`, "");
  },

  async backtest(page) {
    await page.goto(`${BASE}/backtest`, { waitUntil: "networkidle" });
    await page.waitForTimeout(2000);
    await record(page, "backtest", async (h) => {
      await h.wait(500);
      const wskt = page.locator("#panel-WSKT");
      await h.mark("tab-wskt", page.locator("#tab-WSKT"));
      await h.mark("claim-wskt", wskt.locator("p.font-display").first());
      await h.mark("chart-wskt", wskt.locator("canvas").first());
      await h.hover(wskt.locator("p.font-display").first(), 900);
      await h.wait(4200);
      await h.click("tab-sril", page.locator("#tab-SRIL"), 900);
      await h.wait(1200);
      const sril = page.locator("#panel-SRIL");
      await h.mark("claim-sril", sril.locator("p.font-display").first());
      await h.mark("claim-sril-42", sril.locator("p.font-display").nth(1));
      await h.mark("chart-sril", sril.locator("canvas").first());
      await h.hover(sril.locator("p.font-display").nth(1), 900);
      await h.wait(4500);
    });
  },

  async logs(page) {
    await page.goto(`${BASE}/logs`, { waitUntil: "networkidle" });
    await page.waitForTimeout(1500);
    await record(page, "logs", async (h) => {
      await h.wait(600);
      const rows = page.locator("table tr:visible").filter({ hasText: "WIB" });
      await h.mark("table", page.locator("table").first());
      await h.mark("row1", rows.nth(0));
      await h.mark("row2", rows.nth(1));
      await h.mark("row3", rows.nth(2));
      await h.hover(rows.nth(0).getByText("Otomatis"), 900);
      await h.mark("trigger1", rows.nth(0).getByText("Otomatis"));
      await h.wait(2200);
      await h.hover(rows.nth(0).locator("td").last(), 700);
      await h.wait(1200);
      await h.click("expand", rows.nth(0).locator("td").first(), 800);
      await h.wait(1200);
      await h.mark("expanded", page.locator("table").first());
      await h.wait(3500);
    });
  },

  async dashboard(page) {
    await page.goto(`${BASE}/`, { waitUntil: "networkidle" });
    await page.waitForTimeout(2000);
    await record(page, "dashboard", async (h) => {
      await h.wait(1200);
      await h.mark("top", page.locator("main").first());
      await h.scrollTo(700, 2600);
      await h.wait(1500);
      await h.scrollTo(1400, 2600);
      await h.wait(1500);
    });
  },
};

async function revertTriage(page, url, notes) {
  await page.goto(url, { waitUntil: "networkidle" });
  await page.locator("#triage select[name=status]").selectOption("UNTRIAGED");
  await page.locator("#triage textarea[name=notes]").fill(notes);
  await Promise.all([page.waitForURL(/.*/, { waitUntil: "load" }), page.locator("#triage button[type=submit]").click()]);
  console.log("triage reverted:", (await page.locator("dt", { hasText: "Status triage" }).locator("xpath=following-sibling::dd").innerText()).trim());
}

async function login(page) {
  const password = process.env.ADMIN_PASSWORD;
  if (!password) throw new Error("ADMIN_PASSWORD is required for the incident capture");
  await page.goto(`${BASE}/login`, { waitUntil: "networkidle" });
  await page.locator("input[name=password]").fill(password);
  await page.locator("form[action='/login'] button[type=submit]").click();
  await page.waitForLoadState("networkidle");
}

const wanted = process.argv.slice(2);
const names = wanted.length ? wanted : Object.keys(scenes);
const ctx = await chromium.launchPersistentContext(path.join(ROOT, ".browser-profile"), {
  headless: true,
  viewport: VIEWPORT,
  deviceScaleFactor: SCALE,
  userAgent: UA,
  locale: "id-ID",
  timezoneId: "Asia/Jakarta",
});
const page = ctx.pages()[0] ?? (await ctx.newPage());
try {
  for (const name of names) await scenes[name](page);
} finally {
  await ctx.close();
}

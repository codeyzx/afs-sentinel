import real from "./data/real.json";

export const REAL = real;

const DAYS = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];

/** Same wording as afs/telegram.py format_wib: "Minggu 4 Okt 2026, 08:00 WIB". */
export const formatWib = (iso: string) => {
  const d = new Date(new Date(iso).getTime() + 7 * 3600 * 1000);
  const hh = String(d.getUTCHours()).padStart(2, "0");
  const mm = String(d.getUTCMinutes()).padStart(2, "0");
  return `${DAYS[d.getUTCDay()]} ${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}, ${hh}:${mm} WIB`;
};

export const clockWib = (iso: string) => formatWib(iso).split(", ")[1].replace(" WIB", "");

type Run = (typeof real.runs)[number];

/** Same text as afs/telegram.py format_run_summary (these runs had 0 escalations and 0 failures, see /logs). */
export const runSummary = (r: Run) =>
  `✅ Audit Run ${formatWib(r.startedAt)} (${r.trigger === "SCHEDULER" ? "Otomatis · sistem" : "Manual · analis"})\n` +
  `${r.scanned} emiten dipindai · ${r.incidentsNew} Incident baru · 0 Escalation · 0 gagal\n` +
  `Kredit API terpakai: ${r.credits}`;

export const RULES = [
  { name: "Sloan Accrual", weight: 25, core: true, plain: "Laba yang bukan uang tunai" },
  { name: "Divergensi Laba–Kas", weight: 25, core: true, plain: "Laba naik, kas operasi turun" },
  { name: "Altman Z″", weight: 20, core: true, plain: "Risiko kesulitan keuangan" },
  { name: "Beneish", weight: 15, core: false, plain: "Tekanan memoles laporan" },
  { name: "Penjualan Orang Dalam", weight: 10, core: false, plain: "Orang dalam menjual saham" },
  { name: "Laba tanpa Dividen", weight: 5, core: false, plain: "Untung, tapi tidak membagi kas" },
];

export const quarter = (iso: string) => {
  const d = new Date(iso);
  return `${d.getUTCFullYear()}-Q${Math.floor(d.getUTCMonth() / 3) + 1}`;
};

/** The 33 non-financial Emiten in the universe (production `emiten` table). */
export const EMITEN =
  "AADI,ACES,AKRA,AMRT,ANTM,ASII,BRPT,BUMI,CPIN,EMTK,EXCL,GOTO,ICBP,INCO,INDF,INTP,ISAT,ITMG,JPFA,KLBF,MAPI,MDKA,MEDC,MYOR,PGAS,PTBA,SIDO,SMGR,TLKM,TOWR,TPIA,UNTR,UNVR".split(",");

/** Emiten with an open Incident in production. */
export const FLAGGED = ["UNVR", "BUMI", "ITMG", "CPIN", "ANTM", "PGAS", "EXCL", "ACES", "ISAT", "TOWR"];

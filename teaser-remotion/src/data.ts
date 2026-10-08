// Numbers on screen come from the live app (afs-sentinel.herokuapp.com, 8 Okt 2026):
// dashboard, /logs, /backtest and Incident AFS-2026-Q2-0003.

/** The 33 non-financial Emiten in the Universe (config/universe.json). */
export const EMITEN =
  "AADI,ACES,AKRA,AMRT,ANTM,ASII,BRPT,BUMI,CPIN,EMTK,EXCL,GOTO,ICBP,INCO,INDF,INTP,ISAT,ITMG,JPFA,KLBF,MAPI,MDKA,MEDC,MYOR,PGAS,PTBA,SIDO,SMGR,TLKM,TOWR,TPIA,UNTR,UNVR".split(",");

/** Emiten with an open Incident (dashboard: "10 Perlu ditinjau", "23 Aman"). */
export const FLAGGED = ["UNVR", "BUMI", "ITMG", "CPIN", "ANTM", "PGAS", "EXCL", "ACES", "ISAT", "TOWR"];

/** /backtest, WSKT: Composite Risk Score per Report Period. */
export const WSKT_BACKTEST: { q: string; date: string; score: number; sev: "Sedang" | "Rendah" }[] = [
  { q: "2021-Q1", date: "2021-03-31", score: 30.6, sev: "Sedang" },
  { q: "2021-Q2", date: "2021-06-30", score: 30.8, sev: "Sedang" },
  { q: "2021-Q3", date: "2021-09-30", score: 30.8, sev: "Sedang" },
  { q: "2021-Q4", date: "2021-12-31", score: 30.8, sev: "Sedang" },
  { q: "2022-Q1", date: "2022-03-31", score: 30.8, sev: "Sedang" },
  { q: "2022-Q2", date: "2022-06-30", score: 19.4, sev: "Rendah" },
  { q: "2022-Q3", date: "2022-09-30", score: 19.4, sev: "Rendah" },
  { q: "2022-Q4", date: "2022-12-31", score: 42.3, sev: "Sedang" },
  { q: "2023-Q1", date: "2023-03-31", score: 30.8, sev: "Sedang" },
];
export const WSKT_SUSPENDED = "2023-05-08";

/** Forensic Rules with their weights in the Composite Risk Score. */
export const RULES = [
  { name: "Sloan Accrual", weight: 25, plain: "Laba yang bukan uang tunai" },
  { name: "Divergensi Laba–Kas", weight: 25, plain: "Laba naik, kas operasi turun" },
  { name: "Altman Z″", weight: 20, plain: "Risiko kesulitan keuangan" },
  { name: "Beneish", weight: 15, plain: "Tekanan memoles laporan" },
  { name: "Penjualan Orang Dalam", weight: 10, plain: "Orang dalam menjual saham" },
  { name: "Laba tanpa Dividen", weight: 5, plain: "Untung, tapi tidak membagi kas" },
];

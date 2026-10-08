import { loadFont as loadDisplay } from "@remotion/google-fonts/InterTight";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";
import { loadFont as loadSerif } from "@remotion/google-fonts/InstrumentSerif";

// "Sinyal": a forensic thriller at night. Near-black ground, one signal red, data colours only as data.
export const C = {
  night: "#06080A",
  deep: "#0B1014",
  panel: "#10171C",
  line: "rgba(214,228,236,0.10)",
  lineStrong: "rgba(214,228,236,0.22)",
  text: "#EEF3F5",
  dim: "#9AA8B0",
  hint: "#5D6B73",
  red: "#FF3B30",
  redDeep: "#C4231A",
  redGlow: "rgba(255,59,48,0.45)",
  // AFS Sentinel product semantics (Rendah / Sedang / Kritis, Aman / Waspada / Bahaya)
  safe: "#2FBF71",
  warn: "#F2B33D",
  danger: "#FF3B30",
  app: "#0e1920",
};

const display = loadDisplay("normal", { weights: ["400", "500", "600", "700", "800", "900"], subsets: ["latin"] });
const mono = loadMono("normal", { weights: ["400", "500", "700"], subsets: ["latin"] });
const serif = loadSerif("italic", { weights: ["400"], subsets: ["latin"] });
loadSerif("normal", { weights: ["400"], subsets: ["latin"] });

export const F = {
  display: display.fontFamily,
  sans: display.fontFamily,
  mono: mono.fontFamily,
  serif: serif.fontFamily,
};

export const FPS = 30;
export const W = 1920;
export const H = 1080;
export const sec = (s: number) => Math.round(s * FPS);

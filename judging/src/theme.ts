import { loadFont as loadSerif } from "@remotion/google-fonts/Newsreader";
import { loadFont as loadSans } from "@remotion/google-fonts/Geist";
import { loadFont as loadMono } from "@remotion/google-fonts/GeistMono";

// "Case File": a forensic dossier. Warm paper, ink, one red-flag accent, one highlighter.
export const C = {
  paper: "#F1ECE2",
  paperDeep: "#E6DFD1",
  card: "#FBF8F2",
  ink: "#16130F",
  inkSoft: "#3A342C",
  muted: "#6B6358",
  hint: "#9A9184",
  line: "rgba(22,19,15,0.14)",
  lineStrong: "rgba(22,19,15,0.32)",
  red: "#D93A2B",
  redSoft: "rgba(217,58,43,0.12)",
  marker: "#F5D547",
  night: "#0E0D0B",
  // the case-file folder of the intro and outro
  manila: "#DCC79E",
  manilaDeep: "#C4AC7F",
  // AFS Sentinel app palette, only for data marks that echo the product UI
  safe: "#2F9E5B",
  warn: "#D9A514",
  danger: "#D93A2B",
  app: "#0e1920",
};

const serif = loadSerif("normal", { weights: ["400", "500", "600", "700"], subsets: ["latin"] });
loadSerif("italic", { weights: ["400", "500", "600"], subsets: ["latin"] });
const sans = loadSans("normal", { weights: ["400", "500", "600", "700"], subsets: ["latin"] });
const mono = loadMono("normal", { weights: ["400", "500", "600"], subsets: ["latin"] });

export const F = {
  serif: serif.fontFamily,
  sans: sans.fontFamily,
  mono: mono.fontFamily,
};

export const FPS = 30;
export const W = 1920;
export const H = 1080;
export const sec = (s: number) => Math.round(s * FPS);

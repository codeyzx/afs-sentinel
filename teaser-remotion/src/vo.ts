import { staticFile } from "remotion";
import captions from "./data/captions.json";
import vo from "./data/vo.json";
import { FPS } from "./theme";

// Nine voice-over lines, back to back; each scene lasts exactly as long as its line.
export const LINES = vo.voices.map((v, i) => ({
  src: staticFile(`voice/vo-0${i + 1}.wav`),
  seconds: v.duration_s,
  words: v.words.map((w) => ({ text: w.text, start: w.start, end: w.end })),
}));

export const SCENES = (() => {
  let t = 0;
  return LINES.map((l, i) => {
    const from = Math.round(t * FPS);
    t += l.seconds;
    return { index: i, from, dur: Math.round(t * FPS) - from, startSec: t - l.seconds };
  });
})();

// A short silent tail so the end card can breathe; total stays under 60 s.
export const TAIL = 18;
export const TOTAL = SCENES[SCENES.length - 1].from + SCENES[SCENES.length - 1].dur + TAIL;

/** Scene-local frame where word `text` (nth occurrence) starts in line `line` (1-based). */
export const w = (line: number, text: string, nth = 0) => {
  const hits = LINES[line - 1].words.filter((x) => x.text.toLowerCase() === text.toLowerCase());
  const hit = hits[nth];
  if (!hit) throw new Error(`word "${text}" #${nth} not in line ${line}`);
  return Math.round(hit.start * FPS);
};

export type CaptionGroup = { start: number; end: number; text: string; words: { text: string; start: number; end: number }[] };
export const CAPTIONS = (captions.groups as CaptionGroup[]).map((g) => g);

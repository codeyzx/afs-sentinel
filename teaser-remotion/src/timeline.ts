import { staticFile } from "remotion";
import vo from "./gen/vo.json";
import { FPS } from "./theme";

// Everything is placed in seconds on one master clock, then converted to frames.
// Scene cuts from the reveal on are snapped to the music's beat grid (160 BPM, see MUSIC below).

type Word = { text: string; start: number; end: number };
type Line = { id: string; text: string; file: string; duration: number; speechEnd: number; words: Word[] };
const RAW = vo.lines as Line[];
const byId = (id: string) => {
  const l = RAW.find((x) => x.id === id);
  if (!l) throw new Error(`vo line ${id} missing`);
  return l;
};

export const BEAT = 0.37504; // seconds per beat of "Impact Prelude"

// Section B of the score enters on the spoken "AFS" of the reveal; cuts after it sit on its beats.
const INTRO_AT = 17.2;
const TB = INTRO_AT + byId("intro").words[1].start;
const snap = (s: number) => TB + Math.round((s - TB) / BEAT) * BEAT;

const CUT = {
  hook: 0,
  rewind: 6.9,
  who: 13.5,
  reveal: 16.8,
  auto: snap(21.4),
  rules: snap(28.3),
  alert: snap(33.6),
  climax: snap(41.0),
  outro: 51.3,
  end: 59.5,
};

// VO placement in master seconds.
const PLACE: Record<string, number> = {
  date: 0.7,
  halt: 3.75,
  signs: 7.35,
  who: 13.6,
  intro: INTRO_AT,
  auto: CUT.auto + 0.15,
  rules: CUT.rules + 0.12,
  alert: CUT.alert + 0.15,
  proof: CUT.alert + 3.45,
  test: CUT.climax + 0.2,
  flag: CUT.climax + 2.3,
  months: CUT.climax + 5.2,
  name: CUT.outro + 0.5,
  tag: CUT.outro + 2.7,
};

const f = (s: number) => Math.round(s * FPS);

export const LINES = RAW.map((l) => ({
  ...l,
  src: staticFile(l.file),
  at: f(PLACE[l.id]),
  /** words in master frames */
  wf: l.words.map((w) => ({ text: w.text, start: f(PLACE[l.id] + w.start), end: f(PLACE[l.id] + w.end) })),
}));

/** Master frame where `word` (nth occurrence, case-insensitive) starts in line `id`. */
export const w = (id: string, word: string, nth = 0) => {
  const l = LINES.find((x) => x.id === id)!;
  const hits = l.wf.filter((x) => x.text.toLowerCase().replace(/[^\p{L}\p{N}-]/gu, "") === word.toLowerCase());
  if (!hits[nth]) throw new Error(`word "${word}" #${nth} not in ${id}`);
  return hits[nth].start;
};
/** Master frame where line `id` starts / ends speaking. */
export const lineStart = (id: string) => LINES.find((x) => x.id === id)!.at;
export const lineEnd = (id: string) => {
  const l = LINES.find((x) => x.id === id)!;
  return l.at + f(l.speechEnd);
};

export type SceneName = Exclude<keyof typeof CUT, "end">;
const ORDER: SceneName[] = ["hook", "rewind", "who", "reveal", "auto", "rules", "alert", "climax", "outro"];
export const SCENES = ORDER.map((name, i) => {
  const from = f(CUT[name]);
  const to = f(i + 1 < ORDER.length ? CUT[ORDER[i + 1]] : CUT.end);
  return { name, from, dur: to - from };
});
export const scene = (name: SceneName) => SCENES.find((s) => s.name === name)!;
export const TOTAL = f(CUT.end);

/** Convert a master frame to a frame local to scene `name`. */
export const local = (name: SceneName, master: number) => master - scene(name).from;

// Score: "Impact Prelude" (Kevin MacLeod, CC BY 4.0) cut into three sections.
//   A  hook → problem, from the top of the track; stops dead for the reveal.
//   B  enters on "AFS" at the track's 48.07 s phrase and runs under the product montage.
//   C  stops before "dua puluh lima"; re-enters on "bulan" at the 96.08 s full section.
const HIT = w("months", "bulan");
export const MUSIC = {
  sections: [
    { from: f(0.25), to: f(CUT.reveal) + 2, trackAt: 0, level: 0.42, fadeOut: 4 },
    { from: f(TB), to: f(CUT.climax + 4.5), trackAt: 48.07, level: 0.4, fadeOut: 14 },
    { from: HIT, to: TOTAL, trackAt: 96.08, level: 0.48, fadeOut: 75 },
  ],
  hit: HIT,
  revealHit: f(TB),
};

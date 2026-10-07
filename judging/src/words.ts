// Word schedule: the single timing source for the prompter videos (what the team reads) and the
// judging video (captions + visual beats). Times are seconds from the start of the line.

export type Word = { text: string; start: number; end: number };

const PAUSE: [RegExp, number][] = [
  [/…$/, 0.55],
  [/[.?!]$/, 0.42],
  [/[:;]$/, 0.32],
  [/[,—]$/, 0.22],
];

/** Rough Indonesian syllable count: vowel groups (digits read as words count extra). */
export const syllables = (word: string) => {
  const w = word.toLowerCase().replace(/[^a-z0-9]/g, "");
  if (/^\d+$/.test(w)) return Math.max(2, w.length * 2);
  const groups = w.match(/[aiueo]+/g)?.length ?? 1;
  return Math.max(1, groups);
};

const pauseAfter = (word: string) => PAUSE.find(([re]) => re.test(word))?.[1] ?? 0;

/** Spread a line's words over `seconds`, weighted by syllables, with natural pauses at punctuation. */
export function scheduleWords(text: string, seconds: number): Word[] {
  const tokens = text.split(/\s+/).filter(Boolean);
  const isLast = (i: number) => i === tokens.length - 1;
  const pauses = tokens.map((t, i) => (isLast(i) ? 0 : pauseAfter(t)));
  const totalPause = pauses.reduce((a, b) => a + b, 0);
  const weights = tokens.map((t) => syllables(t) + 0.35); // small per-word onset cost
  const totalWeight = weights.reduce((a, b) => a + b, 0);
  const speak = Math.max(0.5, seconds - totalPause);
  let t = 0;
  return tokens.map((text, i) => {
    const dur = (speak * weights[i]) / totalWeight;
    const w = { text, start: t, end: t + dur };
    t += dur + pauses[i];
    return w;
  });
}

/** Syllables per second while speaking: ~4.5–5.5 is comfortable Indonesian, >6 is rushed. */
export const pace = (text: string, seconds: number) => {
  const tokens = text.split(/\s+/).filter(Boolean);
  const syl = tokens.reduce((a, t) => a + syllables(t), 0);
  const pause = tokens.slice(0, -1).reduce((a, t) => a + pauseAfter(t), 0);
  return syl / Math.max(0.5, seconds - pause);
};

const norm = (s: string) => s.toLowerCase().replace(/[^\p{L}\p{N}]/gu, "");

/** Index of the nth (0-based) word that starts with `needle` (punctuation and case ignored). */
export const findWord = (words: Word[], needle: string, nth = 0) => {
  const n = norm(needle);
  let seen = 0;
  for (let i = 0; i < words.length; i++) {
    if (norm(words[i].text).startsWith(n)) {
      if (seen === nth) return i;
      seen++;
    }
  }
  throw new Error(`word "${needle}" (#${nth}) not in line: ${words.map((w) => w.text).join(" ")}`);
};

/** Group a line's words into phrases: split at punctuation, then even out long runs (≤ 8 words). */
export const phraseGroups = (words: Word[]): Word[][] => {
  const segments: Word[][] = [];
  let cur: Word[] = [];
  for (const w of words) {
    cur.push(w);
    if (/[.,:;?!…—]$/.test(w.text)) {
      segments.push(cur);
      cur = [];
    }
  }
  if (cur.length) segments.push(cur);
  // a lone label like "Waskita:" belongs with what follows it
  for (let i = segments.length - 2; i >= 0; i--) {
    if (segments[i].length === 1 && segments[i][0].text.endsWith(":")) segments.splice(i, 2, [...segments[i], ...segments[i + 1]]);
  }
  const out: Word[][] = [];
  for (const seg of segments) {
    const parts = Math.ceil(seg.length / 8);
    const size = Math.ceil(seg.length / parts);
    for (let i = 0; i < seg.length; i += size) out.push(seg.slice(i, i + size));
  }
  // fold tiny fragments ("Sritex:", "AI") into their neighbour
  return out.reduce<Word[][]>((acc, g) => {
    const prev = acc[acc.length - 1];
    if (prev && (g.length <= 1 || prev.length <= 1) && prev.length + g.length <= 9) prev.push(...g);
    else acc.push([...g]);
    return acc;
  }, []);
};

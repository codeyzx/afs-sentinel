import { parseMedia } from "@remotion/media-parser";
import { staticFile } from "remotion";
import sync from "./generated/sync.json";
import { RECORDINGS, TRIM_START, type ClipId } from "./media";
import { SCENES, type Line, type SceneDef } from "./script";
import { FPS } from "./theme";
import { findWord, scheduleWords, type Word } from "./words";

export type ClipDurations = Partial<Record<ClipId, number>>;

export type LineTiming = Line & { from: number; dur: number; words: Word[] };
export type SceneTiming = { def: SceneDef; from: number; dur: number; lines: LineTiming[] };
export type Timing = { scenes: SceneTiming[]; total: number; durations: ClipDurations };

const LIMIT_SECONDS = 180;
export const LIMIT_FRAMES = LIMIT_SECONDS * FPS;

type SyncEntry = { file: string; start: number; end: number; voice?: string; w?: number; hgt?: number; face?: { x: number; y: number; h: number } };
const SYNC = sync as Partial<Record<ClipId, SyncEntry>>;

/** Frame size and median face position of a recording (from scripts/faces.py), if known. */
export const framingOf = (id: ClipId) => {
  const e = SYNC[id];
  return e?.w && e.hgt ? { w: e.w, h: e.hgt, face: e.face } : undefined;
};

/** A clip's file: the explicit name in media.ts, else whatever `npm run sync` found for it. */
export const clipSrc = (id: ClipId): string | null => {
  const file = (RECORDINGS[id] as string | null) ?? SYNC[id]?.file;
  return file ? staticFile(`recordings/${file}`) : null;
};

/** The cleaned, level voice track for a clip (`npm run sync`), already cut to the spoken span. */
export const voiceSrc = (id: ClipId): string | null => {
  const v = SYNC[id]?.voice;
  return v && (RECORDINGS[id] as string | null) === null ? staticFile(`recordings/${v}`) : null;
};

/** Where the take starts: manual TRIM_START wins, else the speech onset found by `npm run sync`. */
export const trimOf = (id: ClipId) => TRIM_START[id] ?? SYNC[id]?.start ?? 0;

/** Real duration when the clip exists, else the script's target. */
const lineSeconds = (line: Line, durations: ClipDurations) => {
  const real = line.clips.map((c) => durations[c]).filter((d): d is number => d !== undefined);
  return real.length ? Math.max(...real) : line.target;
};

export function buildTiming(durations: ClipDurations): Timing {
  let cursor = 0;
  const scenes = SCENES.map((def) => {
    let t = def.lead;
    const lines = def.lines.map((line) => {
      t += line.gap ?? 0;
      const seconds = lineSeconds(line, durations);
      const dur = Math.round(seconds * FPS);
      // The prompter paces the read at `target`; a real take stretches the same schedule.
      const k = seconds / line.target;
      const words = scheduleWords(line.text, line.target).map((w) => ({ ...w, start: w.start * k, end: w.end * k }));
      const lt: LineTiming = { ...line, from: Math.round(t * FPS), dur, words };
      t += dur / FPS;
      return lt;
    });
    const scene: SceneTiming = { def, from: cursor, dur: Math.round((t + def.tail) * FPS), lines };
    cursor += scene.dur;
    return scene;
  });
  return { scenes, total: cursor, durations };
}

async function probe(src: string): Promise<number | undefined> {
  try {
    const url = new URL(src, window.location.href).toString();
    const { slowDurationInSeconds } = await parseMedia({
      src: url,
      fields: { slowDurationInSeconds: true },
      acknowledgeRemotionLicense: true,
    });
    return slowDurationInSeconds;
  } catch (err) {
    console.warn(`Tidak bisa membaca durasi ${src}`, err);
    return undefined;
  }
}

export async function probeRecordings(): Promise<ClipDurations> {
  const entries = await Promise.all(
    (Object.keys(RECORDINGS) as ClipId[]).map(async (id) => {
      const src = clipSrc(id);
      if (!src) return [id, undefined] as const;
      const synced = SYNC[id];
      if (synced && TRIM_START[id] === undefined) return [id, synced.end - synced.start] as const;
      const d = await probe(src);
      return [id, d === undefined ? undefined : Math.max(0.5, d - trimOf(id))] as const;
    }),
  );
  return Object.fromEntries(entries.filter(([, d]) => d !== undefined));
}

/** Scene frame where a word of line `i` starts (needle = word prefix, nth occurrence). */
export const atWord = (scene: SceneTiming, i: number, needle: string, nth = 0, offset = 0) => {
  const l = scene.lines[i];
  return Math.round(l.from + l.words[findWord(l.words, needle, nth)].start * FPS) + offset;
};

/** Scene frame where line `i` ends. */
export const lineEnd = (scene: SceneTiming, i: number) => scene.lines[i].from + scene.lines[i].dur;

export const sceneById = (timing: Timing, id: string) => {
  const s = timing.scenes.find((x) => x.def.id === id);
  if (!s) throw new Error(`scene ${id} missing`);
  return s;
};

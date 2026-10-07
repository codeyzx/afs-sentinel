import React from "react";
import { AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame } from "remotion";
import { SCENES } from "../script";
import { clipSrc, trimOf, type LineTiming, type SceneTiming, type Timing } from "../timeline";
import { C, F, FPS } from "../theme";
import { phraseGroups } from "../words";
import { Kicker } from "./primitives";

/** Bottom-band captions, timed by the word schedule (scene-local frame). */
export const Captions: React.FC<{ lines: LineTiming[]; dark?: boolean; bottom?: number }> = ({ lines, dark, bottom = 46 }) => {
  const frame = useCurrentFrame();
  const line = lines.find((l) => frame >= l.from - 3 && frame < l.from + l.dur);
  if (!line) return null;
  const t = (frame - line.from) / FPS;
  const groups = phraseGroups(line.words);
  let idx = 0;
  for (let i = 0; i < groups.length; i++) if (t >= groups[i][0].start - 0.1) idx = i;
  const since = t - (groups[idx][0].start - 0.1);
  const appear = interpolate(since, [0, 0.16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom, display: "flex", justifyContent: "center", pointerEvents: "none" }}>
      <div
        style={{
          maxWidth: 1300,
          textAlign: "center",
          fontFamily: F.sans,
          fontWeight: 500,
          fontSize: 34,
          lineHeight: 1.3,
          color: dark ? "#FBF8F2" : C.ink,
          background: dark ? "rgba(14,13,11,0.72)" : "rgba(251,248,242,0.92)",
          padding: "10px 24px",
          borderRadius: 10,
          boxShadow: dark ? "none" : "0 6px 20px rgba(40,28,10,0.12)",
          opacity: appear,
          transform: `translateY(${(1 - appear) * 8}px)`,
        }}
      >
        {groups[idx].map((w) => w.text).join(" ")}
      </div>
    </div>
  );
};

/** Top bar: dossier page number, scene title, proof tag, and chapter ticks. */
export const SceneHeader: React.FC<{ scene: SceneTiming; index: number; dark?: boolean }> = ({ scene, index, dark }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [4, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const ink = dark ? "#FBF8F2" : C.ink;
  const muted = dark ? "rgba(251,248,242,0.6)" : C.muted;
  return (
    <div style={{ position: "absolute", left: 96, right: 96, top: 38, display: "flex", alignItems: "center", gap: 18, opacity: p }}>
      <Kicker size={16} color={muted}>
        Berkas {String(index + 1).padStart(2, "0")}/{SCENES.length}
      </Kicker>
      <div style={{ width: 28, height: 1, background: muted }} />
      <Kicker size={16} color={ink}>
        {scene.def.title}
      </Kicker>
      {scene.def.proof && (
        <Kicker size={14} color="#FBF8F2" style={{ background: C.red, padding: "5px 10px", borderRadius: 4 }}>
          {scene.def.proof}
        </Kicker>
      )}
      <div style={{ flex: 1 }} />
      <div style={{ display: "flex", gap: 6 }}>
        {SCENES.map((s, i) => (
          <div key={s.id} style={{ width: i === index ? 34 : 14, height: 4, borderRadius: 2, background: i <= index ? (i === index ? C.red : ink) : muted, opacity: i <= index ? 1 : 0.35 }} />
        ))}
      </div>
    </div>
  );
};

/** All voices: each line's clips play their own audio here, so visuals can reuse a clip freely. */
export const VoiceTrack: React.FC<{ timing: Timing }> = ({ timing }) => (
  <>
    {timing.scenes.flatMap((s) =>
      s.lines.flatMap((l) =>
        l.clips.map((clip) => {
          const src = clipSrc(clip);
          if (!src) return null;
          return (
            <Sequence key={clip} from={s.from + l.from} durationInFrames={l.dur} layout="none">
              {/* group line: three mics, keep it from getting loud */}
              <Audio src={src} startFrom={Math.round(trimOf(clip) * FPS)} volume={l.clips.length > 1 ? 0.6 : 1} name={clip} />
            </Sequence>
          );
        }),
      ),
    )}
  </>
);

/** Music bed, ducked under every spoken line. */
export const MusicBed: React.FC<{ timing: Timing }> = ({ timing }) => {
  const spans = timing.scenes.flatMap((s) => s.lines.map((l) => [s.from + l.from, s.from + l.from + l.dur] as const));
  const volumeAt = (f: number) => {
    const fadeIn = interpolate(f, [0, 45], [0, 1], { extrapolateRight: "clamp" });
    const fadeOut = interpolate(f, [timing.total - 75, timing.total], [1, 0], { extrapolateLeft: "clamp" });
    // distance to nearest speech span, in frames
    let duck = 1;
    for (const [a, b] of spans) {
      if (f >= a - 8 && f <= b + 10) {
        const edge = Math.min(f - (a - 8), b + 10 - f);
        duck = Math.min(duck, interpolate(edge, [0, 8], [1, 0], { extrapolateRight: "clamp" }));
      }
    }
    const base = 0.32;
    const under = 0.11;
    return (under + (base - under) * duck) * fadeIn * fadeOut;
  };
  return <Audio src={staticFile("audio/bgm/bed.mp3")} volume={volumeAt} loop />;
};

export type Sfx = { at: number; name: string; volume?: number; dur?: number };

export const SfxTrack: React.FC<{ cues: Sfx[] }> = ({ cues }) => (
  <>
    {cues.map((c, i) => (
      <Sequence key={i} from={Math.max(0, c.at)} durationInFrames={c.dur ?? 150} layout="none">
        <Audio src={staticFile(`audio/sfx/${c.name}.mp3`)} volume={c.volume ?? 0.5} />
      </Sequence>
    ))}
  </>
);

/** Ink panel that wipes across a cut. Rendered over everything, centered on `at`. */
export const InkWipe: React.FC<{ at: number; color?: string; dir?: 1 | -1 }> = ({ at, color = C.ink, dir = 1 }) => {
  const frame = useCurrentFrame();
  const len = 16;
  if (frame < at - len || frame > at + len) return null;
  const p = (frame - (at - len)) / (len * 2); // 0..1
  const e = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
  const lead = e(Math.min(1, p * 2)); // covers in first half
  const trail = e(Math.max(0, p * 2 - 1)); // uncovers in second half
  const left = dir === 1 ? trail * 100 : (1 - lead) * 100;
  const right = dir === 1 ? (1 - lead) * 100 : trail * 100;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ position: "absolute", top: 0, bottom: 0, left: `${left}%`, right: `${right}%`, background: color }} />
      <div style={{ position: "absolute", top: 0, bottom: 0, left: `${left}%`, right: `${right}%`, borderLeft: `6px solid ${C.red}`, borderRight: `6px solid ${C.red}`, opacity: 0.9 }} />
    </AbsoluteFill>
  );
};

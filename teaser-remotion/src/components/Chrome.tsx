import React from "react";
import { AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame } from "remotion";
import { C, F, FPS } from "../theme";
import { CAPTIONS, LINES, SCENES, TOTAL } from "../vo";

/** Word-timed captions in the bottom band; the spoken word gets the highlighter. */
export const Captions: React.FC<{ dark?: (frame: number) => boolean }> = ({ dark }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const g = CAPTIONS.find((x) => t >= x.start - 0.05 && t < x.end + 0.25);
  if (!g) return null;
  const appear = interpolate(t, [g.start - 0.05, g.start + 0.1], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const isDark = dark?.(frame) ?? false;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 52, display: "flex", justifyContent: "center", pointerEvents: "none" }}>
      <div
        style={{
          fontFamily: F.sans,
          fontWeight: 600,
          fontSize: 44,
          lineHeight: 1.2,
          color: isDark ? "#FBF8F2" : C.ink,
          background: isDark ? "rgba(14,13,11,0.78)" : "rgba(251,248,242,0.94)",
          padding: "10px 26px",
          borderRadius: 10,
          boxShadow: isDark ? "none" : "0 8px 24px rgba(40,28,10,0.14)",
          opacity: appear,
          transform: `translateY(${(1 - appear) * 10}px) scale(${0.96 + appear * 0.04})`,
          display: "flex",
          gap: "0.28em",
        }}
      >
        {g.words.map((wd, i) => {
          const on = t >= wd.start && t < (g.words[i + 1]?.start ?? g.end + 0.25);
          const said = t >= wd.start;
          return (
            <span
              key={i}
              style={{
                position: "relative",
                opacity: said ? 1 : 0.38,
              }}
            >
              {on && (
                <span
                  style={{
                    position: "absolute",
                    left: "-0.12em",
                    right: "-0.12em",
                    top: "0.1em",
                    bottom: "0.02em",
                    background: C.marker,
                    borderRadius: 6,
                    transform: "skewX(-8deg)",
                    zIndex: 0,
                  }}
                />
              )}
              <span style={{ position: "relative", color: on ? C.ink : undefined }}>{wd.text}</span>
            </span>
          );
        })}
      </div>
    </div>
  );
};

export const VoiceTrack: React.FC = () => (
  <>
    {LINES.map((l, i) => (
      <Sequence key={i} from={SCENES[i].from} durationInFrames={Math.ceil(l.seconds * FPS) + 2} layout="none">
        <Audio src={l.src} volume={1} name={`vo-0${i + 1}`} />
      </Sequence>
    ))}
  </>
);

/**
 * Music bed. Starts late so its drop lands on "dua puluh lima" in the climax; ducked under every word.
 * `drops` are frames where the duck lifts fully (e.g. the 25 hit, the end card).
 */
export const MusicBed: React.FC<{ from: number; lift: [number, number][] }> = ({ from, lift }) => {
  const words = LINES.flatMap((l, i) => l.words.map((wd) => [SCENES[i].from + wd.start * FPS, SCENES[i].from + wd.end * FPS] as const));
  const volumeAt = (local: number) => {
    const f = local + from;
    const fadeIn = interpolate(local, [0, 40], [0, 1], { extrapolateRight: "clamp" });
    const fadeOut = interpolate(f, [TOTAL - 45, TOTAL], [1, 0], { extrapolateLeft: "clamp" });
    let duck = 1;
    for (const [a, b] of words) {
      if (f >= a - 6 && f <= b + 8) {
        const edge = Math.min(f - (a - 6), b + 8 - f);
        duck = Math.min(duck, interpolate(edge, [0, 6], [1, 0], { extrapolateRight: "clamp" }));
      }
    }
    for (const [a, b] of lift) if (f >= a && f <= b) duck = Math.max(duck, 0.75);
    const base = 0.5;
    const under = 0.2;
    return (under + (base - under) * duck) * fadeIn * fadeOut;
  };
  return (
    <Sequence from={from} layout="none">
      <Audio src={staticFile("audio/bgm/bed.mp3")} volume={volumeAt} name="music" />
    </Sequence>
  );
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

/** Ink panel wiping across a cut, centered on `at`. */
export const InkWipe: React.FC<{ at: number; color?: string; dir?: 1 | -1; len?: number }> = ({ at, color = C.ink, dir = 1, len = 10 }) => {
  const frame = useCurrentFrame();
  if (frame < at - len || frame > at + len) return null;
  const p = (frame - (at - len)) / (len * 2);
  const e = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
  const lead = e(Math.min(1, p * 2));
  const trail = e(Math.max(0, p * 2 - 1));
  const left = dir === 1 ? trail * 100 : (1 - lead) * 100;
  const right = dir === 1 ? (1 - lead) * 100 : trail * 100;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ position: "absolute", top: 0, bottom: 0, left: `${left}%`, right: `${right}%`, background: color }} />
      <div style={{ position: "absolute", top: 0, bottom: 0, left: `${left}%`, right: `${right}%`, borderLeft: `8px solid ${C.red}`, borderRight: `8px solid ${C.red}` }} />
    </AbsoluteFill>
  );
};

/** Flash frame on a cut. */
export const Flash: React.FC<{ at: number; color?: string; len?: number }> = ({ at, color = "#FBF8F2", len = 9 }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [at - 2, at, at + len], [0, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  if (o <= 0) return null;
  return <AbsoluteFill style={{ background: color, opacity: o, pointerEvents: "none" }} />;
};

/** Short decaying shake for slams, as a transform string. */
export const shake = (frame: number, at: number, amp = 14, len = 10) => {
  const k = frame - at;
  if (k < 0 || k > len) return "none";
  const d = amp * (1 - k / len);
  return `translate(${Math.sin(k * 2.7) * d}px, ${Math.cos(k * 3.1) * d * 0.6}px)`;
};

/** Top-right chapter ticks. */
export const Ticks: React.FC<{ index: number; dark?: boolean }> = ({ index, dark }) => {
  const ink = dark ? "#FBF8F2" : C.ink;
  return (
    <div style={{ position: "absolute", right: 96, top: 44, display: "flex", gap: 6 }}>
      {SCENES.map((s) => (
        <div key={s.index} style={{ width: s.index === index ? 34 : 14, height: 4, borderRadius: 2, background: s.index === index ? (dark ? C.marker : C.red) : ink, opacity: s.index <= index ? 1 : 0.3 }} />
      ))}
    </div>
  );
};

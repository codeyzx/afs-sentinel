import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { C, F } from "../theme";
import { LINES } from "../timeline";
import { ease, easeInOut, prog } from "./primitives";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** Night ground: deep gradient and a faint forensic grid that drifts with the camera. */
export const Backdrop: React.FC<{ grid?: number; drift?: number; tint?: string }> = ({ grid = 0.5, drift = 0, tint = "rgba(40,70,90,0.35)" }) => (
  <AbsoluteFill style={{ background: C.night }}>
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 80% 70% at 50% 40%, ${tint} 0%, transparent 70%)` }} />
    {grid > 0 && (
      <AbsoluteFill
        style={{
          opacity: grid,
          backgroundImage: `linear-gradient(${C.line} 1px, transparent 1px), linear-gradient(90deg, ${C.line} 1px, transparent 1px)`,
          backgroundSize: "96px 96px",
          backgroundPosition: `${-drift}px ${-drift * 0.3}px`,
          maskImage: "radial-gradient(ellipse 70% 60% at 50% 45%, black 20%, transparent 80%)",
        }}
      />
    )}
  </AbsoluteFill>
);

/** Film grain + vignette over everything. */
export const FilmLook: React.FC = () => {
  const frame = useCurrentFrame();
  const seed = frame % 8;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 75% 70% at 50% 48%, transparent 55%, rgba(0,0,0,0.55) 100%)" }} />
      <AbsoluteFill style={{ mixBlendMode: "overlay", opacity: 0.32 }}>
        <svg width="100%" height="100%">
          <filter id={`g${seed}`}>
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={seed * 7 + 1} stitchTiles="stitch" />
            <feColorMatrix values="0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 0.9 0" />
          </filter>
          <rect width="100%" height="100%" filter={`url(#g${seed})`} />
        </svg>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/** Cinema bars. `open` 0 = 2.39:1 letterbox, 1 = full frame. */
export const Letterbox: React.FC<{ open: number }> = ({ open }) => {
  const bar = (1080 - 1920 / 2.39) / 2; // ≈138 px
  const h = bar * (1 - open);
  if (h <= 0.5) return null;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: h, background: "#000" }} />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: h, background: "#000" }} />
    </AbsoluteFill>
  );
};

/** Full-frame flash centred on `at`. */
export const Flash: React.FC<{ at: number; color?: string; len?: number; peak?: number }> = ({ at, color = "#FFFFFF", len = 8, peak = 0.9 }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [at - 1, at, at + len], [0, peak, 0], clamp);
  if (o <= 0) return null;
  return <AbsoluteFill style={{ background: color, opacity: o, mixBlendMode: "screen", pointerEvents: "none" }} />;
};

/** Anamorphic light streak across the frame on a hit. */
export const Streak: React.FC<{ at: number; y?: number; color?: string; len?: number }> = ({ at, y = 540, color = "255,80,64", len = 18 }) => {
  const frame = useCurrentFrame();
  const k = frame - at;
  if (k < -2 || k > len) return null;
  const p = interpolate(k, [-2, 2, len], [0, 1, 0], clamp);
  const wdt = interpolate(k, [-2, len], [0.4, 1.4], clamp);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "screen" }}>
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: y,
          width: 1920 * wdt * 1.4,
          height: 220,
          transform: "translate(-50%,-50%)",
          background: `radial-gradient(ellipse 50% 50% at 50% 50%, rgba(${color},${0.55 * p}) 0%, rgba(${color},${0.12 * p}) 40%, transparent 70%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: y,
          width: 1920 * wdt,
          height: 3,
          transform: "translate(-50%,-50%)",
          background: `linear-gradient(90deg, transparent, rgba(255,235,230,${p}), transparent)`,
          boxShadow: `0 0 24px 6px rgba(${color},${0.8 * p})`,
        }}
      />
    </AbsoluteFill>
  );
};

/** Horizontal slice glitch for a few frames around `at`. Wrap content with it. */
export const Glitch: React.FC<{ at: number; len?: number; children: React.ReactNode }> = ({ at, len = 6, children }) => {
  const frame = useCurrentFrame();
  const k = frame - at;
  if (k < 0 || k > len) return <>{children}</>;
  const slices = 7;
  return (
    <AbsoluteFill>
      {Array.from({ length: slices }, (_, i) => {
        const top = (i / slices) * 100;
        const off = Math.sin((frame + 1) * (i + 3) * 12.9898) * 60 * (1 - k / len);
        return (
          <AbsoluteFill key={i} style={{ clipPath: `inset(${top}% 0 ${100 - top - 100 / slices}% 0)`, transform: `translateX(${off}px)` }}>
            {children}
          </AbsoluteFill>
        );
      })}
      <AbsoluteFill style={{ background: `rgba(255,59,48,${0.18 * (1 - k / len)})`, mixBlendMode: "screen" }} />
    </AbsoluteFill>
  );
};

/** A dip to black around a cut (for stop-downs). */
export const Blackout: React.FC<{ from: number; to: number; fade?: number }> = ({ from, to, fade = 3 }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [from - fade, from, to, to + fade], [0, 1, 1, 0], clamp);
  if (o <= 0) return null;
  return <AbsoluteFill style={{ background: "#000", opacity: o }} />;
};

// ---------- captions ----------

type Group = { start: number; end: number; words: { text: string; start: number; end: number }[] };

/** Caption groups: a line split at its punctuation, at most 7 words per group. */
const GROUPS: Group[] = LINES.flatMap((l) => {
  const tokens = l.text.split(/\s+/);
  const out: Group[] = [];
  let cur: Group["words"] = [];
  l.wf.forEach((wd, i) => {
    const tok = tokens.length === l.wf.length ? tokens[i] : wd.text;
    cur.push({ text: tok, start: wd.start, end: wd.end });
    if (/[.,?!:]$/.test(tok) || cur.length >= 7 || i === l.wf.length - 1) {
      out.push({ start: cur[0].start, end: cur[cur.length - 1].end, words: cur });
      cur = [];
    }
  });
  // hold each group until the next one starts (or a short tail)
  return out.map((g, i) => ({ ...g, end: i + 1 < out.length ? out[i + 1].start - 1 : g.end + 12 }));
});

export const Captions: React.FC<{ hidden?: (frame: number) => boolean; bottom?: (frame: number) => number }> = ({ hidden, bottom }) => {
  const frame = useCurrentFrame();
  if (hidden?.(frame)) return null;
  const g = GROUPS.find((x) => frame >= x.start - 2 && frame <= x.end);
  if (!g) return null;
  const appear = prog(frame, g.start - 2, 6);
  const leave = 1 - prog(frame, g.end - 4, 4, easeInOut);
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: bottom?.(frame) ?? 58,
        display: "flex",
        justifyContent: "center",
        pointerEvents: "none",
        opacity: appear * leave,
        transform: `translateY(${(1 - appear) * 8}px)`,
      }}
    >
      <div
        style={{
          fontFamily: F.display,
          fontWeight: 600,
          fontSize: 42,
          letterSpacing: "-0.01em",
          color: C.text,
          textShadow: "0 2px 18px rgba(0,0,0,0.9), 0 0 2px rgba(0,0,0,0.9)",
          display: "flex",
          gap: "0.26em",
        }}
      >
        {g.words.map((wd, i) => {
          const said = frame >= wd.start;
          const on = said && frame < (g.words[i + 1]?.start ?? g.end);
          return (
            <span key={i} style={{ opacity: said ? 1 : 0.4, position: "relative" }}>
              {wd.text}
              <span
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  bottom: -6,
                  height: 4,
                  background: C.red,
                  borderRadius: 2,
                  transform: `scaleX(${on ? ease(Math.min(1, (frame - wd.start) / 4)) : 0})`,
                  transformOrigin: "left",
                }}
              />
            </span>
          );
        })}
      </div>
    </div>
  );
};

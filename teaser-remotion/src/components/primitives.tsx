import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, F } from "../theme";

export const ease = Easing.bezier(0.22, 1, 0.36, 1);
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);
export const easeIn = Easing.bezier(0.55, 0, 0.9, 0.4);

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** 0→1 over [start, start+dur] frames. */
export const prog = (frame: number, start: number, dur: number, easing = ease) => interpolate(frame, [start, start + dur], [0, 1], { ...clamp, easing });

export const useProgress = (start: number, dur: number, easing = ease) => prog(useCurrentFrame(), start, dur, easing);

export const useSpring = (start: number, config: Partial<{ damping: number; stiffness: number; mass: number }> = { damping: 200 }, durationInFrames?: number) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - start, fps, config, durationInFrames });
};

/** Mono uppercase label. */
export const Kicker: React.FC<{ children: React.ReactNode; color?: string; size?: number; style?: React.CSSProperties }> = ({ children, color = C.dim, size = 20, style }) => (
  <div style={{ fontFamily: F.mono, fontSize: size, letterSpacing: "0.22em", textTransform: "uppercase", color, fontWeight: 500, ...style }}>{children}</div>
);

/** Words rise out of a mask one by one; `starts` gives each word its own frame (e.g. the spoken cue). */
export const RiseWords: React.FC<{
  text: string;
  start: number;
  starts?: number[];
  stagger?: number;
  style?: React.CSSProperties;
  wordStyle?: (word: string, i: number) => React.CSSProperties | undefined;
}> = ({ text, start, starts, stagger = 3, style, wordStyle }) => {
  const frame = useCurrentFrame();
  const words = text.split(" ");
  return (
    <div style={style}>
      {words.map((w, i) => {
        const s = starts?.[i] ?? start + i * stagger;
        const p = prog(frame, s, 14);
        return (
          <span key={i} style={{ display: "inline-block", overflow: "hidden", verticalAlign: "bottom", padding: "0.04em 0.02em 0.22em", marginBottom: "-0.12em" }}>
            <span style={{ display: "inline-block", transform: `translateY(${(1 - p) * 110}%)`, opacity: p, ...wordStyle?.(w, i) }}>
              {w}
              {i < words.length - 1 ? " " : ""}
            </span>
          </span>
        );
      })}
    </div>
  );
};

/** Number counting from `from` to `to`, Indonesian decimal comma. */
export const countValue = (frame: number, from: number, to: number, start: number, dur: number, decimals = 0, easing = ease) =>
  (from + (to - from) * prog(frame, start, dur, easing)).toFixed(decimals).replace(".", ",");

export const FadeIn: React.FC<{ start: number; dur?: number; y?: number; x?: number; blur?: number; children: React.ReactNode; style?: React.CSSProperties }> = ({
  start,
  dur = 16,
  y = 24,
  x = 0,
  blur = 0,
  children,
  style,
}) => {
  const p = useProgress(start, dur);
  return (
    <div style={{ opacity: p, transform: `translate(${(1 - p) * x}px, ${(1 - p) * y}px)`, filter: blur ? `blur(${(1 - p) * blur}px)` : undefined, ...style }}>
      {children}
    </div>
  );
};

/** Deterministic pseudo-random in [0,1) from an integer seed. */
export const rand = (seed: number) => {
  let t = (seed + 0x6d2b79f5) | 0;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

/** Short decaying shake as a translate string, starting at frame `at`. */
export const shake = (frame: number, at: number, amp = 14, len = 10) => {
  const k = frame - at;
  if (k < 0 || k > len) return "translate(0px,0px)";
  const d = amp * (1 - k / len) ** 2;
  return `translate(${Math.sin(k * 2.7) * d}px, ${Math.cos(k * 3.1) * d * 0.6}px)`;
};

/** Pill with a hairline border, used for product facts. */
export const Chip: React.FC<{ children: React.ReactNode; color?: string; style?: React.CSSProperties }> = ({ children, color = C.text, style }) => (
  <div
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 12,
      padding: "12px 22px",
      border: `1.5px solid ${C.lineStrong}`,
      borderRadius: 999,
      background: "rgba(16,23,28,0.72)",
      fontFamily: F.mono,
      fontSize: 22,
      letterSpacing: "0.12em",
      textTransform: "uppercase",
      color,
      backdropFilter: "blur(6px)",
      ...style,
    }}
  >
    {children}
  </div>
);

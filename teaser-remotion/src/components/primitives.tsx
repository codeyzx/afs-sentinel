import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, F } from "../theme";

export const ease = Easing.bezier(0.22, 1, 0.36, 1);
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1);

/** 0→1 over [start, start+dur] frames with the house ease. */
export const useProgress = (start: number, dur: number, easing = ease) => {
  const frame = useCurrentFrame();
  return interpolate(frame, [start, start + dur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing,
  });
};

export const useSpring = (start: number, config = { damping: 200 }, durationInFrames?: number) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return spring({ frame: frame - start, fps, config, durationInFrames });
};

/** Warm paper with grain, faint ledger rules and a soft vignette. */
export const Paper: React.FC<{ rules?: boolean; tone?: string; children?: React.ReactNode }> = ({
  rules = true,
  tone = C.paper,
  children,
}) => (
  <AbsoluteFill style={{ background: tone }}>
    {rules && (
      <AbsoluteFill
        style={{
          backgroundImage: `repeating-linear-gradient(0deg, transparent 0 53px, rgba(22,19,15,0.045) 53px 54px)`,
          backgroundPosition: "0 30px",
        }}
      />
    )}
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, transparent 55%, rgba(80,60,30,0.16) 100%)" }} />
    {children}
    <Grain />
  </AbsoluteFill>
);

export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.22 }) => {
  const frame = useCurrentFrame();
  // Shift the noise a little every other frame so the paper feels filmed, not flat.
  const seed = Math.floor(frame / 2) % 6;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", mixBlendMode: "multiply", opacity }}>
      <svg width="100%" height="100%">
        <filter id={`grain-${seed}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={seed} stitchTiles="stitch" />
          <feColorMatrix values="0 0 0 0 0.35  0 0 0 0 0.3  0 0 0 0 0.24  0 0 0 0.55 0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#grain-${seed})`} />
      </svg>
    </AbsoluteFill>
  );
};

/** Mono uppercase label, the dossier's chrome. */
export const Kicker: React.FC<{ children: React.ReactNode; color?: string; size?: number; style?: React.CSSProperties }> = ({
  children,
  color = C.muted,
  size = 20,
  style,
}) => (
  <div
    style={{
      fontFamily: F.mono,
      fontSize: size,
      letterSpacing: "0.14em",
      textTransform: "uppercase",
      color,
      fontWeight: 500,
      ...style,
    }}
  >
    {children}
  </div>
);

/** Highlighter stroke that sweeps in behind its text. */
export const Marker: React.FC<{
  start: number;
  dur?: number;
  color?: string;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ start, dur = 14, color = C.marker, children, style }) => {
  const p = useProgress(start, dur, easeInOut);
  return (
    <span style={{ position: "relative", display: "inline", whiteSpace: "nowrap", ...style }}>
      <span
        style={{
          position: "absolute",
          left: "-0.12em",
          right: "-0.12em",
          top: "0.12em",
          bottom: "0.02em",
          background: color,
          transformOrigin: "left center",
          transform: `scaleX(${p}) skewX(-8deg)`,
          borderRadius: "0.12em 0.3em 0.18em 0.35em",
          mixBlendMode: "multiply",
          opacity: 0.92,
        }}
      />
      <span style={{ position: "relative" }}>{children}</span>
    </span>
  );
};

/** Hand-drawn red ellipse that draws itself around a box. */
export const DrawCircle: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  start: number;
  dur?: number;
  color?: string;
  stroke?: number;
}> = ({ x, y, w, h, start, dur = 18, color = C.red, stroke = 5 }) => {
  const p = useProgress(start, dur, easeInOut);
  const pad = 18;
  const rx = w / 2 + pad;
  const ry = h / 2 + pad * 0.8;
  const cx = x + w / 2;
  const cy = y + h / 2;
  // An ellipse that overshoots its start a little, like a pen loop.
  const pts: string[] = [];
  const n = 64;
  for (let i = 0; i <= n; i++) {
    const a = -Math.PI * 0.9 + (i / n) * Math.PI * 2.15;
    const wobble = 1 + 0.035 * Math.sin(i * 0.9) + (i / n) * 0.06;
    pts.push(`${cx + Math.cos(a) * rx * wobble},${cy + Math.sin(a) * ry * wobble}`);
  }
  const len = 2 * Math.PI * Math.sqrt((rx * rx + ry * ry) / 2) * 1.1;
  return (
    <svg style={{ position: "absolute", inset: 0, overflow: "visible", pointerEvents: "none" }} width="100%" height="100%">
      <polyline
        points={pts.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray={len}
        strokeDashoffset={len * (1 - p)}
        opacity={p > 0 ? 0.92 : 0}
      />
    </svg>
  );
};

/** Red rubber stamp that slams in. */
export const Stamp: React.FC<{ start: number; children: React.ReactNode; rotate?: number; size?: number; color?: string; blend?: React.CSSProperties["mixBlendMode"] }> = ({
  start,
  children,
  rotate = -8,
  size = 54,
  color = C.red,
  blend = "multiply",
}) => {
  const frame = useCurrentFrame();
  const s = useSpring(start, { damping: 11, stiffness: 220, mass: 0.6 } as never);
  if (frame < start) return null;
  const scale = interpolate(s, [0, 1], [2.4, 1]);
  const opacity = interpolate(frame - start, [0, 3], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div
      style={{
        display: "inline-block",
        transform: `rotate(${rotate}deg) scale(${scale})`,
        opacity,
        border: `${Math.round(size / 10)}px solid ${color}`,
        borderRadius: 10,
        padding: `${size * 0.12}px ${size * 0.4}px`,
        color,
        fontFamily: F.mono,
        fontWeight: 600,
        fontSize: size,
        letterSpacing: "0.12em",
        textTransform: "uppercase",
        mixBlendMode: blend,
        maskImage:
          "radial-gradient(circle at 30% 40%, black 60%, rgba(0,0,0,0.75) 61%, black 70%), linear-gradient(black, black)",
      }}
    >
      {children}
    </div>
  );
};

/** Words rise in one by one. */
export const RiseWords: React.FC<{
  text: string;
  start: number;
  stagger?: number;
  style?: React.CSSProperties;
  wordStyle?: (word: string, i: number) => React.CSSProperties | undefined;
}> = ({ text, start, stagger = 3, style, wordStyle }) => {
  const frame = useCurrentFrame();
  const words = text.split(" ");
  return (
    <div style={style}>
      {words.map((w, i) => {
        const p = interpolate(frame, [start + i * stagger, start + i * stagger + 14], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: ease,
        });
        return (
          <span key={i} style={{ display: "inline-block", overflow: "hidden", verticalAlign: "bottom", paddingBottom: "0.08em" }}>
            <span
              style={{
                display: "inline-block",
                transform: `translateY(${(1 - p) * 105}%)`,
                opacity: p,
                ...wordStyle?.(w, i),
              }}
            >
              {w}
              {i < words.length - 1 ? " " : ""}
            </span>
          </span>
        );
      })}
    </div>
  );
};

/** Count from `from` to `to` over a window. */
export const CountUp: React.FC<{ from?: number; to: number; start: number; dur?: number; decimals?: number }> = ({
  from = 0,
  to,
  start,
  dur = 30,
  decimals = 0,
}) => {
  const p = useProgress(start, dur);
  const v = from + (to - from) * p;
  return <>{v.toFixed(decimals).replace(".", ",")}</>;
};

export const FadeIn: React.FC<{ start: number; dur?: number; y?: number; x?: number; children: React.ReactNode; style?: React.CSSProperties }> = ({
  start,
  dur = 16,
  y = 24,
  x = 0,
  children,
  style,
}) => {
  const p = useProgress(start, dur);
  return <div style={{ opacity: p, transform: `translate(${(1 - p) * x}px, ${(1 - p) * y}px)`, ...style }}>{children}</div>;
};

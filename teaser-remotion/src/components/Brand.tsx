import React from "react";
import { useCurrentFrame } from "remotion";
import { C, F } from "../theme";
import { CaptureName, CamKey, ScreenCapture, Rect } from "./ScreenCapture";
import { ease, easeInOut, prog } from "./primitives";

/**
 * The Sentinel's eye: a ring with tick marks, a sweeping red arc and a centre pupil.
 * `draw` 0→1 draws the ring, `sweep` is the arc angle in degrees.
 */
export const Emblem: React.FC<{ size: number; draw?: number; sweep?: number; glow?: number }> = ({ size, draw = 1, sweep = 0, glow = 0.6 }) => {
  const r = 44;
  const circ = 2 * Math.PI * r;
  const ticks = 36;
  return (
    <svg width={size} height={size} viewBox="-50 -50 100 100" style={{ overflow: "visible", filter: `drop-shadow(0 0 ${size * 0.06}px rgba(255,59,48,${glow}))` }}>
      <circle r={r} fill="none" stroke={C.text} strokeOpacity={0.9} strokeWidth={1.6} strokeDasharray={circ} strokeDashoffset={circ * (1 - draw)} transform="rotate(-90)" />
      <circle r={r - 7} fill="none" stroke={C.text} strokeOpacity={0.18} strokeWidth={0.6} />
      {Array.from({ length: ticks }, (_, i) => {
        const on = i / ticks <= draw;
        const long = i % 9 === 0;
        return (
          <line
            key={i}
            x1={0}
            y1={-r + 2}
            x2={0}
            y2={-r + (long ? 7 : 4)}
            stroke={C.text}
            strokeOpacity={on ? (long ? 0.9 : 0.35) : 0}
            strokeWidth={long ? 1.4 : 0.7}
            transform={`rotate(${(i / ticks) * 360})`}
          />
        );
      })}
      <g transform={`rotate(${sweep - 90})`}>
        <path d={`M 0 0 L ${r - 1} 0 A ${r - 1} ${r - 1} 0 0 0 ${(r - 1) * Math.cos((-50 * Math.PI) / 180)} ${(r - 1) * Math.sin((-50 * Math.PI) / 180)} Z`} fill="url(#sweepGrad)" opacity={draw} />
        <line x1={0} y1={0} x2={r - 1} y2={0} stroke={C.red} strokeWidth={1.6} opacity={draw} />
      </g>
      <defs>
        <radialGradient id="sweepGrad" cx="0" cy="0" r={r} gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor={C.red} stopOpacity={0.05} />
          <stop offset="100%" stopColor={C.red} stopOpacity={0.45} />
        </radialGradient>
      </defs>
      <circle r={5.5 * draw} fill={C.red} />
      <circle r={9 * draw} fill="none" stroke={C.red} strokeOpacity={0.5} strokeWidth={0.8} />
    </svg>
  );
};

/** "AFS SENTINEL" wordmark; letters assemble from `start`. */
export const Wordmark: React.FC<{ start: number; size?: number; stagger?: number }> = ({ start, size = 150, stagger = 1.6 }) => {
  const frame = useCurrentFrame();
  const letters = "AFS SENTINEL".split("");
  return (
    <div style={{ display: "flex", fontFamily: F.display, fontWeight: 800, fontSize: size, letterSpacing: "0.06em", lineHeight: 1, color: C.text }}>
      {letters.map((ch, i) => {
        const p = prog(frame, start + i * stagger, 16);
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              width: ch === " " ? "0.32em" : undefined,
              color: i < 3 ? C.red : C.text,
              opacity: p,
              transform: `translateY(${(1 - p) * 0.35}em) scale(${1 + (1 - p) * 0.4})`,
              filter: `blur(${(1 - p) * 12}px)`,
            }}
          >
            {ch}
          </span>
        );
      })}
    </div>
  );
};

/**
 * A product capture floating in 3D: perspective tilt, soft glow underneath, a reflection line on top.
 * `ry`/`rx` are degrees; `z` pushes it away (negative) or toward the camera.
 */
export const Window3D: React.FC<{
  cap: CaptureName;
  width: number;
  x: number;
  y: number;
  rx?: number;
  ry?: number;
  rz?: number;
  z?: number;
  opacity?: number;
  from?: number;
  startAt?: number;
  timeMap?: [number, number][];
  keys?: CamKey[];
  url: string;
  label?: string;
  glow?: string;
  showCursor?: boolean;
  children?: (toScreen: (r: Rect) => Rect, t: number) => React.ReactNode;
}> = ({ cap, width, x, y, rx = 0, ry = 0, rz = 0, z = 0, opacity = 1, glow = "255,59,48", label, children, ...rest }) => (
  <div style={{ position: "absolute", inset: 0, perspective: 2200, perspectiveOrigin: "50% 45%", opacity }}>
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width,
        transformStyle: "preserve-3d",
        transform: `translate(-50%, -50%) translateZ(${z}px) rotateX(${rx}deg) rotateY(${ry}deg) rotateZ(${rz}deg)`,
      }}
    >
      <div
        style={{
          position: "absolute",
          left: "8%",
          right: "8%",
          bottom: -40,
          height: 80,
          background: `radial-gradient(ellipse 50% 50% at 50% 50%, rgba(${glow},0.35), transparent 70%)`,
          filter: "blur(20px)",
        }}
      />
      <div
        style={{
          position: "relative",
          width,
          height: (width * 9) / 16 + 46,
          borderRadius: 14,
          boxShadow: `0 40px 120px rgba(0,0,0,0.75), 0 0 0 1px rgba(214,228,236,0.14), 0 0 60px rgba(${glow},0.10)`,
        }}
      >
        <ScreenCapture cap={cap} width={width} {...rest} exhibit={label}>
          {children}
        </ScreenCapture>
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: 14,
            pointerEvents: "none",
            background: "linear-gradient(115deg, rgba(255,255,255,0.08) 0%, transparent 28%, transparent 70%, rgba(255,255,255,0.03) 100%)",
          }}
        />
      </div>
    </div>
  </div>
);

/** Focus ring drawn in screen space over a capture rect. */
export const FocusRing: React.FC<{ r: Rect; p: number; color?: string; pad?: number }> = ({ r, p, color = C.red, pad = 10 }) => {
  if (p <= 0) return null;
  return (
    <div
      style={{
        position: "absolute",
        left: r.x - pad,
        top: r.y - pad,
        width: r.w + pad * 2,
        height: r.h + pad * 2,
        border: `3px solid ${color}`,
        borderRadius: 10,
        opacity: p,
        transform: `scale(${1.08 - 0.08 * ease(p)})`,
        boxShadow: `0 0 0 9999px rgba(0,0,0,${0.45 * p}), 0 0 30px ${color}`,
      }}
    />
  );
};

export const usePulse = (period = 30) => {
  const frame = useCurrentFrame();
  return 0.5 + 0.5 * Math.sin((frame / period) * Math.PI * 2);
};

export { easeInOut };

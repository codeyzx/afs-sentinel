import React from "react";
import { Freeze, interpolate, OffthreadVideo, staticFile, useCurrentFrame } from "remotion";
import backtest from "../../public/capture/backtest.json";
import dashboard from "../../public/capture/dashboard.json";
import incidentAi from "../../public/capture/incident-ai.json";
import incidentEvidence from "../../public/capture/incident-evidence.json";
import incidentTriage from "../../public/capture/incident-triage.json";
import logs from "../../public/capture/logs.json";
import scheduler from "../../public/capture/scheduler.json";
import { C, F, FPS } from "../theme";
import { easeInOut, Kicker } from "./primitives";

type Ev = { t: number; type: string; label?: string; x?: number; y?: number; w?: number; h?: number; bx?: number; by?: number };
type Meta = { name: string; duration: number; viewport: { width: number; height: number }; events: Ev[] };

export const CAPTURES = {
  backtest,
  dashboard,
  "incident-ai": incidentAi,
  "incident-evidence": incidentEvidence,
  "incident-triage": incidentTriage,
  logs,
  scheduler,
} as unknown as Record<string, Meta>;
export type CaptureName = keyof typeof CAPTURES;

export type Rect = { x: number; y: number; w: number; h: number };

export const markOf = (cap: CaptureName, label: string): Ev & Rect => {
  const e = CAPTURES[cap].events.find((ev) => ev.type === "mark" && ev.label === label);
  if (!e) throw new Error(`mark ${label} missing in ${cap}`);
  return e as Ev & Rect;
};

/**
 * A camera keyframe. `at` is the capture time (seconds) when the move starts; by default a
 * mark's own timestamp. `target` is a mark label or a rect in page CSS pixels; null = full page.
 */
export type CamKey = { at?: number; target: string | Rect | null; zoom?: number; pad?: number; dur?: number; anchor?: "center" | "top" };

type View = { cx: number; cy: number; s: number };

const viewFor = (rect: Rect | null, vw: number, vh: number, zoom?: number, pad = 40, anchor: "center" | "top" = "center"): View => {
  if (!rect) return { cx: vw / 2, cy: vh / 2, s: 1 };
  const fit = Math.min(vw / (rect.w + pad * 2), vh / (rect.h + pad * 2));
  const s = Math.max(1, Math.min(zoom ?? fit, 3.2));
  let cx = rect.x + rect.w / 2;
  let cy = anchor === "top" ? rect.y - pad + vh / s / 2 : rect.y + rect.h / 2;
  // keep the view inside the page
  const hw = vw / s / 2;
  const hh = vh / s / 2;
  cx = Math.min(Math.max(cx, hw), vw - hw);
  cy = Math.min(Math.max(cy, hh), vh - hh);
  return { cx, cy, s };
};

const cursorAt = (events: Ev[], t: number) => {
  let last: Ev | undefined;
  for (const e of events) {
    if (e.type !== "cursor") continue;
    if (e.t > t) break;
    last = e;
  }
  return last;
};

/**
 * The product, shown as a dark evidence window on the paper. Plays a capture from
 * `startAt` seconds at `from` (scene frame), freezes at its end, and moves a camera between keys.
 */
export const ScreenCapture: React.FC<{
  cap: CaptureName;
  from?: number;
  startAt?: number;
  /** Piecewise [scene frame, capture seconds] pairs; overrides from/startAt (holds and speed-ups). */
  timeMap?: [number, number][];
  keys?: CamKey[];
  url: string;
  exhibit?: string;
  style?: React.CSSProperties;
  width: number;
  showCursor?: boolean;
  children?: (toScreen: (r: Rect) => Rect, t: number) => React.ReactNode;
}> = ({ cap, from = 0, startAt = 0, timeMap, keys = [], url, exhibit, style, width, showCursor = true, children }) => {
  const frame = useCurrentFrame();
  const meta = CAPTURES[cap];
  const { width: vw, height: vh } = meta.viewport;
  const height = (width * vh) / vw;
  const base = width / vw;

  const map = timeMap ?? [
    [from, startAt],
    [from + (meta.duration - startAt) * FPS, meta.duration],
  ];
  const t = Math.min(
    interpolate(frame, map.map((m) => m[0]), map.map((m) => m[1]), { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
    meta.duration - 1 / FPS,
  );

  // camera
  const resolved = keys.map((k) => {
    const rect = typeof k.target === "string" ? markOf(cap, k.target) : k.target;
    const at = k.at ?? (typeof k.target === "string" ? markOf(cap, k.target).t : 0);
    return { at, dur: k.dur ?? 1.0, view: viewFor(rect, vw, vh, k.zoom, k.pad, k.anchor) };
  });
  let view: View = { cx: vw / 2, cy: vh / 2, s: 1 };
  for (const k of resolved) {
    if (t < k.at) break;
    const p = easeInOut(Math.min(1, (t - k.at) / k.dur));
    view = {
      cx: view.cx + (k.view.cx - view.cx) * p,
      cy: view.cy + (k.view.cy - view.cy) * p,
      s: Math.exp(Math.log(view.s) + (Math.log(k.view.s) - Math.log(view.s)) * p),
    };
  }
  const toScreen = (r: Rect): Rect => ({
    x: ((r.x - view.cx) * view.s + vw / 2) * base,
    y: ((r.y - view.cy) * view.s + vh / 2) * base,
    w: r.w * view.s * base,
    h: r.h * view.s * base,
  });

  const cur = showCursor ? cursorAt(meta.events, t) : undefined;
  const lastClick = meta.events.filter((e) => e.type === "click" && e.t <= t).at(-1);
  const clickAge = lastClick ? t - lastClick.t : 99;

  const video = <OffthreadVideo src={staticFile(`capture/${cap}.mp4`)} muted style={{ width: "100%", height: "100%" }} />;

  return (
    <div style={{ position: "absolute", width, ...style }}>
      <WindowChrome url={url} exhibit={exhibit} width={width} />
      <div style={{ position: "relative", width, height, overflow: "hidden", background: C.app, borderRadius: "0 0 14px 14px" }}>
        <div
          style={{
            position: "absolute",
            width: vw,
            height: vh,
            transformOrigin: "0 0",
            transform: `scale(${base}) translate(${vw / 2}px, ${vh / 2}px) scale(${view.s}) translate(${-view.cx}px, ${-view.cy}px)`,
          }}
        >
          <Freeze frame={Math.max(0, Math.round(t * FPS))}>{video}</Freeze>
        </div>
        {cur && <Cursor x={toScreen({ x: cur.x!, y: cur.y!, w: 0, h: 0 }).x} y={toScreen({ x: cur.x!, y: cur.y!, w: 0, h: 0 }).y} clickAge={clickAge} />}
        {children?.(toScreen, t)}
      </div>
    </div>
  );
};

const WindowChrome: React.FC<{ url: string; exhibit?: string; width: number }> = ({ url, exhibit, width }) => (
  <div
    style={{
      width,
      height: 46,
      background: "#1B1916",
      borderRadius: "14px 14px 0 0",
      display: "flex",
      alignItems: "center",
      padding: "0 18px",
      gap: 16,
      boxSizing: "border-box",
    }}
  >
    <div style={{ display: "flex", gap: 8 }}>
      {["#E0604F", "#E3B341", "#5DB36A"].map((c) => (
        <div key={c} style={{ width: 12, height: 12, borderRadius: 6, background: c, opacity: 0.85 }} />
      ))}
    </div>
    <div
      style={{
        flex: 1,
        height: 28,
        borderRadius: 7,
        background: "#2A2723",
        color: "#BDB4A6",
        fontFamily: F.mono,
        fontSize: 15,
        display: "flex",
        alignItems: "center",
        padding: "0 12px",
        overflow: "hidden",
        whiteSpace: "nowrap",
      }}
    >
      <span style={{ color: "#7FBF8E", marginRight: 8 }}>●</span>
      {url}
    </div>
    {exhibit && (
      <Kicker size={13} color="#E8A598">
        {exhibit}
      </Kicker>
    )}
  </div>
);

const Cursor: React.FC<{ x: number; y: number; clickAge: number }> = ({ x, y, clickAge }) => {
  const ring = clickAge < 0.6 ? clickAge / 0.6 : 1;
  const press = clickAge < 0.15 ? 0.82 : 1;
  return (
    <>
      {clickAge < 0.6 && (
        <div
          style={{
            position: "absolute",
            left: x - 30,
            top: y - 30,
            width: 60,
            height: 60,
            borderRadius: 30,
            border: `3px solid ${C.marker}`,
            transform: `scale(${0.3 + ring * 1.1})`,
            opacity: 1 - ring,
          }}
        />
      )}
      <svg
        width={30}
        height={30}
        viewBox="0 0 24 24"
        style={{ position: "absolute", left: x - 4, top: y - 2, transform: `scale(${press})`, transformOrigin: "4px 2px", filter: "drop-shadow(0 2px 3px rgba(0,0,0,0.45))" }}
      >
        <path d="M4 2 L4 19 L8.5 15 L11.5 21.5 L14.2 20.3 L11.3 14 L17.5 14 Z" fill="#FFFFFF" stroke="#111" strokeWidth={1.4} strokeLinejoin="round" />
      </svg>
    </>
  );
};

/** Fade helper for overlays drawn in screen space over a capture. */
export const useOverlay = (startT: number, t: number, len = 0.35) => interpolate(t, [startT, startT + len], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Captions, SfxTrack } from "../components/Chrome";
import { DrawCircle, ease, easeInOut, FadeIn, Grain, Kicker, Marker, Paper, Stamp, useProgress } from "../components/primitives";
import { REAL, quarter } from "../data";
import { atWord } from "../timeline";
import { C, F } from "../theme";
import type { SceneProps } from "./util";

const HEADLINE = "8 Mei 2023 — BEI menghentikan perdagangan saham WSKT";

export const SC01Hook: React.FC<SceneProps> = ({ scene }) => {
  const frame = useCurrentFrame();
  const reveal = atWord(scene, 0, "Sistem");
  const typed = Math.max(0, Math.min(HEADLINE.length, Math.floor((frame - 8) * 1.5)));
  const caret = Math.floor(frame / 8) % 2 === 0;
  const black = interpolate(frame, [reveal - 6, reveal + 4], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      {/* paper + chart underneath, revealed by the black lifting */}
      <Paper>
        <WsktChart start={reveal} />
        <div style={{ position: "absolute", left: 120, top: 640, width: 1100 }}>
          <FadeIn start={reveal + 70} dur={18}>
            <div style={{ fontFamily: F.serif, fontSize: 112, lineHeight: 0.98, fontWeight: 500, color: C.ink, letterSpacing: "-0.02em" }}>
              Ditandai{" "}
              <Marker start={reveal + 82} dur={16}>
                25 bulan
              </Marker>
              <br />
              <span style={{ fontStyle: "italic", fontWeight: 400 }}>lebih awal.</span>
            </div>
          </FadeIn>
        </div>
        <div style={{ position: "absolute", right: 150, top: 760 }}>
          <Stamp start={reveal + 104} size={58}>
            Ditandai
          </Stamp>
        </div>
      </Paper>

      <AbsoluteFill style={{ background: C.night, opacity: black }}>
        <div style={{ position: "absolute", left: 160, top: 430, right: 160 }}>
          <Kicker size={18} color="rgba(241,236,226,0.5)">
            Senin, 8 Mei 2023 · Bursa Efek Indonesia
          </Kicker>
          <div style={{ fontFamily: F.mono, fontSize: 52, color: C.paper, marginTop: 22, lineHeight: 1.25, fontWeight: 500 }}>
            {HEADLINE.slice(0, typed)}
            <span style={{ opacity: caret ? 1 : 0, color: C.red }}>▍</span>
          </div>
        </div>
        <Grain opacity={0.5} />
      </AbsoluteFill>

      <Captions lines={scene.lines} dark={black > 0.5} />
      <SfxTrack
        cues={[
          { at: 8, name: "type-loop", volume: 0.35, dur: 36 },
          { at: reveal - 4, name: "impact", volume: 0.55, dur: 120 },
          { at: reveal + 82, name: "marker", volume: 0.35 },
          { at: reveal + 104, name: "stamp", volume: 0.7 },
        ]}
      />
    </AbsoluteFill>
  );
};

/** WSKT backtest scores up to the suspension, drawn on paper with a camera push into 2021-Q1. */
const WsktChart: React.FC<{ start: number }> = ({ start }) => {
  const frame = useCurrentFrame();
  const all = REAL.backtest.WSKT.rows;
  const rows = all.filter((r) => r.date <= "2023-06-30");
  const X0 = 140;
  const X1 = 1780;
  const Y0 = 560; // score 0
  const Y1 = 150; // score 100
  const n = rows.length;
  const xAt = (i: number) => X0 + ((X1 - X0) * i) / (n - 1);
  const yAt = (s: number) => Y0 - ((Y0 - Y1) * s) / 100;
  // suspension 2023-05-08 sits between 2023-Q1 (i=8) and 2023-Q2 (i=9)
  const xEvent = xAt(8) + (xAt(9) - xAt(8)) * (38 / 91);

  const draw = useProgress(start + 4, 40, easeInOut);
  const pts = rows.map((r, i) => [xAt(i), yAt(r.score ?? 0)] as const);
  const path = pts.map(([x, y], i) => `${i ? "L" : "M"}${x},${y}`).join(" ");
  const len = 2600;

  // a slow drift in, never so far that the suspension leaves the frame
  const scale = interpolate(frame, [start, start + 200], [0.97, 1.02], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const bracket = useProgress(start + 52, 22);
  const first = pts[0];

  return (
    <div style={{ position: "absolute", inset: 0, transform: `scale(${scale})`, transformOrigin: "50% 30%" }}>
      <div style={{ position: "absolute", left: X0, top: 72 }}>
        <Kicker size={18}>Backtest · WSKT · Waskita Karya (Persero) Tbk · skor risiko per kuartal</Kicker>
      </div>
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        {/* severity bands */}
        <rect x={X0} y={yAt(100)} width={X1 - X0} height={yAt(60) - yAt(100)} fill="rgba(217,58,43,0.07)" />
        <rect x={X0} y={yAt(60)} width={X1 - X0} height={yAt(30) - yAt(60)} fill="rgba(217,165,20,0.10)" />
        <rect x={X0} y={yAt(30)} width={X1 - X0} height={yAt(0) - yAt(30)} fill="rgba(47,158,91,0.07)" />
        {[0, 30, 60, 100].map((v) => (
          <g key={v}>
            <line x1={X0} x2={X1} y1={yAt(v)} y2={yAt(v)} stroke={C.line} />
            <text x={X0 - 16} y={yAt(v) + 6} textAnchor="end" fontFamily={F.mono} fontSize={16} fill={C.muted}>
              {v}
            </text>
          </g>
        ))}
        {[
          ["Kritis", 80],
          ["Sedang", 45],
          ["Rendah", 15],
        ].map(([l, v]) => (
          <text key={l} x={X1 - 10} y={yAt(v as number) + 6} textAnchor="end" fontFamily={F.mono} fontSize={15} fill={C.muted} letterSpacing="0.1em">
            {String(l).toUpperCase()}
          </text>
        ))}
        {rows.map((r, i) => (
          <text key={r.date} x={xAt(i)} y={Y0 + 34} textAnchor="middle" fontFamily={F.mono} fontSize={15} fill={C.muted}>
            {quarter(r.date)}
          </text>
        ))}
        {/* event */}
        <line x1={xEvent} x2={xEvent} y1={Y1 - 20} y2={Y0} stroke={C.red} strokeWidth={2.5} strokeDasharray="8 8" opacity={draw} />
        <text x={xEvent - 12} y={Y1 - 30} textAnchor="end" fontFamily={F.mono} fontSize={17} fill={C.red} opacity={draw} letterSpacing="0.06em">
          8 MEI 2023 · SUSPENSI
        </text>
        <path d={path} fill="none" stroke={C.ink} strokeWidth={4} strokeLinejoin="round" strokeDasharray={len} strokeDashoffset={len * (1 - draw)} />
        {pts.map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r={i === 0 ? 9 : 6} fill={i === 0 ? C.red : C.ink} opacity={draw > i / n ? 1 : 0} />
        ))}
        {/* 25-month bracket */}
        <g opacity={bracket}>
          <line x1={first[0]} x2={first[0] + (xEvent - first[0]) * bracket} y1={Y0 + 58} y2={Y0 + 58} stroke={C.red} strokeWidth={3} />
          <line x1={first[0]} x2={first[0]} y1={Y0 + 48} y2={Y0 + 68} stroke={C.red} strokeWidth={3} />
          <line x1={xEvent} x2={xEvent} y1={Y0 + 48} y2={Y0 + 68} stroke={C.red} strokeWidth={3} opacity={bracket > 0.98 ? 1 : 0} />
        </g>
      </svg>
      <DrawCircle x={first[0] - 26} y={first[1] - 26} w={52} h={52} start={start + 48} />
      <div style={{ position: "absolute", left: first[0] + 50, top: first[1] - 92, opacity: interpolate(frame, [start + 56, start + 66], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease }) }}>
        <Kicker size={17} color={C.red}>
          2021-Q1 · pertama kali “Sedang” · skor {String(rows[0].score).replace(".", ",")}
        </Kicker>
      </div>
    </div>
  );
};

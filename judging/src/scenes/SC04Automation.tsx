import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Captions, SceneHeader, SfxTrack } from "../components/Chrome";
import { FaceCam, NameTag } from "../components/FaceCam";
import { markOf, ScreenCapture } from "../components/ScreenCapture";
import { DrawCircle, easeInOut, FadeIn, Kicker, Marker, Paper, useProgress } from "../components/primitives";
import { atWord } from "../timeline";
import { C, F } from "../theme";
import { PIP, SCREEN, type SceneProps } from "./util";

export const SC04Automation: React.FC<SceneProps> = ({ scene, index }) => {
  const line = scene.lines[0];
  const commandAt = atWord(scene, 0, "Heroku");
  const freqAt = atWord(scene, 0, "setiap");
  const dueAt = atWord(scene, 0, "jatuh");
  const archAt = atWord(scene, 0, "Tanpa");
  const cacheAt = atWord(scene, 0, "disimpan");

  const cmd = markOf("scheduler", "command");
  const freq = markOf("scheduler", "frequency");
  const last = markOf("scheduler", "lastRun");
  const next = markOf("scheduler", "nextDue");

  // capture seconds pinned to the voice
  const timeMap: [number, number][] = [
    [0, 0.6],
    [commandAt, cmd.t],
    [freqAt, freq.t],
    [dueAt, last.t],
    [archAt, 14],
  ];
  const swap = useProgress(archAt - 4, 22, easeInOut);

  return (
    <AbsoluteFill>
      <Paper>
        <SceneHeader scene={scene} index={index} />
        <div style={{ opacity: 1 - swap, transform: `translateY(${swap * -30}px)` }}>
          <ScreenCapture
            cap="scheduler"
            timeMap={timeMap}
            width={SCREEN.width}
            style={{ left: SCREEN.left, top: SCREEN.top }}
            url="dashboard.heroku.com/apps/afs-sentinel/scheduler"
            exhibit="Exhibit 01 · Heroku Scheduler"
            keys={[
              { target: { x: cmd.x - 24, y: cmd.y - 40, w: 760, h: cmd.h + 80 }, at: cmd.t - 0.6, zoom: 1.9, dur: 1.1 },
              { target: { x: cmd.x - 10, y: freq.y - 24, w: freq.x + freq.w + 20 - cmd.x, h: 64 }, at: freq.t - 0.4, zoom: 1.75, dur: 1 },
              { target: { x: last.x, y: last.y, w: next.x + next.w - last.x, h: last.h }, at: last.t - 0.5, zoom: 2.0, dur: 1 },
            ]}
          >
            {(toScreen, t) => (
              <>
                {t >= cmd.t && t < freq.t - 0.4 && <DrawCircle {...toScreen(cmd)} start={commandAt + 6} />}
                {t >= freq.t && t < last.t - 0.5 && <DrawCircle {...toScreen(freq)} start={freqAt + 8} />}
                {t >= freq.t && t < last.t - 0.5 && (
                  <Tag rect={toScreen(freq)} start={freqAt + 16}>
                    01:00 UTC = 08:00 WIB · setiap hari
                  </Tag>
                )}
                {t >= last.t && <Tag rect={toScreen({ ...last, w: next.x + next.w - last.x })} start={dueAt + 10}>Jalan tiap hari — pipeline yang memutuskan: jatuh tempo 3 hari</Tag>}
              </>
            )}
          </ScreenCapture>
        </div>

        {swap > 0 && <Architecture start={archAt + 4} cacheAt={cacheAt} opacity={swap} />}

        <FaceCam clip={line.clips[0]} who="Yahya" playFrom={line.from} playDur={line.dur} style={{ ...PIP }} />
        <NameTag who="Yahya" start={10} style={{ left: PIP.left + 20, top: PIP.top + PIP.height - 96 }} dark />
        <FadeIn start={archAt + 30} dur={16} style={{ position: "absolute", left: PIP.left, top: PIP.top + PIP.height + 34, width: PIP.width }}>
          <div style={{ fontFamily: F.serif, fontSize: 40, lineHeight: 1.08, color: C.ink }}>
            <Marker start={archAt + 40}>Tanpa tombol,</Marker>
            <br />
            <Marker start={archAt + 52}>tanpa manusia.</Marker>
          </div>
        </FadeIn>
      </Paper>
      <Captions lines={scene.lines} />
      <SfxTrack
        cues={[
          { at: commandAt + 6, name: "marker", volume: 0.3 },
          { at: freqAt + 8, name: "marker", volume: 0.3 },
          { at: archAt - 4, name: "whoosh", volume: 0.35 },
          ...[0, 1, 2, 3, 4].map((i) => ({ at: archAt + 8 + i * 9, name: "tick", volume: 0.18 })),
          { at: archAt + 40, name: "marker", volume: 0.3 },
        ]}
      />
    </AbsoluteFill>
  );
};

const Tag: React.FC<{ rect: { x: number; y: number; w: number; h: number }; start: number; children: React.ReactNode }> = ({ rect, start, children }) => {
  const p = useProgress(start, 12);
  return (
    <div
      style={{
        position: "absolute",
        left: rect.x,
        top: rect.y + rect.h + 22,
        opacity: p,
        transform: `translateY(${(1 - p) * 10}px)`,
        background: C.red,
        color: "#FBF8F2",
        fontFamily: F.mono,
        fontSize: 19,
        letterSpacing: "0.04em",
        padding: "8px 14px",
        borderRadius: 6,
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </div>
  );
};

type Node = { id: string; title: string; sub: string; x: number; y: number; accent?: boolean };

/** How one unattended run flows. */
const Architecture: React.FC<{ start: number; cacheAt: number; opacity: number }> = ({ start, cacheAt, opacity }) => {
  const frame = useCurrentFrame();
  const nodes: Node[] = [
    { id: "sched", title: "Heroku Scheduler", sub: "tiap hari 01:00 UTC", x: 0, y: 70 },
    { id: "due", title: "Jatuh tempo?", sub: "≥ 3 hari sejak run sukses", x: 300, y: 70, accent: true },
    { id: "api", title: "Sectors API", sub: "laporan kuartalan", x: 600, y: 0 },
    { id: "db", title: "Postgres", sub: "cache permanen", x: 600, y: 170 },
    { id: "rules", title: "6 Forensic Rule", sub: "skor risiko 0–100", x: 900, y: 70 },
    { id: "tg", title: "Telegram", sub: "alert + ringkasan run", x: 1200, y: 0 },
    { id: "web", title: "Web app", sub: "bukti & triage", x: 1200, y: 170 },
  ];
  const edges: [string, string][] = [
    ["sched", "due"],
    ["due", "api"],
    ["api", "db"],
    ["due", "db"],
    ["db", "rules"],
    ["rules", "tg"],
    ["rules", "web"],
  ];
  const NW = 260;
  const NH = 104;
  const pos = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const order = (id: string) => nodes.findIndex((n) => n.id === id);
  const cache = useProgress(cacheAt, 14);
  return (
    <div style={{ position: "absolute", left: SCREEN.left, top: 250, width: 1260, opacity }}>
      <Kicker size={17} color={C.ink}>
        Satu run tanpa pengawasan
      </Kicker>
      <div style={{ position: "relative", marginTop: 40, transform: "scale(0.84)", transformOrigin: "0 0", height: 330 }}>
        <svg width={1500} height={300} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
          {edges.map(([a, b], i) => {
            const A = pos[a];
            const B = pos[b];
            const p = interpolate(frame, [start + order(b) * 9, start + order(b) * 9 + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            const vertical = A.x === B.x;
            const x1 = vertical ? A.x + NW / 2 : A.x + NW;
            const y1 = vertical ? A.y + NH : A.y + NH / 2;
            const x2 = vertical ? B.x + NW / 2 : B.x;
            const y2 = vertical ? B.y : B.y + NH / 2;
            const mx = (x1 + x2) / 2;
            const d = vertical ? `M${x1},${y1} L${x2},${y2}` : `M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`;
            return <path key={i} d={d} fill="none" stroke={C.ink} strokeWidth={2.5} pathLength={1} strokeDasharray="1" strokeDashoffset={1 - p} />;
          })}
          {/* travelling pulse */}
          {frame > start + 70 &&
            (() => {
              const k = ((frame - start - 70) % 60) / 60;
              const x = k * (1200 + NW);
              return <circle cx={x} cy={70 + NH / 2} r={7} fill={C.red} opacity={0.85} />;
            })()}
        </svg>
        {nodes.map((n) => {
          const p = interpolate(frame, [start + order(n.id) * 9, start + order(n.id) * 9 + 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const lit = n.id === "db" ? cache : 0;
          return (
            <div
              key={n.id}
              style={{
                position: "absolute",
                left: n.x,
                top: n.y,
                width: NW,
                height: NH,
                boxSizing: "border-box",
                borderRadius: 12,
                padding: "16px 18px",
                background: n.accent ? C.ink : C.card,
                color: n.accent ? "#FBF8F2" : C.ink,
                border: `2px solid ${lit ? C.red : n.accent ? C.ink : C.lineStrong}`,
                boxShadow: "0 10px 24px rgba(40,28,10,0.10)",
                opacity: p,
                transform: `translateY(${(1 - p) * 16}px)`,
              }}
            >
              <div style={{ fontFamily: F.sans, fontWeight: 700, fontSize: 25 }}>{n.title}</div>
              <div style={{ fontFamily: F.mono, fontSize: 16, marginTop: 6, opacity: 0.75 }}>{n.sub}</div>
            </div>
          );
        })}
        <div
          style={{
            position: "absolute",
            left: 600,
            top: 296,
            width: 560,
            opacity: cache,
            fontFamily: F.mono,
            fontSize: 18,
            color: C.red,
          }}
        >
          ↳ kuartal yang sama tidak pernah dibayar dua kali
        </div>
      </div>
      <div style={{ marginTop: 90 }}>
        <FadeIn start={start + 60} dur={14} y={10}>
          <div style={{ display: "flex", gap: 14 }}>
            {["Jadwal harian", "Jatuh tempo tiap 3 hari", "Tanpa manusia"].map((t) => (
              <div key={t} style={{ fontFamily: F.mono, fontSize: 19, letterSpacing: "0.08em", textTransform: "uppercase", border: `1.5px solid ${C.ink}`, borderRadius: 999, padding: "8px 18px", color: C.ink }}>
                {t}
              </div>
            ))}
          </div>
        </FadeIn>
      </div>
    </div>
  );
};

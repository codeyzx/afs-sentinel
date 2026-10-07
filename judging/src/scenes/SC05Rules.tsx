import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Captions, SceneHeader, SfxTrack } from "../components/Chrome";
import { FaceCam, NameTag } from "../components/FaceCam";
import { easeInOut, FadeIn, Kicker, Paper, useProgress } from "../components/primitives";
import { RULES } from "../data";
import { atWord } from "../timeline";
import { C, F } from "../theme";
import type { SceneProps } from "./util";

export const SC05Rules: React.FC<SceneProps> = ({ scene, index }) => {
  const line = scene.lines[0];
  // rough word positions in the line
  const named = (["Sloan", "divergensi", "Altman", "Beneish", "penjualan", ["laba", 1]] as const).map((w) =>
    typeof w === "string" ? atWord(scene, 0, w) : atWord(scene, 0, w[0], w[1]),
  );
  const listAt = atWord(scene, 0, "Mesinnya");
  const scoreAt = atWord(scene, 0, "Semuanya");

  return (
    <AbsoluteFill>
      <Paper>
        <SceneHeader scene={scene} index={index} />
        <FaceCam clip={line.clips[0]} who="Ais" playFrom={line.from} playDur={line.dur} style={{ left: 96, top: 128, width: 560, height: 760 }} />
        <NameTag who="Ais" start={10} style={{ left: 120, top: 790 }} dark />

        <div style={{ position: "absolute", left: 730, top: 124, width: 1094 }}>
          <FadeIn start={listAt} dur={14}>
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
              <div style={{ fontFamily: F.serif, fontSize: 58, fontWeight: 500, color: C.ink, letterSpacing: "-0.015em" }}>
                6 Forensic Rule <span style={{ fontStyle: "italic", color: C.inkSoft }}>deterministik</span>
              </div>
              <Kicker size={15}>bobot</Kicker>
            </div>
          </FadeIn>
          <div style={{ marginTop: 18, borderTop: `1.5px solid ${C.ink}` }}>
            {RULES.map((r, i) => (
              <RuleRow key={r.name} i={i} rule={r} appear={listAt + 8 + i * 4} lit={named[i]} />
            ))}
          </div>
          <ScoreScale start={scoreAt} />
          <FadeIn start={scoreAt + 30} dur={14} y={6}>
            <div style={{ fontFamily: F.mono, fontSize: 15, color: C.muted, marginTop: 16 }}>
              Disesuaikan dengan data Sectors API · keterbatasan diungkap di README
            </div>
          </FadeIn>
        </div>
      </Paper>
      <Captions lines={scene.lines} />
      <SfxTrack cues={[...named.slice(0, 3).map((f) => ({ at: f, name: "marker", volume: 0.3 })), ...named.slice(3).map((f) => ({ at: f, name: "tick", volume: 0.2 })), { at: scoreAt, name: "whoosh", volume: 0.3 }]} />
    </AbsoluteFill>
  );
};

const RuleRow: React.FC<{ i: number; rule: (typeof RULES)[number]; appear: number; lit: number }> = ({ i, rule, appear, lit }) => {
  const frame = useCurrentFrame();
  const a = interpolate(frame, [appear, appear + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const on = interpolate(frame, [lit, lit + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const bar = useProgress(lit, 18, easeInOut);
  const core = rule.core;
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "54px 1fr 300px 70px",
        alignItems: "center",
        height: 78,
        borderBottom: `1px solid ${C.line}`,
        opacity: a * (0.45 + 0.55 * on),
        position: "relative",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: "6px -10px",
          background: core ? C.redSoft : "rgba(245,213,71,0.22)",
          transformOrigin: "left",
          transform: `scaleX(${on})`,
          borderRadius: 6,
        }}
      />
      <div style={{ position: "relative", fontFamily: F.mono, fontSize: 20, color: core && on ? C.red : C.muted }}>0{i + 1}</div>
      <div style={{ position: "relative" }}>
        <div style={{ fontFamily: F.sans, fontWeight: 600, fontSize: 27, color: C.ink, display: "flex", alignItems: "center", gap: 12 }}>
          {rule.name}
          {core && (
            <span style={{ fontFamily: F.mono, fontSize: 13, letterSpacing: "0.12em", color: "#FBF8F2", background: C.red, padding: "3px 8px", borderRadius: 4, opacity: on }}>
              INTI
            </span>
          )}
        </div>
        <div style={{ fontFamily: F.sans, fontSize: 18, color: C.muted, marginTop: 2 }}>{rule.plain}</div>
      </div>
      <div style={{ position: "relative", height: 12, background: C.line, borderRadius: 6 }}>
        <div style={{ width: `${(rule.weight / 25) * 100 * bar}%`, height: "100%", background: core ? C.red : C.ink, borderRadius: 6 }} />
      </div>
      <div style={{ position: "relative", fontFamily: F.mono, fontSize: 24, fontWeight: 600, color: C.ink, textAlign: "right" }}>{rule.weight}</div>
    </div>
  );
};

/** One composite score, 0–100, with the app's three bands. */
const ScoreScale: React.FC<{ start: number }> = ({ start }) => {
  const p = useProgress(start, 22, easeInOut);
  const needle = useProgress(start + 14, 30, easeInOut);
  const bands = [
    { to: 30, label: "Rendah", color: C.safe },
    { to: 60, label: "Sedang", color: C.warn },
    { to: 100, label: "Kritis", color: C.danger },
  ];
  return (
    <div style={{ marginTop: 26, opacity: p, transform: `translateY(${(1 - p) * 14}px)` }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div style={{ fontFamily: F.serif, fontSize: 34, color: C.ink }}>
          = satu <b>skor risiko</b> <span style={{ fontStyle: "italic" }}>0–100</span>
        </div>
      </div>
      <div style={{ position: "relative", height: 22, display: "flex", marginTop: 14, borderRadius: 4, overflow: "visible" }}>
        {bands.map((b, i) => (
          <div key={b.label} style={{ flex: b.to - (i ? bands[i - 1].to : 0), background: b.color, opacity: 0.85, position: "relative" }}>
            <div style={{ position: "absolute", top: 28, left: 0, fontFamily: F.mono, fontSize: 14, color: C.muted, letterSpacing: "0.1em" }}>{b.label.toUpperCase()}</div>
          </div>
        ))}
        <div style={{ position: "absolute", left: `${45 * needle}%`, top: -10, width: 4, height: 42, background: C.ink, borderRadius: 2 }} />
      </div>
    </div>
  );
};

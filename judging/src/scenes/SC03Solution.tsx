import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Captions, SceneHeader, SfxTrack } from "../components/Chrome";
import { FaceCam, NameTag } from "../components/FaceCam";
import { easeInOut, FadeIn, Kicker, Marker, Paper, useProgress } from "../components/primitives";
import { EMITEN, FLAGGED } from "../data";
import { atWord } from "../timeline";
import { C, F } from "../theme";
import type { SceneProps } from "./util";

const ICONS: Record<string, React.ReactNode> = {
  analis: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
      <path d="M8 11h6M11 8v6" />
    </>
  ),
  manajer: (
    <>
      <path d="M3 3v18h18" />
      <path d="m7 15 4-4 3 3 6-6" />
    </>
  ),
  ritel: (
    <>
      <rect x="6" y="2" width="12" height="20" rx="2.5" />
      <path d="M10 18h4" />
    </>
  ),
};

const AUDIENCE = [
  { key: "analis", label: "Analis riset" },
  { key: "manajer", label: "Manajer investasi" },
  { key: "ritel", label: "Investor ritel" },
];

export const SC03Solution: React.FC<SceneProps> = ({ scene, index }) => {
  const line = scene.lines[0];
  const audienceAt = atWord(scene, 0, "untuk");
  const scanAt = atWord(scene, 0, "memindai");
  const filterAt = atWord(scene, 0, "hanya");
  const decideAt = atWord(scene, 0, "tinggal");

  return (
    <AbsoluteFill>
      <Paper>
        <SceneHeader scene={scene} index={index} />
        <FaceCam clip={line.clips[0]} who="Fathan" playFrom={line.from} playDur={line.dur} style={{ left: 96, top: 128, width: 600, height: 760 }} focus="35% 40%" />
        <NameTag who="Fathan" start={10} style={{ left: 120, top: 790 }} dark />

        <div style={{ position: "absolute", left: 770, top: 128, width: 1054 }}>
          <FadeIn start={4} dur={16}>
            <div style={{ fontFamily: F.serif, fontSize: 76, fontWeight: 600, color: C.ink, letterSpacing: "-0.02em", lineHeight: 1 }}>AFS Sentinel</div>
            <div style={{ fontFamily: F.serif, fontSize: 30, fontStyle: "italic", color: C.inkSoft, marginTop: 8 }}>
              pengawas dini laporan keuangan emiten BEI
            </div>
          </FadeIn>

          <Kicker size={15} style={{ marginTop: 36 }}>
            <FadeIn start={audienceAt} dur={12} y={8}>
              Dibangun untuk
            </FadeIn>
          </Kicker>
          <div style={{ display: "flex", gap: 18, marginTop: 14 }}>
            {AUDIENCE.map((a, i) => (
              <FadeIn key={a.key} start={audienceAt + 6 + i * 6} dur={16} style={{ flex: 1 }}>
                <div style={{ background: C.card, border: `1px solid ${C.line}`, borderRadius: 12, padding: "18px 20px", display: "flex", alignItems: "center", gap: 14 }}>
                  <svg width={38} height={38} viewBox="0 0 24 24" fill="none" stroke={C.ink} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
                    {ICONS[a.key]}
                  </svg>
                  <div style={{ fontFamily: F.sans, fontSize: 24, fontWeight: 600, color: C.ink }}>{a.label}</div>
                </div>
              </FadeIn>
            ))}
          </div>

          <Funnel scanAt={scanAt} filterAt={filterAt} />

          <div style={{ marginTop: 26, fontFamily: F.serif, fontSize: 46, color: C.ink, lineHeight: 1.1 }}>
            <FadeIn start={decideAt - 4} dur={14}>
              Tidak perlu lagi mencari —{" "}
              <Marker start={decideAt + 8} dur={16}>
                <i>tinggal memutuskan.</i>
              </Marker>
            </FadeIn>
          </div>
        </div>
      </Paper>
      <Captions lines={scene.lines} />
      <SfxTrack
        cues={[
          { at: audienceAt + 6, name: "tick", volume: 0.2 },
          { at: scanAt, name: "count", volume: 0.18, dur: 40 },
          { at: filterAt, name: "whoosh", volume: 0.3 },
          { at: decideAt + 8, name: "marker", volume: 0.35 },
        ]}
      />
    </AbsoluteFill>
  );
};

/** 33 ticker chips, a scan line, then only the flagged ones stay lit. */
const Funnel: React.FC<{ scanAt: number; filterAt: number }> = ({ scanAt, filterAt }) => {
  const frame = useCurrentFrame();
  const scan = useProgress(scanAt, 34, easeInOut);
  const filter = useProgress(filterAt, 18);
  const cols = 11;
  const chipW = 86;
  const chipH = 44;
  return (
    <div style={{ marginTop: 34, position: "relative" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <Kicker size={15} color={C.ink}>
          <FadeIn start={scanAt - 6} dur={12} y={8}>
            33 emiten non-keuangan BEI · otomatis · hanya yang berisiko dikirim
          </FadeIn>
        </Kicker>
        <div style={{ fontFamily: F.mono, fontSize: 15, color: C.red, opacity: filter }}>{FLAGGED.length} perlu diperiksa</div>
      </div>
      <div style={{ position: "relative", marginTop: 14, display: "grid", gridTemplateColumns: `repeat(${cols}, ${chipW}px)`, gap: 10 }}>
        {EMITEN.map((t, i) => {
          const col = i % cols;
          const seen = scan * (cols + 1) > col;
          const flagged = FLAGGED.includes(t);
          const appear = interpolate(frame, [scanAt - 10 + i * 0.6, scanAt + i * 0.6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const dim = flagged ? 1 : 1 - filter * 0.72;
          return (
            <div
              key={t}
              style={{
                height: chipH,
                borderRadius: 6,
                display: "grid",
                placeItems: "center",
                fontFamily: F.mono,
                fontSize: 17,
                fontWeight: 600,
                background: flagged && filter > 0 ? C.red : seen ? C.card : "transparent",
                color: flagged && filter > 0 ? "#FBF8F2" : C.ink,
                border: `1px solid ${flagged && filter > 0 ? C.red : C.lineStrong}`,
                opacity: appear * dim,
                transform: `scale(${flagged ? 1 + filter * 0.04 : 1})`,
              }}
            >
              {t}
            </div>
          );
        })}
        {scan > 0 && scan < 1 && (
          <div
            style={{
              position: "absolute",
              top: -8,
              bottom: -8,
              left: scan * (cols * (chipW + 10)),
              width: 3,
              background: C.red,
              boxShadow: `0 0 18px ${C.red}`,
            }}
          />
        )}
      </div>
    </div>
  );
};

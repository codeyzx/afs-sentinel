import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Captions, SceneHeader, SfxTrack } from "../components/Chrome";
import { FaceCam, NameTag } from "../components/FaceCam";
import { easeInOut, FadeIn, Kicker, Marker, Paper, RiseWords, useProgress } from "../components/primitives";
import { EMITEN } from "../data";
import { atWord } from "../timeline";
import { C, F, FPS } from "../theme";
import type { SceneProps } from "./util";

const lerp = (a: number, b: number, p: number) => a + (b - a) * p;

export const SC02Intro: React.FC<SceneProps> = ({ scene, index }) => {
  const line = scene.lines[0];
  const yahyaAt = atWord(scene, 0, "Yahya");
  const aisAt = atWord(scene, 0, "Ais");
  const problemAt = atWord(scene, 0, "Masalahnya");
  const reactions = scene.def.reactions!;

  // grid → Fathan takes the left column
  const split = useProgress(problemAt - 6, 26, easeInOut);
  const cardW = 520;
  const cardH = 650;
  const gap = 36;
  const gridLeft = (1920 - (cardW * 3 + gap * 2)) / 2;
  const top = 170;

  const slot = (i: number) => ({ left: gridLeft + i * (cardW + gap), top, width: cardW, height: cardH });
  const fathanBox = {
    left: lerp(slot(0).left, 96, split),
    top: lerp(top, 150, split),
    width: lerp(cardW, 620, split),
    height: lerp(cardH, 760, split),
  };
  const sideOut = (i: number) => ({ ...slot(i), left: slot(i).left + split * 1400, opacity: 1 - split });

  return (
    <AbsoluteFill>
      <Paper>
        <SceneHeader scene={scene} index={index} />

        {(["Yahya", "Ais"] as const).map((who, k) => {
          const r = reactions[k];
          const s = sideOut(k + 1);
          const play = k === 0 ? yahyaAt : aisAt;
          return (
            <React.Fragment key={who}>
              <FaceCam clip={r.clip} who={who} playFrom={play} playDur={Math.round(r.target * FPS)} style={{ ...s }} />
              <NameTag who={who} start={play} style={{ left: s.left + 24, top: s.top + s.height - 100, opacity: s.opacity }} dark />
            </React.Fragment>
          );
        })}

        <FaceCam clip={line.clips[0]} who="Fathan" playFrom={line.from} playDur={line.dur} style={fathanBox} />
        <NameTag who="Fathan" start={atWord(scene, 0, "Fathan")} style={{ left: fathanBox.left + 24, top: fathanBox.top + fathanBox.height - 100 }} dark />

        {split > 0 && <Problem start={problemAt + 10} />}

        <FadeIn start={8} dur={14} style={{ position: "absolute", left: 96, top: 92 }}>
          <Kicker size={18} color={C.ink}>
            Tim JTKTOP10 · Sectors Hackathon 2026 · Track 2
          </Kicker>
        </FadeIn>
      </Paper>
      <Captions lines={scene.lines} />
      <SfxTrack
        cues={[
          { at: atWord(scene, 0, "Fathan"), name: "tick", volume: 0.25 },
          { at: yahyaAt, name: "tick", volume: 0.25 },
          { at: aisAt, name: "tick", volume: 0.25 },
          { at: problemAt - 6, name: "whoosh", volume: 0.35 },
          { at: problemAt + 40, name: "paper", volume: 0.3 },
        ]}
      />
    </AbsoluteFill>
  );
};

/** Reports pile up faster than an analyst can read them. */
const Problem: React.FC<{ start: number }> = ({ start }) => {
  const frame = useCurrentFrame();
  const cards = EMITEN.slice(0, 24);
  return (
    <div style={{ position: "absolute", left: 790, top: 150, width: 1034, height: 760 }}>
      <div style={{ position: "absolute", left: 0, top: 0, right: 0, height: 470 }}>
        {cards.map((t, i) => {
          const s = start + 8 + i * 3;
          const p = interpolate(frame, [s, s + 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const col = i % 6;
          const row = Math.floor(i / 6);
          const rot = ((i * 37) % 9) - 4;
          return (
            <div
              key={t}
              style={{
                position: "absolute",
                left: col * 168 + (row % 2) * 30,
                top: row * 104,
                width: 150,
                height: 92,
                background: C.card,
                border: `1px solid ${C.line}`,
                borderRadius: 6,
                boxShadow: "0 6px 14px rgba(40,28,10,0.12)",
                transform: `translateY(${(1 - p) * -60}px) rotate(${rot * p}deg)`,
                opacity: p,
                padding: "10px 12px",
                boxSizing: "border-box",
              }}
            >
              <div style={{ fontFamily: F.mono, fontSize: 18, fontWeight: 600, color: C.ink }}>{t}</div>
              <div style={{ fontFamily: F.mono, fontSize: 11, color: C.muted, marginTop: 4, letterSpacing: "0.08em" }}>LAP. KEUANGAN Q2</div>
              <div style={{ marginTop: 8, height: 3, width: "80%", background: C.line }} />
              <div style={{ marginTop: 5, height: 3, width: "60%", background: C.line }} />
            </div>
          );
        })}
      </div>
      <div style={{ position: "absolute", left: 0, top: 500 }}>
        <RiseWords
          text="Ratusan laporan per kuartal."
          start={start + 30}
          style={{ fontFamily: F.serif, fontSize: 68, fontWeight: 500, color: C.ink, letterSpacing: "-0.015em", lineHeight: 1.05 }}
        />
        <div style={{ fontFamily: F.serif, fontSize: 68, fontStyle: "italic", color: C.ink, marginTop: 6, lineHeight: 1.05 }}>
          <FadeIn start={start + 52} dur={14} y={16}>
            Waktu analis{" "}
            <Marker start={start + 66} color={C.marker}>
              terbatas.
            </Marker>
          </FadeIn>
        </div>
      </div>
    </div>
  );
};

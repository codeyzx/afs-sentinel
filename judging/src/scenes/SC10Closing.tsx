import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Captions, SfxTrack } from "../components/Chrome";
import { FaceCam, NameTag } from "../components/FaceCam";
import { easeInOut, Kicker, Marker, Paper, useProgress } from "../components/primitives";
import { END_CARD } from "../media";
import type { Person } from "../script";
import { C, F } from "../theme";
import { type SceneProps } from "./util";

const ORDER: Person[] = ["Fathan", "Yahya", "Ais"];

export const SC10Closing: React.FC<SceneProps> = ({ scene }) => {
  const frame = useCurrentFrame();
  const [lf, la, ly, all] = scene.lines;
  const solo: Record<Person, typeof lf> = { Fathan: lf, Ais: la, Yahya: ly };
  const card = useProgress(all.from - 4, 26, easeInOut);

  const cardW = 520;
  const cardH = 650;
  const gap = 36;
  const gridLeft = (1920 - (cardW * 3 + gap * 2)) / 2;
  // grid → strip of three at the bottom-right of the end card
  const small = { w: 300, h: 260, gap: 18 };
  const box = (i: number) => {
    const a = { left: gridLeft + i * (cardW + gap), top: 170, width: cardW, height: cardH };
    const b = { left: 1920 - 96 - (3 - i) * small.w - (2 - i) * small.gap, top: 640, width: small.w, height: small.h };
    return {
      left: a.left + (b.left - a.left) * card,
      top: a.top + (b.top - a.top) * card,
      width: a.width + (b.width - a.width) * card,
      height: a.height + (b.height - a.height) * card,
    };
  };
  const speaking = scene.lines.find((l) => frame >= l.from && frame < l.from + l.dur);

  return (
    <AbsoluteFill>
      <Paper>
        {ORDER.map((who, i) => {
          const b = box(i);
          const group = frame >= all.from - 4;
          const clip = group ? all.clips[ORDER.indexOf(who)] : solo[who].clips[0];
          const l = group ? all : solo[who];
          const active = speaking && (speaking.who === who || speaking.who === "Bertiga");
          return (
            <React.Fragment key={who}>
              <FaceCam
                key={clip}
                clip={clip}
                who={who}
                playFrom={l.from}
                playDur={l.dur}
                style={{ ...b, opacity: active || !speaking ? 1 : 0.62 }}
                border={active ? `3px solid ${C.red}` : undefined}
                compact={card > 0.5}
              />
              {card < 0.3 && <NameTag who={who} start={6 + i * 4} style={{ left: b.left + 24, top: b.top + b.height - 100, opacity: 1 - card / 0.3 }} dark />}
            </React.Fragment>
          );
        })}

        {card > 0 && <EndCard p={card} start={all.from} />}
      </Paper>
      <Captions lines={scene.lines} />
      <SfxTrack
        cues={[
          { at: all.from - 4, name: "whoosh", volume: 0.3 },
          { at: all.from + 30, name: "marker", volume: 0.3 },
          { at: all.from + 50, name: "impact-soft", volume: 0.35 },
        ]}
      />
    </AbsoluteFill>
  );
};

const EndCard: React.FC<{ p: number; start: number }> = ({ p, start }) => {
  const frame = useCurrentFrame();
  const disclaimer = interpolate(frame, [start + 40, start + 56], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 96, top: 120, width: 1728, opacity: p, transform: `translateY(${(1 - p) * 30}px)` }}>
      <Kicker size={18} color={C.red}>
        Sectors Hackathon 2026 · Track 2 · Automation & Workflows
      </Kicker>
      <div style={{ fontFamily: F.serif, fontSize: 170, fontWeight: 600, color: C.ink, letterSpacing: "-0.035em", lineHeight: 0.95, marginTop: 18 }}>AFS Sentinel</div>
      <div style={{ fontFamily: F.serif, fontSize: 58, fontStyle: "italic", color: C.ink, marginTop: 18 }}>
        <Marker start={start + 30} dur={18}>
          Peringatan dini, sebelum terlambat.
        </Marker>
      </div>
      <div style={{ marginTop: 56, display: "grid", gridTemplateColumns: "auto 1fr", rowGap: 14, columnGap: 28, width: 760 }}>
        {[
          ["Powered by", "Sectors API"],
          ["Kode", END_CARD.github ?? "⟨link GitHub belum diisi — media.ts › END_CARD⟩"],
          ["Coba", END_CARD.app],
          ["Tim", "JTKTOP10 · Fathan · Yahya · Ais"],
        ].map(([k, v]) => (
          <React.Fragment key={k}>
            <Kicker size={16}>{k}</Kicker>
            <div style={{ fontFamily: F.mono, fontSize: 22, color: v.startsWith("⟨") ? C.red : C.ink }}>{v}</div>
          </React.Fragment>
        ))}
      </div>
      <div style={{ position: "absolute", top: 820, left: 0, opacity: disclaimer, fontFamily: F.sans, fontSize: 20, color: C.muted }}>
        Alat analisis & informasi, bukan nasihat investasi.
      </div>
    </div>
  );
};

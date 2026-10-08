import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { SfxTrack } from "../components/Chrome";
import { ease, easeInOut, FadeIn, Grain, Kicker, Marker, Paper, Stamp, useProgress, useSpring } from "../components/primitives";
import { EMITEN, FLAGGED, RULES } from "../data";
import { C, F } from "../theme";

/**
 * Cold open, before the hook: an Audit Run scans the universe on a dark desk, the flagged
 * Emiten turn red, then the case file lands, gets stamped, and flips open onto the hook's black.
 */
export const Intro: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const folderIn = useSpring(66, { damping: 16, stiffness: 120, mass: 0.9 } as never);
  const flip = useProgress(dur - 44, 30, easeInOut);
  const push =
    interpolate(frame, [66, dur - 44], [1, 1.06], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) +
    interpolate(frame, [dur - 24, dur], [0, 0.5], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeInOut });
  const fieldDim = interpolate(frame, [60, 90], [1, 0.35], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const fadeAll = interpolate(frame, [dur - 18, dur - 4], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: C.night }}>
      <AbsoluteFill style={{ opacity: fieldDim * fadeAll }}>
        <TickerField />
      </AbsoluteFill>

      {/* HUD */}
      <AbsoluteFill style={{ opacity: fadeAll }}>
        <div style={{ position: "absolute", left: 96, top: 54, display: "flex", gap: 18, alignItems: "center" }}>
          <div style={{ width: 12, height: 12, borderRadius: 6, background: C.red, opacity: Math.floor(frame / 12) % 2 ? 0.25 : 1 }} />
          <Kicker size={16} color="rgba(241,236,226,0.75)">
            Audit Run · {EMITEN.length} emiten · Sectors API
          </Kicker>
        </div>
        <div style={{ position: "absolute", right: 96, top: 54 }}>
          <Kicker size={16} color="rgba(241,236,226,0.5)">
            Sectors Hackathon 2026 · Track 2
          </Kicker>
        </div>
      </AbsoluteFill>

      {/* the case file */}
      <AbsoluteFill style={{ perspective: 2200, opacity: fadeAll }}>
        <div
          style={{
            position: "absolute",
            left: 330,
            top: 150,
            width: 1260,
            height: 780,
            transform: `translateY(${(1 - folderIn) * 900}px) rotate(${(1 - folderIn) * -6 - 1.2}deg) scale(${push})`,
            transformStyle: "preserve-3d",
          }}
        >
          {/* inside of the folder, seen once the cover flips */}
          <div style={{ position: "absolute", inset: 0, background: C.manilaDeep, borderRadius: 14, boxShadow: "0 40px 90px rgba(0,0,0,0.55)" }}>
            <div style={{ position: "absolute", inset: 40, background: C.card, borderRadius: 6, padding: "56px 70px" }}>
              <Kicker size={17} color={C.red}>
                Lampiran A · Kasus uji
              </Kicker>
              <div style={{ fontFamily: F.serif, fontSize: 96, fontWeight: 600, color: C.ink, letterSpacing: "-0.02em", marginTop: 28 }}>WSKT</div>
              <div style={{ fontFamily: F.serif, fontSize: 40, fontStyle: "italic", color: C.inkSoft, marginTop: 6 }}>Waskita Karya (Persero) Tbk</div>
              <div style={{ height: 1, background: C.lineStrong, margin: "40px 0 30px" }} />
              <div style={{ fontFamily: F.mono, fontSize: 28, color: C.ink, lineHeight: 1.7 }}>
                Peristiwa&nbsp;&nbsp;Suspensi perdagangan BEI
                <br />
                Tanggal&nbsp;&nbsp;&nbsp;8 Mei 2023
              </div>
            </div>
          </div>
          <div
            style={{
              position: "absolute",
              inset: 0,
              transformOrigin: "left center",
              transform: `rotateY(${-flip * 160}deg)`,
              backfaceVisibility: "hidden",
            }}
          >
            <Cover frame={frame} />
          </div>
        </div>
      </AbsoluteFill>

      <Grain opacity={0.45} />

      <SfxTrack
        cues={[
          ...FLAGGED.map((_, i) => ({ at: 14 + i * 4, name: "tick", volume: 0.18 })),
          { at: 50, name: "riser", volume: 0.45 },
          { at: 64, name: "impact-soft", volume: 0.5 },
          { at: 70, name: "paper", volume: 0.5 },
          { at: 104, name: "type", volume: 0.3 },
          { at: 134, name: "stamp", volume: 0.75 },
          { at: dur - 48, name: "whoosh-big", volume: 0.4 },
        ]}
      />
    </AbsoluteFill>
  );
};

const Cover: React.FC<{ frame: number }> = ({ frame }) => {
  const title = useProgress(84, 22);
  return (
    <div style={{ position: "absolute", inset: 0 }}>
      {/* tab */}
      <div style={{ position: "absolute", right: 90, top: -46, width: 300, height: 60, background: C.manila, borderRadius: "14px 14px 0 0" }}>
        <Kicker size={15} color={C.inkSoft} style={{ padding: "16px 24px" }}>
          AFS-2026-T2
        </Kicker>
      </div>
      <Paper tone={C.manila} rules={false}>
        <div style={{ position: "absolute", left: 80, top: 70, right: 80 }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <Kicker size={17} color={C.inkSoft}>
              Berkas perkara · Forensik laporan keuangan
            </Kicker>
            <Kicker size={17} color={C.red}>
              Rahasia · Untuk juri
            </Kicker>
          </div>
          <div style={{ height: 2, background: C.ink, opacity: 0.6, marginTop: 18 }} />

          <div
            style={{
              fontFamily: F.serif,
              fontSize: 168,
              fontWeight: 600,
              color: C.ink,
              letterSpacing: "-0.035em",
              lineHeight: 0.95,
              marginTop: 70,
              opacity: title,
              transform: `translateY(${(1 - title) * 30}px)`,
            }}
          >
            AFS Sentinel
          </div>
          <FadeIn start={100} dur={16}>
            <div style={{ fontFamily: F.serif, fontSize: 46, fontStyle: "italic", color: C.inkSoft, marginTop: 16 }}>
              Sistem peringatan dini <Marker start={112} dur={14}>kesehatan keuangan</Marker> emiten IDX
            </div>
          </FadeIn>

          <div style={{ marginTop: 64, display: "grid", gridTemplateColumns: "220px 1fr", rowGap: 14, width: 760 }}>
            {[
              ["Subjek", `${EMITEN.length} emiten non-keuangan`],
              ["Metode", `${RULES.length} aturan forensik`],
              ["Pengawas", "JTKTOP10"],
            ].map(([k, v], i) => (
              <React.Fragment key={k}>
                <FadeIn start={108 + i * 5} dur={12} y={10}>
                  <Kicker size={16} color={C.inkSoft}>
                    {k}
                  </Kicker>
                </FadeIn>
                <FadeIn start={108 + i * 5} dur={12} y={10}>
                  <div style={{ fontFamily: F.mono, fontSize: 24, color: C.ink, borderBottom: `1px dashed ${C.lineStrong}`, paddingBottom: 4 }}>{v}</div>
                </FadeIn>
              </React.Fragment>
            ))}
          </div>
        </div>
        <div style={{ position: "absolute", right: 110, bottom: 110 }}>
          <Stamp start={134} size={64} rotate={-9}>
            Diawasi
          </Stamp>
        </div>
        {/* a coffee-ring of use, faint */}
        <div style={{ position: "absolute", right: 380, top: 120, width: 170, height: 170, borderRadius: "50%", border: "6px solid rgba(110,70,30,0.08)", opacity: frame > 0 ? 1 : 0 }} />
      </Paper>
    </div>
  );
};

/** Every Emiten in the universe as a faint grid; a scan line passes and leaves the flagged ones red. */
const TickerField: React.FC = () => {
  const frame = useCurrentFrame();
  const cols = 11;
  const cellW = 150;
  const cellH = 120;
  const rows = Math.ceil(EMITEN.length / cols);
  const left = (1920 - cols * cellW) / 2;
  const top = 300;
  const scanY = interpolate(frame, [6, 58], [top - 60, top + rows * cellH + 40], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  const drift = frame * 0.35;
  return (
    <AbsoluteFill style={{ transform: `translateY(${-drift}px)` }}>
      {EMITEN.map((t, i) => {
        const x = left + (i % cols) * cellW;
        const y = top + Math.floor(i / cols) * cellH;
        const hit = scanY > y + 20;
        const flagged = FLAGGED.includes(t) && hit;
        const appear = interpolate(frame, [i * 0.6, i * 0.6 + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return (
          <div key={t} style={{ position: "absolute", left: x, top: y, width: cellW - 18, opacity: appear }}>
            <div style={{ fontFamily: F.mono, fontSize: 30, fontWeight: 600, color: flagged ? C.red : "rgba(241,236,226,0.32)", letterSpacing: "0.04em" }}>
              {flagged ? "● " : ""}
              {t}
            </div>
            <div style={{ height: 3, marginTop: 10, background: flagged ? C.red : "rgba(241,236,226,0.12)", width: `${30 + ((i * 37) % 70)}%` }} />
          </div>
        );
      })}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: scanY,
          height: 2,
          background: C.red,
          boxShadow: `0 0 24px 6px rgba(217,58,43,0.45)`,
          opacity: interpolate(frame, [52, 62], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}
      />
    </AbsoluteFill>
  );
};

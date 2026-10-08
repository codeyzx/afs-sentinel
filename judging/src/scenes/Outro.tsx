import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { SfxTrack } from "../components/Chrome";
import { CountUp, easeInOut, FadeIn, Grain, Kicker, Paper, RiseWords, Stamp, useProgress } from "../components/primitives";
import { EMITEN, FLAGGED, RULES } from "../data";
import { END_CARD } from "../media";
import { PEOPLE, type Person } from "../script";
import { C, F } from "../theme";

/** Frames the outro starts before SC10 ends: the cover closes over the end card. */
export const OUTRO_OVERLAP = 16;

const ORDER: Person[] = ["Fathan", "Yahya", "Ais"];

/**
 * After the end card: the case file closes over it with the findings on its cover, stamped
 * "still watching", then the desk goes dark for the closing line and the credits.
 */
export const Outro: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const close = useProgress(0, OUTRO_OVERLAP + 6, easeInOut);
  const NIGHT = 150;
  const night = useProgress(NIGHT, 20, easeInOut);
  const coverOut = interpolate(frame, [NIGHT - 4, NIGHT + 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeInOut });
  const end = interpolate(frame, [dur - 26, dur - 4], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: C.night, opacity: night }} />

      {/* cover slides down over the end card, later lifts away into the dark */}
      <AbsoluteFill
        style={{
          transform: `translateY(${(close - 1) * 105 + coverOut * -8}%) scale(${1 - coverOut * 0.12})`,
          opacity: 1 - coverOut,
          boxShadow: "0 30px 80px rgba(0,0,0,0.45)",
        }}
      >
        <Paper tone={C.manila} rules={false}>
          <div style={{ position: "absolute", left: 120, top: 110, right: 120 }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <Kicker size={18} color={C.inkSoft}>
                Berkas AFS-2026-T2 · Ringkasan temuan
              </Kicker>
              <Kicker size={18} color={C.inkSoft}>
                Data · Sectors API
              </Kicker>
            </div>
            <div style={{ height: 2, background: C.ink, opacity: 0.6, marginTop: 18 }} />
            <div style={{ fontFamily: F.serif, fontSize: 120, fontWeight: 600, color: C.ink, letterSpacing: "-0.035em", lineHeight: 1, marginTop: 56 }}>AFS Sentinel</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 36, marginTop: 64 }}>
              {[
                { n: EMITEN.length, label: "emiten dipindai\nsetiap Audit Run" },
                { n: RULES.length, label: "aturan forensik\nper laporan" },
                { n: FLAGGED.length, label: "Incident terbuka\ndi produksi" },
                { n: 25, label: "bulan lebih awal\nmenandai WSKT" },
              ].map((s, i) => (
                <FadeIn key={s.label} start={22 + i * 7} dur={14}>
                  <div style={{ borderTop: `3px solid ${i === 3 ? C.red : C.ink}`, paddingTop: 22 }}>
                    <div style={{ fontFamily: F.serif, fontSize: 150, fontWeight: 600, lineHeight: 1, letterSpacing: "-0.03em", color: i === 3 ? C.red : C.ink }}>
                      <CountUp to={s.n} start={24 + i * 7} dur={26} />
                    </div>
                    <div style={{ fontFamily: F.sans, fontSize: 26, color: C.inkSoft, marginTop: 14, whiteSpace: "pre-line", lineHeight: 1.3 }}>{s.label}</div>
                  </div>
                </FadeIn>
              ))}
            </div>
          </div>
          <div style={{ position: "absolute", left: 120, bottom: 150, display: "flex", alignItems: "center", gap: 60 }}>
            <Stamp start={86} size={60} rotate={-6}>
              Berkas ditutup
            </Stamp>
            <Stamp start={112} size={60} rotate={4}>
              Pengawasan berlanjut
            </Stamp>
          </div>
        </Paper>
      </AbsoluteFill>

      {/* dark: closing line, credits, sign-off */}
      {frame >= NIGHT && (
        <AbsoluteFill style={{ opacity: end }}>
          <div style={{ position: "absolute", left: 160, right: 160, top: 250 }}>
            <RiseWords
              text="Tanda bahaya selalu tertulis lebih dulu."
              start={NIGHT + 14}
              stagger={3}
              style={{ fontFamily: F.serif, fontSize: 92, fontWeight: 500, color: C.paper, letterSpacing: "-0.02em", lineHeight: 1.05 }}
            />
            <RiseWords
              text="Sekarang, ada yang membacanya."
              start={NIGHT + 40}
              stagger={3}
              style={{ fontFamily: F.serif, fontSize: 92, fontStyle: "italic", color: C.red, letterSpacing: "-0.02em", lineHeight: 1.05, marginTop: 8 }}
              wordStyle={() => ({ fontWeight: 400 })}
            />
          </div>

          <div style={{ position: "absolute", left: 160, right: 160, top: 610, display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 40 }}>
            {ORDER.map((who, i) => (
              <FadeIn key={who} start={NIGHT + 78 + i * 6} dur={16} y={16}>
                <div style={{ borderTop: "1px solid rgba(241,236,226,0.3)", paddingTop: 18 }}>
                  <Kicker size={15} color="rgba(241,236,226,0.55)">
                    {PEOPLE[who].role}
                  </Kicker>
                  <div style={{ fontFamily: F.serif, fontSize: 52, color: C.paper, marginTop: 8 }}>{PEOPLE[who].full}</div>
                </div>
              </FadeIn>
            ))}
          </div>

          <FadeIn start={NIGHT + 104} dur={18} y={10}>
            <div style={{ position: "absolute", left: 160, right: 160, top: 840, display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
              <div>
                <Kicker size={16} color="rgba(241,236,226,0.55)">
                  JTKTOP10 · Sectors Hackathon 2026 · Track 2 · Data oleh Sectors API
                </Kicker>
                <div style={{ fontFamily: F.mono, fontSize: 24, color: C.paper, marginTop: 12 }}>
                  {END_CARD.github} · {END_CARD.app}
                </div>
              </div>
              <Watching frame={frame} />
            </div>
          </FadeIn>
          <FadeIn start={NIGHT + 120} dur={18} y={0}>
            <div style={{ position: "absolute", left: 160, top: 990, fontFamily: F.sans, fontSize: 18, color: "rgba(241,236,226,0.45)" }}>
              Alat analisis & informasi, bukan nasihat investasi.
            </div>
          </FadeIn>
        </AbsoluteFill>
      )}

      {frame >= NIGHT && <Grain opacity={0.45} />}

      <SfxTrack
        cues={[
          { at: 0, name: "whoosh", volume: 0.3 },
          { at: OUTRO_OVERLAP, name: "paper", volume: 0.5 },
          { at: 86, name: "stamp", volume: 0.7 },
          { at: 112, name: "stamp", volume: 0.7 },
          { at: NIGHT - 6, name: "whoosh-big", volume: 0.3 },
          { at: NIGHT + 14, name: "impact-soft", volume: 0.4 },
        ]}
      />
    </AbsoluteFill>
  );
};

const Watching: React.FC<{ frame: number }> = ({ frame }) => {
  const pulse = (Math.sin(frame / 7) + 1) / 2;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
      <div style={{ position: "relative", width: 16, height: 16 }}>
        <div style={{ position: "absolute", inset: 0, borderRadius: 8, background: C.red }} />
        <div style={{ position: "absolute", inset: -10 * pulse, borderRadius: 30, border: `2px solid ${C.red}`, opacity: 1 - pulse }} />
      </div>
      <Kicker size={18} color={C.paper}>
        AFS Sentinel · memantau
      </Kicker>
    </div>
  );
};

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { shake, SfxTrack, Ticks } from "../components/Chrome";
import { DrawCircle, ease, easeInOut, FadeIn, Grain, Kicker, Marker, Paper, RiseWords, Stamp, useProgress, useSpring } from "../components/primitives";
import { EMITEN } from "../data";
import { C, F } from "../theme";
import { w } from "../vo";

/** One token that slams in: big scale → 1 with a hard settle. */
const Slam: React.FC<{ at: number; children: React.ReactNode; style?: React.CSSProperties; from?: "scale" | "left" | "up" }> = ({ at, children, style, from = "scale" }) => {
  const frame = useCurrentFrame();
  const s = useSpring(at, { damping: 14, stiffness: 260, mass: 0.6 } as never);
  if (frame < at) return <span style={{ ...style, opacity: 0 }}>{children}</span>;
  const tf =
    from === "scale" ? `scale(${interpolate(s, [0, 1], [2.2, 1])})` : from === "left" ? `translateX(${(1 - s) * -220}px)` : `translateY(${(1 - s) * 160}px)`;
  return <span style={{ display: "inline-block", transform: tf, opacity: Math.min(1, (frame - at) / 3), ...style }}>{children}</span>;
};

// ── 1 · Cold open ────────────────────────────────────────────────────────────
export const S1ColdOpen: React.FC = () => {
  const frame = useCurrentFrame();
  const d8 = w(1, "Delapan");
  const dMei = w(1, "Mei");
  const d2023 = w(1, "dua");
  const bursa = w(1, "Bursa");
  const waskita = w(1, "Waskita");
  const lift = useProgress(bursa - 4, 18, easeInOut);
  const shk = [d8, dMei, d2023, waskita + 6].map((a) => shake(frame, a, 12)).find((s) => s !== "none") ?? "none";
  return (
    <AbsoluteFill style={{ background: C.night, transform: shk }}>
      <div style={{ position: "absolute", left: 140, top: 110 }}>
        <FadeIn start={2} dur={12} y={6}>
          <Kicker size={20} color="rgba(241,236,226,0.55)">
            Bursa Efek Indonesia · Senin, 8 Mei 2023
          </Kicker>
        </FadeIn>
      </div>
      <div style={{ position: "absolute", left: 140, top: interpolate(lift, [0, 1], [330, 220]) }}>
        <div style={{ fontFamily: F.serif, fontSize: interpolate(lift, [0, 1], [300, 210]), fontWeight: 600, color: C.paper, letterSpacing: "-0.04em", lineHeight: 0.9, display: "flex", gap: "0.22em" }}>
          <Slam at={d8}>8</Slam>
          <Slam at={dMei} from="left" style={{ fontStyle: "italic", fontWeight: 400 }}>
            Mei
          </Slam>
          <Slam at={d2023} from="up" style={{ color: C.red }}>
            2023
          </Slam>
        </div>
        <div style={{ marginTop: 40, display: "flex", alignItems: "center", gap: 22 }}>
          <div style={{ width: interpolate(lift, [0, 1], [0, 60]), height: 3, background: C.red }} />
          <RiseWords
            text="perdagangan saham WSKT dihentikan."
            start={w(1, "menghentikan")}
            stagger={5}
            style={{ fontFamily: F.serif, fontSize: 74, color: C.paper, letterSpacing: "-0.01em" }}
            wordStyle={(x) => (x === "WSKT" ? { fontFamily: F.mono, fontWeight: 600, color: C.night, background: C.red, padding: "0 12px", borderRadius: 6, fontSize: 62 } : undefined)}
          />
        </div>
      </div>
      <div style={{ position: "absolute", right: 170, top: 640 }}>
        <Stamp start={waskita + 6} size={64} color={C.red} blend="normal">
          Suspensi
        </Stamp>
      </div>
      <Grain opacity={0.5} />
      <SfxTrack
        cues={[
          { at: d8, name: "slam", volume: 0.7 },
          { at: dMei, name: "slam", volume: 0.55 },
          { at: d2023, name: "impact", volume: 0.6, dur: 90 },
          { at: w(1, "menghentikan"), name: "type-loop", volume: 0.25, dur: 30 },
          { at: waskita + 6, name: "stamp", volume: 0.8 },
          { at: waskita + 6, name: "subdrop", volume: 0.5 },
        ]}
      />
    </AbsoluteFill>
  );
};

// ── 2 · Twist ────────────────────────────────────────────────────────────────
export const S2Twist: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const tapi = w(2, "Tapi");
  const semua = w(2, "semuanya");
  const up = useProgress(tapi - 2, 16, easeInOut);
  const shove = useProgress(semua - 2, 16, easeInOut);
  const stackStyle: React.CSSProperties = { fontFamily: F.serif, fontSize: 104, lineHeight: 1.02, color: C.ink, letterSpacing: "-0.025em" };
  return (
    <AbsoluteFill>
      <Paper>
        <Ticks index={1} />
        {/* the wall of 33 reports */}
        {up > 0 &&
          EMITEN.map((t, i) => {
            const col = i % 8;
            const row = Math.floor(i / 8);
            const s = tapi + 2 + i * 0.9;
            const p = interpolate(frame, [s, s + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
            const cx = 120 + col * 216 + (row % 2) * 60;
            const cy = 120 + row * 172;
            const dx = (cx + 90 - 960) * shove * 1.4;
            const dy = (cy + 50 - 470) * shove * 1.6;
            const rot = ((i * 47) % 11) - 5;
            return (
              <div
                key={t}
                style={{
                  position: "absolute",
                  left: cx,
                  top: cy,
                  width: 180,
                  height: 112,
                  background: C.card,
                  border: `1px solid ${C.line}`,
                  borderRadius: 6,
                  boxShadow: "0 8px 18px rgba(40,28,10,0.14)",
                  transform: `translate(${dx}px, ${dy + (1 - p) * -80}px) rotate(${rot * p}deg)`,
                  opacity: p * (1 - shove * 0.55),
                  padding: "12px 14px",
                  boxSizing: "border-box",
                }}
              >
                <div style={{ fontFamily: F.mono, fontSize: 24, fontWeight: 600, color: C.ink }}>{t}</div>
                <div style={{ fontFamily: F.mono, fontSize: 12, color: C.muted, marginTop: 4, letterSpacing: "0.1em" }}>LAP. KEUANGAN</div>
                <div style={{ marginTop: 10, height: 3, width: "80%", background: C.line }} />
                <div style={{ marginTop: 6, height: 3, width: "55%", background: C.line }} />
              </div>
            );
          })}
        <div style={{ position: "absolute", left: 140, top: 190 - up * 120, opacity: (1 - up * 0.85) * (1 - shove) }}>
          <RiseWords text="tandanya sudah ada" start={w(2, "tandanya")} stagger={4} style={stackStyle} />
          <RiseWords text="di laporan keuangan," start={w(2, "di")} stagger={4} style={{ ...stackStyle, fontStyle: "italic", color: C.inkSoft }} />
          <div style={{ ...stackStyle, marginTop: 6 }}>
            <FadeIn start={w(2, "bertahun-tahun") - 2} dur={8} y={30}>
              <Marker start={w(2, "bertahun-tahun") + 2} dur={12} color={C.red}>
                bertahun-tahun
              </Marker>{" "}
              sebelumnya.
            </FadeIn>
          </div>
        </div>
        {shove > 0 && (
          <div style={{ position: "absolute", left: 0, right: 0, top: 360, textAlign: "center", opacity: shove, transform: `scale(${0.9 + shove * 0.1})` }}>
            <div style={{ fontFamily: F.serif, fontSize: 112, color: C.ink, letterSpacing: "-0.025em", lineHeight: 1.05 }}>
              siapa yang sempat
              <br />
              <span style={{ fontStyle: "italic" }}>
                membaca <Marker start={semua + 8}>semuanya?</Marker>
              </span>
            </div>
          </div>
        )}
      </Paper>
      <SfxTrack
        cues={[
          { at: w(2, "bertahun-tahun"), name: "marker", volume: 0.4 },
          { at: tapi, name: "paper", volume: 0.5 },
          { at: tapi + 8, name: "paper", volume: 0.4 },
          { at: tapi + 18, name: "paper", volume: 0.35 },
          { at: semua - 4, name: "whoosh-big", volume: 0.45 },
          { at: dur - 12, name: "reverse", volume: 0.35 },
        ]}
      />
    </AbsoluteFill>
  );
};

// ── 3 · AFS Sentinel ─────────────────────────────────────────────────────────
export const S3Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const afs = w(3, "AFS");
  const peng = w(3, "pengawas");
  const untuk = w(3, "untuk");
  const name = "AFS Sentinel";
  const zoom = interpolate(frame, [0, 190], [1.06, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <Paper>
        <Ticks index={2} />
        <div style={{ position: "absolute", inset: 0, transform: `scale(${zoom})` }}>
          <div style={{ position: "absolute", left: 140, top: 250 }}>
            <FadeIn start={4} dur={10} y={6}>
              <Kicker size={20} color={C.red}>
                Berkas dibuka · pengawas forensik
              </Kicker>
            </FadeIn>
            <div style={{ fontFamily: F.serif, fontSize: 250, fontWeight: 600, color: C.ink, letterSpacing: "-0.045em", lineHeight: 0.95, marginTop: 20, display: "flex" }}>
              {name.split("").map((ch, i) => {
                const s = afs + i * 1.6;
                const p = interpolate(frame, [s, s + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
                return (
                  <span key={i} style={{ display: "inline-block", whiteSpace: "pre", transform: `translateY(${(1 - p) * 90}px)`, opacity: p, color: i < 3 ? C.red : C.ink }}>
                    {ch}
                  </span>
                );
              })}
            </div>
            <div style={{ marginTop: 18 }}>
              <RiseWords
                text="pengawas forensik otomatis untuk emiten BEI"
                start={peng}
                stagger={3}
                style={{ fontFamily: F.serif, fontSize: 60, fontStyle: "italic", color: C.inkSoft }}
              />
            </div>
            <div style={{ display: "flex", gap: 16, marginTop: 50 }}>
              {["BEI · 33 emiten non-keuangan", "Data: Sectors API", "Otomatis · tiap 3 hari"].map((c, i) => (
                <FadeIn key={c} start={untuk + i * 5} dur={10} y={14}>
                  <div style={{ fontFamily: F.mono, fontSize: 24, letterSpacing: "0.06em", textTransform: "uppercase", border: `2px solid ${C.ink}`, borderRadius: 999, padding: "10px 22px", color: i === 2 ? C.card : C.ink, background: i === 2 ? C.ink : "transparent" }}>
                    {c}
                  </div>
                </FadeIn>
              ))}
            </div>
          </div>
          <DrawCircle x={140 - 10} y={250 + 40} w={510} h={240} start={afs + 10} dur={16} stroke={6} />
        </div>
      </Paper>
      <SfxTrack
        cues={[
          { at: afs, name: "braam", volume: 0.5 },
          { at: afs + 10, name: "marker", volume: 0.35 },
          ...[0, 1, 2].map((i) => ({ at: untuk + i * 5, name: "tick", volume: 0.3 })),
        ]}
      />
    </AbsoluteFill>
  );
};

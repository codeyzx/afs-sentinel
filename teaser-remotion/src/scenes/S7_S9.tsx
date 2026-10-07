import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { shake, SfxTrack, Ticks } from "../components/Chrome";
import { CountUp, DrawCircle, easeInOut, FadeIn, Grain, Kicker, Marker, Paper, Stamp, useProgress } from "../components/primitives";
import { markOf, ScreenCapture } from "../components/ScreenCapture";
import { C, F, FPS } from "../theme";
import { w } from "../vo";

const WIN = { left: 96, top: 120, width: 1300 };
const URL = "afs-sentinel.herokuapp.com/incidents/AFS-2026-Q2-0003";

const Callout: React.FC<{ at: number; children: React.ReactNode; top: number }> = ({ at, children, top }) => (
  <FadeIn start={at} dur={8} x={30} y={0} style={{ position: "absolute", left: WIN.left + WIN.width + 40, top, width: 420 }}>
    <div style={{ borderTop: `3px solid ${C.red}`, paddingTop: 12 }}>{children}</div>
  </FadeIn>
);

// ── 7 · Evidence ────────────────────────────────────────────────────────────
export const S7Evidence: React.FC = () => {
  const frame = useCurrentFrame();
  const bukti = w(7, "bukti");
  const dilacak = w(7, "dilacak");
  const aiFoot = markOf("incident-ai", "ai-footer");
  const endpoint = markOf("incident-evidence", "endpoint");
  const formula = markOf("incident-evidence", "formula");
  const inputs = markOf("incident-evidence", "inputs");
  return (
    <AbsoluteFill>
      <Paper>
        <Ticks index={6} />
        {frame < bukti - 2 ? (
          <ScreenCapture
            cap="incident-ai"
            width={WIN.width}
            style={{ left: WIN.left, top: WIN.top }}
            url={URL}
            exhibit="Ringkasan AI"
            showCursor={false}
            timeMap={[
              [0, 1.5],
              [bukti, 3.2],
            ]}
            keys={[{ target: "ai", at: 1.5, zoom: 1.45, dur: 0.01, anchor: "top" }]}
          >
            {(toScreen) => <DrawCircle {...toScreen(aiFoot)} start={w(7, "AI")} dur={10} />}
          </ScreenCapture>
        ) : (
          <ScreenCapture
            cap="incident-evidence"
            width={WIN.width}
            style={{ left: WIN.left, top: WIN.top }}
            url={URL}
            exhibit="Bukti perhitungan"
            timeMap={[
              [bukti - 2, 7.3],
              [dilacak - 4, 8.6],
              [dilacak + 6, 10.4],
              [dilacak + 24, 11.6],
              [dilacak + 80, 12.4],
            ]}
            keys={[
              { target: { x: formula.x, y: formula.y, w: inputs.w, h: inputs.y + inputs.h - formula.y }, at: 7.3, zoom: 1.5, dur: 0.01 },
              { target: "endpoint", at: 10.6, zoom: 2.1, dur: 0.5 },
            ]}
          >
            {(toScreen, t) => <>{t > 11.2 && <DrawCircle {...toScreen(endpoint)} start={w(7, "sumbernya") - 4} dur={10} />}</>}
          </ScreenCapture>
        )}
        <Callout at={w(7, "ringkasan")} top={150}>
          <Kicker size={18}>Ringkasan AI</Kicker>
          <div style={{ fontFamily: F.serif, fontSize: 40, color: C.ink, lineHeight: 1.1, marginTop: 8 }}>ditulis dari 6 Rule Finding</div>
        </Callout>
        <Callout at={bukti} top={360}>
          <Kicker size={18}>Bukti perhitungan</Kicker>
          <div style={{ fontFamily: F.serif, fontSize: 40, color: C.ink, lineHeight: 1.1, marginTop: 8 }}>rumus + angka mentah</div>
        </Callout>
        <Callout at={w(7, "sampai")} top={570}>
          <Kicker size={18} color={C.red}>
            Setiap angka →
          </Kicker>
          <div style={{ fontFamily: F.serif, fontSize: 40, color: C.ink, lineHeight: 1.1, marginTop: 8 }}>
            <Marker start={w(7, "sumbernya")}>endpoint Sectors API</Marker>
          </div>
        </Callout>
      </Paper>
      <SfxTrack
        cues={[
          { at: w(7, "AI"), name: "marker", volume: 0.35 },
          { at: bukti - 2, name: "glitch", volume: 0.3 },
          { at: dilacak + 6, name: "whoosh", volume: 0.3 },
          { at: w(7, "sumbernya") - 4, name: "marker", volume: 0.35 },
        ]}
      />
    </AbsoluteFill>
  );
};

// ── 8 · Climax: 25 → 42 ─────────────────────────────────────────────────────
export const S8Proof: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const sentinel = w(8, "Sentinel");
  const menandai = w(8, "menandai");
  const dua = w(8, "dua");
  const sebelum = w(8, "sebelum");
  const through = dua - 6; // camera rushes through the claim into the red field
  const rush = useProgress(through, 8, easeInOut);
  const red = frame >= dua - 1;
  const srilAt = Math.round(5.15 * FPS);
  const claim = markOf("backtest", "claim-wskt");
  return (
    <AbsoluteFill>
      {!red && (
        <Paper>
          <Ticks index={7} />
          <div style={{ transform: `scale(${1 + rush * 2.4})`, transformOrigin: `${WIN.left + 380}px ${WIN.top + 200}px`, filter: `blur(${rush * 10}px)` }}>
            <ScreenCapture
              cap="backtest"
              width={WIN.width}
              style={{ left: WIN.left, top: WIN.top }}
              url="afs-sentinel.herokuapp.com/backtest"
              exhibit="Backtest · kasus nyata"
              showCursor={false}
              timeMap={[
                [0, 0.2],
                [dua, 2.0],
              ]}
              keys={[
                { target: "chart-wskt", at: 0.2 + (sentinel / FPS / (dua / FPS)) * 1.8 - 0.3, zoom: 1.25, dur: 0.4 },
                { target: "claim-wskt", at: 0.2 + (menandai / FPS / (dua / FPS)) * 1.8, zoom: 1.5, dur: 0.35 },
              ]}
            >
              {(toScreen) => (
                <FadeIn start={menandai + 4} dur={6} y={0} style={{ position: "absolute", ...pos(toScreen(claim)) }}>
                  <div style={{ position: "absolute", inset: 0, background: "rgba(245,213,71,0.25)", borderLeft: `6px solid ${C.marker}` }} />
                </FadeIn>
              )}
            </ScreenCapture>
          </div>
          <div style={{ position: "absolute", left: WIN.left + WIN.width + 40, top: 160, width: 420 }}>
            <FadeIn start={4} dur={8} y={8}>
              <Kicker size={20} color={C.red}>
                Diuji pada kasus nyata
              </Kicker>
              <div style={{ fontFamily: F.serif, fontSize: 54, color: C.ink, lineHeight: 1.05, marginTop: 12 }}>
                WSKT
                <br />
                <span style={{ fontStyle: "italic" }}>Waskita Karya</span>
              </div>
            </FadeIn>
          </div>
        </Paper>
      )}
      {red && (
        <AbsoluteFill style={{ background: C.red, transform: shake(frame, dua, 18, 12) }}>
          <Ticks index={7} dark />
          <div style={{ position: "absolute", left: 140, top: 96 }}>
            <Kicker size={22} color="rgba(251,248,242,0.8)">
              Backtest · WSKT · pertama kali “Sedang” di 2021-Q1
            </Kicker>
          </div>
          <div style={{ position: "absolute", left: 120, top: 190, display: "flex", alignItems: "flex-end", gap: 30 }}>
            <div style={{ fontFamily: F.serif, fontWeight: 600, fontSize: 470, lineHeight: 0.9, color: C.paper, letterSpacing: "-0.06em", transform: `scale(${interpolate(frame, [dua, dua + 8], [1.25, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })})`, transformOrigin: "left bottom" }}>
              <CountUp to={25} start={dua} dur={w(8, "bulan") - dua} />
            </div>
            <div style={{ paddingBottom: 70 }}>
              <FadeIn start={w(8, "bulan")} dur={6} y={20}>
                <div style={{ fontFamily: F.serif, fontStyle: "italic", fontSize: 120, color: C.paper, lineHeight: 1 }}>bulan</div>
              </FadeIn>
              <FadeIn start={sebelum} dur={8} y={14}>
                <div style={{ fontFamily: F.sans, fontSize: 40, fontWeight: 600, color: C.night, marginTop: 14 }}>sebelum suspensi WSKT · 8 Mei 2023</div>
              </FadeIn>
            </div>
          </div>
          <div style={{ position: "absolute", left: 140, top: 700, right: 140, borderTop: "2px solid rgba(14,13,11,0.35)", paddingTop: 22, display: "flex", alignItems: "baseline", gap: 26, opacity: interpolate(frame, [srilAt, srilAt + 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
            <Kicker size={22} color={C.night}>
              Lalu SRIL · Sritex
            </Kicker>
            <div style={{ fontFamily: F.serif, fontWeight: 600, fontSize: 130, color: C.night, lineHeight: 0.9, letterSpacing: "-0.04em" }}>
              <CountUp to={42} start={srilAt} dur={16} />
            </div>
            <div style={{ fontFamily: F.serif, fontStyle: "italic", fontSize: 56, color: C.night }}>bulan sebelum pailit</div>
          </div>
          <div style={{ position: "absolute", right: 150, top: 230 }}>
            <Stamp start={srilAt + 20} size={60} color={C.paper} rotate={-10} blend="normal">
              Ditandai
            </Stamp>
          </div>
          <Grain opacity={0.35} />
        </AbsoluteFill>
      )}
      <SfxTrack
        cues={[
          { at: 6, name: "tick", volume: 0.4 },
          { at: sentinel - 4, name: "whoosh", volume: 0.3 },
          { at: menandai + 4, name: "marker", volume: 0.35 },
          { at: through - 30, name: "reverse", volume: 0.5 },
          { at: dua - 1, name: "braam", volume: 0.85 },
          { at: dua - 1, name: "impact", volume: 0.7, dur: 140 },
          { at: dua, name: "count", volume: 0.3, dur: w(8, "bulan") - dua },
          { at: srilAt, name: "slam", volume: 0.8 },
          { at: srilAt, name: "count", volume: 0.25, dur: 16 },
          { at: srilAt + 20, name: "stamp", volume: 0.85 },
          { at: srilAt + 20, name: "subdrop", volume: 0.5 },
          { at: dur - 8, name: "whoosh-big", volume: 0.4 },
        ]}
      />
    </AbsoluteFill>
  );
};

const pos = (r: { x: number; y: number; w: number; h: number }) => ({ left: r.x - 6, top: r.y - 4, width: r.w + 12, height: r.h + 8 });

// ── 9 · End card ────────────────────────────────────────────────────────────
export const S9Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const afs = w(9, "AFS");
  const per = w(9, "Peringatan");
  const name = "AFS Sentinel";
  const disc = interpolate(frame, [per + 40, per + 52], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <Paper>
        <div style={{ position: "absolute", left: 140, top: 250 }}>
          <FadeIn start={2} dur={10} y={8}>
            <Kicker size={22} color={C.red}>
              Sectors Hackathon 2026 · Track 2 · Automation & Workflows
            </Kicker>
          </FadeIn>
          <div style={{ fontFamily: F.serif, fontSize: 230, fontWeight: 600, color: C.ink, letterSpacing: "-0.045em", lineHeight: 0.95, marginTop: 22, display: "flex" }}>
            {name.split("").map((ch, i) => {
              const s = afs + i * 1.4;
              const p = interpolate(frame, [s, s + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
              return (
                <span key={i} style={{ display: "inline-block", whiteSpace: "pre", transform: `translateY(${(1 - p) * 70}px)`, opacity: p, color: i < 3 ? C.red : C.ink }}>
                  {ch}
                </span>
              );
            })}
          </div>
          <div style={{ fontFamily: F.serif, fontSize: 82, fontStyle: "italic", color: C.ink, marginTop: 26 }}>
            <FadeIn start={per - 2} dur={8} y={16}>
              <Marker start={per + 4} dur={18}>
                Peringatan dini, sebelum terlambat.
              </Marker>
            </FadeIn>
          </div>
          <FadeIn start={per + 22} dur={10} y={10} style={{ marginTop: 56, display: "flex", gap: 40, alignItems: "baseline" }}>
            <Kicker size={20}>Powered by</Kicker>
            <div style={{ fontFamily: F.mono, fontSize: 32, fontWeight: 600, color: C.ink }}>Sectors API</div>
          </FadeIn>
        </div>
        <div style={{ position: "absolute", left: 140, bottom: 170, opacity: disc, fontFamily: F.sans, fontSize: 24, color: C.muted }}>
          Alat analisis & informasi, bukan nasihat investasi.
        </div>
      </Paper>
      <SfxTrack
        cues={[
          { at: afs, name: "braam", volume: 0.55 },
          { at: per + 4, name: "marker", volume: 0.4 },
          { at: per + 22, name: "impact-soft", volume: 0.45 },
        ]}
      />
    </AbsoluteFill>
  );
};

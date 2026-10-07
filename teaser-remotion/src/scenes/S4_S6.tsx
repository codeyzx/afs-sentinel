import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { SfxTrack, Ticks } from "../components/Chrome";
import { CountUp, DrawCircle, easeInOut, FadeIn, Kicker, Marker, Paper, RiseWords, useProgress, useSpring } from "../components/primitives";
import { markOf, ScreenCapture, type Rect } from "../components/ScreenCapture";
import { TelegramWindow, TG_LAYOUT, tgHtml, TgToast } from "../components/Telegram";
import { clockWib, formatWib, REAL, RULES, runSummary } from "../data";
import { C, F } from "../theme";
import { w } from "../vo";

const WIN = { left: 96, top: 120, width: 1300 };

/** A pill that pops on its word. */
const Pop: React.FC<{ at: number; children: React.ReactNode; dark?: boolean }> = ({ at, children, dark }) => {
  const frame = useCurrentFrame();
  const s = useSpring(at, { damping: 13, stiffness: 240, mass: 0.6 } as never);
  if (frame < at) return null;
  return (
    <div
      style={{
        transform: `scale(${0.6 + 0.4 * s}) translateX(${(1 - s) * 40}px)`,
        transformOrigin: "left center",
        opacity: Math.min(1, s * 1.5),
        fontFamily: F.mono,
        fontSize: 26,
        fontWeight: 600,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        padding: "14px 22px",
        borderRadius: 8,
        background: dark ? C.ink : C.red,
        color: "#FBF8F2",
        marginBottom: 16,
        display: "inline-block",
      }}
    >
      {children}
    </div>
  );
};

// ── 4 · Runs by itself ──────────────────────────────────────────────────────
export const S4Autonomous: React.FC = () => {
  const frame = useCurrentFrame();
  const tanpa = w(4, "tanpa");
  const memindai = w(4, "memindai");
  const freq = markOf("scheduler", "frequency");
  const cmd = markOf("scheduler", "command");
  const trig: Rect = { x: 618, y: 190, w: 150, h: 132 };
  const part = frame < tanpa - 2 ? 0 : 1;
  return (
    <AbsoluteFill>
      <Paper>
        <Ticks index={3} />
        {part === 0 ? (
          <ScreenCapture
            cap="scheduler"
            width={WIN.width}
            style={{ left: WIN.left, top: WIN.top }}
            url="dashboard.heroku.com/apps/afs-sentinel/scheduler"
            exhibit="Heroku Scheduler"
            timeMap={[
              [0, 5.6],
              [tanpa, 8.0],
            ]}
            keys={[{ target: { x: cmd.x - 10, y: freq.y - 24, w: freq.x + freq.w + 20 - cmd.x, h: 64 }, at: 5.6, zoom: 1.8, dur: 0.01 }]}
          >
            {(toScreen) => <DrawCircle {...toScreen(freq)} start={w(4, "tiga") + 2} dur={12} />}
          </ScreenCapture>
        ) : (
          <ScreenCapture
            cap="logs"
            width={WIN.width}
            style={{ left: WIN.left, top: WIN.top }}
            url="afs-sentinel.herokuapp.com/logs"
            exhibit="Log audit · data produksi"
            timeMap={[
              [tanpa, 1.9],
              [memindai - 6, 6.6],
              [memindai + 4, 7.2],
              [memindai + 30, 8.5],
              [memindai + 90, 11.0],
            ]}
            keys={[
              { target: { x: 241, y: 160, w: 1010, h: 175 }, at: 1.85, zoom: 1.6, dur: 0.01 },
              { target: { x: 241, y: 160, w: 1118, h: 560 }, at: 7.0, zoom: 1.25, dur: 0.6, anchor: "top" },
            ]}
          >
            {(toScreen, t) => (
              <>
                {t < 6.8 && <DrawCircle {...toScreen(trig)} start={tanpa + 6} dur={12} />}
              </>
            )}
          </ScreenCapture>
        )}
        <div style={{ position: "absolute", left: WIN.left + WIN.width + 40, top: 150, width: 420 }}>
          <Pop at={w(4, "tiga")}>Tiap 3 hari</Pop>
          <Pop at={tanpa + 4}>Tanpa manusia</Pop>
          <Pop at={w(4, "Sectors")} dark>
            Data Sectors API
          </Pop>
          <FadeIn start={memindai} dur={8} y={20} style={{ marginTop: 26 }}>
            <div style={{ fontFamily: F.serif, fontSize: 190, lineHeight: 0.85, fontWeight: 600, color: C.ink, letterSpacing: "-0.04em" }}>
              <CountUp to={33} start={memindai} dur={w(4, "emiten") - memindai + 6} />
            </div>
            <Kicker size={22} color={C.ink} style={{ marginTop: 8 }}>
              emiten dipindai
              <br />
              setiap run
            </Kicker>
          </FadeIn>
        </div>
      </Paper>
      <SfxTrack
        cues={[
          { at: w(4, "tiga"), name: "tick", volume: 0.45 },
          { at: w(4, "tiga") + 2, name: "marker", volume: 0.35 },
          { at: tanpa - 2, name: "glitch", volume: 0.35 },
          { at: tanpa + 4, name: "tick", volume: 0.45 },
          { at: w(4, "Sectors"), name: "tick", volume: 0.45 },
          { at: memindai, name: "count", volume: 0.25, dur: 30 },
          { at: w(4, "emiten") + 6, name: "impact-soft", volume: 0.5 },
        ]}
      />
    </AbsoluteFill>
  );
};

// ── 5 · Six rules ───────────────────────────────────────────────────────────
// VO: "laba yang tak berwujud kas" → Sloan + Divergensi, "utang yang melonjak" → Beneish (leverage), "risiko gagal bayar" → Altman.
const LIGHT: { rule: number; word: [string, number]; tone: "red" | "warn" }[] = [
  { rule: 0, word: ["laba", 0], tone: "red" },
  { rule: 1, word: ["kas", 0], tone: "warn" },
  { rule: 3, word: ["melonjak", 0], tone: "warn" },
  { rule: 2, word: ["gagal", 0], tone: "red" },
];

export const S5Rules: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const enam = w(5, "Enam");
  const CW = 520;
  const CH = 250;
  const G = 34;
  const left0 = (1920 - (CW * 3 + G * 2)) / 2;
  const top0 = 210;
  const pos = (i: number) => ({ x: left0 + (i % 3) * (CW + G), y: top0 + Math.floor(i / 3) * (CH + G) });
  const lit = (i: number) => {
    const l = LIGHT.find((x) => x.rule === i);
    return l ? { at: w(5, ...l.word), tone: l.tone } : undefined;
  };
  // camera: punch toward whichever card is lighting, pull back at the end
  const focus = [...LIGHT].reverse().find((l) => frame >= w(5, ...l.word) - 4);
  const back = frame >= w(5, "bayar") + 10;
  const target = focus && !back ? pos(focus.rule) : null;
  const camP = useProgress(w(5, "mencari"), 12, easeInOut);
  const s = target ? 1 + 0.32 * camP : 1;
  const cx = target ? target.x + CW / 2 : 960;
  const cy = target ? target.y + CH / 2 : 500;
  const tx = (960 - cx) * (s - 1) * 0.9;
  const ty = (480 - cy) * (s - 1) * 0.9;
  return (
    <AbsoluteFill>
      <Paper>
        <Ticks index={4} />
        <div style={{ position: "absolute", left: left0, top: 110 }}>
          <FadeIn start={enam} dur={8} y={10}>
            <Kicker size={22} color={C.ink}>
              6 Forensic Rule · satu skor risiko 0–100
            </Kicker>
          </FadeIn>
        </div>
        <div style={{ position: "absolute", inset: 0, transform: `translate(${tx}px, ${ty}px) scale(${s})`, transformOrigin: `${cx}px ${cy}px`, transition: "none" }}>
          {RULES.map((r, i) => {
            const p = pos(i);
            const a = interpolate(frame, [enam + i * 3, enam + i * 3 + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            const L = lit(i);
            const on = L ? interpolate(frame, [L.at, L.at + 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 0;
            const color = L?.tone === "red" ? C.red : C.warn;
            const dim = target && focus?.rule !== i ? 0.45 : 1;
            return (
              <div
                key={r.name}
                style={{
                  position: "absolute",
                  left: p.x,
                  top: p.y,
                  width: CW,
                  height: CH,
                  boxSizing: "border-box",
                  background: C.card,
                  border: `2px solid ${on ? color : C.lineStrong}`,
                  borderTop: `${on ? 10 : 2}px solid ${on ? color : C.lineStrong}`,
                  borderRadius: 12,
                  padding: "24px 26px",
                  boxShadow: on ? `0 18px 40px ${L?.tone === "red" ? "rgba(217,58,43,0.25)" : "rgba(217,165,20,0.25)"}` : "0 10px 24px rgba(40,28,10,0.08)",
                  opacity: a * dim,
                  transform: `translateY(${(1 - a) * 40}px)`,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ width: 44, height: 44, borderRadius: 22, border: `2px solid ${C.ink}`, display: "grid", placeItems: "center", fontFamily: F.mono, fontSize: 20, fontWeight: 600, background: on ? color : "transparent", color: on ? "#FBF8F2" : C.ink, borderColor: on ? color : C.ink }}>
                    {i + 1}
                  </div>
                  {on > 0 && (
                    <div style={{ fontFamily: F.mono, fontSize: 18, letterSpacing: "0.12em", color: "#FBF8F2", background: color, padding: "6px 12px", borderRadius: 4, transform: `scale(${0.7 + on * 0.3})` }}>
                      {L?.tone === "red" ? "BAHAYA" : "WASPADA"}
                    </div>
                  )}
                </div>
                <div style={{ fontFamily: F.sans, fontWeight: 700, fontSize: 36, color: C.ink, marginTop: 26 }}>{r.name}</div>
                <div style={{ fontFamily: F.sans, fontSize: 24, color: C.muted, marginTop: 6 }}>{r.plain}</div>
                <div style={{ position: "absolute", right: 26, bottom: 22, fontFamily: F.mono, fontSize: 18, color: C.muted }}>bobot {r.weight}</div>
              </div>
            );
          })}
        </div>
      </Paper>
      <SfxTrack
        cues={[
          { at: enam, name: "whoosh", volume: 0.35 },
          ...LIGHT.map((l) => ({ at: w(5, ...l.word), name: "slam", volume: 0.45 })),
          { at: w(5, "bayar") + 10, name: "whoosh", volume: 0.3 },
          { at: dur - 10, name: "glitch", volume: 0.25 },
        ]}
      />
    </AbsoluteFill>
  );
};

// ── 6 · Telegram alert ──────────────────────────────────────────────────────
export const S6Alert: React.FC = () => {
  const frame = useCurrentFrame();
  const janggal = w(6, "janggal");
  const peringatan = w(6, "peringatan");
  const anda = w(6, "Anda");
  const L = TG_LAYOUT;
  const prevRun = REAL.runs.find((r) => r.id === 2)!;
  const messages = [
    { html: tgHtml(runSummary(prevRun)), time: clockWib(prevRun.startedAt), at: -60 },
    {
      html: tgHtml(REAL.alert.text),
      time: clockWib(REAL.alert.sentAt),
      button: REAL.alert.button,
      at: peringatan,
      marks: { 0: peringatan + 4, 1: w(6, "langsung"), 5: w(6, "masuk"), 6: w(6, "masuk") + 5 },
    },
  ];
  const push = useProgress(peringatan, 14, easeInOut);
  const pull = useProgress(anda, 14, easeInOut);
  const zoom = 1 + 0.35 * push - 0.35 * pull;
  const ox = L.side + L.bubbleLeft + L.bubbleW / 2;
  const oy = L.height - 260;
  const press = anda + 18;
  const glow = interpolate(frame, [press - 4, press, press + 10], [0, 1, 0.5], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const shk = frame >= janggal && frame < janggal + 10 ? `translate(${Math.sin((frame - janggal) * 2.6) * 10 * (1 - (frame - janggal) / 10)}px, 0)` : "none";
  return (
    <AbsoluteFill>
      <Paper>
        <Ticks index={5} />
        <div style={{ position: "absolute", left: 96, top: 110, width: L.width * 0.86, height: L.height * 0.86, transform: shk }}>
          <div style={{ position: "absolute", width: L.width, height: L.height, transform: "scale(0.86)", transformOrigin: "0 0", overflow: "hidden", borderRadius: 14 }}>
            <div style={{ position: "absolute", inset: 0, transformOrigin: `${ox}px ${oy}px`, transform: `scale(${zoom})` }}>
              <TelegramWindow messages={messages} buttonGlow={glow} style={{ left: 0, top: 0 }} />
            </div>
          </div>
          <TgToast at={janggal} title="AFS Sentinel" body="🟡 Sedang · UNVR — Unilever Indonesia Tbk · Skor 45/100" style={{ left: L.width * 0.86 - 490, top: 70 }} />
          <div style={{ position: "absolute", top: L.height * 0.86 + 12, left: 0 }}>
            <Kicker size={15}>Rekonstruksi tampilan dari pesan bot asli · {formatWib(REAL.alert.sentAt)}</Kicker>
          </div>
        </div>
        <div style={{ position: "absolute", left: 96 + L.width * 0.86 + 50, top: 230, width: 600 }}>
          <FadeIn start={janggal} dur={8} y={8}>
            <Kicker size={20} color={C.red}>
              ● Peringatan masuk
            </Kicker>
          </FadeIn>
          <RiseWords text="Anda dikabari," start={anda} stagger={3} style={{ fontFamily: F.serif, fontSize: 92, color: C.ink, lineHeight: 1.0, marginTop: 20, letterSpacing: "-0.02em" }} />
          <div style={{ fontFamily: F.serif, fontSize: 92, fontStyle: "italic", color: C.ink, lineHeight: 1.05, letterSpacing: "-0.02em" }}>
            <FadeIn start={anda + 8} dur={8} y={20}>
              <Marker start={anda + 14}>bukan mencari.</Marker>
            </FadeIn>
          </div>
        </div>
      </Paper>
      <SfxTrack
        cues={[
          { at: janggal, name: "ping", volume: 0.8 },
          { at: janggal, name: "impact-soft", volume: 0.4 },
          { at: peringatan, name: "whoosh", volume: 0.3 },
          { at: anda + 14, name: "marker", volume: 0.35 },
          { at: press, name: "click", volume: 0.6 },
        ]}
      />
    </AbsoluteFill>
  );
};

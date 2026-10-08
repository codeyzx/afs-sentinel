import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Emblem, Wordmark } from "../components/Brand";
import { Backdrop } from "../components/Fx";
import { ease, easeIn, easeInOut, Kicker, prog, rand, RiseWords, shake } from "../components/primitives";
import { EMITEN, FLAGGED, WSKT_BACKTEST } from "../data";
import { C, F } from "../theme";
import { lineStart, local, MUSIC, scene, w } from "../timeline";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// ---------------------------------------------------------------- 1. Hook: 8 Mei 2023

const Slam: React.FC<{ at: number; children: React.ReactNode; style?: React.CSSProperties }> = ({ at, children, style }) => {
  const frame = useCurrentFrame();
  const p = prog(frame, at, 7, ease);
  if (frame < at) return <span style={{ ...style, opacity: 0 }}>{children}</span>;
  return (
    <span style={{ display: "inline-block", opacity: Math.min(1, p * 2), transform: `scale(${1.5 - 0.5 * p})`, filter: `blur(${(1 - p) * 14}px)`, ...style }}>
      {children}
    </span>
  );
};

/** Heartbeat trace that runs across the frame and flatlines red at `stopAt`. */
const Trace: React.FC<{ stopAt: number }> = ({ stopAt }) => {
  const frame = useCurrentFrame();
  const head = interpolate(frame, [0, stopAt], [0, 1920 * 0.86], { ...clamp });
  const pts: string[] = [];
  for (let x = 0; x <= head; x += 6) {
    const beat = x % 320;
    let y = 0;
    if (frame < stopAt || x < head - 2) {
      if (beat > 140 && beat < 150) y = -(beat - 140) * 9;
      else if (beat >= 150 && beat < 162) y = -90 + (beat - 150) * 13;
      else if (beat >= 162 && beat < 172) y = 66 - (beat - 162) * 6.6;
    }
    pts.push(`${x},${540 + y * 0.9}`);
  }
  const dead = frame >= stopAt;
  const flat = interpolate(frame, [stopAt, stopAt + 20], [head, 1920], clamp);
  return (
    <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, opacity: 0.55 }}>
      <polyline points={pts.join(" ")} fill="none" stroke={dead ? C.red : "#7FD1B9"} strokeWidth={3} style={{ filter: `drop-shadow(0 0 8px ${dead ? C.red : "#7FD1B9"})` }} />
      {dead && <line x1={head} y1={540} x2={flat} y2={540} stroke={C.red} strokeWidth={3} style={{ filter: `drop-shadow(0 0 10px ${C.red})` }} />}
      {!dead && <circle cx={head} cy={540} r={6} fill="#CFF5EA" />}
    </svg>
  );
};

export const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const t8 = w("date", "Delapan");
  const tMei = w("date", "Mei");
  const t23 = w("date", "dua", 0);
  const halt = lineStart("halt");
  const stop = w("halt", "dihentikan");
  const up = prog(frame, halt - 2, 20, easeInOut);
  const push = interpolate(frame, [0, scene("hook").dur], [1, 1.07]);
  const bar = prog(frame, stop, 8);
  const sh = [t8, tMei, t23, stop].map((a) => shake(frame, a, a === stop ? 22 : 10, 9)).find((s) => s !== "translate(0px,0px)") ?? "none";
  return (
    <AbsoluteFill>
      <Backdrop grid={0.25} tint={frame >= stop ? "rgba(140,20,14,0.45)" : "rgba(40,70,90,0.3)"} />
      <Trace stopAt={stop} />
      <AbsoluteFill style={{ transform: `scale(${push}) ${sh}` }}>
        <Kicker size={22} color={C.dim} style={{ position: "absolute", left: 0, right: 0, top: 200, textAlign: "center", opacity: prog(frame, 6, 18) * (1 - up) }}>
          Bursa Efek Indonesia
        </Kicker>
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: interpolate(up, [0, 1], [330, 215]),
            textAlign: "center",
            fontFamily: F.display,
            fontWeight: 900,
            fontSize: interpolate(up, [0, 1], [300, 168]),
            letterSpacing: "-0.04em",
            lineHeight: 1,
            color: C.text,
            textShadow: "0 0 60px rgba(0,0,0,0.9)",
          }}
        >
          <Slam at={t8}>8</Slam> <Slam at={tMei} style={{ marginRight: "0.22em" }}>MEI</Slam><Slam at={t23} style={{ color: frame >= stop ? C.red : C.text }}>2023</Slam>
        </div>

        {/* ticker board */}
        <div style={{ position: "absolute", left: 0, right: 0, top: 470, display: "flex", flexDirection: "column", alignItems: "center", gap: 26, opacity: prog(frame, halt, 10) }}>
          <div style={{ display: "flex", alignItems: "center", gap: 34, transform: `translateY(${(1 - prog(frame, halt, 16)) * 30}px)` }}>
            <div style={{ fontFamily: F.mono, fontWeight: 700, fontSize: 120, letterSpacing: "0.04em", color: C.text, border: `3px solid ${frame >= stop ? C.red : C.lineStrong}`, padding: "4px 30px", borderRadius: 12 }}>
              WSKT
            </div>
            <div style={{ fontFamily: F.display, fontSize: 40, color: C.dim, lineHeight: 1.25, textAlign: "left" }}>
              Waskita Karya
              <br />
              <span style={{ fontSize: 30, color: C.hint }}>(Persero) Tbk</span>
            </div>
          </div>
          <div
            style={{
              fontFamily: F.mono,
              fontWeight: 700,
              fontSize: 46,
              letterSpacing: "0.2em",
              color: "#fff",
              background: C.red,
              padding: "14px 36px",
              transform: `scaleX(${bar}) scale(${1 + (1 - bar) * 0.3})`,
              opacity: bar,
              boxShadow: `0 0 80px ${C.redGlow}`,
            }}
          >
            PERDAGANGAN DIHENTIKAN
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- 2. Rewind: the signs were there

const QUARTERS_BACK = ["2023-Q1", "2022-Q4", "2022-Q3", "2022-Q2", "2022-Q1", "2021-Q4", "2021-Q3", "2021-Q2", "2021-Q1"];

const ReportCard: React.FC<{ q: string; score: number; sev: "Sedang" | "Rendah"; lit: number; focus: number }> = ({ q, score, sev, lit, focus }) => {
  const col = sev === "Sedang" ? C.warn : C.safe;
  return (
    <div
      style={{
        width: 300,
        height: 400,
        background: "linear-gradient(180deg,#141C22,#0D1317)",
        border: `1.5px solid ${focus > 0 ? `rgba(242,179,61,${0.4 + 0.6 * focus})` : C.lineStrong}`,
        borderRadius: 14,
        padding: 26,
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        gap: 14,
        boxShadow: `0 30px 60px rgba(0,0,0,0.6), 0 0 ${60 * focus}px rgba(242,179,61,${0.5 * focus})`,
      }}
    >
      <Kicker size={14} color={C.hint}>
        Laporan keuangan
      </Kicker>
      <div style={{ fontFamily: F.mono, fontWeight: 700, fontSize: 52, color: C.text }}>WSKT</div>
      <div style={{ fontFamily: F.display, fontWeight: 700, fontSize: 40, color: C.dim }}>{q}</div>
      {Array.from({ length: 5 }, (_, i) => (
        <div key={i} style={{ height: 8, borderRadius: 4, background: C.line, width: `${90 - i * 12}%` }} />
      ))}
      <div style={{ marginTop: "auto", display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ width: 16, height: 16, borderRadius: 8, background: lit > 0 ? col : C.hint, boxShadow: lit > 0 ? `0 0 ${16 * lit}px ${col}` : "none" }} />
        <div style={{ fontFamily: F.mono, fontSize: 19, color: lit > 0 ? col : C.hint, letterSpacing: "0.04em", whiteSpace: "nowrap" }}>
          SKOR {score.toFixed(1).replace(".", ",")} · {sev.toUpperCase()}
        </div>
      </div>
      <div style={{ height: 6, borderRadius: 3, background: col, opacity: lit, transform: `scaleX(${lit})`, transformOrigin: "left" }} />
    </div>
  );
};

export const Rewind: React.FC = () => {
  const frame = useCurrentFrame();
  const L = (m: number) => local("rewind", m);
  const tSigns = L(w("signs", "tanda"));
  const tYears = L(w("signs", "bertahun-tahun"));
  const rewindEnd = 22;
  // camera travels back in time from 2023-Q1 (index 8) to 2021-Q1 (index 0)
  const cards = WSKT_BACKTEST.filter((r) => r.q <= "2023-Q1");
  const travel = interpolate(frame, [rewindEnd, tYears], [cards.length - 1, 0], { ...clamp, easing: easeInOut });
  const SP = 340;
  const focus0 = prog(frame, tYears, 12);
  const odo = interpolate(frame, [0, rewindEnd], [0, QUARTERS_BACK.length - 1], { ...clamp, easing: easeIn });
  const showRewind = frame < rewindEnd + 6;
  return (
    <AbsoluteFill>
      <Backdrop grid={0.35} drift={frame * 3} />
      {/* receding timeline of quarterly reports */}
      <AbsoluteFill style={{ perspective: 1600, opacity: prog(frame, rewindEnd - 6, 12) }}>
        <div
          style={{
            position: "absolute",
            left: 960,
            top: 520,
            transformStyle: "preserve-3d",
            transform: `rotateY(-24deg) rotateX(6deg) translateX(${-travel * SP}px)`,
          }}
        >
          {cards.map((c, i) => {
            const d = Math.abs(i - travel);
            const lit = prog(frame, tSigns + (cards.length - 1 - i) * 3, 10);
            return (
              <div
                key={c.q}
                style={{
                  position: "absolute",
                  left: i * SP - 150,
                  top: -200,
                  transform: `translateZ(${-d * 60 + (i === 0 ? focus0 * 120 : 0)}px)`,
                  opacity: interpolate(d, [0, 4, 7], [1, 0.75, 0.25], clamp),
                }}
              >
                <ReportCard q={c.q} score={c.score} sev={c.sev} lit={lit} focus={i === 0 ? focus0 : 0} />
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
      {/* first-sign label */}
      <div style={{ position: "absolute", left: 0, right: 0, top: 168, textAlign: "center", opacity: focus0, transform: `translateY(${(1 - focus0) * 16}px)` }}>
        <Kicker size={24} color={C.warn}>
          2021-Q1 · Tanda pertama
        </Kicker>
      </div>
      <div
        style={{
          position: "absolute",
          left: 120,
          top: 760,
          fontFamily: F.serif,
          fontStyle: "italic",
          fontSize: 92,
          color: C.text,
          opacity: prog(frame, tYears, 10),
          textShadow: "0 0 40px #000",
        }}
      >
        <RiseWords text="bertahun-tahun sebelumnya." start={tYears} starts={[tYears, L(w("signs", "sebelumnya"))]} />
      </div>
      {/* the rewind itself: odometer and VHS lines */}
      {showRewind && (
        <AbsoluteFill style={{ opacity: 1 - prog(frame, rewindEnd, 6) }}>
          <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0 2px, transparent 2px 5px)" }} />
          <div
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              top: 380,
              textAlign: "center",
              fontFamily: F.mono,
              fontWeight: 700,
              fontSize: 210,
              color: C.text,
              letterSpacing: "0.02em",
              textShadow: `-6px 0 0 rgba(255,59,48,0.7), 6px 0 0 rgba(80,200,255,0.6)`,
              filter: `blur(${Math.abs(Math.sin(frame * 1.7)) * 3}px)`,
              transform: `translateY(${((odo % 1) - 0.5) * 60}px)`,
            }}
          >
            {QUARTERS_BACK[Math.round(odo)]}
          </div>
          <Kicker size={30} color={C.red} style={{ position: "absolute", left: 120, top: 190 }}>
            ◀◀ REW
          </Kicker>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- 3. Who reads them all?

const COLS = 22;
export const Who: React.FC = () => {
  const frame = useCurrentFrame();
  const L = (m: number) => local("who", m);
  const tQ = L(w("who", "siapa"));
  const zoom = interpolate(frame, [0, 44], [5.2, 0.92], { ...clamp, easing: easeInOut });
  const qWords = "siapa yang sempat membaca semuanya?".split(" ");
  const starts = ["siapa", "yang", "sempat", "membaca", "semuanya"].map((x) => L(w("who", x)));
  return (
    <AbsoluteFill>
      <Backdrop grid={0} />
      <AbsoluteFill style={{ transform: `scale(${zoom})`, transformOrigin: "62% 40%" }}>
        <div style={{ position: "absolute", left: 300, top: 6, display: "flex", flexDirection: "column", gap: 6 }}>
          {EMITEN.map((em, r) => (
            <div key={em} style={{ display: "flex", gap: 6, alignItems: "center", height: 26 }}>
              <div style={{ width: 80, fontFamily: F.mono, fontSize: 15, color: C.hint }}>{em}</div>
              {Array.from({ length: COLS }, (_, c) => {
                const flick = rand(r * 97 + c * 13 + Math.floor(frame / 3)) > 0.93;
                return <div key={c} style={{ width: 52, height: 26, borderRadius: 3, border: `1px solid ${C.line}`, background: flick ? "rgba(214,228,236,0.16)" : "rgba(214,228,236,0.035)" }} />;
              })}
            </div>
          ))}
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 60% 40% at 50% 50%, rgba(6,8,10,${0.9 * prog(frame, tQ - 4, 10)}) 30%, rgba(6,8,10,${0.4 * prog(frame, tQ - 4, 10)}) 100%)` }} />
      <Kicker size={22} color={C.dim} style={{ position: "absolute", left: 0, right: 0, top: 360, textAlign: "center", opacity: prog(frame, 20, 14) }}>
        33 emiten · laporan tiap kuartal
      </Kicker>
      <div style={{ position: "absolute", left: 0, right: 0, top: 420, textAlign: "center", fontFamily: F.serif, fontStyle: "italic", fontSize: 108, color: C.text, lineHeight: 1.05 }}>
        <RiseWords text={qWords.join(" ")} start={tQ} starts={starts} />
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- 4. Reveal: AFS Sentinel

export const Reveal: React.FC = () => {
  const frame = useCurrentFrame();
  const L = (m: number) => local("reveal", m);
  const tKen = L(lineStart("intro"));
  const hit = L(MUSIC.revealHit);
  const draw = prog(frame, tKen, 40, easeInOut);
  const burst = prog(frame, hit, 26, ease);
  const big = prog(frame, hit, 18, ease);
  const sweep = frame * 6;
  const size = interpolate(big, [0, 1], [170, 230]);
  return (
    <AbsoluteFill>
      <Backdrop grid={0.3 * big} tint={`rgba(120,24,18,${0.35 * big})`} />
      {/* radar rings before the hit */}
      {frame >= tKen &&
        frame < hit + 10 &&
        [0, 1, 2].map((i) => {
          const k = ((frame - tKen + i * 14) % 42) / 42;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: 960,
                top: 420,
                width: 600 * k,
                height: 600 * k,
                marginLeft: -300 * k,
                marginTop: -300 * k,
                borderRadius: "50%",
                border: `2px solid rgba(255,59,48,${0.5 * (1 - k)})`,
                opacity: 1 - prog(frame, hit, 8),
              }}
            />
          );
        })}
      {/* the 33 Emiten, coloured by their live severity */}
      {EMITEN.map((em, i) => {
        const a = (i / EMITEN.length) * Math.PI * 2 + frame * 0.0025;
        const rx = 820 + (i % 3) * 40;
        const ry = 420 + (i % 2) * 30;
        const px = 960 + Math.cos(a) * rx * burst;
        const py = 470 + Math.sin(a) * ry * burst;
        const flagged = FLAGGED.includes(em);
        const col = flagged ? C.warn : C.safe;
        return (
          <div
            key={em}
            style={{
              position: "absolute",
              left: px,
              top: py,
              transform: `translate(-50%,-50%) scale(${0.4 + 0.6 * burst})`,
              opacity: burst * (0.55 + (flagged ? 0.45 : 0)),
              fontFamily: F.mono,
              fontSize: 22,
              fontWeight: 700,
              color: col,
              padding: "6px 12px",
              border: `1.5px solid ${col}`,
              borderRadius: 8,
              background: "rgba(6,8,10,0.6)",
              boxShadow: flagged ? `0 0 18px rgba(242,179,61,0.35)` : "none",
            }}
          >
            {em}
          </div>
        );
      })}
      <div style={{ position: "absolute", left: 960, top: interpolate(big, [0, 1], [420, 330]), transform: "translate(-50%,-50%)", opacity: prog(frame, tKen, 8) }}>
        <Emblem size={size} draw={draw} sweep={sweep} glow={0.4 + 0.5 * big} />
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 500, display: "flex", justifyContent: "center", transform: shake(frame, hit, 16, 10) }}>
        {frame >= hit - 1 && <Wordmark start={hit} size={150} stagger={1.2} />}
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 700, textAlign: "center", fontFamily: F.serif, fontStyle: "italic", fontSize: 54, color: C.dim, opacity: prog(frame, hit + 20, 16) }}>
        pengawas forensik otomatis untuk emiten BEI
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 800, display: "flex", justifyContent: "center", gap: 40, opacity: prog(frame, hit + 30, 14) }}>
        <Legend color={C.safe} label="23 Aman" />
        <Legend color={C.warn} label="10 Perlu ditinjau" />
      </div>
    </AbsoluteFill>
  );
};

const Legend: React.FC<{ color: string; label: string }> = ({ color, label }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 12, fontFamily: F.mono, fontSize: 20, letterSpacing: "0.12em", color: C.dim, textTransform: "uppercase" }}>
    <div style={{ width: 12, height: 12, borderRadius: 6, background: color, boxShadow: `0 0 10px ${color}` }} />
    {label}
  </div>
);

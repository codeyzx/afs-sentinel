import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Emblem, Window3D, Wordmark } from "../components/Brand";
import { Backdrop } from "../components/Fx";
import { ease, easeInOut, Kicker, prog, RiseWords, shake } from "../components/primitives";
import { WSKT_BACKTEST, WSKT_SUSPENDED } from "../data";
import { C, F } from "../theme";
import { lineEnd, lineStart, local, MUSIC, scene, w } from "../timeline";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// ---------------------------------------------------------------- 8. Climax: 25 months early

const X0 = 260;
const X1 = 1660;
const D0 = Date.parse("2021-01-01");
const D1 = Date.parse("2023-07-01");
const X = (iso: string) => X0 + ((Date.parse(iso) - D0) / (D1 - D0)) * (X1 - X0);
const Y = (s: number) => 790 - (s / 60) * 470;

const Chart: React.FC<{ t0: number; tMark: number; tDua: number; tHit: number }> = ({ t0, tMark, tDua, tHit }) => {
  const frame = useCurrentFrame();
  const pts = WSKT_BACKTEST.map((r) => [X(r.date), Y(r.score)] as const);
  const draw = prog(frame, t0, 40, easeInOut);
  const n = Math.max(1, Math.ceil(draw * (pts.length - 1)));
  const partial = draw * (pts.length - 1) - (n - 1);
  const path = pts.slice(0, n).map((p) => `${p[0]},${p[1]}`);
  const a = pts[n - 1];
  const b = pts[Math.min(n, pts.length - 1)];
  path.push(`${a[0] + (b[0] - a[0]) * partial},${a[1] + (b[1] - a[1]) * partial}`);
  const xs = X(WSKT_SUSPENDED);
  const susp = prog(frame, t0 + 22, 14);
  const mark = prog(frame, tMark, 10);
  const pulse = 0.5 + 0.5 * Math.sin(frame / 4);
  const bracket = prog(frame, tDua - 4, tHit - tDua + 4, easeInOut);
  const [fx, fy] = pts[0];
  return (
    <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, overflow: "visible" }}>
      {/* severity bands */}
      <rect x={X0} y={Y(30)} width={X1 - X0} height={Y(0) - Y(30)} fill={C.safe} opacity={0.06} />
      <rect x={X0} y={Y(60)} width={X1 - X0} height={Y(30) - Y(60)} fill={C.warn} opacity={0.07} />
      <line x1={X0} y1={Y(30)} x2={X1} y2={Y(30)} stroke={C.warn} strokeOpacity={0.35} strokeDasharray="4 8" />
      <text x={X1 + 18} y={Y(30) + 8} fill={C.warn} fontFamily={F.mono} fontSize={20} opacity={0.8}>
        30
      </text>
      <text x={X1 + 18} y={Y(46)} fill={C.warn} fontFamily={F.mono} fontSize={18} opacity={0.7}>
        SEDANG
      </text>
      <text x={X1 + 18} y={Y(14)} fill={C.safe} fontFamily={F.mono} fontSize={18} opacity={0.7}>
        RENDAH
      </text>
      {/* quarter ticks */}
      {WSKT_BACKTEST.map((r, i) => (
        <text key={r.q} x={pts[i][0]} y={Y(0) + 44} fill={C.hint} fontFamily={F.mono} fontSize={19} textAnchor="middle" opacity={prog(frame, t0 + i * 3, 8)}>
          {r.q}
        </text>
      ))}
      {/* score line */}
      <polyline points={path.join(" ")} fill="none" stroke={C.warn} strokeWidth={5} strokeLinejoin="round" style={{ filter: `drop-shadow(0 0 10px ${C.warn})` }} />
      {pts.slice(0, n).map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={8} fill={WSKT_BACKTEST[i].sev === "Sedang" ? C.warn : C.safe} />
      ))}
      {/* suspension */}
      <line x1={xs} y1={Y(60) - 40} x2={xs} y2={Y(60) - 40 + (Y(0) - Y(60) + 40) * susp} stroke={C.red} strokeWidth={4} strokeDasharray="14 10" />
      <g opacity={susp}>
        <text x={xs - 16} y={Y(60) - 56} fill={C.red} fontFamily={F.mono} fontWeight={700} fontSize={24} textAnchor="end">
          8 MEI 2023
        </text>
        <text x={xs - 16} y={Y(60) - 24} fill={C.dim} fontFamily={F.mono} fontSize={19} textAnchor="end">
          PERDAGANGAN WSKT DIHENTIKAN
        </text>
      </g>
      {/* first flag */}
      <g opacity={mark}>
        <circle cx={fx} cy={fy} r={14 + 22 * pulse} fill="none" stroke={C.warn} strokeWidth={3} opacity={1 - pulse * 0.7} />
        <circle cx={fx} cy={fy} r={14} fill={C.warn} />
        <line x1={fx} y1={fy - 20} x2={fx} y2={Y(60) - 40} stroke={C.warn} strokeWidth={2} />
        <text x={fx + 14} y={Y(60) - 56} fill={C.warn} fontFamily={F.mono} fontWeight={700} fontSize={24}>
          2021-Q1 · PERTAMA KALI SEDANG
        </text>
        <text x={fx + 14} y={Y(60) - 24} fill={C.dim} fontFamily={F.mono} fontSize={19}>
          SKOR 30,6 / 100
        </text>
      </g>
      {/* the gap */}
      {bracket > 0 && (
        <g>
          <line x1={fx} y1={Y(60) + 30} x2={fx + (xs - fx) * bracket} y2={Y(60) + 30} stroke={C.text} strokeWidth={3} />
          <line x1={fx} y1={Y(60) + 16} x2={fx} y2={Y(60) + 44} stroke={C.text} strokeWidth={3} />
          {bracket > 0.98 && <line x1={xs} y1={Y(60) + 16} x2={xs} y2={Y(60) + 44} stroke={C.text} strokeWidth={3} />}
        </g>
      )}
    </svg>
  );
};

export const Climax: React.FC = () => {
  const frame = useCurrentFrame();
  const L = (m: number) => local("climax", m);
  const dur = scene("climax").dur;
  const tFlag = L(lineStart("flag"));
  const tMark = L(w("flag", "menandai"));
  const tDua = L(w("months", "dua"));
  const tLima = L(w("months", "lima"));
  const tHit = L(MUSIC.hit);
  const tSeb = L(w("months", "sebelum"));
  const tSril = L(lineEnd("months")) + 10;
  const through = prog(frame, tFlag - 10, 14, easeInOut);
  const red = frame >= tHit && frame < tSril;
  const count = Math.round(25 * prog(frame, tDua, tLima + 4 - tDua, (x) => x));
  const sril = prog(frame, tSril, 14);
  return (
    <AbsoluteFill>
      <Backdrop grid={0.3} drift={frame} />
      {/* the real backtest page first */}
      {frame < tFlag + 6 && (
        <Window3D
          cap="backtest"
          width={1440}
          x={960}
          y={560}
          rx={interpolate(frame, [0, tFlag], [8, 2])}
          z={interpolate(through, [0, 1], [0, 1400]) + interpolate(frame, [0, tFlag], [-120, 0])}
          opacity={prog(frame, 0, 10) * (1 - through)}
          timeMap={[
            [0, 0.3],
            [tFlag, 2.4],
          ]}
          keys={[{ at: 0.6, target: "chart-wskt", zoom: 1.35, dur: 0.8 }]}
          url="afs-sentinel.herokuapp.com/backtest"
          label="Backtest · kasus nyata"
        />
      )}
      <Kicker size={22} color={C.dim} style={{ position: "absolute", left: 120, top: 140, opacity: prog(frame, 4, 10) * (1 - prog(frame, tHit - 2, 4)) }}>
        Backtest · WSKT Waskita Karya · data Sectors API sejak 2021-Q1
      </Kicker>
      {/* our redrawn chart, same numbers */}
      <AbsoluteFill style={{ opacity: through * (frame >= tHit ? 0 : 1) * (1 - 0.7 * prog(frame, tDua - 4, 8)), transform: `scale(${interpolate(through, [0, 1], [0.9, 1])})` }}>
        <Chart t0={tFlag} tMark={tMark} tDua={tDua} tHit={tHit} />
      </AbsoluteFill>
      {/* the count, riding the bracket */}
      {frame >= tDua - 2 && frame < tHit && (
        <div style={{ position: "absolute", left: 0, right: 0, top: 380, textAlign: "center", fontFamily: F.display, fontWeight: 900, fontSize: 300, color: C.text, letterSpacing: "-0.04em", textShadow: "0 0 50px #000" }}>
          {count}
        </div>
      )}
      {/* red takeover */}
      {red && (
        <AbsoluteFill style={{ background: C.red, transform: shake(frame, tHit, 26, 12) }}>
          <div style={{ position: "absolute", left: 0, right: 0, top: 140, textAlign: "center" }}>
            <Kicker size={26} color="rgba(6,8,10,0.75)">
              Sentinel menandai Waskita
            </Kicker>
          </div>
          <div
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              top: 190,
              display: "flex",
              justifyContent: "center",
              alignItems: "baseline",
              gap: 40,
              color: C.night,
              fontFamily: F.display,
              fontWeight: 900,
              transform: `scale(${1.25 - 0.25 * prog(frame, tHit, 8, ease)})`,
            }}
          >
            <span style={{ fontSize: 520, letterSpacing: "-0.06em", lineHeight: 1 }}>25</span>
            <span style={{ fontSize: 190, letterSpacing: "-0.03em" }}>BULAN</span>
          </div>
          <div style={{ position: "absolute", left: 0, right: 0, top: 760, textAlign: "center", fontFamily: F.serif, fontStyle: "italic", fontSize: 110, color: C.night }}>
            <RiseWords text="sebelum suspensi." start={tSeb} starts={[tSeb, L(w("months", "suspensi"))]} />
          </div>
        </AbsoluteFill>
      )}
      {/* second case */}
      {frame >= tSril && (
        <AbsoluteFill style={{ opacity: sril * (1 - prog(frame, dur - 8, 8)) }}>
          <Backdrop grid={0.25} tint="rgba(120,24,18,0.3)" />
          <div style={{ position: "absolute", left: 0, right: 0, top: 250, textAlign: "center" }}>
            <Kicker size={24} color={C.dim}>
              Kasus kedua · SRIL · Sri Rejeki Isman (Sritex)
            </Kicker>
          </div>
          <div style={{ position: "absolute", left: 0, right: 0, top: 320, textAlign: "center", fontFamily: F.display, fontWeight: 900, fontSize: 300, letterSpacing: "-0.05em", color: C.text, lineHeight: 1, transform: `scale(${1.15 - 0.15 * sril})` }}>
            42 <span style={{ fontSize: 130, letterSpacing: "-0.02em" }}>BULAN</span>
          </div>
          <div style={{ position: "absolute", left: 0, right: 0, top: 650, textAlign: "center", fontFamily: F.serif, fontStyle: "italic", fontSize: 84, color: C.red, opacity: prog(frame, tSril + 8, 12) }}>
            sebelum dinyatakan pailit.
          </div>
          <Kicker size={19} color={C.hint} style={{ position: "absolute", left: 0, right: 0, top: 790, textAlign: "center", opacity: prog(frame, tSril + 14, 12) }}>
            Pertama kali Sedang: 2021-Q1 · Pailit: 21 Okt 2024 · sumber: halaman /backtest
          </Kicker>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- 9. Outro

export const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const L = (m: number) => local("outro", m);
  const dur = scene("outro").dur;
  const tName = L(w("name", "afs"));
  const tP = L(w("tag", "peringatan"));
  const tS = L(w("tag", "sebelum"));
  const credits = prog(frame, L(lineEnd("tag")) + 4, 16);
  const out = 1 - prog(frame, dur - 14, 14);
  return (
    <AbsoluteFill style={{ opacity: out }}>
      <Backdrop grid={0.2} tint="rgba(120,24,18,0.25)" />
      <div style={{ position: "absolute", left: 960, top: 250, transform: "translate(-50%,-50%)", opacity: prog(frame, 0, 12) }}>
        <Emblem size={200} draw={prog(frame, 0, 26, easeInOut)} sweep={frame * 5} glow={0.7} />
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 390, display: "flex", justifyContent: "center" }}>
        {frame >= tName - 1 && <Wordmark start={tName - 1} size={140} stagger={1.4} />}
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 580, display: "flex", justifyContent: "center", alignItems: "baseline", gap: 28 }}>
        <div style={{ fontFamily: F.display, fontWeight: 700, fontSize: 72, color: C.text, letterSpacing: "-0.02em" }}>
          <RiseWords text="Peringatan dini." start={tP} starts={[tP, L(w("tag", "dini"))]} />
        </div>
        <div style={{ fontFamily: F.serif, fontStyle: "italic", fontSize: 90, color: C.red }}>
          <RiseWords text="Sebelum terlambat." start={tS} starts={[tS, L(w("tag", "terlambat"))]} />
        </div>
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 760, display: "flex", justifyContent: "center", gap: 18, opacity: credits, transform: `translateY(${(1 - credits) * 14}px)` }}>
        {["Powered by Sectors API", "Sectors Hackathon 2026 · Track 2 Automation & Workflows", "github.com/codeyzx/afs-sentinel"].map((t) => (
          <div key={t} style={{ fontFamily: F.mono, fontSize: 21, letterSpacing: "0.1em", color: C.dim, border: `1.5px solid ${C.lineStrong}`, borderRadius: 999, padding: "10px 22px", textTransform: t.startsWith("github") ? "none" : "uppercase" }}>
            {t}
          </div>
        ))}
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 880, textAlign: "center", fontFamily: F.display, fontSize: 22, color: C.hint, opacity: credits, lineHeight: 1.6 }}>
        Alat analisis &amp; informasi, bukan nasihat investasi.
        <br />
        Musik: “Impact Prelude” — Kevin MacLeod (incompetech.com), CC BY 4.0
      </div>
    </AbsoluteFill>
  );
};

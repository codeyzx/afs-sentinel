import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { FocusRing, Window3D } from "../components/Brand";
import { Backdrop } from "../components/Fx";
import { Phone } from "../components/Phone";
import { countValue, ease, easeInOut, Kicker, prog, RiseWords } from "../components/primitives";
import { markOf } from "../components/ScreenCapture";
import { RULES } from "../data";
import { C, F } from "../theme";
import { lineStart, local, scene, w } from "../timeline";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// ---------------------------------------------------------------- 5. Autonomous: every 3 days, no human

const Stat: React.FC<{ n: string; kicker: string; value: React.ReactNode; at: number; dimAt?: number; accent?: boolean }> = ({ n, kicker, value, at, dimAt, accent }) => {
  const frame = useCurrentFrame();
  const p = prog(frame, at, 14);
  const dim = dimAt === undefined ? 0 : prog(frame, dimAt, 10);
  if (frame < at - 1) return <div style={{ height: 150 }} />;
  return (
    <div style={{ height: 150, opacity: p * (1 - 0.6 * dim), transform: `translateX(${(1 - p) * -40}px)` }}>
      <div style={{ display: "flex", gap: 18, alignItems: "baseline" }}>
        <Kicker size={18} color={C.red}>
          {n}
        </Kicker>
        <Kicker size={18}>{kicker}</Kicker>
      </div>
      <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 84, letterSpacing: "-0.03em", lineHeight: 1.05, color: accent ? C.red : C.text, marginTop: 6 }}>{value}</div>
    </div>
  );
};

export const Auto: React.FC = () => {
  const frame = useCurrentFrame();
  const L = (m: number) => local("auto", m);
  const dur = scene("auto").dur;
  const t3 = L(w("auto", "tiga", 0));
  const tHuman = L(w("auto", "tanpa"));
  const tIa = L(w("auto", "ia"));
  const tApi = L(w("auto", "sectors"));
  const tScan = L(w("auto", "memindai"));
  const enter = prog(frame, 0, 18);
  const ry = interpolate(frame, [0, dur], [-26, -12]);
  const swap = prog(frame, tIa - 3, 8, easeInOut);
  const statusCard = { x: 224, y: 58, w: 1152, h: 230 };
  return (
    <AbsoluteFill>
      <Backdrop grid={0.4} drift={frame * 1.5} />
      {/* window: dashboard, then the audit log */}
      {frame < tIa + 4 && (
        <Window3D
          cap="dashboard"
          width={1180}
          x={1190 + (1 - enter) * 300 - swap * 200}
          y={520}
          ry={ry}
          rx={5}
          opacity={enter * (1 - swap)}
          timeMap={[
            [0, 0.2],
            [tIa, 0.9],
          ]}
          keys={[{ at: 0.2, target: statusCard, zoom: 1.6, dur: 0.6 }]}
          url="afs-sentinel.herokuapp.com"
          label="Data asli produksi"
          showCursor={false}
        >
          {(toScreen) => <FocusRing r={toScreen({ x: 250, y: 80, w: 560, h: 60 })} p={prog(frame, t3, 10) * (1 - prog(frame, tIa - 8, 6))} />}
        </Window3D>
      )}
      {frame >= tIa - 4 && (
        <Window3D
          cap="logs"
          width={1180}
          x={1190 + (1 - swap) * 260}
          y={520}
          ry={ry}
          rx={5}
          opacity={swap}
          timeMap={[
            [tIa - 4, 0.7],
            [tScan - 2, 2.4],
            [tScan, 7.0],
            [dur, 9.6],
          ]}
          keys={[
            { at: 0.7, target: "trigger1", zoom: 2.0, dur: 0.6 },
            { at: 7.0, target: null, dur: 0.5 },
            { at: 8.4, target: { x: 241, y: 230, w: 1118, h: 420 }, zoom: 1.5, dur: 0.8 },
          ]}
          url="afs-sentinel.herokuapp.com/logs"
          label="Jejak audit"
        >
          {(toScreen, t) => <FocusRing r={toScreen(markOf("logs", "trigger1"))} p={prog(frame, tHuman + 6, 8) * (t < 6.9 ? 1 : 0)} />}
        </Window3D>
      )}
      {/* left column: the four facts, each on its word */}
      <div style={{ position: "absolute", left: 110, top: 250 }}>
        <Stat n="01" kicker="Jadwal otomatis" value="tiap 3 hari" at={t3} dimAt={tHuman} />
        <Stat n="02" kicker="Pemicu: sistem" value="tanpa manusia" at={tHuman} dimAt={tApi} />
        <Stat n="03" kicker="Sumber data" value="Sectors API" at={tApi} dimAt={tScan} accent />
        <Stat n="04" kicker="Dipindai tiap run" value={<>{countValue(frame, 0, 33, tScan, 24)} emiten</>} at={tScan} />
      </div>
      {/* data stream from the API stat into the window */}
      {frame >= tApi && (
        <svg width={1920} height={1080} style={{ position: "absolute", inset: 0, opacity: prog(frame, tApi, 8) * (1 - prog(frame, dur - 12, 10)) }}>
          {[0, 1, 2].map((i) => (
            <path
              key={i}
              d={`M 560 ${545 + i * 16} C 700 ${545 + i * 16}, 640 ${470 + i * 40}, 760 ${470 + i * 40}`}
              stroke={C.red}
              strokeWidth={2.5}
              fill="none"
              strokeDasharray="10 18"
              strokeDashoffset={-(frame - tApi) * 6 - i * 9}
              opacity={0.85}
            />
          ))}
        </svg>
      )}
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- 6. Six forensic rules

export const Rules: React.FC = () => {
  const frame = useCurrentFrame();
  const L = (m: number) => local("rules", m);
  const dur = scene("rules").dur;
  const t0 = L(lineStart("rules"));
  const cues: [number, number][] = [
    [0, L(w("rules", "laba"))],
    [1, L(w("rules", "kas"))],
    [3, L(w("rules", "utang"))],
    [2, L(w("rules", "risiko"))],
  ];
  const tAll = L(w("rules", "bayar")) + 10;
  const active = (i: number) => {
    let on = 0;
    for (let k = 0; k < cues.length; k++) {
      const [idx, at] = cues[k];
      const next = k === 1 ? cues[2][1] : cues[k + 1]?.[1] ?? tAll;
      // cards 1 and 2 stay lit together ("laba tanpa kas")
      const end = idx === 0 ? cues[2][1] : next;
      if (idx === i) on = Math.max(on, prog(frame, at, 6) * (1 - prog(frame, end, 6)));
    }
    return on;
  };
  const anyActive = cues.some(([, at]) => frame >= at) && frame < tAll;
  const final = prog(frame, tAll, 12);
  const CW = 270;
  const GAP = 22;
  const total = RULES.length * CW + (RULES.length - 1) * GAP;
  return (
    <AbsoluteFill>
      <Backdrop grid={0.35} drift={frame * 2} />
      <Kicker size={22} color={C.dim} style={{ position: "absolute", left: 0, right: 0, top: 150, textAlign: "center", opacity: prog(frame, t0, 12) }}>
        6 Forensic Rule · data laporan keuangan dari Sectors API
      </Kicker>
      <AbsoluteFill style={{ perspective: 1800 }}>
        <div style={{ position: "absolute", left: 960 - total / 2, top: 250, width: total, height: 520, transformStyle: "preserve-3d", transform: `rotateX(${interpolate(frame, [0, dur], [14, 6])}deg)` }}>
          {RULES.map((r, i) => {
            const dealt = prog(frame, t0 + 2 + i * 3, 14, ease);
            const a = active(i);
            const dim = anyActive && a < 0.5 ? 0.42 : 1;
            return (
              <div
                key={r.name}
                style={{
                  position: "absolute",
                  left: i * (CW + GAP),
                  top: 0,
                  width: CW,
                  height: 480,
                  transform: `translateY(${(1 - dealt) * 380 - a * 34}px) rotateZ(${(1 - dealt) * (i - 2.5) * 6}deg) scale(${1 + a * 0.06})`,
                  opacity: dealt * dim,
                  background: a > 0 ? "linear-gradient(180deg,#2A1210,#120A0A)" : "linear-gradient(180deg,#141C22,#0D1317)",
                  border: `1.5px solid ${a > 0 ? `rgba(255,59,48,${0.4 + 0.6 * a})` : C.lineStrong}`,
                  borderRadius: 16,
                  padding: 26,
                  boxSizing: "border-box",
                  display: "flex",
                  flexDirection: "column",
                  boxShadow: `0 30px 70px rgba(0,0,0,0.6), 0 0 ${70 * a}px rgba(255,59,48,${0.45 * a})`,
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: 54,
                    height: 54,
                    borderRadius: 27,
                    border: `2px solid ${a > 0 ? C.red : C.lineStrong}`,
                    background: a > 0 ? C.red : "transparent",
                    display: "grid",
                    placeItems: "center",
                    fontFamily: F.mono,
                    fontWeight: 700,
                    fontSize: 24,
                    color: C.text,
                  }}
                >
                  {i + 1}
                </div>
                <div style={{ fontFamily: F.display, fontWeight: 700, fontSize: 36, lineHeight: 1.1, color: C.text, marginTop: 30, letterSpacing: "-0.01em" }}>{r.name}</div>
                <div style={{ fontFamily: F.display, fontSize: 24, lineHeight: 1.3, color: a > 0 ? "#FFD2CE" : C.dim, marginTop: 14 }}>{r.plain}</div>
                <div style={{ marginTop: "auto" }}>
                  <Kicker size={15} color={C.hint}>
                    Bobot
                  </Kicker>
                  <div style={{ fontFamily: F.mono, fontWeight: 700, fontSize: 44, color: final > 0 ? C.text : C.hint }}>{r.weight}</div>
                  <div style={{ height: 6, borderRadius: 3, marginTop: 8, background: C.line }}>
                    <div style={{ height: 6, borderRadius: 3, width: `${(r.weight / 25) * 100 * final}%`, background: C.red }} />
                  </div>
                </div>
                {/* scan line while active */}
                {a > 0.2 && (
                  <div
                    style={{
                      position: "absolute",
                      left: 0,
                      right: 0,
                      top: `${((frame * 4) % 120) - 10}%`,
                      height: 60,
                      background: "linear-gradient(180deg, transparent, rgba(255,59,48,0.25), transparent)",
                    }}
                  />
                )}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>
      <div style={{ position: "absolute", left: 0, right: 0, top: 800, display: "flex", justifyContent: "center", alignItems: "center", gap: 22, opacity: final, transform: `translateY(${(1 - final) * 20}px)` }}>
        <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 56, color: C.text, letterSpacing: "-0.02em" }}>→ skor risiko komposit</div>
        <div style={{ fontFamily: F.mono, fontWeight: 700, fontSize: 56, color: C.red }}>0–100</div>
      </div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- 7. Alert on Telegram, then the evidence

export const Alert: React.FC = () => {
  const frame = useCurrentFrame();
  const L = (m: number) => local("alert", m);
  const dur = scene("alert").dur;
  const tOdd = L(w("alert", "janggal"));
  const tWarn = L(w("alert", "peringatan"));
  const tTg = L(w("alert", "telegram"));
  const tProof = L(lineStart("proof"));
  const tAi = L(w("proof", "ringkasan"));
  const tEvid = L(w("proof", "bukti"));
  const tTrace = L(w("proof", "dilacak"));
  const side = prog(frame, tProof - 6, 18, easeInOut);
  const swap = prog(frame, tEvid - 3, 8, easeInOut);
  const winIn = prog(frame, tProof - 2, 16);
  return (
    <AbsoluteFill>
      <Backdrop grid={0.3} tint="rgba(30,70,100,0.35)" />
      {/* headline */}
      <div style={{ position: "absolute", left: 120, top: 300, opacity: 1 - side }}>
        <div style={{ fontFamily: F.display, fontWeight: 800, fontSize: 110, lineHeight: 1, letterSpacing: "-0.035em", color: C.text }}>
          <RiseWords text="ada yang janggal?" start={tOdd - 6} stagger={2} />
        </div>
        <div style={{ fontFamily: F.serif, fontStyle: "italic", fontSize: 76, color: C.red, marginTop: 20 }}>
          <RiseWords text="langsung ke Telegram." start={tWarn} stagger={3} />
        </div>
        <Kicker size={17} color={C.hint} style={{ marginTop: 40, opacity: prog(frame, tTg, 10) }}>
          Rekonstruksi dari teks pesan bot asli · Incident AFS-2026-Q2-0003
        </Kicker>
      </div>
      {/* phone */}
      <div
        style={{
          position: "absolute",
          left: interpolate(side, [0, 1], [1290, 330]),
          top: 540,
          transform: `translate(-50%,-50%) perspective(1600px) rotateY(${interpolate(side, [0, 1], [-14, 14])}deg) rotateZ(${interpolate(side, [0, 1], [2, -2])}deg) scale(${interpolate(side, [0, 1], [0.8, 0.66]) * (0.94 + 0.06 * prog(frame, 0, 20))})`,
          opacity: prog(frame, 0, 10) * (1 - prog(frame, dur - 10, 10)),
        }}
      >
        <Phone notifyAt={tWarn} openAt={tTg + 6} marks={{ insight: tAi, bullets: tEvid }} />
      </div>
      {/* the web app: AI summary, then the traceable evidence */}
      {frame >= tProof - 4 && frame < tEvid + 4 && (
        <Window3D
          cap="incident-ai"
          width={1240}
          x={1210 + (1 - winIn) * 300}
          y={530}
          ry={-10}
          rx={3}
          opacity={winIn * (1 - swap)}
          timeMap={[
            [tProof - 4, 1.0],
            [tEvid, 2.6],
          ]}
          keys={[{ at: 1.0, target: "ai", zoom: 1.35, dur: 0.6 }]}
          url="afs-sentinel.herokuapp.com/incidents/AFS-2026-Q2-0003"
          label="Ringkasan AI"
          showCursor={false}
        />
      )}
      {frame >= tEvid - 4 && (
        <Window3D
          cap="incident-evidence"
          width={1240}
          x={1210}
          y={530}
          ry={-10}
          rx={3}
          opacity={swap * (1 - prog(frame, dur - 8, 8))}
          timeMap={[
            [tEvid - 4, 7.1],
            [tTrace, 8.2],
            [tTrace + 10, 11.3],
            [dur, 12.4],
          ]}
          keys={[
            { at: 7.1, target: "formula", zoom: 2.0, dur: 0.6, pad: 30 },
            { at: 11.3, target: "endpoint", zoom: 2.2, dur: 0.5 },
          ]}
          url="afs-sentinel.herokuapp.com/incidents/AFS-2026-Q2-0003"
          label="Bukti perhitungan"
        />
      )}
      {/* captions for the evidence */}
      <div style={{ position: "absolute", left: 640, top: 150, opacity: winIn }}>
        <Kicker size={20} color={C.dim}>
          {frame < tEvid ? "Ringkasan AI · ditulis dari 6 Rule Finding" : frame < tTrace + 10 ? "Formula + input dari laporan" : "Sumber: /v2/financials/quarterly/UNVR.JK/"}
        </Kicker>
      </div>
    </AbsoluteFill>
  );
};

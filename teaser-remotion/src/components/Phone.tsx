import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { C, F } from "../theme";
import { prog, useSpring } from "./primitives";

// Telegram, dark theme, on a phone. The text is the bot's real message format (afs/telegram.py
// format_incident_message) filled with the live UNVR Incident AFS-2026-Q2-0003.
const T = { bg: "#0E1621", head: "#17212B", bubble: "#182533", text: "#F5F5F5", hint: "#7D8E9E", accent: "#64B5EF", button: "#22374C" };

export const ALERT = {
  title: "🟡 Sedang · UNVR — Unilever Indonesia Tbk",
  score: "Skor 45/100 · Laporan 2026-Q2",
  insight: "Sebagian besar laba tercatat belum menjadi uang tunai dan skor kesehatan keuangan masuk zona merah.",
  bullets: ["22,7% dari aset tercatat sebagai laba yang belum menjadi uang tunai (batas wajar 10%).", "Skor Altman 0,57 — masuk zona kesulitan keuangan."],
  time: "12:07",
};

const PW = 520;
const PH = 1060;

/**
 * `notifyAt`: the lock-screen banner drops in. `openAt`: the chat opens with the full message.
 * `marks`: frames where the insight line / bullets get highlighted.
 */
export const Phone: React.FC<{ notifyAt: number; openAt: number; marks?: { insight?: number; bullets?: number; button?: number } }> = ({ notifyAt, openAt, marks = {} }) => {
  const frame = useCurrentFrame();
  const drop = useSpring(notifyAt, { damping: 15, stiffness: 170 });
  const open = prog(frame, openAt, 12);
  const bubble = useSpring(openAt + 6, { damping: 16, stiffness: 150 });
  const hl = (at?: number) => (at === undefined ? 0 : prog(frame, at, 10));
  return (
    <div
      style={{
        width: PW,
        height: PH,
        borderRadius: 74,
        background: "#05070A",
        padding: 16,
        boxSizing: "border-box",
        boxShadow: "0 0 0 2px #2A3238, 0 0 0 7px #0C1013, 0 60px 140px rgba(0,0,0,0.8), 0 0 80px rgba(100,181,239,0.10)",
        position: "relative",
      }}
    >
      <div style={{ position: "relative", width: "100%", height: "100%", borderRadius: 60, overflow: "hidden", background: T.bg }}>
        {/* lock screen */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "radial-gradient(ellipse 120% 80% at 50% 0%, #1B2B38 0%, #0A1016 60%)",
            opacity: 1 - open,
          }}
        >
          <div style={{ textAlign: "center", marginTop: 120, color: "#E8EEF2", fontFamily: F.display }}>
            <div style={{ fontSize: 26, opacity: 0.8, fontWeight: 500 }}>Selasa, 22 September</div>
            <div style={{ fontSize: 140, fontWeight: 600, letterSpacing: "-0.03em", lineHeight: 1.05 }}>{ALERT.time}</div>
          </div>
          <div
            style={{
              position: "absolute",
              left: 18,
              right: 18,
              top: 380,
              transform: `translateY(${(1 - drop) * -420}px) scale(${0.92 + 0.08 * drop})`,
              opacity: frame >= notifyAt ? 1 : 0,
              background: "rgba(40,52,62,0.82)",
              backdropFilter: "blur(20px)",
              borderRadius: 30,
              padding: "20px 22px",
              color: "#F2F6F8",
              fontFamily: F.display,
              boxShadow: "0 20px 50px rgba(0,0,0,0.5)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
              <TgIcon size={36} />
              <div style={{ fontSize: 20, fontWeight: 600, letterSpacing: "0.02em", opacity: 0.85 }}>TELEGRAM</div>
              <div style={{ marginLeft: "auto", fontSize: 19, opacity: 0.6 }}>sekarang</div>
            </div>
            <div style={{ fontSize: 23, fontWeight: 700 }}>AFS Sentinel</div>
            <div style={{ fontSize: 22, lineHeight: 1.35, marginTop: 4, opacity: 0.92 }}>{ALERT.title}</div>
            <div style={{ fontSize: 21, opacity: 0.72 }}>{ALERT.score}</div>
          </div>
        </div>

        {/* chat */}
        <div style={{ position: "absolute", inset: 0, opacity: open, transform: `scale(${1.04 - 0.04 * open})` }}>
          <div style={{ height: 150, background: T.head, display: "flex", alignItems: "flex-end", padding: "0 26px 18px", gap: 16, boxSizing: "border-box" }}>
            <div style={{ fontSize: 34, color: T.accent }}>‹</div>
            <div style={{ width: 56, height: 56, borderRadius: 28, background: "linear-gradient(135deg,#FF5A4E,#C4231A)", display: "grid", placeItems: "center", color: "#fff", fontFamily: F.display, fontWeight: 800, fontSize: 20 }}>AFS</div>
            <div style={{ fontFamily: F.display }}>
              <div style={{ color: T.text, fontWeight: 600, fontSize: 25 }}>AFS Sentinel</div>
              <div style={{ color: T.hint, fontSize: 19 }}>bot</div>
            </div>
          </div>
          <div style={{ padding: "26px 20px", transform: `translateY(${(1 - bubble) * 60}px)`, opacity: bubble }}>
            <div style={{ background: T.bubble, borderRadius: "22px 22px 8px 8px", padding: "18px 20px 12px", color: T.text, fontFamily: F.display, fontSize: 21, lineHeight: 1.42 }}>
              <div style={{ fontWeight: 700 }}>{ALERT.title}</div>
              <div>{ALERT.score}</div>
              <div style={{ height: 14 }} />
              <Hl p={hl(marks.insight)}>
                <span>🤖 </span>
                <i>{ALERT.insight}</i>
              </Hl>
              <div style={{ height: 14 }} />
              {ALERT.bullets.map((b, i) => (
                <Hl key={i} p={hl(marks.bullets !== undefined ? marks.bullets + i * 6 : undefined)}>
                  • {b}
                </Hl>
              ))}
              <div style={{ textAlign: "right", color: T.hint, fontSize: 16, marginTop: 6 }}>{ALERT.time}</div>
            </div>
            <div
              style={{
                marginTop: 5,
                height: 60,
                borderRadius: "8px 8px 22px 22px",
                background: marks.button !== undefined && frame >= marks.button ? interpolate(frame - marks.button, [0, 8], [0, 1], { extrapolateRight: "clamp" }) > 0.5 ? "#2E5478" : T.button : T.button,
                color: T.text,
                fontFamily: F.display,
                fontWeight: 600,
                fontSize: 22,
                display: "grid",
                placeItems: "center",
              }}
            >
              Buka Incident ↗
            </div>
          </div>
        </div>
        {/* island */}
        <div style={{ position: "absolute", top: 22, left: "50%", width: 150, height: 42, marginLeft: -75, borderRadius: 21, background: "#000" }} />
      </div>
    </div>
  );
};

const Hl: React.FC<{ p: number; children: React.ReactNode }> = ({ p, children }) => (
  <div style={{ position: "relative" }}>
    {p > 0 && (
      <div style={{ position: "absolute", inset: "-3px -10px", background: "rgba(255,59,48,0.16)", borderLeft: `4px solid ${C.red}`, borderRadius: 6, transformOrigin: "left", transform: `scaleX(${p})` }} />
    )}
    <div style={{ position: "relative" }}>{children}</div>
  </div>
);

const TgIcon: React.FC<{ size: number }> = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 48 48">
    <circle cx={24} cy={24} r={24} fill="#2AABEE" />
    <path d="M10.5 23.4 34.6 14c1.1-.4 2.1.3 1.7 2l-4.1 19.4c-.3 1.4-1.1 1.7-2.3 1.1l-6.3-4.7-3 2.9c-.3.3-.6.6-1.3.6l.5-6.5 11.8-10.7c.5-.5-.1-.7-.8-.3L16.3 27l-6.3-2c-1.4-.4-1.4-1.4.5-1.6Z" fill="#fff" />
  </svg>
);

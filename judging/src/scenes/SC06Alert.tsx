import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Captions, SceneHeader, SfxTrack } from "../components/Chrome";
import { FaceCam, NameTag } from "../components/FaceCam";
import { easeInOut, FadeIn, Kicker, Paper, useProgress } from "../components/primitives";
import { TelegramWindow, TG_LAYOUT, tgHtml, TgToast } from "../components/Telegram";
import { clockWib, formatWib, REAL, runSummary } from "../data";
import { atWord } from "../timeline";
import { C, F } from "../theme";
import { PIP, type SceneProps } from "./util";

const WIN = { left: 96, top: 112 };

export const SC06Alert: React.FC<SceneProps> = ({ scene, index }) => {
  const frame = useCurrentFrame();
  const line = scene.lines[0];
  const arrive = atWord(scene, 0, "menerima");
  const sevAt = atWord(scene, 0, "tingkat");
  const scoreAt = atWord(scene, 0, "skor", 1);
  const findAt = atWord(scene, 0, "tiga");
  const zoomAt = atWord(scene, 0, "Satu");
  const clickAt = atWord(scene, 0, "Incident");

  const prevRun = REAL.runs.find((r) => r.id === 2)!;
  const messages = [
    { html: tgHtml(runSummary(prevRun)), time: clockWib(prevRun.startedAt), at: -60 },
    {
      html: tgHtml(REAL.alert.text),
      time: clockWib(REAL.alert.sentAt),
      button: REAL.alert.button,
      at: arrive,
      marks: { 0: sevAt, 1: scoreAt, 5: findAt, 6: findAt + 8 },
    },
  ];

  // camera: zoom around the "Buka Incident" button (bottom of the chat, see TG_LAYOUT)
  const L = TG_LAYOUT;
  const btn = { x: L.side + L.bubbleLeft, y: L.height - L.input - 18 - L.buttonH, w: L.bubbleW, h: L.buttonH };
  const zoom = useProgress(zoomAt, 26, easeInOut);
  const s = 1 + zoom * 0.75;
  const ox = btn.x + btn.w / 2;
  const oy = btn.y + btn.h / 2;

  // cursor flies to the button and clicks
  const fly = useProgress(clickAt - 24, 22, easeInOut);
  const cx = interpolate(fly, [0, 1], [ox + 260, ox]);
  const cy = interpolate(fly, [0, 1], [oy - 220, oy + 6]);
  const clickAge = frame - clickAt;
  const glow = interpolate(frame, [clickAt - 6, clickAt, clickAt + 10], [0, 1, 0.6], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const flash = interpolate(frame, [clickAt + 4, clickAt + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      <Paper>
        <SceneHeader scene={scene} index={index} />
        <div style={{ position: "absolute", ...WIN, width: L.width, height: L.height, overflow: "hidden", borderRadius: 14 }}>
          <div style={{ position: "absolute", inset: 0, transformOrigin: `${ox}px ${oy}px`, transform: `scale(${s})` }}>
            <TelegramWindow messages={messages} buttonGlow={glow} style={{ left: 0, top: 0 }} />
          </div>
          {frame >= clickAt - 24 && (
            <svg width={34} height={34} viewBox="0 0 24 24" style={{ position: "absolute", left: cx - 4, top: cy - 2, filter: "drop-shadow(0 2px 3px rgba(0,0,0,0.5))", transform: `scale(${clickAge >= 0 && clickAge < 5 ? 0.82 : 1})` }}>
              <path d="M4 2 L4 19 L8.5 15 L11.5 21.5 L14.2 20.3 L11.3 14 L17.5 14 Z" fill="#fff" stroke="#111" strokeWidth={1.4} strokeLinejoin="round" />
            </svg>
          )}
          {clickAge >= 0 && clickAge < 18 && (
            <div style={{ position: "absolute", left: ox - 40, top: oy - 40, width: 80, height: 80, borderRadius: 40, border: `3px solid ${C.marker}`, transform: `scale(${0.3 + (clickAge / 18) * 1.4})`, opacity: 1 - clickAge / 18 }} />
          )}
        </div>
        <TgToast at={arrive} title="AFS Sentinel" body="🟡 Sedang · UNVR — Unilever Indonesia Tbk · Skor 45/100" style={{ left: WIN.left + L.width - 500, top: WIN.top + 80 }} />

        <FadeIn start={arrive + 20} dur={14} y={6} style={{ position: "absolute", left: WIN.left, top: WIN.top + L.height + 14 }}>
          <Kicker size={14}>
            Rekonstruksi tampilan dari pesan bot asli · dikirim {formatWib(REAL.alert.sentAt)} · {REAL.alert.eventId}
          </Kicker>
        </FadeIn>

        <FaceCam clip={line.clips[0]} who="Yahya" playFrom={line.from} playDur={line.dur} style={{ ...PIP }} />
        <NameTag who="Yahya" start={10} style={{ left: PIP.left + 20, top: PIP.top + PIP.height - 96 }} dark />
        <div style={{ position: "absolute", left: PIP.left, top: PIP.top + PIP.height + 30, width: PIP.width }}>
          {[
            { t: sevAt, k: "Tingkat keparahan" },
            { t: scoreAt, k: "Skor risiko" },
            { t: findAt, k: "Temuan teratas, bahasa awam" },
          ].map((x) => (
            <FadeIn key={x.k} start={x.t} dur={10} x={-14} y={0}>
              <div style={{ fontFamily: F.sans, fontSize: 24, fontWeight: 600, color: C.ink, display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
                <span style={{ width: 12, height: 12, background: C.marker, border: `1.5px solid ${C.ink}`, borderRadius: 2 }} />
                {x.k}
              </div>
            </FadeIn>
          ))}
        </div>
      </Paper>
      <AbsoluteFill style={{ background: "#FBF8F2", opacity: flash, pointerEvents: "none" }} />
      <Captions lines={scene.lines} />
      <SfxTrack
        cues={[
          { at: arrive, name: "ping", volume: 0.6 },
          { at: sevAt, name: "marker", volume: 0.25 },
          { at: scoreAt, name: "marker", volume: 0.25 },
          { at: findAt, name: "marker", volume: 0.25 },
          { at: zoomAt, name: "whoosh", volume: 0.25 },
          { at: clickAt, name: "click", volume: 0.6 },
          { at: clickAt + 4, name: "whoosh-big", volume: 0.3 },
        ]}
      />
    </AbsoluteFill>
  );
};

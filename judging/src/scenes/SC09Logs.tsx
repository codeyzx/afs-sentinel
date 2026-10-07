import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Captions, SceneHeader, SfxTrack } from "../components/Chrome";
import { FaceCam, NameTag } from "../components/FaceCam";
import { DrawCircle, easeInOut, FadeIn, Kicker, Paper, useProgress } from "../components/primitives";
import { ScreenCapture, type Rect } from "../components/ScreenCapture";
import { TelegramWindow, tgHtml } from "../components/Telegram";
import { clockWib, REAL, runSummary } from "../data";
import { atWord } from "../timeline";
import { C, F } from "../theme";
import { PIP, SCREEN, type SceneProps } from "./util";

// Columns of the three newest (scheduled) rows on /logs, in page pixels.
const ROWS = { y: 190, h: 132 };
const COL: Record<string, Rect> = {
  start: { x: 246, ...ROWS, w: 190 },
  trigger: { x: 618, ...ROWS, w: 150 },
  scanned: { x: 836, ...ROWS, w: 104 },
  credits: { x: 1186, ...ROWS, w: 60 },
};

export const SC09Logs: React.FC<SceneProps> = ({ scene, index }) => {
  const line = scene.lines[0];
  const w = (word: string) => atWord(scene, 0, word);
  const triggerAt = w("Label");
  const stampAt = w("timestamp");
  const scannedAt = w("jumlah");
  const creditAt = w("kredit");
  const tgAt = w("Setiap");
  const slide = useProgress(tgAt - 6, 22, easeInOut);

  const scheduled = REAL.runs.filter((r) => r.trigger === "SCHEDULER").slice(0, 3).reverse();
  const messages = scheduled.map((r, i) => ({
    html: tgHtml(runSummary(r)),
    time: clockWib(r.startedAt),
    at: i === scheduled.length - 1 ? tgAt + 14 : -60,
  }));

  return (
    <AbsoluteFill>
      <Paper>
        <SceneHeader scene={scene} index={index} />
        <div style={{ opacity: 1 - slide * 0.35 }}>
          <ScreenCapture
            cap="logs"
            width={SCREEN.width}
            style={{ left: SCREEN.left, top: SCREEN.top }}
            url="afs-sentinel.herokuapp.com/logs"
            exhibit="Exhibit 07 · Log Audit"
            showCursor={false}
            timeMap={[
              [line.from, 0.3],
              [triggerAt, 1.8],
              [tgAt, 6.6],
            ]}
            keys={[
              { target: "table", at: 0.5, zoom: 1.0, dur: 0.6 },
              { target: { x: 241, y: 160, w: 1010, h: 175 }, at: 1.7, zoom: 1.55, dur: 1 },
            ]}
          >
            {(toScreen, t) => (
              <>
                {t > 2.2 && <DrawCircle {...toScreen(COL.trigger)} start={triggerAt + 10} />}
                {t > 2.2 && <DrawCircle {...toScreen(COL.start)} start={stampAt} color={C.ink} stroke={4} />}
                {t > 2.2 && <DrawCircle {...toScreen(COL.scanned)} start={scannedAt} color={C.ink} stroke={4} />}
                {t > 2.2 && <DrawCircle {...toScreen(COL.credits)} start={creditAt} color={C.ink} stroke={4} />}
                <Label rect={toScreen(COL.trigger)} start={triggerAt + 22}>
                  dipicu scheduler · tak disentuh siapa pun
                </Label>
              </>
            )}
          </ScreenCapture>
        </div>

        {slide > 0 && (
          <div
            style={{
              position: "absolute",
              left: 300,
              top: 214,
              width: 1280,
              height: 800,
              transform: `translateX(${(1 - slide) * 900}px) scale(0.8)`,
              transformOrigin: "0 0",
              opacity: slide,
            }}
          >
            <TelegramWindow messages={messages} />
            <div style={{ position: "absolute", top: 812, left: 0 }}>
              <Kicker size={16}>Rekonstruksi tampilan dari pesan ringkasan run asli · tiga run Terjadwal terakhir</Kicker>
            </div>
          </div>
        )}

        <FaceCam clip={line.clips[0]} who="Yahya" playFrom={line.from} playDur={line.dur} style={{ ...PIP }} />
        <NameTag who="Yahya" start={10} style={{ left: PIP.left + 20, top: PIP.top + PIP.height - 96 }} dark />
        <div style={{ position: "absolute", left: PIP.left, top: PIP.top + PIP.height + 30, width: PIP.width }}>
          {[
            { t: stampAt, k: "Timestamp 08:00 WIB" },
            { t: scannedAt, k: "33 emiten dipindai" },
            { t: creditAt, k: "Kredit API tercatat" },
            { t: tgAt, k: "Lapor ke Telegram, walau nol" },
          ].map((x) => (
            <FadeIn key={x.k} start={x.t} dur={10} x={-14} y={0}>
              <div style={{ fontFamily: F.sans, fontSize: 24, fontWeight: 600, color: C.ink, display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
                <span style={{ width: 12, height: 12, background: C.red, borderRadius: 6 }} />
                {x.k}
              </div>
            </FadeIn>
          ))}
        </div>
      </Paper>
      <Captions lines={scene.lines} />
      <SfxTrack
        cues={[
          { at: triggerAt + 10, name: "marker", volume: 0.3 },
          { at: stampAt, name: "tick", volume: 0.2 },
          { at: scannedAt, name: "tick", volume: 0.2 },
          { at: creditAt, name: "tick", volume: 0.2 },
          { at: tgAt - 6, name: "whoosh", volume: 0.3 },
          { at: tgAt + 14, name: "ping", volume: 0.55 },
        ]}
      />
    </AbsoluteFill>
  );
};

const Label: React.FC<{ rect: Rect; start: number; children: React.ReactNode }> = ({ rect, start, children }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [start, start + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: rect.x - 20, top: rect.y + rect.h + 30, opacity: p, transform: `translateY(${(1 - p) * 10}px)` }}>
      <Kicker size={18} color="#FBF8F2" style={{ background: C.red, padding: "9px 14px", borderRadius: 6, whiteSpace: "nowrap" }}>
        {children}
      </Kicker>
    </div>
  );
};

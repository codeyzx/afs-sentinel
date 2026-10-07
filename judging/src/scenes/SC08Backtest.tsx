import React from "react";
import { AbsoluteFill } from "remotion";
import { Captions, SceneHeader, SfxTrack } from "../components/Chrome";
import { FaceCam, NameTag } from "../components/FaceCam";
import { CountUp, FadeIn, Kicker, Paper } from "../components/primitives";
import { markOf, ScreenCapture, type Rect } from "../components/ScreenCapture";
import { atWord, lineEnd } from "../timeline";
import { C, F } from "../theme";
import { PIP, SCREEN, type SceneProps } from "./util";

export const SC08Backtest: React.FC<SceneProps> = ({ scene, index }) => {
  const line = scene.lines[0];
  const w = (word: string) => atWord(scene, 0, word);
  const wsktAt = w("dua");
  const srilAt = w("empat");
  const claimAt = w("Kalimat");
  const claimW = markOf("backtest", "claim-wskt");
  const claimS = markOf("backtest", "claim-sril-42");

  return (
    <AbsoluteFill>
      <Paper>
        <SceneHeader scene={scene} index={index} />
        <ScreenCapture
          cap="backtest"
          width={SCREEN.width}
          style={{ left: SCREEN.left, top: SCREEN.top }}
          url="afs-sentinel.herokuapp.com/backtest"
          exhibit="Exhibit 06 · Backtest"
          timeMap={[
            [line.from, 0.2],
            [w("Kami"), 0.6],
            [w("Waskita"), 1.0],
            [w("Sritex") - 12, 6.9], // clicks the SRIL tab
            [w("empat"), 9.0],
            [lineEnd(scene, 0), 14.5],
          ]}
          keys={[
            { target: "chart-wskt", at: 0.55, zoom: 1.12, dur: 0.9 },
            { target: "claim-wskt", at: 0.95, zoom: 1.3, dur: 0.9 },
            { target: null, at: 7.0, dur: 0.7 },
            { target: "claim-sril-42", at: 8.9, zoom: 1.3, dur: 0.9 },
          ]}
        >
          {(toScreen, t) => (
            <>
              {t > 1 && t < 6.9 && <Underline rect={toScreen(claimW)} start={wsktAt} />}
              {t > 9.1 && <Underline rect={toScreen(claimS)} start={srilAt + 6} />}
              {t > 9.1 && (
                <FadeIn start={claimAt} dur={12} y={10} style={{ position: "absolute", left: toScreen(claimS).x, top: toScreen(claimS).y + toScreen(claimS).h + 24 }}>
                  <Kicker size={18} color="#FBF8F2" style={{ background: C.red, padding: "9px 14px", borderRadius: 6 }}>
                    ↑ kalimat ini dihasilkan sistem, bukan ditulis tangan
                  </Kicker>
                </FadeIn>
              )}
            </>
          )}
        </ScreenCapture>

        <FaceCam clip={line.clips[0]} who="Ais" playFrom={line.from} playDur={line.dur} style={{ ...PIP, height: 420 }} />
        <NameTag who="Ais" start={10} style={{ left: PIP.left + 20, top: PIP.top + 420 - 96 }} dark />

        <div style={{ position: "absolute", left: PIP.left, top: PIP.top + 450, width: PIP.width }}>
          <Big label="WSKT · lebih awal dari suspensi" start={wsktAt} to={25} />
          <Big label="SRIL · lebih awal dari pailit" start={srilAt} to={42} />
        </div>
      </Paper>
      <Captions lines={scene.lines} />
      <SfxTrack
        cues={[
          { at: wsktAt, name: "count", volume: 0.2, dur: 26 },
          { at: wsktAt + 26, name: "impact-soft", volume: 0.4 },
          { at: w("Sritex") - 4, name: "click", volume: 0.4 },
          { at: srilAt, name: "count", volume: 0.2, dur: 30 },
          { at: srilAt + 30, name: "impact", volume: 0.45, dur: 90 },
          { at: claimAt, name: "marker", volume: 0.3 },
        ]}
      />
    </AbsoluteFill>
  );
};

const Big: React.FC<{ label: string; start: number; to: number }> = ({ label, start, to }) => (
  <FadeIn start={start - 4} dur={10} y={14} style={{ borderTop: `1.5px solid ${C.ink}`, paddingTop: 8, marginBottom: 10 }}>
    <Kicker size={15}>{label}</Kicker>
    <div style={{ fontFamily: F.serif, fontSize: 92, fontWeight: 500, color: C.ink, lineHeight: 1, letterSpacing: "-0.03em" }}>
      <span style={{ color: C.red }}>
        <CountUp to={to} start={start} dur={to > 30 ? 30 : 26} />
      </span>{" "}
      <span style={{ fontSize: 48, fontStyle: "italic" }}>bulan</span>
    </div>
  </FadeIn>
);

const Underline: React.FC<{ rect: Rect; start: number }> = ({ rect, start }) => (
  <FadeIn start={start} dur={10} y={0} style={{ position: "absolute", left: rect.x - 6, top: rect.y - 4, width: rect.w + 12, height: rect.h + 8 }}>
    <div style={{ position: "absolute", inset: 0, background: "rgba(245,213,71,0.22)", borderLeft: `5px solid ${C.marker}`, borderRadius: 4 }} />
  </FadeIn>
);

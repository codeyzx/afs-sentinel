import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Captions, SceneHeader, SfxTrack } from "../components/Chrome";
import { FaceCam, NameTag } from "../components/FaceCam";
import { DrawCircle, FadeIn, Kicker, Marker, Paper, RiseWords } from "../components/primitives";
import { markOf, ScreenCapture, type Rect } from "../components/ScreenCapture";
import type { Person } from "../script";
import { atWord, lineEnd } from "../timeline";
import { C, F } from "../theme";
import { PIP, SCREEN, type SceneProps } from "./util";

const URL = "afs-sentinel.herokuapp.com/incidents/AFS-2026-Q2-0003";

export const SC07Incident: React.FC<SceneProps> = ({ scene, index }) => {
  const frame = useCurrentFrame();
  const [a, b, c] = scene.lines;
  const bStart = b.from - 10;
  const cStart = c.from - 10;
  const part = frame < bStart ? 0 : frame < cStart ? 1 : 2;
  const swapIn = (start: number) => interpolate(frame, [start, start + 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // white from the Telegram click
  const flash = interpolate(frame, [0, 12], [1, 0], { extrapolateRight: "clamp" });

  const speaker: { who: Person; line: typeof a } = part === 1 ? { who: "Ais", line: b } : { who: "Fathan", line: part === 0 ? a : c };

  return (
    <AbsoluteFill>
      <Paper>
        <SceneHeader scene={scene} index={index} />
        {part === 0 && <Evidence scene={scene} />}
        {part === 1 && (
          <div style={{ opacity: swapIn(bStart) }}>
            <AiSummary scene={scene} start={bStart} />
          </div>
        )}
        {part === 2 && (
          <div style={{ opacity: swapIn(cStart) }}>
            <Triage scene={scene} start={cStart} />
          </div>
        )}

        {/* PiP follows whoever is speaking */}
        <FaceCam key={speaker.line.clips[0]} clip={speaker.line.clips[0]} who={speaker.who} playFrom={speaker.line.from} playDur={speaker.line.dur} style={{ ...PIP, opacity: part === 0 ? 1 : swapIn(part === 1 ? bStart : cStart) }} />
        <NameTag key={`tag-${speaker.who}-${part}`} who={speaker.who} start={part === 0 ? 10 : part === 1 ? bStart + 4 : cStart + 4} style={{ left: PIP.left + 20, top: PIP.top + PIP.height - 96 }} dark />

        {part === 1 && (
          <div style={{ position: "absolute", left: PIP.left, top: PIP.top + PIP.height + 30, width: PIP.width }}>
            <RiseWords text="AI menarasikan," start={bStart + 12} style={{ fontFamily: F.serif, fontSize: 44, lineHeight: 1.05, color: C.ink }} />
            <div style={{ fontFamily: F.serif, fontSize: 44, lineHeight: 1.1, color: C.ink, fontStyle: "italic" }}>
              <FadeIn start={atWord(scene, 1, "tidak")} dur={10} y={10}>
                <Marker start={atWord(scene, 1, "pernah")}>tidak pernah menilai.</Marker>
              </FadeIn>
            </div>
          </div>
        )}
        {part === 0 && <EvidenceNotes scene={scene} />}
      </Paper>
      <AbsoluteFill style={{ background: "#FBF8F2", opacity: flash, pointerEvents: "none" }} />
      <Captions lines={scene.lines} />
      <SfxTrack
        cues={[
          { at: atWord(scene, 0, "dibuka"), name: "click", volume: 0.4 },
          { at: bStart, name: "whoosh", volume: 0.3 },
          { at: atWord(scene, 1, "pernah"), name: "marker", volume: 0.35 },
          { at: cStart, name: "whoosh", volume: 0.3 },
          { at: atWord(scene, 2, "diperiksa"), name: "stamp", volume: 0.4 },
        ]}
      />
    </AbsoluteFill>
  );
};

const Evidence: React.FC<{ scene: SceneProps["scene"] }> = ({ scene }) => {
  const m = (l: string) => markOf("incident-evidence", l);
  const w = (word: string, nth = 0) => atWord(scene, 0, word, nth);
  const verdict = m("verdict");
  const card = m("card");
  const formula = m("formula");
  const inputs = m("inputs");
  const endpoint = m("endpoint");
  const chart = m("chart");
  return (
    <ScreenCapture
      cap="incident-evidence"
      width={SCREEN.width}
      style={{ left: SCREEN.left, top: SCREEN.top }}
      url={URL}
      exhibit="Exhibit 03 · Incident"
      timeMap={[
        [scene.lines[0].from, 0.2],
        [w("Vonisnya"), 1.0],
        [w("Setiap"), 3.3], // scroll to the evidence cards
        [w("dibuka"), 6.4], // opens the Sloan card
        [w("rumusnya"), 7.4],
        [w("sampai"), 9.5], // scroll down to the endpoint
        [w("endpoint"), 11.4],
        [w("Grafik"), 14.0], // scroll to the chart
        [w("laba"), 16.2],
        [lineEnd(scene, 0), 20.8],
      ]}
      keys={[
        { target: "verdict", at: 0.3, zoom: 1.45, dur: 1.2 },
        { target: null, at: 3.0, dur: 0.9 },
        { target: "card", at: card.t - 0.1, zoom: 1.7, dur: 1 },
        { target: { x: formula.x, y: formula.y, w: inputs.w, h: inputs.y + inputs.h - formula.y }, at: 7.1, zoom: 1.45, dur: 1 },
        { target: "endpoint", at: endpoint.t - 0.3, zoom: 1.9, dur: 0.9 },
        { target: "chart", at: chart.t - 0.4, zoom: 1.12, dur: 1 },
      ]}
    >
      {(toScreen, t) => (
        <>
          {t > 0.9 && t < 3 && <DrawCircle {...shrink(toScreen(verdict))} start={w("Vonisnya")} />}
          {t > 11.6 && t < 13.9 && <DrawCircle {...toScreen(endpoint)} start={w("endpoint")} />}
          {t > 16.4 && <Legend rect={toScreen(chart)} start={w("naik")} />}
        </>
      )}
    </ScreenCapture>
  );
};

const shrink = (r: Rect): Rect => ({ x: r.x + 10, y: r.y + 4, w: r.w * 0.62, h: r.h - 8 });

const Legend: React.FC<{ rect: Rect; start: number }> = ({ rect, start }) => (
  <FadeIn start={start} dur={12} y={8} style={{ position: "absolute", left: rect.x + rect.w * 0.52, top: rect.y + 6 }}>
    <div style={{ background: C.red, color: "#FBF8F2", fontFamily: F.mono, fontSize: 18, padding: "8px 14px", borderRadius: 6 }}>Laba naik · kas operasi tertinggal</div>
  </FadeIn>
);

/** Side notes under the PiP name what the camera is showing. */
const EvidenceNotes: React.FC<{ scene: SceneProps["scene"] }> = ({ scene }) => {
  const items = [
    { t: atWord(scene, 0, "Vonisnya"), k: "Vonis & skor" },
    { t: atWord(scene, 0, "rumusnya"), k: "Rumus · angka mentah" },
    { t: atWord(scene, 0, "endpoint"), k: "Endpoint Sectors asal" },
    { t: atWord(scene, 0, "Grafik"), k: "Laba vs arus kas" },
  ];
  return (
    <div style={{ position: "absolute", left: PIP.left, top: PIP.top + PIP.height + 30, width: PIP.width }}>
      {items.map((x) => (
        <FadeIn key={x.k} start={x.t} dur={10} x={-14} y={0}>
          <div style={{ fontFamily: F.sans, fontSize: 24, fontWeight: 600, color: C.ink, display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
            <span style={{ width: 12, height: 12, background: C.red, borderRadius: 6 }} />
            {x.k}
          </div>
        </FadeIn>
      ))}
    </div>
  );
};

const AiSummary: React.FC<{ scene: SceneProps["scene"]; start: number }> = ({ scene, start }) => {
  const ai = markOf("incident-ai", "ai");
  const footer = markOf("incident-ai", "ai-footer");
  return (
    <ScreenCapture
      cap="incident-ai"
      width={SCREEN.width}
      style={{ left: SCREEN.left, top: SCREEN.top }}
      url={URL}
      exhibit="Exhibit 04 · Ringkasan AI"
      showCursor={false}
      timeMap={[
        [start, 0.2],
        [start + 50, 2.2],
        [scene.lines[1].from + scene.lines[1].dur, 7.6],
      ]}
      keys={[{ target: "ai", at: 1.6, zoom: 1.4, dur: 0.9, anchor: "top" }]}
    >
      {(toScreen, t) => (
        <>
          {t > 2.4 && <DrawCircle {...toScreen(footer)} start={atWord(scene, 1, "angka")} />}
          {t > 2.4 && (
            <FadeIn start={atWord(scene, 1, "angka") + 10} dur={12} y={8} style={{ position: "absolute", left: toScreen(footer).x, top: toScreen(ai).y + toScreen(ai).h + 18 }}>
              <Kicker size={17} color="#FBF8F2" style={{ background: C.red, padding: "8px 12px", borderRadius: 6 }}>
                Ditulis dari 6 Rule Finding — angka resminya ada di kartu bukti
              </Kicker>
            </FadeIn>
          )}
        </>
      )}
    </ScreenCapture>
  );
};

const Triage: React.FC<{ scene: SceneProps["scene"]; start: number }> = ({ scene, start }) => {
  const select = markOf("incident-triage", "select");
  const badge = markOf("incident-triage", "status-badge");
  const end = scene.lines[2].from + scene.lines[2].dur;
  return (
    <ScreenCapture
      cap="incident-triage"
      width={SCREEN.width}
      style={{ left: SCREEN.left, top: SCREEN.top }}
      url={URL}
      exhibit="Exhibit 05 · Triage"
      timeMap={[
        [start, 0.6],
        [atWord(scene, 2, "sedang"), 4.3],
        [end + 20, 6.6],
      ]}
      keys={[
        { target: { x: 236, y: 380, w: 700, h: 200 }, at: 0.6, zoom: 1.6, dur: 0.6 },
        // after saving, the page reloads at the top: banner + new status badge
        { target: { x: 240, y: 120, w: 1120, h: 200 }, at: 4.45, zoom: 1.45, dur: 0.6 },
      ]}
    >
      {(toScreen, t) => (
        <>
          {t > 1.9 && t < 4.1 && <DrawCircle {...toScreen(select)} start={atWord(scene, 2, "analis")} />}
          {t > 4.8 && <DrawCircle {...toScreen(badge)} start={atWord(scene, 2, "diperiksa")} />}
        </>
      )}
    </ScreenCapture>
  );
};

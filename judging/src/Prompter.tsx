import React from "react";
import { AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame } from "remotion";
import type { ClipId } from "./media";
import { SCENES, type Person } from "./script";
import { C, F, FPS } from "./theme";
import { phraseGroups, scheduleWords, type Word } from "./words";

/** Seconds of countdown before the first word; the take's speech starts exactly at this mark. */
export const COUNTDOWN = 3;
/** Seconds held after the last word ("keep still"). */
export const HOLD = 2;

export type PrompterClip = {
  clip: ClipId;
  who: Person;
  scene: string;
  text: string;
  target: number;
  direction: string;
  kind: "vo" | "cam" | "reaction";
};

export const PROMPTER_CLIPS: PrompterClip[] = SCENES.flatMap((s) => [
  ...s.lines.flatMap((l) =>
    l.clips.map((clip) => ({
      clip,
      who: (l.who === "Bertiga" ? clip.split("_").at(-1) : l.who) as Person,
      scene: `${s.id} · ${s.title}`,
      text: l.text,
      target: l.target,
      direction: l.direction,
      kind: l.kind,
    })),
  ),
  ...(s.reactions ?? []).map((r) => ({
    clip: r.clip,
    who: r.who,
    scene: `${s.id} · ${s.title}`,
    text: r.text,
    target: r.target,
    direction: r.direction,
    kind: "reaction" as const,
  })),
]);

export const prompterId = (clip: ClipId) => `Prompter-${clip.replace(/_/g, "-")}`;
export const prompterFrames = (p: PrompterClip) => Math.round((COUNTDOWN + p.target + HOLD) * FPS);

const INK = "#0E0D0B";
const TEXT = "#F4EFE6";

/**
 * Teleprompter for one clip. Start the camera, press play, read the word that lights up.
 * Text sits at the top of the screen so the eyes stay near a camera mounted above it.
 */
export const Prompter: React.FC<{ clip: ClipId }> = ({ clip }) => {
  const frame = useCurrentFrame();
  const p = PROMPTER_CLIPS.find((x) => x.clip === clip)!;
  const t = frame / FPS - COUNTDOWN; // seconds into the read
  const words = p.kind === "reaction" ? [] : scheduleWords(p.text, p.target);
  const progress = Math.min(1, Math.max(0, t / p.target));
  const done = t >= p.target;

  return (
    <AbsoluteFill style={{ background: INK, fontFamily: F.sans, color: TEXT }}>
      {/* progress along the very top edge */}
      <div style={{ position: "absolute", left: 0, top: 0, height: 10, width: `${progress * 100}%`, background: done ? "#5FD68E" : C.red }} />

      <div style={{ position: "absolute", left: 80, right: 80, top: 44, display: "flex", justifyContent: "space-between", fontFamily: F.mono, fontSize: 24, letterSpacing: "0.1em", color: "rgba(244,239,230,0.55)", textTransform: "uppercase" }}>
        <span>
          {p.clip} · {p.who}
        </span>
        <span>{t < 0 ? `±${p.target} dtk` : done ? "selesai" : `${Math.max(0, p.target - t).toFixed(1)} dtk`}</span>
      </div>

      <div style={{ position: "absolute", left: 80, right: 80, top: 110, height: 520 }}>
        {p.kind === "reaction" ? <ReactionCue p={p} t={t} /> : <Reading words={words} t={t} />}
      </div>

      {t < 0 && <Countdown t={t} />}
      {done && (
        <div style={{ position: "absolute", left: 0, right: 0, top: 660, textAlign: "center", fontFamily: F.mono, fontSize: 40, color: "#5FD68E", letterSpacing: "0.08em" }}>
          TAHAN DIAM · lalu hentikan rekaman
        </div>
      )}

      <div style={{ position: "absolute", left: 80, right: 80, bottom: 60, fontSize: 28, lineHeight: 1.4, color: "rgba(244,239,230,0.5)" }}>
        <span style={{ fontFamily: F.mono, fontSize: 22, letterSpacing: "0.1em", textTransform: "uppercase", color: C.red, marginRight: 14 }}>{p.scene}</span>
        {p.direction}
        {p.kind === "vo" ? " · suara saja (wajah tidak dipakai)" : ""}
      </div>

      {[3, 2, 1].map((n) => (
        <Sequence key={n} from={Math.round((COUNTDOWN - n) * FPS)} durationInFrames={8} layout="none">
          <Audio src={staticFile("audio/prompter-bip.wav")} />
        </Sequence>
      ))}
      <Sequence from={Math.round((COUNTDOWN + p.target) * FPS)} durationInFrames={10} layout="none">
        <Audio src={staticFile("audio/prompter-end.wav")} />
      </Sequence>
    </AbsoluteFill>
  );
};

const Countdown: React.FC<{ t: number }> = ({ t }) => {
  const n = Math.ceil(-t);
  const k = n + t; // 1 → 0 within the second
  return (
    <div style={{ position: "absolute", right: 90, top: 640, display: "flex", alignItems: "baseline", gap: 18 }}>
      <span style={{ fontFamily: F.mono, fontSize: 26, color: "rgba(244,239,230,0.55)", letterSpacing: "0.1em" }}>MULAI DALAM</span>
      <span style={{ fontFamily: F.serif, fontSize: 150, lineHeight: 1, color: C.marker, opacity: 0.4 + 0.6 * k }}>{n}</span>
    </div>
  );
};

/** Current phrase large with the spoken word lit; the next phrase small underneath. */
const Reading: React.FC<{ words: Word[]; t: number }> = ({ words, t }) => {
  const groups = phraseGroups(words);
  let gi = 0;
  for (let i = 0; i < groups.length; i++) if (t >= groups[i][0].start - 0.35) gi = i;
  const cur = groups[gi];
  const next = groups[gi + 1];
  const curIdx = words.findIndex((w) => t >= w.start && t < w.end);
  const inPause = t >= 0 && curIdx === -1 && t < words[words.length - 1].end;
  return (
    <div>
      <div style={{ fontSize: 76, fontWeight: 600, lineHeight: 1.3, letterSpacing: "-0.01em" }}>
        {cur.map((w, i) => {
          const gIdx = words.indexOf(w);
          const lit = gIdx === curIdx;
          const past = t >= w.end;
          return (
            <React.Fragment key={i}>
              <span
                style={{
                  background: lit ? C.marker : "transparent",
                  color: lit ? INK : past ? TEXT : "rgba(244,239,230,0.45)",
                  borderRadius: 8,
                  padding: "0 6px",
                  margin: "0 -6px",
                }}
              >
                {w.text}
              </span>{" "}
            </React.Fragment>
          );
        })}
      </div>
      {next && <div style={{ marginTop: 34, fontSize: 44, lineHeight: 1.3, color: "rgba(244,239,230,0.32)" }}>{next.map((w) => w.text).join(" ")}</div>}
      <div style={{ marginTop: 26, height: 40, fontFamily: F.mono, fontSize: 30, color: C.marker, opacity: inPause ? 1 : 0, letterSpacing: "0.3em" }}>· · jeda</div>
    </div>
  );
};

/** Silent clips: a timed cue instead of words. */
const ReactionCue: React.FC<{ p: PrompterClip; t: number }> = ({ p, t }) => {
  const steps = [
    { at: 0, text: "Diam, tatap kamera, senyum" },
    { at: p.target * 0.35, text: p.text.replace(/[()]/g, "") },
  ];
  const step = steps.filter((s) => t >= s.at).at(-1);
  const pulse = interpolate((t * 2) % 1, [0, 0.5, 1], [0.7, 1, 0.7]);
  return (
    <div style={{ fontSize: 80, fontWeight: 600, lineHeight: 1.2, color: step ? C.marker : "rgba(244,239,230,0.45)", opacity: step ? pulse : 1 }}>
      {step?.text ?? steps[0].text}
    </div>
  );
};

import React from "react";
import { AbsoluteFill, getRemotionEnvironment, Sequence } from "remotion";
import { InkWipe, MusicBed, SfxTrack, VoiceTrack } from "./components/Chrome";
import { Kicker } from "./components/primitives";
import { SC01Hook } from "./scenes/SC01Hook";
import { SC02Intro } from "./scenes/SC02Intro";
import { SC03Solution } from "./scenes/SC03Solution";
import { SC04Automation } from "./scenes/SC04Automation";
import { SC05Rules } from "./scenes/SC05Rules";
import { SC06Alert } from "./scenes/SC06Alert";
import { SC07Incident } from "./scenes/SC07Incident";
import { SC08Backtest } from "./scenes/SC08Backtest";
import { SC09Logs } from "./scenes/SC09Logs";
import { SC10Closing } from "./scenes/SC10Closing";
import { Intro } from "./scenes/Intro";
import { Outro, OUTRO_OVERLAP } from "./scenes/Outro";
import type { SceneProps } from "./scenes/util";
import { INTRO_FRAMES, MIN_FRAMES, OUTRO_FRAMES, videoFrames, type Timing } from "./timeline";
import { C, FPS } from "./theme";

const COMPONENTS: Record<string, React.FC<SceneProps>> = {
  SC01: SC01Hook,
  SC02: SC02Intro,
  SC03: SC03Solution,
  SC04: SC04Automation,
  SC05: SC05Rules,
  SC06: SC06Alert,
  SC07: SC07Incident,
  SC08: SC08Backtest,
  SC09: SC09Logs,
  SC10: SC10Closing,
};

/** Cuts that get an ink wipe; SC06→SC07 rides the white flash of the click instead. */
const NO_WIPE = new Set(["SC07"]);

export type JudgingProps = { timing: Timing };

export const Judging: React.FC<JudgingProps> = ({ timing }) => {
  const total = videoFrames(timing);
  const short = MIN_FRAMES - total;
  return (
    <AbsoluteFill style={{ background: C.paper }}>
      <Sequence durationInFrames={INTRO_FRAMES} name="Intro">
        <Intro dur={INTRO_FRAMES} />
      </Sequence>
      <Sequence from={INTRO_FRAMES} durationInFrames={timing.total} name="Adegan">
        {timing.scenes.map((s, i) => {
          const Comp = COMPONENTS[s.def.id];
          return (
            <Sequence key={s.def.id} from={s.from} durationInFrames={s.dur} name={`${s.def.id} · ${s.def.title}`}>
              <Comp scene={s} index={i} />
            </Sequence>
          );
        })}
        {timing.scenes.slice(1).map((s, i) =>
          NO_WIPE.has(s.def.id) ? null : <InkWipe key={s.def.id} at={s.from} dir={i % 2 ? -1 : 1} />,
        )}
        <SfxTrack
          cues={timing.scenes
            .slice(1)
            .filter((s) => !NO_WIPE.has(s.def.id))
            .map((s) => ({ at: s.from - 14, name: "whoosh", volume: 0.28 }))}
        />
        <VoiceTrack timing={timing} />
      </Sequence>
      <Sequence from={INTRO_FRAMES + timing.total - OUTRO_OVERLAP} durationInFrames={OUTRO_FRAMES + OUTRO_OVERLAP} name="Outro">
        <Outro dur={OUTRO_FRAMES + OUTRO_OVERLAP} />
      </Sequence>
      <Sequence from={INTRO_FRAMES} name="Musik">
        <MusicBed timing={timing} />
      </Sequence>
      {short > 0 && getRemotionEnvironment().isStudio && (
        <div style={{ position: "absolute", right: 24, bottom: 24, background: C.red, padding: "10px 16px", borderRadius: 8 }}>
          <Kicker color="#fff" size={18}>
            ⚠ Durasi {(total / FPS).toFixed(1)} dtk — kurang {(short / FPS).toFixed(1)} dtk dari minimal 3:00.
          </Kicker>
        </div>
      )}
    </AbsoluteFill>
  );
};

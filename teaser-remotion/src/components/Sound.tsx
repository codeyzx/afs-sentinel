import React from "react";
import { Audio, interpolate, Sequence, staticFile } from "remotion";
import { FPS } from "../theme";
import { LINES, MUSIC } from "../timeline";

export const VoiceTrack: React.FC = () => (
  <>
    {LINES.map((l) => (
      <Sequence key={l.id} from={l.at} durationInFrames={Math.ceil(l.duration * FPS) + 2} layout="none" name={`vo ${l.id}`}>
        <Audio src={l.src} volume={1} />
      </Sequence>
    ))}
  </>
);

// Spoken spans in master frames, for ducking the score under the voice.
const SPEECH = LINES.map((l) => [l.at, l.wf[l.wf.length - 1].end] as const);
const duckAt = (f: number) => {
  let d = 1;
  for (const [a, b] of SPEECH) {
    if (f >= a - 8 && f <= b + 10) {
      const edge = Math.min(f - (a - 8), b + 10 - f);
      d = Math.min(d, interpolate(edge, [0, 8], [1, 0], { extrapolateRight: "clamp" }));
    }
  }
  return d; // 1 = open, 0 = fully ducked
};

/** The score, in three sections that start and stop on the edit. */
export const Score: React.FC = () => (
  <>
    {MUSIC.sections.map((s, i) => (
      <Sequence key={i} from={s.from} durationInFrames={s.to - s.from} layout="none" name={`music ${"ABC"[i]}`}>
        <Audio
          src={staticFile("audio/bgm/impact-prelude.mp3")}
          startFrom={Math.round(s.trackAt * FPS)}
          volume={(lf) => {
            const mf = lf + s.from;
            const fin = interpolate(lf, [0, i === 0 ? 6 : 2], [0, 1], { extrapolateRight: "clamp" });
            const fout = interpolate(mf, [s.to - s.fadeOut, s.to], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            const under = s.level * 0.32;
            return (under + (s.level - under) * duckAt(mf)) * fin * fout;
          }}
        />
      </Sequence>
    ))}
  </>
);

export type Sfx = { at: number; name: string; volume?: number; dur?: number; rate?: number };

export const SfxTrack: React.FC<{ cues: Sfx[] }> = ({ cues }) => (
  <>
    {cues.map((c, i) => (
      <Sequence key={i} from={Math.max(0, Math.round(c.at))} durationInFrames={c.dur ?? 150} layout="none" name={`sfx ${c.name}`}>
        <Audio src={staticFile(`audio/sfx/${c.name}.mp3`)} volume={c.volume ?? 0.5} playbackRate={c.rate ?? 1} />
      </Sequence>
    ))}
  </>
);

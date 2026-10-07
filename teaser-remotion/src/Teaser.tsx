import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { Captions, Flash, InkWipe, MusicBed, SfxTrack, VoiceTrack } from "./components/Chrome";
import { S1ColdOpen, S2Twist, S3Intro } from "./scenes/S1_S3";
import { S4Autonomous, S5Rules, S6Alert } from "./scenes/S4_S6";
import { S7Evidence, S8Proof, S9Outro } from "./scenes/S7_S9";
import { C, FPS } from "./theme";
import { SCENES, TOTAL, w } from "./vo";

// Music bed: its drop (40.9 s into the track) lands on "dua puluh lima" in the climax.
const DROP_IN_TRACK = 40.9;
const s8 = SCENES[7];
const s9 = SCENES[8];
const DROP_AT = s8.from + w(8, "dua");
const MUSIC_FROM = Math.max(0, DROP_AT - Math.round(DROP_IN_TRACK * FPS));

const scene = (i: number, el: React.ReactNode) => (
  <Sequence key={i} from={SCENES[i].from} durationInFrames={i === 8 ? SCENES[i].dur + (TOTAL - SCENES[8].from - SCENES[8].dur) : SCENES[i].dur} name={`Frame ${i + 1}`}>
    {el}
  </Sequence>
);

export const Teaser: React.FC = () => {
  const cut = (i: number) => SCENES[i].from;
  const redFrom = s8.from + w(8, "dua") - 1;
  return (
    <AbsoluteFill style={{ background: C.night }}>
      {scene(0, <S1ColdOpen />)}
      {scene(1, <S2Twist dur={SCENES[1].dur} />)}
      {scene(2, <S3Intro />)}
      {scene(3, <S4Autonomous />)}
      {scene(4, <S5Rules dur={SCENES[4].dur} />)}
      {scene(5, <S6Alert />)}
      {scene(6, <S7Evidence />)}
      {scene(7, <S8Proof dur={SCENES[7].dur} />)}
      {scene(8, <S9Outro />)}

      <Flash at={cut(1)} color={C.red} />
      <InkWipe at={cut(2)} />
      <InkWipe at={cut(3)} dir={-1} />
      <Flash at={cut(4)} />
      <InkWipe at={cut(5)} />
      <InkWipe at={cut(6)} dir={-1} color={C.red} />
      <Flash at={cut(7)} />
      <Flash at={cut(8)} len={14} />

      <Captions dark={(f) => f < cut(1) || (f >= redFrom && f < cut(8))} />
      <SfxTrack
        cues={[
          { at: cut(1) - 6, name: "whoosh-big", volume: 0.45 },
          { at: cut(2) - 10, name: "whoosh", volume: 0.4 },
          { at: cut(3) - 10, name: "whoosh", volume: 0.4 },
          { at: cut(5) - 10, name: "whoosh", volume: 0.4 },
          { at: cut(6) - 10, name: "whoosh", volume: 0.4 },
          { at: cut(7) - 2, name: "impact-soft", volume: 0.4 },
          { at: cut(8) - 2, name: "impact", volume: 0.45, dur: 120 },
        ]}
      />
      <VoiceTrack />
      <MusicBed
        from={MUSIC_FROM}
        lift={[
          [DROP_AT - 2, s8.from + s8.dur],
          [s9.from + w(9, "terlambat") + 18, TOTAL],
        ]}
      />
    </AbsoluteFill>
  );
};

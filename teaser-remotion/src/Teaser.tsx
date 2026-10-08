import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import { Captions, FilmLook, Flash, Letterbox, Streak } from "./components/Fx";
import { prog } from "./components/primitives";
import { Score, SfxTrack, VoiceTrack } from "./components/Sound";
import { Hook, Reveal, Rewind, Who } from "./scenes/Act1";
import { Alert, Auto, Rules } from "./scenes/Act2";
import { Climax, Outro } from "./scenes/Act3";
import { C } from "./theme";
import { lineEnd, lineStart, MUSIC, scene, SceneName, w } from "./timeline";

const S = (name: SceneName, el: React.ReactNode) => {
  const s = scene(name);
  return (
    <Sequence key={name} from={s.from} durationInFrames={s.dur} name={name}>
      {el}
    </Sequence>
  );
};

const cut = (name: SceneName) => scene(name).from;
const HIT = MUSIC.hit;
const SRIL = lineEnd("months") + 10;

// Rules scene cue words, for card hits
const RULE_HITS = [w("rules", "laba"), w("rules", "kas"), w("rules", "utang"), w("rules", "risiko")];

const SFX = [
  // hook
  { at: 6, name: "subdrop", volume: 0.5 },
  { at: w("date", "delapan"), name: "slam", volume: 0.32 },
  { at: w("date", "mei"), name: "slam", volume: 0.32 },
  { at: w("date", "dua"), name: "slam", volume: 0.45 },
  { at: lineStart("halt"), name: "click", volume: 0.35 },
  { at: w("halt", "dihentikan") - 1, name: "impact", volume: 0.55, dur: 120 },
  { at: w("halt", "dihentikan"), name: "stamp", volume: 0.4 },
  // rewind
  { at: cut("rewind") - 8, name: "reverse", volume: 0.5 },
  { at: w("signs", "tanda"), name: "marker", volume: 0.25 },
  { at: w("signs", "bertahun-tahun") - 1, name: "impact-soft", volume: 0.45 },
  // who → stop-down → reveal
  { at: cut("who") - 6, name: "whoosh", volume: 0.35 },
  { at: cut("reveal") - 2, name: "glitch", volume: 0.4 },
  { at: lineStart("intro"), name: "tick", volume: 0.35 },
  { at: MUSIC.revealHit - 3, name: "braam", volume: 0.6 },
  { at: MUSIC.revealHit - 1, name: "impact", volume: 0.5, dur: 120 },
  // auto
  { at: cut("auto") - 8, name: "whoosh", volume: 0.4 },
  { at: w("auto", "tiga", 0), name: "click", volume: 0.35 },
  { at: w("auto", "tanpa"), name: "click", volume: 0.35 },
  { at: w("auto", "ia") - 4, name: "whoosh", volume: 0.28 },
  { at: w("auto", "sectors"), name: "click", volume: 0.35 },
  { at: w("auto", "memindai"), name: "count", volume: 0.3, dur: 26 },
  // rules
  { at: cut("rules") - 8, name: "whoosh", volume: 0.38 },
  ...[0, 1, 2, 3, 4, 5].map((i) => ({ at: lineStart("rules") + 2 + i * 3, name: "click", volume: 0.2 })),
  ...RULE_HITS.map((at) => ({ at, name: "slam", volume: 0.22 })),
  // alert + proof
  { at: cut("alert") - 8, name: "whoosh", volume: 0.38 },
  { at: w("alert", "peringatan"), name: "ping", volume: 0.6 },
  { at: w("alert", "telegram") + 6, name: "click", volume: 0.3 },
  { at: lineStart("proof") - 6, name: "whoosh", volume: 0.32 },
  { at: w("proof", "bukti") - 3, name: "whoosh", volume: 0.25 },
  // climax
  { at: cut("climax") - 8, name: "whoosh-big", volume: 0.4 },
  { at: lineStart("flag") - 10, name: "whoosh", volume: 0.35 },
  { at: w("flag", "menandai"), name: "marker", volume: 0.35 },
  { at: HIT - 60, name: "riser-long", volume: 0.5 },
  { at: w("months", "dua"), name: "count", volume: 0.35, dur: HIT - w("months", "dua") },
  { at: HIT - 2, name: "braam", volume: 0.6 },
  { at: HIT - 1, name: "impact", volume: 0.6, dur: 150 },
  { at: HIT, name: "subdrop", volume: 0.5 },
  { at: SRIL, name: "slam", volume: 0.45 },
  // outro
  { at: cut("outro") - 10, name: "whoosh-big", volume: 0.32 },
  { at: w("name", "afs") - 1, name: "impact-soft", volume: 0.3 },
  { at: w("tag", "terlambat") - 1, name: "impact", volume: 0.4, dur: 150 },
];

export const Teaser: React.FC = () => {
  const frame = useCurrentFrame();
  const open = prog(frame, MUSIC.revealHit, 22);
  return (
    <AbsoluteFill style={{ background: C.night }}>
      {S("hook", <Hook />)}
      {S("rewind", <Rewind />)}
      {S("who", <Who />)}
      {S("reveal", <Reveal />)}
      {S("auto", <Auto />)}
      {S("rules", <Rules />)}
      {S("alert", <Alert />)}
      {S("climax", <Climax />)}
      {S("outro", <Outro />)}

      <Streak at={w("halt", "dihentikan")} y={640} />
      <Flash at={MUSIC.revealHit} peak={0.85} len={10} />
      <Streak at={MUSIC.revealHit} y={560} />
      <Flash at={cut("auto")} peak={0.12} len={5} />
      <Flash at={cut("rules")} peak={0.12} len={5} />
      <Flash at={cut("alert")} peak={0.12} len={5} />
      <Flash at={HIT} peak={1} len={8} />
      <Streak at={w("name", "afs")} y={460} />

      <FilmLook />
      <Letterbox open={open} />
      <Captions
        hidden={(f) =>
          (f >= lineStart("who") && f < scene("reveal").from) ||
          (f >= MUSIC.revealHit - 2 && f < scene("auto").from) ||
          (f >= HIT && f < SRIL) ||
          f >= lineStart("name")
        }
      />

      <VoiceTrack />
      <Score />
      <SfxTrack cues={SFX} />
    </AbsoluteFill>
  );
};

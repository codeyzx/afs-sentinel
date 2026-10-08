import React from "react";
import { Composition, Folder } from "remotion";
import { Judging, type JudgingProps } from "./Judging";
import { Prompter, PROMPTER_CLIPS, prompterFrames, prompterId } from "./Prompter";
import { buildTiming, MIN_FRAMES, probeRecordings, videoFrames } from "./timeline";
import { FPS, H, W } from "./theme";

const placeholder = buildTiming({});

export const Root: React.FC = () => (
  <>
    <Composition
      id="Judging"
      component={Judging}
      width={W}
      height={H}
      fps={FPS}
      durationInFrames={videoFrames(placeholder)}
      defaultProps={{ timing: placeholder } satisfies JudgingProps}
      calculateMetadata={async () => {
        const timing = buildTiming(await probeRecordings());
        const total = videoFrames(timing);
        if (total < MIN_FRAMES) console.warn(`Judging: ${(total / FPS).toFixed(1)}s, kurang dari 3:00`);
        return { durationInFrames: total, props: { timing } };
      }}
    />
    <Folder name="Prompter">
      {(["Fathan", "Ais", "Yahya"] as const).map((who) => (
        <Folder key={who} name={who}>
          {PROMPTER_CLIPS.filter((p) => p.who === who).map((p) => (
            <Composition
              key={p.clip}
              id={prompterId(p.clip)}
              component={Prompter}
              width={W}
              height={H}
              fps={FPS}
              durationInFrames={prompterFrames(p)}
              defaultProps={{ clip: p.clip }}
            />
          ))}
        </Folder>
      ))}
    </Folder>
  </>
);

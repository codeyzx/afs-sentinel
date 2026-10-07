import React from "react";
import { Composition, Folder } from "remotion";
import { Judging, type JudgingProps } from "./Judging";
import { Prompter, PROMPTER_CLIPS, prompterFrames, prompterId } from "./Prompter";
import { buildTiming, probeRecordings } from "./timeline";
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
      durationInFrames={placeholder.total}
      defaultProps={{ timing: placeholder } satisfies JudgingProps}
      calculateMetadata={async () => {
        const timing = buildTiming(await probeRecordings());
        if (timing.total > 180 * FPS) console.warn(`Judging: ${(timing.total / FPS).toFixed(1)}s, lebih dari 3:00`);
        return { durationInFrames: timing.total, props: { timing } };
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

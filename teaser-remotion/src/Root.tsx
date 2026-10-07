import React from "react";
import { Composition } from "remotion";
import { Teaser } from "./Teaser";
import { FPS, H, W } from "./theme";
import { TOTAL } from "./vo";

export const Root: React.FC = () => <Composition id="Teaser" component={Teaser} width={W} height={H} fps={FPS} durationInFrames={TOTAL} />;

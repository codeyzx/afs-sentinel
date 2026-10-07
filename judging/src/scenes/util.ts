import type { SceneTiming } from "../timeline";

export type SceneProps = { scene: SceneTiming; index: number };

/** PiP slot used by every screen scene. */
export const PIP = { left: 1404, top: 150, width: 420, height: 540 };
export const SCREEN = { left: 96, top: 128, width: 1260 };

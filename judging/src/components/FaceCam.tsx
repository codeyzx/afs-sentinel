import React from "react";
import { Freeze, interpolate, OffthreadVideo, Sequence, useCurrentFrame } from "remotion";
import { GRADE, type ClipId } from "../media";
import { SCENES, PEOPLE, type Person } from "../script";
import { clipSrc, framingOf, trimOf } from "../timeline";
import { C, F, FPS } from "../theme";
import { Kicker } from "./primitives";

const clipInfo = (clip: ClipId) => {
  for (const s of SCENES) {
    for (const l of s.lines) if (l.clips.includes(clip)) return { text: l.text, direction: l.direction, target: l.target, kind: l.kind };
    for (const r of s.reactions ?? []) if (r.clip === clip) return { text: r.text, direction: r.direction, target: r.target, kind: "cam" as const };
  }
  return { text: "", direction: "", target: 0, kind: "cam" as const };
};

/**
 * A face recording (muted; voices play from the VoiceTrack). Before `playFrom` it holds the
 * first frame, after `playFrom + playDur` it holds the last one. Without a file: a placeholder.
 */
export const FaceCam: React.FC<{
  clip: ClipId;
  who: Person;
  playFrom: number;
  playDur: number;
  style: React.CSSProperties;
  radius?: number;
  /** object-position of the face video, e.g. "50% 35%". */
  focus?: string;
  compact?: boolean;
  border?: string;
}> = ({ clip, who, playFrom, playDur, style, radius = 22, focus = "50% 40%", compact, border }) => {
  const frame = useCurrentFrame();
  const src = clipSrc(clip);
  const trim = Math.round(trimOf(clip) * FPS);
  const speaking = frame >= playFrom && frame < playFrom + playDur;

  const box: React.CSSProperties = {
    position: "absolute",
    overflow: "hidden",
    borderRadius: radius,
    background: C.paperDeep,
    boxShadow: "0 18px 50px rgba(40,28,10,0.22), 0 2px 6px rgba(40,28,10,0.12)",
    border: border ?? `2px solid ${speaking ? C.ink : "rgba(22,19,15,0.18)"}`,
    ...style,
  };

  const scrim = <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: "38%", background: "linear-gradient(transparent, rgba(14,13,11,0.62))" }} />;
  if (!src)
    return (
      <div style={box}>
        <Placeholder clip={clip} who={who} speaking={speaking} compact={compact} />
        {scrim}
      </div>
    );

  const video = <OffthreadVideo src={src} muted startFrom={trim} style={{ ...cropStyle(clip, style, focus), filter: GRADE[who] }} />;

  const local = frame - playFrom;
  return (
    <div style={box}>
      {local < 0 ? (
        <Freeze frame={0}>{video}</Freeze>
      ) : local >= playDur ? (
        <Freeze frame={Math.max(0, playDur - 1)}>{video}</Freeze>
      ) : (
        <Sequence from={playFrom} durationInFrames={playDur} layout="none">
          {video}
        </Sequence>
      )}
      {scrim}
    </div>
  );
};

/**
 * Crop the recording so the face sits centred, a little above the middle, at ~40% of the box
 * height. Falls back to a plain cover crop when the face position is unknown.
 */
const cropStyle = (clip: ClipId, box: React.CSSProperties, focus: string): React.CSSProperties => {
  const fr = framingOf(clip);
  const bw = Number(box.width);
  const bh = Number(box.height);
  if (!fr?.face || !bw || !bh) return { width: "100%", height: "100%", objectFit: "cover", objectPosition: focus };
  const { w, h, face } = fr;
  const s = Math.max(bw / w, bh / h, (0.4 * bh) / (face.h * h));
  const vw = w * s;
  const vh = h * s;
  const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
  return {
    position: "absolute",
    width: vw,
    height: vh,
    maxWidth: "none",
    left: clamp(bw / 2 - face.x * vw, bw - vw, 0),
    top: clamp(bh * 0.42 - face.y * vh, bh - vh, 0),
  };
};

const Placeholder: React.FC<{ clip: ClipId; who: Person; speaking: boolean; compact?: boolean }> = ({ clip, who, speaking, compact }) => {
  const frame = useCurrentFrame();
  const info = clipInfo(clip);
  const bars = 18;
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: `repeating-linear-gradient(-45deg, ${C.paperDeep} 0 22px, #DDD4C3 22px 44px)`,
        display: "flex",
        flexDirection: "column",
        gap: compact ? 8 : 16,
        padding: compact ? 14 : 26,
        fontFamily: F.sans,
        color: C.ink,
      }}
    >
      <div>
        <Kicker size={compact ? 12 : 15} color={C.red}>
          ● Rekam · {info.kind === "vo" ? "suara" : "wajah + suara"}
        </Kicker>
        <div style={{ fontFamily: F.mono, fontSize: compact ? 15 : 22, fontWeight: 600, marginTop: 6, wordBreak: "break-all" }}>{clip}</div>
      </div>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: compact ? 22 : 34 }}>
        {Array.from({ length: bars }, (_, i) => {
          const h = speaking ? 0.25 + 0.75 * Math.abs(Math.sin(frame * 0.35 + i * 1.7) * Math.cos(frame * 0.13 + i)) : 0.12;
          return <div key={i} style={{ flex: 1, height: `${h * 100}%`, background: speaking ? C.ink : C.hint, borderRadius: 2 }} />;
        })}
      </div>
      {!compact && (
        <div style={{ fontSize: 17, lineHeight: 1.35, color: C.inkSoft, background: "rgba(251,248,242,0.85)", padding: "10px 12px", borderRadius: 10 }}>
          <b>{who}</b> · ±{info.target} dtk · {info.direction}
        </div>
      )}
    </div>
  );
};

/** Lower-third name tag: name in serif, role in mono. */
export const NameTag: React.FC<{ who: Person; start: number; style?: React.CSSProperties; dark?: boolean }> = ({ who, start, style, dark }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [start, start + 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const bar = interpolate(frame, [start, start + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", display: "flex", alignItems: "stretch", gap: 12, ...style }}>
      <div style={{ width: 5, background: C.red, transform: `scaleY(${bar})`, transformOrigin: "bottom" }} />
      <div style={{ opacity: p, transform: `translateX(${(1 - p) * -16}px)` }}>
        <div style={{ fontFamily: F.serif, fontSize: 34, fontWeight: 600, lineHeight: 1.05, color: dark ? C.card : C.ink }}>{who}</div>
        <Kicker size={14} color={dark ? "rgba(251,248,242,0.75)" : C.muted} style={{ marginTop: 4 }}>
          {PEOPLE[who].role}
        </Kicker>
      </div>
    </div>
  );
};

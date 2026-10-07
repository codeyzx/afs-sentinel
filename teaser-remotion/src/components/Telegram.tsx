import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { F } from "../theme";
import { useSpring } from "./primitives";

// Telegram Desktop, dark theme, rebuilt from the bot's real message text.
const T = {
  bg: "#0E1621",
  side: "#17212B",
  bubble: "#182533",
  text: "#F5F5F5",
  hint: "#6D7F8F",
  accent: "#64B5EF",
  button: "rgba(82,136,193,0.22)",
  active: "#2B5278",
};

export type TgMessage = {
  html: string;
  time: string;
  button?: string;
  voice?: string;
  /** scene frame the message arrives */
  at: number;
  /** text line index → scene frame its highlight sweeps in */
  marks?: Record<number, number>;
};

const MarkedLine: React.FC<{ html: string; mark?: number }> = ({ html, mark }) => {
  const frame = useCurrentFrame();
  const p = mark === undefined ? 0 : interpolate(frame, [mark, mark + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "relative", minHeight: "0.7em" }}>
      {p > 0 && (
        <div
          style={{
            position: "absolute",
            inset: "-2px -8px",
            background: "rgba(245,213,71,0.28)",
            borderLeft: "4px solid #F5D547",
            transformOrigin: "left",
            transform: `scaleX(${p})`,
            borderRadius: 4,
          }}
        />
      )}
      <span style={{ position: "relative" }} dangerouslySetInnerHTML={{ __html: html || "&nbsp;" }} />
    </div>
  );
};

export const TG_LAYOUT = {
  width: 1280,
  height: 800,
  side: 330,
  header: 64,
  input: 60,
  bubbleLeft: 30,
  bubbleW: 640,
  buttonH: 50,
};

const Bubble: React.FC<{ m: TgMessage; highlight?: number }> = ({ m, highlight = 0 }) => {
  const frame = useCurrentFrame();
  const s = useSpring(m.at, { damping: 16, stiffness: 160 } as never);
  if (frame < m.at) return null;
  return (
    <div style={{ transform: `translateY(${(1 - s) * 40}px)`, opacity: s, width: TG_LAYOUT.bubbleW, marginTop: 10 }}>
      <div
        style={{
          background: T.bubble,
          borderRadius: m.button ? "16px 16px 6px 6px" : "16px 16px 16px 4px",
          padding: "12px 16px 10px",
          color: T.text,
          fontFamily: F.sans,
          fontSize: 21,
          lineHeight: 1.42,
          whiteSpace: "normal",
          position: "relative",
        }}
      >
        {m.voice ? (
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ width: 48, height: 48, borderRadius: 24, background: T.accent, display: "grid", placeItems: "center" }}>
              <div style={{ width: 0, height: 0, borderLeft: "16px solid #fff", borderTop: "10px solid transparent", borderBottom: "10px solid transparent", marginLeft: 4 }} />
            </div>
            <div style={{ display: "flex", gap: 3, alignItems: "center", height: 30 }}>
              {Array.from({ length: 38 }, (_, i) => (
                <div key={i} style={{ width: 4, height: 6 + Math.abs(Math.sin(i * 1.3) * Math.cos(i * 0.4)) * 22, background: "#5E7D9A", borderRadius: 2 }} />
              ))}
            </div>
            <div style={{ color: T.hint, fontSize: 17 }}>{m.voice}</div>
          </div>
        ) : (
          m.html.split("\n").map((l, i) => <MarkedLine key={i} html={l} mark={m.marks?.[i]} />)
        )}
        <div style={{ textAlign: "right", color: T.hint, fontSize: 15, marginTop: 2 }}>{m.time}</div>
      </div>
      {m.button && (
        <div
          style={{
            marginTop: 4,
            height: TG_LAYOUT.buttonH,
            borderRadius: "6px 6px 16px 16px",
            background: highlight > 0 ? `rgba(100,181,239,${0.22 + 0.3 * highlight})` : T.button,
            color: T.text,
            fontFamily: F.sans,
            fontWeight: 600,
            fontSize: 20,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 10,
          }}
        >
          {m.button}
          <span style={{ fontSize: 16, opacity: 0.8 }}>↗</span>
        </div>
      )}
    </div>
  );
};

/** Whole Telegram window. Newest message sits at the bottom of the chat, like the app. */
export const TelegramWindow: React.FC<{
  messages: TgMessage[];
  /** 0..1 glow on the last message's button */
  buttonGlow?: number;
  chatTitle?: string;
  style?: React.CSSProperties;
}> = ({ messages, buttonGlow = 0, chatTitle = "AFS Sentinel", style }) => {
  const frame = useCurrentFrame();
  const L = TG_LAYOUT;
  const unread = messages.filter((m) => frame >= m.at).length;
  return (
    <div
      style={{
        position: "absolute",
        width: L.width,
        height: L.height,
        borderRadius: 14,
        overflow: "hidden",
        display: "flex",
        background: T.bg,
        boxShadow: "0 40px 90px rgba(30,20,5,0.35), 0 4px 12px rgba(30,20,5,0.2)",
        fontFamily: F.sans,
        ...style,
      }}
    >
      <div style={{ width: L.side, background: T.side, borderRight: "1px solid #0B121A", padding: "14px 0" }}>
        <div style={{ margin: "0 14px 12px", height: 40, borderRadius: 20, background: "#242F3D", color: T.hint, fontSize: 17, display: "flex", alignItems: "center", paddingLeft: 18 }}>
          Search
        </div>
        {[
          { name: chatTitle, last: "Bot · peringatan dini", active: true },
          { name: "Saved Messages", last: "" },
        ].map((c, i) => (
          <div key={c.name} style={{ display: "flex", gap: 12, padding: "10px 14px", background: c.active ? T.active : "transparent", alignItems: "center" }}>
            <div
              style={{
                width: 50,
                height: 50,
                borderRadius: 25,
                background: i === 0 ? "#D93A2B" : "#4D6EA8",
                color: "#fff",
                display: "grid",
                placeItems: "center",
                fontWeight: 700,
                fontSize: 19,
              }}
            >
              {i === 0 ? "AFS" : c.name[0]}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ color: T.text, fontWeight: 600, fontSize: 18 }}>{c.name}</div>
              <div style={{ color: c.active ? "#C9D8E6" : T.hint, fontSize: 15, whiteSpace: "nowrap", overflow: "hidden" }}>{c.last}</div>
            </div>
            {i === 0 && unread > 0 && (
              <div style={{ minWidth: 26, height: 26, borderRadius: 13, background: "#fff", color: T.active, fontSize: 14, fontWeight: 700, display: "grid", placeItems: "center" }}>
                {unread}
              </div>
            )}
          </div>
        ))}
      </div>
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <div style={{ height: L.header, background: T.side, display: "flex", alignItems: "center", padding: "0 22px", gap: 14, borderBottom: "1px solid #0B121A" }}>
          <div>
            <div style={{ color: T.text, fontWeight: 600, fontSize: 19 }}>{chatTitle}</div>
            <div style={{ color: T.hint, fontSize: 15 }}>bot</div>
          </div>
        </div>
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "flex-end",
            padding: `0 ${L.bubbleLeft}px 18px`,
            overflow: "hidden",
            background: "radial-gradient(circle at 70% 20%, #13202D 0%, #0E1621 60%)",
          }}
        >
          {messages.map((m, i) => (
            <Bubble key={i} m={m} highlight={i === messages.length - 1 ? buttonGlow : 0} />
          ))}
        </div>
        <div style={{ height: L.input, background: T.side, color: T.hint, fontSize: 18, display: "flex", alignItems: "center", padding: "0 22px" }}>
          Write a message…
        </div>
      </div>
    </div>
  );
};

/** Telegram's HTML subset (b, i) to inline styles we control. */
export const tgHtml = (text: string) =>
  text.replace(/<b>/g, '<b style="font-weight:700">').replace(/<i>/g, '<i style="font-style:italic;color:#C9D6E2">');

/** "Popup" notification like the desktop toast. */
export const TgToast: React.FC<{ at: number; title: string; body: string; style?: React.CSSProperties }> = ({ at, title, body, style }) => {
  const frame = useCurrentFrame();
  const s = useSpring(at, { damping: 15, stiffness: 170 } as never);
  const out = interpolate(frame, [at + 75, at + 90], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  if (frame < at) return null;
  return (
    <div
      style={{
        position: "absolute",
        width: 470,
        background: "#17212B",
        borderRadius: 14,
        padding: "16px 18px",
        display: "flex",
        gap: 14,
        boxShadow: "0 24px 60px rgba(0,0,0,0.4)",
        transform: `translateX(${(1 - s) * 520}px)`,
        opacity: out,
        fontFamily: F.sans,
        ...style,
      }}
    >
      <div style={{ width: 48, height: 48, borderRadius: 24, background: "#D93A2B", color: "#fff", display: "grid", placeItems: "center", fontWeight: 700, fontSize: 17 }}>AFS</div>
      <div style={{ minWidth: 0 }}>
        <div style={{ color: T.text, fontWeight: 600, fontSize: 18 }}>{title}</div>
        <div style={{ color: "#B9C6D3", fontSize: 16, lineHeight: 1.35 }}>{body}</div>
      </div>
    </div>
  );
};

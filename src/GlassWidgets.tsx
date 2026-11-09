import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const FONT = "Inter, Helvetica, Arial, sans-serif";

// Giriş animasyonu: aşağıdan yukarı kayma + bulanıktan nete geçiş
const useEnter = (delay: number) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({
    frame: frame - delay,
    fps,
    config: { damping: 16, mass: 0.9, stiffness: 90 },
  });
  return {
    opacity: interpolate(p, [0, 1], [0, 1]),
    transform: `translateY(${interpolate(p, [0, 1], [60, 0])}px) scale(${interpolate(
      p,
      [0, 1],
      [0.94, 1]
    )})`,
    filter: `blur(${interpolate(p, [0, 1], [12, 0])}px)`,
  };
};

// Buzlu cam panel: arka planı bulanıklaştırır, kenar parlaması ve kayan ışık yansıması ekler
const Glass: React.FC<{
  delay: number;
  style?: React.CSSProperties;
  radius?: number;
  children: React.ReactNode;
}> = ({ delay, style, radius = 44, children }) => {
  const frame = useCurrentFrame();
  const enter = useEnter(delay);
  // Işık yansıması her panelde biraz gecikmeli olarak soldan sağa süzülür
  const sweep = interpolate((frame - delay - 20) % 180, [0, 70], [-60, 160], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "relative",
        borderRadius: radius,
        overflow: "hidden",
        background:
          "linear-gradient(135deg, rgba(255,255,255,0.16) 0%, rgba(255,255,255,0.05) 60%, rgba(255,255,255,0.09) 100%)",
        backdropFilter: "blur(28px) saturate(150%) brightness(1.08)",
        WebkitBackdropFilter: "blur(28px) saturate(150%) brightness(1.08)",
        border: "1.5px solid rgba(255,255,255,0.28)",
        boxShadow:
          "0 30px 60px rgba(5,12,24,0.35), inset 0 1.5px 0 rgba(255,255,255,0.45), inset 0 -1px 0 rgba(255,255,255,0.08)",
        color: "white",
        fontFamily: FONT,
        ...enter,
        ...style,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `linear-gradient(105deg, transparent ${sweep - 25}%, rgba(255,255,255,0.18) ${sweep}%, transparent ${sweep + 25}%)`,
          pointerEvents: "none",
        }}
      />
      <div style={{ position: "relative", height: "100%" }}>{children}</div>
    </div>
  );
};

const Label: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      fontSize: 22,
      fontWeight: 600,
      letterSpacing: 4,
      opacity: 0.7,
    }}
  >
    {children}
  </div>
);

// 09:05'te duran analog saat; yalnızca saniye ibresi hareket eder
const Clock: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const seconds = frame / fps;
  const hour = (9 + 5 / 60) * 30;
  const minute = 5 * 6;
  const second = Math.floor(seconds) * 6 + spring({
    frame: frame % fps,
    fps,
    config: { damping: 10, stiffness: 300 },
  }) * 6;

  const hand = (deg: number, len: number, w: number, color: string) => (
    <line
      x1={60}
      y1={60}
      x2={60 + Math.sin((deg * Math.PI) / 180) * len}
      y2={60 - Math.cos((deg * Math.PI) / 180) * len}
      stroke={color}
      strokeWidth={w}
      strokeLinecap="round"
    />
  );

  return (
    <svg width={150} height={150} viewBox="0 0 120 120">
      <circle cx={60} cy={60} r={56} fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.35)" strokeWidth={1.5} />
      {new Array(12).fill(0).map((_, i) => {
        const a = (i * 30 * Math.PI) / 180;
        return (
          <line
            key={i}
            x1={60 + Math.sin(a) * 46}
            y1={60 - Math.cos(a) * 46}
            x2={60 + Math.sin(a) * 51}
            y2={60 - Math.cos(a) * 51}
            stroke="rgba(255,255,255,0.7)"
            strokeWidth={i % 3 === 0 ? 2.5 : 1.2}
            strokeLinecap="round"
          />
        );
      })}
      {hand(hour, 28, 4, "white")}
      {hand(minute, 40, 3, "white")}
      {hand(second, 44, 1.2, "#ff5a5a")}
      <circle cx={60} cy={60} r={3.5} fill="white" />
    </svg>
  );
};

export const GlassWidgets: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Yavaş Ken Burns yakınlaşması
  // Merkez yüz hizasında tutulur, böylece figür üst widget'lara doğru kaymaz
  const zoom = interpolate(frame, [0, durationInFrames], [1.0, 1.07]);
  const fadeIn = interpolate(frame, [0, 25], [0, 1], { extrapolateRight: "clamp" });
  const fadeOut = interpolate(frame, [durationInFrames - 25, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <AbsoluteFill style={{ opacity: fadeIn * fadeOut }}>
        <AbsoluteFill style={{ transform: `scale(${zoom})`, transformOrigin: "50% 36%" }}>
          <Img
            src={staticFile("memorial.png")}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </AbsoluteFill>
        {/* Hafif vinyet */}
        <AbsoluteFill
          style={{
            background:
              "radial-gradient(ellipse at 50% 45%, transparent 55%, rgba(4,10,20,0.55) 100%)",
          }}
        />

        {/* Üst widget sırası: tarihlerin altındaki boş gökyüzü alanı */}
        <div
          style={{
            position: "absolute",
            top: 365,
            left: 70,
            right: 70,
            display: "flex",
            gap: 28,
            height: 215,
          }}
        >
          <Glass delay={20} style={{ flex: 1, padding: "30px 34px" }}>
            <Label>TARİH</Label>
            <div style={{ fontSize: 92, fontWeight: 700, lineHeight: 1, marginTop: 14 }}>10</div>
            <div style={{ fontSize: 34, fontWeight: 500, marginTop: 6, opacity: 0.9 }}>Kasım</div>
          </Glass>
          <Glass
            delay={30}
            style={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <div style={{ display: "flex", height: "100%", alignItems: "center", justifyContent: "center" }}>
              <Clock />
            </div>
          </Glass>
          <Glass delay={40} style={{ flex: 1, padding: "30px 34px" }}>
            <Label>SAAT</Label>
            <div style={{ fontSize: 92, fontWeight: 300, lineHeight: 1, marginTop: 14, fontVariantNumeric: "tabular-nums" }}>
              09:05
            </div>
            <div style={{ fontSize: 26, fontWeight: 500, marginTop: 12, opacity: 0.75 }}>Saygıyla</div>
          </Glass>
        </div>

        {/* Alt geniş widget: söz */}
        <div style={{ position: "absolute", left: 70, right: 70, bottom: 120 }}>
          <Glass delay={60} radius={52} style={{ padding: "44px 52px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
              <div
                style={{
                  width: 14,
                  height: 14,
                  borderRadius: 7,
                  background: "#ff5a5a",
                  boxShadow: "0 0 18px #ff5a5a",
                  opacity: 0.6 + 0.4 * Math.abs(Math.sin(frame / 20)),
                }}
              />
              <Label>SAYGI VE ÖZLEMLE</Label>
            </div>
            <div style={{ fontSize: 56, fontWeight: 600, lineHeight: 1.2, marginTop: 24 }}>
              “Yurtta sulh, cihanda sulh.”
            </div>
            <div style={{ fontSize: 30, fontWeight: 400, marginTop: 16, opacity: 0.75 }}>
              Mustafa Kemal Atatürk · 1881 – 1938
            </div>
          </Glass>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

import React from "react";
import { ThreeCanvas } from "@remotion/three";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const Knot: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Giriş animasyonu: küçükten büyüğe yaylı ölçekleme
  const scale = spring({ frame, fps, config: { damping: 12, mass: 0.8 } });
  const rotY = (frame / fps) * Math.PI * 0.8;
  const rotX = Math.sin(frame / 40) * 0.4;

  return (
    <mesh scale={scale * 1.4} rotation={[rotX, rotY, 0]}>
      <torusKnotGeometry args={[1, 0.32, 256, 48]} />
      <meshStandardMaterial color="#7c5cff" metalness={0.6} roughness={0.2} />
    </mesh>
  );
};

const Orbiters: React.FC = () => {
  const frame = useCurrentFrame();
  const count = 8;
  return (
    <>
      {new Array(count).fill(0).map((_, i) => {
        const angle = (i / count) * Math.PI * 2 + frame / 30;
        const r = 3.4;
        return (
          <mesh
            key={i}
            position={[
              Math.cos(angle) * r,
              Math.sin(angle * 2) * 0.6,
              Math.sin(angle) * r,
            ]}
          >
            <sphereGeometry args={[0.18, 32, 32]} />
            <meshStandardMaterial
              color={i % 2 === 0 ? "#00e5ff" : "#ff3d81"}
              emissive={i % 2 === 0 ? "#00e5ff" : "#ff3d81"}
              emissiveIntensity={0.6}
            />
          </mesh>
        );
      })}
    </>
  );
};

export const Scene3D: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();

  const titleOpacity = interpolate(frame, [30, 60], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 20, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(circle at 50% 40%, #1b1440 0%, #07060f 70%)",
        opacity: fadeOut,
      }}
    >
      <ThreeCanvas
        width={width}
        height={height}
        camera={{ fov: 45, position: [0, 0, 9] }}
      >
        <ambientLight intensity={0.4} />
        <pointLight position={[5, 5, 5]} intensity={80} color="#ffffff" />
        <pointLight position={[-5, -3, 2]} intensity={40} color="#00e5ff" />
        <Knot />
        <Orbiters />
      </ThreeCanvas>
      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          alignItems: "center",
          paddingBottom: 90,
          opacity: titleOpacity,
        }}
      >
        <div
          style={{
            color: "white",
            fontFamily: "Inter, Helvetica, Arial, sans-serif",
            fontSize: 96,
            fontWeight: 800,
            letterSpacing: 8,
            textShadow: "0 0 30px rgba(124,92,255,0.8)",
          }}
        >
          DEPOM
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

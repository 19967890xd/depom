import React from "react";
import { Composition } from "remotion";
import { Scene3D } from "./Scene3D";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="Scene3D"
      component={Scene3D}
      durationInFrames={150}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};

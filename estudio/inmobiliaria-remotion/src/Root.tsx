import React from "react";
import { Composition } from "remotion";
import datos from "./datos.json";
import { Video } from "./Video";
import "./fuentes";

export const RemotionRoot: React.FC = () => (
  <>
    {Object.entries(datos).map(([id, d]) => (
      <Composition key={id} id={id} component={Video} durationInFrames={d.total} fps={30} width={1080} height={1920} defaultProps={{ id }} />
    ))}
  </>
);

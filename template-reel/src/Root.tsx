import { Composition } from "remotion";
import { Main, CTA_SECONDS } from "./video";
import { DURATION } from "./words";
import { Miniatura, MiniProps } from "./miniatura";

export const FPS = 30;

const MINI: MiniProps = { titulo: "Tu gancho aquí", destacar: "gancho", foto: "miniatura_1.jpg" };

export const Root = () => (
  <>
    <Composition
      id="Main"
      component={Main}
      durationInFrames={Math.ceil((DURATION + CTA_SECONDS) * FPS)}
      fps={FPS}
      width={1080}
      height={1920}
    />
    <Composition id="Miniatura" component={Miniatura} durationInFrames={1} fps={FPS} width={1080} height={1920} defaultProps={MINI} />
  </>
);

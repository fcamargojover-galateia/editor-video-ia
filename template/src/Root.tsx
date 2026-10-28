import { Composition } from "remotion";
import { Main } from "./video";
import { DURATION } from "./words";
import { Miniatura, MiniProps } from "./miniatura";

export const FPS = 30;

const MINI: MiniProps = { titulo: "Tu título aquí", destacar: "título", foto: "miniatura_1.jpg" };

export const Root = () => (
  <>
    <Composition
      id="Main"
      component={Main}
      durationInFrames={Math.ceil(DURATION * FPS)}
      fps={FPS}
      width={1920}
      height={1080}
    />
    <Composition id="Miniatura" component={Miniatura} durationInFrames={1} fps={FPS} width={1280} height={720} defaultProps={MINI} />
  </>
);

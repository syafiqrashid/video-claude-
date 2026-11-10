import {Composition} from 'remotion';
import {TemuCube, TOTAL_FRAMES} from './TemuCube';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="TemuCube"
    component={TemuCube}
    durationInFrames={TOTAL_FRAMES}
    fps={30}
    width={1080}
    height={1920}
  />
);

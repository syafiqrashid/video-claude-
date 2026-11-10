import {AbsoluteFill, interpolate, random, useCurrentFrame, useVideoConfig} from 'remotion';
import {C} from './theme';

type CubeProps = {size: number; rx: number; ry: number; tint: string; glow: number};

const Cube: React.FC<CubeProps> = ({size, rx, ry, tint, glow}) => {
  const h = size / 2;
  const faces = [
    `rotateY(0deg) translateZ(${h}px)`,
    `rotateY(90deg) translateZ(${h}px)`,
    `rotateY(180deg) translateZ(${h}px)`,
    `rotateY(-90deg) translateZ(${h}px)`,
    `rotateX(90deg) translateZ(${h}px)`,
    `rotateX(-90deg) translateZ(${h}px)`,
  ];
  return (
    <div
      style={{
        position: 'absolute',
        width: size,
        height: size,
        transformStyle: 'preserve-3d',
        transform: `rotateX(${rx}deg) rotateY(${ry}deg)`,
      }}
    >
      {faces.map((t, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            inset: 0,
            transform: t,
            border: `${Math.max(2, size * 0.035)}px solid ${tint}`,
            background: `linear-gradient(135deg, ${tint}${i % 2 ? '40' : '22'}, ${C.bgMid}10)`,
            boxShadow: `0 0 ${size * 0.25 * glow}px ${tint}66, inset 0 0 ${size * 0.2}px ${tint}33`,
          }}
        />
      ))}
    </div>
  );
};

const COUNT = 34;

/** Floating 3D cube field used as the animated background. `pulse` (0..1) briefly brightens it. */
export const CubeField: React.FC<{pulse: number}> = ({pulse}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();

  const cubes = new Array(COUNT).fill(0).map((_, i) => {
    const r = (k: string) => random(`${k}-${i}`);
    const z = interpolate(r('z'), [0, 1], [-1800, -150]);
    const size = interpolate(r('s'), [0, 1], [70, 220]);
    const speed = interpolate(r('v'), [0, 1], [0.6, 2.2]);
    const span = height * 2.2;
    const y = ((r('y') * span - frame * speed * 2.2) % span + span) % span - span * 0.3;
    const x = interpolate(r('x'), [0, 1], [-width * 0.6, width * 1.6]);
    const palette = [C.turmeric, C.leaf, C.hitam, C.turmericDeep];
    return {
      i,
      x,
      y,
      z,
      size,
      rx: r('rx') * 360 + frame * speed * 0.9,
      ry: r('ry') * 360 + frame * speed * 1.3,
      tint: palette[Math.floor(r('c') * palette.length)],
    };
  });

  const camRot = Math.sin(frame / 90) * 6;

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse at 50% 40%, ${C.bgMid} 0%, ${C.bgDeep} 70%)`,
        overflow: 'hidden',
      }}
    >
      {/* perspective grid floor */}
      <AbsoluteFill style={{perspective: 900}}>
        <div
          style={{
            position: 'absolute',
            left: -width,
            width: width * 3,
            top: height * 0.55,
            height: height * 1.4,
            transformOrigin: '50% 0%',
            transform: `rotateX(72deg) translateY(${-(frame * 4) % 120}px)`,
            backgroundImage: `linear-gradient(${C.leaf}55 2px, transparent 2px), linear-gradient(90deg, ${C.leaf}55 2px, transparent 2px)`,
            backgroundSize: '120px 120px',
            maskImage: 'linear-gradient(to bottom, black 0%, transparent 70%)',
            WebkitMaskImage: 'linear-gradient(to bottom, black 0%, transparent 70%)',
            opacity: 0.55 + pulse * 0.4,
          }}
        />
      </AbsoluteFill>

      <AbsoluteFill style={{perspective: 1100, perspectiveOrigin: '50% 45%'}}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            transformStyle: 'preserve-3d',
            transform: `rotateY(${camRot}deg)`,
          }}
        >
          {cubes
            .sort((a, b) => a.z - b.z)
            .map((c) => (
              <div
                key={c.i}
                style={{
                  position: 'absolute',
                  left: c.x,
                  top: c.y,
                  transformStyle: 'preserve-3d',
                  transform: `translateZ(${c.z}px)`,
                  opacity: interpolate(c.z, [-1800, -150], [0.35, 0.95]) * (0.75 + pulse * 0.25),
                }}
              >
                <Cube size={c.size} rx={c.rx} ry={c.ry} tint={c.tint} glow={1 + pulse * 2} />
              </div>
            ))}
        </div>
      </AbsoluteFill>

      {/* vignette */}
      <AbsoluteFill
        style={{background: 'radial-gradient(ellipse at 50% 45%, transparent 45%, rgba(0,0,0,0.65) 100%)'}}
      />
    </AbsoluteFill>
  );
};

import {
  AbsoluteFill,
  Audio,
  Easing,
  interpolate,
  OffthreadVideo,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {CubeField} from './CubeField';
import {C, FONT} from './theme';

const FPS = 30;
const INTRO = 90;
const STEP = 105;
const OUTRO = 165;

type Step = {title: string; sub: string; clipAt: number};

// clipAt = second in the source video where each face's footage starts
const STEPS: Step[] = [
  {title: 'Pilih Pokok Induk', sub: 'Keluarkan dari polibeg', clipAt: 8.5},
  {title: 'Asingkan Rizom', sub: 'Potong ikut mata tunas', clipAt: 13},
  {title: 'Gali Lubang', sub: 'Tanah gembur, dalam sejengkal', clipAt: 31.5},
  {title: 'Tanam & Sungkup', sub: 'Tutup dengan rumput kering', clipAt: 42},
];
const OUTRO_CLIP_AT = 94.2;

const STEP_START = (i: number) => INTRO + i * STEP;
const OUTRO_START = STEP_START(STEPS.length);
export const TOTAL_FRAMES = OUTRO_START + OUTRO;

const SRC = staticFile('source.mp4');

// prism face size (9:16, matches source footage)
const FW = 600;
const FH = 1066;

const FaceVideo: React.FC<{clipAt: number; alignFrame: number}> = ({clipAt, alignFrame}) => (
  <OffthreadVideo
    src={SRC}
    muted
    startFrom={Math.max(0, Math.round(clipAt * FPS - alignFrame))}
    style={{width: '100%', height: '100%', objectFit: 'cover'}}
  />
);

const Prism: React.FC<{rotY: number}> = ({rotY}) => {
  return (
    <div
      style={{
        position: 'absolute',
        width: FW,
        height: FH,
        left: -FW / 2,
        top: -FH / 2,
        transformStyle: 'preserve-3d',
        transform: `rotateY(${rotY}deg)`,
      }}
    >
      {STEPS.map((s, i) => {
        // world angle of this face's normal; 0 = facing camera
        const ang = ((rotY + i * 90) % 360 + 360) % 360;
        const facing = Math.cos((ang * Math.PI) / 180); // 1 front, 0 side
        const shade = interpolate(facing, [0, 1], [0.75, 0], {extrapolateLeft: 'clamp'});
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              inset: 0,
              transform: `rotateY(${i * 90}deg) translateZ(${FW / 2}px)`,
              backfaceVisibility: 'hidden',
              overflow: 'hidden',
              background: '#000',
              outline: `8px solid ${C.turmeric}`,
              boxShadow: `0 0 80px ${C.turmeric}55`,
            }}
          >
            {i === 0 ? (
              <>
                <Sequence durationInFrames={OUTRO_START - 20} layout="none">
                  <FaceVideo clipAt={s.clipAt} alignFrame={INTRO} />
                </Sequence>
                <Sequence from={OUTRO_START - 20} layout="none">
                  <FaceVideo clipAt={OUTRO_CLIP_AT} alignFrame={0} />
                </Sequence>
              </>
            ) : (
              <FaceVideo clipAt={s.clipAt} alignFrame={STEP_START(i)} />
            )}
            <div style={{position: 'absolute', inset: 0, background: `rgba(0,0,0,${shade})`}} />
          </div>
        );
      })}
      {/* top & bottom caps */}
      {[1, -1].map((d) => (
        <div
          key={d}
          style={{
            position: 'absolute',
            width: FW,
            height: FW,
            left: 0,
            top: (FH - FW) / 2,
            transform: `rotateX(${90 * d}deg) translateZ(${FH / 2}px)`,
            background: `linear-gradient(135deg, ${C.turmeric}, ${C.turmericDeep})`,
            border: `8px solid ${C.turmeric}`,
          }}
        />
      ))}
    </div>
  );
};

const Title: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const lines = [
    {t: 'TANAM', size: 70, color: C.cream},
    {t: 'TEMU HITAM', size: 118, color: C.turmeric},
    {t: '& TEMU LAWAK', size: 104, color: C.cream},
  ];
  const exit = interpolate(frame, [INTRO - 12, INTRO + 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.in(Easing.cubic),
  });
  return (
    <AbsoluteFill style={{alignItems: 'center', paddingTop: 120, perspective: 1000}}>
      {lines.map((l, i) => {
        const s = spring({frame: frame - 6 - i * 7, fps, config: {damping: 12, mass: 0.7}});
        return (
          <div
            key={l.t}
            style={{
              fontFamily: FONT,
              fontWeight: 900,
              fontSize: l.size,
              lineHeight: 1.05,
              color: l.color,
              letterSpacing: 2,
              textShadow: `0 8px 0 ${C.bgDeep}, 0 0 40px ${C.turmeric}55`,
              transform: `rotateX(${(1 - s) * 90 + exit * -90}deg) translateY(${(1 - s) * 60}px)`,
              opacity: s * (1 - exit),
            }}
          >
            {l.t}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const StepLabel: React.FC<{step: Step; index: number}> = ({step, index}) => {
  const frame = useCurrentFrame(); // local to Sequence
  const {fps} = useVideoConfig();
  const inS = spring({frame: frame - 10, fps, config: {damping: 14}});
  const out = interpolate(frame, [STEP - 12, STEP], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const cubeSpin = frame * 3;
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 150}}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 34,
          padding: '26px 44px 26px 30px',
          borderRadius: 28,
          background: 'rgba(6,20,13,0.78)',
          border: `3px solid ${C.turmeric}88`,
          boxShadow: `0 20px 60px rgba(0,0,0,0.5)`,
          transform: `translateX(${(1 - inS) * -900 + out * 900}px) skewX(${(1 - inS) * 12}deg)`,
          opacity: 1 - out,
        }}
      >
        {/* small spinning number cube */}
        <div style={{width: 110, height: 110, perspective: 500}}>
          <div
            style={{
              width: 110,
              height: 110,
              position: 'relative',
              transformStyle: 'preserve-3d',
              transform: `rotateX(-18deg) rotateY(${cubeSpin}deg)`,
            }}
          >
            {[0, 90, 180, 270].map((a) => (
              <div
                key={a}
                style={{
                  position: 'absolute',
                  inset: 0,
                  transform: `rotateY(${a}deg) translateZ(55px)`,
                  background: `linear-gradient(135deg, ${C.turmeric}, ${C.turmericDeep})`,
                  border: `3px solid ${C.cream}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontFamily: FONT,
                  fontWeight: 900,
                  fontSize: 64,
                  color: C.bgDeep,
                }}
              >
                {index + 1}
              </div>
            ))}
          </div>
        </div>
        <div>
          <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 64, color: C.cream, lineHeight: 1.05}}>
            {step.title}
          </div>
          <div style={{fontFamily: FONT, fontWeight: 600, fontSize: 36, color: C.turmeric, marginTop: 6}}>
            {step.sub}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = spring({frame: frame - 8, fps, config: {damping: 11}});
  const b = spring({frame: frame - 24, fps, config: {damping: 12}});
  const fade = interpolate(frame, [OUTRO - 15, OUTRO], [1, 0], {extrapolateLeft: 'clamp'});
  return (
    <AbsoluteFill style={{alignItems: 'center', opacity: fade}}>
      <div
        style={{
          marginTop: 110,
          textAlign: 'center',
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: 92,
          lineHeight: 1.08,
          color: C.cream,
          textShadow: `0 8px 0 ${C.bgDeep}`,
          transform: `scale(${a}) rotate(${(1 - a) * -8}deg)`,
        }}
      >
        Herba apa lagi
        <br />
        <span style={{color: C.turmeric}}>perlu tanam?</span>
      </div>
      <div
        style={{
          position: 'absolute',
          bottom: 170,
          fontFamily: FONT,
          fontWeight: 800,
          fontSize: 44,
          color: C.bgDeep,
          background: C.turmeric,
          padding: '20px 48px',
          borderRadius: 999,
          transform: `translateY(${(1 - b) * 300}px)`,
          boxShadow: `0 0 50px ${C.turmeric}88`,
        }}
      >
        Komen di bawah 👇
      </div>
    </AbsoluteFill>
  );
};

export const TemuCube: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Intro: prism flies in spinning
  const enter = spring({frame, fps, config: {damping: 16, mass: 1.2}, durationInFrames: 70});
  let rotY = interpolate(enter, [0, 1], [-540, 0]);

  // Each step: spring the prism 90deg to bring the next face forward
  for (let i = 1; i <= STEPS.length; i++) {
    const s = spring({frame: frame - STEP_START(i) + 14, fps, config: {damping: 14, mass: 0.9}});
    rotY -= 90 * s;
  }

  // Ambient sway + bob
  const sway = Math.sin(frame / 28) * 5;
  const bob = Math.sin(frame / 22) * 14;

  // Layout: smaller/lower during intro (room for title), centered in steps, top during outro
  const scale =
    interpolate(enter, [0, 1], [0.1, 0.62]) +
    interpolate(frame, [INTRO - 10, INTRO + 15], [0, 0.18], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) -
    interpolate(frame, [OUTRO_START - 10, OUTRO_START + 15], [0, 0.14], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const y =
    interpolate(frame, [INTRO - 10, INTRO + 15], [1110, 900], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.inOut(Easing.cubic),
    }) +
    interpolate(frame, [OUTRO_START - 10, OUTRO_START + 15], [0, 120], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.inOut(Easing.cubic),
    });

  // Background pulse on each face change
  let pulse = Math.max(0, 1 - Math.abs(frame - INTRO * 0.6) / 20);
  for (let i = 1; i <= STEPS.length; i++) {
    pulse = Math.max(pulse, 1 - Math.abs(frame - STEP_START(i) + 6) / 14);
  }

  const audioVol = (f: number) =>
    interpolate(f, [0, 15, TOTAL_FRAMES - 30, TOTAL_FRAMES], [0, 0.9, 0.9, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });

  return (
    <AbsoluteFill style={{backgroundColor: C.bgDeep}}>
      <Audio src={SRC} volume={audioVol} />
      <CubeField pulse={Math.max(0, pulse)} />

      <AbsoluteFill style={{perspective: 2200}}>
        <div
          style={{
            position: 'absolute',
            left: 540,
            top: y + bob,
            transformStyle: 'preserve-3d',
            transform: `scale(${scale}) rotateX(-8deg) rotateZ(${sway * 0.3}deg)`,
          }}
        >
          <div style={{transformStyle: 'preserve-3d', transform: `rotateY(${sway}deg)`}}>
            <Prism rotY={rotY} />
          </div>
        </div>
      </AbsoluteFill>

      <Sequence durationInFrames={INTRO + 10}>
        <Title />
      </Sequence>

      {STEPS.map((s, i) => (
        <Sequence key={s.title} from={STEP_START(i)} durationInFrames={STEP}>
          <StepLabel step={s} index={i} />
        </Sequence>
      ))}

      <Sequence from={OUTRO_START}>
        <Outro />
      </Sequence>
    </AbsoluteFill>
  );
};

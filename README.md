# video-claude-

Remotion motion graphic: **Tanam Temu Hitam & Temu Lawak** with an animated 3D cube background.

- 1080x1920 (9:16), 30fps, ~22.5s
- Background: floating 3D wireframe cubes + perspective grid floor (`src/CubeField.tsx`)
- Hero: a 3D video prism — each face plays a different clip, it rotates 90° per step (`src/TemuCube.tsx`)

## Setup

Put the source footage at `public/source.mp4` (not committed), then:

```bash
npm install
npm run studio   # preview
npm run render   # -> out/temu-cube.mp4
```

Edit step titles / clip timestamps in the `STEPS` array in `src/TemuCube.tsx`.

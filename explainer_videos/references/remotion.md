# Remotion reference

Use this for code walkthroughs, UI or system-architecture flows, timelines, and styled
typography. Remotion renders React components frame by frame. Animation is a pure function
of `useCurrentFrame()`.

## Setup

```bash
npx create-video@latest --blank remotion   # inside videos/<slug>/
cd remotion && npm i
# Copy narration + assets where staticFile() can reach them:
mkdir -p public && cp -r ../audio public/audio && cp -r ../assets public/assets 2>/dev/null || true
```

Check the installed version's docs if an import fails. Recent versions also ship
`@remotion/media` (with its own `<Audio>`/`<Video>`). The classic `Audio`, `OffthreadVideo`
and `Img` exports from `remotion` are used below.

## Beat-synced scene

```tsx
// src/beats.ts
import timings from "../public/audio/timings.json";
export const FPS = 30;
export const f = (sec: number) => Math.round(sec * FPS);
export function sceneTimings(id: string) {
  const s = timings.scenes.find((x) => x.id === id)!;
  const beats = Object.fromEntries(s.beats.map((b) => [b.id, b]));
  return { durationInFrames: f(s.duration), beats };
}
```

```tsx
// src/scenes/S03Formalize.tsx
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";
import { sceneTimings, f } from "../beats";
import { theme } from "../theme";

const ID = "s03_formalize";
const { beats } = sceneTimings(ID);

export const S03Formalize: React.FC = () => (
  <AbsoluteFill style={{ background: theme.bg, color: theme.text, fontFamily: theme.font }}>
    <Audio src={staticFile(`audio/${ID}.wav`)} />
    <Sequence from={f(beats.b1.start)}>
      <Title />
    </Sequence>
    <Sequence from={f(beats.b2.start)}>
      <QueryBox />   {/* stays mounted until the scene ends */}
    </Sequence>
  </AbsoluteFill>
);

const QueryBox: React.FC = () => {
  const frame = useCurrentFrame();            // local to the Sequence
  const { fps } = useVideoConfig();
  const s = spring({ frame, fps, config: { damping: 200 } });
  return <div style={{ transform: `scale(${s})`, opacity: s, border: `3px solid ${theme.query}` }}>Q = X·W_Q</div>;
};
```

Register one composition per scene, and optionally a `Full` composition that chains them
with `<Series>`:

```tsx
// src/Root.tsx (default output 854x480; change only if the user asks for higher)
<Composition id="s03" component={S03Formalize} fps={FPS} width={854} height={480}
  durationInFrames={sceneTimings("s03_formalize").durationInFrames} />
```

Size everything relative to the frame (`theme.u`, below) so the same code renders cleanly
at 480p or at a larger size later.

## Render

```bash
npx remotion render s03 ../out/s03.mp4 --hardware-acceleration=if-possible --concurrency=100%
npx remotion still s03 check.png --frame=240
```
`--hardware-acceleration=if-possible` uses the GPU encoder (e.g. VideoToolbox on macOS)
when Remotion supports it for the codec, and otherwise falls back to software. If your
Remotion version rejects the flag, drop it.

## Patterns

- **Easing:** `interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) })`.
- **Springs** for objects entering. Use `damping: 200` for no bounce, which suits technical
  content.
- **Code walkthroughs:** render tokens with a syntax highlighter (e.g. `shiki` precomputed
  to HTML), then animate a highlight bar's `top` between line positions on each beat. Dim
  the lines that aren't active.
- **Diagrams:** inline SVG. Animate `strokeDashoffset` to draw paths, and animate
  `<circle>` positions along a path with `@remotion/paths` (`getPointAtLength`).
- **Math:** pre-render KaTeX to HTML (`katex.renderToString`) and color its spans to match
  the palette.
- **Charts:** compute values in plain TS and draw SVG. Animate growth with interpolate.
- **Generated media:** `<Img src={staticFile("assets/x.png")} />`,
  `<OffthreadVideo src={staticFile("assets/hook.mp4")} />`.

## Theme (`src/theme.ts`)

```ts
export const HEIGHT = 480;
export const theme = {
  bg: "#0f1117", text: "#e6e6e6", dim: "#6b7280",
  query: "#60a5fa", key: "#f59e0b", value: "#34d399", error: "#f87171", accent: "#c084fc",
  font: "Inter, system-ui, sans-serif",
  u: HEIGHT / 100,   // 1u = 1% of frame height; body text >= 5u, titles ~8u, strokes >= 0.6u
};
```

## Gotchas

- Never use `Math.random()`, CSS transitions, or `setTimeout`. Everything must be
  deterministic in `frame`. Use `random(seed)` from `remotion`.
- Importing JSON needs `resolveJsonModule` in tsconfig (the default template has it).
- Keep text ≥ 5u (about 24px at 480p). Smaller text is unreadable at the default resolution.

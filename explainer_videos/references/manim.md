# Manim (Community Edition) reference

Default renderer. One `Scene` class per script scene, one `.py` file per scene (or a few per
file), each rendered separately.

## Beat-synced base scene

Copy this into the project as `scenes/beats.py`. It loads `audio/timings.json` (made by
`narrate.py`), attaches the scene's narration track, and lets you size animations to beats.

```python
import json
from pathlib import Path
from manim import Scene

PROJECT = Path(__file__).resolve().parent.parent  # videos/<slug>/

class BeatScene(Scene):
    SCENE_ID: str = ""  # must match a scene id in script.json

    def setup(self):
        timings = json.loads((PROJECT / "audio/timings.json").read_text())
        scene = next(s for s in timings["scenes"] if s["id"] == self.SCENE_ID)
        self.beats = {b["id"]: b for b in scene["beats"]}
        self.scene_duration = scene["duration"]
        self.add_sound(str(PROJECT / "audio" / f"{self.SCENE_ID}.wav"))

    # --- timing helpers -------------------------------------------------
    def now(self) -> float:
        return self.renderer.time

    def at(self, beat_id: str):
        """Wait until the beat's narration starts."""
        gap = self.beats[beat_id]["start"] - self.now()
        if gap > 1e-3:
            self.wait(gap)

    def left(self, beat_id: str) -> float:
        """Seconds until the beat's slot ends (start of the next beat)."""
        return max(0.0, self.beats[beat_id]["slot_end"] - self.now())

    def beat(self, beat_id: str, *anims, share: float = 0.7, min_rt: float = 0.4, **play_kw):
        """Start at the beat, play anims over `share` of the beat, then hold until the slot ends."""
        self.at(beat_id)
        if anims:
            rt = max(min_rt, self.left(beat_id) * share)
            self.play(*anims, run_time=rt, **play_kw)
        hold = self.left(beat_id)
        if hold > 1e-3:
            self.wait(hold)

    def finish(self):
        rest = self.scene_duration - self.now()
        if rest > 1e-3:
            self.wait(rest)
```

Usage:

```python
from manim import *
from beats import BeatScene
from style import C   # palette

class S02Intuition(BeatScene):
    SCENE_ID = "s02_intuition"

    def construct(self):
        q = Vector([2, 1], color=C.query)
        k = Vector([1, 2], color=C.key)
        self.beat("b1", GrowArrow(q))
        self.beat("b2", GrowArrow(k))
        # Several steps in one beat: split the time yourself
        self.at("b3")
        t = self.left("b3")
        self.play(Indicate(q), run_time=t * 0.3)
        self.play(Create(Angle(k, q)), run_time=t * 0.4)
        self.wait(self.left("b3"))
        self.finish()
```

Render (default output: 480p30):
```bash
cd videos/<slug>/scenes
manim -ql -r 854,480 --fps 30 s02_intuition.py S02Intuition   # default output: 854x480 @ 30fps
# Higher resolution only if the user asked: -qh (1080p60) / -qk (4K)
# Output: media/videos/<file>/480p30/<Class>.mp4 (with audio, since add_sound was used)
```
At 480p Manim's own encoding is already fast. Hardware encoding (`scripts/hwenc.py`) is for
the later ffmpeg steps that re-encode.

## Shared style (`scenes/style.py`)

```python
from manim import config, ManimColor
config.background_color = "#0f1117"

class C:
    text = ManimColor("#e6e6e6")
    dim = ManimColor("#6b7280")
    query = ManimColor("#60a5fa")   # blue
    key = ManimColor("#f59e0b")     # amber
    value = ManimColor("#34d399")   # green
    error = ManimColor("#f87171")   # red
    accent = ManimColor("#c084fc")  # purple, for highlights only

FONT = "Inter"   # fall back to the default if it isn't installed
```

## Patterns that teach well

- **Progressive build:** `LaggedStart(*[FadeIn(m, shift=UP*0.2) for m in parts], lag_ratio=0.15)`.
- **Identity through change:** `TransformMatchingTex`, `TransformMatchingShapes`, and
  `ReplacementTransform(old, new)` when a thing becomes another form of itself.
- **Focus:** `Indicate`, `Circumscribe`, `Flash`, `SurroundingRectangle`, or dim the rest
  with `others.animate.set_opacity(0.25)`.
- **Equation ↔ picture:** `MathTex(r"q", r"\cdot", r"k")` with `.set_color_by_tex` (or index
  into submobjects) using the same colors as the vectors. Build the equation term by term in
  step with the narration.
- **Live values:** `ValueTracker` + `always_redraw` / `DecimalNumber.add_updater` for
  quantities that change as a parameter moves (learning rate, angle, temperature).
- **Data structures:** `VGroup` of `Square` + `Text` cells for arrays, `Matrix` /
  `DecimalMatrix` for matrices, `Graph` / `DiGraph` for graphs and trees (layout="tree").
- **Plots:** `Axes` + `axes.plot(f)`, with `axes.get_area`, `get_riemann_rectangles`, and
  `TangentLine` for calculus.
- **Camera:** `MovingCameraScene` with `self.camera.frame.animate.scale(0.5).move_to(x)` to
  zoom into detail. Use it sparingly, and bring the camera back out.
- **Code:** `Code(code_string=..., language="python")`, highlighting lines with a
  `SurroundingRectangle` that moves as the narration steps through.
- **3D:** `ThreeDScene` + `self.set_camera_orientation(phi=..., theta=...)`, and
  `begin_ambient_camera_rotation` slowly. Use 3D only when it is actually needed.

## Generated images inside Manim

`ImageMobject("assets/foo.png").scale_to_fit_height(4)` with `FadeIn`. Keep it as context
next to the diagram, never as the diagram itself.

## Gotchas

- `MathTex` needs LaTeX. If it's missing, use `Text` / `MarkupText` and Unicode math, or
  install BasicTeX (`brew install --cask basictex`), then
  `sudo tlmgr install standalone preview doublestroke relsize fundus-calligra wasysym physics dvisvgm rsfs wasy cm-super everysel`.
- `self.wait(0)` raises an error, so the helpers guard against it. Keep the guards if you
  edit them.
- 480p legibility: the frame is 8 units tall at any resolution, so keep body `Text` at
  `font_size` ≥ 28 and lines at `stroke_width` ≥ 3. Thin hairlines and small labels turn to
  mush at 854×480.
- Text overflowing the frame: the frame is 14.2 × 8 units. Use `.scale_to_fit_width(12)`
  and `.to_edge(UP, buff=0.5)`.
- Leftover mobjects pile up. `FadeOut` whatever isn't needed before the next idea arrives.
- To check frames: `ffmpeg -ss 12.5 -i S02Intuition.mp4 -frames:v 1 check.png`, then Read the
  PNG.

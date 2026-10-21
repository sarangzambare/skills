---
name: explainer-videos
description: Produce a narrated, animated explainer video that teaches a deeply technical concept (algorithms, math, ML, systems, physics, protocols) the way a great professor would. Builds programmatic animations with Manim or Remotion, narrates with Kokoro TTS (local, CPU-friendly), and pulls any extra generative assets (images, video clips; music only on request) from OpenRouter. Runs end to end without asking questions and outputs a 480p MP4 by default. Use when the user asks for an explainer video, an animated lesson, a "3Blue1Brown-style" visualization, or a video that explains how something works.
---

# Explainer Videos

You are making a lecture, not a trailer. The video works only if a motivated viewer who has
never seen the concept can explain it back afterwards. Every choice (script, visuals,
pacing, assets) serves that goal. Looking nice comes second to being understood.

## Operating rules

- **Run fully autonomously.** Don't ask the user questions, wait for approval, or stop at
  checkpoints. If something is ambiguous (audience, length, framework, style), make the most
  reasonable choice, write it in `notes.md`, and keep going. The deliverable is a finished
  `final.mp4`, not a plan. If a tool is missing, install it. If a step fails, fix it or
  fall back (e.g. no LaTeX → `Text`; no OpenRouter key → draw it in code) rather than
  stopping.
- **Default output is 480p (854×480) at 30 fps.** Render at a higher resolution only if the
  user asks for one.
- **Encode with hardware acceleration when available.** Whenever ffmpeg has to re-encode
  video, use the encoder args from `python SKILL_DIR/scripts/hwenc.py`. It detects
  VideoToolbox, NVENC, QSV, VAAPI or AMF and falls back to `libx264 -preset ultrafast`.
  Use stream copy (`-c:v copy`) wherever no re-encode is needed.
- **No background music unless the user asks for it.** The narration is the only audio by
  default. Don't generate music, and don't add sound effects unless they were requested.

## Toolchain at a glance

| Job | Tool | Notes |
|---|---|---|
| Diagrams, math, graphs, step-by-step mechanisms | **Manim Community** (default) | Best for math, geometry, equations, data structures, plots |
| UI-like layouts, code walkthroughs, text-heavy or web-styled scenes | **Remotion** (React) | Use when the content looks more like software or slides than geometry |
| Narration | **Kokoro TTS** via `scripts/narrate.py` | Always the default voice. Runs locally on CPU, no API key |
| Images, b-roll video (music/SFX only on request) | **OpenRouter** via `scripts/openrouter.py` | Only for things you can't draw in code. Key lives in `.env` |
| Muxing, concatenation, loudness | **ffmpeg** + `scripts/hwenc.py` | Hardware encoder auto-detected |

Paths below are relative to this skill's directory (`SKILL_DIR`, the folder holding this
file). Put the project in its own working folder (e.g. `./videos/<slug>/`). Never write
into `SKILL_DIR`.

Pick **one** animation framework per video yourself. Default to Manim. Choose Remotion only
when the subject is mostly code, UI, timelines or styled text. Read the matching reference before
writing any scene code:
- `references/manim.md`
- `references/remotion.md`

Read `references/pedagogy.md` before writing the script. It covers the teaching principles
this skill depends on.

---

## Workflow

Work through these phases in order. Each one produces a file, so you can stop, show the user,
and pick up again later.

### Phase 0: Set up the environment (once per machine)

```bash
# Narration
pip install "kokoro>=0.9" soundfile numpy
brew install espeak-ng            # macOS (Linux: apt-get install espeak-ng). Kokoro needs it as a fallback phonemizer

# Manim (default renderer)
brew install py3cairo pango ffmpeg   # macOS system deps; see manim docs for Linux
pip install manim
# LaTeX for MathTex. Install BasicTeX or MacTeX, or avoid MathTex and use Text

# Remotion (only if chosen)
npx create-video@latest --blank <project-dir>
```

Before you spend any time, check what's already installed (`which manim ffmpeg`,
`python -c "import kokoro"`). Install only what's missing, without asking, and mention it
in the final report. Kokoro downloads its ~330 MB model weights from Hugging Face on first
use. Run `python SKILL_DIR/scripts/hwenc.py` once to detect and cache the hardware encoder.

OpenRouter key: `scripts/openrouter.py` reads `OPENROUTER_API_KEY` from `SKILL_DIR/.env`,
falling back to the environment. If the key is empty, keep going without generated assets
(draw it in code instead) and mention that to the user. Never print the key, and never copy
it into project files.

### Phase 1: Understand the concept deeply

You can't teach what you only half understand. Before you write a word of script:
1. Write `notes.md` in the project folder. Include the precise definition, the core
   mechanism, a minimal worked example with real numbers, the common misconceptions,
   prerequisites, and one or two non-obvious insights (the "aha").
2. If the concept is specialized or recent, check the facts (papers, official docs) rather
   than relying on memory. Wrong content makes the whole video worthless.
3. Decide who the audience is (default: technical undergrad or practicing engineer) and
   which prerequisites you will assume versus briefly recap.

### Phase 2: Lesson plan → `outline.md`

Build the lesson as a chain of **learning objectives**, with each scene earning exactly one.
The standard arc:

1. **Hook / motivating problem** (~10%). A concrete question the concept answers. Make
   the viewer *want* the answer.
2. **Intuition first** (~25%). A physical analogy or tiny example, worked visually with no
   jargon yet.
3. **Formalize** (~30%). Introduce notation and terms, and map each symbol back to the
   picture the viewer already holds.
4. **Worked example, step by step** (~20%). Real numbers, every step shown, nothing
   skipped.
5. **Edge cases, misconceptions, "why it works"** (~10%).
6. **Recap** (~5%). Rebuild the whole idea in one compressed visual, ideally the same
   diagram from the intuition section, now fully labeled.

For each scene, list: objective, the key visual, the narration gist, and what must already
be on screen. Target length: about 150 words of narration per minute. A 5 to 12 minute
video is typical for a deep topic. If the user hasn't given a length, choose one from the
topic's depth and note your choice in `outline.md`.

Don't stop for approval. Critique the outline yourself against `references/pedagogy.md`,
tighten it, and move straight on to the script.

### Phase 3: Script → `script.json`

Narration drives timing. Write it as scenes made of **beats**. A beat is one or two
sentences that go with exactly one visual change.

```json
{
  "title": "How Attention Works",
  "voice": "af_heart",
  "speed": 1.0,
  "scenes": [
    {
      "id": "s01_hook",
      "beats": [
        {"id": "b1", "text": "Read this sentence: the animal didn't cross the street because it was too tired.", "visual": "Sentence fades in word by word"},
        {"id": "b2", "text": "What does 'it' refer to? You knew instantly. A model has to compute that.", "visual": "Arrow from 'it' wavers between 'animal' and 'street'", "pause_after": 0.8}
      ]
    }
  ]
}
```

Rules for narration text:
- Write for the ear. Keep sentences short and use concrete nouns. Say "this arrow", "the
  blue box", and "now watch the top row" so speech and picture stay tied together.
- Before each new term, give the reason for it. Define every term the first time it
  appears, and keep the same word for the same thing throughout.
- Spell out symbols the way a professor says them aloud: "x sub i", "the sum over j",
  "W transpose". Kokoro reads raw LaTeX badly. Write numbers the way you'd say them.
- Fix pronunciation with Kokoro's inline syntax: `[Kokoro](/kˈOkəɹO/)`. Acronyms read as
  letters are usually best spelled with spaces or periods (`G P U`).
- Use `pause_after` (seconds) after a key reveal so the viewer has time to think. Real
  teachers pause.
- Each beat's `visual` field is the animation contract that Phase 5 implements.

### Phase 4: Narration → audio + timings

```bash
python SKILL_DIR/scripts/narrate.py script.json --out audio/
```

This produces `audio/<scene_id>/<beat_id>.wav`, one `audio/<scene_id>.wav` per scene, and
`audio/timings.json` holding each beat's `start`, `end`, and `duration` in seconds within its
scene, plus `audio/captions.srt`. Beats whose text hasn't changed are cached, so re-running
after edits is cheap.

Voices: `af_heart` (default, warm American female), `am_michael`, `am_fenrir` (American
male), `bf_emma`, `bm_george` (British). Set `"lang"` in script.json to `"b"` for British
voices. Speed between 0.9 and 1.05 suits dense technical content.

Listen to (or at least sanity-check) one scene before animating everything. Mispronounced
key terms damage trust.

### Phase 5: Animate, synced to timings

**Animations follow the audio, never the other way around.** Load `timings.json` inside the
scene code and size every animation to its beat's duration (see the beat-sync helpers in
the framework references). Hard-coded `run_time`s drift out of sync whenever narration
changes.

Visual standards. These are not optional:
- **Show the mechanism, don't decorate it.** Every on-screen element should be something
  the narration is talking about right now, or something the viewer must remember. Remove
  everything else.
- **One new idea per beat.** Reveal progressively. Never put a full diagram up and then
  talk through it. Build it piece by piece while you talk.
- **Visual continuity.** Transform objects into their next form (`Transform`,
  `ReplacementTransform`, Remotion interpolation) rather than cutting. When a vector
  becomes a matrix row, *morph* it. Continuity is how viewers keep track of identity.
- **Consistent color semantics.** Define a palette once (e.g. inputs = blue, weights =
  orange, outputs = green, error = red) and never reuse a color for a different meaning.
  Put it in a shared `style.py` or `theme.ts`.
- **Highlight what's being discussed.** Indicate, Circumscribe, dim the rest
  (opacity 0.3), or move a pointer. The viewer's eye should never have to search.
- **Real numbers on screen** in worked examples: matrices with values, arrays with
  contents, step counters.
- **Equations next to their picture.** Color-match each symbol to the visual element it
  names.
- **Readable at 480p.** That's the default output, so text must stay legible at 854×480:
  body text at least about 1/20 of frame height, thick strokes (≥ 3 px), at most about 10
  words of on-screen text at once, safe margins, high contrast. Dark background by default.
- **Pacing.** Leave about 0.5 s of stillness after each major reveal. Don't cram a dense
  equation into a 2 s beat. Split the beat instead.

Render each scene at the output resolution (480p30 by default; see the framework
reference for the exact flags). Check a few frames of each scene (extract stills with
ffmpeg and look at them) for overlap, off-screen text, and sync, then fix and re-render
only the scenes that need it.

### Phase 6: Generated assets (only when code can't draw it)

Use OpenRouter for things like photorealistic context shots ("a real data center", "a
neuron under a microscope") or a cinematic hook clip. Generate music or sound effects
**only if the user asked for them**. Do **not** use it for diagrams, charts, equations, or
anything that has to be exact. Draw those in code, because generative models get the
details wrong.

```bash
# List what's available right now (the catalog changes often, so check before choosing)
python SKILL_DIR/scripts/openrouter.py models --kind image|video|audio

# Image (16:9 for full-frame b-roll; 1:1 for inset illustrations)
python SKILL_DIR/scripts/openrouter.py image --prompt "..." --aspect 16:9 --out assets/datacenter.png

# Short video clip (async; the script polls until done; defaults to 480p)
python SKILL_DIR/scripts/openrouter.py video --prompt "..." --duration 5 --out assets/hook.mp4 [--first-frame assets/frame.png]

# Music / audio, ONLY when the user asked for it
python SKILL_DIR/scripts/openrouter.py audio --prompt "calm ambient instrumental, no vocals, 60 seconds" --out assets/music.wav
```

Default models are set in the script and can be overridden with `--model`. Generation costs
money, so use it sparingly: generate one candidate before many, and reuse assets. Look at
every generated image (Read it) before using it. Reject and regenerate anything with
garbled text, wrong technical details, or a style that clashes with the palette. If it
still isn't right after two tries, draw it in code instead.

Generated clips arrive in arbitrary sizes and frame rates. Normalize each one to the
output format before using it:
```bash
ffmpeg -y -i assets/hook.mp4 -vf "scale=854:480:force_original_aspect_ratio=decrease,pad=854:480:(ow-iw)/2:(oh-ih)/2,fps=30" \
  $(python SKILL_DIR/scripts/hwenc.py) -an assets/hook_480.mp4
```

### Phase 7: Assemble and master

Render each scene to its own file with its scene audio muxed in. Then concatenate. Copy
the video stream wherever you can. When you must re-encode, use the hardware encoder.

```bash
ENC="$(python SKILL_DIR/scripts/hwenc.py)"   # e.g. -c:v h264_videotoolbox -b:v 2M ...

# Per scene (Manim: if the scene used self.add_sound, audio is already embedded; skip this)
ffmpeg -y -i video/s01.mp4 -i audio/s01_hook.wav -c:v copy -c:a aac -shortest out/s01.mp4

# Concatenate. Stream copy works when every scene has the same codec, resolution and fps.
printf "file '%s'\n" out/s*.mp4 > list.txt
ffmpeg -y -f concat -safe 0 -i list.txt -c copy final_raw.mp4
#   If scenes don't match (mixed sources), re-encode instead:
#   ffmpeg -y -f concat -safe 0 -i list.txt -vf "scale=854:480,fps=30" $ENC -c:a aac final_raw.mp4

# Loudness-normalize the narration to -16 LUFS (audio-only re-encode; video is copied)
ffmpeg -y -i final_raw.mp4 -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:v copy -c:a aac -b:a 160k final.mp4
```

**Music only if the user asked for it.** In that case, mix it well under the voice
(around 12% volume, no vocals):
```bash
ffmpeg -y -i final_raw.mp4 -stream_loop -1 -i assets/music.wav \
  -filter_complex "[1:a]volume=0.12[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0,loudnorm=I=-16:TP=-1.5:LRA=11[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 160k final.mp4
```

Ship `captions.srt` alongside the video. Burn it in only if the user asked (that step
re-encodes, so use `$ENC`).

### Phase 8: Review like a student

Before handing the video over, watch it as the target viewer would. Sample frames at every
scene boundary and at key beats, and check:
- [ ] Is every term defined before it's used? Is every symbol tied to a visual?
- [ ] Does each scene earn its objective? Could a viewer pause anywhere and know what the
      screen means?
- [ ] Do audio and animation stay in sync throughout, with nothing drifting by the end?
- [ ] Is there any overlapping, clipped, or too-small text?
- [ ] Are the numbers in the worked example correct? Recompute them.
- [ ] Does the recap actually reconstruct the idea, rather than just listing words?

Fix the problems yourself, re-render only the affected scenes, and re-assemble. Do this
without asking. Only then report to the user: the final path, runtime and resolution, the
scenes and what each teaches, the assumptions you made, which assets were generated (and
their approximate cost), and anything you'd improve with another pass.

---

## Project layout

```
videos/<slug>/
  notes.md          # research + misconceptions
  outline.md        # objectives + scene list + assumptions
  script.json       # narration beats (the source of truth for timing)
  audio/            # narrate.py output: wavs, timings.json, captions.srt
  assets/           # OpenRouter-generated images/video/music
  scenes/           # manim .py files or remotion src/
  style.py|theme.ts # palette + typography, shared by all scenes
  out/              # per-scene muxed mp4s
  final.mp4
```

## Failure modes to avoid

- A slideshow with voice-over: static text while the narrator explains. If nothing moves
  while an idea is being explained, the scene is wrong.
- Animation as decoration: spinning logos, particle backgrounds, transitions that carry
  no meaning.
- Skipping the intuition and jumping straight to equations.
- Narration that describes what's on screen ("here we see a graph") instead of explaining
  what it *means*.
- Generated images standing in for technical diagrams.
- One giant render. Keep scenes separate so a fix costs one scene, not the whole video.
- Stopping to ask the user something. Decide, record the assumption, and deliver the video.

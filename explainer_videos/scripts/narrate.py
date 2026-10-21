#!/usr/bin/env python3
"""Synthesize narration for an explainer video with Kokoro TTS (runs on CPU).

Input:  script.json  {"voice": "af_heart", "speed": 1.0, "lang": "a",
                      "scenes": [{"id": "s01", "beats": [{"id": "b1", "text": "...", "pause_after": 0.5}]}]}
Output (in --out):
  <scene>/<beat>.wav     one clip per beat (cached by text+voice+speed)
  <scene>.wav            full scene track: lead-in + beats + pauses + tail
  timings.json           per-beat start / end / slot_end / duration in seconds, relative to the scene start
  captions.srt           subtitles for the whole video (scenes laid back to back)
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 24000


def to_numpy(audio):
    if hasattr(audio, "detach"):
        audio = audio.detach().cpu().numpy()
    return np.asarray(audio, dtype=np.float32)


def silence(seconds):
    return np.zeros(int(round(seconds * SR)), dtype=np.float32)


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", type=Path)
    ap.add_argument("--out", type=Path, default=Path("audio"))
    ap.add_argument("--voice", help="override script voice (default af_heart)")
    ap.add_argument("--speed", type=float, help="override script speed (default 1.0)")
    ap.add_argument("--lang", help="kokoro lang code: a=American, b=British (default: from voice prefix)")
    ap.add_argument("--gap", type=float, default=0.35, help="default pause between beats (s)")
    ap.add_argument("--lead", type=float, default=0.5, help="silence before the first beat of each scene (s)")
    ap.add_argument("--tail", type=float, default=0.8, help="silence after the last beat of each scene (s)")
    ap.add_argument("--scene", action="append", help="only (re)build these scene ids")
    args = ap.parse_args()

    script = json.loads(args.script.read_text())
    voice = args.voice or script.get("voice", "af_heart")
    speed = args.speed or script.get("speed", 1.0)
    lang = args.lang or script.get("lang") or voice[0]

    from kokoro import KPipeline  # imported late so --help works without kokoro installed

    pipe = KPipeline(lang_code=lang)
    args.out.mkdir(parents=True, exist_ok=True)

    timings_path = args.out / "timings.json"
    old = json.loads(timings_path.read_text()) if timings_path.exists() else {"scenes": []}
    old_scenes = {s["id"]: s for s in old.get("scenes", [])}

    scenes_out = []
    for scene in script["scenes"]:
        sid = scene["id"]
        if args.scene and sid not in args.scene and sid in old_scenes:
            scenes_out.append(old_scenes[sid])
            continue
        sdir = args.out / sid
        sdir.mkdir(exist_ok=True)
        parts = [silence(args.lead)]
        t = args.lead
        beats = []
        for i, beat in enumerate(scene["beats"]):
            text = beat["text"].strip()
            key = hashlib.sha1(f"{voice}|{speed}|{lang}|{text}".encode()).hexdigest()[:12]
            wav = sdir / f"{beat['id']}.wav"
            stamp = sdir / f"{beat['id']}.key"
            if wav.exists() and stamp.exists() and stamp.read_text() == key:
                audio, _ = sf.read(wav, dtype="float32")
            else:
                chunks = [to_numpy(a) for _, _, a in pipe(text, voice=voice, speed=speed) if a is not None]
                if not chunks:
                    raise SystemExit(f"Kokoro produced no audio for {sid}/{beat['id']}: {text!r}")
                audio = np.concatenate(chunks)
                sf.write(wav, audio, SR)
                stamp.write_text(key)
                print(f"  synthesized {sid}/{beat['id']} ({len(audio) / SR:.2f}s)")
            dur = len(audio) / SR
            last = i == len(scene["beats"]) - 1
            pause = beat.get("pause_after", args.tail if last else args.gap)
            beats.append({
                "id": beat["id"],
                "text": text,
                "start": round(t, 3),
                "end": round(t + dur, 3),
                "slot_end": round(t + dur + pause, 3),
                "duration": round(dur, 3),
            })
            parts += [audio, silence(pause)]
            t += dur + pause
        track = np.concatenate(parts)
        sf.write(args.out / f"{sid}.wav", track, SR)
        scenes_out.append({"id": sid, "duration": round(len(track) / SR, 3), "beats": beats})
        print(f"{sid}: {len(track) / SR:.2f}s, {len(beats)} beats")

    timings = {"sample_rate": SR, "voice": voice, "speed": speed, "scenes": scenes_out}
    timings_path.write_text(json.dumps(timings, indent=2))

    lines, offset, n = [], 0.0, 1
    for s in scenes_out:
        for b in s["beats"]:
            lines += [str(n), f"{srt_time(offset + b['start'])} --> {srt_time(offset + b['end'])}", b["text"], ""]
            n += 1
        offset += s["duration"]
    (args.out / "captions.srt").write_text("\n".join(lines))
    print(f"total narration: {offset / 60:.1f} min -> {timings_path}")


if __name__ == "__main__":
    main()

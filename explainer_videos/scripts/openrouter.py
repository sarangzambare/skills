#!/usr/bin/env python3
"""Generate images, video clips and audio/music through OpenRouter (stdlib only).

The API key is read from OPENROUTER_API_KEY in <skill>/.env, then ./.env, then the environment.

  openrouter.py models --kind image|video|audio
  openrouter.py image --prompt "..." --out assets/x.png [--aspect 16:9] [--resolution 2K] [--ref in.png] [--model ...]
  openrouter.py video --prompt "..." --out assets/x.mp4 [--duration 5] [--resolution 1080p] [--first-frame f.png] [--audio]
  openrouter.py audio --prompt "..." --out assets/music.wav [--model google/lyria-3-clip-preview]   # only when music was requested
"""
import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://openrouter.ai/api/v1"
SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULTS = {
    "image": "google/gemini-3.1-flash-image",
    "video": "google/veo-3.1-fast",
    "audio": "google/lyria-3-clip-preview",
}


def load_key():
    for env in (SKILL_DIR / ".env", Path.cwd() / ".env"):
        if env.exists():
            for line in env.read_text().splitlines():
                line = line.strip()
                if line.startswith("OPENROUTER_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip("'\"")
                    if val:
                        return val
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        sys.exit(f"OPENROUTER_API_KEY is not set. Put it in {SKILL_DIR / '.env'}")
    return key


def request(method, path, body=None, key=None, raw=False):
    headers = {"Content-Type": "application/json", "X-Title": "explainer-videos-skill"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    url = path if path.startswith("http") else API + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=600)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} from {url}:\n{e.read().decode(errors='replace')}")
    if raw:
        return resp
    with resp:
        return json.loads(resp.read())


def data_url(path):
    mime = mimetypes.guess_type(path)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode()}"


def image_ref(path):
    return {"type": "image_url", "image_url": {"url": data_url(path)}}


def report_cost(resp):
    cost = (resp.get("usage") or {}).get("cost")
    if cost is not None:
        print(f"cost: ${cost}")


def cmd_models(a):
    kind = a.kind
    if kind == "image":
        models = request("GET", "/images/models")["data"]
    elif kind == "video":
        models = request("GET", "/videos/models")["data"]
    else:
        models = request("GET", f"/models?output_modalities={kind}")["data"]
    for m in models:
        print(f"{m['id']:<50} {m.get('name', '')}")


def cmd_image(a):
    key = load_key()
    body = {"model": a.model or DEFAULTS["image"], "prompt": a.prompt, "n": a.n}
    if a.aspect:
        body["aspect_ratio"] = a.aspect
    if a.resolution:
        body["resolution"] = a.resolution
    if a.ref:
        body["input_references"] = [image_ref(p) for p in a.ref]
    resp = request("POST", "/images", body, key)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    for i, item in enumerate(resp.get("data", [])):
        if "b64_json" in item:
            blob = base64.b64decode(item["b64_json"])
        elif "url" in item:
            with request("GET", item["url"], raw=True) as r:
                blob = r.read()
        else:
            continue
        path = out if i == 0 else out.with_name(f"{out.stem}_{i}{out.suffix}")
        path.write_bytes(blob)
        print(f"wrote {path}")
    report_cost(resp)


def cmd_video(a):
    key = load_key()
    body = {"model": a.model or DEFAULTS["video"], "prompt": a.prompt, "generate_audio": a.audio}
    for field, val in (("duration", a.duration), ("resolution", a.resolution), ("aspect_ratio", a.aspect)):
        if val is not None:
            body[field] = val
    if a.first_frame:
        body["frame_images"] = [{**image_ref(a.first_frame), "frame_type": "first_frame"}]
    if a.ref:
        body["input_references"] = [image_ref(p) for p in a.ref]
    job = request("POST", "/videos", body, key)
    poll = job.get("polling_url") or f"{API}/videos/{job['id']}"
    print(f"job {job.get('id')} submitted; polling...")
    deadline = time.time() + a.timeout
    while True:
        st = request("GET", poll, key=key)
        status = st.get("status")
        if status == "completed":
            break
        if status == "failed":
            sys.exit(f"video generation failed: {json.dumps(st, indent=2)}")
        if time.time() > deadline:
            sys.exit(f"timed out; resume later by polling {poll}")
        print(f"  {status}...")
        time.sleep(10)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    urls = st.get("unsigned_urls") or [f"{API}/videos/{st['id']}/content?index=0"]
    for i, url in enumerate(urls):
        path = out if i == 0 else out.with_name(f"{out.stem}_{i}{out.suffix}")
        with request("GET", url, key=key, raw=True) as r:
            path.write_bytes(r.read())
        print(f"wrote {path}")
    report_cost(st)


def cmd_audio(a):
    key = load_key()
    fmt = Path(a.out).suffix.lstrip(".") or "wav"
    body = {
        "model": a.model or DEFAULTS["audio"],
        "messages": [{"role": "user", "content": a.prompt}],
        "modalities": ["text", "audio"],
        "audio": {"format": fmt, **({"voice": a.voice} if a.voice else {})},
        "stream": True,
    }
    chunks, transcript, usage = [], [], None
    with request("POST", "/chat/completions", body, key, raw=True) as resp:
        for raw in resp:
            line = raw.decode().strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            evt = json.loads(payload)
            if "error" in evt:
                sys.exit(f"error: {evt['error']}")
            usage = evt.get("usage") or usage
            for ch in evt.get("choices", []):
                audio = (ch.get("delta") or {}).get("audio") or {}
                if audio.get("data"):
                    chunks.append(base64.b64decode(audio["data"]))
                if audio.get("transcript"):
                    transcript.append(audio["transcript"])
    if not chunks:
        sys.exit("no audio returned; check the model supports audio output (`models --kind audio`)")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    blob = b"".join(chunks)
    if fmt == "pcm16":
        out = out.with_suffix(".pcm")
    out.write_bytes(blob)
    print(f"wrote {out} ({len(blob)} bytes)")
    if transcript:
        print("transcript:", "".join(transcript)[:300])
    if usage and usage.get("cost") is not None:
        print(f"cost: ${usage['cost']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("models", help="list models that output a modality")
    m.add_argument("--kind", choices=["image", "video", "audio"], required=True)
    m.set_defaults(fn=cmd_models)

    i = sub.add_parser("image", help="text/image -> image")
    i.add_argument("--prompt", required=True)
    i.add_argument("--out", required=True)
    i.add_argument("--model")
    i.add_argument("--aspect", default="16:9")
    i.add_argument("--resolution", help="e.g. 1K, 2K, 4K (model dependent)")
    i.add_argument("--ref", action="append", help="reference image path (repeatable)")
    i.add_argument("--n", type=int, default=1)
    i.set_defaults(fn=cmd_image)

    v = sub.add_parser("video", help="text/image -> video clip (async)")
    v.add_argument("--prompt", required=True)
    v.add_argument("--out", required=True)
    v.add_argument("--model")
    v.add_argument("--duration", type=int)
    v.add_argument("--resolution", default="480p", help="matches the 480p default output; not every model supports it")
    v.add_argument("--aspect", default="16:9")
    v.add_argument("--first-frame", help="image to use as the first frame")
    v.add_argument("--ref", action="append", help="style reference image (repeatable)")
    v.add_argument("--audio", action="store_true", help="let the model generate a soundtrack")
    v.add_argument("--timeout", type=int, default=1200)
    v.set_defaults(fn=cmd_video)

    au = sub.add_parser("audio", help="text -> music / sound / speech")
    au.add_argument("--prompt", required=True)
    au.add_argument("--out", required=True, help="extension picks the format: .wav, .mp3, .flac")
    au.add_argument("--model")
    au.add_argument("--voice", help="only for speech models, e.g. alloy")
    au.set_defaults(fn=cmd_audio)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()

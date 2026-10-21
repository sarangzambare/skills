#!/usr/bin/env python3
"""Print the fastest working H.264 encoder args for ffmpeg on this machine.

Tries hardware encoders first (VideoToolbox, NVENC, QSV, VAAPI, AMF) with a tiny test encode,
falls back to libx264 ultrafast. Result is cached in ~/.cache/explainer-videos/hwenc.txt.

  ffmpeg -i in.mp4 $(python hwenc.py) -c:a aac out.mp4
  python hwenc.py --refresh   # re-detect

Note: the VAAPI args include their own -vf; if you also need filters, prepend them to that chain.
"""
import subprocess
import sys
from pathlib import Path

CACHE = Path.home() / ".cache/explainer-videos/hwenc.txt"

CANDIDATES = [
    ["-c:v", "h264_videotoolbox", "-b:v", "2M", "-allow_sw", "1"],            # macOS
    ["-c:v", "h264_nvenc", "-preset", "p1", "-b:v", "2M"],                    # NVIDIA
    ["-c:v", "h264_qsv", "-preset", "veryfast", "-b:v", "2M"],                # Intel
    ["-c:v", "h264_amf", "-quality", "speed", "-b:v", "2M"],                  # AMD (Windows)
    ["-vaapi_device", "/dev/dri/renderD128", "-vf", "format=nv12,hwupload",
     "-c:v", "h264_vaapi", "-b:v", "2M"],                                      # Linux VAAPI
]
FALLBACK = ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "23"]


def works(args):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
           "-i", "testsrc=size=854x480:rate=30:duration=0.5", *args,
           "-pix_fmt", "yuv420p", "-f", "null", "-"]
    if "h264_vaapi" in args:
        cmd.remove("-pix_fmt"); cmd.remove("yuv420p")
    try:
        return subprocess.run(cmd, capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def main():
    if CACHE.exists() and "--refresh" not in sys.argv:
        print(CACHE.read_text().strip())
        return
    chosen = next((c for c in CANDIDATES if works(c)), FALLBACK)
    if "h264_vaapi" not in chosen:  # vaapi sets its own pixel format via -vf
        chosen = chosen + ["-pix_fmt", "yuv420p"]
    line = " ".join(chosen)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(line)
    print(line)


if __name__ == "__main__":
    main()

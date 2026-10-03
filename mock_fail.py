"""Mock updater: fails mid-way (ffmpeg 404 class) to exercise the error banner."""
import sys
import time

lines = [
    "→ Stopping Windows gateway process(es) before updating Hermes...",
    "✓ Gateway stopped",
    "→ Fetching updates...",
    "→ Found 24 new commit(s)",
    "→ Local changes detected — stashing before update...",
    "→ Pulling updates...",
    "→ Refreshing 19 active lazy backend(s)...",
    "→ Updating Node.js dependencies...",
    "→ Installing cua-driver (default tool)...",
    "  download failed from https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2026-09-10-15-31/ffmpeg.zip: HTTP Error 404: Not Found",
    "✗ Source update preparation failed: ffmpeg: install failed: download failed from https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2026-09-10-15-31/ffmpeg.zip: HTTP Error 404: Not Found",
]

for line in lines:
    print(line, flush=True)
    time.sleep(0.15)
sys.exit(1)

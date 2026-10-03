"""Mock updater: prints a realistic successful update stream (stage markers)."""
import sys
import time

lines = [
    "→ Stopping Windows gateway process(es) before updating Hermes...",
    "✓ Gateway stopped",
    "→ Fetching updates...",
    "→ Found 914 new commit(s)",
    "→ Local changes detected — stashing before update...",
    "→ Pulling updates...",
    "→ Restoring local changes...",
    "→ Refreshing 19 active lazy backend(s)...",
    "→ Warming npx cache for agent-browser...",
    "→ Updating Node.js dependencies...",
    "→ Installing cua-driver (default tool)...",
    "  download https://github.com/BtbN/FFmpeg-Builds/releases/download/x/ffmpeg.zip",
    "→ Building web UI...",
    "✓ assert-dist-built: dist/index.html + assets present",
    "→ Checking if desktop app needs rebuilding...",
    "→ Installing desktop workspace dependencies...",
    "→ Building desktop packaged app...",
    "[stage-native-deps] staged node-pty (win32-x64)",
    "[set-exe-identity] done — Hermes icon + identity stamped",
    "✓ Desktop packaged app ready",
    "✓ Code updated!",
    "→ Syncing bundled skills...",
    "→ Syncing bundled skills to all profiles...",
    "→ Checking configuration for new options...",
    "✓ Profile 'deep': config format updated (v46 → v49)",
    "✓ Update complete! (v0.21.5+3722.gac9a850.dirty → v0.21.5+5842.ga28aaa1) [main @ a28aaa1edfe]",
    "◆ Reclaim ~60% of your session database disk",
    "✓ Gateway started via cold-start after update (PID: 1180)",
]

for line in lines:
    print(line, flush=True)
    time.sleep(0.15)
sys.exit(0)

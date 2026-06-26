#!/usr/bin/env bash
# Process raw screencast recordings into the docs module's web-ready videos.
#
# For each *.webm / *.mp4 in RAW_DIR it:
#   1. trims the leading white/blank frames (Playwright/browser recordings open
#      on a blank frame),
#   2. re-encodes to a web-optimized H.264 MP4 (faststart, yuv420p, <=1280 wide),
#   3. extracts a poster frame from ~35% in.
# Outputs land next to the docs they appear in:
#   static/video/<name>.mp4   and   static/img/poster-<name>.jpg
#
# Usage:  tests/e2e/process-docs-videos.sh [RAW_DIR]
#         RAW_DIR defaults to tests/e2e/screencast-raw
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
RAW_DIR="${1:-$HERE/screencast-raw}"
VID_OUT="$REPO/odoo-addons/tvbo_platform_docs/static/video"
IMG_OUT="$REPO/odoo-addons/tvbo_platform_docs/static/img"

command -v ffmpeg >/dev/null || { echo "ffmpeg not found" >&2; exit 1; }
mkdir -p "$VID_OUT" "$IMG_OUT"

# First timestamp (0..3s) whose average luminance drops below 200 (i.e. content,
# not a blank/white frame). Echoes 0 if it never looks blank.
content_start() {
  local f="$1" t y
  for t in 0 0.3 0.6 0.9 1.2 1.5 2.0 2.5 3.0; do
    y=$(ffmpeg -hide_banner -nostats -ss "$t" -i "$f" \
          -vf "signalstats,metadata=print:key=lavfi.signalstats.YAVG" \
          -frames:v 1 -f null - 2>&1 | grep -oE 'YAVG=[0-9.]+' | head -1 | cut -d= -f2)
    [ -n "$y" ] && awk "BEGIN{exit !($y < 200)}" && { echo "$t"; return; }
  done
  echo 0
}

shopt -s nullglob
found=0
for f in "$RAW_DIR"/*.webm "$RAW_DIR"/*.mp4; do
  found=1
  name="$(basename "$f")"; name="${name%.*}"
  start="$(content_start "$f")"
  ffmpeg -hide_banner -loglevel error -ss "$start" -i "$f" \
    -c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p -movflags +faststart \
    -vf "scale='min(1280,iw)':-2" -an "$VID_OUT/$name.mp4" -y
  dur="$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$VID_OUT/$name.mp4")"
  pt="$(awk "BEGIN{printf \"%.1f\", ${dur:-2} * 0.35}")"
  ffmpeg -hide_banner -loglevel error -ss "$pt" -i "$VID_OUT/$name.mp4" \
    -frames:v 1 -q:v 3 "$IMG_OUT/poster-$name.jpg" -y
  echo "✓ $name  (trim ${start}s, poster ${pt}s, $(du -h "$VID_OUT/$name.mp4" | cut -f1))"
done

[ "$found" = 1 ] || { echo "no *.webm/*.mp4 in $RAW_DIR" >&2; exit 1; }

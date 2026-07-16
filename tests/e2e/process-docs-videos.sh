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

# Average luminance (Y) of the frame at time $2 of file $1.
yavg() {
  ffmpeg -hide_banner -nostats -ss "$2" -i "$1" \
    -vf "signalstats,metadata=print:key=lavfi.signalstats.YAVG" \
    -frames:v 1 -f null - 2>&1 | grep -oE 'YAVG=[0-9.]+' | head -1 | cut -d= -f2
}

# Choose a representative poster timestamp. A fixed fraction (e.g. 35%) can land
# on a "Loading…" spinner or an empty pre-render frame — and average luminance
# can't tell those apart from a settled view (a sparse graph barely moves YAVG).
# Compressed frame size does: a populated graph / filled panel has far more
# visual detail and encodes to a much larger JPEG than a loading/blank frame.
# So sample a few frames across the middle of the clip and keep the busiest one.
poster_time() {
  local f="$1" dur="$2" tmp t frac sz best_sz="" best_t=""
  tmp="$(mktemp -t poster).jpg"
  for frac in 0.35 0.45 0.55 0.65; do
    t="$(awk "BEGIN{printf \"%.1f\", $dur*$frac}")"
    ffmpeg -hide_banner -loglevel error -ss "$t" -i "$f" -frames:v 1 -q:v 3 "$tmp" -y 2>/dev/null || continue
    sz="$(wc -c < "$tmp" 2>/dev/null | tr -d ' ')"; [ -n "$sz" ] || continue
    if [ -z "$best_sz" ] || [ "$sz" -gt "$best_sz" ]; then best_sz="$sz"; best_t="$t"; fi
  done
  rm -f "$tmp"
  [ -n "$best_t" ] || best_t="$(awk "BEGIN{printf \"%.1f\", $dur*0.45}")"
  printf '%s\n' "$best_t"
}

# First timestamp showing real content rather than a blank loading frame.
# Playwright opens the recording on a near-white blank page (YAVG≈235); content
# is always darker (text/graphics). We compare each frame's YAVG to the opening
# blank frame's and trim to the first frame that is meaningfully darker (or
# clearly dark in absolute terms). This is:
#   - theme-agnostic: works for light pages too, where the old fixed YAVG<200
#     test failed and left the white lead in place;
#   - cursor-proof: YAVG (an average) ignores the few dark pixels of the injected
#     cursor, unlike a min/max dynamic-range test;
#   - patient: scans to 12s so long cold-load white leads ("10s just white") are
#     trimmed even when server warm-up did not fully hide them.
# Echoes 0 when the opening frame already shows content (nothing to trim).
content_start() {
  local f="$1" t y base
  base="$(yavg "$f" 0)"; [ -n "$base" ] || base=235
  # If the opening frame is already dark enough to be content (not the near-white
  # blank Playwright opens on), there is no white lead — don't trim anything.
  awk "BEGIN{exit !($base < 215)}" && { echo 0; return; }
  for t in 0.3 0.6 0.9 1.2 1.5 2.0 2.5 3.0 4.0 5.0 6.0 7.0 8.0 9.0 10.0 11.0 12.0; do
    y="$(yavg "$f" "$t")"; [ -n "$y" ] || continue
    awk "BEGIN{exit !(($base - $y) > 10 || $y < 200)}" && { echo "$t"; return; }
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
  pt="$(poster_time "$VID_OUT/$name.mp4" "${dur:-2}")"
  ffmpeg -hide_banner -loglevel error -ss "$pt" -i "$VID_OUT/$name.mp4" \
    -frames:v 1 -q:v 3 "$IMG_OUT/poster-$name.jpg" -y
  echo "✓ $name  (trim ${start}s, poster ${pt}s, $(du -h "$VID_OUT/$name.mp4" | cut -f1))"
done

# Poster-refresh pass: the cinematic demo specs (demo-*.spec.ts) write their mp4
# straight into static/video via helpers/cinematic.ts and never emit a poster, so
# after they re-record their poster goes stale. Regenerate a poster for any docs
# video whose poster is missing or older than the mp4 — keeping every embedded
# video's poster in sync with its current footage. Videos untouched since their
# last poster (poster newer than mp4) are skipped, so this never churns media the
# demo run didn't regenerate.
for v in "$VID_OUT"/*.mp4; do
  [ -e "$v" ] || continue
  name="$(basename "$v")"; name="${name%.*}"
  poster="$IMG_OUT/poster-$name.jpg"
  [ -f "$poster" ] && [ "$poster" -nt "$v" ] && continue
  dur="$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$v")"
  pt="$(poster_time "$v" "${dur:-2}")"
  ffmpeg -hide_banner -loglevel error -ss "$pt" -i "$v" -frames:v 1 -q:v 3 "$poster" -y
  echo "↻ poster-$name.jpg  (from $name.mp4 @ ${pt}s)"
done

[ "$found" = 1 ] || { echo "no *.webm/*.mp4 in $RAW_DIR" >&2; exit 1; }

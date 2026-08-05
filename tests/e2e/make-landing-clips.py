#!/usr/bin/env python3
"""Derive the homepage's two platform clips from the recorded docs screencasts.

The casts are paced for a documentation page: they dwell on each step so a reader
can follow along. On the landing page the same footage sits in a card that loops,
where those dwells read as the video being broken. This cuts every freeze down to
HOLD seconds (which also removes the "Loading..." lead a cold page opens on) and
crops the platform header off the top, so the clip is the app rather than a
screenshot of the site the visitor is already on.

Run after tests/e2e/process-docs-videos.sh; both are idempotent.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STATIC = REPO / 'odoo-addons' / 'tvbo_platform_docs' / 'static'

# How long each pause is allowed to hold. A fixed value makes the clip as long as
# the machine that recorded it was slow — the same cast came back 47s on an idle
# box and 82s on a loaded one, because a slower run splits one dwell into more
# freezes. Solve the hold against a target length instead, so the card gets a clip
# of roughly the same length whoever records it.
TARGET = 45.0
HOLD_MAX = 0.8
HOLD_MIN = 0.25
HEADER_PX = 57  # the platform header; casts are 1280x720 or 1366x900, so crop off iw/ih

# (recorded cast, landing clip) — the landing names say what the card shows.
CLIPS = [
    ('tvbo-find-and-inspect-a-model', 'tvbo-browse-the-library'),
    ('tvbo-build-an-experiment', 'tvbo-build-your-own'),
]


def run(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=False).stdout


def duration(path: Path) -> float:
    return float(run('ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                     '-of', 'csv=p=0', str(path)).strip())


def frame_bytes(path: Path, t: float) -> int:
    """Compressed size of one frame — a stand-in for how much is actually drawn."""
    out = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-ss', f'{t:.2f}',
                          '-i', str(path), '-frames:v', '1', '-q:v', '3', '-f', 'image2pipe',
                          '-c:v', 'mjpeg', '-'], capture_output=True, check=False)
    return len(out.stdout)


def content_start(path: Path, total: float) -> float:
    """First frame showing the populated page rather than a spinner or an empty form.

    A freeze test cannot find this: a 'Loading...' screen animates, so it never
    registers as frozen. Compressed frame size does separate them — blank, spinner
    and filled page sit at clearly different sizes — so take the first frame that
    reaches most of the opening window's peak.
    """
    window = min(12.0, total)
    samples = [(t / 4, frame_bytes(path, t / 4)) for t in range(1, int(window * 4))]
    if not samples:
        return 0.0
    peak = max(size for _, size in samples)
    for t, size in samples:
        if size >= peak * 0.75:
            return max(0.0, t - 0.2)
    return 0.0


def moving_spans(path: Path, total: float) -> list[tuple[float, float]]:
    """Every span worth keeping: each freeze longer than the hold is clipped to it."""
    out = run('ffmpeg', '-hide_banner', '-nostats', '-i', str(path), '-vf',
              'freezedetect=n=-50dB:d=0.35,metadata=mode=print:file=-', '-map', '0:v', '-f', 'null', '-')
    freezes = list(zip((float(x) for x in re.findall(r'freeze_start=([\d.]+)', out)),
                       (float(x) for x in re.findall(r'freeze_duration=([\d.]+)', out))))
    long = [f for f in freezes if f[1] > HOLD_MIN]
    moving = total - sum(length for _, length in long)
    hold = HOLD_MAX if not long else min(HOLD_MAX, max(HOLD_MIN, (TARGET - moving) / len(long)))
    spans, cur = [], 0.0
    for start, length in freezes:
        if length <= hold:
            continue
        end = min(start + hold, total)
        if end > cur:
            spans.append((cur, end))
        cur = min(start + length, total)
    if cur < total:
        spans.append((cur, total))
    return [(a, b) for a, b in spans if b - a > 0.12]


def encode(src: Path, dst: Path, spans: list[tuple[float, float]], tmp: Path) -> None:
    crop = f'crop=iw:ih-{HEADER_PX}:0:{HEADER_PX}'
    parts = []
    for i, (a, b) in enumerate(spans):
        part = tmp / f'{i:03d}.mp4'
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-ss', f'{a:.2f}',
                        '-t', f'{b - a:.2f}', '-i', str(src), '-vf', crop, '-c:v', 'libx264',
                        '-crf', '20', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-an',
                        str(part), '-y'], check=True)
        parts.append(part)
    listing = tmp / 'list.txt'
    listing.write_text(''.join(f"file '{p}'\n" for p in parts))
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
                    '-i', str(listing), '-c:v', 'libx264', '-crf', '22', '-preset', 'medium',
                    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', str(dst), '-y'], check=True)


def poster_time(path: Path, total: float) -> float:
    """Busiest frame across the clip — a settled, populated view.

    The card carries `preload="none"`, so the poster is what most visitors see;
    a fixed early timestamp lands on a half-drawn panel.
    """
    return max((frame_bytes(path, total * f), total * f) for f in (0.35, 0.5, 0.65, 0.8))[1]


def main() -> int:
    missing = [s for s, _ in CLIPS if not (STATIC / 'video' / f'{s}.mp4').exists()]
    if missing:
        print(f'missing recorded cast(s): {", ".join(missing)} — record them first', file=sys.stderr)
        return 1
    for source, landing in CLIPS:
        src = STATIC / 'video' / f'{source}.mp4'
        dst = STATIC / 'video' / f'{landing}.mp4'
        total = duration(src)
        start = content_start(src, total)
        spans = [(max(a, start), b) for a, b in moving_spans(src, total) if b > start]
        with tempfile.TemporaryDirectory() as td:
            encode(src, dst, spans, Path(td))
        out = duration(dst)
        pt = poster_time(dst, out)
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-ss', f'{pt:.2f}', '-i', str(dst),
                        '-frames:v', '1', '-f', 'image2', '-c:v', 'libwebp', '-quality', '80',
                        '-compression_level', '6', str(STATIC / 'img' / f'poster-{landing}.webp'),
                        '-y'], check=True)
        print(f'✓ {landing}  {total:.1f}s → {out:.1f}s in {len(spans)} spans '
              f'(from {start:.1f}s, poster {pt:.1f}s)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

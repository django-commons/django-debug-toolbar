#!/usr/bin/env bash
#
# Regenerate the PNG logos from the SVG sources.
#
# The SVGs are the source of truth. Whenever a logo SVG changes, re-run this
# script so the bundled PNGs stay in sync.
#
# Each SVG is rasterized with headless Chrome at 3x its intrinsic size, keeping
# a transparent background (the square app icons stay opaque via their own
# background rect).
#
# Usage (from this directory):
#     ./regenerate-pngs.sh
#
# Requires Google Chrome. Override the binary with the CHROME env var, e.g.
#     CHROME=chromium ./regenerate-pngs.sh
set -euo pipefail

CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
cd "$(dirname "$0")"

for f in *.svg; do
    w=$(grep -oE 'width="[0-9]+"' "$f" | head -1 | grep -oE '[0-9]+')
    h=$(grep -oE 'height="[0-9]+"' "$f" | head -1 | grep -oE '[0-9]+')
    out="${f%.svg}.png"
    "$CHROME" --headless --disable-gpu --screenshot="$PWD/$out" \
        --window-size="${w},${h}" --force-device-scale-factor=3 \
        --default-background-color=00000000 "file://$PWD/$f" >/dev/null 2>&1
    echo "${f} -> ${out} (${w}x${h} @3x)"
done

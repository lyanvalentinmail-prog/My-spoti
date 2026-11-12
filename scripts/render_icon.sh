#!/usr/bin/env bash
set -euo pipefail

# Render at 4× and downsample for smooth edges. This uses ImageMagick's own
# drawing primitives, so no SVG delegate is required.
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

convert -size 1024x1024 xc:'#06131F' \
  -fill '#081A29' -draw 'circle 512,370 512,20' \
  -fill '#0B2231' -draw 'circle 512,350 512,105' \
  -fill '#0E2A38' -draw 'circle 512,330 512,185' \
  -fill '#E6FFFB' -draw "path 'M 628,230 L 628,548 C 597,531 556,528 515,542 C 445,565 403,624 421,674 C 439,725 510,747 580,724 C 638,705 677,660 679,617 L 679,378 L 817,347 L 817,255 L 628,296 Z'" \
  -fill '#5EEAD4' -draw 'circle 795,296 840,296' \
  -fill '#0E7490' -draw "path 'M -70,701 C 57,615 179,615 306,701 C 433,787 555,787 682,701 C 809,615 931,615 1058,701 L 1058,1024 L -70,1024 Z'" \
  -fill '#14B8A6' -draw "path 'M -73,770 C 53,678 177,678 303,770 C 429,862 553,862 679,770 C 805,678 929,678 1055,770 L 1055,1024 L -73,1024 Z'" \
  -fill '#5EEAD4' -draw "path 'M -68,846 C 57,766 182,766 307,846 C 432,926 557,926 682,846 C 807,766 932,766 1057,846 L 1057,1028 L -68,1028 Z'" \
  -fill none -stroke '#CCFBF1' -strokewidth 18 -draw "path 'M -36,856 C 76,801 188,801 300,856 C 412,911 524,911 636,856 C 748,801 860,801 972,856'" \
  "$tmp/art.png"

convert -size 1024x1024 xc:none -fill white \
  -draw 'roundrectangle 0,0 1023,1023 228,228' "$tmp/mask.png"

convert "$tmp/art.png" "$tmp/mask.png" -alpha off -compose CopyOpacity -composite \
  -resize 256x256 -strip PNG32:"$root/icon.png"

identify -format '✓ icon.png: %wx%h, %b\n' "$root/icon.png"

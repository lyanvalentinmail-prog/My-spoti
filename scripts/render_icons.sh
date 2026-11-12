#!/usr/bin/env bash
set -euo pipefail

# Render at 4× and downsample for smooth edges. ImageMagick's own primitives
# are used so no SVG delegate is required.
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

rounded_mask() {
  convert -size 1024x1024 xc:none -fill white \
    -draw 'roundrectangle 0,0 1023,1023 228,228' "$tmp/mask.png"
}

finish() {
  local source="$1" output="$2"
  convert "$source" "$tmp/mask.png" -alpha off -compose CopyOpacity -composite \
    -resize 256x256 -strip PNG32:"$output"
  identify -format "✓ ${output#$root/}: %wx%h, %b\\n" "$output"
}

render_marea() {
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
    "$tmp/marea.png"
  finish "$tmp/marea.png" "$root/extensions/marea-nocturna/icon.png"
}

render_music() {
  convert -size 1024x1024 xc:'#07111C' \
    -fill '#0C1D2B' -draw 'circle 512,386 512,56' \
    -fill '#102536' -draw 'circle 512,386 512,145' \
    -fill '#B45309' -draw "path 'M 252,433 L 772,433 L 828,555 L 828,800 C 828,837 798,867 761,867 L 263,867 C 226,867 196,837 196,800 L 196,555 Z'" \
    -fill '#FCD34D' -draw "path 'M 252,433 L 772,433 L 828,555 L 196,555 Z'" \
    -fill '#F59E0B' -draw 'roundrectangle 240,555 784,823 24,24' \
    -fill none -stroke '#FFFBEB' -strokewidth 40 -draw 'line 393,657 631,657' \
    -fill none -stroke '#ECFDF5' -strokewidth 74 -draw 'line 512,173 512,527' \
    -fill none -stroke '#ECFDF5' -strokewidth 74 -draw "path 'M 374,393 L 512,535 L 650,393'" \
    -fill '#5EEAD4' -stroke none -draw 'circle 785,239 843,239' \
    "$tmp/music.png"
  finish "$tmp/music.png" "$root/extensions/musica-abierta/icon.png"
}

rounded_mask
case "${1:-all}" in
  all) render_marea; render_music ;;
  marea-nocturna) render_marea ;;
  musica-abierta) render_music ;;
  *) echo "Unknown extension: $1" >&2; exit 2 ;;
esac

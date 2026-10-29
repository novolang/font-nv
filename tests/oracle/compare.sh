#!/usr/bin/env bash
# tests/oracle/compare.sh - shape the same text in the same fonts with this
# package and with HarfBuzz, and compare the glyph numbers, the pen positions,
# the width and the control box of each outline against FreeType's.
#
# Needs libharfbuzz.so.0 and libfreetype.so.6 and python3.  Run from the
# package directory:  bash tests/oracle/compare.sh [FONT FACE]...
# With no arguments it takes the fonts below, which are where Debian-family
# systems install them.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG="$(cd "$HERE/../.." && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/font-nv-oracle.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
( cd "$PKG" && novo build tests/oracle/probe.nv -o "$WORK/probe" >/dev/null 2>&1 ) || { echo "probe did not build"; exit 1; }

fonts=("$@")
if [ ${#fonts[@]} -eq 0 ]; then
  fonts=(
    /usr/share/fonts/truetype/lato/Lato-Regular.ttf 0
    /usr/share/fonts/truetype/lato/Lato-Bold.ttf 0
    /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf 0
    /usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf 0
    /usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf 0
    /usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf 0
    /usr/share/fonts/truetype/open-sans/OpenSans-Regular.ttf 0
    /usr/share/fonts/truetype/roboto-slab/RobotoSlab-Regular.ttf 0
    /usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf 0
    /usr/share/fonts/truetype/freefont/FreeSerif.ttf 0
    /usr/share/fonts/truetype/freefont/FreeSans.ttf 0
    /usr/share/fonts/opentype/fira/FiraSans-Book.otf 0
    /usr/share/fonts/truetype/arphic/uming.ttc 1
  )
fi

texts=("AVA To fi ffi Wa" "The quick brown fox jumps over the lazy dog" "Hello, World! 0123456789"
       "Office affirm Waffle éàüß €" "Typography: Yo Tj Ty P. F, L'")
pass=0; fail=0
for ((i = 0; i < ${#fonts[@]}; i += 2)); do
  font="${fonts[i]}"; face="${fonts[i+1]}"
  [ -f "$font" ] || continue
  for text in "${texts[@]}"; do
    for feats in none liga; do
      ours="$("$WORK/probe" "$font" "$face" "$text" "$feats" 2>&1 | grep -v '^KERNSRC')"
      theirs="$(python3 "$HERE/oracle.py" "$font" "$face" "$text" "$feats" 2>&1)"
      if [ "$ours" == "$theirs" ]; then pass=$((pass + 1)); else
        fail=$((fail + 1)); echo "DIFF $font $face [$text] $feats"; diff <(echo "$ours") <(echo "$theirs") | head -6
      fi
    done
  done
done
echo "oracle: $pass runs agree, $fail differ"
[ "$fail" -eq 0 ]

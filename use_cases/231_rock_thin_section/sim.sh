#!/usr/bin/env bash
# Simulated: Rock Thin Section Preparation
set -euo pipefail

OUTFILE=""
GR=""
CH=""
PG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --grind_rpm) GR="$2"; shift 2 ;;
        --cure_hrs) CH="$2"; shift 2 ;;
        --polish_grit) PG="$2"; shift 2 ;;
        --rock_type) shift 2 ;;
        --target_um) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$GR" ] || [ -z "$CH" ] || [ -z "$PG" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v GR="$GR" -v CH="$CH" -v PG="$PG" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    gr = (GR - 250) / 150; ch = (CH - 30) / 18; pg = (PG - 900) / 300;
    clar = 6.5 - 0.5*gr + 0.5*ch + 0.8*pg - 0.3*gr*gr - 0.2*ch*ch - 0.3*pg*pg + 0.2*ch*pg;
    var_ = 5 + 1.5*gr - 0.5*ch - 0.8*pg + 0.5*gr*gr + 0.2*ch*ch;
    if (clar < 1) clar = 1; if (clar > 10) clar = 10; if (var_ < 1) var_ = 1;
    printf "{\"optical_clarity\": %.1f, \"thickness_variation_um\": %.1f}", clar + n1*0.3, var_ + n2*0.5;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

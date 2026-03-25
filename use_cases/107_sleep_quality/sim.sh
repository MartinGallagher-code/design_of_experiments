#!/usr/bin/env bash
# Simulated: Sleep Quality Optimization
set -euo pipefail

OUTFILE=""
RT=""
SC=""
CC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --room_temp) RT="$2"; shift 2 ;;
        --screen_cutoff) SC="$2"; shift 2 ;;
        --caffeine_cutoff) CC="$2"; shift 2 ;;
        --bedtime) shift 2 ;;
        --wake_time) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$RT" ] || [ -z "$SC" ] || [ -z "$CC" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v RT="$RT" -v SC="$SC" -v CC="$CC" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    rt = (RT - 19) / 3;
    sc = (SC - 75) / 45;
    cc = (CC - 10) / 4;
    slp = 72 + 3*rt + 5*sc + 4*cc - 4*rt*rt - 2*sc*sc - 1.5*cc*cc + 1.5*rt*sc;
    wk = 2.5 - 0.4*rt - 0.6*sc - 0.5*cc + 0.3*rt*rt + 0.2*sc*sc + 0.15*rt*cc;
    if (slp < 20) slp = 20; if (slp > 100) slp = 100;
    if (wk < 0) wk = 0;
    printf "{\"sleep_score\": %.0f, \"wake_count\": %.1f}", slp + n1*4, wk + n2*0.4;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"

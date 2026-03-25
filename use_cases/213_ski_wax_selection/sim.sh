#!/usr/bin/env bash
# Simulated: Ski Wax Temperature Match
set -euo pipefail

OUTFILE=""
WT=""
IT=""
LY=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --out) OUTFILE="$2"; shift 2 ;;
        --wax_temp_mid_c) WT="$2"; shift 2 ;;
        --iron_temp_c) IT="$2"; shift 2 ;;
        --layers) LY="$2"; shift 2 ;;
        --snow_temp) shift 2 ;;
        --ski_base) shift 2 ;;
        *) shift ;;
    esac
done

if [ -z "$WT" ] || [ -z "$IT" ] || [ -z "$LY" ]; then
    echo "Missing required factors" >&2
    exit 1
fi

RESULT=$(awk -v WT="$WT" -v IT="$IT" -v LY="$LY" -v seed="$RANDOM" '
BEGIN {
    srand(seed);
    n1 = (rand() - 0.5) * 2;
    n2 = (rand() - 0.5) * 2;

    wt = (WT - -7.5) / 7.5; it = (IT - 130) / 20; ly = (LY - 2.5) / 1.5;
    glide = 110 + 3*wt + 2*it + 4*ly - 5*wt*wt - 1*it*it - 1*ly*ly + 0.5*wt*it;
    dur = 15 + 2*wt + 1*it + 5*ly - 1*wt*wt + 0.5*it*ly;
    if (glide < 95) glide = 95; if (dur < 3) dur = 3;
    printf "{\"glide_speed_pct\": %.0f, \"durability_km\": %.0f}", glide + n1*2, dur + n2*1;

}')

mkdir -p "$(dirname "$OUTFILE")"
echo "$RESULT" > "$OUTFILE"
echo "  -> $(cat "$OUTFILE")"
